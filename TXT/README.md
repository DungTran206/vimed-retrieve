# BEAR v5 — BM25 + dense tổng quát + SapBERT-XLMR

Cập nhật 22/10/2026. Nhánh thử nghiệm hiện hành giữ fusion BM25/dense và medical gate từ khớp lexical có nguồn. Dense mới kết hợp dense tổng quát với SapBERT-XLMR để bổ sung tương đồng giữa concept y sinh và term xuất hiện thật trong tài liệu.

```text
KB có nguồn → prepare(query LLM)
corpus + raw BM25/dense → cache → document-terms(document LLM)
                                     ↓
                              sapbert-cache
                                     ↓
                    fit → tune → run → [select] → evaluate
```

`select` là LLM chọn lại shortlist tùy chọn sau fusion. Không chạy LLM hoặc encoder trong vòng tune khi feature cache còn hợp lệ.

| Tài liệu | Dùng để |
|---|---|
| [Handover](TXT_handover.md) | Tiếp nhận đầy đủ: inputs, lệnh, cache, tham số, tài nguyên |
| [Proposal](TXT_Proposal.md) | Mục đích từng thành phần và lựa chọn kết hợp dense/SapBERT |
| [Algorithm](BEAR_ALGORITHM.md) | Công thức và semantics chính xác |
| [Study](BEAR_REPLACEMENT_STUDY.md) | Đối chứng, validation, lợi ích/chi phí |
| [PLAN](PLAN.md) | Thứ tự công việc hiện hành |
| [Templates](configs/medical_hypothesis/) | Bind input thật trước khi chạy |
| [Baseline 0,391](PIPELINE_0391.md) | Recipe control và provenance chưa xác minh |
| [Results](reports/RESULTS.md), [log](improvement_log.md) | Kết quả và lịch sử thực tế |
| [Cleanup](reports/CLEANUP_20261022.md) | Phạm vi dọn bản cũ và tra lại trong Git |

Từ repository root:

```powershell
python -B -m TXT.bear.medical_cli --help
python -B -m TXT.bear.medical_cli demo --output-dir TXT/runtime/medical_v5_demo
```

Stage nhận `--config`; mặc định inspect, thêm `--execute` để chạy. Templates còn paths mẫu không phải input đã hiện diện. Đọc tài liệu/demo không tự tải checkpoint hoặc gọi endpoint.

V5 đã triển khai và qua tests kỹ thuật/synthetic; [report v5](reports/SAPBERT_V5_20261022.md) ghi kiểm chứng và phần chưa chạy. Tham số là **ước lượng khởi tạo để thử**, chưa tối ưu và chưa có quality gain được chứng minh trên 593 query thật. Fit chỉ học sigmoid BM25; normalizer SapBERT ban đầu là affine ước lượng.

BR tìm corpus độc lập; BF chỉ chọn union đã cache. SapBERT v5 chưa thêm doc ngoài union. Native chunk/downstream control cần recipe đúng để đo Doc/Chunk/FINAL. Legacy code/configs còn giữ để chạy control và tests, không phải kế hoạch song song với v5.
