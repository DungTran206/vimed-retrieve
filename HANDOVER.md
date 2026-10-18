# Bàn giao: dựng lại bài tốt nhất (FINAL 0,3442)

Bài: `w045_TF` — doc F2 0,3605 · chunk F2 0,3279 (leaderboard 15/10/2026). Tập doc = `w045_zh38w_e120` (0,3272);
chỉ khác ở cách cấp chunk theo p(gold) (`val_calib.py`), lãi +0,017.
Vân tay khi dựng đúng: **doc `c1e068422e5f`, chunk `fd07f9fc029a`**.

## 0. Kiến trúc pipeline hiện tại (từ đầu đến bài nộp)

```
[A] DỮ LIỆU (local + máy GPU)
  profile_dataset.py              tải ViBioMIR → data/queries.jsonl
  crawler.py                      crawl URL kho mới (resume, rate limit theo domain) → store sqlite
  merge_zh_new.py                 gộp các đợt crawl zh vào store (ghi đè dòng lỗi cũ)
  make_store_new.py               store gọn: CHỈ doc kho mới + vinmec → data/corpus_new.sqlite
  clean.py --apply                bỏ dòng boilerplate lặp theo domain   (BẮT BUỘC trước chunk.py)
  chunk.py                        chunk ~900 token theo OFFSET (doc_id, start, end) → bảng chunk
  audit.py                        kiểm toàn chuỗi trên dữ liệu thật (PASS/FAIL)
  export_vi_full.py / export_delta.py   xuất doc vi (toàn bộ / phần mới) ra sqlite nhỏ cho máy GPU


[B] XỬ LÝ CÂU HỎI (máy GPU)
  query_processing/ + scripts/remote_run_llm.sh   Qwen3.5-9B: thực thể y khoa + bản dịch en/zh
                                  → data/queries_enriched.jsonl (109 câu lỗi parse đã vá, xem PROGRESS 11/10)

[C] TRUY HỒI vi: 6 nguồn → RRF (pool H, top-1000)
  slug_bm25.py                    BM25 trên slug URL                     → slug_rank1000
  bm25.py --keep-diacritics       BM25F có dấu (title 3×, tags 2×, ...) → bm25d3_rank, bm25d3_meta
  bm25_ent.py                     BM25 thực thể + bigram                 → bm25ent3_rank
  dense.py (BGE-M3)               title / title+600 ký tự body          → dense_vi3_rank, dense_viB3_rank
     (scripts/run_bm25_full.sh, scripts/run_delta2.sh)
  index/fuse.py  slug:1 bm25d3:1 meta:1 dense_vi3:2.5 dense_viB3:2.5 ent:1  → f_H

[D] RERANK + CHUNK-DENSE (máy GPU)
  qwen_rerank.py (Qwen3-Reranker-4B, P(yes)) chấm top-400 của pool (scripts/wait_and_run_qwen_h.sh)
  merge_scores.py                 hợp các đợt chấm Qwen → qwen_all_h
  index/fuse.py  qwen_all_h:2 f_H:1 → QB6 ;  qwen_all_h:0.5 f_H:1 → QB6w05 ;  index/hybrid_cands.py → QB6_h05
  dense_chunks.py (BGE-M3 trên TỪNG chunk, toàn kho vi; scripts/run_dense_chunks_full.sh)
                                  điểm doc = chunk khớp nhất, kèm best_idx → dense_chunk_full_rank
  index/fuse.py  QB6_h05:1 dense_chunk_pilot:1 → QB7   (pilot: chunk-dense trên top-400 pool H)
  index/fuse.py  QB7:1 chunk_full:1 → blendQB8 ;  :0.5 → blendQB8w05
     → (vá 109 câu) data/rp/c_blendQB8.jsonl, c_blendQB8w05.jsonl         ← ĐẦU VÀO của build_best.sh
  chunk_rerank.py (Qwen chấm chunk) + best_idx → data/chunk_scores_mix.jsonl (chọn chunk nộp)

[E] TRUY HỒI zh (máy GPU / Colab)
  dense.py BGE-M3 trên 226k doc zh kho mới (scripts/run_zh_new.sh)        → dense_zhC3_*_rank
  Qwen3-Embedding-8B cùng doc (scripts/run_zh_q8.sh hoặc scripts/zh_q8_colab.ipynb trên Colab A100) → dense_zhQ8_*_rank

[F] GHÉP + NỘP (local, build_best.sh)
  zh list = RRF(BGE 1 : 8B 0,3) → chen vào vi (W0,45) → thứ tự đầu theo c_blendQB8w05 → lọc kho mới
  val_calib.py --score            p(gold) mỗi doc = logistic(logit P(yes) Qwen, cosine chunk-dense, cosine zh BGE)
                                  β khớp từ ĐIỂM TỔNG 41 bài đã chấm (val_calib.py --logit → data/val/beta.json)
  kế hoạch chunk: top-120 p<0,04 → bỏ chunk; hạng 121–200 p≥0,05 → thêm 1 chunk
  submission.py --chunk-plan → ZIP LZMA (200 doc/câu; 2 chunk × top-40 + 1 chunk × hạng 41–120, theo kế hoạch)
```

