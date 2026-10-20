# PLAN v3 — Bước tiếp theo sau khi đóng L1/L4

Cập nhật **20/10/2026**. Đây là phiên bản **kế hoạch nghiên cứu**; phần mềm `TXT/bear` vẫn là **2.0.0**. Vòng mới `PROPOSED`; lượt này chỉ cập nhật tài liệu.

**Quyết định:** giữ bài **0.4076** làm mốc, không nộp các biến thể L1/L4 vừa thử. Dùng cache để tìm chỗ mất doc đúng, rồi chạy **một họ thử nghiệm, tối đa hai cấu hình mới**. Không có tín hiệu rõ thì giữ bài tốt nhất và dừng vòng này.

Đọc [proposal](TXT_Proposal.md), [handover](TXT_handover.md), [kết quả L1/L4](reports/L1_L4_20261020.md), [nhật ký](improvement_log.md). [PLAN v2](archive/PLAN_v2_before_pivot_20261020.md) giữ nguyên hợp đồng phần mềm và lịch sử N0–N5.

## 1. Thay đổi so với kế hoạch trước

- **N0/N1:** chấp nhận báo cáo chạy đủ 1.200 câu, dựng lại w045 khớp 100%, trung bình thay 5,5 doc/câu. Không chạy lại làm điều kiện mở vòng mới. Thiếu artifact ở checkout chỉ giới hạn việc tự kiểm tại đây.
- **N2 / L1–L4:** đã có kết quả trên cùng bài 0.4076; đóng các cấu hình hiện tại. Không tiếp tục quét λ hoặc thêm title/IDF rồi gọi là cùng phép thử.
- **N3:** bài tốt nhất dùng một chunk toàn thân bài/doc; không ưu tiên chọn chunk nhỏ.
- **N4:** không mở lại routing theo query. Oracle 07/10 được báo chỉ hơn khoảng 1,5% ở phép đo khi đó; không gọi đây là trần của mọi hệ thống.
- **Nhãn:** dùng nhãn BTC có sẵn để đánh giá offline; bỏ yêu cầu chỉ nhận nhãn gán tay. Không biến chunk failure hoặc doc chưa biết nhãn thành doc negative chắc chắn.
- Giảm việc phụ: một bảng chẩn đoán, một bảng kết quả, một entry log đủ cho lượt thử. Không dựng lại hệ thống manifest N0–N5 trước khi đo.

## 2. Điểm xuất phát

### 2.1. Các mốc chất lượng

| Mốc | Điểm bài được báo | Doc F2 | Chunk F2 | Nguồn / ý nghĩa |
|---|---:|---:|---:|---|
| B00 — w045_TF, 15/10 | FINAL 0.3442 | 0.3605 | 0.3279 | Lịch sử baseline |
| R01 — bài TXT/BEAR | FINAL 0.3445 | 0.3612 | 0.3279 | Người dùng báo; FINAL hơn B00 0.0003 |
| Bài tốt nhất hiện tại | **0.4076** | chưa cung cấp | chưa cung cấp | `REPORTED`; chưa gán tên run hoặc metric thành phần |

Không đồng nhất bài 0.4076 với archive có Doc F2 `0.407343155932693`: chưa có liên kết run chứng minh chúng là cùng một bài.

### 2.2. L1/L4 đã giải quyết câu hỏi gì?

Cùng bài 0.4076, giữ `k_q`, số doc ZH và chunk toàn thân bài; chỉ chọn/xếp lại VI trong pool400 bằng `full_v1`. Mỗi họ sáu λ gồm control0:

| λ | 0 | 0.02 | 0.05 | 0.10 | 0.20 | 0.35 |
|---|---:|---:|---:|---:|---:|---:|
| L1: ΔDoc F2 | 0 | +0.0003 | +0.0002 | +0.0003 | −0.0021 | −0.0085 |
| L4: ΔDoc F2 | 0 | +0.0004 | +0.0001 | +0.0003 | −0.0018 | −0.0081 |

Theo báo cáo, CI95 đều chạm0 hoặc ở phía âm; coverage 100%/99,6% chưa có mẫu số chi tiết. Gain tốt nhất +0.0004 chưa chứng minh cải thiện, không phải ΔFINAL. Kết luận chỉ áp dụng cho feature/cấu hình này, không phủ định mọi cách dùng bằng chứng y khoa.

### 2.3. Baseline phải bảo toàn

