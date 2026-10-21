# Medical importance gate — templates

Đọc [handover](../../TXT_handover.md) trước khi chạy. Sao chép template vào một config riêng dưới TXT, điền input thật và output_dir mới. Chạy từ repository root bằng `python -B -m TXT.bear.medical_cli <stage> --config <path> --execute`; mặc định chỉ inspect.

Thứ tự: `kb-import` → `prepare` → `cache` → `fit` → `tune` → `run` → `evaluate`. Lệnh `document-terms` là nhánh tùy chọn, không tự đưa terms vào index. Demo offline: `python -B -m TXT.bear.medical_cli demo`.

Các thông số trong template là khởi tạo để chạy thí nghiệm, chưa là optimum. Fit ghi đè x0/temperature bằng kết quả calibration; min_docs/max_docs chỉ là ví dụ budget, không phải quota baseline. Dense affine [-1,1] chỉ đúng nếu input có score cosine tương ứng; sửa normalizer theo artifact thật. mean-doc budget dùng để so sánh gần cùng chi phí với control.

`cache.bm25_source=null` tính BM25 original/expanded bằng cùng BEAR index trên source union, không dùng điểm BM25F lịch sử làm cùng recipe. Nếu chọn điểm BM25F ngoài, dùng `bm25_source:"bm25"`, đưa score expanded tương ứng hoặc đặt enrichment_weight=0, và dùng pretransform=raw; query_scale của index không tương thích.

`sources` JSONL: `{id, candidates:[{doc_id,score}]}` cho từng query (có thể candidates rỗng). Score tables bổ sung `score_tables:{dense_head:"...",dense_chunk:"..."}` JSONL `{id,doc_id,score}` để chấm đầy đủ union; không có trong top-K không đồng nghĩa score=0. Theo dõi missing masks trong cache.

`include_index_candidates=true` mở rộng union bằng lookup original/expanded: đây là thí nghiệm retrieval thay đổi membership, không gọi là BF cùng union. Phải tính thêm dense/reranker cho doc mới nếu cần; dữ liệu thiếu không được gán 0. Cache rộng cố định phục vụ sweep, chưa đánh giá được doc ngoài cache.

Val hiện có đã được khai thác: template ghi previously_observed_ids=all, holdout là retrospective. Tài liệu chưa có judgment là unknown. Adapter native dùng gold/not_gold như nhãn do file cung cấp; cần ghi nhận nếu not_gold là weak label. `known_positive_recall` là mặc định; muốn tune proxy F2 có thể chọn objective=known_positive_f2_proxy và allow_incomplete_f2=true, tên kết quả vẫn là proxy.

Trước khi thay tier_mode=expected, nhập đủ bốn xác suất backend_label_logits/backend_label_probabilities cùng probability_provenance. Không lấy confidence do model tự viết làm softmax.
