# Quyết định hiện hành — BEAR Doc & Chunk Retrieval

Cập nhật20/10/2026 theo đính chính của người dùng; [PLAN v3.3](../PLAN.md), [thuật toán](../BEAR_ALGORITHM.md).

| Quyết định | Ý nghĩa |
|---|---|
| BEAR tạo doc/chunk inference | Phải có selected_docs và selected_chunks; flags/audit/threshold study chưa đủ |
| Baseline0,391 là control và nguồn ứng viên | Tái dùng cache trước, chưa tuyên bố tìm doc ngoài pool |
| Evidence có cấu trúc | Identity/role/điều kiện và support/conflict cục bộ, khác uniform coverage |
| D1chọn lại doc | Pilot giữ k thực từng query; báo tập doc thay đổi thật |
| C1chọn lại chunk | Giữ doc set/order/slots/budget; native refs phải nối export |
| B0/D1/C1/DC1 | Tối đa3candidate mới và1control trong pilot, không mở weight grid |
| Audit/threshold là hỗ trợ | Hướng threshold-only v3.2 đã được thay |
| L1/L4 vẫn đóng đúng scope | Kết quả0,4076 không bác bỏ mọi evidence/chunk algorithm |
| BTC labels được dùng | Unknown/weak negatives không tự âm; không buộc manual593câu |
| Giữ baseline nếu chưa chứng minh gain | Chấm riêng doc/chunk/joint, CI/sensitivity và integrity phù hợp |
| Code vẫn2.0.0 | Structured relation/conflict và adapter0,391 chưa triển khai đầy đủ trong lượt này |

[LogD06](../improvement_log.md), [PLAN3.2](../archive/PLAN_v3_2_before_doc_chunk_restore_20261020.md), [proposal3.2](../archive/TXT_Proposal_v3_2_before_doc_chunk_restore_20261020.md) giữ lịch sử. Contract/native offsets/R0 cũ vẫn áp dụng cho code tương ứng; không tự áp allocationw045 lên0,391.
