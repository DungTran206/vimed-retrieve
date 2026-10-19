# Kết quả quan sát

| Loại bằng chứng | Kết quả | Phạm vi |
|---|---|---|
| CODE_VERIFIED | 48/48 BEAR unit/integration tests qua; 10/10 legacy offline tests qua | Synthetic fixtures, không phải quality benchmark |
| CODE_VERIFIED | Calibration 8-beta differential khớp scorer scripts/val_calib.py | Fixture; chưa có beta/corpus handover thật |
| CODE_VERIFIED | Chunk tier/plan/whitespace filtering khớp submission.build | 200 docs synthetic, có score và plan edge cases |
| CODE_VERIFIED | Pool→features→ranking, non-VI slot, resume hash/tamper, partial-label guard, frozen holdout một lần | Fixture |
| ARTIFACT_OBSERVED | Macro document0.407343155932693, chunk0.3378781929969602 trên593 positive-gold queries | Archive scoring_result.zip, runtime_observed_unlinked; xem inputs manifest |
| REPORTED | Baseline w045: Doc0.3605 / Chunk0.3279 / FINAL0.3442 | Handover, chưa reproduce |
| UNRESOLVED | R0 thật, L0 thật, fixed/adaptive/chunk/sparse gain, CI/cost/rollback package | Thiếu artifacts/labels và prerequisites |

Không có best fixed/adaptive được chọn, không có kết luận keep/reject chất lượng, không promote.
Không tạo ZIP hoặc chạy GPU. Thời gian unit tests chỉ đo fixture, không ngoại suy throughput corpus.

Lệnh tái kiểm tra trong RUNBOOK. Code/test/config SHA256 trong TXT/manifests/code_inventory.json.
