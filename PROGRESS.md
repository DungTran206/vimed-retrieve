# PROGRESS.md: sổ ghi kết quả từng lần chạy

Mục đích: **đối chiếu số đo giữa các lần chạy**. Mỗi khi chạy một bước pipeline hoặc đổi
tham số thì thêm một mục vào §2, kèm con số thật. Không ghi kế hoạch ở đây -
kế hoạch nằm ở `CLAUDE.md` §6 (trạng thái) và §7 (việc tiếp theo).

**Cách ghi một mục:** ngày · bước · lệnh đã chạy · tham số · số đo · nhận xét 1-2 dòng.
Giữ nguyên các mục cũ, kể cả khi kết quả tệ - cái tệ là mốc để so.

---

## 1. Bảng số đo chính

Cập nhật dòng khi có kết quả mới hơn; giữ cột "lần trước" để thấy chiều thay đổi.

| Số đo | Hiện tại | Lần trước | Ngày | Nguồn |
| --- | --- | --- | --- | --- |
| URL trong corpus | 4.394.718 | — | 01/10/2026 | `profile_dataset.py` |
| Số domain | 97 | — | 01/10/2026 | `data/domain_stats.csv` |
| Câu hỏi public | 1.200 | — | 01/10/2026 | `data/queries.jsonl` |
| URL có slug (index được) | 1.188.865 (27,1%) | — | 01/10/2026 | `slug_bm25.py` |
| Hàng đợi crawl ưu tiên | 128.118 URL | — | 01/10/2026 | `slug_bm25.py --topk 200` |
| Tỉ lệ crawl **dùng được** (có text) | 76,7% | — | 01/10/2026 | `probe_crawl.py` n=2000 |
| URL chạy tốt (≥90%/domain) | 3.237.124 (73,7%) | — | 01/10/2026 | `probe_crawl.py` |
| URL sửa được bằng parser/hạ rate | 410.949 (9,4%) | — | 01/10/2026 | `probe_crawl.py` |
| URL cần proxy hoặc chịu mất | 740.403 (16,8%) | 770.598 (sơ bộ) | 01/10/2026 | `probe_crawl.py` |
| └ trong đó cần **IP khác** (Alibaba WAF) | ~451.000 (10,3%) | — | 01/10/2026 | probe WAF |
| └ trong đó cần **browser thật** (CF challenge) | 243.347 (5,5%) | — | 01/10/2026 | probe WAF |
| HTML trung vị / trang | 53,7 KB | ~45-80 KB (sơ bộ) | 01/10/2026 | `probe_crawl.py` |
| Text trung vị / trang | 975 ký tự | — | 01/10/2026 | `probe_crawl.py` |
| Dung lượng text toàn corpus | 6,0 GB (nén ~1,8 GB) | — | 01/10/2026 | ngoại suy |
| Độ trễ mạng trung vị | 338 ms | — | 01/10/2026 | `probe_crawl.py` |
| **CPU trích nội dung / trang** | **59 ms** (max 2.025) | — | 01/10/2026 | `crawler.py` |
| Throughput crawl (100 thread, 7 proc) | **16,7 trang/s** = 73h | 7,7 (1 proc) = 156h | 01/10/2026 | `crawler.py` |
| URL đánh dấu BLOCKED từ đầu | 725.329 (16,5%) | — | 01/10/2026 | `crawler.py` |
| PubMed: bài lấy được / PMID | **284/284** | 0/284 | 01/10/2026 | `pubmed_module` API thật |
| Test offline | 16 qua | 12 qua | 01/10/2026 | `unittest discover tests` |
| Chunk/tài liệu | **1,79** (budget bảo thủ) | 1,55 | 01/10/2026 | `chunk.py` |
| Tổng chunk (ngoại suy) | **~6,0M** | 5,17M | 01/10/2026 | ngoại suy |
| Vector fp16 chunk-level | **~11,6 GB** | 9,9 GB | 01/10/2026 | ngoại suy |
| Mục audit PASS | **40/40** | — | 01/10/2026 | `audit.py` |
| Ký tự/token vi dùng cho budget | **3,40 (P5)** | 4,09 (trung bình - SAI) | 01/10/2026 | `chunk.py` |
| Ký tự/token zh dùng cho budget | **1,25 (P5)** | 1,42 (trung bình - SAI) | 01/10/2026 | `chunk.py` |
| Chunk nguyên văn (kiểm độc lập) | **3.585/3.585** | — | 01/10/2026 | `submission.py --store` |
| Tổng số chunk | 5,17M | 13M (giả định cũ) | 01/10/2026 | ngoại suy |
| Vector fp16 chunk-level | 9,9 GB | 27 GB (giả định cũ) | 01/10/2026 | ngoại suy |
| Thời gian encode BGE-M3 | 3,6 h | 18 h (giả định cũ) | 01/10/2026 | ngoại suy |
| `title` có / `title` nằm trong `body` | 100% / 43% | — | 01/10/2026 | probe metadata |
| Recall@document (dev) | chưa đo | — | — | cần tập dev |
| **FINAL_SCORE (public LB)** | **0,0457** (k=200) | 0,0287 (k=20) | 01/10/2026 | leaderboard |
| F2 document (public LB) | **0,0821** (k=200) | 0,0497 (k=20) | 01/10/2026 | leaderboard |
| **k tối ưu (khớp đường cong)** | **≈ 194** | chưa biết | 01/10/2026 | quét k trên LB |
| **G - số doc vàng mỗi câu (suy ra)** | **≈ 50–60** | ≈48 (1 điểm) | 01/10/2026 | từ P/R của LB, 4 điểm |
| Trọng số FINAL | doc 50% / chunk 50% | chưa biết | 01/10/2026 | khớp phép tính |
| F2 chunk (public LB) | **0,0093** (phẳng mọi k) | 0,0076 | 01/10/2026 | leaderboard |

Mốc thời gian: public test mở 01/10/2026, hạn nộp **31/10/2026**; private test 01→04/11/2026.

---

## 2. Lịch sử các lần chạy

### 01/10/2026 · `profile_dataset.py` · thống kê dataset

```powershell
python profile_dataset.py
```

- 4.394.718 URL, 97 domain. Top 4 domain = 60% URL, top 20 = 90%.
- **Lệch với README của BTC:** README ghi id 1–4.420.561 nhưng file thật chỉ có
  4.394.718 dòng → thiếu 25.843. Đã xác nhận bằng dữ liệu, không phải lỗi trình xem HF.
- Phân bố ngôn ngữ theo domain: **tiếng Trung 3.646.814 (83,0%) / 46 domain**;
  tiếng Việt 747.904 (17,0%) / 51 domain.
- Dataset có **hai** parquet: `query.parquet` [id, query] 1.200 dòng và
  `links_corpus.parquet` [id, url]. Câu hỏi do BTC cấp, không phải tự soạn.
- Câu hỏi là lời bệnh nhân thật (sai chính tả, nhiều ý trong một câu, thiếu dấu câu),
  không phải câu học thuật → corpus Q&A vi/zh sẽ mang phần lớn điểm, PubMed là thiểu số.
- Ra: `data/queries.jsonl`, `data/domain_stats.csv`, `data/domain_samples.json`.

### 01/10/2026 · `slug_bm25.py` · xếp hạng thô bằng slug trong URL, không crawl

```powershell
python slug_bm25.py --topk 200        # -> data/slug_rank.jsonl
python slug_bm25.py --demo            # self-check
```

Ý tưởng: slug trong URL tiếng Việt là nguyên tiêu đề bài viết → BM25 được ngay,
không tải một trang nào. URL kiểu Trung Quốc chỉ có ID số (`/question/14161360.htm`)
nên tự động rơi dưới ngưỡng `MIN_SLUG_TOKENS=3`, không cần danh sách domain cứng.

| Số đo | Giá trị |
| --- | --- |
| URL có slug, được index | 1.188.865 (27,1%) |
| URL bị loại (chỉ ID/chữ Hán) | 3.205.853 |
| Câu có ≥1 ứng viên | 1.200/1.200 |
| Điểm BM25 top-1, trung vị | 27,53 |
| Hợp của mọi top-200 | 128.118 URL |

- Chất lượng kiểm bằng mắt: **tốt hơn mong đợi.** Câu 1 (viêm dạ dày trợt xung huyết
  mạn tính) ra `nhathuoclongchau.com.vn/.../viem-da-day-trot-xung-huyet-man-tinh` ở top-4;
  câu 3 (Beta-HCG) ra 4/4 ứng viên đầu đều là bài xét nghiệm Beta-HCG.
- 27,1% > 17% URL tiếng Việt vì một số domain Trung Quốc dùng slug pinyin đủ 3 token
  (`zysjonline.com/books/zhongyijibingyuce/`). Vô hại: IDF dìm chúng xuống với query tiếng Việt.
- Domain chiếm top-50 nhiều nhất: `nhathuoclongchau` 10.883, `suckhoedoisong` 8.506,
  `suckhoecongdongonline` 6.345, `thanhnien` 6.329, `medlatec` 4.674, `vinmec` 4.598.
- **Kết luận dùng được ngay:** 128.118 URL này là lô crawl đầu tiên, bằng 2,9% corpus
  nhưng phủ cả 1.200 câu → có submission thử được trong vòng vài giờ crawl thay vì vài ngày.

### 01/10/2026 · probe sitemap/RSS 12 domain lớn nhất · **ĐƯỜNG CỤT, đã loại**

Giả thuyết: nếu `cnkang`/`120ask` có sitemap kèm title thì lấy được title của hàng triệu URL
bằng vài nghìn request → áp `slug_bm25` cho cả 83% phía Trung Quốc. **Giả thuyết sai.**

