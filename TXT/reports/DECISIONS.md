# Quyết định triển khai — 19/10/2026

1. Giữ mọi thay đổi và output dưới TXT. Không sửa legacy code, dirty renames hoặc dữ liệu nguồn.
2. Theo PLAN §1.4/§1.6/§13.3: triển khai CPU/interfaces/fixtures trước; không dựng benchmark hoặc nhãn thật giả khi thiếu artifacts.
3. Giữ baseline w045 REPORTED0.3442 và fingerprints handover; archive0.3726 là ARTIFACT_OBSERVED, runtime_observed_unlinked.
4. Triển khai P200/PLARGE cap400, reference baseline-first, frozen non-VI slots, route support B trước fusion. Không tự suy c_blend là lexical/dense thuần.
5. Exact uniform là V1. Null là unavailable, zero là observed no-match. E yêu cầu tất cả actual support valid; fallback toàn query.
6. CLI chỉ công bố command thực sự có code; job mặc định dry-run. Không công bố sparse/upload. Adaptive pure logic có fixture nhưng run nonzero bị chặn tới T11.
7. Completed runs hash config/code/inputs; file thay đổi thì reject reuse. Partial restart ghi lại shard atomically, không append. Không tự download/cache model bên ngoài TXT.
8. Tuning L1/F0 dev-only, menu khóa. Nếu một trial thiếu primary labels thì không chọn best. Holdout có frozen candidate/control hashes và exposure marker.
9. Nhãn annotation chỉ template; không dùng coding agent làm human judge. Grade2 primary, grade1 topical chỉ secondary.
10. ZIP chỉ technical package, không tự promote hoặc upload. Rollback vẫn là exact R0 sau khi fingerprints được chứng minh.
