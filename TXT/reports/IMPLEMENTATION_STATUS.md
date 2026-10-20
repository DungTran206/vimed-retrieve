# IMPLEMENTATION STATUS — 19/10/2026

> **Báo cáo kỹ thuật lịch sử.** Cập nhật hướng đi 20/10: [PLAN v3.3](../PLAN.md), [baseline 0.391](BASELINE_0391_20261020.md), [L1/L4 lịch sử trên 0.4076](L1_L4_20261020.md). N0/N1 và trials remote đã được người dùng báo; bảng dưới chỉ ghi code/fixtures và inputs checkout khi triển khai. Không dùng cột “thiếu reviewed labels” để cấm nhãn BTC hoặc bắt chạy lại N0/N1. Kiến trúc từ ảnh đã có [Markdown](../PIPELINE_0391.md) và [spec tham chiếu không thực thi](../specs/pipeline_0391.json), chưa liên kết recipe runtime. Lượt docs/spec không thay code 2.0.0, manifests hoặc tests.

**Phạm vi hiện tại:** [BEAR_ALGORITHM](../BEAR_ALGORITHM.md) yêu cầu structured evidence + doc selector + chunk selector. Code2.0 chỉ có nền matcher/features/fusion/chunk scaffolding; chưa triển khai đầy đủ parser/structured conflict/adapter0,391/joint mới. Threshold-only không còn là mục tiêu chính. Các bảng dưới là lịch sử kỹ thuật, không bị sửa thành completed mới.

## Cập nhật code2.0.0 — N0–N5

Chi tiết tại [V2_IMPLEMENTATION.md](next_round/V2_IMPLEMENTATION.md), lệnh tại [v2 runbook](../configs/next_round/README.md). Đã qua63/63tests BEAR và10/10legacy; chưa benchmark relevance thật.

| Task mới | Trạng thái | Evidence / còn thiếu |
|---|---|---|
| N0 | inventory_executed / blocked_input | Provenance CLI ghi18roles thiếu; chưa nối R01 hoặc parity R0 thật |
| N1 | implemented / fixture_verified | Application replay/flags/accounting; R01 artifacts thật chưa có |
| N2 | implemented / fixture_verified | Combined L1_L4 chạy12trials fixture; chưa reviewed dev labels để chọn best |
| N3 | implemented / fixture_verified | C1/C2 native-offset study, local passage evaluator, freeze/export integration; chưa corpus/passages thật |
| N4 | diagnostics_implemented / production_deferred | Oracle/E bins/length/5shuffles; A1 matched-budget orchestration chưa mở, thiếu B/D và headroom evidence |
| N5 | implemented / fixture_verified / full_run_blocked | Preflight, exposure-after-validation, paired doc stats, chunk artifacts freeze/release đã kiểm; multi-control exposure/full1200/package chưa chạy |

## Snapshot T01–T16 trước code2.0

Đối chiếu `TXT/PLAN.md`. Không dùng `done` để thay cho dữ liệu hoặc kết quả thực nghiệm chưa có.
Vòng triển khai này thực hiện nhánh độc lập với dữ liệu theo §1.4, §1.6 và §13.3.
`fixture_verified` chỉ là kiểm tra kỹ thuật trên dữ liệu tổng hợp nhỏ, không phải benchmark thật.

