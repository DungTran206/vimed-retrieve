# PLAN v2 — Vòng cải tiến TXT/BEAR sau kết quả 0.3445

> **Cập nhật triển khai:** xem [V2_IMPLEMENTATION.md](reports/next_round/V2_IMPLEMENTATION.md) và [cấu hình/lệnh v2](configs/next_round/README.md). Task completion kỹ thuật khác nghiệm thu chất lượng trên dữ liệu thật.

> **Phiên bản:** 2.0 · **Ngày:** 19/10/2026 · **Trạng thái:** backend BEAR2.0.0 đã kiểm fixtures; benchmark thật còn blocked bởi snapshot/nhãn. Adaptive production giữ prerequisite guard.
>
> **Mục tiêu:** xác định mức áp dụng thực tế của bài TXT/BEAR đã nộp, kiểm giá trị bổ sung của fixed/local evidence và chunk selection, rồi chỉ mở adaptive khi có bằng chứng về routing. Giữ baseline `w045_TF` làm đối chứng/rollback.
>
> Ý tưởng tại [TXT_Proposal.md](TXT_Proposal.md), vận hành tại [TXT_handover.md](TXT_handover.md), lịch sử tại [improvement_log.md](improvement_log.md). Bản PLAN trước được giữ nguyên tại [archive/PLAN_before_N0_N5_20261019.md](archive/PLAN_before_N0_N5_20261019.md).

## 1. Cách dùng và phạm vi phiên bản mới

### 1.1. Vai trò tài liệu

Proposal giải thích câu hỏi và giả thuyết; PLAN này chốt thứ tự triển khai, hợp đồng kỹ thuật, task và điều kiện nghiệm thu. Handover hướng dẫn thao tác bằng CLI hiện có. Improvement log lưu kết quả và quyết định theo thời gian. Khi triển khai, đọc §2, §5, §11, rồi mở hợp đồng tương ứng ở §6–10.

### 1.2. Thứ tự ưu tiên

Yêu cầu người dùng → code/artifact có provenance → kế hoạch hiện hành này và proposal → báo cáo theo thời điểm → tài liệu lịch sử. Nếu code chưa hỗ trợ điều đã đề xuất, ghi task triển khai rõ; không dùng công thức hoặc tên CLI trong tài liệu thay bằng chứng thực thi.

### 1.3. Phạm vi thay đổi

Mọi code/config/test/report/cache mới vẫn nằm dưới TXT; legacy ngoài TXT chỉ đọc. Code2.0 đã triển khai các công cụ §4/§12; chưa chạy benchmark thật, GPU hoặc submission.

### 1.4. Code hiện có khác với bằng chứng chất lượng

Package CPU `TXT/bear/` đã có. Báo cáo trước ghi 48/48 BEAR fixtures và 10/10 legacy offline tests qua; đó là lịch sử kiểm chứng kỹ thuật, không phải tests vừa chạy hay quality gain. User đã xác nhận kết quả 0.3445 thuộc bài TXT/BEAR; phần chưa biết là liên kết kỹ thuật đến run/config/hash và phạm vi áp dụng, không phải attribution người dùng đã cung cấp.

### 1.5. Kế thừa PLAN trước

Bản archive giữ nguyên bytes, SHA-256 `e8a6e63d4f0a404736400dd44c1973b2bb70f6d215e68283fa84b22a58c20b2c`. Nó mô tả giai đoạn trước triển khai, nên các câu “chưa có package/CLI” không còn là trạng thái hiện hành. T01–T16 và các report cũ phải đọc theo snapshot đó; không tạo lại package hoặc reset trạng thái task khi đổi PLAN.

Giữ ý nghĩa các tham chiếu kỹ thuật: §2.3 baseline, §3.3 write boundary, §5.3 error codes, §6 schema, §7 R0, §8.3 matcher và §10 evaluation. Task giao việc mới ở §11 dùng N0–N5; ánh xạ T cũ được ghi ngay trong task.

### 1.6. Khi thiếu artifact

Đánh dấu dependency cụ thể, trường chưa biết là `null`, decision là `inconclusive` nếu chưa đo được primary metric. Tiếp tục audit phần sẵn có hoặc triển khai interface/fixtures độc lập được giao; không dựng dữ liệu, nhãn, hash hoặc kết quả giả. Chỉ chạy R0 khi cần chứng nhận parity và đủ input; không mặc định phải tái làm toàn bộ pipeline.

## 2. Điểm xuất phát và mục tiêu đo

### 2.1. Baseline và bài TXT/BEAR mới — REPORTED

| Metric | B00: w045_TF, 15/10 | R01: TXT/BEAR, báo 19/10 | Δ hiển thị |
|---|---:|---:|---:|
| FINAL_SCORE | 0.3442 | 0.3445 | +0.0003 |
| DOCS_F2MACRO | 0.3605 | 0.3612 | +0.0007 |
| CHUNKS_F2MACRO | 0.3279 | 0.3279 | 0.0000 |
| DOCS_PRECISION | 0.1884 | 0.1886 | +0.0002 |
| DOCS_RECALL | 0.6047 | 0.6065 | +0.0018 |
| CHUNKS_PRECISION | 0.1931 | 0.1926 | -0.0005 |
| CHUNKS_RECALL | 0.4573 | 0.4585 | +0.0012 |

Nguồn B00: [doc/HANDOVER.md](../doc/HANDOVER.md), các kết quả w045/T2/TF trong [doc/PROGRESS.md](../doc/PROGRESS.md). Nguồn R01: JSON người dùng báo và xác nhận trong hội thoại, entry R01 trong improvement log. Ngày báo không xác định ngày chạy/chấm. Giữ FINAL do nguồn báo; không tính lại từ F2 đã làm tròn.

### 2.2. Điều có thể kết luận

R01 tăng rất nhẹ ở document; chunk tăng recall, giảm precision, F2 bằng nhau ở độ chính xác hiển thị. Chưa có paired per-query scores để kết luận ổn định hoặc quy gain cho H1–H6. Không suy output chunk giống nhau từ F2 bằng nhau. Không promote baseline chỉ từ aggregate score.

