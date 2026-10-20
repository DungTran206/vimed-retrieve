# PLAN v3.2 — Baseline 0,391 và ý tưởng BEAR

Cập nhật **20/10/2026**. Kế hoạch nghiên cứu `PROPOSED`; phần mềm vẫn **BEAR 2.0.0**. Lượt này cải tiến tài liệu và đặc tả, chưa thay thuật toán chạy hoặc đo thêm điểm.

**Baseline giữ nguyên pipeline 0,391 của người dùng.** Vòng tiếp theo kiểm tra **threshold cuối trên p̂**, dùng cache có sẵn. BEAR giúp tìm các lỗi y sinh mà baseline chưa xử lý; chưa cộng thêm coverage, mở routing hay huấn luyện model mới.

Nguồn: [pipeline đọc từ ảnh](PIPELINE_0391.md), [đặc tả tham chiếu JSON](specs/pipeline_0391.json), [proposal BEAR](TXT_Proposal.md), [handover](TXT_handover.md), [log](improvement_log.md). JSON là mô tả, **không phải config chạy CLI**.

## 1. Vì sao kế hoạch đổi

Pipeline đã có BM25F, dense đầu bài, dense chunking, fusion đa ngôn ngữ, Qwen reranker, MaxP, p̂ và threshold. Không cần thêm lại các bước này dưới một tên mới.

Kế hoạch3.1 còn thử nhân số doc VI bằng0.85/1.15 và giữ ZH cuối cố định. Cách đó can thiệp khác policy được vẽ: **300VI+40ZH là ứng viên trước rerank; khoảng160 là trung bình sau threshold**. Kế hoạch3.2 bỏ menu count VI, thử đúng threshold cuối, để counts VI/ZH thay đổi theo cùng policy baseline.

Ý tưởng BEAR được giữ ở phần bảo toàn tên bệnh/thuốc/gene/biến thể, vị trí bằng chứng và quan hệ cần trả lời. Chuyển nó thành phân tích lỗi cụ thể trước khi thiết kế tín hiệu mới; không xem coverage hoặc đồng xuất hiện từ khóa là xác nhận relevance.

L1/L4 uniform coverage đã thử trên0.4076 và chưa có gain rõ. Không mở lại grid chỉ vì đổi baseline. N0/N1 của w045 đã được báo có kết quả; không bắt làm lại như cửa kiểm cho nghiên cứu mới.

## 2. Baseline và bằng chứng

### 2.1. Các mốc cần giữ riêng

| Mốc | Điểm được báo | Doc F2 / Chunk F2 | Vai trò |
|---|---:|---|---|
| B00 — w045_TF,15/10 | FINAL0.3442 | 0.3605 / 0.3279 | Lịch sử |
| R01 — TXT/BEAR | FINAL0.3445 | 0.3612 / 0.3279 | Lịch sử |
| R02 — bài0.4076 | 0.4076 | Chưa cung cấp | Control lịch sử của L1/L4 |
| **B01 — pipeline0.391** | **0.391** | Chưa cung cấp | **Control hiện hành do người dùng chọn** |

Không lấy0.407343... DocF2 trong archive thay metric thiếu của0.391/0.4076. Chọn baseline mới không phải phép so regression giữa hai run.

### 2.2. Kết quả L1/L4 đã có

Best ΔDocF2 được báo: L1+0.0003, L4+0.0004; CI95 chạm0 hoặc âm. Cả hai giữ k từng query, ZH và full-body chunk trên control0.4076, chỉ chọn lại VI trong pool400. [Report đầy đủ](reports/L1_L4_20261020.md) giữ nguyên bảng6λ và giới hạn nhãn. Không chuyển delta/CI sang0.391.

### 2.3. Baseline phải bảo toàn

Theo ảnh: VI có3 nguồn top1000 →union khoảng2200 →RRF k60 →top300; ZH có4 đóng góp trọng số1/1/0.3/0.3 →RRF →400 →top40. Ghép khoảng340 ứng viên →Qwen reranker4B →P(Yes) →MaxP →p̂ →threshold để trung bình khoảng160doc/query.

