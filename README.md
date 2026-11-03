# ViMed Retrieval: bài `gbm3` + cắt k theo từng câu + gộp mảnh (FINAL public 0,4201)

Truy hồi y sinh đa ngôn ngữ (AI Guru R2AI 2026, bộ dữ liệu ViBioMIR). Mỗi câu hỏi tiếng Việt, hệ thống trả về
`relevant_docs` (doc vi/zh) và `relevant_chunks` (đoạn trích **nguyên văn** của các doc đó).

Cách chấm: `FINAL = (F2 doc + F2 chunk) / 2`, với F2 = 5PR / (4P + R) lấy trung bình theo câu.
Từ 23/10, một chunk được tính là khớp khi LCS ≥ 40% chunk vàng **và** ≥ 40% chunk dự đoán.

Repo này dựng lại **đúng từng byte** bài nộp từ các file dữ liệu trung gian (lấy từ Drive, xem §4).
Bài `gbm` đã kiểm trên một thư mục dữ liệu chỉ chứa các file trong danh sách Drive: JSON bài nộp có sha256
`ff54d83cb220…`. Các bài `gbm2`, `gbm2_m2`, `gbm3_m2`, `gbm3q_m2` dựng bằng chính code này: vân tay ở §6.

---

## 1. Kết quả

| Bài | Cách chọn doc | FINAL | Doc F2 | Chunk F2 | Kỳ vọng private |
|---|---|---|---|---|---|
| E `z80base160_v09x_ov_p1152` | p̂ gốc (Qwen3-Reranker-4B + hạng) | 0,3589 | 0,3938 | 0,3239 | ≈ public |
| F `z80dfull_v09x_ov_p1152` | p̂ × 8 hệ số theo ô (bài D) | 0,3628 | 0,3978 | 0,3279 | ≈ public |
| `z80bge1_v09x_ov_p1152` | p̂ − 1,0 × log-hạng BGE-M3 (**1 tham số**) | 0,3727 | 0,4091 | 0,3363 | ≈ public |
| `z80ltr_v09x_ov_p1152` | logistic, 44 đặc trưng | 0,3851 | 0,4213 | 0,3489 | ≈ public (đo chéo khớp leaderboard) |
| `z80gbm_v09x_ov_p1152` | HistGBM, 44 đặc trưng | 0,4035 | 0,4439 | 0,3631 | ~0,39 |
| `z80gbm2_v09x_ov_p1152` | HistGBM, 45 đặc trưng (+ cos BGE-M3 thô) | 0,4104 | 0,4515 | 0,3692 | ~0,395 |
| `z80gbm2_v09x_ov_p1152_m2` | như gbm2, chunk gộp mảnh (`--merge`) | 0,4111 | 0,4515 | 0,3708 | ~0,40 |
| `z80gbm3_v09x_ov_p1152_m2` | HistGBM, 55 đặc trưng (+ cos thô & tương đối 5 danh sách BGE-M3), `--merge` | 0,4189 | 0,4618 | 0,3759 | ~0,395 |
| **`z80gbm3q_v09x_ov_p1152_m2`** | **như gbm3_m2, k theo từng câu (`--cut-q`)** | **0,4201** | **0,4633** | **0,3769** | **~0,397** |

- **ltr:** đo chéo 5 fold theo câu dự báo doc F2 tăng +0,024 so với D; leaderboard đo được +0,0235.
- **gbm:** đo chéo chỉ dự báo +0,010 so với ltr, còn public lên +0,023. Khoảng +0,013 dư ra là phần mô hình cây
  học thuộc nhãn của chính các câu public. Vì vậy private nên kỳ vọng khoảng 0,39.
- **gbm2:** đo chéo dự báo doc +0,0048 so với gbm, public +0,0076 (~+0,003 khớp trong mẫu).
- **`--merge`:** cùng tập doc với gbm2, chỉ đổi chunk: P +0,0057, R −0,0104, chunk F2 +0,0016. Không học nhãn.
- **gbm3:** đo chéo dự báo doc +0,0049 so với gbm2, public +0,0103 (~+0,005 khớp trong mẫu). Mỗi bước học thêm từ
  nhãn public lại phình phần khớp trong mẫu, nên đo chéo mới là thước đo cho private.