Rủi ro cần kiểm ở N1: template pilot chọn 100 query nhưng inference có thể xuất toàn pool và fallback baseline ở query thiếu features. Đây là khả năng từ config/code, chưa xác minh R01 dùng nguyên template. Không ngoại suy gain ×12 hoặc gọi đủ 1.200 dòng là full BEAR.

### 2.3. Baseline phải bảo toàn

| Thuộc tính | Giá trị snapshot B00 |
|---|---|
| Run / doc set | `w045_TF` / `w045_zh38w_e120` |
| Legacy doc / chunk fingerprint | `c1e068422e5f` / `fd07f9fc029a` |
| Query/doc target | QID 1–1200, 200 doc/query |
| Corpus | Đúng `corpus_new.sqlite` clean/chunk khoảng900 token, offsets bất biến |
| Calibration | `scripts/val_calib.py`, beta8 đã freeze; không root MaxP scorer |
| Allocation | Top40 tối đa2, 41–120 tối đa1; top120 p<0.04 bỏ chunk, đuôi p>=0.05 thêm1 |

Ba ZIP root chưa có provenance nối với R01 hoặc B00. Archive score có macro trên593 positive-gold queries/600 query không thay baseline 0.3442 hoặc kết quả R01. Feedback không được join vào inference hoặc dùng làm qrels.

## 3. Kiến trúc và nơi lưu

### 3.1. Cơ chế nghiên cứu vòng này

1. Đo application/fallback trước khi giải thích gain.
2. N2: fixed evidence chọn doc từ pool lớn hơn, kiểm H1/H2.
3. N3: chọn chunk dưới cùng doc set/order/allocation, kiểm H6 độc lập.
4. N4: F0/O0 và E(q)–Δutility kiểm H3; adaptive H4 chỉ mở nếu đủ điều kiện.
5. N5: chọn một candidate trên dev, kiểm interactions, freeze rồi một lần holdout; full inference giữ nguyên frozen parameters.

Sparse H5, IDF, critical weighting, alias/discovery, calibration mới và rechunk giữ backlog cho tới khi có trigger riêng. Không buộc adaptive thành công để giữ một cải tiến fixed/chunk có chứng cứ.

### 3.2. Namespace vòng mới — các đích chưa được tạo

| Loại | Nơi lưu dự kiến |
|---|---|
| Config versioned | `TXT/configs/next_round/` |
| Input nhận thêm | `TXT/inputs/handover/`, `TXT/inputs/evaluation/` |
| Runtime | `TXT/runtime/next_round/N0_v1/` đến `N5_v1/` |
| Reports | `TXT/reports/next_round/` |
| Lịch sử quyết định | `TXT/improvement_log.md`, chỉ nối thêm entries |

Tên reports: `N0_provenance_v1.md`, `N1_application_audit_v1.md`, `N2_fixed_evidence_v1.md`, `N3_chunk_pilot_v1.md`, `N4_routing_controls_v1.md`, `N5_confirmation_v1.md`. Đổi code/config/input/labels thì dùng version/output mới; không ghi đè completed run. Tên dự kiến không chứng nhận file đã tồn tại.

### 3.3. Giới hạn ghi và nguồn bất biến

- Resolve absolute paths và symlink/junction trước ghi; output phải nằm trong TXT, không trùng input hoặc nằm trong `TXT/inputs/`.
- SQLite nguồn mở readonly; nhận snapshot nhất quán, kiểm WAL/writer. Không clean, migrate, thêm index, checkpoint hoặc rechunk nguồn để qua guard.
- Cache/temp/venv mới dưới TXT; dùng Python `-B`, temp và model caches trong `TXT/runtime/`.
- Atomic partial→completed sau validate; resume chỉ khi code/config/input/artifact hashes khớp. Config typo/NaN/duplicate không được âm thầm bỏ qua.
- Không stage runtime/model/input lớn hoặc restore thay đổi có sẵn của người dùng. Không dùng default output legacy ngoài TXT khi chưa audit side effects.

## 4. Code hiện có và gap cần triển khai

| Nhóm | Module trong `TXT/bear/` | Trạng thái cần nhớ |
|---|---|---|
| I/O/contracts/config | `io`, `artifacts`, `contracts`, `config`, `cli` | Có strict schema, hashes, output boundary, resume |
| Snapshot/R0 | `audit`, `adapters`, `baseline`, `reproduce` | CPU recipe và native refs có fixtures; parity thật cần artifact |
| Pool/evidence/inference | `pools`, `matching`, `evidence`, `features`, `fusion` | PLARGE/P200, VI lane, body/local features và fixed modes đã có |
| Study/evaluation | `experiments`, `tuning`, `evaluation`, `evaluate_runner`, `paired` | L1/F0 tune, annotation, reviewed labels, freeze/holdout guards |
| Chunk | `chunk_experiments`, `chunk_study`, `chunk_evaluation` | Có study C1/C2, local-passage diagnostic, freeze refs và export selected chunks; đã kiểm fixtures |
| Release | `integrity`, `release` | Legacy allocation/export path; không tự dùng C1/C2 |

Code2.0 có provenance, application-audit, tune L1/L4/L1_L4/F0, chunk-study, evaluate-chunks, routing-diagnostics và preflight. N0 inventory thật báo18roles thiếu; N1–N5 chưa benchmark thật. N4 production adaptive, sparse/discovery vẫn giữ dependency.

Không sửa algorithm legacy trong vòng này. Nếu cần code mới, thêm dưới TXT và kiểm đúng invariants bị ảnh hưởng. Trạng thái T01–T16 tại [IMPLEMENTATION_STATUS.md](reports/IMPLEMENTATION_STATUS.md) là lịch sử kỹ thuật trước R01, không được hiểu là quality result mới.

## 5. Dependency và trạng thái nghiệm thu

### 5.1. Các cấp bằng chứng

| Cờ | Điều kiện |
|---|---|
| `technical_ready` | Interface/fixtures hợp lệ; chưa chứng minh chất lượng |
| `baseline_verified` | Artifact R0 parity + provenance/integrity đúng snapshot; reuse được |
| `application_audited` | N1 có counts/denominators, fallback và output changes thực |
| `evaluation_ready` | Metric đúng scope, reviewed labels/coverage đủ, protocol/split rõ |
| `selected_dev` | Mọi trial cần thiết có primary metric, chọn theo tie rules đã đăng ký |
| `confirmatory_ready` | Candidate/controls freeze, holdout phù hợp và chưa dùng chọn lại |
| `submission_ready` | Full inference/integrity/package qua; chưa đồng nghĩa đã nộp hoặc gain được xác nhận |

