# BEAR runbook

Chạy từ repo root với Python hiện có. --help không đọc corpus và không import NumPy/pandas/torch.
CLI tự trỏ temp/model cache vào TXT/runtime khi chạy command; tests cần đặt TEMP/TMP trước.

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TEMP = Join-Path (Get-Location) 'TXT/runtime/tmp'
$env:TMP = $env:TEMP
$env:TMPDIR = $env:TEMP
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
python -B -m TXT.bear.cli --help
python -B -m unittest discover -s TXT/tests -t . -v
python -B -m unittest discover -s tests -v
```

Các lệnh dưới đã được kiểm tra ở chế độ đọc/dry-run. Hiện audit, R0, pool và features báo blocked_input, exit1 đúng dự kiến. Không nối chúng thành một chuỗi execute bất kể lỗi.

```powershell
python -B -m TXT.bear.cli audit --config TXT/configs/readiness.json
python -B -m TXT.bear.cli reproduce --config TXT/configs/reproduce.json --dry-run
python -B -m TXT.bear.cli pool --config TXT/configs/pool_v1.json --dry-run
python -B -m TXT.bear.cli features --config TXT/configs/l0_pilot.json --dry-run
python -B -m TXT.bear.cli tune --protocol TXT/configs/tune_l1.json --menu TXT/configs/menus_v1.json --dry-run
```

Sau khi nhận snapshot, đặt trong TXT/inputs/handover/data theo cây gốc, sửa readiness/reproduce paths và expected_sha256 từ file thật. Readiness cũ trỏ data/ để ghi nhận checkout hiện tại; reproduce template trỏ vị trí nhận handover mới. Chưa có source hash thì giữ null, không điền giả.

Các lệnh execute sau **đã implement nhưng chưa verified trên dữ liệu thật**:

```powershell
python -B -m TXT.bear.cli reproduce --config TXT/configs/reproduce.json --execute
python -B -m TXT.bear.cli pool --config TXT/configs/pool_v1.json --execute
python -B -m TXT.bear.cli sample --config TXT/configs/sample_v1.json --execute
python -B -m TXT.bear.cli features --config TXT/configs/l0_smoke.json --execute
python -B -m TXT.bear.cli features --config TXT/configs/l0_pilot.json --execute
python -B -m TXT.bear.cli run --config TXT/configs/run_l1.json --execute
python -B -m TXT.bear.cli tune --protocol TXT/configs/tune_l1.json --menu TXT/configs/menus_v1.json --execute
python -B -m TXT.bear.cli annotation-export --config TXT/configs/annotation_dev.json --execute
```

R0 cần NumPy; membership parquet cần pandas/pyarrow hiện có hoặc cài vào TXT/.venv sau khi cần thật. Không tự cài requirements-train. Pool mặc định chưa có B/D sources, vì chưa có provenance. Thêm source manifest entries verified và artifact/corpus/query hashes trước F0; support lấy B verified, không lấy ranking output gate.

sample ghi split.json và smoke_ids.json theo seed42. Smoke2 chỉ là kiểm I/O; không tune hoặc dùng làm representative estimate. Pilot sử dụng sampled_ids đã freeze. Queries chưa có feature sẽ fallback reference, có explanation.

L1 tune mặc định evaluation_config=null: tạo predictions và ledger diagnostic, không chọn best. annotation_dev.json hiện minh họa một prediction; trước annotation study thật phải liệt kê **tất cả** predictions trong menu preregister. Với P200 dùng topk40; PLARGE dùng differences200.

Người review điền grade/annotator/support offsets/adjudication, đặt qrels đã review dưới TXT/inputs/evaluation. Copy evaluation_dev.template.json thành config version riêng, điền qrels/split SHA256 thật. Không chỉnh grade threshold sau kết quả. Doc F2 cần label_coverage_manifest complete-universe; topK/differences không suy full recall.

Sau đó dùng CLI evaluate/compare với --config và --run-dir hoặc --baseline-dir/--candidate-dir. Tuning config chỉ trỏ evaluation config dev. Freeze dùng --run-dir và --protocol; protocol cần selected_dev_report, controls, split_manifest, cost_ceiling_seconds thực. Holdout config cần frozen_candidate; evaluation lần2 bị reject. Không sửa marker để chọn lại.

Export có CLI --run-dir, --config TXT/configs/export.json --execute. Nó đòi full1200×200, calibration inputs, corpus/offset/hash, rồi gọi LZMA768MiB và testzip/readback/<100000000bytes. Không chạy cho fixtures hoặc pilot; không tự upload. Output technical package không đồng nghĩa phương pháp đã được promote.

Mọi run có manifest partial/completed. Reuse completed chỉ khi code/config/input hashes giống; khác hash cần run_id/output_dir mới. Không sửa trực tiếp completed artifacts. Giữ R0 exact làm rollback sau khi reproduction thành công.

Adaptive production, sparse encoder, C3 allocation và discovery chưa mở theo prerequisite trong PLAN. Không có CLI giả cho các nhánh này; xem task ledger để tiếp quản.
