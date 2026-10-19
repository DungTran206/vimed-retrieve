# TXT handover — Tiếp quản và chạy Biomedical Evidence-Aware Retrieval (BEAR)

> **BEAR2.0.0 đã triển khai:** dùng [v2 runbook](configs/next_round/README.md) và [báo cáo nghiệm thu kỹ thuật](reports/next_round/V2_IMPLEMENTATION.md). N0 inventory đã chạy và blocked_input; N1–N5 backend có fixtures, chưa benchmark thật; adaptive giữ guard.

> Cập nhật: **19/10/2026**. Đây là điểm bắt đầu cho AI tiếp quản nhánh `TXT/`.
>
> Mục tiêu: hiểu baseline cũ, phần BEAR đã làm, điều kiện chạy từng bước, cách đọc kết quả và việc cần làm tiếp. Tài liệu này mô tả **code đang có**, phân biệt với phần mới chỉ được đề xuất.
>
> **Kết quả mới do người dùng báo cho bài TXT/BEAR: FINAL `0.3445`, Doc F2 `0.3612`, Chunk F2 `0.3279`.** So với `w045_TF` ngày 15/10, FINAL tăng `0.0003`, Doc F2 tăng `0.0007`, Chunk F2 giữ nguyên ở độ chính xác hiển thị. Đây là kết quả server **REPORTED**; chưa có run/config/hash tương ứng trong checkout để phân tích cơ chế tạo gain.
>
> **Trạng thái kỹ thuật local:** code CPU đã được kiểm bằng fixtures; các báo cáo readiness/ledger có sẵn là snapshot trước kết quả mới. Vòng tiếp theo bắt đầu bằng nối provenance và audit mức áp dụng thực tế; reuse baseline đã verified nếu có, chỉ tái lập R0 khi cần. [PLAN v2.0](PLAN.md) là nguồn giao việc, dependency và nghiệm thu N0–N5 hiện hành; [proposal](TXT_Proposal.md) giải thích giả thuyết, handover này hướng dẫn vận hành, [improvement_log.md](improvement_log.md) giữ lịch sử.

## 1. AI nhận việc cần đọc gì?

Đọc theo thứ tự sau; đường dẫn trong lệnh luôn tính từ **repo root**.

| Thứ tự | Tài liệu | Cần nắm |
|---|---|---|
| 1 | File handover này | Trạng thái thực tế, chuỗi chạy, điều kiện chuyển bước và xử lý kết quả. |
| 2 | [improvement_log.md](improvement_log.md) | Lịch sử kết quả TXT/BEAR, so sánh mốc 15/10, giới hạn bằng chứng và các lần cập nhật kế hoạch. |
| 3 | [TXT_Proposal.md](TXT_Proposal.md) | Vì sao thử từng hướng: H1–H6, evidence, fixed controls, routing, chunk và thiết kế đánh giá. Ưu tiên các mục 2, 5, 7–13, 17–18. |
| 4 | [PLAN v2.0](PLAN.md) | Làm gì tiếp: nguồn hiện hành cho task N0–N5, dependency và acceptance. Đọc mục 1–10; dùng mục 11 để chọn task đủ điều kiện. |
| 5 | [IMPLEMENTATION_STATUS.md](reports/IMPLEMENTATION_STATUS.md), [KNOWN_LIMITATIONS.md](reports/KNOWN_LIMITATIONS.md), [RESULTS.md](reports/RESULTS.md) | Snapshot kỹ thuật T01–T16: phần code đã kiểm bằng fixture, dữ liệu còn thiếu và chức năng chưa triển khai; không phải trạng thái hoàn tất N0–N5. |
| 6 | [HANDOVER cũ](../doc/HANDOVER.md), [CLAUDE.md](../doc/CLAUDE.md) | Baseline w045, pipeline cũ, dữ liệu cần nhận, scoring, định dạng nộp và các quy định dự án đã ghi nhận. |
| 7 | [EVALUATOR_CONTRACT.md](reports/EVALUATOR_CONTRACT.md), [DECISIONS.md](reports/DECISIONS.md), [RUNBOOK.md](reports/RUNBOOK.md), [DATA_READINESS.md](reports/DATA_READINESS.md) | Phân biệt evaluator/proxy, quyết định kỹ thuật, lệnh hiện có và input còn thiếu. |
| Khi cần | [PROGRESS.md](../doc/PROGRESS.md), [METHODS.md](../doc/METHODS.md), [PIPELINE.md](../doc/PIPELINE.md), [SETUP.md](../doc/SETUP.md) | Lịch sử số đo, các hướng đã thua, kiến trúc và môi trường cũ. Đọc mục có ngày/đính chính liên quan, đặc biệt quanh 12–15/10. |
| Tham khảo lịch sử | [BIOMEDICAL_ADAPTIVE_RETRIEVAL_AGENT_PLAN.md](BIOMEDICAL_ADAPTIVE_RETRIEVAL_AGENT_PLAN.md) | Plan ý tưởng đời trước; không lấy CLI/layout hoặc câu micro F2 trong đó thay hợp đồng mới. |
| Tham khảo hợp đồng cũ | [PLAN trước N0–N5](archive/PLAN_before_N0_N5_20261019.md) | Bản lưu nguyên trạng kế hoạch T01–T16 và các hợp đồng chi tiết; dùng tra lịch sử triển khai, không chọn task vòng mới từ checklist bootstrap cũ. |

**Cách giải quyết mâu thuẫn:** yêu cầu người dùng → hành vi code thực tế và artifact có nguồn gốc → trạng thái triển khai mới → PLAN v2.0 cho task/dependency/nghiệm thu, proposal cho giả thuyết/phương pháp → tài liệu lịch sử. Khác biệt về kết quả phải kiểm tra provenance, không chỉ chọn con số cao hơn.

Những câu như “chưa có package BEAR”, “phiên này chỉ lập kế hoạch” trong [PLAN đã lưu](archive/PLAN_before_N0_N5_20261019.md) và tài liệu cũ mô tả thời điểm soạn chúng. Package hiện đã có; PLAN v2.0 đặt công việc N0–N5 trên nền code đó. `reports/RESULTS.md`, `IMPLEMENTATION_STATUS.md` và ledger cũ chưa phản ánh kết quả server mới: đọc chúng để biết phần code được kiểm tại thời điểm ghi, không dùng câu “fixture-only/chưa có kết quả thật” trong đó để phủ nhận kết quả TXT/BEAR người dùng đã báo. Các tài liệu cũ nhắc `HANDOVER.md`, `CLAUDE.md` ở root thì tìm trong `doc/`.

## 2. Bài toán và hướng BEAR hiện tại

Với mỗi query tiếng Việt, hệ thống chọn document và các đoạn trích y sinh từ corpus đa ngôn ngữ. Baseline đã có BM25, dense, Qwen reranker, nhánh ZH và chunk allocation. BEAR tận dụng các artifact đó, thêm **bằng chứng khớp thuật ngữ/điều kiện y khoa** để thử cải thiện việc chọn document hoặc chunk.

Chuỗi nghiên cứu cần giữ:

```text
N0 Provenance của kết quả mới + baseline parity sẵn có hoặc tái lập khi cần
  → N1 Audit feature coverage, mức áp dụng, fallback và thay đổi doc set
  → N2 Fixed body/local evidence; N3 C1 rồi C2 trên nhánh chunk độc lập
  → N4 F0 đã verified B/D, rồi O0/H3 và controls; adaptive chỉ khi qua gate
  → N5 Chọn candidate hoặc tổ hợp trên dev, freeze, một lần holdout
  → Full features + inference + integrity; package/nộp theo yêu cầu

Nhánh riêng có điều kiện: chunk C1/C2/C3, sparse S1/S2, alias/discovery.
```

