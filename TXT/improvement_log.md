# Nhật ký cải tiến TXT/BEAR

Ngày mở sổ: **19/10/2026**. Đọc cùng [TXT_Proposal.md](TXT_Proposal.md) và [TXT_handover.md](TXT_handover.md). Sổ này theo dõi kết quả từng lượt, mức bằng chứng, quyết định và kế hoạch tiếp theo; không thay manifest hoặc báo cáo của từng run.

## 1. Quy tắc ghi sổ

- **Chỉ nối thêm lịch sử.** Khi sửa một kết luận hoặc bổ sung provenance, thêm mục mới có `corrects_entry`/`supplements_entry`; giữ nguyên số đã báo và lý do đính chính. Kế hoạch chưa chạy phải ghi `PROPOSED`, không ghi như kết quả.
- `reported_date` là ngày nhận/bản nguồn báo kết quả; `execution_date` là ngày job chạy; `scored_date` là ngày evaluator chấm. Không suy hai ngày sau từ ngày báo. Lưu timezone nếu có timestamp.
- `null` nghĩa là chưa biết hoặc chưa có bằng chứng; không thay bằng 0. Phân biệt `not_applicable` với thiếu dữ liệu. Giữ số đầy đủ do nguồn cung cấp; delta từ số hiển thị phải ghi rõ độ chính xác đó.
- Mỗi lượt gắn một thay đổi chính, parent/control, phạm vi P200/PLARGE/chunk-only, query universe, evaluator và ngân sách. Nếu ghép nhiều thay đổi, ghi là integrated run và không quy toàn bộ gain cho một giả thuyết.
- Ghi config/menu đã freeze và SHA-256 của config, menu, input, corpus/query/pool/split, code và output. Tên file giống nhau không chứng minh cùng snapshot. Legacy fingerprint chỉ dùng đối chiếu đúng phạm vi hash của nó.
- Lưu cả số query có output, có đủ feature, thực sự được can thiệp, fallback theo nguyên nhân và số query/doc/chunk đổi so với control. Đủ 1.200 dòng output chưa chứng minh BEAR áp dụng trên cả 1.200 query.
- Nhãn/evaluation cần nguồn và coverage rõ. Điểm tổng người dùng báo không phải qrels. Không biến item chưa judged thành âm tính hoặc dùng feedback để dựng nhãn giả cho inference/gate.
- Chọn cấu hình trên dev; freeze một candidate và các controls trước một lần xác nhận holdout. Không chọn lại nhánh hoặc threshold sau khi xem holdout. Ghi mọi lần xem và mọi trial thua.
- `keep`, `reject`, `inconclusive` là quyết định về chất lượng trong phạm vi đã đo; promote baseline là quyết định riêng, cần bằng chứng và khả năng rollback.

| Mức bằng chứng | Cách hiểu trong sổ |
|---|---|
| `REPORTED` | Người dùng hoặc tài liệu báo kết quả; chưa tự xác minh toàn bộ artifact/run. |
| `ARTIFACT_OBSERVED` | Đã đọc artifact xác định; chỉ kết luận trong phạm vi provenance/semantics đã xác minh. |
| `CODE_VERIFIED` | Đã đối chiếu code hoặc có kiểm thử kỹ thuật; không đồng nghĩa retrieval gain. Khi kế thừa từ báo cáo cũ phải ghi rõ, không nói vừa chạy lại. |
| `PROPOSED` | Kế hoạch chưa chạy hoặc chưa freeze. |
| `UNRESOLVED` | Còn thiếu dữ liệu hoặc liên kết cần thiết để kết luận. |

## 2. Sổ kết quả chất lượng

### B00 — Baseline w045_TF, nguồn ngày 15/10/2026

