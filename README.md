# ViMed Retrieval: quy trình dựng bài nộp

Mỗi câu hỏi tiếng Việt của ViBioMIR, hệ thống trả về `relevant_docs` (doc vi/zh) và `relevant_chunks` (đoạn trích
nguyên văn `body[start:end]` của các doc đó). Mọi lệnh chạy từ gốc repo; `data/` và `runs/` là thư mục tương đối,
không nằm trong git.

## 1. Luồng xử lý

```
links_corpus + query (ViBioMIR) ── crawl → clean → chunk ──→ data/corpus_new.sqlite      ┐
query ── Qwen3.5-9B + Hy-MT2-7B ──→ queries_enriched.jsonl (thực thể, bản dịch zh)       │ dữ liệu trung gian
12 danh sách top-1000 (BM25F, BGE-M3 title/title+600/chunk, BGE-M3 & Qwen3-Emb-8B zh, …)│ (Drive, §3)
Qwen3-Reranker-4B chấm MỌI chunk của 380 ứng viên (GPU) ──→ cc*/ccq*/z80base_scores.jsonl┘
        │
 (1) baseline.cands        RRF 3 nguồn vi → 300 doc vi + RRF 4 nguồn zh → 80 doc zh = 380 ứng viên/câu
 (2) baseline.select_docs  Logistic học nhãn giả Qwen3-32B; p̂ = sigmoid(logit MaxP, log hạng trong ngôn ngữ, zh); ngưỡng chung TB 160 doc/câu
 (3) baseline.recal_docs   hiệu chỉnh p̂ từ cùng nhãn giả, làm phân bố tham chiếu cho bước 5
 (4) baseline.ltr_feats    đặc trưng / cặp (câu, doc): p̂, MaxP, hạng trong 12 danh sách, cos BGE-M3, domain, thực thể…
 (5) baseline.ltr_docs     Logistic / HistGBM học nhãn giả Qwen3-32B, chấm lại 380 ứng viên → chọn tập doc (ngưỡng chung hoặc --cut-q)
 (6) baseline.value_chunks body[:10000] ghép dòng tới 1.152 token XLM-R → giữ mảnh có giá trị kỳ vọng > 0,09
                           (--merge: gộp 2 mảnh liền kề) → nới ranh giới ≤ 5% → JSON → ZIP LZMA → kiểm lại từng câu
```

## 2. Môi trường và mô hình