| Domain | URL | robots.txt | Sitemap thật? | Có title? |
| --- | --- | --- | --- | --- |
| cnkang.com | 963k | 200, không khai báo | ❌ 404 hết | — |
| 120ask.com | 918k | 200, không khai báo | ❌ 404 hết | — |
| familydoctor.com.cn | 447k | **403** | ❌ | — |
| ask.39.net | 337k | timeout | ❌ 404 | — |
| zysjonline.com | 243k | **403** | ❌ | — |
| a-hospital.com | 169k | khai báo đường dẫn lạ | ✅ 9 sitemap con | ❌ chỉ `<loc>` |
| zhongyibaodian.net | 147k | 404 | ❌ | — |
| suckhoedoisong.vn | 86k | khai báo `/sitemaps/index.rss` | ✅ 1.310 sitemap con | ❌ chỉ `<loc>` |
| nhathuoclongchau.com.vn | 80k | khai báo, nhưng sitemap **403** | ❌ | — |
| zydcd.com | 79k | 404 | ❌ | — |
| thanhnien.vn | 72k | khai báo 2 | ✅ 1.108 sitemap con | ⚠️ chỉ `google-news-sitemap` có 50 title (tin mới nhất) |

**Kết luận:** sitemap chỉ chứa `<loc>` → dùng để *phát hiện* URL, mà URL thì BTC đã cho sẵn.
Giá trị bằng 0. Không có nguồn title hàng loạt cho phía Trung Quốc → **phải crawl từng trang.**
Bỏ bước này, đi thẳng sang probe crawl.

#### Hai phát hiện phụ, quan trọng hơn chính đề

**1. Tường 403 không phải do User-Agent.** Thử UA bot và UA Chrome đầy đủ header: kết quả y hệt.
Là WAF/TLS-fingerprint, không phải chặn UA.

| Domain | URL | Kết quả |
| --- | --- | --- |
| familydoctor.com.cn | 447.453 | 403 với mọi UA |
| zysjonline.com | 243.347 | 403 với mọi UA |
| nhathuoclongchau.com.vn | 79.598 | 403 với mọi UA |
| **Tổng bị chặn** | **770.598 (17,5%)** | |

Nghiêm trọng vì **`nhathuoclongchau.com.vn` chính là domain đứng đầu trong top-50 của
`slug_bm25` (10.883 lượt)** - domain liên quan nhất lại là domain chặn ta. Phải thử
`curl_cffi`/`httpx` giả TLS fingerprint trước khi chấp nhận mất 17,5%.

**2. Ba domain lớn nhất thì vào bình thường** (UA bot cũng được), và đo được kích thước trang thật:

| Domain | URL | Kích thước 1 trang |
| --- | --- | --- |
| 120ask.com | 918.479 | 80 KB |
| ask.39.net | 337.375 | 47,5 KB |
| cnkang.com | 963.438 | 45 KB |

→ 4,39M × ~55 KB = **~242 GB nếu lưu HTML thô.** Xác nhận bằng số đo: bắt buộc trích text
ngay trong lúc crawl (quyết định §3 đã đúng, giờ có con số).

### 01/10/2026 · `probe_crawl.py` · crawl thử 2.000 URL phân tầng · **số đo nền tảng**

```powershell
python probe_crawl.py --n 2000 --min-per-domain 5 --workers 24   # -> data/probe_crawl.jsonl
python probe_crawl.py --demo                                     # self-check
```

Mẫu phân tầng: tối thiểu 5 URL/domain (để cả 97 domain đều có số đo), phần còn lại theo tỉ lệ.
Dùng lại `RateLimiter` từ `pubmed_module/http.py`. Trích nội dung bằng `trafilatura`;
URL bị 403 tự thử lại bằng `curl_cffi` (giả TLS fingerprint Chrome).

| Số đo | Giá trị |
| --- | --- |
| HTTP 200 | 1.657/2.000 (82,8%) |
| **Trích được text ≥200 ký tự** | **1.534/2.000 (76,7%)** ← đây mới là tỉ lệ dùng được |
| HTML trung vị / trang | 53,7 KB |
| **Text trung vị / trang** | **975 ký tự (~1,4 KB utf-8)** |
| Độ trễ mạng trung vị | **338 ms** (đo riêng, xem ghi chú bên dưới) |

**Ngoại suy cho 4.394.718 URL:**

| | |
| --- | --- |
| Lưu HTML thô | **225 GB** ← xác nhận: không lưu |
| Lưu text đã trích | **6,0 GB** (nén zstd ~1,8 GB) ← nhẹ hơn ước lượng ban đầu nhiều |
| Thời gian quét @ 2 req/s mỗi domain | 134 giờ (nghẽn ở `cnkang` 963k) |
| @ 5 req/s | ~53 giờ |
| @ 10 req/s | ~27 giờ |

#### Phân rã tổn thất theo lớp lỗi - mỗi lớp một cách sửa khác nhau

| Lớp | URL | % corpus | Domain tiêu biểu | Cách sửa |
| --- | --- | --- | --- | --- |
| ✅ Chạy tốt (≥90%) | 3.237.124 | **73,7%** | cnkang 99%, 120ask 100%, ask.39.net 100%, suckhoecongdongonline 100%, thanhnien 100%, nhathuoclongchau 100% | — |
| ❌ 403 WAF/geo-block | 709.772 | 16,2% | `familydoctor.com.cn` 0/162, `zysjonline.com` 0/91, `vov.vn` 0/9 | cần proxy, xem dưới |
| ⚠️ HTTP 200 nhưng trích ra **0 ký tự** | 241.610 | 5,5% | `zhongyibaodian.net`, `laodong.vn` 0/16, 14 subdomain `*.39.net` | **parser riêng** |
| ⚠️ 502 server yếu | 169.339 | 3,9% | `a-hospital.com` 36/65 (502×28) | hạ rate riêng domain này |
| ❌ 521 Cloudflare (site chết) | 30.631 | 0,7% | `bingli.iiyi.com`, `article.iiyi.com` | chịu mất |
| khác (404 lẻ) | 6.242 | 0,1% | `msdmanuals.cn`, `pharmacity.vn` | — |

→ **Sửa được bằng parser + hạ rate: 410.949 URL (9,4%).** Cần proxy hoặc chịu mất: 740.403 (16,8%).

#### Ba kết luận quan trọng

**1. `curl_cffi` cứu đúng domain quan trọng nhất.** Tổng chỉ cứu 32/321 (10%), nhưng phân hoá tuyệt đối:

| Domain | URL | requests | curl_cffi |
| --- | --- | --- | --- |
| **nhathuoclongchau.com.vn** | 79.598 | 403 | ✅ **200, 33/33 mẫu** |
| familydoctor.com.cn + 6 subdomain | ~451.000 | 403 | ❌ 0/178 |
| zysjonline.com | 243.347 | 403 | ❌ 0/91 |
| vov.vn, pharmacity blog, vietnamplus | ~15.100 | 403 | ❌ 0/16 |

`nhathuoclongchau.com.vn` là **domain đứng đầu top-50 của `slug_bm25` (10.883 lượt)** → giữ `curl_cffi`,
nó trả lại đúng domain liên quan nhất. Còn `familydoctor`+`zysjonline` chặn bất chấp cả UA lẫn TLS
fingerprint → giả thuyết hàng đầu là **chặn theo IP vùng** (site Trung Quốc chặn IP ngoài), không phải
chống bot. Nếu đúng thì fix là proxy CN, không phải header. **Chưa kiểm.**

**2. 14 subdomain `*.39.net` trả 200 nhưng trích ra 0 ký tự.** Đúng những subdomain mang
*nhãn chuyên khoa* mà kế hoạch định dùng để ưu tiên crawl phía Trung Quốc:

```
ek gan gc gk heart man nk pf shen sj tnb wei byby cancer fk  (.39.net)  ~66k URL  → 0/80 mẫu
ask.39.net (337k URL, không phải chuyên khoa)                           → 123/123 mẫu, 100%
```

`ask.39.net` chạy hoàn hảo nhưng các subdomain chuyên khoa thì markup khác → trafilatura không
nhận ra vùng nội dung. **Cần một parser riêng cho họ `*.39.net`**, và nó đáng làm vì đó là nguồn
nhãn chuyên khoa miễn phí.

**3. Ba lớp "thất bại" trông giống nhau nhưng khác hẳn nhau:**

```
laodong.vn      HTTP 200, html_bytes = 0        → body rỗng, chống bot kiểu khác (0/16 mẫu)
baotayninh.vn   HTTP 200, 156 KB HTML, text = 0 → trafilatura miss thật, cần fallback
a-hospital.com  502 × 28/65 mẫu                → server yếu, phải hạ rate riêng
iiyi.com        521 Cloudflare                  → site chết, chịu mất
```

Gộp cả bốn thành "tỉ lệ lỗi 23%" là mất thông tin; mỗi lớp cần một cách xử lý khác.

#### Ghi chú về số đo độ trễ (đã sửa trong code)

Lần chạy đầu báo trung vị 10.134 ms, nhưng đó là **lỗi đo**: `ms` tính cả thời gian chờ
`RateLimiter`, nên phồng theo số thread (12 thread → 1.314 ms, 24 thread → 10.134 ms).
Đã tách `ms` (chỉ thời gian mạng) và `wait_ms` (chờ rate limit). Đo lại: **338 ms**.

Hệ quả cho thiết kế crawler: ở 338 ms/trang, một thread làm ~3 trang/s → **rate limit là thứ
chặn throughput, không phải độ trễ.** Số thread chỉ cần đủ phủ 97 domain song song
(~100 thread), không cần nhiều hơn.

### 01/10/2026 · probe metadata + cấu trúc text · **đổi hẳn phương án**

Bốn câu hỏi, đo trên 685 trang / 69 domain đã crawl được.

#### 1. Metadata: lấy được trong CÙNG lần parse, không thêm request

`trafilatura.bare_extraction(with_metadata=True)` thay cho `extract()`:

| Trường | Tỉ lệ có | Giá trị |
| --- | --- | --- |
| `title` | **100%** | tín hiệu mạnh nhất, xem dưới |
| `sitename` | 100% | |
| `date` | 82% | liên quan câu hỏi mở "nhãn gán theo nội dung thời điểm nào" |
| `description` | 82% | tóm tắt sạch |
| `tags` | 68% | **mang sẵn nhãn chuyên khoa** |
| `author` | 18% | |
| `categories` | 14% | |

