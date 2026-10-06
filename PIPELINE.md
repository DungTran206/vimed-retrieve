# PIPELINE.md: phương án xử lý dữ liệu

Mọi con số trong file này **đã đo**, không ước lượng. Nguồn: `PROGRESS.md` §2.
Thay đổi phương án thì sửa file này và ghi lý do vào `PROGRESS.md` §3.

---

## 0. Bốn ràng buộc bất biến (mọi thiết kế dưới đây bị chúng quyết định)

| # | Ràng buộc | Hệ quả |
| --- | --- | --- |
| 1 | `chunk_text` phải **nguyên văn** từ tài liệu | Giữ một bản text **chính tắc bất biến** cho mỗi doc; chunk chỉ lưu `(doc_id, start, end)`, không lưu text riêng → không thể lệch. |
| 2 | **F2 = 5PR/(4P+R)**, recall nặng 4× | Trả danh sách dài hơn trực giác. Cắt bằng ngưỡng thích ứng, không top-k cố định. Không bao giờ **xoá** doc_id khỏi ứng viên vì lý do trùng lặp. |
| 3 | Local **11,7 GB RAM** (2,9 GB trống), 8 core, 185 GB đĩa. GPU 50 GB VRAM | Mọi bước ở local phải **streaming**, không `list()` cả corpus. Vector và rerank nằm ở máy GPU. |
| 4 | Private phase dùng **chính 1.200 câu đã có** (hệ thống tự chọn subset), không phải câu hỏi mới | **Tính trước được toàn bộ.** Không cần pipeline chạy tự động trong 3 ngày → bước nào chậm/thủ công vẫn chấp nhận được. Đổi lại: private chỉ **5 lượt nộp tổng**, nên cấu hình phải chốt xong ở public. |

### Số đo nền làm cơ sở

```
4.394.718 URL · 97 domain · 83% zh / 17% vi
crawl dùng được 76,7%   ·  text trung vị 975 ký tự  ·  P90 4.886  ·  max 18.255
76,3% tài liệu vừa trọn 1 chunk  →  1,54 chunk/doc  →  5,17M chunk
title 100% · date 82% · description 82% · tags 68%
đoạn văn: phân cách '\n' (KHÔNG có '\n\n'), trung vị 80 ký tự, chỉ 0,04% đoạn vượt 1 chunk
title nằm nguyên văn trong body chỉ 43%  →  title KHÔNG dùng làm chunk_text
```

---

## 1. Giai đoạn 1 — Crawl & store

**Một file SQLite**, không thêm dependency. 3,37M doc × ~2 KB = ~7 GB; SQLite thừa sức,
cho cả ba thứ ta cần: resume theo từng URL, truy cập ngẫu nhiên theo `doc_id`, và quét tuần tự
cho BM25. Ghi bằng **một thread writer** nhận từ queue (WAL mode), ~100 thread fetch.

```sql
CREATE TABLE doc (
  doc_id   TEXT PRIMARY KEY,  -- id trong links_corpus; xuất ra submission dạng CHUỖI
  url      TEXT, domain TEXT,
  lang     TEXT,              -- 'vi'|'zh', suy từ domain, kiểm lại bằng đếm ký tự Hán
  status   INTEGER, err TEXT,
  via      TEXT,              -- 'requests' | 'curl_cffi'
  title    TEXT,              -- 100% có. Trọng số cao khi xếp hạng. KHÔNG làm chunk_text
  descr    TEXT,              -- 82%
  tags     TEXT,              -- 68%, lưu JSON
  pub_date TEXT,              -- 82%
  body     TEXT,              -- *** VĂN BẢN CHÍNH TẮC, BẤT BIẾN ***  chunk cắt từ đây
  simhash  INTEGER,           -- gom gần trùng
  fetched  TEXT
);
CREATE TABLE queue (doc_id TEXT PRIMARY KEY, url TEXT, domain TEXT, prio REAL, state INT);
CREATE INDEX q_state ON queue(state, prio DESC);
```

**Thứ tự hàng đợi:** `prio` lấy từ `data/slug_rank.jsonl` (đã có). 128.118 URL ưu tiên crawl
trước → có submission thử sau vài giờ, không phải vài ngày. Phần còn lại prio = 0, quét nền.

**Rate limit theo từng domain, cấu hình riêng được** — đã đo là một mức chung thì sai:

