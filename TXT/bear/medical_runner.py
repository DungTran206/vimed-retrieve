"""Runnable stages for the user's medical-importance gating experiment.

Inference never reads val labels. Preparation, feature collection, fitting and
selection are separate artifacts so numerical sweeps do not call an LLM again.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import itertools
import unicodedata
import time
from statistics import median
from pathlib import Path

from .contracts import SchemaInvalidError, validate_doc_id
from .io import (assert_valid_output_path, atomic_write_json, canonical_sha256,
                 read_json, read_jsonl, resolve_repo_path, write_jsonl)
from .medical_cache import (begin_stage, checked_records, finite, finish_stage,
                            iter_checked_records, merge_config, VERSION)

SCHEMAS = {
    "kb-import": ({"source_path", "format", "concept_map_path", "source", "allow_empty", "symptom_predicates"}, {"source_path"}),
    "prepare": ({"queries", "kb", "llm", "prepared_input"}, {"queries", "kb", "llm"}),
    "document-terms": ({"index", "doc_ids_path", "llm"}, {"index", "doc_ids_path", "llm"}),
    "cache": ({"prepared", "index", "sources", "score_tables", "bm25_source", "bm25_expanded_source",
               "dense_head_source", "dense_chunk_source", "languages", "include_index_candidates",
               "lookup_top_k", "expanded_top_k", "rrf_k", "rrf_weights"}, {"prepared", "index", "sources"}),
    "fit": ({"cache", "validation", "scoring", "split", "split_path", "fit_options"}, {"cache", "validation", "scoring"}),
    "tune": ({"cache", "validation", "model", "split_path", "trials", "grid", "objective",
              "max_mean_docs", "allow_incomplete_f2", "max_trials"}, {"cache", "validation", "model"}),
    "run": ({"cache", "model", "scoring", "mode", "query_ids"}, {"cache"}),
    "evaluate": ({"predictions", "validation", "split_path", "split", "query_ids", "allow_incomplete_f2"},
                 {"predictions", "validation"}),
}


def validate_stage(command, config):
    if command not in SCHEMAS:
        raise SchemaInvalidError(f"Unknown medical experiment stage: {command}")
    allowed, required = SCHEMAS[command]
    extra = set(config) - (allowed | {"schema_version", "output_dir"})
    missing = (required | {"schema_version", "output_dir"}) - set(config)
    if extra or missing or config.get("schema_version") != 1:
        raise SchemaInvalidError(f"{command}: unknown={sorted(extra)}, missing={sorted(missing)}; schema_version must be 1")
    if not isinstance(config["output_dir"], str):
        raise SchemaInvalidError("output_dir must be a path string")
    assert_valid_output_path(resolve_repo_path(config["output_dir"]))
    if command in {"prepare", "document-terms"}:
        from .medical_query import validate_llm_config
        validate_llm_config(config["llm"])
    if command == "cache":
        if not isinstance(config["sources"], dict) or not config["sources"] and not config.get("include_index_candidates", False):
            raise SchemaInvalidError("cache requires source rankings or include_index_candidates=true")
        for field in ("lookup_top_k", "expanded_top_k"):
            if type(config.get(field, 1000)) is not int or config.get(field, 1000) <= 0:
                raise SchemaInvalidError(f"{field} must be a positive integer")
        if not isinstance(config.get("languages", ["vi"]), list) or not config.get("languages", ["vi"]):
            raise SchemaInvalidError("languages must be a nonempty list")
    if command == "run" and config.get("mode", "medical") not in {"medical", "rrf"}:
        raise SchemaInvalidError("run.mode must be medical or rrf")
    return config


def _input_paths(command, config):
    single = {"kb-import": ("source_path", "concept_map_path"),
              "prepare": ("queries", "kb", "prepared_input"),
              "document-terms": ("index", "doc_ids_path"),
              "cache": ("prepared", "index"), "fit": ("cache", "validation", "split_path"),
              "tune": ("cache", "validation", "model", "split_path"),
              "run": ("cache", "model"), "evaluate": ("predictions", "validation", "split_path")}
    inputs = {key: config[key] for key in single[command] if config.get(key)}
    if command == "prepare":
        inputs["system_prompt"] = config["llm"].get("system_prompt_path", "TXT/prompts/medical_query_system.txt")
        inputs["user_prompt"] = config["llm"].get("user_prompt_path", "TXT/prompts/medical_query_user.txt")
    if command == "document-terms":
        inputs["document_prompt"] = config["llm"].get("document_prompt_path", "TXT/prompts/medical_document_terms.txt")
    if command == "cache":
        inputs.update({"source:" + key: path for key, path in config["sources"].items()})
        inputs.update({"score_table:" + key: path for key, path in config.get("score_tables", {}).items()})
    return inputs


def inspect_experiment(command, config):
    validate_stage(command, config)
    paths = _input_paths(command, config)
    missing = [key for key, path in paths.items() if not resolve_repo_path(path).is_file()]
    return {"status": "blocked_input" if missing else "inputs_present_unverified", "command": command,
            "dry_run": True, "missing_roles": missing, "output_dir": config["output_dir"],
            "implementation_version": VERSION, "hypothesis_only": True,
            "model_contacted": False, "baseline_0391_reproduced": False}


def _read_queries(path):
    rows = {}
    for row in read_jsonl(resolve_repo_path(path)):
        if set(row) & {"gold", "not_gold", "G", "gold_unseen", "qrels", "judgments"}:
            raise SchemaInvalidError("Inference queries must be label-free; use validation only in fit/tune/evaluate")
        qid = row.get("id")
        if type(qid) is not int or qid < 0 or qid in rows:
            raise SchemaInvalidError("Query IDs must be unique nonnegative integers")
        if not isinstance(row.get("query"), str) or not row["query"].strip():
            raise SchemaInvalidError(f"Query {qid} needs nonempty query text")
        rows[qid] = {"id": qid, "query": row["query"], "lang": row.get("lang", "vi")}
    if not rows:
        raise SchemaInvalidError("Query input is empty")
    return rows


def _prepare(config, root):
    from .medical_kb import load_kb
    from .medical_query import prepare_query, validate_prepared
    queries = _read_queries(config["queries"])
    kb = load_kb(resolve_repo_path(config["kb"]))
    imported = {}
    if config.get("prepared_input"):
        for record in checked_records(config["prepared_input"]):
            record = validate_prepared(record, kb_rows=kb)
            if record["id"] in imported:
                raise SchemaInvalidError("prepared_input contains duplicate query IDs")
            imported[record["id"]] = record
        if set(imported) != set(queries):
            raise SchemaInvalidError("prepared_input and queries must have the same query IDs")
    records, model_calls = [], 0
    for qid, query in sorted(queries.items()):
        response_path = root / "responses" / f"{qid}.json"
        if response_path.is_file():
            record = validate_prepared(read_json(response_path), kb_rows=kb)
        elif qid in imported:
            record = imported[qid]
        else:
            record = prepare_query(query, kb, config["llm"])
            model_calls += 1
        if record["id"] != qid or record["query"] != query["query"] or record["lang"] != query["lang"]:
            raise SchemaInvalidError(f"Cached/imported query differs from original: {qid}")
        atomic_write_json(response_path, record)
        records.append(record)
    output = write_jsonl(root / "prepared.jsonl", records)
    return [output, *sorted((root / "responses").glob("*.json"))], {"query_count": len(records),
            "enrichment_term_count": sum(len(row.get("expansion_terms", [])) for row in records),
            "resume_unit": "query", "model_contacted": model_calls > 0, "model_calls": model_calls}


def _rankings(path, universe):
    result = {}
    for row in read_jsonl(resolve_repo_path(path)):
        qid = row.get("id", row.get("query_id"))
        if type(qid) is not int or qid not in universe or qid in result:
            raise SchemaInvalidError(f"Ranking query IDs are duplicated or unexpected: {qid}")
        candidates = row.get("candidates")
        if not isinstance(candidates, list):
            raise SchemaInvalidError("Ranking rows require candidates:[{doc_id,score}]")
        docs = {}
        for rank, item in enumerate(candidates, 1):
            did = validate_doc_id(item["doc_id"])
            if did in docs:
                raise SchemaInvalidError(f"Duplicate ranked document: {qid}/{did}")
            docs[did] = {"score": finite(item["score"]) if item.get("score") is not None else None, "rank": rank}
        result[qid] = docs
    if set(result) != set(universe):
        raise SchemaInvalidError(f"Rankings must cover all queries; missing={sorted(set(universe) - set(result))}")
    return result


def _document_terms(config, root):
    from .corpus_index import CorpusIndex
    from .medical_documents import extract_document
    raw_ids = read_json(resolve_repo_path(config["doc_ids_path"]))
    if not isinstance(raw_ids, list):
        raise SchemaInvalidError("doc_ids_path must contain a JSON list of document IDs")
    ids = [validate_doc_id(value) for value in raw_ids]
    if len(ids) != len(set(ids)):
        raise SchemaInvalidError("document IDs must be unique")
    paths, model_calls = [], 0
    with CorpusIndex(resolve_repo_path(config["index"])) as index:
        for did in ids:
            # Use a digest for file names; external IDs may contain separators.
            output = root / "responses" / (canonical_sha256(did) + ".json")
            document = index.get_document(did)
            if document is None:
                raise SchemaInvalidError(f"Document {did} absent from corpus snapshot")
            if output.is_file():
                record = read_json(output)
                if record.get("doc_id") != did:
                    raise SchemaInvalidError("Resumed document ID differs from requested document")
            else:
                record = extract_document(document, config["llm"])
                atomic_write_json(output, record)
                model_calls += 1
            paths.append(output)
    combined = write_jsonl(root / "document_terms.jsonl", (read_json(path) for path in paths))
    return [combined, *paths], {"document_count": len(paths), "model_calls": model_calls,
                               "index_modified": False, "scope": "diagnostic_term_candidates_only"}


def _score_tables(tables, universe):
    result = {}
    for name, path in tables.items():
        if name not in {"bm25", "bm25_expanded", "dense_head", "dense_chunk"}:
            raise SchemaInvalidError(f"Unsupported score table: {name}")
        scores = {}
        for row in read_jsonl(resolve_repo_path(path)):
            qid, did = row.get("id", row.get("query_id")), validate_doc_id(row["doc_id"])
            key = (qid, did)
            if type(qid) is not int or qid not in universe or key in scores:
                raise SchemaInvalidError(f"Unexpected/duplicate score table key: {key}")
            scores[key] = finite(row["score"])
        result[name] = scores
    return result


def _cache(config, root):
    from .corpus_index import CorpusIndex
    from .medical_query import validate_prepared, match_concepts
    prepared = [validate_prepared(row) for row in checked_records(config["prepared"])]
    universe = {row["id"] for row in prepared}
    if len(universe) != len(prepared):
        raise SchemaInvalidError("Prepared queries contain duplicate IDs")
    sources = {name: _rankings(path, universe) for name, path in config["sources"].items()}
    tables = _score_tables(config.get("score_tables", {}), universe)
    allowed = set(config.get("languages", ["vi"]))
    source_keys = {name: config.get(name + "_source", name if name in sources else None)
                   for name in ("bm25", "bm25_expanded", "dense_head", "dense_chunk")}
    if any(name is not None and name not in sources for name in source_keys.values()):
        raise SchemaInvalidError("*_source must name an available ranking source")
    external_bm25 = source_keys["bm25"] is not None or "bm25" in tables
    rrf_k = finite(config.get("rrf_k", 60), "rrf_k")
    if rrf_k < 0:
        raise SchemaInvalidError("rrf_k must be nonnegative")
    counts, missing = {}, Counter()
    paths = []
    with CorpusIndex(resolve_repo_path(config["index"])) as index:
        for query in sorted(prepared, key=lambda row: row["id"]):
            qid = query["id"]
            query_path = root / "queries" / f"{qid}.json"
            if query_path.is_file():
                cached = read_json(query_path)
                counts[qid] = len(cached["candidates"])
                missing.update(field for candidate in cached["candidates"]
                               for field, observed in candidate["score_available"].items() if not observed)
                paths.append(query_path)
                continue
            original_scores, original_scale = index._lexical_scores(query["query"])
            expanded_text = query["query"] + " " + " ".join(term["text"] for term in query.get("expansion_terms", []))
            expanded_scores, expanded_scale = index._lexical_scores(expanded_text)
            union = set().union(*(set(rows[qid]) for rows in sources.values())) if sources else set()
            if config.get("include_index_candidates", False):
                for values, limit in ((original_scores, config.get("lookup_top_k", 1000)),
                                      (expanded_scores, config.get("expanded_top_k", 1000))):
                    eligible = (did for did in values if index.get_document(did)["lang"] in allowed)
                    union.update(sorted(eligible, key=lambda did: (-values[did], did))[:limit])
            candidates = []
            for did in sorted(union):
                document = index.get_document(did)
                if document is None:
                    raise SchemaInvalidError(f"Document {did} absent from corpus snapshot")
                if document["lang"] not in allowed:
                    continue
                scores = {}
                for field, source_name in source_keys.items():
                    scores[field] = sources[source_name][qid].get(did, {}).get("score") if source_name else None
                # Index scores are computed for every union doc, including true zero.
                # Baseline BM25F scores are never patched with a different BM25 recipe.
                if not external_bm25:
                    scores["bm25"] = original_scores.get(did, 0.0)
                if source_keys["bm25_expanded"] is None and not external_bm25:
                    scores["bm25_expanded"] = expanded_scores.get(did, 0.0)
                for field, values in tables.items():
                    if (qid, did) in values:
                        scores[field] = values[qid, did]
                masks = {field: value is not None for field, value in scores.items()}
                missing.update(field for field, observed in masks.items() if not observed)
                memberships = {name: rows[qid][did] for name, rows in sources.items() if did in rows[qid]}
                rrf = sum(finite(config.get("rrf_weights", {}).get(name, 1.0), "RRF weight") / (rrf_k + entry["rank"])
                          for name, entry in memberships.items())
                candidates.append({"doc_id": did, "lang": document["lang"], "scores": scores,
                                   "score_available": masks, "source_membership": memberships, "rrf_score": rrf,
                                   "concept_matches": match_concepts(query, document),
                                   "index_bm25_original": original_scores.get(did, 0.0),
                                   "index_bm25_expanded": expanded_scores.get(did, 0.0),
                                   "body_sha256": document["body_sha256"]})
            cached = {**query, "candidates": candidates, "query_scale": original_scale or 1.0,
                      "expanded_query_scale": expanded_scale or 1.0,
                      "bm25_recipe": "source_artifact" if external_bm25 else "bear_corpus_lexical_v1",
                      "query_scale_compatible": not external_bm25,
                      "candidate_scope": "source_union_plus_lexical" if config.get("include_index_candidates") else "source_union"}
            atomic_write_json(query_path, cached)
            counts[qid] = len(candidates)
            paths.append(query_path)
    output = write_jsonl(root / "cache.jsonl", (read_json(path) for path in paths))
    return [output, *paths], {"query_count": len(prepared), "counts": counts,
                             "candidate_count": sum(counts.values()), "missing_score_counts": dict(missing),
                             "score_absence_is_not_zero": True, "resume_unit": "query"}


def _load_scoring(config):
    model = read_json(resolve_repo_path(config["model"])) if config.get("model") else {}
    base = model.get("scoring", model.get("best_config", {}))
    return merge_config(base, config.get("scoring", {})), model


def _bm25_recipe(scoring):
    config = scoring.get("bm25", {})
    return {key: config.get(key, default) for key, default in
            (("pretransform", "raw"), ("enrichment_weight", 0.0), ("missing_expanded", "error"))}


def _feature_recipe(cache_path, records):
    """Bind a model to score generation, not to training query IDs or candidates."""
    producer = resolve_repo_path(cache_path).parent / "manifest.json"
    manifest = read_json(producer) if producer.is_file() else {}
    index = manifest.get("inputs", {}).get("index", {})
    return {"bm25_recipes": sorted({row.get("bm25_recipe", "imported_unspecified") for row in records}),
            "query_scale_compatible": sorted({row.get("query_scale_compatible", True) for row in records}),
            "index_sha256": index.get("sha256"),
            "languages": sorted({row.get("lang", "vi") for row in records}),
            "source_score_recipe": {key: manifest.get("config", {}).get(key) for key in
                                    ("bm25_source", "bm25_expanded_source", "dense_head_source", "dense_chunk_source")}}


def _cache_headers(path):
    """Retain query metadata only, never every document's cached spans in RAM."""
    keys = {"id", "query", "lang", "bm25_recipe", "query_scale_compatible"}
    headers, seen = [], set()
    for record in iter_checked_records(path):
        qid = record.get("id")
        if type(qid) is not int or qid in seen:
            raise SchemaInvalidError("Cache query IDs must be unique integers")
        seen.add(qid)
        headers.append({key: record[key] for key in keys if key in record})
    return headers


