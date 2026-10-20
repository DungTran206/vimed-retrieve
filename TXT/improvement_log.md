# Nhật ký cải tiến TXT/BEAR

Ngày mở sổ: **19/10/2026**. Đọc cùng [TXT_Proposal.md](TXT_Proposal.md) và [TXT_handover.md](TXT_handover.md). Sổ này theo dõi kết quả từng lượt, mức bằng chứng, quyết định và kế hoạch tiếp theo; không thay manifest hoặc báo cáo của từng run.

**Hiện hành20/10/2026:** [PLAN v3.3](PLAN.md) và [BEAR_ALGORITHM](BEAR_ALGORITHM.md) xây thuật toán selected_docs/selected_chunks trên0,391. [Readiness và CPU](reports/EXPERIMENT_READINESS_20261020.md) đã kiểm thật:5input roles thiếu, structured algorithm chưa ready, CPU kernel cũ đã đo. Đọc D06/D07; chưa có relevance gain mới.

## 1. Quy tắc ghi sổ

- **Chỉ nối thêm lịch sử.** Khi sửa một kết luận hoặc bổ sung provenance, thêm mục mới có `corrects_entry`/`supplements_entry`; giữ nguyên số đã báo và lý do đính chính. Kế hoạch chưa chạy phải ghi `PROPOSED`, không ghi như kết quả.
- `reported_date` là ngày nhận/bản nguồn báo kết quả; `execution_date` là ngày job chạy; `scored_date` là ngày evaluator chấm. Không suy hai ngày sau từ ngày báo. Lưu timezone nếu có timestamp.
- `null` nghĩa là chưa biết hoặc chưa có bằng chứng; không thay bằng 0. Phân biệt `not_applicable` với thiếu dữ liệu. Giữ số đầy đủ do nguồn cung cấp; delta từ số hiển thị phải ghi rõ độ chính xác đó.
- Mỗi lượt gắn một thay đổi chính, parent/control, phạm vi P200/PLARGE/chunk-only, query universe, evaluator và ngân sách. Nếu ghép nhiều thay đổi, ghi là integrated run và không quy toàn bộ gain cho một giả thuyết.
- Ghi config/menu và định danh artifact thực dùng; bổ sung SHA-256 khi có. Với lượt thử nhỏ, thiếu một trường metadata không buộc chạy lại nghiên cứu đã được báo; giữ `null` và nguồn rõ theo D02. Tên file giống nhau không chứng minh cùng snapshot; legacy fingerprint chỉ đối chiếu đúng phạm vi hash của nó.
- Lưu cả số query có output, có đủ feature, thực sự được can thiệp, fallback theo nguyên nhân và số query/doc/chunk đổi so với control. Đủ 1.200 dòng output chưa chứng minh BEAR áp dụng trên cả 1.200 query.
- Nhãn/evaluation cần nguồn và coverage rõ. Điểm tổng người dùng báo không phải qrels. Không biến item chưa judged thành âm tính hoặc dùng feedback để dựng nhãn giả cho inference/gate.
- Chọn cấu hình trên validation và ghi mọi trial. Nếu có holdout thật chưa xem, freeze candidate/controls trước xác nhận và không chọn lại sau đó. Không gọi 593 câu đã dùng nhiều lượt là holdout sạch hoặc tạo split mới để tuyên bố hết contamination; xem PLAN v3 §10.4.
- `keep`, `reject`, `inconclusive` là quyết định về chất lượng trong phạm vi đã đo; promote baseline là quyết định riêng, cần bằng chứng và khả năng rollback.

| Mức bằng chứng | Cách hiểu trong sổ |
|---|---|
| `REPORTED` | Người dùng hoặc tài liệu báo kết quả; chưa tự xác minh toàn bộ artifact/run. |
| `ARTIFACT_OBSERVED` | Đã đọc artifact xác định; chỉ kết luận trong phạm vi provenance/semantics đã xác minh. |
| `CODE_VERIFIED` | Đã đối chiếu code hoặc có kiểm thử kỹ thuật; không đồng nghĩa retrieval gain. Khi kế thừa từ báo cáo cũ phải ghi rõ, không nói vừa chạy lại. |
| `DOC_ONLY` | Chỉ cập nhật kế hoạch/tài liệu; không có phép đo chất lượng, test hoặc submission mới. |
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

