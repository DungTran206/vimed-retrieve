"""Pool/features/inference orchestration; không import evaluator hoặc qrels."""
from collections import Counter
from dataclasses import asdict
import time
from .adapters import load_chunk_refs, read_queries
from .artifacts import (complete_run, corpus_connection, file_identity, read_corpus_batch,
                        start_run, verify_manifest)
from .contracts import SchemaInvalidError
from .evidence import FEATURE_VERSION, MATCHER_VERSION, document_evidence, query_evidence
from .io import (atomic_write_json, atomic_write_text, canonical_sha256, read_json,
                 read_jsonl, write_jsonl)
from .matching import build_query_concepts, compute_concept_set_hash
from .pools import build_pool, route_support
from .reproduce import load_ranks, membership_ids


def create_pools(cfg):
    source_specs = cfg.get("sources", [])
    input_paths = [cfg[k] for k in ("baseline", "deeper", "corpus", "membership")]
    input_paths += [s["artifact_path"] for s in source_specs]
    if cfg.get("b_family"):
        input_paths.append(cfg["b_family"])
    inputs = [file_identity(p) for p in input_paths]
    from .contracts import HashMismatchError
    for spec in source_specs:
        if file_identity(spec["artifact_path"])["sha256"] != spec["artifact_sha256"]:
            raise HashMismatchError(f"Source hash mismatch: {spec['source_id']}")
        if spec["corpus_hash"] != inputs[2]["sha256"]:
            raise HashMismatchError("Source corpus hash mismatch")
    root, manifest, reused = start_run(cfg["output_dir"], cfg, inputs)
    if reused:
        return manifest
    baseline, deeper = load_ranks(cfg["baseline"]), load_ranks(cfg["deeper"])
    sources = [load_ranks(s["artifact_path"]) for s in source_specs]
    b_family = load_ranks(cfg["b_family"]) if cfg.get("b_family") else {}
    from .io import resolve_repo_path
    verified_b = next((s for s in source_specs if s["source_id"] == "B" and s["complete"]
                       and s["provenance_status"] == "verified"), None)
    if cfg.get("b_family"):
        if not verified_b or resolve_repo_path(verified_b["artifact_path"]) != resolve_repo_path(cfg["b_family"]):
            raise SchemaInvalidError("route support cần B-family artifact đã xác minh trong sources")
    elif verified_b:
        b_family = load_ranks(verified_b["artifact_path"])
    ids = {d for rows in [baseline, deeper, b_family, *sources] for ds in rows.values() for d in ds}
    with corpus_connection(cfg["corpus"]) as conn:
        metadata = read_corpus_batch(conn, sorted(ids))
    languages = {d: row.get("lang") for d, row in metadata.items()}
    members = membership_ids(cfg["membership"])
    eligible = members | {d for d, row in metadata.items() if row.get("domain") == "vinmec.com"}
    pools = []
    for qid, docs in sorted(baseline.items()):
        p = build_pool(docs, deeper.get(qid, []), [s.get(qid, []) for s in sources],
                       languages, eligible, cfg.get("scope", "plarge"), cfg.get("cap", 400))
        support = route_support(b_family.get(qid, []), languages, eligible)
        source_ranks, availability = {}, {}
        for spec, ranks in zip(source_specs, sources):
            name = spec["source_id"]
            mapping = {d: i + 1 for i, d in enumerate(ranks.get(qid, []))}
            source_ranks[name] = mapping
            # Absence chỉ là retrieval miss khi completed retriever được xác minh.
            if spec.get("complete") is not True or spec.get("provenance_status") != "verified":
                availability[name] = "partial_query"
            elif qid not in ranks:
                availability[name] = "missing_query"
            elif spec.get("source_kind") in ("retriever", "family"):
                availability[name] = "not_retrieved"
            else:
                availability[name] = "not_scored"
        pools.append({"query_id": qid, **p, "support": support,
                      "source_ranks": source_ranks, "source_absence": availability})
    pool_path = write_jsonl(root / "pools.jsonl", pools)
    return complete_run(root, manifest, [pool_path], pool_path=str(pool_path),
                        language_policy="frozen_non_vi_slots_v1", query_count=len(pools), corpus_hash=inputs[2]["sha256"])