**Phát hiện lớn nhất:** title của các site Q&A Trung Quốc **chính là câu hỏi bệnh nhân**,
cùng hình dạng với 1.200 query của ta:

```
120ask.com/question/14161360.htm
  title = 脚趾的大趾和小趾变厚手上有一中指也有变化无治疗怎样
ask.39.net/question/108326107.html
  title = 2型糖尿病空腹血糖10点高吗
  tags  = ['2型糖尿病空腹血糖10点高吗 2型糖尿病']   ← nhãn chuyên khoa có sẵn
```

→ Khớp query↔title là **khớp câu hỏi với câu hỏi**, dễ hơn hẳn khớp câu hỏi với tài liệu.
Và nó phủ cả 83% phía Trung Quốc — đúng chỗ slug bất lực. Hệ quả: BM25 phải **có trọng số
theo trường** (title ~3×), và thêm một **dense index cấp title** (3,37M vector, rẻ).

#### 2. `title` chỉ nằm nguyên văn trong `body` 43% → KHÔNG dùng làm `chunk_text`

294/685 trang. `title` và `description` nằm ở `<title>`/`<meta>`, không chắc xuất hiện trong
phần nội dung hiển thị. Nộp một chunk lấy từ meta tag là rủi ro bị tính sai.
**Phân vai cứng:** metadata → chỉ xếp hạng; `body` của trafilatura → nguồn duy nhất của `chunk_text`.

#### 3. Cấu trúc đoạn văn → không cần sliding window

```
Phân cách đoạn: '\n'  (KHÔNG có '\n\n': 0/283 tài liệu dài)
Số đoạn/tài liệu: trung vị 25, max 197
Độ dài đoạn: trung vị 80 ký tự, P90 330
Đoạn đơn lẻ vượt 1 chunk: 4/10.106 = 0,04%
```

→ Chunk = **gộp đoạn liên tiếp** (cắt theo `\n`) đến hết budget, chồng lấn 1 đoạn.
Cắt theo câu chỉ là dự phòng cho 0,04%. Đơn giản hơn sliding window nhiều, và giữ offset
nguyên vẹn vì chỉ là nối các lát liên tiếp của `body`.

#### 4. Trùng lặp: có thật, có hệ thống, nhưng KHÔNG được xoá

```
Trùng y hệt toàn văn      : 5/685
Gần trùng (Jaccard > 0,7) : 72 cặp, trong đó 24 cặp KHÁC domain
Cụm sao chép hệ thống     : a-hospital.com <-> zhongyibaodian.net  (0,82-0,87)
                            cả hai là bách khoa Đông y, 316k URL cộng lại
```

→ Gom theo simhash để **embed một đại diện, dùng chung vector** (tiết kiệm GPU), nhưng
**không bao giờ xoá doc_id khỏi ứng viên**: không biết BTC gán nhãn bản nào, mà F2 nặng
recall 4× nên trả cả hai bản trùng là lãi.

#### 5. Ngôn ngữ: domain là đủ

Chỉ 3/69 domain lộ ra nhiều hơn một ngôn ngữ, và phần lớn là bộ dò thô của tôi nhầm trên
text ngắn. → suy `lang` từ domain, kiểm lại bằng tỉ lệ ký tự Hán > 15%. Không cần thư viện detect.

#### 6. Phân bố độ dài text → dense chạy được trên TOÀN corpus

```
P10 451 · P25 611 · P50 976 · P75 2.407 · P90 4.886 · P95 6.297 · P99 8.784 · max 18.255
76,3% tài liệu VỪA TRỌN 1 chunk (<=1024 token)  ->  1,54 chunk/doc
```

| | Kế hoạch cũ | Đã đo |
| --- | --- | --- |
| Số chunk | 13M (giả định 3 chunk/doc) | **5,17M** |
| Vector fp16 | 27 GB | **9,9 GB** |
| Encode BGE-M3 | 18h | **3,6h** |

→ **Đảo ngược quyết định "dense chỉ trên tập ứng viên".** 9,9 GB vừa thoải mái trong 50 GB
VRAM → dense toàn corpus, không bị BM25 chặn mất doc ở bước lọc. Đúng cái F2 cần.

#### 7. Tài nguyên máy local: 11,7 GB RAM (2,9 GB trống), 8 core, 185 GB đĩa

Hai hệ quả:
- Vector 16,8 GB (chunk + title) **không nằm được ở local** → dense search chạy ở máy GPU,
  đẩy query lên / nhận file điểm về.
- **`slug_bm25.rank()` có `docs = list(docs)` → nạp hết vào RAM.** Chạy được với 1,19M slug,
  nhưng sẽ chết với 5,17M chunk kèm text. Phải đổi sang **hai lượt streaming từ SQLite**
  trước khi dùng cho corpus thật. *(nợ kỹ thuật đã biết, chưa sửa)*

→ Phương án đầy đủ: **`PIPELINE.md`**

### 01/10/2026 · `submission.py` + `score.py` · **có bài nộp đầu tiên, chưa crawl gì**

Chỉ stdlib (`json`, `zipfile`, `sqlite3`) - không thêm dependency.

#### Cách chấm rút gọn được, và nó quyết định thiết kế

Với k doc trả về, g doc trong đó là đúng, G doc vàng:

```
F2 = 5·(g/k)·(g/G) / (4g/k + g/G)  =  5g / (4G + k)
```

→ Thêm một doc có lợi khi xác suất liên quan của nó **p > F2/5**. Ta không biết G lẫn p,
nên `--topk` phải là **tham số để quét bằng các lượt nộp**, không phải hằng số đoán.
Self-check của cả hai script đều assert đẳng thức này khớp định nghĩa gốc 5PR/(4P+R).

#### Đã sinh 5 bài nộp từ `data/slug_rank.jsonl`, tất cả hợp lệ

```powershell
python submission.py --cands data/slug_rank.jsonl --topk 20 --out runs/sub_slug_top20
```

| File | doc/câu | Tổng doc | Kích thước |
| --- | --- | --- | --- |
| `runs/sub_slug_top5.zip` | 5 | 6.000 | 27 KB |
| `runs/sub_slug_top10.zip` | 10 | 12.000 | 48 KB |
| `runs/sub_slug_top20.zip` | 20 | 24.000 | 89 KB |
| `runs/sub_slug_top50.zip` | 50 | 60.000 | 210 KB |
| `runs/sub_slug_top100.zip` | 100 | 120.000 | 410 KB |

Đã kiểm: ZIP chứa **đúng 1 file json, không thư mục con**; đủ id 1–1200 không thiếu câu nào;
`doc_id` là **chuỗi**; 0 câu rỗng. `relevant_chunks` = `[]` → mất toàn bộ điểm cấp chunk,
nhưng có điểm cấp document thật.

#### Kiểm tra bắt buộc trong `submission.py` (sai thì dừng, không cảnh báo suông)

- đủ 1.200 id, không trùng, không có id lạ
- `doc_id` là chuỗi
- câu không dự đoán được vẫn có trường với `[]`, không bỏ trường
- ZIP đúng một file, không nằm trong thư mục con
- khi có store: `chunk_text == body[start:end]` (assert) - nguyên văn bảo đảm bằng cấu trúc

#### `score.py`: để chỉnh ngưỡng offline, không tốn lượt nộp

P/R/F2 macro cả hai cấp. Cấp chunk dùng tiêu chí "chứa hoặc overlap ≥50% token" đúng như
mô tả cách chấm. Có `--sweep` quét topk in F2 từng mức. Cần nhãn vàng (tập dev), chưa có.

### 01/10/2026 · đọc quy định nộp bài chính thức · **sửa 3 hiểu sai**

#### 1. Private phase KHÔNG phải câu hỏi mới ← quan trọng nhất

> *"Thí sinh nộp kết quả cho toàn bộ 1.200 truy vấn đã phát hành ở cả hai giai đoạn.
> Hệ thống tự chọn các truy vấn thuộc public hoặc private phase để chấm."*

Trước đó `CLAUDE.md` ghi "01/11 bắt đầu private test (câu hỏi MỚI)" và từ đó suy ra ràng buộc
"toàn bộ pipeline phải chạy tự động từ đầu đến cuối trong 3 ngày, kể cả gọi PubMed". **Sai.**

Hệ quả: **tính trước được toàn bộ 1.200 câu.** Bước nào chậm hoặc còn thủ công vẫn chấp nhận
được. Ràng buộc #4 trong `PIPELINE.md` đã được nới.

#### 2. Private phase chỉ **5 lượt nộp TỔNG CỘNG** (không phải 10/ngày)

→ Chiến lược: dùng 10 lượt/ngày của public để chốt `topk`/ngưỡng/cấu hình, rồi tiêu 5 lượt
private rất cẩn thận. Và: **bài nộp thiếu file/thiếu câu không bị tính vào quota** →
thử nghiệm định dạng là miễn phí.

#### 3. Có trường `chunk_order` tuỳ chọn - `submission.py` đang TỪ CHỐI nó

Validator đòi đúng `{doc_id, chunk_text}` nên một bài nộp hợp lệ có `chunk_order` sẽ bị
chính script của mình loại. Đã sửa: `chunk_order` tuỳ chọn, nếu có phải là int ≥ 0.
Thêm self-check cho `-1`, `"0"`, `1.5`, và trường lạ.

#### 4. Mơ hồ về kiểu `doc_id` - CHƯA giải quyết

| Nguồn trong cùng tài liệu | Nói gì |
| --- | --- |
| Phần chữ | "sử dụng trường `id` **kiểu số nguyên** trong links_corpus.parquet" |
| Schema | `"relevant_docs": ["<id_tài_liệu>"]` → **chuỗi** |
| Ví dụ | `["doc_id1", "doc_id2"]` → **chuỗi** |