## 4. Lịch sử kế hoạch sau R01 — PROPOSED ngày 19/10, đã thay bằng PLAN v3

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

## 8. Kết quả và quyết định nhận ngày 20/10/2026

### R02 — L1/L4 trên bài tốt nhất 0,4076

| Trường | Giá trị |
|---|---|
| `entry_id` / `supplements_entry` | `R02` / `R01`, `I20`; giữ nguyên các số và diễn giải lịch sử |
| `recorded_date` / `reported_date` | `2026-10-20` / `2026-10-20` |
| `execution_date` / `scored_date` | `null` / `null`; không suy từ ngày nhận báo cáo |
| Mức bằng chứng / nguồn | `REPORTED`; người dùng chuyển kết quả của AI đã chạy thí nghiệm trong hội thoại |
| Control | Bài tốt nhất được báo **0.4076**; technical run/submission ID và bộ bảy metric `null`. Không đồng nhất với archive local có Doc F2 0.407343155932693 |
| Phạm vi / ngân sách | Giữ `k_q` từng câu, số doc ZH và chunk toàn body; chỉ xếp lại/chọn làn VI trên pool 400. Không áp mặc định 200 doc/câu |
| Features / coverage | `full_v1`, coverage được báo **100% / 99,6%**; định nghĩa riêng và mẫu số hai tỷ lệ `null` |
| Trial menu | L1 và L4, mỗi family sáu λ: `0, 0.02, 0.05, 0.10, 0.20, 0.35`; λ=0 là control |
| Nhãn | Mọi doc được chọn có nhãn theo nguồn báo; `not_gold` vẫn có khả năng âm giả do điều kiện chunk overlap |
| Config/code/input/output hashes / query universe | `null`; không dựng thông tin artifact từ lời mô tả |
| CI / per-query / cost | CI95 được báo chạm 0 hoặc âm; endpoints, per-query deltas, bootstrap settings, runtime/RAM/chi phí `null` |
| Report | [L1_L4_20261020.md](reports/L1_L4_20261020.md) |

| λ | Δ Doc F2 L1 | Δ Doc F2 L4 |
|---:|---:|---:|
| 0 | 0 (control) | 0 (control) |
| 0.02 | +0.0003 | +0.0004 |
| 0.05 | +0.0002 | +0.0001 |
| 0.10 | +0.0003 | +0.0003 |
| 0.20 | −0.0021 | −0.0018 |
| 0.35 | −0.0085 | −0.0081 |

**Quyết định:** `reject` các cấu hình L1/L4 đã thử cho việc nộp bài; đóng vòng tuning này. Không đủ bằng chứng về gain ổn định; không suy Δ FINAL từ Δ Doc F2. Bài 0,4076 là control thực nghiệm tiếp theo theo kết quả người dùng báo, không phải promote do fixtures BEAR 2.0.0.

**Giới hạn nhãn:** nguồn báo khoảng 0,5 doc/query là doc đúng bị đưa vào `not_gold` khi không chunk nào overlap ≥ 0,4; chưa biết ID. Ước lượng bias `±0.0002` là số nguồn báo, chưa có sensitivity analysis hoặc bound chứng minh. “Đã có nhãn” không đồng nghĩa mọi nhãn âm chính xác. Không kết luận rằng L1/L4 không thể hữu ích với mọi features/baseline khác.

**Bước tiếp:** chẩn đoán control từ cache theo PLAN v3, chỉ thử một thay đổi khi có headroom. Không mở thêm λ hoặc nộp các point estimate dương rất nhỏ. Giữ nguyên output control và dùng exporter tương thích `k_q`/full body.

### A02 — Kiểm tra nhất quán `val.jsonl` local

| Trường | Giá trị |
|---|---|
| `entry_id` / `supplements_entry` | `A02` / `R02` |
| `recorded_date` / evidence | `2026-10-20` / `ARTIFACT_OBSERVED` |
| Artifact | [val.jsonl](../val.jsonl) tại root checkout; đường dẫn `data/lb/val.jsonl` là phía người chạy báo, chưa xác nhận cùng snapshot |
| Query / unique ID | 593 / 593 |
| Cặp `gold` / `not_gold` | 22.091 / 66.547 |
| `gold_unseen` | 582 query > 0; tổng 20.186 |
| Độ lệch `d_q = G − len(gold) − gold_unseen` | 205 query > 0, tổng 305, trung bình 0,5143338954/query; min 0, max 8 |
| Diễn giải | Kiểm tra trường dữ liệu cùng quy mô với nguồn báo; không chứng minh nguyên nhân chunk-overlap hoặc xác định doc âm giả |
| Quyết định | Dùng nhãn BTC offline với nguồn/semantics rõ; tách negative mức doc, âm suy từ chunk và unknown. Không coi unknown là âm; không bắt gán tay lại toàn bộ 593 câu |
| Quality metric / submission mới | `null` / không có |

