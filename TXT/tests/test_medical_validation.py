"""Calibration checks and label-leakage guards for cached replay."""
import unittest
from unittest.mock import patch

from TXT.bear.medical_scoring import normalize_bm25
from TXT.bear.medical_validation import (
    calibration_samples, evaluate_rankings, fit_sigmoid, split_query_ids,
    tune_configs, validation_from_rows,
)


class TestMedicalValidation(unittest.TestCase):
    def test_native_val_keeps_explicit_negatives_and_unknowns_distinct(self):
        labels = validation_from_rows([{"id": 1, "gold": [11, 12], "not_gold": [13], "G": 3, "gold_unseen": 1}])
        self.assertEqual(labels[1]["qrels"], {"11": 1, "12": 1, "13": 0})
        self.assertEqual(labels[1]["total_gold"], 3)
        self.assertFalse(labels[1]["complete"])
        with self.assertRaises(ValueError):
            validation_from_rows([{"id": 1, "gold": [11], "not_gold": [11]}])

    def test_explicit_qrels_adapter_rejects_graded_or_conflicting_labels(self):
        labels = validation_from_rows([{"query_id": 1, "doc_id": "a", "relevance": 1},
                                      {"query_id": 1, "doc_id": "b", "relevance": 0}])
        self.assertEqual(labels[1]["total_gold"], 1)
        with self.assertRaises(ValueError):
            validation_from_rows([{"query_id": 1, "doc_id": "a", "relevance": 2}])

    def test_query_split_is_reproducible_and_duplicate_queries_do_not_leak(self):
        rows = [{"id": i, "query": f"disease {i}"} for i in range(20)]
        rows[1]["query"] = " DISEASE   0 "
        first = split_query_ids(rows)
        self.assertEqual(first, split_query_ids(rows))
        groups = [set(first[name]) for name in ("calibration", "tune", "holdout")]
        self.assertEqual(set.union(*groups), set(range(20)))
        self.assertFalse(groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2])
        self.assertTrue(any({0, 1} <= group for group in groups))
        self.assertFalse(first["holdout_pristine"])
        recorded = split_query_ids(rows, exposure_status="recorded")
        self.assertTrue(recorded["holdout_pristine"])
        observed = split_query_ids(rows, previously_observed_ids=first["holdout"])
        self.assertFalse(observed["holdout_pristine"])
        all_observed = split_query_ids(rows, previously_observed_ids="all", exposure_status="recorded")
        self.assertEqual(all_observed["previously_observed_ids"], list(range(20)))
        self.assertFalse(all_observed["holdout_pristine"])

    def test_sigmoid_fit_improves_over_constant_and_returns_inference_parameters(self):
        samples = [(float(x), int(x >= 5)) for x in range(10)]
        result = fit_sigmoid(samples)
        self.assertGreater(result["temperature"], 0)
        self.assertAlmostEqual(result["x0"], 4.5, places=3)
        self.assertLess(result["weighted_brier"], 0.25)
        self.assertGreater(normalize_bm25(8, result), normalize_bm25(2, result))
        self.assertTrue(result["converged"])
        with self.assertRaises(ValueError):
            fit_sigmoid([(1, 1), (2, 1)])
        with self.assertRaises(ValueError):
            fit_sigmoid([(1, 1), (1, 0)])

    def test_inverse_signal_cannot_reverse_bm25_order(self):
        result = fit_sigmoid([(float(x), int(x < 5)) for x in range(10)])
        self.assertGreater(result["temperature"], 0)
        self.assertTrue(result["near_flat"])
        self.assertGreaterEqual(normalize_bm25(9, result), normalize_bm25(0, result))

    def test_fit_is_invariant_to_common_weight_scaling_and_huge_weights(self):
        samples = [(float(x), int(x >= 4), 1.0) for x in range(10)]
        baseline = fit_sigmoid(samples)
        huge = fit_sigmoid([(x, y, 1e308) for x, y, _ in samples])
        self.assertAlmostEqual(baseline["x0"], huge["x0"])
        self.assertAlmostEqual(baseline["temperature"], huge["temperature"])

    def test_calibration_uses_exact_blend_and_excludes_unjudged(self):
        rows = [{"id": 1, "query_scale": 2, "candidates": [
            {"doc_id": "a", "scores": {"bm25": 4, "bm25_expanded": 8}},
            {"doc_id": "b", "scores": {"bm25": 2, "bm25_expanded": 6}},
            {"doc_id": "unknown", "scores": {"bm25": 99, "bm25_expanded": 99}},
        ]}]
        labels = validation_from_rows([{"id": 1, "qrels": {"a": 1, "b": 0}}])
        samples = calibration_samples(rows, labels, [1], {"bm25": {
            "enrichment_weight": 0.5, "pretransform": "query_scale"}})
        self.assertEqual(samples, [(3, 1, 0.5), (2, 0, 0.5)])
        rows[0]["query_scale_compatible"] = False
        with self.assertRaisesRegex(ValueError, "unrelated index scale"):
            calibration_samples(rows, labels, [1], {"bm25": {"pretransform": "query_scale"}})

    def test_incomplete_judgments_do_not_produce_true_f2(self):
        labels = validation_from_rows([{"id": 1, "qrels": {"a": 1, "b": 0}}])
        result = evaluate_rankings([{"id": 1, "doc_ids": ["a", "unknown"]}], labels)
        self.assertEqual(result["known_positive_recall"], 1)
        self.assertEqual(result["selected_unjudged_count"], 1)
        self.assertIsNone(result["macro_doc_f2"])
        self.assertIsNone(result["known_positive_f2_proxy"])
        labels[1]["complete"] = True
        complete = evaluate_rankings([{"id": 1, "doc_ids": ["a", "b"]}], labels)
        self.assertAlmostEqual(complete["macro_doc_f2"], 5 / 6)

    def test_finite_tuning_obeys_mean_document_budget(self):
        rows = [{"id": 1, "concepts": [], "candidates": [
            {"doc_id": "a", "scores": {"bm25": 5, "dense_head": 0.9, "dense_chunk": 0.9}},
            {"doc_id": "b", "scores": {"bm25": -5, "dense_head": -0.8, "dense_chunk": -0.8}},
        ]}]
        labels = validation_from_rows([{"id": 1, "qrels": {"a": 1, "b": 0}}])
        configs = [{"selection": {"threshold": 0}}, {"selection": {"threshold": 0.5}}]
        result = tune_configs(rows, labels, [1], configs, max_mean_docs=1)
        self.assertEqual(result["best_trial"], 1)
        self.assertEqual(result["best_metrics"]["mean_docs"], 1)
        self.assertFalse(result["trials"][0]["feasible"])
        with self.assertRaises(ValueError):
            tune_configs(rows, labels, [1], configs, objective="macro_doc_f2")

    def test_tuning_replays_factory_and_discards_full_rankings(self):
        calls = []
        def records():
            calls.append(len(calls) + 1)
            for qid in (1, 2):
                yield {"id": qid, "concepts": [], "candidates": [
                    {"doc_id": "a", "scores": {"bm25": 5, "dense_head": 0.9, "dense_chunk": 0.9}},
                    {"doc_id": "b", "scores": {"bm25": -5, "dense_head": -0.8, "dense_chunk": -0.8}},
                ]}
        labels = validation_from_rows([{"id": qid, "qrels": {"a": 1, "b": 0}} for qid in (1, 2)])
        menus = [{"selection": {"threshold": 0.5}}, {"selection": {"threshold": 1}}]
        def evaluate_lightweight(outputs, *args, **kwargs):
            self.assertEqual(len(outputs), 2)
            self.assertTrue(all(set(row) == {"id", "doc_ids", "selection"} for row in outputs))
            return evaluate_rankings(outputs, *args, **kwargs)
        with patch("TXT.bear.medical_validation.evaluate_rankings", side_effect=evaluate_lightweight):
            result = tune_configs(records, labels, [1, 2], menus, max_mean_docs=1)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(result["best_trial"], 0)
        self.assertEqual(result["best_metrics"]["known_positive_recall"], 1)

    def test_tuning_factory_checks_duplicate_and_missing_ids_on_every_trial(self):
        record = {"id": 1, "concepts": [], "candidates": []}
        labels = validation_from_rows([{"id": 1, "qrels": {"a": 1}}])
        menus = [{}, {}]
        for variant in ("duplicate", "missing"):
            calls = []
            def factory():
                calls.append(1)
                if len(calls) == 1:
                    yield record
                elif variant == "duplicate":
                    yield record
                    yield record
            with self.subTest(variant=variant), self.assertRaisesRegex(ValueError, variant):
                tune_configs(factory, labels, [1], menus)


if __name__ == "__main__":
    unittest.main()
