"""Xuất frozen ranking với calibration/plan legacy, giữ rollback riêng."""
from .artifacts import complete_run, file_identity, read_corpus_batch, corpus_connection, start_run, verify_manifest
from .contracts import SchemaInvalidError
from .io import read_json, resolve_repo_path, write_jsonl, canonical_sha256
from .reproduce import input_identities, load_ranks, load_scores, preflight, membership_ids


def export_run(cfg, run_dir):
    from .baseline import score_frozen_calibration, make_plan_from_calibrated_p
    from .integrity import load_legacy_chunk_scores, build_with_refs, validate_records, package_zip, legacy_readonly_audit
    from submit.submission import fingerprint
    run_dir = resolve_repo_path(run_dir)
    run = verify_manifest(run_dir / "manifest.json")
    inputs = input_identities(cfg)
    ranking_path = run_dir / "candidates.jsonl"
    inputs += [file_identity(ranking_path), file_identity(run_dir / "manifest.json")]
    root, manifest, reused = start_run(cfg["output_dir"], cfg, inputs)
    if reused:
        return manifest
    ranking = load_ranks(ranking_path)
    if set(ranking) != set(range(1, 1201)) or any(len(d) != 200 for d in ranking.values()):
        raise SchemaInvalidError("Export cần 1200 query × 200 doc")
    paths = {r: s["path"] for r, s in cfg["inputs"].items()}
    if resolve_repo_path(cfg["corpus"]) != resolve_repo_path(paths["corpus"]):
        raise SchemaInvalidError("Export corpus khác calibration corpus")
    ids = {d for ds in ranking.values() for d in ds}
    with corpus_connection(paths["corpus"]) as conn:
        docs = read_corpus_batch(conn, sorted(ids))
    languages = {d: row.get("lang") for d, row in docs.items()}
    if any(not languages.get(d) for d in ids):
        raise SchemaInvalidError("Thiếu lang cho allocation")
    members = membership_ids(paths["membership"])
    if any(d not in members and docs[d].get("domain") != "vinmec.com" for d in ids):
        raise SchemaInvalidError("Export có doc ngoài frozen membership và ngoại lệ vinmec.com")
    bundle = {r: load_scores(paths[r]) for r in ("qwen_doc_scores", "chunk_dense", "zh_bge_vi", "zh_bge_zh")}
    p = score_frozen_calibration(ranking, bundle, read_json(paths["beta"]), languages)
    plans = {q: make_plan_from_calibrated_p(q, rows) for q, rows in p.items()}
    records, refs = build_with_refs(ranking, paths["corpus"], load_legacy_chunk_scores(paths["chunk_scores"]), plans, inputs[0]["sha256"])
    validation = validate_records(records, refs, paths["corpus"])
    # Đây là package kỹ thuật; không tự promote phương pháp hoặc upload.
    from .io import atomic_write_json
    audit_path = root / "legacy_audit.json"
    atomic_write_json(audit_path, legacy_readonly_audit(paths["corpus"]))
    artifact_paths = [audit_path, *package_zip(records, root / "submission")]
    artifact_paths.append(write_jsonl(root / "chunk_refs.jsonl", refs))
    artifact_paths.append(write_jsonl(root / "allocation.jsonl", ({"id": q, "candidates": rows} for q, rows in p.items())))
    return complete_run(root, manifest, artifact_paths, integrity=validation,
                        legacy_fingerprints=dict(zip(("doc", "chunk"), fingerprint(records))),
                        provenance_sha256=canonical_sha256(refs), promoted=False,
                        size_limit_assumption="<100000000 bytes", allocation="frozen_handover")
