"""PRF dense (Rocchio): trung bình vector BGE-M3 của top-N doc trong một danh sách hạt giống -> doc láng giềng gần nhất trong kho vi.

Sinh data/prf20_rank.jsonl, một trong 12 danh sách làm đặc trưng hạng ở baseline.ltr_feats. Hạt giống `blendQB3.jsonl` là
danh sách đã rerank của phiên bản pipeline trước (07/10, lấy từ Drive); `emb_viB2` = vector BGE-M3 title + 600 ký tự kho vi
(index.dense --encode --body-chars 600). Chạy local, CPU, vài chục giây:
  python -m index.prf --seed data/blendQB3.jsonl --emb data/emb_viB2 --top 20 --out data/prf20_rank.jsonl
"""
import argparse
import json
import sys

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default="data/blendQB3.jsonl")
    ap.add_argument("--emb", default="data/emb_viB2")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--topk", type=int, default=1000)
    ap.add_argument("--block", type=int, default=100_000)
    ap.add_argument("--out", default="data/prf20_rank.jsonl")
    a = ap.parse_args()
    E = np.load(a.emb + ".npy", mmap_mode="r")
    ids = json.load(open(a.emb + ".ids.json"))
    pos = {str(d): i for i, d in enumerate(ids)}
    seeds = {}
    for l in open(a.seed, encoding="utf-8"):
        r = json.loads(l)
        seeds[r["id"]] = [str(c["doc_id"]) for c in r["candidates"]][:a.top]
    qids = sorted(seeds)
    Q = np.zeros((len(qids), E.shape[1]), np.float32)
    miss = 0
    for k, q in enumerate(qids):
        idx = [pos[d] for d in seeds[q] if d in pos]
        miss += a.top - len(idx)
        if idx:
            v = np.asarray(E[sorted(idx)], np.float32).mean(0)
            Q[k] = v / (np.linalg.norm(v) + 1e-9)
    print(f"seed không có vector: {miss/len(qids):.1f}/câu", flush=True)
    best_s = np.full((len(qids), a.topk), -9, np.float32)
    best_i = np.zeros((len(qids), a.topk), np.int64)
    for s in range(0, len(ids), a.block):
        B = np.asarray(E[s:s + a.block], np.float32)
        S = Q @ B.T
        cand_s = np.concatenate([best_s, S], 1)
        cand_i = np.concatenate([best_i, np.broadcast_to(np.arange(s, s + len(B)), S.shape)], 1)
        top = np.argpartition(-cand_s, a.topk - 1, axis=1)[:, :a.topk]
        best_s = np.take_along_axis(cand_s, top, 1)
        best_i = np.take_along_axis(cand_i, top, 1)
        print(f"  {s + len(B):,}/{len(ids):,}", flush=True)
    with open(a.out, "w", encoding="utf-8") as o:
        for k, q in enumerate(qids):
            order = np.argsort(-best_s[k])
            o.write(json.dumps({"id": q, "candidates": [{"doc_id": ids[best_i[k][j]], "score": round(float(best_s[k][j]), 6)}
                                                        for j in order]}, ensure_ascii=False) + "\n")
    print("->", a.out)


if __name__ == "__main__":
    sys.exit(main())