Mô hình: Qwen3.5-9B, BAAI/bge-m3, Qwen3-Reranker-4B, Qwen3-Embedding-8B (đều mở, ≤15B, trước 01/08/2026).
Số đo từng bước và lý do từng quyết định: `PROGRESS.md` (sổ đo theo ngày), `METHODS.md` (từng phương pháp, đã đo gì),
`CLAUDE.md` (bối cảnh cuộc thi, luật chấm, hạ tầng). Thử nghiệm thất bại (HyDE, tách ý con, viết gọn câu, chunk 450...)
được ghi trong PROGRESS nhưng code của chúng KHÔNG đưa vào repo.

## 1. Code để dựng lại nhanh (bước F)

| File | Vai trò |
| --- | --- |
| `build_best.sh` | chạy cả chuỗi dưới đây, in vân tay để đối chiếu |
| `index/fuse.py` | RRF nhiều danh sách xếp hạng |
| `index/hybrid_cands.py` | lấy TẬP doc từ một danh sách, THỨ TỰ 120 doc đầu từ danh sách khác |
| `crawl/filter_new_corpus.py` | chỉ giữ doc thuộc kho mới của BTC (+ vinmec), bù đủ 200 |
| `scripts/val_calib.py` | chấm p(gold) cho doc (`--score`); khớp lại β khi có điểm mới (`--extract`, `--logit`) |
| `submit/submission.py` | xuất JSON + ZIP đúng định dạng (doc_id số nguyên, chunk nguyên văn theo offset); `--chunk-plan` |

Cần Python 3.10+ với `pandas`, `pyarrow`, `numpy` (`pip install pandas pyarrow numpy`), và bash (Linux/macOS, hoặc Git Bash trên Windows).

## 2. Dữ liệu (KHÔNG có trong git — lấy riêng, đặt đúng đường dẫn)

