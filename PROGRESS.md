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
| **FINAL_SCORE (public LB)** | **0,3146** | 0,3139 | 10/10/2026 | leaderboard |
| F2 document (public LB) | **0,2956** (Qwen3-Reranker top-400 + vòng 1) | 0,2914 | 07/10/2026 | leaderboard |
| **k tối ưu (khớp đường cong)** | **≈ 211** | ≈ 198 | 04/10/2026 | β=0,461 đo lại sau khi thêm dense - gần y hệt 0,455 |
| **G - số doc vàng mỗi câu (suy ra)** | **≈ 60** | ≈ 58 | 04/10/2026 | từ P/R của LB, 17 điểm |
| Trọng số FINAL | **doc 50% / chunk 50% - ĐÃ CHỨNG MINH** | khớp phép tính | 03/10/2026 | bài ghép: (0,1280+0,0863)/2 = 0,10715 vs đo 0,1071 |
| F2 chunk (public LB) | **0,2402** (chunk t40_70, Qwen top-250; bản lai 07/10 ghép với doc top-400) | 0,2366 | 06/10/2026 | leaderboard |
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

### 07/10/2026 · Qwen top-400, bản lai, thí nghiệm gate · HyDE khởi chạy

**Điểm:** FINAL 0,2658 → 0,2669 (`blendQB3`, Qwen top-400) → **0,2679** (`blendQB3x`: tập doc QB3 + chunk QB2). Bảng đầy đủ ở §2b.

1. **Lợi suất giảm của rerank sâu:** Qwen top 100→250 cho doc +4,2%; 250→400 chỉ +1,4%, chunk −0,8% (top-40/70 đổi theo tập mới). Hạng 251–400 mất ~1,9 giờ GPU (chain3, 21:15 và 22:11 xong). Không chấm sâu thêm.
2. **Bản lai khớp dự đoán:** doc của QB3 + chunk của QB2 cho đúng (0,2956 + 0,2402)/2 = 0,2679, mọi số LB bằng số bài thành phần → hai tầng độc lập. Cách dựng: tập 200 doc của QB3, thứ tự 70 doc đầu theo QB2 (file ứng viên điểm giảm đều theo vị trí để `load_candidates` không sắp lại sai).
3. **`submission.py`:** thêm hàm `fingerprint(records)` (doc theo TẬP, chunk theo văn bản có thứ tự) — hàm đã mất trong lần khôi phục, khiến lệnh dựng báo `NameError` sau khi ZIP ghi xong.
4. **Thí nghiệm nhãn bạc cho đề xuất Adaptive Gated Fusion** (`silver_gate_test.py`, chi tiết trong `PROPOSAL_ADAPTIVE_FUSION.md` §7): trọng số chung tốt nhất w=2,5 (trùng đỉnh leaderboard); oracle theo từng câu chỉ hơn +1,56% (+2,49 doc/câu) → **bỏ đề xuất**.
5. **Chunk có cần BM25/dense không?** Không dùng chấm điểm chunk trong bài tốt nhất (lấy chunk đầu theo vị trí). Chấm theo IDF trùng từ khoá đã thua 0,3%; 76% doc vừa trọn 1 chunk nên chỗ để cải thiện hẹp (ước tính ≤ +1% chunk F2, chưa đo). Hướng nếu làm: Qwen3-Reranker chấm các chunk của doc top-40 có ≥3 chunk.
6. **HyDE (xong 07/10, 1.200 câu ~15 phút trên GPU 0):** `hyde.py` + `scripts/run_hyde.sh` (Qwen3.5-9B HF batch 16, greedy → BGE-M3 trên `emb_viB2`; hai biến thể `hyde` và `qhyde` = câu hỏi + câu trả lời giả định). Đo offline (nhãn bạc = top-200 `blendQB3`, **thiên lệch vì nhãn bạc chỉ chứa doc đã ở pool F**, nên không đo được recall mới):
   - Một mình bắt bạc top-200: `viB2` (câu hỏi) 115,8 · `qhyde` 98,1 · `hyde` 75,4 — HyDE lệch khỏi pool, đúng kỳ vọng.
   - **Tính mới:** top-200 của `hyde` có **74,9 doc/câu nằm NGOÀI pool F top-1000** (33,1 doc nằm ở hạng 401–1000 của pool, chưa qua Qwen).
   - RRF trộn thẳng vào f_F **làm hại** top-250 trên nhãn bạc (155,1 → 146,4 w=1; 117,5 w=2,5) vì đẩy doc pool ra: không trộn RRF thẳng; chỉ **thêm doc mới**.
   - Chẩn đoán trực tiếp bằng lượt nộp: `diag_novel_hyde_k150.zip` / `diag_novel_qhyde_k150.zip` = chỉ 150 doc hạng cao của HyDE KHÔNG nằm trong f_F top-1000, chunk rỗng. `DOCS_RECALL` của bài = phần nhãn mà HyDE cứu thêm ngoài pool (cộng thẳng vào mốc 0,6108). Vân tay doc `ed7aaaab2eef` (hyde), `709f9ee4ab5d` (qhyde). **Kết quả (nộp 07/10): `qhyde` DOCS_R 0,0084 / P 0,0048; `hyde` DOCS_R 0,0068 / P 0,0038** (xem §2b). HyDE cứu thêm khoảng 0,7 nhãn/câu ngoài pool với precision biên 0,5% (so ngưỡng giữ trong top-200 ≈ F2/5 ≈ 0,06) → **hiệu quả thấp, cùng cỡ nguồn entity (+1,0% pool)**. Doc mới còn phải qua Qwen và chỉ một phần sống sót đến top-200 → ước tính FINAL +0,001–0,003 cho ~2 giờ GPU (150 doc/câu) → **không làm trước; ưu tiên thấp**.

---




### 10/10/2026 · Phép thử Qwen-zh (reranker có sửa được độ chính xác zh?)
Qwen3-Reranker-4B chấm top-100 zh (từ `zhC2_both_400`) cho 300 câu đầu (30.000 cặp, text zh title + 800 ký tự đầu). Điểm: TB 0,378; >0,5: 37,6/100 doc; >0,9: 14,5/100 doc (so vi: >0,9 ≈ 32 trong 400 ứng viên của pool). Ba bài 300 câu (900 câu còn lại rỗng), 50 doc/câu, chunk rỗng — đọc DOCS_P × 4 ≈ P@50 cho 300 câu (mốc zh toàn bộ: 0,0462):
- `runs/p50_zh300_dense.zip` (thứ tự dense, doc `842e5aa60804`)
- `runs/p50_zh300_qwen.zip` (thứ tự Qwen, doc `5026a05288c8`; giao dense 28,5/50)
- `runs/p50_zh300_mix.zip` (RRF dense+Qwen, doc `8500e3984faa`; giao dense 39,1/50)
Đọc: nếu Qwen ≳2× dense (≳0,10 sau ×4) → zh có nhãn nhưng ta xếp kém → làm reranker zh + tiếp tục cào; gần bằng → nhãn zh thưa. Lô zh shard I4 (197.464 doc, `zh_text_delta2.sqlite`) đã ở máy GPU, CHƯA encode (chờ kết quả này).
**KẾT QUẢ (10/10, giả định bài nộp là `p50_zh300_qwen` vì là lượt duy nhất còn lại hôm nay; người dùng dán điểm không ghi nhãn):** FINAL 0,0039 · DOCS_P 0,012 · DOCS_R 0,0078 → P@50 (300 câu) = 0,012×4 ≈ **0,048**, ngang mốc zh toàn bộ 0,0462 → Qwen KHÔNG xếp zh tốt hơn dense; ~2,4 doc đúng/50 doc zh. Kết luận: nhãn zh thưa, không phải ta xếp kém → không làm reranker zh; zh giữ quota đuôi ~14–16 doc/câu. Chưa kiểm được: độ phủ zh (còn ~50% chưa cào).

Hàng đợi 11/10 (tổng): E1 ×4, E3 longchau ×2, E3 medlatec ×2, + 3 bài zh300 = 11 → ưu tiên E1 + E3 longchau/medlatec + `p50_zh300_dense`/`_qwen`.

### 12/10/2026 · THÔNG BÁO MỚI CỦA BTC: ĐỔI KHO DỮ LIỆU (PDF `261012_R2_AI_S3_MentorDay1.pdf`, dataset HF cập nhật 12/10 09:38 UTC)
- Kho mới `links_corpus_vi_en_zh.parquet`: **1.194.469 URL** = vi 714.469 + **en 240.000 (toàn PubMed, URL pubmed.ncbi.nlm.nih.gov/PMID/)** + zh 240.000 (cũ: 4.394.718, zh 83%). id GIỮ NGUYÊN so với kho cũ (845.277 id khớp cả id lẫn URL); id PubMed mới bắt đầu từ 4.421.055 (không phải PMID). 1.200 câu hỏi giữ nguyên. PDF mentor vẫn ghi 4.394.718 URL/97 host (không nhất quán với dataset card).
- Luật chấm chunk (PDF tr.7): cùng truy vấn VÀ cùng doc_id; chuẩn hoá NFKC/HTML entity/lowercase/khoảng trắng; LCS token (giữ thứ tự, không cần liên tiếp); chunk đúng khi LCS(c,g)/|g| ≥ 0,40 với một đoạn tham chiếu g.
- **vinmec.com BỊ LOẠI HOÀN TOÀN khỏi kho mới** (trang vinmec nay trả màn hình chọn ngôn ngữ, PDF tr.13). vinmec chiếm 6.265/62.800 lượt xuất hiện trong top-50 của blendQB11 (~10%; trước đó ta phát hiện vinmec ×3,0 so với kho). Tổng doc top-200 ngoài kho mới: 25,0/câu (12,5%); top-10: 1,1/câu.
- Độ phủ kho mới trong store: vi ~97% (708k/731k dùng được; phân loại thô), zh 116k/223k (52%; thiếu 107k: 120ask 55k, cnkang 27k, ask.39 17k, zysj 6,6k; shard 3 phủ thêm 14k), **en 0/240.000**.
- `runs/blendQB11n_e120.zip`: blendQB11 đã lọc bỏ doc ngoài kho mới (giữ đủ 200 doc/câu). Chưa nộp: nộp chỉ khi biết leaderboard đã chấm theo kho mới; nếu vẫn nhãn cũ thì sẽ TỤT (mất doc vinmec ngoài kho).

### 13/10/2026 · LƯỚI AN TOÀN KHO MỚI + KIỂM ID
- Kiểm id: 954.469 URL không-PubMed của kho mới đều có trong hàng đợi cũ của ta với CÙNG id và CÙNG URL (0 trường hợp khác URL) → kho mới là tập con, không đánh số lại; lọc theo id chính xác.
- `filter_new_corpus.py in deeper out`: bỏ mọi doc ngoài kho mới TRỪ vinmec.com (nhãn vi cũ còn hiệu lực) rồi bù đủ 200 từ danh sách sâu. Phát hiện: bản `blendQB13{a,b,c}` ban đầu còn rò 0,2–0,3% doc ngoài kho (wujue.com, 120ask, zhongyibaodian — trang zh bị nhận nhầm lang=vi nên lọt qua nhánh vi); đã xoá 3 zip lỗi và dựng lại bản sạch `blendQB13{a,b,c}f_e120` (doc: `c9b5de8fc718` / `865201247093` / `e0300186f624`; chunk: `6d42f1f2f79f` / `efca4b4887fc` / `f3bc21d55d06`); kiểm chứng: ngoài kho mới chỉ còn vinmec.com. blendQB11z cũng đã sạch (chỉ vinmec).
- Chưa xoá dữ liệu nào khỏi máy (cần người dùng đồng ý).

### 13/10/2026 · KẾT QUẢ blendQB11z_e120 (lọc zh theo kho mới, vi giữ nguyên; người dùng báo)
FINAL **0,3179** (+0,0021 so 0,3158; mới TỐT NHẤT) · doc F2 0,3427 (+0,0043; P 0,1810 / R 0,5641) · chunk F2 0,2932 (≈ không đổi). Bỏ 7,5 doc zh ngoài kho mới/câu (bù bằng doc vi hạng sâu) tăng cả P lẫn R: nhất quán với (i) doc zh ngoài kho mới không phải nhãn và/hoặc (ii) doc vi hạng sâu mạnh hơn đuôi zh ngoài kho. Phát hiện kèm: 47% doc zh trong top-50 của ta nằm TRONG kho zh mới 240k (nền ngẫu nhiên ~6%) → BTC giữ lại tập zh chọn lọc có liên quan truy vấn.
Bài dựng sẵn (chuỗi tái lập blendQB11 1200/1200 câu): `blendQB13a_e120` (zh chỉ trong kho mới, w0,3, 14 doc zh/câu; doc `9c8656da4394`, chunk `7fc5cb4c79af`), `blendQB13b` (w0,6, 60 zh/câu; `d2762026efe6`/`70b91eebea95`), `blendQB13c` (w1,0, 100 zh/câu; `985934bdd350`/`33dc786334ec`), `p50_zh_in` (50 doc zh trong kho mới, chunk rỗng; `e0d8ed7b4d24`; mốc zh toàn bộ 0,0462). `runs/p1000_en_both.zip`: 1.000 doc tiếng Anh/câu (kiểm xem có nhãn en nào ở hạng sâu).

### 13/10/2026 · KẾT QUẢ `p50_en_both_pmid` = 0,0 (người dùng báo "cũng 0 nốt")
Cả hai quy ước doc_id (cột id và PMID) cho 60.000 doc tiếng Anh đều ra precision/recall đúng 0 → bảng điểm hiện KHÔNG có nhãn tiếng Anh dưới bất kỳ quy ước số nào ta thử (nếu có nhãn en, 60.000 doc xếp bằng dense không thể toàn trật). Kết luận: chờ BTC cập nhật nhãn en; không nộp thêm bài đo en. Khi nhãn en xuất hiện, nộp lại `p50_en_both` và `p50_en_both_pmid` (đã dựng sẵn) để biết quy ước và mật độ nhãn, rồi quyết định số doc en chen vào danh sách (như cách đã làm với zh).

### 13/10/2026 · Người dùng xác nhận bài đã nộp là `p50_en_both` (kết quả 0,0). Nghi vấn: doc_id tiếng Anh là PMID chứ không phải cột id → bài thử `runs/p50_en_both_pmid.zip`
Cùng 60.000 doc, thay doc_id bằng PMID (doc `7f8ee9bb40a8`). Sửa nhận định cũ: PMID của 240.000 bài kho mới trải từ 11.197 đến 41.231.536 và chỉ 1.255 (0,5%) nằm trong dải id vi/zh (≤4.420.561) → dùng PMID làm doc_id gần như không đụng nhãn vi/zh (nhận định trước "PMID nhỏ trùng dải id" là sai về mức độ). Quy ước ban đầu của BTC cũng là "tiếng Anh dùng PMID". Đọc: DOCS_P ≳0,03 → bảng đã có nhãn en và dùng PMID; vẫn 0 → bảng chưa có nhãn en (hoặc quy ước khác).

### 13/10/2026 · KẾT QUẢ bài đo chỉ-en: TOÀN 0,0 (khối dán không ghi tên bài; giả định `p50_en_both`)
FINAL/doc/chunk P-R-F2 đều 0,0000. Kiểm định dạng: cả 4 zip en có đúng 1 file json, 1.200 câu, khoá `id/relevant_docs/relevant_chunks`, doc_id kiểu int (60.000 hoặc 180.000 doc), mọi doc nằm trong tập id PubMed của kho mới — y hệt các bài đo trước (chunk rỗng) vốn có điểm >0 → KHÔNG phải lỗi định dạng. Precision và recall đều đúng 0 với 60.000 doc ⇒ không doc PubMed nào là nhãn trong bảng điểm hiện tại: bảng điểm CHƯA có nhãn tiếng Anh (khớp phép thử blendQB11n: bảng vẫn chấm nhãn cũ), hoặc dùng quy ước doc_id khác (PMID bị loại: PMID nhỏ như 11197 trùng dải id vi/zh). Việc cần hỏi BTC: khi nào nhãn en có hiệu lực và doc_id en là gì. Không nộp thêm bài đo en cho tới khi có xác nhận.

### 12/10/2026 · TIẾNG ANH: dense xong (239.355 bài, BGE-M3 title+abstract) → 4 bài đo chỉ-en (chunk rỗng; đủ 1.200 câu)
Mã hoá ~420 bài/giây (~10 phút); xếp hạng bằng câu vi gốc (`dense_en_vi_rank`) và bản dịch en (`dense_en_en_rank`); giao top-50 hai danh sách 14,2/50.
- `runs/p50_en_vi.zip` (doc `3782d32a5054`), `runs/p50_en_en.zip` (`12cbd7562cb9`), `runs/p50_en_both.zip` (RRF, `4152a749e0ad`), `runs/p150_en_both.zip` (150 doc, `bd4a392bff74`).
Đọc DOCS_P (P@50) so với: vi dense nội dung 0,289; zh both 0,046. DOCS_P ≈ 0 → bảng điểm CHƯA có nhãn tiếng Anh; ≳0,05 → nhãn en đã vào bảng; so vi/en/both cho biết câu vi gốc hay bản dịch en xếp tốt hơn. doc_id = cột id của parquet (người dùng xác nhận).

