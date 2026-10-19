"""Baseline handover recipe wrapper and exact calibration compatibility adapter under TXT.

Preserves exact legacy behaviors, parity checks, and differential testing against
the frozen scripts/val_calib.py implementation.
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .contracts import (
    ERROR_BASELINE_PARITY_FAILED,
    ERROR_INPUT_MISSING,
    ERROR_SCHEMA_INVALID,
    BaselineParityFailedError,
    InputMissingError,
    SchemaInvalidError,
    validate_doc_id,
    validate_finite_number,
    validate_query_id,
)
from .io import (
    assert_valid_output_path,
    atomic_write_json,
    atomic_write_text,
    canonical_sha256,
    read_json,
    read_jsonl,
    resolve_repo_path,
    write_jsonl,
)


def score_frozen_calibration(
    ranking: Mapping[int, Sequence[str]],
    source_bundle: Mapping[str, Any],
    beta: Sequence[float],
    doc_languages: Mapping[str, str],
) -> dict[int, list[dict[str, Any]]]:
    """Score p(gold) for candidates using the exact 8-beta logistic regression recipe.
    
    Ported strictly from scripts/val_calib.py:207-234.
    
    Beta is a sequence of 8 finite floats:
    [intercept, logitQ, hasQ, cosChunk, hasCosChunk, isZH, cosZH, hasZH]
    """
    if len(beta) != 8:
        raise SchemaInvalidError(f"Beta must contain exactly 8 coefficients, got {len(beta)}")
    for i, b in enumerate(beta):
        validate_finite_number(b, f"beta[{i}]")

    b_arr = np.array(beta, dtype=np.float64)
    qwen_scores = source_bundle.get("qwen_doc_scores", {})
    chunk_scores = source_bundle.get("chunk_dense", {})
    zh_vi_scores = source_bundle.get("zh_bge_vi", {})
    zh_zhq_scores = source_bundle.get("zh_bge_zh", {})

    output: dict[int, list[dict[str, Any]]] = {}

    for qid, docs in ranking.items():
        q_int = validate_query_id(qid)
        q_qwen = qwen_scores.get(q_int, {})
        q_chunk = chunk_scores.get(q_int, {})
        q_zh_vi = zh_vi_scores.get(q_int, {})
        q_zh_zhq = zh_zhq_scores.get(q_int, {})

        rows: list[list[float]] = []
        doc_list: list[str] = []

        for doc in docs:
            doc_id = validate_doc_id(doc)
            doc_list.append(doc_id)

            qy = q_qwen.get(doc_id)
            cs = q_chunk.get(doc_id)
            zc = max(q_zh_vi.get(doc_id, -1.0), q_zh_zhq.get(doc_id, -1.0))

            lang = doc_languages.get(doc_id)
            if lang == "zh":
                # Vector for ZH: [0, 0, 0, 0, 1, max(zc, 0), zc >= 0]
                rows.append([0.0, 0.0, 0.0, 0.0, 1.0, float(max(zc, 0.0)), float(zc >= 0)])
            else:
                # Vector for VI/non-ZH:
                # Clamp qy to [0.001, 0.999] if present
                if qy is not None:
                    t = min(max(float(qy), 0.001), 0.999)
                    logit_q = float(np.log(t / (1.0 - t)))
                    has_q = 1.0
                else:
                    logit_q = 0.0
                    has_q = 0.0

                cs_val = float(cs) if cs is not None else 0.0
                has_cs = 1.0 if cs is not None else 0.0
                rows.append([logit_q, has_q, cs_val, has_cs, 0.0, 0.0, 0.0])

        if not rows:
            output[q_int] = []
            continue

        X = np.array(rows, dtype=np.float64)
        logits = b_arr[0] + X @ b_arr[1:]
        p_vals = 1.0 / (1.0 + np.exp(-logits))

        cands = [
            {"doc_id": d, "p": round(float(p), 4)}
            for d, p in zip(doc_list, p_vals)
        ]
        output[q_int] = cands

    return output


def make_plan_from_calibrated_p(
    query_id: int,
    candidates: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    """Derive chunk allocation plan for a query from rounded p(gold).
    
    Rules per PLAN.md §2.3 & §7.1:
    - index < 120 and p < 0.04 -> plan 0 (remove chunk, keep doc)
    - index >= 120 and p >= 0.05 -> plan 1 (add 1 chunk if doc has none)
    - Thresholds are evaluated on p already rounded to 4 decimals.
    """
    plan: dict[str, int] = {}
    for idx, c in enumerate(candidates):
        doc_id = validate_doc_id(c["doc_id"])
        p_val = float(c["p"])
        if idx < 120 and p_val < 0.04:
            plan[doc_id] = 0
        elif idx >= 120 and p_val >= 0.05:
            plan[doc_id] = 1
    return plan


def rrf_fuse_rankings(
    rankings_with_weights: Sequence[tuple[Mapping[int, Sequence[str]], float]],
    k: int = 60,
    top_k: int = 1000,
) -> dict[int, list[tuple[float, str]]]:
    """Deterministic Reciprocal Rank Fusion (RRF) preserving string-ID tie order."""
    scores: dict[int, dict[str, float]] = {}
    
    for r_dict, weight in rankings_with_weights:
        for qid, doc_ids in r_dict.items():
            if qid not in scores:
                scores[qid] = {}
            for rank_idx, doc_id in enumerate(doc_ids, start=1):
                inc = weight / (k + rank_idx)
                scores[qid][doc_id] = scores[qid].get(doc_id, 0.0) + inc

    fused: dict[int, list[tuple[float, str]]] = {}
    for qid, doc_scores in scores.items():
        # Sort by (-score, doc_id_string)
        sorted_docs = sorted(doc_scores.items(), key=lambda pair: (-pair[1], pair[0]))
        fused[qid] = [(score, doc) for doc, score in sorted_docs[:top_k]]

    return fused


def build_head_hybrid(
    base_docs: Sequence[str],
    alt_docs: Sequence[str],
    max_head: int = 120,
    alt_scan: int = 240,
) -> list[str]:
    """Port of hybrid_cands head extraction logic: alt[:alt_scan] intersect base[:200]."""
    base_200 = list(base_docs[:200])
    base_set = set(base_200)
    
    head: list[str] = []
    seen: set[str] = set()
    for d in alt_docs[:alt_scan]:
        if d in base_set and d not in seen:
            head.append(d)
            seen.add(d)
            if len(head) >= max_head:
                break
                
    # Append remaining base_200 docs
    tail = [d for d in base_200 if d not in seen]
    return head + tail


def filter_and_refill_candidates(
    candidates: Sequence[str],
    deep_pool: Sequence[str],
    eligible_ids: set[str],
    vinmec_ids: set[str],
    target_count: int = 200,
) -> list[str]:
    """Keep ID in membership or domain vinmec.com; refill from deep pool to target_count."""
    filtered: list[str] = []
    seen: set[str] = set()
    
    def is_eligible(did: str) -> bool:
        return did in eligible_ids or did in vinmec_ids

    for d in candidates:
        if is_eligible(d) and d not in seen:
            filtered.append(d)
            seen.add(d)
            
    if len(filtered) < target_count:
        for d in deep_pool:
            if is_eligible(d) and d not in seen:
                filtered.append(d)
                seen.add(d)
                if len(filtered) == target_count:
                    break

    return filtered