- **`--cut-q`:** thay ngưỡng chung bằng k riêng mỗi câu = argmax F2 kỳ vọng 5·Σp/(4Ĝ+k), Ĝ = 1,48 × Σp (xác suất gbm3).
  Đo chéo doc +0,0039 ± 0,0017 (k TB 160 → 149); public doc +0,0015, chunk +0,0010. Public thấy ít hơn vì p trong
  mẫu sắc hơn p ngoài mẫu mà hằng 1,48 được khớp. Ngày 26/10 cùng cách với p̂ gốc thì thua ngưỡng chung.
- **Kỳ vọng private** = doc F2 đo chéo + ~0,005 (doc vàng "ẩn" mà nhãn val thiếu), rồi trừ phần public bị thổi.

## 2. Phát hiện chính: nhãn vàng ≈ "doc được BGE-M3 xếp cao"

Đo doc F2 bằng đo chéo 5 fold trên 593 câu public, giữ ngưỡng chung 160 doc/câu. Mỗi dòng thêm đặc trưng
vào mô hình logistic của dòng trên:

| Đặc trưng | Doc F2 |
|---|---|
| p̂ + MaxP Qwen | 0,3818 |
| **+ hạng trong 5 danh sách BGE-M3** (title, title+600, chunk, zh câu vi, zh câu dịch) | **0,4038** |
| + hạng các danh sách khác (BM25, PRF, slug, Qwen3-Emb) thay cho BGE-M3 | 0,3899 |
| mọi hạng + domain + nội dung (đủ 44 đặc trưng, logistic) | 0,4097 |
| cùng 44 đặc trưng, HistGBM | 0,4195 |
| + cos BGE-M3 thô (gbm2) | 0,4243 |
| + cos thô & cos − top-1 của câu, 5 danh sách BGE-M3 (gbm3) | **0,4292** |
| + SapBERT (thực thể ↔ title) thay vì cos BGE | 0,4183 |
| gbm3 + BGE-M3 sparse / ColBERT (380 ứng viên) | 0,4285–0,4302 (không hơn) |
| gbm3 + điểm thô các danh sách không phải BGE (BM25, PRF, slug, Qwen3-Emb) | 0,4289 (không hơn) |
| gbm3 + bge-reranker-v2-m3 (title + 600 ký tự) | 0,4290 (không hơn) |
| **gbm3, k theo từng câu (`--cut-q`) thay ngưỡng chung** | **0,4331** |

- Trên cặp có nhãn ở fold giữ riêng, AUC của mô hình logistic 44 đặc trưng là **0,790**.
  Reranker Qwen3-4B fine-tune bằng LoRA trên nhãn chỉ đạt 0,763; Qwen gốc 0,723.
- Giả thuyết hợp lý nhất: BTC lập danh sách doc để gán nhãn bằng một retriever kiểu BGE-M3.
  Từ 14/10 đã có dấu hiệu: ở tiếng Trung, BGE-M3 hơn Qwen3-Embedding-8B 33% trên leaderboard,
  dù 8B "tốt hơn" trên mọi thước đo nội bộ.

## 3. Luồng xử lý