def _same_assignments(left, right):
    return all(sorted(left.get(name, [])) == sorted(right.get(name, []))
               for name in ("calibration", "tune", "holdout"))


def _calibration_matches(scoring, calibration):
    return bool(calibration) and all(scoring.get("bm25", {}).get(key) == calibration.get(key)
                                     for key in ("x0", "temperature"))


def _checked_split(split, records, labels):
    universe = {row["id"] for row in records}
    occupied, groups = set(), {}
    for name in ("calibration", "tune", "holdout"):
        ids = split.get(name)
        if not isinstance(ids, list) or not ids or any(type(qid) is not int for qid in ids) or len(ids) != len(set(ids)):
            raise SchemaInvalidError(f"Split {name} needs unique integer query IDs")
        if occupied & set(ids) or set(ids) - universe or set(ids) - set(labels):
            raise SchemaInvalidError(f"Split {name} overlaps or includes unavailable queries/judgments")
        occupied.update(ids)
        for row in records:
            if row["id"] in ids:
                label_query = labels[row["id"]].get("query", "")
                if label_query and label_query != row["query"]:
                    raise SchemaInvalidError(f"Validation query text differs from inference query: {row['id']}")
                text = " ".join(unicodedata.normalize("NFKC", row["query"]).casefold().split())
                key = text or str(row["id"])
                if key in groups and groups[key] != name:
                    raise SchemaInvalidError("Identical normalized queries cannot cross split boundaries")
                groups[key] = name
    return split


