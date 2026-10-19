"""N3 controlled native-offset chunk selector study; no implicit allocation changes."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from .adapters import load_chunk_refs
from .application_audit import indexed
from .artifacts import (file_identity, verify_manifest, start_run, complete_run,
                        corpus_connection, read_corpus_batch)
from .baseline import make_plan_from_calibrated_p
from .chunk_experiments import select_chunks
from .contracts import SchemaInvalidError
from .integrity import build_with_refs, load_legacy_chunk_scores, validate_records
from .io import (read_json, read_jsonl, write_jsonl, atomic_write_json,
                 atomic_write_text, resolve_repo_path, canonical_sha256)
from .reproduce import load_ranks


def run_chunk_study(cfg):
    if cfg["experiment"] not in ("C1", "C2"):
        raise SchemaInvalidError("Chunk study supports C1/C2 only")
    run_path = resolve_repo_path(cfg["ranking_dir"]) / "manifest.json"
    run = verify_manifest(run_path)
    rank_path = run_path.parent / "candidates.jsonl"
    inputs = [file_identity(p) for p in (run_path, rank_path, cfg["corpus"], cfg["allocation"], cfg["chunk_scores"])]
    corpus_hash = inputs[2]["sha256"]
    origin = run.get("corpus_hash")
    if run["config"].get("pool_manifest"):
        origin = verify_manifest(run["config"]["pool_manifest"])["corpus_hash"]
    elif run["config"].get("inputs", {}).get("corpus", {}).get("path"):
        source_path = resolve_repo_path(run["config"]["inputs"]["corpus"]["path"])
        origin = next((item["sha256"] for item in run["inputs"] if resolve_repo_path(item["path"]) == source_path), None)
    if origin != corpus_hash:
        raise SchemaInvalidError("Chunk study corpus differs from frozen ranking snapshot")
    ranking = load_ranks(rank_path)
    if cfg.get("query_ids_path"):
        inputs.append(file_identity(cfg["query_ids_path"]))
        ids = read_json(inputs[-1]["path"])
        ids = ids if isinstance(ids, list) else ids["sampled_ids"]
        if not ids or len(ids) != len(set(ids)) or set(ids) - set(ranking):
            raise SchemaInvalidError("Invalid pilot query universe")
        ranking = {q: ranking[q] for q in ids}
    if not ranking or any(len(docs) != 200 for docs in ranking.values()):
        raise SchemaInvalidError("Chunk control requires 200 documents per query")
    allocations = indexed(read_jsonl(inputs[3]["path"]), "id")
    plans = {}
    for qid, docs in ranking.items():
        probabilities = allocations.get(qid, {}).get("candidates", [])
        if [r["doc_id"] for r in probabilities] != docs:
            raise SchemaInvalidError("Allocation order must exactly match frozen ranking")
        plans[qid] = make_plan_from_calibrated_p(qid, probabilities)
    evidence, feature_inputs = {}, []
    if cfg["experiment"] == "C2":
        fm = verify_manifest(cfg.get("feature_manifest"))
        if verify_manifest(fm["pool_manifest"])["corpus_hash"] != corpus_hash:
            raise SchemaInvalidError("Chunk evidence corpus differs from study snapshot")
        feature_inputs.append(file_identity(cfg["feature_manifest"]))
        for identity in fm["artifacts"]:
            if Path(identity["path"]).name.startswith("chunks_"):
                for row in read_jsonl(identity["path"]):
                    key = row["query_id"], row["doc_id"], row["ref"]["exporter_idx"]
                    if key in evidence:
                        raise SchemaInvalidError("Duplicate chunk feature")
                    evidence[key] = row
    inputs += feature_inputs
    root, manifest, reused = start_run(cfg["output_dir"], cfg, inputs)
    if reused:
        return manifest
    scores = load_legacy_chunk_scores(inputs[4]["path"])
    control, control_refs = build_with_refs(ranking, cfg["corpus"], scores, plans, corpus_hash)
    records, sidecar, ledger = [], [], []
    totals = Counter()
    with corpus_connection(cfg["corpus"]) as conn:
        for qid, docs in sorted(ranking.items()):
            refs = load_chunk_refs(conn, docs, corpus_hash)
            bodies = read_corpus_batch(conn, docs)
            chosen = []
            for rank, doc in enumerate(docs, 1):
                native = refs.get(doc, [])
                slots = 2 if rank <= 40 else (1 if rank <= 120 else 0)
                if plans[qid].get(doc) == 0:
                    slots = 0
                elif rank > 120:
                    slots = plans[qid].get(doc, 0)
                if not slots:
                    continue
                sc = scores.get(qid, {}).get(doc)
                if sc and set(sc) - {r.exporter_idx for r in native}:
                    raise SchemaInvalidError("Chunk score index outside verified native namespace")
                values = {}
                for ref in native:
                    feature = evidence.get((qid, doc, ref.exporter_idx))
                    if feature is not None:
                        if feature["ref"] != asdict(ref):
                            raise SchemaInvalidError("Chunk feature mapping/body/corpus hash mismatch")
                        values[ref.exporter_idx] = feature["coverage"]
                selected, reason = select_chunks(native, slots, rank, cfg["experiment"], sc, values or None)
                chosen.extend(selected)
                ledger.append({"query_id": qid, "doc_id": doc, "rank": rank, "slots": slots,
                               "actual_chunks": len(selected), "native_count": len(native),
                               "complete_scores": bool(native) and sc is not None and all(r.exporter_idx in sc for r in native),
                               "reason": reason, "selected_indices": [r.exporter_idx for r in selected]})
                totals[reason] += 1
                totals["multi_chunk_documents"] += len(native) > 1
            chunks = []
            for pos, ref in enumerate(chosen):
                chunks.append({"doc_id": int(ref.doc_id), "chunk_text": bodies[ref.doc_id]["body"][ref.start:ref.end]})
                sidecar.append({"query_id": qid, "doc_rank": docs.index(ref.doc_id) + 1,
                                "output_position": pos, **asdict(ref)})
            records.append({"id": qid, "relevant_docs": [int(d) for d in docs], "relevant_chunks": chunks})
    validate_records(control, control_refs, cfg["corpus"], query_ids=ranking)
    validation = validate_records(records, sidecar, cfg["corpus"], query_ids=ranking)
    slots_before = Counter((r["query_id"], r["doc_id"]) for r in control_refs)
    slots_after = Counter((r["query_id"], r["doc_id"]) for r in sidecar)
    if slots_before != slots_after:
        raise SchemaInvalidError("Selector changed per-document actual chunk budget")
    paths = [write_jsonl(root / "candidates.jsonl", [{"id": q, "candidates": ds} for q, ds in sorted(ranking.items())]),
             atomic_write_json(root / "records.json", records), atomic_write_json(root / "control_records.json", control),
             write_jsonl(root / "chunk_refs.jsonl", sidecar), write_jsonl(root / "control_chunk_refs.jsonl", control_refs),
             write_jsonl(root / "selection_details.jsonl", ledger)]
    summary = {"schema_version": 2, "status": "diagnostic_only", "experiment": cfg["experiment"],
               "queries": len(ranking), "slot_invariant": True, "counts": dict(totals),
               "characters": sum(len(c["chunk_text"]) for r in records for c in r["relevant_chunks"]),
               "whitespace_tokens": sum(len(c["chunk_text"].split()) for r in records for c in r["relevant_chunks"]),
               "quality_decision": "inconclusive", "zip_bytes": None, "promoted": False}
    paths += [atomic_write_json(root / "chunk_study.json", summary),
              atomic_write_text(root / "report.md", "# N3 chunk selector study\n\nSame documents/order and actual slots verified.\n\n" +
                  "Quality remains inconclusive without separately reviewed passage evaluation.\n")]
    return complete_run(root, manifest, paths, candidate_kind="chunk", corpus_hash=corpus_hash,
                        selector=cfg["experiment"], allocation_sha256=inputs[3]["sha256"],
                        integrity=validation, provenance_sha256=canonical_sha256(sidecar), summary=summary)
