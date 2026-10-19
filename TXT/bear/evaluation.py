"""Evaluation contracts, token sequence LCS diagnostics, macro Doc F2, and replacement delta guards."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .contracts import (
    ERROR_LABEL_COVERAGE_INSUFFICIENT,
    ERROR_SCHEMA_INVALID,
    LabelCoverageInsufficientError,
    SchemaInvalidError,
    validate_doc_id,
    validate_query_id,
)


def lcs_token_length(seq_a: Sequence[str], seq_b: Sequence[str]) -> int:
    """Compute the Longest Common Subsequence (LCS) length of two token sequences.
    
    Uses standard O(min(m, n)) memory Dynamic Programming.
    """
    if not seq_a or not seq_b:
        return 0

    # Ensure seq_b is the shorter sequence to minimize memory footprint
    if len(seq_a) < len(seq_b):
        seq_a, seq_b = seq_b, seq_a

    m, n = len(seq_a), len(seq_b)
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)

    for item_a in seq_a:
        for j in range(1, n + 1):
            if item_a == seq_b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = prev[j] if prev[j] > curr[j - 1] else curr[j - 1]
        prev, curr = curr, [0] * (n + 1)

    return prev[n]


def passage_match_diagnostic(
    pred_tokens: Sequence[str],
    gold_tokens: Sequence[str],
    pred_doc_id: str,
    gold_doc_id: str,
    threshold: float = 0.40,
) -> bool:
    """Diagnostic match for passage chunks based on LCS overlap ratio.
    
    Requires pred_doc_id == gold_doc_id and LCS(pred, gold) / len(gold) >= threshold.
    """
    clean_pred_doc = validate_doc_id(pred_doc_id)
    clean_gold_doc = validate_doc_id(gold_doc_id)

    if clean_pred_doc != clean_gold_doc:
        return False

    if not gold_tokens:
        return False

    lcs_len = lcs_token_length(pred_tokens, gold_tokens)
    overlap_ratio = lcs_len / len(gold_tokens)
    return overlap_ratio >= threshold


def compute_doc_f2(relevant_retrieved: int, total_retrieved: int, total_gold: int) -> float:
    """Compute per-query Document F2 score: 5 * g / (4 * G + k)."""
    if total_gold <= 0 or total_retrieved <= 0:
        return 0.0
    denominator = 4 * total_gold + total_retrieved
    return (5.0 * relevant_retrieved) / denominator


def compute_macro_doc_f2(
    query_metrics: Mapping[int, tuple[int, int, int]],
    empty_gold_policy: str = "excluded",
) -> float:
    """Compute Macro Document F2 across queries.
    
    query_metrics: {qid: (relevant_retrieved, total_retrieved, total_gold)}
    empty_gold_policy: 'excluded' (default per runtime archive) ignores queries with total_gold == 0.
    """
    scores: list[float] = []

    for qid, (g, k, G) in query_metrics.items():
        if G == 0 and empty_gold_policy == "excluded":
            continue
        scores.append(compute_doc_f2(g, k, G))

    if not scores:
        return 0.0
    return float(sum(scores) / len(scores))


def compute_replacement_delta(
    docs_a: Sequence[str],
    docs_b: Sequence[str],
    qrels: Mapping[str, int],
    relevance_threshold: int = 1,
    k: int = 200,
) -> dict[str, Any]:
    """Compute paired replacement Δhits and ΔP@k between two ranked lists A and B.
    
    Guarantees:
    - If ANY document in (added union removed) is unjudged in qrels, returns
      status='not_available' and unjudged count; never silently imputes 0.
    """
    list_a = [validate_doc_id(d) for d in docs_a[:k]]
    list_b = [validate_doc_id(d) for d in docs_b[:k]]
    if k <= 0 or len(list_a) != k or len(list_b) != k or len(set(list_a)) != k or len(set(list_b)) != k:
        raise SchemaInvalidError("Replacement cần hai ranking đủ k, không duplicate")

    set_a = set(list_a)
    set_b = set(list_b)

    added = sorted(set_a - set_b)
    removed = sorted(set_b - set_a)

    unjudged_added = [d for d in added if d not in qrels]
    unjudged_removed = [d for d in removed if d not in qrels]
    all_unjudged = sorted(set(unjudged_added + unjudged_removed))

    if all_unjudged:
        return {
            "status": "not_available",
            "delta_hits": None,
            "delta_p": None,
            "unjudged_count": len(all_unjudged),
            "unjudged_docs": all_unjudged,
            "added_count": len(added),
            "removed_count": len(removed),
        }

    hits_added = sum(1 for d in added if qrels[d] >= relevance_threshold)
    hits_removed = sum(1 for d in removed if qrels[d] >= relevance_threshold)
    delta_hits = hits_added - hits_removed
    delta_p = delta_hits / float(k)

    return {
        "status": "available",
        "delta_hits": delta_hits,
        "delta_p": delta_p,
        "hits_added": hits_added,
        "hits_removed": hits_removed,
        "added_count": len(added),
        "removed_count": len(removed),
    }