def compute_features(cfg):
    pool_manifest = verify_manifest(cfg["pool_manifest"])
    query_paths = [cfg[k] for k in ("queries", "enriched_queries", "expansion_queries") if cfg.get(k)]
    inputs = [file_identity(cfg["pool_manifest"]), file_identity(cfg["corpus"])] + [file_identity(p) for p in query_paths]
    if inputs[1]["sha256"] != pool_manifest["corpus_hash"]:
        from .contracts import HashMismatchError
        raise HashMismatchError("Feature corpus khác frozen pool corpus")
    selected = None
    if cfg.get("query_ids_path"):
        inputs.append(file_identity(cfg["query_ids_path"]))
        selected_data = read_json(cfg["query_ids_path"])
        selected = set(selected_data if isinstance(selected_data, list) else selected_data["sampled_ids"])
        if not selected:
            raise SchemaInvalidError("Feature query selection rỗng")
    root, manifest, reused = start_run(cfg["output_dir"], cfg | {"matcher": MATCHER_VERSION}, inputs)
    if reused:
        return manifest
    queries = read_queries(query_paths[0], cfg.get("enriched_queries"), cfg.get("expansion_queries"))
    started = time.perf_counter()
    batch_size = cfg.get("query_batch_size", 20)
    if not 1 <= batch_size <= 100:
        raise SchemaInvalidError("query_batch_size cần 1..100")
    corpus_hash = inputs[1]["sha256"]
    # Mỗi query shard: một snapshot readonly, batches <=900; body không tích lũy toàn corpus.
    shards, counts, routes = [], Counter(), []
    unique_docs, unique_queries, distributions, cases = set(), set(), {}, []
    pools = iter(read_jsonl(pool_manifest["pool_path"]))
    batch = []
    def flush(batch, conn, index):
        ids = sorted({r["doc_id"] for p in batch for r in p["reference"]} |
                     {r["doc_id"] for p in batch for r in p["support"]["docs"]})
        documents = read_corpus_batch(conn, ids)
        refs = load_chunk_refs(conn, ids, corpus_hash)
        rows, chunk_rows, support_rows = [], [], []
        for pool in batch:
            qid = pool["query_id"]
            unique_queries.add(qid)
            if qid not in queries:
                raise SchemaInvalidError(f"Thiếu query {qid}")
            query = queries[qid]
            concepts = build_query_concepts(qid, query.query, query.entities)
            c_hash = compute_concept_set_hash(concepts)
            workset = list(dict.fromkeys([r["doc_id"] for r in pool["reference"]] +
                                        [r["doc_id"] for r in pool["support"]["docs"]]))
            per_doc = {}
            lookup = {r["doc_id"]: r for r in pool["reference"]}
            for doc in workset:
                unique_docs.add(doc)
                f = document_evidence(concepts, documents.get(doc, {}), refs.get(doc, []))
                for chunk in f.pop("chunk_features"):
                    chunk_rows.append({"query_id": qid, "doc_id": doc, **chunk})
                row = {"schema_version": 1, "query_id": qid, "doc_id": doc,
                       "pool_hash": pool["pool_hash"], "corpus_hash": corpus_hash,
                       "concept_set_hash": c_hash, "query_hash": inputs[2]["sha256"],
                       "feature_version": FEATURE_VERSION, "matcher_version": MATCHER_VERSION,
                       "config_hash": manifest["config_hash"], "parse_status": query.parse_status,
                       "lang": documents.get(doc, {}).get("lang"), **f,
                       "source_ranks": {k: r.get(doc) for k, r in pool["source_ranks"].items()},
                       "availability": {k: "ranked" if doc in r else pool["source_absence"][k]
                                        for k, r in pool["source_ranks"].items()}}
                per_doc[doc] = row
                counts["pair_count"] += 1
                counts[row["evidence_status"]] += 1
                counts["parse_" + query.parse_status] += 1
                rank = lookup.get(doc, {}).get("baseline_rank")
                rank_bin = "extras_support" if rank is None else ("1_40" if rank <= 40 else "41_120" if rank <= 120 else "121_200")
                language = row["lang"] or "unknown"
                counts[f"language_{language}"] += 1
                counts[f"mapping_incomplete_{language}"] += int(row["mapping_coverage"] != 1)
                for feature_name in ("body_coverage", "title_coverage", "local_max_all", "body_length", "chunk_count", "entity_count"):
                    key = language + "/" + rank_bin + "/" + feature_name
                    stat = distributions.setdefault(key, {"count": 0, "missing": 0, "sum": 0, "min": None, "max": None})
                    value = row[feature_name]
                    if value is None:
                        stat["missing"] += 1
                    else:
                        stat["count"] += 1
                        stat["sum"] += value
                        stat["min"] = value if stat["min"] is None else min(stat["min"], value)
                        stat["max"] = value if stat["max"] is None else max(stat["max"], value)
                if row["mapping_coverage"] != 1 and len(cases) < 20:
                    cases.append({"query_id": qid, "doc_id": doc, "reason": "mapping_or_entities_unavailable"})
                if doc in lookup:
                    row.update(lookup[doc])
                    rows.append(row)
                else:
                    support_rows.append(row | {"support_only": True})
            routes.append({"query_id": qid, **query_evidence(pool["support"], per_doc)})
        shard_paths = []
        for name, data in (("pairs", rows), ("chunks", chunk_rows), ("support", support_rows)):
            path = root / f"{name}_{index:04d}.jsonl"
            write_jsonl(path, data)
            shard_paths.append(path)
        shard_manifest = {"schema_version": 1, "status": "completed", "config_hash": manifest["config_hash"],
                          "row_count": len(rows), "unique_keys": len({(r['query_id'], r['doc_id']) for r in rows}),
                          "artifacts": [file_identity(p) for p in shard_paths]}
        path = root / f"shard_{index:04d}.json"
        atomic_write_json(path, shard_manifest)
        return [path, *shard_paths]
    with corpus_connection(cfg["corpus"]) as conn:
        for pool in pools:
            if selected is not None and pool["query_id"] not in selected:
                continue
            batch.append(pool)
            if len(batch) == batch_size:
                shards.extend(flush(batch, conn, len(shards) // 4))
                batch = []
        if batch:
            shards.extend(flush(batch, conn, len(shards) // 4))
    if selected is not None and unique_queries != selected:
        raise SchemaInvalidError("Pool thiếu query IDs đã freeze")
    route_path = write_jsonl(root / "routes.jsonl", routes)
    stats = dict(counts) | {"seconds": time.perf_counter() - started, "queries": len(routes),
                           "label_usage": "none", "sqlite_batch_limit": 900,
                           "unique_docs": len(unique_docs), "unique_queries": len(unique_queries),
                           "distributions": distributions, "error_cases": cases,
                           "peak_ram_bytes": None, "io_bytes": None,
                           "unmeasured_cost_fields": ["peak_ram_bytes", "io_bytes"]}
    atomic_write_json(root / "L0.json", stats)
    atomic_write_text(root / "L0.md", "# L0 diagnostics\n\n" + str(stats) + "\n\nKhông có quality claim.\n")
    return complete_run(root, manifest, [*shards, route_path, root / "L0.json", root / "L0.md"],
                        pair_paths=[str(p) for p in shards if p.name.startswith("pairs_")],
                        routes_path=str(route_path), pool_manifest=cfg["pool_manifest"])


def inference(cfg):
    from .fusion import rank_query
    if cfg["mode"] == "adaptive" and cfg.get("lambda", 0) != 0:
        from .contracts import InputMissingError
        raise InputMissingError("A1 production chưa mở: cần O0 dev headroom, controls và freeze best F0 theo T11; pure gate có fixture riêng")
    pool_manifest = verify_manifest(cfg["pool_manifest"])
    inputs = [file_identity(cfg["pool_manifest"])]
    features, routes = {}, {}
    bypass = cfg["mode"] == "baseline" or cfg.get("lambda", 0) == 0
    if not bypass:
        fm = verify_manifest(cfg.get("feature_manifest"))
        from .io import resolve_repo_path
        if resolve_repo_path(fm["pool_manifest"]) != resolve_repo_path(cfg["pool_manifest"]):
            raise SchemaInvalidError("Feature/pool manifest không cùng nguồn")
        inputs.append(file_identity(cfg["feature_manifest"]))
        for path in fm["pair_paths"]:
            for row in read_jsonl(path):
                features.setdefault(row["query_id"], {})[row["doc_id"]] = row
        routes = {r["query_id"]: r for r in read_jsonl(fm["routes_path"])}
    root, manifest, reused = start_run(cfg["output_dir"], cfg, inputs)
    if reused:
        return manifest
    candidates, details = [], []
    for pool in read_jsonl(pool_manifest["pool_path"]):
        qid = pool["query_id"]
        docs, explanation = rank_query(pool, features.get(qid, {}), cfg, routes.get(qid))
        candidates.append({"id": qid, "candidates": [{"doc_id": d, "score": len(docs)-i} for i, d in enumerate(docs)]})
        details.append({"query_id": qid, "pool_hash": pool["pool_hash"], **explanation})
    paths = [write_jsonl(root / "candidates.jsonl", candidates),
             write_jsonl(root / "ranking_details.jsonl", details)]
    return complete_run(root, manifest, paths, query_count=len(candidates), label_usage="none")
