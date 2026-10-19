"""Paired statistical testing, group-aware bootstrap confidence intervals, and decision metrics."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from .contracts import SchemaInvalidError, validate_query_id


def paired_group_bootstrap(
    query_deltas: Mapping[int, float],
    query_groups: Mapping[int, int] | None = None,
    n_resamples: int = 10000,
    seed: int = 42,
    ci_level: float = 0.95,
) -> dict[str, Any]:
    """Perform group-aware bootstrap on paired query deltas (e.g. ΔP@200 or ΔF2).
    
    Resamples query groups with replacement to respect clustering.
    Calculates query-weighted mean estimator and percentile bootstrap CI.
    """
    if not query_deltas:
        raise SchemaInvalidError("query_deltas cannot be empty for bootstrap testing")
    from .contracts import validate_finite_number
    if type(n_resamples) is not int or n_resamples <= 0 or not 0 < ci_level < 1:
        raise SchemaInvalidError("Bootstrap budget/CI không hợp lệ")
    for q, delta in query_deltas.items():
        validate_query_id(q)
        validate_finite_number(delta, "query_delta")
    if query_groups is not None and any(q not in query_groups for q in query_deltas):
        raise SchemaInvalidError("Group map thiếu qid")

    qids = sorted(query_deltas.keys())
    deltas = np.array([query_deltas[q] for q in qids], dtype=np.float64)

    # 1. Basic counts
    wins = int(np.sum(deltas > 1e-9))
    losses = int(np.sum(deltas < -1e-9))
    ties = len(deltas) - wins - losses
    mean_delta = float(np.mean(deltas))

    # 2. Build groups
    if query_groups is None:
        # Default: each query is its own group
        groups: dict[int, list[int]] = {i: [i] for i in range(len(qids))}
    else:
        # Map each query index to its group ID
        group_to_indices: dict[int, list[int]] = {}
        for idx, q in enumerate(qids):
            gid = query_groups.get(q, q)
            if gid not in group_to_indices:
                group_to_indices[gid] = []
            group_to_indices[gid].append(idx)
        groups = {i: idxs for i, idxs in enumerate(group_to_indices.values())}

    group_keys = list(groups.keys())
    n_groups = len(group_keys)

    # 3. Bootstrap resampling
    rng = np.random.default_rng(seed)
    boot_means = np.empty(n_resamples, dtype=np.float64)

    for b in range(n_resamples):
        sampled_group_keys = rng.choice(group_keys, size=n_groups, replace=True)
        # Flatten sampled indices
        sampled_indices: list[int] = []
        for gk in sampled_group_keys:
            sampled_indices.extend(groups[gk])
        boot_means[b] = np.mean(deltas[sampled_indices])

    # 4. Percentile CI
    alpha = (1.0 - ci_level) / 2.0
    ci_lower = float(np.percentile(boot_means, alpha * 100.0))
    ci_upper = float(np.percentile(boot_means, (1.0 - alpha) * 100.0))

    return {
        "n_queries": len(qids),
        "n_groups": n_groups,
        "n_resamples": n_resamples,
        "mean_delta": mean_delta,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ci_level": ci_level,
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "is_significant_positive": ci_lower > 0.0,
    }

