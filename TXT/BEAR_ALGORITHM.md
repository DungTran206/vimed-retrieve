# BEAR v5 — Công thức và hợp đồng score

Cập nhật 22/10/2026. [Proposal](TXT_Proposal.md) nêu mục đích; [handover](TXT_handover.md) ghi vận hành. V5 giữ lexical medical gate, đưa SapBERT vào nhánh dense.

## 1. Salience và lexical gate

Hard tier mode dùng a_i=s[tier_i]. Điểm khởi tạo: generic=0,05; supporting=0,30; discriminative=0,70; decisive=1,00. Vai trò phụ thuộc query. Concept gốc phải có span thật; alias cùng concept được gom; expansions tách riêng.

Expected mode chỉ khi có đủ bốn xác suất lớp thật cùng phương pháp/provenance; không dùng confidence model tự viết.

```text
m_i = 1 nếu exact concept hoặc source-backed alias xuất hiện trong document
m_i = 0 nếu không quan sát được khớp lexical
G_raw = Σ_i a_i² m_i / Σ_i a_i             # chỉ original concepts
G_raw = 0                                # mẫu số = 0
G = min(G_raw, min_required m_i)          # required_cap=true, có required
G = G_raw                                # trường hợp còn lại
α = α_min + (α_max − α_min) G
```

Ban đầu α_min=0,10, α_max=0,85. Tier-2-only full match cho G=0,30. Thiếu required có thể đưa G về 0. Giữ protected identifiers/numbers/boundaries; no-match khác missing khác negative relevance.

**SapBERT không đi vào m_i/G ở biến thể đầu.** Cosine cao không biến term thành source-backed KB alias.

## 2. BM25

```text
B = (1 − w) B_original + w B_enriched
u_B = B                                  # pretransform=raw
u_B = B / query_scale                     # pretransform=query_scale
z_B = sigmoid((u_B − x0) / T), T > 0
```

w khởi tạo 0,25. Original/enriched phải cùng recipe; không vá external BM25F bằng enriched prototype khác distribution. Query scale chỉ dùng nếu tương thích recipe/index; missing expanded theo policy khai báo.

Fit học x0/T trên calibration judged positives/negatives. x0 khác candidate threshold. Tune đổi w/pretransform phải refit trên calibration từ raw cache, không dùng tune/holdout labels để fit.

## 3. Dense tổng quát

```text
z_H = normalize_head(raw_dense_head)
z_C = normalize_chunk(raw_dense_chunk)
D_generic = (h z_H + c z_C) / (h + c)
```

Khởi tạo h=c=0,50; chuẩn hóa từng source riêng bằng affine/sigmoid khai báo. Affine [-1,1] chỉ phù hợp source cosine đúng domain. Missing giữ mask; available-policy renormalize trên component có thật, error-policy từ chối. Observed zero khác thiếu score.

## 4. SapBERT concept–term similarity

Encoder mục tiêu [SapBERT-XLMR multilingual](https://huggingface.co/cambridgeltl/SapBERT-UMLS-2020AB-all-lang-from-XLMR) xử lý concept/term ngắn; không mặc định encode nguyên document như sentence retriever.

Document terms có literal spans trong title/body, field/kind/assertion. Kiểm lại spans/hashes theo index trước semantic cache. SapBERT chỉ xét original query concepts có kind khác intent. Encoder dùng CLS, L2, max_length=64, batch_size=64 khởi tạo, checkpoint pin bằng local identity/revision rõ.

```text
e_i = L2(CLS(encoder(query_concept_i)))
v_j = L2(CLS(encoder(document_literal_term_j)))
c_ij = dot(e_i, v_j)                       # cosine, cache toàn matrix
t_ij = clip((c_ij − low) / (high − low), 0, 1)
s_i = max_j t_ij                           # i: original concepts, loại kind=intent
S_sap = Σ_i a_i s_i / Σ_i a_i              # khi có actual pair và tổng importance>0
```

Khởi tạo low=0,20, high=0,90; đây là transform ước lượng, chưa probability calibration đã fit. Max từng concept tránh cộng lặp nhiều aliases. Giữ full matrix cho phép đổi normalizer và a_i offline. Khi có ít nhất một actual concept–term pair, concept riêng thiếu comparison đóng góp 0. Nếu không có eligible concept, tổng importance=0 hoặc toàn matrix không có pair thì S_sap là missing; available-policy renormalize các dense branches còn bật/có thật, error-policy báo lỗi.

S_sap cao chưa chứng minh cùng concept, đúng relation/population hoặc document trả lời intent. Assertion lưu để audit; phủ định không tự irrelevant. Phân biệt document_terms có terms=[] với thiếu record. Embeddings import cần provenance/namespace/dimension; fixture vectors không phải model inference thật.

## 5. Dense mới và fusion

```text
D_new = (1 − λ) D_generic + λ S_sap
F = α z_B + (1 − α) D_new
```

Khởi tạo λ=0,30. λ=0 giữ generic dense; λ=1 là ablation thay dense bằng SapBERT. Config:

```json
"sapbert": {"weight": 0.30, "method": "affine", "low": 0.20, "high": 0.90}
```

Khi đủ components, trọng số là α cho BM25; (1−α)(1−λ) cho generic; (1−α)λ cho SapBERT. Missing-policy/effective weights phải log; BM25-only opt-in rõ.

**α là tỷ trọng BM25, không phải điểm cộng evidence.** Với dense cố định: dF/dα=z_B−D_new. Tăng α có thể giảm F nếu BM25 thấp. Giữ SapBERT trong D_new tránh semantic confirmation tự chuyển weight sang lexical score thấp, nhưng chưa chứng minh gate tối ưu.

## 6. Selection và LLM tùy chọn

Sort deterministic theo F/ties; lọc global hoặc max-original-tier bucket threshold, sau đó optional min_docs fill/max_docs cap. Log threshold-pass/floor-add/cap-remove riêng.

`select` lấy IDs đã selected từ run và giới hạn shortlist/text. LLM chỉ chọn subset IDs được gửi; kiểm duplicate/unknown IDs, deterministic min-fill và cap. Initial max_candidates=40, document_max_chars=2.000, min_docs=0, max_docs=40: budget ước lượng.

Selector không sửa F hoặc thêm doc ngoài shortlist. Lưu chosen IDs, raw response và selection diagnostics riêng. So với control cùng shortlist/output budget. Đổi candidate set/corpus/prompt/model phải invalid cache.

## 7. Invariants

- BF output subset union; SapBERT/selector không tìm doc ngoài union. BR corpus retrieval là experiment riêng.
- Inference không đọc labels; calibration/tune/holdout không overlap; duplicate queries cùng split.
- Tune λ/affine/tier/alpha/threshold từ full raw cache không gọi lại encoder/LLM.
- Literal spans, model/prompt/corpus identity và masks được kiểm; cosine không thành alias KB đã duyệt.
- Fit stage học BM25 sigmoid; không gọi Sap transform là learned khi mới ước lượng/tune ranking.
- Native chunk/downstream p̂ threshold khác candidate threshold. Demo/tests chưa chứng minh gain.

[Study](BEAR_REPLACEMENT_STUDY.md) định nghĩa phép so sánh; [handover](TXT_handover.md) ghi cache/commands.
