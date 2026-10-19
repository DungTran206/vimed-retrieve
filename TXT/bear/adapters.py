"""Strict data adapters and deterministic chunk/ranking mappings for BEAR."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .contracts import (
    ERROR_SCHEMA_INVALID,
    SchemaInvalidError,
    validate_doc_id,
    validate_finite_number,
    validate_query_id,
)
from .io import read_jsonl


@dataclass(frozen=True)
class RankedDocItem:
    """Document entry within a ranked query preserving exact source array order."""
    doc_id: str
    rank: int  # 1-based index in array
    score: float | None = None
    availability: str = "ranked"  # ranked, not_retrieved, not_scored, not_applicable

    def __post_init__(self) -> None:
        validate_doc_id(self.doc_id)
        if self.rank < 1:
            raise SchemaInvalidError(f"Rank must be >= 1, got {self.rank}")
        if self.score is not None:
            validate_finite_number(self.score, "score")


@dataclass(frozen=True)
class RankedQuery:
    """Complete ranked list for a single query."""
    query_id: int
    items: list[RankedDocItem]
    cutoff: int = field(init=False)

    def __post_init__(self) -> None:
        validate_query_id(self.query_id)
        object.__setattr__(self, "cutoff", len(self.items))


@dataclass(frozen=True)
class QueryRecord:
    """Query definition with joined entities and translation views."""
    query_id: int
    query: str
    entities: list[dict[str, Any]] = field(default_factory=list)
    parse_status: str = "unknown"  # verified, unknown, failed
    language_views: dict[str, str] = field(default_factory=dict)
    translation_provenance: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_query_id(self.query_id)


@dataclass(frozen=True)
class DocumentRecord:
    """Document record retrieved from read-only corpus store."""
    doc_id: str
    title: str
    body: str
    lang: str | None
    domain: str | None
    body_sha256: str

    def __post_init__(self) -> None:
        validate_doc_id(self.doc_id)


@dataclass(frozen=True)
class ChunkRef:
    """Deterministic reference to a document chunk."""
    corpus_hash: str
    doc_id: str
    body_sha256: str
    chunk_id_native: int
    ord_native: int
    exporter_idx: int
    start: int
    end: int
    text_sha256: str
    mapping_status: str = "verified"

    def __post_init__(self) -> None:
        validate_doc_id(self.doc_id)
        if self.start < 0 or self.end <= self.start:
            raise SchemaInvalidError(f"Invalid chunk offsets [{self.start}, {self.end}] for doc {self.doc_id}")


@dataclass(frozen=True)
class ChunkScore:
    """Chunk level score from Qwen or dense chunk models."""
    query_id: int
    doc_id: str
    chunk_idx: int
    score: float

    def __post_init__(self) -> None:
        validate_query_id(self.query_id)
        validate_doc_id(self.doc_id)
        if self.chunk_idx < 0:
            raise SchemaInvalidError(f"chunk_idx must be >= 0, got {self.chunk_idx}")
        validate_finite_number(self.score, "score")


def map_runtime_doc_id(raw_id: str, expected_namespace: str = "corpus") -> str:
    """Safely map runtime doc ID (e.g. 'corpus:123') to canonical internal ID '123'."""
    prefix = f"{expected_namespace}:"
    if not raw_id.startswith(prefix):
        raise SchemaInvalidError(f"Doc ID '{raw_id}' does not match expected namespace '{expected_namespace}'")
    suffix = raw_id[len(prefix):]
    return validate_doc_id(suffix)


def read_rank_source(file_path: Path | str, source_manifest: Mapping[str, Any] | None = None) -> Iterator[RankedQuery]:
    """Read a ranking JSONL source.
    
    Preserves exact array ordering as rank (source_rank = idx + 1).
    Rejects duplicate doc_id in same query.
    Distinguishes score 0.0 from not_scored.
    """
    path = Path(file_path)
    seen_qids = set()
    for line_no, row in enumerate(read_jsonl(path), 1):
        qid = validate_query_id(row.get("query_id") or row.get("id") or row.get("qid"))
        if qid in seen_qids:
            raise SchemaInvalidError(f"{path}:{line_no}: duplicate query {qid}")
        seen_qids.add(qid)
        cands_raw = row.get("candidates") or row.get("docs") or row.get("ranked_docs") or []
        if not isinstance(cands_raw, list):
            raise SchemaInvalidError(f"{path}:{line_no}: candidates cần list")
        
        seen_docs: set[str] = set()
        items: list[RankedDocItem] = []
        
        for idx, item in enumerate(cands_raw, start=1):
            if isinstance(item, (str, int)):
                doc_id = validate_doc_id(item)
                score = None
            elif isinstance(item, dict):
                doc_id = validate_doc_id(item.get("doc_id") or item.get("id") or item.get("doc"))
                score_raw = item.get("score")
                score = validate_finite_number(score_raw, "score", allow_none=True)
            else:
                raise SchemaInvalidError(f"Invalid candidate type in {path} for query {qid}: {type(item).__name__}")
                
            if doc_id in seen_docs:
                raise SchemaInvalidError(f"Duplicate doc_id '{doc_id}' in query {qid} in {path}")
            seen_docs.add(doc_id)
            
            items.append(RankedDocItem(
                doc_id=doc_id,
                rank=idx,
                score=score,
                availability="ranked",
            ))
            
        yield RankedQuery(query_id=qid, items=items)


def read_queries(
    query_path: Path | str,
    enriched_path: Path | str | None = None,
    expansion_path: Path | str | None = None,
) -> dict[int, QueryRecord]:
    """Read queries and join enriched entities without external dependencies."""
    records: dict[int, QueryRecord] = {}
    
    # 1. Base queries
    for row in read_jsonl(query_path):
        qid = validate_query_id(row.get("id") or row.get("query_id") or row.get("qid"))
        text = str(row.get("query") or row.get("text") or "").strip()
        if not text:
            raise SchemaInvalidError(f"Query {qid} in {query_path} has empty query text")
        if qid in records:
            raise SchemaInvalidError(f"Duplicate query {qid} in {query_path}")
        records[qid] = QueryRecord(
            query_id=qid,
            query=text,
            language_views={"vi": text},
        )
        
    # 2. Enriched queries join
    if enriched_path:
        seen_enriched = set()
        for row in read_jsonl(enriched_path):
            qid = validate_query_id(row.get("id") or row.get("query_id") or row.get("qid"))
            if qid in seen_enriched:
                raise SchemaInvalidError(f"Duplicate enriched query {qid}: {enriched_path}")
            seen_enriched.add(qid)
            if qid not in records:
                raise SchemaInvalidError(f"Unknown enriched query {qid}: {enriched_path}")
            base = records[qid]
            entities = row.get("entities") or []
            parse_status = row.get("parse_status", "unknown")
            lang_views = dict(base.language_views)
            if "en" in row and isinstance(row["en"], str):
                lang_views["en"] = row["en"]
            if "zh" in row and isinstance(row["zh"], str):
                lang_views["zh"] = row["zh"]
                
            records[qid] = QueryRecord(
                query_id=qid,
                query=base.query,
                entities=entities,
                parse_status=parse_status,
                language_views=lang_views,
                translation_provenance=row.get("translation_provenance", {}),
            )
            
    if expansion_path:
        from dataclasses import replace
        seen = set()
        for row in read_jsonl(expansion_path):
            qid = validate_query_id(row.get("id"))
            if qid in seen or qid not in records:
                raise SchemaInvalidError(f"Duplicate/unknown expansion qid {qid}")
            seen.add(qid)
            status = "unknown" if "parse_ok" not in row else ("parsed" if row["parse_ok"] is True else "failed")
            records[qid] = replace(records[qid], parse_status=status)
    return records


def read_chunk_scores(file_path: Path | str, namespace_manifest: Mapping[str, Any] | None = None) -> Iterator[ChunkScore]:
    """Read chunk scores JSONL and detect duplicate keys."""
    path = Path(file_path)
    seen_keys: set[tuple[int, str, int]] = set()
    
    for row in read_jsonl(path):
        qid = validate_query_id(row.get("query_id") or row.get("qid") or row.get("id"))
        doc_id = validate_doc_id(row.get("doc_id") or row.get("doc"))
        chunk_idx = row.get("chunk_idx") if row.get("chunk_idx") is not None else row.get("idx")
        if type(chunk_idx) is not int or chunk_idx < 0:
            raise SchemaInvalidError(f"{path}: idx phải integer >=0")
        score_val = validate_finite_number(row.get("score"), "score", allow_none=False)
        
        key = (qid, doc_id, chunk_idx)
        if key in seen_keys:
            raise SchemaInvalidError(f"Duplicate chunk score key (qid={qid}, doc={doc_id}, idx={chunk_idx}) in {path}")
        seen_keys.add(key)
        
        yield ChunkScore(
            query_id=qid,
            doc_id=doc_id,
            chunk_idx=chunk_idx,
            score=score_val,  # type: ignore[arg-type]
        )


def read_docs_readonly(
    db_path: Path | str,
    doc_ids: Sequence[str | int],
    batch_size: int = 900,
) -> Iterator[DocumentRecord]:
    """Read documents from SQLite corpus store strictly in read-only mode in batches <= 900."""
    if type(batch_size) is not int or not 1 <= batch_size <= 900:
        raise SchemaInvalidError("batch_size phải trong 1..900")
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Corpus database not found: {path}")

    # Open strictly in read-only mode via URI
    uri_path = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri_path, uri=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        from .artifacts import corpus_schema
        key, tables = corpus_schema(conn)
        for field_name in ("title", "lang", "domain"):
            if field_name not in tables["doc"]:
                raise SchemaInvalidError(f"doc thiếu {field_name}")
        clean_ids = [validate_doc_id(did) for did in doc_ids]
        # Batch in chunks <= 900
        for i in range(0, len(clean_ids), batch_size):
            chunk_ids = clean_ids[i:i + batch_size]
            placeholders = ",".join(["?"] * len(chunk_ids))
            cur.execute(
                f"SELECT {key} AS id, title, body, lang, domain FROM doc WHERE {key} IN ({placeholders})",
                chunk_ids,
            )
            for row in cur.fetchall():
                body_text = row["body"] or ""
                b_hash = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
                yield DocumentRecord(
                    doc_id=str(row["id"]),
                    title=str(row["title"] or ""),
                    body=body_text,
                    lang=row["lang"],
                    domain=row["domain"],
                    body_sha256=b_hash,
                )
    finally:
        conn.close()


def load_chunk_refs(
    db_path_or_conn: Path | str | sqlite3.Connection,
    doc_ids: Sequence[str | int],
    corpus_hash: str = "unhashed",
    batch_size: int = 900,
) -> dict[str, list[ChunkRef]]:
    """Load native chunks for doc_ids, discard empty slices, and assign exporter_idx in ORDER BY chunk_id.
    
    Validates character code point slices body[start:end].
    """
    if type(batch_size) is not int or not 1 <= batch_size <= 900:
        raise SchemaInvalidError("batch_size phải trong 1..900")
    close_conn = False
    if isinstance(db_path_or_conn, (str, Path)):
        path = Path(db_path_or_conn).resolve()
        uri_path = f"file:{path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri_path, uri=True)
        conn.row_factory = sqlite3.Row
        close_conn = True
    else:
        conn = db_path_or_conn

    cur = conn.cursor()
    result: dict[str, list[ChunkRef]] = {}

    try:
        from .artifacts import corpus_schema
        key, tables = corpus_schema(conn)
        if not {"chunk_id", "doc_id", "start", "end"} <= set(tables["chunk"]):
            raise SchemaInvalidError("chunk thiếu schema offsets")
        ord_field = "ord" if "ord" in tables["chunk"] else "chunk_id AS ord"
        clean_ids = [validate_doc_id(did) for did in doc_ids]
        for i in range(0, len(clean_ids), batch_size):
            batch_slice = clean_ids[i:i + batch_size]
            placeholders = ",".join(["?"] * len(batch_slice))
            
            # Fetch doc bodies for validation
            cur.execute(f"SELECT {key} AS id, body FROM doc WHERE {key} IN ({placeholders})", batch_slice)
            bodies = {str(row["id"]): (row["body"] or "") for row in cur.fetchall()}
            
            # Fetch chunks ordered by chunk_id
            cur.execute(
                f"SELECT chunk_id, doc_id, {ord_field}, start, end FROM chunk WHERE doc_id IN ({placeholders}) ORDER BY chunk_id ASC",
                batch_slice,
            )
            chunk_rows = cur.fetchall()

            for crow in chunk_rows:
                did = str(crow["doc_id"])
                if did not in bodies:
                    continue
                body = bodies[did]
                start = crow["start"]
                end = crow["end"]
                
                # Check slice bounds
                if start < 0 or end > len(body) or start >= end:
                    # Discard invalid or empty slice per submission.py contract
                    continue
                
                slice_text = body[start:end]
                if not slice_text.strip():
                    continue
                    
                body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
                text_hash = hashlib.sha256(slice_text.encode("utf-8")).hexdigest()

                if did not in result:
                    result[did] = []
                    
                exporter_idx = len(result[did])
                result[did].append(ChunkRef(
                    corpus_hash=corpus_hash,
                    doc_id=did,
                    body_sha256=body_hash,
                    chunk_id_native=crow["chunk_id"],
                    ord_native=crow["ord"],
                    exporter_idx=exporter_idx,
                    start=start,
                    end=end,
                    text_sha256=text_hash,
                    mapping_status="verified",
                ))
    finally:
        if close_conn:
            conn.close()

    return result

