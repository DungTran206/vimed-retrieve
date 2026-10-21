# BEAR v4 — Protocol thử nghiệm medical-gated fusion

Cập nhật 21/10/2026. Thí nghiệm kiểm chứng hypothesis của người dùng; chưa có quality gain trên control 0,391. Phải giúp chạy thử khi có inputs, ghi hạn chế nhưng không dùng chúng thay cho experiment.

## 1. Câu hỏi nghiên cứu

- H_score: score fusion được chuẩn hóa khai thác độ mạnh match tốt hơn RRF không?
- H_medical: taxonomy theo query và observed important-concept matches giúp phân bổ BM25/dense tốt hơn trọng số cố định không?
- H_threshold: variable-K theo threshold tốt hơn top-K ở cùng mean budget không?
- H_adaptive: threshold theo query-tier buckets tốt hơn global threshold không?
- H_enrich: bệnh→triệu chứng có nguồn giúp retrieval thêm relevant docs mà không tạo quá nhiều drift không?
- H_cache: cache đủ raw features cho phép tune mà không gọi lại LLM/retrieval khi inputs không đổi không?

Expected-tier confidence, required-concept cap và document-side LLM candidate extraction là các ablations tùy chọn. Query salience không đồng nghĩa pairwise LLM relevance. Document extraction nếu thử phải lưu trích đoạn thật; chỉ đọc docs đã retrieve không tự cứu docs ngoài union.

## 2. Runs và invariants

| Run | Candidate pool | Fusion/selection | Phần thay đổi |
|---|---|---|---|
| B0 | Control pre-fusion sources | RRF đúng k/weights/ties + top-K | Mốc |
| M0 | Cùng B0 union | Calibrated fixed mix + top-K | Dùng score magnitudes |
| M1 | Cùng B0 union | Medical-gated mix + top-K | Medical salience/gate |
| M2 | Cùng B0 union | M1 + global threshold | Variable-K |
| M3 | Cùng B0 union | M1 + tier-bucket threshold | Query-adaptive selection |
| E_alias | Retrieval có alias nguồn | Recipe đã khóa | Vocabulary đồng nghĩa |
| E_symptom | Retrieval có bệnh→triệu chứng | Recipe đã khóa | Related-concept expansion |
| P_expected | Cùng M1/E pool | Actual 4-class probability expectation | Confidence use |
| BR | Corpus/index trong scope | Retriever độc lập | Khả năng tìm ngoài union |

So M0/M1/M2/M3 giữ corpus/query/lang/raw sources/depth và downstream. Enrichment đổi union nên cần so riêng với union gốc; báo docs mới thực sự tìm được và known-positive contribution. BF không tự thêm doc ngoài union để bù. BR/BF không là prerequisite của nhau; joint đo riêng, không cộng gain.

Ngân sách: M0/M1 top-K như control; M2/M3 chọn threshold để mean/tổng candidate budget gần control rồi so chất lượng. Báo thêm curve nếu chủ động đổi budget. Kmin/Kmax và floor/cap events phải có log, không gọi floor-added docs là threshold-pass.

## 3. Validation protocol

Chia theo query thành calibration, tuning, holdout; ít dữ liệu dùng query folds. Không có query overlap giữa fit/tune/evaluation. Query từng khai thác trước đây vẫn là development/exploratory, không pristine holdout.

Calibration sigmoid BM25: raw hoặc query_scale, fit x0/temperature bằng explicit positive/negative judgments. Dense transform cũng khai báo/fit riêng. Unknown/unjudged không là negative; nếu positives-only, báo known-positive coverage và chưa khẳng định probability calibration. Negative sampling và class-prior correction nếu có phải ghi rõ.

Tuning: lưu search space, objective, budget constraint, seed và toàn bộ trials. Tune tier scores/alpha/enrichment/threshold từ cache; chọn config rồi khóa trước holdout. Nếu chạy nhiều lần nhìn holdout thì báo đúng exploratory status.

## 4. Metrics

Candidate stage cần known-positive coverage, precision/F2 chỉ khi judgments cho phép semantics đó, nDCG/MRR nếu graded/rank labels đủ; union coverage giới hạn recall tối đa. Khi judgments không đầy đủ, không báo unknown thành false positive hoặc gọi coverage là true recall.

Selection/cost: mean/median/p95/max docs/query, query không có docs, floor/cap count, missing-source rate, dense-only/BM25-only/fallback share, LLM calls/tokens/latency, reranker calls, retrieval/cache runtime và disk. Calibration: log-loss/Brier/reliability trên distribution có nhãn rõ. Các metric này trả lời những câu khác nhau, không suy FINAL từ calibration hoặc ΔDoc.

Nếu đủ baseline linkage thì chạy cùng Qwen checkpoint/prompt/preprocessing/MaxP/p̂/threshold/chunk policy, đo Doc/Chunk/FINAL theo scorer đúng semantics và paired query uncertainty. Doc mới thiếu cache phải inference đúng recipe, không gán score 0. Candidate score threshold khác downstream p̂ threshold.

## 5. Dữ liệu ngoài và audit

KB cần concept IDs, labels/aliases/ngôn ngữ, quan hệ và source provenance. CMeIE/OpenCMKG là source candidates, không tự clinical gold. Vietnamese mappings chưa duyệt giữ trạng thái đó; không dịch rồi gắn nhãn chuẩn y khoa. Original query concepts và expansions tách riêng; gate mặc định chỉ original.

Match audit cần identifier boundaries, units/numbers, phrase spans và aliases. Kiểm các lỗi điển hình: tên bệnh chung nhưng sai subtype; term phụ match nhiều làm gate cao; doc chỉ liệt kê tên mà không trả lời intent; sai population; phủ định bị coi sai là irrelevant; expansion drift; Chinese terms không phù hợp Vietnamese index.

Các lỗi không phải lý do từ chối thử. Ghi tần suất trên mẫu có tiêu chí chọn rõ, thử biến thể cấu hình, đo lại đúng split.

## 6. Cache và reproducibility

Giữ raw scores từng nguồn, original/enriched BM25, source masks/ranks/depth/query scale; query tiers/probs khi có; observed term matches; KB/model/prompt/corpus/index hashes. Giữ labels/splits riêng, không để inference đọc đáp án chọn docs.

Tính lại fusion/threshold từ cache khi chỉ đổi tham số. Đổi enrichment term/depth có thể cần retrieve lại; đổi model/prompt cần prepare lại; đổi matcher/aliases/corpus cần matches lại. Cache top-K cũ không đủ đánh giá docs ngoài nó.

## 7. Kết luận được phép và việc chưa làm

Engineering demo chỉ xác nhận paths/schema/formulas/invariants. Quality claim cần real judgments/control/downstream đúng recipe. Chưa đủ inputs thì report `missing`, chạy available stages và ghi command tiếp theo, không dựng control/negative/provenance giả.

Native selected_chunks/exporter chưa được thay trong hypothesis này. Lịch sử L1/L4/N0/N1 giữ nguyên, không cần làm lại prerequisite. Báo kết quả âm đầy đủ; nếu một thành phần không cải thiện, kết luận theo thực nghiệm thay vì xóa run để giữ câu chuyện.

Vận hành theo [handover](TXT_handover.md), mục đích/công thức ở [proposal](TXT_Proposal.md) và [algorithm](BEAR_ALGORITHM.md). [Archive v3.5](archive/BEAR_REPLACEMENT_STUDY_v3_5_20261020.md) giữ protocol trước.