| Domain | Mức | Căn cứ |
| --- | --- | --- |
| `cnkang.com`, `120ask.com`, `ask.39.net` | 8–10 req/s | 99–100% thành công, chịu tải tốt |
| `a-hospital.com` | 1–2 req/s | 502 ở 28/65 mẫu, server yếu |
| mặc định | 5 req/s | |

**Nút cổ chai là CPU, không phải mạng.** Đo được `trafilatura` tốn 59 ms CPU/trang và bị GIL
→ trần ~17 trang/s dù bao nhiêu thread. Phần trích **phải** chạy ở `ProcessPoolExecutor`
(`--procs`, mặc định số core − 1). Đo thật: 1 process → 7,7 trang/s (156h); 7 process →
**16,7 trang/s (73h)**. Trên máy GPU nhiều core hơn sẽ nhanh hơn.

**403 → tự thử lại bằng `curl_cffi`** (`impersonate="chrome"`). Cứu 100%
`nhathuoclongchau.com.vn` (79.598 URL — domain liên quan nhất theo `slug_bm25`).

**Lưu HTML thô CHỈ khi trích thất bại.** Lưu hết = 225 GB. Lưu riêng phần thất bại
(~240k trang × 53 KB ≈ 12 GB, nén ~2 GB) để viết parser mà **không phải crawl lại 27 giờ**.

**Chạy trên máy GPU** (Linux, tmux; crawl không dùng VRAM nên song song được với embed).
Cần xác nhận ổ còn ≥ 30 GB.

## 1b. Parser riêng cho 9,4% trả 200 nhưng trích rỗng

Ba lớp khác nhau, không phải "trafilatura kém":

| Nhóm | URL | Hiện tượng | Cách xử lý |
| --- | --- | --- | --- |
| 14 subdomain `*.39.net` (`tnb`, `fk`, `gan`, `nk`, `heart`…) | ~66k | 200, markup khác `ask.39.net` | selector riêng bằng lxml (đã có sẵn) |
| `zhongyibaodian.net` | 147k | 88% OK, 12% rỗng | fallback: lấy khối `<div>` dài nhất |
| `laodong.vn` | 31k | 200 nhưng **html_bytes = 0** | không phải lỗi trích; chống bot kiểu khác, cần điều tra riêng |
| `baotayninh.vn` | 1,2k | 200, 156 KB HTML, text = 0 | fallback khối dài nhất |

Fallback chung khi `trafilatura` trả `None`: lấy `<div>`/`<article>` có nhiều text nhất bằng
`lxml`. Rẻ, bắt được phần lớn. Selector riêng chỉ viết cho nhóm `*.39.net` (có lợi vì
`tags` của họ mang sẵn nhãn chuyên khoa).

---

## 2. Giai đoạn 2 — Chuẩn hoá

Chỉ làm những việc **không phá offset**: chuẩn hoá xảy ra **trước khi** `body` được chốt,
sau đó `body` bất biến vĩnh viễn.

1. Giải mã đúng (site Trung Quốc dùng GB2312/GBK — `trafilatura` nhận từ bytes, đã kiểm đúng).
2. NFC Unicode. Thu gọn khoảng trắng ngang, **giữ nguyên `\n`** (là ranh giới đoạn duy nhất).
3. Bỏ dòng boilerplate lặp lại ≥ N lần trong cùng domain (phát hiện tự động, không hardcode).
4. `lang`: suy từ domain (đủ cho 66/69 domain đã kiểm), kiểm lại bằng tỉ lệ ký tự Hán > 15%.

**Không** bỏ dấu, **không** chuyển phồn↔giản, **không** stem trên `body`. Mọi biến đổi đó
chỉ xảy ra ở *tầng index*, trên bản copy — `body` phải khớp nguyên văn với trang gốc.

---

## 3. Giai đoạn 3 — Chunk theo offset

Số đo quyết định thiết kế: đoạn văn trung vị **80 ký tự**, chỉ **0,04%** đoạn tự nó vượt
1 chunk. Nên **không cần sliding window trên text thô** — chỉ cần gộp đoạn liên tiếp:

```python
def chunk_offsets(body, budget_chars, overlap_paras=1):
    """Gộp các đoạn (cắt theo '\n') liên tiếp cho đến hết budget.
    Trả [(start, end)] -> chunk_text = body[start:end], luôn nguyên văn."""
```

