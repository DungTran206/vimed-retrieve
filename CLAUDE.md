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
| `BAAI/bge-reranker-v2-m3` | 03/2024 | 568M | Apache-2.0 | Reranker vòng cũ (top-1000); nay chỉ còn làm tín hiệu phụ |
| `Qwen/Qwen3-Reranker-4B` | 06/2025 | 4B | Apache-2.0 | **Reranker chính** (P(yes) của "yes"/"no"), chấm top-250 trở đi |
| `Qwen/Qwen3-Embedding-4B` | 06/2025 | 4B | Apache-2.0 | Đã tải, đo 74 doc/s (2,4 giờ cho 646k doc), **chưa dùng** |

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

- **Đăng nhập máy GPU (06/10): server đòi CẢ key LẪN mật khẩu** (`publickey` rồi `password`, thấy qua `ssh -vv`:
  `partial success`). Hôm 05/10 chỉ cần key; có người đổi cấu hình `sshd`. Key `~/.ssh/id_ed25519` (`vimed-crawler`)
  đã được server chấp nhận. **Mật khẩu do người dùng giữ, KHÔNG ghi vào file nào**; mỗi phiên hỏi lại. Cách chạy lệnh
  không tương tác: `SSH_ASKPASS` trỏ vào script `printf '%s\n' "$VIMED_PW"` + `SSH_ASKPASS_REQUIRE=force`, truyền mật khẩu
  qua biến môi trường của từng lệnh. Tunnel `localhost:2223` mở ở máy Windows.
- Máy GPU: 24 core CPU (BM25 chạy được ở đó), GPU 0 hay bị người khác dùng (đo 4–65% tải, có lúc 17 GB), GPU 1 thường trống.
  Chỉ chạy việc của mình, đặt `CUDA_VISIBLE_DEVICES`, không dừng tiến trình của người khác (xem ghi nhớ trong memory).
  Cẩn thận `pkill -f <mẫu>` qua ssh: mẫu khớp cả chính lệnh ssh và tự cắt phiên.
- GPU local thực tế là **RTX 4050 6 GB** (không phải 8 GB), torch 2.6 chạy được nhưng chậm (~220 doc/s so với ~2.000 trên 4090).
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
├── clean.py                  # lọc dòng boilerplate lặp theo domain (document frequency)
├── chunk.py                  # cắt chunk theo OFFSET vào doc.body (không lưu text)
├── predict.py                # áng điểm trước khi nộp, lọc lượt nộp vô ích
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

**Điểm leaderboard: `FINAL_SCORE = 0,2658`** (doc F2 0,2914 · chunk F2 0,2402, k=200; cập nhật 06/10/2026). Bài tốt nhất: `runs/blendQB2_t40_70.zip` = pool F (slug + BM25 có dấu + dense title/nội dung vi + BM25 entity) → Qwen3-Reranker-4B chấm top-250 → RRF(Qwen w2, vòng 1 w1) → chunk 900 token, 2 chunk × 40 doc + 1 chunk × doc 41–70. Trước đó (04/10) là 0,0457 với slug thuần. **Chi tiết đã đo: `PROGRESS.md` §2b.**
Số đo chi tiết từng lần chạy: `PROGRESS.md`. Cửa vào cho người mới: `README.md`.

### Pipeline đang cho điểm tốt nhất (06/10/2026, FINAL 0,2658)
```
queries_enriched.jsonl (Qwen3.5: entity, bản dịch en/zh)
  ├─ slug_bm25                      → data/slug_rank1000.jsonl
  ├─ bm25.py --keep-diacritics      → bm25d2_rank / bm25d2_meta.jsonl   (store vi_slim.sqlite, 689.740 doc vi)
  ├─ dense.py (BGE-M3) title        → dense_vi2_rank.jsonl              (w=2,5)
  ├─ dense.py --body-chars 600      → dense_viB2_rank.jsonl             (title + 600 ký tự đầu body, w=2,5)
  └─ bm25_ent.py (entity + bigram)  → bm25ent_rank.jsonl                (đa tiến trình)
        |  fuse.py (RRF)  ->  data/f_F.jsonl  (pool F, top-1000, recall 0,6108 ở k=1000)
        v
qwen_rerank.py (Qwen3-Reranker-4B, máy GPU) chấm blendF hạng 1-250 -> qwen_all.jsonl
        |  fuse.py  qwen_all:2  f_F:1   -> blendQB2.jsonl
        v
submission.py --topk 200 --store data/corpus_vifull.sqlite --chunks-per-doc 2 --chunk-from-top 40 --extra-one 70 --int-ids
        -> runs/blendQB2_t40_70.zip (94,0 MB, 114.760 chunk)
```
Store: **`data/corpus_vifull.sqlite`** (vi 689k doc đã `clean.py` + `chunk.py`; cả 1,05M zh từ GPU) và `data/vi_slim.sqlite` (vi-only, có index `doc_id`).
Crawl: vi **gần đủ** (Long Châu 40.735 doc có nội dung; còn ~51k URL `prio=0` chưa cào, không quan trọng). zh: shard 0/5 trên máy GPU **đã chạy xong**
(273.511 URL, 9,8 giờ, 85,8% dùng được); shard 1/5–4/5 (~1,68M URL) chưa chạy và **chưa đáng chạy** (xem dưới).

