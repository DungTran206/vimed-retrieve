"""Query-disjoint calibration and finite-menu replay of the medical hypothesis.

Only explicit judgments train a sigmoid. Unjudged documents never become
negatives. Native val.jsonl is accepted without using labels during inference.
The fitted sigmoid is a feature calibration on the judged sampling distribution,
not a guarantee of corpus-wide probability calibration.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import unicodedata
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .medical_scoring import blended_bm25, finite, pretransform_bm25, score_record, sigmoid


def _binary(value: Any) -> int:
    if type(value) is not int or value not in (0, 1):
        raise ValueError("qrels labels must be explicit binary integers 0 or 1")
    return value


def _query_id(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("query id must be a nonnegative integer")
    return value


def _doc_id(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value).strip():
        raise ValueError("doc_id must be a nonempty string or integer")
    return str(value)


def validation_from_rows(rows: Iterable[Mapping[str, Any]]) -> dict[int, dict[str, Any]]:
    """Adapt native val rows, per-query qrels, or normalized pairwise qrels.

    Query rows: {id, gold, not_gold, G, gold_unseen} or
    {id, qrels:{doc_id:0|1}, total_gold?, complete:false}.
    Pair rows: {query_id,doc_id,relevance:0|1}; completeness remains false.
    """
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        if "query_id" in row and "doc_id" in row:
            qid = _query_id(row["query_id"])
            item = result.setdefault(qid, {"id": qid, "query": "", "qrels": {},
                                           "total_gold": 0, "complete": False, "gold_unseen": 0,
                                           "label_source": "explicit_pair_qrels"})
            if item["label_source"] != "explicit_pair_qrels":
                raise ValueError("cannot mix query and pair qrels for the same query")
            identity = _doc_id(row["doc_id"])
            label = _binary(row["relevance"])
            if identity in item["qrels"]:
                raise ValueError("duplicate pair qrel")
            item["qrels"][identity] = label
            item["total_gold"] += label
            continue
        qid = _query_id(row.get("id"))
        if qid in result:
            raise ValueError(f"duplicate validation query {qid}")
        if "qrels" in row:
            if not isinstance(row["qrels"], Mapping):
                raise ValueError("qrels must be a mapping")
            qrels = {_doc_id(doc): _binary(label) for doc, label in row["qrels"].items()}
            if len(qrels) != len(row["qrels"]):
                raise ValueError("doc IDs collide after normalization")
            source = "explicit_query_qrels"
            total = row.get("total_gold", sum(qrels.values()))
            unseen = row.get("gold_unseen", 0)
        elif "gold" in row:
            positive_ids = [_doc_id(doc) for doc in row["gold"]]
            negative_ids = [_doc_id(doc) for doc in row.get("not_gold", [])]
            if len(set(positive_ids)) != len(positive_ids) or len(set(negative_ids)) != len(negative_ids):
                raise ValueError("duplicate native validation document")
            if set(positive_ids) & set(negative_ids):
                raise ValueError("gold and not_gold overlap")
            qrels = {doc: 1 for doc in positive_ids} | {doc: 0 for doc in negative_ids}
            source = "native_val_gold_not_gold"
            unseen = row.get("gold_unseen", 0)
            total = row.get("G", len(positive_ids) + unseen)
        else:
            raise ValueError("validation row needs gold, qrels, or normalized pair fields")
        if type(total) is not int or total < sum(qrels.values()):
            raise ValueError("total_gold must include all known positives")
        if type(unseen) is not int or unseen < 0:
            raise ValueError("gold_unseen must be a nonnegative integer")
        complete = row.get("complete", False)
        if type(complete) is not bool:
            raise ValueError("complete must be an explicit boolean")
        if complete and total != sum(qrels.values()):
            raise ValueError("complete binary judgments cannot contain unseen positives")
        result[qid] = {"id": qid, "query": row.get("query", ""), "qrels": qrels,
                       "total_gold": total, "complete": complete, "gold_unseen": unseen,
                       "label_source": source}
    if not result:
        raise ValueError("validation judgments are empty")
    return result


def load_validation(path: str | Path) -> dict[int, dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        return validation_from_rows(json.loads(line) for line in handle if line.strip())


def split_query_ids(records: Iterable[Mapping[str, Any]], *, seed: int = 391,
                    calibration_fraction: float = 0.4, tune_fraction: float = 0.4,
                    previously_observed_ids: Iterable[int] | str = (),
                    exposure_status: str = "unknown") -> dict[str, Any]:
    """Group duplicate normalized queries; never split random q-doc pairs."""
    if not 0 < calibration_fraction < 1 or not 0 < tune_fraction < 1 or calibration_fraction + tune_fraction >= 1:
        raise ValueError("calibration and tune fractions must leave a positive holdout")
    if exposure_status not in {"unknown", "recorded"}:
        raise ValueError("exposure_status must be unknown or recorded")
    if isinstance(previously_observed_ids, str) and previously_observed_ids != "all":
        raise ValueError("previously_observed_ids must be a query ID sequence or 'all'")
    groups: dict[str, list[int]] = {}
    seen = set()
    for row in records:
        qid = _query_id(row["id"])
        if qid in seen:
            raise ValueError("duplicate query id in split input")
        seen.add(qid)
        query = " ".join(unicodedata.normalize("NFKC", row.get("query", "")).casefold().split())
        key = query if query else f"id:{qid}"
        groups.setdefault(key, []).append(qid)
    if len(groups) < 3:
        raise ValueError("need at least three distinct query groups for calibration/tune/holdout")
    keys = sorted(groups)
    random.Random(seed).shuffle(keys)
    n_cal = max(1, min(len(keys) - 2, int(len(keys) * calibration_fraction)))
    n_tune = max(1, min(len(keys) - n_cal - 1, int(len(keys) * tune_fraction)))
    assignments = {"calibration": keys[:n_cal], "tune": keys[n_cal:n_cal + n_tune],
                   "holdout": keys[n_cal + n_tune:]}
    manifest: dict[str, Any] = {name: sorted(qid for key in group_keys for qid in groups[key])
                                for name, group_keys in assignments.items()}
    observed = seen.copy() if previously_observed_ids == "all" else set(previously_observed_ids)
    if any(type(qid) is not int for qid in observed):
        raise ValueError("previously observed query IDs must be integers")
    manifest.update({"seed": seed, "grouping": "NFKC-casefold-whitespace-query",
                     "group_count": len(groups), "query_count": len(seen),
                     "previously_observed_ids": sorted(observed & seen),
                     "exposure_status": exposure_status,
                     "holdout_previously_observed_ids": sorted(observed & set(manifest["holdout"])),
                     "holdout_pristine": exposure_status == "recorded" and not bool(observed & set(manifest["holdout"])),
                     "holdout_caveat": "A query-disjoint retrospective split does not erase earlier validation exposure; unknown exposure is never called pristine.",
                     "query_groups": {str(qid): hashlib.sha256(key.encode()).hexdigest()
                                      for key, ids in groups.items() for qid in ids}})
    return manifest


def calibration_samples(records: Iterable[Mapping[str, Any]], labels: Mapping[int, Mapping[str, Any]],
                        query_ids: Iterable[int], scoring_config: Mapping[str, Any], *,
                        balance_queries: bool = True) -> list[tuple[float, int, float]]:
    """Use judged candidates only, exactly matching the inference BM25 recipe."""
    wanted = set(query_ids)
    samples = []
    found = set()
    for row in records:
        qid = row["id"]
        if qid not in wanted:
            continue
        if qid in found:
            raise ValueError("duplicate calibration query record")
        found.add(qid)
        if qid not in labels:
            raise ValueError(f"missing judgments for calibration query {qid}")
        judgments = labels[qid]["qrels"]
        local = []
        for candidate in row.get("candidates", []):
            identity = str(candidate["doc_id"])
            if identity not in judgments:
                continue
            raw, _ = blended_bm25(candidate.get("scores", {}), scoring_config.get("bm25", {}))
            if raw is None:
                continue
            score = pretransform_bm25(raw, scoring_config.get("bm25", {}), row.get("query_scale", 1.0),
                                     query_scale_compatible=row.get("query_scale_compatible", True))
            local.append((score, _binary(judgments[identity])))
        weight = 1 / len(local) if balance_queries and local else 1.0
        samples.extend((score, label, weight) for score, label in local)
    if found != wanted:
        raise ValueError(f"calibration query records missing: {sorted(wanted - found)}")
    return samples


def _softplus(value: float) -> float:
    return max(value, 0.0) + math.log1p(math.exp(-abs(value)))


def fit_sigmoid(samples: Sequence[Sequence[float]], *, l2: float = 1e-4,
                max_iter: int = 200, tolerance: float = 1e-8) -> dict[str, Any]:
    """Fit positive-slope logistic using damped Newton and stdlib only.

    Samples are (pretransformed_BM25,binary_label[,weight]). Standardization is
    internal numerical conditioning and is folded back into x0 and temperature.
    Inverse correlation is represented by a near-flat positive slope, never by
    reversing BM25 order. Degenerate scores or one-class labels are rejected.
    """
    if l2 <= 0 or max_iter <= 0 or tolerance <= 0:
        raise ValueError("l2, max_iter and tolerance must be positive")
    parsed = []
    for sample in samples:
        if len(sample) not in (2, 3):
            raise ValueError("calibration samples need score,label[,weight]")
        x = finite(sample[0], "calibration score")
        y = _binary(sample[1])
        weight = finite(sample[2], "sample weight") if len(sample) == 3 else 1.0
        if weight <= 0:
            raise ValueError("sample weights must be positive")
        parsed.append((x, y, weight))
    if not parsed or {y for _, y, _ in parsed} != {0, 1}:
        raise ValueError("sigmoid calibration needs both explicitly judged classes")
    # Common weight scaling must not alter the fit or overflow the total weight.
    largest_weight = max(weight for _, _, weight in parsed)
    parsed = [(x, y, weight / largest_weight) for x, y, weight in parsed]
    if any(weight == 0 for _, _, weight in parsed):
        raise ValueError("sample weight dynamic range exceeds floating-point precision")
    total_weight = math.fsum(weight for _, _, weight in parsed)
    mean = sum(x * weight for x, _, weight in parsed) / total_weight
    variance = sum(weight * (x - mean) ** 2 for x, _, weight in parsed) / total_weight
    if variance <= 1e-20:
        raise ValueError("sigmoid calibration needs nonconstant BM25 scores")
    scale = math.sqrt(variance)
    data = [((x - mean) / scale, y, weight / total_weight) for x, y, weight in parsed]
    prevalence = sum(y * weight for _, y, weight in data)
    slope = 1.0
    intercept = math.log(prevalence / (1 - prevalence))
    slope_floor = 1e-6

    def objective(a: float, b: float) -> float:
        return sum(weight * (_softplus(a * x + b) - y * (a * x + b))
                   for x, y, weight in data) + 0.5 * l2 * a * a

    converged = False
    iterations = 0
    loss = objective(slope, intercept)
    for iterations in range(1, max_iter + 1):
        ga = l2 * slope
        gb = 0.0
        haa = l2
        hab = 0.0
        hbb = 1e-12
        for x, y, weight in data:
            p = sigmoid(slope * x + intercept)
            residual = weight * (p - y)
            curvature = weight * p * (1 - p)
            ga += residual * x
            gb += residual
            haa += curvature * x * x
            hab += curvature * x
            hbb += curvature
        projected_ga = 0.0 if slope <= slope_floor and ga > 0 else ga
        if max(abs(projected_ga), abs(gb)) <= tolerance:
            converged = True
            break
        determinant = haa * hbb - hab * hab
        if determinant <= 0:
            break
        delta_a = (hbb * ga - hab * gb) / determinant
        delta_b = (haa * gb - hab * ga) / determinant
        step = 1.0
        accepted = False
        for _ in range(40):
            proposed_a = max(slope_floor, slope - step * delta_a)
            proposed_b = intercept - step * delta_b
            proposed_loss = objective(proposed_a, proposed_b)
            if proposed_loss <= loss:
                difference = abs(loss - proposed_loss)
                slope, intercept, loss = proposed_a, proposed_b, proposed_loss
                accepted = True
                if difference <= tolerance * tolerance:
                    converged = True
                break
            step *= 0.5
        if not accepted or converged:
            break
    coefficient = slope / scale
    raw_intercept = intercept - slope * mean / scale
    temperature = 1.0 / coefficient
    x0 = -raw_intercept / coefficient
    predictions = [sigmoid((x - x0) / temperature) for x, _, _ in parsed]
    brier = sum(weight * (p - y) ** 2 for p, (_, y, weight) in zip(predictions, parsed)) / total_weight
    log_loss = sum(weight * (_softplus((x - x0) / temperature) - y * (x - x0) / temperature)
                   for x, y, weight in parsed) / total_weight
    return {"x0": x0, "temperature": temperature, "coefficient": coefficient,
            "intercept": raw_intercept, "sample_count": len(parsed),
            "positive_count": sum(y for _, y, _ in parsed), "weighted_prevalence": prevalence,
            "weighted_brier": brier, "weighted_log_loss": log_loss,
            "iterations": iterations, "converged": converged, "l2": l2,
            "near_flat": slope <= slope_floor * 1.01,
            "calibration_scope": "explicitly judged cached candidates only"}


def evaluate_rankings(outputs: Sequence[Mapping[str, Any]], labels: Mapping[int, Mapping[str, Any]],
                      query_ids: Iterable[int] | None = None, *,
                      allow_incomplete_f2: bool = False) -> dict[str, Any]:
    """Known-positive recall is available; true precision needs complete judgments.

    F2 is computed only for a query with complete binary labels and no selected
    unjudged docs. With explicit allow_incomplete_f2, a known-positive proxy is
    reported separately and never named true F2 or precision.
    """
    indexed = {}
    for output in outputs:
        if output["id"] in indexed:
            raise ValueError("duplicate output query")
        indexed[output["id"]] = output
    wanted = sorted(indexed if query_ids is None else set(query_ids))
    if not wanted:
        raise ValueError("no evaluation queries")
    recalls = []
    total_recalls = []
    f2_values = []
    proxy_values = []
    counts = []
    unjudged = 0
    fallback_added = 0
    per_query = []
    for qid in wanted:
        if qid not in indexed or qid not in labels:
            raise ValueError(f"missing predictions or judgments for query {qid}")
        output = indexed[qid]
        docs = output.get("doc_ids", output.get("selection", {}).get("doc_ids"))
        if docs is None or len(set(docs)) != len(docs):
            raise ValueError("evaluation requires a unique selected doc_ids list")
        docs = [str(identity) for identity in docs]
        judgments = labels[qid]["qrels"]
        positives = {identity for identity, label in judgments.items() if label == 1}
        hits = len(set(docs) & positives)
        unknown = sum(identity not in judgments for identity in docs)
        total = labels[qid].get("total_gold", len(positives))
        recall = hits / len(positives) if positives else None
        total_recall = hits / total if total else None
        if recall is not None:
            recalls.append(recall)
        if total_recall is not None:
            total_recalls.append(total_recall)
        complete = labels[qid].get("complete", False) and unknown == 0
        f2 = (5 * hits / (4 * total + len(docs)) if total else None) if complete else None
        if f2 is not None:
            f2_values.append(f2)
        proxy = (5 * hits / (4 * total + len(docs)) if total else None) if allow_incomplete_f2 else None
        if proxy is not None:
            proxy_values.append(proxy)
        counts.append(len(docs))
        unjudged += unknown
        fallback_added += output.get("selection", {}).get("fallback_added_count", 0)
        per_query.append({"id": qid, "selected_count": len(docs), "known_positive_hits": hits,
                          "known_positive_count": len(positives), "total_gold": total,
                          "known_positive_recall": recall, "reported_gold_recall": total_recall,
                          "selected_unjudged_count": unknown, "doc_f2": f2,
                          "known_positive_f2_proxy": proxy})
    return {"query_count": len(wanted), "mean_docs": sum(counts) / len(counts),
            "min_docs": min(counts), "max_docs": max(counts),
            "known_positive_recall": sum(recalls) / len(recalls) if recalls else None,
            "reported_gold_recall": sum(total_recalls) / len(total_recalls) if total_recalls else None,
            "macro_doc_f2": sum(f2_values) / len(f2_values) if len(f2_values) == len(wanted) else None,
            "complete_f2_query_count": len(f2_values),
            "known_positive_f2_proxy": sum(proxy_values) / len(proxy_values) if proxy_values else None,
            "selected_unjudged_count": unjudged, "fallback_added_count": fallback_added,
            "precision": None, "per_query": per_query,
            "label_policy": "explicit judgments; unjudged are unknown"}


def tune_configs(records: Sequence[Mapping[str, Any]] | Callable[[], Iterable[Mapping[str, Any]]],
                 labels: Mapping[int, Mapping[str, Any]],
                 query_ids: Iterable[int], configs: Sequence[Mapping[str, Any]], *,
                 objective: str = "known_positive_recall", max_mean_docs: float | None = None,
                 allow_incomplete_f2: bool = False) -> dict[str, Any]:
    """Evaluate a finite predeclared menu on tune queries only, with budget control.

    Large caches should pass a callable producing a fresh iterator for each
    trial. Only one query's full feature/span payload is scored at a time, and
    only selected IDs plus selection statistics survive until evaluation.
    """
    if objective not in ("known_positive_recall", "reported_gold_recall", "macro_doc_f2", "known_positive_f2_proxy"):
        raise ValueError("unsupported tuning objective")
    if objective == "known_positive_f2_proxy" and not allow_incomplete_f2:
        raise ValueError("proxy objective requires allow_incomplete_f2=true")
    if not configs:
        raise ValueError("tuning menu is empty")
    if max_mean_docs is not None and finite(max_mean_docs, "max_mean_docs") <= 0:
        raise ValueError("max_mean_docs must be positive")
    ids = set(query_ids)
    if not ids:
        raise ValueError("no tune query IDs")
    trials = []
    for index, config in enumerate(configs):
        outputs = []
        found = set()
        replay = records() if callable(records) else records
        for row in replay:
            qid = row["id"]
            if qid not in ids:
                continue
            if qid in found:
                raise ValueError(f"duplicate tune query record {qid} in trial {index}")
            found.add(qid)
            scored = score_record(row, config)
            outputs.append({"id": scored["id"], "doc_ids": scored["doc_ids"],
                            "selection": scored["selection"]})
            # The ranking contains per-document diagnostics and must not be
            # retained while reading the next query or evaluating another trial.
            del scored
        if found != ids:
            raise ValueError(f"tune records missing query IDs in trial {index}: {sorted(ids - found)}")
        metrics = evaluate_rankings(outputs, labels, ids, allow_incomplete_f2=allow_incomplete_f2)
        objective_value = metrics[objective]
        feasible = objective_value is not None and (max_mean_docs is None or metrics["mean_docs"] <= max_mean_docs)
        trials.append({"trial": index, "config": copy.deepcopy(config), "metrics": metrics,
                       "feasible": feasible, "objective_value": objective_value})
    eligible = [trial for trial in trials if trial["feasible"]]
    if not eligible:
        raise ValueError("no feasible tuning config; check label completeness, objective and mean-doc budget")
    best = max(eligible, key=lambda trial: (trial["objective_value"], -trial["metrics"]["mean_docs"], -trial["trial"]))
    return {"best_config": best["config"], "best_trial": best["trial"], "best_metrics": best["metrics"],
            "objective": objective, "max_mean_docs": max_mean_docs, "tune_query_ids": sorted(ids),
            "trial_count": len(trials), "trials": trials,
            "selection_policy": "maximize objective within mean-doc budget, then minimize mean docs, then menu order"}