| Máy | Cài đặt | Dùng cho |
|---|---|---|
| Local / CPU (Python 3.13) | `pip install -r env/requirements-local.txt` | crawl, BM25, PRF, mọi bước `baseline`, xuất bài |
| GPU (Linux, CUDA, 24 GB/card) | `bash scripts/remote_setup.sh` (tạo `.venv-vllm` cho Qwen3.5/Hy-MT2 và `.venv-train` cho embedding/reranker), rồi `bash scripts/download_models.sh` | xử lý câu hỏi, embedding, chấm chunk |

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1      # Linux: python -m venv .venv && . .venv/bin/activate
pip install -r env\requirements-local.txt
python -m unittest discover tests                        # 22 test offline
```

`scikit-learn` được ghim 1.9.1 (cùng numpy 2.4.4, pandas 3.0.3) vì HistGBM có thể ra cây khác ở phiên bản khác.

| Mô hình | Revision (commit HF) | Vai trò |
|---|---|---|
| [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) | `9a0624b896d81da7492a910ffa53731274b6cf3d` | embedding vi/zh (title, title + 600 ký tự, chunk); tokenizer cắt chunk |
| [Qwen/Qwen3-Reranker-4B](https://huggingface.co/Qwen/Qwen3-Reranker-4B) | `22e683669bc0f0bd69640a1354a6d0aebcfeede5` | chấm mọi chunk của 380 ứng viên |
| [Qwen/Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B) | `1d8ad4ca9b3dd8059ad90a75d4983776a23d44af` | danh sách dense cho doc zh |
| [Qwen/Qwen3-Embedding-4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B) | `5cf2132abc99cad020ac570b19d031efec650f2b` | danh sách dense title vi (đặc trưng) |
| [Qwen/Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | trích thực thể y khoa từ câu hỏi |
| [tencent/Hy-MT2-7B](https://huggingface.co/tencent/Hy-MT2-7B) | `9b0eb4e8f001def3e5ff6469a0ac96fdb39ec223` | dịch câu hỏi vi → zh có bảng thuật ngữ |

Mô hình dùng lúc suy luận/nộp bài có trọng số công khai, ≤ 15B tham số, phát hành trước 01/08/2026, dùng checkpoint gốc.
Qwen3-32B chỉ chạy inference để tạo nhãn giả cho Logistic và HistGBM; không được dùng lúc nộp bài. Prompt và tham số: `query_processing/expand.py` (thực thể), `query_processing/translate.py` (dịch),
`rerank/qwen_rerank.py` (reranker, được `rerank/chunk_rerank.py` gọi); chỉ dẫn truy vấn của Qwen3-Embedding nằm trong
`scripts/run_zh_q8.sh` và `scripts/run_qemb.sh`.

`value_chunks` cần tokenizer `BAAI/bge-m3` trong cache HF (code đặt `HF_HUB_OFFLINE=1`). Tải một lần:
`huggingface-cli download BAAI/bge-m3 config.json tokenizer.json tokenizer_config.json sentencepiece.bpe.model special_tokens_map.json`.

## 3. Dữ liệu trung gian

Drive: <https://drive.google.com/drive/folders/1vPQtULP8A0fKNtGq1VwXvo7hSiCkniR9>. Tải về rồi đặt nguyên cấu trúc thư mục
vào `data/` (ví dụ `data/corpus_new.sqlite`). Nhãn học của Logistic, HistGBM và `recal_docs` đặt tại
`C:/Users/DumgTran/Downloads/val_fixed.jsonl`.

| File | Cỡ | Sinh bằng | Làm lại được? |
|---|---|---|---|
| `queries.jsonl` | | `crawl.profile_dataset` (1.200 câu `{id, query}` từ `query.parquet`) | có |
| `vibiomir_new/links_corpus_vi_en_zh.parquet` | 35 MB | HF `AIGuruTinix/ViBioMIR` (revision `71be0e1239a1`), 1.220.598 URL | có |
| `corpus_new.sqlite` | 5,6 GB | `crawl.crawler` → `utils.clean --apply` → `index.chunk` → `scripts/make_store_new.py` (+ `merge_zh_new.py`); 969.899 doc | crawl mất nhiều ngày |
| `queries_enriched.jsonl` | 1,4 MB | `query_processing.pipeline` (Qwen3.5-9B + Hy-MT2-7B; `scripts/remote_run_llm.sh`) | GPU |
| `bm25d3_rank.jsonl`, `bm25ent3_rank.jsonl` | 45 + 47 MB | `index.bm25 --keep-diacritics`, `index.bm25_ent` (`scripts/run_bm25_full.sh`) | có (CPU) |
| `dense_viB3_rank.jsonl`, `dense_vi2_rank.jsonl` | 46 + 46 MB | `index.dense` BGE-M3 (title + 600 ký tự body / title) | GPU |
| `dense_chunk_full_rank.jsonl` | 64 MB | `index.dense_chunks` (`scripts/run_dense_chunks_full.sh`) | GPU |
| `dense_zhC3_{vi,zhq,zhq109}_rank.jsonl` | 47 + 47 + 4 MB | `scripts/run_zh_new.sh` (BGE-M3, doc zh) | GPU |
| `dense_zhQ8_{vi,zhq,zhq109}_rank.jsonl` | 47 + 47 + 4 MB | `scripts/run_zh_q8.sh` (Qwen3-Embedding-8B, doc zh) | GPU |
| `dense_q4t_rank.jsonl` | 46 MB | `scripts/run_qemb.sh` (Qwen3-Embedding-4B, title kho vi) | GPU |
| `slug_rank1000.jsonl` | 166 MB | `index.slug_bm25 --topk 1000` | có |
| `prf20_rank.jsonl` | 47 MB | `index.prf` (hạt giống `blendQB3.jsonl`, vector `emb_viB2`) | có (CPU) |
| `bm25zh_new_rank.jsonl` | 46 MB | `index.bm25` với câu vi rỗng + câu dịch zh (§5.C) | có (CPU) |
| `vi_full.sqlite`, `vi_text.sqlite`, `vi_text_delta.sqlite`, `zh_text_new.sqlite`, `chunk_offsets_s{0,1}.sqlite` | | bản trích cột của `corpus_new.sqlite` cho máy GPU (`scripts/export_vi_full.py` …) | lấy từ Drive |
| `emb_zhC2.npy` + `.ids.json` | | vector BGE-M3 doc zh; `scripts/run_zh_new.sh` thay các hàng mã hoá lại để ra `emb_zhC3` | lấy từ Drive |
| `queries_zhq.jsonl`, `queries_zhq109.jsonl` | | câu dịch zh tách từ `queries_enriched.jsonl`; 109 câu dịch lỗi đã dịch lại | lấy từ Drive |
| `blendQB3.jsonl`, `emb_viB2.npy` + `.ids.json` | 49 MB + 1,4 GB | đầu vào của `index.prf` | lấy từ Drive |
| `cc_scores.jsonl`, `ccq_a_scores.jsonl`, `ccq_b_scores.jsonl`, `z80base_scores.jsonl` | 29 + 12 + 11 + 4 MB | `rerank.chunk_rerank --prep/--score` (Qwen3-Reranker-4B) | GPU, nhiều giờ |
| `C:/Users/DumgTran/Downloads/val_fixed.jsonl` | 699 KB | Qwen3-32B inference đánh nhãn `gold`/`not_gold` cho 200 câu | đầu vào học của `select_docs`, `recal_docs`, `ltr_docs` |
| `val/p_w045.jsonl`, `lb/val.jsonl`, `lb/folds.json` | | dữ liệu leaderboard cũ, chỉ còn phục vụ đối chiếu offline | không |
| `value_chunks/doc_T.json`, `value_chunks/doc_lines.pkl` (tuỳ chọn) | 4 + 40 MB | cache số token / ranh giới dòng; thiếu thì tự tính lại | có |

## 4. Dựng bài từ dữ liệu trung gian (CPU, ~45 phút)

Một lệnh dựng bài `gbm3q` từ nhãn giả Qwen3-32B rồi nén và kiểm ZIP (Linux hoặc Git Bash):

```bash
bash scripts/build_submission.sh
```

Từng bước (PowerShell: viết mỗi lệnh trên một dòng hoặc thay `\` cuối dòng bằng dấu backtick):

```bash
# bước 1–2: chung cho mọi bài
python -m baseline.cands --n-zh 80 --out data/clean_cands_z80.jsonl
python -m baseline.select_docs --cands data/clean_cands_z80.jsonl \
    --scores data/cc_scores.jsonl data/ccq_a_scores.jsonl data/ccq_b_scores.jsonl data/z80base_scores.jsonl \
    --labels C:/Users/DumgTran/Downloads/val_fixed.jsonl --docs 160 --out data/val/docs_z80base160.json --dump data/val/z80base_scores.json