def _fit(config, root):
    from .medical_validation import load_validation, split_query_ids, calibration_samples, fit_sigmoid
    from .medical_scoring import validate_scoring_config
    records = _cache_headers(config["cache"])
    labels = load_validation(resolve_repo_path(config["validation"]))
    if config.get("split_path"):
        split = read_json(resolve_repo_path(config["split_path"]))
    else:
        split = split_query_ids([row for row in records if row["id"] in labels], **config.get("split", {}))
    _checked_split(split, records, labels)
    scoring = copy.deepcopy(config["scoring"])
    validate_scoring_config(scoring)
    samples = calibration_samples(iter_checked_records(config["cache"], verify=False), labels, split["calibration"], scoring)
    calibration = fit_sigmoid(samples, **config.get("fit_options", {}))
    scoring.setdefault("bm25", {}).update({key: calibration[key] for key in ("x0", "temperature")})
    split_path = atomic_write_json(root / "splits.json", split)
    model = {"implementation_version": VERSION, "scoring": scoring, "calibration": calibration,
             "bm25_recipe": _bm25_recipe(scoring), "split": split, "split_path": str(split_path),
             "feature_recipe": _feature_recipe(config["cache"], records),
             "calibration_query_ids": split["calibration"], "fit_options": config.get("fit_options", {}),
             "probability_scope": "judged candidates under the frozen cache/label sampling policy",
             "hypothesis_only": True, "quality_gain_established": False}
    model_path = atomic_write_json(root / "model.json", model)
    return [split_path, model_path], {"calibration_query_count": len(split["calibration"]),
                                     "sample_count": len(samples), "holdout_evaluated": False}


