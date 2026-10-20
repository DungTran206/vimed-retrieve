# BEAR — Retrieval doc và chunk

**BEAR phải tạo doc set và chunks bằng chứng.** Baseline0,391 cung cấp ứng viên/score và làm control; audit và threshold tuning là công cụ hỗ trợ.

| Đọc | Vai trò |
|---|---|
| **[BEAR_ALGORITHM.md](BEAR_ALGORITHM.md)** | Evidence Engine →Doc Selector →Chunk Selector và output inference |
| [PIPELINE_0391.md](PIPELINE_0391.md) | Baseline đọc từ hai ảnh |
| [TXT_Proposal.md](TXT_Proposal.md) | H_doc/H_chunk/H_joint |
| [PLAN v3.3](PLAN.md) | A0adapter →A1evidence →A2doc →A3chunk →A4joint/evaluation |
| [TXT_handover.md](TXT_handover.md), [RUNBOOK](reports/RUNBOOK.md) | Code đã có/gap và bước tiếp |
| [JSON tham chiếu](specs/pipeline_0391.json) | Facts baseline và thiết kế chưa thực thi |
| [Log](improvement_log.md), [RESULTS](reports/RESULTS.md) | Lịch sử và metric |
| **[Readiness và CPU/GPU](reports/EXPERIMENT_READINESS_20261020.md)** | Code/inputs đã kiểm, phép đo CPU và checklist máy GPU |

D1chọn lại doc, C1chọn lại chunk cùng budget, DC1ghép hai selector; không chỉ đổi order hoặc tăng text budget. Tái dùng pool baseline trước khi nghĩ tới retrieval toàn kho mới.

L1/L4 cũ vẫn đóng đúng scope; kết quả đó chưa bác bỏ mọi evidence/chunk algorithm. BTC labels dùng offline với semantics đúng, không buộc gán tay593câu.

**Trạng thái20/10:** software2.0.0 có matcher/features/fusion/chunk scaffolding; structured relation/conflict và adapter0,391 chưa triển khai đầy đủ. v3.3 là đặc tả, chưa có gain mới. [v3.2 threshold-only](archive/PLAN_v3_2_before_doc_chunk_restore_20261020.md) đã được thay theo đính chính của người dùng.

Đã chạy [preflight A0](configs/bear_doc_chunk/README.md):5/6roles input còn thiếu tại checkout, val.jsonl hiện diện. CPU có thể chạy nhánh cache+feature nhẹ sau khi có inputs/code; [tool benchmark](tools/benchmark_cpu.py) chỉ đo kernel exact cũ, không chứng minh structured BEARv3.3 đã chạy được.

Người dùng có thể dùng máy GPU khác, thông số chưa biết. [Checklist bàn giao](reports/EXPERIMENT_READINESS_20261020.md#7-máy-gpu-đã-có-còn-thiếu-gì-và-ai-chuẩn-bị) giải thích dữ liệu cần lấy, code agent cần bổ sung và phần model/môi trường chỉ cần khi chạy inference mới. Chưa có phép chạy hoặc ETA GPU.
