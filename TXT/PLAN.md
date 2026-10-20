# PLAN v3.3 — Xây BEAR chọn doc và chunk

Cập nhật20/10/2026 theo đính chính của người dùng. **Mục tiêu: thuật toán inference tạo doc set và chunks**, không dừng ở audit hoặc tuning threshold. Software hiện vẫn2.0.0; thiết kế mới `PROPOSED`, chưa được triển khai đầy đủ/đo gain trong lượt này.

## 1. Mục tiêu và thứ tự ưu tiên

Baseline [0,391](PIPELINE_0391.md) cung cấp corpus/query, ứng viên từ BM25/dense, ranks/score Qwen/MaxP/p̂ và policy xuất hiện có. BEAR bổ sung **Evidence Engine → Doc Selector → Chunk Selector**; output phải đi được tới submission.

Đặc tả thuật toán: **[BEAR_ALGORITHM.md](BEAR_ALGORITHM.md)**. [Proposal](TXT_Proposal.md) giải thích giả thuyết. Audit phục vụ kiểm feature; threshold/count tuning phục vụ operating point. Hai phần đó không thay mục tiêu doc/chunk retrieval.

## 2. Baseline và kết quả cũ

### 2.1. Baseline hiện hành

0,391 là baseline người dùng chọn; ảnh ghi300VI+40ZH trước rerank, threshold cho trung bình khoảng160doc/query. Chưa có full metrics/run/config hoặc policy output chunk đầy đủ; không tự điền từ w045/0,4076.

### 2.2. Bằng chứng cần giữ

L1/L4 trên0,4076 có best ΔDocF2+0.0003/+0.0004, CI95 chạm0/âm theo báo cáo. Giữ nguyên [bảng kết quả](reports/L1_L4_20261020.md); không chạy lại uniform coverage chỉ vì đổi baseline. Kết quả đó chưa bác bỏ mọi thuật toán evidence hoặc chunk retrieval.

N0/N1 của w045 đã được báo chạy1200câu/parity100%/trung bình5,5doc đổi; không làm lại như prerequisite. Full-body chunk của0,4076 không tự là policy0,391.

### 2.3. Baseline phải bảo toàn

Dùng đúng prediction, candidates, corpus/query snapshot, score/precision/ties, `k_q` thực và native chunk policy của0,391. Bypass BEAR phải trả đúng doc/chunk baseline. Đối chiếu input này không phải dựng lại toàn bộ w045.

## 3. Kiến trúc và output

`retrievers/reranker baseline → structured local evidence → BEAR doc set + BEAR chunk refs → exporter`.

Pilot tái dùng pool đang có; chưa tuyên bố tìm doc ngoài pool. Ghi rõ scope VI hay đa ngôn ngữ. Mỗi run xuất `selected_docs`, `selected_chunks`, availability/fallback và per-query metrics, không chỉ một report giải thích.

### 3.3. Giới hạn ghi

Mọi thay đổi mới trong TXT; legacy, corpus, nhãn nguồn và completed runs chỉ đọc. Runtime dự kiến `TXT/runtime/bear_doc_chunk/<run_id>/`, chưa được tạo trong lượt sửa docs. Không tự upload hoặc tải model mới để lấp phần thiếu input.

## 4. Thuật toán cần xây

- **Query representation:** entity/identifier, quan hệ/intent và điều kiện có span/mapping/availability.
- **Evidence:** support/conflict trong cùng ngữ cảnh, khác đếm entity uniform; conflict không suy từ thiếu từ khóa hoặc nhắc thực thể khác ở đoạn không liên quan.
- **Doc selector:** điểm nền kết hợp evidence hợp lệ để thay tập doc; pilot giữ k từng query nhằm cô lập chất lượng doc.
- **Chunk selector:** chọn chunk/window nguyên văn dưới cùng slots/token budget; feature ref phải nối tới chunk thực xuất.
- **Fallback:** thiếu extractor/mapping thì giữ baseline ở scope khai báo; missing khác0, không tự loại doc thiếu feature.

Công thức, scope D1-VI và matrix B0/D1/C1/DC1 ở [đặc tả](BEAR_ALGORITHM.md). Không coi parser quan hệ, conflict scorer hoặc hệ số đã tồn tại chỉ vì có tên trong tài liệu.

## 5. Dữ liệu và mức sẵn sàng

Cần đúng inputs cho phần đang làm: query/doc/native chunk refs; source/reranker/p̂ scores; output/budget baseline; nhãn BTC đúng snapshot để chấm. Không buộc nhận đủ14roles của recipe w045. D1/C1 có dependencies riêng, không bắt một nhánh chờ nhánh kia nếu đã đủ input.

### 5.3. Error codes và thiếu input