def _trial_configs(config, base):
    if "trials" in config and "grid" in config:
        raise SchemaInvalidError("Specify either trials or grid")
    if "trials" in config:
        if not isinstance(config["trials"], list):
            raise SchemaInvalidError("trials must be a list of scoring overrides")
        overrides = config["trials"]
    else:
        grid = config.get("grid", {"selection.threshold": [0.4, 0.5, 0.6]})
        if not isinstance(grid, dict) or any(not isinstance(values, list) or not values for values in grid.values()):
            raise SchemaInvalidError("grid maps dotted scoring paths to nonempty value lists")
        size = 1
        for values in grid.values():
            size *= len(values)
        if size > config.get("max_trials", 4096):
            raise SchemaInvalidError(f"Grid has {size} trials; narrow it or raise max_trials explicitly")
        overrides = []
        for combination in itertools.product(*grid.values()):
            override = {}
            for key, value in zip(grid, combination):
                parts = key.split(".")
                cursor = override
                for part in parts[:-1]:
                    cursor = cursor.setdefault(part, {})
                cursor[parts[-1]] = value
            overrides.append(override)
    if not overrides or len(overrides) > config.get("max_trials", 4096):
        raise SchemaInvalidError("Empty or excessively large trial menu")
    return [merge_config(copy.deepcopy(base), override) for override in overrides]


