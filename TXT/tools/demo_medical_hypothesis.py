"""Synthetic end-to-end replay; not medical data or evidence of a quality gain."""
from __future__ import annotations

from pathlib import Path
import hashlib

from TXT.bear.corpus_index import build_index
from TXT.bear.io import assert_valid_output_path, atomic_write_json, read_json, resolve_repo_path, write_jsonl
from TXT.bear.medical_runner import run_experiment
from TXT.bear.medical_semantic import validate_encoder_config


def run_demo(output_dir="TXT/runtime/medical_hypothesis_demo"):
    root = assert_valid_output_path(resolve_repo_path(output_dir))
    fixtures = root / "synthetic_inputs"
    queries, kb, prepared, documents, labels = [], [], [], [], []
    sources = {name: [] for name in ("bm25", "dense_head", "dense_chunk")}
    for qid in range(1, 13):
        name, symptom = f"bệnh thử {qid}", f"biểu hiện giả lập {qid}"
        text = f"Triệu chứng của {name} là gì?"
        queries.append({"id": qid, "query": text, "lang": "vi"})
        disease = {"concept_id": f"synthetic:disease:{qid}", "labels": {"vi": name, "zh": f"测试病{qid}"},
                   "aliases": {"vi": [], "zh": []}}
        manifestation = {"concept_id": f"synthetic:symptom:{qid}", "labels": {"vi": symptom},
                         "aliases": {"vi": [], "zh": []}}
        kb.append({"disease": disease, "symptom": manifestation, "relation": "has_symptom",
                   "source": {"name": "SYNTHETIC_SOFTWARE_FIXTURE", "record_id": str(qid)}})
        start = text.index(name)
        prepared.append({"schema_version": 1, "id": qid, "query": text, "lang": "vi", "intent": ["symptoms"],
                         "concepts": [{"concept_id": disease["concept_id"], "text": name, "kind": "disease",
                                       "origin": "query", "tier": 4 if qid % 2 else 2, "required": False,
                                       "probabilities": None, "aliases": {"vi": [name], "zh": []},
                                       "anchor": {"start": start, "end": start + len(name)}}],
                         "expansion_terms": [], "metadata": {"synthetic": True, "model_contacted": False}})
        ids = [str(qid * 10 + offset) for offset in (1, 2, 3)]
        documents.extend([
            {"doc_id": ids[0], "lang": "vi", "title": f"Triệu chứng {name}",
             "body": f"Triệu chứng của {name}: {symptom}. Nội dung giả lập phần mềm. {name} có mục triệu chứng."},
            {"doc_id": ids[1], "lang": "vi", "title": "Thông tin chung", "body": f"Thông tin tổng quát về {name}."},
            {"doc_id": ids[2], "lang": "vi", "title": "Chủ đề khác", "body": "Văn bản nền không nêu bệnh đang tìm."}])
        labels.append({"id": qid, "query": text, "qrels": {ids[0]: 1, ids[1]: 0, ids[2]: 0},
                       "total_gold": 1, "complete": True})
        for field, scores in (("bm25", (9.0, 3.0, 0.0)), ("dense_head", (0.80, 0.85, 0.15)),
                              ("dense_chunk", (0.93, 0.50, 0.10))):
            pairs = sorted(zip(ids, scores), key=lambda pair: (-pair[1], pair[0]))
            sources[field].append({"id": qid, "candidates": [{"doc_id": did, "score": value} for did, value in pairs]})
    paths = {name: fixtures / f"{name}.jsonl" for name in ("queries", "kb", "prepared", "corpus", "validation")}
    for name, rows in (("queries", queries), ("kb", kb), ("prepared", prepared), ("corpus", documents), ("validation", labels)):
        write_jsonl(paths[name], rows)
    source_paths = {}
    for name, rows in sources.items():
        source_paths[name] = str(write_jsonl(fixtures / f"{name}.jsonl", rows))
    index_path = fixtures / "index.sqlite"
    if not index_path.exists():
        build_index(paths["corpus"], index_path)
    # These vectors and the revision marker are explicit software fixtures,
    # never represented as outputs from a real SapBERT checkpoint/tokenizer.
    encoder = validate_encoder_config({"revision": "a" * 40})
    term_records, vectors = [], {}
    for document in documents:
        qid = int(document["doc_id"]) // 10
        name = f"bệnh thử {qid}"
        term = name if name in document["body"] else "Văn bản"
        start = document["body"].index(term)
        vectors[term] = [1.0, 0.0] if term == name else [0.0, 1.0]
        term_records.append({"schema_version": 1, "doc_id": document["doc_id"], "lang": "vi",
                             "title_sha256": hashlib.sha256(document["title"].encode("utf-8")).hexdigest(),
                             "body_sha256": hashlib.sha256(document["body"].encode("utf-8")).hexdigest(),
                             "truncated": False,
                             "windows": [{"field": "title", "start": 0, "end": len(document["title"]),
                                          "original_length": len(document["title"])},
                                         {"field": "body", "start": 0, "end": len(document["body"]),
                                          "original_length": len(document["body"])}],
                             "terms": [{"text": term, "field": "body", "kind": "disease" if term == name else "other",
                                        "assertion": "affirmed", "origin": "document_literal",
                                        "anchor": {"start": start, "end": start + len(term)}}],
                             "metadata": {"synthetic": True, "model_contacted": False}})
    terms_path = write_jsonl(fixtures / "document_terms.jsonl", term_records)
    embeddings_path = write_jsonl(fixtures / "embeddings.jsonl", [
        {"text": text, "embedding": vector, "encoder": encoder,
         "provenance": {"synthetic": True, "method": "software_fixture_not_model_output"},
         "token_count": len(text.split()) + 2, "truncated": False}
        for text, vector in sorted(vectors.items())])
    scoring = {"tier_scores": [0.05, 0.30, 0.70, 1.0], "tier_mode": "hard", "required_cap": True,
               "alpha_min": 0.1, "alpha_max": 0.85, "dense_floor": 0.1,
               "bm25": {"pretransform": "query_scale", "x0": 0.3, "temperature": 0.15,
                        "enrichment_weight": 0.0, "missing_expanded": "error"},
               "dense": {"head_weight": 0.5, "chunk_weight": 0.5,
                         "head": {"method": "affine", "low": -1, "high": 1},
                         "chunk": {"method": "affine", "low": -1, "high": 1}},
               "sapbert": {"weight": 0.3, "method": "affine", "low": 0.2, "high": 0.9},
               "missing_scores": "available", "allow_bm25_only": False,
               "selection": {"mode": "threshold", "threshold": 0.5, "thresholds_by_tier": {},
                             "min_docs": 0, "max_docs": 3, "top_k": 2}}
    stages = {
        "kb-import": {"source_path": str(paths["kb"]), "format": "canonical", "output_dir": str(root / "kb")},
        "prepare": {"queries": str(paths["queries"]), "kb": str(root / "kb" / "kb.jsonl"),
                    "llm": {"model": "Qwen/Qwen3.5-9B", "num_parameters_b": 9},
                    "prepared_input": str(paths["prepared"]), "output_dir": str(root / "prepare")},
        "cache": {"prepared": str(root / "prepare" / "prepared.jsonl"), "index": str(index_path),
                  "sources": source_paths, "bm25_source": None, "bm25_expanded_source": None,
                  "dense_head_source": "dense_head", "dense_chunk_source": "dense_chunk",
                  "languages": ["vi"], "include_index_candidates": False, "output_dir": str(root / "cache")},
        "sapbert-cache": {"cache": str(root / "cache" / "cache.jsonl"), "index": str(index_path),
                          "document_terms": str(terms_path), "embeddings_input": str(embeddings_path),
                          "encoder": encoder, "output_dir": str(root / "sapbert_cache")},
        "fit": {"cache": str(root / "sapbert_cache" / "cache.jsonl"), "validation": str(paths["validation"]),
                "scoring": scoring, "split": {"seed": 391, "calibration_fraction": 0.4, "tune_fraction": 0.4,
                                              "exposure_status": "recorded", "previously_observed_ids": []},
                "output_dir": str(root / "fit")},
        "tune": {"cache": str(root / "sapbert_cache" / "cache.jsonl"), "validation": str(paths["validation"]),
                 "model": str(root / "fit" / "model.json"), "objective": "macro_doc_f2", "max_mean_docs": 2,
                 "grid": {"selection.threshold": [0.4, 0.6, 0.8], "alpha_max": [0.6, 0.85],
                          "sapbert.weight": [0.0, 0.3, 1.0]},
                 "output_dir": str(root / "tune")},
        "run": {"cache": str(root / "sapbert_cache" / "cache.jsonl"), "model": str(root / "tune" / "best_config.json"),
                "output_dir": str(root / "run")},
        "evaluate": {"predictions": str(root / "run" / "scores.jsonl"), "validation": str(paths["validation"]),
                     "split_path": str(root / "fit" / "splits.json"), "split": "holdout", "output_dir": str(root / "evaluate")}}
    outcomes = {}
    for command, options in stages.items():
        config = {"schema_version": 1, **options}
        atomic_write_json(root / "configs" / f"{command}.json", config)
        result = run_experiment(command, config)
        outcomes[command] = {"status": result["status"], "reused": result.get("reused", False)}
    rrf_config = {"schema_version": 1, **stages["run"], "mode": "rrf", "output_dir": str(root / "rrf_control")}
    run_experiment("run", rrf_config)
    summary = {"status": "completed", "synthetic_only": True, "real_model_called": False,
               "real_medical_data_used": False, "baseline_0391_reproduced": False,
               "quality_gain_established": False, "query_count": len(queries), "stages": outcomes,
               "holdout_metrics": read_json(root / "evaluate" / "evaluation.json"),
               "output_dir": str(root)}
    atomic_write_json(root / "demo_summary.json", summary)
    return summary


if __name__ == "__main__":
    from TXT.bear.io import canonical_json_dumps
    print(canonical_json_dumps(run_demo()))
