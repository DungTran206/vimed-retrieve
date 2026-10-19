"""Recipe R0 CPU với paths explicit, calibration frozen và provenance."""
from pathlib import Path
from .adapters import read_rank_source
from .artifacts import (complete_run, corpus_connection, file_identity, read_corpus_batch,
                        required_path, start_run)
from .contracts import BaselineParityFailedError, InputMissingError, SchemaInvalidError
from .io import atomic_write_json, read_json, write_jsonl

ROLES = ("corpus", "vi_base", "vi_alt", "zh_bge_vi", "zh_bge_zh", "zh_bge_patch",
         "zh_q8_vi", "zh_q8_zh", "zh_q8_patch", "membership", "chunk_scores",
         "qwen_doc_scores", "chunk_dense", "beta")


def load_ranks(path):
    return {q.query_id: [i.doc_id for i in q.items] for q in read_rank_source(required_path(path))}


def load_scores(path):
    return {q.query_id: {i.doc_id: i.score for i in q.items if i.score is not None}
            for q in read_rank_source(required_path(path))}


def membership_ids(path):
    path = required_path(path)
    if path.suffix == ".json":
        return set(read_json(path))
    import pandas as pd
    return set(pd.read_parquet(path, columns=["id"])["id"].astype(str))


def preflight(cfg):
    declarations = cfg.get("inputs", {})
    missing = [r for r in ROLES if not declarations.get(r, {}).get("path") or
               not Path(required_or_none(declarations[r]["path"])).is_file()]
    return {"status": "blocked_input" if missing else "inputs_present_unverified",
            "missing_roles": missing, "stages": ["patch400", "zh_rrf", "membership",
            "vi_zh_rrf", "head120", "filter_refill", "calibration8", "plan", "build", "parity"],
            "output_dir": cfg.get("output_dir", "TXT/runtime/runs/R0")}


def required_or_none(value):
    from .io import resolve_repo_path
    return resolve_repo_path(value)


def input_identities(cfg):
    identities = []
    from .contracts import HashMismatchError
    for role in ROLES:
        spec = cfg["inputs"][role]
        identity = file_identity(spec["path"])
        if spec.get("expected_sha256") and identity["sha256"] != spec["expected_sha256"]:
            raise HashMismatchError(f"Hash mismatch: {role}")
        identities.append(identity)
    return identities


def execute(cfg, export=False):
    report = preflight(cfg)
    if report["missing_roles"]:
        raise InputMissingError("R0 thiếu: " + ", ".join(report["missing_roles"]))
    from .baseline import (rrf_fuse_rankings, build_head_hybrid, filter_and_refill_candidates,
                           score_frozen_calibration, make_plan_from_calibrated_p)
    from .integrity import build_with_refs, validate_records, package_zip
    from submit.submission import fingerprint
    from .io import canonical_sha256
    inputs = input_identities(cfg)
    root, manifest, reused = start_run(report["output_dir"], cfg | {"export": export}, inputs)
    if reused:
        return manifest
    paths = {r: cfg["inputs"][r]["path"] for r in ROLES}
    base, alt = load_ranks(paths["vi_base"]), load_ranks(paths["vi_alt"])
    if set(base) != set(range(1, 1201)) or set(alt) != set(base):
        raise SchemaInvalidError("R0 cần qid 1..1200 đầy đủ")
    zh_sources = []
    for prefix, weight in (("zh_bge", 1), ("zh_q8", .3)):
        vi = {q: ds[:400] for q, ds in load_ranks(paths[prefix + "_vi"]).items()}
        zh = {q: ds[:400] for q, ds in load_ranks(paths[prefix + "_zh"]).items()}
        patch = {q: ds[:400] for q, ds in load_ranks(paths[prefix + "_patch"]).items()}
        if set(vi) != set(base) or set(zh) != set(base) or not set(patch) <= set(base):
            raise SchemaInvalidError("ZH source query universe khác R0")
        zh.update(patch)
        zh_sources.extend([(vi, weight), (zh, weight)])
    members = membership_ids(paths["membership"])
    zf = rrf_fuse_rankings(zh_sources)
    zh = {q: [d for _, d in rows if d in members] for q, rows in zf.items()}
    deep = {q: [d for _, d in rows] for q, rows in rrf_fuse_rankings([(base, 1), (zh, .45)]).items()}
    all_ids = sorted({d for ds in deep.values() for d in ds})
    with corpus_connection(paths["corpus"]) as conn:
        metadata = read_corpus_batch(conn, all_ids)
    vinmec = {d for d, row in metadata.items() if row.get("domain") == "vinmec.com"}
    ranking = {q: filter_and_refill_candidates(build_head_hybrid(deep[q], alt[q]), deep[q], members, vinmec) for q in sorted(base)}
    if any(len(ds) != 200 for ds in ranking.values()):
        raise SchemaInvalidError("Không refill đủ 200 docs")
    languages = {d: row.get("lang") for d, row in metadata.items()}
    if any(not languages.get(d) for ds in ranking.values() for d in ds):
        raise SchemaInvalidError("Corpus thiếu doc/lang trong R0")
    bundle = {r: load_scores(paths[r]) for r in ("qwen_doc_scores", "chunk_dense", "zh_bge_vi", "zh_bge_zh")}
    probabilities = score_frozen_calibration(ranking, bundle, read_json(paths["beta"]), languages)
    plans = {q: make_plan_from_calibrated_p(q, rows) for q, rows in probabilities.items()}
    from .integrity import load_legacy_chunk_scores
    scores = load_legacy_chunk_scores(paths["chunk_scores"])
    records, refs = build_with_refs(ranking, paths["corpus"], scores, plans, inputs[0]["sha256"])
    validate_records(records, refs, paths["corpus"])
    observed = dict(zip(("doc", "chunk"), fingerprint(records)))
    expected = cfg.get("expected_fingerprints", {"doc": "c1e068422e5f", "chunk": "fd07f9fc029a"})
    paths_out = []
    for name, data in (("candidates", [{"id": q, "candidates": [{"doc_id": d, "score": round(1-i/(len(ds)+1), 6)} for i, d in enumerate(ds)]} for q, ds in ranking.items()]),
                       ("deep", [{"id": q, "candidates": [{"doc_id": d, "score": round(1-i/(len(ds)+1), 6)} for i, d in enumerate(ds)]} for q, ds in deep.items()]),
                       ("allocation", [{"id": q, "candidates": rows} for q, rows in probabilities.items()]),
                       ("chunk_refs", refs)):
        paths_out.append(write_jsonl(root / (name + ".jsonl"), data))
    atomic_write_json(root / "records.json", records)
    paths_out.append(root / "records.json")
    atomic_write_json(root / "parity.json", {"expected": expected, "observed": observed,
                       "matches": observed == expected})
    paths_out.append(root / "parity.json")
    if observed != expected:
        raise BaselineParityFailedError(f"R0 fingerprint khác: {observed}; debug: {root}")
    if export:
        paths_out.extend(package_zip(records, root / "submission"))
    return complete_run(root, manifest, paths_out, observed_fingerprints=observed,
                        canonical_ranking_sha256=canonical_sha256(ranking),
                        provenance_sha256=canonical_sha256(refs), parity_verified=True)
