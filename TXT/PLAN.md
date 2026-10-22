# PLAN v5 — SapBERT-XLMR trong dense và LLM chọn shortlist

Cập nhật 22/10/2026. Đọc [handover](TXT_handover.md) để tiếp nhận; [proposal](TXT_Proposal.md), [algorithm](BEAR_ALGORITHM.md) và [study](BEAR_REPLACEMENT_STUDY.md) cùng mô tả kiến trúc v5.

## 1. Phạm vi hiện hành

Giữ BM25 gốc/enriched, lexical medical gate và fusion hai nhánh. Dense mới kết hợp dense tổng quát/SapBERT-XLMR; thêm LLM chọn shortlist tùy chọn. Đây là hypothesis cần thực nghiệm, chưa là recipe tăng điểm.

```text
D_new = (1 − λ) D_generic + λ S_sap
F = α z_B + (1 − α) D_new
```

Ban đầu λ=0,30; α=0,10+0,75G_lexical. SapBERT không sửa gate. Query LLM chọn enrichment từ whitelist KB có nguồn; document LLM trích literal terms; selector LLM chỉ chọn subset shortlist sau fusion.

## 2. Thứ tự thực hiện

1. Bind corpus/query IDs, index, source rankings trước RRF và labels. Xuất query label-free nếu lấy text từ val; labels chỉ vào fit/tune/evaluate.
2. Chuẩn hóa KB ngoại có nguồn, nhãn/alias VI/ZH và trạng thái mapping. Không tự coi bản dịch/quan hệ là clinical gold.
3. Chạy `kb-import → prepare` với intent gating/expansion cap.
4. Chạy `cache` giữ BM25 original/enriched, generic dense head/chunk, masks/ranks và lexical matches trên union cố định, rồi `document-terms` lấy unique doc IDs từ cache. Có thể trích terms trước bằng doc_ids_path rõ; tái dùng khi corpus/prompt/model không đổi.
5. Chạy `sapbert-cache` từ checkpoint local hoặc embeddings import có provenance. Giữ full cosine matrix theo concept–term, vectors/identity và literal spans.
6. Fit sigmoid BM25 trên calibration. Tune λ, Sap affine, tier scores, alpha, enrichment và threshold từ cache; không gọi lại LLM/encoder.
7. Run config đã khóa; so λ=0 / 0,30 / 1 cùng union. λ=1 là ablation thay dense bằng SapBERT, chưa promote mặc định.
8. Thử `select` sau run với shortlist/prompt/budget đã khóa. Cache response/chosen IDs; evaluate cả trước và sau selector.
9. Báo coverage, chất lượng, missingness, candidate budget, tokens/runtime/GPU/disk, cả kết quả âm. Chạy downstream control đúng recipe khi đủ artifacts để đo FINAL.

Thiếu inputs thì báo đúng artifact còn thiếu, tiếp tục stage độc lập có thể chạy. Không đợi chứng minh gain trước khi thử phương án đã được ủy quyền.

## 3. Đối chứng

| So sánh | Giữ cố định | Câu hỏi |
|---|---|---|
| RRF / fixed calibrated / medical-gated | Union, nguồn, language, output budget | Gate/fusion có ích thêm không |
| λ=0 / 0,30 / 1 | BM25, gate, union, generic scores | Kết hợp hay thay dense tốt hơn |
| λ/affine/tier variants | Full cosine/raw-score cache | Tham số ổn định trên tune |
| No enrichment / aliases / disease→symptom | Corpus, matched budget; báo union đổi | Thêm được positives nào |
| Run / run+LLM select | Universe, shortlist limit, output budget | Selector đủ ích so chi phí không |

Không quy gain cho SapBERT khi đổi đồng thời mọi phần. Giữ cùng mean/tổng output budget hoặc báo cost curve. Required cap, tier thresholds và expected-tier probabilities là ablations có config.

## 4. Validation

Val native có 593 query, judgments chưa đầy đủ: default known-positive recall; unknown không thành negative. Chia calibration/tune/holdout theo query, normalized duplicates cùng split. Val đã khai thác trước đây thì retrospective holdout không pristine.

Tests/demo xác nhận kỹ thuật, chưa chứng minh quality corpus thật. Fit dùng positives/negatives do file cung cấp, ghi weak-negative assumption và exposure. Cosine cao chưa chứng minh synonym, relation, dose hoặc relevance toàn câu.

## 5. Phiên bản và thư mục

Hiện branch `Tung`; người dùng sẽ tự tạo branch. Khuyến nghị `exp/sapbert-xlmr` để tách mã; commit giữ source, manifests/log giữ recipe và kết quả.

`TXT/runtime/` và `TXT/inputs/` bị gitignore; giữ completed runs/caches và backup artifacts riêng. Đổi recipe/input/code dùng output_dir mới, không đè completed manifest. Dọn prose cũ theo [cleanup report](reports/CLEANUP_20261022.md); giữ baseline/eval controls/provenance và dependency code.
