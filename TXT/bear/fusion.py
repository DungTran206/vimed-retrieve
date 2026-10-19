"""Pure inference: residual, gate toàn query và fallback reference."""
import math
from .contracts import SchemaInvalidError, validate_finite_number
from .pools import merge_vi_lane


def rank_component(rank, state, k=60):
    validate_finite_number(k, "rank_k", min_val=0)
    if state == "ranked":
        if type(rank) is not int or rank < 1:
            raise SchemaInvalidError("rank phải là số nguyên >=1")
        return (k + 1) / (k + rank)
    if state == "not_retrieved":
        return 0.0
    if state in ("not_scored", "not_applicable", "missing_vector", "missing_text",
                 "missing_query", "partial_query"):
        return None
    raise SchemaInvalidError(f"availability không hợp lệ: {state}")


def validate_weights(weights):
    if not weights or abs(sum(weights.values()) - 1) > 1e-9:
        raise SchemaInvalidError("weights cần tổng 1")
    for key, value in weights.items():
        validate_finite_number(value, key, min_val=0)
    return weights


def fixed_evidence_score(ref_component, z, lambda_e):
    validate_finite_number(lambda_e, "lambda", min_val=0, max_val=1)
    validate_finite_number(z, "coverage", min_val=0, max_val=1)
    return (1 - lambda_e) * ref_component + lambda_e * z


def fixed_score(ref_component, branch_components, weights, lambda_):
    validate_finite_number(lambda_, "lambda", min_val=0, max_val=1)
    validate_weights(weights)
    if set(weights) != set(branch_components):
        raise SchemaInvalidError("Branch components/weights khác keys")
    return (1 - lambda_) * ref_component + lambda_ * sum(weights[k] * branch_components[k] for k in weights)


def query_gate(e_value, threshold, temperature):
    validate_finite_number(e_value, "E", min_val=0, max_val=1)
    validate_finite_number(threshold, "tau", min_val=0, max_val=1)
    validate_finite_number(temperature, "T", min_val=1e-12)
    z = (e_value - threshold) / temperature
    return 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))


def adaptive_weights(gate, lexical_endpoint, semantic_endpoint):
    validate_weights(lexical_endpoint)
    validate_weights(semantic_endpoint)
    if set(lexical_endpoint) != set(semantic_endpoint):
        raise SchemaInvalidError("Endpoints khác branches")
    return {k: gate * lexical_endpoint[k] + (1 - gate) * semantic_endpoint[k] for k in lexical_endpoint}


def rank_query(pool, features, config, route=None):
    mode, lam = config["mode"], config.get("lambda", 0)
    if mode not in ("baseline", "fixed_evidence", "fixed", "adaptive"):
        raise SchemaInvalidError(f"mode không hợp lệ: {mode}")
    validate_finite_number(lam, "lambda", min_val=0, max_val=1)
    if mode == "baseline" or lam == 0:
        return list(pool["baseline"]), {"fallback_reason": None, "bypass": True}
    weights = config.get("weights", {"B": .5, "D": .5})
    gate = None
    if mode == "adaptive" and route and route.get("route_eligible"):
        endpoints = config.get("endpoints", {"lexical": {"B": .8, "D": .2}, "semantic": {"B": .2, "D": .8}})
        gate = query_gate(route["E"], config["tau"], config["temperature"])
        weights = adaptive_weights(gate, endpoints["lexical"], endpoints["semantic"])
    details = []
    for row in pool["reference"]:
        if not row["selectable"]:
            continue
        doc = row["doc_id"]
        feature = features.get(doc, {})
        ref = rank_component(row["reference_rank"], "ranked")
        if mode == "fixed_evidence":
            z = feature.get(config.get("feature_name", "body_coverage"))
            if z is None or feature.get("mapping_coverage") != 1:
                return list(pool["baseline"]), {"fallback_reason": "evidence_unavailable", "doc_id": doc}
            score = fixed_evidence_score(ref, z, lam)
        else:
            components = {k: rank_component(feature.get("source_ranks", {}).get(k),
                          feature.get("availability", {}).get(k, "missing_query")) for k in weights}
            if any(v is None for v in components.values()):
                return list(pool["baseline"]), {"fallback_reason": "family_unavailable", "doc_id": doc}
            score = fixed_score(ref, components, weights, lam)
        details.append({"doc_id": doc, "score": score, "reference_rank": row["reference_rank"]})
    details.sort(key=lambda r: (-r["score"], r["reference_rank"], r["doc_id"]))
    return merge_vi_lane(pool, [r["doc_id"] for r in details]), {
        "fallback_reason": None, "gate_value": gate, "selected_weights": weights,
        "route_fallback": mode == "adaptive" and gate is None, "details": details}