```
links_corpus + query (ViBioMIR) ── crawl → clean → chunk ──→ data/corpus_new.sqlite      ┐
query ── Qwen3.5-9B + Hy-MT2-7B ──→ queries_enriched.jsonl (thực thể, bản dịch en/zh)    │ dữ liệu trung gian
12 danh sách top-1000 (BM25F, BGE-M3 title/title+600/chunk, BGE-M3 & Qwen3-Emb-8B zh, …)│ (Drive, §4)
Qwen3-Reranker-4B chấm MỌI chunk của 380 ứng viên (GPU) ──→ cc*/ccq*/z80base_scores.jsonl┘
        │
 (1) baseline.cands        RRF 3 nguồn vi → 300 doc vi + RRF 4 nguồn zh → 80 doc zh = 380 ứng viên/câu
 (2) baseline.select_docs  p̂ = sigmoid(logit MaxP, log hạng trong ngôn ngữ, zh); --dump p̂ của mọi ứng viên
 (3) baseline.recal_docs   p̂' của bài D (8 hệ số theo ô) — chỉ dùng làm PHÂN BỐ THAM CHIẾU cho bước 5
 (4) baseline.ltr_feats    đặc trưng / cặp (câu, doc): logit p̂, MaxP, log-hạng 12 danh sách, cos BGE-M3, domain, thực thể…
 (5) baseline.ltr_docs     HistGBM (gbm3: 55 đặc trưng) học trên cặp có nhãn (data/lb/val.jsonl) → điểm → ánh xạ
                           phân vị về p̂' → ngưỡng CHUNG 160 doc/câu → relevant_docs; --cut-q: k theo từng câu
                           = argmax 5·Σp/(4·1,48·Σp_câu + k) trên xác suất gbm (TB 152 doc/câu)
 (6) baseline.value_chunks body[:10000] ghép dòng tới 1.152 token XLM-R; --merge: mỗi doc chọn (quy hoạch động) các
                           khoảng 1 mảnh hoặc 2 mảnh liền kề gộp thành 1 chunk, giữ khi p̂ × π − 0,09 > 0 (π theo
                           vị trí); thêm chunk của ứng viên ngoài tập nếu đạt ngưỡng; nới ranh giới chunk liền kề ≤ 5%
                           → JSON 1,05 GB → ZIP LZMA 92,5 MB → kiểm lại từng câu
```

Bước 1–6 chạy local, không cần GPU, tổng khoảng 30 phút cộng 15 phút nén.

## 4. Dữ liệu (không nằm trong git, lấy từ Drive và đặt vào `data/`)

Drive: <https://drive.google.com/drive/folders/1vPQtULP8A0fKNtGq1VwXvo7hSiCkniR9>. Tải về rồi đặt nguyên cấu trúc thư mục
vào `data/` ở gốc repo (ví dụ `data/corpus_new.sqlite`, `data/val/p_w045.jsonl`, `data/lb/val.jsonl`).

