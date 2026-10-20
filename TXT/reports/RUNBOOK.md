# Runbook — Xây BEAR chọn doc và chunk

Theo [PLAN v3.3](../PLAN.md) và [BEAR_ALGORITHM](../BEAR_ALGORITHM.md). Mục tiêu output doc/chunk thực; threshold-only v3.2 không còn là kế hoạch chính. Software2.0.0 chưa có runner đầy đủ cho đặc tả mới.

## A0 — Adapter baseline

Dùng prediction/candidates/scores/corpus/query/native chunks và budget/exporter0,391 thật. Bypass trả đúng output gốc. Không tái tạo toànw045, ép k160/200 hoặc suy policychunk từ ảnh.

## A1 — Evidence có cấu trúc

Chọn một support/conflict khác uniform coverage; xuất spans, role/identity mapping, availability và fallback. Unknown khác observed no-match; evidence không tự gold hoặc hard-filter. Không trả list rỗng rồi coi detector đã xong.

## A2 — Doc selector

Kết hợp điểm nền và evidence hợp lệ, chọn lại doc theo một config pilot đã khóa và k thực từng query. Xuất selected_docs/added/removed. Chỉ đổi thứ tự cùng tập chưa tăng DocF2.

Nếu chỉ có VIfeatures thì ghi D1-VI và giữ non-VI/VIcount baseline làm đối chứng. Thiếu feature trong scope thì baseline fallback, không loại doc chưa có feature.

## A3 — Chunk selector

C1giữ doc set/order/slots/token budget; chọn native chunks/windows bằng evidence và score nền có thật. Xuất selected_chunks nối đúng corpus/body/offset/hash và exporter.

Không thêm text rồi gọi gain do selector. Nếu full-body duy nhất không có lựa chọn tương đương, báo C1không có headroom; ảnh chưa chứng minh policy đó.

## A4 — Ablation và joint

B0baseline; D1doc-only; C1chunk-only; DC1joint. Tối đa3candidate mới và1control cho pilot; không thêm grid. Hai selector có thể được giữ độc lập.

Chấm DocF2/ChunkF2 và FINAL bằng metric đúng scope/scorer. BTC labels được dùng, unknown/weak not_gold không tự âm. K đổi cần hits control/sensitivity cả docs giữ nguyên; giữ query universe và report fallback.

Audit phục vụ debug/kiểm feature, threshold/count tuning phục vụ operating point hoặc control phụ. Chúng không thay output retrieval.

## Công cụ và ghi kết quả

[JSON tham chiếu](../specs/pipeline_0391.json) không chạy CLI; [configs N0–N5](../configs/next_round/README.md) là scaffolding lịch sử. Evaluator/exporter fixed200/reviewed còn cần adapter.

Khi thực thi, output mới dướiTXT/runtime/bear_doc_chunk/run_id và nối [log](../improvement_log.md). Lượt này chưa triển khai parser/selector mới, tạo run hoặc đo gain.

## Kiểm tra chuẩn bị thực tế và đo CPU

[Readiness20/10](EXPERIMENT_READINESS_20261020.md) ghi code còn thiếu và5input roles chưa có. Từ repo root:

    python -B -m TXT.bear.cli provenance --config TXT/configs/bear_doc_chunk/preflight_0391.template.json --dry-run

Exit1 cùng blocked_input là kết quả khi thiếu file, không phải lỗi cài đặt. Không chạy --execute hoặc oldrun/export để giả BEARv3.3. Config chỉ inventory, không inference.

Đo kernel CPU cũ, không tải model:

    python -B -m TXT.tools.benchmark_cpu --output TXT/runtime/bear_doc_chunk/cpu_probe_new.json

Output mới dùng tên khác khi đo lại. Benchmark synthetic chỉ kernel exact, không tính structured extraction/I/O/evaluation/export. Khi A0–A3 đủ inputs/code, đo20query thật đại diện, cache feature một lần và kiểm RAM trước fullB0/D1/C1/DC1. Model inference mới có dự toán riêng.