- `budget_chars`: `CHARS_PER_TOKEN` đo bằng tokenizer BGE-M3 thật, dùng **phân vị thấp**
  (zh 1,25 · vi 3,40) chứ không phải trung bình - văn bản đậm nhất xuống tới 1,32 ký tự/token
  nên budget theo trung bình cho ra chunk 2.787 token, vượt trần.
- Chồng lấn **1 đoạn** giữa hai chunk liền kề: rẻ (đoạn trung vị 80 ký tự) và tránh cắt
  đứt một "phần thông tin" giữa hai chunk — đúng cái cách chấm cấp chunk đo.
- Đoạn đơn lẻ vượt budget (0,04%): cắt theo câu. Dự phòng hiếm, viết đơn giản.

**`--target-tokens` là núm xoay thật, và nó bị trần ZIP 100 MB quyết định** (cập nhật 04/10):

| target | chunk | chunk/doc | độ dài trung vị | doc 1 chunk | chunk vừa trong 96 MB |
| --- | --- | --- | --- | --- | --- |
| 900 | 1.085.111 | 1,68 | 2.605 ký tự | 41,0% | ~125.000 |
| **400** | **2.366.199** | **3,65** | **1.200 ký tự** | 14,3% | **~270.000** |

Chunk ngắn một nửa thì nhét được gấp đôi vào cùng dung lượng → recall cấp chunk tăng, nhưng
precision có thể giảm vì chunk ngắn dễ CẮT NGANG một phần thông tin mà chunk dài bao trọn.
Bảng `chunk_t900` giữ bản sao của cấu hình 900 để quay lại trong một lệnh.

Lưu `chunk(chunk_id, doc_id, start, end, n_tokens)`. **Không lưu text của chunk** — lấy ra
bằng `body[start:end]`, nên không thể có chuyện chunk_text lệch khỏi tài liệu.

---

## 4. Giai đoạn 4 — Index

### 4a. BM25 có trọng số theo trường — tự viết, không cần Lucene

Mẹo trong `slug_bm25.py` tổng quát hoá được: **chỉ có 1.200 query**, nên không cần inverted
index toàn corpus. Chỉ cần `df` của các term xuất hiện trong query, rồi một lượt doc-at-a-time.
Đã chạy được trên 1,19M doc; 5,17M chunk là ~4×.

**Phải sửa trước:** `slug_bm25.rank()` đang có `docs = list(docs)` → nạp hết vào RAM.
Với 11,7 GB RAM và 5,17M chunk thì chết. Đổi sang **hai lượt streaming từ SQLite**
(lượt 1 tính df + avgdl, lượt 2 cho điểm). Bộ nhớ còn O(query × topk).

Trọng số theo trường (title là tín hiệu mạnh nhất, đo được 100% có):

| Trường | Trọng số đề xuất | Lý do |
| --- | --- | --- |
| `title` | **3,0** | Với site Q&A, title **chính là câu hỏi bệnh nhân** — khớp query↔title là khớp câu hỏi với câu hỏi |
| `tags` | 2,0 | 68% có, mang nhãn chuyên khoa |
| `descr` | 1,5 | 82% có, là tóm tắt sạch |
| `body` | 1,0 | |

Tách từ: `pyvi`/`underthesea` cho vi, `jieba` cho zh. Query tiếng Việt được dịch sang zh
bằng Hy-MT2 (đã có trong `pubmed_module/translate.py`) để khớp vào index zh.

### 4b. Dense — ĐÃ CHẠY ở cấp title, là đòn mạnh nhất của cả giải

**Số thật (04/10), rẻ hơn mọi dự toán trước đó:**

| | Dự toán cũ | **Đo được** |
| --- | --- | --- |
| Cấp | chunk, 13M vector | **title, 643.583 vector** |
| Vector fp16 | 27 GB | **1,32 GB** |
| Thời gian encode | 18 h | **~6 phút** (một card 4090) |
| doc F2 | — | **0,1284 → 0,1705 (+32,8%)** |

Chỉ title mà ăn đậm vì với site Q&A, **title chính là câu hỏi bệnh nhân** - khớp query↔title
là khớp câu hỏi với câu hỏi. Cùng lý do `bm25.py` cho `title` trọng số cao nhất (3,0).

