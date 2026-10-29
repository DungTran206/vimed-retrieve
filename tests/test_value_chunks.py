"""Kiểm các bất biến của luật giữ mảnh theo giá trị (baseline/value_chunks)."""
import unittest

from baseline.value_chunks import (gold_cells, keep_idx, line_bounds, merge_pi, merge_plan, overlap_spans, pack_pi,
                                   pack_spans, piece_pi, pieces)


class TestValueChunks(unittest.TestCase):
    def test_cells_are_distributions(self):
        for T in (1, 500, 1152, 5000, 30000):
            self.assertAlmostEqual(sum(p for _, _, p in gold_cells(T)), 1.0)
            self.assertTrue(all(0 <= s < e <= T for s, e, _ in gold_cells(T)))

    def test_short_doc_one_piece_always_matches(self):
        self.assertAlmostEqual(piece_pi([(0, 2000)], 2000, 500, 500)[0], 1.0)

    def test_long_doc_earlier_half_worth_more(self):
        first, second = piece_pi([(0, 5000), (5000, 10000)], 10000, 2600, 2600)
        self.assertTrue(0 < second < first < 1)

    def test_set_doc_keeps_best_piece_extra_doc_may_drop(self):
        pis = [0.2, 0.5]
        self.assertEqual(keep_idx(pis, 0.01, 0.09, in_set=True), [1])
        self.assertEqual(keep_idx(pis, 0.01, 0.09, in_set=False), [])
        self.assertEqual(keep_idx(pis, 0.5, 0.09, in_set=False), [0, 1])
        self.assertEqual(keep_idx(pis, 0.3, 0.09, in_set=False), [1])

    def test_overlap_only_between_kept_neighbours(self):
        t = "".join(f"câu số {i} nói về bệnh.\n" for i in range(400))
        sp = pieces(t, 3000)
        self.assertGreaterEqual(len(sp), 3)
        allk = overlap_spans(t, sp, list(range(len(sp))))
        for (a, b), (a0, b0), (sa, sb) in zip(allk, sp, [(0, 0)] + sp[:-1]):
            self.assertTrue(0 <= a <= a0 and b0 <= b <= len(t))
            self.assertLessEqual((a0 - a) + (b - b0), 2 * 200)
        self.assertEqual(allk[0][0], 0)
        self.assertEqual(allk[-1][1], len(t))
        self.assertGreater(allk[0][1], sp[0][1])           # mảnh đầu nới sang phải
        self.assertLess(allk[1][0], sp[1][0])              # mảnh sau nới sang trái
        gap = overlap_spans(t, sp, [0, 2])                 # không liền kề: giữ nguyên
        self.assertEqual(gap, [sp[0], sp[2]])

    def test_pack_spans_contiguous_capped_and_cover(self):
        b = "\n".join(("dòng " * k).strip() for k in (30, 5, 400, 40, 3, 60)) + "\n"
        starts, pos = [], 0                       # "token" = từ (giả lập): ký tự đầu mỗi từ của norm(b)
        from baseline.value_chunks import norm
        nb = norm(b)
        for i, ch in enumerate(nb):
            if ch != " " and (i == 0 or nb[i - 1] == " "):
                starts.append(i)
        toks, chrs = line_bounds(b, starts)
        self.assertEqual(toks[0], 0)
        self.assertEqual((toks[-1], chrs[-1]), (len(starts), len(b)))
        sp = pack_spans(toks, chrs, 100)
        self.assertEqual((sp[0][0], sp[0][2]), (0, 0))
        self.assertEqual((sp[-1][1], sp[-1][3]), (toks[-1], len(b)))
        for (_, e, _, ce), (s, _, cs, _) in zip(sp, sp[1:]):
            self.assertEqual((e, ce), (s, cs))   # liền mạch cả token lẫn ký tự
        self.assertTrue(all(e - s <= 100 for s, e, _, _ in sp))
        self.assertTrue(any(e - s == 100 for s, e, _, _ in sp))   # dòng 400 từ bị cắt cứng
        pis = pack_pi(toks, chrs, [(s, e) for s, e, _, _ in sp])
        self.assertEqual(len(pis), len(sp))
        self.assertTrue(all(0 <= x <= 1 for x in pis))

    def test_merge_plan(self):
        # hai mảnh π 0,5 mỗi mảnh, gộp lại khớp chắc (π 1): một chunk gộp thay vì hai chunk
        self.assertEqual(merge_plan([0.5, 0.5], [1.0], 0.5, 0.09, True), [(0, 2)])
        # gộp không giữ được khớp (π gộp 0,5): giữ riêng từng mảnh đáng giữ
        self.assertEqual(merge_plan([0.5, 0.5], [0.5], 0.5, 0.09, True), [(0, 1), (1, 2)])
        # không khoảng nào đáng giữ: doc trong tập ép giữ khoảng π lớn nhất, doc ngoài tập bỏ
        self.assertEqual(merge_plan([0.1, 0.3, 0.2], [0.35, 0.4], 0.05, 0.09, True), [(1, 3)])
        self.assertEqual(merge_plan([0.1, 0.3, 0.2], [0.35, 0.4], 0.05, 0.09, False), [])
        self.assertEqual(merge_plan([], [], 0.5, 0.09, True), [])

    def test_merge_pi_short_doc_and_pair(self):
        toks, chrs = [0, 600, 1200, 1800], [0, 2000, 4000, 6000]       # 3 dòng × 600 token
        self.assertAlmostEqual(merge_pi([0, 600], [0, 2000], [(0, 600)], 600)[0], 1.0)  # doc 1 dòng: chắc khớp
        one, pair = merge_pi(toks, chrs, [(0, 600), (0, 1800)], 1800)
        self.assertTrue(0 < one < 1 and 0 <= pair <= 1)

    def test_pieces_verbatim_and_cover(self):
        t = ("đoạn một.\n" * 300)[:2990] + "\n" + "甲乙丙。" * 700
        sp = pieces(t, 1860)
        self.assertEqual("".join(t[a:b] for a, b in sp), t)


if __name__ == "__main__":
    unittest.main()