def _tune(config, root):
    from .medical_validation import load_validation, calibration_samples, fit_sigmoid, tune_configs
    records = _cache_headers(config["cache"])
    labels = load_validation(resolve_repo_path(config["validation"]))
    model = read_json(resolve_repo_path(config["model"]))
    split = read_json(resolve_repo_path(config["split_path"])) if config.get("split_path") else model["split"]
    _checked_split(split, records, labels)
    if not _same_assignments(split, model["split"]):
        raise SchemaInvalidError("Tuning split differs from the fitted model; start a new fit for the new split")
    if model.get("feature_recipe") != _feature_recipe(config["cache"], records):
        raise SchemaInvalidError("Tuning score-generation recipe differs from the fitted model")
    configs = _trial_configs(config, model["scoring"])
    calibrations, refits = [], {}
    for scoring in configs:
        if _bm25_recipe(scoring) != _bm25_recipe(model["scoring"]):
            # Changing enrichment mixing/normalization changes the score recipe.
            # Refit on calibration queries ONLY; no inference/model calls needed.
            recipe_key = canonical_sha256(_bm25_recipe(scoring))
            if recipe_key not in refits:
                samples = calibration_samples(iter_checked_records(config["cache"], verify=False), labels, split["calibration"], scoring)
                refits[recipe_key] = fit_sigmoid(samples, **model.get("fit_options", {}))
            calibration = refits[recipe_key]
            scoring["bm25"].update({key: calibration[key] for key in ("x0", "temperature")})
        else:
            calibration = model.get("calibration")
        calibrations.append(calibration)
    result = tune_configs(lambda: iter_checked_records(config["cache"], verify=False), labels, split["tune"], configs,
                          objective=config.get("objective", "known_positive_recall"),
                          max_mean_docs=config.get("max_mean_docs"),
                          allow_incomplete_f2=config.get("allow_incomplete_f2", False))
    winner = result["best_trial"]
    best = {"implementation_version": VERSION, "scoring": result["best_config"],
            "calibration": calibrations[winner], "bm25_recipe": _bm25_recipe(result["best_config"]),
            "split": split, "fit_options": model.get("fit_options", {}),
            "feature_recipe": model.get("feature_recipe"),
            "calibration_parameters_overridden": not _calibration_matches(result["best_config"], calibrations[winner]),
            "objective": result["objective"], "best_trial": winner, "best_metrics": result["best_metrics"],
            "tune_query_ids": split["tune"], "holdout_evaluated": False,
            "hypothesis_only": True, "quality_gain_established": False}
    best_path = atomic_write_json(root / "best_config.json", best)
    trials_path = write_jsonl(root / "trials.jsonl", result["trials"])
    summary_path = atomic_write_json(root / "tuning.json", {key: value for key, value in result.items() if key != "trials"})
    return [best_path, trials_path, summary_path], {"trial_count": result["trial_count"],
             "best_trial": winner, "tune_query_count": len(split["tune"]), "holdout_evaluated": False}


