# BEAR 2.0 — Cấu hình và thứ tự chạy

Backend **2.0.0** triển khai phần CPU của PLAN N0–N5. Các JSON tại đây là templates có paths rõ; chưa có snapshot/qrels/passages thật. Không đổi hash rỗng thành hash giả hoặc chạy mọi lệnh thành một batch bỏ qua lỗi. Tất cả lệnh tính từ repo root; thiết lập temp/cache theo handover.

```powershell
python -B -m TXT.bear.cli --version
python -B -m TXT.bear.cli --help
```

## N0 — Provenance

```powershell
python -B -m TXT.bear.cli provenance --config TXT/configs/next_round/provenance_v2.json --dry-run
```

Đã execute inventory trên checkout và lưu [report N0](../../reports/next_round/N0_provenance_v1.md). Thiếu18roles:14R0, baseline manifest và3R01 artifacts. Kết quả người dùng báo vẫn giữ REPORTED; không tự nối ba ZIP root. Khi nhận dữ liệu, bind paths/expected_sha256 thật và dùng output N0 version mới; manifest completed cũ không được overwrite.

`linkage_record` tùy chọn là JSON human-reviewed gồm `reviewer`, `adjudication="reviewed"`, `submission_id`, `submission_sha256`, `scoring_output_sha256`, `candidate_manifest_sha256`. Code kiểm hashes trùng inventory và candidate manifest verified; không suy liên kết từ tên file. Baseline verification cần run manifest parity thật, không dùng snapshot `manifests/baseline.json` chưa reproduced.

## N1 — Audit applicability

Bind `application_audit_v2.json.run_dir` tới đúng directory R01 có manifest/candidates/ranking_details. Công cụ replay inference từ config/features/pool để phát hiện output không khớp; đọc input, chỉ ghi audit dưới output_dir.

```powershell
python -B -m TXT.bear.cli application-audit --config TXT/configs/next_round/application_audit_v2.json --dry-run
python -B -m TXT.bear.cli application-audit --config TXT/configs/next_round/application_audit_v2.json --execute
```

Output: `application.json`, `per_query.jsonl`, `report.md`, manifest. Flags feature/eligible/applied/bypass/fallback/order/docset có thể giao nhau, mẫu số là expected_queries. Score coverage/chunk changes chưa có input thì null. Fixed eligibility không dùng route_eligible. Corpus/query IDs/scope thực lấy từ artifacts, không mặc định BEAR đã áp dụng full1200.

## N2 — Body/local, cùng budget

```powershell
python -B -m TXT.bear.cli tune --protocol TXT/configs/next_round/tune_body_local_v2.json --menu TXT/configs/next_round/menus_v2.json --dry-run
```

Family `L1_L4` đăng ký12trials: L1 body và L4 local_max_all cùng λ `[0,.02,.05,.10,.20,.35]`. Cũng hỗ trợ family L1/L4 riêng và F0 cũ. Sau khi có verified pool/features mới thêm `--execute` để tạo predictions. evaluation_config=null chỉ diagnostic, selection inconclusive.

Trước dev selection: export blinded annotation union added/removed của **cả12** `N2_v1/L1_i/candidates.jsonl` và `N2_v1/L4_i/candidates.jsonl`; nhận nhãn reviewed; bind evaluation config thật vào protocol mới và dùng output version khác để scoring. Không chọn best trên subset label khác nhau giữa trials. Không mở holdout ở bước này.

## N3 — Chunk C1/C2

```powershell
python -B -m TXT.bear.cli chunk-study --config TXT/configs/next_round/chunk_c1_v2.json --dry-run
python -B -m TXT.bear.cli chunk-study --config TXT/configs/next_round/chunk_c2_v2.json --dry-run
```