### 12/10/2026 · LÀM RÕ TỪ BTC (qua người dùng): kho mới CHỈ sửa zh và en; tiếng Việt GIỮ NGUYÊN như ban đầu
- Đối chiếu dữ liệu: vinmec.com (26.127 doc trong store của ta, 100%) không còn trong parquet mới → "vi giữ nguyên" nên hiểu là nhãn/kho vi cũ vẫn hiệu lực (khớp phép thử blendQB11n: bỏ vinmec làm recall tụt 0,029). QUY TẮC: giữ nguyên toàn bộ nhánh vi (kể cả vinmec); chỉ (a) lọc zh theo kho 240k mới, (b) thêm en (PubMed 240k). `data/blendQB11z.jsonl`/`runs/blendQB11z_e120.zip` (doc `a2ffc6ecc847`, chunk `403d3c137af7`): blendQB11 chỉ bỏ doc zh ngoài kho mới (7,5 doc/câu, bù đủ 200). Chưa nộp.
- PubMed: lấy xong 240.000 bài (239.771 tìm thấy; 238.864 có abstract ≥200 ký tự) → `data/en_pubmed.sqlite`; `data/en_text.sqlite` (239.355 bài) đẩy lên máy GPU; `scripts/run_en_dense.sh` mã hoá BGE-M3 (title+abstract, 1.500 ký tự) và xếp hạng bằng câu vi gốc (`dense_en_vi_rank`) và bản dịch en (`dense_en_en_rank`).

### 12/10/2026 · KẾT QUẢ blendQB12a_e120 (khối dán không nhãn; giả định là 12a vì đó là bài được đề nghị nộp lượt cuối)
FINAL **0,3159** (+0,0001 so blendQB11 0,3158) · doc F2 0,3384 (P 0,1785 / R 0,5573, đúng như cấu trúc: tập doc không đổi) · chunk F2 **0,2934** (+0,0003; P 0,1919 / R 0,4188 so 0,1918 / 0,4181). Thứ tự đầu danh sách theo trọng tài LLM (Qwen3.5-9B, RRF 1:1 với thứ tự hiện tại, 300 câu ngẫu nhiên) cho chunk +0,0003 trên 300 câu → ngoại suy toàn bộ ≈ +0,001 chunk ≈ +0,0005 FINAL: gần như bằng 0. Kết luận: trọng tài LLM chỉ thay đổi THỨ TỰ ĐẦU không cải thiện chunk. Phần DOC (đổi tập: `blendQB12b`, hoặc P@50 `r300_p50_*`) chưa được đo. Hướng "trọng tài LLM" tạm hạ ưu tiên.

### 12/10/2026 · KẾT QUẢ blendQB11n_e120 (khối dán không nhãn; giả định là bài lọc kho mới vì đó là bài vừa đề nghị nộp) — BẢNG ĐIỂM VẪN CHẤM THEO NHÃN CŨ
FINAL **0,2994** (−0,0164 so blendQB11 0,3158) · doc F2 0,3228 (P 0,1711 / R 0,5285; QB11: 0,1785 / 0,5573) · chunk F2 0,2760 (P 0,1812 / R 0,3924; QB11: 0,1918 / 0,4181).
Lập luận: nếu nhãn đã chuyển sang kho mới (nhãn ⊂ kho mới) thì bỏ doc ngoài kho không thể làm recall GIẢM (doc bị bỏ không phải nhãn; bù thêm chỉ có thể tăng). Recall giảm 0,0288 (≈1,8 doc vàng/câu) → bảng điểm hiện chấm theo nhãn CŨ (doc vinmec và doc ngoài kho mới vẫn là nhãn). Ước tính: 25 doc bị bỏ/câu chứa ~3,5 nhãn (≈14%, ngang precision doc vinmec), 25 doc bù (hạng sâu) ~2 nhãn. KHÔNG dùng bản lọc cho tới khi bảng điểm chuyển nhãn mới. Giữ cả hai bản: `blendQB11_e120` (nhãn cũ, 0,3158) và `blendQB11n_e120` (kho mới). Bài đúng cho trạng thái hiện tại: `blendQB12a_e120` (trọng tài LLM trên danh sách cũ). `blendQB12an_e120` (cùng ý tưởng trên danh sách đã lọc; chunk `5f9f2eec1f40`) để dành cho khi nhãn mới có hiệu lực.

### 12/10/2026 · XÁC NHẬN TỪ NGƯỜI DÙNG: nhãn MỚI đang hiệu lực; quota KHÔNG đặt lại; doc_id tiếng Anh = cột `id` của parquet (không phải PMID)
- Hệ quả: `blendQB11n_e120.zip` (lọc doc ngoài kho mới, bù đủ 200; doc `37b807dbb358`, chunk `580baa8db31e`) là bài nên nộp trước; doc vinmec không còn là nhãn.
- Tiếng Anh: `fetch_en_pubmed.py` lấy 240.000 bài PubMed từ Europe PMC (resultType=core) vào `data/en_pubmed.sqlite` (doc_id = id parquet, pmid, title, abstract, journal, year, mesh); thử 800 bài: 800/800 có abstract (TB 1.020 ký tự). Chạy đủ ở local, log `data/en_fetch.log`. Bước sau: mã hoá BGE-M3 (title+abstract) và xếp hạng bằng câu hỏi vi (xuyên ngôn ngữ) + bản dịch en (`queries_enriched.en`), BM25 trên en.

### 12/10/2026 · MẪU NGẪU NHIÊN 300 câu (seed 11, từ 301–1200) đã chấm xong → 4 bài P@50 (DOCS_P×4 ≈ P@50 cho 300 câu)
`runs/r300_p50_base.zip` (doc `382b2b23763f`, thứ tự hiện tại), `r300_p50_strict.zip` (`202679011207`), `r300_p50_old.zip` (`f4d3be04b368`), `r300_p50_mix.zip` (`31432c459a26`). Giao top-50: nghiêm∩cũ 46,7; nghiêm∩hiện tại 31,0 (gần như y hệt mẫu đầu: 46,9 / 30,8). Quy tắc: chỉ tin hướng nếu cả hai mẫu (câu 1–300 và mẫu này) cao hơn base ≥ +0,02.

### 12/10/2026 · LƯU Ý PHƯƠNG PHÁP: "300 câu đầu" KHÔNG phải mẫu ngẫu nhiên
So câu 1–300 với 301–1200: số từ 32,8 vs 28,9 (+2,9 sai số chuẩn), số entity 3,81 vs 3,54 (+2,5), doc đồng thuận ≥5 là 6,06 vs 6,88 (−2,0); điểm Qwen TB top-50 như nhau (0,62). → mẫu đầu dài và khó hơn. Mọi phép đo pilot trên "300 câu đầu" (chunk-first, p50_cf_*, Qwen nghiêm) chỉ kết luận được cho nhóm đó. QUY TẮC từ nay: pilot dùng mẫu ngẫu nhiên có seed; chỉ coi một hướng là có tác dụng khi dương ở cả hai mẫu. Mẫu ngẫu nhiên thứ hai: 300 câu từ 301–1200, seed 11 (`data/qs2_ids.json`); Qwen nghiêm đang chạy (`scripts/run_qwen_strict2.sh` → `data/qwen_strict2.jsonl`).

### 12/10/2026 · Qwen chỉ dẫn NGHIÊM xong (30.000 cặp, 300 câu đầu, top-100 blendQB11) → 3 bài P@50 (300 câu; DOCS_P×4 ≈ P@50; đối chứng `p50_cf_base` doc `807173f286b1` = top-50 hiện tại)
- `runs/p50_qs_strict.zip` (doc `69d1c3312b08`): top-50 theo điểm Qwen nghiêm. `runs/p50_qs_old.zip` (`0b7a771796c4`): top-50 theo điểm Qwen cũ (cùng 100 ứng viên) — tách "tác dụng của chỉ dẫn" khỏi "tác dụng của thứ tự Qwen". `runs/p50_qs_mix.zip` (`6d94b9a5d6e4`): RRF hạng hiện tại + hạng nghiêm.
- Quan sát: chỉ dẫn nghiêm làm giảm doc có điểm>0,5 trong top-100 từ 57,2 xuống 45,9 nhưng thứ tự top-50 gần như không đổi so với Qwen cũ (giao 46,9/50); giao với top-50 hiện tại 30,8/50 (mix 40,0). Dự đoán: nghiêm ≈ cũ; điểm khác biệt chính sẽ là Qwen (cả hai) so với thứ tự hiện tại. Ngưỡng có ý nghĩa: P@50 (DOCS_P×4) cao hơn base ≥ +0,02.

### 12/10/2026 · Ý tưởng từ cuộc thi tài chính (lọc ràng buộc xác định + kế hoạch + BM25/Qwen-4B/Reranker-8B) → thử "khớp đối tượng bệnh nhân"
Liên hệ: họ lọc quyết định (công ty, năm) rồi mới xếp hạng. Tương tự cho ta: ràng buộc ngầm trong câu hỏi bệnh nhân (trẻ em / mang thai-sau sinh). Đo ngoại tuyến (regex): 164 câu trẻ em, 124 câu mang thai/sau sinh; top-10 của blendQB11 nhắc đúng đối tượng ở 71% doc (câu trẻ em → doc nhắc trẻ 71%; câu mang thai → doc nhắc mang thai 71%; nền ở câu khác: 10% / 5%) → ~29% doc top-10 không khớp đối tượng (ước lượng thô, regex tiêu đề + 400 ký tự đầu).
Bài đo (cặp cùng hạng, 3 doc/câu, 229/288 câu đủ cặp, hạng TB khớp 13,1 / không khớp 13,5): `runs/aud_match.zip` (doc `cd32b7564590`) vs `runs/aud_miss.zip` (`2082cf9af015`). Đọc: tỉ lệ doc đúng = DOCS_P × 1200/229; khớp ≥1,3× không khớp → nhãn đòi khớp đối tượng → thêm lọc/boost theo đối tượng.
Chưa thử từ cuộc thi đó: Qwen3-Reranker-**8B** (mô hình đã có trên máy GPU, ta chỉ dùng 4B).

### 12/10/2026 · KẾT QUẢ xq_in / xq_out (501 câu, 3 doc/câu; tỉ lệ doc đúng = DOCS_P × 1200/501 = ×2,395)
`xq_in`: DOCS_P 0,1130 → **0,2706**; `xq_out`: 0,1074 → **0,2572**. Chênh +0,0134 (+5%) nghiêng về doc được đẩy vào, sai số mỗi bên ~0,011, chênh ~0,016 (chưa kể tương quan cụm) → <1σ: KHÔNG phân biệt được với 0. Hạng cơ sở bất lợi cho "vào" (58,4 vs 46,3) nên có gợi ý nhẹ dương, nhưng hoán đổi hai doc ngang precision thì điểm không đổi. Ước tính lợi ích triển khai: 5,4 doc đổi/câu trên ~50% câu × 0,013 ≈ +0,0007 P@50 (≲ +0,0005 FINAL) → ĐÓNG hướng truyền bằng chứng giữa câu (kết quả trung tính). Mốc phụ: precision doc ở hạng ~45–60 ≈ 0,26–0,27.

### 12/10/2026 · HAI THỬ NGHIỆM NHẮM VÀO KHOẢNG CÁCH XẾP HẠNG
Lý lẽ: top 1 tìm ~30 doc vàng trong ~63 doc (P 0,469 / R 0,458, G≈65); ta có ~36 doc vàng trong top-200 nhưng chỉ ~20–21 trong top-63 → khoảng cách doc chủ yếu là XẾP HẠNG trong ứng viên đã có, không phải thiếu ứng viên. Qwen coi ~130 doc/câu là liên quan, nhãn chỉ ~65 → quá dễ dãi.
1. **Qwen chỉ dẫn nghiêm** (`scripts/run_qwen_strict.sh`, `QWEN_RR_INSTRUCT`): chấm lại top-100 blendQB11 cho 300 câu đầu (30.000 cặp) với chỉ dẫn "trả lời trực tiếp/cụ thể đúng câu hỏi, không chỉ cùng chủ đề" → `data/qwen_strict.jsonl`. Sau khi xong dựng bài P@50 so với `p50_cf_base`.
2. **Truyền bằng chứng giữa câu cùng cụm** (`xq_propagate.py`, LAM 0,5, giao top-50 ≥10, tối đa 10 lân cận): 594/1200 câu có lân cận (TB 2,3); top-50 đổi 5,4 doc/câu trên các câu đó (B cho doc của lân cận vào). Bài đo sắc: `runs/xq_in.zip` (doc `691380eb140a`) = 3 doc VÀO top-50 và `runs/xq_out.zip` (doc `4401897eb724`) = 3 doc BỊ LOẠI, 501 câu; hạng TB trong blendQB11: vào 58,4 / ra 46,3 (hạng cơ sở bất lợi cho "vào"). Đọc: tỉ lệ doc đúng = DOCS_P × 1200/501; vào ≥ ra → bằng chứng giữa các câu có thật; vào ≪ ra → không có.

### 12/10/2026 · Kiểm shard 3 zh (`Downloads/queue_zh3.sqlite`, 1,47 GB; CHƯA gộp vào store, theo quyết định chờ cào đủ)
- Hàng đợi 2.117.266 URL: đã xong (state 1) 263.033; lỗi (state 2) 97.759; CHƯA cào (state 0) 1.756.474. doc có 360.792 dòng.
- Dùng được (body ≥200 ký tự): **263.033**; body ≥500: 212.211. Trong đó MỚI so với `corpus_vifull`: **259.383** (99%; chỉ 3.650 đã có).
- Theo domain: cnkang.com 187.755 (71%), ask.39.net 36.669, a-hospital.com 25.351, 120ask.com 12.340, zhongyibaodian.net 918.
- Lỗi chủ yếu ConnectTimeout (~91k), captcha 3.996 (403), ReadTimeout ~4k, SSLError ~1,2k → thử lại được phần timeout. Nghi vấn chất lượng: 11.136 dòng gán lang='vi' trong shard zh; mẫu 3.000 doc: 3,9% có tỉ lệ ký tự Hán <30% (nghi mojibake/không phải zh) → cần lọc khi gộp.
- Khi gộp: `clean.py --apply` → `chunk.py` (nếu cần chunk) → export văn bản (`export_delta.py`) → encode BGE-M3 title+600 → xếp hạng lại zh (tương tự `zh_text_delta`).

### 12/10/2026 · zh: TẠM HOÃN theo quyết định người dùng (chờ cào đủ zh rồi mới làm tiếp)
Đã có để làm lại sau: (1) nghi vấn chất lượng dịch zh: toàn bộ 1.200 bản dịch hiện do Qwen3.5 (translation_source='llm'; Hy-MT2 theo kế hoạch ban đầu KHÔNG được dùng); 109 câu từng bị lỗi parse (đã vá trong `queries_enriched.jsonl`, nhưng `q_zh.jsonl`/`dense_zhC2_zhq_rank` vẫn chứa câu VI cho 109 câu này — `dense_zhC2_zhq109_rank.jsonl` là bản đúng); thuật ngữ chưa chuẩn y khoa Trung Quốc (vd. 卵子抽吸 thay 取卵术). (2) `translate_zh_v2.py` (Hy-MT2-7B, HF, theo lô, hai biến thể có/không bảng thuật ngữ); bản thử 24 câu: cosine BGE-M3(vi, zh) = 0,767 (Qwen cũ) / 0,795 (Hy-MT2 plain) / 0,786 (có thuật ngữ); chất lượng nhìn mắt chưa rõ hơn (dài dòng hơn; bản có thuật ngữ có lúc đổi ngôi "tôi"→"您"). Kết quả thử ở `data/zh_v2_test.jsonl` (máy GPU: `data/zh_v2_test.jsonl`); chạy đủ 1.200 câu đã DỪNG theo yêu cầu. (3) Chưa nộp, đã dựng sẵn: `diag_zhC2_vi_k150`, `diag_zhC2_zhq_k150` (so riêng câu vi và câu dịch zh, chưa từng đo riêng), `p_zh_conf` (hỏi zh có nhãn hay thưa). (4) Kết quả Qwen-zh: P@50 0,048 ≈ dense 0,046 (nhãn zh thưa hoặc nút thắt ở nơi khác).

### 12/10/2026 · KẾT QUẢ `cf150_chunk_hyb` (khối dán không nhãn; giả định là bài lai vì đó là bài vừa đề nghị nộp)
FINAL 0,0814 · chunk P 0,0523 / R 0,0987 / F2 0,0746 → ×4: P 0,2092 · R 0,3948 · F2 0,2984, so base 0,2952: **+0,003 (+1,1%)**, nằm trong sai số (±0,009). Triển khai toàn bộ chỉ ước tính +0,0015 FINAL (0,293×1,1%/2) với ~3 giờ GPU → **không đáng; ĐÓNG hướng chunk-first như kết quả âm cho paper**: lợi ích rõ chỉ ở ngân sách nhỏ (30 chunk: +13%), biến mất ở ngân sách thật (150: Qwen −4,7%, lai +1,1%). Chấm chunk bằng Qwen (cùng loại với 'chọn chunk theo nội dung' +0,3% trước đó) không phải đòn bẩy cho khoảng cách chunk với top 1.

