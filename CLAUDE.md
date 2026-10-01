# CLAUDE.md: bối cảnh dự án ViMed Retrieval

File này để Claude Code nắm toàn bộ bối cảnh. Đọc hết trước khi sửa code.
Giao tiếp với người dùng bằng **tiếng Việt**. Comment trong code cũng viết tiếng Việt.

---

## 1. Cuộc thi

**Bài toán:** truy hồi thông tin y sinh đa ngôn ngữ. Với mỗi truy vấn tiếng Việt, tìm và xếp hạng
tài liệu cùng đoạn nội dung liên quan từ các nguồn **tiếng Việt, tiếng Anh, tiếng Trung**.
Chấm ở hai cấp: **document** và **chunk**.

**Mốc thời gian** (hạn chót đều là 23:59 giờ Việt Nam, UTC+7):

| Ngày | Sự kiện |
| --- | --- |
| 01/10/2026 | Phát hành public test |
| 31/10/2026 | Hạn nộp public test |
| 01/11/2026 | Bắt đầu private phase |
| 04/11/2026 | Hạn nộp hệ thống |
| 11/11/2026 | Công bố kết quả |

**Private phase KHÔNG phải câu hỏi mới.** Quy định chính thức: *"Thí sinh nộp kết quả cho toàn bộ 1.200
truy vấn đã phát hành ở cả hai giai đoạn. Hệ thống tự chọn các truy vấn thuộc public hoặc private phase
để chấm; không cần biết trước cách chia phase."* → 1.200 câu hiện có đã chứa cả hai phase.
Nghĩa là **tính trước được toàn bộ**, không có áp lực chạy pipeline tự động trong 3 ngày.

**Giới hạn lượt nộp:** public **10 bài/ngày**; private **5 bài TỔNG CỘNG** → dùng public để chốt cấu hình,
rồi tiêu 5 lượt private rất cẩn thận. Bài nộp thiếu file/thiếu câu thì không được chấm **và không bị tính
vào quota** → thử nghiệm định dạng là miễn phí.

**Kết quả chỉ chính thức khi có working notes paper** mô tả đầy đủ phương pháp. Phải viết, đừng để sát hạn.

### 1.1 Quy định về mô hình (đã xác nhận với BTC)

- Chỉ dùng mô hình **mở** (trọng số công khai, ví dụ trên Hugging Face). **Cấm LLM đóng** (GPT, Gemini...)
  ở MỌI bước, kể cả dịch, sinh dữ liệu giả, chấm nhãn.
- Mỗi mô hình phải **phát hành trước 01/08/2026** và có **≤ 15B tham số**. Giới hạn tính cho **từng mô hình riêng**,
  không cộng dồn, và áp dụng cho **mọi** mô hình kể cả embedding và reranker.
- Fine-tune từ mô hình gốc hợp lệ: **được**, nhưng giữ checkpoint ở chế độ **private**, không công khai.
- Prune mô hình > 15B xuống ≤ 15B: được.
- Dùng mô hình > 15B làm **teacher** để distill: được, miễn teacher chỉ dùng khi huấn luyện, không chạy lúc suy luận.
- **Chưa rõ:** mô hình MoE tính theo tổng tham số hay tham số kích hoạt → coi như tính theo **tổng** cho an toàn.
  Cũng chưa rõ teacher có phải tuân theo mốc ngày không.
- Dữ liệu ngoài: được dùng, nhưng phải trích dẫn nguồn đầy đủ.

### 1.2 Cách chấm

Tính riêng từng truy vấn, rồi lấy **trung bình macro** trên toàn tập.

- **Cấp document:** D là tập tài liệu trả về, G là tập tài liệu đúng.
  Precision = |D∩G| / |D|, Recall = |D∩G| / |G|.
- **Cấp chunk:** I là tập "phần thông tin cần thiết". Một `chunk_text` được tính là relevant nếu chứa hoặc
  **overlap đủ** với ít nhất một phần trong I.
  Precision = số chunk relevant / tổng số chunk trả về; Recall = số phần thông tin được bao phủ / |I|.
  Khuyến nghị mỗi chunk không quá khoảng **1.024 tokens**.
