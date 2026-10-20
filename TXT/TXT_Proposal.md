# TXT Proposal v3.3 — BEAR tạo doc và chunk

Cập nhật20/10/2026 theo đính chính của người dùng. Baseline0,391 giữ làm control; **BEAR là thuật toán retrieval doc/chunk**. Việc v3.2 thu hẹp BEAR thành audit và threshold-only không thể hiện đủ mục tiêu ban đầu, nên được thay bằng thiết kế dưới đây.

Đặc tả inference: **[BEAR_ALGORITHM.md](BEAR_ALGORITHM.md)**. Kế hoạch xây/test: [PLAN v3.3](PLAN.md). Baseline đọc từ ảnh: [PIPELINE_0391.md](PIPELINE_0391.md). Software vẫn2.0.0; thuật toán mới chưa triển khai đầy đủ hoặc được chứng minh gain.

## 1. BEAR để làm gì?

Với query và corpus, BEAR phải trả:
1. **Doc được chọn/xếp hạng:** tài liệu nào nên đưa vào kết quả.
2. **Chunk được chọn trong các doc đó:** đoạn nào là bằng chứng phù hợp với yêu cầu query.

Baseline BM25/dense/Qwen/MaxP cung cấp ứng viên và tín hiệu nền. BEAR dùng bằng chứng y sinh có cấu trúc để thay đổi lựa chọn doc và chunk. Explanations/audit giúp kiểm tra thuật toán; chúng không thay hai output trên.

Pilot tái dùng ứng viên baseline, không cần xây lại retriever toàn kho. Đây là retrieval hai tầng với evidence-based reranking/selection, chưa tuyên bố phát hiện doc ngoài pool.

## 2. Khác baseline ở đâu?

| Thành phần | Baseline0,391 | BEAR đề xuất |
|---|---|---|
| Sinh ứng viên | BM25F/dense/fusion; khoảng300VI+40ZH trước rerank | Tái dùng làm giai đoạn đầu của pilot |
| Chấm phù hợp | Qwen/MaxP/p̂ | Kết hợp điểm nền với support/conflict có span, identity/role/điều kiện |
| Chọn doc | Threshold trên p̂; mean khoảng160 theo ảnh | BEAR Doc Selector; pilot giữ k thực từng query để kiểm chất lượng thay doc |
| Chọn chunk nộp | Ảnh chưa mô tả | BEAR Chunk Selector chọn đoạn nguyên văn, cùng slots/token budget đối chứng |
| Kiểm chứng | Score baseline do người dùng báo | Ablation doc-only, chunk-only và joint; chưa có số mới |

Không mặc định dense chunking hoặc MaxP đã giải quyết tối ưu bài toán **chọn chunk được xuất**: score đoạn, aggregation doc và exporter là những bước cần phân biệt. Cũng không mặc định chúng chưa đủ tốt; C1 phải đo trực tiếp.

## 3. Ý tưởng thuật toán

Biểu diễn query thành entity/identifier + quan hệ/intent + điều kiện/đối tượng, mỗi phần có span/mapping và mức sẵn sàng. So sánh ở từng ngữ cảnh chunk, thay vì chỉ đếm thực thể rải trong body.

Feature support ghi đoạn nào hỗ trợ cùng thực thể và yêu cầu; feature conflict ghi khác biệt rõ trong ngữ cảnh đang so. Thiếu từ khóa không tự là xung đột. Một doc có nhắc biến thể khác ở một đoạn không tự bị phạt nếu đoạn khác trả lời đúng query.

Điểm đề xuất:
`doc_score = baseline_component + α × structured_evidence`;
`chunk_score = baseline_chunk_component + γ × structured_evidence`.
Support/conflict, aggregation, normalization và fallback được đặc tả trong [BEAR_ALGORITHM](BEAR_ALGORITHM.md), chưa có hệ số/parser giả định đã hoạt động.

**L1/L4 cũ vẫn đóng:** uniform body/local coverage chưa tăng rõ trên0,4076. Thiết kế mới chỉ đáng thử nếu feature có cấu trúc thực sự khác coverage cũ; không đổi tên local_max rồi chạy lại grid.