### D02 — Chuyển sang kế hoạch từ control 0,4076

| Trường | Giá trị |
|---|---|
| `entry_id` / `supplements_entry` | `D02` / `R02`, `A02`; cập nhật hướng đi sau D01/I20 |
| `recorded_date` / evidence | `2026-10-20` / `DOC_ONLY`; các phép thử tiếp theo là `PROPOSED` |
| Nguồn hiện hành | [PLAN v3](PLAN.md), [proposal](TXT_Proposal.md), [handover](TXT_handover.md), [README](README.md) và [RESULTS](reports/RESULTS.md) |
| Kết luận được tiếp nhận | N0/N1 đủ 1.200 câu, w045 parity 100%, trung bình 5,5 doc đổi/query là `REPORTED`; không bắt lặp lại. N3 không ưu tiên khi control dùng full body. Routing oracle cũ khoảng 1,5% trên silver là bằng chứng hẹp để hạ ưu tiên, không phải upper bound cho mọi cách định tuyến |
| Thay đổi kế hoạch | Đóng L1/L4; chẩn đoán control 0,4076 rồi thử một thay đổi từ cache theo PLAN v3 trước khi quyết định stop/go. Không chạy lại L1/L4 hoặc mở rộng grid |
| Cách ghi metadata | Mẫu log đầy đủ phía trên là khả năng lưu khi có dữ liệu, không phải danh sách thủ tục phải hoàn tất trước mọi phép thử nhỏ. Artifact ở máy người chạy có thể được dẫn từ đó; field chưa biết giữ `null`, không biến thiếu artifact local thành yêu cầu làm lại công việc đã báo |
| Code / kiểm tra / metric | Phần mềm giữ 2.0.0. Không chạy lại tests hoặc benchmark, không chạy GPU, nén ZIP hoặc submit trong lượt sửa docs. Kết quả 63/63 + 10/10 là kiểm tra lịch sử I20 |
| Quyết định / rollback | Kế hoạch N0–N5 phía trên là lịch sử; dùng PLAN v3. Nếu probe không có gain đáng tin trong phạm vi nhãn được đánh giá, giữ bài 0,4076 và dừng vòng đó |

Các entry mới tách số nguồn báo, quan sát artifact local và quyết định tài liệu. Không thay nhãn đánh giá bằng output suy luận, không quy score 0,4076 cho phần triển khai TXT chưa benchmark.

## 9. Đổi baseline theo yêu cầu người dùng —20/10/2026

### B01 — Baseline hiện hành Pipeline0,391

| Trường | Giá trị |
|---|---|
| `entry_id` / `supplements_entry` | `B01` / `R02`, `D02`; đổi mốc làm việc, không sửa kết quả cũ |
| Ngày ghi / nguồn | 2026-10-20; người dùng yêu cầu “baseline mới trong file pipeline0,391” |
| Baseline được chọn | **0.391**; `USER_SELECTED` / `REPORTED`, chưa xác nhận score artifact |
| Nguồn local | [Pipeline0,391 - Miro.html](<../Pipeline 0,391 - Miro.html>) |
| Quan sát artifact | `ARTIFACT_OBSERVED`: tên board Pipeline0,391 và đoạn editor “Embed title + 600 kí tự”; bản lưu canvas chưa cung cấp recipe đầy đủ |
| Full metrics / run ID / ngày chạy-chấm | `null`; không tự gán0.391 là Doc F2, Chunk F2 hay tái tạo FINAL từ nó |
| Corpus/query snapshot, k, quota, cap, chunk/exporter | Chưa xác nhận; không kế thừa full-body/pool400/calibration từ0.4076 hoặc w045 |
| Report nguồn | [BASELINE_0391_20261020.md](reports/BASELINE_0391_20261020.md) |
| Bằng chứng chất lượng mới / submission mới | `null` / không có; đổi baseline không là phép đo regression từ0.4076 |
| Vai trò0.4076/L1/L4 | Giữ nguyên toàn bộ số ở R02; không chuyển delta hoặc CI sang0.391 |

