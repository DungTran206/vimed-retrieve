# PubMed module: hiểu câu hỏi, dịch, và xây kho tiếng Anh

```
câu hỏi tiếng Việt
   │  [1] expand     Qwen3.5-9B  → thực thể y khoa (vi/en/zh) + 3–5 truy vấn PubMed
   │  [2] translate  Hy-MT2-7B   → bản dịch en + zh, dùng thực thể làm bảng thuật ngữ
   │  [3] search     ESearch + Europe PMC → PMID ứng viên (gộp bằng RRF)
   ▼  [4] fetch      PubTator (dự phòng EFetch) → title + abstract
```

Hai mô hình đều thoả thể lệ (≤15B, phát hành trước 1/8/2026):
Qwen3.5-9B (2/3/2026, Apache 2.0) và Hy-MT2-7B (21/5/2026, Apache 2.0).

---

## 1. Chuẩn bị môi trường

**GPU:** khuyến nghị 24 GB (RTX 3090/4090, L4, A10G). Mỗi bước chỉ nạp một mô hình.
GPU 16 GB: xem mục 6. GPU T4 (Kaggle/Colab miễn phí) không hỗ trợ bf16/FP8 và có thể
gặp lỗi với kiến trúc mới của Qwen3.5, nên cần thử trước.

```bash
python -m venv .venv && source .venv/bin/activate      # Python 3.10–3.12
pip install -r requirements.txt
python -m unittest discover tests                       # 12 test offline, phải OK hết
```

**NCBI API key** (miễn phí, tăng giới hạn từ 3 lên 10 request/giây):
đăng nhập https://www.ncbi.nlm.nih.gov/ → Account Settings → API Key Management → Create.

```bash
export NCBI_API_KEY=xxxxxxxx
export NCBI_EMAIL=ban@example.com
```

**Tải trước mô hình** (khoảng 18 GB + 15 GB), để lúc chạy không phải chờ:

```bash
huggingface-cli download Qwen/Qwen3.5-9B
huggingface-cli download tencent/Hy-MT2-7B
```

---

## 2. Bước kiểm tra nhanh: chỉ phần API, không cần GPU

Thư mục `examples/manual_run/` có sẵn `expansions.jsonl` viết tay cho 2 câu mẫu:

```bash
python -m pubmed_module.pipeline --queries examples/sample_queries.jsonl \
    --out examples/manual_run --stages search,fetch
```

Kiểm tra:
- Log cuối phải có dòng `Corpus tiếng Anh: N bài`, với N khoảng vài trăm.
- `candidates.jsonl` → `search_log`: mỗi truy vấn có `count > 0`; trường `translation` cho biết PubMed hiểu truy vấn thế nào.
- `pubmed_corpus.jsonl`: mở vài dòng, `title` và `abstract` phải có chữ, `source` phần lớn là `pubtator`.

Nếu bước này lỗi thì dừng lại sửa trước (thường do mạng hoặc tường lửa chặn `ncbi.nlm.nih.gov` / `ebi.ac.uk`).

---

## 3. Kiểm tra từng mô hình trên câu mẫu

```bash
# Bước 1: Qwen3.5-9B
python -m pubmed_module.pipeline --queries examples/sample_queries.jsonl \
    --out runs/test --stages expand

# Bước 2: Hy-MT2-7B (process mới → VRAM của Qwen đã được giải phóng)
python -m pubmed_module.pipeline --queries examples/sample_queries.jsonl \
    --out runs/test --stages translate
```

Mở và đọc bằng mắt:
- `runs/test/expansions.jsonl`: `parse_ok` phải là `true`; `entities[].vi` phải là cụm có thật trong câu hỏi; `pubmed_queries` gọn, không có từ để hỏi.
- `runs/test/translations.jsonl`: `en`/`zh` là một câu dịch sạch, không kèm giải thích; `glossary_en`/`glossary_zh` là các cặp thuật ngữ đã dùng.
- `runs/test/queries_enriched.jsonl`: `translation_source` = `hy-mt2`.

---

## 4. Chạy thật trên tập câu hỏi của BTC

```bash
bash scripts/run_pubmed_all.sh data/public_test.jsonl runs/public
```

