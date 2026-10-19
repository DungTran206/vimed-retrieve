# TXT handover — Tiếp quản và chạy Biomedical Evidence-Aware Retrieval (BEAR)

> Cập nhật: **19/10/2026**. Đây là điểm bắt đầu cho AI tiếp quản nhánh `TXT/`.
>
> Mục tiêu: hiểu baseline cũ, phần BEAR đã làm, điều kiện chạy từng bước, cách đọc kết quả và việc cần làm tiếp. Tài liệu này mô tả **code đang có**, phân biệt với phần mới chỉ được đề xuất.
>
> **Trạng thái hiện tại: đã có code CPU và kiểm thử bằng fixtures; chưa tái lập baseline hoặc benchmark BEAR trên dữ liệu thật. Việc tiếp theo là nhận đúng snapshot, bind config/hash, rồi chạy R0.**

## 1. AI nhận việc cần đọc gì?

Đọc theo thứ tự sau; đường dẫn trong lệnh luôn tính từ **repo root**.

| Thứ tự | Tài liệu | Cần nắm |
|---|---|---|
| 1 | File handover này | Trạng thái thực tế, chuỗi chạy, điều kiện chuyển bước và xử lý kết quả. |
| 2 | [IMPLEMENTATION_STATUS.md](reports/IMPLEMENTATION_STATUS.md), [KNOWN_LIMITATIONS.md](reports/KNOWN_LIMITATIONS.md), [RESULTS.md](reports/RESULTS.md) | Task nào đã có code, task nào chỉ qua fixture, phần thiếu dữ liệu hoặc chưa triển khai. |
| 3 | [TXT_Proposal.md](TXT_Proposal.md) | Ý tưởng hiện tại: H1–H6, evidence, fixed controls, routing, chunk và thiết kế đánh giá. Ưu tiên các mục 2, 5, 7–13, 17–18. |
| 4 | [PLAN.md](PLAN.md) | Hợp đồng triển khai. Đọc mục 1–10; dùng mục 11 để chọn task và dependency. |
| 5 | [HANDOVER cũ](../doc/HANDOVER.md), [CLAUDE.md](../doc/CLAUDE.md) | Baseline w045, pipeline cũ, dữ liệu cần nhận, scoring, định dạng nộp và các quy định dự án đã ghi nhận. |
| 6 | [EVALUATOR_CONTRACT.md](reports/EVALUATOR_CONTRACT.md), [DECISIONS.md](reports/DECISIONS.md), [RUNBOOK.md](reports/RUNBOOK.md), [DATA_READINESS.md](reports/DATA_READINESS.md) | Phân biệt evaluator/proxy, quyết định kỹ thuật, lệnh hiện có và input còn thiếu. |
| Khi cần | [PROGRESS.md](../doc/PROGRESS.md), [METHODS.md](../doc/METHODS.md), [PIPELINE.md](../doc/PIPELINE.md), [SETUP.md](../doc/SETUP.md) | Lịch sử số đo, các hướng đã thua, kiến trúc và môi trường cũ. Đọc mục có ngày/đính chính liên quan, đặc biệt quanh 12–15/10. |
| Tham khảo lịch sử | [BIOMEDICAL_ADAPTIVE_RETRIEVAL_AGENT_PLAN.md](BIOMEDICAL_ADAPTIVE_RETRIEVAL_AGENT_PLAN.md) | Plan ý tưởng đời trước; không lấy CLI/layout hoặc câu micro F2 trong đó thay hợp đồng mới. |

**Cách giải quyết mâu thuẫn:** yêu cầu người dùng → hành vi code thực tế và artifact có nguồn gốc → trạng thái triển khai mới → quyết định trong `TXT/PLAN.md` và `TXT/TXT_Proposal.md` → tài liệu lịch sử. Khác biệt về kết quả phải kiểm tra provenance, không chỉ chọn con số cao hơn.

Một số câu trong proposal/PLAN như “chưa có package BEAR”, “phiên này chỉ lập kế hoạch” mô tả thời điểm soạn tài liệu. Package hiện đã có; xem task ledger và code để biết trạng thái tiếp quản. Các tài liệu cũ nhắc `HANDOVER.md`, `CLAUDE.md` ở root thì tìm trong `doc/`.

## 2. Bài toán và hướng BEAR hiện tại

Với mỗi query tiếng Việt, hệ thống chọn document và các đoạn trích y sinh từ corpus đa ngôn ngữ. Baseline đã có BM25, dense, Qwen reranker, nhánh ZH và chunk allocation. BEAR tận dụng các artifact đó, thêm **bằng chứng khớp thuật ngữ/điều kiện y khoa** để thử cải thiện việc chọn document hoặc chunk.

Chuỗi nghiên cứu cần giữ:

```text
Đúng snapshot + baseline/evaluator readiness
  → Frozen pool + query concepts + exact/local evidence (L0)
  → Nhãn reviewed + fixed evidence (L1) / fixed B–D fusion (F0)
  → Kiểm tra routing headroom và controls
  → Adaptive (A1), chỉ khi đủ điều kiện
  → Full inference + integrity + package

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

### 3.1. Snapshot phải tái lập

| Thuộc tính | Giá trị bàn giao — REPORTED |
|---|---|
| Run/ngày | `w045_TF`, 15/10/2026 |
| Doc F2 / Chunk F2 / FINAL | `0.3605 / 0.3279 / 0.3442` |
| Legacy doc fingerprint | `c1e068422e5f` |
| Legacy chunk fingerprint | `fd07f9fc029a` |
| Kích thước submission | Đủ query ID 1–1200; 200 doc/query |
| Corpus/chunk | Đúng `corpus_new.sqlite` đã clean, chunk bằng offset, khoảng 900 token |
| Calibration | **`scripts/val_calib.py` và beta 8 hệ số của snapshot** |

`TXT/manifests/baseline.json` hiện là `not_reproduced`, `observed_metrics=null`, `observed_fingerprints=null`. Tái tạo đúng fingerprint xác nhận artifact parity; không có nghĩa đã chạy lại server và đo lại điểm leaderboard.

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
| Chunk | `chunk_experiments.py` | C1/C2 mới có pure selectors; chưa có study runner hoàn chỉnh. C3 chưa mở. |
| Release | `integrity.py`, `release.py` | Có technical validation/package; chưa xuất release thật hoặc promote. |

Ledger T01–T16 trong `reports/IMPLEMENTATION_STATUS.md` là nơi cập nhật tiến độ chi tiết. Adaptive nonzero hiện bị CLI runner chặn dù pure gate logic đã có. Sparse encoder/CLI, discovery, document gate và SPLADE chưa được triển khai để chạy production. Không tự tạo CLI giả hoặc đánh dấu toàn PLAN đã xong.

Đã chạy lại khi soạn handover: **48/48 test BEAR** trong `TXT/tests/` và **10/10 test legacy** trong `tests/test_offline.py` đều qua. Chúng kiểm fixtures/logic, không phải relevance benchmark. `TXT/manifests/code_inventory.json` là inventory lần triển khai trước; đối chiếu hash thực khi tiếp quản, không dùng như chứng cứ run mới.

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

`data/` hiện chỉ có `.gitkeep`. Readiness ghi thiếu **22 logical roles**; recipe R0 riêng cần **14 roles**. Không chờ đủ qrels/tokenizer mới chạy R0, và không hiểu global audit còn blocked là mọi công đoạn đều bị chặn.

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

**Không chạy cả mục này thành một batch bỏ qua lỗi.** Sau mỗi lệnh, kiểm JSON status, `$LASTEXITCODE`, manifest và artifact cần thiết rồi mới sang bước kế. Các lệnh execute bên dưới đã có code nhưng chưa được xác nhận trên dữ liệu thật.

### Bước A — Kiểm tra môi trường, inventory và readiness

```powershell
python -B -m unittest discover -s TXT/tests -t . -v
python -B -m unittest discover -s tests -v
python -B -m TXT.bear.cli audit --config TXT/configs/readiness.json
python -B -m TXT.bear.cli reproduce --config TXT/configs/reproduce.json --dry-run
```

Hai suite dự kiến 48 và 10 tests. Audit ghi `TXT/manifests/inputs.json`, `TXT/manifests/baseline.json`, `TXT/reports/DATA_READINESS.md` theo config. Hiện audit/R0 thiếu input thì exit 1 là dự kiến; tune dry-run chỉ báo menu chứ chưa kiểm được toàn downstream.

Sau khi bind snapshot thật, `reproduce --dry-run` cần hết `missing_roles`. `inputs_present_unverified` mới chỉ xác nhận file có mặt, chưa chứng minh schema/hash/parity. Global audit có thể còn thiếu nhãn/tokenizer; ghi rõ dependency nào còn thiếu, vẫn chạy R0 nếu đủ 14 roles đúng snapshot.

### Bước B — Tái lập R0, chưa ZIP

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

Sau L0: báo số query/pair/chunk và feature hợp lệ, runtime, đo RAM/I/O thực; chưa có benchmark thì ghi chưa đo. Partial restart hiện recompute shard, không cam kết skip shard hoàn tất. L0 distributions không chứng minh H1/H2 hoặc relevance gain.

### Bước E — Tạo fixed trial predictions trên dev

Một run ví dụ có thể chạy bằng `run --config TXT/configs/run_l1.json --execute`, nhưng đây chưa phải kết quả chọn tốt nhất. Để tạo đủ L1 menu:

```powershell
python -B -m TXT.bear.cli tune --protocol TXT/configs/tune_l1.json --menu TXT/configs/menus_v1.json --dry-run
python -B -m TXT.bear.cli tune --protocol TXT/configs/tune_l1.json --menu TXT/configs/menus_v1.json --execute
```

L1 có 6 λ: `[0,0.02,0.05,0.10,0.20,0.35]`, dùng body exact uniform. Output mặc định `TXT/runtime/studies/L1_dev/L1_0/` đến `L1_5/`, mỗi trial có `candidates.jsonl`, `ranking_details.jsonl`, manifest; study có `trials.json`, `selection.json`.

**`tune_l1.json` hiện `evaluation_config=null`: chỉ tạo predictions/ledger diagnostic, không chọn best.** Kiểm λ0 khớp reference; đọc `ranking_details.jsonl` để thấy fallback. Inference vẫn có thể xuất toàn query trong pool dù features chỉ có sample; các query thiếu features fallback reference. Vì vậy đủ 1.200 dòng chưa chứng minh đã áp dụng BEAR toàn tập.

F0 có menu 18 configs trong `menus_v1.json`; chỉ tạo tuning config family F0 khi B/D sources/features đã verified. L2 IDF chưa có, L3 critical cần reviewed provenance, L4 local cần study riêng. Không tự chạy toàn bộ plan cũ E0–E10 hoặc mở rộng grid sau nhìn kết quả.

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

Đoạn delta/CI trên áp dụng cho PLARGE `replacement_delta_p`. Runner hiện chỉ tự thêm paired bootstrap cho metric đó; P200 `precision_at_k` mới trả P@40/per-query values của candidate. Muốn kết luận paired gain/CI P200 phải chấm control và dùng utility paired đúng cùng query/groups, hoặc hoàn thiện runner trước study; không giả định truyền `--baseline-dir` đã tự có ΔP@40/CI.

Muốn tune có scoring cho đủ menu, tạo **`TXT/configs/tune_l1_scored_v1.json`** từ config tuning cũ: trỏ `evaluation_config` tới dev config đã bind và đổi `output_dir` thành `TXT/runtime/studies/L1_dev_scored_v1`. Chạy:

```powershell
python -B -m TXT.bear.cli tune --protocol TXT/configs/tune_l1_scored_v1.json --menu TXT/configs/menus_v1.json --execute
```

**Không sửa config rồi chạy lại vào `L1_dev` đã completed.** Code/input/config hash đổi sẽ reject reuse. Study scored mới tái tạo trials và chấm cùng planned dev universe; `selection.json` chỉ chọn khi tất cả trial metrics available. Thiếu labels thì bổ sung annotation và version output, không ép select.

### Bước G — Quyết định có mở adaptive hay giữ fixed

Thực hiện T11 theo PLAN trước A1: B/D endpoints, dev oracle O0/headroom, E(q) bins so với chênh lệch utility, best constant, query-only control và shuffled-E controls seeds `[11,23,37,53,71]`.

Adaptive production hiện bị chặn; muốn chạy phải hoàn thiện phần runner/prerequisite còn thiếu, test phù hợp và cập nhật ledger, không chỉ bật mode trong JSON. Sparse S1/S2 cần checkpoint/revision/API/cost audit; C1/C2 cần mapping/score coverage và study runner; C3 cần budget/allocation study riêng. Thiếu trigger thì giữ backlog. Fixed có thể được confirm độc lập nếu adaptive không có headroom.

### Bước H — Freeze candidate chính, rồi một lần holdout

Chỉ thực hiện khi primary dev đủ labels và candidate/control đã chọn. Tạo **`TXT/configs/protocol_confirm_v1.json`** từ protocol template, bind `selected_dev_report` là **`evaluation.json` có status available của đúng candidate**; không dùng `selection.json` thay nó. Bind controls, split, thresholds và `cost_ceiling_seconds` thực. Protocol hiện `proposed_not_frozen`, các trường null chưa đủ để freeze.

Ví dụ nếu dev chọn `L1_1` trong study scored:

```powershell
python -B -m TXT.bear.cli freeze --run-dir TXT/runtime/studies/L1_dev_scored_v1/L1_1 --protocol TXT/configs/protocol_confirm_v1.json
```

Đây chỉ là ví dụ đường dẫn; thay bằng trial **thật sự được dev chọn**. Output `<selected_run>/frozen.json` bind candidate/control/code/protocol/split/selection hashes. Chốt candidate chính trước khi xem holdout; không lần lượt thử fixed/adaptive/chunk trên cùng holdout đã mở.

Annotation holdout dùng config version riêng, `split=holdout`, `frozen_candidate` trỏ file frozen, chỉ liệt kê candidate/controls đã freeze. Nhận nhãn reviewed ở file holdout riêng. Tạo **`TXT/configs/evaluation_holdout_v1.json`** với hashes thật, metric/coverage đúng protocol, `split=holdout`, frozen path và output riêng.

**Trước gọi chấm:** kiểm schema, đủ labels, hashes, metric/k/coverage, candidate/control và contamination bằng quy trình đọc/validate độc lập. `evaluate_runner.py` hiện ghi `holdout_exposure.json` **trước** một số kiểm metric/coverage/qrels; lỗi sau đó vẫn có thể đã tiêu lần mở. Không dùng lệnh holdout để thử config. Không xóa marker để chấm/chọn lại.

Với PLARGE, gọi **một lần compare** cho candidate chính so R0; không gọi evaluate thử trước:

```powershell
python -B -m TXT.bear.cli compare --baseline-dir TXT/runtime/runs/R0 --candidate-dir TXT/runtime/studies/L1_dev_scored_v1/L1_1 --config TXT/configs/evaluation_holdout_v1.json
```

Nếu cần nhiều confirmatory controls trong cùng exposure, hoàn thiện orchestration theo protocol trước khi mở; runner hiện không cho gọi lại compare nhiều lần trên cùng frozen candidate. Guard local không thay thế việc review contamination. `confirmatory_eligible=false` phải được nêu trong kết luận dù CLI vẫn tính được metric.

## 8. Có kết quả rồi phải làm gì?

Trước khi nhìn con số gain, xác nhận: input/hash đúng, run completed, cùng pool/components/chunk policy, cùng planned query universe, metric hợp coverage và evaluator được ghi tên rõ.

| Kết quả | Việc cần làm |
|---|---|
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
Runtime/RAM/I/O/GPU/annotation cost đã đo; trường nào chưa đo
Integrity/parity, lỗi/missingness và kết quả âm
Quyết định keep/reject/inconclusive, lý do, bước tiếp và rollback
```