- **Evidence trước:** đo entity có đúng identifier, có cùng đoạn, có critical terms hay không. Coverage cao chưa chứng minh trả lời đúng; matcher hiện chưa hiểu phủ định/quan hệ/intent.
- **Fixed trước adaptive:** trước hết kiểm tra evidence có ích ngoài baseline rank không. Chỉ mở gate khi E(q) dự báo được lợi thế lexical so với semantic và adaptive thắng best fixed công bằng.
- **Không bắt buộc adaptive thắng:** giữ fixed, chỉ cải thiện chunk, hoặc kết luận chưa đủ bằng chứng đều là kết quả hợp lệ.
- **Không dùng p(gold), cosine, Qwen confidence, lexical coverage hoặc điểm leaderboard tổng hợp làm qrels.**

Ba phạm vi phải phân biệt:

| Phạm vi | Can thiệp | Metric/giới hạn |
|---|---|---|
| P200 | Sắp lại cùng 200 doc baseline | Doc F2 theo tập không đổi. Primary local mặc định P@40; chunk có thể thay đổi do thứ tự. |
| PLARGE | Chọn 200 từ pool lớn hơn, mặc định cap 400 | Có thể thay doc set. Primary mặc định paired ΔP@200 khi judged đủ mọi added/removed. |
| PNEW/discovery | Tìm candidate ngoài nguồn/pool hiện có | Chưa mở; cần bằng chứng pool hiện tại là điểm nghẽn và study riêng. |

V1 chỉ sort/select **VI lane**, giữ nguyên vị trí và doc của non-VI baseline. Không suy selection gain VI thành gain ZH hoặc FINAL. `pool_v1.json` hiện chọn **PLARGE**, không phải P200.

## 3. Baseline cũ và cách chấm cần kế thừa

### 3.1. Baseline lịch sử và kết quả TXT/BEAR mới

| Thuộc tính | Giá trị bàn giao — REPORTED |
|---|---|
| Run/ngày | `w045_TF`, 15/10/2026 |
| Doc F2 / Chunk F2 / FINAL | `0.3605 / 0.3279 / 0.3442` |
| Doc precision / recall | `0.1884 / 0.6047` |
| Chunk precision / recall | `0.1931 / 0.4573` |
| Legacy doc fingerprint | `c1e068422e5f` |
| Legacy chunk fingerprint | `fd07f9fc029a` |
| Kích thước submission | Đủ query ID 1–1200; 200 doc/query |
| Corpus/chunk | Đúng `corpus_new.sqlite` đã clean, chunk bằng offset, khoảng 900 token |
| Calibration | **`scripts/val_calib.py` và beta 8 hệ số của snapshot** |

Nguồn baseline: [doc/HANDOVER.md](../doc/HANDOVER.md) và các mục w045/T2/TF trong [doc/PROGRESS.md](../doc/PROGRESS.md), quanh dòng 2623–2631. w045_TF giữ nguyên tập doc w045, nên kế thừa doc precision/recall trên.

| Chỉ số | w045_TF 15/10 — REPORTED | TXT/BEAR mới — REPORTED | Δ tuyệt đối |
|---|---:|---:|---:|
| FINAL | 0.3442 | 0.3445 | +0.0003 |
| Doc F2 macro | 0.3605 | 0.3612 | +0.0007 |
| Chunk F2 macro | 0.3279 | 0.3279 | 0.0000 |
| Doc precision | 0.1884 | 0.1886 | +0.0002 |
| Doc recall | 0.6047 | 0.6065 | +0.0018 |
| Chunk precision | 0.1931 | 0.1926 | −0.0005 |
| Chunk recall | 0.4573 | 0.4585 | +0.0012 |

Người dùng xác nhận đây là điểm bài TXT/BEAR. Chấp nhận attribution này; phần cần nối ở N0 là ID bài/run, config/code/input hashes, phạm vi query và scoring output. Gain hiển thị đến từ document; chunk đang đổi precision lấy recall và chưa tăng F2. Chưa có per-query comparison để khẳng định gain ổn định, hoặc quy gain cho H1/H2/H3 hay một cơ chế cụ thể. Nếu cùng scorer/query set và 200 doc/query, chỉ đổi thứ tự cùng tập doc không tạo doc F2 gain.

`TXT/manifests/baseline.json` trong snapshot local cũ là `not_reproduced`, `observed_metrics=null`, `observed_fingerprints=null`; nó chưa được cập nhật từ run mới. Nếu đã có baseline artifact verified đúng snapshot/hashes thì reuse và ghi nguồn; chỉ chạy lại R0 khi artifact thiếu, parity chưa xác minh hoặc có mismatch. Tái tạo đúng fingerprint xác nhận artifact parity; không có nghĩa đã chạy lại server và đo lại điểm leaderboard. Không gán fingerprints w045 cho run TXT/BEAR mới.

Legacy chunk fingerprint chỉ hash text theo thứ tự, không gồm doc_id/offset; vì vậy luôn kiểm integrity/provenance cùng fingerprint, không dùng hash đó thay toàn bộ validation.

**Recipe R0 trong code hiện tại:**

1. Đọc VI base `c_blendQB8` và VI alt `c_blendQB8w05`.
2. Mỗi model ZH lấy top-400 từ vi-query và zh-query; thay cả row các query có trong patch `zhq109`.
3. RRF bốn nguồn ZH, trọng số BGE `1/1`, Qwen8B `0.3/0.3`, `k=60`, top-1000; lọc membership kho mới.
4. RRF VI base `1` với ZH `0.45` → deep list. Chọn tập top-200; head tối đa 120 lấy theo VI alt top-240 giao tập đó.
5. Lọc membership, giữ ngoại lệ domain chính xác `vinmec.com`; refill từ deep cho đủ 200.
6. Tính p bằng beta đóng băng; calibration dùng ZH BGE vi/zhq **gốc**, không thay bằng patch109. Làm tròn p 4 chữ số trước áp ngưỡng.
7. Top-40 tối đa 2 chunk/doc; hạng 41–120 tối đa 1 chunk đầu. Top-120 có `p < 0.04` bỏ chunk, giữ doc; hạng 121–200 có `p >= 0.05` thêm 1 chunk đầu.
8. Build records, kiểm offsets/IDs/provenance và cả hai fingerprint. Mặc định chưa nén ZIP.

Ở top-40, khi có hơn 2 chunk và có scores thì chọn 2 chunk tốt nhất, xuất lại theo thứ tự chunk; khi thiếu điều kiện thì lấy chunk đầu. Đừng hiểu nhầm mọi tầng đều chọn chunk tốt nhất theo Qwen. Chi tiết rounding, tie, calibration và selector ở `TXT/PLAN.md` §7 và `TXT/bear/baseline.py`.

**Hai bẫy legacy:**

- Không dùng root `val_calib.py` thay bản `scripts/`: root có MaxP và các thử nghiệm mới hơn; không refit hoặc chạy `--extract/--logit` khi tái lập.
- Handover cũ ghi `bash build_best.sh`, nhưng file nằm ở `scripts/build_best.sh`. Script còn `cd` vào `scripts/` trong khi nhiều đường dẫn giả định repo root. **Không chạy nguyên xi để vận hành TXT; dùng `TXT.bear.cli reproduce`.** Giữ script làm nguồn recipe, không cần sửa pipeline cũ.

### 3.2. Metric và ba tầng evaluator

- Với từng query: `Doc F2 = 5*g / (4*G + k)`, g là số doc đúng đã chọn, G là số gold, k là số doc chọn. Macro là trung bình F2 từng query, không phải F2(mean P, mean R).
- Cùng tập 200 doc, đổi thứ tự không tăng Doc F2. Thứ tự vẫn ảnh hưởng tầng chunk.
- FINAL lịch sử được ghi nhận là `(Doc F2 + Chunk F2)/2`.
- `submit/score.py` chỉ là **legacy proxy**, không scorer chính thức. Local whitespace token LCS trong TXT chỉ là diagnostic; chưa gọi `official_chunk_f2`.
- Với passage diagnostic, phải cùng qid/doc và `LCS(pred_tokens,gold_tokens)/len(gold_tokens) >= 0.40`. Chưa có đủ tokenizer/normalization/duplicate/aggregation semantics để chứng nhận tương đương official.
- Nhãn chưa đủ không mặc định là grade 0. Full-corpus Recall/F2 cần gold universe đầy đủ; top-K hoặc differences labels chỉ cho phép metric đúng phạm vi đó.