Script chạy lần lượt 3 lệnh (expand → translate → search,fetch), mỗi lệnh một process.
Tham số thêm sau hai tham số đầu được truyền cho mọi bước, ví dụ
`bash scripts/run_pubmed_all.sh data/public_test.jsonl runs/public --retmax 200`.

**Chạy lại an toàn:** `expand`/`translate` thấy file đã có thì dùng lại (thêm `--regen` để làm lại);
mọi request PubMed được cache trong `cache.sqlite`; bài đã tải không tải lại.
Nếu bị ngắt giữa chừng, chỉ cần chạy lại đúng lệnh cũ.

**Private test (1/11–4/11):** dùng một thư mục out MỚI, ví dụ `runs/private`, rồi chạy lại y hệt.

---

## 5. Đầu ra

| File | Nội dung | Dùng cho |
| --- | --- | --- |
| `expansions.jsonl` | thực thể, truy vấn PubMed, bản dịch nháp, `raw` (đầu ra gốc của LLM) | debug bước 1 |
| `translations.jsonl` | bản dịch Hy-MT2 và bảng thuật ngữ đã dùng | debug bước 2 |
| `queries_enriched.jsonl` | **mỗi câu một bản ghi đầy đủ**: `query`, `en`, `zh`, `entities`, `pubmed_queries` | BM25/dense cho cả 3 kho |
| `candidates.jsonl` | PMID ứng viên mỗi câu (điểm RRF, nguồn, thứ hạng) + `search_log` | lọc ứng viên, đo recall |
| `pubmed_corpus.jsonl` | `pmid`, `title`, `abstract`, `source` | chunk + index kho tiếng Anh |

---

## 6. Khi thiếu VRAM hoặc không cài được vLLM

| Tình huống | Cách chạy |
| --- | --- |
| GPU 16 GB, dùng vLLM | Trỏ `--llm-model` tới một bản lượng tử AWQ của Qwen3.5-9B và `--mt-model tencent/Hy-MT2-7B-FP8` (FP8 cần GPU đời Ada/Hopper như L4, 4090, H100) |
| Không cài được vLLM | `bash scripts/run_pubmed_all.sh ... --backend hf --load-in-4bit` (chậm hơn nhiều, nhưng chạy được) |
| vLLM báo lỗi `limit_mm_per_prompt` | Module tự thử lại không có tham số này; nếu vẫn lỗi, cập nhật vLLM |
| vLLM chưa hỗ trợ Hy-MT2 | Chạy riêng bước dịch bằng `--backend hf`, bước expand vẫn dùng vLLM |
| Hết VRAM khi nạp | Giảm `--gpu-mem 0.75` |

---

## 7. Các tham số hay dùng

| Tham số | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `--llm-model` | `Qwen/Qwen3.5-9B` | mô hình cho bước expand |
| `--mt-model` | `tencent/Hy-MT2-7B` | mô hình cho bước translate |
| `--no-glossary` | tắt | dịch không kèm bảng thuật ngữ, để so sánh chất lượng |
| `--mt-greedy` | tắt | dịch bằng greedy thay cho tham số khuyến nghị của Hy-MT2 |
| `--retmax` | 100 | số PMID lấy về cho mỗi truy vấn con |
| `--max-candidates` | 300 | số PMID giữ lại cho mỗi câu hỏi |
| `--no-epmc` | tắt | chỉ tìm qua NCBI, bỏ Europe PMC |

---

## 8. Ghi chú

- Văn bản ưu tiên lấy từ PubTator (nguồn BTC gợi ý); `chunk_text` sau này phải cắt nguyên văn từ `title`/`abstract`.
- Truy vấn có field tag (`[MeSH Terms]`, `[tiab]`) chỉ gửi tới NCBI, vì Europe PMC dùng cú pháp khác.
- Bảng thuật ngữ chỉ gồm thực thể mà phần tiếng Việt xuất hiện nguyên văn trong câu hỏi, để tránh thuật ngữ LLM tự bịa lọt vào bản dịch.
- Ghi lại tên, phiên bản và ngày phát hành của mọi mô hình đã dùng để khai báo với BTC.
