# N0 provenance — kiểm tra checkout, 19/10/2026

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
