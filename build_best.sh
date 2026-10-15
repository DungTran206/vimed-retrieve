#!/usr/bin/env bash
# Dựng lại bài tốt nhất từ các file trung gian đã giữ (tái lập được cho private phase).
#   bash build_best.sh [TÊN_ĐẦU_RA]          mặc định runs/rebuild
# Bài tốt nhất 15/10: FINAL 0,3262 (w04_zh38w_e120) — vân tay doc 7ea17e35e329, chunk 72a9d14ce27c.
# Chỉ làm các bước NHẸ cuối (~20–30 phút, local, không GPU). Các bước NẶNG phía trước (crawl → clean → chunk → BM25/dense →
# Qwen3-Reranker → chunk-dense → c_blendQB8*; mã hoá zh BGE-M3 / Qwen3-Emb-8B) xem METHODS.md và PROGRESS.md.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONUTF8=1
OUT=${1:-runs/rebuild}
need() { [ -s "$1" ] || { echo "THIẾU $1"; exit 1; }; }
for f in data/rp/c_blendQB8.jsonl data/rp/c_blendQB8w05.jsonl data/dense_zhC3_vi_rank.jsonl data/dense_zhC3_zhq_rank.jsonl \
         data/dense_zhC3_zhq109_rank.jsonl data/dense_zhQ8_vi_rank.jsonl data/dense_zhQ8_zhq_rank.jsonl \
         data/dense_zhQ8_zhq109_rank.jsonl data/vibiomir_new/links_corpus_vi_en_zh.parquet data/chunk_scores_mix.jsonl \
         data/corpus_new.sqlite; do need "$f"; done
mkdir -p data/rp

echo "1) danh sách zh: mỗi model lấy top-400 (câu vi) và top-400 (câu dịch zh, vá 109 câu dịch lỗi)"
python - <<'E'
import json
def rd(p): return {json.loads(l)["id"]: json.loads(l) for l in open(p, encoding="utf-8")}
def cut(R): return {i: {"id": i, "candidates": r["candidates"][:400]} for i, r in R.items()}
for m, tag in (("zhC3", "z3"), ("zhQ8", "z8")):
    v, q = cut(rd(f"data/dense_{m}_vi_rank.jsonl")), cut(rd(f"data/dense_{m}_zhq_rank.jsonl"))
    q.update(cut(rd(f"data/dense_{m}_zhq109_rank.jsonl")))
    for name, R in ((f"{tag}v", v), (f"{tag}q", q)):
        with open(f"data/rp/{name}.jsonl", "w", encoding="utf-8") as o:
            for i in sorted(R): o.write(json.dumps(R[i], ensure_ascii=False) + "\n")
E
echo "2) RRF BGE-M3 1 : Qwen3-Emb-8B 0,3 (8B một mình THUA BGE), lọc kho mới"
python fuse.py data/rp/z3v.jsonl:1 data/rp/z3q.jsonl:1 data/rp/z8v.jsonl:0.3 data/rp/z8q.jsonl:0.3 --topk 1000 --out data/rp/z38w_both.jsonl | tail -1
python - <<'E'
import json
import pandas as pd
new = set(pd.read_parquet("data/vibiomir_new/links_corpus_vi_en_zh.parquet")["id"].astype(str))
with open("data/rp/zh38w_in.jsonl", "w", encoding="utf-8") as o:
    for l in open("data/rp/z38w_both.jsonl", encoding="utf-8"):
        r = json.loads(l); Z = [str(c["doc_id"]) for c in r["candidates"] if str(c["doc_id"]) in new]
        o.write(json.dumps({"id": r["id"], "candidates": [{"doc_id": d, "score": round(1 - i / (len(Z) + 1), 6)}
                                                          for i, d in enumerate(Z)]}) + "\n")
E
echo "3) chen zh (W0,4 → ~31 zh/câu) vào danh sách vi; thứ tự 120 doc đầu theo c_blendQB8w05; lọc kho mới"
python fuse.py data/rp/c_blendQB8.jsonl:1 data/rp/zh38w_in.jsonl:0.4 --topk 1000 --out data/rp/q9_z38w_04.jsonl | tail -1
python hybrid_cands.py data/rp/q9_z38w_04.jsonl data/rp/c_blendQB8w05.jsonl 120 data/rp/q13_z38w_04.jsonl 200 | tail -1
python filter_new_corpus.py data/rp/q13_z38w_04.jsonl data/rp/q9_z38w_04.jsonl data/rp/q14_z38w_04.jsonl | tail -1
echo "4) dựng bài: top-200 doc, 2 chunk × 40 doc đầu + 1 chunk × hạng 41–120, chunk chọn theo điểm, bzip2"
python submission.py --cands data/rp/q14_z38w_04.jsonl --topk 200 --store data/corpus_new.sqlite \
    --chunks-per-doc 2 --chunk-from-top 40 --extra-one 120 --int-ids \
    --chunk-scores data/chunk_scores_mix.jsonl --zip-method bzip2 --out "$OUT"
rm -f "$OUT.json"
echo "Xong. Vân tay phải là doc=7ea17e35e329 chunk=72a9d14ce27c (w04_zh38w_e120, FINAL 0,3262)."
