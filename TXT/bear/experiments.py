"""Protocol/split freeze và blinded annotation; không tự tạo nhãn."""
import random
import unicodedata
from .adapters import read_queries
from .artifacts import (complete_run, corpus_connection, file_identity, read_corpus_batch,
                        required_path, start_run, verify_manifest)
from .contracts import SchemaInvalidError
from .io import (atomic_write_json, canonical_sha256, read_json, read_jsonl,
                 resolve_repo_path, sha256_file, write_jsonl)
from .reproduce import load_ranks


def split_queries(queries, sample_size=100, dev_size=60, seed=42, reviewed_groups=None):
    if not 0 < dev_size < sample_size <= len(queries):
        raise SchemaInvalidError("Cần 0 < dev_size < sample_size <= số query")
    normalized = {}
    groups = {}
    for qid, text in sorted(queries.items()):
        key = " ".join(unicodedata.normalize("NFKC", text).lower().split())
        normalized.setdefault(key, qid)
        groups[qid] = normalized[key]
    if reviewed_groups:
        # Union cả exact và reviewed mappings, giữ tính bắc cầu.
        parent = {q: q for q in queries}
        def find(q):
            while parent[q] != q:
                parent[q] = parent[parent[q]]
                q = parent[q]
            return q
        for q, group in groups.items():
            parent[find(q)] = find(group)
        for group in reviewed_groups:
            if any(q not in queries for q in group):
                raise SchemaInvalidError("Reviewed group có qid lạ")
            for q in group[1:]:
                parent[find(q)] = find(group[0])
        groups = {q: find(q) for q in queries}
    rng = random.Random(seed)
    sampled = sorted(rng.sample(sorted(queries), sample_size))
    members = {}
    for q in sampled:
        members.setdefault(groups[q], []).append(q)
    keys = sorted(members)
    rng.shuffle(keys)
    dev = []
    for group in keys:
        proposed = len(dev) + len(members[group])
        if abs(proposed - dev_size) <= abs(len(dev) - dev_size):
            dev.extend(members[group])
    holdout = sorted(set(sampled) - set(dev))
    if not dev or not holdout:
        raise SchemaInvalidError("Grouping không cho phép split dev/holdout; cần protocol khác")
    return {"sampled_ids": sampled, "dev": sorted(dev), "holdout": holdout,
            "query_groups": {str(q): groups[q] for q in sampled},
            "seed": seed, "procedure": "SRS IDs, group-preserving split",
            "actual_counts": {"dev": len(dev), "holdout": len(holdout)}}


def sample(cfg):
    paths = [cfg["queries"], cfg["protocol"]]
    if cfg.get("reviewed_groups"):
        paths.append(cfg["reviewed_groups"])
    inputs = [file_identity(p) for p in paths]
    root, manifest, reused = start_run(cfg["output_dir"], cfg, inputs)
    if reused:
        return manifest
    queries = read_queries(cfg["queries"])
    split = split_queries({q: r.query for q, r in queries.items()}, cfg.get("sample_size", 100),
                          cfg.get("dev_size", 60), cfg.get("seed", 42),
                          read_json(cfg["reviewed_groups"]) if cfg.get("reviewed_groups") else None)
    observed = cfg.get("previously_observed_ids", [])
    # Luôn ghi contamination từ scoring archive nếu có, không đọc hidden grades.
    archive = resolve_repo_path("scoring_result.zip")
    if archive.is_file():
        import zipfile, json
        with zipfile.ZipFile(archive) as z:
            if "details.jsonl" in z.namelist():
                with z.open("details.jsonl") as source:
                    observed = sorted(set(observed) | {int(json.loads(line)["id"]) for line in source})
    split.update(schema_version=1, query_hash=inputs[0]["sha256"], protocol_hash=inputs[1]["sha256"],
                 previously_observed_ids=sorted(set(observed) & set(split["sampled_ids"])),
                 confirmatory_eligible=not (set(observed) & set(split["holdout"])))
    path = root / "split.json"
    atomic_write_json(path, split)
    smoke_path = root / "smoke_ids.json"
    atomic_write_json(smoke_path, sorted(random.Random(cfg.get("seed", 42)).sample(sorted(queries), 2)))
    return complete_run(root, manifest, [path, smoke_path], split_path=str(path), split_hash=sha256_file(path))