Các trạng thái không thay thế nhau. `completed` trong manifest chỉ là job kỹ thuật; decision vẫn có thể `inconclusive`. Mức `REPORTED`, `ARTIFACT_OBSERVED`, `CODE_VERIFIED`, `PROPOSED`, `UNRESOLVED` phải ghi riêng với decision chất lượng.

### 5.2. Input tối thiểu theo stage

R0 cần14 roles: `corpus`, `vi_base`, `vi_alt`, `zh_bge_vi`, `zh_bge_zh`, `zh_bge_patch`, `zh_q8_vi`, `zh_q8_zh`, `zh_q8_patch`, `membership`, `chunk_scores`, `qwen_doc_scores`, `chunk_dense`, `beta`. Paths thật theo [reproduce.json](configs/reproduce.json) và handover; không điền hash giả.

- N0 R01: submission/run ID, code/config/input/output hashes, query universe, scoring output, timestamps nếu có.
- N1: pool/feature/run manifests, L0/pair/ranking-details/candidates, R0 reference, export allocation/refs nếu có.
- N2: query/enriched entities, frozen pool/corpus, reviewed dev differences cho cả L1/L4, split/protocol.
- N3: chunk refs/scores có mapping verified, fixed doc/order/plan, passage references và evaluator đúng phạm vi để kết luận chất lượng.
- N4: B/D sources có provenance, frozen families/support, nhãn đủ endpoints/menu/control utility.
- N5: selected dev reports, candidate/controls frozen, holdout annotations/coverage, cost ceiling và full-data dependencies.

`readiness.json` cũ còn paths `data/...`, downstream dùng `TXT/inputs/handover/data/...`; bind thống nhất ở config version mới. Có đủ14 roles R0 không đồng nghĩa đủ entities/B/D/qrels. Global readiness thiếu tokenizer không chặn L1 local study nếu evaluator local đã đủ hợp đồng riêng.

### 5.3. Error codes và cách xử lý

| Code | Xử lý |
|---|---|
| `INPUT_MISSING` | Liệt kê role/path thiếu đúng stage; dừng phần phụ thuộc |
| `HASH_MISMATCH` | Kiểm provenance, không sửa hash để hợp thức hóa input lạ |
| `SCHEMA_INVALID` | Nêu key/path/line; không tự dedupe/cast IDs hoặc bỏ validation |
| `BASELINE_PARITY_FAILED` | Debug intermediate, chưa đo gain so baseline đó |
| `FEATURE_UNAVAILABLE` | Fallback đã freeze + reason; null khác no-match0 |
| `LABEL_COVERAGE_INSUFFICIENT` | Primary unavailable/inconclusive; bổ sung reviewed judgments |
| `EVALUATOR_UNVERIFIED` | Chỉ báo local/diagnostic có tên/version đúng |
| `OUTPUT_OUTSIDE_TXT` | Sửa config/output trước khi ghi |

## 6. Hợp đồng dữ liệu và provenance

### 6.1. IDs, nguồn rank/score và source config

Internal QID là integer hợp lệ; doc IDs của snapshot là canonical decimal strings, submission là integers. Không nhận bool/float ID, không `int(float(x))`, không bỏ prefix `corpus:` hoặc canonicalize collision tùy tiện. Adapter namespace khác cần mapping có bằng chứng.

Rank từ1 theo original array order; giữ raw score có precision nguồn, không sort lại source vì điểm đã round/tie. Reject duplicate QID/doc, invalid rank, NaN/Inf, thiếu fields bắt buộc.

Pool source config hiện chấp nhận: `source_id`, `artifact_path`, `artifact_sha256`, `source_kind`, `complete`, `provenance_status`, `query_hash`, `corpus_hash`, tùy chọn `query_view`, `field`, `requested_cutoff`. `source_kind` là retriever/reranker/family; schema thật ở [config.py](bear/config.py) là chuẩn cho config nạp trực tiếp.

Rich provenance như input-candidate hash, actual cutoffs, eligible universe, model/checkpoint/revision/tokenizer/prompt/field/truncation/dtype/script hash và child family weights lưu sidecar riêng. Các keys đó **chưa được pool config nhận trực tiếp**; muốn mở schema phải có task/test riêng. `complete=true` và `verified` cần chứng cứ, không chỉ tự ghi cờ.

| Availability | Rank component | Nghĩa |
|---|---|---|
| `ranked` | `(k+1)/(k+R)` | Có rank thật, raw score0 vẫn hợp lệ |
| `not_retrieved` | 0 | Completed retriever, doc thuộc universe nhưng ngoài cutoff |
| `not_scored` / `not_applicable` | null | Subset chưa chấm / doc ngoài universe nguồn |
| `missing_query`, `partial_query`, `missing_text`, `missing_vector` | null | Thiếu input/coverage, giữ reason |
| Artifact bắt buộc thiếu | Error | Không biến thành source rỗng hoặc similarity0 |

Không renormalize weights riêng theo doc mất score. Fixed completeness kiểm trên selectable VI; frozen non-VI slots không phải missing feature cần route. Source ranks giữ gốc trước restrict pool.

### 6.2. Query/concepts

Giữ query gốc, entity strings gốc, source indices và hash. VI entity phải `verified_in_query` mới vào denominator; not-in-query vẫn giữ diagnostics. Enriched JSON đọc được không chứng minh `parse_ok=true`; join expansion provenance hoặc ghi unknown.

Mỗi concept tính tối đa một lần dù nhiều aliases. Translation không tự là verified synonym. Critical/type/alias cần reviewed provenance; chưa có thì null/unavailable, không đoán từ chữ hoa/rarity. Giữ mapping coverage theo ngôn ngữ; thấp/thiếu thì fallback, không gọi là lexical failure.

### 6.3. Corpus/chunk refs

Inspect schema SQLite thật; read batches<=900 IDs khi dùng native adapter. Stable ref tối thiểu gồm `corpus_hash`, `doc_id`, `body_sha256`, `chunk_id_native`, `ord_native`, `exporter_idx`, `start`, `end`, `text_sha256`, mapping namespace/status.

