"""N0: inventory explicit artifacts; never infer submission linkage from filenames."""
from .artifacts import file_identity, required_path, start_run, complete_run, verify_manifest
from .contracts import HashMismatchError, InputMissingError, SchemaInvalidError
from .io import atomic_write_json, atomic_write_text, read_json


def inspect_provenance(cfg, execute=False):
    inputs, inventory, missing = [], {}, []
    for role, spec in cfg["inputs"].items():
        if not spec.get("path"):
            missing.append(role)
            inventory[role] = None
            continue
        try:
            identity = file_identity(spec["path"])
        except (FileNotFoundError, InputMissingError):
            missing.append(role)
            inventory[role] = None
            continue
        if spec.get("expected_sha256") and spec["expected_sha256"] != identity["sha256"]:
            raise HashMismatchError(f"Provenance input changed: {role}")
        inputs.append(identity)
        inventory[role] = identity
    linked = False
    if cfg.get("linkage_record"):
        inputs.append(file_identity(cfg["linkage_record"]))
        link = read_json(required_path(cfg["linkage_record"]))
        if link.get("adjudication") != "reviewed" or not link.get("reviewer") or not link.get("submission_id"):
            raise SchemaInvalidError("Linkage needs reviewed provenance and submission_id")
        for role in ("submission", "scoring_output", "candidate_manifest"):
            if not inventory.get(role) or link.get(role + "_sha256") != inventory[role]["sha256"]:
                raise HashMismatchError(f"Linkage does not bind {role}")
        verify_manifest(inventory["candidate_manifest"]["path"])
        linked = True
    parity = None
    if inventory.get("baseline_manifest"):
        baseline = verify_manifest(inventory["baseline_manifest"]["path"])
        parity = baseline.get("parity_verified") is True and baseline.get("observed_fingerprints") == {
            "doc": "c1e068422e5f", "chunk": "fd07f9fc029a"}
    report = {"schema_version": 2, "status": "blocked_input" if missing else "available",
              "evidence": "REPORTED", "reported": cfg["reported"], "inventory": inventory,
              "missing_roles": missing, "submission_linkage": "linked_reviewed" if linked else "unresolved",
              "baseline_parity_verified": parity, "quality_decision": "inconclusive",
              "observed_metrics": None, "promoted": False}
    if not execute:
        return report | {"dry_run": True}
    root, manifest, reused = start_run(cfg["output_dir"], cfg, inputs)
    if reused:
        return manifest
    paths = [atomic_write_json(root / "provenance.json", report),
             atomic_write_text(root / "report.md", "# N0 provenance\n\n" +
                f"Linkage: {report['submission_linkage']}; baseline parity: {parity}.\n\n" +
                "Missing roles: " + ", ".join(missing) + "\n\nReported scores are not observed qrels or a quality gain verification.\n")]
    return complete_run(root, manifest, paths, readiness_status=report["status"],
                        missing_roles=missing, submission_linkage=report["submission_linkage"])