**Mốc so sánh mới là artifact bài 0.4076 của người vận hành**, cùng corpus, query set, ranking, `k_q`, danh sách ZH/non-VI và exporter toàn thân bài đang dùng. Ghi đường dẫn/định danh khi chạy; chưa có artifact ở checkout thì không đặt tên hoặc tạo fingerprint giả.

B00 vẫn được giữ: `w045_TF`, doc fingerprint `c1e068422e5f`, chunk fingerprint `fd07f9fc029a`, 1.200×200doc. Đây là ràng buộc B00; không áp mặc định lên bài 0.4076.

## 3. Phạm vi và nơi lưu

### 3.1. Luồng công việc

`M0: tái dùng cách chấm → M1: tìm nút thắt → M2: một phép thử từ cache → M3: giữ hoặc dừng`.

M0/M1 tái dùng outputs lượt vừa chạy. Không yêu cầu reproduce w045, tạo lại full_v1 hoặc gán nhãn tay toàn tập.

### 3.2. Đầu ra tối thiểu

Khi thực thi, dự kiến lưu `diagnosis.csv`, `trials.csv`, `per_query.csv` và cấu hình ngắn trong `TXT/runtime/pivot_v3/<run_id>/`. Một report dẫn tới các file thật, nối kết luận vào log. Runtime này **chưa được tạo** bởi lần sửa tài liệu.

Ghi parent/control, định danh artifact thực dùng, query universe, nguồn nhãn, quy tắc thử, mọi cấu hình/metric và quyết định. Không dựng thêm bộ khung quản trị nếu không giúp trả lời có tăng điểm hay không.

### 3.3. Giới hạn ghi

Mọi thay đổi mới nằm trong `TXT/`. Legacy code, corpus, nhãn nguồn và outputs cũ chỉ đọc. Output mới dùng tên riêng, không ghi đè bài 0.4076/run đã xong. Không tự upload bài nộp trong lượt cập nhật tài liệu.

## 4. Khả năng code hiện có

BEAR2.0.0 đã có pool/features, L1/L4, audit, chunk study và paired metrics. Báo cáo kỹ thuật trước ghi **63/63 BEAR +10/10 legacy tests** qua fixtures; không phải benchmark hoặc tests vừa chạy hôm nay.

Runner qrels hiện yêu cầu schema reviewed; một số pool/evaluate/release gắn `k=200` và allocation B00. **Chưa có adapter BTC val.jsonl/variable-k bảo đảm dùng thẳng cho bài 0.4076.** Ưu tiên script chấm/exporter của lượt thật vừa chạy. Nếu cần code, chỉ bổ sung adapter/diagnostic nhỏ cho phép thử; không triển khai lại N0–N5.

## 5. Bằng chứng và thiếu dữ liệu

### 5.1. Trạng thái

`REPORTED`: người dùng/người vận hành báo. `ARTIFACT_OBSERVED`: kiểm trực tiếp file với phạm vi rõ. `CODE_VERIFIED`: kiểm kỹ thuật, không chứng minh gain. `PROPOSED`: chưa chạy.

### 5.2. Input theo đúng phép thử

Dùng bài0.4076, ranking/score cache liên quan, nhãn BTC và script chấm lượt vừa chạy. Chỉ yêu cầu file thiếu cho phép thử đang chọn. Thiếu deep scores thì bỏ nhánh phụ thuộc; không phủ nhận kết quả remote hoặc chặn chẩn đoán cache hiện có.

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

Corpus/chunk đúng snapshot, offsets Unicode end-exclusive, text nguyên văn `body[start:end]`. Hash body gốc UTF-8; không dùng `body.find(text)` để suy offset đoạn lặp. Full-body chunk dùng đúng nội dung/offset exporter bài tốt nhất đang xuất.