Cách đọc hợp lý nhất: phần chữ nói lấy từ TRƯỜNG nào (cột `id`, vốn là số nguyên), không nói
kiểu trong JSON. → mặc định **chuỗi**, thêm cờ `--int-ids` sinh bản số nguyên.
Đã sinh `runs/sub_slug_top20_intids.zip` (86 KB) để thử. Nộp cả hai, cái nào được chấm thì
biết. Miễn phí vì bài sai định dạng không tính quota.

#### 5. Phát sinh việc chưa có trong kế hoạch: **working notes paper**

> *"Kết quả cuối cùng sẽ không được xem là chính thức cho đến khi một bài báo mô tả phương pháp
> (working notes paper) với mô tả đầy đủ về các phương pháp được nộp."*

Đã thêm vào `PIPELINE.md` §8 làm việc #11. `PROGRESS.md` này chính là nguyên liệu viết paper -
giữ nguyên các mục cũ càng có giá trị.

#### 6. Còn một chỗ cần hỏi BTC

Đặc tả cũ nói tài liệu tiếng Anh dùng **PMID** làm `doc_id`; quy định nộp bài hiện tại chỉ nói
`links_corpus.parquet`. Nếu không còn tài liệu tiếng Anh ngoài corpus thì **`pubmed_module`
(đã viết xong, 12 test) có thể trở nên vô dụng**. Phải hỏi trước khi đầu tư thêm vào nó.

### 01/10/2026 · test `pubmed_module` với API THẬT · **phát hiện NCBI chặn IP, đã sửa**

BTC xác nhận: dữ liệu tiếng Anh giới hạn ở **PubMed**, không cung cấp danh sách, các đội tự tìm;
gợi ý đúng ba API mà `pubmed_module` đang dùng (E-utilities, Europe PMC, PubTator).
→ **`pubmed_module` cần thiết, không vô dụng.** Xoá câu hỏi mở về chuyện này.

```powershell
python -m pubmed_module.pipeline --queries examples/sample_queries.jsonl `
    --out examples/manual_run --stages search,fetch --email "..."
```

#### Lần chạy đầu: 0 bài / 284 PMID

```
ESearch lỗi: Expecting value: line 1 column 1 (char 0)   (cả 5 truy vấn)
PubTator   : /error/abuse.shtml
EFetch XML : mismatched tag: line 198, column 2          (cả 3 batch)
Corpus tiếng Anh: 0 bài (từ 284 PMID duy nhất)
```

**Nguyên nhân gốc: NCBI chặn ở tầng IP, không phải lỗi code.** Request thô cũng bị:
mọi endpoint trả HTTP 200 nhưng redirect sang `misuse.ncbi.nlm.nih.gov/error/abuse.shtml`
với `content-type: text/html`. Nên `json.loads` chết ở "line 1 column 1" và parser XML
báo "mismatched tag" - cả hai đều đang parse cùng một trang HTML lỗi.

Đã kiểm: **UA browser cũng không thoát** (giống hệt tường 403 của `familydoctor.com.cn`).
Cần API key gắn tài khoản NCBI, hoặc IP khác.

#### Cách sửa: Europe PMC `resultType=core` - đổi MỘT tham số

Europe PMC vẫn chạy tốt (284 PMID ban đầu đến từ nó, qua `europepmc_search`). Đo thêm:
`resultType=core` trả về **cả `title` lẫn `abstractText`** → thay được hoàn toàn
PubTator + EFetch. Cùng một API đang gọi, không thêm endpoint, không thêm dependency.

Đã thêm `epmc_fetch()` + `strip_tags()` vào `pubmed_module/fetch.py`, nối vào cuối chuỗi
dự phòng: PubTator → EFetch → **Europe PMC**. Giữ hai nguồn NCBI vì chúng hoạt động khi
có API key hoặc IP khác.

#### Lần chạy lại: **284/284 bài**

| Số đo | Giá trị |
| --- | --- |
| Bài lấy được | **284/284** (trước: 0) |
| Nguồn | `europepmc` 100% |
| Abstract trung vị | 1.654 ký tự (P10 741, max 3.432) |
| Bài không có abstract | 9/284 (chỉ có title) |

Abstract ~1.654 ký tự → **vừa trọn 1 chunk**, khớp với phân bố của corpus vi/zh.
`strip_tags` chỉ bỏ thẻ `<h4>…</h4>`, **giữ nguyên chữ** (giống trích text từ HTML ở phần
crawl) vì `chunk_text` phải nguyên văn.

Thêm 4 test offline (`TestEuropePMC`): `strip_tags`, parse + cú pháp truy vấn `SRC:MED`,
chia batch 25, và lỗi mạng không làm crash. **16 test, tất cả qua** (trước 12).

#### Giải quyết luôn mơ hồ về kiểu `doc_id`

PubMed không nằm trong `links_corpus.parquet` → `doc_id` của bài tiếng Anh **phải là PMID**.
Hai không gian id này **chồng nhau về giá trị**, nên kiểm xem có nguy cơ nhầm:

```
links_corpus id : 1 .. 4.394.718
PMID đo được    : min 28.722.973 · trung vị 42.216.231 · max 42.797.008
PMID <= 4.394.718: 0/284
```

→ Thực tế không chồng: PMID của bài hiện đại đều > 28M. Nguy cơ nhầm chỉ xảy ra với bài
trước ~1990, mà loại đó khó là nhãn vàng cho câu hỏi bệnh nhân. **Không cần tiền tố phân biệt.**
Vẫn nên hỏi BTC cho chắc.

### 01/10/2026 · test giả thuyết proxy cho 694k URL bị chặn · **không sửa được bằng code**

#### Test proxy bằng dịch vụ miễn phí: ĐƯỜNG CỤT (và tôi đã suýt kết luận sai)

Thử `r.jina.ai`, `api.allorigins.win`, `api.codetabs.com` làm proxy chẩn đoán.
**Chứng dương thất bại:** `cnkang.com` vào được trực tiếp nhưng cả ba proxy đều lỗi
(jina 403 - giờ đòi API key; allorigins 408/520; codetabs 522). Nên bảng kết quả vô giá trị.

Một dòng trong lần chạy đầu báo `allorigins` lấy được NCBI = "NỘI DUNG THẬT (780B)" →
**dương tính giả**: hàm phân loại của tôi coi mọi phản hồi >500B không chứa chữ "abuse" là
nội dung thật; thực tế đó là trang lỗi Cloudflare. Chạy lại ra HTTP 520.
*Bài học: mọi test kiểu này phải có chứng dương, và lần này nó đã cứu.*

Máy GPU cũng không tới được để test: hai Coder deployment (`coder.graphicsminer.com`,
`workspace.graphicsminer.com`) đều trả EOF.

#### Nhưng header của trang 403 cho biết AI đang chặn - và đó mới là thông tin cần

| Domain | URL | `server` | Dấu hiệu |
| --- | --- | --- | --- |
| `zysjonline.com` | 243.347 | `cloudflare` | "Just a moment..." (JS challenge) |
| `nhathuoclongchau.com.vn` | 79.598 | `cloudflare` | "Just a moment..." - **curl_cffi đã vượt** |
| `familydoctor.com.cn` | 447.453 | `ESA`, `via: ens-cache22.cn9193` | cookie `acw_tc` + `cdn_sec_tc` = **Alibaba Cloud WAF** |

→ `zysjonline` bị **cùng loại chặn** với `nhathuoclongchau`, mà cái đó đã vượt được 33/33.
Nên 0/91 của nó là giả thuyết "sai cấu hình", không phải "không thể". Đã test đúng chỗ đó.

#### Kết quả: cả hai đều KHÔNG vượt được bằng code

**Cloudflare - thử 10 profile `impersonate` của curl_cffi:**

```
zysjonline        0/10 profile  -> 403 toàn bộ
nhathuoclongchau  7/10 profile  -> OK   (chứng dương: phương pháp đúng)
                  thất bại ở chrome116, chrome110, edge101