| Trường | Giá trị |
|---|---|
| `entry_id` / `parent_control` | `B00` / `null` |
| `recorded_date` / `reported_date` | `2026-10-19` / `2026-10-15` |
| `execution_date` / `scored_date` | `null` / `null`; tài liệu xác định snapshot leaderboard 15/10, không cung cấp timestamp job/chấm riêng |
| Mức bằng chứng / nguồn | `REPORTED`; [doc/HANDOVER.md](../doc/HANDOVER.md), P/R từ [doc/PROGRESS.md](../doc/PROGRESS.md), mục kết quả `w045_zh38w_e120` và `w045_TF` ngày 15/10 |
| Run / evaluator | `w045_TF` / leaderboard được tài liệu báo; evaluator version và scoring split hash `null` |
| Phạm vi thay đổi | Giữ tập doc `w045_zh38w_e120`; đổi allocation chunk bằng p(gold) đã kế thừa |
| Query universe / số doc | ID 1–1200, 200 doc/query (`REPORTED`); execution manifest/observed counts `null` |
| Recipe / policy | W ZH `0.45`; top-40 tối đa 2 chunk/doc, hạng 41–120 tối đa 1; bỏ chunk top-120 khi p<0.04, thêm 1 chunk đuôi khi p>=0.05; chunk khoảng 900 token; calibration snapshot `scripts/val_calib.py` |
| Frozen config/menu | Recipe được bàn giao; config ID/hash, menu ID/hash và thời điểm freeze `null` |
| Input/code/output SHA-256 | `null`; không suy hash từ tên artifact trong recipe |
| Legacy fingerprint doc / chunk | `c1e068422e5f` / `fd07f9fc029a` (`REPORTED`) |
| Applicability / fallback / change counts | Query thực áp dụng, fallback reasons, số query/doc/chunk đổi, actual slot/chunk/token count: `null` |
| Ngân sách / chi phí | 200 doc/query, policy chunk trên, ZIP LZMA; giới hạn ZIP 100 MB do dự án ghi nhận; actual bytes, CPU/GPU time, RAM/VRAM, annotation cost: `null` |
| Report/artifact links | [Handover gốc](../doc/HANDOVER.md), [lịch sử số đo](../doc/PROGRESS.md), [baseline manifest](manifests/baseline.json); liên kết execution artifact đã verified `null` |

| Metric | B00 — giá trị được báo |
|---|---:|
| `FINAL_SCORE` | 0.3442 |
| `DOCS_F2MACRO` | 0.3605 |
| `CHUNKS_F2MACRO` | 0.3279 |
| `DOCS_PRECISION` | 0.1884 |
| `DOCS_RECALL` | 0.6047 |
| `CHUNKS_PRECISION` | 0.1931 |
| `CHUNKS_RECALL` | 0.4573 |

**Quyết định:** giữ B00 làm mốc so sánh được báo. Đây là snapshot lịch sử, chưa phải tuyên bố đã reproduce trong checkout này. CI/per-query differences `null`. Lượt allocation lịch sử tăng FINAL từ 0.3272 lên 0.3442 theo tài liệu; không quy gain đó cho BEAR mới.

**Bước tiếp / rollback:** N0 kiểm provenance/parity; giữ nguyên artifact và recipe B00, không ghi đè corpus/calibration hoặc thay baseline khi thử candidate.

### R01 — Bài nộp TXT/BEAR được người dùng báo ngày 19/10/2026

| Trường | Giá trị |
|---|---|
| `entry_id` / `parent_control` | `R01` / `B00` dùng để so sánh; execution parent manifest `null` |
| `recorded_date` / `reported_date` | `2026-10-19` / `2026-10-19` |
| `execution_date` / `scored_date` | `null` / `null`; ngày báo không xác định ngày chạy hoặc ngày chấm |
| Mức bằng chứng / nguồn | `REPORTED`; JSON 7 metric trong hội thoại và người dùng xác nhận đây là bài nộp từ `TXT_handover`/ý tưởng trong thư mục TXT |
| Run / submission ID / evaluator | Technical run ID `null`; submission ID `null`; evaluator version/split hash `null` |
| Phương pháp được xác nhận | TXT/BEAR integrated submission; không suy đây là một ablation L1, L4, F0, adaptive hoặc chunk-only cụ thể |
| Phạm vi / query universe | P200/PLARGE/chunk-only thực tế `null`; query IDs/count và doc count thực tế `null`; target của handover là ID 1–1200, 200 doc/query |
| Frozen config/menu | Config path/hash, menu/hash, chosen trial, lambda/feature/endpoints và freeze time: `null` |
| Input/code/output provenance | Corpus/query/pool/split/source/feature manifest hashes, code hash/commit, output JSON/ZIP SHA-256: `null` |
| Fingerprints / report links | Observed doc/chunk fingerprints `null`; execution/evaluation/compare/selection reports `null` |
| Applicability | Output query count, feature query/pair count, đủ mapping/source scores, query thực áp dụng residual, actual scope: `null` |
| Fallback / thay đổi | Fallback total và theo reason; query/doc thêm/mất; rank đổi; chunk thêm/mất/đổi selector/slots: `null` |
| Ngân sách / chi phí | Actual doc/chunk/token/character/ZIP bytes, budget matched với B00, CPU/GPU time, peak memory, annotation cost: `null` |
| Paired statistics | Per-query differences, CI95%, bootstrap settings, win/tie/loss, subgroup regressions: `null` |