| File | Cỡ | Sinh bằng | Làm lại được? |
|---|---|---|---|
| `queries.jsonl` | | `crawl.profile_dataset` (1.200 câu `{id, query}` từ `query.parquet`) | có |
| `corpus_new.sqlite` | 5,4 GB | `crawl/crawler.py` → `utils/clean.py --apply` → `index/chunk.py` → `scripts/make_store_new.py` (+ `merge_zh_new.py`) | crawl mất nhiều ngày |
| `vibiomir_new/links_corpus_vi_en_zh.parquet` | 35 MB | tải từ HF `AIGuruTinix/ViBioMIR` | có |
| `queries_enriched.jsonl` | 1,4 MB | `query_processing.pipeline` (Qwen3.5-9B + Hy-MT2-7B, GPU; `scripts/remote_run_llm.sh`) | GPU |
| `bm25d3_rank.jsonl`, `bm25ent3_rank.jsonl` | 45 + 47 MB | `index.bm25 --keep-diacritics`, `index.bm25_ent` (`scripts/run_bm25_full.sh`) | có (CPU) |
| `dense_viB3_rank.jsonl`, `dense_vi2_rank.jsonl` | 46 + 46 MB | `index.dense` BGE-M3 (title + 600 ký tự body / title) | GPU |
| `dense_chunk_full_rank.jsonl` | 64 MB | `index.dense_chunks` (`scripts/run_dense_chunks_full.sh`) | GPU |
| `dense_zhC3_{vi,zhq,zhq109}_rank.jsonl` | 47 + 47 + 4 MB | `scripts/run_zh_new.sh` (BGE-M3, doc zh) | GPU |
| `dense_zhQ8_{vi,zhq,zhq109}_rank.jsonl` | 47 + 47 + 4 MB | `scripts/run_zh_q8.sh` (Qwen3-Embedding-8B, doc zh) | GPU |
| `slug_rank1000.jsonl` | 166 MB | `index.slug_bm25 --topk 1000` | có |
| `prf20_rank.jsonl` | 47 MB | `index.prf` (PRF trên vector BGE-M3 `emb_viB2`, hạt giống `blendQB3.jsonl`) | có (CPU, ~1 phút; đã kiểm trùng sha) |
| `dense_q4t_rank.jsonl` | 46 MB | `scripts/run_qemb.sh` (Qwen3-Embedding-4B trên title kho vi) | GPU ~45 phút |
| `bm25zh_new_rank.jsonl` | 46 MB | `index.bm25` với câu vi rỗng + câu dịch zh (lệnh ở §5) | có (CPU) |
| `vi_full.sqlite`, `vi_text.sqlite`, `vi_text_delta.sqlite`, `zh_text_new.sqlite`, `chunk_offsets_s{0,1}.sqlite` | | bản trích từ `corpus_new.sqlite` để chạy trên máy GPU (`scripts/export_vi_full.py` …) | lấy từ Drive |
| `emb_zhC2.npy` + `.ids.json` | | vector BGE-M3 doc zh đời trước; `scripts/run_zh_new.sh` thay các hàng đã mã hoá lại để ra `emb_zhC3` | lấy từ Drive |
| `queries_zhq.jsonl`, `queries_zhq109.jsonl` | | câu dịch zh (Hy-MT2-7B) tách từ `queries_enriched.jsonl`; 109 câu dịch lỗi đã dịch lại | lấy từ Drive |
| `blendQB3.jsonl`, `emb_viB2.npy` + `.ids.json` | 49 MB + 1,4 GB | danh sách đã rerank và vector BGE-M3 (title + 600 ký tự) của phiên bản pipeline trước (07/10); chỉ dùng làm đầu vào cho `index.prf` | lấy từ Drive |
| `cc_scores.jsonl`, `ccq_a_scores.jsonl`, `ccq_b_scores.jsonl`, `z80base_scores.jsonl` | 29 + 12 + 11 + 4 MB | `rerank.chunk_rerank --prep/--score` (Qwen3-Reranker-4B gốc, GPU) | nhiều giờ GPU |
| `val/p_w045.jsonl` | 8 MB | `scripts/val_calib.py` (nhãn mềm suy từ điểm tổng leaderboard) | lấy từ Drive |
| **`lb/val.jsonl`, `lb/folds.json`** | 2 MB | nhãn 593 câu public từ file chấm chi tiết leaderboard (**BTC đã khoá, không tải lại được**) | **KHÔNG** |
| `value_chunks/doc_T.json`, `value_chunks/doc_lines.pkl` (tuỳ chọn) | 4 + 40 MB | cache số token / ranh giới dòng; thiếu thì `value_chunks` tự tính lại | có |

`value_chunks` cần tokenizer `BAAI/bge-m3` có sẵn trong cache HF, vì code đặt `HF_HUB_OFFLINE=1`.
Tải một lần bằng `huggingface-cli download BAAI/bge-m3 config.json tokenizer.json tokenizer_config.json sentencepiece.bpe.model special_tokens_map.json`.

## 5. Chạy

Có hai đường: **5.1** dựng lại đúng bài nộp từ dữ liệu trung gian trên Drive (CPU, ~45 phút), **5.2** chạy toàn bộ từ
dữ liệu BTC (crawl nhiều ngày + vài chục giờ GPU). Mọi lệnh chạy từ gốc repo; `data/` và `runs/` là thư mục tương đối.

**Môi trường.**

| Máy | Cài đặt | Dùng cho |
|---|---|---|
| Local / CPU (Python 3.13) | `pip install -r env/requirements-local.txt` | crawl, BM25, PRF, mọi bước `baseline`, xuất bài |
| GPU (Linux, CUDA, 24 GB/card) | `bash scripts/remote_setup.sh` (tạo `.venv-vllm` cho Qwen3.5/Hy-MT2 và `.venv-train` cho embedding/reranker; gói ở `env/requirements-train.txt`), rồi `bash scripts/download_models.sh` | xử lý câu hỏi, embedding, Qwen chấm chunk |

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1      # Linux: python -m venv .venv && . .venv/bin/activate
pip install -r env\requirements-local.txt
python -m unittest discover tests                        # 22 test offline
```

### 5.1 Dựng bài nộp từ dữ liệu trung gian

Cần các file ở §4 (trừ đầu vào dành riêng cho máy GPU). Một lệnh chạy đủ các bước dưới đây, so sha256 JSON với bài đã nộp
rồi nén và kiểm ZIP (Linux, hoặc Git Bash trên Windows):

```bash
bash scripts/build_submission.sh
```

Từng bước (trên PowerShell, viết mỗi lệnh trên một dòng hoặc thay `\` cuối dòng bằng dấu backtick):

```bash
python -m baseline.cands --n-zh 80 --out data/clean_cands_z80.jsonl
python -m baseline.select_docs --cands data/clean_cands_z80.jsonl \
    --scores data/cc_scores.jsonl data/ccq_a_scores.jsonl data/ccq_b_scores.jsonl data/z80base_scores.jsonl \
    --docs 160 --out data/val/docs_z80base160.json --dump data/val/z80base_scores.json