Đủ corpus/ranking/rounded allocation/chunk_scores và C2 chunk features mới `--execute`. Ranking phải đúng snapshot corpus; allocation doc order phải đúng ranking. Query_ids_path chọn pilot IDs, hỗ trợ IDs không liên tiếp. Giữ doc set/order/head/allocation và actual per-doc slots; score thiếu → chunk đầu, out-of-range namespace → error. C2 đối chiếu refs/hash native, không dùng body score thay score từng chunk.

Output gồm selected/control `records.json`, `chunk_refs.jsonl`, `selection_details.jsonl`, candidates, summary và manifest. Tokens/chars được báo như budget thực; ZIP bytes=null vì chưa nén.

Local passages JSONL cần: `query_id`, `doc_id`, `start`, `end`, `body_sha256`, `reference_source`, `annotator`, `adjudication="reviewed"`, `label_policy_version`. Phải nhận từ reviewer; không sinh nhãn bằng coding AI. Bind passages_hash/split_hash thật trong evaluate_chunks_dev_v2.json.

```powershell
python -B -m TXT.bear.cli preflight --run-dir TXT/runtime/next_round/N3_v1/C1 --config TXT/configs/next_round/evaluate_chunks_dev_v2.json
python -B -m TXT.bear.cli evaluate-chunks --run-dir TXT/runtime/next_round/N3_v1/C1 --config TXT/configs/next_round/evaluate_chunks_dev_v2.json
```

`local_passage_recall` = tỷ lệ reviewed references có match LCS/gold_tokens≥.40 cùng query/doc. Tokenizer local NFKC/HTML/lowercase/whitespace. Đây là **diagnostic trên local references**, không official Chunk F2 hay full-corpus recall. Report có paired delta so control và `official_equivalent=false`.

## N4 — Routing diagnostics

Sau N2, chạy menu F0 bằng các B/D sources verified. Bind lexical/semantic/fixed dev evaluation reports, feature manifest và query metadata JSONL gồm `query_id`, `query_length`, `language_view`, `length_bin` đã preregister.

```powershell
python -B -m TXT.bear.cli routing-diagnostics --config TXT/configs/next_round/routing_diagnostics_v2.json --dry-run
```

Đủ inputs mới execute. Reports phải available/dev, cùng metric/split/qrels/baseline và query universe. Có oracle headroom, E bins, endpoint rule, query-length rule và shuffled-E seeds11/23/37/53/71. Đây là diagnostics, **không phải matched-budget A1 tuning/controls**; adaptive_ready=false, production guard vẫn đóng. Không bỏ guard hoặc gọi silver/aggregate scores là qrels để qua dependency.

## N5 — Freeze, preflight, một lần holdout và export

Chọn một candidate trên dev đúng cùng primary scope, interactions trước freeze. Protocol cần selected_dev_report là evaluation.json available/dev đúng candidate hash, controls, split_manifest, positive cost_ceiling_seconds. Chunk candidate còn cần records_sha256 từ chunk evaluation report. Freeze bind candidate manifest/artifacts và evaluation contract.

`freeze --run-dir <selected-run> --protocol <bound-protocol>` ghi frozen artifact ngay. Với holdout config đã bind, dùng `preflight --run-dir <selected-run> --baseline-dir <control-run> --config <evaluation>` trước khi document compare; chunk preflight không cần baseline-dir vì control nằm trong cùng chunk study.

Preflight không trả scores và không ghi exposure; lỗi metric/labels/contract chưa tiêu lần mở. Lệnh evaluate/compare/evaluate-chunks thật mới exclusive-claim sau validation, chỉ một lần. Không xóa marker. Multi-control confirmatory trong cùng exposure chưa orchestration; hoàn thiện trước nếu protocol đòi nhiều controls.

Full inference giữ frozen params, query_ids_path=null, output mới. `export --run-dir <full-run> --config <bound-export>` mặc định dry-run; `--execute` mới package. Release kiểm1200×200/membership/native offsets, giữ selected C1/C2 thay vì quay về legacy selector, kiểm corpus/head/actual slots và ZIP readback. Chưa có full package thật trong checkout; không tự upload hoặc promote.
