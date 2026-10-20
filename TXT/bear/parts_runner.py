"""Independent corpus retrieval and fusion runners; no judgments or GPU dependencies."""
import os
import time
from collections import Counter

from .adapters import read_rank_source
from .artifacts import complete_run, file_identity, required_path, start_run
from .contracts import InputMissingError, SchemaInvalidError, validate_query_id
from .io import (assert_valid_output_path, atomic_write_json, canonical_json_dumps, read_json, read_jsonl,
                 resolve_repo_path)
from .retrieval import BearRetriever, PARTS_VERSION, validate_budget
from .evidence_fusion import BearFusion


def _input_paths(cfg, command):
    if command == "corpus-index":
        return {"corpus": cfg["corpus"]}
    paths = {"index": cfg["index"], "queries": cfg["queries"]}
    if command == "evidence-fuse":
        paths.update({"source:" + name: path for name, path in cfg["sources"].items()})
    return paths


def inspect_parts(cfg, command):
    """Check paths only; schema/content, snapshot linkage and relevance remain unverified."""
    if command not in ("corpus-index", "retrieve", "evidence-fuse"):
        raise SchemaInvalidError(f"Unknown BEAR part: {command}")
    paths = _input_paths(cfg, command)
    assert_valid_output_path(resolve_repo_path(cfg["output_dir"]),
                             [resolve_repo_path(p) for p in paths.values()])
    missing = []
    for role, path in paths.items():
        try:
            required_path(path)
        except InputMissingError:
            missing.append(role)
    return {"status": "blocked_input" if missing else "inputs_present_unverified",
            "command": command, "dry_run": True, "missing_roles": missing,
            "output_dir": cfg["output_dir"], "implementation_version": PARTS_VERSION,
            "quality_evaluated": False}


def _queries(path):
    queries = {}
    for row in read_jsonl(path):
        # This is an inference file, not val.jsonl. Do not accept answer-bearing rows.
        if set(row) & {"gold", "not_gold", "gold_unseen", "G", "judgments", "qrels"}:
            raise SchemaInvalidError("Inference queries must not contain relevance labels")
        key = next((key for key in ("id", "query_id", "qid") if key in row), None)
        qid = validate_query_id(row.get(key))
        if qid in queries:
            raise SchemaInvalidError(f"Duplicate query {qid}")
        text = row.get("query", row.get("text"))
        if not isinstance(text, str) or not text.strip():
            raise SchemaInvalidError(f"Query {qid} needs nonempty query text")
        queries[qid] = {"id": qid, "query": text,
                       **{key: row[key] for key in ("entities", "relations", "lang") if key in row}}
    if not queries:
        raise SchemaInvalidError("Query file is empty")
    return queries


def _sources(cfg, query_ids):
    sources = {}
    for name, path in cfg["sources"].items():
        for raw in read_jsonl(required_path(path)):
            keys = [key for key in ("candidates", "docs", "ranked_docs") if key in raw]
            if len(keys) != 1 or not isinstance(raw[keys[0]], list):
                raise SchemaInvalidError(f"Source {name} needs one explicit ranking-list field in every row")
        rows = {row.query_id: [{"doc_id": item.doc_id, "score": item.score}
                              for item in row.items] for row in read_rank_source(required_path(path))}
        if set(rows) != set(query_ids):
            raise SchemaInvalidError(f"Source {name} must cover exactly the query universe; "
                                     f"missing={sorted(set(query_ids) - set(rows))}, "
                                     f"extra={sorted(set(rows) - set(query_ids))}")
        sources[name] = rows
    return sources


