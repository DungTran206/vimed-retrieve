# Cấu hình BEAR 2.0 — N0–N5 lịch sử

Cập nhật **20/10/2026**: [PLAN v3.3, A0–A4](../../PLAN.md) dùng **pipeline 0,391**; xem [bản pipeline từ ảnh](../../PIPELINE_0391.md), [hồ sơ baseline](../../reports/BASELINE_0391_20261020.md), [runbook](../../reports/RUNBOOK.md). JSON tại đây giữ để tra cứu/tái lập kỹ thuật, **không là chuỗi chạy mặc định mới**.

N0/N1 đã có đáp án từ lần chạy 1200 câu được báo. L1/L4 trên 0,4076 không tăng đáng tin nên đóng cấu hình đó; đổi baseline không mở lại 12 trials. Không bắt gán tay toàn bộ, không chạy routing/chunk để hoàn thành checklist. Xem [L1/L4](../../reports/L1_L4_20261020.md).

## Các template giữ lại

| File | Chức năng 2.0 | Cách dùng |
|---|---|---|
| provenance_v2.json | Inventory/linkage artifacts cũ | Khi cần kiểm một liên kết cụ thể; không là cửa kiểm bắt buộc. |
| application_audit_v2.json | Replay/audit mức áp dụng | N0/N1 đã có báo cáo, không bắt làm lại. |
| menus_v2.json, tune_body_local_v2.json | Sáu λ L1, sáu λ L4 | Lịch sử, không tiếp tục tuning hiện tại. |
| chunk_c1_v2.json, chunk_c2_v2.json | Chunk native/allocation cũ | Có thể tái dùng scaffolding cho C1 khi nối đúng0,391; không áp full-body0,4076. |
| evaluate_chunks_dev_v2.json | Local passage recall/nhãn reviewed | Diagnostic local, không thay official Chunk F2. |
| routing_diagnostics_v2.json | Oracle/Ebins/rules/shuffles | Diagnostic, không là production routing. |

Backend vẫn **2.0.0**. Không điền hash giả hoặc ghi đè completed runtime để làm như có kết quả. [Reports ngày 19/10](../../reports/next_round/V2_IMPLEMENTATION.md) phản ánh checkout khi đó, không phủ nhận lượt chạy ngoài checkout.

## Hướng hiện hành: chọn doc và chunk

[BEAR_ALGORITHM](../../BEAR_ALGORITHM.md) yêu cầu selected_docs và selected_chunks. A0baseline adapter →A1evidence có cấu trúc →A2doc selector →A3chunk selector →A4B0/D1/C1/DC1. Pilot tối đa3candidate mới và1control, giữ budgets để cô lập từng selector.

Audit và threshold tuning là hỗ trợ, không thay retrieval. JSON tại đây là template lịch sử, chưa tự đáp ứng parser/structured conflict hoặc variable-k/export0,391. [Spec tham chiếu](../../specs/pipeline_0391.json) không chạy CLI. Không giả annotator/hashes, không ép200doc hoặc ngầm đổi policy chunk.

## Khi cần công cụ cũ

Từ repo root, ví dụ chỉ đọc thông tin/dry-run:

    python -B -m TXT.bear.cli --version
    python -B -m TXT.bear.cli --help
    python -B -m TXT.bear.cli provenance --config TXT/configs/next_round/provenance_v2.json --dry-run

Chỉ bind input thật, config/output mới cho một chức năng cụ thể. Không chạy batch N0–N5 thay phép đo nhỏ mà PLAN yêu cầu.