Offsets là Python Unicode code points, end-exclusive; `0<=start<end<=len(body)`, text đúng nguyên văn `body[start:end]`. Hash UTF-8 body gốc, không hash body normalized để chứng nhận provenance. Không dùng `body.find(text)` vì đoạn có thể lặp.

Exporter idx được gán sau bỏ slices rỗng, theo native `chunk_id` order. Dense `best_idx`, `off.idx`, `ord` và global `chunk_id` không tự bằng exporter idx. External mapping thiếu offsets/hash verified thì unavailable; không dùng chọn chunk.

### 6.4. Features, labels và audit ledger tách miền

Pair rows lưu QID/doc/pool/query/corpus/config/feature hashes, rank/source/availability, lang/mapping, body/title/local/critical coverages, length/chunk-count và matched/missing concepts. Chunk features keyed bằng stable refs; support features cho E(q) có thể nằm ngoài ranking pool.

Inference không nhận grade/gold/relevance/qrels. Allocation p(gold) là artifact legacy riêng, không phải nhãn hoặc routing feature. `critical_mismatches=[]` trong code hiện tại không chứng minh không có sai quan hệ/phủ định.

Audit N1 bổ sung per-query ledger có mẫu số: expected/output/feature/eligible/applied/fallback/bypass, changed-order/top40/docset/chunks, added/removed, và feature/score/calibration coverage. Các nhóm có thể giao nhau; ghi định nghĩa thay vì cộng tất cả thành100%.

## 7. R0 compatibility và rollback

### 7.1. Recipe exact khi cần reproduce

1. Đọc VI base/alt; mỗi model ZH lấy top400 của vi-query và zh-query; patch109 **replace cả row** sau cut400.
2. RRF bốn nguồn ZH, k60, weights1/1/0.3/0.3, top1000; tie string doc ID; giữ stage rounding6 của legacy.
3. ZH stage chỉ membership, re-encode score `round(1-i/(len(Z)+1),6)`, i từ0. Ngoại lệ vinmec chỉ ở final filter.
4. RRF VI base1 với ZH0.45, k60/top1000 → deep; base top200, head tối đa120 lấy từ VI alt top240 giao set đó; nối base còn lại, không scan sâu hơn alt để bù head.
5. Final filter giữ membership hoặc exact domain `vinmec.com`; refill từ deep đúng order, không duplicate, đủ200 hoặc fail. Không sửa corpus policy khi reproduce.
6. Frozen calibration dùng ZH BGE vi/zhq **gốc**, không patch109; p round4 rồi áp `<0.04` top120, `>=0.05` đuôi.
7. Build tương đương topk200/per_doc2/chunk_from_top40/extra_one120/int IDs/queries=None; kiểm schema, offsets, fingerprints và provenance. Không nén ZIP chỉ để kiểm parity.

### 7.2. Calibration8

Beta finite8 theo thứ tự `(intercept,logitQ,hasQ,cosChunk,hasCosChunk,isZH,cosZH,hasZH)`. Qwen có giá trị thì clip `[.001,.999]` trước logit, missing dùng logit0/hasQ0; cosine0 khác missing. ZH `zc=max(Zv.get(doc,-1),Zq.get(doc,-1))` theo recipe; vector7 là `[0,0,0,0,1,max(zc,0),zc>=0]`. Non-ZH vector7 là `[logitQ,hasQ,cosChunk_or0,hasCosChunk,0,0,0]`.

NumPy float64, từng query/original order, logistic như scorer frozen, serialize p round4 trước threshold. Không refit, không `--extract/--logit`, không root `val_calib.py` MaxP. Giữ differential calibration fixture hiện có; khi thay compatibility code mới cần rerun test phù hợp.

### 7.3. Chunk tiers exact

| Tầng | Selector B00 |
|---|---|
| Rank1–40 | Tối đa2; khi >2 chunk và có scores thì chọn theo `(-score_default_minus1,exporter_idx)`, xuất lại native order |
| Rank41–120 | Tối đa1 chunk đầu, không nhận chunk_scores ở nhánh này |
| Top120 plan0 | Xóa chunk, giữ doc |
| Rank121–200 plan1 | Thêm1 chunk đầu nếu doc chưa có chunk |

Plan n>0 không reset count của doc đã có chunks. R0 không truyền qtext; hàm legacy có qtext sẽ overwrite lựa chọn scores nên không tự bật. Mở scores cho tầng sau là C1 experiment, không sửa parity recipe.

### 7.4. Reuse, manifest và parity

Reuse baseline khi manifest/code/input hashes và parity/integrity cùng snapshot đã verified. Nếu chưa có thì nhận inputs và reproduce qua `TXT.bear.cli`; không chạy nguyên `scripts/build_best.sh` có lỗi cwd/output legacy.

Giữ reported scores tách observed scores. Legacy doc fingerprint bỏ rank, chunk fingerprint bỏ doc ID/offset; thêm canonical order-aware ranking hash và provenance hash QID/doc/rank/chunk-position/offset/body/text. ZIP SHA-256 nhận diện package, không thay semantic parity. Mismatch thì debug stage/order/patch/filter/p/plan/idx; không tune weights để ép hash.

## 8. Pool, support và evidence

### 8.1. Scope và VI lane

P200 chỉ đổi thứ tự cùng200 doc: Doc F2 toàn tập không đổi; primary có thể P@40 hoặc chunk metric hợp lệ. PLARGE chọn200 từ cap400 baseline-first pool; baseline phải có mặt, extras theo frozen deeper rank, không dùng nhãn để build pool. Không có extra VI thì không có VI selection headroom; đổi study scope/version nếu cần.

Chỉ sắp/chọn VI; giữ non-VI doc và vị trí baseline. Reference = baseline200 đúng order rồi extras theo deep đã khóa; λ0 trả đúng baseline. Không suy VI local gain thành ZH hoặc FINAL gain.

### 8.2. Support E(q) và B/D

B-family từ lexical sources có provenance; D-family từ dense sources thật. Mixed `c_blendQB8` không phải lexical/dense thuần. Cached family verified dùng được; nếu dựng family từ child ranks thì freeze child list/weights và family rank trước restrict pool.

