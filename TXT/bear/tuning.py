"""Menu L1/F0 preregistered: inference và evaluation là hai bước riêng."""
import time
from .artifacts import required_path, file_identity
from .config import command_config, fields
from .contracts import SchemaInvalidError
from .experiments import fixed_menu, select_dev
from .io import atomic_write_json, read_json, resolve_repo_path, canonical_sha256


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
    elif family == "L1":
        trials = [{"id": f"L1_{i}", "mode": "fixed_evidence", "lambda": lam, "feature_name": "body_coverage"}
                  for i, lam in enumerate((0, .02, .05, .10, .20, .35))]
        if menus.get("L1") != trials:
            raise SchemaInvalidError("L1 menu khác PLAN")
    else:
        raise SchemaInvalidError("Vòng đầu chỉ L1/F0; A1 cần O0/controls và study mới")
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
    if ec:
        inputs += [file_identity(protocol["evaluation_config"]), file_identity(ec["qrels_path"]), file_identity(ec["split_manifest"])]
    root, manifest, reused = start_run(protocol["output_dir"], protocol | {"menu": menus}, inputs)
    if reused:
        return manifest
    ledger = []
    for trial in trials:
        name = trial["id"]
        cfg = base | {k: v for k, v in trial.items() if k != "id"} | {
            "run_id": protocol["study_id"] + "_" + name, "output_dir": str(root / name)}
        started = time.perf_counter()
        inference(cfg)
        report = evaluate(ec | {"output_dir": str(root / name / "evaluation")}, root / name,
                          protocol.get("baseline_dir")) if ec else {"status": "diagnostic_only", "metric": None}
        ledger.append({**trial, "config_hash": canonical_sha256(cfg), "status": report["status"],
                       "metric": report["metric"], "cost_seconds": time.perf_counter() - started})
        atomic_write_json(root / "trials.json", ledger)
    best = select_dev(ledger) if all(t["status"] == "available" for t in ledger) else None
    atomic_write_json(root / "selection.json", {"best": best, "status": "selected_dev" if best else "inconclusive",
                                               "holdout_opened": False})
    return complete_run(root, manifest, [root / "trials.json", root / "selection.json"],
                        selection_status="selected_dev" if best else "inconclusive", trials=len(ledger))
