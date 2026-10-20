# N0 provenance — kiểm tra checkout, 19/10/2026

> Inventory checkout lịch sử; không là prerequisite chạy lại. N0/N1 đã được nguồn báo1200câu/parity100%/5.5doc đổi. Hướng hiện hành [PLAN v3.3](../../PLAN.md), [BEAR_ALGORITHM](../../BEAR_ALGORITHM.md) xây doc/chunk selector trên0,391; giữ nguyên status/đếm lịch sử bên dưới.

Đã execute inventory bằng BEAR2.0; chưa reproduce baseline hoặc nối R01 với artifact.

Điểm TXT/BEAR do người dùng báo vẫn REPORTED: FINAL0.3445, Doc F2 0.3612, Chunk F2 0.3279.

Status blocked_input; linkage unresolved; observed_metrics=null; quality_decision=inconclusive.

18roles chưa có trong checkout:

- `baseline_manifest`
- `beta`
- `candidate_manifest`
- `chunk_dense`
- `chunk_scores`
- `corpus`
- `membership`
- `qwen_doc_scores`
- `scoring_output`
- `submission`
- `vi_alt`
- `vi_base`
- `zh_bge_patch`
- `zh_bge_vi`
- `zh_bge_zh`
- `zh_q8_patch`
- `zh_q8_vi`
- `zh_q8_zh`

Runtime: `TXT/runtime/next_round/N0_v1/provenance.json` và manifest có hashes thực. Chi tiết [V2_READINESS.json](V2_READINESS.json). Không gán ba ZIP root cho R01. Nhận dữ liệu rồi dùng config/output version mới; không overwrite manifest completed của inventory này.