- **F2 = 5·P·R / (4·P + R)**: Recall nặng gấp 4 lần Precision.
- Rút gọn được: với k doc trả về, g doc trúng, G doc vàng → **F2 = 5g / (4G + k)**.
  Thêm một doc có lợi khi xác suất liên quan **p > F2/5**.
- **`FINAL_SCORE` = (F2_document + F2_chunk) / 2** - chia đều, đo được từ leaderboard 01/10.
- **G ≈ 50–60** (suy từ P/R của 4 lượt nộp). Rất lớn → phải nộp danh sách DÀI và nộp HẾT chunk mỗi doc.
- **k = 200**: đã quét k=20/100/200/500 trên leaderboard, đỉnh ở k\* ≈ 194 (DOCS_F2 = 0,0821).
  Phải quét lại khi truy hồi tốt lên - k\* không phải hằng số.

### 1.3 Định dạng nộp bài

File `.json` duy nhất, nén vào ZIP (chỉ chứa đúng một file, không nằm trong thư mục con),
nộp tại mục My Submissions trên http://leaderboard.aiguru.com.vn/ (số lần nộp mỗi ngày có giới hạn).

```json
[
  {
    "id": 1,
    "relevant_docs": ["123", "34567890"],
    "relevant_chunks": [
      {"doc_id": "123", "chunk_text": "đoạn trích NGUYÊN VĂN từ tài liệu 123"}
    ]
  }
]
```

- Phải có **đủ mọi id** câu hỏi; thiếu câu hoặc sai định dạng thì không được chấm.
- Không dự đoán được thì vẫn phải có trường đó với danh sách rỗng `[]`.
- `doc_id`: tài liệu vi/zh dùng trường `id` trong `links_corpus.parquet`; tài liệu tiếng Anh dùng **PMID**
  (PubMed không nằm trong corpus link - BTC đã xác nhận các đội tự tìm). Đo được PMID hiện đại đều > 28M
  còn `links_corpus.id` ≤ 4,39M nên hai dải không chồng nhau trên thực tế.
- ✅ **ĐÃ GIẢI (01/10, thí nghiệm trên leaderboard): `doc_id` PHẢI là SỐ NGUYÊN trong JSON.**
  Cùng nội dung, kiểu chuỗi → FINAL 0; kiểu số nguyên → DOCS_F2 0,0497. Schema và ví dụ trong đặc tả
  BTC gây nhầm, phần chữ mới đúng. **Luôn dùng `submission.py --int-ids`.**
- `chunk_order`: trường **tuỳ chọn**, nếu có phải là số nguyên không âm. Bỏ qua thì hệ thống dùng
  vị trí trong mảng `relevant_chunks`.
- `chunk_text` phải được **trích nguyên văn** từ tài liệu gốc, không được viết lại hay sinh mới.
  → Lưu văn bản gốc sau khi làm sạch, và cắt chunk bằng offset.

### 1.4 Dữ liệu

Dataset: https://huggingface.co/datasets/AIGuruTinix/ViBioMIR (giấy phép CC BY-NC 4.0)

- `query.parquet`: **1.200** câu hỏi `{id, query}`. Độ dài trung vị 18 từ, P95 84 từ, dài nhất 283 từ
  → có nhiều câu dài, nhiều ý, cần tách ý con.
- `links_corpus.parquet`: **4.394.718** URL `{id, url}`, `id` kiểu int64. README của BTC ghi dải
  1–4.420.561; **đã giải (01/10)**: `id` chạy 583→4.420.561 nhưng **khuyết 25.843 id** trong dải,
  không phải thiếu dữ liệu. Gắn nhãn cả ba ngôn ngữ vi/en/zh. Các đội **tự crawl**.
  Phân bố: **tiếng Trung 83,0%** (46 domain) / tiếng Việt 17,0% (51 domain), tổng 97 domain.
- **Tiếng Anh:** chỉ giới hạn trong PubMed. BTC không đưa danh sách; các đội tự tìm. `doc_id` = PMID.
  ⚠️ **NCBI chặn IP máy local** (đo 01/10/2026: ESearch/EFetch/PubTator đều trả HTTP 200 nhưng redirect
  sang `misuse.ncbi.nlm.nih.gov/error/abuse.shtml`, UA browser cũng không thoát) → **Europe PMC
  (`resultType=core`, trả cả title lẫn abstract) là nguồn chính**, NCBI chỉ là dự phòng khi có API key
  hoặc IP khác. Đã test thật: 284/284 bài, abstract trung vị 1.654 ký tự.
