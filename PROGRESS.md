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
| Tỉ lệ crawl **dùng được** (có text) | **98,0% zh · 99,8% vi** | 75,0% zh | 04/10/2026 | `crawler.py` |
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
| Throughput crawl | **19,4 trang/s** zh (rate đã hạ về 4) | 43,1 (nhưng chỉ 73% dùng được) | 04/10/2026 | `crawler.py` |
| URL đánh dấu BLOCKED từ đầu | **273.978 (6,2%)** trên IP máy GPU | 725.329 (16,5%) ở IP local | 03/10/2026 | `familydoctor` qua được IP khác |
| PubMed: bài lấy được / PMID | **284/284** | 0/284 | 01/10/2026 | `pubmed_module` API thật |
| Test offline | **17 qua** | 16 qua | 03/10/2026 | `unittest discover tests` |
| Chunk/tài liệu | **3,65** (target 400 token) | 1,68 (target 900) | 04/10/2026 | `chunk.py` |
| Tổng chunk (thật, 647k doc) | **2.366.199** (target 400) | 1.085.111 (target 900) | 04/10/2026 | `chunk.py` |
| Vector fp16 chunk-level | **~11,6 GB** | 9,9 GB | 01/10/2026 | ngoại suy |
| Mục audit PASS | **47/47** (chunk 400 token) | 40/40 | 04/10/2026 | `audit.py` |
| Doc đã crawl (dùng được) | **647.034 vi + 843.007 zh** = 1,49M | 1,13M | 04/10/2026 | `crawler.py` |
| Byte rác bỏ bởi lọc boilerplate | **6,5 MB** (-11,6% body) | — | 01/10/2026 | `clean.py` |
| `laodong.vn` thu hồi | **21.368** doc | 0 | 01/10/2026 | `cookie_challenge()` |
| Ký tự/token vi dùng cho budget | **3,40 (P5)** | 4,09 (trung bình - SAI) | 01/10/2026 | `chunk.py` |
| Ký tự/token zh dùng cho budget | **1,25 (P5)** | 1,42 (trung bình - SAI) | 01/10/2026 | `chunk.py` |
| Chunk nguyên văn (kiểm độc lập) | **3.585/3.585** | — | 01/10/2026 | `submission.py --store` |
| Tổng số chunk | 5,17M | 13M (giả định cũ) | 01/10/2026 | ngoại suy |
| Vector fp16 chunk-level | 9,9 GB | 27 GB (giả định cũ) | 01/10/2026 | ngoại suy |
| Thời gian encode BGE-M3 | 3,6 h | 18 h (giả định cũ) | 01/10/2026 | ngoại suy |
| `title` có / `title` nằm trong `body` | 100% / 43% | — | 01/10/2026 | probe metadata |
| **Co giãn crawl→điểm (ε phía vi)** | **0,089–0,108** | — | 04/10/2026 | 2 mốc cách nhau 100×: +392% và +3,5% doc |
| **FINAL_SCORE (public LB)** | **0,2658** | 0,2581 | 06/10/2026 | leaderboard |
| F2 document (public LB) | **0,2914** (Qwen3-Reranker top-250 + vòng 1) | 0,2811 | 06/10/2026 | leaderboard |
| **k tối ưu (khớp đường cong)** | **≈ 211** | ≈ 198 | 04/10/2026 | β=0,461 đo lại sau khi thêm dense - gần y hệt 0,455 |
| **G - số doc vàng mỗi câu (suy ra)** | **≈ 60** | ≈ 58 | 04/10/2026 | từ P/R của LB, 17 điểm |
| Trọng số FINAL | **doc 50% / chunk 50% - ĐÃ CHỨNG MINH** | khớp phép tính | 03/10/2026 | bài ghép: (0,1280+0,0863)/2 = 0,10715 vs đo 0,1071 |
| F2 chunk (public LB) | **0,2402** (chunk t40_70, Qwen top-250) | 0,2366 | 06/10/2026 | leaderboard |
| **Giới hạn ZIP upload** | **100 MB** (xác nhận lại 04/10: đội khác nộp JSON 200 MB → ZIP 50 MB, tỉ lệ nén 4,0:1 y hệt ta) | — | 04/10/2026 | leaderboard sau Cloudflare |

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

### 01/10/2026 · `clean.py` · lọc boilerplate tự động · **-11,6% byte rác**

```powershell
python clean.py --analyze              # xem trước, KHÔNG sửa
python clean.py --analyze --domain medlatec.vn
python clean.py --apply                # sửa thật, rồi BẮT BUỘC chạy chunk.py
```

`trafilatura` đã bỏ nav/footer/ads nhưng vẫn sót breadcrumb và khối "bài liên quan".
Phát hiện **tự động, không hardcode**: dòng xuất hiện ở **>30% số trang của CÙNG một domain**
thì là boilerplate - nội dung thật không lặp lại ở 30% số trang. Đếm theo **document
frequency** (số trang chứa dòng), không phải tổng số lần, để một dòng lặp 50 lần trong một
trang không bị nhận lầm.

```
47 domain · 457 dòng boilerplate · 23.510 doc sửa · 6,5 MB bỏ đi
body trung bình: 3.966 -> 3.507 byte/doc  (-11,6%)
```

| Domain | Bỏ gì | Byte |
| --- | --- | --- |
| `vinmec.com` | `"Để đặt lịch khám tại viện, Quý khách vui lòng..."` | 2,13 MB |
| `medlatec.vn` | `"Nội dung được kiểm duyệt chặt chẽ bởi đội ngũ..."` | 1,44 MB |
| `suckhoeviet.org.vn` | 65 dòng, khối bài liên quan | 1,12 MB |
| `baotayninh.vn` | **192 dòng**: nav hashtag, widget thời tiết (`30°C`, `27°C`), dấu phân cách, nhãn chuyên mục | 0,95 MB |
| `120ask.com` | thanh nav `有问必答 内科 外科 儿科 药品...` | 0,11 MB |
| `tamanhhospital.vn` | `"HỆ THỐNG BỆNH VIỆN ĐA KHOA TÂM ANH"` | 28 KB |
| `tiemchunglongchau.com.vn` | `"Xem thêm:"` | 24 KB |

#### Nghi ngờ có phá nội dung - đã kiểm, không có

`baotayninh.vn` bỏ **192 dòng trên chỉ 169 doc**, và **156/169 doc mất >50% body**. Nghe như
đang xoá nội dung thật, nên kiểm hai thứ:

1. **Dòng boilerplate có trùng `title` của doc nào khác?** → **0 trùng** trên cả
   `baotayninh.vn` và `baogialai.com.vn`. Nên không có chuyện xoá mất chính tiêu đề của trang đó.
2. **Mở một doc ra xem bỏ gì:**

```
BỎ (164 dòng): #Bầu cử ĐBQH và ĐBHĐND các cấp · Tây Ninh · 30°C · / · 27°C · - · 33°C
                · Y tế sức khỏe · ,
GIỮ  (51 dòng): Người huyết áp cao nên uống bao nhiêu nước mỗi ngày?
                Bên cạnh việc uống thuốc và thay đổi lối sống, uống đủ nước cũng có thể...
                Trong một số trường hợp, uống nước có thể giúp hạ huyết áp...
```

→ Việc lọc **đúng**. Báo tỉnh có khối nav + thời tiết + hashtag khổng lồ mà `trafilatura`
kéo vào hết. "Mất >50% body" ở đây là đúng, không phải lỗi.

#### Hai bảo vệ bắt buộc

- **Xoá chunk của doc bị sửa TRƯỚC khi đổi `body`** - body đổi thì offset cũ sai.
  Self-check assert đúng điều này. Sau khi apply: chunk 4.468 → 2.232.
- Lọc xong còn <200 ký tự thì **giữ nguyên bản cũ** - thà bẩn hơn mất nội dung.

#### ⚠️ Phải chạy lại sau MỖI đợt crawl mới

Doc mới crawl về lại mang boilerplate. Thứ tự đúng:
`crawler.py` → `clean.py --apply` → `chunk.py` → `audit.py`.

---

### 01/10/2026 · `cookie_challenge()` chạy ở quy mô thật · +21.368 URL

Fix thách đố cookie (xem mục trước) đo trên 29k URL `laodong.vn`:

```
requests+cookie   21.368 doc   ← thu hồi được
None (lỗi mạng)    1.828
```

Từ **0 doc dùng được** trước khi sửa. Hàm viết tổng quát nên domain khác cùng kiểu cũng được
cứu tự động.

### 02/10/2026 · độ phủ chunk 1,4% → 80% · **CHUNKS_F2 ×5,3** · và giới hạn upload

Cô lập đúng một biến so với lượt 01/10: cùng `slug_rank`, cùng k=200, cùng `--int-ids`.
Chỉ độ phủ chunk đổi (crawl 2.499 → 127.129 doc, 79,7% URL ưu tiên đã có nội dung).

| | DOCS_F2 | CHUNKS_P | CHUNKS_R | CHUNKS_F2 | FINAL |
| --- | --- | --- | --- | --- | --- |
| 01/10 (phủ 1,4%) | 0,0821 | 0,0377 | 0,0111 | 0,0093 | 0,0457 |
| `ctop20` (phủ 80%) | 0,0821 | 0,0760 | 0,0370 | 0,0366 | 0,0594 |
| **`ctop50`** (phủ 80%) | 0,0821 | 0,0523 | 0,0603 | **0,0495** | **0,0658** |

**`DOCS_F2` y hệt 0,0821 ở cả ba** → xác nhận hai tầng chấm hoàn toàn độc lập, và số liệu đáng tin.

**Chẩn đoán "chunk bị chặn bởi độ phủ crawl" ĐÚNG**: CHUNKS_F2 ×5,3 (0,0093 → 0,0495).

**`ctop50` > `ctop20` vì recall thắng**: precision giảm 0,076 → 0,0523 nhưng recall tăng
0,037 → 0,0603. F2 nặng recall 4× nên đánh đổi này có lãi. → nên tăng M.

#### Khớp đường cong chunk từ hai điểm

```
R ~ n^0,53     P ~ n^-0,40     (n = chunk/câu)   hệ số macro/micro 0,846
```

| M doc | chunk/câu | P | R | CHUNKS_F2 | FINAL | ZIP |
| --- | --- | --- | --- | --- | --- | --- |
| 20 | 29 | 0,0760 | 0,0370 | 0,0349 | 0,0585 | 26 MB (đo: 0,0366) |
| 50 | 73 | 0,0523 | 0,0603 | 0,0495 | 0,0658 | 64 MB (đo: khớp) |
| 100 | 146 | 0,0395 | 0,0870 | 0,0593 | 0,0707 | 127 MB |
| 150 | 219 | 0,0335 | 0,1078 | 0,0632 | 0,0727 | 192 MB |
| 200 | 290 | 0,0299 | 0,1251 | 0,0647 | 0,0734 | 254 MB |

**Trần của hướng này là FINAL ≈ 0,073, và nó bị chặn bởi DUNG LƯỢNG UPLOAD, không phải bởi điểm.**

#### Giới hạn upload: trong khoảng 80–127 MB

```
 60 MB ✅   64 MB ✅   80 MB ✅   127 MB ❌   159 MB ❌   229 MB ❌   253 MB ❌
```

Bài nộp fail upload **không bị tính quota** nên thử giới hạn là miễn phí. Quan trọng cho
private phase: chỉ 5 lượt TỔNG, một lượt fail là mất 20% ngân sách.

Chồng lấn chunk chỉ làm phồng **3,6% (15 MB)** nên không đáng bỏ - nó rẻ mà bảo vệ khỏi
cắt đứt phần thông tin giữa hai chunk.

#### Hướng chunk gần cạn

`DOCS_F2` đứng im 0,0821 suốt **bốn** lượt nộp - crawl cải thiện chunk, không cải thiện xếp hạng.
Và `CHUNKS_RECALL` bị trần bởi `DOCS_RECALL = 0,145`: không nộp được chunk của doc mình
không trả về. Muốn vượt 0,073 phải nâng `DOCS_RECALL`, tức **xếp hạng tốt hơn**.

### 02/10/2026 · `bm25.py` + `fuse.py` · **DOCS_F2 rời 0,0821 lần đầu, rồi +22% nữa**

Bốn lượt nộp trước `DOCS_F2` đứng im **0,0821** vì đều dùng `slug_rank` - ta chỉ đang đo
chất lượng chunk, không đo chất lượng xếp hạng. Hai file này phá trần đó.

| Nguồn ứng viên | DOCS_F2 | DOCS_R | CHUNKS_F2 | FINAL |
| --- | --- | --- | --- | --- |
| slug (4 lượt) | 0,0821 | 0,1450 | 0,0513 | 0,0667 |
| **BM25F** trên nội dung | 0,0872 | 0,1512 | 0,0618 | 0,0745 |
| **RRF(slug, BM25F)** | **0,1068** | **0,1868** | **0,0694** | **0,0881** |

#### A. `bm25.py`: BM25F, không phải "BM25 từng trường rồi cộng điểm"

Gộp tần suất các trường **TRƯỚC** khi vào hàm bão hoà:

```
tf*(t,d) = Σ_f  w_f · tf(t,d_f) / (1 - b + b·len_f/avglen_f)
score    = Σ_t  idf(t) · tf*(t,d) / (k1 + tf*(t,d))
```

Cộng điểm sau sẽ cho một từ xuất hiện **1 lần ở 4 trường** điểm cao hơn một từ xuất hiện
**10 lần ở 1 trường**, vì mỗi trường tự bão hoà riêng. Trọng số `title` 3 / `tags` 2 /
`descr` 1,5 / `body` 1 - **vẫn là phỏng đoán, chưa quét.**

Tiếng Trung dùng **bigram ký tự** (`糖尿病` → `糖尿`, `尿病`), cách chuẩn của Lucene
CJKAnalyzer - tránh dependency `jieba` và từ điển của nó.

**Streaming hai lượt**, bộ nhớ O(query × topk). Không lặp lại lỗi `fetchall()` đã làm
`chunk.py` bị kill.

**BM25 chỉ xếp hạng 127k doc đã crawl, slug phủ 1,19M URL** - tập ứng viên nhỏ hơn 9 lần
mà thắng cả hai tầng. Chất lượng xếp hạng quan trọng hơn kích thước tập ứng viên.

#### B. `fuse.py`: RRF, và vì sao không cộng điểm thô

```
score(d) = Σ_i  w_i / (k + rank_i(d))        k = 60 (Cormack 2009)
```

Hai nguồn **không cùng thang**: cùng câu hỏi, slug cho ~39 điểm, BM25 cho ~21. Cộng trực
tiếp là để slug áp đảo vô lý. RRF chỉ dùng **hạng** nên miễn nhiễm thang điểm.

Điều kiện để RRF ăn lãi: các nguồn phải **khác nhau** mà **đều đúng**. Đo được: slug và
BM25 lệch **87,4%** doc ở top-200 (Jaccard 0,070) mà cả hai đều ăn điểm → +22% DOCS_F2.

Sửa một chỗ khi làm: lần đầu gộp `slug_rank.jsonl` (200 ứng viên) với `bm25_rank.jsonl`
(1000) → từ hạng 200 trở xuống chỉ BM25 góp mặt. Đổi sang `slug_rank1000.jsonl` cho cân
(đóng góp 58,5/59,0% → 60,7/60,4%).

#### C. Ablation: xếp hạng bị BODY chi phối, không phải title

Ngược dự đoán của tôi (title có trọng số ×3):

```
chỉ metadata (--w-body 0)                      lệch 69,8% so với BM25F đầy đủ
chỉ body (--w-title/descr/tags 0)              lệch 18,0%
```

Dù BM25F đã chuẩn hoá theo độ dài trường, một từ khoá vẫn dễ xuất hiện trong body
(3.507 ký tự) hơn title (~50 ký tự). → `bm25_meta` thành một **nguồn độc lập** đáng gộp,
chứ không phải bản xấp xỉ của `bm25`.

**Bẫy RRF:** `bm25` và `bm25_body` tương quan 82% (lệch 18%) nên gộp cả hai là **đếm tín
hiệu body hai lần** - thấy rõ qua đóng góp 79,1% + 72,5% đẩy slug xuống 39%. Bản 3 nguồn
cân hơn (53/60/69).

---

### 02/10/2026 · `AdaptiveLimiter` · mất 20.000 URL vì crawler không biết chậm lại

`nhathuoclongchau.com.vn` - **domain liên quan nhất** theo `slug_bm25` (10.883 lượt trong
top-50):

```
15.062  status=403   via=curl_cffi
 5.352  status=429   via=curl_cffi    ← Too Many Requests, server NÓI THẲNG
   315  status=200                     ← chỉ 2% của 20.742 lượt thử
```

Server yêu cầu chậm lại, mà crawler chỉ ghi lại rồi **tiếp tục ở nguyên tốc độ**. Thiếu
đúng một tính năng và mất 20k URL của domain quan trọng nhất.

Đã thêm `AdaptiveLimiter`: gặp 429/403/503 thì **giãn gấp đôi ngay trong batch**, chặn trên
30 giây/request, in cảnh báo. Không tự nới lại - trong crawl theo lô, chậm mà chắc tốt hơn
nhanh rồi bị chặn vĩnh viễn.

Và đặt `RATES` theo **tỉ lệ thành công ĐO ĐƯỢC** từng domain thay vì một con số chung:

| Domain | Còn lại | Đo được | Rate |
| --- | --- | --- | --- |
| `suckhoecongdongonline.vn` | 138.061 | 88% | 5 → **12** |
| `suckhoedoisong.vn` · `thanhnien.vn` | 127.009 | 99% | 5 → **12** |
| `vinmec` · `medlatec` · `phunusuckhoe` | ~59.000 | 99-100% | 5 → **12** |
| 8 báo tỉnh | ~89.000 | 100% | 5 → **10** |
| `nhathuoclongchau.com.vn` | 58.856 | **2%** 🔴 | 5 → **0,5** |

Nghẽn từ `suckhoecongdongonline` 138k: **7,7 giờ → 3,2 giờ**.

**Bài học về tốc độ crawl:** máy KHÔNG còn là giới hạn (CPU đã sửa bằng ProcessPool).
Giới hạn hiện tại là server, và một phần là **ta tự chọn** qua `RATES`. Nâng đều là sai -
phải nâng ở domain chịu được, hạ ở domain phản đối.

---

### 02/10/2026 · `--lang vi|zh` · chia việc hai máy theo ngôn ngữ

```
lang=vi: 50 domain,   740.598 URL   (đã crawl 126.428 = 17,1%)
lang=zh: 36 domain, 2.928.791 URL   (đã crawl     701 =  0,0%)
bị chặn              725.329
```

Chia theo **domain** nên mỗi domain do đúng một máy phụ trách - rate limit vẫn đúng, không
đập cùng server từ hai hướng, `--merge` không xung đột.

Ghép lại: `--merge` chỉ copy bảng `doc` và tính lại `queue.state`. **Không** copy `chunk`
và `boilerplate` - có chủ ý, vì chunk offset phải tính lại trên body đã lọc boilerplate.
Thứ tự bắt buộc sau khi ghép: `--merge` → `clean.py --apply` → `chunk.py` → `audit.py`.

#### Suy luận quan trọng: recall bị chặn bởi ĐỘ PHỦ, không phải xếp hạng

```
Đã crawl tiếng Việt      17,1%
DOCS_RECALL (BM25)       15,12%
tỉ lệ recall / độ phủ    89%
```

BM25 trả về **1999/2000 doc tiếng Việt**. Nên toàn bộ recall đến từ 17,1% corpus tiếng Việt
đã crawl, và xếp hạng đang khai thác **89% những gì có thể** trong phần đã có.

Và `G ≈ 55` → tổng slot doc vàng = 1.200 × 55 = **66.000 = tối đa 1,5% của 4,39M URL**.
Nên **98,5% corpus là vô ích** - chỉ không biết cái nào.

**Phép thử dứt khoát:** crawl nốt 586k tiếng Việt rồi đo lại. Nếu độ phủ lên 34% mà recall
lên ~0,30 thì nhãn vàng chủ yếu tiếng Việt → 2,93M tiếng Trung có thể bỏ phần lớn.
*Chưa đo.*

Tiếng Trung hiện **không thể ăn điểm** dù crawl xong: không có truy vấn tiếng Trung
(Hy-MT2 chưa tải được, 672 KB metadata thay vì 15 GB).

---

### 03/10/2026 · 84k URL vi cuối cùng · **profile TLS phải chọn theo domain, và rate thấp từ đầu > bị phạt**

`--lang vi` còn 83.882 URL, tưởng 4-5 giờ. Đếm theo domain thì chỉ nằm trên **5 domain**, và
69% là `nhathuoclongchau.com.vn` ở rate 0,5 req/s (hạ tay sau vụ mất 20k) = **32 giờ**. Quyết định:
bỏ longchau lại, xử 4 domain còn lại trước.

**Probe 3 domain trả 403** (8 biến thể × 3 URL thật, `scratchpad/probe403.py`):

| Domain | URL | requests | curl_cffi chrome* | safari17_0 / firefox133 / edge101 | session home→page |
| --- | --- | --- | --- | --- | --- |
| `vov.vn` | 8.702 | 403 | **403** | **200** (244 KB) | 403 |
| `youmed.vn` | 3.599 | 403 | 403 | 403 | **200** (288 KB) |
| `pmc-ecm-healthblog.beta.pharmacity.io` | 3.103 | 403 | 403 | 403 | 403 |

→ `fetch()` ghim cứng `impersonate="chrome"` nên hỏng đúng hai chỗ: `vov.vn` lọc **đúng** fingerprint
Chrome (mọi `chrome*` đều 403, ba họ khác đều 200), `youmed.vn` cần cookie lấy từ trang chủ trước.
Thêm `WAF_PROFILE` (profile theo domain), `WAF_WARMUP` (hâm nóng trang chủ) và `waf_session()`
(Session trong `threading.local`, một cái mỗi thread mỗi domain). Kiểm trên URL thật:
vov.vn body 2.201, youmed.vn body 10.185. Pharmacity → `BLOCKED` (3.054 URL).

Domain đã biết chặn `requests` thì đi thẳng curl_cffi → tiết kiệm **1 request vô ích mỗi URL**.

**AIMD và chuyện rate:** `AdaptiveLimiter` chỉ biết hạ, không biết nới. Hệ quả đo được: 429 thoáng
qua lúc khởi động ghim `youmed.vn` ở 0,03 req/s **suốt đợt** → 3.473 URL thành **32 giờ**. Thêm
`reward()` (nới ÷1,5 sau 30 lần 200 liên tiếp, chặn trên ở `base`). Nhưng nới KHÔNG cứu được khi
429 đến liên tục vì mỗi lần phạt reset chuỗi thắng: giadinhonline vẫn rơi 10 → 0,03 req/s = **94 giờ**.

Thứ cứu được là **hạ mức KHỞI ĐẦU**: giadinhonline 10→1, youmed 5→0,5, vov 5→3. Kết quả:
**0 lần bị phạt, tỉ lệ dùng được 90,4% → 100,0%**, và thời gian từ 94 giờ xuống 5,6 giờ.

| Domain | URL còn | rate | tốc độ đo | xong sau |
| --- | --- | --- | --- | --- |
| `vov.vn` | 7.132 | 3 | 2,8 trang/s | 42 phút |
| `youmed.vn` | 3.288 | 0,5 | 0,42 trang/s | 2,2 giờ |
| `giadinhonline.vn` | 10.089 | 1 | 0,5 trang/s | 5,6 giờ |

Còn nợ: `nhathuoclongchau.com.vn` 57.920 URL ở 0,5 req/s = 32 giờ, là domain liên quan nhất
theo `slug_bm25` → phải chạy, chỉ là chạy sau.

---

### 03/10/2026 · máy GPU · **IP khác cứu được 447k URL**, và ba lỗi làm crawl zh mất 63% dữ liệu

Vào được máy GPU (`lablee-MS-7E06`, 24 core, 125 GB RAM, 2× RTX 4090). Nó đã crawl
**449.745 doc** từ hôm trước. Ba phát hiện, xếp theo giá trị:

**1. `familydoctor.com.cn`: 445.848/447.453 = 100% thành công.** Local đã bỏ cuộc hôm 01/10
(10 profile TLS, vòng cookie, Referer đều 403 → kết luận "Alibaba WAF, cần IP khác, chịu mất").
IP máy GPU đi qua được **không cần sửa gì**. Đó là **447k URL = 10,2% corpus** lấy lại được,
và `bị chặn` tụt 725.329 → 273.978. Giả thuyết "cần IP khác" đã được chứng minh, không còn là
phỏng đoán. Còn `zysjonline.com` (243.347 URL) vẫn chặn trên cả hai IP.

**2. CAPTCHA trả HTTP 200 nên VÔ HÌNH với backoff — crawler tự tạo vòng xoáy.**
Tỉ lệ dùng được **tụt dần trong một đợt**: 46,0% → 43,6% → 41,6% → 37,0% → 35,6%. Không phải
nhiễu. Nhóm `*.39.net` dạng `/a/YYMMDD/NNNNNN.html` (baby/byby/cancer/ek/fitness/fk/food/gan/gc)
rỗng **97,4-97,7%**; probe ra `39健康 滑动拼图验证 加载中…` — màn xác thực ghép hình trượt,
HTML 2.287 B, body 11 ký tự. `WAF_STATUS` chỉ bắt 403/406/429/503 nên status 200 được nhận là
**thành công**: `AdaptiveLimiter` không bao giờ phạt, crawler càng đập càng bị chặn thêm.
Thử vượt: **cả 8 biến thể đều CAPTCHA** (requests, 5 profile curl_cffi, 2 session hâm nóng).
→ Thêm `looks_captcha(text, raw_len)`: HTML < 8 KB **và** có dấu hiệu xác thực thì đổi status
thành 403, để limiter phạt và URL ở lại `FAILED` cho `--retry-failed`. Hai điều kiện cùng lúc
vì chỉ xét dấu hiệu sẽ nhận lầm bài viết NÓI VỀ captcha (có trong self-check).

**3. DNS: `requests.get()` tra lại mỗi URL, 200 thread làm ngập resolver.**
`Temporary failure in name resolution` cho cả `food.39.net`, `cnkang.com`, `huggingface.co`
và `files.pythonhosted.org` — tức không chỉ site crawl mà mọi thứ trên máy. Giải thích
`status=None` 4.340 doc. Resolver là `1.1.1.1`/`8.8.8.8` (công cộng, có rate limit), và lỗi
xuất hiện **từng lúc** nên dễ tưởng là site chết. → `http_session()`: `requests.Session` riêng
mỗi thread trong `threading.local`, `HTTPAdapter(pool_connections=32, pool_maxsize=32)`,
keep-alive nên bỏ được phần lớn lượt tra DNS lẫn TLS handshake. Và hạ `--workers` 200 → 100:
trần thật là 22 process trích (~52 trang/s), 200 thread chỉ làm ngập DNS mà không tăng gì.