### D03 — Đồng bộ kế hoạch v3.1 theo baseline0,391

| Trường | Giá trị |
|---|---|
| `entry_id` / `corrects_entry` | `D03` / phần “control tiếp theo0.4076” của `D02`; giữ lịch sử D02 |
| Ngày ghi / trạng thái | 2026-10-20 / `DOC_ONLY`; M0–M3 vẫn `PROPOSED` |
| Tài liệu hiện hành | [PLAN v3.1](PLAN.md), [proposal](TXT_Proposal.md), [handover](TXT_handover.md), [README](README.md), runbook và các report liên quan |
| Kế hoạch trước đổi baseline | [PLAN v3 snapshot](archive/PLAN_v3_before_baseline_0391_20261020.md) |
| M0 | Dùng đúng artifacts/evaluator/recipe pipeline0.391; không lấy λ0/hits/per-query score0.4076 thay control mới; không dựng lại toàn bộ w045 |
| M1/M2 | Đọc count, policy chunk, ngôn ngữ và cap thật `P0` của0.391. Một họ/tối đa hai candidate; A đổi countVI chỉ khi recipe phù hợp và chưa thử, B mở cap thật nếu có headroom/cache |
| Invariants | Mọi phần không can thiệp giữ theo baseline0.391 thực có; không mặc định một chunk body/doc hoặc cap400; control phải khớp đúng tập doc/policy mới |
| Quyết định dừng | Không có gain đáng tin thì `retain_0.391`; không tự mở lại L1/L4 chỉ vì đổi baseline |
| Code / tests / benchmark | Giữ software2.0.0; không sửa code hoặc chạy benchmark/tests mới trong lượt này |

B01/D03 thay baseline hiện hành, không xóa B00/R01/R02, A02, D01/D02 hoặc I20. Số đo và ngày chạy không có artifact xác nhận tiếp tục để `null`.

## 10. Bổ sung sơ đồ pipeline cho agent —20/10/2026

### D04 — Chuyển hai ảnh Miro thành Markdown

| Trường | Giá trị |
|---|---|
| `entry_id` / `supplements_entry` | `D04` / `B01`, `D03` |
| Ngày ghi / loại thay đổi | 2026-10-20 / `DOC_ONLY`; không sửa code hoặc chạy benchmark |
| Nguồn | Hai ảnh Miro do người dùng đính kèm trong hội thoại; quan sát trực tiếp nội dung ảnh, chưa đối chiếu run/config |
| File tạo | [PIPELINE_0391.md](PIPELINE_0391.md), gồm luồng chữ, Mermaid, tham số và phần chưa rõ |
| VI đọc từ ảnh | BM25F có dấu title×3/tags×2/descr×1.5/body×1; dense đầu bài title+600 ký tự đầu body; dense chunking. Mỗi nguồn top1000; union khoảng2200; RRF k60; lấy300VI |
| ZH đọc từ ảnh | BGE-M3/Qwen3-8B với queryVI gốc và queryZH dịch bằng Qwen3.5-9B; weights1/1/0.3/0.3; RRF →400 →40ZH. Chưa ghi k RRF nhánh này |
| Rerank/chọn doc | 300VI+40ZH →Qwen reranker4B →P(Yes)/softmax →MaxP →p̂ →threshold, mục tiêu trung bình160doc/query |
| Phân biệt cần giữ | 340 là ứng viên trước rerank;160 là trung bình sau threshold. Quota đầu vào không bảo đảm quota đầu ra; “Lấy full” không xác nhận chunk=body |
| Phần còn thiếu | Threshold/MaxP/phép tính p̂, model revisions, chunk nộp/exporter, paths/config và metric thành phần |
| Đồng bộ bàn giao | README/handover/PLAN/proposal và report baseline dẫn bản Markdown. Phép thử count phải dùng policy sau rerank/tính p̂, không dùng prefix raw ranking như baseline |
| Metric / submission mới | `null` / không có; lịch sử L1/L4 trên0.4076 giữ nguyên |

D04 bổ sung thông tin ảnh mà bản HTML canvas trước đó chưa đọc được. Baseline vẫn0.391, software vẫn2.0.0; không tự mở thêm phép thử hoặc thay recipe theo suy đoán.