### 3.3. Ba ZIP ở root không phải baseline đã tái lập

`scoring_result.zip` có kết quả **ARTIFACT_OBSERVED**, provenance `runtime_observed_unlinked`:

| Quan sát | Giá trị |
|---|---|
| Query trong archive / có gold để tính macro | 600 / 593 |
| Doc F2 / Chunk F2 / FINAL hiển thị | `0.407343155932693 / 0.3378781929969602 / 0.3726` |
| Runtime config | LCS/gold tokens 0.4; duplicate threshold 0.8; empty gold excluded |
| Tokenizer path được runtime ghi | `/app/program/tokenizer.json`, chưa có trong checkout |

Chưa xác minh archive này thuộc bài nộp nào hoặc liên kết với w045. Không đổi baseline 0.3442 thành 0.3726; không lấy feedback làm qrels/inference features. `best_gold_chunk_id` không cung cấp gold passage text. Tên `unknown_doc` trong diagnostics chưa đủ để suy semantics.

`prediction_result.zip` chứa `metadata` và `x12m_ext10.json`; `x12m_ext10.zip` chứa một JSON. Entry JSON khoảng 717 MB chưa nén. Nếu kiểm tra, đọc theo luồng, chọn đúng entry và xác minh hash/provenance; không `json.load` toàn entry chỉ để xem schema. Wrapper archive có metadata không phải ZIP một JSON dùng để nộp.

## 4. Phần đã làm và bản đồ code để tiếp tục

| Nhóm | File dưới `TXT/bear/` | Trạng thái sử dụng |
|---|---|---|
| CLI/config/I/O | `cli.py`, `config.py`, `contracts.py`, `io.py`, `artifacts.py` | Có validate, output boundary, atomic writes và hash/resume. |
| Audit/adapters | `audit.py`, `adapters.py` | Có inventory và native SQLite/chunk refs; adapter external dense-index→native-offset còn thiếu. |
| R0 | `baseline.py`, `reproduce.py` | Có recipe CPU; calibration/chunk parity qua fixture, chưa qua snapshot thật. |
| Pool/evidence | `pools.py`, `matching.py`, `evidence.py`, `features.py` | Có PLARGE/P200, protected exact matcher, features/shards/L0 và inference. Chưa đo RAM/I/O thật, chưa có global IDF. |
| Experiment/evaluation | `fusion.py`, `experiments.py`, `tuning.py`, `evaluation.py`, `evaluate_runner.py`, `paired.py` | Có L1/F0 orchestration, annotation export, reviewed labels, paired bootstrap, freeze/holdout guards. |
| Chunk | chunk_experiments.py, chunk_study.py, chunk_evaluation.py | Code2.0 có C1/C2 study/local diagnostic, freeze refs và export selected chunks; C3 chưa mở |
| Release | `integrity.py`, `release.py` | Có technical validation/package; chưa xuất release thật hoặc promote. |

Ledger T01–T16 trong `reports/IMPLEMENTATION_STATUS.md` là snapshot tiến độ triển khai trước kết quả mới; đối chiếu với run thực trước khi cập nhật status. Hợp đồng/task T01–T16 gốc được giữ trong [PLAN đã lưu](archive/PLAN_before_N0_N5_20261019.md); công việc vòng tiếp theo dùng N0–N5 trong [PLAN v2.0](PLAN.md), không chuyển trạng thái fixture cũ thành nghiệm thu vòng mới. Adaptive nonzero hiện bị CLI runner chặn dù pure gate logic đã có. Sparse encoder/CLI, discovery, document gate và SPLADE chưa được triển khai để chạy production. Không tự tạo CLI giả hoặc đánh dấu toàn PLAN đã xong.

Lần triển khai nền ghi nhận48/48BEAR và10/10legacy tests. Code2.0 đã chạy **63/63BEAR +10/10legacy**, gồm15tests v2; vẫn chỉ fixture/logic, chưa relevance benchmark. Code/config/test identities mới ở `TXT/manifests/code_inventory_v2.json`; inventory cũ giữ làm lịch sử.

## 5. Quy tắc vận hành trước mọi lần chạy

1. Mọi file mới, input nhận thêm, config, cache, temp, báo cáo, run và submission nằm dưới **`TXT/`**. Input legacy ngoài TXT chỉ đọc. Không ghi vào `TXT/inputs/` bằng job output.
2. Không sửa body, clean/rechunk, thêm index/migrate SQLite, crawl lại hoặc refit beta để bù snapshot thiếu. Nhận bản SQLite nhất quán, không đang có writer/WAL; code có guard WAL. Không tự checkpoint nguồn để lách guard.
3. Kiểm tra `git status` và `AGENTS.md` nếu có. Snapshot lúc bàn giao đã có staged rename tài liệu root→`doc/`, `TXT/` và root `val_calib.py` chưa track; giữ nguyên thay đổi của người dùng.
4. Internal doc IDs là chuỗi số chuẩn; submission JSON phải là **integer IDs**. Chunk text là nguyên văn `body[start:end]`, offset Python Unicode; không viết lại hoặc tự gộp/cắt boundaries trong experiment khác.
5. `null` là unavailable, coverage 0 là đã quan sát không match. `not_retrieved`, `not_scored`, thiếu artifact và mapping lỗi cần phân biệt. Không thay tất cả bằng 0.
6. `best_idx` từ dense ngoài không tự bằng `chunk_id`, `ord` hoặc exporter index. Chỉ dùng sau khi mapping offsets/hash đã verified.
7. Không tự tải model hoặc chạy job GPU/full-corpus khi cached artifact đủ. Theo quy định dự án trong `doc/CLAUDE.md`, pipeline thi/gán nhãn có giới hạn mô hình mở, tham số và ngày phát hành; không dùng coding AI này làm nguồn gold. Khi cần xác nhận luật hiện hành, dùng nguồn BTC.

