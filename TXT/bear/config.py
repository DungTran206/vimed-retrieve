"""Schema riêng cho từng lệnh; chặn typo, nhãn trong inference và kiểu sai."""
from .contracts import SchemaInvalidError
from .io import load_config

PATH = (str, type(None))
COMMON = {"schema_version": int, "output_dir": str}
SCHEMAS = {
    "audit": {"snapshot": str, "inputs": dict, "archives": list, "outputs": dict,
              "runtime": dict},
    "reproduce": {"inputs": dict, "expected_fingerprints": dict},
    "pool": {"baseline": str, "deeper": str, "corpus": str, "membership": str,
             "scope": str, "cap": int, "sources": list, "b_family": PATH},
    "features": {"pool_manifest": str, "queries": str, "enriched_queries": PATH,
                 "expansion_queries": PATH, "corpus": str, "query_batch_size": int, "query_ids_path": PATH},
    "run": {"run_id": str, "pool_manifest": str, "feature_manifest": PATH,
            "mode": str, "lambda": (int, float), "feature_name": str, "weights": dict,
            "tau": (int, float), "temperature": (int, float), "endpoints": dict},
    "sample": {"queries": str, "sample_size": int, "dev_size": int, "seed": int,
               "previously_observed_ids": list, "reviewed_groups": PATH,
               "protocol": str},
    "annotation-export": {"queries": str, "corpus": str, "baseline": str,
                          "predictions": list, "split_manifest": str, "split": str,
                          "k": int, "mode": str, "seed": int, "frozen_candidate": PATH},
    "evaluate": {"qrels_path": str, "qrels_hash": str, "split_manifest": str,
                 "split_hash": str, "split": str, "primary_metric": str, "k": int,
                 "label_policy_version": str, "coverage": str,
                 "empty_gold_policy": str, "bootstrap_samples": int,
                 "bootstrap_seed": int, "frozen_candidate": PATH, "label_coverage_manifest": PATH},
    "export": {"corpus": str, "inputs": dict, "expected_fingerprints": dict},
}
REQUIRED = {
    "audit": ("inputs",), "reproduce": ("inputs",),
    "pool": ("baseline", "deeper", "corpus", "membership", "output_dir"),
    "features": ("pool_manifest", "queries", "corpus", "output_dir"),
    "run": ("run_id", "pool_manifest", "mode", "output_dir"),
    "sample": ("queries", "protocol", "output_dir"),
    "annotation-export": ("queries", "corpus", "baseline", "predictions", "split_manifest", "split", "k", "mode", "output_dir"),
    "evaluate": ("qrels_path", "qrels_hash", "split_manifest", "split_hash", "split", "primary_metric", "k", "label_policy_version", "coverage", "output_dir"),
    "export": ("corpus", "inputs", "output_dir"),
}


def fields(obj, schema, where, required=()):
    if not isinstance(obj, dict):
        raise SchemaInvalidError(f"{where}: cần JSON object")
    extra = set(obj) - set(schema)
    missing = set(required) - set(obj)
    if extra or missing:
        raise SchemaInvalidError(f"{where}: unknown={sorted(extra)}, missing={sorted(missing)}")
    for key, value in obj.items():
        types = schema[key] if isinstance(schema[key], tuple) else (schema[key],)
        if type(value) not in types:
            raise SchemaInvalidError(f"{where}.{key}: sai kiểu {type(value).__name__}")


def validate_config(cfg, command):
    fields(cfg, COMMON | SCHEMAS[command], command, ("schema_version", *REQUIRED[command]))
    for role, spec in cfg.get("inputs", {}).items():
        fields(spec, {"path": PATH, "expected_sha256": PATH}, f"inputs.{role}", ("path",))
        digest = spec.get("expected_sha256")
        if digest is not None and (len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)):
            raise SchemaInvalidError(f"inputs.{role}: SHA256 không hợp lệ")
    if command == "audit":
        fields(cfg.get("outputs", {}), {k: str for k in
               ("input_manifest", "baseline_manifest", "readiness_report")}, "outputs")
        fields(cfg.get("runtime", {}), {"seed": int, "dry_run": bool}, "runtime")
        if any(type(p) is not str for p in cfg.get("archives", [])):
            raise SchemaInvalidError("archives: cần list path")
    if command == "pool":
        source_ids = set()
        for source in cfg.get("sources", []):
            fields(source, {"source_id": str, "artifact_path": str, "artifact_sha256": str,
                           "source_kind": str, "complete": bool, "provenance_status": str,
                           "query_hash": str, "corpus_hash": str, "query_view": str,
                           "field": str, "requested_cutoff": int}, "source",
                   ("source_id", "artifact_path", "artifact_sha256", "source_kind", "complete", "provenance_status", "corpus_hash", "query_hash"))
            if source["source_id"] in source_ids or source["source_kind"] not in ("retriever", "reranker", "family"):
                raise SchemaInvalidError("Source ID trùng hoặc kind không hợp lệ")
            source_ids.add(source["source_id"])
    if command == "run":
        from .fusion import validate_weights
        if "weights" in cfg:
            validate_weights(cfg["weights"])
        if "endpoints" in cfg:
            fields(cfg["endpoints"], {"lexical": dict, "semantic": dict}, "endpoints", ("lexical", "semantic"))
            for weights in cfg["endpoints"].values():
                validate_weights(weights)
    return cfg


def command_config(path, command):
    return validate_config(load_config(path), command)
