"""Corpus-wide lexical candidate index for the two BEAR replacement experiments.

The index stores original Unicode bodies, exact body offsets, and an inverted
lexical index. It is independent of baseline rankings and intentionally uses no
labels, translations inferred from labels, or model-generated medical facts.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import math
import os
import re
import sqlite3
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .contracts import SchemaInvalidError, validate_doc_id
from .io import assert_valid_output_path, canonical_json_dumps, read_jsonl
from .structured_evidence import query_terms, score_evidence, tokenize


INDEX_VERSION = "bear_corpus_lexical_v1"
SCORER_VERSION = "bm25_structured_phrases_v1"
WINDOW_VERSION = "original_body_sentence_window_v1"


def _readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.with_name(path.name + "-wal").exists():
        raise SchemaInvalidError(f"SQLite snapshot has a WAL sidecar; checkpoint/copy it before use: {path}")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _documents(path: Path) -> Iterator[dict[str, Any]]:
    if path.suffix.lower() in {".sqlite", ".sqlite3", ".db"}:
        connection = _readonly(path)
        try:
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(doc)")}
            identifier = "doc_id" if "doc_id" in columns else "id" if "id" in columns else None
            if identifier is None or "body" not in columns:
                raise SchemaInvalidError("Corpus SQLite requires doc.(doc_id or id), body")
            selected = [identifier, "body"] + [name for name in ("lang", "title") if name in columns]
            # Column names come exclusively from the fixed allowlist above.
            sql = "SELECT " + ",".join('"' + name + '"' for name in selected) + ' FROM doc ORDER BY "' + identifier + '"'
            for row in connection.execute(sql):
                result = dict(row)
                result["doc_id"] = result.pop(identifier)
                yield result
        finally:
            connection.close()
    else:
        yield from read_jsonl(path)


def _validate_document(raw: Mapping[str, Any]) -> dict[str, Any]:
    identifier = raw.get("doc_id", raw.get("id"))
    doc_id = validate_doc_id(identifier)
    if "doc_id" in raw and "id" in raw and validate_doc_id(raw["id"]) != doc_id:
        raise SchemaInvalidError(f"Conflicting id and doc_id for {doc_id}")
    body, title, lang = raw.get("body"), raw.get("title"), raw.get("lang")
    for field, value in (("body", body), ("title", title), ("lang", lang)):
        if value is not None and not isinstance(value, str):
            raise SchemaInvalidError(f"Document {doc_id}: {field} must be a string or null")
    if lang is not None and (not lang or lang != lang.strip()):
        raise SchemaInvalidError(f"Document {doc_id}: language must be nonempty without padding")
    return {"doc_id": doc_id, "body": body, "title": title, "lang": lang}


def body_chunks(body: str | None, doc_id: str, chunk_chars: int = 1200) -> list[dict[str, Any]]:
    """Split original text at sentence/whitespace boundaries with Python offsets."""
    if type(chunk_chars) is not int or chunk_chars <= 0:
        raise SchemaInvalidError("chunk_chars must be a positive integer")
    if not body:
        return []
    boundaries = [match.end() for match in re.finditer(r"(?<=[.!?。！？])\s+|\n+", body)]
    boundaries.append(len(body))
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    result: list[dict[str, Any]] = []
    start = 0
    while start < len(body):
        while start < len(body) and body[start].isspace():
            start += 1
        if start >= len(body):
            break
        limit = min(start + chunk_chars, len(body))
        candidates = [point for point in boundaries if start < point <= limit]
        end = max(candidates) if candidates else limit
        if not candidates and end < len(body):
            spaces = [match.start() + start for match in re.finditer(r"\s+", body[start:end])]
            if spaces:
                end = spaces[-1]
        while end > start and body[end - 1].isspace():
            end -= 1
        if end <= start:
            end = limit
        ordinal = len(result)
        result.append({"doc_id": doc_id, "chunk_id_native": f"bear:{doc_id}:{ordinal}",
                       "ref_kind": "bear_window", "generator_version": WINDOW_VERSION,
                       "body_sha256": body_hash,
                       "text_sha256": hashlib.sha256(body[start:end].encode("utf-8")).hexdigest(),
                       "start": start, "end": end})
        start = end
    return result


def build_index(corpus_path: str | Path, index_path: str | Path, *,
                chunk_chars: int = 1200, overwrite: bool = False) -> dict[str, Any]:
    """Build a disk index from JSONL or a read-only existing ``doc`` SQLite table.

    Destination and temporary files must be below TXT and outside TXT/inputs.
    A failed build leaves an existing destination untouched.
    """
    source = Path(corpus_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    destination = assert_valid_output_path(index_path, input_paths=[source])
    if destination.exists() and not overwrite:
        raise FileExistsError(destination)
    if type(chunk_chars) is not int or chunk_chars <= 0:
        raise SchemaInvalidError("chunk_chars must be a positive integer")
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".partial", dir=destination.parent)
    os.close(handle)
    temporary = assert_valid_output_path(temporary_name, input_paths=[source, destination])
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(temporary)
        connection.executescript("""
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE documents (doc_id TEXT PRIMARY KEY, lang TEXT, title TEXT,
                body TEXT, length INTEGER NOT NULL, body_hash TEXT);
            CREATE TABLE chunks (doc_id TEXT NOT NULL, ordinal INTEGER NOT NULL,
                chunk_id_native TEXT NOT NULL, start INTEGER NOT NULL, end INTEGER NOT NULL,
                PRIMARY KEY(doc_id,ordinal));
            CREATE TABLE postings (term TEXT NOT NULL, doc_id TEXT NOT NULL,
                tf INTEGER NOT NULL, PRIMARY KEY(term,doc_id));
            CREATE TABLE terms (term TEXT PRIMARY KEY, df INTEGER NOT NULL);
        """)
        digest = hashlib.sha256()
        document_count = total_length = chunk_count = 0
        languages: Counter[str] = Counter()
        for raw in _documents(source):
            document = _validate_document(raw)
            doc_id, body, title, lang = (document[key] for key in ("doc_id", "body", "title", "lang"))
            # Title tokens have a fixed, documented weight of two. No stripping
            # of accents, decimal punctuation, hyphen identifiers, or gene digits.
            counts = Counter(tokenize(body or ""))
            counts.update(tokenize(title or ""))
            counts.update(tokenize(title or ""))
            length = sum(counts.values())
            try:
                connection.execute("INSERT INTO documents VALUES (?,?,?,?,?,?)", (
                    doc_id, lang, title, body, length,
                    hashlib.sha256(body.encode("utf-8")).hexdigest() if body is not None else None))
            except sqlite3.IntegrityError as error:
                raise SchemaInvalidError(f"Duplicate corpus document ID: {doc_id}") from error
            refs = body_chunks(body, doc_id, chunk_chars)
            connection.executemany("INSERT INTO chunks VALUES (?,?,?,?,?)", (
                (doc_id, ordinal, ref["chunk_id_native"], ref["start"], ref["end"])
                for ordinal, ref in enumerate(refs)))
            connection.executemany("INSERT INTO postings VALUES (?,?,?)", (
                (term, doc_id, count) for term, count in sorted(counts.items())))
            digest.update(canonical_json_dumps(document).encode("utf-8") + b"\n")
            document_count += 1
            total_length += length
            chunk_count += len(refs)
            if lang is not None:
                languages[lang] += 1
        if not document_count:
            raise SchemaInvalidError("Cannot build a BEAR index from an empty corpus")
        connection.execute("INSERT INTO terms SELECT term,COUNT(*) FROM postings GROUP BY term")
        connection.execute("CREATE INDEX postings_doc_id ON postings(doc_id)")
        connection.execute("CREATE INDEX documents_language ON documents(lang)")
        metadata = {"index_version": INDEX_VERSION, "scorer_version": SCORER_VERSION,
                    "corpus_hash": digest.hexdigest(), "document_count": document_count,
                    "total_length": total_length, "average_length": total_length / document_count if document_count else 0,
                    "languages": dict(sorted(languages.items())), "chunk_count": chunk_count,
                    "chunk_chars": chunk_chars, "source_path": str(source),
                    "candidate_policy": "all_documents_matching_any_query_token",
                    "title_token_weight": 2, "window_generator_version": WINDOW_VERSION,
                    "bm25_k1": 1.2, "bm25_b": 0.75,
                    "lexical_normalization": "BM25 / (2.2 * sum(query_term_IDF)), clipped at 1",
                    "score_formula": "0.6 * lexical_score + 0.4 * evidence_score",
                    "lexical_weight": 0.6, "evidence_weight": 0.4,
                    "empty_corpus_policy": "reject"}
        connection.executemany("INSERT INTO metadata VALUES (?,?)", (
            (key, canonical_json_dumps(value)) for key, value in sorted(metadata.items())))
        connection.commit()
        connection.close()
        connection = None
        os.replace(temporary, destination)
        return metadata
    finally:
        if connection is not None:
            connection.close()
        if temporary.exists():
            temporary.unlink()


class CorpusIndex:
    """Read-only corpus retrieval and identical evidence scoring for fusion."""

    def __init__(self, index_path: str | Path):
        self.path = Path(index_path).resolve()
        self.connection = _readonly(self.path)
        try:
            self.metadata = {row["key"]: json.loads(row["value"])
                             for row in self.connection.execute("SELECT key,value FROM metadata")}
            if self.metadata.get("index_version") != INDEX_VERSION:
                raise SchemaInvalidError("Unsupported BEAR corpus index version")
        except Exception:
            self.connection.close()
            raise

    def __enter__(self) -> "CorpusIndex":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        doc_id = validate_doc_id(doc_id)
        row = self.connection.execute("SELECT doc_id,lang,title,body,body_hash FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
        if not row:
            return None
        document = dict(row)
        document["body_sha256"] = document["body_hash"]
        return document

    def get_refs(self, doc_id: str) -> list[dict[str, Any]]:
        doc_id = validate_doc_id(doc_id)
        document = self.get_document(doc_id)
        if document is None:
            return []
        result = []
        for row in self.connection.execute(
                "SELECT doc_id,chunk_id_native,start,end FROM chunks WHERE doc_id=? ORDER BY ordinal", (doc_id,)):
            ref = dict(row)
            ref.update({"ref_kind": "bear_window", "generator_version": WINDOW_VERSION,
                        "corpus_hash": self.metadata["corpus_hash"],
                        "body_sha256": document["body_sha256"],
                        "text_sha256": hashlib.sha256(document["body"][ref["start"]:ref["end"]].encode("utf-8")).hexdigest()})
            result.append(ref)
        return result

    @staticmethod
    def _top_k(top_k: int) -> None:
        if type(top_k) is not int or top_k <= 0:
            raise SchemaInvalidError("top_k must be a positive integer")

    def _lexical_scores(self, query: str | Mapping[str, Any]) -> tuple[dict[str, float], float]:
        terms = sorted(set(query_terms(query)))
        scores: dict[str, float] = defaultdict(float)
        count = self.metadata["document_count"]
        average = self.metadata["average_length"] or 1
        normalizer = 0.0
        for term in terms:
            entry = self.connection.execute("SELECT df FROM terms WHERE term=?", (term,)).fetchone()
            # Missing query terms still count in normalization so a partial
            # match does not become a perfect lexical result.
            df = entry["df"] if entry else 0
            idf = math.log(1 + (count - df + 0.5) / (df + 0.5)) if count else 0
            normalizer += idf * 2.2
            if entry is None:
                continue
            for row in self.connection.execute(
                    "SELECT p.doc_id,p.tf,d.length FROM postings p JOIN documents d USING(doc_id) WHERE p.term=?", (term,)):
                tf = row["tf"]
                denominator = tf + 1.2 * (0.25 + 0.75 * row["length"] / average)
                scores[row["doc_id"]] += idf * tf * 2.2 / denominator
        return dict(scores), normalizer

    def _score(self, query: str | Mapping[str, Any], document: Mapping[str, Any],
               raw_lexical: float, normalizer: float) -> dict[str, Any]:
        doc_id = document["doc_id"]
        refs = self.get_refs(doc_id)
        evidence = score_evidence(query, document, refs)
        lexical = min(1.0, raw_lexical / normalizer) if normalizer else 0.0
        score = 0.6 * lexical + 0.4 * evidence["evidence_score"]
        return {"doc_id": doc_id, "lang": document.get("lang"), "score": score,
                "lexical_score": lexical, "bm25_score": raw_lexical,
                "evidence": evidence, "best_evidence_chunk_ref": evidence.get("best_evidence_chunk_ref"),
                "scorer_version": SCORER_VERSION}

    def score_document(self, query: str | Mapping[str, Any], doc_id: str) -> dict[str, Any]:
        document = self.get_document(doc_id)
        if document is None:
            raise KeyError(f"Document not in BEAR corpus index: {doc_id}")
        lexical, normalizer = self._lexical_scores(query)
        return self._score(query, document, lexical.get(document["doc_id"], 0.0), normalizer)

    def rank_documents(self, query: str | Mapping[str, Any], doc_ids: Iterable[str], *,
                       top_k: int = 100) -> list[dict[str, Any]]:
        """Rank exactly the supplied union, using the same corpus-level scorer."""
        self._top_k(top_k)
        identifiers = sorted({validate_doc_id(value) for value in doc_ids})
        lexical, normalizer = self._lexical_scores(query)
        def scored_rows():
            for identifier in identifiers:
                document = self.get_document(identifier)
                if document is None:
                    raise KeyError(f"Document not in BEAR corpus index: {identifier}")
                yield self._score(query, document, lexical.get(identifier, 0.0), normalizer)
        return heapq.nsmallest(top_k, scored_rows(), key=lambda row: (-row["score"], row["doc_id"]))

    def search(self, query: str | Mapping[str, Any], top_k: int = 100, *,
               languages: Sequence[str] | None = None) -> list[dict[str, Any]]:
        """Rank all lexical matches in the corpus, optionally within languages.

        There is no baseline pool and no hidden pre-evidence candidate budget.
        This lexical prototype cannot retrieve a document sharing no indexed
        query token; translated views must be explicitly supplied and anchored.
        """
        self._top_k(top_k)
        if languages is not None and (isinstance(languages, str) or
                any(not isinstance(value, str) or not value for value in languages)):
            raise SchemaInvalidError("languages must be a sequence of nonempty strings")
        allowed = set(languages) if languages is not None else None
        lexical, normalizer = self._lexical_scores(query)
        def scored_rows():
            for identifier in sorted(lexical):
                document = self.get_document(identifier)
                if allowed is None or document["lang"] in allowed:
                    yield self._score(query, document, lexical[identifier], normalizer)
        return heapq.nsmallest(top_k, scored_rows(), key=lambda row: (-row["score"], row["doc_id"]))
