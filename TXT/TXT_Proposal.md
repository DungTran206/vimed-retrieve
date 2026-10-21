# TXT Proposal v4 — Medical salience, calibrated fusion và adaptive threshold

Cập nhật 21/10/2026. Đây là **giả thuyết thử nghiệm người dùng muốn kiểm chứng**, chưa phải kết luận phương pháp tốt hơn baseline 0,391. Cần triển khai và chạy phần thực nghiệm có đủ dữ liệu, ghi cả kết quả thuận và nghịch. Phản biện giúp thiết kế đối chứng, không phải lý do dừng ý tưởng trước khi thử.

## 1. Vấn đề và mục đích

BM25 có lợi thế khi query và tài liệu cùng chứa tên bệnh, thuốc, subtype, chỉ số hoặc điều kiện quan trọng. Dense tìm được cách diễn đạt khác query. RRF chỉ dùng thứ hạng nên bỏ qua mức mạnh/yếu của score và không biểu diễn trực tiếp ý nghĩa y khoa của một khớp lexical.

BEAR prototype `corpus_parts_v1` dùng BM25 và evidence lexical/structured theo luật; công thức cũ `0,6 × lexical + 0,4 × evidence` không phải cơ chế adaptive mới. IDF đo độ hiếm trong corpus; coverage đo mức phủ từ/cụm; cả hai không tự đánh giá vai trò y khoa của term theo câu hỏi.

Giả thuyết mới: **document khớp concept quan trọng trong query thì tăng vai trò BM25; chỉ khớp từ ít quan trọng hoặc thiếu concept chính thì dựa nhiều hơn vào dense.** LLM dưới 15B phân loại term/concept của query một lần. Không bắt buộc chấm LLM relevance cho hàng nghìn query–document pairs rồi cộng một điểm thứ ba.

Mục tiêu là enrichment có nguồn để giảm thiếu vocabulary; tận dụng độ mạnh của score; chọn số ứng viên thích ứng theo query; và cache bước đắt để tối ưu offline. Tất cả đều là điều cần đo, chưa có gain được chứng minh từ cuộc thảo luận này.

## 2. Vị trí trong pipeline và phạm vi

```text
Query → LLM 9B: intent + original concepts + taxonomy
      + KB: disease → symptom/alias → chọn enrichment có nguồn
      ↓ cache query analysis
BM25 gốc + BM25 enriched + dense sources
      ↓ union rộng + raw scores + source masks
Observed concept matches trong document
      ↓ calibration → medical gate → BM25/dense fusion
      ↓ adaptive threshold + min_docs/max_docs tùy chọn
Cùng Qwen reranker / MaxP / p̂ / native chunk policy control
```

**Score fusion thay RRF; threshold thay cách cắt top-K sau fusion.** Threshold không tự tạo ranking. Candidate threshold cũng khác threshold `p̂` downstream; không áp một ngưỡng lên thang điểm khác.

| Nhánh | Search space | Vai trò |
|---|---|---|
| BEAR-Retriever / BR | Corpus/index trong scope | Tìm độc lập, có thể ngoài source union; vẫn giữ thí nghiệm riêng |
| BEAR-Fusion / BF | Union các retriever | Vị trí chính thử calibrated medical-gated fusion |
| Prototype v3.5 | Lexical/explicit relation scorer cũ | Đối chứng kỹ thuật, CLI/archive riêng |

BF không cứu doc mọi retriever đã bỏ. Enrichment trước retrieval có thể đổi union; cần tách phần tăng recall do nguồn ứng viên và phần tăng chất lượng do fusion. BR và BF không phải prerequisite của nhau. Evidence window vẫn diagnostic; thay đổi này chưa tự triển khai native `selected_chunks`/submission selector.

## 3. LLM mới và taxonomy theo ngữ cảnh