| Metric | B00 — 15/10 | R01 — người dùng báo | Delta R01 − B00 |
|---|---:|---:|---:|
| `FINAL_SCORE` | 0.3442 | 0.3445 | +0.0003 |
| `DOCS_F2MACRO` | 0.3605 | 0.3612 | +0.0007 |
| `CHUNKS_F2MACRO` | 0.3279 | 0.3279 | 0.0000 |
| `DOCS_PRECISION` | 0.1884 | 0.1886 | +0.0002 |
| `DOCS_RECALL` | 0.6047 | 0.6065 | +0.0018 |
| `CHUNKS_PRECISION` | 0.1931 | 0.1926 | −0.0005 |
| `CHUNKS_RECALL` | 0.4573 | 0.4585 | +0.0012 |

Delta trên tính chính xác từ **các số hiển thị bốn chữ số**. Giữ `FINAL_SCORE` do nguồn báo; không tính lại FINAL bằng các thành phần đã làm tròn. Chunk F2 bằng nhau ở độ chính xác hiển thị, trong khi chunk P/R thay đổi; không kết luận output chunk, số chunk hoặc artifact giống nhau.

**Diễn giải:** điểm báo cao hơn B00 nhẹ, phần Doc F2 tăng và chunk F2 chưa tăng ở mức hiển thị. Chưa có bằng chứng để quy gain cho evidence, local evidence, query gate hoặc sparse riêng; chưa có paired CI để kết luận có ý nghĩa thống kê. Đây là kết quả bài nộp TXT/BEAR đã được người dùng xác nhận, dù liên kết kỹ thuật còn thiếu.

**Quyết định:** `inconclusive` về lợi ích ổn định/cơ chế H1–H6; **chưa promote baseline**. Không gán R01 cho `scoring_result.zip`, `prediction_result.zip` hoặc `x12m_ext10.zip` ở root khi chưa có provenance. Archive score đã quan sát trong tài liệu là một observation riêng, không thay cho các metric R01 và không phải nguồn qrels mới.

**Bước tiếp / rollback:** N0–N1 liên kết đúng run và kiểm mức áp dụng thực tế; sau đó N2/N3. Giữ B00 và R01 thành hai artifact độc lập khi nhận được file; rollback về recipe/artifact B00 đã xác minh nếu candidate không đạt tiêu chí. Không xóa kết quả R01 khi có đính chính; nối thêm entry.

## 3. Lịch sử kiểm chứng kỹ thuật được kế thừa

### T00 — Trạng thái code CPU/fixtures trong tài liệu ngày 19/10/2026

`CODE_VERIFIED` **được kế thừa từ tài liệu**, không phải tests vừa chạy khi lập sổ: [IMPLEMENTATION_STATUS.md](reports/IMPLEMENTATION_STATUS.md), [RESULTS.md](reports/RESULTS.md) và [TXT_handover.md](TXT_handover.md) ghi nhận 48/48 tests BEAR, 10/10 tests offline legacy qua; calibration/tầng chunk, pool/features/ranking và guards có fixture coverage. Thời điểm chạy, môi trường và code hash của những lần chạy đó cần lấy từ report/manifest gốc; khi chưa liên kết thì `null`.