Giữ đúng corpus/query snapshot, danh sách ứng viên, score/precision, cách tính MaxP/p̂, comparator/ties, chunk policy và exporter thực dùng. Chưa có threshold, công thức calibration hoặc chunk nộp từ ảnh; không tự điền từ w045 hoặc0.4076.

Trước phép thử, control ở threshold baseline phải khớp đúng doc set/counts và policy chunk của artifact0.391 đang có. Đây là đối chiếu input của phép thử, không reproduce toàn w045 hoặc chạy lại N0/N1.

## 3. Phạm vi và nơi lưu

### 3.1. Luồng công việc

`M0: nối đúng control/score → M1: phân tích biên + lỗi BEAR → M2: tối đa hai threshold → M3: chọn hoặc giữ baseline`.

M1 dùng được ngay các output/cache thực có. Phân tích lỗi BEAR không bắt buộc gán tay593câu hoặc chặn phép thử threshold.

### 3.2. Đầu ra tối thiểu

Một cấu hình mô tả control/menu/query universe; `diagnosis.csv`, `trials.csv`, `per_query.csv` dưới `TXT/runtime/threshold_0391/<run_id>/` khi thực thi. Nối kết luận vào log và dẫn file thật. Các runtime này **chưa được tạo** trong lượt sửa tài liệu.

Ghi đường dẫn/định danh snapshot thực dùng, nguồn nhãn, threshold/control, actual counts/coverage, mọi trial và quyết định. Metadata chưa có giữ null; không biến ghi chép thành một dự án riêng.

### 3.3. Giới hạn ghi

Mọi thay đổi mới trong `TXT/`; legacy, corpus, nhãn nguồn và output cũ chỉ đọc. Không ghi đè baseline/run đã hoàn tất hoặc tự upload bài. Không tải model/chạy lại embedding toàn kho để phục vụ vòng cache này.

## 4. Code hiện có và phần chưa tương thích

BEAR2.0.0 có evidence matcher/features, fusion, audit, paired metrics, chunk study và release. Kết quả63/63BEAR+10/10legacy fixtures là nghiệm thu lịch sử, không phải gain hoặc tests vừa chạy.

Một số runner dùng reviewed-qrels, fixed-k/complete-universe guards; exporter cũ yêu cầu1.200×200doc và allocation B00. **Chưa có CLI threshold-study0.391 được nghiệm thu.** Tái dùng evaluator/exporter đúng baseline; nếu cần, chỉ bổ sung adapter mỏng cho cache p̂, variable-k và nguồn nhãn BTC.

Code root `val_calib.py` có nhánh `--maxp`, đọc max score/query-doc từ `data/cc_scores.jsonl` và có cấu hình beta8/beta10. Đây là quan sát code, **chưa chứng minh0.391 dùng nhánh này**. Không gọi code đó mặc định vì có thể fit/ghi beta; không dùng compatibility calibration8 của w045 thay model MaxP chưa được nối artifact.

Hàm `score_cands(..., top=200)` của file này còn mặc định cắt200ứng viên; không coi gọi nó nguyên trạng là đã chấm đủ300VI+40ZH theo ảnh. Kiểm cache thực có đủ p̂ của cả doc được chọn lẫn doc có thể được thêm khi hạ threshold.

## 5. Trạng thái và input

### 5.1. Mức bằng chứng

`REPORTED`: người dùng báo; `ARTIFACT_OBSERVED`: đọc file/ảnh với phạm vi rõ; `CODE_VERIFIED`: đối chiếu kỹ thuật; `PROPOSED`: chưa chạy; `DOC_ONLY`: sửa tài liệu.

### 5.2. Input thực sự cần

Prediction/control0.391, cache score p̂ cho tập ứng viên, policy threshold/precision/comparator thực dùng, query universe và evaluator/nhãn cùng snapshot. Chunk exporter chỉ cần khi xác nhận tác động chunk/package; không yêu cầu đủ14roles w045.