Support mặc định top20 B-family, kE60, tách ranking pool và có thể chứa doc ngoài pool. `sources=[]`, `b_family=null` của template chỉ đủ evidence-only, chưa đủ F0/routing. Partial reranker không tự là whole-universe retriever.

### 8.3. Protected matcher

Evidence matcher độc lập tokenizer BM25/evaluator. NFC + whitespace/case policy có version; giữ dấu, số, short tokens, identifier structure và boundaries. Test type1≠type2, BRCA1≠BRCA10, V600E≠V600K, mg≠mcg; không tự đổi liều hoặc xác nhận alias bằng cosine. Không sửa BM25 tokenizer trong cùng evidence experiment.

### 8.4. Body/local và availability

Uniform concept coverage là feature vòng này. `body_coverage` tính toàn body; `local_max_all` max trên mọi native chunks; lưu length/chunk-count để kiểm thiên lệch max. `local_top2_mean` có trong code nhưng chưa nằm menu N2; title blend/IDF/critical weighting là study sau.

No concept/text/mapping hợp lệ → null, khác coverage0 đã tính. Fixed evidence fallback toàn query nếu selectable doc thiếu feature hoặc mapping coverage≠1. Không hard-filter vì coverage thấp. Matcher hiện chưa hiểu relation/negation/intent nên cần hard-negative error analysis, chưa được gọi là xác nhận đúng y khoa.

### 8.5. Full features và chi phí

Pilot dùng sampled IDs; full config dùng `query_ids_path=null`, output version mới. Không tự tăng100→1200 trước khi biết application bottleneck/cost. Đo runtime/RAM/I/O theo scope thật; fields chưa đo giữ null. Partial restart hiện recompute shard, chưa cam kết skip completed shards. Không ngoại suy quality gain từ coverage hoặc nhân gain sample.

## 9. Fixed residual, menus và routing có điều kiện

### 9.1. Công thức và deterministic order

```text
r(rank) = (60+1)/(60+rank)
S_evidence = (1-lambda)*r_ref + lambda*Z
S_fixed = (1-lambda)*r_ref + lambda*(wB*rB+wD*rD)
g = sigmoid((E-tau)/T)
w(q) = g*w_lex+(1-g)*w_sem
```

λ∈[0,1], T>0, weights finite/nonnegative/tổng1 tolerance1e-9. Không cộng raw BM25/cosine/Qwen. λ0/baseline bypass reference, không cần features. Experimental sort không round trước, tie `(-score,reference_rank,doc_id_string)`; export monotonic integer scores theo rank để loader giữ order. R0 intermediate vẫn dùng recipe legacy.

### 9.2. Menu N2 và F0

| Study | Menu đăng ký | Khả năng chạy hiện tại |
|---|---|---|
| L1 | body_coverage; λ `[0,.02,.05,.10,.20,.35]` | `tune` family L1, sáu trials |
| L4 | local_max_all; cùng sáu λ | Tune family L4 hoặc L1_L4; combined study có12trials đăng ký trong menus_v2 |
| F0 | λ `[.10,.25]`, wB `[0,.10,.20,.35,.50,.65,.80,.90,1]`, wD=1-wB | `tune` family F0,18 trials khi B/D đủ |

Preregister menu/pool/split/labels/primary trước scoring. L1 và L4 cùng tuning budget/fallback/universe; không thêm title/top2/IDF sau khi nhìn dev mà giữ tên study cũ. Dev tie metric tolerance1e-12: λ thấp hơn, cost thấp hơn, ID lexical. Ghi toàn bộ trials, `evaluation_config=null` không chọn best.

### 9.3. E(q), O0 và A1 chưa mở

E là weighted body coverage trên support B trước fusion, weights `1/(60+original_B_rank)`. Lưu actual_K, E_valid, gamma; route chỉ khi actual_K>0 và **mọi** support doc hợp lệ/mapping đầy đủ. Coverage0 valid; missing không bị loại denominator để nâng E. E unavailable thì best fixed fallback, không ép route.

O0 dev-only khóa hai lexical/semantic endpoints và λ trước khi đo utility. Oracle chọn config cho cả query, không từng doc; đúng metric scope, không deploy hoặc dùng silver/feedback làm gold. Kiểm E bins với ΔU lexical−semantic; không có variation/headroom hoặc sai hướng thì defer adaptive.

N4 cần best F0/constant, query-only length và shuffled-E controls seeds `[11,23,37,53,71]`; shuffle trong language/length bins đã khóa, báo bins nhỏ và mọi seeds. A1 template tối đa18 configs: hai λ F0 × tau dev E quantiles `[.25,.50,.75]` × T `[.05,.10,.20]`, endpoints lexical .8/.2 và semantic .2/.8. Đây là menu PROPOSED, chưa có production runner; dedup quantiles nhưng không cắt18 F0 hoặc thêm A1 configs bù. Không đổi dấu gate sau holdout; không mở A2 đồng thời để săn candidate.

## 10. Evaluation, annotation và quyết định

### 10.1. Ba tầng evaluator

`submit/score.py` là legacy proxy. Local document/replacement và passage diagnostics có contract/version riêng. Official-equivalent chỉ khi có đủ tokenizer/normalization/reference/duplicates/aggregation/scorer semantics và differential evidence. Archive LCS0.4/duplicate0.8 chưa cung cấp toàn bộ semantics đó.

### 10.2. Document/replacement metrics

Per-query Doc F2=`5*g/(4*G+k)`; macro là mean per-query F2, không F2(meanP,meanR). Full-universe F2 cần complete-universe labels/manifest và explicit empty-gold policy. P@K cần judged toàn topK. Replacement cùngk: added/removed đều judged, Δhits=rel_added−rel_removed, ΔP=Δhits/k; common docs triệt tiêu.

Không biết G thì ΔP không được gọi là official ΔF2. Unjudged không là grade0. Mọi trial dùng cùng planned evaluation query universe; thiếu labels thì primary inconclusive, không chọn complete-case subset thuận lợi.

### 10.3. Chunk diagnostics và runner gap

Passage refs cần same QID/doc, text/offset/body hash và reviewed source. Local LCS giữ thứ tự, diagnostic match `LCS(pred,gold)/len(gold)>=.40`; tokenizer/normalizer có tên/hash. Chưa đủ official semantics thì không gọi `official_chunk_f2`.