# bước 3–5: các bài bge1 / ltr / gbm3 / gbm3q
python -m baseline.recal_docs --mode full --tag dfull --labels C:/Users/DumgTran/Downloads/val_fixed.jsonl
python -m baseline.ltr_feats                                  # → data/val/ltr_feats.pkl
python -m baseline.ltr_docs --mode gbm3 --cut-q --labels C:/Users/DumgTran/Downloads/val_fixed.jsonl  # → data/val/{recal_gbm3q_scores,docs_recal_gbm3q}.json
# bước 6
python -m baseline.value_chunks build    --tau 0.09 --scope all --overlap --recal gbm3q --cut pack --merge
python -m baseline.value_chunks compress --tau 0.09 --scope all --overlap --recal gbm3q --cut pack --merge
python -m baseline.value_chunks verify   --tau 0.09 --scope all --overlap --recal gbm3q --cut pack --merge
```

Các bài khác chỉ đổi bước 5 và tham số của bước 6 (`build`, `compress`, `verify` dùng cùng tham số):

| Bài (ZIP trong `runs/`) | Bước 5 | Tham số bước 6 |
|---|---|---|
| `z80base160_v09x_ov_p1152` | bỏ bước 3–5 | `--tau 0.09 --scope all --overlap --cut pack` |
| `z80bge1_v09x_ov_p1152` | `ltr_docs --mode bge1` | `--tau 0.09 --scope all --overlap --recal bge1 --cut pack` |
| `z80ltr_v09x_ov_p1152` | `ltr_docs --mode ltr` | `--tau 0.09 --scope all --overlap --recal ltr --cut pack` |
| `z80gbm3_v09x_ov_p1152_m2` | `ltr_docs --mode gbm3` | `--tau 0.09 --scope all --overlap --recal gbm3 --cut pack --merge` |
| `z80gbm3q_v09x_ov_p1152_m2` | `ltr_docs --mode gbm3 --cut-q` | `--tau 0.09 --scope all --overlap --recal gbm3q --cut pack --merge` |

- `compress` nén LZMA từ điển 768 MB, cần khoảng 6–7 GB RAM trống.
- Lần nén trước bị ngắt thì xoá `runs/*.zip.part` rồi chạy lại.

## 5. Chạy lại từ đầu (crawl nhiều ngày + vài chục giờ GPU)

Mỗi bước đọc/ghi file riêng nên chạy lại được từng bước. Mọi bước đọc danh sách URL của BTC
`data/vibiomir_new/links_corpus_vi_en_zh.parquet` (1.220.598 URL). Hệ thống chỉ dùng tài liệu tiếng Việt và tiếng Trung:
240.000 URL tiếng Anh (`pubmed.ncbi.nlm.nih.gov`) bị bỏ ngay khi nạp queue (`SKIP_DOMAINS` trong `crawl/crawler.py`).

**A. Dữ liệu BTC và crawl (local).** Thứ tự bắt buộc: crawl → clean → chunk → audit, vì `clean` đổi body nên offset chunk
phải tính lại.

```bash
huggingface-cli download AIGuruTinix/ViBioMIR --repo-type dataset --revision 71be0e1239a19dfd7a717e2bc13e3bec21bd0334 --local-dir data/vibiomir_new
python -m crawl.profile_dataset            # tải ViBioMIR từ HF → data/queries.jsonl, thống kê domain
python -m crawl.crawler --db data/corpus_vifull.sqlite        # crawl 980.598 URL vi + zh, tự tiếp tục khi bị ngắt
python -m utils.clean --apply --db data/corpus_vifull.sqlite   # bỏ boilerplate theo domain (dòng lặp trên nhiều trang)
python -m index.chunk --db data/corpus_vifull.sqlite           # chunk theo offset (doc_id, start, end)
python scripts/make_store_new.py data/corpus_vifull.sqlite data/corpus_new.sqlite   # chỉ giữ doc thuộc kho BTC (+ vinmec.com)
python -m utils.audit                      # kiểm chuỗi crawl → chunk → submission
python scripts/export_vi_full.py --store data/corpus_new.sqlite --out data/vi_full.sqlite   # bản vi gọn cho máy GPU
```

**B. Xử lý câu hỏi (GPU).**

```bash
bash scripts/remote_run_llm.sh data/queries.jsonl runs/public   # Qwen3.5-9B trích thực thể, Hy-MT2-7B dịch vi→zh
cp runs/public/queries_enriched.jsonl data/
```

**C. 12 danh sách truy hồi top-1000.**

```bash
bash scripts/run_bm25_full.sh                                   # bm25d3_rank, bm25ent3_rank (CPU nhiều lõi, ~1 giờ)
python -m index.slug_bm25 --topk 1000 --out data/slug_rank1000.jsonl
python -m index.dense --encode --db data/vi_full.sqlite --emb data/emb_viB3 --body-chars 600
python -m index.dense --rank --emb data/emb_viB3 --out data/dense_viB3_rank.jsonl
python -m index.dense --encode --db data/vi_full.sqlite --emb data/emb_vi2
python -m index.dense --rank --emb data/emb_vi2 --out data/dense_vi2_rank.jsonl
bash scripts/run_dense_chunks_full.sh                           # dense_chunk_full_rank (BGE-M3 trên mọi chunk, 2 GPU)
CUDA_VISIBLE_DEVICES=1 bash scripts/run_zh_new.sh               # dense_zhC3_{vi,zhq,zhq109}_rank (BGE-M3, doc zh)
bash scripts/run_zh_q8.sh                                       # dense_zhQ8_*_rank (Qwen3-Embedding-8B, doc zh)
CUDA_VISIBLE_DEVICES=0 bash scripts/run_qemb.sh                 # dense_q4t_rank (Qwen3-Embedding-4B, title vi)
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

Bài nộp dùng 4 file điểm (`cc_scores`, `ccq_a_scores`, `ccq_b_scores`, `z80base_scores`) chấm qua nhiều đợt; một lượt chấm
như trên phủ cùng các cặp (doc, chunk) nhưng có thể lệch nhỏ do số học fp16. Khi đó truyền
`--scores data/z80_chunk_scores.jsonl` cho `baseline.select_docs` thay cho 4 file.

**E. Dựng bài.** Giữ `C:/Users/DumgTran/Downloads/val_fixed.jsonl` tại đúng đường dẫn; đây là nhãn giả do Qwen3-32B inference tạo để train/fine-tune Logistic và HistGBM. Sau đó chạy §4.

## 6. Vân tay bài cũ để đối chiếu

Các vân tay dưới đây thuộc bài train bằng dữ liệu cũ; sau khi đổi sang `val_fixed.jsonl`, output phải có SHA-256 khác.

| Bài | Vân tay tập doc | sha256 JSON | sha256 ZIP |
|---|---|---|---|
| gbm3q_m2 | `e748c64a44a3` | `89c7dd84d108daa6b57d52d1baf1ee93c80b9690be726b060c10310c8f3df357` | `0e7b16212842…` (90.456.146 byte) |
| gbm3_m2 | `65a3e79ef452` | `e5cc90429e276348a693cb9a003ec42cf50e8f10ca3551bcc070d6031f37f160` | `742a11f4a96f…` (92.310.181 byte) |
| ltr | `7127181e3cb0` | `7a5c101a023a…` | `af20ee55f7fc…` (87.930.246 byte) |
| bge1 | `cbb46814f61d` | `d14b39a58700…` | `9ca48fa70a4e…` (92.615.981 byte) |
| base160_p1152 | `9acf4a3bb1be` | `afad6e410d1f…` | `18409042e71c…` (94.746.989 byte) |

## 7. Cấu trúc repo

```
baseline/         các bước 1–6 ở §1
crawl/ utils/     crawl, làm sạch boilerplate, kiểm toàn chuỗi (utils/audit.py)
index/            chunk theo offset, BM25F, BM25 thực thể, slug, BGE-M3/Qwen3-Emb (dense, dense_chunks), RRF (fuse), PRF
query_processing/ expand.py (thực thể), translate.py (dịch vi→zh), llm.py (backend vLLM/HF), pipeline.py (điều phối)
rerank/           Qwen3-Reranker-4B chấm chunk
submit/           kiểm định dạng, vân tay, nén ZIP (submission.py), chấm offline (score.py)
scripts/          build_submission.sh, lệnh chạy trên máy GPU, tải mô hình, tác vụ dựng kho
env/              requirements-local.txt (CPU), requirements-train.txt (GPU)
tests/            test offline
```

`chunk_text` luôn là lát cắt nguyên văn `body[start:end]` của `corpus_new.sqlite`; không lưu text chunk riêng.
