# Chuẩn bị BEAR doc/chunk trên baseline0,391

**Hiện hành PLAN3.5:** hai phần Retriever/Fusion đã có prototype và [configs riêng](../bear_parts/README.md). Các inventory F1/pilot3.3 bên dưới là lịch sử chuẩn bị, không thay lệnh retrieve/evidence-fuse và không buộc Retriever phải đọc pool baseline.

## F1 — Thay fusion trước top300 (thiết kế3.4)

[Replacement study](../../BEAR_REPLACEMENT_STUDY.md) ưu tiên BEAR chọn lại ứng viên trên union ba nguồn VI trước fusion. Inventory riêng:

    python -B -m TXT.bear.cli provenance --config TXT/configs/bear_doc_chunk/preflight_replacement_f1.template.json --dry-run

Config này được CLI provenance hiện có nhận, **không chạy inference F1**. Role source rankings phải chứa từng nguồn trước cắt top300, union/dedup và candidates ZH đóng băng; pool cuối340 không đủ. Runtime policy cần đúng Qwen/MaxP/p̂/threshold và chunk/export0,391. Qwen cache bao phủ doc mới hoặc khả năng chạy bổ sung cần kiểm riêng, chưa nằm trong phép kiểm hiện diện file này. Structured evidence/adapter/runner vẫn cần triển khai.

Đã chạy dry-run20/10: exit1/blocked_input,5roles thiếu, btc_validation hiện diện; [report F1](../../reports/bear_replacement_f1_preflight_20261020.json). Không suy readiness inference từ inventory.

## Pilot selector3.3 — Inventory đã có

preflight_0391.template.json là config **provenance inventory**, được CLI hiện có nhận; không phải config inference v3.3. Hiện có5role thiếu và1role validation hiện diện; xem [readiness report](../../reports/EXPERIMENT_READINESS_20261020.md).

    python -B -m TXT.bear.cli provenance --config TXT/configs/bear_doc_chunk/preflight_0391.template.json --dry-run

Exit1 + status blocked_input là trạng thái thiếu file, không phải lỗi cài đặt. Khi có dữ liệu, copy config sang tên mới và điền path/hash thật; không dùng lại completed output hoặc ép schema cũ cho dữ liệu mới. Một manifest/source thật có thể bind nhiều role đúng nghĩa.

Inventory available vẫn chưa xác nhận schema, baseline linkage, labels hoặc implementation. Structured evidence/adapter/selector v3.3 còn cần triển khai; oldpool/export có fixed200 nên không thay bằng lệnh run cũ. [PLAN](../../PLAN.md) và [BEAR_ALGORITHM](../../BEAR_ALGORITHM.md) giữ mục tiêu selected_docs/selected_chunks.

CPU-first tái dùng scores/embeddings đã cache, xử lý query/shard và cache features một lần cho các ablation. Không tự gọi model/refit beta. [Benchmark script](../../tools/benchmark_cpu.py) đo kernel exact cũ, không phải thuật toán mới.

Máy GPU khác có thể dùng theo người dùng, nhưng chưa có thông số/môi trường được kiểm. Xem [checklist GPU và lý do từng input](../../reports/EXPERIMENT_READINESS_20261020.md#7-máy-gpu-đã-có-còn-thiếu-gì-và-ai-chuẩn-bị). Config này vẫn chỉ inventory file; GPU không làm đầy các path null hoặc hoàn thiện runner mới. Khi replay đủ cache không cần chạy lại model baseline.
