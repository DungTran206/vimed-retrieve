# PLAN v3.1 — Tiếp tục từ baseline Pipeline 0,391

Cập nhật **20/10/2026**. Đây là phiên bản **kế hoạch nghiên cứu**; phần mềm `TXT/bear` vẫn là **2.0.0**. Vòng mới `PROPOSED`; lượt này chỉ cập nhật tài liệu.

**Quyết định mới:** dùng **baseline 0.391** theo chỉ định người dùng và file [Pipeline 0,391 - Miro.html](<../Pipeline 0,391 - Miro.html>). Dùng đúng ranking, cách chọn doc/chunk và evaluator của pipeline này để chạy M0–M3. Vẫn giới hạn **một họ thử nghiệm, tối đa hai cấu hình mới**; không có cải thiện đáng tin thì giữ baseline 0.391.

**0.4076 là mốc lịch sử của lượt L1/L4**, không còn là control vòng tiếp theo. Hai ảnh Miro đã được chuyển thành **[PIPELINE_0391.md](PIPELINE_0391.md)**:300VI+40ZH trước rerank; Qwen4B →P(Yes) →MaxP →p̂ →threshold để trung bình160doc/query. Đây không phải fixed-k160; không suy chunk=body từ “Lấy full”. Các tham số chưa ghi trong ảnh và full metrics được nêu ở [ghi nhận baseline](reports/BASELINE_0391_20261020.md).

Đọc [proposal](TXT_Proposal.md), [handover](TXT_handover.md), [kết quả L1/L4](reports/L1_L4_20261020.md), [nhật ký](improvement_log.md). [PLAN v2](archive/PLAN_v2_before_pivot_20261020.md) giữ hợp đồng phần mềm và lịch sử N0–N5; [PLAN v3 trước đổi baseline](archive/PLAN_v3_before_baseline_0391_20261020.md) giữ quyết định cũ.

## 1. Thay đổi so với kế hoạch trước

- **N0/N1:** chấp nhận báo cáo chạy đủ 1.200 câu, dựng lại w045 khớp 100%, trung bình thay 5,5 doc/câu. Không chạy lại làm điều kiện mở vòng mới. Thiếu artifact ở checkout chỉ giới hạn việc tự kiểm tại đây.
- **N2 / L1–L4:** đóng các cấu hình đã thử trên bài 0.4076. Các delta/CI đó không phải phép đo trên 0.391; thay baseline không tự động mở lại grid.
- **N3:** full-body chunk/doc là thông tin của bài 0.4076. Baseline 0.391 chưa xác nhận policy chunk; giữ đúng policy mới khi chạy phép thử. Chưa ưu tiên mở chunk study chỉ vì thay baseline.
- **N4:** không mở lại routing theo query. Oracle 07/10 được báo chỉ hơn khoảng 1,5% ở phép đo khi đó; không gọi đây là trần của mọi hệ thống.
- **Nhãn:** dùng nhãn BTC có sẵn để đánh giá offline; bỏ yêu cầu chỉ nhận nhãn gán tay. Không biến chunk failure hoặc doc chưa biết nhãn thành doc negative chắc chắn.
- Giảm việc phụ: một bảng chẩn đoán, một bảng kết quả, một entry log đủ cho lượt thử. Không dựng lại hệ thống manifest N0–N5 trước khi đo.

## 2. Điểm xuất phát

### 2.1. Các mốc chất lượng

| Mốc | Điểm bài được báo | Doc F2 | Chunk F2 | Nguồn / ý nghĩa |
|---|---:|---:|---:|---|
| B00 — w045_TF, 15/10 | FINAL 0.3442 | 0.3605 | 0.3279 | Lịch sử baseline |
| R01 — bài TXT/BEAR | FINAL 0.3445 | 0.3612 | 0.3279 | Người dùng báo; FINAL hơn B00 0.0003 |
| Bài 0.4076 — lịch sử R02 | 0.4076 | chưa cung cấp | chưa cung cấp | `REPORTED`; control của thí nghiệm L1/L4 cũ |
| **B01 — baseline hiện hành** | **0.391** | chưa cung cấp | chưa cung cấp | Người dùng chọn theo file Pipeline 0,391; chưa xác nhận metric thành phần/run ID |

Các số 0.391, 0.4076 và Doc F2 archive `0.407343155932693` chưa có liên kết run/evaluator để so trực tiếp. Việc chọn baseline 0.391 không phải kết quả đo regression từ bài 0.4076.