Document evaluator giữ các metrics cũ; chunk_evaluation mới đo local_passage_recall với official_equivalent=false trên reviewed offset references. Freeze bind toàn candidate manifest/artifacts, selected records/refs và yêu cầu records hash trong dev report cho chunk candidate. Export giữ C1/C2 selected chunks, kiểm same corpus/doc/head/slots; chưa có official chunk evaluator hoặc quality benchmark thật.

### 10.4. Sample/split và contamination

Reuse frozen split nếu hợp lệ; không resample để tìm kết quả đẹp. Khi chưa có split, mặc định SRS100 không hoàn lại seed42, target60dev/40holdout, group exact duplicates NFKC/lower/whitespace; ghi actual counts. Grouping không tự thêm mọi group member vào sample. Reviewed near-duplicates cần mapping, không gộp chỉ vì cùng bệnh. Smoke2 chỉ kiểm I/O.

Sample runner ghi qids đã quan sát từ root scoring archive vào contamination ledger. Giao holdout thì `confirmatory_eligible=false`; không đổi seed/xóa exposure để gọi pristine. Kết quả aggregate R01 đã được nhìn phải ghi trong study history; không suy toàn bộ public/private split từ nó.

### 10.5. Annotation workflow

1. Freeze pool/menu/split trước export. PLARGE differences gồm union added/removed của **mọi L1/L4 trial**; P200 top40 cần đủ topK.
2. Blinded export ẩn source/rank/score; reviewer điền grade0 không relevant,1 đúng chủ đề chưa trả lời,2 có supporting answer; primary grade2, policy `local_answer_v1`.
3. Nhãn có annotator, `adjudication=reviewed`, policy version, supporting passages/offset/body hashes và lý do; coding AI không tự điền gold. Quota annotation/audit/disagreement policy đăng ký trước; detailed workflow lịch sử ở archive §10.5 vẫn là reference.
4. Bind qrels/split hashes lowercase64hex thật; evaluation chỉ nhận labels riêng, không cho inference đọc.
5. Khi thay menu/labels/config, version output; thiếu required labels thì bổ sung review hoặc ghi inconclusive, không ép selection.

### 10.6. Paired inference và tiêu chí

Runner2.0 có paired control deltas/CI cho replacement, precision_at_k và macro_doc_f2 khi đủ control judgments. Chunk evaluator có paired CI cho local passage recall, không đổi tên thành official Chunk F2.

Template ΔP@200≥.005, CI lower>0, subgroup tolerance−.01 là **đề xuất trước freeze**; .005 tương ứng trung bình thêm1 relevant doc/query, không phải ngưỡng FINAL. Cost ceiling phải có số đo thực. CI không sửa pooling/contamination/incomplete-label bias. Quyết định `keep/reject/inconclusive` theo scope và evidence; promotion/technical packaging là mốc riêng.

### 10.7. Một lần holdout đúng candidate

Chọn nhánh/candidate/interactions trên dev bằng primary metric cùng scope, không so ΔP với local LCS để chọn winner. Freeze một candidate chính + controls, code/config/input/menu/split/labels, primary/thresholds/cost/contamination trước holdout. `selected_dev_report` phải là evaluation.json available/dev đúng candidate hash, không selection.json.

Runner2.0 validation trước exclusive exposure claim; CLI preflight chỉ trả readiness, không scores/marker. Freeze bind metric/coverage/policy đã chọn. Multi-control trong cùng exposure vẫn cần orchestration riêng; không gọi evaluate thử rồi compare hoặc xóa marker. Candidate fixed/chunk đủ điều kiện không phải chờ adaptive.

## 11. Task triển khai giao trực tiếp — N0 đến N5

Các task dưới đây là hợp đồng nghiệm thu; backend2.0 có fixture coverage. N0 inventory là blocked_input, N1–N5 benchmark chưa nghiệm thu vì thiếu artifacts/labels; xem báo cáo v2. Tên output dự kiến không thay bằng chứng thực thi.

### N0 — Liên kết R01 và xác minh baseline

**Dependency:** entry B00/R01, baseline recipe và run artifacts nhận được. **Ánh xạ cũ:** T02/T03/T04.

**Công việc:** kiểm git/instructions; inventory B00/R01; nối score với submission/code/config/input/output hashes/query/scorer; stream hash JSON entry khi archive lớn, không load717MB để xem schema. Reuse baseline verified hoặc nhận14roles rồi R0 parity; missing field giữ null, không gán fingerprints B00 cho R01.

**Đầu ra:** `N0_provenance_v1.md`; `N0_v1/provenance.json` dự kiến, bảng linked/unlinked/missing + reference artifact đã verified. Muốn tool audit mới thì triển khai riêng, chưa có CLI tự suy liên kết run.

**Nghiệm thu:** các liên kết có evidence; baseline parity/integrity verified trước causal comparison hoặc blocker cụ thể. Không cần GPU/re-submit. Khi thiếu R01 artifact, vẫn được kiểm R0 và code/config audit riêng, chưa gán R01 cho template.

### N1 — Audit application/fallback và actual changes

**Dependency:** artifacts của scope audit; N0 xác nhận input/reference tương ứng. **Ánh xạ cũ:** T05/T07/T10, thêm audit mới.

**Công việc:** xây công cụ read-only trong `TXT/bear/` nếu chưa có; input explicit manifests/L0/pairs/ranking_details/candidates/refs. Freeze định nghĩa eligible/applied/fallback theo mode; fixed không dùng `route_eligible` thay eligibility riêng.

Ledger tối thiểu mỗi QID gồm: expected/output/feature availability, selectable VI pair counts, concept/mapping validity, bypass/effective λ, applied flag/fallback reason; changed-order/top40/docset/chunks, added/removed VI, extra VI count và dense/Qwen/calibration support coverage. Hash doc set tách hash order. Report both no-features và đủ features nhưng output không đổi. Các count có denominator; scope sample/full rõ.

**Đầu ra:** `N1_application_audit_v1.md`, per-query JSONL/summary/manifest dưới `N1_v1/`. Giữ unknown null; không gọi chunk-applied từ việc document features đã có.