### Số đo quan trọng đã chốt (chi tiết: `PROGRESS.md` §2 mục 06/10 và §2b)
- **Nhãn vàng ≈ 70/câu (G≈70).** Pool F ở k=1000 chứa 61% nhãn; top-200 sau rerank chứa 47,8%.
- **zh chỉ ~2,6% nhãn** ở độ phủ ~35% (bài zh-only: P 0,0089, g_zh 1,78/200 doc). Ngoại suy phủ 100% cũng chỉ +~7% recall → **đừng đầu tư thêm cho zh**.
- **Điểm doc chỉ phụ thuộc TẬP doc nộp, không phụ thuộc thứ tự** (06/10: cùng tập → P/R y hệt; tập khác → khác). Ghi chú 04/10 "doc có tính thứ tự" là sai.
- **Điểm chunk phụ thuộc thứ tự đầu danh sách** (chunk lấy từ top-40/70): Qwen xếp đầu tốt hơn bge, chunk +10,5%.
- **PubMed/tiếng Anh: BTC đã bỏ khỏi trang chính thức** (người dùng xác nhận 06/10) → dừng nhánh `pubmed_module`.
- **Chunk:** 2 chunk × 40 doc đầu + 1 chunk × doc 41–70 hơn 2×64 (chunk thứ hai của doc hạng 41–64 đóng góp ~0 recall). Chọn chunk theo trùng từ khoá câu hỏi **không hơn** lấy chunk đầu (−0,3%).
- **k=200 vẫn ở vùng phẳng** (tính từ β≈0,46: k=290 ngang k=200). Không đáng quét lại.
- Trần ZIP **100 MB**; bài tốt nhất 94 MB. Bản `submission.py` hiện tại cho ZIP lớn hơn ~1,2% so với trước 06/10 (xem "Nợ kỹ thuật").

### Việc đang chạy lúc viết (06/10 ~20:00 giờ máy GPU)
- Qwen3-Reranker chấm **hạng 251–400** của blendF trên GPU 1 (`data/chain3.sh`, log `data/qwen_chain3.log`, đầu ra `data/qwen_rr3_h1.jsonl`, `qwen_rr3_h2.jsonl`, trên máy GPU).
  Ước ~1,8 giờ (150 doc/câu ≈ 5,5 giây/câu × 1.200). Tự chạy lại tối đa 6 lần nếu chết; dòng cuối log là `CHAIN_DONE`.
  **Ước tính "100 phút cho hạng 251–500" đưa ra trước đó là SAI** (250 doc/câu ≈ 3,1 giờ).
- Khi xong: kéo về, gộp `qwen_rr.jsonl` + `qwen_rr2.jsonl` + `qwen_rr2_h2.jsonl` + `qwen_rr3_*` thành `qwen_all.jsonl` (sắp theo điểm giảm dần),
  `fuse.py qwen_all:2 f_F:1`, dựng bài `t40_70`, nộp. Kỳ vọng thêm vài % điểm doc (lợi suất giảm dần: điểm Qwen TB 0,564 ở hạng 1–100, 0,327 ở hạng 101–250).

### Ý tưởng chưa làm (xếp theo kỳ vọng)
1. **HyDE** (LLM mở viết câu trả lời giả định 2 câu → dense BGE-M3): nhắm đúng nút cổ chai pool (recall 0,61), chưa có số đo.
2. **Cấp số chunk theo ngân sách MB** (đặt chunk ở nơi precision biên cao nhất) thay vì quy tắc hạng cố định; ngưỡng theo MB, không theo P(yes) cố định (điểm Qwen bão hoà).
3. Qwen3-Embedding-4B (bản title ~45 phút) làm nguồn dense thứ ba cho pool; thử bằng bài k=1000.
4. Trộn Qwen với bge (bài A) kém bài chỉ Qwen (B): giữ Qwen một mình.
5. **Working notes paper** — `PROGRESS.md` là nguyên liệu. **Chưa viết.**
6. Cập nhật `run_pipeline.py` (đang chạy chuỗi cũ 03/10) để tái lập được bài tốt nhất.

### Nợ kỹ thuật đã biết
- `bm25.py` tokenize mọi trường **hai lần** (2 lượt) và chạy một luồng (58 phút cho 647k doc vi). `bm25_ent.py` là bản đa tiến trình, dùng làm mẫu nếu phải chạy lại.
- `crawler.py --merge` dùng `INSERT OR IGNORE`: dòng 403/429 cũ **chặn mất** bản crawl thành công ở store khác (đã làm mất 17k doc Long Châu). Sau merge phải thay các dòng không có `body`
  bằng bản có `body` từ store nguồn, đặt lại `queue.state` (DONE ⇔ body ≥ 200 ký tự, `audit.py` kiểm), và gán `lang` cho doc thiếu (đừng chạy truy vấn quét cả bảng 9 GB; update theo khoá chính).
