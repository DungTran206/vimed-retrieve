"""Evaluation process riêng: qrels reviewed, planned universe, holdout một lần."""
from .artifacts import file_identity, required_path, verify_identity
from .contracts import HashMismatchError, SchemaInvalidError
from .evaluation import compute_doc_f2, compute_replacement_delta
from .io import atomic_write_json, read_json, read_jsonl, resolve_repo_path, sha256_file
from .reproduce import load_ranks


def reviewed_qrels(path, policy):
    qrels = {}
    for row in read_jsonl(required_path(path)):
        if row.get("adjudication") != "reviewed" or not row.get("annotator"):
            raise SchemaInvalidError("Primary labels yêu cầu human reviewed/adjudicated")
        if row.get("label_policy_version") != policy or type(row.get("grade")) is not int or row["grade"] not in (0, 1, 2):
            raise SchemaInvalidError("Qrel grade/policy không hợp lệ")
        qid, doc = row["query_id"], row["doc_id"]
        from .contracts import validate_query_id, validate_doc_id
        qid, doc = validate_query_id(qid), validate_doc_id(doc)
        if doc in qrels.setdefault(qid, {}):
            raise SchemaInvalidError("Duplicate qrel")
        qrels[qid][doc] = row["grade"]
    return qrels


def evaluate(cfg, run_dir, baseline_dir=None):
    candidate_path = required_path(resolve_repo_path(run_dir) / "candidates.jsonl")
    candidate = load_ranks(candidate_path)
    if sha256_file(required_path(cfg["qrels_path"])) != cfg["qrels_hash"]:
        raise HashMismatchError("Qrels hash mismatch")
    if sha256_file(required_path(cfg["split_manifest"])) != cfg["split_hash"]:
        raise HashMismatchError("Split hash mismatch")
    if cfg["split"] not in ("dev", "holdout"):
        raise SchemaInvalidError("Split phải dev/holdout")
    split = read_json(cfg["split_manifest"])
    qids = split[cfg["split"]]
    baseline_path = required_path(resolve_repo_path(baseline_dir) / "candidates.jsonl") if baseline_dir else None
    baseline = load_ranks(baseline_path) if baseline_path else None
    if cfg["split"] == "holdout":
        frozen_path = required_path(cfg.get("frozen_candidate"))
        frozen = read_json(frozen_path)
        if frozen["candidate_sha256"] != sha256_file(candidate_path) or frozen["split_hash"] != cfg["split_hash"]:
            raise HashMismatchError("Holdout candidate/split chưa freeze")
        for item in frozen["controls"] + frozen["code"] + [frozen["protocol"], frozen["selection"]]:
            verify_identity(item)
        if baseline_path and str(baseline_path) not in frozen["control_paths"]:
            raise SchemaInvalidError("Control chưa preregister")
        exposure = frozen_path.parent / "holdout_exposure.json"
        if exposure.exists():
            raise SchemaInvalidError("Holdout đã mở; không evaluate/chọn lại")
        atomic_write_json(exposure, {"candidate_sha256": frozen["candidate_sha256"],
                                    "evaluation_config": cfg, "status": "exposed"})
    metric, k = cfg["primary_metric"], cfg["k"]
    if metric not in ("precision_at_k", "replacement_delta_p", "macro_doc_f2") or type(k) is not int or k < 1:
        raise SchemaInvalidError("Metric/k không hợp lệ")
    needed = {"precision_at_k": ("complete_topk", "complete_universe"),
              "replacement_delta_p": ("complete_differences", "complete_universe"),
              "macro_doc_f2": ("complete_universe",)}
    if cfg["coverage"] not in needed[metric]:
        raise SchemaInvalidError("Metric không phù hợp coverage contract")
    if cfg.get("empty_gold_policy", "excluded") not in ("excluded", "zero"):
        raise SchemaInvalidError("empty_gold_policy không hợp lệ")
    if metric == "macro_doc_f2":
        coverage_manifest = read_json(required_path(cfg.get("label_coverage_manifest")))
        if (coverage_manifest.get("coverage") != "complete_universe" or
            coverage_manifest.get("qrels_hash") != cfg["qrels_hash"] or
            not set(qids) <= set(coverage_manifest.get("complete_query_ids", []))):
            raise SchemaInvalidError("Doc F2 cần complete-universe manifest đúng qrels/query universe")
    qrels = reviewed_qrels(cfg["qrels_path"], cfg["label_policy_version"])
    rows, missing = [], []
    for qid in qids:
        docs = candidate.get(qid, [])[:k]
        labels = qrels.get(qid, {})
        row = {"query_id": qid, "value": None}
        if len(docs) != k:
            row["reason"] = "ranking_short_or_missing"
        elif metric == "replacement_delta_p":
            if baseline is None or len(baseline.get(qid, [])[:k]) != k:
                raise SchemaInvalidError("Replacement cần baseline cùng k")
            result = compute_replacement_delta(docs, baseline[qid], labels, relevance_threshold=2, k=k)
            row.update(result)
            row["value"] = result["delta_p"]
        elif metric == "macro_doc_f2":
            # complete_universe là assertion của manifest nhãn; explicit zero vẫn phải có cho predicted.
            if any(d not in labels for d in docs):
                row["reason"] = "unjudged_predictions"
            else:
                gold = sum(g >= 2 for g in labels.values())
                if not gold and cfg.get("empty_gold_policy", "excluded") == "excluded":
                    row.update(excluded_empty_gold=True)
                else:
                    row["value"] = compute_doc_f2(sum(labels[d] >= 2 for d in docs), k, gold)
        elif all(d in labels for d in docs):
            row["value"] = sum(labels[d] >= 2 for d in docs) / k
        else:
            row["reason"] = "unjudged_topk"
        if row["value"] is None and not row.get("excluded_empty_gold"):
            missing.append(qid)
        rows.append(row)
    values = [r["value"] for r in rows if r["value"] is not None]
    report = {"schema_version": 1, "status": "available" if not missing and values else "inconclusive",
              "evaluation_source": "local_answer_v1", "split": cfg["split"], "primary_metric": metric,
              "planned_queries": len(qids), "effective_queries": len(values), "missing_query_ids": missing,
              "metric": sum(values) / len(values) if values and not missing else None,
              "candidate_sha256": sha256_file(candidate_path), "per_query": rows,
              "confirmatory_eligible": split.get("confirmatory_eligible", False)}
    if baseline is not None and metric == "replacement_delta_p" and report["status"] == "available":
        from .paired import paired_group_bootstrap
        report["paired"] = paired_group_bootstrap({r["query_id"]: r["value"] for r in rows},
                    {int(q): g for q, g in split["query_groups"].items()},
                    cfg.get("bootstrap_samples", 10000), cfg.get("bootstrap_seed", 42))
    atomic_write_json(resolve_repo_path(cfg["output_dir"]) / "evaluation.json", report,
                      input_paths=[candidate_path, cfg["qrels_path"], cfg["split_manifest"]])
    return report