def run_parts(cfg, command):
    """Run one component into an immutable directory compatible with existing manifests."""
    preflight = inspect_parts(cfg, command)
    if preflight["missing_roles"]:
        raise InputMissingError("Missing part inputs", {"missing_roles": preflight["missing_roles"]})
    inputs = [file_identity(path) for path in _input_paths(cfg, command).values()]
    previous_manifest = resolve_repo_path(cfg["output_dir"]) / "manifest.json"
    if command == "corpus-index" and (previous_manifest.parent / "index.sqlite").exists() \
            and not previous_manifest.is_file():
        raise FileExistsError("Existing index is not bound to a BEAR run manifest; choose a fresh output directory")
    resume_partial = previous_manifest.is_file() and read_json(previous_manifest).get("status") == "partial"
    root, manifest, reused = start_run(cfg["output_dir"], cfg | {"part": command}, inputs)
    if reused:
        return manifest
    from .corpus_index import CorpusIndex, build_index
    started = time.perf_counter()
    if command == "corpus-index":
        # A matching partial manifest binds this run's generated index. Rebuild it
        # atomically after interruption; completed runs return above and unrelated
        # files without a prior partial manifest are never overwritten.
        summary = build_index(required_path(cfg["corpus"]), root / "index.sqlite",
                              chunk_chars=cfg.get("chunk_chars", 1200), overwrite=resume_partial)
        metadata_path = atomic_write_json(root / "index_metadata.json", summary)
        return complete_run(root, manifest, [root / "index.sqlite", metadata_path],
                            stage="corpus_index", implementation_version=PARTS_VERSION,
                            elapsed_seconds=time.perf_counter() - started, quality_evaluated=False)
    validate_budget(cfg["top_k"], cfg.get("languages"))
    queries = _queries(required_path(cfg["queries"]))
    sources = _sources(cfg, queries) if command == "evidence-fuse" else None
    counts, statuses, elapsed = {}, Counter(), {}
    with CorpusIndex(required_path(cfg["index"])) as index:
        part = BearRetriever(index) if command == "retrieve" else BearFusion(index)
        candidates_path = assert_valid_output_path(root / "candidates.jsonl")
        evidence_path = assert_valid_output_path(root / "evidence.jsonl")
        candidate_partial = candidates_path.with_suffix(".jsonl.partial")
        evidence_partial = evidence_path.with_suffix(".jsonl.partial")
        # Stream both artifacts by query; do not retain all corpus evidence in RAM.
        with candidate_partial.open("w", encoding="utf-8", newline="\n") as candidate_out, \
                evidence_partial.open("w", encoding="utf-8", newline="\n") as evidence_out:
            for qid, query in sorted(queries.items()):
                tick = time.perf_counter()
                if sources is None:
                    hits = part.retrieve(query, top_k=cfg["top_k"], languages=cfg.get("languages"))
                else:
                    hits = part.fuse(query, {name: rows[qid] for name, rows in sources.items()},
                                     top_k=cfg["top_k"], languages=cfg.get("languages"))
                counts[qid] = len(hits)
                elapsed[qid] = time.perf_counter() - tick
                for rank, hit in enumerate(hits, 1):
                    statuses[hit.get("evidence", {}).get("structured_status", "unavailable")] += 1
                    evidence_out.write(canonical_json_dumps({"id": qid, "rank": rank, **hit}) + "\n")
                candidate_out.write(canonical_json_dumps({"id": qid, "candidates": [
                    {"doc_id": hit["doc_id"], "score": hit["score"]} for hit in hits]}) + "\n")
            for output in (candidate_out, evidence_out):
                output.flush()
                os.fsync(output.fileno())
        os.replace(candidate_partial, candidates_path)
        os.replace(evidence_partial, evidence_path)
        metadata = dict(index.metadata)
    diagnostics = {"stage": part.stage, "candidate_scope": part.candidate_scope,
                   "implementation_version": PARTS_VERSION, "query_count": len(queries),
                   "top_k": cfg["top_k"], "languages": cfg.get("languages"),
                   "counts": counts, "per_query_seconds": elapsed,
                   "structured_status_counts": dict(statuses), "index_metadata": metadata,
                   "quality_evaluated": False,
                   "chunk_refs_are_diagnostics_not_submission": True}
    diagnostics_path = atomic_write_json(root / "diagnostics.json", diagnostics)
    return complete_run(root, manifest, [candidates_path, evidence_path, diagnostics_path],
                        stage=part.stage, candidate_scope=part.candidate_scope,
                        implementation_version=PARTS_VERSION,
                        elapsed_seconds=time.perf_counter() - started, query_count=len(queries),
                        quality_evaluated=False)