Thiết lập PowerShell từ repo root:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TEMP = Join-Path (Get-Location) 'TXT/runtime/tmp'
$env:TMP = $env:TEMP
$env:TMPDIR = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
python -B -m TXT.bear.cli --help
```

CLI tự trỏ model/temp cache vào `TXT/runtime/`. Tests chạy riêng cần thiết lập temp như trên. Dùng `-B` để import legacy không sinh `__pycache__` bên ngoài TXT. Nếu cần môi trường mới, đặt ở `TXT/.venv/`, cache pip/uv dưới `TXT/runtime/cache/`; không tự cài toàn `requirements-train.txt`. R0 cần NumPy; đọc membership parquet cần pandas/pyarrow. Không cần GPU để ghép cached rankings.

Các job `reproduce/pool/sample/features/run/tune/annotation-export/export` mặc định dry-run, muốn chạy phải có `--execute`. **`audit`, `evaluate`, `compare`, `freeze` không có cơ chế dry-run này**: audit ghi inventory/report, evaluate/compare chấm ngay, freeze ghi frozen artifact. `--help` mới chỉ xem giao diện.

## 6. Cần nhận dữ liệu nào và sửa config ra sao?

Snapshot readiness trước kết quả mới ghi `data/` chỉ có `.gitkeep`, thiếu **22 logical roles**; recipe R0 riêng cần **14 roles**. Kiểm lại artifact/run đã dùng cho bài TXT/BEAR trước khi lập danh sách thiếu hiện tại. Không mặc định phải nhận lại mọi input hoặc chạy lại baseline. Không chờ đủ qrels/tokenizer mới chạy R0 nếu việc tái lập cần thiết, và không hiểu global audit còn blocked là mọi công đoạn đều bị chặn.

Nhận snapshot vào `TXT/inputs/handover/data/`, giữ cây tương đối như gói cũ:

| Vai trò | Đường dẫn tương đối trong `data/` | Dùng cho |
|---|---|---|
| `corpus` | `corpus_new.sqlite` | Body/lang/domain/chunk offsets; snapshot cũ khoảng 5.5 GB |
| `vi_base`, `vi_alt` | `rp/c_blendQB8.jsonl`, `rp/c_blendQB8w05.jsonl` | VI recipe |
| `zh_bge_vi/zh/patch` | `dense_zhC3_vi_rank.jsonl`, `dense_zhC3_zhq_rank.jsonl`, `dense_zhC3_zhq109_rank.jsonl` | ZH BGE |
| `zh_q8_vi/zh/patch` | `dense_zhQ8_vi_rank.jsonl`, `dense_zhQ8_zhq_rank.jsonl`, `dense_zhQ8_zhq109_rank.jsonl` | ZH Qwen8B |
| `membership` | `vibiomir_new/links_corpus_vi_en_zh.parquet` | Kho được phép của snapshot |
| `chunk_scores` | `chunk_scores_mix.jsonl` | Legacy chunk selector |
| `qwen_doc_scores`, `chunk_dense` | `qwen_all_h.jsonl`, `dense_chunk_full_rank.jsonl` | Frozen calibration |
| `beta` | `val/beta.json` | Đúng 8 hệ số, không fit lại |

Đó là 14 roles R0. Bổ sung theo bước sau:

- `queries.jsonl`, `queries_enriched.jsonl`: sampling/concepts/L0; xác minh query snapshot và parse/translation provenance.
- Lexical/dense source artifacts kèm source manifests: cần cho B-family/D-family, support E(q), F0/A1. Không coi `c_blendQB8` là lexical hoặc dense thuần.
- Qrels reviewed và passage refs dưới `TXT/inputs/evaluation/`: local evaluation. Official tokenizer/scorer/spec chỉ cần khi muốn tái chấm tương đương official, không chặn local study đúng phạm vi.

Handover cũ nhắc `vimed_data_nho.zip` + `vimed_data_val.zip`, SQLite tải riêng. Các gói này chưa có để kiểm chứng ở checkout; không tự suy ba ZIP root thay thế chúng.

**Trước chạy thật:** copy config thành phiên bản riêng nếu cần, bind paths và `expected_sha256` từ file thật. `readiness.json` hiện còn trỏ **`data/...`**, trong khi `reproduce.json` và config downstream trỏ **`TXT/inputs/handover/data/...`**. Đồng bộ chúng; CLI không tự tìm file ở vị trí khác. Không điền hash giả. Hash có thể lấy bằng:

```powershell
(Get-FileHash -Algorithm SHA256 -LiteralPath TXT/inputs/handover/data/val/beta.json).Hash.ToLowerInvariant()
```

Ghi SHA-256 dạng **64 ký tự hex chữ thường**; output hash mặc định của PowerShell viết hoa, không hợp `expected_sha256` validator. Đối chiếu schema với `TXT/bear/adapters.py`, `TXT/bear/artifacts.py` và `TXT/PLAN.md` §6: qid trùng, doc trùng, score không hữu hạn, corpus thiếu body/lang hoặc source universe khác snapshot đều cần xử lý trước benchmark. Source manifest phải có artifact/corpus/query hashes, cutoff, completeness và provenance được xác minh.

## 7. Trình tự chạy và điều kiện chuyển bước

### 7.1. Vòng tiếp theo N0–N5

Đây là tóm tắt vận hành sau kết quả TXT/BEAR `0.3445`; task, dependency và acceptance chi tiết theo [PLAN v2.0 §11](PLAN.md), lý do nghiên cứu theo [proposal §13](TXT_Proposal.md#13-lộ-trình-triển-khai-và-điều-kiện-chuyển-bước), lịch sử theo [improvement_log.md](improvement_log.md). N0–N5 vẫn là kế hoạch chưa nghiệm thu. Các report/output N0–N5 dưới đây **chưa được tạo**; đường dẫn là đích đề xuất dưới `TXT/reports/next_round/` hoặc `TXT/runtime/next_round/`. Config mới của vòng này đặt trong `TXT/configs/next_round/`, tham chiếu các template đang có; không chỉnh manifest completed để reuse sai hash.

| Mốc | Việc ưu tiên và điều kiện chuyển | Đầu ra dự kiến — chưa tạo |
|---|---|---|
| **N0** | Nối score người dùng báo với run/submission/config/code/input hashes, qids và scoring output. Reuse baseline có parity/integrity verified cùng snapshot; chỉ reproduce khi thiếu chứng cứ hoặc mismatch. Giữ riêng điểm REPORTED và parity local. | `TXT/reports/next_round/N0_provenance_v1.md`; `TXT/runtime/next_round/N0_v1/provenance.json` |
| **N1** | Audit features thực có và đường áp dụng/fallback, rồi đếm ranking/docset thay đổi thực so reference. Sample100 có freeze dùng cho chẩn đoán; audit full1200 khi có artifact toàn tập. Thiếu full features thì chỉ đề xuất full run sau khi biết bottleneck/cost, không ngoại suy gain hay runtime bằng nhân 12, không ép routing. | `TXT/reports/next_round/N1_application_audit_v1.md`; bảng per-query dưới `TXT/runtime/next_round/N1_v1/` |
| **N2** | Đo fixed body L1 so local L4 trong **cùng PLARGE/pool/labels/query set/chunk policy**. Giữ λ `[0,0.02,0.05,0.10,0.20,0.35]`, λ0/reference và non-VI slots; combined tune L1_L4 có12registered trials. Chỉ kết luận trong judged scope. | `TXT/reports/next_round/N2_fixed_evidence_v1.md`; trials/ledger dưới `TXT/runtime/next_round/N2_v1/` |
| **N3** | Pilot chunk độc lập: **C1 trước, C2 sau** với doc set/order, corpus/chunk boundaries và allocation đóng băng; đổi selector để tách cơ chế. Kiểm mapping và score coverage theo tầng, gồm extra VI nếu có. Không gộp gain C1/C2 hoặc đổi allocation trong cùng ablation. | `TXT/reports/next_round/N3_chunk_pilot_v1.md`; C1/C2 outputs dưới `TXT/runtime/next_round/N3_v1/` |
| **N4** | Chỉ chạy F0 khi B/D source family, ranks và features đã verified. Sau fixed endpoints mới O0/H3, E(q)–utility, best constant, query-only và shuffled-E controls. Adaptive cần qua gate và runner đã hoàn thiện; thiếu headroom thì giữ fixed. | `TXT/reports/next_round/N4_routing_controls_v1.md`; trials/controls dưới `TXT/runtime/next_round/N4_v1/` |
| **N5** | So các candidate hoặc tổ hợp **trên dev** bằng primary metric cùng scope, kiểm tương tác và cost rồi chọn **một** candidate chính; freeze trước **một lần** holdout. Không so ΔP trực tiếp với local LCS để chọn nhánh. Sau đó mới full features/inference và integrity cho candidate đã chốt. Không mở holdout riêng cho từng nhánh, không tự submit. | `TXT/reports/next_round/N5_confirmation_v1.md`; frozen/full/integrity outputs dưới `TXT/runtime/next_round/N5_v1/` |

**Checklist N1 cần ghi thành số đo:**

- Planned/effective qids, sample/full scope và hashes; pool size/cap, extra VI thực có, source provenance, frozen non-VI slots và eligibility theo query.
- Số query/pair có concepts, body/local evidence hợp lệ; unavailable theo nguyên nhân và no-match/zero riêng. Đếm feature eligibility riêng với số query thực dùng nonzero evidence và số query fallback reference; ghi effective mode/weight, không dùng số dòng output làm mẫu số áp dụng BEAR.
- Với cùng reference, đếm query đổi thứ tự, đổi top-40, đổi tập top-200; added/removed VI per-query và tổng. Giữ cả query đủ feature nhưng ranking không đổi và query không eligible để thấy cơ chế đang tác động ở đâu.
- Với added/extra VI, đếm body/chunk refs verified, dense/Qwen scores có sẵn, missing/not-scored, selector fallback và allocation eligibility. Có feature document không đồng nghĩa chunk đã được chọn bằng score hoặc có chunk hợp lệ.
- Ghi prediction/code/config/input/feature hashes và threshold/weight thực; phân biệt sample100 features với full1200 predictions. Báo cost đã đo trên scope thật; chưa đo thì ghi chưa đo. Không cưỡng ép routing để làm tỷ lệ áp dụng trông cao hơn.

**N2 code2.0:** tune hỗ trợ L1/L4/L1_L4/F0; dùng configs/next_round/tune_body_local_v2.json + menus_v2.json để tạo đủ12body/local trials. evaluation_config=null chưa chọn best; bind reviewed dev evaluation trước scoring. Judgments phải phủ union differences mọi trials, cùng pool/query/chunk policy.

**N3/N5 code2.0:** chunk-study giữ actual slots/doc/order; evaluate-chunks đo local_passage_recall, freeze bind records/refs và yêu cầu records hash trong dev report; release giữ selected chunks. Đây là local diagnostic, chưa official Chunk F2; snapshot/passages thật còn thiếu.

### 7.2. Lệnh vận hành hiện có theo dependency

Các bước A–H là hướng dẫn thao tác, không phải yêu cầu chạy lại cả pipeline sau điểm mới. Áp dụng chúng cho phần còn thiếu ở N0–N5; các tên config/output cũ là ví dụ có sẵn. Config mới dùng `TXT/configs/next_round/`, runtime dùng `TXT/runtime/next_round/`, report dùng `TXT/reports/next_round/` theo bảng §7.1. **Không chạy cả mục này thành một batch bỏ qua lỗi.** Sau mỗi lệnh, kiểm JSON status, `$LASTEXITCODE`, manifest và artifact cần thiết rồi mới sang bước kế. Khả năng chạy thực phải được kiểm từ run/artifact tương ứng, không suy từ fixtures.

### Bước A — Kiểm tra môi trường, inventory và readiness

```powershell
python -B -m unittest discover -s TXT/tests -t . -v
python -B -m unittest discover -s tests -v
python -B -m TXT.bear.cli audit --config TXT/configs/readiness.json
python -B -m TXT.bear.cli reproduce --config TXT/configs/reproduce.json --dry-run
```

Hai suite được ghi nhận trước đây có 48 và 10 tests; chỉ chạy checks phù hợp khi đổi code hoặc cần xác minh môi trường, không chạy lại tests vì chỉ cập nhật tài liệu. Audit ghi `TXT/manifests/inputs.json`, `TXT/manifests/baseline.json`, `TXT/reports/DATA_READINESS.md` theo config; kiểm đích ghi trước khi gọi để giữ snapshot cũ. Thiếu input thì exit 1 là dự kiến; tune dry-run chỉ báo menu chứ chưa kiểm được toàn downstream.

Sau khi bind snapshot thật, `reproduce --dry-run` cần hết `missing_roles`. `inputs_present_unverified` mới chỉ xác nhận file có mặt, chưa chứng minh schema/hash/parity. Global audit có thể còn thiếu nhãn/tokenizer; ghi rõ dependency nào còn thiếu, vẫn chạy R0 nếu đủ 14 roles đúng snapshot.

### Bước B — Reuse baseline verified hoặc tái lập R0 khi cần, chưa ZIP

N0 kiểm baseline artifact/parity report và hashes đã có trước. Nếu đủ, ghi nguồn vào report N0 và đi tiếp; không chạy lại R0 chỉ vì manifest cũ trong checkout chưa cập nhật. Lệnh dưới chỉ dùng khi chưa có baseline verified đúng snapshot hoặc đang giải quyết mismatch.

```powershell
python -B -m TXT.bear.cli reproduce --config TXT/configs/reproduce.json --execute
```

Mặc định output `TXT/runtime/runs/R0/`:

| Artifact | Cần xem gì? |
|---|---|
| `manifest.json` | `status=completed`, `parity_verified=true`, hashes đúng inputs/code/config |
| `parity.json` | `matches=true`; observed doc/chunk khớp `c1e068422e5f` / `fd07f9fc029a` |
| `candidates.jsonl`, `deep.jsonl` | 200 doc/query cuối và deep list dùng dựng pool |
| `allocation.jsonl` | p(gold) đã round4, để kiểm thresholds/plan |
| `records.json`, `chunk_refs.jsonl` | JSON submission chưa nén và sidecar offsets/provenance |

Nếu `BASELINE_PARITY_FAILED`, **dừng so chất lượng**. So snapshot/hash, patch109, RRF/tie/order, membership/vinmec/refill, scorer 8-beta, round4 và chunk refs. Không tune trọng số hoặc thay expected fingerprint để làm pass. Lưu debug artifacts và nguyên nhân; chỉ đánh dấu R0 verified khi cả hai hash đúng và integrity qua.

Giữ R0 bất biến làm rollback. Ghi kết quả thật vào report mới và task T04; không chỉ sửa trạng thái reported score thành observed score.

### Bước C — Frozen pool và representative sample

```powershell
python -B -m TXT.bear.cli pool --config TXT/configs/pool_v1.json --dry-run
python -B -m TXT.bear.cli pool --config TXT/configs/pool_v1.json --execute
python -B -m TXT.bear.cli sample --config TXT/configs/sample_v1.json --execute
```

Pool ở `TXT/runtime/pools/plarge_v1/{manifest.json,pools.jsonl}`. Kiểm giữ đủ baseline, extras đúng membership, cap, không duplicate, frozen non-VI slots và số extra VI thực có. Pool có thể chứa extra ZH/EN từ deep/sources; chỉ VI lane được sort/select, non-VI extras không được thay vào output. Pool không có extra VI thì không tạo selection headroom.

**Config pool hiện `sources=[]`, `b_family=null`.** Có thể dùng cho L1 evidence-only, nhưng chưa có B/D features để diễn giải F0 hoặc E(q) routing. Trước F0/A1, đăng ký nguồn thật theo schema trong `config.py`/`features.py`; build family từ child ranks có provenance, giữ original source rank trước khi restrict pool. Support B top-20 độc lập với output gate, có thể chứa doc ngoài ranking pool. Không suy family chỉ từ tên artifact.

Sample output ở `TXT/runtime/studies/sample_v1/`: `split.json`, `smoke_ids.json`, manifest. Sample 100 query không hoàn lại, seed 42; target dev60/holdout40, group exact duplicates nên số thực có thể lệch. Không lấy first-N vì lịch sử query đầu dài/khó hơn.

Đọc `actual_counts`, `query_groups`, query/split hashes và `confirmatory_eligible`. Sampling tự ghi qids đã quan sát từ `scoring_result.zip` vào contamination ledger. Nếu giao holdout thì `confirmatory_eligible=false`; không gọi nó là pristine/confirmatory chỉ vì CI đẹp. Không đổi seed để săn holdout thuận lợi.

### Bước D — Smoke2 rồi L0 pilot

```powershell
python -B -m TXT.bear.cli features --config TXT/configs/l0_smoke.json --execute
python -B -m TXT.bear.cli features --config TXT/configs/l0_pilot.json --execute
```

Smoke dùng `smoke_ids.json` kiểm I/O trên 2 query, không dùng chọn config hoặc ngoại suy chất lượng. Pilot dùng `sampled_ids` đã freeze trong split, mặc định batch 20; uniform exact là V1.

Output pilot `TXT/runtime/features/uniform_v1/`: `pairs_*.jsonl`, `chunks_*.jsonl`, `support_*.jsonl`, `shard_*.json`, `routes.jsonl`, `L0.json`, `L0.md`, manifest. Đọc L0 để kiểm missingness/parse status/mapping, coverage theo rank/language bins, số chunk, availability E(q), gamma và fallback. Kiểm vài trường hợp identifier/type 1–2/long-doc bằng text/offset thật.

Không có B support thì E(q) chưa dùng được cho routing. E(q) chỉ available khi actual support không rỗng và **tất cả** support docs valid; coverage=0 vẫn valid. Không nâng E bằng cách bỏ các doc thiếu feature khỏi denominator.

Sau L0: báo số query/pair/chunk và feature hợp lệ, runtime, đo RAM/I/O thực; chưa có benchmark thì ghi chưa đo. Hoàn tất checklist N1 về **feature eligibility, áp dụng thực và ranking/docset changes** trước diễn giải số đo chất lượng. Partial restart hiện recompute shard, không cam kết skip shard hoàn tất. L0 distributions không chứng minh H1/H2 hoặc relevance gain.

### Bước E — Tạo fixed trial predictions trên dev

Một run ví dụ có thể chạy bằng `run --config TXT/configs/run_l1.json --execute`, nhưng đây chưa phải kết quả chọn tốt nhất. Để tạo đủ L1 menu:

```powershell
python -B -m TXT.bear.cli tune --protocol TXT/configs/tune_l1.json --menu TXT/configs/menus_v1.json --dry-run
python -B -m TXT.bear.cli tune --protocol TXT/configs/tune_l1.json --menu TXT/configs/menus_v1.json --execute
```

L1 có 6 λ: `[0,0.02,0.05,0.10,0.20,0.35]`, dùng body exact uniform. Output mặc định `TXT/runtime/studies/L1_dev/L1_0/` đến `L1_5/`, mỗi trial có `candidates.jsonl`, `ranking_details.jsonl`, manifest; study có `trials.json`, `selection.json`.

**`tune_l1.json` hiện `evaluation_config=null`: chỉ tạo predictions/ledger diagnostic, không chọn best.** Kiểm λ0 khớp reference; đọc `ranking_details.jsonl` để thấy fallback. Inference vẫn có thể xuất toàn query trong pool dù features chỉ có sample; các query thiếu features fallback reference. Vì vậy đủ 1.200 dòng chưa chứng minh đã áp dụng BEAR toàn tập.

F0 vẫn có18configs và cần B/D verified. L4/L1_L4 đã chạy qua tune2.0 trên fixtures với menu sáu λ; L2 IDF/L3 critical là study sau. Không mở rộng grid sau khi nhìn kết quả.

### Bước F — Annotation dev và chấm tất cả trials

1. Copy `annotation_dev.json` thành **`TXT/configs/annotation_dev_v1.json`**. Mặc định mới liệt kê `L1_example`; phải thay `predictions` bằng **cả 6** `TXT/runtime/studies/L1_dev/L1_i/candidates.jsonl` của menu đã preregister.
2. PLARGE dùng `mode=differences`, `k=200`; P200 là study/config riêng, dùng `mode=topk`, `k=40` và metric P@40.
3. Chạy export sau khi config đã đủ:

```powershell
python -B -m TXT.bear.cli annotation-export --config TXT/configs/annotation_dev_v1.json --execute
```

Output mặc định `TXT/runtime/annotation/dev_v1/blinded.jsonl`: query/body/language và trường nhãn rỗng, ẩn rank/source/score. Nhờ người review điền `grade` integer 0/1/2, `annotator`, `adjudication="reviewed"`, `label_policy_version="local_answer_v1"`, supporting passages/offsets/body hash và lý do. Grade 0 = sai/không liên quan, 1 = đúng chủ đề nhưng chưa trả lời, 2 = có supporting answer. Primary dùng grade 2; không đổi threshold sau kết quả. Audit/adjudication mẫu theo PLAN §10.5.

Đặt qrels reviewed dưới `TXT/inputs/evaluation/`. Không cho coding AI tự điền gold để vượt blocker. Inference/features không nhận qrels; nhãn chỉ đi qua evaluation.

4. Copy `evaluation_dev.template.json` thành **`TXT/configs/evaluation_dev_v1.json`**; điền `qrels_path`, `qrels_hash`, `split_hash` bằng SHA-256 thật. Giữ `split=dev`, metric/scope/coverage đã đăng ký. Mỗi lần compare nên có `output_dir` riêng để không ghi đè report trial khác.
5. Ví dụ chấm một trial PLARGE sau khi đã tạo config trên:

```powershell
python -B -m TXT.bear.cli compare --baseline-dir TXT/runtime/runs/R0 --candidate-dir TXT/runtime/studies/L1_dev/L1_1 --config TXT/configs/evaluation_dev_v1.json
```

`compare/evaluate` chạy ngay, **không thêm `--execute` hoặc `--dry-run`**. Đọc `evaluation.json`: status, planned/effective queries, missing IDs, per-query delta và paired CI. Mọi added/removed phải có judgment; thiếu một doc cần thiết thì không suy label=0 hoặc chọn best từ subset thuận lợi.

Runner2.0 có paired bootstrap cho replacement và precision_at_k/macro_doc_f2 khi cung cấp baseline và đủ control judgments. P200 có paired ΔP@40 đúng query/groups; thiếu labels báo lỗi trước exposure.

Muốn tune có scoring cho đủ menu, tạo **`TXT/configs/tune_l1_scored_v1.json`** từ config tuning cũ: trỏ `evaluation_config` tới dev config đã bind và đổi `output_dir` thành `TXT/runtime/studies/L1_dev_scored_v1`. Chạy:

```powershell
python -B -m TXT.bear.cli tune --protocol TXT/configs/tune_l1_scored_v1.json --menu TXT/configs/menus_v1.json --execute
```

**Không sửa config rồi chạy lại vào `L1_dev` đã completed.** Code/input/config hash đổi sẽ reject reuse. Study scored mới tái tạo trials và chấm cùng planned dev universe; `selection.json` chỉ chọn khi tất cả trial metrics available. Thiếu labels thì bổ sung annotation và version output, không ép select.

### Bước G — Quyết định có mở adaptive hay giữ fixed

Thực hiện N4 theo PLAN v2.0 §11 trước A1: B/D endpoints, dev oracle O0/headroom, E(q) bins so với chênh lệch utility, best constant, query-only control và shuffled-E controls seeds `[11,23,37,53,71]`. T11 trong [PLAN đã lưu](archive/PLAN_before_N0_N5_20261019.md) là hợp đồng triển khai lịch sử để tra thêm, không phải task mới để chạy lại từ đầu.

Adaptive production hiện bị chặn; muốn chạy phải hoàn thiện phần runner/prerequisite còn thiếu, test phù hợp và cập nhật ledger, không chỉ bật mode trong JSON. Sparse S1/S2 cần checkpoint/revision/API/cost audit; C1/C2 cần mapping/score coverage và study runner; C3 cần budget/allocation study riêng. Thiếu trigger thì giữ backlog. Fixed có thể được confirm độc lập nếu adaptive không có headroom.

### Bước H — Freeze candidate chính, rồi một lần holdout

Compare bên dưới dùng document metrics. Với chunk candidate dùng evaluate-chunks và local-passage config; freeze2.0 bind selected records/refs và không nhận dev document-only score cho chunk candidate.

Đây là bước freeze/holdout trong N5, chỉ thực hiện sau dev selection: primary dev đủ labels, các nhánh đủ điều kiện trong N2/N3/N4 được so sánh trên dev, tổ hợp được kiểm tương tác và đã chọn một candidate/control chính. Nhánh deferred không chặn chọn fixed/chunk đã được kiểm chứng. Không mở holdout độc lập cho mỗi nhánh rồi chọn winner. Tạo **`TXT/configs/protocol_confirm_v1.json`** từ protocol template, bind `selected_dev_report` là **`evaluation.json` có status available của đúng candidate**; không dùng `selection.json` thay nó. Với vòng mới đặt config version dưới `TXT/configs/next_round/`. Bind controls, split, thresholds và `cost_ceiling_seconds` thực. Protocol hiện `proposed_not_frozen`, các trường null chưa đủ để freeze.

Ví dụ nếu dev chọn `L1_1` trong study scored:

```powershell
python -B -m TXT.bear.cli freeze --run-dir TXT/runtime/studies/L1_dev_scored_v1/L1_1 --protocol TXT/configs/protocol_confirm_v1.json
```

Đây chỉ là ví dụ đường dẫn; thay bằng trial **thật sự được dev chọn**. Output `<selected_run>/frozen.json` bind candidate/control/code/protocol/split/selection hashes. Chốt candidate chính trước khi xem holdout; không lần lượt thử fixed/adaptive/chunk trên cùng holdout đã mở.

Annotation holdout dùng config version riêng, `split=holdout`, `frozen_candidate` trỏ file frozen, chỉ liệt kê candidate/controls đã freeze. Nhận nhãn reviewed ở file holdout riêng. Tạo **`TXT/configs/evaluation_holdout_v1.json`** với hashes thật, metric/coverage đúng protocol, `split=holdout`, frozen path và output riêng.

**Trước chấm:** dùng CLI preflight để kiểm config/hashes/coverage/labels/contract; không trả scores hoặc tiêu exposure. Code2.0 exclusive-claim exposure sau validation. Không xóa marker hoặc dùng evaluate thử trước compare; vẫn review contamination theo protocol.

Với PLARGE, gọi **một lần compare** cho candidate chính so R0; không gọi evaluate thử trước:

```powershell
python -B -m TXT.bear.cli compare --baseline-dir TXT/runtime/runs/R0 --candidate-dir TXT/runtime/studies/L1_dev_scored_v1/L1_1 --config TXT/configs/evaluation_holdout_v1.json
```

Nếu cần nhiều confirmatory controls trong cùng exposure, hoàn thiện orchestration theo protocol trước khi mở; runner hiện không cho gọi lại compare nhiều lần trên cùng frozen candidate. Guard local không thay thế việc review contamination. `confirmatory_eligible=false` phải được nêu trong kết luận dù CLI vẫn tính được metric.

## 8. Có kết quả rồi phải làm gì?

Trước khi nhìn con số gain, xác nhận: input/hash đúng, run completed, cùng pool/components/chunk policy, cùng planned query universe, metric hợp coverage và evaluator được ghi tên rõ.

| Kết quả | Việc cần làm |
|---|---|
| Điểm TXT/BEAR mới `0.3445`, tăng `0.0003` so 15/10 | Giữ là REPORTED, nối provenance N0 và audit N1; chưa quy gain cho H1/H2/H3, chưa chọn tiếp một nhánh chỉ từ aggregate score. |
| Test qua, dry-run hết missing | Chuyển sang execute đúng bước; chưa kết luận chất lượng. |
| R0 fingerprints lệch | Dừng so BEAR, debug parity, báo sai khác và dependency. |
| L0 thiếu views/mapping/coverage | Sửa adapter hoặc bổ sung artifact có provenance; version run và chạy lại diagnostics phù hợp. |
| Dev có trial tốt hơn | Ghi toàn bộ ledger, chọn theo tie rules rồi freeze; chưa gọi là holdout gain. |
| Thiếu labels, CI rộng, evaluator/holdout không phù hợp | `inconclusive`; ghi cụ thể cần bổ sung gì. Thiếu dữ liệu không phải phương pháp thất bại. |
| Holdout valid đạt thresholds | Đề xuất `keep` cho cơ chế đã được thử, sau khi kiểm subgroup/cost và đủ chứng cứ. |
| Bằng chứng đủ cho thấy thua control hoặc gain không đáng cost | `reject`; giữ kết quả âm và dùng R0/fixed đã xác minh. |

Threshold khởi điểm trong protocol là **đề xuất cần freeze trước holdout**: gain tuyệt đối ≥ `0.005`, CI95% lower > 0, subgroup tolerance `-0.01`, chi phí trong ceiling. PLARGE ΔP@200 = 0.005 tương ứng trung bình thêm 1 relevant doc/query. Bootstrap theo query groups 10.000 lần, seed42; báo sample size và win/tie/loss. CI không sửa được pooling bias/contamination, nhóm nhỏ cần nêu bất định.

Chỉ giữ adaptive khi vượt **best fixed cùng components/pool/budget**, có controls hỗ trợ routing và không regression nghiêm trọng. Gain L1 không chứng minh A1; gain P@40 hoặc local passage diagnostic không tự thành gain Doc/Chunk/FINAL official. Không cộng gain các study riêng để dự đoán FINAL.

Mỗi experiment cần report dưới `TXT/reports/` ghi:

```text
Study/run, câu hỏi và cơ chế thay đổi
Config/protocol/menu/split/code/input hashes, snapshot, seed
Pool/scope/language policy; reference và controls
Evaluator/label policy/coverage; planned và effective queries; contamination
Tất cả trials, per-query delta, mean/CI, win–tie–loss, subgroup/fallback
Feature-eligible queries/pairs so với actual applied/fallback queries
Ranking/top-40/docset changed counts; added/removed VI và extra-VI score/chunk coverage
Runtime/RAM/I/O/GPU/annotation cost đã đo; trường nào chưa đo
Integrity/parity, lỗi/missingness và kết quả âm
Quyết định keep/reject/inconclusive, lý do, bước tiếp và rollback
```

Cập nhật `IMPLEMENTATION_STATUS.md`, `RESULTS.md`, `DECISIONS.md`, `KNOWN_LIMITATIONS.md` và handover theo kết quả thật khi có artifact tương ứng. Giữ các report/ledger trước điểm mới như snapshot lịch sử; bản cập nhật điểm hiện ở [improvement_log.md](improvement_log.md). Không ghi đè report cũ để che trial thua. Kết quả server được ghi REPORTED ngay khi người dùng cung cấp; nối submission/run/hash/config với scoring output trước khi chứng nhận provenance hoặc đổi baseline kỹ thuật.

## 9. Khi nào và cách xuất submission?

Technical package và quyết định chọn phương pháp là hai mốc riêng. Không xuất pilot như thể BEAR đã áp dụng đủ tập, không tự upload/promote.

Release2.0 giữ selected C1/C2 records/refs khi candidate_kind=chunk, kiểm same corpus/doc/head/actual slots trước validate/package. Release vẫn cần full1200×200 và đủ14inputs frozen; pilot không thể xuất thành full submission.

1. Baseline verified đã có hoặc R0 đã qua parity, giữ nguyên làm rollback; không yêu cầu reproduce lại nếu chứng cứ sẵn đủ.
2. Candidate có bằng chứng phù hợp, config/parameters đã freeze. Copy pilot feature config thành **`TXT/configs/l0_full_v1.json`**, đặt `query_ids_path=null`, output mới (ví dụ `TXT/runtime/features/full_v1`). Run config full phải trỏ `feature_manifest` tới manifest mới này và giữ đúng frozen parameters. Không tune lại từ holdout. Đối chiếu subset đã đánh giá vẫn có hành vi tương đương, ghi full run provenance.
3. Kiểm full ranking đủ 1.200×200, membership/non-VI slots/missing feature/fallback đúng policy. Báo số query có đủ features, actual applied/fallback, ranking/docset thay đổi và score/chunk coverage của extra VI như N1. Có 1.200 rows do baseline fallback chưa đủ để chứng nhận full BEAR inference.
4. Copy `export.json` thành config release version riêng, bind đúng 14 inputs, corpus/hash và `output_dir` mới. Ví dụ sau khi đã tạo `TXT/configs/run_full_v1.json` và `TXT/configs/export_release_v1.json`:

```powershell
python -B -m TXT.bear.cli features --config TXT/configs/l0_full_v1.json --execute
python -B -m TXT.bear.cli run --config TXT/configs/run_full_v1.json --execute
python -B -m TXT.bear.cli export --run-dir TXT/runtime/runs/full_v1 --config TXT/configs/export_release_v1.json --dry-run
python -B -m TXT.bear.cli export --run-dir TXT/runtime/runs/full_v1 --config TXT/configs/export_release_v1.json --execute
```

Đặt `output_dir` của run config đúng `TXT/runtime/runs/full_v1` như ví dụ. Những config `*_v1` thêm ở các bước F/H/release là **file cần tạo/bind khi đủ điều kiện**, không có sẵn trong snapshot hiện tại.

Exporter tính lại frozen p/plan cho **doc/order mới**, giữ công thức/ngưỡng cũ; kiểm integer IDs, đủ query/docs, membership và ngoại lệ `vinmec.com`, body/offset/text hash/chunk order. Lưu provenance ngoài JSON nộp, không tự thêm explanation keys vào schema nộp.

Output release: `submission.json`, `submission.zip`, `chunk_refs.jsonl`, `allocation.jsonl`, `legacy_audit.json`, manifest. ZIP chứa đúng một JSON ở gốc, LZMA dictionary 768 MiB; code kiểm testzip/readback và giới hạn bảo thủ **`<100000000 bytes`**. Dự trù RAM nén, chưa có cost benchmark thật. Legacy readonly audit là diagnostic; lỗi schema không phải lý do migrate/clean nguồn.

Manifest release mặc định `promoted=false`. Ghi fingerprint/SHA-256 package, nối về run/report và giữ rollback; chỉ upload/nộp khi người dùng yêu cầu. Kiểm quy định/nền tảng hiện hành trước bước nộp, không suy mọi luật hiện tại từ ghi chú lịch sử. Working notes cần mô tả cả cơ chế, controls và giới hạn kết quả.

## 10. Resume, lỗi thường gặp và bước xử lý

`manifest.status=completed` chỉ xác nhận job kỹ thuật hoàn tất; selection vẫn có thể `inconclusive`, protocol vẫn có thể chưa confirmatory. Completed runs chỉ reuse khi **code/config/inputs/artifacts hashes không đổi**. Đổi tham số, thêm nhãn, sửa code hoặc thay snapshot → `run_id/output_dir` mới; không sửa tay manifest hoặc artifacts completed.

| Tình huống | Cách xử lý |
|---|---|
| `blocked_input` / `INPUT_MISSING` | Xem missing roles đúng command; sửa path hoặc nhận đúng artifact. Không chạy tiếp bước phụ thuộc. |
| `SCHEMA_INVALID` | Xem type/key/qid/doc duplication/lang/offset và source contract; không bỏ validation để chạy. |
| `HASH_MISMATCH` | Xác minh file thực so provenance; completed run dùng output mới sau thay đổi hợp lệ. Không thay hash để hợp thức hóa file không rõ nguồn. |
| `BASELINE_PARITY_FAILED` | Debug R0 theo bước B; chưa benchmark BEAR. |
| `FEATURE_UNAVAILABLE` / fallback nhiều | Kiểm concepts/views/support/source mapping; phân biệt unavailable với no-match. |
| Label coverage thiếu / evaluation `inconclusive` | Export đủ required judgments, human review và version evaluation; không tự gán 0. |
| Output ngoài TXT / đè input | Đổi config về `TXT/runtime/...` hoặc `TXT/reports/...`; guard resolve cả symlink/junction. |
| SQLite/WAL thay đổi | Nhận lại snapshot nhất quán, không tự sửa database nguồn. |
| Holdout đã có exposure marker | Giữ marker/history, báo đã exposed; không rerun để chọn winner mới. |

## 11. AI tiếp theo nên bắt đầu ngay thế nào?

1. Đọc handover để vận hành, [improvement_log.md](improvement_log.md) để nắm lịch sử, proposal §13 để hiểu hướng nghiên cứu, rồi [PLAN v2.0 §11](PLAN.md) để chọn task/dependency/nghiệm thu N0–N5. Kiểm dirty state và run/artifact hiện có. Ghi nhận kết quả TXT/BEAR đã được người dùng báo; đừng tạo lại bộ BEAR hoặc xem ledger cũ là bằng chứng chưa từng có điểm mới.
2. Làm **N0**: nối score với run/config/hashes/qids, kiểm baseline verified để reuse. Nếu cần R0 mới kiểm 14 roles, bind/hash và reproduce; lập thiếu hụt theo đúng bước, không mặc định toàn bộ pipeline phải chạy lại.
3. Làm **N1**: audit features và application/fallback/ranking/docset changes trên phạm vi artifact thật. Phân biệt sample100/full1200, không suy đủ 1.200 rows là đủ BEAR. Ghi extra-VI score/chunk coverage và cost đã đo.
4. Làm **N2/N3 độc lập** sau readiness của từng nhánh: fixed body/local với sáu λ; C1 rồi C2 với doc set/allocation cố định. N4 chỉ mở khi có N2 và B/D verified, rồi F0/O0/H3/controls. Chưa đủ labels hoặc runner thì ghi thiếu cụ thể; không ép adaptive và không mở rộng grid sau nhìn điểm.
5. **N5** chọn một candidate hoặc tổ hợp trên dev sau kiểm tương tác, freeze rồi một lần holdout; sau đó full features/integrity. Mọi output mới của vòng tiếp theo dưới `TXT/reports/next_round/` hoặc `TXT/runtime/next_round/`; không tự nộp bài.
6. Kết thúc lượt làm việc bằng: lệnh thực chạy, output, bằng chứng, blocker, quyết định và bước kế tiếp. Code2.0 đã chạy fixtures/tests/N0 inventory; chưa benchmark thật/GPU/full package/submission. Xem report v2 để phân biệt lịch sử sửa tài liệu với lượt triển khai code.

Prompt ngắn có thể giao cho AI tiếp quản:

> Đọc `TXT/TXT_handover.md` để vận hành, `TXT/improvement_log.md` để nắm lịch sử, `TXT/TXT_Proposal.md` §13 để hiểu hướng nghiên cứu và `TXT/PLAN.md` v2.0 §11 để chọn task/dependency/nghiệm thu N0–N5. PLAN gốc T01–T16 đã lưu tại `TXT/archive/PLAN_before_N0_N5_20261019.md`; ledger kỹ thuật cũ là snapshot, không phải nghiệm thu N0–N5. Người dùng đã báo kết quả bài TXT/BEAR FINAL 0.3445, Doc F2 0.3612, Chunk F2 0.3279; giữ attribution này và nối provenance kỹ thuật ở N0. Reuse baseline verified hoặc reproduce khi thật sự cần, rồi N1 audit feature eligibility so với actual application/fallback và ranking/docset changes, phân biệt sample100/full1200. N2 fixed body/local cùng sáu λ và N3 C1 rồi C2 là hai nhánh độc lập sau readiness. N4 cần N2 và B/D verified, rồi F0/O0/H3/controls; adaptive chỉ khi qua gate. N5 chọn một candidate hoặc tổ hợp trên dev, kiểm tương tác, freeze, một lần holdout rồi full features/integrity. Config mới dưới `TXT/configs/next_round/`, outputs dưới `TXT/reports/next_round/` hoặc `TXT/runtime/next_round/`; tên file dự kiến chưa phải artifact đã có. Giữ report/ledger cũ như snapshot trước điểm mới, không dùng proxy/feedback làm qrels, không tự nộp bài. Ghi bằng chứng, blocker và bước kế tiếp cụ thể.