Cập nhật `IMPLEMENTATION_STATUS.md`, `RESULTS.md`, `DECISIONS.md`, `KNOWN_LIMITATIONS.md` và handover theo kết quả thật. Giữ lịch sử, không ghi đè report cũ để che trial thua. Nếu có kết quả server mới, lưu liên kết submission/run/hash/config với scoring archive trước khi đổi baseline.

## 9. Khi nào và cách xuất submission?

Technical package và quyết định chọn phương pháp là hai mốc riêng. Không xuất pilot như thể BEAR đã áp dụng đủ tập, không tự upload/promote.

1. R0 đã qua parity và giữ nguyên làm rollback.
2. Candidate có bằng chứng phù hợp, config/parameters đã freeze. Copy pilot feature config thành **`TXT/configs/l0_full_v1.json`**, đặt `query_ids_path=null`, output mới (ví dụ `TXT/runtime/features/full_v1`). Run config full phải trỏ `feature_manifest` tới manifest mới này và giữ đúng frozen parameters. Không tune lại từ holdout. Đối chiếu subset đã đánh giá vẫn có hành vi tương đương, ghi full run provenance.
3. Kiểm full ranking đủ 1.200×200, membership/non-VI slots/missing feature/fallback đúng policy. Có 1.200 rows do baseline fallback chưa đủ để chứng nhận full BEAR inference.
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