### 2.2. L1/L4 trên 0.4076 — bằng chứng lịch sử

Cùng bài 0.4076, giữ `k_q`, số doc ZH và chunk toàn thân bài; chỉ chọn/xếp lại VI trong pool400 bằng `full_v1`. Mỗi họ sáu λ gồm control0:

| λ | 0 | 0.02 | 0.05 | 0.10 | 0.20 | 0.35 |
|---|---:|---:|---:|---:|---:|---:|
| L1: ΔDoc F2 | 0 | +0.0003 | +0.0002 | +0.0003 | −0.0021 | −0.0085 |
| L4: ΔDoc F2 | 0 | +0.0004 | +0.0001 | +0.0003 | −0.0018 | −0.0081 |

Theo báo cáo, CI95 đều chạm0 hoặc ở phía âm; coverage 100%/99,6% chưa có mẫu số chi tiết. Gain tốt nhất +0.0004 chưa chứng minh cải thiện, không phải ΔFINAL. Kết luận chỉ áp dụng cho feature/cấu hình này, không phủ định mọi cách dùng bằng chứng y khoa.

### 2.3. Baseline phải bảo toàn

**Mốc so sánh hiện hành là pipeline0.391**, nguồn người dùng chỉ định tại file Miro và hai ảnh bổ sung. Đọc [bản pipeline bằng chữ](PIPELINE_0391.md) trước khi triển khai: đầu vào rerank300VI+40ZH, output chọn theo threshold trên p̂ với mục tiêu trung bình160doc/query. Khi chạy, dùng artifact tương ứng của người vận hành để có threshold thật, corpus/query set, ranking/counts và policy chunk/exporter. Ảnh mô tả kiến trúc, chưa đủ để tự điền config tái tạo đầy đủ.

M0 chỉ đối chiếu control mới theo artifact có sẵn, không yêu cầu làm lại N0/N1 của w045. Không dùng λ0 hoặc per-query scores của 0.4076 thay control 0.391.

B00 vẫn được giữ: `w045_TF`, doc fingerprint `c1e068422e5f`, chunk fingerprint `fd07f9fc029a`, 1.200×200doc. Đây là ràng buộc B00; không áp mặc định lên baseline 0.391.

## 3. Phạm vi và nơi lưu

### 3.1. Luồng công việc

`M0: tái dùng cách chấm → M1: tìm nút thắt → M2: một phép thử từ cache → M3: giữ hoặc dừng`.

M0/M1 dùng outputs có sẵn của pipeline 0.391; chỉ tái dùng cache cũ khi cùng snapshot và recipe phù hợp. Không yêu cầu reproduce w045, tạo lại full_v1 hoặc gán nhãn tay toàn tập.

### 3.2. Đầu ra tối thiểu

Khi thực thi, dự kiến lưu `diagnosis.csv`, `trials.csv`, `per_query.csv` và cấu hình ngắn trong `TXT/runtime/pivot_v3/<run_id>/`. Một report dẫn tới các file thật, nối kết luận vào log. Runtime này **chưa được tạo** bởi lần sửa tài liệu.

Ghi parent/control, định danh artifact thực dùng, query universe, nguồn nhãn, quy tắc thử, mọi cấu hình/metric và quyết định. Không dựng thêm bộ khung quản trị nếu không giúp trả lời có tăng điểm hay không.

### 3.3. Giới hạn ghi

Mọi thay đổi mới nằm trong `TXT/`. Legacy code, corpus, nhãn nguồn và outputs cũ chỉ đọc. Output mới dùng tên riêng, không ghi đè baseline 0.391 hoặc các artifact 0.4076/run đã xong. Không tự upload bài nộp trong lượt cập nhật tài liệu.

## 4. Khả năng code hiện có

BEAR2.0.0 đã có pool/features, L1/L4, audit, chunk study và paired metrics. Báo cáo kỹ thuật trước ghi **63/63 BEAR +10/10 legacy tests** qua fixtures; không phải benchmark hoặc tests vừa chạy hôm nay.

Runner qrels hiện yêu cầu schema reviewed; một số pool/evaluate/release gắn `k=200` và allocation B00. **Chưa xác nhận runner/evaluator/exporter BEAR tương thích pipeline 0.391.** Ưu tiên script chấm/exporter thực dùng cho baseline mới. Nếu cần code, chỉ bổ sung adapter/diagnostic nhỏ cho phép thử; không triển khai lại N0–N5.

