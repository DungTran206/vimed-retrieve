# Kết quả và quyết định hiện hành

## 22/10/2026 — v5 SapBERT-XLMR và optional LLM selector

Đã triển khai `medical_gate_sapbert_v2`: SapBERT concept–literal-term cache, generic/Sap dense fusion, semantic recipe identity, document terms từ cache union và LLM chọn subset shortlist. Lexical gate exact/source-backed aliases giữ riêng. Initial λ=0,30 và Sap affine 0,20–0,90 là ước lượng để tune, không phải optimum hoặc probability calibration đã fit.

Kiểm chứng cuối sau xóa prose cũ: **full TXT suite 173/173 tests qua trong 43,921 giây; 10/10 legacy tests qua**. Mười templates đã preflight đúng schema và báo paths mẫu chưa bind; 72 tuning configs hợp lệ trong max_trials=96. Không có LLM call trong kiểm numerical/preflight. Chi tiết [report v5](SAPBERT_V5_20261022.md), [preflight JSON](medical_v5_preflight_20261022.json), vận hành [handover](../TXT_handover.md).

Chưa tải checkpoint/dataset, chưa gọi endpoint/encoder thật, chưa fit trên real candidate pool hoặc đo gain trên 593 query. Gain=null; baseline 0,391 chưa được tái lập bằng v5. Kết quả lịch sử bên dưới giữ nguyên phạm vi, không quy gain cũ cho SapBERT/selector.

## 21/10/2026 — medical importance hypothesis v4

Đã triển khai taxonomy query terms, source-backed enrichment, Qwen3.5-9B client/prompts, original-concept matching, sigmoid calibration, BM25/dense medical gate, global/tier thresholds và cache replay. Có nhánh document-term extraction tùy chọn. Báo cáo [MEDICAL_HYPOTHESIS_20261021](MEDICAL_HYPOTHESIS_20261021.md) ghi phạm vi và readiness cụ thể.

Kiểm chứng thực hiện: **136/136 TXT tests + 10/10 legacy tests đạt**; gồm 38 tests cho phần medical mới. Demo offline 12 query synthetic đã chạy qua đủ bảy stages, chạy control RRF và kiểm reuse; không gọi model thật, không dùng KB y khoa thật, không suy gain từ fixture. CLI templates đã kiểm schema/preflight. Một số ResourceWarning đến từ legacy test helpers; không có test failure.

Val thật chỉ được đọc inventory/schema: 593 queries, 22.091 gold, 66.547 not_gold và 20.186 gold_unseen. Chưa fit/calibrate trên ứng viên thật vì KB, prepared queries, index và source scores ở paths template chưa có. Endpoint Qwen chưa được gọi. Không có baseline 0,391 rerun, quality gain hoặc submission mới.

**Triển khai lịch sử 20/10 — PLAN3.5:** BEAR có hai phần độc lập: corpus retrieval và fusion thay RRF, dùng chung index/scorer. [Báo cáo triển khai](BEAR_PARTS_20261020.md) ghi 98 BEAR +10 legacy tests qua và demo tổng hợp chạy thật. Đây là prototype lexical/explicit-relation, chưa có quality gain hoặc baseline0,391 parity mới. Các đoạn v3.3/v3.4 bên dưới mô tả lịch sử trước triển khai hai phần.

Cập nhật **20/10/2026**. Người dùng đã chọn **baseline mới 0,391** và xác nhận tiếp tục ý tưởng BEAR trong proposal. [PIPELINE_0391.md](../PIPELINE_0391.md) ghi kiến trúc đọc từ hai ảnh; [spec tham chiếu](../specs/pipeline_0391.json) không phải config thực thi. Điểm có mức bằng chứng `REPORTED`, baseline là `USER_SELECTED`; chưa liên kết metric/run/cache. Xem [hồ sơ baseline](BASELINE_0391_20261020.md), [snapshots kế hoạch cũ](CLEANUP_20261022.md) và [lịch sử cải tiến](../improvement_log.md).

**Mở rộng3.4 theo người dùng, lịch sử:** F1/R1/C1/S1/J1 từng là thiết kế thử BEAR thay từng khối retrieval, ưu tiên fusion trước top300; xem snapshots qua cleanup. Đây chưa là kết quả quality. Pilot selector3.3 và các số lịch sử bên dưới giữ đúng phạm vi, không chứng minh BEAR đã thay candidate generator toàn kho.

L1/L4 trên **bài 0,4076 trước đây** vẫn đóng theo kết quả đã báo: tối đa `+0.0003` / `+0.0004` Doc F2, CI95 chạm 0 hoặc âm. [Bảng sáu λ và giới hạn nhãn](L1_L4_20261020.md) là lịch sử của control đó; không chuyển delta hoặc CI sang baseline 0,391 và không chạy lại chỉ vì thay baseline.

## Kết quả chất lượng