Giữ `INPUT_MISSING/HASH_MISMATCH/SCHEMA_INVALID/BASELINE_PARITY_FAILED/FEATURE_UNAVAILABLE/LABEL_COVERAGE_INSUFFICIENT/EVALUATOR_UNVERIFIED/OUTPUT_OUTSIDE_TXT` theo code hiện có. Chỉ rõ file/scope thiếu; không giả hash, annotator, score, parser output hoặc judgments.

## 6. Hợp đồng ID, chunk và nhãn

Giữ namespace và score/rank gốc trước restrict pool. Chunk nguyên văn `body[start:end]`, offsets Unicode end-exclusive, cùng corpus/body/text hash. Không dùng body.find để chứng nhận đoạn lặp. Window mới cần provenance riêng.

Judgments chỉ dùng train/dev/evaluation theo protocol, không đọc đáp án để chọn doc/chunk riêng từng query khi inference. Unknown không là negative; chunk-derived not_gold có thể âm giả. Coding agent không tự gán relevance y khoa. Chi tiết compatibility cũ: [PLAN v2 §6](archive/PLAN_v2_before_pivot_20261020.md#6-hợp-đồng-dữ-liệu-và-provenance).

## 7. R0 compatibility giữ riêng

Code baseline.py vẫn phục vụ B00/w045, fingerprints `c1e068422e5f/fd07f9fc029a`,200doc/query và allocation/calibration8 cũ; [recipe exact](archive/PLAN_v2_before_pivot_20261020.md#7-r0-compatibility-và-rollback). Không dùng exporter đó mặc định cho0,391.

## 8. Giả thuyết BEAR

### 8.1. H_doc

Một tín hiệu y sinh có cấu trúc, ngoài baseline score và uniform coverage, giúp chọn **tập doc** đúng hơn trong cùng pool/budget. Thứ tự thay đổi mà tập doc không đổi chưa tăng DocF2.

### 8.2. H_chunk

Cùng doc set/order/slots, evidence chọn được chunk liên quan hơn selector baseline. Nếu không có lựa chọn khác dưới cùng budget thì ghi không có headroom, không bắt tăng số chunk/text.

### 8.3. Protected matcher

Giữ dấu/số/boundaries; BRCA1≠BRCA10, type1≠type2, mg≠mcg. Alias/type/intent cần nguồn kiểm; không mặc định extractor hiểu quan hệ. Evidence là feature inference cần kiểm, không tự là gold.

## 9. Đối chứng và ngân sách

| Run | Doc | Chunk | Mục đích |
|---|---|---|---|
| B0 | Baseline | Baseline | Control |
| D1 | BEAR | Baseline policy | Cô lập doc selection |
| C1 | Baseline set/order | BEAR, cùng budget | Cô lập chunk selection |
| DC1 | BEAR | BEAR | Kiểm tương tác/output cuối |

Tối đa3candidate mới và1control cho một thiết kế pilot đã khóa, không thêm weight grid cùng lúc. Mỗi selector chỉ thử một feature/cơ chế có cấu trúc và một config đã khai báo. Khóa scope và selection budget trước khi chấm.

D1-VI có thể giữ non-VI baseline và số VI baseline để cô lập evidence khi ZH alias chưa đủ; đây là đối chứng chủ đích, không phải khẳng định baseline có quota cuối. Đa ngôn ngữ mở khi mapping/score đủ.

Threshold-only study của v3.2 chuyển thành đối chứng phụ/operating-point tuning sau hoặc ngoài ablation chính. Không gọi tuning threshold là toàn bộ BEAR.

## 10. Đánh giá hai tầng

- **D1:** paired DocF2 cùng query universe; report tập doc thêm/bớt, scope applied/fallback và CI. Nếu chỉ đổi order, nói rõ không có doc-set gain.
- **C1:** giữ doc set/order/slots/text budget, chấm chunk bằng scorer đúng semantics. Local LCS chỉ là diagnostic nếu tokenizer/spec chưa official-equivalent.
- **DC1:** đo doc/chunk và FINAL thật; không suy FINAL từ ΔDoc, không quy gain do tăng slots cho selector.
- BTC val được dùng offline; không bắt gán tay lại593câu. 205dòng/tổng305 bất nhất số đếm không xác định ID lỗi;±0.0002 không phải bound.
- Khi k giữ nguyên, ΔDocF2 phụ thuộc judged added/removed; nếu k đổi thì cần hits control và sensitivity cả doc giữ nguyên. [Evaluator contract](reports/EVALUATOR_CONTRACT.md) giữ công thức.
- 593câu đã khai thác không là holdout mới. Freeze candidate trước tập thật chưa xem nếu có; CI không sửa nhãn sai/selection bias.

Promotion cần gain đáng tin trong scope đúng, CI/sensitivity phù hợp và package hợp lệ; chưa đủ thì giữ0,391. Một nhánh có thể được giữ nếu thắng độc lập dù joint không thắng.

## 11. Công việc triển khai tiếp — A0 đến A4

| Bước | Việc cụ thể | Điều kiện xong |
|---|---|---|
| **A0 — Baseline adapter** | Nối candidates/scores/native chunks/budget với0,391; bypass trả đúng output gốc | Có control doc/chunk và policy thực, không config giả |
| **A1 — Evidence có cấu trúc** | Chọn một loại support/conflict có span/role mapping; phân biệt unknown/no-match và fallback | Có feature tính được trên dữ liệu thật cùng availability; không trả list rỗng rồi coi detector xong |
| **A2 — Doc retrieval** | Tích hợp evidence vào score/rank và chọn lại doc theo budget pilot; xuất selected_docs | D1 thật, thay doc được ghi nhận; không chỉ report/audit |
| **A3 — Chunk retrieval** | Tích hợp evidence vào chọn native chunks/windows, giữ slots/budget; nối exporter | C1 thật và selected_chunks xuất đúng ref/text |
| **A4 — Joint và đánh giá** | Chạy B0/D1/C1/DC1 trong phạm vi đủ inputs; đo riêng hai tầng và joint | Có metric/sensitivity/decision và artifact có thể review |

A2/A3 có thể triển khai độc lập sau phần A0/A1 cần thiết; A4 joint chỉ mở khi cả hai selector hoạt động. Kiểm thử khi sửa code phải kiểm lựa chọn doc/chunk thật, bypass/fallback, mapping và export; tests fixture không chứng minh gain.

## 12. Code hiện có và gap

Package2.0 có matcher/evidence uniform, fusion và C1/C2 scaffolding. Cần bổ sung feature cấu trúc/quan hệ và adapter/scope0,391; một số evaluator/exporter vẫn fixed200/reviewed-qrels. Chưa có runner đầy đủ theo BEAR_ALGORITHM. Root val_calib có MaxP/beta8/10 nhưng chưa liên kết run, không tự refit.

**Chuẩn bị20/10:** [readiness report](reports/EXPERIMENT_READINESS_20261020.md) ghi preflight A0 thật còn5input roles thiếu. [Config inventory](configs/bear_doc_chunk/preflight_0391.template.json) được CLIprovenance hiện có nhận, không là config inference mới.

**CPU-first có điều kiện:** tái dùng scores/embeddings đã cache, chọn feature cấu trúc nhẹ có availability rõ; xử lý theo query/shard và cache evidence một lần cho B0/D1/C1/DC1. Nếu A1 cần LLM trích quan hệ mới hoặc rerunQwen thì tài nguyên/ETA tính riêng. [Benchmark CPU](reports/cpu_kernel_benchmark_20261020.json) đo kernel cũ; khi adapter/selector có thật, đo20query đại diện trước full run. Không dùng synthetic kernel làm ETA end-to-end.

**Máy GPU khác đã được người dùng cho biết có thể dùng:** không giới hạn thiết kế A1 vào rule nhẹ chỉ vì máy local. Chọn cơ chế có thể kiểm chứng theo mục tiêu evidence; nếu cần model thì bổ sung inference/cache trên máy GPU, không mặc định gọi lại toàn baseline. Chưa biết phần cứng hoặc checkpoint nên chưa có batch/ETA. [Checklist GPU và inputs](reports/EXPERIMENT_READINESS_20261020.md#7-máy-gpu-đã-có-còn-thiếu-gì-và-ai-chuẩn-bị) nêu phần lấy từ máy baseline và phần code agent cần viết; thứ tự A0–A4 giữ nguyên.

## 13. Bước bắt đầu

Đọc README →pipeline →BEAR_ALGORITHM →proposal →PLAN →handover. Tiếp tục A0/A1 từ input có thật, không bắt làm lại N0/N1 hoặc gán tay toàn tập. Thiếu input phần nào ghi scope đó, vẫn làm phần độc lập.

## 14. Trạng thái và lịch sử

Đích hoàn tất là thuật toán tạo doc/chunk và kết quả đối chứng; audit/threshold study đơn lẻ chưa đạt đích. Lượt này chỉ sửa đặc tả, chưa gọi A0–A4 hoàn thành hoặc tăng điểm.

[PLAN3.2 đã thay](archive/PLAN_v3_2_before_doc_chunk_restore_20261020.md), [log D06](improvement_log.md), [decisions](reports/DECISIONS.md). Các mục §2.3/§3.3/§5.3/§6/§7/§8.3 giữ nghĩa compatibility cho code.