Model đề xuất: **`Qwen/Qwen3.5-9B`**, đáp ứng giới hạn dưới 15B. Đây là model query-role/enrichment mới, không tự thay Qwen reranker hiện hành. [Model card chính thức](https://huggingface.co/Qwen/Qwen3.5-9B).

Một request xử lý một query cùng KB candidates; output JSON gồm intent, concept nguyên gốc/span thật, loại entity, tier, alias/expansion được chọn và source IDs. Không bịa term hoặc nguồn khi thiếu dữ liệu. Matching document được tính sau từ cache, không đòi LLM đọc toàn corpus.

| Tier | Role | Điểm khởi tạo | Định nghĩa |
|---:|---|---:|---|
| 1 | `generic` | 0,05 | Từ chung/lời hỏi, ít phân biệt nhu cầu |
| 2 | `supporting` | 0,30 | Bối cảnh hoặc biểu hiện hỗ trợ, chưa quyết định |
| 3 | `discriminative` | 0,70 | Đặc điểm chuyên biệt giúp phân biệt với chủ đề gần |
| 4 | `decisive` | 1,00 | Concept/điều kiện trọng tâm; thiếu nó có thể đổi mục đích hoặc đối tượng query |

Đây là taxonomy vai trò, không phải loại entity. “Thai kỳ” có thể là điều kiện quyết định ở query chống chỉ định, nhưng chỉ là bối cảnh ở query khác. Tên bệnh không mặc định luôn tier 4. Điểm là tham số ưu tiên, không phải xác suất relevance.

Ví dụ “Thuốc A có chống chỉ định cho người mang thai mắc bệnh B không?”: thuốc A, thai kỳ và quan hệ chống chỉ định có thể là concept quyết định. Chỉ khớp “bệnh”, “thuốc” không được gate cao. Có đúng tên thuốc vẫn chưa bảo đảm document nói đúng population hoặc relation; downstream vẫn cần đánh giá phần đó.

### Confidence tùy chọn

Mặc định hard label: `a_i=s[tier_i]`. Nếu backend thực sự cung cấp đủ bốn xác suất lớp, thử `a_i=Σ_k P(tier=k|query,concept_i)×s_k`. Cách lấy phân phối phải được lưu. Không dùng confidence model tự viết; không dùng logprob cả đoạn JSON hoặc chỉ token đầu của một nhãn nhiều token làm xác suất lớp. Backend không hỗ trợ thì dùng hard tier, ghi probabilities null. Đây là ablation, không phải điều kiện chặn thử nghiệm.

## 4. Enrichment và dữ liệu ngoài

Mục tiêu là dữ liệu **bệnh → triệu chứng có provenance và concept chuẩn hóa**, không chỉ bảng hai cột dịch tự động.

- [CBLUE/CMeIE](https://github.com/CBLUEbenchmark/CBLUE#cmeie): corpus quan hệ có schema; cần chọn đúng relation và chuyển annotation thành KB records có nguồn. Extraction dataset không tự là clinical gold.
- [OpenCMKG](https://github.com/RuiqingDing/OpenCMKG): có quan hệ gần `disease_has_symptom`; kiểm source, duplicate, phạm vi, license và mapping trước nhập.
- Chưa xác minh một nguồn Việt công khai thỏa đầy đủ chuẩn concept/quan hệ/provenance/phạm vi. Có thể nhập dữ liệu Việt người dùng có, hoặc thêm nhãn Việt vào concept ID nguồn và ghi trạng thái bản dịch/duyệt. Không coi LLM dịch một lần là chuẩn hóa y khoa hoàn tất.

Schema cần disease ID/tên/ngôn ngữ, symptom ID/tên/ngôn ngữ, relation, source ID/URL. Nếu có thì giữ alias, tần suất, mức đặc hiệu, population, polarity và phiên bản. Phân biệt triệu chứng, biến chứng, tác dụng phụ. Mapping Việt/Trung qua concept IDs; alias dùng match phải có source/kiểm duyệt, không tự được nâng thành exact evidence từ một phán đoán gần nghĩa.

LLM chọn term theo intent từ KB candidates đã đưa vào. Query triệu chứng có thể mở rộng biểu hiện; query liều thuốc không cần thêm toàn bộ triệu chứng. Giữ riêng:

```text
original concepts = điều người dùng thật sự nêu
expansion concepts = gợi ý retrieval, không phải điều kiện query mới
```

BM25 gốc/enriched được lưu riêng để tune `enrichment_weight`. Gate mặc định chỉ dùng original concepts. Có thể thử expansion đóng góp nhỏ hơn trong ablation có config. Số term, intent gating và hệ số là tham số thử, không phải quy tắc để từ chối thực nghiệm. So `no enrichment / aliases only / disease→symptom`; term xuất phải phù hợp ngôn ngữ corpus.

### Nhánh bổ sung: LLM tìm term candidates trong document

Để khám phá cách diễn đạt query enrichment bỏ sót, có thể chạy LLM dưới 15B một lần/document và cache terms có exact title/body spans, loại entity và assertion status. Đây là bước kiểm tra được nguyên văn; model không được tự thêm alias/medical fact không xuất hiện. Prompt và CLI `document-terms` riêng cho phép thử nhánh này mà không đổi medical gate query.

Đưa terms đã trích vào index phụ/normalization hoặc retrieval vòng hai là thí nghiệm tiếp theo có config riêng. Chỉ đọc docs đã retrieve không trực tiếp cứu docs ngoài union. Trích lại từ vốn trong body không tự mở vocabulary; tác dụng có thể ở phrase selection, concept mapping và weighting. Extraction chưa đồng nghĩa hoàn tất document expansion hoặc tăng recall.

## 5. Medical gate từ observed match

Gọi `a_i∈[0,1]` là salience original concept; `m_i∈[0,1]` là mức khớp đã quan sát. Bản đầu dùng 1 cho exact phrase/source-backed alias, 0 khi không thấy. Partial match nếu có phải có định nghĩa và evidence.

```text
G(q,d) = Σ_i(a_i² × m_i(q,d)) / Σ_i a_i
G = 0 khi mẫu số bằng 0
```

Gate trong `[0,1]`, giữ salience tuyệt đối: query toàn concept 0,30 và khớp hết chỉ được `G=0,30`, không thành 1 như coverage thông thường. Với concept 1 và 0,3: chỉ khớp concept quan trọng cho `G≈0,769`, chỉ khớp concept phụ cho `G≈0,069`, khớp cả hai cho `G≈0,838`.

Dedup concept, không đếm nhiều alias thành nhiều điều kiện. Giữ boundaries/số/đơn vị: BRCA1 khác BRCA10; 5 mg khác 15 mg. No-match khác mâu thuẫn và không tự là negative relevance. Document bác bỏ quan hệ vẫn có thể trả lời đúng query, không phạt mọi phủ định.

`required_cap` là tùy chọn để hạn chế gate khi thiếu concept bắt buộc; phải ablate rõ. Đây là công thức khởi tạo cho hypothesis, không phải tối ưu đã chứng minh.

## 6. Chuẩn hóa score và fusion

```text
z_B = sigmoid((u(B,q) − x0) / T), T > 0
alpha = alpha_min + (alpha_max − alpha_min) × G
F = alpha × z_B + (1 − alpha) × z_D
```

`T` càng lớn càng smooth. `x0` là mốc input mà output bằng 0,5, **không phải threshold giữ doc cuối**. Sigmoid đơn điệu, không đổi thứ hạng BM25; lợi ích là phối hợp score và chọn operating point. Xem [sigmoid calibration](https://scikit-learn.org/stable/modules/calibration.html#sigmoid).

Thử `raw` hoặc `query_scale` với scale query/IDF đã cache. Phải lưu công thức scale/snapshot; thiếu metadata thì không bịa IDF. Một sigmoid chung có thể lệch theo query length/ngôn ngữ/enrichment; kiểm nhóm trước khi tăng tham số. Dense cũng cần transform xác định: affine với miền score khai báo hoặc sigmoid fit; mix head/chunk bằng weights có config. Cosine trong khoảng cố định chưa tự là xác suất relevance.

Không giữ 0,6/0,4 từ scorer cũ. Salience LLM đi vào gate/alpha, không cần additive LLM relevance. `dense_floor` tùy chọn giữ đóng góp dense tối thiểu. `F` vẫn là score ranking/selection, chưa chắc là xác suất cuối dù component đã calibrated.

Giữ missing masks: không xuất hiện trong truncated source không đồng nghĩa raw score 0. Nếu không re-score union, dùng policy `available`/`error` có log; BM25-only phải opt-in. Không áp calibrator của BM25F thật vào BM25 prototype như cùng distribution. [Nghiên cứu fusion](https://arxiv.org/abs/2210.11934) cung cấp cơ sở thử score fusion, không phải bằng chứng gain ở corpus này.

## 7. Adaptive threshold

```text
selected(q) = {d : F(q,d) ≥ tau(bucket(q))}
```

Một threshold chung đã cho số docs khác nhau theo query. Biến thể adaptive dùng bucket tầng cao nhất của original concepts hoặc nhóm khai báo trước; không dùng relevance labels lúc inference. `min_docs` bù top-score, `max_docs` chặn chi phí nếu bật. Log threshold pass / floor added / cap removed riêng. Có thể thử min=0 trước, rồi bounded policy.

Báo mean/median/p95/max docs/query và reranker calls/latency. Giữ mean/tổng budget gần control khi so chất lượng; nếu thay budget thì báo đường chất lượng–chi phí. Tăng quá nhiều buckets trên val nhỏ dễ overfit; bắt đầu global rồi vài bucket đủ support.

## 8. Dùng val để fit và tune

Chia **theo query** thành calibration/tuning/holdout hoặc nested query folds. Không chia ngẫu nhiên các cặp cùng query. Query đã khai thác nhiều lần không thành pristine holdout vì chia lại.

1. Khóa corpus/query/KB/model/prompt/depth; cache union đủ rộng.
2. Calibration: fit `x0,T` bằng positive/negative explicit. Unknown không negative. Chỉ positives thì vẫn đo known-positive coverage, chưa fit probability calibration có cơ sở.
3. Tuning: tìm tier scores, enrichment weight, gate/alpha và threshold trong search space đã lưu.
4. Chọn objective rõ, chẳng hạn coverage hoặc DocF2 dưới mean candidate budget. Retrieval metric không tự đại diện FINAL.
5. Khóa config, đánh giá holdout cùng downstream khi đủ inputs.

Negative sampling lệch distribution có thể làm sigmoid lệch prior; ghi sampling/weights. Khi nhãn đủ, đo log-loss/Brier/reliability cùng retrieval metrics; calibration tốt hơn không tự chứng minh ranking tốt hơn. Query đã dùng chỉ là exploratory/dev nếu không có holdout độc lập.

## 9. Cache phục vụ tối ưu offline

| Artifact | Phải giữ | Tính lại khi |
|---|---|---|
| KB | IDs/aliases/relations/provenance/version | Source/mapping đổi |
| Query analysis | Raw query, intent/spans, tiers, actual class probs nếu có, expansions | Query/model/prompt/KB candidates đổi |
| Retrieval | Union IDs, original/enriched BM25, dense raw scores/ranks/depth, source masks, query scale | Index/retriever/depth/terms đổi |
| Term matches | Concept/alias/origin/location/match type/corpus identity | Matcher/corpus/alias đổi |
| Calibration | Parameters/split/label semantics/sampling | Nhãn/split/pretransform đổi |
| Fusion/selection | Gate/alpha/transformed scores/F/bucket/threshold/reason | Tính lại rẻ từ cache |
| Downstream | Qwen/MaxP scores đúng recipe trên docs cần dùng | Doc mới hoặc model/prompt đổi |
| Manifest | Hash/config/model/prompt/KB/corpus identity/counts/runtime | Mỗi stage/run |

Không chỉ lưu fusion score hoặc top-K cuối. Full probabilities cho phép đổi tier scores không gọi LLM; hard labels vẫn đủ tune điểm tier. Cache chỉ đánh giá docs đã lưu; đổi terms/depth có thể phải retrieve lại, đổi matcher phải match lại.

## 10. Đối chứng và tiêu chí kết luận

| Run | Pool/query | Fusion | Selection | Câu hỏi |
|---|---|---|---|---|
| B0 | Control | RRF đúng recipe | Top-K control | Mốc đối chiếu |
| M0 | Cùng union B0 | Calibrated fixed | Top-K | Score magnitude có ích không |
| M1 | Cùng union B0 | Medical-gated | Top-K | Taxonomy/gate có ích thêm không |
| M2 | Cùng union B0 | Medical-gated | Global threshold | Variable-K cùng mean budget |
| M3 | Cùng union B0 | Medical-gated | Tier threshold | Adaptive hơn global không |
| E1 | Aliases/disease→symptom | Recipe đã khóa | Cùng budget policy | Enrichment tăng recall không |
| C1 | Cùng M1/E1 | Hard vs expected tiers | Cùng policy | Actual probabilities có ích không |

BR vẫn nghiên cứu riêng, không cộng gain BR+BF. Kết quả âm lưu nguyên cùng config. Hạn chế nguồn/overfit/cost ghi trong report, không dùng để trì hoãn experiment chạy được.

## 11. Trạng thái và tài liệu vận hành

Đường mới: `TXT.bear.medical_cli`, configs `configs/medical_hypothesis/`; legacy CLI vẫn riêng. [Handover](TXT_handover.md) chỉ thao tác, [algorithm](BEAR_ALGORITHM.md) chỉ công thức, [study](BEAR_REPLACEMENT_STUDY.md) chỉ protocol.

Không khẳng định đã chạy Qwen 9B/nhập toàn KB/rerun 0,391/đo gain chỉ từ code/demo. Thiếu inputs thì chạy stage làm được và demo, ghi đúng file/endpoint/label còn thiếu cùng command tiếp theo; không tạo scores/provenance/metrics giả.

Phiên bản trước ở [archive v3.5](archive/TXT_Proposal_v3_5_20261020.md). Lịch sử L1/L4/N0/N1 giữ nguyên phạm vi, không yêu cầu lặp lại trước hypothesis này.