| Bản / thí nghiệm | Mức bằng chứng | Kết quả | Phạm vi diễn giải |
|---|---|---|---|
| w045_TF, nguồn 15/10 | `REPORTED` | FINAL 0.3442; Doc F2 0.3605; Chunk F2 0.3279 | Mốc lịch sử B00; không còn là control thực nghiệm ưu tiên |
| TXT/BEAR R01, nhận 19/10 | `REPORTED` | FINAL 0.3445; Doc F2 0.3612; Chunk F2 0.3279 | Δ FINAL +0.0003 từ số hiển thị so với B00; chưa quy gain cho một thành phần |
| Bài 0,4076, nhận trước/đến 20/10 | `REPORTED` | Điểm được báo 0.4076; bộ bảy metric `null` | Control lịch sử của L1/L4, đã được thay trong kế hoạch hiện hành; chưa có run ID/hashes để liên kết. Không suy các thành phần score |
| L1 trên control 0,4076, nhận 20/10 | `REPORTED` | Best Δ Doc F2 +0.0003; λ lớn giảm | Sáu λ gồm control; CI95 được báo chạm 0 hoặc âm; không nộp |
| L4 trên cùng control, nhận 20/10 | `REPORTED` | Best Δ Doc F2 +0.0004; λ lớn giảm | Cùng pool/feature và ngân sách được báo; đóng L1/L4 hiện tại |
| Baseline 0,391 theo file pipeline, chọn ngày 20/10 | `USER_SELECTED` / `REPORTED` | Điểm được báo 0.391; tên metric và bộ bảy metric `null` | Baseline hiện hành. Ảnh có 300 VI + 40 ZH trước rerank, threshold trên p̂ nhắm mean 160 doc/query; chưa liên kết counts/cache/threshold/chunk thực. Không kế thừa recipe 0,4076 |
| Local `scoring_result.zip`, run chưa liên kết | `ARTIFACT_OBSERVED` | Macro doc 0.407343155932693; chunk 0.3378781929969602 trên 593 positive-gold queries | Số trong archive, xem inputs manifest. **Chưa liên kết với bài 0,4076**; không dùng thay các metric còn thiếu hoặc B00/R01 |

Không có Δ FINAL mới, public submission mới hoặc baseline quality benchmark do lượt sửa tài liệu này thực hiện. Không diễn giải chênh lệch 0,391 và 0,4076 là regression thực nghiệm khi chưa nối đúng metric, dữ liệu và scorer. Thiếu artifact local không có nghĩa các phép thử được báo chưa từng chạy ở phía người vận hành.

## Nhãn và chẩn đoán dữ liệu

File `val.jsonl` local có 593 query, 22.091 cặp `gold`, 66.547 cặp `not_gold`. Có 205 query lệch giữa `G` và `len(gold)+gold_unseen`, tổng lệch 305, trung bình 0,5143/query. Đây là kiểm tra trường dữ liệu, chưa xác định doc ID hoặc chứng minh nguyên nhân gán nhầm âm. Chi tiết và phân biệt với ước lượng bias `±0.0002` do nguồn báo nằm trong [report L1/L4](L1_L4_20261020.md).

Nhãn BTC có thể dùng offline; không biến âm suy từ chunk thành negative chắc chắn ở mức doc hoặc coi unknown là 0. Khi threshold làm k thay đổi, ΔF2 phụ thuộc cả hits control: uncertainty ở docs giữ nguyên cũng phải xét, không chỉ added/removed. Không yêu cầu gán tay lại toàn bộ tập; xem [hợp đồng đánh giá](EVALUATOR_CONTRACT.md).

## Hướng triển khai lịch sử v3.3 — đã được thay bằng v5

Theo đính chính người dùng tại thời điểm đó, kế hoạch v3.3 dùng A0adapter →A1structured evidence →A2doc →A3chunk →A4ablation/joint. B0baseline; D1doc-only; C1chunk-only cùng budget; DC1joint. Đây là bản ghi lịch sử; workflow hiện hành theo handover v5.

Audit/threshold-only của v3.2 đã thay làm hướng chính; chúng chỉ hỗ trợ phát triển hoặc chọn operating point. Không có parser/selector mới, run hoặc quality gain được thực hiện trong lần sửa tài liệu. Số liệu lịch sử trong bảng giữ nguyên.

## Kiểm chứng kỹ thuật lịch sử

Backend **BEAR 2.0.0** có **63/63 BEAR + 10/10 legacy tests** qua trong lượt triển khai trước, không chạy lại hôm nay. [Báo cáo 19/10](next_round/V2_IMPLEMENTATION.md) lưu nghiệm thu fixtures và inventory local thiếu 18 roles. Các thiếu hụt đó mô tả checkout tại thời điểm chạy, không phủ định kết quả ngoài máy được báo sau đó.

| Bằng chứng được kế thừa | Phạm vi |
|---|---|
| Calibration 8-beta differential khớp scorer `scripts/val_calib.py` | Fixture; không chứng minh corpus/beta handover thật |
| Chunk tier/plan/whitespace filtering khớp `submission.build` | 200 docs synthetic; không tự chứng nhận recipe baseline 0,391 khi k/chunk chưa xác nhận |
| Pool → features → ranking, resume/tamper guards, partial-label guard, freeze/holdout controls | Code invariants; không phải relevance gain |
| N0/N1 đủ 1.200 câu, w045 parity 100%, trung bình 5,5 doc đổi/câu | `REPORTED` từ người chạy; ghi nhận, không bắt lặp lại như prerequisite vòng mới |

Không chạy tests, benchmark, GPU, tạo ZIP hoặc submit trong lượt cập nhật này. Code version giữ 2.0.0; thay đổi hiện tại là kế hoạch và tài liệu.