- `load_candidates()` của `submission.py` **sắp lại ứng viên theo điểm giảm dần**: file ứng viên trộn hai thang điểm sẽ nộp sai tập doc (đã mất 1 lượt nộp: FINAL 0,2459 thay vì ~0,2589).
  File tự ghép phải có điểm giảm đều theo vị trí.
- `submission.py`: lỡ xoá rồi khôi phục `validate`/`write_zip` từ git HEAD; bản gốc (chưa commit) nén chặt hơn ~1,2%. Các ZIP đã dựng trước đó vẫn hợp lệ. `--extra-one`, `--chunk-query` là tuỳ chọn mới.
- `audit.py` còn **1 FAIL vô hại**: "không gọi request tới domain đã biết bị chặn" — danh sách `BLOCKED` viết cho IP local, máy GPU crawl được familydoctor (447k doc).
- `qwen_rerank.py`: bản đầu tính logits mọi vị trí (hết VRAM) và xử lý OOM sai chỗ (trong khối `except`); đã sửa. Vẫn nên đặt `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, batch 32.
- Store local lớn (`corpus_vifull.sqlite` ~9,4 GB, `vi_slim.sqlite` ~4 GB, `corpus_merged.sqlite` 9,4 GB): có thể xoá `corpus_merged`, `corpus_gpu`, `corpus.sqlite` cũ khi chắc chắn không cần.
- Chưa cài `pyvi`/`underthesea`; vi chỉ tách từ đơn + bigram từ (trong `bm25_ent.py`). zh dùng bigram ký tự, không cần jieba.

## 7. Việc tiếp theo (theo thứ tự ưu tiên)

1. **Gộp Qwen hạng 251–400 và nộp** (xem "Việc đang chạy"). Quota public 10 lượt/ngày; đã dùng đủ ngày 06/10.
2. Thử **HyDE** hoặc **Qwen3-Embedding title** để nới pool; đo bằng bài k=1000 (chỉ nhìn DOCS_RECALL, mốc hiện 0,6108).
3. Thử cấp chunk theo ngân sách MB.
4. **Chuẩn bị private phase** (01–04/11, 5 lượt tổng cộng): chốt cấu hình ổn nhất, có sẵn 2–3 bài đã dựng, ZIP < 100 MB, vân tay ghi sổ. 1.200 câu đã chứa cả hai phase nên tính trước được hết.
5. **Viết working notes paper**.
6. Cập nhật `run_pipeline.py` và `audit.py` theo cấu hình mới.

## 8. Câu hỏi còn mở cho BTC

| Câu hỏi | Trạng thái |
| --- | --- |
| BTC có cung cấp sẵn nội dung đã crawl không? | ✅ **KHÔNG** - các đội tự crawl cả 4,39M URL. Đã xác nhận. |
| Tài liệu tiếng Anh nằm trong corpus link hay chỉ PubMed? | ✅ **chỉ PubMed**, BTC không đưa danh sách, các đội tự tìm. Gợi ý E-utilities / Europe PMC / PubTator. |
| 25.843 URL chênh giữa README và file thật? | ✅ `id` khuyết trong dải, không thiếu dữ liệu. |
| Kiểu `doc_id` trong JSON? | ✅ **SỐ NGUYÊN** - thí nghiệm trên leaderboard: chuỗi → 0, số nguyên → 0,0497. |
| Nhãn gán theo nội dung trang ở thời điểm nào (trang có thể đã sửa/chết → `chunk_text` không khớp)? | ❓ **chưa hỏi** |
| PubMed/tiếng Anh còn trong đề không? | ✅ **Đã bị bỏ khỏi trang chính thức** (người dùng xác nhận 06/10); nhánh PubMed dừng. |
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
- **Thứ tự chuỗi dữ liệu BẮT BUỘC:** `crawler.py` → `clean.py --apply` → `chunk.py` → `audit.py`.
  `clean.py` đổi `doc.body` nên offset chunk cũ sai; nó tự xoá chunk của doc bị sửa và `chunk.py`
  phải chạy SAU. Doc mới crawl lại mang boilerplate nên **`clean.py` phải chạy lại sau mỗi đợt crawl**.
- **Sau khi đổi bất cứ thứ gì trong chuỗi dữ liệu: chạy `python audit.py`** - nó kiểm trên dữ liệu
  THẬT (store + bài nộp sinh ra từ store), 40 mục qua 4 tầng crawl→chunk→submission→score.
  `--demo` không thay được: hai bug về trần token chỉ lộ ra ở `audit.py`.
- Cập nhật mục 6 và 7 của file này khi trạng thái thay đổi. **Người mới vào đọc `README.md` trước.**
- Chạy xong bước nào, hoặc đổi tham số: **thêm một mục vào `PROGRESS.md` §2 kèm số đo thật**, và cập nhật
  bảng §1. Giữ nguyên mục cũ kể cả khi kết quả tệ - cái tệ là mốc để so. Quyết định đã chốt thì ghi vào §3
  kèm lý do, để sau không bàn lại.