| File | Cỡ | Là gì |
| --- | --- | --- |
| `data/corpus_new.sqlite` | 5,5 GB | văn bản đã crawl + clean của kho mới (vi + zh, kèm vinmec), bảng `chunk` (offset, chunk ~900 token) |
| `data/rp/c_blendQB8.jsonl` | 29 MB | xếp hạng vi cuối cùng (BM25/dense/chunk-dense → Qwen3-Reranker-4B → RRF) |
| `data/rp/c_blendQB8w05.jsonl` | 29 MB | như trên, trọng số Qwen 0,5 — dùng cho THỨ TỰ 120 doc đầu |
| `data/dense_zhC3_{vi,zhq,zhq109}_rank.jsonl` | 103 MB | xếp hạng zh bằng BGE-M3 (câu vi / câu dịch zh / 109 câu dịch vá) |
| `data/dense_zhQ8_{vi,zhq,zhq109}_rank.jsonl` | 103 MB | như trên bằng Qwen3-Embedding-8B |
| `data/chunk_scores_mix.jsonl` | 79 MB | điểm từng chunk để chọn chunk nộp |
| `data/vibiomir_new/links_corpus_vi_en_zh.parquet` | 37 MB | danh sách kho mới của BTC |
| `data/qwen_all_h.jsonl` | 27 MB | P(yes) Qwen3-Reranker-4B cho ~555 doc/câu (đặc trưng của p(gold)) |
| `data/dense_chunk_full_rank.jsonl` | 67 MB | cosine chunk-dense BGE-M3 (đặc trưng của p(gold)) |
| `data/val/beta.json` | 160 B | hệ số logistic của p(gold) |

Gói chia sẻ: `vimed_data_nho.zip` (13 file cũ) + `vimed_data_val.zip` (3 file p(gold) mới) — giải nén tại thư mục gốc repo,
giữ nguyên đường dẫn `data/...`; cộng `data/corpus_new.sqlite` tải riêng.



## 3. Chạy

```bash
bash build_best.sh runs/best      # ~30–40 phút, không cần GPU → runs/best.zip (~58 MB, LZMA)
```

Dòng cuối phải in `vân tay: doc=c1e068422e5f chunk=fd07f9fc029a`. Khác là thiếu/sai file dữ liệu.

## 4. Chuỗi làm gì

1. **zh**: mỗi model (BGE-M3, Qwen3-Emb-8B) lấy top-400 theo câu vi và top-400 theo câu dịch zh →
   RRF với trọng số BGE 1 : 8B 0,3 (8B một mình THUA BGE trên leaderboard; chỉ có ích làm tín hiệu đồng thuận) → lọc kho mới.
2. **Chen zh vào vi**: RRF(danh sách vi w1, danh sách zh w0,45) → ~39 doc zh/câu, rơi vào hạng 121–200.
3. **Thứ tự đầu**: 120 doc đầu xếp theo `c_blendQB8w05` (chunk chỉ lấy từ top-120 nên thứ tự đầu quyết định chunk).
4. **p(gold)**: logistic trên đặc trưng sẵn có, khớp bằng điểm TỔNG của các bài đã chấm (mỗi bài = một phương trình
   DOCS_P = TB p) — KHÔNG dò nhãn từng câu. Không đổi tập doc, chỉ dùng để quyết định chunk.
5. **Nộp**: 200 doc/câu; chunk = 2 chunk × 40 doc đầu + 1 chunk × doc hạng 41–120 (chọn chunk điểm cao nhất),
   bỏ chunk của doc top-120 có p<0,04, thêm 1 chunk cho doc hạng 121–200 có p≥0,05. Ngưỡng dò trên leaderboard:
   (bỏ, đuôi) = (0,06, 0,15) 0,3420 · (0,09, 0,15) 0,3381 · (0,06, 0,10) 0,3429 · (0,06, 0,07) 0,3436 · (0,04, 0,05) **0,3442**.
   Lấy hết đuôi (e200) từng THUA → đỉnh nằm giữa.

Các bước NẶNG tạo ra file ở mục 2 (crawl, clean, chunk, BM25, BGE-M3, Qwen3-Reranker-4B, chunk-dense) cần GPU
và nhiều ngày máy; không cần chạy lại để tái lập bài này.

## 5. Lưu ý khi nộp

- Leaderboard giới hạn **dung lượng lưu trữ mỗi tài khoản**: hết chỗ thì xoá file bài cũ ở trang Resources.
- ZIP tối đa 100 MB. `--zip-method lzma` nhỏ hơn bzip2 ~35% (server chấp nhận).
- `doc_id` PHẢI là số nguyên (`--int-ids`), kiểu chuỗi → điểm 0.