Các kiểm tra trên không chứng minh relevance gain hoặc full-data parity. C1/C2 hiện có pure selectors; adaptive runner còn prerequisites; sparse/discovery chưa có study hoàn chỉnh. Báo cáo fixture cũ chưa chứa kết quả R01 được người dùng báo sau đó; giữ hai mức bằng chứng riêng. Không chạy lại tests, benchmark hoặc GPU để tạo entry này.

## 4. Kế hoạch hiện tại sau R01 — PROPOSED

Mọi mốc dưới đây chưa có kết quả nếu chưa được nối bằng entry thực nghiệm. Mỗi study ghi budget/trial menu/cost ceiling và primary metric trước khi chạy. N2/N3 có thể chuẩn bị độc lập sau N0–N1; mọi lựa chọn nhánh và interaction đều dùng dev trước N5.

| ID | Việc cần làm | Đối chứng / đầu ra để chuyển bước |
|---|---|---|
| **N0 — Provenance và parity** | Nhận run/submission ID, JSON/ZIP và report của R01; gắn config/code/input/output hashes, query universe/evaluator; xác minh B00 bằng recipe/fingerprints trước khi so công bằng. | Manifest B00/R01, config freeze status và parity report. Nếu thiếu artifact, ghi `UNRESOLVED` cụ thể; không giả reproduction. |
| **N1 — Audit feature và mức áp dụng** | Đếm output/features/eligible/applied/fallback theo query và reason; đếm doc/rank/chunk đổi so với control; xác minh B/D family provenance, candidate headroom và budget thực. | L0/application report. Template `l0_pilot.json` dùng sample; run có thể xuất toàn pool với query thiếu feature fallback. `pool_v1.json` có `sources=[]`, `b_family=null`. Đây là rủi ro từ template cần kiểm với config R01, chưa phải kết luận R01 chỉ áp dụng trên sample. |
| **N2 — Fixed body/local evidence** | Kiểm H1/H2 bằng L1 `body_coverage` và L4 đề xuất `local_max_all`, cùng pool/split/λ/reference/tuning budget; phân tích rank/language/length/chunk-count bins. | L1 dùng 6 λ `{0, 0.02, 0.05, 0.1, 0.2, 0.35}` trong [menus_v1.json](configs/menus_v1.json). L4 đăng ký riêng 6 config cùng λ qua `run`/`compare`; `tune` hiện chỉ có family L1/F0, không coi L4 đã có runner family. Báo toàn bộ trial và fallback. |
| **N3 — C1/C2 chunk pilot độc lập** | Giữ doc set, allocation, slot budget và offset snapshot; báo token budget thực tế vì thay chunk có thể đổi độ dài. C1 mở existing scores cho tầng 41–120/đuôi, C2 so local evidence trên cùng tầng. Audit multi-chunk và score coverage trước. | Chunk report với actual chunks/token/ZIP, mapping/fallback và labels/diagnostic đúng phạm vi; không quy gain do thêm slot cho selector. Hoàn thiện study runner trước execution. |
| **N4 — F0/O0, H3 và controls** | Chỉ khi nguồn B/D và nhãn đủ: tune best fixed F0 với menu đã khóa; đo oracle menu/headroom và quan hệ E(q)–Δutility; constant/query-only/shuffled controls. Chỉ mở adaptive nếu có cơ sở. | Verified source manifests; O0/H3/control report và cost/headroom đủ đáng thử. Silver oracle chỉ diagnostic; không dùng điểm tổng hoặc p(gold) làm gold. Sparse là nhánh có điều kiện, chưa tự mở. |
| **N5 — Chọn, freeze, xác nhận và full integrity** | Chọn một candidate cuối cùng và mọi interactions trên dev, freeze config/menu/code/protocol/controls; xác nhận holdout một lần. Sau đó áp cùng frozen parameters với full features, kiểm integrity/fallback/parity. | Paired estimate/CI và cost, regression check; full query/feature counts; JSON/ZIP hashes, provenance và rollback package. Không chọn lại giữa fixed/adaptive/chunk sau khi xem holdout; promote chỉ khi đạt protocol đã freeze. |