## 5. Bằng chứng và thiếu dữ liệu

### 5.1. Trạng thái

`REPORTED`: người dùng/người vận hành báo. `ARTIFACT_OBSERVED`: kiểm trực tiếp file với phạm vi rõ. `CODE_VERIFIED`: kiểm kỹ thuật, không chứng minh gain. `PROPOSED`: chưa chạy.

### 5.2. Input theo đúng phép thử

Dùng artifact baseline 0.391, ranking/score cache, nhãn BTC cùng snapshot và script chấm tương ứng. Chỉ yêu cầu file thiếu cho phép thử đang chọn. Thiếu deep scores thì bỏ nhánh phụ thuộc; không phủ nhận kết quả remote hoặc chặn chẩn đoán cache hiện có.

### 5.3. Error codes của phần mềm tiếp tục giữ

| Code | Cách xử lý |
|---|---|
| `INPUT_MISSING` | Nêu file/phép thử phụ thuộc; không nói mọi nghiên cứu đều bị chặn |
| `HASH_MISMATCH` | Kiểm snapshot; không sửa hash để hợp thức hóa |
| `SCHEMA_INVALID` | Nêu key/path sai; không ép kiểu/dedupe tùy tiện |
| `BASELINE_PARITY_FAILED` | Kiểm đúng control; không tune tham số để ép khớp |
| `FEATURE_UNAVAILABLE` | Missing khác score0; không bịa score |
| `LABEL_COVERAGE_INSUFFICIENT` | Báo unknown/sensitivity; không gọi metric chính xác |
| `EVALUATOR_UNVERIFIED` | Gọi đúng metric local hoặc metric tái lập |
| `OUTPUT_OUTSIDE_TXT` | Sửa đường dẫn trước khi ghi |

## 6. Hợp đồng dữ liệu tiếp tục giữ

QID/doc ID khớp namespace nguồn; không cắt prefix/ép float thành int tùy tiện. Ranking giữ thứ tự/score gốc trước lọc. Missing score khác0; không chuẩn hóa trọng số riêng theo doc thiếu nguồn.

Corpus/chunk đúng snapshot, offsets Unicode end-exclusive, text nguyên văn `body[start:end]`. Hash body gốc UTF-8; không dùng `body.find(text)` để suy offset đoạn lặp. Policy chunk theo exporter baseline 0.391, hiện chưa xác nhận. Nếu policy là full-body thì dùng đúng body/offset của nó; không tự bật full-body từ thông tin 0.4076.

