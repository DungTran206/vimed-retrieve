"""Kiểm hai bất biến của bước chọn doc bằng đặc trưng (baseline.ltr_docs)."""
import unittest
import json
import tempfile
from pathlib import Path

import numpy as np

from baseline.ltr_docs import load_labels, quantile_map, select, select_q


class TestLtrDocs(unittest.TestCase):
    def test_qwen_labels_without_g_use_gold_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "val_fixed.jsonl"
            path.write_text(json.dumps({"id": 7, "query": "q", "gold": [1], "not_gold": [2, 3]}) + "\n", encoding="utf-8")
            val, gold, lab = load_labels(path)
        self.assertEqual(val[7]["G"], 1)
        self.assertEqual(gold[7], {"1"})
        self.assertEqual(lab[7], {"1", "2", "3"})

    def test_quantile_map_keeps_order_and_reference_distribution(self):
        s = np.array([3.0, -1.0, 7.0, 0.5])
        ref = [0.4, 0.1, 0.9, 0.2]
        out = quantile_map(s, ref)
        self.assertEqual(sorted(out), sorted(ref))
        self.assertEqual(list(np.argsort(out)), list(np.argsort(s)))

    def test_common_threshold_keeps_k_mean_per_query_and_never_empty(self):
        S2 = {"1": [["a", 0.9], ["b", 0.8], ["c", 0.7]], "2": [["x", 0.1], ["y", 0.05]]}
        D, thr = select(S2, k_mean=1)
        self.assertEqual(sum(len(v) for v in D.values()), 3)   # 2 cặp cao nhất + 1 doc giữ cho câu rỗng
        self.assertEqual(D["1"], ["a", "b"])
        self.assertEqual(D["2"], ["x"])
        self.assertEqual(thr, 0.8)

    def test_per_query_cut_maximises_expected_f2(self):
        # Ĝ = 1,85 → 5Σp/(4Ĝ+k): k1 0,107 · k2 0,181 · k3 0,173 · k4 0,162 → giữ 2; câu điểm thấp vẫn ≥ 1 doc
        D = select_q({"1": [("c", 0.1), ("a", 0.9), ("d", 0.05), ("b", 0.8)], "2": [("x", 0.001)]}, c=1.0)
        self.assertEqual(D["1"], ["a", "b"])
        self.assertEqual(D["2"], ["x"])


if __name__ == "__main__":
    unittest.main()
