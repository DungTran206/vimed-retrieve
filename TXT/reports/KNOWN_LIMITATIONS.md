# Giới hạn snapshot lịch sử —20/10/2026

Hiện hành 21/10: [medical hypothesis v4](MEDICAL_HYPOTHESIS_20261021.md) đã có code chạy và 146 tests đạt tổng cộng. Chưa có kết quả chất lượng thật; inputs/endpoint và source quality phải được ghi đúng. Các hạn chế lịch sử bên dưới không là lý do từ chối hay trì hoãn việc chạy hypothesis đã được ủy quyền.

Theo [PLANv3.3](../PLAN.md) và [BEAR_ALGORITHM](../BEAR_ALGORITHM.md), đích là doc/chunk retrieval, không chỉ audit/threshold.

- Baseline0,391 là mốc người dùng chọn; ảnh có kiến trúc nhưng chưa đủ run/config/scorer, MaxP/p̂ và chunk export để tái tạo đầy đủ.
- Code2.0 có matcher/uniform features/fusion/C1C2scaffolding. Structured relation/intent/conflict mới chưa hoạt động đầy đủ; critical_mismatches có chỗ trả list rỗng. Không gọi placeholder là thuật toán hoàn tất.
- Pilot tái dùng pool baseline, chưa tìm doc ngoài pool. Nếu chỉ có VIfeatures thì ghi D1-VI và non-VI fallback; đa ngôn ngữ cần aliases/mapping đủ.
- D1 cố định k từng query để kiểm chất lượng tập doc; chỉ đổi order cùng tập không tăng DocF2. C1 giữ doc set/order/slots/token budget để kiểm selector.
- Chunk policy0,391 chưa xác nhận. Full-body duy nhất có thể không còn selector headroom dưới cùng budget; không kết luận điều này từ “Lấy full” hoặc0,4076.
- Evidence là feature hỗ trợ inference, chưa tự xác nhận relevance y khoa. Unknown khác no-match; sai identifier ở đoạn không liên quan không tự là conflict toàn doc.
- BTC val593qid có205dòng bất nhất/tổng305, không định danh doc sai; weaknot_gold có thể âm giả. ±0.0002 không là bound. K đổi còn cần hits control và sensitivity cả doc giữ nguyên.
- 593câu đã khai thác không là holdout sạch. Bootstrap không sửa label bias hoặc selection bias.
- Doc/Chunk/FINAL khác metric; local LCS thiếu tokenizer/spec không gọi officialChunkF2. Không suy ΔFINAL từ ΔDoc hoặc quy gain tăng text budget cho selector.
- Runner/exporter cũ còn fixed200/manual-qrels/allocationw045; cần adapter0,391. Không tự fit beta8/10 hoặc sửa corpus để khớp thiết kế.
- L1/L4 cũ đóng đúng scope, không chứng minh mọi evidence/chunk algorithm vô ích. Audit và threshold tuning chỉ hỗ trợ, không thay output selected_docs/selected_chunks.
- Lượt này chỉ docs/spec; tests63+10 là nghiệm thu lịch sử, chưa có implementation/gain mới cho v3.3.

[Handover](../TXT_handover.md), [evaluator](EVALUATOR_CONTRACT.md), [trạng thái code](IMPLEMENTATION_STATUS.md), [log](../improvement_log.md).