Nhãn chỉ dùng đánh giá/chẩn đoán; không join `gold/not_gold/gold_unseen/G_q` vào thuật toán chọn doc production. Chi tiết schema code2.0 tại [PLAN v2 §6](archive/PLAN_v2_before_pivot_20261020.md#6-hợp-đồng-dữ-liệu-và-provenance).

## 7. Compatibility lịch sử B00

### 7.1. Recipe R0

Code `baseline.py` vẫn tái lập w045: top400 mỗi model/query language, patch109 replace row; ZH RRF k60 weights1/1/0.3/0.3; VI:ZH1:0.45; base top200/head tối đa120 từ alt top240; membership/vinmec/refill; calibration8 và allocation B00. Recipe exact/rounding/ties giữ ở [PLAN v2 §7](archive/PLAN_v2_before_pivot_20261020.md#7-r0-compatibility-và-rollback).

Đây là hợp đồng compatibility, **không phải bước bắt đầu lại** hoặc exporter mặc định vòng mới. Không refit beta/đổi allocation B00 để xuất baseline 0.391.

## 8. Chẩn đoán đúng tầng

### 8.1. Ba tập khác nhau

1. **Source pool:** hợp ứng viên các retriever, có thể sâu hơn400.
2. **Rerank/study pool:** tập có score để chọn lại;400 là scope lượt L1/L4.
3. **Selected set:** docs thực xuất trong baseline 0.391 với `k_q` của nó.

Theo ảnh, VI có3 nguồn top1000, union khoảng2200, RRF k60 lấy300; ZH có bước400→40; tập ghép trước rerank là340. Không gọi400 là cap VI hoặc340/160 là cùng một tầng. Đối chiếu counts/cap thực từ config/cache; `P0` của phép thử mở pool phải chỉ rõ tầng VI/ZH/rerank nào trong [pipeline](PIPELINE_0391.md).

### 8.2. Không lặp hướng cũ thành ý tưởng mới

`doc/METHODS.md` ghi HyDE/PRF/subquery/một số dense sources mở pool cho kết quả yếu; tăng Qwen prefix1000→3000 ký tự không hơn ở phép đo đó. Chunk-dense đã có trong lịch sử baseline. Không ưu tiên chạy lại các hướng này hoặc routing nếu chưa có bằng chứng mới khác điều kiện cũ.

### 8.3. Protected matcher của package2.0

Giữ NFC/whitespace/case policy có version; dấu, số, short tokens, identifiers/boundaries. `type1≠type2`, `BRCA1≠BRCA10`, `V600E≠V600K`, `mg≠mcg`; không tự xác nhận alias bằng cosine. Matcher chưa hiểu đủ quan hệ/negation/intent; coverage không phải medical correctness. Hợp đồng vẫn áp dụng cho code dù nhánh nghiên cứu L1/L4 đóng.

## 9. Ngân sách thử mới

Chọn **một họ thử nghiệm**, tối đa **hai cấu hình khác control**, sau M1. Đọc lịch sử và recipe baseline 0.391 để bỏ phép thử đã làm. Không mở menu kết hợp nhiều trọng số/λ/model.

M2 có hai lựa chọn: số doc nếu chưa thử trên baseline mới, hoặc mở phạm vi chọn/chấm lại nếu có known positives và cache phù hợp. Không đủ điều kiện cả hai thì giữ baseline; không tạo thêm ý tưởng để lấp lịch.

## 10. Evaluation cho nhãn thực có

### 10.1. Nhãn BTC được dùng, nhưng giữ đúng nghĩa

Người vận hành có `data/lb/val.jsonl`; checkout có [val.jsonl](../val.jsonl). Chưa chứng minh hai file giống hệt. Local file có593qid, các trường `G/gold/not_gold/gold_unseen`. `gold` là positive đã biết; `not_gold` có thể chứa gold doc vì chunk bài trước không overlap≥0.4. Không coi chunk failure là doc negative chắc chắn; ID thiếu là unknown.

Kiểm local thấy205câu có `G−len(gold)−gold_unseen>0`, tổng305, trung bình0.5143doc/câu. Bất nhất này không chỉ ra doc nào sai hoặc chứng minh nguyên nhân. **±0.0002** là ước lượng người chạy báo, chưa phải bound/CI được xác minh.

### 10.2. Doc F2 và thay đổi tập doc

Mỗi query: `F2_q=5*g_q/(4*G_q+k_q)`; lấy mean cùng query universe/empty-gold policy control. Không tính macroF2 từ mean precision/recall.

Biết `G_q` thật và judgments đầy đủ cho tập dự đoán thì tính được DocF2, **không cần ID mọi gold doc ngoài tập đó**. Khi giữ `k_q`, judgments đáng tin trên added/removed đủ cho `ΔF2_q=5*Δg_q/(4*G_q+k_q)`. Khi đổi k, dùng đầy đủ hai công thức F2 và số hits control đáng tin; không dùng mẫu số chung.

### 10.3. Chunk và FINAL

Bài 0.4076 được báo dùng một chunk body/doc và hai tầng gần nhau; chưa xác nhận điều đó cho 0.391, và không bảo đảm hai metric bằng nhau. Chỉ gọi ChunkF2/FINAL chính thức khi dùng đúng scorer/semantics/tokenizer. Local LCS hoặc ΔDocF2 không thay hai metric đó. Parse score archive không đồng nghĩa đã tái lập scorer cho candidate mới.

### 10.4. CI và tập đã được xem

Paired CI95 dùng cùng query universe, ghi resampling/seed. Bootstrap không sửa false negatives hệ thống. 593câu đã xem/chọn nhiều cấu hình là validation đã được khai thác; không gọi lại là holdout sạch. Nếu có tập thực sự chưa xem, khóa candidate trước xác nhận; không tạo split mới rồi tuyên bố hết contamination.

### 10.5. Sensitivity thay gán tay hàng loạt

M0 phân biệt doc judgments trực tiếp, chunk-derived weak negatives và unknown. Dùng nhãn BTC thay yêu cầu gán tay bắt buộc. Tái dùng hits/counts control từ scoring artifact khi có đúng liên kết baseline.

Với changed docs có nhãn yếu/unknown, báo point estimate theo file hiện có và sensitivity nếu chúng thực ra là positive. Nếu hits control chưa chắc, đưa cả bất định đó vào phép so khi đổi k. Chỉ dùng ngân sách lỗi/query khi có chứng cứ là bound cho đúng snapshot; không lấy305 hoặc ±0.0002 làm bound mặc định. Không định lượng được thì ghi `inconclusive` ở kết luận cần nhãn đó. Có thể review đúng changed docs quyết định kết quả; không buộc gán lại593câu.

### 10.6. Tiêu chí quyết định

Chỉ cân nhắc promote khi ΔDocF2 dương, paired CI95 lower>0, hướng tăng còn giữ dưới sensitivity hợp lý đã nêu và chi phí/export hợp lệ. Báo subgroup để thấy gain tập trung ở đâu và các regression; không tự đặt thêm gate chưa định lượng. Có scorer Chunk/FINAL thì kiểm trực tiếp trước quyết định nộp. Tiêu chí này không bảo đảm điểm public/private tăng.

CI chạm0, sensitivity đổi dấu hoặc thiếu coverage không kiểm soát: giữ baseline 0.391. Không nộp chỉ để xác nhận gain cỡ nhiễu. Không dùng ngưỡng ΔP@200 cũ để phán ΔDocF2/FINAL.

## 11. Các việc cần làm — M0 đến M3

### M0 — Dùng đúng control/evaluator của pipeline 0.391

**Tối đa nửa ngày, cùng M1.** Dùng artifact baseline 0.391, ranking/score cache và evaluator tương ứng; đọc `k_q`, độ sâu `P0`, cách xử lý ngôn ngữ, policy chunk và định dạng nộp thực tế. Kiểm query IDs, `G_q`, nhãn/unknown đúng snapshot. Tái dùng control outputs đã có của baseline mới; không thay bằng λ0/per-query scores 0.4076 hoặc dựng lại w045.

**Đầu ra:** mô tả control/cách chấm, coverage và phần chỉ ước lượng. Điểm báo 0.391 không phải nhãn doc hoặc bộ metrics thành phần. Adapter nếu cần chỉ giải quyết known-G/variable-k/label states; không giả annotator để ép file BTC vào schema manual qrels.

### M1 — Doc đúng còn bị bỏ ở đâu?

**Nửa ngày, cache hiện có.** Với known positives, chia thành bốn nhóm tách nhau: đã chọn; ở study/rerank pool `P0` của baseline mới nhưng không chọn; ngoài `P0` nhưng trong source/deep cache; ngoài mọi cache hiện có. Ghi rank bins, ngôn ngữ, nguồn, coverage và độ sâu cache. Gold chưa biết ID không đưa vào nhóm “ngoài cache” như thể đã tìm thấy.

Oracle cùng k/quota chỉ chẩn đoán **headroom trên known positives**, không là oracle đầy đủ/dự báo chắc chắn. Không dùng oracle chọn doc production.

Đọc recipe/lịch sử 0.391: `k_q` đã tối ưu chưa, ranking sâu tới đâu, doc ngoài `P0` có đủ đúng loại score không? **Đầu ra:** `diagnosis.csv` và chọn A/B ở M2 hoặc đi thẳng M3.

### M2 — Một phép thử từ cache

**Tối đa một ngày máy**, control + tối đa hai candidate; không mặc định GPU/model mới.

**A — Chính sách số doc, ưu tiên nếu chưa thử trên 0.391.** Chỉ mở sau khi recipe xác nhận có làn VI để can thiệp. Giữ ranking/score recipe, danh sách ZH/non-VI thực có và policy chunk của 0.391; thay số VI bằng **cùng một hệ số cho mọi query**:
`c∈{0.85,1.00,1.15}`, `nVI'_q=round_half_up(c*nVI_q)`, `k'_q=nNonVI_q+nVI'_q`.
c=1 phải giữ đúng tập doc và chunk policy của baseline 0.391. Chọn prefix VI theo ranking cũ đã khớp control, giữ thứ tự non-VI. Không chọn k tối ưu riêng từng câu bằng nhãn; k thay đổi có chủ đích ở nhánh A.

**Bổ sung từ ảnh Miro:** baseline đang dùng threshold trên p̂, không phải top-k trước rerank. Nếu nghiên cứu A, ranking phải là đầu ra sau rerank/MaxP/tính p̂ và control phải khớp policy threshold thực tế. Menu count là phép thử đề xuất, không phải tham số của pipeline hoặc bằng chứng baseline chưa tối ưu threshold.

Kiểm trước giới hạn sốdoc/ZIP thật và ranking đủ sâu cho c=1.15. Không đủ thì bỏ candidate/ghi lý do, không clamp từng query rồi gọi cùng một phép thử. Nếu cùng chính sách đã được tối ưu trên baseline này thì bỏ A, không quét lại.

**B — Mở phạm vi chọn/chấm lại, chỉ khi M1 có headroom.** Giữ `k_q`, quota/danh sách ZH/non-VI và policy chunk của 0.391; mở từ cap thật `P0` lên tối đa hai cap lớn hơn, chốt trước scoring theo cache/score và ngân sách thực có. Baseline selected docs luôn có mặt. Giữ score recipe/ranker/ties; không đổi fusion weights, không tính lại source ranks sau restrict pool, không gán Qwen score0 cho doc chưa được chấm.

Chỉ làm B nếu cache đủ score cùng nghĩa hoặc rerank bổ sung nhỏ được dự toán trước và hoàn tất trong ngân sách. Không đủ thì dừng B. Đây không phải retriever/PRF/HyDE mới. Chỉ dùng ví dụ400→800/1000 nếu xác nhận `P0=400` và có cache tương ứng; không áp các cap của lượt L1/L4 cũ sang baseline mới.

**Chọn đúng một họ:** A nếu chưa thử và cache/giới hạn cho phép; nếu A đã giải quyết thì B chỉ khi có headroom/score thật. Không chạy cả A+B hoặc ghép best sau khi xem điểm. Không có nhánh đủ điều kiện thì giữ baseline.

### M3 — Có số rồi quyết định

Xuất mọi trials: ΔDocF2/paired CI95, số câu/doc đổi, judged/weak-negative/unknown coverage, sensitivity, chi phí và dung lượng ZIP nếu đã tạo. Có scorer đúng thì thêm ChunkF2/FINAL thực đo; chưa có ghi null.

Chọn tối đa một candidate theo §10.6 hoặc `retain_0.391`. Chỉ candidate đáng thử mới chạy full1.200câu, kiểm IDs/membership, counts theo policy mới, chunk text/offset/package theo đúng policy của baseline mới bằng exporter phù hợp. Không dùng fixed200/allocation B00 âm thầm đổi bài mới. Package kỹ thuật không đồng nghĩa đã nộp hoặc có điểm mới.

## 12. Lịch dự kiến

| Thời gian | Việc và điểm dừng |
|---|---|
| 20–21/10 | M0/M1 từ outputs hiện có; không chờ đủ mọi inputs N0 |
| 21–22/10 | M2 nếu đủ điều kiện; tối đa hai candidate |
| 23/10 | M3 keep/stop; không kéo dài bằng thêm λ/routing |
| 24–30/10 | Chỉ xác nhận/đóng gói candidate có bằng chứng; nếu không, giữ baseline 0.391/hoàn thiện working notes |
| 31/10 | Hạn public theo người dùng; kiểm giờ đóng thực tế trước thao tác nộp |

Ngân sách/lịch dự kiến không yêu cầu dùng hết thời gian; kết luận sớm thì dừng sớm.

## 13. Agent tiếp theo bắt đầu

1. Đọc report L1/L4, PLAN và handover; không khởi động lại N0–N5.
2. Đọc [baseline 0.391](reports/BASELINE_0391_20261020.md); dùng script/outputs đúng pipeline mới lập M1, không lấy control 0.4076 thế vào.
3. Ghi “chọn A/B vì…” hoặc “không còn phép thử đủ điều kiện”; rồi mới chấm tối đa hai candidate.
4. Nối số thật/quyết định vào log; không gọi plan, fixture tests hay oracle là gain thực.

## 14. Hoàn tất và tài liệu kế thừa

Vòng nghiên cứu xong khi có M1 và quyết định M3 dựa trên số thật, hoặc lý do dừng cụ thể; không bắt buộc nộp mới. Lần cập nhật tài liệu này chưa thực thi M0–M3.

[Runbook](reports/RUNBOOK.md), [evaluator contract](reports/EVALUATOR_CONTRACT.md), [decisions](reports/DECISIONS.md), [giới hạn](reports/KNOWN_LIMITATIONS.md), [trạng thái code](reports/IMPLEMENTATION_STATUS.md). Các contract/error code/R0/matcher được code2.0 dẫn theo § vẫn có mục tương ứng; chi tiết tại PLANv2 archive. Reports N0–N5 ngày19/10 là snapshot checkout/fixtures khi đó, không phủ nhận lượt thật người dùng vừa báo.