## 11. Gắn baseline0,391 với ý tưởng BEAR —20/10/2026

### D05 — Kế hoạch3.2: threshold đúng tầng và BEAR phân tích lỗi

| Trường | Giá trị |
|---|---|
| `entry_id` / `corrects_entry` / `supplements_entry` | `D05` / menu countVI ở `D03` / `D04`, `B01`; giữ nguyên nội dung lịch sử |
| Nguồn yêu cầu | Người dùng yêu cầu cải tiến TXT theo baseline và xác nhận ý tưởng là BEAR trong proposal hiện có |
| Ngày / trạng thái | 2026-10-20 / `DOC_ONLY`; các nghiên cứu mới vẫn `PROPOSED` |
| Vấn đề được sửa | Kế hoạch cũ thử VIcount×0.85/1.15 và giữ ZH sau lọc; sơ đồ thực có300VI+40ZH trước rerank rồi threshold trên p̂, counts output biến thiên |
| Phép thử hiện hành | Giữ candidates/scores/MaxP/p̂/chunk, chỉ đổi threshold cuối nếu baseline xác nhận mộtτ₀chung và chưa tối ưu cùng phép thử |
| Menu hữu hạn | Tối đa2threshold khác control, chọn từ score không dùng nhãn để meanTOTALcounts gần0.85K̄₀/1.15K̄₀. K̄₀ đo thật,160 chỉ là mục tiêu trên ảnh. Không áp hệ số cho VI hoặc từng query |
| Ý tưởng BEAR được giữ | Bảo toàn identifier/biến thể, evidence cùng ngữ cảnh, quan hệ/intent; audit doc gần threshold bằng span/cờ/mức chắc chắn. Chưa hard-filter, đổi score, coi flags là gold hoặc mở routing |
| Nhánh BEAR sau này | Chỉ đề xuất pilot cho1loại mismatch có bằng chứng bổ sung ngoài L1/L4; chưa mở trong vòng threshold. Pool/refitcalibration là backlog riêng |
| Sửa đánh giá | Khi k đổi, delta phụ thuộc hits control g₀; uncertainty của doc giữ nguyên cũng có thể ảnh hưởng. Sensitivity không chỉ xét added/removed;±0.0002 và305không phải bound |
| Tài liệu / đặc tả | [PLAN v3.2](PLAN.md), [proposal](TXT_Proposal.md), [handover](TXT_handover.md), README/runbook/reports; [JSON tham chiếu](specs/pipeline_0391.json) không chạy CLI |
| Bản lưu trước cập nhật | [PLAN3.1](archive/PLAN_v3_1_before_threshold_alignment_20261020.md), [proposal3.1](archive/TXT_Proposal_v3_1_before_threshold_alignment_20261020.md) |
| Code quan sát, chưa liên kết run | Root val_calib.py có --maxp/beta8 hoặc10, nhưng chưa xác minh0.391 dùng recipe đó; không thực thi fit/ghi beta |
| Software / metric mới | Giữ2.0.0; không sửa code, chạy benchmark/GPU hoặc submit. Gain mới/CI/Chunk/FINAL = null |
| Quyết định giữ | Nếu không có gain đáng tin hoặc phép thử đã tối ưu, retain_0.391. Không tự chạy lại L1/L4 hay N0/N1 |

D05 cải tiến sự phù hợp giữa baseline, ý tưởng và phép thử. Nó không chứng minh điểm retrieval đã tăng; số thực nghiệm được nối bằng entry riêng khi có run thật.

## 12. Khôi phục mục tiêu thuật toán BEAR —20/10/2026

### D06 — BEAR phải retrieve doc và chunk

