"""N4 dev-only oracle/evidence diagnostics; never unlock adaptive from silver/aggregate scores."""
import random
from statistics import mean, median
from .artifacts import file_identity, verify_manifest, start_run, complete_run
from .application_audit import indexed
from .contracts import SchemaInvalidError, validate_finite_number
from .io import read_json, read_jsonl, atomic_write_json, atomic_write_text


def routing_statistics(lexical, semantic, fixed, evidence, lengths, bins):
    qids = sorted(lexical)
    if not qids or set(semantic) != set(qids) or set(fixed) != set(qids):
        raise SchemaInvalidError("Routing utilities must cover the same non-empty query universe")
    for values in (lexical, semantic, fixed):
        for value in values.values():
            validate_finite_number(value, "utility")
    valid = [q for q in qids if evidence.get(q) is not None]
    for q in valid:
        validate_finite_number(evidence[q], "E", min_val=0, max_val=1)
    oracle = mean(max(lexical[q], semantic[q]) - fixed[q] for q in qids)
    result = {"queries": len(qids), "evidence_queries": len(valid), "oracle_headroom": oracle,
              "endpoint_delta": {str(q): lexical[q] - semantic[q] for q in qids},
              "best_constant_utility": max(mean(lexical.values()), mean(semantic.values()), mean(fixed.values())),
              "evidence_bins": [], "shuffled_controls": [], "query_only_utility": None}
    if not valid:
        return result
    ordered = sorted(valid, key=lambda q: (evidence[q], q))
    # Never split tied E values into apparently discriminative bins.
    for value in sorted({evidence[q] for q in valid}):
        members = [q for q in ordered if evidence[q] == value]
        result["evidence_bins"].append({"E": value, "queries": len(members),
            "mean_delta": mean(lexical[q] - semantic[q] for q in members)})
    threshold = median(evidence[q] for q in valid)
    result["threshold_dev_median"] = threshold
    result["evidence_rule_utility"] = mean(lexical[q] if evidence[q] >= threshold else semantic[q] for q in valid)
    if all(q in lengths for q in valid):
        length_threshold = median(lengths[q] for q in valid)
        result["query_only_utility"] = mean(lexical[q] if lengths[q] >= length_threshold else semantic[q] for q in valid)
    for seed in (11, 23, 37, 53, 71):
        rng, shuffled, groups = random.Random(seed), dict(evidence), {}
        for q in valid:
            if q not in bins:
                raise SchemaInvalidError("Shuffle bin missing query")
            groups.setdefault(bins[q], []).append(q)
        moved = 0
        for members in groups.values():
            members = sorted(members)
            values = [evidence[q] for q in members]
            rng.shuffle(values)
            moved += sum(v != evidence[q] for q, v in zip(members, values))
            shuffled.update(zip(members, values))
        result["shuffled_controls"].append({"seed": seed, "changed_evidence_queries": moved,
            "utility": mean(lexical[q] if shuffled[q] >= threshold else semantic[q] for q in valid)})
    return result


def run_routing_diagnostics(cfg):
    paths = [cfg[k] for k in ("lexical_report", "semantic_report", "fixed_report", "feature_manifest", "query_metadata")]
    inputs = [file_identity(p) for p in paths]
    reports = [read_json(i["path"]) for i in inputs[:3]]
    for report in reports:
        if report.get("split") != "dev" or report.get("status") != "available":
            raise SchemaInvalidError("Routing uses complete dev evaluations only")
    for key in ("primary_metric", "split_hash", "qrels_hash", "baseline_sha256"):
        values = [r.get(key) for r in reports]
        if key != "baseline_sha256" and any(v is None for v in values):
            raise SchemaInvalidError(f"Routing report missing provenance: {key}")
        if len(set(values)) != 1:
            raise SchemaInvalidError(f"Routing controls differ in {key}")
    fm = verify_manifest(cfg["feature_manifest"])
    routes = indexed(read_jsonl(fm["routes_path"]), "query_id")
    metadata = indexed(read_jsonl(inputs[4]["path"]), "query_id")
    utilities = []
    for report in reports:
        rows = indexed(report["per_query"], "query_id")
        if any(r.get("value") is None for r in rows.values()):
            raise SchemaInvalidError("Missing endpoint utility")
        utilities.append({q: r["value"] for q, r in rows.items()})
    evidence = {q: r.get("E") if r.get("route_eligible") else None for q, r in routes.items()}
    lengths = {q: r["query_length"] for q, r in metadata.items()}
    bins = {q: (r["language_view"], r["length_bin"]) for q, r in metadata.items()}
    stats = routing_statistics(*utilities, evidence, lengths, bins)
    stats.update(status="diagnostic_only", adaptive_ready=False,
                 decision="defer" if stats["oracle_headroom"] < cfg["minimum_headroom"] else "review_controls",
                 prerequisite="Endpoint-rule/shuffle diagnostics are not matched-budget trained A1 evidence; production guard remains closed")
    root, manifest, reused = start_run(cfg["output_dir"], cfg, inputs)
    if reused:
        return manifest
    paths = [atomic_write_json(root / "routing.json", stats),
             atomic_write_text(root / "report.md", "# N4 routing diagnostics\n\n" +
                f"Oracle headroom: {stats['oracle_headroom']}; decision: {stats['decision']}.\n\n" +
                "Dev-only diagnostics; adaptive remains gated, not a confirmatory gain.\n")]
    return complete_run(root, manifest, paths, adaptive_ready=False, routing_decision=stats["decision"])
