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
- Dùng mô hình > 15B làm **teacher** để distill: **ĐƯỢC PHÉP** (miễn student nộp bài $\le 15$B lúc suy luận).
- Mô hình kiến trúc **MoE** (Mixture-of-Experts): **HỢP LỆ** khi tham số kích hoạt (active parameters) $\le 15$B theo thông lệ.
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
đo xem nó có tăng recall của tập ứng viên trước bước rerank hay không.
**Kết quả 07/10 (nhãn bạc, `PROPOSAL_ADAPTIVE_FUSION.md` §7): trọng số dense chung tối ưu w=2,5; oracle theo từng câu chỉ hơn +1,56% (+2,49 doc/câu) → bỏ phần gate, giữ như phân tích âm tính cho paper.** Mở rộng truy vấn bằng từ điển y khoa chưa thử. Lưu ý: SPLADE gần như chỉ dùng được cho tiếng Anh;
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
| `Qwen/Qwen3-Embedding-8B` | 06/2025 | 8B | Apache-2.0 | Thử cho zh (15/10, Colab A100): P@50 zh **0,083 < BGE-M3 0,110** → không dùng (nghi nhãn BTC thiên về BGE) |

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
├── build_best.sh                 # dựng lại bài tốt nhất từ file trung gian (~35 phút, không GPU; dựng w045_TF 0,3442: tập doc w045 + cấp chunk theo p(gold) của val_calib.py)
├── BTC_QUESTIONS.md / PAPER_DRAFT.md / LITERATURE.md  # câu hỏi gửi BTC (đơn giản, song ngữ) / bản nháp working notes / bài báo đã tra
├── CLEANUP_PLAN.md           # dọn dự án 08/10: cái gì đã xoá/giữ và vì sao; STORE SỐNG = data/corpus_vifull.sqlite
├── METHODS.md                # ĐỌC ĐỂ HIỂU TỪNG PHƯƠNG PHÁP: làm gì, vì sao, số đo, trạng thái ✅❌⏳
├── PROPOSAL_ADAPTIVE_FUSION.md  # đề xuất gate BM25↔dense + đánh giá + kết quả nhãn bạc (đã bỏ)
├── bm25.py / bm25_ent.py     # BM25F có trọng số trường (có dấu) / BM25 entity+bigram đa tiến trình
├── dense.py                  # BGE-M3: --encode doc, --rank câu hỏi (cũng chạy Qwen3-Embedding)
├── fuse.py                   # RRF nhiều nguồn xếp hạng
├── qwen_rerank.py            # Qwen3-Reranker-4B (P(yes)); rerank.py = bge-reranker vòng cũ
├── chunk_rerank.py           # chấm chunk bằng Qwen, chọn chunk cho submission.py --chunk-scores
├── hyde.py / decompose.py / prf.py   # HyDE (đã đo: yếu) / tách ý con (đang chạy) / PRF dense (chờ điểm)
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
├── scripts/                  # remote_setup / download_models / remote_check(.py) / remote_run_llm / sync / run_pubmed_all / run_hyde / run_qemb / run_subq
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