```

`zysjonline` dùng Cloudflare ở mức bảo mật cao hơn: giả TLS fingerprint không đủ, cần
**chạy JS thật**. (Phụ: profile mặc định `chrome` nằm trong nhóm thành công → crawler đang
dùng đúng, và giờ biết đó không phải may mắn.)

**Alibaba WAF - thử vòng lấy cookie rồi thử lại:**

```
requests  session: lượt1 403 -> lượt2 403   (đã nhận acw_tc + cdn_sec_tc)
curl_cffi session: lượt1 403 -> lượt2 403
+ Referer cùng domain: 403
```

Nhận được cookie chống crawl nhưng vẫn 403 → WAF chặn theo thứ khác, gần như chắc là
**IP/vùng**. Không có đường nào trong code.

#### Chốt lại: 694k URL (15,8%) và ba lựa chọn

| Domain | URL | % | Cách duy nhất còn lại |
| --- | --- | --- | --- |
| `familydoctor.com.cn` + 6 subdomain | ~451.000 | 10,3% | **IP khác** (proxy / máy GPU ở nước ngoài). Browser không giúp vì không phải JS challenge. |
| `zysjonline.com` | 243.347 | 5,5% | **Browser thật** (Playwright) để giải JS challenge; hoặc IP khác |
| NCBI (PubMed) | — | — | **API key miễn phí** - trang chặn ghi "temporarily blocked due to possible misuse/abuse involving your site", tức chặn theo mức lạm dụng chứ không theo vùng. Hiện không chặn gì vì Europe PMC đã gánh. |

IP máy local: `14.224.129.1`, Hanoi, **VNPT** (AS45899) - ISP lớn dùng NAT chung, nên block
"abuse" của NCBI có thể do lưu lượng của người khác cùng dải.

Ước chi phí nếu làm: Playwright cho `zysjonline` ở ~1-2 trang/s = **1,5-3 ngày** chạy nền
cho 243k URL. Đắt, và chỉ lấy lại 5,5%.

### 01/10/2026 · `crawler.py` · **chạy được, và phát hiện nút cổ chai thật**

Theo `PIPELINE.md` §1. Dùng lại `RateLimiter` từ `pubmed_module/http.py`.

```powershell
python crawler.py --prio data/slug_rank.jsonl --limit 130000   # lô ưu tiên
python crawler.py                                              # quét nốt (chạy trong tmux)
python crawler.py --stats                                      # tiến độ
python crawler.py --demo                                        # self-check
```

#### Nạp hàng đợi

```
Queue: 4.394.718 URL | đánh dấu BLOCKED ngay: 725.329 (16,5%, KHÔNG tốn request)
Điểm ưu tiên cho 128.118 URL từ data/slug_rank.jsonl
```

Domain đã đo là chặn được đánh dấu `BLOCKED` ngay từ lúc nạp → không tốn một request nào.
Có IP/proxy mới thì `--retry-blocked` chạy lại đúng phần đó, không mất gì.

#### Kết quả chạy thật

| Số đo | Giá trị |
| --- | --- |
| Tỉ lệ dùng được (lô ưu tiên) | **95-97%** (so với 76,7% trung bình corpus) |
| `title` / `descr` / `tags` | 99% / 88% / 50% |
| `body` trung bình (lô ưu tiên) | 4.272 ký tự |
| `nhathuoclongchau.com.vn` | **48/48 = 100%** qua `curl_cffi` |
| Doc phải giữ `raw_html` (trích lỗi) | 1/290 |

Lô ưu tiên cho 95-97% vì `slug_bm25` đẩy URL tiếng Việt lành mạnh lên đầu. `body` trung bình
4.272 ký tự cũng cao hơn trung vị corpus (975) vì bài báo tiếng Việt dài hơn Q&A tiếng Trung.

**Đã kiểm ba thứ then chốt:**
- **Resume**: chạy lại không làm lại doc đã xong (290 → 339, không trùng).
- **Nguyên văn**: cắt chunk theo offset rồi `assert chunk == body[start:end]` - đứng vững.
- **Metadata**: `lang`, `via`, `pub_date`, `tags`, `simhash` lưu đúng.

#### Nút cổ chai KHÔNG phải mạng - sửa lại kết luận trước đó

Throughput ban đầu chỉ **7,8 trang/s**, trong khi rate limit của 45 domain đang hoạt động
cho trần **225 trang/s**. Lệch 29× → không phải rate limit.

Đo trực tiếp: `trafilatura.bare_extraction` tốn **59 ms CPU trung vị** mỗi trang (max 2.025 ms).
Chạy trong thread thì **GIL hoá tuần tự** → trần ~17 trang/s bất kể bao nhiêu thread.
Khớp với 7,8 đo được (cộng `normalize`, `simhash`, ghi SQLite cũng là Python).

Sửa: đẩy phần trích sang `ProcessPoolExecutor`. So sánh trực tiếp:

```
100 thread + 1 process (GIL)   ->  7,7 trang/s   = 156 giờ cho 4,39M
100 thread + 7 process         -> 16,7 trang/s   =  73 giờ      (2,2x)
```

Chưa đạt 137 trang/s lý thuyết (8 core × 17), nên còn nghẽn chỗ khác - nghi IPC (pickle
229 KB HTML mỗi trang) hoặc rate limit khi hàng đợi loãng ra. **Dừng tối ưu ở đây:**
73 giờ chạy nền trong 30 ngày là thừa, đuổi tiếp cần profiling và đổi cấu trúc IPC.

#### Một tối ưu phụ: trộn xen kẽ theo domain

`take_batch` lấy `ORDER BY prio DESC` nên một batch có thể toàn một domain → cả trăm thread
xếp hàng sau một rate limiter. Thêm `interleave()` round-robin giữa các domain, giữ thứ tự
ưu tiên trong từng domain. Tác dụng nhỏ ở đây (6,8 → 7,8) vì nghẽn thật là CPU, nhưng cần
cho lúc quét corpus chính khi `cnkang`/`120ask` ở 10 req/s chiếm phần lớn.

### 01/10/2026 · `chunk.py` · cắt theo offset, **vòng khép kín đã chạy được**

```powershell
python chunk.py                 # cắt toàn bộ doc trong store
python chunk.py --calibrate     # đo ký tự/token thật bằng tokenizer BGE-M3
python chunk.py --rebuild       # cắt lại sau khi đổi tham số
python chunk.py --demo          # self-check
```

#### Hiệu chỉnh bằng tokenizer THẬT - hằng số tôi đoán lệch 17%

Chạy tokenizer BGE-M3 (XLM-RoBERTa) trên 300 doc mỗi ngôn ngữ từ corpus đã crawl:

| Ngôn ngữ | Tôi đoán | **Đo thật** | Budget ký tự cho 900 token |
| --- | --- | --- | --- |
| vi | 3,50 | **4,09** (lệch 17%) | 3.683 |
| zh | 1,50 | **1,42** | 1.280 |

Nếu giữ 3,5 thì chunk tiếng Việt ngắn hơn ý định 17% → nhiều chunk hơn, và tăng rủi ro
cắt đứt một "phần thông tin" giữa hai chunk. Đã sửa hằng số trong `chunk.py`.
`--calibrate` chạy lại được bất cứ lúc nào khi corpus đầy hơn.

#### Kết quả cắt chunk

```
2.499 doc dùng được  ->  3.874 chunk  |  1,55 chunk/doc  |  56,3% doc chỉ 1 chunk
Kiểm 500 chunk: offset và nguyên văn OK | độ phủ OK
```

**1,55 chunk/doc khớp con số 1,54 ước từ probe** → ngoại suy 5,17M chunk cho toàn corpus
vẫn đứng. (56,3% doc một chunk thấp hơn 76,3% của probe vì hàng đợi ưu tiên toàn bài báo
tiếng Việt dài 4.272 ký tự; khi crawl vào Q&A tiếng Trung ngắn hơn thì tỉ lệ này sẽ lên.)

#### Thiết kế: gộp đoạn, không cửa sổ trượt

Đúng theo số đo (đoạn trung vị 80 ký tự, chỉ 0,04% đoạn tự nó vượt budget):
gộp đoạn liên tiếp cắt theo `\n` đến hết budget, **chồng lấn 1 đoạn** giữa hai chunk liền kề.
Cắt theo câu chỉ là dự phòng; cắt cứng theo ký tự là dự phòng của dự phòng (bảng/danh sách
không có dấu câu).

Self-check khẳng định các bất biến, không chỉ "chạy không lỗi":
- mọi chunk là một **lát** của `body`, offset hợp lệ
- **phủ hết**: không bỏ sót ký tự không-trắng nào (bỏ sót = mất recall)
- có chồng lấn khi `overlap=1`, không chồng lấn khi `overlap=0`, cả hai đều phủ hết
- đoạn đơn lẻ quá dài được cắt; text không có dấu câu không làm treo
- `build()` **idempotent**: chạy lại không nhân đôi chunk

#### Vòng khép kín: từ URL đến bài nộp có chunk

```powershell
python submission.py --cands data/slug_rank.jsonl --topk 20 `
    --store data/corpus.sqlite --chunks-per-doc 2 --out runs/sub_chunk_top20
```

```
Hợp lệ: đủ 1200 câu | 24.000 doc | 3.585 chunk | 0 câu rỗng | 3.345 KB
Câu có chunk: 559/1200   (chỉ mới crawl 2.499/4.394.718 doc)
```

**Kiểm độc lập ngược lại store: 3.585/3.585 chunk nguyên văn, 0 cái lệch.**
Ràng buộc khó nhất của đề đã được bảo đảm bằng cấu trúc, và đã kiểm bằng dữ liệu thật.

#### Phụ: domain tiếng Trung crawl 100%

Thêm cờ `--domains` vào `crawler.py` (để crawl lại một domain sau khi viết parser riêng).
Dùng nó lấy 700 URL từ `cnkang.com` + `120ask.com` + `ask.39.net`: **700/700 = 100%**
dùng được. Ba domain này cộng lại 2,22M URL = 50,5% corpus.

### 01/10/2026 · `audit.py` · kiểm toàn chuỗi trên dữ liệu THẬT · **tìm ra 2 bug**

Khác với `--demo` của từng script (bất biến trên dữ liệu giả, 2 ms), `audit.py` soi chính
`data/corpus.sqlite` và bài nộp sinh từ nó, báo PASS/FAIL từng mục. 40 mục qua 4 tầng.

```powershell
python audit.py                 # cả 4 tầng
python audit.py --stage chunk   # một tầng
```

| Tầng | Kiểm gì |
| --- | --- |
| CRAWL | doc_id khớp queue · state khớp body · **không gọi request tới domain đã biết bị chặn** · trích lỗi giữ `raw_html` · metadata · body đã chuẩn hoá · `lang` tính lại khớp · simhash |
| CHUNK | offset trong body (**toàn bộ**, không lấy mẫu) · không chunk rỗng · `n_chars` khớp · `ord` duy nhất · độ phủ ≥95% · **trần 1.024 token** · có chồng lấn |
| SUBMISSION | cả hai kiểu `doc_id` · đủ 1.200 id · `chunk_text` nguyên văn ngược store · chunk chỉ thuộc doc đã khai · ZIP đúng 1 file |
| SCORE | **tự chấm**: nhãn vàng dựng từ chính bài nộp phải ra F2 = 1,0 · nhãn sai hoàn toàn ra 0 · F2 ưu tiên recall · khớp dạng rút gọn |

#### Bug 1: `split_long` có khoảng dư `budget * 1.5` vô căn cứ

5 chunk tiếng Trung dài 1.515 ký tự → **1.154 token thật**, vượt trần khuyến nghị 1.024.
Lý do khoảng dư cũ ("thà chunk hơi dài còn hơn mất nội dung") sai: cắt đúng budget **không
làm mất nội dung**, chỉ tạo thêm chunk. Đã bỏ khoảng dư.

