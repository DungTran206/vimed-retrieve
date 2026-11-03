"""Gộp nhiều nguồn ứng viên bằng RRF (Reciprocal Rank Fusion); baseline.cands dùng `load` và `rrf`.

    score(d) = Σ_i  w_i / (k + rank_i(d))        rank bắt đầu từ 1

Vì sao RRF chứ không cộng điểm thô: điểm BM25 và điểm slug **không cùng thang** (slug ~39,
BM25 ~21 cho cùng câu hỏi) và phân bố khác nhau, nên cộng trực tiếp là để nguồn có điểm lớn
hơn áp đảo mà không có lý do gì. RRF chỉ dùng **hạng**, nên miễn nhiễm với thang điểm.

`k` làm phẳng phần đầu: k lớn thì các hạng đầu gần bằng nhau (tin nguồn ít hơn), k nhỏ thì
hạng 1 áp đảo. k=60 là giá trị kinh điển trong bài gốc của Cormack 2009.

Đo được ngày 02/10: slug và BM25 lệch nhau **87,4% doc** ở top-200 (Jaccard 0,070) mà cả hai
đều ăn điểm (slug DOCS_F2 0,0821 · BM25 0,0872) → đúng tình huống RRF có lãi nhất.

  python index/fuse.py data/slug_rank.jsonl data/bm25_rank.jsonl --out data/fused.jsonl
  python index/fuse.py data/slug_rank.jsonl:1 data/bm25_rank.jsonl:2 --out data/fused.jsonl
  python index/fuse.py --demo
"""
import argparse
import collections
import json
import sys


def load(path):
    """{qid: [doc_id theo hạng]}"""
    out = {}
    for line in open(path, encoding="utf-8"):
        o = json.loads(line)
        out[int(o["id"])] = [str(c["doc_id"]) for c in o["candidates"]]
    return out


def rrf(sources, k=60, topk=1000):
    """`sources`: [(tên, {qid: [doc_id]}, trọng số)]. Trả {qid: [(score, doc_id)]}."""
    qids = sorted({q for _, r, _ in sources for q in r})
    out = {}
    for qid in qids:
        acc = collections.defaultdict(float)
        for _, ranks, w in sources:
            for i, doc_id in enumerate(ranks.get(qid, []), start=1):
                acc[doc_id] += w / (k + i)
        # Sắp theo điểm giảm dần; doc_id làm khoá phụ để kết quả tái lập được
        out[qid] = sorted(((s, d) for d, s in acc.items()),
                          key=lambda t: (-t[0], t[1]))[:topk]
    return out


def coverage(sources, fused, at=200):
    """Mỗi nguồn góp bao nhiêu phần vào top-`at` sau khi gộp."""
    print(f"\nĐóng góp vào top-{at} sau khi gộp:")
    for name, ranks, w in sources:
        tot = hit = 0
        for qid, fl in fused.items():
            top = {d for _, d in fl[:at]}
            src = set(ranks.get(qid, [])[:at * 2])
            tot += len(top)
            hit += len(top & src)
        print(f"  {name:34} w={w:<4} {hit/max(tot,1)*100:5.1f}% số slot")


def demo():
    """Self-check: RRF miễn nhiễm thang điểm, trọng số có tác dụng, kết quả tái lập được."""
    # Hai nguồn, thang điểm chênh nhau 1000 lần -> RRF phải CHO CÙNG kết quả
    A = {1: ["a", "b", "c"]}
    B = {1: ["c", "b", "a"]}
    r1 = rrf([("A", A, 1.0), ("B", B, 1.0)], k=60)
    # Đối xứng hoàn toàn: a và c cùng điểm (hạng 1+3), b ở giữa (2+2)
    sc = dict((d, s) for s, d in r1[1])
    assert abs(sc["a"] - sc["c"]) < 1e-12, sc
    assert sc["b"] < sc["a"], sc      # 2/62 x2 < 1/61 + 1/63

    # Trọng số: ưu tiên B thì thứ tự của B phải thắng
    r2 = rrf([("A", A, 1.0), ("B", B, 5.0)], k=60)
    assert [d for _, d in r2[1]][0] == "c", r2[1]
    r3 = rrf([("A", A, 5.0), ("B", B, 1.0)], k=60)
    assert [d for _, d in r3[1]][0] == "a", r3[1]

    # Doc chỉ có ở MỘT nguồn vẫn được vào, xếp sau doc có ở cả hai
    C = {1: ["x", "y"]}
    D = {1: ["x", "z"]}
    out = [d for _, d in rrf([("C", C, 1.0), ("D", D, 1.0)], k=60)[1]]
    assert out[0] == "x", out
    assert set(out) == {"x", "y", "z"}, out

    # k nhỏ -> hạng 1 áp đảo; k lớn -> các hạng đầu gần bằng nhau
    E = {1: ["p", "q"]}
    F = {1: ["q", "r"]}
    small = dict((d, s) for s, d in rrf([("E", E, 1.0), ("F", F, 1.0)], k=1)[1])
    big = dict((d, s) for s, d in rrf([("E", E, 1.0), ("F", F, 1.0)], k=1000)[1])
    assert small["q"] / small["r"] > big["q"] / big["r"], (small, big)

    # topk giới hạn đúng, và câu không có ở nguồn nào thì rỗng
    assert len(rrf([("A", A, 1.0)], topk=2)[1]) == 2
    assert rrf([("A", {9: []}, 1.0)])[9] == []

    # Tái lập được: cùng đầu vào -> cùng đầu ra, kể cả khi điểm bằng nhau
    assert rrf([("A", A, 1.0), ("B", B, 1.0)]) == rrf([("A", A, 1.0), ("B", B, 1.0)])
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sources", nargs="*", metavar="FILE[:TRỌNG_SỐ]")
    ap.add_argument("--k", type=int, default=60, help="hằng số RRF (kinh điển: 60)")
    ap.add_argument("--topk", type=int, default=1000)
    ap.add_argument("--out", default="data/fused.jsonl")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    demo()
    if len(a.sources) < 2:
        sys.exit("Cần ít nhất 2 nguồn. Vd: python index/fuse.py data/slug_rank.jsonl data/bm25_rank.jsonl")

    srcs = []
    for spec in a.sources:
        path, _, w = spec.rpartition(":")
        if not path or "/" in w or "\\" in w:   # không có ':' -> toàn bộ là đường dẫn
            path, w = spec, "1"
        ranks = load(path)
        srcs.append((path.split("/")[-1], ranks, float(w)))
        print(f"Nạp {path}: {len(ranks)} câu, "
              f"trung bình {sum(len(v) for v in ranks.values())/max(len(ranks),1):.0f} ứng viên/câu, "
              f"trọng số {w}")

    fused = rrf(srcs, a.k, a.topk)
    with open(a.out, "w", encoding="utf-8") as f:
        for qid in sorted(fused):
            hits = [{"doc_id": d, "score": round(s, 6)} for s, d in fused[qid]]
            f.write(json.dumps({"id": qid, "candidates": hits}, ensure_ascii=False) + "\n")
    nz = sum(1 for v in fused.values() if v)
    print(f"\nĐã ghi {a.out} | k={a.k} | câu có ứng viên: {nz}/{len(fused)} | "
          f"trung bình {sum(len(v) for v in fused.values())/max(len(fused),1):.0f} ứng viên/câu")
    coverage(srcs, fused)


if __name__ == "__main__":
    sys.exit(main())
