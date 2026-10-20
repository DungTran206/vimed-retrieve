# Handover — BEAR Doc & Chunk Retrieval

Cập nhật20/10/2026, [PLAN v3.3](PLAN.md), software2.0.0. Người dùng xác nhận BEAR nhằm tạo thuật toán retrieve doc và chunk; v3.2 chỉ audit/threshold đã được thay.

## 1. Đọc trước

[BEAR_ALGORITHM](BEAR_ALGORITHM.md) →[pipeline0,391](PIPELINE_0391.md) →[proposal](TXT_Proposal.md) →[PLAN](PLAN.md). [JSON](specs/pipeline_0391.json) là tham chiếu, không config CLI.

## 2. Control và lịch sử

Baseline0,391: ảnh ghi300VI+40ZH ứng viên →Qwen/MaxP/p̂/threshold, mean khoảng160doc/query. Chưa có đầy đủ run/config/metrics hoặc chunk nộp; không ép k160/200,40ZH cuối hoặc chunk=body từ “Lấy full”.

w045FINAL0.3442 và TXT/BEARFINAL0.3445 giữ lịch sử. L1/L4 trên0.4076 có best ΔDocF2+0.0003/+0.0004, CI95 chạm0/âm theo báo cáo; không chạy lại uniform coverage dưới tên mới. N0/N1 w045 đã được báo đủ1200câu/parity100%/5.5doc đổi, không làm lại như prerequisite.

## 3. Công việc cần xây

| Bước | Output cần có |
|---|---|
| A0adapter | Nối control/candidates/scores/native chunks/budget; bypass đúng baseline |
| A1evidence | Một support/conflict có identity/role/điều kiện, span/mapping/availability/fallback |
| A2doc | selected_docs: chọn lại tập doc theo score BEAR, pilot giữ k thực từng query |
| A3chunk | selected_chunks: native chunks/windows nguyên văn cùng slots/token budget, nối exporter |
| A4joint | B0/D1/C1/DC1 và metric riêng doc/chunk/joint |

A2/A3 có thể phát triển độc lập. Chỉ flags/report chưa hoàn tất BEAR; threshold study chỉ là công cụ operating point.

## 4. Đối chứng và nhãn

B0baseline cả hai tầng; D1đổi doc selector/giữ chunk policy; C1giữ doc set/order/slots và đổi chunk selector; DC1ghép hai selector. Tối đa3candidate mới và1control trong một pilot, không thêm grid.

D1-VI nếu chỉ có mapping VI đáng tin: giữ non-VI và VI count baseline làm đối chứng, không nói baseline có quota ZH cuối. Nếu full-body duy nhất không có lựa chọn dưới cùng budget, ghi C1không có headroom ở scope đó.

BTC val được dùng; không giả annotator hoặc gán tay lại593câu. not_gold suy từ chunk có thể âm giả, unknown không tự âm;±0.0002/tổng305 không phải bound. D1fixed-k cần judgments changed docs; k đổi cần hits control/sensitivity cả docs giữ nguyên. C1giữ budget; local LCS không tự official ChunkF2, ΔDoc không tự ΔFINAL.

## 5. Code đã có/gap

2.0.0 có matcher, uniform/local/critical coverage, fusion và C1/C2scaffolding. Structured relation/conflict mới chưa triển khai; critical_mismatches có chỗ trả list rỗng. Không xem placeholder là detector xong.

Runner/evaluator/exporter còn assumptions w045/fixed200/manual-qrels. Cần adapter0,391 và policy chunk thật. Rootval_calib cóMaxP/beta8/10 nhưng chưa liên kết run; không tự refit.

Dùng input thật cho A0/A1, thiếu phần nào ghi scope phần đó và làm phần độc lập. Mọi output mới dướiTXT, nguồn/completed artifacts chỉ đọc. [Runbook](reports/RUNBOOK.md), [logD06](improvement_log.md) hướng dẫn tiếp. Chưa có implementation structured-retrieval hoặc benchmark relevance mới.

## 6. Chuẩn bị chạy và CPU/GPU — đã kiểm20/10

[Readiness report](reports/EXPERIMENT_READINESS_20261020.md) và [JSON preflight](reports/bear_doc_chunk_preflight_20261020.json):blocked_input,5roles thiếu, chỉ btc_validation hiện diện. data/ chỉ có .gitkeep; không tự dùng ZIP lịch sử chưa liên kết làm control0,391.

[Config preflight](configs/bear_doc_chunk/preflight_0391.template.json) chạy bằng CLIprovenance --dry-run; exit1 là thiếu input. Đây là inventory A0, không chạy BEARv3.3. Bind paths thật trên máy có dữ liệu, đồng thời bổ sung code A1–A3 còn thiếu.

CPU chạy được nhánh cached-score+feature nhẹ; chưa cam kết toàn bộ structured relation extraction chỉ cần CPU. Máy đo i5-1135G7/8luồng/RAM7.8GiB, RAM trống lúc đo0.7GiB: khởi đầu streaming1worker. Kernel cũ ngoại suy khoảng9/39/153phút cho408kpair ở body4k/20k/80kchar; chưa tính I/O/feature mới/scorer/export. ETA end-to-end chưa có, cần20query thật sau khi đủ input/code. [Script benchmark](tools/benchmark_cpu.py) không tải model.

[LogD07](improvement_log.md) ghi kiểm tra này; không biến số CPU tổng hợp thành chất lượng retrieval.

**Cập nhật GPU:** người dùng sẵn sàng dùng máy GPU khác, chưa biết thông số. Không chờ hardware để viết code, cũng chưa coi môi trường/model đã sẵn. [Readiness §7](reports/EXPERIMENT_READINESS_20261020.md#7-máy-gpu-đã-có-còn-thiếu-gì-và-ai-chuẩn-bị) tách dữ liệu cần lấy từ máy baseline, code agent phải triển khai, nhãn/scorer và môi trường máy GPU. Tái dùng cache khi đủ; GPU chỉ dùng cho phần model cần tính mới. Không ép nhánh CPU hoặc cam kết ETA từ cấu hình chưa kiểm; [logD08](improvement_log.md) ghi quyết định này.
