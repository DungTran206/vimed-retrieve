"""Kiểm hai bất biến của bước chọn doc bằng đặc trưng (baseline.ltr_docs)."""
import unittest

import numpy as np

from baseline.ltr_docs import quantile_map, select


class TestLtrDocs(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