**Điểm leaderboard: `FINAL_SCORE = 0,3442`** (doc F2 0,3605 · chunk F2 0,3279; cập nhật 15/10/2026). Bài tốt nhất: `runs/w045_TF.zip` (LZMA; bỏ chunk p<0,04, đuôi p≥0,05; T6 0,3436, T4 0,3429, T2 0,3420) = w045 + cấp chunk theo p(gold) của `val_calib.py` (`--chunk-plan data/val/plan_TF.json`, đã có trong build_best.sh). Trước đó `runs/w045_zh38w_e120.zip` 0,3272 (zh W0,45 ~39 zh/câu; w05 hoà 0,3272, w04 0,3262; zh list `rp/zh38w_in` = RRF BGE-M3 1 : Qwen3-Emb-8B 0,3; 8B một mình THUA BGE). Trước đó `runs/blendQB14_w04_e120.zip` 0,3253 (= QB14 nhưng zh w0,4 → 31 zh/câu; w035 0,3244). `runs/blendQB14_e120.zip` (0,3222) = công thức 13af (0,3182) nhưng danh sách zh mới (zh kho mới phủ 95%, đã clean, mã hoá lại; chi tiết PROGRESS 14/10). Trước đó `runs/blendQB11_e120.zip` (0,3158) (= blendQB10 [tập doc của blendQB9a + thứ tự đầu của blendQB8w05] + vá 109 câu parse lỗi; QB10 chưa nộp). Trước đó `runs/blendQB9a_e120.zip` (0,3139) = `blendQB8b` + 14 doc zh/câu (dense zh BGE-M3, RRF w0,3) chen ở hạng 121–200 (zh nhiều hơn ~16 doc/câu thì tụt). Trước đó `runs/blendQB8b_e120.zip` (0,3126) = RRF(`blendQB7`, chunk-dense TOÀN KHO vi) + chunk chọn theo chunk khớp nhất. **Đo zh lại (10/10): 150 doc zh/câu cho DOCS_R 0,0559, P 0,0266 → zh có nhãn đáng kể, đừng bỏ.** Trước đó `runs/blendQB7b_e120.zip` (0,3072) = `blendQB7_e120` + chunk chọn theo chunk khớp nhất (`chunk_scores_mix.jsonl`). Trước đó `runs/blendQB7_e120.zip` (0,3068) = `blendQB6_h05` RRF với **chunk-dense** (BGE-M3 trên chunk, `dense_chunks.py`, điểm doc = chunk khớp nhất; pilot trên 400 ứng viên pool H) → top-200 → chunk e120 bzip2. Đang mở rộng chunk-dense ra TOÀN kho vi (`scripts/run_dense_chunks_full.sh`). Trước đó `blendQB6_h05_e120.zip` (0,2931) = như `blendQB5_h05_e120` nhưng pool H (BM25F, BM25F meta và BM25 entity chạy lại trên kho vi đầy đủ 741.586 doc, `vi_full.sqlite`) + Qwen chấm bù 6.246 cặp. Trước đó `blendQB5_h05_e120.zip` (0,2920) = bản lai (tập doc: RRF Qwen w2 / pool G w1; thứ tự 120 doc đầu: Qwen w0,5 / pool G w1; Qwen chấm cả đợt 2) dựng bằng `hybrid_cands.py`. Trước đó `blendQB4_e120.zip` (0,2895) = chuỗi Long Châu (crawl nốt 78.555 doc, embed 55k doc mới, pool G = f_F với vector mới, Qwen chấm 26.811 cặp doc mới, RRF Qwen w2 / f_G w1, chunk e120 bzip2). Trước đó `runs/blendQB3x_cr_e120.zip` (0,2770) = `blendQB3x_cr` + nén **bzip2** (`--zip-method bzip2`, server chấp nhận) + 1 chunk cho doc hạng 41–120 (174.760 chunk, 93,6 MB). Trước đó `runs/blendQB3x_cr.zip` (0,2682) = `blendQB3x_t40_70` + chọn chunk bằng điểm Qwen (`chunk_rerank.py`, chỉ +0,0003). `blendQB3x_t40_70.zip` (0,2679) = bản lai (tập doc của `blendQB3` với Qwen chấm top-400, chunk của `blendQB2`; QB3 một mình 0,2669, QB2 0,2658). Mô tả dưới đây là QB2; khác biệt chỉ là Qwen chấm top-400 thay vì top-250 ở phần tập doc. Còn lại = pool F (slug + BM25 có dấu + dense title/nội dung vi + BM25 entity) → Qwen3-Reranker-4B chấm top-250 → RRF(Qwen w2, vòng 1 w1) → chunk 900 token, 2 chunk × 40 doc + 1 chunk × doc 41–70. Trước đó (04/10) là 0,0457 với slug thuần. **Chi tiết đã đo: `PROGRESS.md` §2b.**
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
Store: **`data/corpus_new.sqlite`** (từ 14/10, mặc định của mọi script; `make_store_new.py`): CHỈ doc thuộc kho mới của BTC (`data/vibiomir_new/links_corpus_vi_en_zh.parquet`) + vinmec.com, 966.845 doc, 5,3 GB; zh kho mới phủ 95% (228k/240k), đã clean + chunk. Dựng lại blendQB14 từ store này cho vân tay y hệt. Store cũ `corpus_vifull.sqlite` (2,78M doc, gồm zh/vi ngoài kho mới) không còn dùng. `data/vi_slim.sqlite` (vi-only, `bm25_ent.py`) và `vi_full.sqlite` (nguồn cho script GPU) vẫn dùng.
Crawl: vi **gần đủ** (Long Châu 40.735 doc có nội dung; còn ~51k URL `prio=0` chưa cào (**07/10: ĐO ĐƯỢC CÓ NHÃN, P 0,0174 → đang crawl nốt, xem PROGRESS §2b**)). zh: shard 0/5 trên máy GPU **đã chạy xong**
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

