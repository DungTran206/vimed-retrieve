# BEAR v5 — Protocol thử nghiệm SapBERT và LLM selector

Cập nhật 22/10/2026. Mục tiêu là đo phần cải thiện thêm của SapBERT-XLMR và LLM chọn shortlist trong medical-gated BM25/dense fusion. Chưa có quality gain được chứng minh so với baseline 0,391.

## 1. Câu hỏi thực nghiệm

- Giữ generic dense rồi thêm SapBERT có tốt hơn thay generic bằng SapBERT không?
- SapBERT concept–term similarity bổ sung gì ngoài generic head/chunk scores trên cùng union?
- Lexical medical gate có giúp hơn fixed alpha khi dense đã có SapBERT không?
- Enrichment có nguồn thêm positives ngoài union hoặc cải thiện thứ hạng không?
- LLM selector giữ/bỏ doc có cải thiện đủ bù chi phí và mất recall không?
- Full feature cache có giúp tune offline mà không gọi lại model không?

Hiệu quả đa ngôn ngữ phải đo trên VI/ZH theo corpus/query cụ thể; model multilingual không bảo đảm mọi ngôn ngữ hoặc mọi kiểu query tăng điểm.

## 2. Runs tối thiểu

| Run | Pool | Recipe | Biến được thử |
|---|---|---|---|
| B0 | Control sources | RRF đúng recipe + top-K | Control có provenance |
| G0 | Cùng union | Calibrated BM25 + generic, fixed alpha | Score magnitudes |
| G1 | Cùng union | Lexical gate + generic, λ=0 | Gate |
| S03 | Cùng union | G1 + SapBERT, λ=0,30 | Kết hợp dense |
| S1 | Cùng union | G1 + SapBERT, λ=1 | Thay generic dense |
| S_best | Cùng union | λ/affine/alpha được chọn trên tune | Chốt recipe |
| L0 | Shortlist S_best | Fusion top-K hoặc bounded threshold | Budget control selector |
| L1 | Cùng shortlist | LLM select, cùng max output | Selector |
| E0/Ea/Es | Union được ghi rõ | No-enrich / aliases / symptoms | Vocabulary và pool change |

Bật retrieval expansion làm union đổi thì báo experiment riêng; BF/SapBERT/selector không tự lấy doc ngoài union. BR corpus retrieval vẫn độc lập. Không cộng gain các experiment khác pool hoặc downstream.

Giữ corpus/query/lang/source recipe/depth/missing-policy và native chunk/downstream control. Nếu select chỉ xem top40, control selector cũng chỉ xem cùng shortlist; báo both recall trước shortlist và sau shortlist để thấy trần hiệu quả.

## 3. Splits và tuning

Chia calibration/tune/holdout theo query; normalized duplicates cùng split. Đã xem val thì ghi exposure thật, holdout là retrospective/exploratory. Lưu split IDs/seed, không mở holdout để chọn λ/threshold/prompt.

Fit stage chỉ học BM25 x0/T từ judged positives/negatives. Sap affine low/high và λ ban đầu là ước lượng, được chọn theo retrieval objective trên tune; chưa là probability calibration. Tune đổi BM25 enrichment/pretransform cần refit calibration split từ raw cache. Không dùng unknown như negative để làm đủ hai lớp.

Grid/search space, objective, max_mean_docs, seed và mọi trials phải lưu. Không chạy model trong mỗi numerical trial; full cosine matrix/raw scores cho phép replay. Selector prompt/shortlist budget thử riêng sau numerical tuning; nếu nhìn holdout để sửa prompt thì đánh dấu exploratory.

## 4. Metric và chi phí

Native judgments không đầy đủ: known-positive recall/coverage là default. F2 chỉ khi completeness/semantics cho phép; explicit proxy phải ghi tên/assumption. Union coverage là trần trước selection; selector không tăng trần đó.

Báo mean/median/p95/max docs/query, threshold pass/min-fill/max-cap, missing component share, zero-output queries, runtime/cache bytes. SapBERT cần số unique strings encoded, batches, matrix pairs, encoder wall/GPU time. LLM cần calls/tokens/latency theo query/document/selector, tỷ lệ cache hit và lỗi/schema retries.

Nếu đúng baseline/downstream artifacts thì đo Doc/Chunk/FINAL bằng scorer đúng contract và paired query uncertainty. Calibration log-loss/Brier/reliability chỉ có ý nghĩa trên labeled distribution rõ; không suy FINAL từ calibration.

So cùng mean/tổng candidate budget hoặc báo cost curve. Report tăng chất lượng nhưng tăng reranker load riêng; không gọi matched-budget nếu chỉ cùng max_docs mà mean khác đáng kể.

## 5. Error audit

Lấy mẫu queries/documents theo tiêu chí đã ghi; phân theo VI/ZH, lời đời thường/thuật ngữ, dài/ngắn, acronym và missingness. Rà:

- Alias thật bị exact matcher bỏ sót nhưng SapBERT giúp.
- Entity cùng họ/liên quan bị cosine coi như cùng concept; sai subtype/ID/dose/number.
- Term có mặt nhưng document không trả lời intent hoặc sai population/relation.
- Document terms bị trích thiếu hoặc prefix truncate làm mất thông tin.
- Enrichment sai intent/ngôn ngữ, quá nhiều symptom terms.
- LLM selector bỏ known-positive hoặc chọn theo bằng chứng ngoài snippets được gửi.

Assertion/negation cần ngữ cảnh; câu bác bỏ giả định vẫn có thể relevant. Không đưa cặp cosine cao thành KB alias đã duyệt mà thiếu nguồn/validation riêng.

## 6. Provenance và kết luận

Giữ code commit, input/output hashes, model checkpoint identity/revision, prompts, KB/corpus/index, raw scores, masks, full cosines, splits và candidate IDs. Không đè completed artifacts; đổi recipe dùng output_dir mới.

Tests/demo chỉ kiểm engineering behavior; không gọi fixtures là clinical labels hoặc model inference thật. Báo kết quả âm và phạm vi chưa chạy. Khuyến nghị giữ branch riêng cho source changes; manifests không thay Git snapshot, branch không sao lưu runtime bị ignore.

Vận hành theo [handover](TXT_handover.md); công thức tại [algorithm](BEAR_ALGORITHM.md).
