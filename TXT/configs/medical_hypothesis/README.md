# Medical fusion v5 — templates

Đọc [handover](../../TXT_handover.md) trước khi chạy. Sao chép template vào một config riêng dưới TXT, điền input thật và output_dir mới. Chạy từ repository root bằng `python -B -m TXT.bear.medical_cli <stage> --config <path> --execute`; mặc định chỉ inspect.

Thứ tự mới: `kb-import` → `prepare` → `cache` → `document-terms` → `sapbert-cache` → `fit` → `tune` → `run` → `evaluate`. `select` là LLM cherry-pick tùy chọn giữa run và evaluate. Tất cả templates ghi vào `TXT/runtime/medical_v5/`; dùng thư mục mới cho mỗi recipe. Demo offline: `python -B -m TXT.bear.medical_cli demo --output-dir TXT/runtime/medical_v5_demo_001`.

Fusion vẫn là `F=alpha*z_B+(1-alpha)*D_new`, với `D_new=(1-lambda)*D_generic+lambda*S_sapbert`. Gate chỉ nhận exact/source-backed alias của original concepts; SapBERT không tăng gate. `S_sapbert` được tổng hợp từ ma trận query-concept ↔ literal-document-term, không cần thêm encoder toàn document. Library mặc định lambda=0 để tương thích; v5 fit template khởi tạo `sapbert.weight=0.3`. Tune cả 0, mixture và 1 để đo control/mix/replacement.

Các thông số trong template là khởi tạo để chạy thí nghiệm, chưa là optimum. Fit ghi đè x0/temperature bằng kết quả calibration; min_docs/max_docs chỉ là ví dụ budget, không phải quota baseline. Dense affine [-1,1] chỉ đúng nếu input có score cosine tương ứng; sửa normalizer theo artifact thật. mean-doc budget dùng để so sánh gần cùng chi phí với control.

`sapbert_cache.template.json`: điền `encoder.local_path` trỏ snapshot checkpoint thật. Mặc định CLS trước pooler, L2, max_length=64, batch_size=64, local_files_only=true, overflow=error; không tự download. Có thể dùng model ID với revision SHA bất biến và local_path=null nếu checkpoint đã ở local HF cache. Torch/Transformers chỉ cần khi encode thật. Để dùng vectors đã tính ở máy GPU, thêm `embeddings_input` JSONL `{text,embedding,encoder,provenance,token_count,truncated}`; `encoder` phải cùng recipe, token_count tính trước truncation có special tokens. Không dùng revision/vector minh họa synthetic của demo làm input thật.

`document_terms.template.json` lấy unique doc IDs từ base cache và gọi LLM một lần/doc; cũng nhận `doc_ids_path` JSON list thay cho cache. Term phải có title/body span thật, language và corpus hashes; nhãn assertion được giữ để audit. `sapbert-cache` kiểm nguồn rồi lưu embeddings theo text và toàn bộ cosine matrix để tune lambda, tier weights và affine/sigmoid transform mà không encode hay gọi LLM lại. Không có term là missing evidence, không tự gán score 0.

`cache.bm25_source=null` tính BM25 original/expanded bằng cùng BEAR index trên source union, không dùng điểm BM25F lịch sử làm cùng recipe. Nếu chọn điểm BM25F ngoài, dùng `bm25_source:"bm25"`, đưa score expanded tương ứng hoặc đặt enrichment_weight=0, và dùng pretransform=raw; query_scale của index không tương thích.

`sources` JSONL: `{id, candidates:[{doc_id,score}]}` cho từng query (có thể candidates rỗng). Score tables bổ sung `score_tables:{dense_head:"...",dense_chunk:"...",sapbert:"..."}` JSONL `{id,doc_id,score}` để chấm đầy đủ union; không có trong top-K không đồng nghĩa score=0. Imported sapbert score là raw cosine; không cung cấp đồng thời imported cosine và ma trận cho cùng candidate. Theo dõi missing masks trong cache. Điền `source_recipes` bằng checkpoint/revision/pooling/normalization/chunking của các sources ngoài để model binding phát hiện thay recipe.

`include_index_candidates=true` mở rộng union bằng lookup original/expanded: đây là thí nghiệm retrieval thay đổi membership, không gọi là BF cùng union. Phải tính thêm dense/reranker cho doc mới nếu cần; dữ liệu thiếu không được gán 0. Cache rộng cố định phục vụ sweep, chưa đánh giá được doc ngoài cache.

`prepare.template.json` giới hạn max_kb_candidates=256 và max_expansion_terms=8. KB canonical hỗ trợ vi/zh/en; alias/label/has_symptom phải có nguồn. LLM chọn IDs từ whitelist theo intent và ngôn ngữ, không tự sinh bản dịch hoặc facts. CMeIE cần concept map; OpenCMKG cần chuyển canonical như handover.

`select.template.json` chỉ chọn trong shortlist từ selection của run, tối đa 40 docs, 2.000 ký tự/doc, min=0/max=40 khởi tạo. Threshold/top-K dùng để tạo shortlist; giữ fused score và thứ hạng gốc. Endpoint trả `selected_doc_ids`, IDs ngoài shortlist/duplicate/JSON sai bị từ chối; min fill/max cap có log. Nếu muốn so LLM với threshold độc lập, tạo một run top-K riêng cho LLM. Selector chỉ đọc corpus trùng index_sha256 trong scored rows. Đổi shortlist/query/corpus/model/prompt thì tạo cache select mới; tune số học không tự gọi selector.

Val hiện có đã được khai thác: template ghi previously_observed_ids=all, holdout là retrospective. Tài liệu chưa có judgment là unknown. Adapter native dùng gold/not_gold như nhãn do file cung cấp; cần ghi nhận nếu not_gold là weak label. `known_positive_recall` là mặc định; muốn tune proxy F2 có thể chọn objective=known_positive_f2_proxy và allow_incomplete_f2=true, tên kết quả vẫn là proxy.

Trước khi thay tier_mode=expected, nhập đủ bốn xác suất backend_label_logits/backend_label_probabilities cùng probability_provenance. Không lấy confidence do model tự viết làm softmax.

Danh mục hyperparameters và cách invalidate từng cache nằm trong [handover](../../TXT_handover.md). `fit` hiện chỉ học sigmoid BM25; SapBERT affine 0.2–0.9 là estimate để tune, không được báo là probability calibration đã fit.