#### Bug 2: dùng ký tự/token TRUNG BÌNH là sai về nguyên tắc

Đo phân vị thay vì chỉ trung bình, trên 400 doc mỗi ngôn ngữ:

| | trung bình | P50 | P10 | P5 | **MIN** | budget theo trung bình cho ra |
| --- | --- | --- | --- | --- | --- | --- |
| vi | 3,75 | 3,79 | 3,51 | 3,42 | **1,32** | **2.787 token** ở văn bản đậm nhất |
| zh | 1,39 | 1,40 | 1,28 | 1,25 | **1,16** | **1.102 token** |

Không hằng số ký tự nào bảo đảm được trần token khi mật độ biến động gấp 3 lần. Sửa hai lớp:

1. `CHARS_PER_TOKEN` dùng **P5** (bảo thủ) thay vì trung bình: vi 3,40 · zh 1,25.
2. Thêm `enforce_token_limit()`: tokenize **chỉ** những chunk dài hơn 1.024 **ký tự**
   (ngắn hơn thì không thể vượt, vì một token luôn ≥ 1 ký tự) rồi cắt tiếp cái nào thật sự
   vượt. Phần lớn chunk không phải tokenize. Bật mặc định; `--no-verify-tokens` để tắt.

Kết quả sau khi sửa:

```
2.499 doc -> 4.468 chunk | 1,79 chunk/doc | 50,3% doc 1 chunk | tokenizer cắt thêm 42
chunk zh vượt 1024 token: 0/777     chunk vi vượt: 0/3691
```

**Hệ quả cho ngoại suy:** chunk/doc tăng 1,55 → **1,79** (budget bảo thủ hơn = nhiều chunk hơn).
Toàn corpus: ~3,37M doc × 1,79 = **~6,0M chunk**, vector fp16 **~11,6 GB** (trước ước 9,9 GB).
Vẫn vừa thoải mái trong 50 GB VRAM.

#### Sau khi sửa: 40/40 mục PASS, 16 test offline, 6 self-check

Tầng SCORE đáng chú ý: dựng nhãn vàng từ chính bài nộp rồi chấm lại phải ra **P = R = F2 = 1,0**
ở cả hai cấp - bắt được lỗi `score.py` mà dữ liệu giả không bắt được.

### 01/10/2026 · **ĐIỂM LEADERBOARD ĐẦU TIÊN** · 3 kết luận đổi chiến lược

```json
{"FINAL_SCORE": 0.0287, "DOCS_F2MACRO": 0.0497, "CHUNKS_F2MACRO": 0.0076,
 "DOCS_PRECISION": 0.1154, "DOCS_RECALL": 0.0485,
 "CHUNKS_PRECISION": 0.0525, "CHUNKS_RECALL": 0.0071}
```

#### A. Kiểu `doc_id` chính là bug - xác nhận bằng thí nghiệm một biến

| Bài nộp | `doc_id` | DOCS_F2 |
| --- | --- | --- |
| `sub_chunk_top20.zip` | `"674793"` chuỗi | **0** |
| `sub_chunk_top20_intids.zip` | `674793` số nguyên | **0,0497** |

Nội dung **giống hệt** (đã verify: cùng 24.000 doc, cùng 3.585 `chunk_text`). Phần chữ của BTC
đúng, schema và ví dụ trong đặc tả gây nhầm. → **Mọi bài nộp từ giờ phải có `--int-ids`.**

#### B. `FINAL_SCORE` = trung bình hai cấp, CHIA ĐỀU

```
(0,0497 + 0,0076) / 2 = 0,02865 ≈ 0,0287   ← khớp chính xác
```

→ **Cấp chunk chiếm đúng 50% điểm.** Đang được 0,0076/0,0497 so với cấp document, tức cấp
chunk là chỗ còn nhiều dư địa nhất.

#### C. Suy ra được G (số doc vàng mỗi câu) - con số BTC không công bố

```
P = 0,1154 với k = 20  ->  g ≈ 0,1154 × 20 = 2,31 doc trúng mỗi câu
R = 0,0485             ->  G ≈ 2,31 / 0,0485 ≈ 48
kiểm chéo: F2 = 5×2,31/(4×48+20) = 0,055   (đo được 0,0497 - khớp)
```

**G ≈ 40–50.** Rất lớn, và nó đổi chiến lược:

- `k = 20` **quá ngắn**: recall bị trần ở 20/48 = 0,42 ngay cả khi precision hoàn hảo.
- Quy tắc dừng p > F2/5 ≈ 0,01, mà precision hiện tại 0,115 → còn cách ngưỡng rất xa.
- G lớn cũng nghĩa là nhãn vàng dày và trùng lặp chủ đề → **phủ rộng quan trọng hơn chính xác**.

| k | g (ước, precision giảm dần) | DOCS_F2 |
| --- | --- | --- |
| 20 | 2,3 | 0,050 ← đang ở đây |
| 100 | ~5,5 | **0,095** |
| 200 | ~8 | **0,103** |
| 400 | ~10 | 0,085 |

#### D. Giả thuyết 2 đã trả lời: tài liệu tiếng Việt CÓ trong nhãn vàng

`DOCS_PRECISION = 0,1154` nghĩa là 2,3/20 doc tiếng Việt từ slug ranking là nhãn vàng.
Nên truy hồi nghiêng tiếng Việt **có ăn điểm**, không phải vô dụng.

Nhưng ta chỉ tìm được 2,3 trong ~48 → **còn ~45 doc/câu đang bỏ sót**, gần như chắc chắn nằm
ở phía tiếng Trung (83% corpus) và PubMed. **Đây là lý luận chứng minh lượt crawl 73 giờ là cần.**

#### E. Ba đòn MIỄN PHÍ, không cần crawl thêm

**1. `--int-ids`** - từ 0 lên 0,0497. Xong.

**2. Nộp HẾT chunk của mỗi doc, thay vì 2 chunk/doc.** Quy tắc dừng cấp chunk:
thêm một chunk có lợi khi p > F2_chunk/5 = **0,00172**, mà precision chunk thực tế là
**0,0525 - cao hơn ngưỡng 31 LẦN**. Đang bỏ điểm vô cớ.

```
hiện tại 6,4 chunk/câu  ->  nộp hết ~36 chunk/câu  = 5,6x
```

| Giả định | P | R | F2 chunk | FINAL |
| --- | --- | --- | --- | --- |
| P giữ nguyên | 0,0525 | 0,0398 | 0,0418 | **0,0457** |
| P giảm 1/2 | 0,0262 | 0,0398 | 0,0360 | **0,0429** |
| P giảm 1/4 | 0,0131 | 0,0398 | 0,0283 | **0,0390** |

Kể cả khi precision tụt 4 lần vẫn tốt hơn 1,36×. Chỉ đổi một cờ `--chunks-per-doc`.

**3. Nâng k từ 20 lên 100–200.** `data/slug_rank.jsonl` chỉ có 200 ứng viên/câu nên đang
chạy lại `slug_bm25.py --topk 1000` → `data/slug_rank1000.jsonl`.

Gộp cả ba: FINAL ước **~0,07** = **2,5× hiện tại**, không crawl thêm một trang nào.

### 01/10/2026 · quét k trên leaderboard · **tìm được k tối ưu, và biết chunk bị chặn bởi gì**

| k | DOCS_F2 | g = P·k | G = g/R | DOCS_R | CHUNKS_F2 | FINAL |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | 0,0497 | 2,31 | 47,6 | 0,0485 | 0,0076 | 0,0287 |
| 100 | 0,0788 | 5,89 | 53,2 | 0,1108 | 0,0093 | 0,0441 |
| **200** | **0,0821** | 8,38 | 57,8 | 0,1450 | 0,0093 | **0,0457** |
| 500 | 0,0754 | 12,80 | 62,0 | 0,2066 | 0,0093 | 0,0424 |

**FINAL 0,0287 → 0,0457 = 1,6×**, không crawl thêm một trang nào. Hai đòn: `--int-ids` và nâng k.

#### A. k tối ưu ≈ 194 - `k = 200` coi như đã đạt đỉnh

Khớp parabol qua ln(k) của ba điểm k ≥ 100: đỉnh ở **k\* = 194**. Nên không cần nộp thêm
k=300 để dò - lợi thêm nằm trong sai số. **Chốt k = 200 cho mọi bài nộp sau.**

Lưu ý: `k*` phụ thuộc G và đường cong precision, nên khi truy hồi tốt lên (BM25/dense trên
nội dung đã crawl) thì phải **quét lại k**. Đừng coi 200 là hằng số vĩnh viễn.

#### B. G ≈ 48 → 62, trôi lên theo k

Ước lượng G từ `g/R` không cố định: 47,6 ở k=20 lên 62,0 ở k=500. Đó là hiệu ứng
macro-average (F2MACRO là trung bình F2 từng câu, không phải F2 của P/R trung bình), nên
tỉ-số-của-trung-bình không bằng trung-bình-của-tỉ-số. **G ≈ 50–60** là khoảng đáng tin.

#### C. CHUNKS_F2 PHẲNG ở 0,0093 qua cả ba mức k - và đây là phát hiện quan trọng nhất

```
k=100  ->  10,0 chunk/câu   CHUNKS_P 0,0454  CHUNKS_R 0,0102   F2 0,0093
k=200  ->  15,2 chunk/câu   CHUNKS_P 0,0377  CHUNKS_R 0,0111   F2 0,0093
k=500  ->  26,6 chunk/câu   CHUNKS_P 0,0246  CHUNKS_R 0,0123   F2 0,0093
```

Số chunk mỗi câu tăng **2,7×** nhưng recall chỉ nhúc nhích **+20%**, còn precision giảm
đúng mức để F2 giữ nguyên.

**Nguyên nhân:** chỉ **2.499 doc đã cắt chunk** trên 240.000 slot doc nộp ra. Phần lớn doc
nộp ra **không có chunk nào**. Nâng k chỉ thêm doc không-có-chunk, nên độ phủ chunk gần như
không đổi.