def annotation_export(cfg):
    split = read_json(required_path(cfg["split_manifest"]))
    if cfg["split"] not in ("dev", "holdout") or cfg["mode"] not in ("differences", "topk"):
        raise SchemaInvalidError("split/mode không hợp lệ")
    if cfg["split"] == "holdout":
        frozen = read_json(required_path(cfg.get("frozen_candidate")))
        if frozen["split_hash"] != sha256_file(cfg["split_manifest"]):
            raise SchemaInvalidError("Frozen candidate split mismatch")
        allowed = {frozen["candidate_path"], *frozen.get("control_paths", [])}
        if set(map(str, map(resolve_repo_path, cfg["predictions"]))) - allowed:
            raise SchemaInvalidError("Holdout chỉ annotation candidate/controls đã freeze")
    paths = [cfg["queries"], cfg["corpus"], cfg["baseline"], cfg["split_manifest"], *cfg["predictions"]]
    inputs = [file_identity(p) for p in paths]
    root, manifest, reused = start_run(cfg["output_dir"], cfg, inputs)
    if reused:
        return manifest
    queries = read_queries(cfg["queries"])
    baseline = load_ranks(cfg["baseline"])
    predictions = [load_ranks(p) for p in cfg["predictions"]]
    pairs = set()
    for qid in split[cfg["split"]]:
        for prediction in predictions:
            if qid not in prediction or qid not in baseline:
                raise SchemaInvalidError(f"Annotation thiếu qid {qid}")
            left, right = set(prediction[qid][:cfg["k"]]), set(baseline[qid][:cfg["k"]])
            docs = left ^ right if cfg["mode"] == "differences" else left | right
            pairs.update((qid, d) for d in docs)
    shuffled = sorted(pairs)
    random.Random(cfg.get("seed", 42)).shuffle(shuffled)
    with corpus_connection(cfg["corpus"]) as conn:
        metadata = read_corpus_batch(conn, sorted({d for _, d in pairs}))
    rows = []
    for index, (qid, doc) in enumerate(shuffled):
        if doc not in metadata:
            raise SchemaInvalidError(f"Annotation doc thiếu text: {doc}")
        row = metadata[doc]
        rows.append({"annotation_id": f"a{index:06d}", "query_id": qid, "query": queries[qid].query,
                     "doc_id": doc, "language": row.get("lang"), "body": row.get("body"),
                     "grade": None, "annotator": None, "adjudication": "unreviewed",
                     "supporting_passages": [], "label_policy_version": "local_answer_v1", "notes": ""})
    path = write_jsonl(root / "blinded.jsonl", rows)
    return complete_run(root, manifest, [path], pairs=len(rows), labels_generated=False)


def freeze(run_dir, protocol_path):
    root = resolve_repo_path(run_dir)
    manifest = verify_manifest(root / "manifest.json")
    protocol = read_json(required_path(protocol_path))
    for field in ("split_manifest", "selected_dev_report", "controls", "cost_ceiling_seconds"):
        if field not in protocol or protocol[field] is None:
            raise SchemaInvalidError(f"Freeze cần protocol.{field}")
    split = read_json(required_path(protocol["split_manifest"]))
    dev = read_json(required_path(protocol["selected_dev_report"]))
    if dev.get("status") != "available" or dev.get("split") != "dev":
        raise SchemaInvalidError("Freeze cần primary dev evaluation hợp lệ")
    from .contracts import validate_finite_number
    validate_finite_number(protocol["cost_ceiling_seconds"], "cost_ceiling_seconds", min_val=0)
    if protocol["cost_ceiling_seconds"] <= 0:
        raise SchemaInvalidError("Cost ceiling must be positive")
    if protocol.get("primary_metric") and dev.get("primary_metric") and protocol["primary_metric"] != dev["primary_metric"]:
        raise SchemaInvalidError("Protocol primary metric differs from selected dev metric")
    candidate = root / "candidates.jsonl"
    if dev.get("candidate_sha256") != sha256_file(candidate):
        raise SchemaInvalidError("Dev selection không thuộc candidate này")
    code = sorted((resolve_repo_path("TXT/bear")).glob("*.py"))
    frozen = {"schema_version": 1, "candidate_path": str(candidate),
              "candidate_sha256": sha256_file(candidate), "manifest_sha256": sha256_file(root / "manifest.json"),
              "protocol": file_identity(protocol_path), "split_hash": sha256_file(protocol["split_manifest"]),
              "control_paths": [str(resolve_repo_path(p)) for p in protocol["controls"]],
              "controls": [file_identity(p) for p in protocol["controls"]],
              "code": [file_identity(p) for p in code], "selection": file_identity(protocol["selected_dev_report"]),
              "confirmatory_eligible": split["confirmatory_eligible"], "holdout_exposed": False}
    # Bind the whole candidate, including selector, offsets and selected chunks.
    if manifest.get("candidate_kind") == "chunk":
        selected_records = root / "records.json"
        selected_refs = root / "chunk_refs.jsonl"
        for item in (selected_records, selected_refs):
            identity = file_identity(item)
            if identity not in manifest["artifacts"]:
                raise SchemaInvalidError("Chunk candidate artifacts not bound to run manifest")
        if dev.get("records_sha256") != sha256_file(selected_records):
            raise SchemaInvalidError("Chunk freeze needs selected chunk evaluation, not document-only score")
    frozen.update(candidate_kind=manifest.get("candidate_kind", "document"),
                  candidate_manifest=file_identity(root / "manifest.json"),
                  candidate_artifacts=manifest["artifacts"],
                  evaluation_contract={key: dev.get(key, protocol.get(key)) for key in (
                      "primary_metric", "k", "coverage", "label_policy_version", "empty_gold_policy")
                      if dev.get(key, protocol.get(key)) is not None})
    path = root / "frozen.json"
    if path.exists() and read_json(path) != frozen:
        raise SchemaInvalidError("Candidate đã freeze, không overwrite")
    atomic_write_json(path, frozen)
    return frozen


def fixed_menu():
    return [{"id": f"F0_{i:02d}", "mode": "fixed", "lambda": lam,
             "weights": {"B": b, "D": round(1-b, 10)}}
            for i, (lam, b) in enumerate(( (lam, b) for lam in (.10, .25)
                for b in (0, .10, .20, .35, .50, .65, .80, .90, 1)))]


def select_dev(trials):
    if not trials or any(t.get("status") != "available" for t in trials):
        raise SchemaInvalidError("Không chọn best khi trial thiếu primary labels")
    best = max(t["metric"] for t in trials)
    tied = [t for t in trials if best - t["metric"] <= 1e-12]
    return min(tied, key=lambda t: (t["lambda"], t["cost_seconds"], t["id"]))