**Nghiệm thu:** accounting khớp input counts, fallback giải thích được; đo coverage và headroom thay vì suy từ số rows. Nếu chỉ sample100, ghi rõ, không nhân gain12 hoặc ép route. Thiếu full artifact chỉ chặn phần full audit.

**Kiểm tra code khi triển khai:** fixtures gồm partial features→baseline, đủ features nhưng rank không đổi, order-only đổi set không đổi, PLARGE replacement, missing mapping/score và frozen non-VI. Tests phải chứng minh audit phân biệt các tình huống, không chỉ mirror formatter.

### N2 — Fixed body/local evidence study

**Dependency:** baseline/pool/features valid, N1 đã audit scope; reviewed labels/split đủ để chọn best. **Ánh xạ cũ:** T09/T10.

**Công việc:** freeze PLARGE cap400/VI lane, reference và chunk policy; tạo sáu body trials L1 và sáu local_max_all configs L4 cùng λ/menu budget; mỗi phép so chỉ đổi body→local, không thêm IDF/critical/title. Dùng tune L1 hiện có; L4 run/compare + ledger hoặc triển khai orchestration trước study.

Nếu chưa có features thật, smoke2→L0 selected pilot trước; không mặc định full1200. Annotate union differences mọi trials rồi score cùng planned dev universe. Đối chiếu λ0 reference và missingness; phân tích within rank/language/body-length/chunk-count bins và hard negatives relation/identifier.

**Đầu ra:** `N2_fixed_evidence_v1.md`; configs dưới `configs/next_round/`, trials/predictions/dev evaluation/selection ledger dưới `N2_v1/`. Scored protocol phải bind evaluation config, khác predictions-only template.

**Nghiệm thu:** toàn menu và labels có provenance, paired ΔP@200/CI/cost/fallback, best fixed theo tie rules hoặc reject/inconclusive rõ. Không convert ΔP thành F2/FINAL; chưa mở holdout. Pool không có extra VI thì đổi study sang P200 metric đúng hoặc thêm verified deep sources trong version khác.

### N3 — C1/C2 chunk study độc lập

**Dependency:** baseline/control doc set/order/plan verified, refs/scores mapping, passage labels/evaluator cho quality claim. **Ánh xạ cũ:** T03/T12.

**Công việc:** audit multi-chunk + complete score coverage theo tiers; hoàn thiện study/export path gọi selectors, bind selector config/ref outputs/slot counts trong manifests; add evaluator/freeze support nếu cần confirmatory chunk. Đổi selector, giữ doc set/order/allocation/boundaries/beta. C1 dùng existing scores cho41–120/đuôi, C2 dùng local evidence cùng slots; không đủ features fallback chunk đầu đúng protocol và report.

**Đầu ra:** `N3_chunk_pilot_v1.md`; control/C1/C2 refs, predictions, actual slots/chunks/tokens/chars/overlap/ZIP/cost và mapping/fallback summaries dưới `N3_v1/`. Thiếu passage labels thì output chỉ headroom/integrity diagnostic, chưa chọn best chất lượng.

**Nghiệm thu:** proof cùng doc/order/slots và text slices; quality metric đúng contract, hoặc explicit inconclusive. Chọn chunk khác có thể đổi token length dù slot bằng nhau; báo variation, không giả matched token budget. C3 allocation/rechunk/rerank GPU cần trigger/budget riêng.

**Kiểm tra code khi triển khai:** native/external index mismatch, score thiếu, ties, empty chunks, doc một/nhiều chunk, head legacy bất biến, slot invariant và freeze tamper trên refs/selector. Lịch sử IDF/chunk-first không ủng hộ mặc định gain lớn.

### N4 — F0/O0/H3 và adaptive có gate

**Dependency:** N2 có kết luận fixed dev, N0/N1 valid, B/D source/family/support verified và labels đủ utilities. **Ánh xạ cũ:** T05/T10/T11.

**Công việc:** run18 F0 configs; khóa best fixed/endpoints; đo oracle query-level + E bins/Δutility; constant/query-only/shuffle controls. Ghi headroom/cost và kiểm hướng E trước mở A1. Nếu headroom/tín hiệu không đủ, kết thúc N4 bằng defer routing và giữ fixed.

Chỉ khi go mới hoàn thiện adaptive orchestration/prerequisite validation và tests rồi dùng menu A1 §9.3. Không bỏ guard chỉ để chạy. Controls cùng components/pool/source rank/missingness/chunk policy/budget, ghi mọi trials/seeds, chưa mở holdout.

**Đầu ra:** `N4_routing_controls_v1.md`, F0/O0/bins/control/A1 ledger nếu đủ điều kiện dưới `N4_v1/`.

**Nghiệm thu:** quyết định go/defer có primary utility và coverage rõ; candidate adaptive chỉ shortlist khi hơn best fixed công bằng và controls hỗ trợ. H1 hoặc chunk gain không chứng minh H3/H4. Sparse/alias không tự thành dependency.

### N5 — Dev selection, single holdout, full integrity

**Dependency:** có ít nhất một candidate với primary dev đủ evidence; N3/N4 có thể deferred. Freeze runner/evaluator phải bind đúng artifact của cơ chế candidate.

**Công việc:** chọn primary metric cùng scope; so shortlist và tổ hợp trên dev, interaction check trước freeze. Thiếu nhãn để so tổ hợp thì diagnostic hoặc chọn một cơ chế chính cùng guardrails đã đăng ký, chưa tuyên bố FINAL tăng. Chốt một candidate + controls/protocol/cost ceiling, prevalidate độc lập, một lần holdout theo §10.7.

Sau xác nhận, full config query_ids_path=null và frozen parameters/output mới. Release2.0 giữ selected C1/C2 refs/records sau kiểm same corpus/doc/head/actual slots. Full submission vẫn phải qua1200×200 integrity/membership/non-VI/offset/hash và ZIP dưới100000000bytes; dự trù RAM nén dictionary768MiB.

**Đầu ra:** `N5_confirmation_v1.md`, selected dev report/frozen hashes/holdout report/full run/integrity và package nếu xuất dưới `N5_v1/`; log quyết định/rollback.

**Nghiệm thu:** paired evidence/cost/subgroups đúng protocol, không chọn lại sau holdout; full technical checks không thay quality conclusion. Keep/reject/inconclusive và promotion được ghi riêng. Không tự upload/nộp khi user mới yêu cầu lập kế hoạch.

