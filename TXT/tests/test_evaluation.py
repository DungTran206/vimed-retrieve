"""Unit tests for BEAR evaluation contracts, token sequence LCS, and paired bootstrap statistics."""

from __future__ import annotations

import unittest

from TXT.bear.evaluation import (
    compute_doc_f2,
    compute_macro_doc_f2,
    compute_replacement_delta,
    lcs_token_length,
    passage_match_diagnostic,
)
from TXT.bear.paired import paired_group_bootstrap


class TestEvaluation(unittest.TestCase):
    def test_lcs_token_length_and_order(self) -> None:
        seq_a = ["a", "b", "c", "d"]
        seq_b = ["a", "c", "d"]
        self.assertEqual(lcs_token_length(seq_a, seq_b), 3)

        # Reversed order: LCS is only 1
        seq_rev = ["d", "c", "b", "a"]
        self.assertEqual(lcs_token_length(seq_a, seq_rev), 1)

        # Empty sequences
        self.assertEqual(lcs_token_length([], ["a"]), 0)
        self.assertEqual(lcs_token_length([], []), 0)

    def test_passage_match_diagnostic(self) -> None:
        gold = ["ung", "thư", "phổi", "giai", "đoạn", "muộn"]  # 6 tokens
        # 3 out of 6 tokens = 0.50 >= 0.40 -> True
        pred_match = ["ung", "thư", "phổi"]
        self.assertTrue(passage_match_diagnostic(pred_match, gold, "d1", "d1", threshold=0.40))

        # 2 out of 6 tokens = 0.333 < 0.40 -> False
        pred_low = ["ung", "thư"]
        self.assertFalse(passage_match_diagnostic(pred_low, gold, "d1", "d1", threshold=0.40))

        # Exact boundary 40%: 2 out of 5 tokens = 0.40 -> True
        gold_5 = ["t1", "t2", "t3", "t4", "t5"]
        pred_2 = ["t1", "t2"]
        self.assertTrue(passage_match_diagnostic(pred_2, gold_5, "d1", "d1", threshold=0.40))

        # Different doc_id -> False regardless of text match
        self.assertFalse(passage_match_diagnostic(gold, gold, "d1", "d2", threshold=0.40))

    def test_doc_f2_macro_vs_micro_and_empty_gold_policy(self) -> None:
        # q1: g=10, k=20, G=10 -> F2 = 5*10 / (4*10 + 20) = 50 / 60 = 0.8333
        # q2: g=0, k=20, G=10 -> F2 = 0
        # q3: g=0, k=20, G=0  -> empty gold query
        query_metrics = {
            1: (10, 20, 10),
            2: (0, 20, 10),
            3: (0, 20, 0),
        }

        # Policy 'excluded': only q1 and q2 are averaged
        macro_f2_ex = compute_macro_doc_f2(query_metrics, empty_gold_policy="excluded")
        expected_ex = (compute_doc_f2(10, 20, 10) + compute_doc_f2(0, 20, 10)) / 2.0
        self.assertAlmostEqual(macro_f2_ex, expected_ex, places=6)

        # Contrast with naive F2 of mean P and mean R (micro-style fallacy):
        # mean P = (10/20 + 0/20)/2 = 0.25; mean R = (10/10 + 0/10)/2 = 0.50
        # F2(P, R) = 5*P*R / (4*P + R) = 5*0.25*0.5 / (4*0.25 + 0.5) = 0.625 / 1.5 = 0.4166
        # Macro F2 = (0.8333 + 0)/2 = 0.4166 in this toy, but let's check with asymmetric k
        query_metrics_asym = {
            1: (5, 10, 10),   # F2 = 25 / 50 = 0.5
            2: (2, 20, 5),    # F2 = 10 / 40 = 0.25
        }
        macro_val = compute_macro_doc_f2(query_metrics_asym)
        self.assertAlmostEqual(macro_val, (0.5 + 0.25) / 2.0, places=6)

    def test_replacement_delta_and_completeness_guard(self) -> None:
        docs_a = ["d1", "d2", "d3", "d4"]
        docs_b = ["d1", "d2", "d5", "d6"]

        # 1. Unjudged document in added/removed must trigger 'not_available'
        qrels_partial = {"d1": 1, "d2": 1, "d3": 1}  # d4, d5, d6 missing
        res_partial = compute_replacement_delta(docs_a, docs_b, qrels_partial, k=4)
        self.assertEqual(res_partial["status"], "not_available")
        self.assertIn("d4", res_partial["unjudged_docs"])
        self.assertIsNone(res_partial["delta_hits"])

        # 2. Complete qrels: added={'d3', 'd4'}, removed={'d5', 'd6'}
        # A gains d3 (rel=1), d4 (rel=1) -> +2
        # B had d5 (rel=1), d6 (rel=0) -> -1
        # Net delta_hits = +1, delta_p = 1 / 4 = 0.25
        qrels_complete = {"d1": 1, "d2": 1, "d3": 1, "d4": 1, "d5": 1, "d6": 0}
        res_complete = compute_replacement_delta(docs_a, docs_b, qrels_complete, k=4)
        self.assertEqual(res_complete["status"], "available")
        self.assertEqual(res_complete["delta_hits"], 1)
        self.assertEqual(res_complete["delta_p"], 0.25)

        # Negative delta hits
        qrels_neg = {"d1": 1, "d2": 1, "d3": 0, "d4": 0, "d5": 1, "d6": 1}
        res_neg = compute_replacement_delta(docs_a, docs_b, qrels_neg, k=4)
        self.assertEqual(res_neg["delta_hits"], -2)
        self.assertEqual(res_neg["delta_p"], -0.50)

    def test_paired_group_bootstrap(self) -> None:
        # 10 queries, grouped in pairs (5 groups of 2)
        deltas = {
            1: 0.05, 2: 0.05,  # group 100
            3: 0.02, 4: 0.02,  # group 101
            5: 0.00, 6: 0.00,  # group 102
            7: 0.03, 8: 0.03,  # group 103
            9: -0.01, 10: -0.01, # group 104
        }
        groups = {
            1: 100, 2: 100,
            3: 101, 4: 101,
            5: 102, 6: 102,
            7: 103, 8: 103,
            9: 104, 10: 104,
        }

        res = paired_group_bootstrap(deltas, query_groups=groups, n_resamples=1000, seed=42)
        self.assertEqual(res["n_queries"], 10)
        self.assertEqual(res["n_groups"], 5)
        self.assertAlmostEqual(res["mean_delta"], 0.018, places=4)
        self.assertTrue(res["ci_lower"] < res["mean_delta"] < res["ci_upper"])
        self.assertEqual(res["wins"], 6)
        self.assertEqual(res["ties"], 2)
        self.assertEqual(res["losses"], 2)


if __name__ == "__main__":
    unittest.main()

