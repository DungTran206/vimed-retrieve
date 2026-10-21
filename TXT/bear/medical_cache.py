"""Stage-specific, resumable artifacts for the medical-gate hypothesis.

Expensive query inference is independent of later scoring/config changes. Inputs,
prompts and the code used by each stage are hashed; a changed input never silently
reuses an old run. Runtime output remains below TXT and never overwrites inputs.
"""
from __future__ import annotations

import math
from pathlib import Path

from .contracts import HashMismatchError, SchemaInvalidError
from .io import (assert_valid_output_path, atomic_write_json, canonical_sha256,
                 read_json, resolve_repo_path, sha256_file)

VERSION = "medical_gate_hypothesis_v1"


def identity(path):
    path = resolve_repo_path(path)
    if path is None or not path.is_file():
        raise FileNotFoundError(f"Missing input file: {path}")
    if path.suffix in {".sqlite", ".sqlite3", ".db"} and Path(str(path) + "-wal").exists():
        raise SchemaInvalidError(f"Use a checkpointed SQLite snapshot: {path}")
    return {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}


def begin_stage(command, cfg, inputs, dependencies=()):
    root = assert_valid_output_path(resolve_repo_path(cfg["output_dir"]))
    identities = {name: identity(path) for name, path in inputs.items() if path is not None}
    for item in identities.values():
        if Path(item["path"]).is_relative_to(root):
            raise SchemaInvalidError("An output directory must not contain its immutable inputs")
    code = {str(resolve_repo_path(path)): sha256_file(resolve_repo_path(path)) for path in dependencies}
    if "api_key" in cfg.get("llm", {}):
        raise SchemaInvalidError("Use llm.api_key_env, never put API secrets in config/cache")
    recipe = {"version": VERSION, "command": command, "config": cfg,
              "inputs": identities, "code": code}
    key = canonical_sha256(recipe)
    manifest_path = root / "manifest.json"
    if manifest_path.is_file():
        previous = read_json(manifest_path)
        if previous.get("cache_key") != key:
            raise HashMismatchError(f"Output belongs to different inputs/config/code; choose a fresh output_dir: {root}")
        if previous.get("status") == "completed":
            for item in previous.get("artifacts", []):
                if identity(item["path"]) != item:
                    raise HashMismatchError(f"Cached artifact changed: {item['path']}")
            return root, previous, True
    elif root.exists() and any(root.iterdir()):
        raise SchemaInvalidError(f"Refuse to overwrite an unbound nonempty directory: {root}")
    manifest = {**recipe, "cache_key": key, "status": "partial", "artifacts": [],
                "hypothesis_only": True, "baseline_0391_reproduced": False}
    atomic_write_json(manifest_path, manifest)
    return root, manifest, False


def finish_stage(root, manifest, artifacts, **details):
    for item in manifest["inputs"].values():
        if identity(item["path"]) != item:
            raise HashMismatchError(f"Input changed during execution: {item['path']}")
    manifest.update(details)
    manifest["artifacts"] = [identity(path) for path in artifacts]
    manifest["status"] = "completed"
    atomic_write_json(root / "manifest.json", manifest)
    return manifest


def iter_checked_records(path, *, verify=True):
    """Read cached query rows, checking the producer manifest when available."""
    from .io import read_jsonl
    resolved = resolve_repo_path(path)
    manifest_path = resolved.parent / "manifest.json"
    if verify and manifest_path.is_file():
        manifest = read_json(manifest_path)
        if manifest.get("status") != "completed":
            raise SchemaInvalidError(f"Producer is not completed: {manifest_path}")
        recorded = [item for item in manifest.get("artifacts", []) if Path(item["path"]) == resolved]
        if not recorded or identity(resolved) != recorded[0]:
            raise HashMismatchError(f"Artifact not bound to producer manifest: {resolved}")
    yield from read_jsonl(resolved)


def checked_records(path):
    return list(iter_checked_records(path))


def finite(value, name="score"):
    if type(value) not in (float, int) or not math.isfinite(value):
        raise SchemaInvalidError(f"{name} must be a finite number")
    return float(value)


def merge_config(base, override):
    result = dict(base)
    for key, value in override.items():
        result[key] = merge_config(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else value
    return result