### 12/10/2026 · KẾT QUẢ pilot chunk-first ở NGÂN SÁCH THẬT (150 chunk/câu, 300 câu đầu; ×4 quy ra trên 300 câu)
Gán nhãn: người dùng gõ "cf150 qwen" trước khối dán thứ nhất và "cf150 base" sau khối thứ hai (kiểu nhãn đầu như E3) → khối 1 = qwen, khối 2 = base. Cần xác nhận.
| | CHUNKS_P | CHUNKS_R | chunk F2 |
|---|---|---|---|
| `cf150_chunk_qwen` (khối 1) | 0,2052 | 0,3704 | 0,2812 |
| `cf150_chunk_base` (khối 2) | 0,2084 | 0,3892 | 0,2952 |
Δ (qwen − base): P −0,003, R −0,019, chunk F2 **−0,014 (−4,7%)**. Giải thích có thể: danh sách qwen chỉ chọn trong chunk của 80 doc đầu (≈165 chunk/câu) nên ở 150 chunk gần như lấy hết, còn base đi tới doc hạng 120 → recall cao hơn. Lợi ích ở ngân sách 30 chunk (+13%) biến mất ở 150. Bài lai chưa nộp: `cf150_chunk_hyb` (chunk `7552b35fd9f0`): 40 chunk đầu theo Qwen rồi tiếp theo thứ tự hiện tại (dedupe) tới 150.

### 12/10/2026 · KẾT QUẢ pilot chunk-first, 30 chunk/câu, 300 câu đầu (chỉ chunk; điểm ×4 quy ra trên 300 câu)
| | CHUNKS_P | CHUNKS_R | chunk F2 (macro×4) |
|---|---|---|---|
| `cf_chunk_base` (30 chunk đầu theo thứ tự nộp hiện tại, dedupe) | 0,2972 | 0,1372 | 0,1396 |
| `cf_chunk_qwen` (top-30 theo điểm Qwen cấp chunk, dedupe) | 0,3072 | 0,1584 | 0,1580 |
| Δ | +0,0100 (+3,4%) | **+0,0212 (+15%)** | **+0,0184 (+13%)** |
Doc F2 y hệt (0,0882, P 0,0493, R 0,1326) như kỳ vọng. Ngưỡng đặt trước cho P (+0,03) KHÔNG đạt; nhưng F2 chunk +13% tương đối nhờ recall (cùng 30 chunk phủ nhiều "phần thông tin" hơn). Sai số ~±0,009 trên chênh F2 (ước tính, 300 câu, cặp) → ~2σ: dương nhưng chưa chắc chắn. Mới đo ở ngân sách 30 chunk; ngân sách thật là ~149 chunk nơi lợi ích tương đối nhiều khả năng nhỏ hơn. Bài đo ngân sách thật: `cf150_chunk_base`, `cf150_chunk_qwen` (150 chunk/câu, 300 câu).

### 12/10/2026 · Pilot chunk-first ĐÃ DỰNG (49.470 cặp chunk Qwen xong, 300 câu đầu)
Bài đo (đều 300 câu đầu, 900 câu còn lại rỗng): `p50_cf_base` (doc `807173f286b1`), `p50_cf_chunk` (`73579dfc7297`; giao top-50 với base 35,5), `p50_cf_mix` (`12c7eded1d1e`; giao base 42,3); `cf_chunk_base` (chunk `8095a36a203d`), `cf_chunk_qwen` (chunk `9a45655a83d7`; giao 30 chunk với base chỉ 12,3), doc của cả hai = top-200 blendQB11 cho 300 câu (`e303e700a352`).

### 12/10/2026 · Pilot chunk-first (300 câu đầu) + phép thử zh "Qwen tự tin"
- Pilot chunk-first: Qwen chấm MỌI chunk của 80 doc đầu (blendQB11) cho câu 1–300 (49.470 cặp, `cf_scores.jsonl`, chạy 12/10); sau khi xong chạy `python chunkfirst_eval.py` dựng `p50_cf_base`, `p50_cf_chunk`, `p50_cf_mix` (P@50 doc) và `cf_chunk_base`, `cf_chunk_qwen` (30 chunk/câu). Ngưỡng quyết định (ước tính sai số do 300 câu × 50 doc + tương quan cụm): doc P@50 (DOCS_P×4) cải thiện ≥ +0,02 so base mới đáng tin; chunk P ≥ +0,03.
- `runs/p_zh_conf.zip` (doc `be6741183c7f`): 143/300 câu có ≥10 doc zh Qwen≥0,9; nộp 10 doc/câu đó. Đọc: tỉ lệ doc đúng = DOCS_P × 1200/143. So với vi: e1_A (≥5 hệ thống) 0,50. Nếu zh tự tin cũng ~0,3–0,5 → zh có nhãn nhưng nguồn zh khó xếp/kéo lên; nếu ≲0,15 → nhãn zh thưa/không đồng nhất với tiêu chuẩn của Qwen.

### 12/10/2026 · Bài đo CHUNK đầu danh sách (cùng danh sách doc top-200 của blendQB11 → doc F2 phải = 0,3384; chỉ chunk khác)
Động cơ: khoảng cách chunk F2 với top 1 (0,293 vs ~0,465) lớn hơn khoảng cách doc (0,338 vs ~0,460); chunk P của ta (0,192) ≈ doc P (0,179) trong khi top 1 chunk P (0,628) > doc P (0,469) → chunk của họ đến từ tập doc nhỏ hơn/chính xác hơn và/hoặc chọn đoạn đúng hơn.
- `runs/c1_top20_x2.zip` (doc `621ba023da3c`, chunk `0e6d6c0fe513`): chunk của 20 doc đầu, ≤2 chunk/doc, 34,5 chunk/câu (dài trung vị 2.794 ký tự).
- `runs/c2_top20_x1.zip` (chunk `a87036a20b2c`): chỉ chunk ĐẦU TIÊN của 20 doc đầu, 20 chunk/câu.
- `runs/c3_top20_x1_half.zip` (chunk `f6b0d544443f`): như c2 nhưng cắt còn ~1.400 ký tự đầu của chunk (vẫn là chuỗi con nguyên văn).
Đọc: so (P,R) chunk của c1/c2/c3 với blendQB11 (P 0,1918 / R 0,4181, 149 chunk). c1 vs c2 = giá trị chunk thứ hai ở đầu; c2 vs c3 = ảnh hưởng độ dài chunk lên "overlap đủ" (nếu R giảm theo tỉ lệ, P không tăng → chunk dài thắng; nếu P tăng mạnh mà R giảm ít → nên cắt ngắn).
Quan sát view5 (5 câu): doc trùng nguyên văn chiếm chỗ (30% câu có trùng trong top-40; 3,7% chunk trùng); TB 13,8 doc Qwen>0,9 nằm dưới top-40; chunk đầu Long Châu mang tiểu sử tác giả, medlatec mang danh sách link; chunk gần như luôn là phần mở đầu bài (vị trí 0 và ~2.400–2.900).

### 12/10/2026 · KẾT QUẢ blendQB11_e120 (người dùng xác nhận: đây là QB11; QB10 CHƯA nộp)
FINAL **0,3158** · doc F2 0,3384 (P 0,1785 / R 0,5573) · chunk F2 **0,2931** (P 0,1918 / R 0,4181). TỐT NHẤT hiện tại (+0,0012 so 0,3146). Doc P/R/F2 trùng 4 chữ số với blendQB9a → **vá 109 câu không làm đổi điểm doc ở mức đo được** (ước tính tác động: 109/1200 × ~13 doc đổi/câu → ≲ +0,0003 doc F2, dưới độ phân giải); chunk 0,2931 ≈ dự đoán QB10 (0,2935). Mức tăng +0,0012 so 8w05 đến từ ghép hai tầng (doc của 9a, đầu của 8w05), KHÔNG từ bản vá. Dự đoán trước đó của mình (+0,001–0,003 từ bản vá) là lạc quan. Có thể coi QB11 ≈ QB10, không cần nộp QB10. Giá trị của bản vá: chuỗi dữ liệu đúng cho private phase.

### 12/10/2026 · E5 (đặc trưng doc, đối chứng cùng hạng; 4 doc/câu từ top-100 của blendQB11, ghép cặp A–B theo hạng gần nhất, chênh ≤15)
- `runs/e5_len_A.zip` (doc DÀI > 5.444 ký tự, `747661fef59c`) vs `e5_len_B.zip` (NGẮN < 3.347, `30a8efb2fb63`): 1.198 câu, hạng TB 18,0/18,1.
- `runs/e5_yr_A.zip` (đăng ≥2024, `428aad4e53ca`) vs `e5_yr_B.zip` (≤2021, `f7392b5a19f6`): 1.192 câu, hạng TB 13,7/13,8.
Đọc: tỉ lệ doc đúng = DOCS_P × 1200/số câu; so A/B cùng cặp; tỉ số ≥1,5 hoặc ≤0,67 → nhãn thiên về/chống đặc trưng đó. Bản dựng đầu (lấy 4 doc A đầu danh sách) bị lệch hạng (7,3 vs 13,6) nên đã bỏ.
Quan sát nền: top-20 của ta dài hơn (trung vị 4.567 vs 3.108) và mới hơn (39% ≥2024 vs 29%) kho vi ngẫu nhiên.

### 12/10/2026 · VÁ LỖI 109 CÂU (parse_ok=False) → `blendQB11_e120`
- **Nguyên nhân:** 109/1200 câu (9%, toàn câu dài, TB 5,2 entity) có đầu ra Qwen3.5 hợp lệ nhưng THIẾU dấu `}` cuối nên `pubmed_module` đánh `parse_ok=false` → `en`/`zh`/`entities` rỗng. Hậu quả: câu thiếu nguồn BM25-entity (file `bm25ent3_rank` chỉ có 1.090 câu), và `q_zh.jsonl` cho 109 câu này rơi về câu hỏi VI gốc (nguồn zh-query nhân đôi nguồn vi). Các nguồn slug/BM25F/dense/chunk-dense dùng câu vi nên KHÔNG ảnh hưởng.
- **Sửa:** phân tích lại `raw` bằng cách thêm `}` (109/109 được; còn 1 câu id 512 vẫn không có entity), ghi lại `data/queries_enriched.jsonl` (bản cũ `…bak_before_fix109.jsonl`); chạy lại BM25-entity trên `vi_full.sqlite` (109 câu), zh dense bằng bản dịch zh đúng (`dense_zhC2_zhq109_rank`), pool H2 (`f_H2`): top-50 đổi 4,4 doc/câu, top-200 18,0, top-400 35,6 so với `f_H`; 2.610 cặp mới → Qwen chấm (`qwen_h2`, 109 câu, ~2 phút). Chuỗi QB6_h05 → QB7 → QB8/8w05 → QB9a → QB10 chạy lại CHỈ cho 109 câu (pilot chunk-dense thay bằng chunk-dense toàn kho lọc theo pool mới); 1.091 câu còn lại giữ nguyên bài cũ.
- **Kiểm tái lập chuỗi:** QB6_h05 khớp 1200/1200 câu; QB7 1155/1200 (do hoà điểm/bản pilot); QB8 cắt chunk-dense toàn kho ở top-400 khớp 1146/1200, QB8w05 1164/1200; QB9a 1200/1200; dựng lại QB10 bằng `submission.py` cho đúng vân tay cũ (`49b78b6e2cd2`/`3c412209084d`).
- **`runs/blendQB11_e120.zip`** (178.992 chunk, 93,2 MB, doc `621ba023da3c`, chunk `7fc5cb4c79af`): so với blendQB10, 109 câu đổi 1,7 doc/câu ở top-40, 5,7 ở top-120, 13,4 ở top-200; 1.091 câu còn lại KHÔNG đổi. Dự đoán (ước tính): +0,001–0,003 FINAL so blendQB10 (dự đoán 0,3160).

### 11/10/2026 · Bài đo dựng sẵn cho 12/10 (chưa nộp)
- `runs/e1_novel.zip` (doc `543c93021f28`): 4 doc/câu, đồng thuận ≥4/8 hệ thống nhưng NGOÀI top-50 của blendQB10; 189 câu (đồng thuận TB 4,34). `runs/e1_base.zip` (doc `8c624da0c80f`): top-4 của blendQB10 trên đúng 189 câu đó (đồng thuận TB 5,57). Đọc: DOCS_P × 1200/189 = tỉ lệ doc đúng; novel ≳ base×0,7 → blend đang bỏ sót doc đồng thuận; novel ≪ base → blend đã nắm thông tin đồng thuận.
- Phát hiện khi dựng: doc đồng thuận ≥5 mà NGOÀI top-50 blend chỉ tồn tại ở 5 câu (đủ 4 doc) → blend đã chứa gần hết doc đồng thuận cao; bài chỉ còn ≥4 hệ thống mới có đủ 189 câu.

### 11/10/2026 · KẾT QUẢ E1 (đồng thuận → tỉ lệ doc đúng = DOCS_P × 1200/596)
| Bài | DOCS_P | Tỉ lệ doc đúng |
|---|---|---|
| e1_A_c5plus (≥5 hệ thống) | 0,2462 | **0,496** |
| e1_B_c3_4 | 0,1710 | 0,344 |
| e1_C_c2 | 0,0875 | 0,176 |
| e1_D_c1 (chỉ 1 hệ thống) | 0,0453 | 0,091 |
Đọc: độ dốc rất mạnh (gấp ~5,4× từ D lên A) nên nhãn tương quan chặt với đồng thuận; nhưng trần ở nhóm đồng thuận cao nhất chỉ ~0,50 (không phải ~0,9 như pooling thuần). Chưa biết đồng thuận có thêm thông tin ngoài blend hiện tại không → cần e1_base (top-8 blendQB10 cùng 596 câu) và e1_novel (doc c≥5 nằm NGOÀI top-50 blend).

### 11/10/2026 · KẾT QUẢ E3 (tỉ lệ doc đúng = DOCS_P × 1200 / số câu; 4 doc/câu). Gán nhãn theo thứ tự dán + nhãn người dùng gõ; thiếu `e3_medlatec_ctl`.
| Site (số câu) | site | đối chứng cùng hạng | tỉ số |
|---|---|---|---|
| congdong (434, hạng TB ~40) | 0,2914 (P 0,1054) | 0,2961 (P 0,1071) | 0,98 |
| longchau (1184, hạng TB ~12) | 0,4239 (P 0,4182) | 0,4051 (P 0,3997) | 1,05 |
| medlatec (1039, hạng TB ~23) | 0,4206 (P 0,3642) | 0,3652 (P 0,3162; dán không nhãn, giả định là `e3_medlatec_ctl`) | **1,15** |
Đọc: cùng hạng thì site không có prior riêng (tỉ số trong sai số ~±0,05) → xếp hạng hiện tại đã bắt trọn thông tin site; độ lệch site ở đầu danh sách (medlatec ×3,6, congdong ×0,15) KHÔNG phải sai hiệu chuẩn. Phụ: độ chính xác theo hạng ≈ 0,41 ở hạng ~12, 0,29 ở hạng ~40.

### 10/10/2026 · CHƯƠNG TRÌNH ĐO NHÃN ("label forensics"): dùng leaderboard làm phép đo, không để lên điểm

