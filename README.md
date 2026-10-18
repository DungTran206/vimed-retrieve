# ViMed Retrieval — cửa vào cho cả nhóm

Truy hồi thông tin y sinh đa ngôn ngữ. Query tiếng Việt → tìm tài liệu + đoạn nội dung liên
quan từ nguồn **vi / zh / en**. Chấm ở hai cấp: **document** và **chunk**.

```
Hạn nộp public  31/10/2026        Private phase  01–04/11/2026 (chỉ 5 lượt nộp TỔNG)
Lượt nộp public 10 bài/ngày        Leaderboard    leaderboard.aiguru.com.vn
```

**Điểm hiện tại: `FINAL_SCORE = 0.2679`** (doc F2 0,2956 · chunk F2 0,2402, k=200; 07/10/2026). Bài tốt nhất: `runs/blendQB3x_t40_70.zip`.

> **Cập nhật 06/10/2026 — ĐỌC TRƯỚC:** tình hình đã đổi nhiều so với các mục bên dưới (viết lúc điểm 0,0457).
> Trạng thái thật, pipeline đang cho điểm tốt nhất, việc đang chạy và việc tiếp theo: **`CLAUDE.md` §6–7**.
> Nhật ký đo và các bài học: **`PROGRESS.md` mục 06/10 và §2b**. Các "Việc #1–#6" ở §4 dưới đây là **lịch sử**:
> crawl vi gần đủ, zh chỉ ~2,6% nhãn (không đáng thêm), corpus PubMed đã tích hợp trong ViBioMIR, `bm25.py` đã có, đã có dense + Qwen3-Reranker.
> Còn thật sự mở: working notes paper (#6), chuẩn bị private phase, các thí nghiệm mở rộng pool (**HyDE đang chạy 07/10**: `hyde.py`, `scripts/run_hyde.sh`; Qwen3-Embedding title).
> Đề xuất nghiên cứu `PROPOSAL_ADAPTIVE_FUSION.md` (gate BM25↔dense) đã thử trên nhãn bạc (07/10): oracle theo từng câu chỉ hơn trọng số chung +1,56% → **bỏ** (xem §6–7 của file đó).

---

## 1. Bắt đầu từ đâu

**Windows / PowerShell 5** (không có `&&`, `source`, `bash`, `rsync` — xem `SETUP.md`):

```powershell
git clone <repo-url> vimed
cd vimed
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r env\requirements-local.txt
```

**Linux / máy GPU:**

```bash
git clone <repo-url> vimed && cd vimed
pip install -r env/requirements-local.txt
```

Rồi kiểm tra — cả hai lệnh phải xanh hết trước khi sửa bất cứ gì:

```
python -m unittest discover tests    # test offline
python utils/audit.py                # 40 mục trên dữ liệu thật (cần có data/corpus.sqlite)
```

**Dữ liệu không nằm trong repo** (`.gitignore` loại `data/`, `runs/`, `*.sqlite`). Sinh lại:

```
python crawl/profile_dataset.py    # tải ViBioMIR → data/queries.jsonl + thống kê domain
python index/slug_bm25.py --topk 200   # → data/slug_rank.jsonl (xếp hạng từ slug, không crawl)
python crawl/crawler.py --prio data/slug_rank.jsonl    # → data/corpus.sqlite
python utils/clean.py --apply                          # lọc boilerplate lặp theo domain
python index/chunk.py                                  # cắt chunk theo offset
python utils/audit.py                                  # phải PASS hết 40 mục
```

**Thứ tự này quan trọng.** `clean.py` đổi `doc.body` nên mọi offset chunk cũ sai → nó tự xoá
chunk của doc bị sửa, và `chunk.py` phải chạy SAU để cắt lại. Chạy sai thứ tự thì `audit.py` báo.

`crawler.py` resume được theo từng URL nên Ctrl+C an toàn, chạy lại là tiếp tục.

## 2. Chuỗi xử lý — ai đụng vào đâu

```
links_corpus.parquet (4,39M URL)   query.parquet (1.200 câu)
         │                                  │
         ├── index/slug_bm25.py ──────────────────┤   xếp hạng từ slug URL, KHÔNG crawl
         │        └→ data/slug_rank.jsonl       (dùng để xếp thứ tự hàng đợi crawl)
         │
         └── crawl/crawler.py ─→ data/corpus.sqlite   ← TẤT CẢ dữ liệu crawl nằm ở đây
                                 │  bảng doc:   body (bất biến) + title/descr/tags
                                 │  bảng queue: trạng thái từng URL, resume được
                                 ↓
                            index/chunk.py ─→ bảng chunk: CHỈ (doc_id, start, end)
                                 ↓
                         index/bm25.py, index/bm25_ent.py, index/dense.py, index/fuse.py, rerank/qwen_rerank.py, rerank/chunk_rerank.py (xem METHODS.md)
                                 ↓
                          submit/submission.py ─→ runs/*.zip ─→ leaderboard
                                 ↑
                          submit/score.py (chấm offline), utils/audit.py (kiểm toàn chuỗi)
```

**Ràng buộc quan trọng nhất của cả đề:** `chunk_text` phải **nguyên văn** từ tài liệu gốc.
Nên `doc.body` là bất biến, và `chunk` chỉ lưu offset — `chunk_text = body[start:end]`.
Không có đường nào để chunk lệch khỏi tài liệu. **Đừng bao giờ lưu text của chunk riêng.**

## 3. Đọc gì ở đâu

| File | Nội dung | Khi nào đọc |
| --- | --- | --- |
| **`README.md`** | file này | đầu tiên |
| **`CLAUDE.md`** | luật cuộc thi, cách chấm, mô hình được dùng, hạ tầng, quy ước làm việc | trước khi viết code |
| **`METHODS.md`** | **từng phương pháp đang dùng/đang thử: làm gì, vì sao, số đo, ✅❌⏳** (đọc cái này để hiểu hướng đi) | sau README |
| **`LITERATURE.md`** | bài báo IR liên quan (đã tra) và hướng nào hợp với bài toán, kèm kỳ vọng | khi chọn hướng mới |
| **`PIPELINE.md`** | thiết kế từng bước xử lý dữ liệu + lý do + thứ tự làm | khi làm một bước cụ thể |
| **`PROGRESS.md`** | **sổ số đo mọi lần chạy**, quyết định đã chốt kèm lý do, bảng điểm leaderboard | khi cần con số, hoặc trước khi định làm lại gì |
| `SETUP.md` | setup 2 máy (local PowerShell + máy GPU) | khi dựng môi trường |

`PROGRESS.md` dài 1.000 dòng. **Không cần đọc hết.** Ba mục đáng đọc trước:
§1 (bảng số đo chính) · §2b (bảng điểm leaderboard) · §3 (quyết định đã chốt kèm lý do).

## 4. Việc cho 3 người — xếp theo giá trị

### Việc #1: crawl `familydoctor.com.cn` — 451k URL, CHỈ máy GPU làm được

`familydoctor.com.cn` + 7 subdomain = **451.351 URL = 10,3% corpus**, trả 403 từ mạng VNPT
ở Hà Nội nhưng **200 từ máy GPU**. Đã xác nhận: Alibaba WAF chặn **theo IP**, và 200/200 URL
thử đều trích được nội dung (body 3.295 ký tự, title 100%, descr 100%, tags 96%).

```bash
tmux new -s fd      # 451k @ 5 req/s ≈ 25 giờ, đừng để đứt khi mất SSH
python crawl/crawler.py --domains "familydoctor.com.cn,baidianfeng.familydoctor.com.cn,familydoctor.cn,qy.familydoctor.com.cn,v.familydoctor.com.cn,ask.familydoctor.com.cn,yanglao.familydoctor.com.cn,ypk.familydoctor.com.cn" --retry-blocked --workers 30
```

Xong thì `scp` file `data/corpus.sqlite` về máy chính rồi `python crawl/crawler.py --merge <file>`.

**`zysjonline.com` (243k, 5,5%) thì KHÔNG phải vấn đề IP** — vẫn 403 từ cả hai máy. Đó là
Cloudflare JS challenge: 10 profile `impersonate` của `curl_cffi` đều thất bại trong khi chứng
dương `nhathuoclongchau` qua được 7/10. Muốn lấy thì cần browser thật (Playwright), ~1,5–3 ngày
cho 243k URL. Chưa đáng.

### Việc #2: crawl song song 3 máy — nút cổ chai hiện tại

Crawl là chặn duy nhất của **cả hai tầng điểm** (xem `PROGRESS.md` §2, mục "quét k").
Một máy mất 73 giờ; ba máy chia theo domain mất ~20 giờ.

Chia theo **domain** chứ không theo id, để mỗi domain do đúng một máy phụ trách — giữ nguyên
rate limit, không đập cùng một server từ 3 hướng.

```powershell
# Máy A                                  # Máy B                 # Máy C
python crawl/crawler.py --shard 0/3            --shard 1/3             --shard 2/3
```

Chia cân: mỗi phần ~1.223.000 URL. Chạy trong `tmux`/`screen` nếu là Linux. Ctrl+C an toàn,
resume từ đúng chỗ dừng.

Xong thì gộp về một máy:

```
python crawl/crawler.py --merge <duong_dan>/corpus_mayB.sqlite
python crawl/crawler.py --merge <duong_dan>/corpus_mayC.sqlite
python index/chunk.py                 # cắt chunk cho doc mới
python utils/audit.py                 # phải PASS hết
```

`--merge` chạy lại nhiều lần an toàn (`INSERT OR IGNORE`), và nó tự tính lại trạng thái
`queue` theo nội dung thật chứ không tin `state` của máy kia.

### Việc #3: parser cho 9,4% crawl được nhưng trích ra 0 ký tự

~380k URL trả HTTP 200 nhưng `trafilatura` không lấy được nội dung.

```powershell
# xem nhóm nào đang lỗi, và nhóm nào còn HTML để sửa offline
python -c "import sqlite3; c=sqlite3.connect('data/corpus.sqlite'); print(c.execute('SELECT domain,count(*) FROM doc WHERE status=200 AND length(body)<200 GROUP BY domain ORDER BY 2 DESC LIMIT 15').fetchall())"
```

| Nhóm | URL | Hiện tượng | Trạng thái |
| --- | --- | --- | --- |
| `laodong.vn` | 31k | thách đố cookie: HTTP 200 với 177 byte JS đặt cookie rồi reload | ✅ **ĐÃ SỬA** — `cookie_challenge()` trong `crawl/crawler.py`. Cần `--retry-failed --domains laodong.vn` |
| 14 subdomain `*.39.net` (`tnb`, `fk`, `gan`, `nk`, `heart`…) | ~66k | markup khác `ask.39.net` (cái này chạy 100%) | ⏳ **chưa crawl tới** — nằm sâu trong hàng đợi. Lấy mẫu trước bằng `--domains "tnb.39.net,fk.39.net" --limit 50` |
| `zhongyibaodian.net`, `baotayninh.vn` | ~148k | `trafilatura` trượt, fallback "khối div dài nhất" chưa bắt được | ⏳ chưa crawl tới |

Cách làm: lấy mẫu ~50 URL của nhóm cần sửa bằng `--domains`, xem `doc.raw_html` (crawler tự
lưu HTML khi trích thất bại), viết selector trong `crawl/crawler.py:extract_fallback()`, rồi
`--domains "..." --retry-failed`. Đáng làm vì `tags` của nhóm `*.39.net` mang sẵn nhãn chuyên khoa.

**Mẫu đã gặp, đáng để ý:** `laodong.vn` không phải lỗi trích mà là chống bot kiểu nhẹ — server
trả JS đặt cookie với **giá trị nằm sẵn trong phản hồi**, nên chỉ cần set lại rồi gọi lần hai,
không cần chạy JS. `cookie_challenge()` xử lý mẫu này một cách tổng quát nên có thể cứu cả
domain khác cùng kiểu.

### Việc #4: BM25 có trọng số trường (`index/bm25.py` — chưa có)

Bước tiếp theo của pipeline, **độc lập với crawl**, viết được ngay.

Mẹo trong `index/slug_bm25.py` tổng quát hoá được: chỉ có 1.200 query nên **không cần inverted
index toàn corpus** — chỉ cần `df` của các term xuất hiện trong query, rồi một lượt
doc-at-a-time. Khỏi Lucene, khỏi Java.

Trọng số đề xuất (lý do ở `PIPELINE.md` §4a):

| Trường | Trọng số | Vì sao |
| --- | --- | --- |
| `title` | **3,0** | Với site Q&A, title **chính là câu hỏi bệnh nhân** → khớp query↔title là khớp câu hỏi với câu hỏi |
| `tags` | 2,0 | 65% doc có, mang nhãn chuyên khoa |
| `descr` | 1,5 | 94% doc có |
| `body` | 1,0 | |

**Hai cái bẫy phải xử lý:**
1. `slug_bm25.rank()` có `docs = list(docs)` → nạp hết vào RAM. Chạy được với slug nhưng
   **sẽ chết** với 6M chunk trên máy 11,7 GB RAM. Phải **streaming hai lượt** từ SQLite.
2. Tách từ: tiếng Việt cần `pyvi`/`underthesea`, tiếng Trung cần `jieba` — **chưa cài**.

### Ghi chú về corpus tiếng Anh

BTC đã tích hợp tài liệu tiếng Anh/PubMed vào dataset ViBioMIR. Không cần gọi NCBI,
Europe PMC hay PubTator để tải corpus riêng; dùng dữ liệu đã có trong dataset.

### Việc #6: working notes paper

> *"Kết quả cuối cùng sẽ không được xem là chính thức cho đến khi một bài báo mô tả phương
> pháp (working notes paper) với mô tả đầy đủ về các phương pháp được nộp."*

**Chưa ai bắt đầu.** `PROGRESS.md` chính là nguyên liệu — mọi số đo, mọi quyết định kèm lý do,
mọi đường cụt đã thử đều ở đó. Đừng để sát hạn.

---

## 5. ĐỪNG làm lại những việc này — đã thử và thất bại

Tiết kiệm cho bạn vài ngày. Chi tiết và số đo ở `PROGRESS.md`.

| Đã thử | Kết quả | Đừng |
| --- | --- | --- |
| `sitemap.xml` của 12 domain lớn nhất | chỉ có `<loc>`, **không có title**. URL thì BTC đã cho sẵn | tìm title qua sitemap |
| Proxy miễn phí (jina, allorigins, codetabs) | cả ba hỏng; **chứng dương `cnkang.com` cũng thất bại** nên kết quả vô giá trị | dùng proxy công cộng |
| `familydoctor.com.cn` từ mạng VNPT | 403 mọi cách. Nhưng **200 từ máy GPU** → đúng là chặn theo IP, đã giải quyết | nghĩ nó không lấy được |
| 10 profile `impersonate` của `curl_cffi` trên `zysjonline` | 0/10 (chứng dương `nhathuoclongchau` 7/10 → phương pháp đúng, đích không vượt được) | thử thêm profile |
| Vòng lấy cookie `acw_tc` + Referer cho `familydoctor` | vẫn 403 | thử header |
| `doc_id` kiểu **chuỗi** trong JSON | **FINAL = 0**. Phải là **số nguyên** (`--int-ids`) | bỏ `--int-ids` |
| `k = 20` doc mỗi câu | G ≈ 50–60 nên quá ngắn. Đỉnh ở **k ≈ 194** | dùng k nhỏ |
| Nâng k để cải thiện điểm chunk | `CHUNKS_F2` **phẳng ở 0,0093** qua k=100/200/500 — bị chặn bởi độ phủ crawl | kỳ vọng k cứu tầng chunk |
| Lưu HTML thô | 4,39M × 53,7 KB = **225 GB**. Text đã trích chỉ ~14 GB | lưu HTML (trừ khi trích lỗi) |
| Trích nội dung trong thread | `trafilatura` tốn 59 ms CPU/trang, **GIL hoá tuần tự** → trần 17 trang/s | bỏ `ProcessPoolExecutor` |
| Ký tự/token **trung bình** để tính budget chunk | vi trung bình 3,75 nhưng **min 1,32** → chunk 2.787 token | dùng trung bình (phải dùng P5 + tokenizer thật) |
| Cắt giảm phạm vi crawl theo domain | 83% URL là ID số thuần, **không một bit thông tin nào** trong URL | cố thu hẹp phía tiếng Trung |

---

## 6. Repo

**Repo này phải để PRIVATE trong suốt thời gian thi** - code truy hồi là phương pháp của nhóm.
Theo luật BTC, checkpoint fine-tune cũng phải giữ private, không công khai lên Hugging Face.

Không đưa lên repo: `data/` (corpus 1,19 GB + dữ liệu BTC giấy phép CC BY-NC), `runs/`
(bài nộp), `*.sqlite`, `.venv*`, `models/`. `.gitignore` đã loại sẵn.

## 7. Quy ước khi làm việc

- **Đổi bất cứ thứ gì trong chuỗi dữ liệu → chạy `python audit.py`.** `--demo` không thay được:
  hai bug về trần token chỉ lộ ra ở `audit.py`.
- Mọi script có `--demo` làm self-check trên dữ liệu giả, chạy trong vài ms.
- **Chạy xong bước nào → thêm một mục vào `PROGRESS.md` §2 kèm SỐ ĐO THẬT**, cập nhật bảng §1.
  Giữ nguyên mục cũ kể cả khi kết quả tệ — cái tệ là mốc để so, và là nguyên liệu viết paper.
- Quyết định đã chốt thì ghi `PROGRESS.md` §3 **kèm lý do**, để sau không bàn lại.
- Giao tiếp và comment code bằng **tiếng Việt**.
- `data/corpus.sqlite` **không có bản thứ hai**. Mất là crawl lại từ đầu. Sao lưu bằng
  `VACUUM INTO` (an toàn khi đang ghi), đừng copy file trực tiếp lúc crawler đang chạy.
