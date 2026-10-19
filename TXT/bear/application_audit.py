"""N1 application accounting by replay, without relevance labels or source mutation."""
from collections import Counter
from .artifacts import file_identity, verify_manifest, start_run, complete_run, required_path
from .contracts import SchemaInvalidError
from .fusion import rank_query
from .io import read_jsonl, write_jsonl, atomic_write_json, atomic_write_text, canonical_sha256, resolve_repo_path
from .reproduce import load_ranks, load_scores


def indexed(rows, key):
    result = {}
    for row in rows:
        value = row[key]
        if value in result:
            raise SchemaInvalidError(f"Duplicate {key}: {value}")
        result[value] = row
    return result


def load_features(path, pool_manifest):
    fm = verify_manifest(path)
    if resolve_repo_path(fm["pool_manifest"]) != resolve_repo_path(pool_manifest):
        raise SchemaInvalidError("Features reference a different pool")
    rows = {}
    for part in fm["pair_paths"]:
        for row in read_jsonl(part):
            qid, doc = row["query_id"], row["doc_id"]
            if doc in rows.setdefault(qid, {}):
                raise SchemaInvalidError("Duplicate feature pair")
            rows[qid][doc] = row
    routes = indexed(read_jsonl(fm["routes_path"]), "query_id")
    return fm, rows, routes


def chunk_signatures(path):
    result = {}
    if path:
        seen = set()
        for row in read_jsonl(required_path(path)):
            key = row["query_id"], row["output_position"]
            if key in seen:
                raise SchemaInvalidError("Duplicate chunk output position")
            seen.add(key)
            result.setdefault(key[0], []).append((key[1], row["doc_id"], row["start"], row["end"], row["text_sha256"]))
        result = {q: sorted(values) for q, values in result.items()}
    return result


def audit_application(cfg):
    run_path = required_path(resolve_repo_path(cfg["run_dir"]) / "manifest.json")
    run = verify_manifest(run_path)
    config = run["config"]
    pm = verify_manifest(config["pool_manifest"])
    pools = indexed(read_jsonl(pm["pool_path"]), "query_id")
    candidates = load_ranks(run_path.parent / "candidates.jsonl")
    details = indexed(read_jsonl(run_path.parent / "ranking_details.jsonl"), "query_id")
    if set(candidates) != set(pools) or set(details) != set(pools):
        raise SchemaInvalidError("Output/details query universe differs from pool")
    inputs = [file_identity(run_path), file_identity(config["pool_manifest"])]
    features, routes = {}, {}
    if config.get("feature_manifest"):
        _, features, routes = load_features(config["feature_manifest"], config["pool_manifest"])
        inputs.append(file_identity(config["feature_manifest"]))
    baseline = load_ranks(cfg["baseline"]) if cfg.get("baseline") else {q: p["baseline"] for q, p in pools.items()}
    for key in ("baseline", "candidate_chunk_refs", "baseline_chunk_refs"):
        if cfg.get(key):
            inputs.append(file_identity(cfg[key]))
    score_sources = {}
    for name, path in cfg.get("calibration_sources", {}).items():
        inputs.append(file_identity(path))
        score_sources[name] = load_scores(path)
    before_chunks = chunk_signatures(cfg.get("baseline_chunk_refs"))
    after_chunks = chunk_signatures(cfg.get("candidate_chunk_refs"))
    root, manifest, reused = start_run(cfg["output_dir"], cfg, inputs)
    if reused:
        return manifest
    ledger, totals = [], Counter()
    mode, lam = config["mode"], config.get("lambda", 0)
    for qid, pool in sorted(pools.items()):
        if baseline.get(qid) != pool["baseline"]:
            raise SchemaInvalidError("Audit baseline differs from frozen reference")
        f = features.get(qid, {})
        replayed, reason = rank_query(pool, f, config, routes.get(qid))
        if replayed != candidates[qid] or reason.get("fallback_reason") != details[qid].get("fallback_reason"):
            raise SchemaInvalidError(f"Recorded inference does not match replay: qid {qid}")
        selectable = [r for r in pool["reference"] if r["selectable"]]
        feature_name = config.get("feature_name", "body_coverage")
        eligible_pairs = sum(f.get(r["doc_id"], {}).get(feature_name) is not None and
                             f.get(r["doc_id"], {}).get("mapping_coverage") == 1 for r in selectable)
        bypass = mode == "baseline" or lam == 0
        fallback = reason.get("fallback_reason")
        applied = not bypass and fallback is None and bool(selectable)
        old, new = baseline[qid], candidates[qid]
        extras = [r["doc_id"] for r in selectable if r["baseline_rank"] is None]
        added, removed = sorted(set(new) - set(old)), sorted(set(old) - set(new))
        row = {"query_id": qid, "output_present": True, "feature_present": bool(f),
               "selectable_pairs": len(selectable), "feature_pairs": sum(r["doc_id"] in f for r in selectable),
               "eligible_evidence_pairs": eligible_pairs, "fully_eligible":
                   bool(selectable) and eligible_pairs == len(selectable) if mode == "fixed_evidence" else applied,
               "mode": mode, "lambda": lam, "bypass": bypass, "applied": applied,
               "fallback_reason": fallback, "route_eligible": routes.get(qid, {}).get("route_eligible"),
               "changed_order": old != new, "changed_top40": old[:40] != new[:40],
               "changed_docset": set(old) != set(new), "added": added, "removed": removed,
               "extra_vi_count": len(extras), "set_sha256": canonical_sha256(sorted(new)),
               "order_sha256": canonical_sha256(new), "changed_chunks": None,
               "score_coverage_added": {name: {"available": sum(d in source.get(qid, {}) for d in added),
                    "required": len(added)} for name, source in score_sources.items()} if score_sources else None}
        if cfg.get("baseline_chunk_refs") and cfg.get("candidate_chunk_refs"):
            row["changed_chunks"] = before_chunks.get(qid, []) != after_chunks.get(qid, [])
        for key in ("feature_present", "fully_eligible", "applied", "bypass", "changed_order", "changed_docset", "changed_top40", "changed_chunks"):
            if row[key]:
                totals[key] += 1
        if fallback:
            totals["fallback/" + fallback] += 1
        ledger.append(row)
    summary = {"schema_version": 2, "status": "available", "expected_queries": len(pools),
               "output_queries": len(candidates), "feature_queries": sum(bool(features.get(q)) for q in pools),
               "counts": dict(totals), "selectable_pairs": sum(r["selectable_pairs"] for r in ledger),
               "eligible_evidence_pairs": sum(r["eligible_evidence_pairs"] for r in ledger),
               "feature_scope": "full_pool" if all(features.get(q) for q in pools) else "partial_or_bypass",
               "label_usage": "none", "quality_decision": "inconclusive",
               "count_policy": "flags may overlap; denominator expected_queries; evidence eligibility is not route eligibility"}
    paths = [write_jsonl(root / "per_query.jsonl", ledger), atomic_write_json(root / "application.json", summary),
             atomic_write_text(root / "report.md", "# N1 application audit\n\n" +
                 f"Queries: {len(pools)}; features: {summary['feature_queries']}; applied: {totals['applied']}.\n\n" +
                 "Counts measure execution, not relevance gain. See per_query.jsonl for overlapping flags and fallback reasons.\n")]
    return complete_run(root, manifest, paths, audit_status="available", summary=summary)