BGE-M3 **đa ngôn ngữ**: query tiếng Việt khớp trực tiếp title tiếng Trung, không cần dịch -
thứ BM25 không làm được. Nhưng trên kho zh (phủ 23%) nó vẫn THUA (0,1217), xem §5.

**Hạ tầng thật khác dự toán:** máy GPU là 2× RTX 4090 **24 GB RỜI**, không phải một card
50 GB. Nên model phải vừa 24 GB hoặc chia card (`device_map="auto"`).

**Dense cấp chunk chưa làm** vì đắt hơn nhiều: 2,37M chunk × 1.200 ký tự so với 643k title
× ~50 ký tự, tức dài gấp ~27 lần. Ước 5-10 giờ, hoặc ~2 giờ nếu cắt `max_seq_length=256`.

Hai index, không phải một:

| Index | Số vector | Dùng cho |
| --- | --- | --- |
| **title-level** | 3,37M (1/doc) | Rẻ, tín hiệu rất mạnh với site Q&A (query↔title = câu hỏi↔câu hỏi) |
| **chunk-level** | 5,17M | Cấp chunk của bài chấm, và tài liệu dài |

Cả hai nằm ở **máy GPU**. Local 11,7 GB RAM không giữ nổi → tra cứu theo lô: đẩy query lên,
nhận file điểm về. Đúng nguyên tắc "máy GPU nhận file vào, trả file ra" đã có.

### 4c. Trùng lặp — gom để tiết kiệm, KHÔNG xoá

Đã đo: 5/685 trùng y hệt, 72 cặp gần trùng (Jaccard > 0,7), 24 cặp **khác domain**.
Có cụm sao chép hệ thống: `a-hospital.com ↔ zhongyibaodian.net` ở 0,82–0,87 (cả hai là
bách khoa Đông y, 316k URL cộng lại).

Cách xử lý, do ràng buộc #2 quyết định:
- Gom theo `simhash` → **embed một đại diện, dùng chung vector** (tiết kiệm chi phí GPU).
- **Không bao giờ xoá doc_id khỏi ứng viên.** Không biết BTC gán nhãn cho bản nào; mà F2
  nặng recall 4× nên trả cả hai bản trùng là lãi, không phải lỗ.

---

## 5. Giai đoạn 5 — Truy hồi, gộp, rerank

**Luồng ĐANG CHẠY THẬT (cập nhật 04/10/2026, FINAL 0,1841).** Mỗi nhánh kèm số đo trên
leaderboard; nhánh đã thử mà thua được ghi rõ để không ai làm lại.

```
query (vi), 1.200 câu
  │
  ├─ slug_bm25.py   BM25 trên SLUG URL          → 1000 ứng viên  w=1,0   (40,5% slot)
  │                 KHÔNG cần crawl; nguồn duy nhất trả về doc chưa crawl
  ├─ bm25.py        BM25F title 3× tags 2×      → 1000 ứng viên  w=1,0   (46,3% slot)
  │                 descr 1,5× body 1×
  ├─ bm25.py --w-body 0   chỉ title/tags/descr  → 1000 ứng viên  w=1,0   (53,7% slot)
  └─ dense.py       BGE-M3 trên 643.583 TITLE   → 1000 ứng viên  w=2,5   (74,9% slot)
                                                                  ↑ đỉnh, đã quét
        ↓  fuse.py — RRF: Σ w/(60 + rank)       → 1000 ứng viên/câu
   rerank.py — bge-reranker-v2-m3 (cross-encoder) trên top-200
        ↓   văn bản chấm = title + 700 ký tự đầu body
   submission.py --topk 200 --chunks-per-doc 2 --chunk-from-top 64 --int-ids
        ↓
   200 doc_id  +  ~125.000 chunk (96 MB, sát trần ZIP 100 MB)
```

### Đóng góp đo được của từng bước

| Bước | doc F2 | Ghi chú |
| --- | --- | --- |
| slug một mình (chưa crawl) | 0,0821 | mốc đầu tiên |
| + BM25F (nguồn thứ 2) | 0,1068 | **+22%** - lợi suất RRF cao nhất ở nguồn thứ 2 |
| + BM25 meta (nguồn thứ 3) | 0,1077 | chỉ +2,6% - cùng họ lexical |
| crawl 127k → 647k doc | 0,1284 | dữ liệu, không đổi thuật toán |
| **+ dense-title (nguồn thứ 4)** | **0,1705** | **+32,8% CẢ HAI TẦNG** - đòn lớn nhất |
| + dense w=1,0 → 2,5 | 0,1845 | quét w: 1,0/1,5/**2,5**/4,0/∞ → đỉnh ở 2,5 |
| **+ rerank top-200** | **0,1948** | +5,6% dù GIỮ ĐÚNG cùng tập 200 doc |

