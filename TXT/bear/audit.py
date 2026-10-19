"""Readiness và macro archive; feedback chỉ nằm trong báo cáo quan sát."""
from datetime import datetime, timezone
from pathlib import Path
import json
import zipfile
from .artifacts import corpus_connection, corpus_schema, file_identity
from .config import command_config
from .contracts import SchemaInvalidError
from .io import atomic_write_json, atomic_write_text, resolve_repo_path, read_json


def inspect_archive(path):
    info = file_identity(path)
    with zipfile.ZipFile(path) as archive:
        info["members"] = [{"name": x.filename, "bytes": x.file_size,
                            "compressed_bytes": x.compress_size} for x in archive.infolist()]
        if "evaluation.json" not in archive.namelist():
            return info
        evaluation = json.loads(archive.read("evaluation.json"))
        info["evaluation"] = evaluation
        info["provenance_status"] = "runtime_observed_unlinked"
        if "details.jsonl" in archive.namelist():
            seen = set()
            totals = {level: [] for level in ("document", "chunk")}
            with archive.open("details.jsonl") as source:
                for line in source:
                    row = json.loads(line)
                    qid = int(row.get("id", row.get("query_id")))
                    if qid in seen:
                        raise SchemaInvalidError(f"Archive duplicate qid {qid}")
                    seen.add(qid)
                    for level in totals:
                        record = row[level]
                        if record["gold"] > 0:
                            totals[level].append(record["f2"])
            checks = {}
            for level, values in totals.items():
                actual = sum(values) / len(values) if values else None
                reported = evaluation.get(level, {}).get("f2")
                checks[level] = {"effective_queries": len(values), "macro_f2": actual,
                                 "reported": reported, "matches": reported is not None and
                                 actual is not None and abs(actual - reported) < 1e-10}
            info["macro_checks"] = checks
            info["observed_query_ids"] = sorted(seen)
    return info


def run_audit(config_path):
    cfg = command_config(config_path, "audit")
    inputs, archives = {}, {}
    for role, spec in cfg.get("inputs", {}).items():
        path = resolve_repo_path(spec["path"])
        item = {"declared_path": spec["path"], "status": "missing", "sha256": None}
        if path and path.is_file():
            try:
                item.update(file_identity(path))
                expected = spec.get("expected_sha256")
                item["status"] = "hash_mismatch" if expected and expected != item["sha256"] else "verified"
                if path.suffix in (".sqlite", ".db"):
                    with corpus_connection(path) as conn:
                        _, item["schema"] = corpus_schema(conn)
                elif path.suffix == ".jsonl":
                    from .io import read_jsonl
                    count, preview = 0, None
                    for row in read_jsonl(path):
                        count += 1
                        preview = preview or sorted(row)
                    item.update(rows=count, schema_keys=preview)
            except (SchemaInvalidError, OSError) as error:
                item.update(status="invalid", reason=str(error))
        inputs[role] = item
    for value in cfg.get("archives", []):
        path = resolve_repo_path(value)
        archives[value] = inspect_archive(path) if path.is_file() else {"status": "missing"}
    missing = [r for r, i in inputs.items() if i["status"] == "missing"]
    invalid = [r for r, i in inputs.items() if i["status"] not in ("verified", "missing")]
    status = "blocked_input" if missing or invalid else "ready"
    manifest = {"schema_version": 1, "snapshot": cfg.get("snapshot"),
                "audit_timestamp": datetime.now(timezone.utc).isoformat(),
                "readiness_status": status, "missing_count": len(missing),
                "missing_roles": missing, "invalid_roles": invalid,
                "inputs": inputs, "archives": archives}
    outputs = cfg.get("outputs", {})
    input_paths = [i["declared_path"] for i in inputs.values() if i["declared_path"]]
    baseline = {"schema_version": 1, "baseline_run": "w045_TF", "status": "not_reproduced",
                "reported_metrics": {"doc_f2": .3605, "chunk_f2": .3279, "final": .3442},
                "expected_fingerprints": {"doc": "c1e068422e5f", "chunk": "fd07f9fc029a"},
                "observed_fingerprints": None, "observed_metrics": None,
                "observed_archive_run": archives.get("scoring_result.zip"),
                "missing_inputs": missing}
    atomic_write_json(resolve_repo_path(outputs.get("input_manifest", "TXT/manifests/inputs.json")), manifest, input_paths=input_paths)
    baseline_path = resolve_repo_path(outputs.get("baseline_manifest", "TXT/manifests/baseline.json"))
    # Audit không được ghi đè một kết quả R0 đã thực hiện.
    if not baseline_path.exists() or read_json(baseline_path).get("status") not in ("completed", "reproduced"):
        atomic_write_json(baseline_path, baseline, input_paths=input_paths)
    lines = ["# DATA READINESS", "", f"Trạng thái: `{status}`; thiếu {len(missing)}/{len(inputs)} roles.",
             "", "| Role | Path | Status |", "|---|---|---|"]
    lines += [f"| {r} | {i['declared_path']} | {i['status']} |" for r, i in inputs.items()]
    lines += ["", "Archives chỉ là ARTIFACT_OBSERVED, chưa liên kết với w045.",
              "Macro checks và IDs đã quan sát nằm trong input manifest; không dùng feedback làm qrels.",
              "", "Thiếu handover chặn R0/pool thật; thiếu queries chặn L0/sampling thật;",
              "thiếu nhãn reviewed chặn dev selection và holdout. Fixtures vẫn chạy độc lập."]
    atomic_write_text(resolve_repo_path(outputs.get("readiness_report", "TXT/reports/DATA_READINESS.md")), "\n".join(lines) + "\n", input_paths=input_paths)
    return manifest, int(status != "ready")
