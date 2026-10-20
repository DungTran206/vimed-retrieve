# Chuẩn bị BEAR doc/chunk trên baseline0,391

preflight_0391.template.json là config **provenance inventory**, được CLI hiện có nhận; không phải config inference v3.3. Hiện có5role thiếu và1role validation hiện diện; xem [readiness report](../../reports/EXPERIMENT_READINESS_20261020.md).

    python -B -m TXT.bear.cli provenance --config TXT/configs/bear_doc_chunk/preflight_0391.template.json --dry-run

Exit1 + status blocked_input là trạng thái thiếu file, không phải lỗi cài đặt. Khi có dữ liệu, copy config sang tên mới và điền path/hash thật; không dùng lại completed output hoặc ép schema cũ cho dữ liệu mới. Một manifest/source thật có thể bind nhiều role đúng nghĩa.

Inventory available vẫn chưa xác nhận schema, baseline linkage, labels hoặc implementation. Structured evidence/adapter/selector v3.3 còn cần triển khai; oldpool/export có fixed200 nên không thay bằng lệnh run cũ. [PLAN](../../PLAN.md) và [BEAR_ALGORITHM](../../BEAR_ALGORITHM.md) giữ mục tiêu selected_docs/selected_chunks.

CPU-first tái dùng scores/embeddings đã cache, xử lý query/shard và cache features một lần cho các ablation. Không tự gọi model/refit beta. [Benchmark script](../../tools/benchmark_cpu.py) đo kernel exact cũ, không phải thuật toán mới.

Máy GPU khác có thể dùng theo người dùng, nhưng chưa có thông số/môi trường được kiểm. Xem [checklist GPU và lý do từng input](../../reports/EXPERIMENT_READINESS_20261020.md#7-máy-gpu-đã-có-còn-thiếu-gì-và-ai-chuẩn-bị). Config này vẫn chỉ inventory file; GPU không làm đầy các path null hoặc hoàn thiện runner mới. Khi replay đủ cache không cần chạy lại model baseline.
