# BEAR 2.0.0 — Nghiệm thu kỹ thuật, 19/10/2026

> Snapshot kỹ thuật lịch sử. Hướng hiện hành là [PLAN v3.3](../../PLAN.md) và [BEAR_ALGORITHM](../../BEAR_ALGORITHM.md): structured evidence + doc selector + chunk selector trên0,391. Code2.0/nghiệm thu ở dưới chưa triển khai đầy đủ thiết kế mới; không bắt chạy lại N0/N1.

Triển khai theo PLAN v2 và PLAN_v2_draft; mọi thay đổi dưới TXT, legacy chỉ đọc. Đây là backend CPU đã kiểm fixtures, **chưa phải nghiệm thu quality benchmark N0–N5 trên dữ liệu thật**. Điểm R01 người dùng báo vẫn FINAL0.3445/Doc0.3612/Chunk0.3279, không có score mới trong lượt triển khai này.

## Phần đã triển khai

| Mốc | Code/hành vi có thật | Bằng chứng và phần còn thiếu |
|---|---|---|
| N0 | `provenance.py`, explicit inventory/hashes, reviewed linkage record, baseline parity check; không đoán ZIP/run association | Đã execute inventory checkout:18roles thiếu, linkage unresolved; [report](N0_provenance_v1.md), [readiness](V2_READINESS.json). Chưa R0 parity thật. |
| N1 | `application_audit.py`, replay so candidates/details, flags/denominators cho features/eligible/applied/fallback, đổi order/top40/set, added/removed, optional score/chunk coverage | Fixtures phân biệt partial/noop/reorder/replacement/frozen non-VI; thiếu R01 manifests/pool/features để audit thực. |
| N2 | Tune L1/L4/L1_L4;12trials body/local cùng menu; selection chỉ khi mọi trial đủ labels; hash-bind manifests/predictions/evaluation artifacts | Combined study fixture chạy12trials và từ chối reuse khi prediction bị sửa; chưa qrels/snapshot thật. |
| N3 | `chunk_study.py`: native refs, corpus/ranking/allocation alignment, C1/C2, score/mapping fallback, per-doc slot invariant; `chunk_evaluation.py`: reviewed local-passage recall/paired CI | Fixtures kiểm pilot IDs không liên tiếp, actual slots/head giữ, selected chunks thay đúng, mismatch corpus/index bị chặn; thiếu corpus/passages thật. |
| N4 | `routing_diagnostics.py`: same-universe dev reports, oracle headroom, E bins, length/endpoint rules và5shuffle seeds | Pure diagnostic fixtures; **chưa matched-budget A1 orchestration/controls**, adaptive_ready=false và production guard giữ nguyên. Thiếu B/D verified/reviewed utilities để chạy thật. |
| N5 | Readiness preflight; exclusive exposure sau validation; paired doc metrics; freeze whole candidate artifacts/metric contract; chunk freeze cần records hash; release giữ selected chunks thay vì ghi đè legacy | Fixtures kiểm thiếu/invalid labels không tiêu exposure, second exposure/tamper/document-only chunk selection bị từ chối; selected-release path giữ chunks/slots. Chưa full1200×200/package/holdout thật; multi-control exposure chưa mở. |

## Đã kiểm tra

- **63/63 tests BEAR** (`python -B -m unittest discover -s TXT/tests -t . -q`), gồm15tests v2 và48tests nền.
- **10/10 tests legacy offline** (`python -B -m unittest discover -s tests -v`).
- CLI version `BEAR 2.0.0`, help lazy;7config schemas mới hợp lệ; tune dry-run đăng ký12trials.
- N4 runner smoke với synthetic dev reports qua; từ chối holdout reports, giữ adaptive_ready=false và xuất đủ5shuffle controls.
- Provenance execute + dry-runs R0/N1/C1/C2/N4 ghi đúng blocked_input; N2 dry-run chỉ xác nhận menu, chưa benchmark.
- Python3.13.1; temp/cache dưới TXT. Có ResourceWarning về connection SQLite từ fixture nền trong suite; test results vẫn OK, không có lỗi benchmark bị bỏ qua.

Không cài model/dependencies, chạy GPU, crawl, refit beta, mở holdout thật, nén full package hoặc submit. Thời gian fixtures không ngoại suy throughput/RAM/I/O corpus thật; các cost chưa đo giữ null. Tài liệu và phiên bản nguồn trước được giữ trong archive; report/log cũ là snapshot lịch sử.

## Cách chạy tiếp

Đọc [v2 runbook](../../configs/next_round/README.md). N0 runtime đã hoàn tất inventory có missing inputs, nên khi nhận artifacts phải tạo config/output version mới. Cần14R0 roles, baseline run manifest và R01 candidate_manifest/submission/scoring_output để nối provenance; tiếp đó bind N1 thật. Nhãn dev/passages và B/D là dependencies riêng của N2/N3/N4, không tự sinh để vượt blocker.

Chưa promote baseline; giữ B00/R01 riêng. N4 A1 production và N5 multi-control confirmatory là phần deferred theo đúng prerequisite, không đánh dấu complete vì có pure diagnostics. Local passage recall không thay official Chunk F2. Các thay đổi/giới hạn mới đã được nối trong improvement_log và handover.