def _evaluate(config, root):
    from .medical_validation import load_validation, evaluate_rankings
    rows = iter_checked_records(config["predictions"])
    outputs = []
    for row in rows:
        if "candidates" in row:
            outputs.append({"id": row["id"], "doc_ids": [item["doc_id"] for item in row["candidates"]]})
        else:
            outputs.append({"id": row["id"], "doc_ids": row.get("doc_ids", row.get("selection", {}).get("doc_ids")),
                            "selection": row.get("selection", {})})
    labels = load_validation(resolve_repo_path(config["validation"]))
    split = read_json(resolve_repo_path(config["split_path"])) if config.get("split_path") else None
    split_name = config.get("split", "holdout") if split is not None else "all_predictions_retrospective"
    if split is not None and split_name not in {"calibration", "tune", "holdout"}:
        raise SchemaInvalidError("evaluate.split must be calibration, tune or holdout")
    if split is not None:
        assignments = [set(split.get(name, [])) for name in ("calibration", "tune", "holdout")]
        if any(assignments[i] & assignments[j] for i in range(3) for j in range(i + 1, 3)):
            raise SchemaInvalidError("Evaluation split assignments overlap")
    ids = config.get("query_ids", split[split_name] if split is not None else None)
    if split is not None and ids is not None and set(ids) - set(split[split_name]):
        raise SchemaInvalidError("query_ids must be contained in the selected split")
    result = evaluate_rankings(outputs, labels, ids, allow_incomplete_f2=config.get("allow_incomplete_f2", False))
    result.update(split=split_name, hypothesis_only=True, baseline_0391_reproduced=False,
                  official_chunk_or_final_metric=False,
                  holdout_pristine=split.get("holdout_pristine", False) if split else False,
                  exposure_status=split.get("exposure_status", "unknown") if split else "unknown")
    output = atomic_write_json(root / "evaluation.json", result)
    return [output], {"query_count": result["query_count"], "split": split_name,
                      "known_positive_recall": result["known_positive_recall"],
                      "macro_doc_f2": result["macro_doc_f2"]}