Thiếu score hoặc threshold thì chỉ dừng nhánh phụ thuộc; vẫn ghi được chẩn đoán và kiến trúc. Không giả score0, annotator, threshold hoặc metric để vượt thiếu input.

### 5.3. Error codes của phần mềm tiếp tục giữ

`INPUT_MISSING`, `HASH_MISMATCH`, `SCHEMA_INVALID`, `BASELINE_PARITY_FAILED`, `FEATURE_UNAVAILABLE`, `LABEL_COVERAGE_INSUFFICIENT`, `EVALUATOR_UNVERIFIED`, `OUTPUT_OUTSIDE_TXT` giữ nghĩa trong code. Báo đúng input/scope thiếu; không kết luận mọi nghiên cứu đều bị chặn.

## 6. Hợp đồng dữ liệu

Giữ namespace ID và thứ tự/score nguồn; không ép float thành ID, tự dedupe hoặc tính lại RRF ranks sau restrict pool. Missing khác0. Cache p̂ phải nối đúng query/doc/corpus/score recipe.

Chunk giữ nguyên văn, offsets Unicode end-exclusive và body/hash snapshot. “Lấy full” sau top300 chỉ nói về danh sách ứng viên; không chứng minh chunk=body.

Nhãn `gold/not_gold/G/gold_unseen` chỉ dùng đánh giá/chẩn đoán, không đọc vào inference để chọn doc hay threshold riêng từng query. Chi tiết code2.0 vẫn ở [PLAN v2 §6](archive/PLAN_v2_before_pivot_20261020.md#6-hợp-đồng-dữ-liệu-và-provenance).

## 7. Compatibility B00 được giữ riêng

### 7.1. Recipe R0

Baseline module vẫn phục vụ w045 với fingerprints `c1e068422e5f/fd07f9fc029a`,200doc/query, calibration8 và allocation cũ. [PLAN v2 §7](archive/PLAN_v2_before_pivot_20261020.md#7-r0-compatibility-và-rollback) giữ recipe exact/rounding/ties. Đây không phải exporter/control mặc định của0.391.

## 8. Ý tưởng BEAR nằm ở đâu trong pipeline mới?

### 8.1. Điều baseline đã làm

BM25F giữ khớp từ; dense giúp diễn đạt khác; dense chunking đưa thông tin đoạn vào retrieval; reranker/MaxP chấm lại; threshold chọn tập doc. BEAR phải cho thông tin bổ sung ngoài các bước này mới đáng thay score.

### 8.2. Phân tích lỗi cụ thể, chưa thay điểm

Xem doc gần threshold có mismatch về identifier/biến thể, phủ định, quan hệ/chỉ định, liều/đơn vị, nhóm bệnh nhân hoặc từ khóa nằm ở các đoạn không liên quan. Lưu query span, đoạn văn dẫn chứng, cờ quan sát và mức chắc chắn/unknown.

Coding agent có thể trích text và cờ kỹ thuật, không tự biến nhận định y khoa thành gold. `not_gold` yếu không đủ gọi doc là false positive. Không hard-filter hoặc tự sửa p̂ vì một cờ BEAR.

Chỉ khi có lỗi lặp lại và tín hiệu khác L1/L4, mới đề xuất pilot riêng cho **một loại mismatch**, có đối chứng và nhãn phù hợp. Pilot đó chưa được mở trong vòng threshold.

### 8.3. Protected matcher tiếp tục giữ

Giữ dấu/số/boundaries, `type1≠type2`, `BRCA1≠BRCA10`, `V600E≠V600K`, `mg≠mcg`. Alias không được tự xác nhận bằng cosine; coverage/đồng xuất hiện chưa chứng minh relation hoặc medical correctness.

## 9. Menu thử nghiệm: threshold cuối, không VI-count

Chỉ khi artifact xác nhận **một threshold chung τ₀** và cùng score/comparator/rounding, chọn tối đa hai threshold khác control từ **phân bố p̂ không dùng nhãn**.

Gọi `K̄₀` là số doc trung bình thực tế của control trên query universe cache đã khai báo. Không ép bằng160. Hai mục tiêu là `0.85×K̄₀` và `1.15×K̄₀`, tính trên **tổng VI+ZH**, không phải số VI hoặc count riêng từng query.

Với mỗi mục tiêu, chọn threshold khả dụng có mean count gần mục tiêu nhất; nếu hòa, chọn threshold gần τ₀ nhất, rồi giá trị threshold nhỏ hơn. Giữ đúng precision/comparator/ties của baseline. Ghi threshold và mean đạt thật; score rời rạc có thể không đạt mục tiêu chính xác. Bỏ threshold trùng control/trùng nhau hoặc không đổi output; không bù bằng mở grid.

Threshold/targets chốt trước khi dùng nhãn chấm. Giữ nguyên score p̂ và toàn bộ ứng viên thực có, reranker/MaxP/cách tính p̂, chunk selector/exporter không can thiệp. Counts và tỷ lệ VI/ZH cuối được thay đổi tự nhiên. Không cố định40ZH, top160/query, hoặc quotaVI×0.85/1.15.

Nếu threshold theo query/ngôn ngữ hoặc có policy bổ sung chưa rõ, không giả định globalτ₀; dùng đúng policy/config trước khi thiết kế phép thử tương ứng. Nếu lịch sử đã tối ưu cùng threshold trên baseline này, bỏ study thay vì lặp. Mở pool, refit calibration, BEAR residual và routing nằm **backlog riêng**, không ghép vào hai trial hiện tại.

## 10. Đánh giá đúng khi số doc thay đổi

### 10.1. Nhãn BTC dùng được, nhưng giữ semantics

Checkout [val.jsonl](../val.jsonl) có593query; đường dẫn người chạy báo là `data/lb/val.jsonl`, chưa chứng minh cùng snapshot. `gold` là positive đã biết; `not_gold` có thể suy từ chunk failure nên có false negatives. Unknown không tự thành0.

205dòng có `G−len(gold)−gold_unseen>0`, tổng305, chưa xác định ID lỗi hoặc bound cho chúng. Ước lượng±0.0002 của người chạy không phải CI/bound bảo đảm. Không bắt gán tay lại toàn593câu.

### 10.2. Variable-k cần cả hits control

`F2_q=5*g_q/(4*G_q+k_q)`; mean theo cùng query universe/empty-gold policy, không tính F2 từ meanP/meanR.

Khi k đổi, đặt `D₀=4G+k₀`, `D₁=4G+k₁` và `Δg=hits_added−hits_removed`:
`ΔF2=5*[g₀*(1/D₁−1/D₀)+Δg/D₁]`.

Cần hits control đáng tin hoặc đủ judgments cho hai prediction sets. Vì hệ số của g₀ khác0, uncertainty của **doc giữ nguyên** cũng có thể ảnh hưởng delta. Không chỉ kiểm added/removed; đưa bất định g₀ vào sensitivity. Khi k giữ nguyên mới dùng được `5*Δg/(4G+k)`.

### 10.3. Chunk và FINAL

Giữ selector/chunk budget theo cùng policy baseline cho mỗi doc; thêm/bớt doc có thể đổi số chunk toàn bài. Ảnh chưa mô tả output chunk. Chỉ gọi ChunkF2/FINAL chính thức khi có scorer đúng semantics/tokenizer; chưa có ghi null. ΔDoc không tự bằng ΔFINAL.

### 10.4. CI và dữ liệu đã khai thác

Paired CI95 trên cùng query universe, ghi seed/resamples. Bootstrap không sửa nhãn sai hoặc selection bias.593câu đã được xem nhiều lần là validation đã khai thác; không đổi tên thành holdout sạch. Nếu có tập thực sự chưa xem, freeze candidate trước xác nhận.

### 10.5. Sensitivity và audit BEAR

Báo judgments trực tiếp/weak-negative/unknown cho changed docs **và uncertainty hits control**. Chỉ dùng error budget khi có bound chứng minh cho đúng snapshot. Không đủ thì `inconclusive`; vẫn báo known-positive diagnostics. Audit span/mismatch BEAR không thay relevance labels.

### 10.6. Chọn hoặc giữ baseline

Chỉ cân nhắc candidate khi ΔDocF2 dương, paired CI95 lower>0, sensitivity hợp lý không đảo hướng và chi phí/export hợp lệ. Báo nhóm được/mất lợi; đo Chunk/FINAL trực tiếp nếu scorer sẵn. CI không bảo đảm public/private tăng.

Không rõ gain, nhãn hoặc score scope: `retain_0.391`. Không nộp chỉ để dò gain cỡ nhiễu; không chọn top-k/threshold riêng query bằng gold.

## 11. M0–M3 giao việc

| Bước | Việc làm và đầu ra tối thiểu |
|---|---|
| **M0 — Control đúng** | Nhận cache p̂/prediction/policy0.391; xác nhận scope threshold, comparator/precision và replay đúng selected set/counts/chunk policy. Không dựng lại w045, không refit beta. |
| **M1 — Biên threshold + BEAR** | Đếm known positives trên/dưới τ₀, nhãn yếu/unknown, phân bố score/ngôn ngữ/counts. Xem một số trường hợp sát biên để ghi mismatch/identifier/intent kèm text; không coi audit là gold hoặc điều kiện gán tay hàng loạt. |
| **M2 — Hai threshold tối đa** | Dùng menu §9 đã chọn không nhìn nhãn. Giữ score/candidates/chunk policy; chấm cả hai và control. Nếu đã tối ưu/không đủ điều kiện, bỏ qua và sang M3. |
| **M3 — Có số rồi quyết định** | Ghi mọi trial, paired metric/CI, sensitivity gồm g₀, actual counts/VI-ZH/chi phí. Chọn tối đa một candidate hoặc giữ0.391. Nối log; chỉ full export bằng pipeline tương thích khi có bằng chứng. |

Đầu ra M1 có thể đề xuất một nghiên cứu BEAR riêng sau này; không dùng nó để mở thêm λ trong M2.

## 12. Ngân sách và điểm dừng

M0/M1 cùng nửa buổi từ cache có sẵn; M2 tối đa một ngày máy; M3 quyết định ngay khi có số. Không GPU/model mới mặc định. Theo mốc public31/10 người dùng cung cấp, ưu tiên kết luận20–23/10,24–30/10 chỉ xác nhận/đóng gói candidate đáng giữ. Kiểm giờ đóng thực tế trước nộp.

Không có phép thử đủ điều kiện hoặc không có gain đáng tin thì dừng sớm. Không yêu cầu dùng hết ngày hoặc tạo bài nộp mới.

## 13. Agent tiếp theo đọc theo thứ tự

[README](README.md) →[pipeline](PIPELINE_0391.md) →[proposal](TXT_Proposal.md) →PLAN này →[handover](TXT_handover.md). Chỉ đọc archives khi cần code/recipe lịch sử; không chạy batch N0–N5.

Trả kết quả bằng bảng control/two trials hoặc lý do dừng cụ thể, không viết “tăng điểm” từ spec, fixture tests hoặc oracle.

## 14. Hoàn tất và lịch sử

Vòng nghiên cứu xong khi có chẩn đoán M1 và quyết định M3 từ số thật hoặc lý do dừng có phạm vi; không bắt buộc mở model mới/nộp mới. Lượt này chưa thực thi M0–M3.

[PLAN3.1 trước cập nhật](archive/PLAN_v3_1_before_threshold_alignment_20261020.md), [evaluator](reports/EVALUATOR_CONTRACT.md), [runbook](reports/RUNBOOK.md), [decisions](reports/DECISIONS.md), [limits](reports/KNOWN_LIMITATIONS.md), [code status](reports/IMPLEMENTATION_STATUS.md). Các mục §2.3/§3.3/§5.3/§6/§7/§8.3 vẫn giữ nghĩa compatibility cho code; chi tiết cũ nằm ở PLANv2 archive.