| Task | Trạng thái | Code/artifacts và bằng chứng | Còn thiếu / bước tiếp |
|---|---|---|---|
| T01 | fixture_verified | config.py, io.py, artifacts.py, CLI lazy; reject unknown/type/nonfinite, output guard, atomic partial/completed, code/input hashes | Các schema mới phải được bổ sung khi mở study mới |
| T02 | fixture_verified / blocked_input | audit.py; inputs.json, baseline.json, DATA_READINESS; verify macro archive, hash-mismatch regression test | 22/22 input roles thiếu theo readiness; schema corpus thật chưa kiểm |
| T03 | partial / fixture_verified | adapters.py: duplicate IDs/qids/scores, source-order, SQLite id/doc_id, <=900 batches, native refs | External dense offsets adapter chưa làm; tags/expanded translation provenance chưa đủ toàn schema §6 |
| T04 | implemented / blocked_input | reproduce.py + baseline.py; dry-run báo 14 roles thiếu; differential 8-beta và chunk tiers vs exporter gốc đã qua | Full R0, intermediate parity/fingerprints 1200×200 chưa chạy; qtext overwrite chưa có differential riêng |
| T05 | fixture_verified / blocked_input | pools.py, features.create_pools; baseline-first, cap, VI lane, non-VI slots, support outside pool | Corpus/ranking/membership thật; B/D source manifests có hash/provenance thật |
| T06 | fixture_verified | matching.py; protected spans, NFC, deterministic concepts/views hash, alias chỉ từ record có review | Relation/intent chưa được hiểu; critical provenance do người review cung cấp |
| T07 | partial / fixture_verified | evidence.py, features.py; title/body/all-native-chunk, E/gamma, shards/checksums, L0 bins; selected smoke/pilot IDs | Real smoke/pilot; peak RAM/I/O đo thực; global IDF; cache partial hiện recompute shard thay vì bỏ qua shard đã hoàn thành |
| T08 | fixture_verified / blocked_input | evaluation.py, evaluate_runner.py, paired.py; macro, complete-topK, differences guards, group bootstrap; macro archive matched | Qrels reviewed, official tokenizer/spec và full coverage manifest |
| T09-A | fixture_verified / blocked_input | experiments.split_queries/sample: SRS100, group dev/holdout, contamination ledger, seed42 smoke2; protocol template | Query artifact thật và cost ceiling; stress annotations riêng chưa có |
| T09-B | implemented / blocked_input | blinded annotation-export; grade=null, không có rank/score/source; holdout chỉ frozen candidate/controls | Annotator/adjudicator thật, supporting refs và coverage completion |
| T10-A | fixture_verified | baseline/λ0, fixed evidence, fixed residual, deterministic candidates và explanations; pipeline fixture qua | Real predictions trên preregistered menu |
| T10-B | implemented / blocked_input | tuning.py: L1 6 trials, F0 18; dev only; separate evaluation; toàn bộ trials ghi ledger; thiếu labels không chọn best | Chạy dev đầy đủ labels; L2 IDF chưa mở, L3/L4 là pure feature variants chưa có study xác nhận |
| T11 | partial / dependency_deferred | Pure sigmoid/endpoints/fallback; freeze hashes + one-exposure holdout guard được test | O0/headroom/bins, query-only/shuffle controls, A1 tuning chưa mở; CLI chặn adaptive nonzero cho tới prerequisite |
| T12 | partial / dependency_deferred | chunk_experiments.py: C1/C2 pure selectors, complete-score fallback, giữ slot/offset | Real mapping/coverage và C1/C2 study runner; C3 budget study chưa có |
| T13 | dependency_deferred | Không tạo sparse encoder giả hoặc tự cài model; không đăng ký CLI sparse khi chưa implement | PLAN yêu cầu checkpoint/revision/API audit, benchmark/cost ceiling và S1 prerequisite trước S2 |
| T14 | partial / blocked_input | integrity.py/release.py: 1200×200, integer IDs, membership/vinmec exception, refs/body/slice/hash/order, LZMA/testzip/readback/size guard; legacy audit_chunk readonly wrapper | Dev interactions, R0 thật, final package/ZIP chưa chạy; chưa promote/upload |
| T15 | dependency_deferred | Alias/discovery/local gate/SPLADE giữ backlog theo trigger PLAN | Không tự mở nhánh khi chưa có bằng chứng |
| T16 | documentation_updated | RUNBOOK, RESULTS, DECISIONS, KNOWN_LIMITATIONS, task ledger và code hash inventory | Real run/cost/CI/rollback artifacts bổ sung sau input handover |

## Kiểm tra đã chạy

```powershell
python -B -m unittest discover -s TXT/tests -t . -v
python -B -m unittest discover -s tests -v
python -B -m TXT.bear.cli --help
python -B -m TXT.bear.cli audit --config TXT/configs/readiness.json
python -B -m TXT.bear.cli reproduce --config TXT/configs/reproduce.json --dry-run
python -B -m TXT.bear.cli pool --config TXT/configs/pool_v1.json --dry-run
python -B -m TXT.bear.cli features --config TXT/configs/l0_pilot.json --dry-run
python -B -m TXT.bear.cli tune --protocol TXT/configs/tune_l1.json --menu TXT/configs/menus_v1.json --dry-run
```

48/48 BEAR tests; 10/10 legacy offline tests qua tại lần kiểm tra ghi trong RESULTS.
Audit/R0/pool/features dry-run trả blocked_input đúng dự kiến. Tune dry-run xác nhận menu6, chưa chạy ranking/metric.
Environment: Windows, Python3.13.1, NumPy2.3.3. Không cài thêm dependency, chạy GPU, crawl, refit beta hoặc nộp leaderboard.

## Write boundary và dirty state

Tất cả code/config/test/report mới hoặc sửa nằm dưới TXT. Runtime fixtures/cache được ignore bằng TXT/.gitignore.
Giữ nguyên các staged renames root→doc và untracked val_calib.py đã có của người dùng; không stage/commit.
`TXT/manifests/code_inventory.json` chứa SHA256 của code/config/test/doc triển khai; không hash nó vào chính nó.

## Bước tiếp theo của snapshot19/10 — đã được PLAN v3.3 thay thế

Nhận đúng handover dưới TXT/inputs/handover, update paths/hash từ file thật → audit → R0 execute (chưa ZIP) → đối chiếu fingerprints → frozen pool → sample/smoke2 → L0 pilot. Sau đó mới annotation/dev/fixed selection. T11–T15 chỉ mở theo trigger; không đánh dấu toàn PLAN hoàn thành khi các điều kiện này chưa có.

**Bước tiếp hiện hành:** A0adapter control0,391 →A1structured evidence →A2selected_docs →A3selected_chunks →A4B0/D1/C1/DC1. D1giữ k thực từng query, C1giữ doc set/order/slots/budget. Audit/threshold là công cụ hỗ trợ. Chưa có code hoặc metric mới từ lượt tài liệu.

## Kiểm tra chuẩn bị20/10 — công cụ phụ trợ mới

Đã thêm [config inventory](../configs/bear_doc_chunk/preflight_0391.template.json), chạy dry-run ghi5roles thiếu; [benchmark utility](../tools/benchmark_cpu.py) đã chạy, lưu [JSON CPU](cpu_kernel_benchmark_20261020.json). Đây là kernel exact cũ, không là implementation structured selector hoặc quality benchmark. Package vẫn2.0.0. [Readiness](EXPERIMENT_READINESS_20261020.md) tách rõ thiếu code/inputs và điều kiện CPU.