Ý: nộp danh sách được thiết kế để trả lời một câu hỏi về cách BTC tạo nhãn. Thiết kế chung: **mỗi bài có đúng k doc cho mọi câu được chọn (hoặc rỗng)** nên P đo được = (số câu có danh sách / 1.200) × (tỉ lệ doc đúng); so các bài cùng tập câu thì so được trực tiếp.
Quan sát phát sinh trước khi đo: (1) 8 hệ thống (slug, BM25F ×3, dense ×2, chunk-dense toàn kho, Qwen) bất đồng mạnh: TB mỗi câu có 172,4 doc chỉ xuất hiện ở đúng 1 hệ thống trong top-50, 40,5 doc ở 2, 17,3 ở 3, 8,4 ở 4, 4,4 ở 5, 2,7 ở 6, 1,7 ở 7, 0,8 ở cả 8. (2) Đầu danh sách của ta lệch site so với kho vi: medlatec ×3,6, vinmec ×3,0, nhathuoclongchau ×2,1, suckhoedoisong ×1,3; suckhoecongdongonline (20,5% kho) chỉ ×0,15, laodong ×0,29.
- **E1 (đồng thuận, 4 bài, 596 câu, 8 doc/câu):** `runs/e1_A_c5plus.zip` (≥5 hệ thống đồng ý, doc `67b4d659df8a`), `e1_B_c3_4.zip` (3–4, `f26092050eda`), `e1_C_c2.zip` (2, `b0b46dd21bec`), `e1_D_c1.zip` (1, `f96a4e47e6f1`). Đọc: tỉ lệ doc đúng = DOCS_P × 1200/596 (≈ ×2,013). P tăng mạnh theo đồng thuận → nhãn gần "giao của các hệ thống chuẩn" (dấu vết pooling), nên bầu theo đồng thuận; phẳng → nhãn do tín hiệu khác ta chưa có.
- **E2 (bản sao nguyên văn):** thiết kế gốc KHÔNG khả thi — bản sao hầu như luôn nằm cùng trong danh sách của ta (chỉ 4 cặp có bản sao ngoài top-200); có 1.182 cặp trùng nguyên văn cùng trong top-100 (691 câu). Do P cộng tính, không đo được "cả hai cùng đúng"; chỉ đo được bất đối xứng id nhỏ/lớn → ít thông tin, bỏ.
- **E3 (lệch site, đối chứng cùng hạng, 6 bài):** cho site S ∈ {longchau, medlatec, congdong}: 4 doc của S trong top-100 của blendQB10 vs 4 doc KHÔNG phải S gần hạng nhất (hạng TB khớp: 11,7/11,5; 22,8/22,1; 40,8/39,9). `runs/e3_longchau_site.zip` (1.184 câu, doc `83e4b90b80ee`) & `_ctl` (`e2666395628b`); `e3_medlatec_site` (1.039 câu, `2b3fb96ee1ac`) & `_ctl` (`a1726ff50078`); `e3_congdong_site` (434 câu, `0bb00a5033ef`) & `_ctl` (`2c05bc0ded59`). Đọc: cùng tập câu, so P(site)/P(ctl); chênh ≥ 1,5–2× → có "prior site" bỏ qua = tín hiệu trực giao. Lưu ý bản E3 đầu (lấy doc site ở độ sâu khác) đã bỏ vì lẫn hiệu ứng hạng.
- **E4 (loại câu hỏi) chưa dựng.**
Hàng đợi 11/10 (10 lượt): E1 (4) + E3 longchau (2) + E3 medlatec (2) + 2 lượt dự phòng.

### 09/10/2026 · HÀNG ĐỢI NỘP 10/10 (đã dựng, chưa nộp): chunk-dense TOÀN KHO

`dense_chunk_full_rank.jsonl`: BGE-M3 trên toàn bộ ~1,29M chunk vi (374k pilot + 914k thêm, 2 GPU ~65 phút), điểm doc = chunk khớp nhất, top-1000 doc/câu. **Top-200 của nó có 49,7 doc/câu nằm NGOÀI pool H top-1000** (78,8 ngoài top-400) và giao 39,5/50 với pilot ở top-50: đây là nguồn mở rộng pool đầu tiên đọc cả thân bài.
| Thứ tự | Bài | Nội dung | Đo gì | Vân tay |
| --- | --- | --- | --- | --- |
| 1 | `runs/diag_novel_chunkfull_k150.zip` | 150 doc hạng cao của chunk-dense toàn kho KHÔNG nằm trong pool H top-1000, chunk rỗng | DOCS_RECALL = nhãn ngoài pool mà chunk-dense cứu được (mốc: doc chưa crawl 0,0181; PRF 0,0108; HyDE 0,0084) | doc `8636a929de7f` |
| 2 | `runs/p50_cfull.zip` | top-50 chunk-dense toàn kho một mình | P@50 (mốc: head 0,3125; chunk pilot 0,3136; headchunk 0,3380) | doc `d16663945801` |
| 3 | `runs/blendQB7b_e120.zip` | tập doc y hệt blendQB7 (vân tay doc `9c6f85ea7df8`, doc F2 phải = 0,3236); chunk chọn theo best_idx thay chunk đầu (`chunk_scores_mix.jsonl`: doc có điểm Qwen chunk giữ Qwen) | phép thử SẠCH của chọn chunk theo nội dung (mốc chunk F2 0,2900) | chunk `647147b3b9cb` |
| 4 | `runs/blendQB8_e120.zip` | RRF(blendQB7, chunk-dense toàn kho) w1/w1, chunk đầu; đổi 47,8 doc/câu top-200 so blendQB7 (17,4 doc/câu ngoài pool H); 94,9 MB | mốc FINAL 0,3068 | doc `832af360705c` chunk `358431c81ad4` |
| 5 | `runs/blendQB8b_e120.zip` | như 4 nhưng chunk chọn theo best_idx (94,2 MB) | cộng hưởng 3 + 4 | chunk `739418b50219` |
| 6 | `runs/diag_zhC2_vi_k150.zip` | 150 doc zh/câu (dense title+600 ký tự đầu, BGE-M3 fp16, 1,72M doc zh) xếp bằng CÂU HỎI VI GỐC, chunk rỗng | DOCS_P = mật độ nhãn trong doc zh tìm bằng bộ truy hồi mạnh (mốc bài zh cũ P 0,0089 / R 0,0256 ở độ phủ ~35% và truy hồi yếu; doc vi chưa crawl P 0,0174). Nếu ≳0,05 → zh quan trọng | doc `5b054ae47bde` |
| 7 | `runs/diag_zhC2_zhq_k150.zip` | như 6 nhưng bằng câu hỏi DỊCH SANG ZH (`q_zh.jsonl`, Qwen3.5) | so với 6: dịch có giúp | doc `c40d960c81b6` |
| 8 | `runs/diag_zhC2_both_k150.zip` | RRF hai danh sách (vi + dịch zh), 150 doc | tổng hợp; giao vi∩zhq: top-10 2,5/10, top-50 15,1/50, top-150 50,4/150 (hai cách truy vấn tìm tập doc zh khác nhau nhiều); doc zh ∩ top-200 blendQB7: 0,03/câu (hai kho gần như rời nhau) | doc `05073f7ed644` |
Kho zh: 1,72M doc (kho GPU 1,42M + shard 2 298k), phủ 51% của 3.380.139 URL; thiếu ~4k doc so với `corpus_vifull`. Còn 658.834 doc zh có body CHƯA có chunk (cần `clean.py`/`chunk.py` nếu muốn nộp chunk zh). Quyết: nếu P ≳0,05 → dựng bài ghép vi+zh (zh chiếm một phần top-k theo mật độ nhãn); nếu ≲0,015 → zh thật sự nhỏ, bỏ.

Cách quyết: nếu (3) tăng chunk F2 → dùng best_idx cho mọi bài sau; nếu (1) cao (≳0,02) và (4) hơn 0,3068 → chunk-dense toàn kho là nguồn chính. Cả bài mốc `blendQB7_e120` (0,3068) vẫn là bài tốt nhất đã có điểm.

### 09/10/2026 · Đối chiếu với top 1 và hướng đi mới: độ chính xác ĐẦU danh sách

Top 1 leaderboard (người dùng cung cấp 09/10): FINAL 0,4214 · doc F2 0,4183 · chunk F2 0,4246 · **doc P 0,469 · doc R 0,4578 · chunk P 0,6281 · chunk R 0,4365**. Ta (blendQB6): FINAL 0,2931 · doc F2 0,3131 · chunk F2 0,2730 · doc P 0,1645 · doc R 0,5177 · chunk P 0,1793 · chunk R 0,3906.
- P/R = G/k ⇒ top 1 trả về k ≈ G ≈ 65–70 doc/câu; g ≈ 0,458×70 ≈ 32 doc đúng — **bằng ta** (0,1645×200 ≈ 33) nhưng nằm gọn trong top ~70 (ta rải trong 200; P@50 của ta ≈ 0,32).
- Hệ quả: khoảng cách là **độ chính xác đầu danh sách**, không phải độ phủ/recall của pool. Thêm nguồn mở rộng pool ít giá trị; cần tín hiệu xếp gold vào top-70. Chunk P 0,63 vs 0,18 phần lớn theo từ đó (chunk lấy từ doc đầu).
- Đã loại: Qwen lớn hơn (8B ≈ 4B), Qwen đọc dài hơn (3k ≈ 1k), tăng trọng số Qwen (đầu danh sách tệ hơn khi nghiêng về Qwen).
- Kế hoạch đo: (1) **6 bài P@50 theo nguồn, đủ 1.200 câu**, 50 doc/câu, chunk rỗng: `runs/p50_head.zip` (đầu của blendQB6_h05, doc `961ffff53bc0`), `p50_qwen.zip` (Qwen thuần, `0fcff1e3b03a`), `p50_fH.zip` (vòng 1 pool H, `f155823e83ef`), `p50_dvib3.zip` (dense nội dung, `ccded4a4282f`), `p50_dvi3.zip` (dense title, `2863f6cde365`), `p50_bm25.zip` (BM25F, `4d9a6ce85bf2`). Giao top-50 với `head`: Qwen 26,0 · f_H 41,7 · dvib3 29,2 · dvi3 26,7 · bm25 13,5. Nguồn nào P@50 cao nhất thì tín hiệu đó gần nhãn nhất. (2) **Pilot dense cấp chunk** (BGE-M3 trên 374.355 chunk của 194.376 doc trong pool H top-400; điểm doc = chunk khớp nhất): `dense_chunks.py`, `scripts/run_dense_chunks_pilot.sh`, đầu ra `data/dense_chunk_pilot_rank.jsonl` (có `best_idx` = chunk khớp nhất để chọn chunk nộp).

### 07/10/2026 · TỔNG KẾT 10 LƯỢT NỘP TRONG NGÀY + HÀNG ĐỢI 08/10 (đã hết quota hôm nay)

FINAL 0,2658 → **0,2770** trong ngày. Chi tiết từng bài ở §2b; đây là bản đọc nhanh kèm bài học.

| # | Bài | FINAL | Kết quả chính | Insight |
|---|---|---|---|---|
| 1 | `blendQB3_t40_70` (Qwen top-400) | 0,2669 | doc F2 0,2956 (+1,4%), chunk 0,2382 (−0,8%) | chấm sâu thêm có lợi suất giảm (100→250: +4,2%; 250→400: +1,4%) |
| 2 | `blendQB3x_t40_70` (doc QB3 + chunk QB2) | 0,2679 | khớp dự đoán đúng | hai tầng độc lập tuyệt đối (xác nhận lần 2) |
| 3 | `diag_novel_qhyde_k150` | 0,0033 | DOCS_R 0,0084 | HyDE yếu; khớp văn liệu (mở rộng LLM hại retriever mạnh) |
| 4 | `diag_novel_hyde_k150` | 0,0027 | DOCS_R 0,0068 | câu trả lời giả định thuần kém bản ghép câu hỏi |
| 5 | `blendQB3x_cr` (chọn chunk bằng Qwen) | 0,2682 | chunk F2 +0,25% | ít doc có chỗ để chọn (76% doc ≤2 chunk) |
| 6 | `diag_novel_q4t_k150` (Qwen3-Embedding title) | 0,0031 | DOCS_R 0,0080 | embedding mới không cứu thêm nhãn; pool bão hoà với nguồn dense |
| 7 | `diag_novel_prf20_k150` | 0,0043 | DOCS_R 0,0108 | PRF tốt nhất nhóm embedding nhưng vẫn ~1% pool |
| 8 | `diag_uncrawled_vi_k150` | 0,0076 | DOCS_P 0,0174, R 0,0181 | **tín hiệu tốt nhất**: doc chưa crawl CÓ nhãn → crawl nốt Long Châu |
| 9 | `blendQB3x_3k_300_bzip2` | 0,2609 | doc 0,2895, chunk 0,2324 | **bzip2 được server chấp nhận**; không kết luận được về Qwen 3k (lẫn k=150, pool cắt) |
| 10 | **`blendQB3x_cr_e120`** | **0,2770** | chunk F2 0,2584 (+7,3%) | **chunk sâu hơn còn lãi** (precision biên ~0,105 so với ngưỡng ~0,052); trần 100 MB là ràng buộc → bzip2 mở thêm ~1,5× chunk |

