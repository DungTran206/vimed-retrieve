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

- `budget_chars`: khác nhau theo ngôn ngữ (zh ~1,5 ký tự/token, vi ~3,5) → zh ~1.400,
  vi ~3.200 ký tự cho mục tiêu ~900 token. **Là núm xoay, phải hiệu chỉnh trên tập dev.**
- Chồng lấn **1 đoạn** giữa hai chunk liền kề: rẻ (đoạn trung vị 80 ký tự) và tránh cắt
  đứt một "phần thông tin" giữa hai chunk — đúng cái cách chấm cấp chunk đo.
- Đoạn đơn lẻ vượt budget (0,04%): cắt theo câu. Dự phòng hiếm, viết đơn giản.
- 76,3% tài liệu → **1 chunk duy nhất = cả body**. Không làm gì thêm.

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

### 4b. Dense — chạy được trên TOÀN corpus, không chỉ ứng viên

Đây là chỗ kế hoạch cũ sai 3×: 5,17M chunk chứ không phải 13M.

| | Cũ (sai) | Đã đo |
| --- | --- | --- |
| Số chunk | 13M | **5,17M** |
| Vector fp16 | 27 GB | **9,9 GB** |
| Encode BGE-M3 | 18h | **3,6h** |

9,9 GB vừa thoải mái trong 50 GB VRAM → **dense toàn corpus**, không bị BM25 chặn mất doc ở
bước lọc. Đúng cái F2 cần.

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

## 5. Giai đoạn 5 — Truy hồi, gộp, cắt ngưỡng

```
query (vi)
  ├─ Qwen3.5-9B  → thực thể + tách ý con (câu dài: P95 84 từ, max 283 từ)
  ├─ Hy-MT2-7B   → bản dịch zh (và en cho PubMed)
  │
  ├─ BM25 vi  (title 3× / tags 2× / descr 1.5× / body 1×)
  ├─ BM25 zh  (trên bản dịch)
  ├─ dense title-level  (BGE-M3, đa ngôn ngữ — bắc cầu vi↔zh không cần dịch)
  ├─ dense chunk-level
  └─ PubMed  (pubmed_module, đã viết xong)
        ↓  RRF gộp
   bge-reranker-v2-m3 trên top ~300/câu
        ↓
   NGƯỠNG THÍCH ỨNG: p(liên quan) > F*/5     ← chỗ thắng thua thật của F2
```

Câu nhiều ý: tách ý con, truy hồi riêng từng ý, hợp nhất — vì `I` (tập phần thông tin cần
thiết) ở cách chấm cấp chunk được tính theo từng phần, recall đo trên độ phủ các phần.

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