Liên kết thực hiện: [RUNBOOK.md](reports/RUNBOOK.md), [DATA_READINESS.md](reports/DATA_READINESS.md), [EVALUATOR_CONTRACT.md](reports/EVALUATOR_CONTRACT.md), [KNOWN_LIMITATIONS.md](reports/KNOWN_LIMITATIONS.md), [DECISIONS.md](reports/DECISIONS.md). Các đường dẫn trong template là điểm bắt đầu, không phải bằng chứng job đã chạy hoặc R01 đã dùng đúng template đó.

Namespace dự kiến của vòng mới thống nhất theo proposal §13 và handover §7.1: configs dưới `TXT/configs/next_round/`, runtime dưới `TXT/runtime/next_round/N0_v1/` đến `N5_v1/`, reports dưới `TXT/reports/next_round/` với tên `N0_provenance_v1.md`, `N1_application_audit_v1.md`, `N2_fixed_evidence_v1.md`, `N3_chunk_pilot_v1.md`, `N4_routing_controls_v1.md`, `N5_confirmation_v1.md`. Các file/thư mục này chưa được tạo. Chọn candidate bằng primary metric cùng scope; không cộng hoặc so trực tiếp ΔP với local LCS để suy FINAL. Khi có kết quả, nối entry mới; giữ bảng kế hoạch này làm lịch sử đề xuất.

## 5. Mẫu nối thêm cho mỗi lượt

```yaml
entry_id: null
corrects_entry: null
supplements_entry: null
status: PROPOSED                  # REPORTED | ARTIFACT_OBSERVED | CODE_VERIFIED | UNRESOLVED
recorded_date: null
reported_date: null
execution_date: null
scored_date: null
timezone: null
source_links: []
run_id: null
submission_id: null
hypothesis: null
single_change: null
parent_control_id: null
scope: null                       # p200 | plarge | chunk_only | integrated
query_universe: null
evaluator_version_and_semantics: null
label_source_policy_and_coverage: null
frozen_config_path_and_sha256: null
frozen_menu_path_and_sha256: null
freeze_time: null
all_trials_ledger: null
input_corpus_query_pool_split_source_feature_hashes: null
code_commit_and_sha256_manifest: null
output_json_zip_sha256_and_legacy_fingerprints: null
counts:                          # Lưu actual counts và denominator; không chỉ tỷ lệ
  output_queries: null
  feature_queries_and_pairs: null
  fully_eligible_queries: null
  intervention_applied_queries: null
  fallback_queries_by_reason: null
  changed_queries_doc_add_drop_rank_and_chunks: null
budget_and_actual_docs_slots_chunks_tokens_chars_zip_bytes: null
cost_cpu_gpu_seconds_memory_annotation: null
metrics:
  FINAL_SCORE: null
  DOCS_F2MACRO: null
  CHUNKS_F2MACRO: null
  DOCS_PRECISION: null
  DOCS_RECALL: null
  CHUNKS_PRECISION: null
  CHUNKS_RECALL: null
metric_precision_and_delta_vs_control: null
per_query_delta_ci95_bootstrap_groups_seed_replicates: null
win_tie_loss_and_subgroup_regressions: null
dev_selection_report: null
holdout_exposures_and_protocol: null
decision: null                    # keep | reject | inconclusive
baseline_promotion: null
limits_and_negative_results: null
next_step: null
rollback_artifact_and_recipe: null
report_artifact_links: []
```

Khi điền entry, giải thích ngắn vì sao quyết định phù hợp với bằng chứng, đặc biệt nếu metric official, local labels và proxy khác nhau. Thiếu CI/nhãn/artifact thì ghi giới hạn; không tự điền giá trị để làm bản ghi trông hoàn chỉnh.

## 6. Lịch sử cập nhật tài liệu

### D01 — Đồng bộ kế hoạch triển khai N0–N5, 19/10/2026

