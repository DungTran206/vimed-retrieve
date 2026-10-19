"""Synthetic fixture generator for BEAR unit tests and differential validation.

All fixtures are generated under TXT/runtime/tmp/<case_name> strictly complying
with the TXT boundary rule.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any, Mapping, Sequence

from TXT.bear.contracts import TXT_DIR
from TXT.bear.io import atomic_write_json, atomic_write_text, canonical_json_dumps, write_jsonl


def get_fixture_dir(case_name: str) -> Path:
    """Return an isolated directory for a specific test case under TXT/runtime/tmp."""
    d = TXT_DIR / "runtime" / "tmp" / "fixtures" / case_name
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_synthetic_corpus_db(
    db_path: Path,
    docs: Sequence[Mapping[str, Any]],
    chunks: Sequence[Mapping[str, Any]] | None = None,
) -> Path:
    """Create a SQLite database mirroring the corpus schema (tables 'doc' and 'chunk')."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE doc (
            id TEXT PRIMARY KEY,
            title TEXT,
            body TEXT,
            lang TEXT,
            domain TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE chunk (
            chunk_id INTEGER PRIMARY KEY,
            doc_id TEXT,
            ord INTEGER,
            start INTEGER,
            end INTEGER,
            n_chars INTEGER
        )
    """)

    for d in docs:
        cur.execute(
            "INSERT INTO doc (id, title, body, lang, domain) VALUES (?, ?, ?, ?, ?)",
            (str(d["id"]), d.get("title", ""), d.get("body", ""), d.get("lang", "vi"), d.get("domain", "test.vn")),
        )

    if chunks is not None:
        for c in chunks:
            cur.execute(
                "INSERT INTO chunk (chunk_id, doc_id, ord, start, end, n_chars) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    int(c["chunk_id"]),
                    str(c["doc_id"]),
                    int(c["ord"]),
                    int(c["start"]),
                    int(c["end"]),
                    int(c["end"] - c["start"]),
                ),
            )

    conn.commit()
    conn.close()
    return db_path


def create_synthetic_rank_source(
    file_path: Path,
    ranked_queries: Sequence[Mapping[str, Any]],
) -> Path:
    """Create a synthetic JSONL rank source file."""
    rows: list[dict[str, Any]] = []
    for item in ranked_queries:
        rows.append({
            "query_id": int(item["query_id"]),
            "candidates": [
                {
                    "doc_id": str(c["doc_id"]),
                    "score": float(c["score"]) if c.get("score") is not None else None,
                }
                for c in item["candidates"]
            ],
        })
    write_jsonl(file_path, rows)
    return file_path


def create_synthetic_chunk_scores(
    file_path: Path,
    score_records: Sequence[Mapping[str, Any]],
) -> Path:
    """Create a synthetic chunk scores JSONL file."""
    rows: list[dict[str, Any]] = []
    for s in score_records:
        rows.append({
            "query_id": int(s["query_id"]),
            "doc_id": str(s["doc_id"]),
            "chunk_idx": int(s["chunk_idx"]),
            "score": float(s["score"]),
        })
    write_jsonl(file_path, rows)
    return file_path

