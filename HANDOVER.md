# Bàn giao: dựng lại bài tốt nhất (FINAL 0,3262)

Bài: `w04_zh38w_e120` — doc F2 0,3589 · chunk F2 0,2935 (leaderboard 15/10/2026).
Vân tay khi dựng đúng: **doc `7ea17e35e329`, chunk `72a9d14ce27c`**.

## 1. Code (trong repo)

| File | Vai trò |
| --- | --- |
| `build_best.sh` | chạy cả chuỗi dưới đây, in vân tay để đối chiếu |
| `fuse.py` | RRF nhiều danh sách xếp hạng |
| `hybrid_cands.py` | lấy TẬP doc từ một danh sách, THỨ TỰ 120 doc đầu từ danh sách khác |
| `filter_new_corpus.py` | chỉ giữ doc thuộc kho mới của BTC (+ vinmec), bù đủ 200 |
| `submission.py` | xuất JSON + ZIP đúng định dạng (doc_id số nguyên, chunk nguyên văn theo offset) |

Cần Python 3.10+ với `pandas`, `pyarrow` (`pip install pandas pyarrow`), và bash (Linux/macOS, hoặc Git Bash trên Windows).

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

Tuỳ chọn (tiếng Anh, CHƯA dùng vì bảng điểm chưa có nhãn en): `data/en_pubmed.sqlite` (0,5 GB, 240k bài PubMed),
`data/dense_en_{vi,en}_rank.jsonl`.

## 3. Chạy

```bash
bash build_best.sh runs/best      # ~20–30 phút, không cần GPU → runs/best.zip (~93 MB, bzip2)
```

Dòng cuối phải in `vân tay: doc=7ea17e35e329 chunk=72a9d14ce27c`. Khác là thiếu/sai file dữ liệu.

## 4. Chuỗi làm gì

1. **zh**: mỗi model (BGE-M3, Qwen3-Emb-8B) lấy top-400 theo câu vi và top-400 theo câu dịch zh →
   RRF với trọng số BGE 1 : 8B 0,3 (8B một mình THUA BGE trên leaderboard; chỉ có ích làm tín hiệu đồng thuận) → lọc kho mới.
2. **Chen zh vào vi**: RRF(danh sách vi w1, danh sách zh w0,4) → ~31 doc zh/câu, rơi vào hạng 121–200.
3. **Thứ tự đầu**: 120 doc đầu xếp theo `c_blendQB8w05` (chunk chỉ lấy từ top-120 nên thứ tự đầu quyết định chunk).
4. **Nộp**: 200 doc/câu; chunk = 2 chunk × 40 doc đầu + 1 chunk × doc hạng 41–120 (chọn chunk điểm cao nhất).

Các bước NẶNG tạo ra file ở mục 2 (crawl, clean, chunk, BM25, BGE-M3, Qwen3-Reranker-4B, chunk-dense) cần GPU
và nhiều ngày máy; không cần chạy lại để tái lập bài này.

## 5. Lưu ý khi nộp

- Leaderboard giới hạn **dung lượng lưu trữ mỗi tài khoản**: hết chỗ thì xoá file bài cũ ở trang Resources.
- ZIP tối đa 100 MB. `--zip-method lzma` nhỏ hơn bzip2 ~35% (server chấp nhận).
- `doc_id` PHẢI là số nguyên (`--int-ids`), kiểu chuỗi → điểm 0.
