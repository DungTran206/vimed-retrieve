"""Pool đóng băng, reference baseline-first, support trước fusion."""
from .contracts import SchemaInvalidError
from .io import canonical_sha256


def build_pool(baseline, deeper, sources, languages, eligible, scope="plarge", cap=400):
    if scope not in ("p200", "plarge") or cap < 200:
        raise SchemaInvalidError("scope phải p200/plarge, cap>=200")
    if len(baseline) != 200 or len(set(baseline)) != 200:
        raise SchemaInvalidError("Baseline cần đúng 200 doc duy nhất")
    if any(d not in eligible for d in baseline):
        raise SchemaInvalidError("Baseline conflict với frozen eligibility")
    ordered = list(baseline)
    seen = set(ordered)
    if scope == "plarge":
        # Source priority là thứ tự list đã đăng ký, không lấy labels.
        for sequence in [deeper, *sources]:
            for doc in sequence:
                if len(ordered) >= cap:
                    break
                if doc in eligible and doc not in seen:
                    ordered.append(doc)
                    seen.add(doc)
    rows = [{"doc_id": d, "reference_rank": i + 1,
             "baseline_rank": i + 1 if i < 200 else None,
             "lang": languages.get(d), "selectable": languages.get(d) == "vi"}
            for i, d in enumerate(ordered)]
    return {"baseline": list(baseline), "reference": rows, "scope": scope,
            "pool_hash": canonical_sha256(rows), "actual_size": len(rows),
            "selectable_extra_vi_count": sum(r["selectable"] for r in rows[200:]),
            "unknown_language_count": sum(r["lang"] is None for r in rows)}


def route_support(b_family, languages, eligible, k=20):
    support, unknown = [], []
    for rank, doc in enumerate(b_family, 1):
        if doc not in eligible:
            continue
        if languages.get(doc) is None:
            unknown.append(doc)
            break
        if languages[doc] == "vi":
            support.append({"doc_id": doc, "source_rank": rank})
        if len(support) == k:
            break
    return {"docs": support, "support_hash": canonical_sha256(support),
            "unverified_language": unknown, "requested_K": k}


def merge_vi_lane(pool, sorted_vi):
    baseline = pool["baseline"]
    vi = {r["doc_id"] for r in pool["reference"] if r["selectable"]}
    slots = sum(d in vi for d in baseline)
    picked = list(sorted_vi[:slots])
    if len(picked) != slots or len(set(picked)) != slots or any(d not in vi for d in picked):
        raise SchemaInvalidError("VI lane không đủ hoặc chứa doc không hợp lệ")
    iterator = iter(picked)
    result = [next(iterator) if d in vi else d for d in baseline]
    if pool["scope"] == "p200" and set(result) != set(baseline):
        raise SchemaInvalidError("P200 thay đổi document set")
    return result


def family_ranking(children, weights):
    if not children or set(children) != set(weights):
        raise SchemaInvalidError("Family thiếu child/weight")
    from .baseline import rrf_fuse_rankings
    fused = rrf_fuse_rankings([(children[k], weights[k]) for k in children], top_k=10**9)
    return {q: [d for _, d in rows] for q, rows in fused.items()}