def _run(config, root):
    from .medical_scoring import score_record, select_ranked, validate_scoring_config
    records = _cache_headers(config["cache"])
    scoring, model = _load_scoring(config)
    validate_scoring_config(scoring)
    if model and _bm25_recipe(scoring) != _bm25_recipe(model.get("scoring", {})):
        raise SchemaInvalidError("BM25 recipe changed after fitting; use fit/tune to recalibrate that cached recipe")
    if model.get("feature_recipe") and model["feature_recipe"] != _feature_recipe(config["cache"], records):
        raise SchemaInvalidError("Score-generation recipe differs from fitted model; fit a new calibration")
    selected_ids = set(config["query_ids"]) if config.get("query_ids") is not None else {row["id"] for row in records}
    if selected_ids - {row["id"] for row in records}:
        raise SchemaInvalidError("run.query_ids includes IDs outside the cache")
    counts = []
    def scored_rows():
        for record in iter_checked_records(config["cache"], verify=False):
            if record["id"] not in selected_ids:
                continue
            if config.get("mode", "medical") == "rrf":
                ranking = sorted(({"doc_id": candidate["doc_id"], "score": candidate["rrf_score"],
                                   "fused_score": candidate["rrf_score"]} for candidate in record["candidates"]),
                                 key=lambda item: (-item["score"], item["doc_id"]))
                selection_cfg = merge_config(scoring.get("selection", {}), {"mode": "top_k"})
                selection = select_ranked(ranking, record["concepts"], selection_cfg)
                result = {"id": record["id"], "query": record["query"], "ranking": ranking,
                          "selection": selection, "doc_ids": selection["doc_ids"], "score_schema": "rrf_control"}
            else:
                result = score_record(record, scoring)
            counts.append(len(result["doc_ids"]))
            yield result
    scores_path = write_jsonl(root / "scores.jsonl", scored_rows())
    def selected_rows():
        for result in read_jsonl(scores_path):
            lookup = {item["doc_id"]: item["score"] for item in result["ranking"]}
            yield {"id": result["id"], "candidates": [{"doc_id": did, "score": lookup[did]} for did in result["doc_ids"]]}
    candidates_path = write_jsonl(root / "candidates.jsonl", selected_rows())
    scoring_path = atomic_write_json(root / "scoring.json", scoring)
    return [scores_path, candidates_path, scoring_path], {"query_count": len(counts),
             "mean_docs": sum(counts) / len(counts) if counts else 0, "mode": config.get("mode", "medical"),
             "median_docs": median(counts) if counts else 0,
             "p95_docs": sorted(counts)[(95 * len(counts) + 99) // 100 - 1] if counts else 0,
             "max_docs": max(counts, default=0), "cache_streamed_by_query": True,
             "candidate_scores_are_not_downstream_p_hat": True, "labels_read": False,
             "calibration_fitted": _calibration_matches(scoring, model.get("calibration")),
             "calibration_parameters_overridden": bool(model.get("calibration")) and not _calibration_matches(scoring, model.get("calibration"))}


def run_experiment(command, config):
    started = time.perf_counter()
    validate_stage(command, config)
    preflight = inspect_experiment(command, config)
    if preflight["missing_roles"]:
        return preflight
    dependencies = ["TXT/bear/medical_runner.py", "TXT/bear/medical_cache.py", "TXT/bear/io.py"]
    dependencies += {"kb-import": ["TXT/bear/medical_kb.py"],
                     "prepare": ["TXT/bear/medical_kb.py", "TXT/bear/medical_query.py"],
                     "document-terms": ["TXT/bear/medical_documents.py", "TXT/bear/medical_query.py"],
                     "cache": ["TXT/bear/medical_query.py", "TXT/bear/corpus_index.py", "TXT/bear/structured_evidence.py"],
                     "fit": ["TXT/bear/medical_scoring.py", "TXT/bear/medical_validation.py"],
                     "tune": ["TXT/bear/medical_scoring.py", "TXT/bear/medical_validation.py"],
                     "run": ["TXT/bear/medical_scoring.py"],
                     "evaluate": ["TXT/bear/medical_validation.py"]}[command]
    root, manifest, reused = begin_stage(command, config, _input_paths(command, config), dependencies)
    if reused:
        return {**manifest, "reused": True}
    if command == "kb-import":
        from .medical_kb import import_kb
        rows = import_kb(config)
        output = write_jsonl(root / "kb.jsonl", rows)
        artifacts, details = [output], {"relation_count": len(rows), "clinical_cleanliness_verified": False}
    else:
        runner = {"prepare": _prepare, "cache": _cache, "run": _run,
                  "document-terms": _document_terms,
                  "fit": _fit, "tune": _tune, "evaluate": _evaluate}[command]
        artifacts, details = runner(config, root)
    return finish_stage(root, manifest, artifacts, elapsed_seconds=time.perf_counter() - started, **details)