- `profile_dataset.py` tải dataset, xuất `data/queries.jsonl` và thống kê domain vào
  `data/domain_stats.csv`, `data/domain_samples.json`.

---

## 2. Chiến lược baseline

**Những điểm rút ra từ cách chấm:**
- F2 ưu tiên Recall → trả danh sách dài hơn trực giác, nhưng không vô hạn.
- Cắt danh sách bằng **ngưỡng thích ứng**, không dùng top-k cố định. Ngưỡng gần tối ưu cho Fβ là xác suất liên quan
  (đã hiệu chỉnh) lớn hơn khoảng **F\*/(1+β²) = F\*/5**, với F\* là điểm F2 đạt được.
- Chunk dài (khoảng 400–800 tokens) dễ "trúng" phần thông tin hơn chunk ngắn, giúp cả P lẫn R.
  **Không cần cửa sổ trượt**: đã đo được đoạn văn trung vị chỉ 80 ký tự và 76,3% tài liệu vừa
  trọn 1 chunk → gộp đoạn liên tiếp (cắt theo `\n`), chồng lấn 1 đoạn. Chunk chỉ lưu
  `(doc_id, start, end)`; `chunk_text = body[start:end]` nên không thể lệch khỏi tài liệu gốc.

**Pipeline dự kiến:**
1. **Hiểu câu hỏi:** Qwen3.5-9B trích thực thể y khoa (vi/en/zh), sinh 3–5 truy vấn PubMed. *(đã làm)*
2. **Dịch câu hỏi** (không dịch corpus): Hy-MT2-7B dịch vi→en và vi→zh, dùng thực thể làm bảng thuật ngữ. *(đã làm)*
3. **Kho tiếng Anh:** gửi truy vấn lên ESearch/Europe PMC → PMID → PubTator (dự phòng EFetch). *(đã làm)*
4. **Kho Việt/Trung:** crawl 4,4 triệu URL, trích nội dung chính, phát hiện ngôn ngữ. *(chưa làm)*
5. **Chunk + index:** BM25 **có trọng số theo trường** (title 3× / tags 2× / descr 1.5× / body 1×),
   theo từng ngôn ngữ (pyvi/underthesea cho vi, jieba cho zh) trên TOÀN BỘ corpus.
   Dense (BGE-M3) **cũng chạy trên toàn corpus** - ngoại suy từ số đo thật: **~6,0M chunk,
   ~11,6 GB fp16**. Hai index: cấp title (~3,37M vector, tín hiệu rất mạnh vì title site Q&A
   chính là câu hỏi bệnh nhân) và cấp chunk (~6,0M). *(chưa làm)*
6. **Gộp điểm** bằng RRF, rồi **rerank** bằng bge-reranker-v2-m3, rồi **cắt ngưỡng**. *(chưa làm)*
7. **Câu nhiều ý:** tách thành ý con, truy hồi riêng từng ý rồi hợp nhất. *(chưa làm)*
8. **Tập dev tự tạo** (đề không cho nhãn): LLM mở sinh câu hỏi từ chunk (nhãn giả) + gán nhãn tay khoảng 30–50 câu public,
   dùng để chỉnh ngưỡng, kích thước chunk, trọng số. *(chưa làm)*
9. **Fine-tune reranker** trên dữ liệu giả (có thể dùng teacher > 15B để sinh và chấm dữ liệu). *(sau cùng)*

**Ý tưởng nghiên cứu riêng của người dùng (làm SAU baseline):** dynamic fusion giữa BM25/SPLADE/dense với gate dựa trên
bằng chứng lexical L(q,d) và độ rõ nghĩa C(q), cùng mở rộng truy vấn bằng từ điển y khoa. Chỉ coi là phần thử nghiệm thêm,
đo xem nó có tăng recall của tập ứng viên trước bước rerank hay không. Lưu ý: SPLADE gần như chỉ dùng được cho tiếng Anh;
nếu cần sparse đa ngôn ngữ thì dùng đầu ra sparse của BGE-M3.

---

## 3. Mô hình đang dùng (đều hợp lệ)