| Trường | Giá trị |
|---|---|
| entry_id / corrects_entry | D06 / D05; giữ nguyên lịch sử v3.2 |
| Nguồn đính chính | Người dùng: “BEAR ban đầu là để tạo thuật toán retrieve doc và chunk” |
| Sai phạm vi được sửa | v3.2 thu hẹp BEAR thành audit và threshold-only; chưa thể hiện đủ mục tiêu thuật toán |
| Vai trò hiện hành | Retrieval hai tầng: tái dùng candidates/score baseline0,391 →structured evidence →Doc Selector + Chunk Selector →output doc/chunk |
| Output nghiệm thu | selected_docs và selected_chunks nối được tới submission; flags/report đơn lẻ chưa đủ |
| Thiết kế | [BEAR_ALGORITHM.md](BEAR_ALGORITHM.md), [proposal3.3](TXT_Proposal.md), [PLAN3.3](PLAN.md) |
| Công việc tiếp | A0adapter →A1structured evidence →A2doc selection →A3chunk selection →A4ablation/joint |
| Đối chứng mới | B0baseline, D1doc-only, C1chunk-only, DC1joint; tối đa3candidate mới và1control trong pilot đã khóa |
| Budget pilot | D1giữ k thực từng query để cô lập thay doc; C1giữ doc set/order/slots/text budget để cô lập chunk selector |
| L1/L4 | Vẫn đóng cấu hình uniform coverage đã thử trên0,4076; không suy mọi structured evidence/chunk algorithm vô ích hoặc chạy lại tên mới |
| Audit/threshold | Công cụ kiểm feature và operating point/control phụ; không thay mục tiêu retrieval |
| Code/gain | Giữsoftware2.0.0; matcher/uniform features/fusion/C1C2scaffolding có sẵn, structured relation/conflict và adapter mới chưa triển khai đầy đủ. Chưa có benchmark/metric/gain mới |
| Bản lưu | [PLAN3.2](archive/PLAN_v3_2_before_doc_chunk_restore_20261020.md), [proposal3.2](archive/TXT_Proposal_v3_2_before_doc_chunk_restore_20261020.md) |
| Tính nhất quán | README/handover/runbook/reports/spec được đồng bộ; facts baseline/metrics lịch sử giữ nguyên |

D06 sửa mục tiêu và đặc tả; chưa đánh dấu thuật toán mới đã code xong. Bằng chứng triển khai và quality gain chỉ nối thêm khi thực sự có run/evaluation.

## 13. Chuẩn bị thử nghiệm và tài nguyên —20/10/2026

### D07 — Preflight A0 và benchmark CPU tái lập được

| Trường | Giá trị |
|---|---|
| entry_id / supplements_entry | D07 / D06; mục tiêu BEARdoc/chunk giữ nguyên |
| Bằng chứng | CODE_VERIFIED cho CLI/config/tool phụ trợ; ARTIFACT_OBSERVED cho input inventory và CPU microbenchmark; không phải retrieval quality benchmark |
| File chuẩn bị | [Preflight template](configs/bear_doc_chunk/preflight_0391.template.json), [readiness report](reports/EXPERIMENT_READINESS_20261020.md), [benchmark tool](tools/benchmark_cpu.py) |
| Preflight đã chạy | CLIprovenance --dry-run; statusblocked_input, exit1; [JSON thực](reports/bear_doc_chunk_preflight_20261020.json) |
| Inputs hiện diện | btc_validation:rootval.jsonl,864073byte; tồn tại file không chứng minh mọi labels negative đáng tin |
| Inputs thiếu | queries, baseline_0391_predictions, candidates_and_cached_scores, corpus, baseline_chunk_policy_and_refs |
| Code chưa đủ | Structured relation/conflict/evidence mới + adapter/Doc/Chunk runner0,391; oldpool/chunkstudy/export còn fixed200. Không đánh dấu A1–A4xong |
| Phần code mới | Benchmark utility đo kerneldocument_evidence exact cũ, không sửa corepackage hoặc triển khai thuật toán mới |
| Môi trường đo | 11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz;8logicalthreads;RAM7.8GiB;available0.7GiB lúc đo;Python3.13.1 |
| Workload synthetic | 8concepts/query,chunk1000char,nooverlap,1thread,3samples×0.65s/scenario;repeatedtext và warmcache |
| Kernel medians | 4kchar:725.58pair/s;20k:173.63;80k:44.51 |
| Ngoại suy408000pair | 9.37min / 39.16min / 152.77min theo4k/20k/80kchar;chỉkernel,không fullrun |
| Scope và giới hạn | [JSON CPU](reports/cpu_kernel_benchmark_20261020.json). Không tính I/O,feature structured mới,selectors,scorer/bootstrap/export hoặc model inference. ETA end-to-end=null |
| Tài nguyên | CPU được cho nhánh cache+feature nhẹ khi có inputs/code; model/LLM mới hoặc rerunQwen cần dự toán riêng. Không giả toàn bộ BEAR đã CPU-ready |
| Bước đo tiếp | 20query thật đại diện sau khi adapter/selector hoạt động;streamquery1worker trước/cachefeaturemộtlần cho các ablation |
| Ngân sách sơ bộ | 1–4giờ fullnhẹ/cacheđầyđủ là lịch dự phòng chưa kiểm, có thể vượt do scorer/memory;không gồm thời gian code và chuẩn bị data |
| Gain / tests | Relevance metrics mới=null. Không chạy lại63+10tests cũ;toolbenchmark đã được chạy thực thành công |
| Source và rollback | Không đổi corpus/models/beta/sourceMiro/legacy artifacts;package vẫn2.0.0 |

