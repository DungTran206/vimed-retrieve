# Giới hạn — BEAR v5 và các snapshots lịch sử

## Hiện hành 22/10/2026

V5 đã có SapBERT cache/fusion và optional LLM selector, kiểm chứng kỹ thuật/synthetic cuối sau cleanup: full TXT suite 173/173 tests và 10/10 legacy tests qua. [Report v5](SAPBERT_V5_20261022.md) và [handover](../TXT_handover.md) ghi phạm vi thực tế.

Chưa có checkpoint/endpoint inference thật hoặc quality gain trên 593 query. SapBERT cosine không tự chứng minh synonym/relation/relevance toàn câu; generic dense vẫn giữ trong biến thể đầu. SapBERT không mở rộng union, selector không lấy doc ngoài shortlist. Full-matrix cache giảm chi phí sweep nhưng lần trích document terms/encode đầu vẫn có thể đắt.

Affine low/high, λ và budgets là ước lượng. Fit học BM25 sigmoid, chưa học Sap probability calibrator. Native judgments không đầy đủ; unknown không negative và retrospective holdout không pristine. Nội dung bị prefix truncate không chứng minh full-document coverage.

Các hạn chế giúp thiết kế đối chứng; không phải lý do từ chối chạy thí nghiệm đã được ủy quyền. Thiếu artifact nào thì báo đúng phần đó, tiếp tục stage độc lập có input.

## Snapshot 21/10/2026 — v4

[Medical hypothesis v4](MEDICAL_HYPOTHESIS_20261021.md) đã ghi 146 tests tổng cộng tại thời điểm đó, chưa quality experiment thật. Không dùng số tests lịch sử thay cho tình trạng v5.

## Snapshot 20/10/2026 — kế hoạch v3.3

Đoạn dưới ghi phạm vi kế hoạch v3.3 lúc đó, đã được v5 thay thế; cách tra snapshot nguồn ở [cleanup](CLEANUP_20261022.md).

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