## 4. Hai giả thuyết và một phép ghép

- **H_doc:** evidence bổ sung ngoài baseline giúp thay vào doc đúng hơn trong cùng pool và k từng query.
- **H_chunk:** cùng doc set/order/slots, evidence chọn được chunk tốt hơn selector baseline.
- **H_joint:** hai selector có thể ghép thành output tốt hơn; phải kiểm riêng tương tác, không cộng các delta như thể độc lập.

| Run | Chọn doc | Chọn chunk |
|---|---|---|
| B0 | Baseline | Baseline |
| D1 | BEAR | Baseline policy |
| C1 | Baseline set/order | BEAR |
| DC1 | BEAR | BEAR |

Một pilot gồm tối đa3candidate mới và1control, không mở cả weight grid. Doc/chunk có thể làm độc lập; không buộc adaptive routing phải có ích trước.

Nếu chỉ có evidence VI đáng tin, D1-VI giữ non-VI và VI count baseline để cô lập tín hiệu. Đây là thiết kế đối chứng, không giả định output baseline luôn giữ40ZH. Multilingual selection cần aliases/mapping tương ứng.

Nếu chunk baseline là full-body duy nhất và không còn lựa chọn dưới budget tương đương thì ghi không có headroom cho C1. Ảnh0,391 chưa xác nhận policy này; không lấy cấu hình0,4076 làm kết luận.

## 5. Audit và threshold phục vụ thuật toán thế nào?

Audit giúp chọn/kiểm feature, phát hiện extractor sai và giải thích fallback. Nó là công cụ phát triển BEAR, không phải sản phẩm cuối thay retrieval.

Threshold/count tuning giúp chọn operating point sau khi đã có score/selector BEAR. Khi score đổi thang, không tái dùng τ₀ máy móc. Threshold-only có thể là control phụ, nhưng không dùng nó làm tiêu chí hoàn thành BEAR.

Routing, sparse, pool expansion và model mới giữ có điều kiện. Trước mắt tái dùng cache/corpus, tập trung một feature có cấu trúc và hai output.

## 6. Đánh giá và điều chưa biết

BTC val được dùng offline; không bắt gán tay toàn593câu. not_gold suy từ chunk failure có thể âm giả; unknown không tự thành negative. Cờ hoặc nhận xét AI không là gold.

D1 cố định k thực từng query; cần relevance đáng tin trên changed docs để tính delta. Nếu k thay đổi, còn cần hits control/sensitivity cả docs giữ nguyên. C1 giữ doc set/order/slots và text budget; scorer chunk thiếu tokenizer/spec thì local LCS chỉ là diagnostic. DC1 cần Doc/Chunk/FINAL thực, không suy FINAL từ ΔDoc.

Giữ lịch sử L1/L4: best+0.0003/+0.0004 DocF2 trên0,4076, CI95 chạm0/âm theo nguồn báo; [report](reports/L1_L4_20261020.md). N0/N1 w045 đã có kết quả được báo, không chạy lại như prerequisite.

Baseline0,391 còn thiếu run/config/full metrics, native chunk policy và công thức p̂/MaxP đã liên kết. Code2.0 có matcher/uniform features/C1C2 scaffolding nhưng thiếu structured relation/conflict và adapter mới; không gọi plan là thuật toán đã chạy.

## 7. Thay đổi đã sửa lại

v3.3 khôi phục trọng tâm **xây Doc Selector + Chunk Selector**, đưa audit về hỗ trợ và threshold về operating-point study. [PLAN](PLAN.md) dùng A0baseline adapter →A1evidence →A2doc →A3chunk →A4joint/evaluation.

Chưa có gain mới hoặc implementation mới trong lần sửa tài liệu. [Log D06](improvement_log.md) giữ đính chính; [proposal3.2](archive/TXT_Proposal_v3_2_before_doc_chunk_restore_20261020.md) được lưu nguyên lịch sử.