| Mô hình | Phát hành | Kích thước | Giấy phép | Vai trò |
| --- | --- | --- | --- | --- |
| `Qwen/Qwen3.5-9B` | 02/03/2026 | ~9B (dense, đa phương thức) | Apache-2.0 | Expand: thực thể + truy vấn PubMed |
| `tencent/Hy-MT2-7B` | 21/05/2026 | ~7B | Apache-2.0 | Dịch vi→en/zh có bảng thuật ngữ |
| `BAAI/bge-m3` | 01/2024 | 568M | MIT | Embedding đa ngôn ngữ |
| `BAAI/bge-reranker-v2-m3` | 03/2024 | 568M | Apache-2.0 | Reranker |

Dự phòng: Gemma 4 12B (03/06/2026), Qwen3-8B. Không dùng được: Qwen3.6 (27B, 35B-A3B), Gemma 4 26B/31B,
Hy-MT2-30B-A3B (vượt 15B nếu tính tổng tham số).

Ghi chú kỹ thuật:
- Qwen3.5-9B cần vLLM ≥ 0.17.0. Bản Small mặc định tắt thinking; code vẫn truyền `enable_thinking=False`.
- Hy-MT2 cần transformers ≥ 5.6.0, không có system prompt. Prompt bảng thuật ngữ theo đúng model card
  (prompt tiếng Anh cho đích tiếng Anh, prompt tiếng Trung cho đích tiếng Trung).
  Tham số khuyến nghị: temperature 0.7, top_p 0.6, top_k 20, repetition_penalty 1.05.
- vLLM tự ghim phiên bản transformers → máy GPU dùng **hai môi trường**: `.venv-vllm` và `.venv-train`.

---

## 4. Hạ tầng

| Máy | Mô tả | Dùng cho |
| --- | --- | --- |
| **Local** | Windows, **PowerShell 5** (không hỗ trợ `&&`), miniconda, GPU 8 GB. WSL chưa có bản Linux → **không có bash/rsync**. | Điều phối, crawl, gọi PubMed, BM25, xuất bài nộp, suy luận nhẹ (embedding câu hỏi) |
| **Máy GPU** | Linux (`lablee-MS-7E06`), **2× RTX 4090 24 GB** (không phải một card 50 GB), RAM 125 GB, ổ 3,6 TB còn 1,6 TB. Máy của thầy, dùng chung. | **CHỈ** việc local không làm được: Qwen3.5-9B (~19 GB), Hy-MT2-7B (~15 GB), embed ~6M chunk, rerank hàng loạt, fine-tune |

**Chia việc đã chốt:** crawl **giữ ở local** - không cần GPU, mà ngốn mạng liên tục 20–73 giờ nên
không đặt lên máy dùng chung. Lập luận cũ ("Windows ngủ là đứt") đã mất giá trị: resume hoạt động
hoàn hảo, ngắt giữa đường mất nhiều nhất 199 doc (commit mỗi 200).

**Hai card 24 GB RỜI, không liền mạch** → model phải vừa trong 24 GB hoặc chia card.
Qwen3.5-9B ~19 GB vừa một card nhưng chật khi cộng KV cache. Lợi thế: **chạy hai model song song,
mỗi card một cái**.