1. Đọc các nguồn ở mục 1, kiểm dirty state và input hiện có; đừng tạo lại bộ BEAR từ đầu.
2. Chạy help/tests và R0 dry-run. Nếu chưa nhận dữ liệu, bàn giao **danh sách 14 roles R0 còn thiếu + query/source/label dependency theo bước**, tiếp tục phần adapter/fixture độc lập nếu có task phù hợp.
3. Khi đủ snapshot, bind paths/hash → audit → R0 execute → parity → pool/sample → smoke2/L0. Sau mỗi mốc cập nhật report bằng số đo thật.
4. Có L0 hợp lệ mới tạo menu predictions, annotation reviewed và dev selection. Chưa đủ điều kiện thì giữ T11–T15 ở trạng thái deferred tương ứng.
5. Kết thúc lượt làm việc bằng: đã chạy lệnh nào, output ở đâu, bằng chứng gì, blocker còn lại, quyết định và **bước kế tiếp cụ thể**.

Prompt ngắn có thể giao cho AI tiếp quản:

> Đọc `TXT/TXT_handover.md` và các file được chỉ dẫn, đối chiếu code/config hiện tại. Tiếp tục task đầu tiên đủ dependency trong `TXT/reports/IMPLEMENTATION_STATUS.md`; mọi file/output mới dưới TXT. Ưu tiên nhận/bind snapshot và tái lập R0 trước benchmark. Không nhầm fixture/proxy với quality gain, không dùng feedback làm qrels, không tự mở holdout, chạy GPU nặng hoặc nộp bài khi chưa đủ điều kiện. Hoàn tất phần được giao và ghi report kết quả/blocker cùng bước tiếp theo.