D07 tách **docs đúng hướng**, **inputs/code chưa ready** và **CPU kernel đã đo**. Không coi một CLI inventory hoặc microbenchmark tổng hợp là runBEARv3.3 thành công.

## 14. Chuẩn bị dùng máy GPU khác —20/10/2026

### D08 — Tách tài nguyên, dữ liệu và phần code còn thiếu

| Trường | Giá trị |
|---|---|
| entry_id / supplements_entry | D08 / D06, D07; giữ hướng BEAR retrieve doc/chunk |
| Nguồn | Người dùng sẵn sàng dùng máy GPU khác; chưa biết card/VRAM/RAM/OS, mô tả cấu hình ổn |
| Trạng thái | DOC_ONLY; không có GPU connection/model execution mới, hardware chưa kiểm |
| Tài liệu | [Readiness §7](reports/EXPERIMENT_READINESS_20261020.md#7-máy-gpu-đã-có-còn-thiếu-gì-và-ai-chuẩn-bị), PLAN, README, handover và config README |
| Dữ liệu cần bàn giao | Query, corpus, output control0,391, pool/score cache, policy/native chunk refs; một nguồn có thể đáp ứng nhiều role |
| Lý do | Có nội dung để tính evidence, doc thay thế để chọn, control/budget đúng để so và refs để xuất chunk nguyên văn |
| Trách nhiệm code | Agent triển khai adapter variable-k, structured evidence, Doc/Chunk selectors, runner/evaluator/export; không chuyển việc này thành yêu cầu người dùng cung cấp thuật toán |
| Nhãn | val.jsonl đã có, không bắt gán tay593câu; official ChunkF2/FINAL còn cần passage judgments/scorer đúng semantics |
| Tài nguyên | Tái dùng cache khi đủ; GPU dùng cho model mới hoặc cache thiếu. Không khóa A1 vào feature nhẹ chỉ vì local CPU |
| Môi trường/ETA | Kiểm backend/driver/dependencies/checkpoint khi vào máy; chưa ấn định VRAM/batch/thời gian. Smoke rồi20query thật trước full |
| Code/software/gain | Core vẫn2.0.0; không thêm runner/feature mới, không chạy benchmark relevance, metric mới=null |

D08 ghi nhận khả năng dùng GPU; không coi tài nguyên đã giải quyết các input/code gaps và không tự mở grid hoặc chạy lại pipeline từ đầu.

## 15. Thử BEAR thay từng khối retrieval —20/10/2026

### D09 — Baseline là control; mở nghiên cứu thay fusion/rerank/chunk/source

| Trường | Giá trị |
|---|---|
| entry_id / supplements_entry | D09 / D06–D08; giữ lịch sử và metric đã báo |
| Nguồn | Người dùng hỏi vì sao BEAR chỉ đánh giá trên baseline và đề nghị thử thay các phần retrieval |
| Nguyên nhân giới hạn cũ | Pilot selector tái dùng pool/scores để cô lập evidence; code cũ còn fixed200/laneVI. Chưa là bằng chứng BEAR không thay được tầng khác |
| Thiết kế | [BEAR_REPLACEMENT_STUDY](BEAR_REPLACEMENT_STUDY.md), PLAN/proposal3.4; software vẫn2.0.0 |
| Ưu tiên F1 | BEAR-only thay RRF/chọn top300VI trên union trước fusion; giữ source retrieval/ZH/downstream. RRF+evidence là residual ablation riêng |
| R1/C1/S1/J1 | R1thay Qwen/MaxP với control fixed-k thực; C1thay chunk cùng budget; S1cần corpus index/generator thật; J1đo ghép các phần có ích |
| Dữ liệu F1 cần thêm | Từng ranking nguồn trước fusion và union; doc mới cần Qwen cache hoặc inference đúng baseline, không điền score giả |
| Budget thí nghiệm | Stage studies tuần tự một candidate và control tương ứng; giới hạn3candidate của pilot D1/C1/DC1 vẫn áp dụng pilot đó, không là giới hạn toàn bộ nghiên cứu |
| Config / kiểm thực tế | [Inventory F1](configs/bear_doc_chunk/preflight_replacement_f1.template.json) qua CLIprovenance --dry-run; exit1/blocked_input; [report](reports/bear_replacement_f1_preflight_20261020.json) |
| Thiếu / hiện diện | Thiếu5roles: queries,corpus,predictions0,391,source rankings/candidatesZH,runtime/chunkpolicy; val.jsonl hiện diện |
| Kiểm tra tài liệu/config | JSON syntax và gitdiff whitespace được kiểm; không chạy lại coretests vì không đổi thuật toán |
| Trạng thái quality | Chưa triển khai scorer/index/runner mới, chạy relevance benchmark, upload hoặc submit. Gain mới=null |

D09 mở thiết kế thay khối theo yêu cầu; giữ phân biệt kiểm input thực tế với inference và quality evaluation. Không tuyên bố F1 tìm doc ngoài union hoặc S1 đã có retriever toàn kho.

## 16. Triển khai Retriever và Fusion độc lập —20/10/2026

### D10 — Hai phần có vai trò khác nhau, dùng chung index/scorer

| Trường | Giá trị |
|---|---|
| entry_id / corrects_entry | D10 / ưu tiên F1-trước, S1-để-sau của D09; giữ lịch sử |
| Yêu cầu | Người dùng đề nghị cả phần thay retrieval và phần thay RRF nếu không thừa; triển khai và cập nhật handover |
| Kết luận thiết kế | Không thừa: Retriever tìm độc lập từ corpus; Fusion chỉ xếp lại dedup union nguồn. Hai phần dùng chung index/evidence, không bắt chạy nối tiếp |
| Implementation | [corpus_index](bear/corpus_index.py), [structured_evidence](bear/structured_evidence.py), [retrieval](bear/retrieval.py), [evidence_fusion](bear/evidence_fusion.py), [runner](bear/parts_runner.py) |
| CLI/config | corpus-index, retrieve, evidence-fuse; [configs](configs/bear_parts/index.template.json); output candidates/evidence/diagnostics/manifest riêng |
| Phiên bản | Prototype corpus_parts_v1; legacy package/runner2.0.0 vẫn giữ nguyên fixed200 và compatibility cũ |
| Cơ chế thật | SQLite inverted index từ corpus; BM25 + phrase/entity evidence; binding subject/predicate/object khai báo cùng câu/thứ tự/polarity, span/availability rõ |
| Giới hạn | Chưa có parser quan hệ y sinh tự động/ngữ nghĩa đầy đủ; raw query dùng lexical fallback; VI mặc định, chưa chứng minh ZH recall. Generated window refs chỉ diagnostic, chưa là submission chunk selector |
| Đối chứng | B0 retrieval baseline+RRF; BR BEAR-Retriever thay đầu ra khối ứng viên VI; BF retrieval baseline+BEAR-Fusion thay RRF; cùng top-k/lang/corpus/downstream và nhánh ZH control |
| Kiểm chứng | 98/98 tests BEAR, gồm35 mới, +10/10 legacy; CLI được execute trên fixture; input/config/code/tamper/resume/WAL/malformed-source guards qua |
| Demo thực | [comparison](runtime/bear_parts/demo_two_parts_final_20261020/comparison.json): BR lấy c_outside ngoài union; BF không ra ngoài union và đổi thứ hạng RRF nhờ explicit relation |
| Dữ liệu thật | Dry-run các config mẫu blocked_input: corpus/query/index/source rankings chưa có ở paths chuẩn; artifacts baseline0,391 còn thiếu |
| Quality / side effects | Gain mới=null; không model/GPU inference, submit hoặc upload. Corpus nguồn chỉ đọc |
| Bàn giao | [Handover](TXT_handover.md), PLAN/proposal/algorithm/replacement study/runbook/spec được cập nhật phân biệt BR và BF; [báo cáo](reports/BEAR_PARTS_20261020.md) |

D10 triển khai phần mềm cho hai nghiên cứu riêng, không suy fixture thành metric thật hoặc tuyên bố toàn bộ BEAR doc/chunk đã hoàn tất.
