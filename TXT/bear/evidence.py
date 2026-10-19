"""Uniform exact body/title/local và E có availability explicit."""
from dataclasses import asdict
from .matching import build_protected_pattern, normalize_text

MATCHER_VERSION = "nfc_lower_space_protected_v2"
FEATURE_VERSION = "uniform_exact_v1"


def coverage(concepts, text, language):
    active = [c for c in concepts if c.vi_span_status == "verified_in_query"]
    mapped = [c for c in active if c.views.get(language)]
    if not active or text is None or not mapped:
        return {"coverage": None, "mapping_coverage": len(mapped) / len(active) if active else 0,
                "matched_concepts": [], "missing_concepts": [c.concept_id for c in active]}
    target = normalize_text(text)
    matches = [c for c in mapped if build_protected_pattern(c.views[language]).search(target)]
    ids = {c.concept_id for c in matches}
    return {"coverage": len(matches) / len(mapped), "mapping_coverage": len(mapped) / len(active),
            "matched_concepts": sorted(ids),
            "missing_concepts": [c.concept_id for c in active if c.concept_id not in ids],
            "matched_phrases": [c.views[language] for c in matches]}


def document_evidence(concepts, document, refs):
    lang = document.get("lang")
    body = document.get("body")
    body_cov = coverage(concepts, body, lang)
    title_cov = coverage(concepts, document.get("title"), lang)
    chunks = []
    for ref in refs:
        cov = coverage(concepts, body[ref.start:ref.end] if body is not None else None, lang)
        chunks.append({"ref": asdict(ref), "coverage": cov["coverage"],
                       "matched_concepts": cov["matched_concepts"]})
    valid = sorted([c for c in chunks if c["coverage"] is not None],
                   key=lambda c: (-c["coverage"], c["ref"]["start"], c["ref"]["end"], c["ref"]["chunk_id_native"]))
    active = [c for c in concepts if c.vi_span_status == "verified_in_query"]
    critical = [c for c in active if c.critical]
    return {"has_entities": bool(active), "entity_count": len(active),
            "has_critical_terms": bool(critical),
            "body_coverage": body_cov["coverage"], "exact_coverage": body_cov["coverage"],
            "concept_coverage": body_cov["coverage"],
            "critical_coverage": coverage(critical, body, lang)["coverage"] if critical else None,
            "title_coverage": title_cov["coverage"],
            "mapping_coverage": body_cov["mapping_coverage"],
            "local_max_all": valid[0]["coverage"] if valid else None,
            "local_top2_mean": sum(c["coverage"] for c in valid[:2]) / min(2, len(valid)) if valid else None,
            "matched_concepts": body_cov["matched_concepts"],
            "missing_concepts": body_cov["missing_concepts"],
            "matched_phrases": body_cov.get("matched_phrases", []),
            "best_evidence_chunk_ref": valid[0]["ref"] if valid else None,
            "body_length": len(body) if body is not None else None, "chunk_count": len(refs),
            "evidence_status": "missing_text" if body is None else ("empty_text" if not body else "computed"),
            "critical_mismatches": [], "chunk_features": chunks}


def query_evidence(support, features, k_e=60):
    total = valid_weight = numerator = 0.0
    for item in support["docs"]:
        weight = 1 / (k_e + item["source_rank"])
        total += weight
        f = features.get(item["doc_id"], {})
        if f.get("body_coverage") is not None and f.get("mapping_coverage") == 1:
            valid_weight += weight
            numerator += weight * f["body_coverage"]
    eligible = bool(total) and abs(total - valid_weight) < 1e-12 and not support.get("unverified_language")
    e_valid = numerator / valid_weight if valid_weight else None
    return {"E": e_valid if eligible else None, "E_valid": e_valid,
            "weighted_availability_gamma": valid_weight / total if total else 0,
            "route_eligible": eligible, "actual_K": len(support["docs"]),
            "requested_K": support["requested_K"], "support_hash": support["support_hash"],
            "k_E": k_e, "feature_definition": FEATURE_VERSION,
            "fallback_reason": None if eligible else "incomplete_support"}
