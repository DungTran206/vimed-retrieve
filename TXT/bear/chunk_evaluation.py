"""Reviewed local-passage recall diagnostic, kept distinct from official Chunk F2."""
import hashlib
import html
import unicodedata
from .application_audit import indexed
from .artifacts import required_path, verify_manifest, verify_identity, corpus_connection, read_corpus_batch
from .contracts import SchemaInvalidError, HashMismatchError, validate_doc_id, validate_query_id
from .evaluation import passage_match_diagnostic
from .evaluate_runner import claim_exposure
from .integrity import validate_records
from .io import (read_json, read_jsonl, resolve_repo_path, sha256_file,
                 atomic_write_json, assert_valid_output_path)


def tokens(text):
    return unicodedata.normalize("NFKC", html.unescape(text)).lower().split()


def evaluate_chunks(cfg, run_dir, preflight_only=False):
    root = resolve_repo_path(run_dir)
    manifest = verify_manifest(root / "manifest.json")
    records_path = required_path(root / "records.json")
    corpus_hash = sha256_file(required_path(cfg["corpus"]))
    if manifest.get("candidate_kind") != "chunk" or manifest["corpus_hash"] != corpus_hash:
        raise SchemaInvalidError("Chunk evaluation needs selected chunk run from the same corpus")
    if cfg["primary_metric"] != "local_passage_recall" or cfg["coverage"] != "complete_local_passages":
        raise SchemaInvalidError("Only reviewed local passage recall diagnostic is supported")
    for field in ("passages", "split_manifest"):
        expected = cfg["passages_hash" if field == "passages" else "split_hash"]
        if sha256_file(required_path(cfg[field])) != expected:
            raise HashMismatchError(f"Chunk evaluation hash mismatch: {field}")
    if cfg["split"] not in ("dev", "holdout"):
        raise SchemaInvalidError("Chunk evaluation split must be dev/holdout")
    split = read_json(cfg["split_manifest"])
    qids = split[cfg["split"]]
    if not qids or len(qids) != len(set(qids)):
        raise SchemaInvalidError("Invalid chunk evaluation query universe")
    for q in qids:
        validate_query_id(q)
    if not set(qids) <= {int(q) for q in split.get("query_groups", {})}:
        raise SchemaInvalidError("Chunk evaluation group mapping missing planned queries")
    records = read_json(records_path)
    control_path = required_path(root / "control_records.json")
    control = read_json(control_path)
    candidates = indexed(records, "id")
    controls = indexed(control, "id")
    from .io import read_jsonl
    validate_records(records, list(read_jsonl(root / "chunk_refs.jsonl")), cfg["corpus"], query_ids=candidates)
    validate_records(control, list(read_jsonl(root / "control_chunk_refs.jsonl")), cfg["corpus"], query_ids=controls)
    if any(candidates.get(q, {}).get("relevant_docs") != controls.get(q, {}).get("relevant_docs") for q in set(candidates) | set(controls)):
        raise SchemaInvalidError("Chunk comparison changes document ranking")
    references, seen = {}, set()
    raw = list(read_jsonl(cfg["passages"]))
    with corpus_connection(cfg["corpus"]) as conn:
        bodies = read_corpus_batch(conn, {validate_doc_id(r["doc_id"]) for r in raw})
    for row in raw:
        q, doc = validate_query_id(row["query_id"]), validate_doc_id(row["doc_id"])
        if row.get("adjudication") != "reviewed" or not row.get("annotator") or not row.get("reference_source") or row.get("label_policy_version") != cfg["label_policy_version"]:
            raise SchemaInvalidError("Passages must have human-reviewed provenance and policy")
        body = bodies.get(doc, {}).get("body")
        start, end = row["start"], row["end"]
        if (body is None or type(start) is not int or type(end) is not int or not 0 <= start < end <= len(body)
                or hashlib.sha256(body.encode()).hexdigest() != row["body_sha256"]):
            raise SchemaInvalidError("Gold passage body hash/offset mismatch")
        key = q, doc, start, end
        if key in seen:
            raise SchemaInvalidError("Duplicate local passage")
        seen.add(key)
        gold = tokens(body[start:end])
        if not gold:
            raise SchemaInvalidError("Empty local passage tokens")
        references.setdefault(q, []).append((doc, gold))
    output = assert_valid_output_path(resolve_repo_path(cfg["output_dir"]) / "evaluation.json",
                                     [records_path, control_path, cfg["passages"], cfg["split_manifest"]])
    exposure, frozen = None, None
    if cfg["split"] == "holdout":
        frozen_path = required_path(cfg.get("frozen_candidate"))
        frozen = read_json(frozen_path)
        if (frozen.get("candidate_kind") != "chunk" or frozen["candidate_sha256"] != sha256_file(root / "candidates.jsonl")
                or frozen["split_hash"] != cfg["split_hash"]):
            raise HashMismatchError("Chunk candidate/split not frozen")
        for key, value in frozen.get("evaluation_contract", {}).items():
            if cfg.get(key) != value:
                raise SchemaInvalidError(f"Chunk evaluation differs from frozen contract: {key}")
        for identity in frozen["controls"] + frozen["code"] + frozen["candidate_artifacts"] + [
                frozen["candidate_manifest"], frozen["protocol"], frozen["selection"]]:
            verify_identity(identity)
        exposure = frozen_path.parent / "holdout_exposure.json"
        if exposure.exists():
            raise SchemaInvalidError("Holdout already exposed")
    missing = [q for q in qids if q not in references or q not in candidates or q not in controls]
    if preflight_only:
        return {"status": "inconclusive" if missing else "ready", "missing_query_ids": missing,
                "primary_metric": "local_passage_recall", "exposure_consumed": False}
    rows = []
    for q in qids:
        if q in missing:
            rows.append({"query_id": q, "value": None, "reason": "missing_local_passages_or_predictions"})
            continue
        def score(record):
            predictions = [(str(c["doc_id"]), tokens(c["chunk_text"])) for c in record["relevant_chunks"]]
            return sum(any(passage_match_diagnostic(pred, gold, pd, gd) for pd, pred in predictions)
                       for gd, gold in references[q]) / len(references[q])
        value, base = score(candidates[q]), score(controls[q])
        rows.append({"query_id": q, "value": value, "control_value": base, "delta": value - base})
    report = {"schema_version": 2, "status": "inconclusive" if missing else "available", "split": cfg["split"],
              "primary_metric": "local_passage_recall", "evaluation_source": "local_passage_diagnostic_v1",
              "coverage": cfg["coverage"], "label_policy_version": cfg["label_policy_version"],
              "tokenizer": "nfkc_html_lower_whitespace_v1", "official_equivalent": False,
              "metric": sum(r["value"] for r in rows) / len(rows) if not missing else None,
              "planned_queries": len(qids), "effective_queries": len(qids) - len(missing),
              "missing_query_ids": missing, "per_query": rows, "records_sha256": sha256_file(records_path),
              "candidate_sha256": sha256_file(root / "candidates.jsonl"), "split_hash": cfg["split_hash"],
              "passages_hash": cfg["passages_hash"], "confirmatory_eligible": split.get("confirmatory_eligible", False)}
    if not missing:
        from .paired import paired_group_bootstrap
        report["paired"] = paired_group_bootstrap({r["query_id"]: r["delta"] for r in rows},
            {int(q): group for q, group in split["query_groups"].items()},
            cfg.get("bootstrap_samples", 10000), cfg.get("bootstrap_seed", 42))
    if exposure is not None:
        if missing:
            raise SchemaInvalidError("Incomplete chunk holdout coverage; exposure not consumed")
        claim_exposure(exposure, {"candidate_sha256": frozen["candidate_sha256"], "evaluation_config": cfg, "status": "exposed"})
    atomic_write_json(output, report, input_paths=[records_path, cfg["passages"], cfg["split_manifest"]])
    return report
