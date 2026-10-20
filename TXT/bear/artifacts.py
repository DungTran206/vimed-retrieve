"""Artifact bất biến, hash thực, đọc SQLite snapshot và run manifest."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from .contracts import HashMismatchError, InputMissingError, SchemaInvalidError
from .io import (assert_valid_output_path, atomic_write_json, canonical_sha256,
                 read_json, resolve_repo_path, sha256_file)


def required_path(value):
    path = resolve_repo_path(value)
    if path is None or not path.is_file():
        raise InputMissingError(f"Thiếu file: {value}")
    return path


def file_identity(value):
    path = required_path(value)
    if path.suffix.lower() in (".sqlite", ".sqlite3", ".db") and Path(str(path) + "-wal").exists():
        raise SchemaInvalidError(f"SQLite có WAL: cần snapshot nhất quán do chủ dữ liệu cung cấp: {path}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def verify_identity(identity):
    actual = file_identity(identity["path"])
    if actual != identity:
        raise HashMismatchError(f"Input thay đổi: {identity['path']}")
    return actual


def verify_manifest(path):
    path = required_path(path)
    data = read_json(path)
    if data.get("status") != "completed":
        raise SchemaInvalidError(f"Manifest chưa completed: {path}")
    for item in data.get("inputs", []) + data.get("artifacts", []):
        verify_identity(item)
    return data


def start_run(output, cfg, inputs):
    root = assert_valid_output_path(resolve_repo_path(output), [i["path"] for i in inputs])
    for identity in inputs:
        if Path(identity["path"]).is_relative_to(root):
            raise SchemaInvalidError(f"Output directory chứa input immutable: {identity['path']}")
    # Run identity bao gồm code thực để không reuse cache sau khi sửa thuật toán.
    from .io import TXT_DIR, REPO_ROOT
    code_paths = sorted((TXT_DIR / "bear").glob("*.py")) + [REPO_ROOT / p for p in (
        "submit/submission.py", "scripts/val_calib.py", "index/fuse.py", "index/hybrid_cands.py",
        "crawl/filter_new_corpus.py")]
    cfg = cfg | {"code_hashes": {str(p.relative_to(REPO_ROOT)): sha256_file(p) for p in code_paths}}
    manifest = root / "manifest.json"
    key = canonical_sha256({"config": cfg, "inputs": inputs})
    if manifest.exists():
        old = read_json(manifest)
        if old.get("config_hash") != key:
            raise HashMismatchError(f"Không reuse output với config/input khác: {root}")
        if old.get("status") == "completed":
            verify_manifest(manifest)
            return root, old, True
    data = {"schema_version": 1, "status": "partial", "config_hash": key,
            "config": cfg, "inputs": inputs, "artifacts": [],
            "created_at": datetime.now(timezone.utc).isoformat()}
    atomic_write_json(manifest, data, input_paths=[i["path"] for i in inputs])
    return root, data, False


def complete_run(root, manifest, paths, **details):
    for item in manifest["inputs"]:
        verify_identity(item)
    manifest.update(details)
    manifest["artifacts"] = [file_identity(p) for p in paths]
    manifest["status"] = "completed"
    atomic_write_json(root / "manifest.json", manifest)
    return manifest


@contextmanager
def corpus_connection(path):
    path = required_path(path)
    if Path(str(path) + "-wal").exists():
        raise SchemaInvalidError(f"Snapshot có WAL: {path}")
    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN")
        yield conn
    finally:
        conn.close()


def corpus_schema(conn):
    tables = {name: [r[1] for r in conn.execute(f"PRAGMA table_info({name})")]
              for name in ("doc", "chunk")}
    key = "doc_id" if "doc_id" in tables["doc"] else "id"
    if key not in tables["doc"] or "body" not in tables["doc"]:
        raise SchemaInvalidError("doc cần doc_id/id và body")
    return key, tables


def read_corpus_batch(conn, ids):
    key, tables = corpus_schema(conn)
    fields = [key] + [f for f in ("title", "body", "lang", "domain") if f in tables["doc"]]
    rows = {}
    ids = list(ids)
    for offset in range(0, len(ids), 900):
        batch = ids[offset:offset + 900]
        marks = ",".join("?" for _ in batch)
        for row in conn.execute(f"SELECT {','.join(fields)} FROM doc WHERE {key} IN ({marks})", batch):
            rows[str(row[key])] = dict(row)
    return rows