### Đã xong (07/10)
- Qwen hạng 251–400 xong, đã gộp (`data/qwen_all.jsonl`, bản cũ `qwen_all_250.jsonl`) và nộp: FINAL 0,2669 (+0,4%). Doc +1,4%, chunk −0,8%. **Lợi suất giảm rõ: chấm sâu thêm không còn đáng GPU** (xem `PROGRESS.md` §2b 07/10).

### Ý tưởng chưa làm (xếp theo kỳ vọng)
1. ~~**HyDE**~~ — **đã đo 07/10: yếu.** 150 doc HyDE ngoài pool F chỉ cho DOCS_R 0,0084 (`qhyde`) / 0,0068 (`hyde`), precision biên ~0,5%. Cùng cỡ nguồn entity; không đáng rerank trước. `hyde.py`, `scripts/run_hyde.sh` giữ để tái lập. Pool recall 0,61 hầu như đã bão hoà với nguồn rẻ. **Qwen3-Embedding-4B title cũng yếu (DOCS_R 0,0080, 07/10).** Ba nguồn embedding/entity đều cho ~0,008 → nhãn bị mất khác loại với thứ embedding bắt được.
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

**Quota 07/10 đã hết (10/10). Hàng đợi nộp 08/10 và tổng kết 10 bài hôm nay: `PROGRESS.md`, mục "TỔNG KẾT 10 LƯỢT NỘP" (trước §2b).**

1. ~~Gộp Qwen 251–400~~ và ~~bản lai doc-QB3 + chunk-QB2~~ (xong 07/10, **0,2679** đúng dự đoán). **HyDE đang chạy** trên GPU 0 (`scripts/run_hyde.sh`, log `data/hyde_run.log` trên máy GPU, đầu ra `dense_hyde_viB2_rank.jsonl`, `dense_qhyde_viB2_rank.jsonl`).
2. ~~HyDE~~ (yếu, xem trên). Còn thử **Qwen3-Embedding title** hoặc tách ý con cho câu dài để nới pool; đo bằng bài chỉ-doc-mới (như `diag_novel_*`), nhìn DOCS_RECALL.
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
| Nhãn gán theo nội dung trang ở thời điểm nào (trang có thể đã sửa/chết → `chunk_text` không khớp)? | ✅ **Đã chốt (đội, xem `BTC_QUESTIONS.md`): coi như bản mới nhất, không hỏi BTC** |
| PubMed/tiếng Anh còn trong đề không? | ✅ **Đã bị bỏ khỏi trang chính thức** (người dùng xác nhận 06/10); nhánh PubMed dừng. |
| MoE tính tổng hay tham số kích hoạt? Teacher distill có phải tuân mốc ngày? | ✅ **Đã chốt (quyết định của đội, CHƯA có xác nhận chính thức của BTC):** MoE tính theo tham số KÍCH HOẠT ≤ 15B là hợp lệ; teacher distill được phép khi huấn luyện. Rủi ro tuân thủ: nên ghi rõ trong paper; hiện bài tốt nhất không dùng mô hình MoE nào |
| `doc_id` của bài PubMed là PMID - hệ thống chấm phân biệt với `links_corpus.id` thế nào? | ✅ **Hết hiệu lực:** PubMed/tiếng Anh đã bị BTC bỏ khỏi đề |

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