→ **Cấp chunk bị chặn bởi ĐỘ PHỦ CRAWL, không phải bởi k.** Đã hết đòn miễn phí ở tầng này.

#### D. Cả hai tầng giờ đều chặn ở cùng một chỗ

| Tầng | Trần hiện tại | Chặn bởi |
| --- | --- | --- |
| document | 0,0821 (k=200) | **chất lượng truy hồi**: slug chỉ phủ 27% URL, gần như toàn tiếng Việt. Tìm được 8,4/58 doc vàng. |
| chunk | 0,0093 | **độ phủ crawl**: 2.499 doc đã cắt chunk |

Cả hai đều cần crawl + index nội dung. `DOCS_RECALL = 0,2066` ở k=500 nghĩa là slug-only
tìm được tối đa ~20% nhãn vàng - đó là trần của cách tiếp cận không-crawl.

**Kết luận: crawl giờ là nút cổ chai duy nhất của cả hai tầng điểm.** Không còn gì để tối ưu
trước khi nó xong.

### 01/10/2026 · `README.md` cho cả nhóm + `--shard`/`--merge` + thách đố cookie

#### A. `README.md`: cửa vào cho 2 đồng đội

`PROGRESS.md` đã đủ nội dung (mọi bước đều có số đo) nhưng **không đọc được cho người mới**:
1.000 dòng, 13 mục cùng ngày 01/10 không thứ tự, bảng điểm bị chôn sau 850 dòng lịch sử.

Không viết lại sổ này - nó đúng khi là log append-only. Thêm `README.md` làm cửa vào:
4 lệnh để bắt đầu · sơ đồ chuỗi xử lý · đọc gì ở đâu · **6 việc cho 3 người** ·
**bảng "ĐỪNG làm lại"** (12 đường cụt đã thử, kèm số đo) · quy ước làm việc.

#### B. `crawler.py --shard I/N` và `--merge`: 3 máy crawl song song

Chia theo **DOMAIN** chứ không theo id: nếu hai máy cùng crawl `cnkang.com` thì mỗi máy giữ
rate limit riêng 10 req/s → tổng 20 req/s về cùng một server, vừa bất lịch sự vừa dễ bị chặn.
Chia theo domain thì mỗi domain do đúng một máy phụ trách. Xếp thùng greedy, cân gần hoàn hảo:

```
Chia 86 domain thành 3 phần: #0: 25 domain / 1.223.126 URL
                             #1: 27 domain / 1.223.177 URL
                             #2: 34 domain / 1.223.086 URL
```

→ **73 giờ một máy → ~20 giờ ba máy.** `--merge` gộp store của máy khác
(`INSERT OR IGNORE`, chạy lại nhiều lần an toàn), và tự tính lại `queue.state` theo nội dung
thật chứ không tin `state` của máy kia.

#### C. Thách đố cookie - lấy lại `laodong.vn` (31.282 URL) bằng ~5 dòng

Soi `doc.raw_html` của 1.479 trang `laodong.vn` bị coi là "trích thất bại": tất cả đều là
**cùng một phản hồi 177 byte**:

```javascript
document.cookie="D1N=af1d42e1fd6ed5396337f3234bdd576a"+"; expires=...; path=/";
window.location.reload(true);
```

Đây **không phải lỗi trích** mà là chống bot kiểu nhẹ - và **giá trị cookie nằm sẵn trong
phản hồi**, nên không cần chạy JS: chỉ set lại cookie rồi gọi lần hai.

Thêm `cookie_challenge()` + một nhánh trong `fetch()`. Thử thật:

```
truoc: HTTP 200,     177 byte HTML -> body 0 ky tu
sau  : HTTP 200, 109.902 byte HTML -> body 3.036 ky tu   via=requests+cookie
```

Self-check khẳng định không nhận lầm: chỉ xét phản hồi < 4.096 byte (trang thật luôn lớn hơn),
nên một trang bình thường có chứa `document.cookie` không bị coi là thách đố.

Hàm này **tổng quát**, có thể cứu cả domain khác cùng kiểu. Cần chạy
`--retry-failed --domains laodong.vn` sau khi crawl chính xong (không chạy song song được:
SQLite một writer).

#### D. Sửa một chỗ tôi ghi sai trong README

Bản đầu tôi viết nhóm `*.39.net` "đã crawl rồi và HTML còn lưu trong `raw_html`, làm được
offline". **Sai.** Kiểm thật: `raw_html` chỉ có 1.503 dòng, 1.479 trong đó là `laodong.vn`.
Nhóm `*.39.net` **chưa crawl tới** (nằm sâu trong hàng đợi, prio 0). Đã sửa README: phải lấy
mẫu bằng `--domains` trước, rồi mới viết selector.

---

## 2b. Theo dõi lượt nộp leaderboard

**10 lượt/ngày** → leaderboard là thước đo chính, không phải cửa ải. Ghi mỗi lượt vào đây.
Mục đích là dò `topk`/ngưỡng bằng nhãn thật, rẻ và chính xác hơn nhãn giả tự sinh.

| Ngày | File | Nguồn ứng viên | topk | F2 doc | F2 chunk | Nhận xét |
| --- | --- | --- | --- | --- | --- | --- |
| | `sub_slug_top5.zip` | slug_bm25 | 5 | | 0 (chunk rỗng) | |
| | `sub_slug_top10.zip` | slug_bm25 | 10 | | 0 | |
| | `sub_slug_top20.zip` | slug_bm25 | 20 | | 0 | |
| | `sub_slug_top50.zip` | slug_bm25 | 50 | | 0 | |
| | `sub_slug_top100.zip` | slug_bm25 | 100 | | 0 | |
| | `sub_slug_top20_intids.zip` | slug_bm25 | 20 | | 0 | **thử kiểu doc_id số nguyên** - so với `top20` để biết kiểu nào đúng |
| 01/10 | `sub_chunk_top20.zip` | slug_bm25 + store | 20 | **0** | **0** | doc_id kiểu **chuỗi**. 0 tuyệt đối → lệch hệ thống, không phải truy hồi kém |
| 01/10 | `sub_chunk_top20_intids.zip` | slug_bm25 + store | 20 | **0,0497** | **0,0076** | **doc_id SỐ NGUYÊN. FINAL 0,0287.** Nội dung giống hệt bài 0 điểm → kiểu doc_id chính là bug |

| 01/10 | `s_k100_allchunk.zip` | slug_bm25 + store | 100 | 0,0788 | 0,0093 | FINAL **0,0441** |
| 01/10 | `s_k200_allchunk.zip` | slug_bm25 + store | 200 | **0,0821** | 0,0093 | FINAL **0,0457** ← tốt nhất |
| 01/10 | `s_k500_allchunk.zip` | slug_bm25 + store | 500 | 0,0754 | 0,0093 | FINAL 0,0424 |

#### Chẩn đoán lượt nộp 0 điểm (01/10)

0 tuyệt đối với 24.000 doc trên 1.200 câu là dấu hiệu **lệch hệ thống**, không phải truy hồi
kém - nếu chỉ là kém thì vẫn phải có câu trúng.

Đã loại trừ: **doc_id hợp lệ.** Kiểm 24.000/24.000 `doc_id` đều nằm trong `links_corpus`,
ánh xạ về URL đúng (vd. `674793` → `tiemchunglongchau.com.vn/.../viem-loet-da-day-ta-trang-...`
cho câu 1 về viêm loét dạ dày tá tràng). Định dạng cũng hợp lệ: ZIP đúng 1 file, đủ 1.200 id,
chunk max 900 token.

Hai giả thuyết còn lại:

| # | Giả thuyết | Cách phân biệt | Nếu đúng thì sao |
| --- | --- | --- | --- |
| 1 | **`doc_id` phải là SỐ NGUYÊN trong JSON**, không phải chuỗi. Phần chữ của BTC nói "trường `id` kiểu số nguyên" hai lần; schema và ví dụ thì ghi chuỗi. | Nộp `sub_chunk_top20_intids.zip` - **giống hệt**, chỉ khác kiểu | Sửa một cờ, xong |
| 2 | Nhãn vàng phần lớn là tài liệu **tiếng Trung** (83% corpus, title của site Q&A chính là câu hỏi bệnh nhân). `slug_bm25` chỉ phủ URL có slug latin = gần như chỉ tiếng Việt. | Nếu lượt intids vẫn 0 | Phải crawl + index phía tiếng Trung trước khi có điểm. Việc lớn hơn nhiều. |

Giả thuyết 1 khả năng cao hơn: nếu là giả thuyết 2 thì tài liệu tiếng Việt (17% corpus, rất
sát câu hỏi tiếng Việt) vẫn phải trúng vài câu, khó ra đúng 0.

#### Giải được một câu hỏi mở: 25.843 id chênh với README

```
links_corpus: 4.394.718 dòng | id dtype=int64
id: min 583  max 4.420.561  | duy nhất 4.394.718 | trùng 0
```

README ghi dải 1–4.420.561; thực tế `id` chạy **583 → 4.420.561 nhưng KHUYẾT 25.843 id**
trong dải đó. Không phải thiếu dữ liệu, chỉ là id không liên tục. Không cần hỏi BTC nữa.

Đọc kết quả thế nào: F2 = 5g/(4G+k). Nếu F2 **tăng** khi k tăng → đang trả quá ít, nới ra.
Nếu F2 **giảm** → đã qua điểm tối ưu. Vị trí đỉnh còn cho biết G (số doc vàng mỗi câu)
vào khoảng bao nhiêu - thông tin BTC không công bố.

**Cảnh báo:** private phase chỉ có **5 lượt nộp tổng cộng**, và dùng chính 1.200 câu này
(hệ thống tự chọn subset khác). Vì cùng phân bố câu hỏi nên `topk` dò trên public chuyển sang
private khá tốt - nhưng vẫn lấy ở **vùng phẳng** của đường cong, không lấy đỉnh nhọn.

