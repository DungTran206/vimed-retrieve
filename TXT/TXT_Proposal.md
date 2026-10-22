# TXT Proposal v5 — BM25, dense tổng quát và SapBERT-XLMR

Cập nhật 22/10/2026. Đây là giả thuyết người dùng muốn triển khai/thử nghiệm; chưa có kết luận tăng điểm so với baseline 0,391. Các thông số ban đầu được ghi rõ là **ước lượng**, được tune trên tập phù hợp và có đối chứng.

## 1. Vấn đề cần giải quyết

Người hỏi có thể dùng lời diễn đạt đời thường, viết tắt hoặc ngôn ngữ khác tài liệu. BM25 dễ bỏ lỡ khi query/document ít chia sẻ term. Dense tổng quát bổ sung ý nghĩa câu và cách diễn đạt; SapBERT-XLMR bổ sung độ tương đồng giữa các tên gọi concept y sinh đa ngôn ngữ.

Ba vai trò bổ trợ nhau, không chia ranh giới tuyệt đối: BM25 cũng có thể tìm lời đời thường; generic dense có thể nhận tên bệnh; SapBERT có thể nhầm những entity liên quan. Tất cả vẫn phải đo trên dữ liệu Việt/Trung thực tế.

SapBERT-XLMR được thiết kế cho multilingual biomedical entity linking, không mặc định được huấn luyện để xếp relevance của toàn đoạn tài liệu cho mọi câu hỏi. Vì vậy biến thể đầu **giữ dense tổng quát và trộn thêm SapBERT**, đồng thời giữ λ=1 làm ablation thay thế. Nguồn thiết kế: [model card](https://huggingface.co/cambridgeltl/SapBERT-UMLS-2020AB-all-lang-from-XLMR), [bài báo multilingual biomedical entity linking](https://aclanthology.org/2021.acl-short.72/).

## 2. Kiến trúc thống nhất

```text
KB ngoài có nguồn → kb-import → prepare(query concepts/tiers/enrichment)
corpus + sources → cache(BM25 original/enriched, generic dense, lexical matches)
cache union → document-terms(literal spans, một lần/document)
cache + terms + SapBERT-XLMR → sapbert-cache(full cosine matrix)
                                      ↓
                     fit BM25 → tune offline → run
                                                ↓
                                  [LLM select shortlist]
                                                ↓
                         evaluate + downstream control khi đủ artifacts
```

BR có thể retrieve độc lập từ corpus; BF chỉ chọn union nguồn. V5 cập nhật BF. SapBERT matching chạy sau retrieval chỉ cải thiện điểm của doc đã có trong union; muốn tìm thêm doc phải làm experiment retrieval/index riêng.

## 3. Query concepts và enrichment có nguồn

Query LLM dưới 15B, initial model Qwen/Qwen3.5-9B, thực hiện hai việc trong một lần phân tích:

- Trích concept gốc có span thật trong query, gán vai trò generic/supporting/discriminative/decisive và required nếu phù hợp.
- Chọn expansion IDs từ whitelist KB theo intent; không tự sinh fact/alias, không coi triệu chứng liên quan là synonym bệnh.

Tier scores khởi tạo [0,05; 0,30; 0,70; 1,00]. Vai trò phụ thuộc câu hỏi. Hard tier là mặc định; expected tier chỉ khi có bốn xác suất lớp thật từ backend cùng provenance, không dùng confidence tự viết.

KB canonical có concept IDs, nhãn/alias theo ngôn ngữ, relation disease→symptom và nguồn từng record. Có adapter CMeIE; OpenCMKG/nguồn khác cần export/mapping về schema hỗ trợ. Hiện hỗ trợ vi/zh/en; ngôn ngữ ngoài đó cần adapter, không chỉ đổi lang rồi kỳ vọng chạy.

Enrichment được chặn theo intent khi symptoms không phù hợp câu hỏi điều trị/liều/tương tác. max_expansion_terms=8 và max_kb_candidates=256 là cap khởi tạo để kiểm soát drift/token; chạy aliases-only/no-enrichment làm đối chứng. KB bổ sung vocabulary/relations; chưa tự nhập tài liệu ngoài vào corpus kết quả.

## 4. Lexical gate giữ ý tưởng ban đầu

Giữ khớp exact hoặc source-backed alias m_i∈{0,1} cho original query concepts:

```text
G_raw = Σ_i a_i² m_i / Σ_i a_i
G = G_raw, có optional required_cap
α = 0,10 + (0,85 − 0,10) G
```

Mẫu số 0 thì G=0. Tier-2-only khớp hết vẫn G=0,30. Nếu required_cap bật, thiếu required có thể đưa gate về 0. Nhiều alias của một concept không thành nhiều phiếu.

Gate chỉ định **tỷ trọng BM25**. Nó không phải điểm thưởng relevance: khi z_B thấp hơn dense, tăng α có thể làm document tụt điểm. Do đó kết quả semantic từ SapBERT không được chuyển thành lexical m_i ở biến thể đầu.

## 5. BM25 original/enriched và generic dense

```text
B = (1 − w) B_original + w B_enriched
z_B = sigmoid((u_B − x0) / T)
D_generic = 0,50 z_dense_head + 0,50 z_dense_chunk
```

w=0,25 khởi tạo. u_B là raw B hoặc B/query_scale tương thích. BM25 original/enriched cần cùng recipe. Fit học x0/T từ calibration positives/negatives; dense head/chunk transform khai báo riêng.

Điểm chưa xuất hiện trong source top-K là missing, không tự 0. Cache giữ masks, raw scores và query scale để tune trung thực. External BM25F không chia bằng scale từ prototype khác recipe.

## 6. SapBERT trên concept và term thật trong document

Document LLM trích term từ title/body với exact spans, entity kind và assertion. Term phải thực sự có trong text; model không tự tạo đồng nghĩa hoặc suy fact mới. Trích một lần/document rồi tái dùng cho mọi query khi corpus/prompt/model không đổi. Tập doc IDs có thể lấy từ cache union, không cần đọc toàn corpus.

Encode original query concept (loại kind=intent) và document literal terms bằng checkpoint SapBERT-XLMR pin identity, CLS/L2. Tính cosine từng cặp, normalize rồi lấy max trên term cho từng query concept đủ điều kiện, cuối cùng average theo importance a_i:

```text
c_ij = cosine(query_concept_i, document_term_j)
s_i = max_j clip((c_ij − 0,20) / (0,90 − 0,20), 0, 1)
S_sap = Σ_i a_i s_i / Σ_i a_i
```

0,20/0,90 là **ước lượng khởi tạo**, không phải threshold synonym đã chứng minh. Cache full matrix để đổi affine/tier offline. Missing document_terms record phải phân biệt với document đã trích hợp lệ nhưng terms rỗng; cả trường hợp không có actual pairs hoặc không có eligible query concepts đều không tạo Sap score quan sát thật. Khi Sap thiếu, available-policy dùng lại nhánh dense còn bật/có thật; không tự gán semantic score 0.

Cosine cao chỉ là similarity evidence. Nó chưa xác nhận hai từ có thể thay thế nhau, đúng subtype/dose/negation/population hay relevance toàn câu. Những cặp có liên quan nhưng khác concept cần nằm trong error audit.

## 7. Fusion dense mới

```text
D_new = (1 − λ) D_generic + λ S_sap
F(q,d) = α(q,d) z_B(q,d) + (1 − α(q,d)) D_new(q,d)
```

Initial λ=0,30, tức phần dense có 70% generic và 30% SapBERT khi đủ components. Trọng số cuối của SapBERT là (1−α)λ, thay đổi theo lexical gate. So λ=0 / 0,30 / 1 trên cùng union/budget để quyết định kết hợp hay thay thế.

F dùng ranking/selection; score bounded hoặc sigmoid không làm nó tự thành xác suất relevance cuối. V5 không thêm additive LLM relevance cho mọi query–doc.

## 8. Threshold và LLM chọn shortlist

Threshold global ban đầu 0,50; có optional tier-bucket thresholds, min_docs fill và max_docs cap. Chúng là tham số experiment, khác downstream p̂ threshold.

Sau run có thể dùng LLM cherry-pick shortlist từ các IDs đã selected, ban đầu tối đa 40 doc/query, 2.000 ký tự/doc, chọn 0–40 doc. Code chỉ nhận subset hợp lệ, áp min-fill/cap deterministic và lưu raw response/chosen IDs/diagnostics.

Selector đọc giới hạn text nên không chứng nhận đã xem toàn document. Nó không tìm doc ngoài shortlist. Cần đo selector riêng với matched-budget control; giảm số doc có thể tăng precision nhưng mất positives. Không chạy selector trong mọi trial của tune.

## 9. Tài nguyên, cache và khả năng thử

Query LLM tốn theo số query; document LLM tốn theo số document duy nhất; embeddings theo số concept/term duy nhất; semantic matrix theo các cặp trong union. Đây là các bước đắt được cache. Replay công thức/threshold rẻ hơn và không gọi lại LLM/encoder.

Bảng hyperparameters, mức ước lượng/range và invalidation ở [handover](TXT_handover.md). Selector cache phụ thuộc candidate set/corpus/prompt/model; thay λ có thể đổi shortlist và buộc chạy selector lại. Vì vậy tune numerical trước, selector thử sau với config đã khóa.

## 10. Validation và giới hạn kết luận

Native val có 593 query với judgments không đầy đủ; default known-positive recall. Unknown không tự negative; not_gold dùng theo semantics do file cung cấp và ghi nhận weak-label assumption. Query từng khai thác không thành pristine holdout chỉ vì chia lại.

So control RRF, fixed/medical-gated fusion, λ variants, enrichment và selector theo [study](BEAR_REPLACEMENT_STUDY.md). Giữ downstream Qwen/MaxP/p̂/native chunk recipe để quy kết gain khi có artifacts; tests/demo chưa là quality experiment. Kết quả âm, chi phí và lỗi đều lưu.

[PLAN](PLAN.md) ghi thứ tự tiếp tục; [handover](TXT_handover.md) là tài liệu tiếp nhận đầy đủ. Prose cũ được dọn theo [cleanup](reports/CLEANUP_20261022.md), giữ lịch sử kết quả và baseline spec/eval controls.
