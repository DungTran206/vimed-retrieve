"""Menu L1/F0 preregistered: inference và evaluation là hai bước riêng."""
import time
from .artifacts import required_path, file_identity
from .config import command_config, fields
from .contracts import SchemaInvalidError
from .experiments import fixed_menu, select_dev
from .io import atomic_write_json, read_json, resolve_repo_path, canonical_sha256


def evidence_menu(family):
    if family not in ("L1", "L4"):
        raise SchemaInvalidError("Evidence family must be L1/L4")
    return [{"id": f"{family}_{i}", "mode": "fixed_evidence", "lambda": lam,
             "feature_name": "body_coverage" if family == "L1" else "local_max_all"}
            for i, lam in enumerate((0, .02, .05, .10, .20, .35))]


def tune(protocol_path, menu_path, split="dev", execute=False):
    if split != "dev":
        raise SchemaInvalidError("Tuning chỉ được chạy trên dev")
    protocol = read_json(required_path(protocol_path))
    fields(protocol, {"schema_version": int, "study_id": str, "family": str,
                      "run_config": str, "evaluation_config": (str, type(None)),
                      "baseline_dir": (str, type(None)), "output_dir": str}, "tuning protocol",
           ("schema_version", "study_id", "family", "run_config", "evaluation_config", "output_dir"))
    menus = read_json(required_path(menu_path))
    family = protocol["family"]
    if family == "F0":
        trials = fixed_menu()
        if menus.get("F0") != trials:
            raise SchemaInvalidError("F0 cần đúng 18 trials đã chốt trong PLAN")
    elif family in ("L1", "L4", "L1_L4"):
        families = ("L1", "L4") if family == "L1_L4" else (family,)
        trials = []
        for name in families:
            expected = evidence_menu(name)
            if menus.get(name) != expected:
                raise SchemaInvalidError(f"{name} menu khác PLAN")
            trials.extend(expected)
    else:
        raise SchemaInvalidError("Chỉ L1/L4/L1_L4/F0; A1 cần O0/controls và study mới")
    if not execute:
        return {"status": "dry_run", "family": family, "trials": len(trials), "split": "dev"}
    base = command_config(protocol["run_config"], "run")
    ec = command_config(protocol["evaluation_config"], "evaluate") if protocol["evaluation_config"] else None
    if ec and ec["split"] != "dev":
        raise SchemaInvalidError("Evaluation config của tuning phải dev")
    from .features import inference
    from .evaluate_runner import evaluate
    from .artifacts import start_run, complete_run
    inputs = [file_identity(p) for p in (protocol_path, menu_path, protocol["run_config"])]
    from .artifacts import verify_manifest
    for key in ("pool_manifest", "feature_manifest"):
        if base.get(key):
            verify_manifest(base[key])
            inputs.append(file_identity(base[key]))
    if ec:
        inputs += [file_identity(protocol["evaluation_config"]), file_identity(ec["qrels_path"]), file_identity(ec["split_manifest"])]
        if protocol.get("baseline_dir"):
            inputs.append(file_identity(resolve_repo_path(protocol["baseline_dir"]) / "candidates.jsonl"))
    root, manifest, reused = start_run(protocol["output_dir"], protocol | {"menu": menus}, inputs)
    if reused:
        return manifest
    ledger, trial_artifacts = [], []
    for trial in trials:
        name = trial["id"]
        cfg = base | {k: v for k, v in trial.items() if k != "id"} | {
            "run_id": protocol["study_id"] + "_" + name, "output_dir": str(root / name)}
        started = time.perf_counter()
        trial_manifest = inference(cfg)
        trial_artifacts.extend(resolve_repo_path(item["path"]) for item in trial_manifest["artifacts"])
        report = evaluate(ec | {"output_dir": str(root / name / "evaluation")}, root / name,
                          protocol.get("baseline_dir")) if ec else {"status": "diagnostic_only", "metric": None}
        if ec:
            trial_artifacts.append(root / name / "evaluation/evaluation.json")
        ledger.append({**trial, "config_hash": canonical_sha256(cfg), "status": report["status"],
                       "metric": report["metric"], "cost_seconds": time.perf_counter() - started,
                       "primary_metric": ec["primary_metric"] if ec else None,
                       "evaluation_path": str(root / name / "evaluation/evaluation.json") if ec else None,
                       "manifest": file_identity(root / name / "manifest.json")})
        atomic_write_json(root / "trials.json", ledger)
    best = select_dev(ledger) if all(t["status"] == "available" for t in ledger) else None
    atomic_write_json(root / "selection.json", {"best": best, "status": "selected_dev" if best else "inconclusive",
                                               "holdout_opened": False})
    return complete_run(root, manifest, [root / "trials.json", root / "selection.json",
                        *[resolve_repo_path(t["manifest"]["path"]) for t in ledger], *trial_artifacts],
                        selection_status="selected_dev" if best else "inconclusive", trials=len(ledger))