### Đã thử và THUA — đừng làm lại

| Nhánh | Kết quả | Vì sao |
| --- | --- | --- |
| BM25 thêm `bm25_body` (nguồn thứ 4 cùng loại) | 0,1058 < 0,1077 | tương quan 82% với `bm25_rank` |
| dense-title trên kho **zh** | 0,1217 < 0,1284 | kho zh mới phủ 23%; g_zh = 0,54 doc/câu, cần > 1,2 |
| BM25F trên kho **zh** (query đã dịch) | 0,1195 | g_zh = 0,32 - kém cả dense zh, dù dùng 4 trường |
| dense MỘT MÌNH (bỏ 3 nguồn lexical) | 0,1680 < 0,1845 | lexical vẫn mang thông tin dense không có |
| trọng số lệch về slug hoặc meta (×2) | 0,1228 / 0,1214 | khi các nguồn ngang nhau thì để ĐỀU |
| k = 150 hoặc 265 thay vì 200 | 0,1703 / 0,1261 | β = 0,461, k\* = 211 → giữ k=200 |

### Chưa làm

- **Ngưỡng thích ứng** `p(liên quan) > F*/5` thay cho top-k cố định. Vẫn đang dùng k=200.
  Ngưỡng dừng hiện tại: doc 0,039 · chunk 0,035.
- **dense chunk-level** (2,37M chunk sau khi cắt 400 token). Đắt: chunk dài gấp 27 lần title.
- **PubMed** - `pubmed_module` đã chạy xong `expand` cho 1.200 câu, có `pubmed_queries`,
  nhưng chưa `search`/`fetch`. Kho thứ ba, chưa có một doc tiếng Anh nào.
- **Tách ý con** cho câu dài (P95 84 từ, max 283 từ).
- **Hy-MT2-7B**: KHÔNG dùng. Qwen3.5 tự dịch vi→zh ngay trong bước `expand`
  (1.091/1.200 câu có bản dịch), nên không cần mô hình dịch riêng.

### Hai điều về cách chấm, phát hiện bằng thực nghiệm

1. **Cấp document CÓ tính thứ tự**, không chỉ tập hợp. `rr_2x55` giữ đúng cùng tập 200 doc
   với `dvi25_2x55` (kiểm 1200/1200 câu) mà DOCS_F2 vẫn tăng 0,1845 → 0,1948. Trái với công
   thức `P = |D∩G|/|D|` trong đặc tả.
2. **Cải thiện đầu danh sách ăn CẢ HAI tầng.** Chunk chỉ lấy từ `--chunk-from-top` doc đầu,
   nên mọi đòn tăng precision ở đầu được tính đôi: chunk F2 đã đi 0,0898 → 0,1192 → 0,1353
   → 0,1442 → 0,1677 → 0,1733 mà **không đổi một tham số chunk nào**.

---

## 6. Giai đoạn 6 — Xuất bài nộp & tự chấm

Viết **trước** khi có pipeline hoàn chỉnh, để nộp thử sớm lấy mốc leaderboard:

- `submission.py`: đọc ứng viên → JSON đúng định dạng → ZIP (một file, không thư mục con).
  Kiểm bắt buộc: **đủ 1.200 id**, `doc_id` đúng kiểu, thiếu thì `[]` chứ không bỏ trường,
  `chunk_order` (nếu có) là int ≥ 0, và `chunk_text == body[start:end]` (assert, không tin tưởng).
  Cờ `--int-ids` để thử kiểu số nguyên - xem mơ hồ về kiểu `doc_id` ở `CLAUDE.md` §1.3.
- `score.py`: P/R/F2 macro cấp document và cấp chunk (xấp xỉ overlap). Dùng cho tập dev.

Nộp thử lần đầu bằng chính `data/slug_rank.jsonl` — chưa crawl gì đã có một mốc thật.

---