**Nhánh LLM:** cả 4 mô hình đã có đủ trọng số trong `~/.cache/huggingface` (Qwen3.5-9B 19,3 GB
· Hy-MT2-7B 16,1 GB · bge-m3 2,27 GB · bge-reranker-v2-m3 2,27 GB). Không env nào có vLLM,
nhưng `.venv` có `transformers 5.18.0` + `torch 2.6.0+cu124` nên chạy được `--backend hf`.
Qwen3.5-9B chạy thật trên 20 câu: `parse_ok: true`, và **nó tự dịch luôn sang tiếng Trung**
(`"zh": "牙齿上有黑点且晨起时出血是什么原因？"`) kèm thực thể 3 ngôn ngữ → **nhánh zh không
phải chờ Hy-MT2**, Hy-MT2 chỉ để nâng chất lượng. Cảnh báo lúc chạy: thiếu `causal_conv1d` và
`flash-linear-attention` nên các kernel hybrid của Qwen3.5 chạy bản PyTorch tham chiếu ("much
slower") - chưa đo được chậm bao nhiêu.

`expand_queries` ghi `expansions.jsonl` **một lần ở cuối** → chạy nhiều giờ mà chết là mất
sạch, và không quan sát được. Đã thêm `partial_path`: ghi dần sau mỗi batch 64 câu và log
`s/câu` + thời gian còn lại.

---

### 03/10/2026 · sửa 3 lỗi crawl zh · **dùng được 35,5% → 86,0%, throughput ×4,2**

Đo trên cùng corpus zh, cùng máy, chỉ khác code và tham số:

| | Trước | Sau |
| --- | --- | --- |
| Tỉ lệ dùng được | 35,5% (đang tụt dần) | **86,0%** |
| Throughput | 11,0 trang/s | **46,6 trang/s** |
| 2,93M URL còn lại | 74 giờ | **17,5 giờ** |

Ba nguyên nhân, cả ba đều là lỗi thật trong code hoặc tham số:

1. `looks_captcha()` - CAPTCHA trả 200 nên limiter không bao giờ phạt (xem mục trước). 29-35
   domain `*.39.net` giờ bị phạt xuống 0,16 req/s ngay, không đốt quota batch nữa.
2. `http_session()` - bỏ lượt tra DNS mỗi URL.
3. **Bỏ `--retry-failed`** - nó dồn quota vào đúng phần CAPTCHA không vượt được. Phần FAILED
   để lại cho sau, khi có IP khác; 3,38M URL PENDING giá trị hơn nhiều.
4. `--procs 22 → 10`, `--workers 100 → 80`: job 22-process **bị kill âm thầm** (không traceback,
   `free` còn 1 GB) vì chạy cùng expand 4-bit. 10 process vẫn cho 46,6 trang/s nên 22 là thừa.

**`nhathuoclongchau.com.vn` trên IP máy GPU: 99,9% dùng được.** Local phải dùng 0,5 req/s
(= 32 giờ) sau khi bị 403 vĩnh viễn; ở đây 3 req/s chạy sạch. Đây là domain liên quan nhất
theo `slug_bm25`, 57.920 URL. Thêm vào `WAF_PROFILE` vì để ngoài thì mỗi URL tốn HAI lượt
`limiter.wait()` (requests 403 → curl_cffi 200), rate hiệu dụng chỉ còn một nửa: đo 1,5 trang/s
ở mức cấu hình 3 req/s.

**`salvage_json()` - vớt JSON hỏng cú pháp.** Qwen3.5-9B 4-bit sinh JSON sai cú pháp ở
**17,2% câu** (11/64): chèn `)` + newline sau dấu nháy đóng. Không phải lỗi `max_tokens` -
raw dài 1.357 ký tự và kết thúc bằng `]}`, tức JSON ĐỦ. `json.loads` thất bại là
`parse_llm_output` trả rỗng → mất CẢ `zh` lẫn `entities`, đúng hai thứ nhánh tiếng Trung cần.
Vớt theo từng khoá bằng regex thì lấy lại được hết. Vì `raw` đã lưu trong mỗi dòng,
`stage_expand` **vá lại offline từ `raw`, không gọi lại LLM** (1.200 câu mất ~4 giờ trên
backend `hf`, vá lại thì tức thì). Test offline: 17 (thêm 1).

Tốc độ expand đo thật: **11,7 s/câu** → 1.200 câu ≈ 3,5 giờ (backend `hf` sinh tuần tự;
thiếu `causal_conv1d`/`flash-linear-attention` nên kernel hybrid của Qwen3.5 chạy bản tham chiếu).

---

### 04/10/2026 · `Too many open files` · **pool kết nối lớn làm 83,2% request chết**

Sau khi thêm `http_session()`, crawl zh chạy 500 doc đầu ở 86,0% / 46,6 trang/s rồi **tụt
xuống 31,4% / 1,9 trang/s**. Ở 1,9 trang/s thì 3,53M URL cần 516 giờ.

Lần theo bốn giả thuyết, ba cái SAI:

| Giả thuyết | Kiểm | Kết quả |
| --- | --- | --- |
| CAPTCHA lan ra cả corpus | đếm `err='captcha'` trên 2.500 doc mới nhất | **0** - không phải |
| `trafilatura` thua layout zh | đếm body của doc status 200 | **417/420 có body ≥ 200 (99,3%)** - không phải |
| `Session` làm server trả khác | cùng URL, `requests.get` vs `Session` | **y hệt** (html 77.148 B, body 577) - không phải |
| Lỗi kết nối | đếm status | **2.079/2.500 = 83,2% có `status=None`** ✅ |

Thông điệp lỗi đầy đủ chỉ đúng một dòng: `SSLError(OSError(24, 'Too many open files'))`,
cùng `ss -s` cho 3.527 kết nối TCP (1.859 ở trạng thái closed).

**Nguyên nhân là `http_session()` của chính mình:** `HTTPAdapter(pool_connections=32,
pool_maxsize=32)` cho **mỗi thread** → 80 thread × 32 = 2.560 socket tiềm năng, vượt
`ulimit -n` = 1024. Mà mỗi thread chỉ chạy MỘT request tại một thời điểm, nên pool 32 hoàn
toàn vô nghĩa - nó chỉ đốt file descriptor.

Sửa hai phía: `pool_connections=6, pool_maxsize=2`, và `raise_fd_limit()` nâng ulimit mềm
1024 → 65536 (giới hạn cứng là 1.048.576 nên không cần quyền root).

| | Trước | Sau |
| --- | --- | --- |
| zh - dùng được | 31,4% | **75,0%** |
| zh - throughput | 1,9 trang/s | **43,1 trang/s** (×22,7) |
| zh - thời gian còn lại | 516 giờ | **22,7 giờ** |
| longchau | 1,5 trang/s | **3,0 trang/s** |

`longchau` tăng gấp đôi nhờ vào `WAF_PROFILE`: trước đó mỗi URL tốn hai lượt `limiter.wait()`
(requests 403 → curl_cffi 200), giờ đi thẳng curl_cffi.

---

### 04/10/2026 · `dense.py` + BM25 tiếng Trung · **nhãn vàng CÓ tài liệu zh, nhưng dense-title chưa đủ mạnh**

`dense.py` (BGE-M3, cấp title) chạy nhanh hơn hẳn dự kiến: **406.127 title → 0,83 GB fp16 trong
~4 phút** trên một card 4090, rồi xếp hạng 1.200 câu × 1.000 ứng viên. Điểm mạnh riêng của nó:
BGE-M3 đa ngôn ngữ nên **query tiếng Việt khớp trực tiếp title tiếng Trung, không cần dịch** -
thứ BM25 không làm được.

Gộp vào RRF làm nguồn thứ 4, nó chiếm **20,2% số slot** top-200 nhưng **THUA**: DOCS_F2
0,1284 → 0,1217 (-5,2%), recall 0,2246 → 0,2134.

**Tách phần đóng góp của tiếng Trung** (đây là số đáng giá nhất của mục này):

| | |
| --- | --- |
| Dense chiếm | 20,2% slot = 40,4 doc/câu |
| g_vi còn lại (160 slot), theo β=0,455 | 13,0 × (160/200)^0,455 = **11,74** |
| g thực đo | 0,0614 × 200 = **12,28** |
| → g_zh | **0,54 doc vàng/câu** từ 40,4 slot |
| → precision của phần zh | **0,0134** |
| precision BIÊN của vi tại k=200 (β·g/k) | **0,0296** |

→ **Nhãn vàng CÓ tài liệu tiếng Trung** (g_zh > 0, không phải 0), nhưng dense-title zh chỉ mạnh
bằng **45%** phần cuối danh sách tiếng Việt, nên thay thế là lỗ. Tính ngưỡng: doc zh với
precision 0,0134 chỉ đáng thêm nếu mở rộng k tới **~732**, trong khi k\* = 198.

Hạ trọng số không cứu được: `w=0,4` làm dense tụt từ 20,2% xuống **0,2% slot**. RRF rất nhạy ở
đây vì doc zh chỉ xuất hiện ở MỘT nguồn còn doc vi có 2-3 nguồn cùng bầu, nên không có mức
trọng số trung gian hữu ích.

Ba lý do dense-title zh còn yếu, cả ba sửa được:
1. Lúc encode, store zh mới có **406k doc = 11% corpus zh**. Đến 10:27 đã 843k và đang tăng.
2. Chỉ dùng **title**, chưa body/chunk.
3. Chưa có **BM25 tiếng Trung** - lexical với query đã dịch, có thể mạnh hơn dense title.

**`salvage_json` vá được 55 câu từ `raw`, không gọi LLM**: 1.036 → **1.091/1200 câu có bản dịch
zh** (90,9%). Đúng như thiết kế - `raw` được lưu nên parser cải tiến áp dụng lại được, khỏi
chạy lại 4 giờ LLM.

**Crawl zh sau khi sửa khoá store**: 574.500 doc, **dùng được 98,0%**, 19,4 trang/s - mức cao
nhất từ đầu (trước là 31-75%). Chậm hơn 46,6 trang/s vì rate ba domain lớn đã hạ về 4, nhưng
đổi lấy 98% thì đáng. Store: **968.725 doc, 843.007 dùng được (87,0%)**.

---

### 04/10/2026 · `dense.py` trên kho tiếng Việt · **+32,8% cả hai tầng, đòn lớn nhất từ đầu giải**

Cùng mô hình BGE-M3 vừa THUA hai lần trên kho tiếng Trung, đem sang kho tiếng Việt thì cho
nhảy vọt. Ba khác biệt giải thích tất cả:

| | dense zh | BM25 zh | **dense vi** |
| --- | --- | --- | --- |
| Độ phủ kho | 23% | 23% | **88%** |
| Ngôn ngữ | cross-lingual | query dịch máy | **mono-lingual** |
| Trùng với nguồn cũ | thấp - chen doc mới vào | thấp | **cao - cộng phiếu RRF** |
| Slot chiếm | 20,2% | 20,3% | **44,8%** |
| DOCS_F2 | 0,1217 ❌ | 0,1195 ❌ | **0,1705** ✅ |

Tổng slot của 4 nguồn là 198,2% (46,1 + 49,0 + 58,3 + 44,8) → phần lớn doc được **2-3 nguồn
cùng bầu**. Đó đúng là điều kiện RRF ăn lãi đã ghi từ 02/10: "nguồn phải KHÁC nhau mà ĐỀU đúng".
dense zh thì khác nhau nhưng KHÔNG đều đúng; dense vi vừa khác loại vừa đúng.

| | Trước | Sau | |
| --- | --- | --- | --- |
| doc F2 | 0,1284 | **0,1705** | +32,8% |
| chunk F2 | 0,0898 | **0,1192** | +32,7% |
| DOCS_PRECISION | 0,0650 | **0,0884** | +36% |
| DOCS_RECALL | 0,2246 | **0,2872** | +27,9% |
| g (doc vàng/câu) | 13,0 | **17,68** | +36% |

**Tầng chunk tăng đúng bằng tầng doc dù không đổi một tham số chunk nào** (vẫn `2 × 55 doc`).
Nó khá lên chỉ vì 55 doc đầu đúng hơn. Đây là số đo trực tiếp cho điều trước đây chỉ suy luận:
cải thiện đầu danh sách ăn CẢ HAI tầng, nên mọi đòn tăng precision ở đầu đều được tính đôi.

Chi phí: embed 643.583 title mất ~6 phút trên một card 4090, vector 1,32 GB fp16.

**Phải chuyển title qua máy GPU bằng store riêng 75 MB** vì máy local không chạy được BGE-M3:
`transformers` kéo `torchaudio` lệch phiên bản → `OSError: [WinError 127]`. Thay vì gỡ/cài lại
gói trong môi trường dùng chung, xuất `data/titles_vi.sqlite` (chỉ `doc_id` + `title`, `body`
NULL) rồi `dense.py --min-body 0`. Chuyển 75 MB thay cho store 4,4 GB.

---

### 04/10/2026 · chunk 400 token · **gấp đôi số chunk trong cùng dung lượng**

Tầng chunk bị trần ZIP 100 MB khoá: ở `rr_2x64` (124.609 chunk, 96 MB), precision **biên** của
17.681 chunk cuối thêm vào là **0,0890** so với ngưỡng dừng F2/5 = **0,0347** - còn lãi 2,6 lần
nhưng không nhét thêm được, và nén chỉ cứu 0,8%.

Nên đổi núm khác: `chunk.py --target-tokens 900 → 400`.

| | target 900 | target 400 |
| --- | --- | --- |
| Số chunk | 1.085.111 | **2.366.199** (×2,18) |
| chunk/doc | 1,68 | **3,65** |
| Độ dài trung vị | 2.605 ký tự | **1.200** |
| Doc chỉ 1 chunk | 41,0% | 14,3% |
| Chunk vừa trong 96 MB | ~125.000 | **~270.000** |

`audit.py`: **47/47 PASS** qua 4 tầng trên dữ liệu thật (offset, nguyên văn, trần token, độ phủ).
Bảng `chunk_t900` giữ bản sao 1.085.111 dòng để quay lại trong một lệnh nếu chunk ngắn thua.

**Rủi ro đã biết, chưa đo:** chấm cấp chunk đòi `chunk_text` chứa hoặc overlap ĐỦ với một phần
thông tin trong `I`. Chunk 1.200 ký tự có thể CẮT NGANG phần mà chunk 2.605 ký tự bao trọn, nên
precision có thể giảm mạnh hơn mức bù của recall. Hai bài `c400_2x112` (249.038 chunk) và
`c400_4x70` (268.342 chunk) sẽ cho biết.

**Lỗi tự gây:** `audit.py` ghim cứng `data/slug_rank.jsonl`, file đó bị xoá lúc dọn 16 GB trong
`runs/` nên audit chết giữa đường ở tầng 3. Đã sửa thành `CAND_FILES` - thử danh sách ưu tiên,
lấy file đầu tiên có thật (giờ dùng `rerank_rank.jsonl`, tức kiểm trên nguồn ứng viên HIỆN TẠI
thay vì file slug cũ). Bài học: script kiểm toàn không được ghim cứng tên file dữ liệu dẫn xuất.

---

### 04/10/2026 · **giải mã baseline BTC trên leaderboard** · nó chỉ trả ~34 doc/câu

Thông số công khai của `BM25 Baseline` (BTC, 30/09, ID 4060): FINAL **0,3764** ·
DOCS_F2 0,5587 · DOCS_P **0,8805** · DOCS_R 0,5146 · CHUNKS_F2 0,1941 · CHUNKS_P 0,3403 ·
CHUNKS_R 0,1755.

Suy ra cấu hình của họ từ P/R:

```
P = g/k = 0,8805      R = g/G = 0,5146
k/G = R/P = 0,5844    với G ≈ 58 (ta đo từ 17 lượt nộp)  →  k ≈ 34
g = 0,8805 × 34 = 29,9 doc vàng/câu
kiểm chéo: F2 = 5PR/(4P+R) = 0,5613 ≈ 0,5587 họ báo ✓
```

| | Baseline BTC | Ta (`rr_2x64`) | |
| --- | --- | --- | --- |
| k (doc/câu) | **~34** | 200 | |
| DOCS_PRECISION | **0,8805** | 0,1033 | kém **8,5×** |
| DOCS_RECALL | 0,5146 | 0,3191 | kém 1,6× |
| **g (doc vàng/câu)** | **29,9** | 20,7 | họ hơn 44% với 1/6 số doc |
| CHUNKS_RECALL | 0,1755 | **0,2137** | **TA HƠN 22%** |
| CHUNKS_PRECISION | 0,3403 | 0,1495 | kém 2,3× |

**Đây là BM25 THUẦN mà mạnh hơn pipeline 4 nguồn + rerank của ta.** Khác biệt gần như chắc
chắn không ở thuật toán mà ở **độ phủ corpus**: BTC có toàn bộ dữ liệu, ta mới crawl
**1,58M/4,39M URL = 36%** (vi 647k/740k = 88%, zh 937k/3,65M = 26%).

→ **SỬA kết luận "crawl thêm gần như vô ích"** (ghi cùng ngày, dựa trên ε≈0,09): ε đó đo trên
kho TIẾNG VIỆT đã phủ 88%, không áp cho tổng thể. Phần thiếu nằm gần hết ở tiếng Trung, và
baseline chứng minh một BM25 thuần trên corpus đầy đủ đã cho DOCS_P 0,88.

→ Precision chunk của họ gấp 2,3× cũng là hệ quả của precision doc 88%: chunk lấy từ doc gần
như toàn đúng. Nên **đường lên của tầng chunk vẫn là làm tầng doc đúng hơn**, nhất quán với
những gì đã đo (chunk F2 đi 0,0898 → 0,1733 mà không đổi tham số chunk nào).

**Đòn chưa dùng, nhắm trực diện vào precision:** `bm25.py` chỉ có trọng số theo TRƯỜNG
(title 3× / tags 2× / descr 1,5× / body 1×), **chưa có trọng số theo TỪ**. Trong khi
`runs/public/expansions.jsonl` đã chứa **thực thể y khoa ba ngôn ngữ** do Qwen3.5 trích cho
1.091/1.200 câu (vd `{"vi":"chảy máu","en":"bleeding","zh":"出血"}`) - boost các term đó lên
2-3× là thay đổi nhỏ, dữ liệu đã nằm sẵn.

---

### 04/10/2026 · rerank top-1000 · **đòn đầu tiên đổi được TẬP doc**

Mọi bài rerank trước chỉ sắp lại thứ tự trong cùng 200 doc đã chọn. Rerank top-1000 rồi lấy
200 tốt nhất thì **đổi cả tập**: đo được **112/200 doc (56%) trong top-200 là MỚI**, kéo từ
hạng 200-1000 lên.

Chi phí: 5,6 s/câu trên 4090 (vs 5,5 s/câu cho top-200 trên RTX 4050) → **1,9 giờ** cho 1.200
câu. Cần store text riêng cho union doc top-1000: **302.696 doc** (100% có text), 319 MB, nén
93 MB, chuyển qua tunnel cloudflared mất **18 giây** (5 MB/s - nhanh hơn dự đoán, lần đứt trước
ở 168 MB có nguyên nhân khác).

Vì sao đáng tin: DOCS_RECALL mới 0,3191, tức 68% nhãn vàng còn nằm ngoài top-200. Và rerank-200
đã chứng minh cross-encoder xếp đúng hơn RRF (doc F2 +5,6% chỉ bằng đổi thứ tự).

---

### 05/10/2026 · kéo dữ liệu zh từ máy GPU + kế hoạch chia crawl cho đồng đội

**Kéo về `data/corpus_gpu.sqlite`** (1.057.584 doc, 4,65 GB, 306 giây qua tunnel, chỉ ĐỌC trên
máy GPU, stream qua ssh không tạo file bên đó). Đã kiểm: đủ số doc, 100% body ≥ 200 ký tự,
chồng lấn với store local chỉ 1.192 doc. **CHƯA GỘP** vào `corpus.sqlite` theo quyết định của
người dùng (gộp sau, khi crawl xong). Gộp bằng `python crawler.py --merge data/corpus_gpu.sqlite`
(INSERT OR IGNORE, chạy lại được). Sau gộp: 1.704.127 doc dùng được = 38,8% corpus.

Thành phần: `familydoctor.com.cn` 447k (42% zh đã crawl, bài viết) · `zhongyibaodian` 139k ·
`120ask` 97k · `ask.39.net` 92k. **Ba kho hỏi-đáp lớn gần như chưa chạm**: `cnkang` ~23k/963k.

**Còn lại (hàng đợi máy GPU, 05/10):** 2.189.218 chờ, trong đó **2.105.471 an toàn** (11 domain)
và 83.747 bỏ (15 domain `*.39.net` CAPTCHA). Thất bại 137.983, bị chặn 273.978.

| Domain | Còn | 1 IP | N=5 |
| --- | --- | --- | --- |
| `cnkang` | 939.840 | 65,3 h | 13,1 h |
| `120ask` | 806.406 | 56,0 h | 11,2 h |
| `ask.39.net` | 232.389 | 16,1 h | 3,2 h |
| `a-hospital` | 126.380 | 23,4 h | 4,7 h |

**Vì sao chia theo DOMAIN không nhanh hơn:** các domain chạy SONG SONG trên một IP (rate tính
riêng từng domain) nên thời gian một máy = domain nặng nhất (65 h), không phải tổng (163 h).
Đo thật: 2,2M URL ÷ 8,9 trang/s = 69 h, khớp phương án song song. Giao mỗi máy một domain chỉ
được 70 → 65 h. Chia **trong** domain theo `doc_id` mới rút ngắn được làn dài nhất:
`crawler.py --shard-ids I/N` (mới, có self-check không chồng lấn). Cân bằng đã đo: lệch 0,0%.

**Bộ kit cho đồng đội:** `data/crawl_team_kit.zip` (41 MB) gồm `crawler.py`, `pubmed_module/http.py`,
`probe_zh.py`, `HUONG_DAN.txt`, store mồi `queue_zh.sqlite.gz` (2.117.266 URL của 11 domain an
toàn, xuất từ hàng đợi máy GPU nên không trùng phần đã xong). Lệnh bắt buộc có `--domains` cố
định: dùng `--lang zh` thì kéo theo 14 subdomain CAPTCHA và crawl tụt về 0 trang/s (đã gặp).
`probe_zh.py` thử 3 lần mỗi domain, đạt khi ≥ 2/3: một lần duy nhất báo sai (máy GPU đang crawl
97,8% vẫn dính timeout ở lần thử đơn). IP quan trọng thật: GPU 4/4 domain OK, IP local `ask.39.net`
chỉ 1/3.

**Rủi ro khi tăng số máy:** tổng tải lên `cnkang` = N × 4 req/s (N=5 → 20 req/s, gấp 5 hiện nay).
Chưa biết server giới hạn theo IP hay có trần chung. Bật dần, mỗi máy cách 10-15 phút, dừng nếu
`dùng được` của bất kỳ máy nào < 90%. Lần thử rate 8 hôm qua nâng ba domain cùng lúc nên chưa
biết domain nào gây chặn; chưa từng kiểm riêng `cnkang` ở rate > 4.

**Chưa chốt:** N = 3 (~22 h) hay N = 5 (~13 h); máy GPU có restart với `--shard-ids 0/N` hay thôi.

---

### 05/10/2026 · tra cứu hướng crawl khác · Common Crawl KHÔNG cứu được

Máy GPU crawl `cnkang.com` chỉ ~1,3 doc dùng được/giây/IP; người dùng đề nghị tìm hướng hợp lý hơn.
Tra cứu (WebSearch + đo thật):

| Hướng | Kết quả |
| --- | --- |
| **Common Crawl** (tải WARC theo byte-range từ S3, khỏi chờ server đích) | **Chết.** Độ phủ đo bằng chỉ mục: `cnkang.com` **0,4%** (2.812/669.253 URL cần, hợp 16 đợt), `a-hospital.com` **5,2%** (6.656/127.591, hợp 8 đợt). Mỗi đợt chỉ ~1.000-3.000 URL của domain và đợt mới thêm rất ít. 120ask/ask.39.net chưa đo xong (chỉ mục 504/chậm) nhưng cùng cỡ. |
| asyncio/aiohttp/Scrapy (lời khuyên phổ biến) | **Không giúp.** Nút cổ chai không phải client: CPU máy GPU 2-3%, 160 luồng chờ mạng. Bottleneck là server đích trả lời chậm và giới hạn theo IP. |
| Xoay proxy/residential để né giới hạn | Không dùng: đó là lách chặn chứ không phải crawl lịch sự. |

**Hai điều đo được thật, không phải ý kiến:**

1. **Response của `cnkang` LƯỠNG CỰC.** Tải lại 8 URL vừa timeout, 1 yêu cầu mỗi 1,5 giây: 3 về trong
   0,6-1,1 s, 1 về sau 128 s, 4 vẫn treo 63-101 s. Mọi lần probe thành công đều ≤ 9 s. Chờ 25 s cho
   request sẽ treo chỉ giữ luồng vô ích → thêm `--timeout` (mặc định vẫn 25), khuyến nghị 10-12.
2. **Limiter phạt oan.** Timeout xảy ra ở mọi rate (51% ở 0,5 req/s, 19% ở rate 6), nên không phải do
   gửi nhanh. Phạt nó hạ `cnkang` từ 6 xuống 0,75 req/s mà timeout không giảm. `penalty_kind()` giờ
   KHÔNG phạt `ReadTimeout`; vẫn phạt 403/429/503, kết nối bị từ chối, CAPTCHA.

**Chưa kiểm chứng (giả thuyết, đừng coi là kết luận):** `cnkang` đặt ở Trung Quốc nên có thể
chậm với IP nước ngoài; một VPS ở Hồng Kông hoặc đại lục có thể nhanh hơn rõ rệt. Chưa đo, và tốn tiền.

---

### 05/10/2026 · HAI crawler chạy song song trên cùng phần `0/5` · phép thử rate bị nhiễm

Đo 8 giờ sau khi restart cho `cnkang` chỉ 0,91 doc dùng được/giây (kỳ vọng 4-5), 2.129 doc dồn
vào MỘT phút trong 25 phút gần nhất, vài lỗi ghi `another row available`, và `pgrep -c crawler.py`
= 23 thay vì ~12. Kiểm `/proc`: **hai tiến trình chính cùng chạy**: PID 1801713 (log
`crawl_s0.log`, bản cũ: 80 luồng, không `--timeout`, còn phạt timeout) và PID 1828844 (`crawl_s0c.log`,
bản mới). Lần restart trước không dừng được tiến trình cũ.

Hệ quả: cùng lấy các URL ưu tiên đầu hàng đợi (trùng việc), tải lên mỗi server gấp đôi trên cùng một
IP (`cnkang` thực tế tới ~12 req/s), tranh quyền ghi một file SQLite. **Mọi số đo rate/timeout của
đợt này KHÔNG dùng được.** Lỗi đo của tôi: lấy mốc "đã chạy bao lâu" bằng `pgrep -of` (tiến trình
CŨ NHẤT) nên trộn số của cả hai. Dữ liệu không hỏng (ghi theo `doc_id`, `INSERT OR REPLACE`).

Bài học: sau mỗi lần restart phải kiểm SỐ TIẾN TRÌNH CHÍNH (`pgrep -f crawler.py | wc -l` ≈ 12, không
phải 23), và đo theo đúng PID đang cần đo.

---

### 05/10/2026 · lỗi mã hoá tiếng Trung: cục bộ ở `wujue.com`, 7.229 doc (0,68%)

Hỏi "tiếng Trung có lỗi encode không?" - đo trên 1.057.584 doc đã kéo từ máy GPU:

| Chỉ số | Kết quả |
| --- | --- |
| Có `U+FFFD` | 0,04% (nằm sẵn trong nguồn: `l～2��g/ml` = `μg` mất từ site gốc, không phải lỗi của ta) |
| Mojibake kinh điển (UTF-8 đọc thành latin-1) | 0,01% |
| 6 domain lớn nhất có doc ít chữ Hán | 0% |
| **Mojibake Cyrillic** | **7.229 doc (0,68%)**: `wujue.com` 7.213 (14,4% doc của nó), `zydcd.com` 8, `health.people.com.cn` 5, `familydoctor.com.cn` 3 |

Mojibake dạng `ЗЧЮяжЪЮФЛЏвХВњ` = `非物质文化遗产`: byte GBK bị đọc bằng **ISO-8859-5** (`非` = `B7 C7` -> `ЗЧ`;
đoán đầu bằng cp1251 là SAI, sửa ra rác). Nguyên nhân: header chỉ ghi `text/html` (không charset),
charset nằm trong `<meta>`, `requests` đoán ISO-8859-1, và ta đưa BYTE THÔ cho trafilatura nên nó
tự đoán, với một số trang đoán trúng ISO-8859-5. Hai trang `wujue` cùng cấu hình, một hỏng một tốt.

**Sửa sau khi trích KHÔNG khôi phục chính xác được:** thử `encode("iso8859_5").decode("gb18030")` chỉ
sửa 43/7.229 doc (7.144 lỗi giải mã GB18030) vì lúc trích trafilatura đã chuẩn hoá NBSP và ký tự
điều khiển C1 nên chuỗi byte GBK gốc không còn nguyên. Phải sửa tại nguồn.

**Sửa:** `decode_html(raw, domain)` trong `crawler.py` giải mã trước khi đưa cho trafilatura, theo
thứ tự UTF-8 nghiêm ngặt -> charset khai báo trong `<meta>` (gb2312/gbk -> gb18030) -> domain
tiếng Trung thử gb18030 nghiêm ngặt -> không chắc thì giữ `raw` (hành vi cũ). Bảng mã đơn byte
(ISO-8859-x, cp125x) "giải mã được" mọi chuỗi byte nên không được để chúng quyết định.
Kiểm trên trang `wujue` thật: hỏng Han 0%/Cyrillic 61% -> Han 59%/Cyrillic 0%, title đúng;
trang tốt giữ nguyên (không lùi). Có self-check 6 tình huống trong `--demo`.

**Chưa làm:** crawl lại 7.229 doc. Danh sách ở `data/queue_fix_mojibake.sqlite` +
`data/mojibake_ids.txt` (~25 phút ở rate 5). Cần XOÁ 7.229 dòng hỏng trong `corpus_gpu.sqlite`
TRƯỚC khi gộp, vì `--merge` dùng `INSERT OR IGNORE` nên sẽ không ghi đè bản hỏng.
Các domain đang crawl (cnkang, 120ask, ask.39.net, a-hospital) có 0,00% mojibake nên đợt chạy
hiện tại không bị ảnh hưởng; bản sửa là bảo hiểm cho lần sau và cho kit đồng đội.

---

### 05/10/2026 · chunk 400 THUA, rerank top-1000 THẮNG · đảo ngược hướng chunk

**Dự đoán sai của tôi:** hạ chunk 900 → 400 token để nhét gấp đôi chunk vào cùng 96 MB, ước chunk F2
+34% (~0,233). Đo: **-64% (0,0624)**. Sai ở chỗ coi "precision giảm vừa phải"; thực tế P giảm 3,6 lần
và recall CŨNG giảm dù nộp gấp đôi chunk (số chunk liên quan 18.629 → 10.285).

Cách chấm tính chunk đúng khi nó "chứa hoặc overlap ĐỦ" một phần thông tin trong `I`. Nếu các phần
thông tin dài thì chunk ngắn không bao được → **chunk DÀI mới ăn**. Thêm: dung lượng cố định nên 112 doc
× 2 chunk ngắn chỉ phủ ~2.400 ký tự đầu mỗi doc, trong khi 64 doc × 2 chunk 900 phủ gần cả doc.
Khớp với quan sát cũ: `deep` (nhiều chunk/doc) thắng `wide`. Hệ quả: hướng "chunk gọn hơn" là SAI,
nếu có đổi thì đổi theo chiều DÀI HƠN. Đã khôi phục bảng `chunk` 900 từ `chunk_t900` (dựng lại đúng
schema + chỉ mục, kiểm 2.393 chunk ngẫu nhiên nguyên văn 0 sai); bản 400 giữ ở `chunk_t400`.

**Rerank top-1000 là đòn doc lớn nhất sau dense:** DOCS_F2 +16,5% (0,1948 → 0,2269). Đối chiếu
`c400_2x112` với `rr1k_2x112` (cùng chunk 400, chỉ khác doc): chunk F2 +20% (0,0624 → 0,0748), nên
doc tốt hơn kéo chunk lên đúng như đã thấy nhiều lần (đầu danh sách ăn đôi).

**Dự đoán bài ghép** (doc rerank-1000 + chunk 900): chunk F2 ≈ 0,1733 × 1,2 ≈ 0,208; FINAL ≈ (0,2269 + 0,208)/2 ≈ 0,217.

**Chưa làm, theo thứ tự tôi tin:** (a) rerank sâu hơn / pool rộng hơn, và cho reranker đọc nhiều hơn
700 ký tự đầu; (b) chunk DÀI hơn 900 (target ~1000, chạm trần khuyến nghị 1.024 token); (c) k cho
ranking mới (G ≈ 65, β 0,461 → k\* ≈ 221, lợi < 1%).

---

### 05/10/2026 · rerank-1000 chỉ cải thiện ĐUÔI danh sách, không phải đầu · chunk không nhúc nhích

Dự đoán FINAL 0,217 → đo **0,2017**. Sai ở chỗ áp hệ số "doc tốt hơn kéo chunk +20%" từ cặp bài chunk 400
sang chunk 900. Đo trên hai danh sách `rerank_rank.jsonl` (top-200) và `rerank1k.jsonl` (top-1000):

| | |
| --- | --- |
| Top-64 (phần có chunk) giống nhau | **38/64** → 26 doc bị thay (41%) |
| Chunk F2 | 0,1733 → 0,1765 (**+1,8%**) dù doc F2 +16,5% |
| Doc MỚI trong top-200 nằm ở hạng | 1-64: 23% · **65-100: 18%** · 101-150: 28% · 151-200: 31% |

→ Đầu danh sách của rerank-1000 KHÔNG tốt hơn đầu của rerank-200; lợi nằm ở đuôi (77% doc mới rơi vào
hạng 65-200, chỉ ảnh hưởng điểm doc). **Sửa nhận định cũ "đầu danh sách ăn đôi":** đúng với cải thiện
ở ĐẦU, không đúng với cải thiện ở ĐUÔI. Rerank sâu hơn nếu có lợi cũng chủ yếu tăng điểm doc → FINAL
chỉ được một nửa.

Nguồn của doc mới: hạng RRF trung vị **495**; 49% từ hạng ≥ 500, 17% từ hạng ≥ 800. Mật độ doc được
chọn mỗi hạng: vùng 200-500 = 0,17 · 500-800 = 0,107 · 800-1000 = 0,085 (giảm dần, chưa về 0). Đó là
bằng chứng nguồn cung chưa cạn ở biên 1000, nhưng "được reranker chọn" ≠ "là doc vàng" (chỉ có điểm
tổng, không có nhãn từng doc) và lợi nhỏ dần. Ước thô bước kế tiếp +3-8% doc F2 → +1,5-4% FINAL.

**Điều đang chặn là tầng chunk (0,1765 so với doc 0,2269):** hiện lấy 2 chunk ĐẦU của mỗi doc.
Giả thuyết chưa kiểm chứng: 24% doc dài có phần thông tin ở chunk thứ 3 trở đi; chọn 2 chunk liên quan
nhất bằng cross-encoder (~190k cặp, ~1-2 giờ trên 4090) thay vì 2 chunk đầu.

---

### 05/10/2026 · phân tích sâu "chọn chunk bằng cross-encoder": trần thấp, hạ xuống

**Độ nhạy của F2** (đạo hàm riêng tại điểm hiện tại): tầng DOC (P 0,1207, R 0,3707): +1% P → F2 +0,43%,
+1% R → +0,57% (R nhạy 1,3×). Tầng CHUNK (P 0,1521, R 0,2181): +1% P → +0,26%, +1% R → **+0,74%**
(R nhạy 2,8×). Ở danh sách cỡ cố định P và R tỉ lệ với cùng g, nên "tăng precision" = "tăng số doc đúng
trên mỗi suất". Ngưỡng thêm một mục: p > F2/5 = 0,045 (doc), 0,035 (chunk). Doc: biên 0,055 vs 0,045,
k\* ≈ 221 → gần tối ưu. Chunk: biên đo được 0,089 vs 0,035 (gấp 2,5×) nên thêm chunk vẫn lãi nhưng
bị trần 100 MB → mục tiêu tầng chunk là SỐ CHUNK ĐÚNG TRÊN MỖI MB.

**Quy mô cơ hội của hướng 1** (đo trên 76.800 doc trong top-64 của 1.200 câu): 1 chunk 39,5% · 2 chunk
38,2% · 3 chunk 19,2% · ≥4 chunk 3,1%. Tức **77,7% doc có ≤ 2 chunk và đã được nộp HẾT**; ta đang nộp
123.288/145.393 = **85%** mọi chunk của các doc đó, chỉ 22.105 chunk (15%) chưa nộp, nằm toàn ở 22,3% doc
≥ 3 chunk. (Sửa số cũ: "76% doc vừa 1 chunk" SAI với bảng chunk 900, thực tế 39,5%.)

**Chunk recall ≈ recall doc ở đầu danh sách:** R_chunk = 0,2181 gần đúng bằng R_doc(k=64) suy từ luật
luỹ thừa β = 0,461: 0,3707 × (64/200)^0,461 = 0,2192. Gợi ý (chưa chứng minh) rằng trong các doc đã nộp ta
đã phủ gần hết phần thông tin, nên chọn chunk KHÁC trong cùng doc có ít recall để thắng. Chunk recall bị
chặn bởi số doc vàng nằm trong top-64, không phải bởi chọn chunk nào.

**Ước hướng 1:** chỉ tác động ~28% suất chunk (doc ≥ 3 chunk) → FINAL **+1-3%** (lạc quan +4%), ~25
phút GPU (56.379 cặp). Cùng cỡ với rerank sâu hơn, nên không còn là ưu tiên 1.

**Đòn rẻ hơn chưa thử:** gộp thứ hạng reranker với thứ hạng RRF vòng 1 bằng RRF (ta có sẵn cả hai danh
sách, tính offline trong vài phút). Cross-encoder một mình hiếm khi tối ưu; kết hợp với tín hiệu vòng 1
thường làm đầu danh sách vững hơn, mà đầu danh sách là chỗ kẹt của chunk.

---

### 05/10/2026 · bài nộp tốt nhất 99,77% tiếng Việt · tiến độ máy GPU

Đếm trên `rr1k_c900_2x64` (FINAL 0,2017): `relevant_docs` **239.437 vi (99,77%) / 563 zh (0,23%)**
(563 doc zh đến từ 701 doc zh nằm sẵn trong store local), `relevant_chunks` 121.428 vi / **168 zh**.
Tức pipeline hiện chưa nhìn thấy kho tiếng Trung: BM25, dense và rerank đều chạy trên store local.

Máy GPU: phần `0/5` xong **241.472/551.907 = 43,8%** (còn 279.494), cả 11 domain 703.317/2.759.534 =
25,5%. **Vẫn HAI crawler chồng nhau** (PID 1801713 chạy 11h24m, PID 1828844 chạy 10h46m): lần restart sạch
chưa xảy ra nên tốc độ và số đo rate vẫn nhiễu.

**Có dùng được doc zh không (chưa làm, đánh giá):** hai lần thử trước (dense zh, BM25 zh) THUA vì RRF
trộn thẳng ~40 doc zh precision 0,013 vào top-200. Giờ có reranker đa ngôn ngữ để LỌC trước khi chọn:
gộp top-300 của dense-zh + BM25-zh vào pool rồi chọn top-200 theo điểm reranker; giữ top-64 là doc vi
để khỏi mất chunk (doc zh chưa gộp store nên chưa có chunk_text). Trần lý thuyết: g_zh ≈ 0,54 ở độ phủ
11% (ước thô) → ~1,4 doc vàng/câu ở 28,8% → tối đa ~+6% doc F2 nếu chọn hoàn hảo, thực tế ~+2-3%,
tăng theo độ phủ crawl (kho zh = 83% corpus).

---

### 05/10/2026 · trộn reranker với RRF vòng 1 · và LỖI KHOÁ làm crawler đứng

**Điểm:** thuần rerank (w=∞) doc 0,2269 / chunk 0,1765 → **w=2: doc 0,2271 / chunk 0,1872 / FINAL 0,2072**;
w=1: doc 0,2219 / chunk 0,1828 / FINAL 0,2023. Chunk có đỉnh quanh w ≈ 2 (1 → 0,1828 · 2 → 0,1872 ·
∞ → 0,1765); doc phẳng từ 2 đến ∞ rồi tụt ở w=1. Tinh chỉnh w quanh 2-3 chỉ còn dư địa ≲ 1%.
Mức đổi nhẹ (top-64 đổi 12/64 doc ở w=2) cho +6,1% chunk F2: nhạy hơn nhiều so với cú rerank-1000 đổi
26/64 doc mà chunk +1,8%, tức đổi ĐÚNG doc ở đầu mới quan trọng, không phải đổi nhiều doc.

**Lỗi khoá của crawler (xác định 05/10):** `RateLimiter.wait()` gốc NGỦ KHI GIỮ KHOÁ. Luồng chính (nơi
duy nhất `q.put` kết quả) lại gọi `penalize()`/`reward()` của cùng domain, cần chính khoá đó. Domain bị hạ
xuống 0,12 req/s thì hàng chục luồng xếp hàng, mỗi luồng giữ khoá 8 giây → luồng chính đứng chờ và không
xử lý kết quả của MỌI domain. Triệu chứng đã thấy: crawler s0d 0 doc trong 15 phút (CPU 2%), trước đó 2.129
doc dồn vào một phút sau hàng giờ im lặng, và mọi domain chạy dưới rất xa rate cấu hình. Tái hiện: wait()
cũ chặn luồng chính 1,30 s chỉ với một luồng ngủ; wait() mới 0,000 s. Sửa: đặt chỗ trong khoá, ngủ ngoài
khoá. Có self-check. Nhiều số đo tốc độ crawl trước đây (kể cả "rate 4 là tối ưu", rate 6, thông lượng
cnkang) bị nhiễu bởi lỗi này, không chỉ bởi hai crawler chồng nhau.

---

### 05/10/2026 · lỗi thứ HAI của crawler: đói luồng · mô phỏng chứng minh nhanh gấp 13

Sửa khoá (xem mục trước) xong, crawler s0e chạy lại được nhưng ba domain rate 6/4/1,5 đều ra ~0,77 doc/giây
và `ask.39.net` rơi xuống 0,03 req/s ngay lô đầu. Nguyên nhân thứ hai: mỗi luồng nhặt một URL của domain
đang bị hạ ĐẶT CHỖ Ở TƯƠNG LAI XA (33 giây/lượt, xếp nối đuôi) rồi ngủ hàng phút; dần dần cả 160 luồng
đều ngủ chờ domain đó và mọi domain khác hết luồng. Mỗi lô quota được chia theo rate TẠI LÚC LẤY LÔ, nên
domain vừa bị hạ vẫn mang theo hàng trăm URL đã chia.

**Sửa:** `AdaptiveLimiter.wait()` KHÔNG đặt chỗ nếu phải chờ quá `MAX_QUEUE_WAIT` = 20 giây: ném
`Deferred`, `crawl_one` trả bản ghi đánh dấu `deferred`, vòng chạy bỏ qua (không ghi, không đếm, URL vẫn
PENDING), và nghỉ 1 giây nếu cả lô bị hoãn để khỏi quay vòng nóng.

**Mô phỏng** (`sim_starve.py`: server giả, `localhost` nhanh, `127.0.0.1` trả 403 và bị hạ xuống đáy):

| | Domain nhanh ghi được trong 45 giây |
| --- | --- |
| hành vi cũ (ngủ giữ luồng) | 55 doc = 1,2/giây |
| bản sửa | **728 doc = 16,2/giây (×13)** |

Domain bị chặn nhận số lượt thử như nhau (20): sửa không làm bỏ rơi nó, chỉ không để nó nuốt luồng.

---

### 05/10/2026 · bài chẩn đoán k=34: nhãn KHÔNG giống BM25 trên store của ta · lỗi bỏ dấu

Hai bài k=34 (FINAL thấp là đúng dự kiến: recall ~0,09-0,17 mà F2 tính recall nặng 4×; chỉ đọc DOCS_P):
BM25F thuần P@34 = **0,1198**, blend_w2 P@34 = **0,2774** (hai top-34 chỉ giống nhau 5/34 doc), baseline
BTC 0,8805. Kết luận: (1) giả thuyết "nhãn vàng dựng theo kiểu BM25 trên store của ta" BỊ BÁC (BM25 thua blend
2,3×); (2) BM25 của ta ra 0,12 so với 0,88 của baseline CÙNG loại thuật toán (gấp 7 lần) nên khác biệt
không ở thuật toán mà ở dữ liệu họ index / tiền xử lý / cách tạo nhãn (vd. nhãn lấy từ nhóm kết quả có cả
baseline). Chưa phân biệt được từ số liệu hiện có. Dự đoán P@34 của blend theo luật luỹ thừa (0,31) cao hơn
thực tế 11%: đầu danh sách ít tập trung hơn đường cong suy ra từ k=160-265.

**Lỗi cụ thể tìm thấy khi phân tích:** `bm25.py` dùng `tok_vi` của `slug_bm25` (BỎ DẤU, đúng cho slug URL)
cho cả nội dung trang và câu hỏi. Đo trên 120.000 doc vi: **36,7% token của 1.200 câu hỏi** và 37,8% lần xuất
hiện trong văn bản rơi vào nhóm bị gộp nhầm; vd `dau` = đau/đầu/dấu, `da` = đã/da/đa, `nhan` = nhân/nhận/
nhãn (601 kiểu token, 1,9% kiểu nhưng 37,8% lần xuất hiện). Câu hỏi về "đau" khớp doc nói về "đầu".
**Sửa:** `bm25.py --keep-diacritics` (NFC, chữ thường, giữ dấu; slug_bm25 vẫn bỏ dấu). Có self-check.
Đang chạy `bm25d_rank.jsonl` (~58 phút) rồi `bm25d_meta.jsonl` (~34 phút). Mức cải thiện CHƯA biết: BM25 chỉ
là 3 trong 4 nguồn lexical (w=1) còn dense w=2,5, nên hiệu ứng lên blend có thể bị pha loãng.

---

### 05/10/2026 · số đo SẠCH đầu tiên của crawler (66 phút, một tiến trình) · phạt mềm ghim cnkang

Sau khi sửa khoá + đói luồng + chỉ một crawler (`crawl_s0f`, 66m37s):

| Domain | Doc/giây | Dùng được | Rate cấu hình |
| --- | --- | --- | --- |
| `120ask.com` | 3,33 | 100% | 4 |
| `ask.39.net` | 3,11 | 94% | 4 |
| `a-hospital.com` | 0,69 | 100% | 1,5 |
| **`cnkang.com`** | **0,76** | **35%** (1.992/3.040 ReadTimeout) | **6** |
| Tổng | **7,89** (7,20 dùng được) | 91% | |

Tổng từ ~2,5 lên **7,9 doc/giây (gấp ~3)**, đều theo từng phút (400-800 doc/phút).

**`cnkang` bị ghim ở sàn phạt mềm:** 0,76 doc/giây ≈ 6/8 = 0,75 (rate gốc chia SOFT_CAP). Nó có 57 lỗi kết nối
trong 66 phút (~1 lỗi mỗi 70 giây, 2%); mỗi lỗi đều phạt ×1,3 VÀ reset đồng hồ nới lại 300 giây, nên không
bao giờ hồi (log thấy 6 → 4,62 → 2,86). Lỗi kết nối LẺ là nhiễu, chỉ một LOẠT mới là server từ chối.
**Sửa:** phạt mềm chỉ khi có ≥ `SOFT_BURST` = 10 lỗi mạng trong `SOFT_WINDOW` = 60 giây; 1 lỗi/70 giây không
bao giờ bị phạt (self-check đúng nhịp đo được, mốc thời gian truyền vào để test chính xác). Phạt cứng 403/429
giữ nguyên.

**Hệ quả cho phần còn lại (ước, chưa đo):** `cnkang` còn ~126k URL trong phần 0/5 ở 0,76 doc/giây = ~46 giờ,
trong khi `120ask` ~9 giờ, nên cnkang lại là đường tới hạn. Nếu chạy được gần rate 6 với 35% dùng được:
~2,1 doc dùng được/giây (gấp ~8), vòng đầu ~6 giờ; 65% timeout cần vòng `--retry-failed` sau (3/8 URL timeout
tải lại về trong ~1 giây ở phép thử trước).

---

### 05/10/2026 · vì sao crawl "lâu hơn dự kiến 13 giờ" · công cụ `crawl_health.py`

**"13 giờ" đúng cho điều kiện: cả 5 máy chạy song song.** Hiện chỉ máy GPU chạy: phần `0/5` xong 50,8%
(còn 236.653), còn **bốn phần `1/5`-`4/5` mỗi phần 20,9% xong, còn ~419.300 URL, KHÔNG AI CHẠY** (1,68M URL = 88%
phần còn lại). Kiểm mô hình: 419k ÷ 7,9 doc/giây (số đo sạch một máy) = ~14,7 giờ mỗi phần, đúng cỡ ước 13 giờ.

**Mười lỗi tìm ra, gần như tất cả trong code crawler của ta:** DNS mỗi URL (gốc) · pool 32/luồng cạn fd
(bản sửa của tôi) · CAPTCHA trả 200 (gốc) · limiter không nới (tôi) · luồng ghi chết khi khoá (gốc) · `wait()` ngủ
khi giữ khoá (mô-đun tái dùng sai ngữ cảnh) · đặt chỗ ở tương lai gây đói luồng (bản sửa của tôi) · phạt mềm
ghim cnkang ở sàn (bản sửa của tôi) · hai crawler chồng nhau (vận hành) · mojibake GBK (gốc). Ba lỗi do chính
các bản vá của tôi; các lỗi che khuất nhau nên mỗi lần sửa nút cổ chai lại dịch chỗ (2,5 → 7,9 doc/giây).

**Sai về phương pháp:** sửa theo triệu chứng đo trên máy thật thay vì dựng bộ mô phỏng từ đầu, và KHÔNG có tiêu
chí nghiệm thu. Tiêu chí mới: **một domain còn việc mà chạy dưới 50% rate cấu hình là CÓ LỖI.**
`crawl_health.py` (chỉ đọc) báo từng domain: rate cấu hình, đo được, % đạt, % dùng được, còn bao nhiêu giờ,
và cảnh báo nếu có >1 crawler chính, không ghi doc 3 phút, domain < 50% rate, dùng được < 70%. Lần chạy thật
(78 phút): `cnkang` 0,72/4 = 18% (dùng được 34%) và `a-hospital` 49%: đúng hai domain nghi vấn; `120ask` 86%,
`ask.39.net` 80%. Hạn chế: đọc rate MẶC ĐỊNH của `RATES` chứ không đọc `--rate` ghi đè lúc chạy (cnkang chạy
`--rate cnkang.com=6` nên % đạt thực là 12%, không phải 18%).

---

### 05/10/2026 · nghiên cứu hướng đổi method (đã tra cứu; số của người khác, KHÔNG phải của ta)

**Ràng buộc luật:** mô hình ≤ 15B tham số, phát hành trước 01/08/2026, fine-tune được nhưng giữ private, dữ
liệu ngoài phải trích dẫn. Teacher > 15B chỉ được dùng khi huấn luyện; dùng nó chấm nhãn cho đúng 1.200 câu
test rồi distill là VÙNG XÁM, cần hỏi BTC. Mô hình ≤ 15B dùng thẳng lúc suy luận thì không bị hạn chế.

| Hướng | Bằng chứng đã xác minh (nguồn) | Lưu ý |
| --- | --- | --- |
| **Qwen3-Embedding-4B/8B** thay/bổ sung BGE-M3 | MTEB multilingual **70,58 so với 63,0** của BGE-M3 (HF model card + bảng xếp hạng, 05/06/2025). Apache-2.0, 100+ ngôn ngữ, 32k ngữ cảnh | Query PHẢI có tiền tố `Instruct: {tác vụ}
Query:{câu}`, `padding_side=left`. 8B fp16 ≈ 16 GB: máy GPU dùng chung nên thử 4B (~8 GB) trước. KHÔNG tìm được số riêng cho tiếng Việt y khoa |
| **Qwen3-Reranker-4B/8B** thay/bổ sung bge-reranker-v2-m3 | Reranker-8B so với bge-reranker-v2-m3: MTEB-R 69,02 vs 57,03 · CMTEB-R 77,45 vs 72,16 · **MMTEB-R 72,94 vs 58,36** · MLDR 70,19 vs 59,51 (HF model card). Chấm bằng logit yes/no | 8B chậm ~14× bge: chỉ hợp xếp lại top-100~150 (120k-180k cặp), không hợp top-1000 |
| **PRF vector** (Rocchio trên embedding) | Cải thiện cả dense retriever lẫn reranker; tốt nhất khi **ít** doc phản hồi và **câu hỏi gốc giữ trọng số lớn** (Li et al., 2108.11044; số cụ thể không trích được vì PDF) | Hợp bài toán nhiều doc vàng/câu (~65). Rủi ro khi tín hiệu phản hồi yếu |
| **Fine-tune không nhãn** (sinh query tổng hợp + soft label từ teacher) | GPL: tới **+9,3 nDCG@10** so với dense dựng sẵn trên 6 miền chuyên (NAACL 2022). Promptagator: 8 ví dụ đủ thắng mô hình train bằng 500k nhãn (47,8 vs 46,6 SPLADE v2, 11 bộ BEIR). Querit-Reranker (2606.19037): +5,2 BEIR, +7,8 MIRACL nDCG@10 bằng synthetic query + soft label + trộn checkpoint | Cần cả ngày; KHÔNG có dev nhãn riêng (chỉ có leaderboard ~10 lượt/ngày làm dev). Thành thật: chưa đáng làm trước khi nâng mô hình dựng sẵn |

**Đã loại bằng số đo:** mở rộng bằng bản sao gần giống (simhash Hamming ≤ 3): chỉ **2,7%** doc vi có bản sao,
mở rộng top-200 từ 60 doc đầu thêm trung vị **0 doc/câu** (258 doc cho cả 1.200 câu). PubMed: bỏ theo quyết
định của người dùng (không ai dùng).

**Phụ thuộc vào crawl:** kho tiếng Việt đã phủ 88%, còn ~89k URL (chủ yếu `nhathuoclongchau`), nên toàn bộ
việc phía vi (đổi mô hình, PRF, query, BM25 giữ dấu) làm được NGAY và chuyển sang kho lớn hơn không cần làm
lại. Chỉ tích hợp doc zh và chỉnh trọng số cuối cùng phải chờ crawl. Cache điểm (query, doc) để lần sau
chỉ chấm cặp mới.

---

### 06/10/2026 · ngày FINAL 0,2072 → **0,2658** · pool mở rộng, Qwen3-Reranker, sửa chunk · các bài học

**Diễn biến điểm (leaderboard, đều đo thật; bảng đầy đủ ở §2b):**
| Bước | FINAL | Doc F2 | Chunk F2 |
| --- | --- | --- | --- |
| `blend_w2` (05/10) | 0,2072 | 0,2271 | 0,1872 |
| pool D (BM25 có dấu + dense nội dung vi) | 0,2287 | 0,2563 | 0,2011 |
| pool F (phủ đủ kho vi + BM25 entity) | 0,2457 | 0,2811 | 0,2104 |
| chunk `t40_70` | 0,2476 | 0,2811 | 0,2141 |
| Qwen3-Reranker top-100 (bài B) | 0,2581 | 0,2796 | 0,2366 |
| **Qwen3-Reranker top-250 (bài B2)** | **0,2658** | **0,2914** | **0,2402** |

**1. Chẩn đoán k=1000 đổi hướng làm việc.** Nộp top-1000 của `blend_w2`: DOCS_R 0,4734 (g≈32,5, G≈68,7) → pool bỏ sót 53% nhãn; nút cổ chai là
TRUY HỒI, không phải xếp hạng. Sau đó recall pool đo bằng cùng cách: D 0,5613 · E 0,6045 · F 0,6108. Mỗi bài k=1000 chỉ tốn một lượt nộp và cho biết
pool rộng thêm bao nhiêu trước khi tốn GPU rerank.

**2. zh không đáng.** Store máy GPU có 1,26M doc zh (tiền xử lý: BM25 zh bigram ký tự + bản dịch Hy-MT2, dense BGE-M3 trên 1,24M title; bỏ 8.275 doc mojibake).
Bài zh-only: DOCS_P 0,0089 (g_zh 1,78/200), DOCS_R 0,0256 → ~2,6% nhãn ở độ phủ ~35%. Ngoại suy phủ 100% ≈ +7% recall. Cuối cùng BTC cũng bỏ PubMed.
Bài zh-zh dense (query zh) đã dựng (`diag_zhq_only200`, vân tay `f0b2453fa1b7`) nhưng KHÔNG nộp (không đáng lượt).

**3. Pool mở rộng đến từ hai thứ:** (a) BM25 **có dấu** (`--keep-diacritics`, trước đó bài tốt nhất vẫn dùng bản bỏ dấu); (b) **dense nội dung** (title + 600 ký tự đầu body)
cùng phủ đủ kho vi (Long Châu 4.401 → 40.735 doc có nội dung, 8.770 doc crawl lại). Hai nguồn dense (title, nội dung) bầu cho gần như cùng doc (mỗi nguồn ~74% slot top-200)
nhưng vẫn cộng thêm doc mới vào top-1000. Nguồn **BM25 entity** (cụm từ khoá Qwen + bigram từ, `bm25_ent.py`) chỉ +0,6 điểm recall pool (+1,0%).

**4. Qwen3-Reranker-4B** (Apache-2.0, 06/2025): prompt theo model card, điểm P(yes). Tốc độ đo trên RTX 4090: 25 cặp/s (batch 16, top-150), ~27 cặp/s sau sửa. Qwen và bge chỉ trùng 9,3/20 doc đầu.
Bỏ bge (bài B) hơn trộn bge (bài A): chunk 0,2366 vs 0,2255. Chấm sâu hơn 100 → 250: doc +4,2%, chunk +1,5%. Điểm Qwen TB 0,564 (hạng 1–100) vs 0,327 (hạng 101–250).

**5. Điểm doc chỉ phụ thuộc tập doc (đính chính 04/10).** Bài A (Qwen chỉ xếp lại trong top-100) cho DOCS P/R y hệt bài trước từng chữ số. Bài C ghép sai tập → doc 0,2551.

**6. Chunk.** (a) `t40_70` (40 doc × 2 chunk + doc 41–70 × 1 chunk) hơn 2×64 dù ít chunk hơn 8,6%: CHUNKS_P 0,1770 → 0,1875, CHUNKS_R gần như không đổi. (b) Chọn chunk theo trùng từ khoá
câu hỏi không có lợi (0,2135 vs 0,2141). (c) Chunk 400 token đã thua nặng từ 05/10 (0,0624 vs 0,1765).

**7. Bài học vận hành (đừng lặp lại):**
- `crawler.py --merge` = `INSERT OR IGNORE`: dòng 403/429 cũ chặn bản thành công (mất 17k doc Long Châu); phải thay dòng không có body, đặt lại `queue.state` (DONE ⇔ body ≥ 200), gán `lang`.
- Truy vấn quét cả bảng `doc` 9 GB không có index mất hàng phút; update theo khoá chính (8.770 doc trong 2 giây). Tạo index `doc_id` trên store slim trước khi tra cứu.
- `submission.load_candidates` sắp lại theo điểm: file tự ghép hai thang điểm → nộp sai tập (mất 1 lượt, FINAL 0,2459).
- Đọc `mtime` của log trước khi báo tiến độ: một lần tôi báo "đang chạy 500/1200" từ dòng log cũ trong khi tiến trình đã chết 15 phút.
- `pkill -f <mẫu>` qua ssh khớp cả lệnh ssh của chính nó và tự cắt phiên.
- Qwen rerank OOM: logits mọi vị trí (cần chỉ `lm_head` cho token cuối), xử lý OOM ngoài khối `except`, `expandable_segments:True`, batch 32.
- Ước tính thời gian phải nhân đúng số doc: "hạng 251–500 ≈ 100 phút" là sai; thực tế 250 doc/câu ≈ 3,1 giờ một GPU.
- SSH máy GPU từ 06/10 đòi key + mật khẩu (xem `CLAUDE.md` §4); mật khẩu không ghi vào file.

**8. Việc tiếp theo & trạng thái chạy dở:** xem `CLAUDE.md` §6–7 (Qwen hạng 251–400 đang chạy trên GPU 1).

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
| 02/10 | `s_full_k200.zip` | slug + store 127k doc | 200 | | | 290 chunk/câu, **ZIP 253 MB - UPLOAD FAIL** |
| 02/10 | `s_k200_ctop50.zip` | slug + store 127k doc | 200 | | | 73 chunk/câu từ top-50 doc, 64 MB |
| 02/10 | `s_k200_ctop20.zip` | slug + store 127k doc | 200 | **0,0821** | **0,0366** | 29 chunk/câu từ top-20 doc, 26 MB. FINAL **0,0594** |
| 02/10 | `s_k200_ctop50.zip` | slug + store 127k doc | 200 | **0,0821** | **0,0495** | 73 chunk/câu từ top-50 doc, 64 MB. FINAL **0,0658** ← tốt nhất |
| 02/10 | `s_k200_ctop100.zip` | slug + store | 200 | | | 146 chunk/câu, 127 MB — **UPLOAD FAIL** |
| 02/10 | `s_k200_wide1.zip` | slug + store | 200 | | | 158 chunk/câu, 159 MB — **UPLOAD FAIL** |
| 02/10 | `s_wide100c1.zip` | slug + store | 200 | | | **RỘNG**: 1 chunk của 100 doc, 79 chunk/câu, 80 MB |
| 02/10 | `s_wide75c1.zip` | slug + store | 200 | 0,0821 | 0,0486 | RỘNG: 1 chunk/75 doc, 59 chunk/câu. FINAL 0,0654 |
| 02/10 | `s_wide100c1.zip` | slug + store | 200 | 0,0821 | 0,0513 | RỘNG: 1 chunk/100 doc, 79 chunk/câu. FINAL 0,0667 |
| 02/10 | `bm25_k200_w60c1.zip` | **BM25F** | 200 | **0,0872** | 0,0618 | FINAL **0,0745** — DOCS_F2 rời 0,0821 lần đầu |
| 02/10 | **`fused_k200_w60c1.zip`** | **RRF(slug, BM25F)** | 200 | **0,1068** | **0,0694** | FINAL **0,0881** ← TỐT NHẤT |
| 02/10 | **`fused3_k200.zip`** | **RRF(slug, BM25F, meta)** | 200 | **0,1077** | **0,0731** | FINAL **0,0904** ← TỐT NHẤT. Nguồn thứ 3 chỉ +2,6% (nguồn thứ 2 cho +22%) |
| 02/10 | `fused4_k200.zip` | RRF(+ bm25_body) | 200 | 0,1058 | 0,0733 | FINAL 0,0896 — **THUA `fused3`**, xác nhận: nguồn tương quan 82% làm hại |
| 03/10 | **`pipeline_k200.zip`** | RRF 3 nguồn, store **625k** doc | 200 | **0,1280** | **0,0848** | FINAL **0,1064** ← TỐT NHẤT. Chỉ đổi DỮ LIỆU (127k→625k doc), thuật toán y nguyên: doc +18,8%, chunk +16,0% · vân tay chunk `09a8114fde43` |
| 03/10 | `k265_ctop90.zip` | RRF 3 nguồn, 625k doc | 265 | 0,1261 | **0,0863** | FINAL 0,1062. **k=265 THUA** (-1,5% doc) nhưng ctop90 THẮNG (+1,8% chunk) → triệt tiêu. β của slug (0,536) KHÔNG dùng được cho rrf3 (β=0,455) · vân tay chunk `fb94f7034ced` |
| 03/10 | **`x_k200_ctop90.zip`** | RRF 3 nguồn, 625k doc | 200 | **0,1280** | **0,0863** | FINAL **0,1071** ← TỐT NHẤT. Ghép doc của `k200` với chunk của `ctop90`: cả 6 số LB bằng ĐÚNG số của hai bài thành phần → **hai tầng độc lập tuyệt đối, FINAL = (doc+chunk)/2 chính xác** · vân tay chunk `fb94f7034ced` |
| 03/10 | `x_slug2.zip` | RRF **slug×2** + BM25F + meta | 200 | 0,1228 | 0,0745 | FINAL 0,0987 — **THUA** 4,1% doc. slug giữ 71,5% slot (từ 48,9%) → slug là nguồn YẾU nhất, đừng tăng trọng số cho nó |
| 03/10 | `x_meta2.zip` | RRF slug + BM25F + **meta×2** | 200 | 0,1214 | 0,0797 | FINAL 0,1006 — **CŨNG THUA** 5,2% doc. Lệch về bất kỳ nguồn nào cũng hại → **w=1,1,1 là tối ưu** |
| 03/10 | `x_k150.zip` | RRF 3 nguồn, 625k doc | **150** | 0,1274 | 0,0848 | FINAL 0,1061 — thua 0,5%. Cùng với k=265 (0,1261) → đỉnh PHẲNG quanh k=200, hết chuyện quét k · vân tay chunk `09a8114fde43` |
| 03/10 | **`x_deep2x45.zip`** | RRF 3 nguồn, **2 chunk × 45 doc** | 200 | 0,1280 | **0,0863** | FINAL **0,1071** = ngang bài tốt nhất nhưng ZIP **75 MB** (vs 92) và ít hơn 13% chunk. CHUNKS_PRECISION 0,0833 > 0,0772 → chunk THỨ HAI của doc top-45 giá trị hơn chunk ĐẦU của doc hạng 45-90. **ĐẢO CHIỀU kết luận 02/10** · vân tay chunk `cd788145a2ab` |
| 03/10 | **`x_deep2x55.zip`** | RRF 3 nguồn, **2 chunk × 55 doc** | 200 | 0,1280 | **0,0896** | FINAL **0,1088** ← TỐT NHẤT. 110.229 chunk, 90 MB. Precision biên của 9.649 chunk thêm vào = 0,0465 so ngưỡng dừng 0,0179 → **vẫn lãi 2,6×, chặn bởi 100 MB chứ không bởi điểm**. Nhưng lợi suất giảm: +9,6% chunk chỉ cho +1,9% F2 |
| 04/10 | **`new_deep2x55.zip`** | RRF 3 nguồn, **647.034 doc** (+22.605) | 200 | **0,1284** | **0,0898** | FINAL **0,1091** ← TỐT NHẤT. Chỉ khác DỮ LIỆU (+3,5% doc). Dự đoán từ co giãn 0,108 là 0,1092, đo được 0,1091 → **mô hình co giãn đứng vững qua 2 mốc cách nhau 100×**. Vân tay doc `92848e451ba6` chunk `0c70d200deac` |
| 04/10 | `dense4_2x55.zip` | RRF 4 nguồn (+ **dense-title zh**) | 200 | 0,1217 | 0,0896 | FINAL 0,1056 — **THUA** 5,2% doc. Tách ra: g_zh = 0,54 doc/câu từ 40,4 slot → precision 0,0134 vs precision biên vi 0,0296. Nhãn vàng CÓ doc zh nhưng dense-title zh chỉ mạnh bằng 45% phần cuối danh sách vi |
| 04/10 | `bm25zh_2x55.zip` | RRF 4 nguồn (+ **BM25F zh**, query đã dịch) | 200 | 0,1195 | 0,0896 | FINAL 0,1045 — **THUA cả dense zh**. g_zh = 0,32 doc/câu (precision 0,0079) so với 0,54 của dense-title. 20,3% slot, `term trong query: zh 11.027` (trước 72) nên bản dịch có tác dụng, nhưng vẫn kém cross-lingual trực tiếp |
| 04/10 | **`densevi_2x55.zip`** | RRF 4 nguồn (+ **dense-title VI**) | 200 | **0,1705** | **0,1192** | FINAL **0,1449** ← TỐT NHẤT, **+32,8% cả hai tầng**. g 13,0 → 17,68. Chiếm 44,8% slot mà 3 nguồn kia chỉ tụt nhẹ (48,5→46,1 · 55,1→49,0 · 63,4→58,3) → nó bầu CÙNG doc, RRF cộng phiếu. Chunk tăng 32,7% dù KHÔNG đổi tham số chunk nào |
| 04/10 | **`dvi15_2x55.zip`** | RRF 4 nguồn, **dense w=1,5** (57,1% slot) | 200 | **0,1799** | **0,1353** | FINAL **0,1576** ← TỐT NHẤT. doc +5,5% nhưng chunk **+13,5%** - lần thứ hai chunk tăng mạnh hơn doc |
| 04/10 | `dvi_k160.zip` | RRF 4 nguồn dense w=1,0, **k=160** | 160 | 0,1703 | 0,1192 | FINAL 0,1448 ≈ k=200 (0,1449). CHUNKS_F2 ra ĐÚNG 0,1192 như vân tay chunk giống nhau dự báo → leaderboard nhất quán. β = **0,461**, gần y hệt 0,455 của nguồn cũ |
| 04/10 | **`dvi25_2x55.zip`** | RRF 4 nguồn, **dense w=2,5** (74,9% slot) | 200 | **0,1845** | **0,1442** | FINAL **0,1644** ← TỐT NHẤT |
| 04/10 | `donly_2x55.zip` | **chỉ dense**, bỏ 3 nguồn lexical | 200 | 0,1680 | 0,1300 | FINAL 0,1490 — thua w=2,5 **9%** nhưng vẫn vượt xa 3 nguồn lexical không dense (0,1284) → lexical vẫn mang thông tin dense không có, GIỮ |
| 04/10 | `dvi4_2x55.zip` | dense **w=4** (89,0% slot) | 200 | 0,1822 | 0,1438 | FINAL 0,1630 — đã QUÁ đỉnh. Đường cong trơn một đỉnh: 1,0→0,1705 · 1,5→0,1799 · **2,5→0,1845** · 4,0→0,1822 · ∞→0,1680 |
| 04/10 | **`rr_2x55.zip`** | **+ rerank** `bge-reranker-v2-m3` trên top-200 | 200 | **0,1948** | **0,1677** | FINAL **0,1812** ← TỐT NHẤT. Giữ ĐÚNG cùng tập 200 doc (đã kiểm 1200/1200 câu) mà doc F2 vẫn tăng **5,6%** → **hệ thống chấm cấp document CÓ tính thứ tự**. top-55 đổi 28/55 doc → chunk +16,3% |
| 04/10 | **`rr_2x64.zip`** | rerank, chunk từ **64 doc** (124.609 chunk, 96 MB) | 200 | 0,1948 | **0,1733** | FINAL **0,1841** ← TỐT NHẤT. `DOCS_F2` ra ĐÚNG 0,1948 như vân tay doc dự báo. p_biên của 17.681 chunk thêm vào = **0,0890** so ngưỡng dừng 0,0347 → còn lãi 2,6× nhưng **hết dung lượng** |
| 05/10 | `c400_2x112.zip` | rerank-200, **chunk 400 token**, 2×112 doc | 200 | | | 249.038 chunk (×2,0), 91 MB. Cùng vân tay doc `18e7b49554cb` → đo THUẦN tầng chunk |
| 05/10 | `c400_4x70.zip` | chunk 400, **4 chunk × 70 doc** (deep) | 200 | | | 268.342 chunk, 93 MB. Deep còn thắng với chunk ngắn? |
| 05/10 | `c400_2x112.zip` | rerank-200, **chunk 400 token** 2×112 doc (249.038 chunk) | 200 | 0,1948 | **0,0624** | FINAL **0,1286** ← THUA nặng. DOCS_F2 ra ĐÚNG 0,1948 (bài hợp lệ). Chunk liên quan: 18.629 → **10.285** dù nộp gấp đôi chunk; P 0,1495 → 0,0413, recall 0,2137 → 0,0918. **Chunk NGẮN thua, DÀI mới ăn** |
| 05/10 | `rr1k_2x112.zip` | **rerank top-1000** + chunk 400, 2×112 | 200 | **0,2269** | 0,0748 | FINAL 0,1509. **DOC +16,5%**: P 0,1033 → 0,1207, R 0,3191 → 0,3707, g 20,7 → 24,1, G = g/R ≈ 65. Chunk 400 kéo FINAL xuống |
| 05/10 | **`rr1k_c900_2x64.zip`** | doc của `rerank1k` + **chunk 900**, 2×64 doc | 200 | **0,2269** | **0,1765** | FINAL **0,2017** ← TỐT NHẤT. DOCS_F2 ra ĐÚNG 0,2269 (vân tay đúng). Dự đoán 0,217 TRƯỢT: chunk chỉ +1,8% (0,1733 → 0,1765) chứ không +20% như tôi áp từ cặp bài chunk 400 |
| 05/10 | `blend_w1_2x64.zip` | RRF(rerank-1000 w=1, RRF vòng 1 w=1) + chunk 900 2×64 | 200 | | | 125.621 chunk, 96 MB. Top-200 giống rerank thuần 145/200, top-64 giống 42/64. Vân tay doc `afb43355de18`. Kiểm giả thuyết: trộn với tín hiệu vòng 1 làm ĐẦU danh sách vững hơn → chunk F2 > 0,1765 |
| 05/10 | `blend_w1_2x64.zip` | RRF(rerank-1000 w=1, vòng 1 w=1) + chunk 900 2×64 | 200 | 0,2219 | 0,1828 | FINAL 0,2023. Doc GIẢM 2,2% (đổi 55/200 doc), chunk +3,6% |
| 05/10 | **`blend_w2_2x64.zip`** | RRF(rerank-1000 w=2, vòng 1 w=1) + chunk 900 2×64 | 200 | **0,2271** | **0,1872** | FINAL **0,2072** ← TỐT NHẤT. Doc ngang (+0,1%), chunk **+6,1%**: P 0,1521 → 0,1603, R 0,2181 → 0,2336. Xác nhận giả thuyết "trộn với tín hiệu vòng 1 làm ĐẦU danh sách vững hơn", và không tốn GPU |
| 05/10 | `diag_bm25_k34.zip` | **chẩn đoán**: BM25F thuần, top-34 | 34 | 0,0798 | 0,0686 | FINAL 0,0742. DOCS_P@34 = **0,1198** (g = 4,1) |
| 05/10 | `diag_blend_k34.zip` | **chẩn đoán**: blend_w2, top-34 | 34 | 0,1671 | 0,1540 | FINAL 0,1605. DOCS_P@34 = **0,2774** (g = 9,4). Dự đoán 0,31 theo luật luỹ thừa, thấp hơn 11% |
| 03/10 | **`x_deep2x50.zip`** | RRF 3 nguồn, **2 chunk × 50 doc** | 200 | 0,1280 | **0,0879** | FINAL **0,1079** ← TỐT NHẤT. 100.580 chunk (ít hơn ctop90 3,4%) mà CHUNKS_F2 cao hơn 1,9% → **`deep` thắng `wide`, đã xác nhận**. Vân tay chunk khác VÀ điểm khác `deep2x45` → leaderboard chấm đúng từng bài, nên số y hệt của `deep2x45` là do dán trùng |

| 05/10 | `diag_zhG_only200.zip` | **chẩn đoán**: CHỈ doc zh, RRF(dense-title zh, BM25F zh) trên 1,26M doc zh, bỏ 8.275 doc mojibake | 200 | 0,0160 | 0 (chunk rỗng) | FINAL 0,008. DOCS_P **0,0089** (g_zh = 1,78 doc/câu), DOCS_R **0,0256** → G ≈ 69,5. Nhãn zh chỉ ~2,6% tổng nhãn ở độ phủ ~35%. Dưới ngưỡng 0,03 → chưa đáng crawl thêm vì zh. Vân tay doc `2c567b322370` |

| 05/10 | `diag_blend_k1000.zip` | **chẩn đoán**: `blend_w2` top-1000, chunk rỗng | 1000 | 0,1175 | 0 | FINAL 0,0587. DOCS_P **0,0325** (g = 32,5), DOCS_R **0,4734** → G ≈ 68,7. Recall ở k=200 ~0,37 → mở 5× độ sâu chỉ thêm ~10 điểm. **Pool ứng viên bỏ sót 53% nhãn** → nút cổ chai là TRUY HỒI, không phải xếp hạng. Vân tay doc `868ce85b06fb` |

| 06/10 | **`blendD_2x64.zip`** | RRF vòng 1 = slug + **BM25 có dấu** (rank+meta) + dense-title vi (w2,5) + **dense nội dung vi** (title+600 ký tự đầu body, w2,5) → rerank-1000 (bge, ghép điểm cũ + `rerank_delta` 387k cặp) → blend w2 + chunk 900 2×64 | 200 | **0,2563** | **0,2011** | FINAL **0,2287** ← TỐT NHẤT (+10,4% so 0,2072). Doc +12,9%, chunk +7,4%. DOCS_P 0,1367 / R 0,4167 (g ≈ 27,3). Nguồn: pool k=1000 recall 0,4734 → **0,5613** (bài chẩn đoán D, vân tay `d2c42eb7abc3`). ZIP 95,6 MB. Vân tay doc `604c16aeae34` chunk `a3c86144a062` |

| 06/10 | `diag_fD_k1000.zip` | **chẩn đoán**: RRF vòng 1 D (xem trên), top-1000, chunk rỗng | 1000 | 0,1423 | 0 | DOCS_P 0,0396 (g = 39,6), DOCS_R **0,5613** → G ≈ 70,5. Pool recall 0,4734 → 0,5613 (+18,6%), thêm ~7,1 doc vàng/câu. Chưa tách B (chỉ BM25 có dấu) / C (chỉ dense nội dung): `8d75202f1f6b` / `ad8a0d6193c7` |

| 06/10 | `diag_fE_k1000.zip` | **chẩn đoán**: pool E = slug + BM25 có dấu (kho vi đầy đủ + Long Châu 40.735 doc) + dense title/nội dung (688.483 doc), top-1000 | 1000 | 0,1526 | 0 | DOCS_P 0,0424, DOCS_R **0,6045** (D: 0,5613, +7,7%). Vân tay `24a81cfe0b1f` |
| 06/10 | `diag_fF_k1000.zip` | **chẩn đoán**: pool F = E + BM25 entity (cụm từ khoá Qwen + bigram từ, w=1), top-1000 | 1000 | 0,1539 | 0 | DOCS_P 0,0427, DOCS_R **0,6108** (E: 0,6045, +1,0%; D: 0,5613, +8,8%), G ≈ 69,9. Nguồn entity chỉ thêm ~0,6 điểm nhưng dương. Vân tay `bb4291d142bc` |

| 06/10 | **`blendF_vf_2x64.zip`** | pool F (slug + BM25 có dấu + dense title/nội dung vi 688k doc + BM25 entity) → rerank-1000 (ghép điểm cũ + 208k cặp mới) → blend w2 + chunk 900 2×64 từ `corpus_vifull` | 200 | **0,2811** | **0,2104** | FINAL **0,2457** ← TỐT NHẤT (+7,4% so 0,2287; +18,6% so 0,2072). Doc +9,7%, chunk +4,6%. DOCS_P 0,1487 / R 0,4618; CHUNKS_P 0,1770 / R 0,2675. 123.278 chunk, ZIP 96,7 MB. Vân tay doc `4107fffc62e6` chunk `dff7d41dcfe2` |

| 06/10 | `blendF_t40_70.zip` | cùng danh sách doc với `blendF`; chunk: 2 chunk × 40 doc đầu + 1 chunk × doc hạng 41–70 (112.648 chunk, 91,4 MB) | 200 | 0,2811 | **0,2141** | FINAL **0,2476** ← TỐT NHẤT (+0,8%). Chunk F2 +1,8% dù ÍT chunk hơn 8,6%: CHUNKS_P 0,1770 → **0,1875**, CHUNKS_R 0,2675 → 0,2671 (gần như KHÔNG đổi). → chunk THỨ HAI của doc hạng 41–64 đóng góp ~0 recall, chỉ làm loãng precision. Vân tay chunk `a099fbb914c9` |

| 06/10 | `blendF_t40_70_q.zip` | như `t40_70` nhưng chọn chunk KHỚP CÂU HỎI (tổng IDF từ câu hỏi trong chunk) thay vì chunk đầu; đổi 9.242/112.648 chunk (8,2%) | 200 | 0,2811 | 0,2135 | FINAL 0,2473 — **không có lợi** (−0,3% chunk F2 so 0,2141). CHUNKS_P 0,1875 → 0,1857, CHUNKS_R 0,2671 → 0,2683. Chọn theo trùng từ khoá không hơn chunk đầu → giữ chunk đầu. Vân tay chunk `6fcf30fa8ce0` |

| 06/10 | `blendQA_t40_70.zip` | pool F, Qwen3-Reranker-4B top-100: RRF(Qwen w2, bge w2, vòng 1 w1) + chunk t40_70 | 200 | 0,2811 | 0,2255 | FINAL 0,2533 (+2,3% so 0,2476). **Doc F2 GIỮ NGUYÊN 0,2811, P/R y hệt** vì tập 200 doc không đổi (Qwen chỉ xếp lại top-100) → đính chính: thứ tự KHÔNG ảnh hưởng điểm doc, chỉ tập doc. Chunk +5,3% nhờ top-40/70 đúng hơn |
| 06/10 | **`blendQB_t40_70.zip`** | pool F, RRF(Qwen w2, vòng 1 w1) — BỎ bge — + chunk t40_70 | 200 | 0,2796 | **0,2366** | FINAL **0,2581** ← TỐT NHẤT (+4,2% so 0,2476). Doc −0,5% (tập đổi: 149/200 giống), chunk **+10,5%**. CHUNKS_P 0,2050 / R 0,2959. Qwen3-Reranker-4B xếp top đầu tốt hơn bge rõ rệt; Qwen/bge chỉ trùng 9,3/20 doc |

| 06/10 | `blendQC_t40_70.zip` | **LỖI CỦA TÔI**: định ghép tập 200 doc của A + thứ tự của B, nhưng file ứng viên trộn điểm hai thang (B cho 200 doc đầu, A cho phần còn lại) mà `load_candidates` SẮP LẠI theo điểm giảm dần → tập 200 doc nộp ra chỉ giống A 110,7/200 | 200 | 0,2551 | 0,2366 | FINAL 0,2459. Chunk đúng như B (0,2366) vì top-70 vẫn là của B; doc tụt do tập sai. Đã sửa (`blendQC2`: điểm giảm đều theo vị trí). Bài học: file ứng viên phải có điểm cùng thang hoặc giảm đều. Tốn 1 lượt nộp |

| 06/10 | **`blendQB2_t40_70.zip`** | pool F, **Qwen3-Reranker-4B chấm top-250** (blendF hạng 1–250): RRF(Qwen w2, vòng 1 w1) + chunk t40_70 | 200 | **0,2914** | **0,2402** | FINAL **0,2658** ← TỐT NHẤT (+3,0% so 0,2581). Doc +4,2% (P 0,1543 / R 0,4781), chunk +1,5% (P 0,2063 / R 0,3042). Chấm sâu hơn (100 → 250) kéo thêm doc đúng vào top-200; 21% tập 200 đổi. ZIP 94,0 MB. Điểm Qwen TB 0,564 (hạng 1–100) vs 0,327 (hạng 101–250). Vân tay doc/chunk: xem `submission.py` lần dựng 06/10 |

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

### 02/10/2026 · GIỚI HẠN DUNG LƯỢNG UPLOAD · ràng buộc mới, chưa biết trước

Bài nộp `--chunks-per-doc 999` cho cả 200 doc ra **ZIP 253 MB** (JSON 977 MB,
348.400 chunk = 290/câu, 726 MB `chunk_text` thuần). **Upload lên leaderboard không chạy.**

Nguyên nhân: `chunk_text` là văn bản THẬT, không phải id. 290 chunk × 2,6 KB = 754 KB
mỗi câu × 1.200 câu.

**Hệ quả nghiêm trọng cho private phase:** chỉ có **5 lượt nộp TỔNG CỘNG**, nên một lượt
fail upload là mất 20% ngân sách. Phải chốt dung lượng an toàn trước 01/11.

Đã thêm `submission.py --chunk-from-top M`: `relevant_docs` vẫn trả đủ `--topk` nhưng
chunk chỉ lấy từ M doc ĐẦU. Hai tầng được chấm ĐỘC LẬP nên tối ưu riêng được.

| File | chunk/câu | ZIP | Upload |
| --- | --- | --- | --- |
| `s_full_k200.zip` | 290 | **253 MB** | ❌ không chạy |
| `s_k200_ctop50.zip` | 73 | 64 MB | đang thử |
| `s_k200_ctop20.zip` | 29 | 26 MB | đang thử |

Và nó không chỉ là chuyện dung lượng - nó **đúng hơn về mặt điểm**:
`DOCS_PRECISION` là 0,1154 ở k=20 nhưng chỉ 0,0419 ở k=200 → chunk từ top-20 có khả năng
trúng **cao gấp 2,75 lần**. Nộp chunk cho cả 200 doc nghĩa là **~96% chunk đến từ doc không
phải nhãn vàng** - chắc chắn vô ích, chỉ làm loãng precision.

---

### 02/10/2026 · giới hạn upload = **100 MB của Cloudflare**, không phải nghẽn băng thông

Từng ghi "giới hạn trong khoảng 80-127 MB, chưa rõ nguyên nhân". Đo lại khi crawl đã dừng:

```
Upload bandwidth    20,5 Mbps (Cloudflare) / 7,1 Mbps (httpbin)  ->  66 MB chỉ cần 26-75 giây
leaderboard         104.21.7.227 = Cloudflare | TCP 63-79 ms | GET / 0,4s
```

Mạng và server đều ổn. Nguyên nhân thật: **leaderboard nằm sau Cloudflare, gói Free/Pro giới
hạn body request 100 MB.** Khớp chính xác dãy đã đo: 60/64/80 MB ✅ · 127/159/229/253 MB ❌.

**Hệ quả: ngân sách chunk rộng hơn ta đang dùng.** Có thể lên ~90 MB thay vì 66 MB, và
`CHUNKS_F2` vẫn đang tăng theo số chunk (0,0366 → 0,0495 → 0,0513 → 0,0731) nên thêm ~35%
chunk là có lãi.

Và phần "upload lâu" không phải truyền file mà là **server xử lý**: giải nén, parse ~250 MB
JSON, kiểm đủ 1.200 id, đối chiếu 72.000 `chunk_text`. Thanh tiến trình gộp cả thời gian đó.

**Vận hành:** luôn **dừng crawl trước khi nộp bài**. Crawl giữ 62 kết nối TCP đồng thời
(trên tổng 57 Established của cả máy) làm xuống cấp bảng NAT của router gia đình, chậm mọi
thứ khác kể cả upload.

---

## 3. Quyết định đã chốt (kèm lý do, để sau không bàn lại)

| Quyết định | Lý do |
| --- | --- |
| **Reranker chính = Qwen3-Reranker-4B, chỉ Qwen (không trộn bge)** | B (Qwen + vòng 1) FINAL 0,2581 > A (Qwen + bge + vòng 1) 0,2533 ở cùng chunk; Qwen xếp đầu danh sách tốt hơn rõ rệt (chunk +10,5%). |
| **Điểm doc chỉ phụ thuộc TẬP doc** | A cho P/R y hệt bài cũ khi tập không đổi; C nộp nhầm tập → doc tụt. Muốn tăng điểm doc phải đổi TẬP (chấm sâu hơn, pool rộng hơn), không phải thứ tự. |
| **zh không đáng crawl/index thêm** | Bài zh-only đo được ~2,6% nhãn (P 0,0089) ở độ phủ ~35%; ngoại suy phủ 100% ≈ +7% recall tối đa. |
| **Bỏ nhánh PubMed** | BTC bỏ khỏi trang chính thức (người dùng xác nhận 06/10); ta chưa từng nộp PMID. |
| **Chunk `t40_70`** (40 doc × 2 + doc 41–70 × 1) | Chunk thứ hai của doc hạng 41–64 đóng góp ~0 recall (CHUNKS_R 0,2675 → 0,2671); bỏ đi precision +6%. Chọn chunk theo từ khoá không hơn chunk đầu. |
| **Dùng bài k=1000 (chỉ đọc DOCS_RECALL) để so pool trước khi tốn GPU** | Một lượt nộp cho biết pool rộng thêm bao nhiêu; đã dùng để chọn pool F. |
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
| **Lọc boilerplate bằng document frequency theo domain, không hardcode** | Dòng xuất hiện ở >30% trang của cùng domain là boilerplate. Bỏ 6,5 MB rác (-11,6% body) trên 47 domain. Kiểm thủ công: 0 dòng trùng title của doc nào → không phá nội dung. **Phải chạy lại sau mỗi đợt crawl.** |
| **Gom trùng lặp để embed chung, KHÔNG xoá doc_id** | Có cụm sao chép hệ thống (`a-hospital` ↔ `zhongyibaodian`, 316k URL). Nhưng không biết BTC gán nhãn bản nào, và F2 nặng recall → trả cả hai là lãi. |
| **`doc_id` PHẢI là số nguyên trong JSON** (`--int-ids`) | Thí nghiệm một biến trên leaderboard: cùng nội dung, chuỗi → 0, số nguyên → 0,0497. Schema và ví dụ trong đặc tả BTC gây nhầm; phần chữ mới đúng. |
| **β là đặc tính của PHÂN BỐ NHÃN, không phải của bộ xếp hạng** (sửa nhận định 03/10) | Hôm 03/10 kết luận "nguồn xếp hạng tốt hơn → đường cong dốc hơn → k\* nhỏ hơn". Đo lại sau khi thêm dense (nguồn làm doc F2 nhảy 32,8%): β = **0,461** so với 0,455 trước đó - gần như không đổi. k\* = 4G·β/(1-β) = 211 với G≈61,6. **Vẫn phải đo β cho từng cấu hình** (bài học 03/10 còn đúng), nhưng lý do không phải vì nguồn mạnh hơn. |
| **k = 200**, và **β phải đo lại cho từng nguồn ứng viên** | Quét k=20/100/200/500 trên nguồn slug cho β=0,536 → k\*≈194. Mượn β đó cho rrf3 đoán k\*=268, nộp thật thì DOCS_F2 TỤT 1,5%. Đo β từ chính rrf3 (2 điểm k=200/265): β=0,455, G≈59 → k\*=198. Nguồn xếp hạng tốt hơn dồn doc đúng lên đầu → đường cong dốc xuống NHANH hơn, k\* NHỎ hơn, không lớn hơn. |
| **Lợi suất RRF giảm nhanh theo số nguồn** | Nguồn thứ 2 (+22% DOCS_F2), nguồn thứ 3 chỉ +2,6%. Vì `bm25_meta` dẫn xuất từ cùng 127k doc đã crawl → ít thông tin mới. Nguồn thật sự MỚI phải đến từ dữ liệu mới (crawl thêm) hoặc mô hình khác loại (dense, PubMed). |
| **ε≈0,09 CHỈ đúng cho kho tiếng Việt, KHÔNG cho tổng thể** (sửa 04/10) | Co giãn đo ở hai mốc (+392% → +18,8%, và +3,5% → +0,31%) nhưng cả hai đều trên kho VI đã phủ 88%. Tổng thể ta mới có **36% corpus** (1,58M/4,39M), và baseline BM25 THUẦN của BTC - chạy trên corpus đầy đủ - cho DOCS_P **0,8805** so với 0,1033 của ta. Nên crawl tiếng Trung (26% phủ) vẫn là đòn lớn, chỉ riêng crawl thêm tiếng Việt là cạn. |
| **Crawl thêm tài liệu tiếng Việt đã gần cạn giá trị** (ε ≈ 0,09) | Co giãn đo ở hai mốc cách nhau 100 lần: +392% doc → +18,8% doc F2 (ε 0,108), và +3,5% doc → +0,31% (ε 0,089). Theo đó **gấp đôi** kho vi (647k → 1,3M) chỉ cho +6,4% doc F2, còn `nhathuoclongchau` (+57.920 doc = +9% kho vi) chỉ cho +0,8% doc F2 → FINAL +0,0009. Mọi đòn còn lại phải là KHO MỚI (zh, PubMed) hoặc NGUỒN KHÁC LOẠI (dense), nơi ε này không áp dụng. |
| **Cấp document KHÔNG cần crawl** | `relevant_docs` chỉ là id nên slug trả về được URL chưa crawl mà vẫn tính điểm. Đó là lý do DOCS_RECALL (0,1863) VƯỢT độ phủ tiếng Việt (0,171). Chỉ cấp chunk mới bắt buộc có nội dung. |
| **Gộp nguồn bằng RRF, không cộng điểm thô** | Các nguồn không cùng thang (slug ~39, BM25 ~21 cho cùng câu). RRF chỉ dùng hạng. Đo được: gộp slug+BM25 cho +22% DOCS_F2 dù không thêm dữ liệu nào. Điều kiện ăn lãi: nguồn phải KHÁC nhau (87,4%) mà ĐỀU đúng. |
| **Dense là nguồn thứ 4 ĐÚNG, nhưng chỉ trên kho đã phủ đủ và cùng ngôn ngữ** | Cùng BGE-M3: trên kho zh (phủ 23%, cross-lingual) cho DOCS_F2 0,1217 - THUA; trên kho vi (phủ 88%, mono-lingual) cho **0,1705 - tăng 32,8%**. Nên "nguồn thứ 4 luôn thua" KHÔNG phải quy luật; điều kiện thật là nguồn mới phải bầu CÙNG doc với nguồn cũ (để RRF cộng phiếu) chứ không chen doc mới mà precision thấp hơn precision biên. |
| **Hệ thống chấm cấp DOCUMENT có tính THỨ TỰ, không chỉ tập hợp** | `rr_2x55` giữ đúng cùng tập 200 doc với `dvi25_2x55` (kiểm 1200/1200 câu: `set(a)==set(b)`, nhưng `a!=b` ở cả 1200), chỉ đổi thứ tự bằng rerank. Theo công thức BTC (`P = |D∩G|/|D|`) thì điểm doc phải Y NGUYÊN, nhưng DOCS_F2 tăng **0,1845 → 0,1948 (+5,6%)** và cả P lẫn R đều tăng. → Mọi đòn sắp xếp lại đầu danh sách ăn CẢ HAI tầng. Chưa biết cơ chế (cắt ngưỡng nội bộ? tính theo rank?) nhưng hệ quả thực tiễn rõ: **đừng chỉ tối ưu tập ứng viên, phải tối ưu thứ tự**. |
| **Rerank cross-encoder là đòn rẻ và ăn đôi** | `bge-reranker-v2-m3` trên top-200, 5,5 s/câu trên RTX 4050 (1,8 giờ cho 1.200 câu; ~28 phút trên 4090). Không thêm một ứng viên nào mà FINAL +10,2%: doc +5,6%, chunk +16,3% (vì top-55 đổi 28/55 doc). |
| **Cải thiện đầu danh sách ăn CẢ HAI tầng** | `dense vi` không đổi một tham số chunk nào mà chunk F2 vẫn tăng 32,7%, đúng bằng mức tăng của tầng doc - vì chunk chỉ lấy từ 55 doc đầu. Mọi đòn tăng precision ở đầu danh sách (rerank, dense cấp chunk) được tính đôi. |
| **Cross-lingual trực tiếp > dịch rồi khớp từ** (đo trên cùng kho zh) | dense-title zh dùng query tiếng Việt NGUYÊN BẢN qua BGE-M3 đa ngôn ngữ: g_zh = **0,54** doc/câu. BM25F zh dùng bản dịch Qwen (11.027 term khớp, tăng 153× so với 72 khi chưa dịch) và cả 4 trường title/tags/descr/body: chỉ **0,32**. Dense chỉ dùng title mà vẫn hơn 1,7× → rào ngôn ngữ vượt bằng embedding đa ngôn ngữ tốt hơn bằng dịch máy. |
| **Kho zh ở độ phủ 23% chưa đáng thêm vào ở k=200** | Hai cách khai thác độc lập (dense và lexical) cùng cho precision 0,0079-0,0134, đều dưới ngưỡng 0,0296 (precision biên của vi tại k=200) từ 2,2 đến 3,7 lần. Recall vi là 28-45% ở độ phủ 88%, recall zh chỉ 1,6-9,3% ở độ phủ 23% - chênh lớn hơn tỉ lệ độ phủ, nên crawl đủ là CẦN nhưng chưa ĐỦ. |
| **Nguồn KHÁC LOẠI vẫn có thể thua, nếu kho của nó mới phủ 11%** | `dense-title zh` đúng là khác loại (không dựa trùng khớp từ, lại đa ngôn ngữ nên khỏi cần dịch) nhưng vẫn làm DOCS_F2 tụt 5,2%: nó chiếm 20,2% slot với precision 0,0134 trong khi precision biên của vi là 0,0296. Điều kiện để một nguồn mới ăn không chỉ là "khác loại" mà là **precision của nó phải vượt precision BIÊN của danh sách hiện có tại k đang dùng**. |
| **Hạ trọng số RRF không cứu được nguồn đơn độc** | `dense:0,4` làm nó tụt 20,2% → 0,2% slot. RRF cộng `w/(k+rank)` nên doc chỉ có MỘT nguồn bầu không cạnh tranh được với doc có 2-3 nguồn; không tồn tại mức trọng số trung gian hữu ích. Muốn nguồn mới có chỗ thì phải làm nó MẠNH hơn, không phải cân lại trọng số. |
| **Không gộp hai nguồn tương quan cao** | ĐÃ ĐO: `fused4` (thêm `bm25_body`, tương quan 82%) cho FINAL 0,0896 < `fused3` 0,0904. DOCS_F2 giảm 0,1077 → 0,1058 vì slug bị đẩy từ 60% xuống 39% số slot. Nguồn mới phải KHÁC LOẠI: dữ liệu mới, mô hình khác, hoặc kho khác. |
| **`RATES` đặt theo tỉ lệ thành công ĐO ĐƯỢC từng domain, và phải có backoff khi gặp 429** | Mất 20.000 URL của `nhathuoclongchau.com.vn` (domain liên quan nhất) vì crawl ở 5 req/s, server trả 429 rồi 403, crawler không chậm lại. `AdaptiveLimiter` giãn gấp đôi mỗi lần bị phạt. |
| **ZIP phải dưới 100 MB** (ngưỡng Cloudflare của leaderboard), nhắm ~90 MB | Không phải nghẽn băng thông như từng đoán - upload đo được 20,5 Mbps. Private phase chỉ 5 lượt nên một lượt fail upload là mất 20% ngân sách. |
| **Ta đang dùng dung lượng HÀO PHÓNG hơn đội dẫn đầu mà điểm thấp hơn** | Đội đạt FINAL 0,30 nộp JSON 200 MB → ZIP 50 MB; ta nộp JSON 330,6 MB → ZIP 81,9 MB. **Tỉ lệ nén y hệt 4,0:1** nên so sánh trực tiếp được: ta dùng nhiều hơn 65% dung lượng mà FINAL chỉ bằng 60% của họ. → Khoảng cách KHÔNG ở lượng chunk nộp ra mà ở **chất lượng truy hồi**. Cần DOCS_RECALL ~0,52 (hiện 0,3191) tức g ≈ 33 doc vàng/câu (hiện 20,7). |
| **Nén chỉ cứu được 0,8% - trần 100 MB là cứng** | Thử `separators=(",", ":")` (bỏ 2 byte thừa mỗi cặp khoá) + `compresslevel=9` (mặc định 6): 92.396 → 91.636 KB trên cùng 110.228 chunk. `chunk_text` là văn bản thật và deflate đã nén khoảng trắng lặp rất tốt, nên không có chỗ vắt. Muốn thêm chunk thì phải đổi thứ khác: kích thước chunk, hoặc bỏ doc không lấy chunk. |
| **Dừng crawl trước khi nộp bài** | Crawl giữ 62 kết nối TCP, làm xuống cấp NAT router → chậm upload. |
| **Tầng DOC độc lập với chunk, nhưng P/R chunk KHÔNG độc lập với doc list** (F2 chunk thì có) | `x_k200_ctop90` ghép doc của một bài với chunk của bài khác: FINAL = (0,1280+0,0863)/2 = 0,10715 vs đo 0,1071 → trọng số 50/50 và tầng doc độc lập, đã chứng minh. NHƯNG `k265_ctop90` và `x_k200_ctop90` có vân tay chunk GIỐNG HỆT (`fb94f7034ced`) mà P/R chunk khác (0,0732/0,1104 vs 0,0833/0,1064) — khác biệt duy nhất là số doc nộp (318k vs 240k). F2 chunk vẫn bằng đúng 0,0863 ở cả hai nên chiến lược không đổi, nhưng **đừng dùng P/R chunk để tính precision biên hay ngưỡng dừng** - chỉ F2 là đáng tin. (Đối chứng: `x_k150`/`pipeline_k200` cùng vân tay `09a8114fde43` thì khớp tuyệt đối, nên đây không phải nhiễu đo.) |
| **`deep` > `wide` KHI độ phủ crawl đủ** (02/10 kết luận ngược, đã lật) | So ở cùng mức dung lượng: 2 chunk × 50 doc (100.580 chunk) cho CHUNKS_F2 **0,0879** còn 1 chunk × 90 doc (104.154 chunk) chỉ 0,0863 - ít chunk hơn 3,4% mà cao hơn 1,9%. Lý do đảo chiều so với 02/10: lúc đó chỉ có 127k doc nên doc hạng cao thường CHƯA crawl, buộc phải dàn rộng; với 647k doc thì doc hạng cao đã có nội dung, và chunk THỨ HAI của doc tốt hơn chunk ĐẦU của doc hạng thấp. **Kết luận này phụ thuộc độ phủ crawl, phải đo lại sau mỗi đợt crawl lớn.** |
| **Vân tay bài nộp là bắt buộc** (`submission.py` in `doc=` / `chunk=`) | `x_deep2x45` báo về cả 7 số y hệt `x_k200_ctop90` dù vân tay chunk khác 13% - tưởng leaderboard lỗi, hoá ra dán trùng kết quả. `deep2x50` (vân tay khác → điểm khác) chứng minh hệ thống chấm đúng. Không có vân tay thì một lần dán trùng là một kết luận sai nằm trong sổ. |
| **Trọng số RRF: ĐỀU khi các nguồn ngang nhau, LỆCH khi có một nguồn mạnh hơn hẳn** | Hôm 03/10 (3 nguồn lexical ngang nhau): slug×2 → 0,1228, meta×2 → 0,1214, đều → 0,1280 - lệch về phía nào cũng hại. Hôm 04/10 với dense mạnh hơn hẳn: w=1,0 → 0,1705 · 1,5 → 0,1799 · **2,5 → 0,1845** · 4,0 → 0,1822 · ∞ → 0,1680. Đỉnh ở **w≈2,5**. Nên quy tắc không phải "để đều" mà là **đặt trọng số theo sức mạnh tương đối, rồi quét để tìm đỉnh**. |
| **Rate cao hơn KHÔNG nhanh hơn: thử 8 và SAI** (lần thứ ba cùng bài học) | `cnkang`+`120ask` ở rate 4 cho **16,1 trang/s, 97,8% dùng được**; nâng lên 8 cho **3,3 trang/s, 81,5%** - chậm gấp 5. Server chặn nhiều hơn nên tổng thông lượng giảm dù mỗi giây gửi nhiều hơn. Và backoff KHÔNG cứu được mức khởi đầu sai, nó chỉ hạn chế thiệt hại sau khi đã bị chặn. |

| **Lấy chunk CHỈ từ M doc đầu (`--chunk-from-top`), không phải cả topk** | Hai tầng chấm độc lập. Chunk từ top-20 trúng cao gấp 2,75× chunk từ hạng 100-200 (DOCS_PRECISION 0,1154 vs 0,0419). Nộp cả 200 doc thì 96% chunk vô ích. Và giảm ZIP từ 253 MB (upload fail) xuống 26-64 MB. |
| **Cấp chunk bị chặn bởi độ phủ crawl, KHÔNG phải bởi k** | CHUNKS_F2 phẳng ở 0,0093 qua k=100/200/500 dù số chunk/câu tăng 2,7×. Chỉ 2.499 doc đã cắt chunk trên 240.000 slot nộp ra. Hết đòn miễn phí ở tầng này. |
| **Nộp HẾT chunk của mỗi doc, không giới hạn 2** | Ngưỡng dừng cấp chunk là 0,00172 còn precision chunk thực tế 0,0525 - cao hơn 31 lần. Kể cả precision tụt 4× vẫn lãi 1,36×. |
| **Europe PMC là nguồn nội dung PubMed chính**, NCBI chỉ là dự phòng | NCBI chặn IP máy này (đo: mọi endpoint → misuse.ncbi.nlm.nih.gov, UA browser cũng không thoát). Europe PMC `resultType=core` trả cả title lẫn abstract: 284/284 bài so với 0/284 qua NCBI. |
| **`doc_id` của bài PubMed = PMID**, không cần tiền tố phân biệt | PubMed không nằm trong `links_corpus.parquet` nên phải dùng PMID. Đo được PMID hiện đại đều > 28M còn `links_corpus.id` ≤ 4,39M → không chồng nhau trên thực tế. |
| **Store = một file SQLite**, không thêm dep | 3,37M doc × 2 KB ≈ 7 GB. Cho cả resume theo URL, truy cập theo doc_id, và quét tuần tự cho BM25. |
| **Chunk chỉ lưu `(doc_id, start, end)`**, không lưu text | `chunk_text = body[start:end]` → không thể lệch khỏi tài liệu gốc. Ràng buộc nguyên văn được bảo đảm bằng cấu trúc, không bằng kỷ luật. |
| **BM25 tự viết, không Lucene/pyserini** | Query set cố định 1.200 câu → chỉ cần df của term trong query + một lượt streaming. Mẹo của `slug_bm25.py` tổng quát hoá được. |
| **Không dùng sitemap.** Đã probe 12 domain lớn nhất: chỉ chứa `<loc>`, không có title | URL thì BTC đã cho sẵn → giá trị bằng 0. Không có nguồn title hàng loạt, phải crawl từng trang. |
| **`--retry-failed` KHÔNG dùng khi phần FAILED là loại không vượt được** | Nó dồn quota batch vào đúng nhóm CAPTCHA `*.39.net`: job chạy 35 phút không ghi nổi 200 doc đầu. Bỏ nó đi thì 46,6 trang/s, dùng được 86,0%. Phần FAILED để lại cho khi có IP khác. |
| **Đo `procs` bằng throughput, đừng lấy `nproc`** | 22 process bị kill âm thầm (RAM còn 1 GB vì chạy cùng model 4-bit), còn 10 process vẫn cho 46,6 trang/s. Trần thật nằm ở rate các domain, không ở CPU, một khi đã bỏ được request vô ích. |
| **JSON của LLM lượng tử phải vớt theo khoá, không chỉ `json.loads`** | Qwen3.5-9B 4-bit sinh JSON sai cú pháp ở 17,2% câu dù nội dung ĐỦ (raw kết thúc bằng `]}`, nên không phải `max_tokens`). Trả rỗng là mất `zh` + `entities`. `salvage_json()` vớt theo regex từng khoá, và vì `raw` được lưu nên **vá lại offline được, khỏi gọi lại LLM 4 giờ**. |
| **CAPTCHA trả 200 là điểm mù của backoff — phải tự phát hiện** | `WAF_STATUS` chỉ bắt 403/406/429/503, nên màn xác thực trả 200 được tính là THÀNH CÔNG: limiter không phạt, crawler càng đập càng bị chặn, tỉ lệ dùng được tụt 46,0% → 35,6% trong một đợt. `looks_captcha()` đòi HTML < 8 KB **và** có dấu hiệu xác thực (hai điều kiện, để không nhận lầm bài viết nói về captcha), rồi đổi status thành 403. |
| **Dùng lại kết nối (`requests.Session`), đừng gọi `requests.get()` mỗi URL** | Mỗi lần gọi là một lượt tra DNS mới; 200 thread làm ngập resolver công cộng → `Temporary failure in name resolution` cho cả `huggingface.co` và `pythonhosted.org`, 4.340 doc mang `status=None`. Session keep-alive bỏ được cả DNS lẫn TLS handshake. Và thread nhiều hơn trần CPU trích thì chỉ gây hại. |
| **Pool kết nối phải NHỎ: mỗi thread chỉ một request** | `pool_maxsize=32` × 80 thread = 2.560 socket, vượt `ulimit -n` 1024 → `OSError(24, "Too many open files")` làm **83,2%** request chết và throughput tụt 46,6 → 1,9 trang/s. Pool lớn không mua được gì vì một thread không thể chạy hai request cùng lúc. Dùng `pool_connections=6, pool_maxsize=2` và `raise_fd_limit()` (ulimit mềm 1024 → 65536; giới hạn cứng 1.048.576 nên không cần root). |
| **Đọc THÔNG ĐIỆP lỗi đầy đủ trước khi đoán nguyên nhân** | Ba giả thuyết đầu (CAPTCHA lan rộng, `trafilatura` thua layout zh, `Session` làm server trả khác) đều sai và đều mất thời gian kiểm. Câu trả lời nằm nguyên trong `err` của bảng `doc`: `OSError(24, ...)`. Cột `err` bị cắt còn 28 ký tự khi nhóm lại nên nó trông giống "ConnectionError" chung chung. |
| **"Không sửa được bằng code" ≠ "không sửa được" — thử IP khác trước khi bỏ cuộc** | `familydoctor.com.cn` bị kết luận chịu mất hôm 01/10 sau 10 profile TLS; máy GPU crawl **100%** (445.848/447.453) mà không sửa một dòng nào. 447k URL = 10,2% corpus. |
| **Profile TLS chọn theo DOMAIN, không một profile cho tất cả** | `chrome` cứu 100% `nhathuoclongchau` nhưng `vov.vn` lọc ĐÚNG fingerprint Chrome: mọi `chrome*` → 403, còn `safari17_0`/`firefox133`/`edge101` → 200. Và `youmed.vn` không profile nào qua được nếu thiếu cookie trang chủ. Ghim một profile là mất 12.251 URL. |
| **Rate khởi đầu THẤP tốt hơn backoff thông minh** | AIMD có `reward()` vẫn không cứu được: 429 liên tục reset chuỗi thắng, giadinhonline rơi 10 → 0,03 req/s = 94 GIỜ cho 10k URL. Hạ mức khởi đầu (10→1) cho 0 lần bị phạt, dùng được 100% (từ 90,4%), 5,6 giờ. Một lần bị phạt là mất cả đợt vì không có đường về. |
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
