"""Cached medical-importance gating, calibrated score fusion and selection.

This is an experimental, independent path.  Taxonomy scores control the lexical
weight; they are NOT an extra additive LLM relevance feature.  No labels or LLM
calls are consumed by this module, so cached features can be replayed cheaply.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

DEFAULT_TIER_SCORES = (0.05, 0.30, 0.70, 1.0)


def _config_fields(config: Mapping[str, Any], allowed: set[str], name: str) -> None:
    if not isinstance(config, Mapping):
        raise ValueError(f"{name} must be an object")
    extra = set(config) - allowed
    if extra:
        raise ValueError(f"{name} has unknown keys: {sorted(map(str, extra))}")


def validate_scoring_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
    """Fail on typos even when the corresponding branch has no candidates.

    This validates the public replay config, not calibration diagnostic objects.
    The lower-level normalize_bm25 function intentionally also accepts a complete
    fit_sigmoid result so callers can inspect a fitted model directly.
    """
    _config_fields(config, {"tier_scores", "tier_mode", "required_cap", "alpha_min", "alpha_max",
                           "dense_floor", "bm25", "dense", "missing_scores", "allow_bm25_only",
                           "selection"}, "scoring")
    tiers = config.get("tier_scores", DEFAULT_TIER_SCORES)
    if not isinstance(tiers, (list, tuple)) or len(tiers) != 4:
        raise ValueError("tier_scores must contain four numbers")
    tiers = [unit(value, "tier score") for value in tiers]
    if any(a > b for a, b in zip(tiers, tiers[1:])):
        raise ValueError("tier_scores must be nondecreasing")
    if config.get("tier_mode", "hard") not in {"hard", "expected"}:
        raise ValueError("tier_mode must be hard or expected")
    for key in ("required_cap", "allow_bm25_only"):
        if key in config and type(config[key]) is not bool:
            raise ValueError(f"{key} must be a boolean")
    _alpha_limits(config)
    if config.get("missing_scores", "available") not in {"available", "error"}:
        raise ValueError("missing_scores must be available or error")
    bm25 = config.get("bm25", {})
    _config_fields(bm25, {"pretransform", "x0", "temperature", "enrichment_weight", "missing_expanded"}, "scoring.bm25")
    if bm25.get("pretransform", "raw") not in {"raw", "query_scale"}:
        raise ValueError("bm25.pretransform must be raw or query_scale")
    finite(bm25.get("x0", 0.0), "bm25.x0")
    if finite(bm25.get("temperature", 1.0), "bm25.temperature") <= 0:
        raise ValueError("bm25.temperature must be positive")
    unit(bm25.get("enrichment_weight", 0.0), "bm25.enrichment_weight")
    if bm25.get("missing_expanded", "error") not in {"error", "original"}:
        raise ValueError("bm25.missing_expanded must be error or original")
    dense = config.get("dense", {})
    _config_fields(dense, {"head_weight", "chunk_weight", "head", "chunk"}, "scoring.dense")
    weights = [unit(dense.get(f"{part}_weight", 0.5), f"dense.{part}_weight") for part in ("head", "chunk")]
    if sum(weights) == 0:
        raise ValueError("at least one dense source needs positive weight")
    for part in ("head", "chunk"):
        normalizer = dense.get(part, {})
        if not isinstance(normalizer, Mapping):
            raise ValueError(f"dense.{part} must be an object")
        method = normalizer.get("method", "affine")
        if method == "affine":
            _config_fields(normalizer, {"method", "low", "high"}, f"scoring.dense.{part}")
            low = finite(normalizer.get("low", -1.0), f"dense.{part}.low")
            high = finite(normalizer.get("high", 1.0), f"dense.{part}.high")
            if high <= low:
                raise ValueError(f"dense.{part}.high must exceed low")
        elif method == "sigmoid":
            _config_fields(normalizer, {"method", "x0", "temperature"}, f"scoring.dense.{part}")
            finite(normalizer.get("x0", 0.0), f"dense.{part}.x0")
            if finite(normalizer.get("temperature", 1.0), f"dense.{part}.temperature") <= 0:
                raise ValueError(f"dense.{part}.temperature must be positive")
        else:
            raise ValueError(f"dense.{part}.method must be affine or sigmoid")
    selection = config.get("selection", {})
    _config_fields(selection, {"mode", "threshold", "thresholds_by_tier", "min_docs", "max_docs", "top_k"}, "scoring.selection")
    if selection.get("mode", "threshold") not in {"threshold", "top_k"}:
        raise ValueError("selection.mode must be threshold or top_k")
    unit(selection.get("threshold", 0.5), "selection.threshold")
    thresholds = selection.get("thresholds_by_tier", {})
    if not isinstance(thresholds, Mapping):
        raise ValueError("thresholds_by_tier must be an object")
    canonical_keys = [str(key) for key in thresholds]
    if len(set(canonical_keys)) != len(canonical_keys) or any(key not in {"0", "1", "2", "3", "4"} for key in canonical_keys):
        raise ValueError("thresholds_by_tier needs unique tier keys 0..4")
    for value in thresholds.values():
        unit(value, "tier threshold")
    for key, default in (("min_docs", 0), ("max_docs", 300), ("top_k", 300)):
        value = selection.get(key, default)
        if type(value) is not int or value < 0:
            raise ValueError(f"selection.{key} must be a nonnegative integer")
    if selection.get("min_docs", 0) > selection.get("max_docs", 300):
        raise ValueError("selection.min_docs cannot exceed max_docs")
    return config


def finite(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return float(value)


def unit(value: Any, name: str) -> float:
    value = finite(value, name)
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be in [0, 1]")
    return value


def sigmoid(value: float) -> float:
    """Numerically stable logistic, including extreme finite scores."""
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def pretransform_bm25(raw: float, config: Mapping[str, Any], query_scale: float = 1.0, *,
                      query_scale_compatible: bool = True) -> float:
    value = finite(raw, "bm25")
    method = config.get("pretransform", "raw")
    if method == "raw":
        return value
    if method == "query_scale":
        if query_scale_compatible is False:
            raise ValueError("query_scale pretransform cannot divide external BM25 scores by an unrelated index scale; use raw or provide compatible source-derived scaling")
        scale = finite(query_scale, "query_scale")
        if scale <= 0:
            raise ValueError("query_scale must be positive")
        return value / scale
    raise ValueError("bm25.pretransform must be raw or query_scale")


def blended_bm25(scores: Mapping[str, Any], config: Mapping[str, Any]) -> tuple[float | None, list[str]]:
    """Mix original/expanded RAW scores with a fixed query recipe before calibration.

    Expansion recipe/index changes require new cached retrieval and calibration.
    Missing expanded scores never silently become zero.
    """
    weight = unit(config.get("enrichment_weight", 0.0), "bm25.enrichment_weight")
    missing_policy = config.get("missing_expanded", "error")
    if missing_policy not in ("error", "original"):
        raise ValueError("bm25.missing_expanded must be error or original")
    original = scores.get("bm25")
    expanded = scores.get("bm25_expanded")
    flags: list[str] = []
    if original is not None:
        original = finite(original, "bm25")
    if expanded is not None:
        expanded = finite(expanded, "bm25_expanded")
    if weight == 0:
        return original, flags
    if expanded is None:
        if missing_policy == "error":
            raise ValueError("expanded BM25 is required by enrichment_weight")
        return original, ["expanded_bm25_missing_used_original"]
    if weight == 1:
        return expanded, flags
    if original is None:
        return None, ["original_bm25_missing_for_blend"]
    return (1 - weight) * original + weight * expanded, flags


def normalize_bm25(raw: float, config: Mapping[str, Any], query_scale: float = 1.0, *,
                    query_scale_compatible: bool = True) -> float:
    x0 = finite(config.get("x0", 0.0), "bm25.x0")
    temperature = finite(config.get("temperature", 1.0), "bm25.temperature")
    if temperature <= 0:
        raise ValueError("bm25.temperature must be positive")
    return sigmoid((pretransform_bm25(raw, config, query_scale,
                                    query_scale_compatible=query_scale_compatible) - x0) / temperature)


def normalize_dense(raw: float, config: Mapping[str, Any]) -> float:
    value = finite(raw, "dense score")
    method = config.get("method", "affine")
    if method == "affine":
        low = finite(config.get("low", -1.0), "dense.low")
        high = finite(config.get("high", 1.0), "dense.high")
        if high <= low:
            raise ValueError("dense.high must exceed dense.low")
        return min(1.0, max(0.0, (value - low) / (high - low)))
    if method == "sigmoid":
        temperature = finite(config.get("temperature", 1.0), "dense.temperature")
        if temperature <= 0:
            raise ValueError("dense.temperature must be positive")
        return sigmoid((value - finite(config.get("x0", 0.0), "dense.x0")) / temperature)
    raise ValueError("dense method must be affine or sigmoid")


def importance(concept: Mapping[str, Any], config: Mapping[str, Any]) -> float:
    scores = config.get("tier_scores", DEFAULT_TIER_SCORES)
    if len(scores) != 4:
        raise ValueError("tier_scores needs four values")
    scores = [unit(value, "tier score") for value in scores]
    if any(a > b for a, b in zip(scores, scores[1:])):
        raise ValueError("tier_scores must be nondecreasing")
    tier = concept.get("tier")
    if isinstance(tier, bool) or not isinstance(tier, int) or not 1 <= tier <= 4:
        raise ValueError("concept tier must be an integer from 1 to 4")
    mode = config.get("tier_mode", "hard")
    if mode == "hard":
        return scores[tier - 1]
    if mode != "expected":
        raise ValueError("tier_mode must be hard or expected")
    probabilities = concept.get("probabilities")
    if not isinstance(probabilities, (list, tuple)) or len(probabilities) != 4:
        raise ValueError("expected mode requires four label probabilities per concept")
    if (concept.get("probability_method") not in {"backend_label_logits", "backend_label_probabilities"}
            or not isinstance(concept.get("probability_provenance"), dict)
            or not concept["probability_provenance"]):
        raise ValueError("expected mode requires actual backend label probabilities/logits and nonempty probability_provenance; self-reported confidence is not accepted")
    probabilities = [unit(value, "tier probability") for value in probabilities]
    if not math.isclose(sum(probabilities), 1.0, abs_tol=1e-5):
        raise ValueError("tier probabilities must sum to one")
    return sum(p * score for p, score in zip(probabilities, scores))


def medical_gate(concepts: Sequence[Mapping[str, Any]], matches: Sequence[Mapping[str, Any]],
                 config: Mapping[str, Any]) -> dict[str, Any]:
    """Absolute salience survives full coverage: one tier-1 match gives G=.05.

    Concept IDs identify alias groups.  Each query concept occurs exactly once;
    multiple document matches for that ID use max match rather than adding votes.
    Enrichment-only concepts cannot manufacture original-query requirements.
    """
    originals = [concept for concept in concepts if concept.get("origin") == "query"]
    identities = [concept.get("concept_id") for concept in originals]
    if any(not isinstance(identity, str) or not identity for identity in identities):
        raise ValueError("original concepts require nonempty concept_id strings")
    if len(set(identities)) != len(identities):
        raise ValueError("query concept_id must be unique; group aliases before gating")
    found: dict[str, float] = {}
    for match in matches:
        identity = match.get("concept_id")
        value = unit(match.get("match"), "concept match")
        found[identity] = max(found.get(identity, 0.0), value)
    details = []
    denominator = 0.0
    numerator = 0.0
    required_matches = []
    for concept in originals:
        salience = importance(concept, config)
        matched = found.get(concept["concept_id"], 0.0)
        denominator += salience
        numerator += salience * salience * matched
        if concept.get("required", False):
            required_matches.append(matched)
        details.append({"concept_id": concept["concept_id"], "importance": salience,
                        "match": matched, "required": bool(concept.get("required", False))})
    gate = numerator / denominator if denominator else 0.0
    uncapped = gate
    if config.get("required_cap", True) and required_matches:
        gate = min(gate, min(required_matches))
    return {"gate": gate, "uncapped_gate": uncapped, "concepts": details,
            "original_concept_count": len(originals), "missing_original_concepts": not originals,
            "max_original_tier": max((c["tier"] for c in originals), default=0)}


def _alpha_limits(config: Mapping[str, Any]) -> tuple[float, float]:
    lower = unit(config.get("alpha_min", 0.1), "alpha_min")
    upper = unit(config.get("alpha_max", 0.85), "alpha_max")
    dense_floor = unit(config.get("dense_floor", 0.1), "dense_floor")
    if lower > upper or upper > 1 - dense_floor + 1e-12:
        raise ValueError("require alpha_min <= alpha_max <= 1 - dense_floor")
    return lower, upper


def score_candidate(record: Mapping[str, Any], candidate: Mapping[str, Any],
                    config: Mapping[str, Any]) -> dict[str, Any]:
    missing_policy = config.get("missing_scores", "available")
    if missing_policy not in ("available", "error"):
        raise ValueError("missing_scores must be available or error")
    lower, upper = _alpha_limits(config)
    scores = candidate.get("scores", {})
    bm25_config = config.get("bm25", {})
    raw_bm25, flags = blended_bm25(scores, bm25_config)
    normalized_bm25 = (None if raw_bm25 is None else normalize_bm25(
        raw_bm25, bm25_config, record.get("query_scale", 1.0),
        query_scale_compatible=record.get("query_scale_compatible", True)))
    gate = medical_gate(record.get("concepts", []), candidate.get("concept_matches", []), config)
    alpha = lower + (upper - lower) * gate["gate"]
    dense_config = config.get("dense", {})
    dense_sum = 0.0
    dense_weight = 0.0
    dense_components: dict[str, Any] = {}
    missing = []
    if normalized_bm25 is None:
        missing.append("bm25")
    for short, source in (("head", "dense_head"), ("chunk", "dense_chunk")):
        weight = unit(dense_config.get(f"{short}_weight", 0.5), f"dense.{short}_weight")
        if not weight:
            continue
        value = scores.get(source)
        if value is None:
            missing.append(source)
            dense_components[source] = None
            continue
        normalized = normalize_dense(value, dense_config.get(short, {}))
        dense_components[source] = normalized
        dense_sum += weight * normalized
        dense_weight += weight
    if dense_config.get("head_weight", 0.5) == 0 and dense_config.get("chunk_weight", 0.5) == 0:
        raise ValueError("at least one dense source needs positive weight")
    if missing and missing_policy == "error":
        raise ValueError(f"missing enabled scores for {candidate.get('doc_id')}: {missing}")
    dense = dense_sum / dense_weight if dense_weight else None
    if dense is None:
        if normalized_bm25 is None:
            raise ValueError(f"no retrieval scores for {candidate.get('doc_id')}")
        if not config.get("allow_bm25_only", False):
            raise ValueError("all dense scores missing; enable allow_bm25_only explicitly")
        fused = normalized_bm25
        effective_alpha = 1.0
        flags.append("bm25_only_explicit")
    elif normalized_bm25 is None:
        fused = dense
        effective_alpha = 0.0
        flags.append("dense_only_missing_bm25")
    else:
        fused = alpha * normalized_bm25 + (1 - alpha) * dense
        effective_alpha = alpha
    if missing:
        flags.append("available_source_weights_renormalized")
    identity = candidate.get("doc_id")
    if not isinstance(identity, str) or not identity:
        raise ValueError("candidate.doc_id must be a nonempty string")
    return {"doc_id": identity, "lang": candidate.get("lang"), "score": fused,
            "fused_score": fused, "bm25_raw_blend": raw_bm25,
            "bm25_normalized": normalized_bm25, "dense_normalized": dense,
            "dense_components": dense_components, "alpha_requested": alpha,
            "alpha_effective": effective_alpha, "medical_gate": gate,
            "missing_scores": missing, "flags": flags,
            "rrf_score": candidate.get("rrf_score")}


def select_ranked(ranking: Sequence[Mapping[str, Any]], concepts: Sequence[Mapping[str, Any]],
                  config: Mapping[str, Any]) -> dict[str, Any]:
    """Apply an inference-only threshold AFTER sorting, then explicit budget guards."""
    mode = config.get("mode", "threshold")
    maximum = config.get("max_docs", 300)
    minimum = config.get("min_docs", 0)
    for key, value in (("max_docs", maximum), ("min_docs", minimum)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"selection.{key} must be a nonnegative integer")
    if minimum > maximum:
        raise ValueError("selection.min_docs cannot exceed max_docs")
    bucket = max((concept["tier"] for concept in concepts if concept.get("origin") == "query"), default=0)
    ordered = sorted(ranking, key=lambda item: (-finite(item.get("fused_score", item.get("score")), "fusion score"), str(item["doc_id"])))
    threshold = None
    fallback_count = 0
    clipped = 0
    if mode == "top_k":
        top_k = config.get("top_k", maximum)
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 0:
            raise ValueError("selection.top_k must be a nonnegative integer")
        eligible = ordered[:top_k]
    elif mode == "threshold":
        thresholds = config.get("thresholds_by_tier", {})
        if not isinstance(thresholds, Mapping) or any(str(key) not in {"0", "1", "2", "3", "4"} for key in thresholds):
            raise ValueError("thresholds_by_tier keys must be 0..4")
        for value in thresholds.values():
            unit(value, "tier threshold")
        threshold = unit(thresholds.get(str(bucket), thresholds.get(bucket, config.get("threshold", 0.5))), "threshold")
        eligible = [item for item in ordered if item.get("fused_score", item.get("score")) >= threshold]
        if len(eligible) < minimum:
            fallback_count = min(minimum, len(ordered)) - len(eligible)
            eligible = ordered[:minimum]
    else:
        raise ValueError("selection.mode must be threshold or top_k")
    before_cap = len(eligible)
    if len(eligible) > maximum:
        clipped = len(eligible) - maximum
        eligible = eligible[:maximum]
    return {"mode": mode, "threshold": threshold, "tier_bucket": bucket,
            "doc_ids": [item["doc_id"] for item in eligible], "selected_count": len(eligible),
            "candidate_count": len(ordered), "before_cap_count": before_cap,
            "fallback_added_count": fallback_count, "cap_removed_count": clipped,
            "above_threshold_count": (sum(item.get("fused_score", item.get("score")) >= threshold for item in ordered)
                                      if threshold is not None else None),
            "minimum_unmet": len(eligible) < minimum}


def score_record(record: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    validate_scoring_config(config)
    candidates = record.get("candidates", [])
    identities = [candidate.get("doc_id") for candidate in candidates]
    if len(set(identities)) != len(identities):
        raise ValueError("candidate doc_ids must be unique within a query")
    ranking = [score_candidate(record, candidate, config) for candidate in candidates]
    ranking.sort(key=lambda item: (-item["fused_score"], item["doc_id"]))
    for rank, item in enumerate(ranking, 1):
        item["rank"] = rank
    selection = select_ranked(ranking, record.get("concepts", []), config.get("selection", {}))
    return {"id": record["id"], "query": record.get("query", ""), "lang": record.get("lang"),
            "ranking": ranking, "selection": selection,
            "doc_ids": selection["doc_ids"], "score_schema": "medical-gate-v1"}