## 7. Chạy ở đâu

| Bước | Máy | Lý do |
| --- | --- | --- |
| Crawl 4,39M + trích + store | **GPU (Linux)** | tmux, không dùng VRAM → song song với embed; Windows ngủ là đứt giữa 27h |
| Chuẩn hoá, chunk theo offset | GPU hoặc local | CPU thuần, streaming |
| BM25 (streaming từ SQLite) | **Local** | 8 core đủ; nhưng **phải streaming**, 11,7 GB RAM |
| Trích nội dung khi crawl | cùng máy với crawler, **ProcessPool** | 59 ms CPU/trang, GIL → đây là nút cổ chai thật, không phải mạng |
| Embed 5,17M chunk + 3,37M title | **GPU** | 3,6h, 9,9 GB VRAM |
| Dense search, rerank | **GPU** | vector 16,8 GB không nằm được ở local |
| Gộp RRF, cắt ngưỡng, xuất ZIP | **Local** | nhẹ |
| PubMed search/fetch | **Local** | nghẽn ở rate limit API |

---

## 8. Thứ tự làm, và cái gì chặn cái gì

| # | Việc | Chặn gì | Ước |
| --- | --- | --- | --- |
| 1 | ~~`submission.py` + `score.py`~~ ✅ **XONG 01/10** | — | xong |
| 2 | Nộp thử - 7 file đã sẵn trong `runs/` | ⏳ **hệ thống chưa mở lượt nộp** | chờ |
| 3 | ~~Kiểm proxy~~ ✅ **XONG 01/10**: không sửa được bằng code → quyết định bỏ qua, để trạng thái `BLOCKED` retry sau | — | xong |
| 4 | ~~Crawler + store (§1)~~ ✅ **XONG 01/10** → `crawler.py`, 16,7 trang/s | — | xong |
| 5 | Crawl 128k ưu tiên → chunk → BM25 → nộp thử lần 2 | vòng lặp đo được đầu tiên | 1 ngày |
| 6 | Parser cho 9,4% (§1b) | +410k URL | 0,5 ngày |
| 7 | Crawl nền toàn corpus | | ~27h chạy nền |
| 8 | Embed + dense + rerank trên máy GPU | | 1 ngày |
| 9 | Hiệu chỉnh `topk`/ngưỡng **bằng leaderboard** (10 lượt/ngày, nhãn thật) | **chỗ thắng thua của F2** | liên tục |
| 10 | **Tập dev** 30–50 câu gán tay - chỉ để kiểm cấp chunk (LB không tách riêng được) | hiệu chỉnh kích thước chunk, overlap | 1 ngày |
| 11 | **Working notes paper** - kết quả không chính thức nếu thiếu | công nhận kết quả | 1–2 ngày |

Việc 1–3 không phụ thuộc crawler → làm ngay được. Việc 7 chạy nền song song với 8–10.

---

## 9. Cố tình bỏ qua (và khi nào thì thêm)

| Bỏ | Lý do | Thêm khi |
| --- | --- | --- |
| Phân loại câu hỏi theo chuyên khoa để ưu tiên crawl phía zh | Là bảo hiểm cho crawl chậm. Crawl 27h, không chậm. Hơn nữa `tags` trên trang đã mang sẵn nhãn chuyên khoa (68%) | không bao giờ |
| Sliding window trên text thô | 76,3% doc là 1 chunk; đoạn trung vị 80 ký tự nên gộp đoạn là đủ | không bao giờ |
| Lucene / pyserini / `bm25s` | Query set cố định 1.200 câu → một lượt streaming là đủ, khỏi Java | nếu cần truy vấn tương tác, không phải batch |
| Xoá bản trùng lặp | F2 nặng recall; không biết BTC gán nhãn bản nào | không bao giờ |
| Dense chỉ trên tập ứng viên | Đã đo: toàn corpus chỉ 9,9 GB / 3,6h | — (đã đảo ngược) |
| SPLADE | Gần như chỉ dùng được cho tiếng Anh. Cần sparse đa ngữ thì dùng đầu ra sparse của BGE-M3 | sau baseline |
| Fine-tune reranker, dynamic fusion | Sau khi có baseline đo được | sau việc #10 |
| Hàng đợi phân tán (Redis…) | SQLite 4,4M dòng thừa sức, 1 máy crawl | không bao giờ |