| Trường | Giá trị |
|---|---|
| `entry_id` / `supplements_entry` | `D01` / `R01`; bổ sung kế hoạch sau kết quả được báo, không sửa các entry trước |
| `recorded_date` / `reported_date` | `2026-10-19` / `2026-10-19` |
| Loại cập nhật / trạng thái kế hoạch | Chỉ tài liệu / `PROPOSED`; N0–N5 chưa được nghiệm thu |
| Nguồn hiện hành | [TXT_Proposal.md](TXT_Proposal.md) giải thích giả thuyết/phương pháp; [PLAN v2.0](PLAN.md) quy định task/dependency/acceptance; [TXT_handover.md](TXT_handover.md) hướng dẫn vận hành; sổ này giữ lịch sử |
| Bản lưu lịch sử | [PLAN trước N0–N5](archive/PLAN_before_N0_N5_20261019.md) giữ nguyên kế hoạch T01–T16 và hợp đồng chi tiết; ledger kỹ thuật hiện có vẫn là snapshot triển khai trước kết quả mới |
| Phạm vi kế hoạch | Giữ N0 provenance → N1 application audit; N2 fixed body/local và N3 chunk độc lập sau readiness; N4 có điều kiện; N5 chọn trên dev, freeze rồi một lần holdout |
| Kết quả thực nghiệm / metric mới | `null`; không có experiment, test, benchmark, GPU job hoặc submission được chạy trong lần đồng bộ tài liệu này |
| Quyết định / bước tiếp | Dùng PLAN v2.0 làm nguồn giao việc vòng mới; bắt đầu task N0 đủ dependency, giữ nguyên các metric B00/R01 và các giới hạn bằng chứng đã ghi |

Việc đồng bộ tài liệu không xác nhận provenance bài nộp, hoàn tất N0–N5 hoặc promote baseline. Các report/runtime của vòng mới vẫn là đích dự kiến; khi có kết quả thật, nối entry mới cùng artifact/hash và quyết định trong đúng phạm vi đã đo.

## 7. Triển khai phần mềm2.0

### I20 — Backend CPU BEAR2.0.0, 19/10/2026

| Trường | Giá trị |
|---|---|
| entry_id / supplements_entry | I20 / D01 và R01; giữ nguyên các metric/diễn giải lịch sử |
| evidence / phạm vi | CODE_VERIFIED bằng fixtures + ARTIFACT_OBSERVED của N0 inventory checkout; chưa quality benchmark |
| Phần thay đổi | Provenance và application replay audit; tune L1/L4/L1_L4; native C1/C2 study/local evaluator; routing dev diagnostics; preflight, paired doc metrics, whole-candidate freeze và selected-chunk release |
| Kiểm tra thực chạy | 63/63tests BEAR (15v2 +48nền),10/10legacy;7config schemas;12trial dry menu; CLI BEAR2.0.0 |
| N0 thực chạy | Inventory execute có18roles missing, linkage unresolved, baseline parity chưa xác minh; không gán root ZIPs cho R01 |
| N1–N5 thật | Chưa có R01 runtime/features/pool/corpus/qrels/passages để chạy benchmark; fixture status không thay nghiệm thu chất lượng |
| Metric mới / per-query gain / CI thật | null; FINAL0.3445 vẫn là số R01 người dùng báo trước đó, không phải kết quả v2 mới đo |
| Routing và confirmatory giới hạn | A1 production vẫn gated; rule/shuffle diagnostics chưa là matched-budget A1 controls. Multi-control một exposure và official chunk evaluator chưa mở |
| Cost thật / full release | RAM/I/O/GPU/annotation/full corpus runtime/ZIPbytes: null; chưa nén package thật, mở holdout thật, upload hoặc promote |
| Report/code identities | [V2_IMPLEMENTATION](reports/next_round/V2_IMPLEMENTATION.md), [readiness](reports/next_round/V2_READINESS.json), [N0](reports/next_round/N0_provenance_v1.md), [code inventory v2](manifests/code_inventory_v2.json) |
| Decision / bước tiếp | Quality inconclusive; kỹ thuật v2 đã qua fixtures. Nhận/bind14R0 roles + baseline manifest +3R01 artifacts, version N0 output rồi chạy N1 thật; labels/passages/B–D là dependencies riêng |
| Rollback | Giữ recipe/artifacts B00 và R01 riêng; không đổi corpus/beta hoặc promote baseline vì tests xanh |

Token/passage metric mới là local_passage_recall với tokenizer local và official_equivalent=false; không so trực tiếp nó với Doc ΔP hoặc gọi official Chunk F2. Runtime fixtures chỉ chứng minh invariants. Trạng thái N0 partial được lưu bằng manifest/hashes; khi nhận inputs khác phải dùng output version mới, không sửa completed manifest.