python -m baseline.recal_docs --mode full --tag dfull
python -m baseline.ltr_feats                                  # → data/val/ltr_feats.pkl
python -m baseline.ltr_docs --mode gbm3 --cut-q               # → data/val/{recal_gbm3q_scores,docs_recal_gbm3q}.json
python -m baseline.value_chunks build    --tau 0.09 --scope all --overlap --recal gbm3q --cut pack --merge
python -m baseline.value_chunks compress --tau 0.09 --scope all --overlap --recal gbm3q --cut pack --merge  # ≥ 4 GiB RAM trống
python -m baseline.value_chunks verify   --tau 0.09 --scope all --overlap --recal gbm3q --cut pack --merge  # đọc lại ZIP, so từng câu
```

- Kết quả nằm ở `runs/z80gbm3q_v09x_ov_p1152_m2.zip`.
- Dựng bài khác: đổi `--mode` thành `gbm2`, `gbm`, `ltr` hoặc `bge1` ở `ltr_docs`, rồi đổi `--recal` theo cho khớp.
  Bỏ `--cut-q` thì ra ngưỡng chung 160 (tag không có hậu tố `q`). Bỏ `--merge` thì ra bài chunk cắt cũ (hậu tố `_m2` biến mất).
- Đo chéo: `python -m baseline.ltr_docs --mode gbm3 --cv` in doc F2 đo chéo 5 fold của p̂ gốc và của mô hình.
- `compress` nén LZMA với từ điển 768 MB, cần khoảng 6–7 GB RAM. Trên máy 12 GB phải tắt trình duyệt trước.
- Nếu lần nén trước bị ngắt, xoá `runs/*.zip.part` rồi chạy lại.

### 5.2 Chạy lại từ đầu

Mỗi bước đọc/ghi file riêng nên chạy lại được từng bước. Thời gian đo trên máy của đội (local 12 GB RAM; GPU 2× RTX 4090).

**A. Dữ liệu BTC và crawl (local, nhiều ngày).** Thứ tự bắt buộc: crawl → clean → chunk → audit, vì `clean` đổi body nên
offset chunk cũ phải tính lại.

```bash
python -m crawl.profile_dataset            # tải ViBioMIR từ HF → data/queries.jsonl, thống kê domain
python -m crawl.crawler --db data/corpus_vifull.sqlite        # crawl 4,39 triệu URL, tự tiếp tục khi bị ngắt
python -m utils.clean --apply --db data/corpus_vifull.sqlite   # bỏ boilerplate theo domain (dòng lặp trên nhiều trang)
python -m index.chunk --db data/corpus_vifull.sqlite           # chunk theo offset (doc_id, start, end)
python scripts/make_store_new.py data/corpus_vifull.sqlite data/corpus_new.sqlite   # chỉ giữ doc thuộc kho BTC (+ vinmec.com)
python -m utils.audit                      # kiểm toàn chuỗi crawl → chunk → submission
python scripts/export_vi_full.py --store data/corpus_new.sqlite --out data/vi_full.sqlite   # bản vi gọn cho máy GPU
```

`vi_text*.sqlite`, `zh_text_new.sqlite` và `chunk_offsets_s{0,1}.sqlite` là các bản trích cột (doc_id, title, body / offset
chunk) của `corpus_new.sqlite` để chép sang máy GPU; bản dùng cho bài nộp có trên Drive.

**B. Xử lý câu hỏi (GPU).** Prompt nằm trong `query_processing/expand.py` (thực thể, Qwen3.5-9B) và
`query_processing/translate.py` (dịch có bảng thuật ngữ, Hy-MT2-7B); prompt reranker trong `rerank/qwen_rerank.py`.

```bash
bash scripts/remote_run_llm.sh data/queries.jsonl runs/public   # Qwen3.5-9B trích thực thể, Hy-MT2-7B dịch vi→zh
cp runs/public/queries_enriched.jsonl data/
```

**C. 12 danh sách truy hồi top-1000.**

```bash
bash scripts/run_bm25_full.sh                                   # bm25d3_rank, bm25ent3_rank (CPU nhiều lõi, ~1 giờ)
python -m index.slug_bm25 --topk 1000 --out data/slug_rank1000.jsonl
# BGE-M3 trên kho vi: title + 600 ký tự (viB3) và chỉ title (vi2)
python -m index.dense --encode --db data/vi_full.sqlite --emb data/emb_viB3 --body-chars 600
python -m index.dense --rank --emb data/emb_viB3 --out data/dense_viB3_rank.jsonl
python -m index.dense --encode --db data/vi_full.sqlite --emb data/emb_vi2
python -m index.dense --rank --emb data/emb_vi2 --out data/dense_vi2_rank.jsonl
bash scripts/run_dense_chunks_full.sh                           # dense_chunk_full_rank (BGE-M3 trên mọi chunk, 2 GPU)
CUDA_VISIBLE_DEVICES=1 bash scripts/run_zh_new.sh               # dense_zhC3_{vi,zhq,zhq109}_rank (BGE-M3, doc zh)
bash scripts/run_zh_q8.sh                                       # dense_zhQ8_*_rank (Qwen3-Embedding-8B, doc zh)
CUDA_VISIBLE_DEVICES=0 bash scripts/run_qemb.sh                 # dense_q4t_rank (Qwen3-Embedding-4B, title vi)
# BM25 tiếng Trung chỉ bằng câu dịch: phía câu vi để rỗng
python -c "import json; open('data/zh_only_q_empty.jsonl','w').writelines(json.dumps({'id':i,'query':''})+'\n' for i in range(1,1201))"
python -m index.bm25 --queries data/zh_only_q_empty.jsonl --queries-zh data/queries_enriched.jsonl --out data/bm25zh_new_rank.jsonl
python -m index.prf --seed data/blendQB3.jsonl --emb data/emb_viB2 --top 20 --out data/prf20_rank.jsonl
```

**D. Qwen3-Reranker-4B chấm mọi chunk của 380 ứng viên (local chuẩn bị, GPU chấm).**

```bash
python -m baseline.cands --n-zh 80 --out data/clean_cands_z80.jsonl
python -m rerank.chunk_rerank --prep --cands data/clean_cands_z80.jsonl --top 380 --min-chunks 1 --cands-out data/z80_chunk_cands.jsonl
python -m rerank.chunk_rerank --score --cands-out data/z80_chunk_cands.jsonl --scores data/z80_chunk_scores.jsonl   # máy GPU
```

Bài nộp dùng 4 file điểm (`cc_scores`, `ccq_a_scores`, `ccq_b_scores`, `z80base_scores`) chấm qua nhiều đợt trên các tập
ứng viên trước đó; một lượt chấm như trên phủ cùng các cặp (doc, chunk) nhưng có thể lệch nhỏ do số học fp16.
Khi đó truyền `--scores data/z80_chunk_scores.jsonl` cho `baseline.select_docs` thay cho 4 file cũ.

**E. Nhãn và dựng bài.** `data/lb/val.jsonl` và `data/lb/folds.json` lấy từ Drive (không sinh lại được, xem §7),
rồi chạy đúng các lệnh ở §5.1.

## 6. Vân tay để đối chiếu

| Bài | Vân tay tập doc | sha256 JSON | sha256 ZIP |
|---|---|---|---|
| gbm3q_m2 | `e748c64a44a3` | `89c7dd84d108daa6b57d52d1baf1ee93c80b9690be726b060c10310c8f3df357` | `0e7b16212842…` (90.456.146 byte) |
| gbm3_m2 | `65a3e79ef452` | `e5cc90429e276348a693cb9a003ec42cf50e8f10ca3551bcc070d6031f37f160` | `742a11f4a96f…` (92.310.181 byte) |
| gbm2_m2 | `5db565f913a2` | `fbdcc3a87eeee036c9f58d93802f1add914c987d868fddd614da69393ba5ec88` | `d77138e8c9ae…` (92.538.060 byte) |
| gbm2 | `5db565f913a2` | `23e5293a6a934f937486e299de2333529ce58b567fd083c8270415668fdb634d` | `dcb6e7bf24b7…` (87.600.182 byte) |
| gbm | `872cbc242d11` | `ff54d83cb220aa20956c8e752c49ea675e7db5b597707367e537d9d79ad8f1dd` | `2ecf0f173f9a…` (87.563.114 byte) |
| ltr | `7127181e3cb0` | `7a5c101a023a…` | `af20ee55f7fc…` (87.930.246 byte) |
| bge1 | `cbb46814f61d` | `d14b39a58700…` | `9ca48fa70a4e…` (92.615.981 byte) |

**Mô hình và revision checkpoint** (tải đúng các bản này bằng `scripts/download_models.sh`):

| Mô hình | Revision (commit HF) | Vai trò |
|---|---|---|
| [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) | `9a0624b896d81da7492a910ffa53731274b6cf3d` | embedding vi/zh (title, title + 600 ký tự, chunk); tokenizer cắt chunk |
| [Qwen/Qwen3-Reranker-4B](https://huggingface.co/Qwen/Qwen3-Reranker-4B) | `22e683669bc0f0bd69640a1354a6d0aebcfeede5` | chấm mọi chunk của 380 ứng viên (MaxP, p̂) |
| [Qwen/Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B) | `1d8ad4ca9b3dd8059ad90a75d4983776a23d44af` | danh sách dense phụ cho doc zh |
| [Qwen/Qwen3-Embedding-4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B) | `5cf2132abc99cad020ac570b19d031efec650f2b` | danh sách dense title vi (đặc trưng hạng) |
| [Qwen/Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | trích thực thể y khoa từ câu hỏi |
| [tencent/Hy-MT2-7B](https://huggingface.co/tencent/Hy-MT2-7B) | `9b0eb4e8f001def3e5ff6469a0ac96fdb39ec223` | dịch câu hỏi vi → zh có bảng thuật ngữ |

Mọi mô hình có trọng số công khai, ≤ 15B tham số, phát hành trước 01/08/2026, dùng checkpoint gốc (không fine-tune).
Không dùng LLM đóng ở bất kỳ bước nào.

- Các bài trên dựng bằng Python 3.13, scikit-learn 1.9.1, numpy 2.4.4 và pandas 3.0.3.
- HistGBM có thể ra cây khác nếu đổi phiên bản scikit-learn, nên `requirements-local.txt` ghim đúng bản này.

## 7. Nhãn dùng để học

`ltr`, `gbm`, `gbm2`, `gbm3`, tham số β của `bge1` và hằng 1,48 của `--cut-q` đều được chọn hoặc học từ **nhãn 593 câu public**
(`--merge` thì không: chỉ dùng p̂ và mô hình vị trí đoạn vàng khớp từ điểm tổng leaderboard). Nhãn này rút từ file chấm
chi tiết (`scoring_result`) mà leaderboard public trả về trong giai đoạn public. Đội đã hỏi và được BTC đồng ý dùng, với
điều kiện không đưa trực tiếp đáp án vào bài nộp: mô hình học trên nhãn rồi dự đoán cho cả 1.200 câu, tập doc nộp do
mô hình chọn. Bài D/F cũng dùng 8 hệ số và con số 160 doc/câu chọn bằng chính nhãn này.

Vì học trên câu public nên điểm public không phải đánh giá độc lập; số đo cho câu private là **đo chéo 5 fold theo câu**
(`ltr_docs --cv`, chia ở `data/lb/folds.json`). Các bài theo mức dùng nhãn:

| Mức | Bài | Dùng nhãn |
|---|---|---|
| gần sạch | `bge1` | 1 số (β = 1) + ngưỡng 160 doc/câu |
| vùng xám | `ltr` | 44 hệ số logistic, giải thích được từng hệ số |
| xám đậm | `gbm`, `gbm2`, `gbm3`, `gbm3q` | mô hình cây 200 vòng, khó giải thích; public bị thổi phồng ~0,013–0,025 |

## 8. Đã thử và không hiệu quả (đừng làm lại)

| Hướng | Kết quả |
|---|---|
| Qwen3-Reranker-8B thay 4B | ngang 4B trên leaderboard, cả ở cấp doc (08/10) lẫn cấp chunk (17/10) |
| Chọn mảnh trong doc bằng điểm Qwen hoặc cos BGE-M3 | xếp đúng mảnh khớp 65%, thua chọn theo vị trí (75%); trộn hai tín hiệu không hơn |
| Cắt chunk kiểu RecursiveCharacterTextSplitter / ghép dòng 1.152 token | recall +0,023 nhưng precision −0,008 → hoà |
| Đổi τ, bỏ quy tắc ép giữ ≥1 mảnh/doc | mọi biến thể trong ±0,004 giả lập; bài no-force τ 0,08 thực tế −0,0022 chunk |
| Lấy chunk sau 10.000 ký tự đầu | 100% đoạn vàng (22.091 doc vàng, file chấm cũ) nằm trong body[:10000] |
| Thêm nguồn truy hồi (HyDE, PRF, BM25 zh, chunk-dense toàn kho, tách ý con) | doc mới chỉ ~1% là vàng, dưới ngưỡng có lãi ~8% |
| Mở rộng pool 380 bằng top-10/30/100 của 12 danh sách | đoạn đậm nhất (BGE title top-10, 90% đã nhãn) chỉ 3,6% vàng |
| `--cut-q` với Ĝ hồi quy theo đặc trưng mức câu thay c·Σp | đo chéo +0,0010 (c·Σp +0,0039) |
| LLM zero-shot (Qwen3-8B) xét doc sát ngưỡng | không phân biệt được doc vàng (7,4% so với nền 7,1%) |
| Doc tiếng Anh (PubMed 240k) | 0 nhãn trên leaderboard |
| Doc vàng "chưa thấy" (~23/câu) | không do thiếu dữ liệu: doc vi/zh thiếu trong kho chỉ chứa ~0,2–0,3 vàng/câu; vàng rải mỏng trong chủ đề đông |

## 9. Cấu trúc repo

```
baseline/         các bước 1–6 ở §3 (cands, select_docs, recal_docs, ltr_feats, ltr_docs, value_chunks)
crawl/ utils/     crawl, làm sạch boilerplate, kiểm toàn chuỗi (utils/audit.py)
index/            chunk theo offset, BM25F, BM25 thực thể, slug, BGE-M3/Qwen3-Emb (dense, dense_chunks), RRF (fuse), PRF (prf)
query_processing/ expand.py (Qwen3.5-9B: thực thể), translate.py (Hy-MT2-7B: dịch vi→zh), llm.py (backend vLLM/HF),
                  pipeline.py (điều phối, ghi queries_enriched.jsonl); không gọi API ngoài
rerank/           Qwen3-Reranker-4B chấm doc / chunk (GPU)
submit/           kiểm định dạng, vân tay, nén ZIP (submission.py), chấm offline (score.py)
scripts/          build_submission.sh (dựng bài một lệnh), lệnh chạy trên máy GPU, tải mô hình, tác vụ dựng kho
env/              requirements-local.txt (CPU), requirements-train.txt (GPU)
tests/            test offline
```

- Mô hình và revision: §6.
- **Repo phải để PRIVATE** suốt thời gian thi.
- **Không đưa lên git:** `data/` (dữ liệu BTC theo giấy phép CC BY-NC 4.0) và `runs/`.
- **`chunk_text` luôn là lát cắt nguyên văn** `body[start:end]` của `corpus_new.sqlite`, không bao giờ lưu text chunk riêng.