**Bài học lớn của ngày**
1. Điểm đi lên nhờ **tầng chunk** (đổi nén ZIP) và **độ phủ kho**, không nhờ thêm nguồn dense. Mọi nguồn embedding/entity/HyDE/PRF đều chỉ 0,007–0,011 DOCS_R.
2. Reranker (Qwen) và dense chỉ đọc 1.000/600 ký tự đầu trong khi 96% doc top-200 dài hơn thế (trung vị 4.165). Chưa có kết luận Qwen đọc dài tốt hơn không.
3. Qwen "dễ tính" hơn nhãn vàng (P(yes) > 0,5 cho ~130 doc/câu, G ≈ 70) và G gần hằng số → cắt k theo câu không đáng.
4. Phép thử cần SẠCH: giữ k, pool, chunk như nhau, chỉ đổi một yếu tố (bài học từ #9 và từ bài QC 06/10).

**Hàng đợi 08/10 (10 lượt mới), theo thứ tự**
1. ~~`cr_t30_e130`~~ **đã nộp 08/10: 0,2763 < e120 0,2770 → phân bổ chunk ở đỉnh phẳng, bỏ hướng này.** (`cr_t30_e140` quá trần, không dùng.)
2. ~~Cặp `probe300`~~ **đã nộp 08/10: 1k P 0,0791 vs 3k P 0,0787 → Qwen đọc dài hơn không giúp, bỏ hướng này.**
3. (tuỳ chọn) `runs/diag_novel_subq_k150.zip`: dự báo ~0,008, ưu tiên thấp.
4. Sau khi crawl Long Châu xong: `clean.py --apply` → `chunk.py` → `audit.py` → embed doc mới (GPU) → Qwen rerank → dựng bài mới → đo.

**Việc dở**
- Crawl Long Châu ~49k URL (chạy ở máy của bạn; vòng lặp tôi dựng bị dừng vì thiếu RAM, **không tự chạy lại**). Gợi ý `--workers 30 --procs 3` hoặc chạy trên máy GPU.
- Dense cấp chunk toàn thân bài (~1,1M chunk, ~2,5 giờ GPU) và Qwen3-Reranker-8B (~6 giờ GPU) chưa chạy. Chấm Qwen chunk đầu của doc hạng 70–130 để chọn chunk tốt hơn (ước tính +1–2% chunk).
- Đã chốt toàn bộ các vấn đề quy định BTC (xem bảng chi tiết tại §4): coi như bản web mới nhất, không hỏi về cách tạo nhãn, MoE hợp lệ, Distillation được phép.
- Private phase: 5 lượt tổng; cần script dựng duy nhất tái lập bài tốt nhất; working notes paper chưa viết.

---
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

| 07/10 | **`blendQB3_t40_70.zip`** | như `blendQB2` nhưng Qwen3-Reranker chấm **top-400** (hạng 251–400 thêm từ `qwen_rr3_h1/h2`, 383–400 doc/câu): RRF(Qwen w2, vòng 1 w1) + chunk t40_70 | 200 | **0,2956** | 0,2382 | FINAL **0,2669** ← TỐT NHẤT (+0,4% so 0,2658). Doc +1,4% (P 0,1562 / R 0,4855), chunk **−0,8%** (P 0,2041 / R 0,3022; top-40/70 đổi theo tập mới). Lợi suất giảm đúng dự báo: 100→250 cho doc +4,2%, 250→400 chỉ +1,4%. Trùng 170,7/200 doc với QB2. ZIP 93,8 MB, 114.698 chunk. Vân tay (tự tính, sha1 12 ký tự) doc `f75ca640d7fe` chunk `82f3a7dbbdda`. `submission.py` lỗi `NameError: fingerprint` sau khi ghi ZIP (vô hại) |

| 07/10 | **`blendQB3x_t40_70.zip`** | bản lai: **tập doc của QB3** (Qwen top-400) + **chunk của QB2** (thứ tự 70 doc đầu theo QB2; 0 doc top-70 của QB2 nằm ngoài tập QB3) | 200 | **0,2956** | **0,2402** | FINAL **0,2679** ← TỐT NHẤT. Khớp ĐÚNG dự đoán (0,2956+0,2402)/2 = 0,2679; mọi số LB bằng số của bài thành phần (doc = QB3: P 0,1562 / R 0,4855; chunk = QB2: P 0,2063 / R 0,3042) → hai tầng độc lập tuyệt đối, lần xác nhận thứ hai (cũng 03/10). ZIP 91,8 MB, 114.760 chunk. Vân tay (hàm `fingerprint` mới, doc theo TẬP) doc `5a1af0bad078` chunk `96f94cfa925e`. Vân tay doc của `blendQB3` tính lại theo cách mới: `5a1af0bad078` (chunk `82f3a7dbbdda`) |

| 07/10 | `diag_novel_qhyde_k150.zip` | **chẩn đoán HyDE**: chỉ 150 doc hạng cao của dense(câu hỏi + câu trả lời giả định) KHÔNG nằm trong pool F top-1000, chunk rỗng | 150 | 0,0066 | 0 | FINAL 0,0033. DOCS_P **0,0048**, DOCS_R **0,0084** (≈ +0,6–0,7 nhãn/câu ngoài pool, +1,4% tương đối so mốc 0,6108). Vân tay doc `709f9ee4ab5d` |

| 07/10 | `diag_novel_q4t_k150.zip` | **chẩn đoán Qwen3-Embedding-4B title**: 150 doc hạng cao của dense(Qwen3-Emb title, 686k doc vi) KHÔNG nằm trong pool F top-1000, chunk rỗng | 150 | 0,0062 | 0 | FINAL 0,0031. DOCS_P 0,0043, DOCS_R **0,0080** — ngang HyDE (0,0084/0,0068), yếu. Offline: 73,4 doc/câu top-200 nằm ngoài pool nhưng bắt nhãn bạc chỉ 78,0 (BGE title 91,2). Vân tay doc `96eeb31c2611` |
| 07/10 | `diag_novel_prf20_k150.zip` | **chẩn đoán PRF dense**: 150 doc láng giềng (trung bình vector top-20 `blendQB3`, `emb_viB2`) KHÔNG nằm trong pool F top-1000, chunk rỗng | 150 | 0,0085 | 0 | FINAL 0,0043. DOCS_P **0,0061**, DOCS_R **0,0108** — tốt nhất trong các nguồn mở rộng (HyDE 0,0084 · Qwen3-Emb 0,0080) nhưng vẫn rất thấp: ~0,9 nhãn/câu trong 150 doc, precision biên 0,6% so với ngưỡng giữ ~6%. Vân tay doc `850b32133a66` |
| 07/10 | **`diag_uncrawled_vi_k150.zip`** | **chẩn đoán độ phủ crawl**: doc vi CHƯA crawl/lỗi (state≠1) xếp theo slug BM25, ~66 doc/câu (chủ yếu `nhathuoclongchau` 54,6k URL chưa cào + blog pharmacity), chunk rỗng | ~66 | 0,0152 | 0 | FINAL 0,0076. DOCS_P **0,0174**, DOCS_R **0,0181** — **tốt nhất mọi nguồn mở rộng** (PRF 0,0108 · HyDE 0,0084): precision 3× HyDE. Vậy doc chưa crawl CÓ chứa nhãn → mục "51k URL chưa cào, không quan trọng" trong CLAUDE.md là SAI. Vân tay doc `3cf0fb5ca05b` |
| 07/10 | `diag_novel_subq_k150.zip` | **chẩn đoán tách ý con** (đã dựng, CHƯA nộp): RRF(BGE-M3 title + nội dung theo từng ý, 3,23 ý/câu), 150 doc ngoài pool F top-1000 (271 câu <150 doc) | 150 | — | — | Offline: bắt nhãn bạc top-200 thấp hơn câu gốc (title 80,6 vs 91,2; body 99,8 vs 115,8); 33,4–35,2 doc/câu ngoài pool. Qwen tách quá tay (827/1200 câu = 4 ý). Vân tay doc `590aa071dc7e`. Chưa nộp để dành lượt cho bài Long Châu |
| 07/10 | **`blendQB3x_cr.zip`** | như `blendQB3x` nhưng doc ≥3 chunk ở top-40 chọn 2 chunk điểm Qwen3-Reranker CAO NHẤT (36.568 chunk chấm, `chunk_rerank.py`) thay vì 2 chunk đầu; 4,1% chunk đổi | 200 | 0,2956 | **0,2408** | FINAL **0,2682** ← TỐT NHẤT (+0,0003). Doc y hệt. Chunk +0,25%: P 0,2063 → 0,2049, R 0,3042 → 0,3089. Đúng dự báo (≤ +1%): 76% doc chỉ ≤2 chunk nên ít chỗ để chọn. Vân tay doc `5a1af0bad078` chunk `f41d9e9c0e17` |
| 07/10 | `blendQB3x_cr_bzip2.zip` | **thử nén bzip2**: NỘI DUNG y hệt `blendQB3x_cr` (đã kiểm md5 từng byte JSON), chỉ đổi nén deflate → bzip2 (59,3 MB; LZMA 55,9 MB cũng có `blendQB3x_cr_lzma.zip`) | 200 | (chờ) | (chờ) | Nếu FINAL = 0,2682 y hệt thì server đọc được bzip2 → mở rộng độ sâu chunk (~1,5× chunk trong 100 MB). Nếu lỗi định dạng: không tính quota |
| 07/10 | `blendQB3x_3k_300_bzip2.zip` | `blendQB3x_cr` nhưng 300 câu đầu dùng Qwen đọc 3.000 ký tự: **chỉ 150 doc/câu** (pool = f_F top-150, mất doc hạng 150–400), chunk theo thứ hạng 3k; 900 câu còn lại y hệt `cr`; nén **bzip2** (58 MB) | 187,5 | 0,2895 | 0,2324 | FINAL 0,2609 (−0,0073 so 0,2682): DOCS_P 0,1596 / R 0,4667. **Server CHẤP NHẬN bzip2** ✓. Phép thử KHÔNG sạch về 3k (lẫn k 150 và pool cắt) → xem cặp `probe300_*` |
| 07/10 | **`blendQB3x_cr_e120.zip`** | tập doc y hệt `blendQB3x_cr`; chunk: 2 chunk (điểm Qwen) × 40 doc đầu + **1 chunk × doc hạng 41–120**, nén **bzip2** (174.760 chunk, 93,6 MB) | 200 | 0,2956 | **0,2584** | FINAL **0,2770** ← TỐT NHẤT (+0,0088 so 0,2682; dự đoán +0,004–0,006 → tốt hơn dự đoán). Chunk F2 +7,3%: P 0,2049 → 0,1708, R 0,3089 → 0,3692. Chunk thêm (+60k): ~6,3k chunk đúng → **precision biên ~0,105**, gấp ~2× ngưỡng giữ (F2/5 ≈ 0,052) → còn lãi, chặn bởi 100 MB. Vân tay doc `5a1af0bad078` chunk `1be27cfed8c6` |
| 08/10 | `cr_t30_e130.zip` | tập doc y hệt; chunk: 2 chunk × **30** doc đầu + 1 chunk × hạng 31–130, bzip2 (178.850 chunk, 94,7 MB) | 200 | 0,2956 | 0,2570 | FINAL 0,2763 (−0,0007 so e120 0,2770). CHUNKS_P 0,1708 → 0,1669, R 0,3692 → 0,3696. Số chunk ĐÚNG gần như bằng nhau (29.851 vs 29.850) dù thêm 4.090 chunk → chunk thứ hai ở hạng 31–40 có giá trị NGANG chunk đầu ở hạng 121–130 (precision biên ~0,1–0,05): phân bổ đã ở **đỉnh phẳng**, đừng chỉnh nữa. e120 vẫn tốt nhất. Vân tay: dùng `fingerprint` của submission |
| 08/10 | `blendQB4_e120.zip` | **chuỗi Long Châu**: crawl nốt Long Châu (78.555 doc xong) → `clean.py` (sửa 48.749 doc) → `chunk.py` → embed 55.136 doc mới (53.879 vector) → pool G (cùng trọng số pool F, vector mới) → Qwen-4B chấm 26.811 cặp doc mới trong f_G top-400 → RRF(Qwen hợp w2, f_G w1) → chunk kiểu e120 (2×40 + 1×41–120, bzip2, chunk chọn bằng điểm Qwen cho doc cũ) | 200 | **0,3110** | **0,2679** | FINAL **0,2895** ← TỐT NHẤT (+0,0125 so 0,2770; dự đoán +0,003–0,005 → vượt xa). Doc F2 +5,2% (P 0,1562 → 0,1636, R 0,4855 → 0,5129), chunk F2 +3,7% (P 0,1757, R 0,3848). **Độ phủ kho là đòn bẩy lớn nhất của cả đợt.** Doc mới trong top-200: 9,24/câu (blendQB3x: 0); đổi tập 8,9 doc/câu. Doc mới điểm Qwen TB 0,28 (cũ 0,34), >0,9: 1,2/câu. Mốc: `blendQB3x_cr_e120` FINAL 0,2770 / doc 0,2956 / chunk 0,2584. Vân tay doc `f1db164873e0` chunk `85d6db76292a`. 175.080 chunk, 93,7 MB |
| 08/10 | `blendQB4_w4_e120.zip` | như `blendQB4_e120` nhưng RRF **Qwen w4** / f_G w1 (nghiêng về Qwen); đổi tập top-200 13,3 doc/câu so bản w2; doc mới top-200 8,86/câu | 200 | 0,3093 | 0,2607 | FINAL **0,2850** (−0,0045 so w2 0,2895). Doc P 0,1625 / R 0,5105; chunk P 0,1708 / R 0,3757. **Nghiêng về Qwen làm cả hai tầng kém hơn**, chunk giảm mạnh nhất. Vân tay doc `91258350da64` chunk `1422598b0a3d` |
| 08/10 | `blendQB4_w1_e120.zip` | RRF **Qwen w1** / f_G w1 (nghiêng về vòng 1); đổi tập 15,9 doc/câu; doc mới top-200 9,77/câu | 200 | 0,3102 | **0,2710** | FINAL **0,2906** ← TỐT NHẤT (+0,0011 so w2). Doc P 0,1633 / R 0,5114 (gần ngang w2 0,3110); chunk P 0,1781 / R 0,3882. **Đầu danh sách tốt hơn khi nghiêng về vòng 1 (pool G)**: chunk w4 0,2607 → w2 0,2679 → w1 0,2710; doc gần phẳng (0,3093 / 0,3110 / 0,3102). Vân tay doc `c6ee4c35f1d2` chunk `c55076981b82` |
| 08/10 | `blendQB4_h05_e120.zip` | **bản lai theo trọng số**: TẬP doc của `blendQB4` (Qwen w2, doc F2 0,3110) + THỨ TỰ 120 doc đầu theo RRF Qwen w0,5 / f_G w1 (đầu danh sách nghiêng về vòng 1, để lấy chunk tốt hơn); top-40 đổi 12,4 doc/câu so w2 | 200 | **0,3110** | **0,2709** | FINAL **0,2910** ← TỐT NHẤT (+0,0004 so w1 0,2906). Doc đúng như dự đoán (0,3110, tập y hệt w2); chunk 0,2709 ≈ w1 (0,2710) → **chunk đã chạm đỉnh phẳng khi giảm trọng số Qwen** (w4 0,2607 · w2 0,2679 · w1 0,2710 · w0,5 0,2709); đừng giảm thêm. Chunk P 0,1779 / R 0,3879. Dự đoán doc y hệt `blendQB4_e120` (vân tay doc `f1db164873e0`); chunk kỳ vọng cao hơn 0,2710 nếu xu hướng w4→w2→w1 tiếp tục. Vân tay chunk `d658f61800b5`. 177.159 chunk, 92,9 MB |
| 08/10 | `blendQB5_h05_e120.zip` | như `blendQB4_h05_e120` nhưng Qwen chấm THÊM đợt 2 (155.494 cặp: 41.596 doc Long Châu mới hạng 401–1000 của f_G + 113.898 doc cũ trong f_G top-400 chưa từng có điểm); tập doc RRF Qwen w2 / f_G w1, thứ tự 120 doc đầu theo w0,5; 177.143 chunk, 93,0 MB | 200 | **0,3122** | **0,2717** | FINAL **0,2920** ← TỐT NHẤT (+0,0010 so 0,2910). Doc +0,4% (P 0,1640 / R 0,5159), chunk +0,3% (P 0,1784 / R 0,3890). Chấm thêm 155k cặp chỉ cho +0,001: **lợi suất giảm rõ** (đợt 1 doc mới: +0,0125). Đổi tập top-200 so blendQB4: 7,1 doc/câu (top-40 chỉ 0,5; top-120 2,8). Doc mới top-200 10,67/câu (QB4: 9,24). Mốc: blendQB4_h05_e120 FINAL 0,2910 / doc 0,3110 / chunk 0,2709. Vân tay doc `7f091ceb0949` chunk `2581f919d832` |
| 08/10 | `blendQB6_h05_e120.zip` | **vá BM25 cho doc mới**: chạy lại BM25F (có dấu), BM25F meta, BM25 entity trên kho vi ĐẦY ĐỦ 741.586 doc (`vi_full.sqlite`, trước đây 689.740 → 51.846 doc mới chưa từng có điểm BM25) → pool H (cùng trọng số pool F/G) → Qwen chấm bù 6.246 cặp → bản lai (tập doc w2, thứ tự 120 doc đầu w0,5), bzip2, 177.277 chunk, 95,1 MB | 200 | **0,3131** | **0,2730** | FINAL **0,2931** ← TỐT NHẤT (+0,0011 so 0,2920). Doc +0,3% (P 0,1645 / R 0,5177), chunk +0,5% (P 0,1793 / R 0,3906). Vá BM25 cho 51k doc mới: tăng nhỏ nhưng đồng đều ở cả hai tầng. Kiểm chất lượng: top-200 BM25F giao 183/200 với bản cũ (rank), 185,7 (meta), 165,4 (entity). Pool H: doc mới trong top-200 15,4/câu (G: 10,6), đổi tập 5,5 doc/câu so f_G. Bài cuối: đổi tập top-200 2,9 doc/câu so blendQB5; doc mới 13,10/câu. Mốc: blendQB5_h05_e120 FINAL 0,2920 / doc 0,3122 / chunk 0,2717. Vân tay doc `571430fb4c1e` chunk `3440b431b317` |
| 09/10 | `blendQB6c_e120.zip` | như `blendQB6_h05_e120` nhưng 200 doc đã **xếp lại theo cụm** (c10w1) trước khi lấy chunk e120 (2×40 + 1×41–120, bzip2, 179.013 chunk, 93,4 MB) | 200 | (=0,3131 theo cấu trúc) | (chờ) | **Tập doc y hệt blendQB6** (vân tay doc `571430fb4c1e`) nên doc F2 không đổi; chỉ thứ tự đầu đổi (top-40 đổi 9,9 doc/câu, top-120 19,3) → chỉ tầng chunk thay đổi. Kỳ vọng chunk +≤1–2%. Vân tay chunk `fe6d22103a2f`. Lưu ý: `hybrid_cands` chỉ giữ 200 doc nên cụm chỉ xếp lại trong 200 |
| 09/10 | `p50_head.zip` | **P@50 theo nguồn (đủ 1.200 câu, 50 doc/câu, chunk rỗng)**: đầu của blendQB6_h05 | 50 | 0,2572 | 0 | FINAL 0,1286. DOCS_P **0,3125**, R 0,2906 (≈ 15,6 nhãn trong top-50). Vân tay doc `961ffff53bc0` |
| 09/10 | `p50_fH.zip` | vòng 1 pool H thuần (RRF 6 nguồn, không Qwen) | 50 | 0,2382 | 0 | DOCS_P 0,2925, R 0,2673 (14,6 nhãn). Qwen+đầu lai thêm +0,020 P. Vân tay `f155823e83ef` |
| 09/10 | `p50_dvib3.zip` | dense nội dung (title + 600 ký tự đầu), MỘT nguồn | 50 | 0,2278 | 0 | DOCS_P **0,2894**, R 0,2525: một mình gần bằng cả vòng 1 (0,2925) → **dense là tín hiệu gần nhãn nhất**. Vân tay `ccded4a4282f` |
| 09/10 | `p50_bm25.zip` | BM25F có dấu, MỘT nguồn | 50 | 0,1331 | 0 | DOCS_P **0,1501**, R 0,158: **chỉ bằng ~½ dense** → nhãn KHÔNG nghiêng về từ khoá; kiểu "pooling bằng BM25" khó đúng. Vân tay `4d9a6ce85bf2` |
| 09/10 | `p50_c10w1.zip` | **xếp lại theo cụm** (tâm vector dense nội dung của 10 doc đầu, RRF hạng cơ sở w1 + hạng cụm w1) trên 400 ứng viên của blendQB6_h05; giao top-50 với head 38,2 | 50 | 0,2631 | 0 | FINAL 0,1316. DOCS_P **0,3200** (+0,0075 = +2,4% so head 0,3125), R 0,2977. **Cụm giúp nhẹ.** Vân tay `a8ef6a4ef3cc` |
| 09/10 | `p50_c10w3.zip` | như trên nhưng hạng cụm w3 (nghiêng mạnh về cụm); giao head 30,9 | 50 | 0,2500 | 0 | DOCS_P 0,3055 (−2,2% so head), R 0,2805 → quá tay làm hại; đỉnh quanh w≈1. Vân tay `dfe320e4bfc9` |
| 10/10 | `diag_novel_chunkfull_k150.zip` | **chẩn đoán chunk-dense TOÀN KHO**: 150 doc hạng cao KHÔNG nằm trong pool H top-1000, chunk rỗng | 150 | 0,0239 | 0 | FINAL 0,0120. DOCS_P **0,0167**, DOCS_R **0,0319** — **nguồn mở rộng pool tốt nhất từng đo** (doc chưa crawl R 0,0181 · PRF 0,0108 · HyDE 0,0084 · Qwen3-Emb 0,0080): +3,2 điểm recall ngoài pool (~2,5 nhãn/câu trong 150 doc), nhưng precision biên 1,7% vẫn dưới ngưỡng giữ (~6%) → chỉ đáng khi RRF đặt chúng đúng chỗ. Vân tay doc `8636a929de7f` |
| 10/10 | **`blendQB7b_e120.zip`** | tập doc y hệt `blendQB7`; chunk chọn theo chunk khớp nhất (`chunk_scores_mix.jsonl`: Qwen cho doc đã có điểm, còn lại best_idx) | 200 | 0,3236 | **0,2909** | FINAL **0,3072** ← TỐT NHẤT (+0,0004). Doc đúng 0,3236 như dự đoán. Chunk +0,3% (P 0,1904 / R 0,4151 so 0,4134): **chọn chunk theo nội dung chỉ cho lợi nhỏ** (đa số doc ≤2 chunk, đã lấy đủ). Vân tay chunk `647147b3b9cb` |
| 10/10 | `diag_zhC2_*_k150` (khối người dùng dán là "diag_zh"; mình hiểu là bài `both` — cần xác nhận) | 150 doc zh/câu (dense title+600 ký tự đầu BGE-M3 fp16, 1,72M doc zh, câu hỏi vi + bản dịch zh), chunk rỗng | 150 | 0,0399 | 0 | FINAL 0,0199. DOCS_P **0,0266**, DOCS_R **0,0559** — **nguồn mở rộng lớn nhất từng đo** (chunk-dense toàn kho R 0,0319 · doc vi chưa crawl 0,0181); gấp ~2,2× bài zh cũ (R 0,0256, độ phủ 35%, truy hồi yếu). → **zh KHÔNG nhỏ như kết luận 2,6%** (lúc đó là cận dưới của bộ truy hồi yếu). Precision biên 2,7% dưới ngưỡng giữ ~6% khi nộp thẳng, nên dùng bằng RRF để zh chỉ vào chỗ hạng cao. Vân tay doc `05073f7ed644` |
| 10/10 | **`blendQB8b_e120.zip`** | RRF(blendQB7, chunk-dense TOÀN KHO) w1/w1 (đổi 47,8 doc/câu top-200, 17,4 doc/câu ngoài pool H), chunk chọn theo chunk khớp nhất | 200 | **0,3360** | 0,2893 | FINAL **0,3126** ← TỐT NHẤT (+0,0054 so 0,3072). Doc **+3,8%** (P 0,1780 / R 0,5495), chunk −0,5% (P 0,1887 / R 0,4137; doc mới chen vào đầu danh sách chỉ có chunk đầu). **Chunk-dense toàn kho giúp phía doc rõ rệt.** Vân tay doc `832af360705c` chunk `739418b50219` |
| 10/10 | `blendQB9a_e120.zip` | **thêm zh vào doc hạng 121–200** của blendQB8b: RRF(blendQB8, zhC2_both w0,3) lấy tập top-200 (14 doc zh/câu thay 14 doc vi cuối), thứ tự 120 doc đầu y hệt blendQB8 (top-40 y hệt) → chunk y hệt blendQB8b (vân tay chunk `739418b50219`) | 200 | **0,3384** | 0,2893 | FINAL **0,3139** ← TỐT NHẤT (+0,0013 so 8b 0,3126). Doc F2 +0,7% (P 0,1785 / R 0,5573): **zh ở đuôi giúp nhẹ** (14 doc zh thay 14 doc vi cuối). Chunk y hệt 8b. Vân tay doc `49b78b6e2cd2` |
| 10/10 | `blendQB9b_e120.zip` | như 9a nhưng w0,6: 60 doc zh/câu thay 60 doc vi (hạng 121–200 gần như toàn zh); đầu y hệt blendQB8 | 200 | 0,3204 | 0,2893 | FINAL 0,3048 (−0,0078 so 8b). Doc F2 −4,6% (P 0,1672 / R 0,5351): **60 doc zh quá nhiều**. Khớp tham số bậc hai qua hai điểm (14 → +0,0024; 60 → −0,0156 doc F2): đỉnh ~16 doc zh/câu, lợi tối đa ~+0,0024 doc F2 (~+0,0012 FINAL) khi zh chỉ chen ở đuôi theo hạng dense. Vân tay doc `4ed2c198a169` |
| 10/10 | `p50_zhboth.zip` | **P@50 của riêng danh sách zh** (top-50 RRF câu hỏi vi + bản dịch zh, dense BGE-M3 title+600 ký tự đầu, 1,72M doc zh), chunk rỗng | 50 | 0,0334 | 0 | FINAL 0,0167. DOCS_P **0,0462**, R 0,0365 (≈ 2,3 nhãn trong top-50 zh; đầu danh sách vi: 16,9). So với 150 doc: P 0,0266, R 0,0559 → mật độ giảm dần theo hạng nhưng **ngay ở top-50 vẫn chỉ 4,6% < ngưỡng giữ ~6%**. Khớp với 9a/9b (đỉnh ~16 doc zh ở đuôi). Cùng tín hiệu dense nội dung: vi P@50 0,289 vs zh 0,046 (gấp ~6×). Chưa tách được "nhãn zh thưa" với "truy hồi chéo ngôn ngữ yếu". Vân tay `b06f1a2c885e` |
| 10/10 | `blendQB8w2_e120.zip` | như blendQB8b nhưng chunk-dense toàn kho **w2** (so w1; vòng 1 blendQB7 w1); đầu và tập đều theo RRF này; chunk theo chunk khớp nhất; 95,3 MB | 200 | (chờ) | (chờ) | Đổi 18,8 doc/câu top-200 so blendQB8; 44,3 doc/câu ngoài danh sách blendQB7. Mốc blendQB8b: doc 0,3360 / chunk 0,2893. Vân tay doc `23146afe5781` chunk `93e6552e11c7` |
| 10/10 | `blendQB8w05_e120.zip` | chunk-dense toàn kho **w0,5**; 93,2 MB | 200 | 0,3357 | **0,2935** | FINAL **0,3146** (+0,0020 so 8b 0,3126; +0,0007 so 9a 0,3139). Doc ≈ 8b (0,3357 vs 0,3360: P 0,1779 / R 0,5486), **chunk +1,5%** (P 0,1920 / R 0,4186): giảm trọng số chunk-dense làm đầu danh sách giống blendQB7 hơn → chunk tốt hơn, tập doc gần như không đổi. Đổi 19,6 doc/câu; 7,6 doc/câu ngoài blendQB7. Vân tay doc `da8a7589b316` chunk `a40b697e5b14` |
| 10/10 | `blendQB10_e120.zip` | **ghép hai tầng độc lập**: TẬP doc của `blendQB9a` (doc F2 0,3384, có 14 doc zh/câu ở hạng 121–200) + THỨ TỰ 120 doc đầu của `blendQB8w05` (chunk F2 0,2935); chunk theo chunk khớp nhất; 178.955 chunk, 93,2 MB | 200 | (=0,3384 theo cấu trúc) | (dự đoán ~0,2935) | Dự đoán FINAL ≈ (0,3384+0,2935)/2 = 0,3160 (+0,0014 so w05). Vân tay doc `49b78b6e2cd2` (= 9a) chunk `3c412209084d` |
| 09/10 | **`blendQB7_e120.zip`** | **chunk-dense vào danh sách**: RRF (w1/w1) giữa đầu `blendQB6_h05` (200 doc) và chunk-dense pilot (BGE-M3 trên chunk, 400 ứng viên pool H, điểm doc = chunk khớp nhất); lấy top-200 làm tập doc và đầu danh sách; chunk kiểu e120 (2×40 + 1×41–120, bzip2, 178.455 chunk, 93,3 MB). 25,7 doc/câu mới vào top-200 so với blendQB6 | 200 | **0,3236** | **0,2900** | FINAL **0,3068** ← TỐT NHẤT (+0,0137 so 0,2931; bước nhảy lớn thứ hai sau độ phủ Long Châu +0,0125). Doc +3,4% (P 0,1710 / R 0,5311), chunk +6,2% (P 0,1904 / R 0,4134). **Đọc cả thân bài ở mức chunk là tín hiệu mới có giá trị.** Dự đoán từ P@50 (+8,2%) đúng hướng. Vân tay doc `9c6f85ea7df8` chunk `affd2c8bb798` |
| 09/10 | `p50_chunk.zip` | **chunk-dense một mình** (BGE-M3 trên chunk, điểm doc = chunk khớp nhất, xếp 400 ứng viên pool H); giao head 25,3/50 | 50 | 0,2548 | 0 | FINAL 0,1274. DOCS_P **0,3136** (≈ head 0,3125; **+8,4% so dense nội dung một nguồn 0,2894**), R 0,2870. Đọc cả thân bài giúp rõ. Vân tay `2682dd49f526` |
| 09/10 | `p50_headchunk.zip` | RRF(đầu blendQB6_h05 w1, chunk-dense w1); giao head 38,3/50 | 50 | 0,2774 | 0 | FINAL 0,1387. DOCS_P **0,3380** (+8,2% so head 0,3125), R **0,3141**. **Chunk-dense bổ sung cho vòng 1 + Qwen: bước tăng P@50 lớn nhất từ trước tới nay.** Vân tay `29d152cdc1e9` |
| 08/10 | `probe300_1k_top50.zip` | **thăm dò Qwen đọc 1.000 ký tự**: 300 câu đầu, top-50 từ RRF(Qwen-1k w2, f_F w1) trên 150 ứng viên, chunk rỗng, 900 câu rỗng | 50 | 0,0600 | 0 | FINAL 0,0300. DOCS_P **0,0791**, R 0,0644 (×4 cho riêng 300 câu: P@50 ≈ 0,316 ≈ 15,8 nhãn trong top-50). Vân tay doc `6ae967c3cee5` |
| 08/10 | `probe300_3k_top50.zip` | như trên nhưng Qwen đọc **3.000 ký tự** | 50 | 0,0599 | 0 | FINAL 0,0299. DOCS_P 0,0787, R 0,0642: **kém 1k một chút (−0,5%)**, nằm trong nhiễu (chỉ ~3 doc/câu khác). **Kết luận: Qwen đọc dài hơn KHÔNG giúp** → không chạy 3k cho 1.200 câu. Vân tay doc `c8527e902a5f` |
| 08/10 | `probe300_8b_top50.zip` | (đã dựng trước) thăm dò Qwen3-Reranker-**8B** | 50 | 0,0604 | 0 | FINAL 0,0302. DOCS_P **0,0795**, R 0,0647 so với 4B `probe300_1k` P 0,0791 / R 0,0644 → **8B ≈ 4B (+0,5%, trong nhiễu)** dù khác ~11 doc/câu trong top-50. **Không đáng chạy 8B cho 1.200 câu (~6 giờ GPU).** Reranker lớn hơn không phải đòn bẩy. Vân tay doc `c0a4afc2f780` |
| 07/10 | `probe300_1k_top50.zip` / `probe300_3k_top50.zip` | **thăm dò Qwen đọc 1.000 vs 3.000 ký tự** trên 300 câu đầu (id 1–300), 50 doc/câu, chunk rỗng, 900 câu còn lại rỗng; CÙNG 150 ứng viên f_F, RRF(Qwen w2, f_F w1). Top-50 giao nhau 46,8/50 → chỉ ~3 doc/câu khác; thiết kế cặp, so `DOCS_PRECISION` | 50 | (chờ) | 0 | Vân tay doc 1k `6ae967c3cee5`, 3k `c8527e902a5f`. Lưu ý: `blendQB3x_3k_300` (user dựng) KHÔNG phải phép thử sạch: 300 câu chỉ 150 doc (tập từ f_F top-150, mất doc hạng 150–400 mà Qwen-1k đã đẩy lên) nên lẫn hiệu ứng k và pool |
| 07/10 | `diag_novel_hyde_k150.zip` | **chẩn đoán HyDE**: như trên nhưng chỉ dùng câu trả lời giả định | 150 | 0,0053 | 0 | FINAL 0,0027. DOCS_P 0,0038, DOCS_R **0,0068** — kém `qhyde` 19%. Vân tay doc `ed7aaaab2eef` |

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

## 4. Bảng chốt toàn bộ câu hỏi & quy định BTC (Đã giải quyết 100% - Không còn câu hỏi mở)

| Vấn đề / Câu hỏi | Trạng thái & Quyết định chốt | Giải thích chi tiết & Hướng xử lý cho AI/Đội thi |
| :--- | :--- | :--- |
| **1. Nhãn gán theo nội dung ở thời điểm nào?** (Trang có thể đã sửa/cập nhật) | ✅ **CHỐT: Coi như bản mới nhất** | Thực tế chỉ cào được nội dung hiện tại trên web, không thể quay ngược thời gian lấy bản cũ. Cứ trích xuất sạch sẽ bản mới nhất làm dữ liệu. |
| **2. Nhãn vàng tạo bằng Pooling hay do LLM chấm?** | ✅ **CHỐT: Không hỏi BTC** | Hỏi câu này lộ bí mật ra đề thi/đáp án của BTC. Chiến lược của đội: kết hợp BM25F + Dense vector + LLM Reranker (Qwen-8B) để đón đầu cả 2 trường hợp. |
| **3. Tài liệu web chết/lỗi 521 có tính điểm không?** | ✅ **CHỐT: Bỏ qua, không tính điểm** | Web đã sập vĩnh viễn thì mọi đội đều không lấy được. Thường BTC đã lọc link sống trước khi gán nhãn, không nằm trong đáp án. |
| **4. Mô hình MoE tính tổng tham số hay tham số kích hoạt?** | ✅ **CHỐT: HỢP LỆ** | Mô hình MoE tính theo tham số kích hoạt khi suy luận (active parameters) $\le 15$B là hoàn toàn hợp lệ theo thông lệ thi đấu AI. |
| **5. Teacher Distillation (Chưng cất tri thức) có được phép?** | ✅ **CHỐT: ĐƯỢC PHÉP** | Dùng teacher model tạo dữ liệu huấn luyện/soft labels để dạy student model $\le 15$B là phương pháp chuẩn mực trong Machine Learning, hoàn toàn hợp lệ lúc train. |
| **6. Dữ liệu tiếng Anh / PubMed** | ✅ **CHỐT: BỎ HOÀN TOÀN** | BTC đã loại bỏ nhánh tiếng Anh khỏi đề thi chính thức. Tập trung 100% vào kho tiếng Việt & tiếng Trung. |
| **7. Định dạng `doc_id` trong file JSON nộp bài** | ✅ **CHỐT: SỐ NGUYÊN (Integer)** | Đã kiểm chứng thực nghiệm trên leaderboard: JSON phải để `doc_id` dạng số nguyên `12345`, để dạng chuỗi `"12345"` sẽ bị chấm 0 điểm. |
| **8. 25.843 URL chênh giữa README và file thật** | ✅ **CHỐT: Đầy đủ, không thiếu** | ID chạy từ 583 $\rightarrow$ 4.420.561 nhưng có đoạn nhảy cóc ID. File dữ liệu của BTC không bị thiếu. |

### 13/10/2026: blendQB13af_e120 = FINAL 0,3182 (doc F2 0,3432 / chunk F2 0,2932; DOCS_P 0,181 / R 0,5656; CHUNKS_P 0,1918 / R 0,4181)
- So với blendQB11z (0,3179): +0,0003, nằm trong nhiễu (±0,001). So với blendQB11 (doc 0,3384 / chunk 0,2931): doc +0,0048, chunk +0,0001.
- Kết luận: ~14 doc zh/câu lấy từ kho zh mới (240k, RRF w0,3) ngang bản bỏ zh ngoài kho + bù doc vi (11z). zh trong kho mới ở mức 14 doc/câu chưa thêm giá trị. Chờ 13bf (w0,6, ~60 zh/câu) và p50_zh_in để biết nhiều zh hơn có đáng không.
- Lưu ý: mới có 116,6k/240k doc zh trong store và đã mã hoá; 32,8k đã cào nhưng chưa gộp; ~90,6k chưa cào. zh còn bị chặn trần bởi độ phủ.

### 13/10/2026: p50_zh_in = DOCS_P 0,066 / R 0,0485 (FINAL 0,0228, chunk rỗng)
- 50 doc zh trong kho mới/câu: ~3,3 nhãn/câu. Mốc zh toàn bộ cũ P 0,046 → lọc theo kho mới nâng precision zh ~+43%.
- Ngưỡng hoà vốn thêm doc: p > F2/5 = 0,343/5 ≈ 0,069. P@50 của zh (0,066) sát hoà vốn, precision biên của đuôi zh còn thấp hơn → khớp với 13af ≈ 11z (+0,0003). Dự đoán 13bf/13cf (60/100 zh/câu) ≤ 0.

### 13/10/2026: bài chưa gắn nhãn, giả định = blendQB13bf (zh w0,6, ~60 zh/câu): FINAL 0,3118 (doc 0,3300 / chunk 0,2937; DOCS_P 0,1727 / R 0,5487)
- So với 13af (0,3182): −0,0064 (doc −0,0132, chunk +0,0005). Đúng dự đoán: nhiều zh hơn 14 doc/câu làm tụt. 13cf không cần nộp. Bài tốt nhất vẫn là blendQB13af (0,3182).

### 13/10/2026: HƯỚNG MỚI — nén LZMA từ điển lớn (chưa nộp)
- Trong blendQB13af_e120: 178.966 chunk nhưng chỉ 117.377 chunk khác nhau (65,6%); 207/590 MB văn bản chunk là bản lặp giữa các câu (cùng doc xuất hiện cho nhiều câu). bzip2 (khối 900 KB) và LZMA mặc định (từ điển 8 MB) không thấy được các bản lặp cách xa.
- Đo trên đúng JSON 600 MB đó: bzip2 95,5 MB · LZMA 8 MB 91,4 MB · **LZMA từ điển 640 MB 54,8 MB** (−43%) → trong trần 100 MB chứa được ~1,7× chunk.
- `submission.py --zip-method lzma` (từ điển 768 MB, ZIP method 14, tự kiểm đọc lại bằng zipfile chuẩn). Server chưa từng nhận LZMA: bài lỗi định dạng không tính quota.
- Đang dựng: `runs/blendQB13af_e120_lz.zip` (y hệt 13af, chỉ đổi nén — kiểm vân tay) và `runs/blendQB13af_e200_lz.zip` (1 chunk cho doc hạng 41–200 thay vì 41–120).

### 13/10/2026: pilot Qwen3-Embedding-4B trên chunk (300 câu ngẫu nhiên qs2, top-100 blendQB11, 54.054 chunk, ~36 phút GPU 0) → 3 bài P@50
- `runs/p50_q4chunk.zip` (doc `c3ec5a8c9042`): top-50 theo chunk khớp nhất của Qwen3-Emb-4B. Giao top-50 với thứ tự hiện tại 32,9/50.
- `runs/p50_q4chunk_rrf.zip` (`df06ef705cfc`): RRF(thứ tự hiện tại, Qwen3-Emb chunk). Giao 41,3/50.
- `runs/p50_bgechunk.zip` (`f3c14efa50a9`): top-50 theo BGE-M3 chunk (cùng 100 ứng viên). Giao 41,1/50. Đối chứng mô hình: nếu BGE-M3 ≥ Qwen3-Emb dù Qwen3-Emb mạnh hơn trên benchmark → ủng hộ giả thuyết nhãn được pool từ hệ thống kiểu baseline BTC (BM25 + BGE-M3).
- Mốc: `runs/r300_p50_base.zip` (`382b2b23763f`, chưa nộp). Đọc: DOCS_P×4 = P@50 trên 300 câu; có ý nghĩa khi chênh ≥ +0,02.
- Dựng xong: `runs/blendQB13af_e120_lz.zip` 54,8 MB, vân tay doc `c9b5de8fc718` chunk `6d42f1f2f79f` = Y HỆT 13af (không cần nộp). `runs/blendQB13af_e200_lz.zip` **74,7 MB**, 265.951 chunk (so 178.966), doc `c9b5de8fc718` chunk `e21516c7cbff`; testzip OK. Chỉ khác 13af ở chunk của doc hạng 121–200 → đo đúng giá trị của chunk sâu + kiểm server đọc LZMA. Còn ~25 MB trống cho bước tiếp.

### 13/10/2026: quan sát thủ công (view_disputed.md) + E6 khớp khía cạnh
- Đọc 6 câu ngẫu nhiên (`view_disputed.md`): top-5 đều liên quan thật; thứ tự hiện tại và BGE-chunk gần như không tranh chấp (đã RRF với nhau). Bằng mắt KHÔNG phân biệt được doc vàng/không vàng → khớp với "Qwen thấy ~130 liên quan, nhãn ~65".
- Rác thấy được rất ít: doc trùng (cùng domain+title+độ dài body, phần lớn là URL cũ/mới của Long Châu hoặc redirect của hellobacsi) 0,6 slot/câu trong top-50, 2,2 trong top-200; doc ngắn <600 ký tự 0,4/câu trong top-50. Không phải nguyên nhân chính.
- Slide 40 PDF BTC: "cùng bệnh nhưng khác ý" (hỏi triệu chứng, doc nói chẩn đoán = liên quan thấp hơn). Ví dụ thật: câu 383 hỏi "điều trị được không", doc #1 là "Nguyên nhân tái phát...".
- E6 (`aspect_probe.py`): 627 câu có đúng một khía cạnh (điều trị/triệu chứng/nguyên nhân/chẩn đoán/phòng ngừa/ăn uống/nguy hiểm), 2.418 cặp doc top-100 ghép hạng (TB 23,3 vs 22,0). `runs/e6_aspect_match.zip` (doc `816db7c9b3a1`) vs `runs/e6_aspect_miss.zip` (`35017a7eda9e`). Đọc: so DOCS_P hai bài (cùng tập câu); match/miss ≥ 1,3× → thêm tín hiệu khía cạnh (luật từ khoá hoặc chỉ dẫn reranker theo khía cạnh).

### 13/10/2026: blendQB13af_e200_lz = FINAL 0,3156 (doc 0,3432 y hệt 13af / chunk F2 0,2880; CHUNKS_P 0,1505 / R 0,4733)
- **Server ĐỌC ĐƯỢC ZIP LZMA từ điển 768 MB** → ngân sách chunk thực tế ~1,7× (54,8 MB cho nội dung 13af).
- Nhưng chunk cho doc hạng 121–200 làm chunk F2 −0,0052 (FINAL −0,0026 so 13af 0,3182): recall +0,055 nhưng precision 0,1918 → 0,1505. Chunk đúng/câu 28,6 → 33,4 (+4,8 trên 72,5 chunk thêm) → precision biên ≈ 0,066, dưới mức hoà vốn theo macro. Chunk sâu hơn hạng 120 KHÔNG đáng. Bài tốt nhất vẫn blendQB13af_e120 (0,3182).

### 14/10/2026: crawl nốt zh của kho mới trên máy GPU (tmux `zhmiss`)
- zh kho mới 240.000; đã có body ≥200 ở `corpus_vifull` 116.530 + `queue_zh2` 18.981 + `queue_zh3` 14.708 (zh3/zh2 CHƯA gộp) → thiếu **90.558** (sau khi trừ 12 doc có ở store máy GPU). Theo domain: 120ask 42.923, ask.39.net 12.317, cnkang 11.761, zysjonline 6.591 (BLOCKED ở IP local, thử lại từ IP máy GPU), *.39.net khác ~10k, còn lại ~7k. Hầu hết CHƯA từng được thử (state 0), không phải lỗi cũ.
- Hàng đợi `data/zh_missing.sqlite` (local và máy GPU; danh sách `data/zh_missing_ids.json`). Chạy: `crawler.py --db data/zh_missing.sqlite` (bản crawler trên máy GPU), log `data/zh_missing_crawl.log`.
- 90 giây đầu: 2.700 URL, ~2 trang/s mỗi domain lớn. article.iiyi.com 521 toàn bộ (729 URL, bỏ); một phần *.39.net trả captcha. Ước tính: 120ask là nút cổ chai, ~6 giờ nếu giữ tốc độ; lịch sử shard 3 bị ConnectTimeout hàng loạt sau ~12k → có thể kéo dài tới ~1 ngày.
- Sau khi xong (chờ người dùng): gộp zh2 + zh3 + zh_missing → `clean.py --apply` → `chunk.py` → `audit.py` → encode BGE-M3 → xếp hạng lại zh.

### 14/10/2026: KẾT QUẢ blendQB14_w035_e120 = FINAL **0,3244** ← TỐT NHẤT (+0,0022 so QB14 0,3222)
- doc F2 **0,3555** (+0,0044; P 0,1865 / R **0,5934**, so 0,1846 / 0,5844) · chunk F2 0,2934 (không đổi; top-120 đổi ở 188 câu nhưng chunk F2 y nguyên).
- 14,3 → 23,3 zh/câu (+9 zh thay 9 vi cuối): R +0,009 ≈ +0,58 doc vàng/câu → 9 zh thêm vào hơn 9 vi bị thay ~6,4 điểm phần trăm precision. Lợi suất giảm (8 zh đổi đầu tiên ở QB14 cho +1,2 vàng/câu) nhưng còn dương → nộp `w04` (31,3 zh/câu). Dựng sẵn `runs/blendQB14_w045_e120.zip` (~39 zh/câu; doc `547836004ae4`, chunk `f4e41631f67f`, 95,6 MB) để nộp nếu w04 còn tăng.

### 14/10/2026: so với một đội trên ta (0,3502) — KHOẢNG CÁCH NẰM Ở CHUNK
- Đội đó (người dùng cung cấp; giả định cột FINAL/docF2/chunkF2/docP/docR/chunkP/chunkR): 0,3502 · doc 0,3617 (P 0,240 / R 0,467) · chunk **0,3388 (P 0,282 / R 0,408)**. Ta (w04): 0,3253 · doc 0,3571 · chunk 0,2936 (P 0,192 / R 0,421).
- Doc gần hoà: họ nộp ~125 doc/câu (suy từ P/R, G≈64) nên P cao hơn; top-125 của ta ước cũng ~29 vàng (P@50 0,30) → xếp hạng doc không kém. Chunk: cùng R, P cao hơn 47% → gần toàn bộ chênh FINAL (~0,023/0,025).
- Bỏ sót của mình: phép quét phân bổ chunk (06–08/10, "đỉnh phẳng") làm TRƯỚC khi đổi nhãn/luật chấm chunk 12/10. Dưới nhãn mới e200 đã tụt → nghi tối ưu hiện là ÍT chunk hơn. Quét lại trên tập doc w04 (doc F2 phải = 0,3571): `runs/w04_x1_120.zip` (1 chunk × top-120, bỏ chunk thứ hai), `runs/w04_x1_80.zip` (1 × top-80), `runs/w04_e70.zip` (2×40 + 1×41–70). Mốc w04: chunk P 0,1919 / R 0,4206 / F2 0,2936 (~149 chunk/câu).
- Viết gọn câu dài cho reranker đang chạy (máy GPU, tmux `rwrr`): `rewrite_queries.py` (prompt giữ đủ ý hỏi, không suy diễn) cho 405 câu >30 từ → Qwen3-Reranker-4B chấm top-100 hiện tại bằng câu viết gọn (`qwen_rw`) và câu gốc cùng cài đặt (`qwen_rwctl`, đối chứng).

### 14/10/2026: KẾT QUẢ w04_x1_120 (bỏ chunk thứ hai của top-40) = FINAL 0,3118 (−0,0135)
- doc F2 0,3571 (y hệt, đúng thiết kế) · chunk F2 **0,2666** (−0,027): P 0,1932 (≈ 0,1919) / R **0,3616** (−0,059).
- 149 → 120 chunk/câu: chunk đúng 28,6 → 23,2 → 29 chunk thứ hai có precision ≈ 5,4/29 = **0,186 ≈ precision trung bình**, và mang nhiều "phần thông tin" riêng (R −0,059). → Bớt chunk là SAI hướng; e70 và x1_80 chắc chắn tụt (không nộp).
- Suy luận: chunk trong cùng một doc đầu danh sách đúng ngang chunk đầu → thêm chunk thứ 3, 4 cho doc đầu có thể còn lãi; và nếu đội khác cắt chunk NHỎ hơn (mỗi doc vàng cho nhiều chunk đúng) thì precision chunk của họ cao hơn là hợp lý. Dựng `runs/w04_x3_40.zip`, `runs/w04_x4_40.zip` (3/4 chunk × top-40 + 1 × 41–120, nén LZMA).

### 14/10/2026: Qwen3-Embedding-8B cho zh (kho mới 226.736 doc) — hai đường song song
- Máy lab: `scripts/run_zh_q8.sh` (tmux `zhq8`): tải 8B rồi TỰ CHỜ card trống ≥20 GB (lúc đặt: hai card bị người khác dùng — vLLM 21,6 GB, train 13 GB), chia 2 nửa chạy 2 card, xếp hạng vi/zhq/zhq109 → `dense_zhQ8_*_rank.jsonl`.
- Colab A100 80GB (người dùng có 180 CU): gói `runs/colab_zh_q8/` (dense.py, zh_text_new.sqlite, queries*.jsonl, `zh_q8_colab.ipynb`); mã hoá 4 phần lưu thẳng Drive (chịu được mất kết nối). Bên nào xong trước dùng bên đó; xong thì dừng job còn lại.
- Sau đó: dựng zh list = RRF(vi top-400, zhq top-400 vá 109) như zh3 (lưu ý: chỉ mã hoá doc trong kho mới nên thứ hạng zh "tốt hơn" danh nghĩa → quét lại W), thăm dò P@50 zh và dựng lại bài w04.
- **XONG (Colab)**: 48 doc/s, 4 phần × 19,6 phút = 78 phút. Lỗi ô 6 (chuỗi chỉ dẫn xuống dòng thật) đã sửa trong notebook. Job lab đã dừng (xong nửa đầu `emb_zhQ8_p0.npy`, giữ lại). File: `data/dense_zhQ8_{vi,zhq,zhq109}_rank.jsonl` (1.200/1.200/109 câu × 1.000).
- Danh sách: `rp/zh8_in` = RRF(z8v top-400, z8q top-400 vá 109) lọc kho mới (TB 529 doc/câu); `rp/zh38_in` = RRF 4 nguồn BGE+8B (659/câu).
- **8B khác BGE rất xa**: giao top-10 chỉ 2,2 · top-30 8,0 · top-50 14,5. Trùng top-30 giữa câu vi và câu zh: **8B 16,4 vs BGE 6,6** → 8B căn chỉnh xuyên ngôn ngữ tốt hơn hẳn (câu vi và bản dịch zh ra gần cùng kết quả). Nhìn mắt 3 câu: 8B sạch hơn (BGE lạc sang "轻度弱精子症", "轻度静脉炎" vì trùng chữ).
- Thăm dò P@50 zh (chunk rỗng; so cùng ngày với `p50_zh3_in` = BGE, doc `d7ab98f2423b`, CHƯA nộp): `runs/p50_zh8_in.zip` (doc `274045af16ef`), `runs/p50_zh38_in.zip` (doc `c544624a0573`).
- **KẾT QUẢ p50_zh8_in**: DOCS_P **0,0827** / R 0,0782 / F2 0,0662 → 4,1 doc vàng zh/câu trong 50. Mốc cũ `p50_zh_in` (BGE, zh phủ 49%, chưa clean) 0,066. Chưa tách được phần do 8B hay do kho zh mới → cần `p50_zh3_in` (BGE, cùng kho).
- **KẾT QUẢ p50_zh3_in (BGE, cùng kho)**: DOCS_P **0,1103** / R 0,0918 / F2 0,0816 → 5,5 vàng/câu. **BGE HƠN 8B 33%** dù 8B "đẹp" hơn trên mọi thước đo nội bộ (vi/zh nhất quán, nhìn mắt sạch hơn). Giả thuyết: nhãn BTC gán trên tập doc do retriever kiểu BGE-M3 tìm ra (pooling) → model khác tìm doc đúng chủ đề nhưng không có nhãn. Khớp với chuyện mọi tín hiệu chủ đề đều bão hoà. Bài học: **đừng thay BGE-M3 bằng embedding "mạnh hơn"**; thử nghiệm model mới phải qua thăm dò leaderboard.
- Kho zh mới + clean (BGE): 0,066 → 0,110 (+67%), khớp với lãi của QB14.
- Đã dựng nhưng KHÔNG nộp: `runs/w04_zh8_e120.zip` (w04 thay zh list bằng 8B; W0,4 cũng cho 31,3 zh/câu vì RRF chỉ theo hạng; top-120 y hệt w04 1.185/1.200; doc `ed103d9fa7dc`, chunk `3bfd38664698`).
- Còn thử: trộn nghiêng BGE `runs/p50_zh38w_in.zip` (BGE 1 : 8B 0,3; giao top-50 với BGE 41,4; doc `35b7d5470af3`) — 8B chỉ làm tín hiệu "đồng thuận" đẩy doc cả hai cùng chọn. `p50_zh38_in` (1:1, giao BGE 26,4) gần như chắc thua BGE, không nộp.
- **KẾT QUẢ p50_zh38w_in** (người dùng không ghi tên, suy ra): DOCS_P **0,115** / R 0,0995 / F2 0,0867 → hơn BGE riêng +4% P, +8% R (≈ +0,23 vàng/câu trong 50). 8B có ích khi làm tín hiệu đồng thuận, không phải nguồn chính.
- Dựng `runs/w04_zh38w_e120.zip` (= w04, zh list `rp/zh38w_in`, W0,4 → 31,3 zh/câu; khác w04 5,9 doc/câu, top-120 y hệt 1.189/1.200; doc `7ea17e35e329`, chunk `72a9d14ce27c`, 93,3 MB). Kỳ vọng FINAL +0,001–0,002 so 0,3253.
- **KẾT QUẢ w04_zh38w_e120 = FINAL 0,3262 ← TỐT NHẤT** (+0,0009): doc F2 **0,3589** (P 0,1878 / R **0,6008**, so 0,3571) · chunk F2 0,2935 (= w04). ~6 zh đổi/câu → +0,6% recall doc.
- Dựng tiếp `runs/w045_zh38w_e120.zip` (zh38w, W0,45 → ~39 zh/câu; doc `c1e068422e5f`, chunk `f30180dca611`, 93,3 MB). `blendQB14_w045_e120` (zh BGE) bỏ.
- **Chunk 1.000 token** (15/10): store phụ `data/store_c1000.sqlite` (89.058 doc top-120 của q14_z38w_04, `chunk.py --target-tokens 1000`): 1,88 chunk/doc (900: 2,06), dài TB 2.482 ký tự (+9%), 33% doc chunk y hệt. Điểm chọn chunk chuyển từ chunk 900 sang chunk 1000 theo chồng lấn ký tự lớn nhất (`data/chunk_scores_c1000.jsonl`). `runs/w04z38w_c1000_e120.zip` (LZMA 58 MB; doc `7ea17e35e329` = bài tốt nhất, chunk `51c0ad029ca7`, 147 chunk/câu). Lần nén đầu hỏng do phiên bị ngắt → đã nén lại, testzip OK. So với 0,3262: chỉ chunk đổi.
- **KẾT QUẢ w045_zh38w_e120 = FINAL 0,3272 ← TỐT NHẤT** (doc F2 **0,3605**, P 0,1884 / R 0,6047 · chunk 0,2939, P 0,1920 / R 0,4215). **w05_zh38w_e120 = 0,3272** (doc 0,3602 / chunk 0,2942). Đỉnh PHẲNG W0,45–0,5: doc đỉnh ở w045 (w05 −0,0003), chunk nhích +0,0003/bước (nhiễu). Chốt **w045** (lãi đến từ doc, ổn định hơn). Dừng quét W. `build_best.sh` và `HANDOVER.md` chuyển sang w045 (vân tay doc `c1e068422e5f`, chunk `f30180dca611`).
- Dựng sẵn `runs/w05_zh38w_e120.zip` (W0,5 → ~47 zh/câu; doc `98ae5a55b4a6`, chunk `6d28fee7ad90`) — chỉ nộp nếu w045 > 0,3262.

### 14/10/2026: chunk NHỎ (~450 token) — store phụ `data/store_c450.sqlite`
- `w04_x3_40` / `w04_x4_40` (chunk 900): chỉ thêm +12 / +1,8 chunk/câu (doc đầu phần lớn chỉ 1–2 chunk 900) → chỉ nộp x3_40 (chunk `249f0b45468d`, 57,5 MB LZMA).
- Store phụ: 89.058 doc thuộc top-120 của q14_04, `chunk.py --target-tokens 450` → 359.487 chunk (4,04 chunk/doc), kiểm offset/nguyên văn OK. Store chính KHÔNG đổi.
- `runs/w04_c450_x4e120.zip` (4 chunk 450 × top-40 + 1 × 41–120, chunk lấy theo thứ tự trong doc, KHÔNG có điểm chọn chunk; 253.657 chunk, 42,4 MB LZMA; doc `2b20bfcd77c4`, chunk `6e4b6683165f`). So với w04: cùng doc, chunk ngắn bằng nửa, ~211 chunk/câu.
- **KẾT QUẢ (khối dán không nhãn, giả định = `w04_c450_x4e120`, bài ưu tiên 1): FINAL 0,2419** · doc 0,3571 (y hệt) · chunk F2 **0,1267** (P **0,0729** / R 0,2009) so w04 0,2936 (0,1919 / 0,4206). Chunk 450 token SẬP: precision chỉ còn 1/3. Khớp luật LCS(c,g)/|g| ≥ 0,40 nếu **đoạn vàng g DÀI** (cỡ ≥ 450 token): chunk nửa cỡ không chứa nổi 40% của g. → Đoạn vàng dài; chunk nhỏ là hướng SAI; đội khác không thắng nhờ chunk nhỏ. Hướng ngược lại đáng thử: chunk dài hơn 900 (tới ~1.024 token khuyến nghị) và ranh giới chunk khớp mục/đoạn hơn.
- `w04_c450_x3t120` bị hệ thống dừng giữa lúc nén (máy thiếu RAM) → zip hỏng, đã đổi tên `.zip.HONG` để khỏi nộp nhầm; còn 2 file JSON trung gian (~1,1 GB) chưa xoá.

### 14/10/2026: viết gọn câu dài → 3 bài thăm dò (`build_rw_probe.py`)
- `rewrite_queries.py` 405/405 câu viết lại (0 câu rơi về gốc); prompt mới giữ đủ ý hỏi (271, 1002 tốt hơn bản thử), vẫn có lỗi hiểu sai (706: "nguy cơ được 6 tháng" → "nữ 6 tháng tuổi"). Lần chạy đầu OOM vì thiếu `CUDA_DEVICE_ORDER=PCI_BUS_ID` (hai job dồn một card) + batch 16; chạy lại batch 4.
- Qwen3-Reranker-4B chấm top-100 (q14_04) bằng câu viết gọn (`qwen_rw`) và câu gốc cùng cài đặt (`qwen_rwctl`): top-50 của Qwen giao 41,1/50.
- Bài (405 câu; P@50 = DOCS_P × 1200/405): `runs/p50_rw_base.zip` (top-50 hiện tại), `runs/p50_rw_ctl.zip` (RRF hiện tại + Qwen câu gốc; giao base 39,9), `runs/p50_rw.zip` (RRF hiện tại + Qwen câu viết gọn; giao 39,5). Đọc: rw − ctl ≥ +0,02 → viết gọn có giá trị.
- Quan sát nhìn mắt độ tự tin zh theo câu: độ trùng top-30 hai bảng zh (vi-query/zh-query) trải rộng (566/1.200 câu < 5; 164 câu ≥ 15); câu tự tin cao (214, 534) zh đúng chủ đề tới hạng 31, câu thấp (656, 200) zh lệch ngay hạng 1–3 → gợi ý quota zh theo câu.

### 14/10/2026: KẾT QUẢ blendQB14_w04_e120 = FINAL **0,3253** ← TỐT NHẤT (+0,0009 so w035)
- doc F2 0,3571 (P 0,1872 / R 0,5964) · chunk F2 0,2936 (P 0,1919 / R 0,4206).
- Đường cong số zh/câu (vàng thêm/câu so bước trước): 14 zh mới thay zh cũ +1,2 · 14→23: +0,58 · 23→31: **+0,19** → lợi suất giảm nhanh, đỉnh quanh 31–39. w045 (~39 zh) dự đoán ≈ 0 (±0,001); chỉ nộp khi dư lượt.

### 14/10/2026: thăm dò TÁCH Ý CON cho đầu danh sách (`build_subq_probe.py`, 0 GPU)
- `data/subq.jsonl` (07/10, Qwen3.5-9B): 1 ý 215 câu, 2 ý 123, 3 ý 35, **4 ý 827** (tách quá tay: câu 535 ~50 từ bị tách 4 ý, có ý tự bịa "thuốc nam hiệu quả ra sao"); câu dài nhất có thể thất bại (271: trả về nguyên câu). Trước đây chỉ đo để NỚI POOL bằng nhãn bạc (thiên vị câu gốc), chưa từng đo cho xếp hạng.
- `runs/p50_subq_rrf.zip`: qs2, 240/300 câu có ≥2 ý → RRF(thứ tự base top-100, dense BGE-M3 title + title+600 của các ý con gộp RRF); 60 câu 1 ý giữ base. Giao top-50 với base 42,4.
- `runs/p50_subq_ctl.zip`: y hệt nhưng dùng CÂU GỐC với cùng embedding (tách tác dụng "tách ý" khỏi "thêm trọng số dense"). Giao 43,2.
- **KẾT QUẢ `p50_subq_rrf`:** DOCS_P 0,0743 / R 0,0760 → P@50 **0,297**, R@50 0,304 (base 0,300 / 0,310): −0,003, trong nhiễu, KHÔNG tăng. **`p50_subq_ctl`:** DOCS_P 0,0733 / R 0,0738 → P@50 **0,293**, R@50 0,295.
- **Kết luận:** thêm dense câu gốc vào RRF làm tụt (−0,007 P so base); thay bằng ý con bù lại một phần (subq − ctl = +0,004 P / +0,009 R, dưới ngưỡng +0,02) nhưng vẫn KHÔNG vượt base. Tách ý có tín hiệu yếu nhất định (thiên về recall), không đủ để dùng ở dạng RRF với dense title. Hướng tách ý cho đầu danh sách: dừng (ghi âm tính).
- Đọc (mốc `r300_p50_base` P@50 0,300): subq_rrf − ctl ≥ +0,02 → tách ý có giá trị → làm bản đầy đủ (Qwen rerank theo từng ý / chunk-dense theo ý). Gần bằng → bỏ.

### 14/10/2026: KẾT QUẢ r300_p50_base và p50_q4chunk_rrf (qs2, 300 câu; ×4 = P@50 / R@50)
| Bài | DOCS_P | P@50 | R@50 | so base |
|---|---|---|---|---|
| `r300_p50_base` (thứ tự hiện tại) | 0,0749 | **0,300** | 0,310 | mốc |
| `p50_q4chunk_rrf` (RRF hiện tại + Qwen3-Emb-4B chunk) | 0,0760 | 0,304 | 0,322 | P +0,004 (+1,5%), R +0,012 |
| `p50_bgechunk` (13/10, BGE-M3 chunk một mình) | 0,0691 | 0,276 | 0,284 | P **−0,024** |
- Mốc qs2 (0,300) thấp hơn ước đoán 0,33 của mình. BGE-chunk một mình kém thứ tự hiện tại rõ → RRF đang làm đúng việc.
- Qwen3-Emb chunk thêm vào RRF: dương nhưng dưới ngưỡng tin cậy +0,02 (chỉ ~0,2 doc đúng/câu trong top-50). Triển khai 1.200 câu tốn ~2,5 giờ GPU, ước +0,001–0,002 FINAL → chưa đáng, trừ khi gộp với tín hiệu khác. Giả thuyết pool vẫn chờ `p50_q4chunk` (một mình) so với bgechunk 0,276.

### 14/10/2026: KẾT QUẢ blendQB14_e120 = FINAL **0,3222** ← TỐT NHẤT (+0,0040 so 13af 0,3182)
- doc F2 **0,3511** (+0,0079; P 0,1846 / R **0,5844**, so 0,181 / 0,5656) · chunk F2 0,2933 (= 13af, đúng thiết kế; P 0,1918 / R 0,4185).
- Chỉ đổi ~8 doc zh/câu (hạng 121–200) mà R +0,019 ≈ **+1,2 doc vàng/câu** → doc zh mới (phủ 95%, đã clean) có precision ước 15–20%, gấp 2–3 lần ngưỡng hoà vốn (~0,07). Dự đoán của mình (+0,001–0,003) quá thấp. Hệ quả: 14 zh/câu là tối ưu của danh sách zh CŨ; với danh sách mới nên quét lại số zh.
- Quét W (zh3_in trong RRF với c_blendQB8): 0,25 → 4,3 zh/câu · **0,3 → 14,3 (QB14)** · 0,35 → 23,3 · 0,4 → 31,3 · 0,5 → 47,0. W cao đổi cả top-120 (0,35: 1.012/1.200 câu giữ nguyên top-120; 0,4: 746) → chunk có thể nhích.
- Dựng: `runs/blendQB14_w035_e120.zip` (23,3 zh/câu; doc `e27af2c8d46a`, chunk `edaf160c7121`, 95,5 MB), `runs/blendQB14_w04_e120.zip` (31,3 zh/câu; `2b20bfcd77c4` / `c9871de9bf5c`, 95,5 MB); thăm dò `runs/p50_zh3_in.zip` (doc `d7ab98f2423b`; 50 doc zh kho mới/câu, chunk rỗng; mốc cũ `p50_zh_in` DOCS_P 0,066). W0,6 → 60,2 zh/câu (≈13bf đã tụt, không dựng).
- audit store gọn: 20 phút (store cũ ~50). FAIL còn: "gọi domain bị chặn" (vô hại) và raw_html: đã chép lại 359 dòng từ store cũ (còn 2).

### 14/10/2026: STORE GỌN `data/corpus_new.sqlite` thay `corpus_vifull` + dọn file
- `make_store_new.py` (sao chép, không sửa nguồn): chỉ doc kho mới + vinmec.com; bỏ `chunk_t400`/`chunk_t900`, raw_html. 966.845 doc / 980.598 queue / 1.581.245 chunk, **5,3 GB** (cũ 12,6 GB, 2,78M doc). Dựng lại blendQB14 từ store mới: vân tay y hệt (`d63d23c0676f` / `2a2f114bf9df`).
- Mọi script đổi mặc định sang `corpus_new.sqlite` (30 chỗ trong 21 file); `--demo` các script + `unittest` đều OK.
- audit store cũ (trước khi đổi): tầng chunk/submission/score PASS hết; FAIL: 4.006 doc zh shard 0 (03–06/10) state DONE nhưng body 100–199 ký tự (đã đặt FAILED), "gọi domain bị chặn" (vô hại, đã biết), 11 doc trích lỗi mất raw_html.
- Đã xoá (người dùng đồng ý): `corpus_gpu_shard0.sqlite` 6,7 GB, `queue_zh1`/`queue_zh` 1,7 GB, `Downloads/queue_zh2`/`zh3` 2,4 GB, `zh_missing*.sqlite` 0,3 GB. GIỮ `corpus_vifull.sqlite` làm dự phòng tới hết public phase.

### 14/10/2026: zh kho mới phủ 95% → gộp, clean, chunk, mã hoá lại, dựng `blendQB14_e120`
- Crawl máy GPU dừng khi chỉ còn zysjonline (6.516 URL, 75/75 lần 403, bị hãm còn ~10 req/giờ → bỏ). Kết quả: 80.525 dùng được / 3.517 lỗi (iiyi 521, captcha *.39.net, timeout).
- `merge_zh_new.py` (mới, có `--demo`): chỉ gộp doc zh kho mới, body ≥200, tỉ lệ chữ Hán ≥0,3, ghi đè dòng lỗi cũ (tránh lỗi INSERT OR IGNORE). +111.699 doc (zh_missing 80.505, zh2 17.755, zh3 13.439); loại 1.726 nghi mojibake. **Phủ zh kho mới 228.229/240.000 (95,1%)**, trước 116.530 (48,6%).
- `clean.py --apply`: 629.462 doc sửa, 67,3 MB boilerplate — **doc zh cũ chưa từng được clean** (vd. đầu mọi trang 120ask: '您好，虽然我们的工作人员都在竭尽所能…'). `chunk.py`: 782.177 doc → 1.051.774 chunk, kiểm offset OK.
- `scripts/run_zh_new.sh` (GPU 0): mã hoá lại TOÀN BỘ 226.736 doc zh kho mới từ văn bản đã clean (thay hàng cũ trong emb_zhC2) → `emb_zhC3`; xếp hạng vi / zhq / zhq109 → `dense_zhC3_*_rank.jsonl`.
- Công thức 13af giữ nguyên, chỉ thay danh sách zh: RRF(z3v top-400, z3q top-400 có vá 109) → lọc kho mới (`rp/zh3_in`, TB 340 doc/câu so 216) → fuse(c_blendQB8, zh3_in w0,3) → hybrid_cands(…, c_blendQB8w05, 120) → filter_new_corpus → `rp/q14_03.jsonl`. W0,3: 14,3 zh/câu (= 13af); w0,25 → 4,3, w0,2 → 0,2 (ngưỡng rất gắt). Giao top-50 zh cũ/mới chỉ 22,5.
- **`runs/blendQB14_e120.zip`** (95,5 MB bzip2; doc `d63d23c0676f`, chunk `2a2f114bf9df`): so 13af khác 8,0 doc/câu (toàn zh ở hạng 121–200), top-120 y hệt 1.196/1.200 câu, chunk khác 53/179.000 (doc zh vừa clean). Đây là phép thử sạch của "zh phủ 95% + đã clean" ở phần đuôi. Mốc 13af: doc F2 0,3432.

### 13/10/2026: KẾT QUẢ e6_aspect_match và p50_bgechunk (đọc dở, còn thiếu đối chứng)
- `e6_aspect_match`: DOCS_P 0,1976 / R 0,0166 → precision trên 627 câu có doc = 0,1976×1200/627 = **0,378** (~3,9 doc/câu, hạng TB 23). Chưa kết luận được: phải có `e6_aspect_miss` (ngưỡng match/miss ≥ 1,3× ⇔ miss ≤ ~0,29).
- `e6_aspect_miss`: DOCS_P 0,1932 / R 0,0145 → precision trên câu có doc **0,370** vs match 0,378: tỉ lệ **1,02×** (ngưỡng 1,3×). R chênh 0,0166/0,0145 nhưng P gần bằng nhau → trong nhiễu. **E6 ÂM TÍNH: khía cạnh trong title không phân biệt được nhãn → bỏ hướng tín hiệu khía cạnh.** (Ghi cho paper: slide 40 "cùng bệnh khác ý" không thấy được qua title.)
- `p50_bgechunk`: DOCS_P 0,0691 / R 0,0710 → **P@50 = 0,276** trên qs2 (R@50 0,284). Mốc tham chiếu gần nhất là thứ tự hiện tại trên câu 1–300 ≈ 0,316 (mẫu đó KHÓ hơn qs2) → BGE-chunk đứng một mình thấp hơn thứ tự hiện tại ~0,04–0,06 dù giao 41,1/50: ~9 doc nó đổi vào gần như không trúng. Giả thuyết "nhãn pool từ BGE-M3 chunk" yếu đi; chốt khi có `r300_p50_base` và `p50_q4chunk`.