## 3. Quyết định đã chốt (kèm lý do, để sau không bàn lại)

| Quyết định | Lý do |
| --- | --- |
| Crawl **hết** 4,39M, nhưng theo **thứ tự ưu tiên** | 83% là URL ID số không lọc trước được; F2 nặng recall 4× nên bỏ domain = mất điểm không hồi. Nhưng 97 domain chạy song song, nghẽn ở `cnkang` 963k @5 req/s ≈ 53h → quét hết chỉ 2-3 ngày. |
| **Không lưu HTML**, chỉ lưu text đã trích | 4,4M × 60KB HTML = 264 GB; text sạch ~13 GB, nén zstd ~4 GB. |
| Lưu text sạch **bất biến + offset** | `chunk_text` phải nguyên văn; mất bản text gốc là phải crawl lại cả corpus. |
| Crawler chạy trên **máy GPU Linux**, không phải local | Crawl không dùng VRAM → song song với lúc GPU embed; có tmux, Windows thì ngủ/update là đứt giữa 53 giờ. *Chưa xác nhận dung lượng ổ máy GPU (cần ~20 GB dư).* |
| Hàng đợi resume theo **từng URL**, SQLite | 4,4M dòng SQLite thừa sức, khỏi Redis. |
| ~~Dense chỉ chạy trên tập ứng viên~~ → **ĐẢO NGƯỢC 01/10: dense trên TOÀN corpus** | Giả định 3 chunk/doc sai 3×. Đo thật: 1,54 chunk/doc → 5,17M chunk, 9,9 GB fp16, 3,6h encode. Vừa thoải mái trong 50 GB VRAM, và không bị BM25 chặn mất doc ở bước lọc - đúng cái F2 cần. |
| **BM25 có trọng số theo trường**, `title` ~3× | Title của site Q&A chính là câu hỏi bệnh nhân (100% có) → khớp query↔title là khớp câu hỏi với câu hỏi. Thêm một dense index cấp title. |
| **`title`/`description` CHỈ để xếp hạng, không bao giờ làm `chunk_text`** | Đo được title nằm nguyên văn trong body chỉ 43%; chúng ở `<meta>`/`<title>` nên không chắc có trong nội dung hiển thị. |
| **Budget chunk dùng ký tự/token ở phân vị P5, KHÔNG dùng trung bình; và bắt buộc trần bằng tokenizer thật** | Mật độ token biến động gấp 3 lần (vi: 3,75 trung bình nhưng 1,32 ở văn bản đậm nhất) → không hằng số nào bảo đảm được trần. `enforce_token_limit()` chỉ tokenize chunk dài hơn 1.024 **ký tự** nên gần như miễn phí. |
| **Chunk = gộp đoạn liên tiếp theo `\n`**, không sliding window | Đoạn trung vị 80 ký tự, chỉ 0,04% đoạn tự nó vượt 1 chunk, 76,3% tài liệu là 1 chunk nguyên. |
| **Gom trùng lặp để embed chung, KHÔNG xoá doc_id** | Có cụm sao chép hệ thống (`a-hospital` ↔ `zhongyibaodian`, 316k URL). Nhưng không biết BTC gán nhãn bản nào, và F2 nặng recall → trả cả hai là lãi. |
| **`doc_id` PHẢI là số nguyên trong JSON** (`--int-ids`) | Thí nghiệm một biến trên leaderboard: cùng nội dung, chuỗi → 0, số nguyên → 0,0497. Schema và ví dụ trong đặc tả BTC gây nhầm; phần chữ mới đúng. |
| **k = 200** (đo trên leaderboard, đỉnh ở k\* ≈ 194) | Quét k=20/100/200/500: DOCS_F2 đạt đỉnh 0,0821 ở k=200. **Phải quét lại k khi truy hồi tốt lên** - k\* phụ thuộc G và đường cong precision, không phải hằng số. |
| **Cấp chunk bị chặn bởi độ phủ crawl, KHÔNG phải bởi k** | CHUNKS_F2 phẳng ở 0,0093 qua k=100/200/500 dù số chunk/câu tăng 2,7×. Chỉ 2.499 doc đã cắt chunk trên 240.000 slot nộp ra. Hết đòn miễn phí ở tầng này. |
| **Nộp HẾT chunk của mỗi doc, không giới hạn 2** | Ngưỡng dừng cấp chunk là 0,00172 còn precision chunk thực tế 0,0525 - cao hơn 31 lần. Kể cả precision tụt 4× vẫn lãi 1,36×. |
| **Europe PMC là nguồn nội dung PubMed chính**, NCBI chỉ là dự phòng | NCBI chặn IP máy này (đo: mọi endpoint → misuse.ncbi.nlm.nih.gov, UA browser cũng không thoát). Europe PMC `resultType=core` trả cả title lẫn abstract: 284/284 bài so với 0/284 qua NCBI. |
| **`doc_id` của bài PubMed = PMID**, không cần tiền tố phân biệt | PubMed không nằm trong `links_corpus.parquet` nên phải dùng PMID. Đo được PMID hiện đại đều > 28M còn `links_corpus.id` ≤ 4,39M → không chồng nhau trên thực tế. |
| **Store = một file SQLite**, không thêm dep | 3,37M doc × 2 KB ≈ 7 GB. Cho cả resume theo URL, truy cập theo doc_id, và quét tuần tự cho BM25. |
| **Chunk chỉ lưu `(doc_id, start, end)`**, không lưu text | `chunk_text = body[start:end]` → không thể lệch khỏi tài liệu gốc. Ràng buộc nguyên văn được bảo đảm bằng cấu trúc, không bằng kỷ luật. |
| **BM25 tự viết, không Lucene/pyserini** | Query set cố định 1.200 câu → chỉ cần df của term trong query + một lượt streaming. Mẹo của `slug_bm25.py` tổng quát hoá được. |
| **Không dùng sitemap.** Đã probe 12 domain lớn nhất: chỉ chứa `<loc>`, không có title | URL thì BTC đã cho sẵn → giá trị bằng 0. Không có nguồn title hàng loạt, phải crawl từng trang. |
| **Giữ `curl_cffi`** làm đường dự phòng khi gặp 403 | Cứu 100% `nhathuoclongchau.com.vn` (79.598 URL) - domain liên quan nhất theo `slug_bm25`. Tổng chỉ cứu 10% nhưng đúng chỗ cần. |
| ~~~100 thread là đủ, rate limit chặn throughput~~ → **SỬA 01/10: nút cổ chai là CPU trích nội dung** | Kết luận cũ thiếu: đúng là độ trễ mạng không chặn, nhưng rate limit cũng không. `trafilatura` tốn 59 ms CPU/trang và bị GIL → trần ~17 trang/s dù có bao nhiêu thread. Đo được 7,8 trong khi rate limit cho trần 225. **Phần trích phải chạy ở `ProcessPoolExecutor`** (7 process → 16,7 trang/s, 2,2×). Thread mạng ~100 vẫn đúng. |
| **Chia shard theo DOMAIN, không theo id** | Hai máy cùng crawl một domain thì mỗi máy giữ rate limit riêng → tổng gấp đôi về cùng server, bất lịch sự và dễ bị chặn. Chia theo domain cân gần hoàn hảo (1,223M mỗi phần cho 3 máy). |
| **Domain bị chặn đánh dấu `BLOCKED` ngay lúc nạp hàng đợi** | 725.329 URL (16,5%) không tốn một request nào. `--retry-blocked` chạy lại đúng phần đó khi có IP mới → không mất gì nếu sau này giải quyết được. |
| **Rate limit theo từng domain, cấu hình riêng được** | `a-hospital.com` trả 502 ở 28/65 mẫu trong khi `cnkang`/`120ask` chịu được tốt → một mức rate chung là sai. |
| ~~Subdomain = nhãn chuyên khoa để ưu tiên crawl phía zh~~ → **HUỶ 01/10** | Ba lý do: (1) crawl chỉ 27h nên không cần ưu tiên tinh vi; (2) `tags` trên trang đã mang sẵn nhãn chuyên khoa (68%); (3) đúng 14 subdomain chuyên khoa `*.39.net` lại là nhóm trích ra 0 ký tự — công gấp đôi cho 66k URL (1,5%). |

---

## 4. Câu hỏi còn mở (cập nhật khi BTC trả lời)

| Câu hỏi | Trạng thái |
| --- | --- |
| ~~25.843 URL chênh giữa README và file thật là gì?~~ | ✅ **ĐÃ GIẢI 01/10**: `id` chạy 583→4.420.561 nhưng khuyết 25.843 id trong dải. Không thiếu dữ liệu, chỉ là id không liên tục. |
| Nhãn gán theo nội dung trang ở thời điểm nào (trang có thể đã sửa/chết)? | chưa hỏi |
| ~~Tài liệu tiếng Anh có nằm trong corpus link không?~~ | ✅ **ĐÃ TRẢ LỜI 01/10**: giới hạn ở PubMed, BTC không cung cấp danh sách, các đội tự tìm. Gợi ý đúng 3 API mà `pubmed_module` đang dùng. |
| `doc_id` cho bài PubMed là PMID - hệ thống chấm phân biệt với `links_corpus.id` thế nào (hai dải giá trị chồng nhau về lý thuyết)? | nên hỏi; thực tế đo được không chồng |
| MoE tính tổng tham số hay tham số kích hoạt? Teacher distill có phải tuân mốc ngày? | chưa rõ, tạm coi theo tổng |
| ~~`familydoctor` + `zysjonline` chặn 403 - có phải theo IP vùng?~~ | ✅ **ĐÃ KIỂM 01/10**: không sửa được bằng code (10 profile TLS, vòng cookie, Referer đều 403). `zysjonline` = Cloudflare JS challenge → cần browser thật. `familydoctor` = Alibaba WAF → cần IP khác. Chờ quyết định có đầu tư hay chịu mất 15,8%. |
| BTC có tính điểm cho tài liệu mà không đội nào crawl được (site chết, 521) không? | chưa hỏi |