Nhãn chỉ dùng đánh giá/chẩn đoán; không join `gold/not_gold/gold_unseen/G_q` vào thuật toán chọn doc production. Chi tiết schema code2.0 tại [PLAN v2 §6](archive/PLAN_v2_before_pivot_20261020.md#6-hợp-đồng-dữ-liệu-và-provenance).

## 7. Compatibility lịch sử B00

### 7.1. Recipe R0

Code `baseline.py` vẫn tái lập w045: top400 mỗi model/query language, patch109 replace row; ZH RRF k60 weights1/1/0.3/0.3; VI:ZH1:0.45; base top200/head tối đa120 từ alt top240; membership/vinmec/refill; calibration8 và allocation B00. Recipe exact/rounding/ties giữ ở [PLAN v2 §7](archive/PLAN_v2_before_pivot_20261020.md#7-r0-compatibility-và-rollback).

Đây là hợp đồng compatibility, **không phải bước bắt đầu lại** hoặc exporter mặc định vòng mới. Không refit beta/đổi allocation B00 để xuất bài0.4076.

## 8. Chẩn đoán đúng tầng

### 8.1. Ba tập khác nhau

1. **Source pool:** hợp ứng viên các retriever, có thể sâu hơn400.
2. **Rerank/study pool:** tập có score để chọn lại;400 là scope lượt L1/L4.
3. **Selected set:** docs thực xuất trong bài0.4076 với `k_q` của nó.

Không suy source pool bài tốt nhất chỉ có400doc. `doc/HANDOVER.md` đã có nguồn top1000; đọc cache bài mới trước khi chọn hướng.

### 8.2. Không lặp hướng cũ thành ý tưởng mới

`doc/METHODS.md` ghi HyDE/PRF/subquery/một số dense sources mở pool cho kết quả yếu; tăng Qwen prefix1000→3000 ký tự không hơn ở phép đo đó. Chunk-dense đã có trong lịch sử baseline. Không ưu tiên chạy lại các hướng này hoặc routing nếu chưa có bằng chứng mới khác điều kiện cũ.

### 8.3. Protected matcher của package2.0

Giữ NFC/whitespace/case policy có version; dấu, số, short tokens, identifiers/boundaries. `type1≠type2`, `BRCA1≠BRCA10`, `V600E≠V600K`, `mg≠mcg`; không tự xác nhận alias bằng cosine. Matcher chưa hiểu đủ quan hệ/negation/intent; coverage không phải medical correctness. Hợp đồng vẫn áp dụng cho code dù nhánh nghiên cứu L1/L4 đóng.

## 9. Ngân sách thử mới

Chọn **một họ thử nghiệm**, tối đa **hai cấu hình khác control**, sau M1. Đọc lịch sử bài0.4076 để bỏ phép thử đã làm. Không mở menu kết hợp nhiều trọng số/λ/model.

M2 có hai lựa chọn: số doc nếu chưa thử trên baseline mới, hoặc mở phạm vi chọn/chấm lại nếu có known positives và cache phù hợp. Không đủ điều kiện cả hai thì giữ baseline; không tạo thêm ý tưởng để lấp lịch.

## 10. Evaluation cho nhãn thực có

### 10.1. Nhãn BTC được dùng, nhưng giữ đúng nghĩa

Người vận hành có `data/lb/val.jsonl`; checkout có [val.jsonl](../val.jsonl). Chưa chứng minh hai file giống hệt. Local file có593qid, các trường `G/gold/not_gold/gold_unseen`. `gold` là positive đã biết; `not_gold` có thể chứa gold doc vì chunk bài trước không overlap≥0.4. Không coi chunk failure là doc negative chắc chắn; ID thiếu là unknown.

Kiểm local thấy205câu có `G−len(gold)−gold_unseen>0`, tổng305, trung bình0.5143doc/câu. Bất nhất này không chỉ ra doc nào sai hoặc chứng minh nguyên nhân. **±0.0002** là ước lượng người chạy báo, chưa phải bound/CI được xác minh.

### 10.2. Doc F2 và thay đổi tập doc

Mỗi query: `F2_q=5*g_q/(4*G_q+k_q)`; lấy mean cùng query universe/empty-gold policy control. Không tính macroF2 từ mean precision/recall.

Biết `G_q` thật và judgments đầy đủ cho tập dự đoán thì tính được DocF2, **không cần ID mọi gold doc ngoài tập đó**. Khi giữ `k_q`, judgments đáng tin trên added/removed đủ cho `ΔF2_q=5*Δg_q/(4*G_q+k_q)`. Khi đổi k, dùng đầy đủ hai công thức F2 và số hits control đáng tin; không dùng mẫu số chung.

### 10.3. Chunk và FINAL

Một chunk body/doc làm hai tầng gần nhau theo báo cáo, không bảo đảm bằng nhau. Chỉ gọi ChunkF2/FINAL chính thức khi dùng đúng scorer/semantics/tokenizer. Local LCS hoặc ΔDocF2 không thay hai metric đó. Parse score archive không đồng nghĩa đã tái lập scorer cho candidate mới.

### 10.4. CI và tập đã được xem

Paired CI95 dùng cùng query universe, ghi resampling/seed. Bootstrap không sửa false negatives hệ thống. 593câu đã xem/chọn nhiều cấu hình là validation đã được khai thác; không gọi lại là holdout sạch. Nếu có tập thực sự chưa xem, khóa candidate trước xác nhận; không tạo split mới rồi tuyên bố hết contamination.

### 10.5. Sensitivity thay gán tay hàng loạt

M0 phân biệt doc judgments trực tiếp, chunk-derived weak negatives và unknown. Dùng nhãn BTC thay yêu cầu gán tay bắt buộc. Tái dùng hits/counts control từ scoring artifact khi có đúng liên kết baseline.

Với changed docs có nhãn yếu/unknown, báo point estimate theo file hiện có và sensitivity nếu chúng thực ra là positive. Nếu hits control chưa chắc, đưa cả bất định đó vào phép so khi đổi k. Chỉ dùng ngân sách lỗi/query khi có chứng cứ là bound cho đúng snapshot; không lấy305 hoặc ±0.0002 làm bound mặc định. Không định lượng được thì ghi `inconclusive` ở kết luận cần nhãn đó. Có thể review đúng changed docs quyết định kết quả; không buộc gán lại593câu.

### 10.6. Tiêu chí quyết định

Chỉ cân nhắc promote khi ΔDocF2 dương, paired CI95 lower>0, hướng tăng còn giữ dưới sensitivity hợp lý đã nêu và chi phí/export hợp lệ. Báo subgroup để thấy gain tập trung ở đâu và các regression; không tự đặt thêm gate chưa định lượng. Có scorer Chunk/FINAL thì kiểm trực tiếp trước quyết định nộp. Tiêu chí này không bảo đảm điểm public/private tăng.

CI chạm0, sensitivity đổi dấu hoặc thiếu coverage không kiểm soát: giữ0.4076. Không nộp chỉ để xác nhận gain cỡ nhiễu. Không dùng ngưỡng ΔP@200 cũ để phán ΔDocF2/FINAL.

## 11. Các việc cần làm — M0 đến M3

### M0 — Tái dùng cách chấm vừa chạy

**Tối đa nửa ngày, cùng M1.** Nhận đúng đường dẫn artifact0.4076, ranking/score cache, script chấm L1/L4; kiểm query IDs, `G_q/k_q`, cách tạo `not_gold`, labels/unknown trên changed docs. Tái dùng λ0/per-query control có sẵn; không dựng lại w045.

**Đầu ra:** mô tả control/cách chấm, coverage và phần chỉ ước lượng. Aggregate0.4076 không phải nhãn doc. Adapter nếu cần chỉ giải quyết known-G/variable-k/label states; không giả annotator để ép file BTC vào schema manual qrels.

### M1 — Doc đúng còn bị bỏ ở đâu?

**Nửa ngày, cache hiện có.** Với known positives, chia thành bốn nhóm tách nhau: đã chọn; ở study pool400 nhưng không chọn; ngoài study pool400 nhưng trong source/deep cache; ngoài mọi cache hiện có. Ghi rank bins, ngôn ngữ, nguồn, coverage và độ sâu cache. Gold chưa biết ID không đưa vào nhóm “ngoài cache” như thể đã tìm thấy.

Oracle cùng k/quota chỉ chẩn đoán **headroom trên known positives**, không là oracle đầy đủ/dự báo chắc chắn. Không dùng oracle chọn doc production.

Đọc recipe/lịch sử0.4076: `k_q` đã tối ưu chưa, ranking sâu tới đâu, doc ngoài400 có đủ đúng loại score không? **Đầu ra:** `diagnosis.csv` và chọn A/B ở M2 hoặc đi thẳng M3.

### M2 — Một phép thử từ cache

**Tối đa một ngày máy**, control + tối đa hai candidate; không mặc định GPU/model mới.

**A — Chính sách số doc, ưu tiên nếu chưa thử trên0.4076.** Giữ ranking/score recipe, danh sách ZH/non-VI và một chunk body/doc; thay số VI bằng **cùng một hệ số cho mọi query**:
`c∈{0.85,1.00,1.15}`, `nVI'_q=round_half_up(c*nVI_q)`, `k'_q=nNonVI_q+nVI'_q`.
c=1 là control và phải giữ đúng tập doc bài0.4076. Chọn prefix VI theo ranking cũ đã khớp control, giữ thứ tự non-VI. Không chọn k tối ưu riêng từng câu bằng nhãn; k thay đổi có chủ đích ở nhánh A.

Kiểm trước giới hạn sốdoc/ZIP thật và ranking đủ sâu cho c=1.15. Không đủ thì bỏ candidate/ghi lý do, không clamp từng query rồi gọi cùng một phép thử. Nếu cùng chính sách đã được tối ưu trên baseline này thì bỏ A, không quét lại.

**B — Mở phạm vi chọn/chấm lại, chỉ khi M1 có headroom.** Giữ `k_q`, quota/danh sách ZH/non-VI và chunk body; study/rerank pool VI400→800, tối đa1000 nếu cache có độ sâu/score phù hợp. Baseline selected docs luôn có mặt. Giữ score recipe/ranker/ties; không đổi fusion weights, không tính lại source ranks sau restrict pool, không gán Qwen score0 cho doc chưa được chấm.

Chỉ làm B nếu cache đủ score cùng nghĩa hoặc rerank bổ sung nhỏ được dự toán trước và hoàn tất trong ngân sách. Không đủ thì dừng B. Đây không phải retriever/PRF/HyDE mới;400/800/1000 là depth study dự kiến, không phải giới hạn source pool đã xác minh.

**Chọn đúng một họ:** A nếu chưa thử và cache/giới hạn cho phép; nếu A đã giải quyết thì B chỉ khi có headroom/score thật. Không chạy cả A+B hoặc ghép best sau khi xem điểm. Không có nhánh đủ điều kiện thì giữ baseline.

### M3 — Có số rồi quyết định

Xuất mọi trials: ΔDocF2/paired CI95, số câu/doc đổi, judged/weak-negative/unknown coverage, sensitivity, chi phí và dung lượng ZIP nếu đã tạo. Có scorer đúng thì thêm ChunkF2/FINAL thực đo; chưa có ghi null.

Chọn tối đa một candidate theo §10.6 hoặc `retain_0.4076`. Chỉ candidate đáng thử mới chạy full1.200câu, kiểm IDs/membership, counts theo policy mới, body text/offset/package bằng exporter phù hợp. Không dùng fixed200/allocation B00 âm thầm đổi bài mới. Package kỹ thuật không đồng nghĩa đã nộp hoặc có điểm mới.

## 12. Lịch dự kiến

| Thời gian | Việc và điểm dừng |
|---|---|
| 20–21/10 | M0/M1 từ outputs hiện có; không chờ đủ mọi inputs N0 |
| 21–22/10 | M2 nếu đủ điều kiện; tối đa hai candidate |
| 23/10 | M3 keep/stop; không kéo dài bằng thêm λ/routing |
| 24–30/10 | Chỉ xác nhận/đóng gói candidate có bằng chứng; nếu không, giữ bài tốt nhất/hoàn thiện working notes |
| 31/10 | Hạn public theo người dùng; kiểm giờ đóng thực tế trước thao tác nộp |

Ngân sách/lịch dự kiến không yêu cầu dùng hết thời gian; kết luận sớm thì dừng sớm.

## 13. Agent tiếp theo bắt đầu

1. Đọc report L1/L4, PLAN và handover; không khởi động lại N0–N5.
2. Dùng script/outputs lượt0.4076 lập M1 và kiểm semantics nhãn trong cùng buổi.
3. Ghi “chọn A/B vì…” hoặc “không còn phép thử đủ điều kiện”; rồi mới chấm tối đa hai candidate.
4. Nối số thật/quyết định vào log; không gọi plan, fixture tests hay oracle là gain thực.

## 14. Hoàn tất và tài liệu kế thừa

Vòng nghiên cứu xong khi có M1 và quyết định M3 dựa trên số thật, hoặc lý do dừng cụ thể; không bắt buộc nộp mới. Lần cập nhật tài liệu này chưa thực thi M0–M3.

[Runbook](reports/RUNBOOK.md), [evaluator contract](reports/EVALUATOR_CONTRACT.md), [decisions](reports/DECISIONS.md), [giới hạn](reports/KNOWN_LIMITATIONS.md), [trạng thái code](reports/IMPLEMENTATION_STATUS.md). Các contract/error code/R0/matcher được code2.0 dẫn theo § vẫn có mục tương ứng; chi tiết tại PLANv2 archive. Reports N0–N5 ngày19/10 là snapshot checkout/fixtures khi đó, không phủ nhận lượt thật người dùng vừa báo.