## 12. CLI thật, config và kiểm chứng

### 12.1. Lệnh đang có

| Command `python -B -m TXT.bear.cli ...` | Hành vi |
|---|---|
| `reproduce/pool/sample/features/run/annotation-export` | `--config`; mặc định dry-run, `--execute` mới chạy |
| `tune` | --protocol, --menu, dev-only; dry-run mặc định; L1/L4/L1_L4/F0 |
| `export` | `--run-dir`, `--config`; dry-run mặc định |
| `audit` | `--config`; chạy và ghi output ngay |
| `evaluate` | `--run-dir`, `--config`; chấm ngay |
| `compare` | `--baseline-dir`, `--candidate-dir`, `--config`; chấm ngay |
| `freeze` | `--run-dir`, `--protocol`; ghi frozen artifact ngay |

Code2.0 có provenance/application-audit/chunk-study/routing-diagnostics (dry-run mặc định) và evaluate-chunks/preflight (chạy ngay; preflight không scores/exposure). Hướng dẫn tại [v2 runbook](configs/next_round/README.md). Sparse/A1 production chưa mở; evaluate/compare/freeze/audit không nhận --execute/--dry-run.

### 12.2. Config version mới

Các templates v2 đã có trong `TXT/configs/next_round/`; bind paths/hash thật và output đúng N-stage. L4 cần `mode=fixed_evidence`, `feature_name=local_max_all` và sáu λ, hoặc dùng combined L1_L4 protocol; không nạp unsupported keys. Không viết config rỗng trông như đã bind data. Source rich sidecars §6.1 tách pool config.

Ví dụ đọc giao diện hoặc dry-run dependencies, **chưa chạy trong lần viết PLAN này**:

```powershell
python -B -m TXT.bear.cli --help
python -B -m TXT.bear.cli reproduce --config TXT/configs/reproduce.json --dry-run
python -B -m TXT.bear.cli tune --protocol TXT/configs/tune_l1.json --menu TXT/configs/menus_v1.json --dry-run
```

### 12.3. Kiểm chứng phù hợp thay đổi

Chỉ đổi Markdown: kiểm diff/links/UTF-8/metric deltas/dependency consistency. Khi thực sự sửa code N1/N2/N3/N4, chạy tests của invariants mới và suite liên quan; không dùng test xanh làm quality benchmark. Thiết lập temp/cache dưới TXT trước tests. Handover giữ lệnh PowerShell chi tiết.

Không cài model/GPU dependencies để kiểm Markdown hoặc audit cached artifacts. CPU R0 cần NumPy; đọc membership parquet cần pandas/pyarrow. Cost ceilings/model API audit cho sparse vẫn là task sau, chưa mở trong vòng này.

## 13. Dependency, song song và bước bắt đầu

### 13.1. Dependency graph

```text
N0 provenance + baseline verified
  → N1 application/fallback/output audit
      ├─ N2 fixed body/local dev study ─┐
      │    └─ N4 F0/O0/H3/controls    │
      │          └─ A1 chỉ khi go    ├─ N5 dev shortlist/interactions
      └─ N3 C1/C2 chunk dev study ────┘      → freeze one → one holdout
                                                → full features/integrity
```

N2/N3 độc lập sau readiness mỗi nhánh. N4 cần B/D + N2, không cần N3. Nhánh thiếu labels có thể làm audit/runner độc lập; không tính metric thiếu coverage. N5 chỉ cần candidate hợp lệ, không đợi mọi backlog/adaptive/sparse.

### 13.2. Mốc bàn giao

Mỗi task bàn giao input/config/code/output identities, lệnh thật đã chạy, expected/effective scope, số đo/CI/cost/missingness, quyết định và task tiếp theo. Append improvement log, giữ trials âm và rollback; cập nhật trạng thái kỹ thuật theo bằng chứng mới, không sửa report cũ để che lịch sử.

Giữ task status riêng: planned/in-progress/blocked-input/diagnostic/completed; quality decision riêng: keep/reject/inconclusive. Dependency missing không đồng nghĩa phương pháp bị reject. Chưa có kết quả thì report phải nói chưa đo, không ghi0 hoặc simulated gain.

### 13.3. Agent tiếp theo bắt đầu ngay

1. Đọc plan, proposal §2/§13, handover và improvement log; kiểm git/instructions mới.
2. N0 inventory/link R01, reuse verified baseline hoặc chỉ yêu cầu14roles còn thiếu để R0.
3. N1 phân tích artifacts có sẵn; nếu thiếu công cụ audit thì implement tool độc lập theo §11, không chạy experiment/gate để thay việc audit.
4. Báo N0/N1 result/blockers và chọn N2/N3 task đầu tiên đủ input. Chưa tự mở holdout, full GPU jobs hoặc nộp bài.

## 14. Definition of Done và nguồn tra cứu

- [ ] Điểm B00/R01 được giữ đúng, reported/observed tách biệt và provenance/missing fields rõ.
- [ ] N0/N1 có thực chứng hoặc blocker cụ thể; sample/full và eligible/applied/fallback không bị đánh đồng.
- [ ] N2/N3 có controlled results đúng scope hoặc dependency report; không quy coverage/slot gain cho selector/gate.
- [ ] N4 có quyết định go/defer, chưa bypass guard khi thiếu evidence.
- [ ] N5 chỉ complete khi candidate/metric/controls/holdout/full integrity thực sự đủ; mọi nhánh không bắt buộc phải chạy.
- [ ] Config/menu/input/code/labels/output hashes, cost, negative results, log và rollback được giữ.

Tra cứu: [proposal](TXT_Proposal.md), [handover](TXT_handover.md), [improvement log](improvement_log.md), [technical ledger](reports/IMPLEMENTATION_STATUS.md), [evaluator contract](reports/EVALUATOR_CONTRACT.md), [runbook](reports/RUNBOOK.md), [baseline gốc](../doc/HANDOVER.md). Chi tiết T01–T16 và thiết kế trước ở [PLAN archive](archive/PLAN_before_N0_N5_20261019.md); khi mâu thuẫn về thứ tự/khả năng hiện có, dùng PLAN v2 và code thật.