- Chuyển file: dùng `scp` (có sẵn trên Windows). Đẩy lên: chạy `scp -P <port> -r vimed user@IP:~/` từ thư mục cha
  của `vimed`. Kéo về: `scp -P <port> -r user@IP:~/vimed/runs/<tên> .\vimed\runs\`.
  `scripts/sync.sh` chỉ dùng được nếu có WSL hoặc chạy từ Linux.
- File chuyển từ Windows có thể bị CRLF → trên máy GPU gặp lỗi `$'\r': command not found` thì chạy
  `sed -i 's/\r$//' scripts/*.sh`.
- Trên máy GPU: chạy việc dài trong `tmux`; đặt `HF_HOME=$HOME/hf_cache`.
- Khi viết lệnh cho người dùng chạy trên máy local, **dùng cú pháp PowerShell**.

**Thiết lập máy GPU** (chi tiết trong `SETUP.md`):
```bash
bash scripts/remote_setup.sh      # tạo .venv-vllm và .venv-train
bash scripts/download_models.sh   # ~37 GB
bash scripts/remote_check.sh 2>&1 | tee runs/remote_check.log   # test từng mô hình
bash scripts/remote_run_llm.sh data/queries.jsonl runs/public   # expand + translate (MT_BACKEND=hf nếu cần)
```

---

## 5. Cấu trúc dự án

```
vimed/
├── README.md                 # CỬA VÀO cho cả nhóm: bắt đầu từ đâu, việc cho 3 người, ĐỪNG làm lại gì
├── CLAUDE.md                 # file này
├── SETUP.md                  # hướng dẫn setup hai máy (lệnh local = PowerShell + scp)
├── PROGRESS.md               # SỔ SỐ ĐO từng lần chạy, để đối chiếu. Ghi vào đây sau mỗi lần chạy
├── PIPELINE.md               # PHƯƠNG ÁN xử lý dữ liệu (schema store, chunk, index, thứ tự làm)
├── profile_dataset.py        # tải ViBioMIR, xuất data/queries.jsonl, thống kê URL
├── slug_bm25.py              # BM25 trên slug URL (không crawl) → data/slug_rank.jsonl
├── probe_crawl.py            # crawl thử mẫu phân tầng, đo tỉ lệ/byte/rate limit thật
├── crawler.py                # crawl 4,39M URL → data/corpus.sqlite (resume, rate limit/domain)
├── chunk.py                  # cắt chunk theo OFFSET vào doc.body (không lưu text)
├── submission.py             # xuất JSON+ZIP, kiểm những lỗi làm bài không được chấm
├── score.py                  # P/R/F2 macro hai cấp, --sweep quét topk
├── audit.py                  # KIỂM TOÀN CHUỖI trên dữ liệu thật, PASS/FAIL từng mục
├── pubmed_module/            # hiểu câu hỏi + dịch + xây kho PubMed (README riêng bên trong)
│   ├── http.py               # HttpClient: rate limit theo dịch vụ, retry, cache SQLite (KVStore)
│   ├── search.py             # esearch(), europepmc_search(); truy vấn có [field tag] chỉ gửi NCBI
│   ├── fetch.py              # PubTator (pubtator3 → URL cũ) + EFetch dự phòng; lưu từng bài trong store
│   ├── llm.py                # VLLMChat, HFChat, make_backend()
│   ├── query_gen.py          # prompt Qwen (few-shot), parse JSON chịu lỗi, fallback
│   ├── translate.py          # Hy-MT2: build_glossary, build_prompt, translate_queries, enrich
│   └── pipeline.py           # CLI: --stages expand,translate,search,fetch
├── scripts/                  # remote_setup / download_models / remote_check(.py) / remote_run_llm / sync / run_pubmed_all
├── env/                      # requirements-local.txt, requirements-train.txt, requirements-pubmed.txt
├── tests/test_offline.py     # 16 test offline: python -m unittest discover tests
├── examples/                 # 2 câu mẫu + expansions viết tay (để test PubMed không cần GPU)
├── data/                     # dữ liệu (không đưa vào git)
└── runs/<tên>/               # kết quả mỗi lần chạy
```

**Đầu ra của pubmed_module** (trong `runs/<tên>/`):
`expansions.jsonl` (thực thể, truy vấn PubMed, đầu ra gốc của LLM) → `translations.jsonl` (bản dịch Hy-MT2 + bảng thuật ngữ)
→ `queries_enriched.jsonl` (**bản ghi đầy đủ mỗi câu; các bước sau đọc từ file này**) → `candidates.jsonl`
(PMID xếp theo RRF + `search_log`) → `pubmed_corpus.jsonl` (`pmid`, `title`, `abstract`, `source`) → `cache.sqlite`.

---

## 6. Trạng thái hiện tại

**Điểm leaderboard: `FINAL_SCORE = 0,0457`** (doc F2 0,0821 · chunk F2 0,0093, k=200).
Số đo chi tiết từng lần chạy: `PROGRESS.md`. Cửa vào cho người mới: `README.md`.

### Đã xong và đã chạy được

| Thành phần | Trạng thái |
| --- | --- |
| `profile_dataset.py` | ✅ 4.394.718 URL / 97 domain / 1.200 câu hỏi |
| `slug_bm25.py` | ✅ xếp hạng từ slug URL, không crawl. 1.188.865 URL có slug (27,1%) |
| `probe_crawl.py` | ✅ 2.000 URL phân tầng: dùng được 76,7%, text 975 ký tự/trang |
| `crawler.py` | ✅ chạy được, **16,7 trang/s** (100 thread + 7 process). `--shard I/N`, `--merge`, `--domains`, resume theo từng URL |
| `chunk.py` | ✅ cắt theo offset, 1,79 chunk/doc, bắt buộc trần 1.024 token bằng tokenizer thật |
| `submission.py` | ✅ xuất JSON+ZIP, chặn mọi lỗi làm bài không được chấm |
| `score.py` | ✅ P/R/F2 macro hai cấp, `--sweep` quét topk |
| `audit.py` | ✅ **40 mục PASS** trên dữ liệu thật qua 4 tầng |
| `pubmed_module` | ✅ 16 test, **đã test API thật**: 284/284 bài qua Europe PMC |

### Đang chạy

- **Crawl lô ưu tiên**: ~54k/126k xong. Store `data/corpus.sqlite`.
  Toàn corpus còn 3,6M URL ≈ **73 giờ một máy, ~20 giờ nếu 3 máy chia `--shard`**.

### Chưa có

- `bm25.py` (BM25 có trọng số trường trên store) ← **bước tiếp theo, độc lập với crawl**
- Dense (BGE-M3 trên title + chunk), rerank, cắt ngưỡng thích ứng
- Tập dev gán tay (chỉ cần cho tầng chunk; tầng document đã dò được bằng leaderboard)
- **Working notes paper** - kết quả không chính thức nếu thiếu

### Nợ kỹ thuật đã biết

- `slug_bm25.rank()` có `docs = list(docs)` → nạp hết vào RAM. Chạy được với slug nhưng
  **sẽ chết** với ~6M chunk trên máy 11,7 GB RAM. `bm25.py` phải **streaming hai lượt** từ SQLite.
- Chưa cài `pyvi`/`underthesea` (tách từ vi) và `jieba` (tách từ zh).
- `familydoctor.com.cn` + `zysjonline.com` = **694k URL (15,8%)** chặn 403, không vượt được bằng
  code. Đã đánh dấu `BLOCKED` trong queue; `--retry-blocked` chạy lại khi có IP khác.
- Máy GPU: chưa vào được (`ssh lablee@localhost -p 2223` cần key). `scripts/remote_check.sh`
  **chưa chạy** → Qwen3.5/Hy-MT2/BGE-M3/reranker chưa test trên GPU thật.

## 7. Việc tiếp theo (theo thứ tự ưu tiên)

Phân việc cho 3 người: **`README.md` §4**. Lý do từng bước: `PIPELINE.md` §8.

**Trần hiện tại và nguyên nhân** (đo trên leaderboard, `PROGRESS.md` mục "quét k"):

| Tầng | Trần | Chặn bởi |
| --- | --- | --- |
| document | 0,0821 | **chất lượng truy hồi** - slug chỉ phủ 27% URL, tìm được 8,4/~55 doc vàng |
| chunk | 0,0093 | **độ phủ crawl** - CHUNKS_F2 phẳng qua k=100/200/500 |

→ **Crawl là nút cổ chai duy nhất của cả hai tầng.** Hết đòn miễn phí.

1. **Crawl xong lô ưu tiên** → `chunk.py` → nộp lại `k=200` với chunk phủ đầy.
   Đây là lúc `CHUNKS_F2` phải nhảy khỏi 0,0093.
2. **`bm25.py`**: BM25 có trọng số trường (title 3× / tags 2× / descr 1,5× / body 1×),
   streaming hai lượt từ SQLite. Độc lập với crawl, viết được ngay.
3. **Crawl toàn corpus** - chia `--shard 0/3`, `1/3`, `2/3` cho 3 máy (~20 giờ).
4. **Parser cho ~380k URL trả 200 nhưng trích rỗng** (`README.md` §4 việc #3).
   `laodong.vn` (31k) đã sửa bằng `cookie_challenge()`, cần `--retry-failed`.
5. **Máy GPU**: `remote_check.sh`, rồi embed ~6,0M chunk + ~3,37M title, dense + rerank.
6. **Quét lại k** sau khi truy hồi tốt lên - `k*` phụ thuộc G và độ dốc precision, không phải hằng số.
7. Nhánh PubMed: expand + translate 1.200 câu trên GPU → search + fetch ở local.
8. Tập dev gán tay cho tầng chunk; hiệu chỉnh ngưỡng thích ứng.
9. **Working notes paper** - `PROGRESS.md` là nguyên liệu.
10. Fine-tune reranker; thử dynamic fusion (ý tưởng của người dùng).

## 8. Câu hỏi còn mở cho BTC

| Câu hỏi | Trạng thái |
| --- | --- |
| BTC có cung cấp sẵn nội dung đã crawl không? | ✅ **KHÔNG** - các đội tự crawl cả 4,39M URL. Đã xác nhận. |
| Tài liệu tiếng Anh nằm trong corpus link hay chỉ PubMed? | ✅ **chỉ PubMed**, BTC không đưa danh sách, các đội tự tìm. Gợi ý E-utilities / Europe PMC / PubTator. |
| 25.843 URL chênh giữa README và file thật? | ✅ `id` khuyết trong dải, không thiếu dữ liệu. |
| Kiểu `doc_id` trong JSON? | ✅ **SỐ NGUYÊN** - thí nghiệm trên leaderboard: chuỗi → 0, số nguyên → 0,0497. |
| Nhãn gán theo nội dung trang ở thời điểm nào (trang có thể đã sửa/chết → `chunk_text` không khớp)? | ❓ **chưa hỏi** |
| MoE tính tổng hay tham số kích hoạt? Teacher distill có phải tuân mốc ngày? | ❓ chưa rõ, tạm coi theo tổng |
| `doc_id` của bài PubMed là PMID - hệ thống chấm phân biệt với `links_corpus.id` thế nào? | ❓ nên hỏi; thực tế đo được hai dải không chồng (PMID > 28M, id ≤ 4,39M) |

## 9. Quy ước khi làm việc

- Mỗi bước pipeline đọc/ghi file riêng (JSONL/parquet/npy), chạy lại được từng bước; có cache để không gọi lại API
  hay tải lại dữ liệu.
- Bước nào cần GPU thì chạy theo lô trên máy GPU: nhận file vào, trả file ra. Mỗi mô hình chạy trong một process riêng.
- Không bao giờ để LLM viết lại `chunk_text`; luôn giữ được ánh xạ chunk → (doc_id, offset) về văn bản gốc.
  Chunk lưu `(doc_id, start, end)` chứ không lưu text, nên ràng buộc nguyên văn được bảo đảm bằng
  **cấu trúc dữ liệu**, không bằng kỷ luật. `title`/`description` chỉ dùng để xếp hạng, không bao giờ
  làm `chunk_text` (đo được: title nằm nguyên văn trong body chỉ 43%).
- Thiết kế từng bước xử lý dữ liệu đã chốt ở **`PIPELINE.md`**; đổi thì sửa file đó và ghi lý do vào
  `PROGRESS.md` §3.
- Ghi lại tên, phiên bản, ngày phát hành của mọi mô hình và nguồn dữ liệu ngoài để khai báo với BTC.
- Khi sửa code: thêm hoặc cập nhật test offline, chạy `python -m unittest discover tests` (hiện 16 test).
  Mọi script độc lập có `--demo` làm self-check trên dữ liệu giả: `slug_bm25`, `probe_crawl`,
  `crawler`, `chunk`, `submission`, `score`.
- **Sau khi đổi bất cứ thứ gì trong chuỗi dữ liệu: chạy `python audit.py`** - nó kiểm trên dữ liệu
  THẬT (store + bài nộp sinh ra từ store), 40 mục qua 4 tầng crawl→chunk→submission→score.
  `--demo` không thay được: hai bug về trần token chỉ lộ ra ở `audit.py`.
- Cập nhật mục 6 và 7 của file này khi trạng thái thay đổi. **Người mới vào đọc `README.md` trước.**
- Chạy xong bước nào, hoặc đổi tham số: **thêm một mục vào `PROGRESS.md` §2 kèm số đo thật**, và cập nhật
  bảng §1. Giữ nguyên mục cũ kể cả khi kết quả tệ - cái tệ là mốc để so. Quyết định đã chốt thì ghi vào §3
  kèm lý do, để sau không bàn lại.
