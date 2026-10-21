# BEAR v4 — Thuật toán medical-gated fusion

Cập nhật 21/10/2026. [Proposal](TXT_Proposal.md) giải thích mục đích; tài liệu này chốt công thức/invariants. Đây là hypothesis thử nghiệm, chưa là quality claim.

## 1. Search spaces

**BR** tìm corpus/index độc lập, có thể ngoài union baseline. **BF** chỉ xếp/chọn union source; v4 ưu tiên thử medical-gated fusion ở BF. Corpus/index trong BF chỉ cấp text, không thêm tài liệu ngoài union.

Legacy `corpus_parts_v1`, CLI `TXT.bear.cli corpus-index|retrieve|evidence-fuse` và fixed `0,6 lexical + 0,4 evidence` vẫn riêng; không tuyên bố v4 là default mọi pipeline cũ.

## 2. Query salience

LLM query-role mặc định `Qwen/Qwen3.5-9B` (<15B), output JSON theo prompt. Concept nguyên gốc phải neo trong query, alias có nguồn, expansion khác original.

| Tier | Role | Initial score |
|---:|---|---:|
| 1 | generic | 0,05 |
| 2 | supporting | 0,30 |
| 3 | discriminative | 0,70 |
| 4 | decisive | 1,00 |

Role theo query, không tự theo loại entity. Dedup concept/aliases. Hard mode: `a_i=s[tier_i]`. Expected mode: `a_i=Σ_k p_ik s_k` chỉ khi đủ bốn xác suất lớp thật. Không dùng confidence tự viết hoặc logprob JSON làm confidence class. Không có probabilities hãy cấu hình hard; expected đang bật mà thiếu probabilities sẽ báo lỗi.

## 3. Observed match và medical gate

`m_i(q,d)` là evidence thực đã match trong document: exact concept/source-backed alias 1, không thấy 0; partial match cần định nghĩa riêng. Giữ span/location/match type/origin/corpus identity để audit.

```text
A = Σ_i a_i                       # original concepts, default
G = Σ_i(a_i² × m_i) / A            # A > 0
G = 0                             # A = 0
```

`G∈[0,1]`. Query chỉ tier 2 và khớp hết vẫn G=0,30. `required_cap` có thể giảm gate khi concept required không khớp, phải khai báo/ablate. Nhiều alias không thành nhiều concept. BRCA1≠BRCA10; 5mg≠15mg; giữ boundaries/số/đơn vị.

No-match, missing feature và conflict khác nhau. Phủ định không tự giảm relevance: tài liệu bác bỏ một giả định có thể trả lời đúng query. Gate lexical chưa chứng minh đúng relation/population toàn tài liệu.

## 4. Calibration và raw inputs

Giữ original BM25, enriched BM25, từng dense source và missing masks. Original/enriched blend bằng `enrichment_weight` theo recipe xác định; thiếu expanded score dùng `missing_expanded` đã khai báo.

```text
u_B = B                           # pretransform=raw
u_B = B / query_scale              # pretransform=query_scale, scale>0 từ cache
z_B = sigmoid((u_B − x0_B) / temperature_B)
z_Dj = affine_or_sigmoid(raw_Dj)
z_D = weighted_mix(z_D_head, z_D_chunk)
```

`query_scale` có thể được xây từ query IDF; lưu công thức/snapshot, không bịa IDF nếu thiếu. `temperature>0`, càng lớn càng smooth. `x0` là input midpoint z=0,5, khác threshold cuối. Sigmoid đơn điệu không đổi ranking một nguồn.

Affine dense dùng `low/high` được khai báo, sigmoid dùng parameters fit. Score bounded chưa tự là calibrated probability. Không dùng calibrator BM25F thật cho BM25 prototype khác distribution. Giữ missing-score policy `available`/`error`; không tự gán truncated-source absence thành raw 0. BM25-only chỉ khi opt-in, ghi coverage/fallback.

## 5. Adaptive fusion

```text
alpha = alpha_min + (alpha_max − alpha_min) × G
F = alpha × z_B + (1 − alpha) × z_D
0 ≤ alpha_min ≤ alpha_max ≤ 1
```

`dense_floor` nếu bật giới hạn alpha để giữ dense contribution. Gate cao tăng vai trò BM25; gate thấp tăng dense. LLM salience điều khiển alpha, không cần additive LLM relevance. Missing-source policy phải giống giữa tune/run. `F` là ranking score, chưa tự là final probability.

## 6. Selection

```text
bucket(q) = global hoặc max original tier
pass(q) = {d : F(q,d) ≥ threshold[bucket(q)]}
selected(q) = optional_min_docs_fill_then_max_docs_cap(pass)
```

Sort deterministic và giữ doc/query namespaces. Log threshold-pass/floor-add/cap-remove riêng. Query không có concept dùng fallback đã khai báo. Không đọc labels ở inference. Một threshold chung đã tạo variable-K; tier buckets là biến thể cần so với global. Score fusion thay RRF, threshold là selection sau ranking.

## 7. Fitting và tuning

Chia theo query thành calibration/tuning/holdout. Chỉ nhãn explicit positives/negatives vào calibration; unknown không là negative. Positive-only evaluation là known-positive coverage, không tự full recall.

Fit x0/temperature trên calibration, tune tier weights/alpha/enrichment/threshold trên tuning, lock rồi evaluate holdout. Một class hoặc thiếu negatives không đủ fit probability calibration có cơ sở; ghi chính xác, vẫn chạy demo/available stages. Query từng khai thác không pristine holdout khi chia lại.

## 8. Cache và output

Cache giữ raw query, concepts/tiers/probs nếu có, original/enriched scores, dense sources/masks/ranks/depth/query scale, matches và identity. Đổi tier scores/sigmoid/alpha/threshold tính lại rẻ; đổi query/KB/expansion/corpus cần invalidation tương ứng. Union đã cache là giới hạn có thể đánh giá offline.

Candidate adapter:

```json
{"id": 1, "candidates": [{"doc_id": "123", "score": 0.75}]}
```

Feature/selection outputs giữ gate/alpha/component scores/F/bucket/threshold/reason; manifest có hash/config/version/counts. Tên artifacts/lệnh chính xác ở [handover](TXT_handover.md).

Native chunk control chưa đổi. `bear_window` và evidence spans diagnostic, chưa native `selected_chunks`. Doc mới downstream cần Qwen score/cache đúng recipe; không gán 0 hoặc áp threshold p̂ lên fusion score.

## 9. Invariants cần kiểm

- BF output subset cached union; BR riêng có thể lấy outside-union.
- Tune weights/calibration/threshold không gọi lại LLM nếu cache đủ.
- Missing source/no-match không biến thành negative labels.
- Tier-2-only full match không cho gate 1; protected identifiers không match substring sai.
- Calibration/tuning/holdout không overlap query; fit không đọc holdout labels.
- Unsupported class probabilities có trạng thái thật, không bịa confidence.
- Synthetic tests/demo chứng minh kỹ thuật, chưa quality trên 0,391.

Protocol ở [study](BEAR_REPLACEMENT_STUDY.md), bản trước ở [archive](archive/BEAR_ALGORITHM_v3_5_20261020.md).
