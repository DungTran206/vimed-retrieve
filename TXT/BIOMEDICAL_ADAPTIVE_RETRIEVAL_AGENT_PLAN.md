# Biomedical Evidence-Aware Adaptive Retrieval (BEAR)

> **Tài liệu thiết kế lịch sử, ngày18/10.** [PLAN v3.3](PLAN.md) và [BEAR_ALGORITHM](BEAR_ALGORITHM.md) khôi phục mục tiêu BEAR chọn doc/chunk trên [baseline0,391](PIPELINE_0391.md). Audit/threshold tuning chỉ hỗ trợ. Nội dung dưới đây giữ để tra ý tưởng/code cũ; dùng proposal/PLAN hiện hành khi khác scope.

> **Implementation specification / Research plan cho coding agent**  
> Ngôn ngữ: tiếng Việt | Phiên bản tài liệu: 1.0 | Ngày tổng hợp: 18/10/2026  
> **Nguồn nội bộ:** `HANDOVER.md` (snapshot leaderboard 15/10/2026) và `biomedical_multilingual_hybrid_retrieval_project.md`.  
> **Mục tiêu:** đánh giá và triển khai có kiểm soát *query-adaptive hybrid retrieval*, không phá hủy baseline đã hoạt động.

## 0. Quy ước và chỉ dẫn bắt buộc cho agent

### 0.1. Phân biệt mức độ chắc chắn

- **[ĐÃ CÓ]**: thông tin được mô tả rõ trong hai file nguồn. Không đồng nghĩa đã đọc/kiểm tra mã nguồn thực tế.
- **[ĐỀ XUẤT]**: thiết kế mới trong tài liệu này; **chưa được thực nghiệm chứng minh**.
- **[GIẢ THUYẾT]**: phát biểu nghiên cứu cần benchmark/ablation.
- **[CHƯA XÁC MINH]**: phải kiểm tra repository, cấu trúc dữ liệu hoặc luật chấm trước khi thực thi.

### 0.2. Quy tắc vận hành

1. **Không tự viết lại pipeline hiện tại.** Giữ `build_best.sh` và luồng xuất submission gốc như baseline bất biến.
2. **Đọc repository và kiểm tra schema thực tế trước khi code.** Không suy diễn rằng các key, bảng, CLI flag, score scale hoặc path đề xuất bên dưới đã tồn tại.
3. **Tạo module mới ở nhánh/đường dẫn độc lập, có feature flags và chế độ `baseline`.** Tắt toàn bộ module mới phải tái tạo ranking/submission baseline, nếu đầy đủ dữ liệu.
4. **Không tái chạy bước nặng** (crawl / clean / embedding toàn kho / Qwen rerank) nếu đã có artifact phù hợp. Thử nghiệm trên candidate pool cỡ nhỏ trước.
5. **Không dùng điểm tổng leaderboard như nhãn relevance của từng `(query, document)`**. Không dùng `p(gold)` làm ground truth.
6. Thực hiện **một giả thuyết tại một thời điểm**. Ghi lại input snapshot, config, seed, model/checkpoint, kết quả và thay đổi so với baseline.
7. Không làm thay đổi quy tắc nộp: ID, offset, ngôn ngữ/tập corpus hợp lệ, giới hạn kích thước ZIP. Luật chấm chính thức chỉ được kết luận sau khi đọc `CLAUDE.md` / tài liệu BTC.
8. Bất kỳ thay đổi nào không có bằng chứng tăng metric phải ở chế độ tùy chọn (`experimental`) thay vì mặc định.
9. Nếu phát hiện các run mới hơn `HANDOVER.md`, **cập nhật bảng baseline theo bằng chứng repository**, nhưng không âm thầm ghi đè snapshot 15/10/2026 mô tả trong tài liệu này.
10. Gặp đầu vào thiếu/không hợp lệ: báo lỗi/đánh dấu missing và sinh báo cáo; **không tự tạo dữ liệu hay nhãn**.

---

## 1. Mục tiêu và định hướng

### 1.1. Bài toán

Truy hồi **document ID và chunk ID/văn bản chunk** liên quan đến câu hỏi y khoa trong kho tài liệu đa ngôn ngữ, chủ yếu VI/ZH theo pipeline đã ghi nhận. Metric cuộc thi tập trung vào **F2 micro**; đầu ra cần tuân thủ đúng định dạng nộp.

Các truy vấn có thể gặp:
- Rare medical entities (gene, protein, biến thể, thuốc, bệnh).
- Exact medical term match nhưng sai quan hệ giữa các thực thể.
- Synonym/abbreviation mismatch (HCC ↔ hepatocellular carcinoma).
- Translation/terminology mismatch VI ↔ ZH/EN.
- Tài liệu dài, keyword xuất hiện ở các đoạn khác nhau.

### 1.2. Giả thuyết nghiên cứu chủ đạo

> **[GIẢ THUYẾT]** Các feature mô tả bằng chứng lexical y khoa (`exact coverage`, `concept coverage`, `critical entity coverage`, `local passage coverage`) có thể dự báo được khi nào lexical retrieval đáng tin hơn semantic/sparse retrieval. Từ đó **adaptive fusion** có thể vượt **fixed fusion** trên những tập query nhất định.

Không mặc định chứng minh được giả thuyết này. Nếu ablation không cho thấy cải thiện, giữ baseline.

### 1.3. Quyết định kỹ thuật

**Ưu tiên triển khai:**

1. **Lexical Evidence Engine** dùng artifact đang có.
2. **BGE-M3 sparse scoring** trên candidate pool cố định, trước khi cân nhắc SPLADE riêng.
3. **Fixed fusion + sparse**, rồi **query-level adaptive fusion**.
4. Chỉ khi có bằng chứng rõ: document-level gate, medical synonyms expansion, new candidate discovery, SPLADE độc lập.
5. Chunk selection/allocation được đánh giá như một mục tiêu riêng, không trộn lẫn với doc retrieval.

---

## 2. Hiện trạng theo `HANDOVER.md` — nguồn sự thật về baseline snapshot

### 2.1. Kết quả đã được ghi lại (15/10/2026)

| Chỉ số | Giá trị | Ghi chú |
|---|---:|---|
| Submission | `w045_TF` | Bài được bàn giao trong `HANDOVER.md` |
| Doc F2 | **0.3605** | Giá trị leaderboard trong handover |
| Chunk F2 | **0.3279** | Giá trị leaderboard trong handover |
| FINAL | **0.3442** | Snapshot 15/10/2026, **không khẳng định là kết quả mới nhất** |
| Fingerprint doc | `c1e068422e5f` | Phải trùng khi tái lập baseline |
| Fingerprint chunk | `fd07f9fc029a` | Phải trùng khi tái lập baseline |

`(0.3605 + 0.3279)/2 = 0.3442`, nhưng **cách tính FINAL chính thức chưa được xác minh từ luật chấm**. Không hardcode giả thuyết này thành evaluator.

`w045_TF` dùng cùng tập doc như `w045_zh38w_e120` (0.3272 theo handover) và thay đổi cách phân bổ chunk dùng `p(gold)`, tăng khoảng **0.017** điểm FINAL. Vì vậy thay đổi thứ tự doc và chunk policy cần được đo riêng.

### 2.2. Hạ tầng/pipeline [ĐÃ CÓ]

```text
ViBioMIR / URL corpus
  -> crawl + clean + chunk theo offset (~900 token)
  -> corpus_new.sqlite

Query
  -> Qwen3.5-9B: y khoa entities + translate EN/ZH
  -> queries_enriched.jsonl

Retrieval VI
  -> slug BM25
  -> BM25F có dấu (title 3x, tags 2x, ...)
  -> entity + bigram BM25
  -> BGE-M3 Dense(title), Dense(title+600 ký tự body)
  -> RRF pool H top-1000
  -> Qwen3-Reranker-4B (P(yes), chấm top-400)
  -> BGE-M3 chunk-dense / chunk-rerank
  -> c_blendQB8, c_blendQB8w05

Retrieval ZH
  -> BGE-M3 + Qwen3-Embedding-8B
  -> RRF (BGE:1, Qwen8B:0.3)

Merge + submission
  -> ghép ZH vào VI (w=0.45)
  -> ưu tiên thứ tự 120 doc đầu theo c_blendQB8w05
  -> lọc doc thuộc corpus cho phép
  -> val_calib.py tính p(gold)
  -> chunk allocation
  -> submission.py: 200 doc/query, ZIP LZMA
```

**File/script [ĐÃ CÓ theo handover]:**

| File/script | Mục đích |
|---|---|
| `build_best.sh` | Tạo lại baseline, fingerprint |
| `fuse.py` | Weighted RRF |
| `hybrid_cands.py` | Tập doc từ một danh sách, thứ tự top-120 từ danh sách khác |
| `filter_new_corpus.py` | Chỉ giữ corpus hợp lệ và bù 200 doc |
| `val_calib.py` | `p(gold)` scoring/fit từ điểm tổng bài chấm |
| `submission.py` | Tạo kết quả nộp; ID nguyên, chunk nguyên văn theo offset |
| `audit.py` | Kiểm tra chuỗi dữ liệu |
| `data/corpus_new.sqlite` | Corpus VI + ZH, 5.5 GB, có bảng chunk |
| `data/queries_enriched.jsonl` | Query với entity/translation |
| `data/rp/c_blendQB8.jsonl` | Rank VI sau hybrid/rerank |
| `data/rp/c_blendQB8w05.jsonl` | Rank VI dùng thứ tự top-120 |
| `data/qwen_all_h.jsonl` | Qwen P(yes) cho các doc được chấm |
| `data/dense_chunk_full_rank.jsonl` | Dense trên chunk |
| `data/chunk_scores_mix.jsonl` | Điểm chunk hỗ trợ chọn chunk |
| `data/dense_zhC3_{vi,zhq,zhq109}_rank.jsonl` | BGE-M3 ZH ranks |
| `data/dense_zhQ8_{vi,zhq,zhq109}_rank.jsonl` | Qwen8B ZH ranks |
| `data/val/beta.json` | Hệ số p(gold) fit từ điểm tổng |
| `data/vibiomir_new/links_corpus_vi_en_zh.parquet` | Danh sách corpus của BTC |

**Cần đọc thêm trước khi thay baseline:** `PROGRESS.md`, `METHODS.md`, `CLAUDE.md` (được `HANDOVER.md` dẫn chiếu nhưng không có trong 2 attachment cung cấp ở đây).

### 2.3. Submission policy hiện tại [ĐÃ CÓ]

- `200 doc/query`.
- Cơ chế cơ sở: `2 chunk/doc` cho top-40, `1 chunk/doc` cho rank 41–120.
- Điều chỉnh: top-120 có `p(gold) < 0.04` thì bỏ chunk; rank 121–200 có `p(gold) >= 0.05` thì thêm 1 chunk.
- Ngưỡng nêu trên được tune qua leaderboard; **không phải ngưỡng probability đã hiệu chỉnh bằng ground truth**.
- `doc_id` phải là **integer**, chunk xuất nguyên văn theo offset; ZIP tối đa 100 MB; nguồn handover cho biết LZMA được chấp nhận.
- Hạn chế EN: trong handover có kho 240k PubMed nhưng **chưa dùng** vì chưa có nhãn EN trên bảng điểm; chỉ sử dụng khi xác minh được corpus hợp lệ.

### 2.4. `p(gold)` là gì và không là gì

- Theo handover: một mô hình logistic dùng các feature như `logit(P(yes) Qwen)`, chunk-dense cosine, ZH BGE cosine; `beta` được fit bằng **điểm tổng** từ 41 bài leaderboard; `DOCS_P = mean(p)` trong phương pháp fit được mô tả.
- `p(gold)` được dùng **để quyết định chunk**, không làm thay đổi tập doc trong submission được bàn giao.
- **Không có bằng chứng từ 2 file rằng nó là probability được calibrate theo nhãn item-level.** Không dùng làm ground truth để train mới; tránh teacher-bias/leakage.

---

## 3. So sánh ý tưởng với hiện trạng

| Thành phần | Đã có trong pipeline? | Hướng đi |
|---|---|---|
| VI/EN/ZH query translation | Có (Qwen3.5-9B) | Tái sử dụng, audit lỗi thuật ngữ |
| Medical entity extraction | Có | Trích feature có cấu trúc |
| BM25, BM25F, entity BM25 | Có | Không xây lại |
| Dense doc/chunk | Có | Tái sử dụng score/rank |
| RRF fixed fusion | Có | Giữ baseline để so sánh |
| Qwen4B reranking | Có | Tái sử dụng, không rerun vô cớ |
| Per-pair lexical evidence | Chưa mô tả là module riêng | **Pha 2** |
| Critical/concept coverage | Chưa mô tả là module riêng | **Pha 2** |
| BGE-M3 sparse branch | Chưa mô tả là branch hiện hành | **Pha 3**, cần encode lexical weights nếu artifact chưa có |
| Query-level dynamic fusion | Chưa mô tả | **Pha 4** |
| Document-level dynamic fusion | Chưa mô tả | Sau query gate |
| SPLADE độc lập | Chưa mô tả | Thử sau BGE sparse, theo từng ngôn ngữ |
| Verified medical expansion | Chưa mô tả là branch | Sau khi xác minh có lexical failure |
| Chunk policy p(gold) | Có | Giữ nguyên trong phép thử doc ranking đầu tiên |

---

## 4. Kiến trúc mục tiêu [ĐỀ XUẤT]

```text
                          EXISTING PIPELINE
      q_vi ---> Qwen entities + translation ---> q_vi/q_en/q_zh
         |                                           |
         |                    EXISTING RETRIEVERS   |
         +------ BM25 family, dense, Qwen, chunk-dense, ZH ----+
                                                                |
                                                 Candidate pool + ranks/scores
                                                                |
                NEW FEATURE ENGINE                              |
      entity normalization / IDF / critical terms               |
                 |                                              |
      exact + concept + critical + local chunk coverage --------+
                 |                                              |
           query-level evidence                                 |
                 |                                              |
                NEW BGE-M3 SPARSE scoring (optional) ------------+
                                                                |
                             Fixed-Fusion Control & Adaptive Gate
                                                                |
                               Residual rank-based fusion
                                                                |
                        doc rerank (optionally pool expansion)
                                                                |
                           existing chunk selection + p(gold)
                                                                |
                            existing submission + audit + ZIP
```

**Tách rõ 3 năng lực:**

1. **Candidate discovery**: tìm tài liệu chưa nằm trong pool cũ (muốn tăng recall thật sự).
2. **Document reranking**: sắp thứ tự candidate có sẵn (có thể tăng chất lượng cấp chunk, không tự động tăng Doc F2 nếu tập doc giữ nguyên và metric doc là set-based).
3. **Chunk reranking/allocation**: tối ưu chunk F2 và FINAL; không trộn với đánh giá retriever.

V1 **chỉ can thiệp rerank** và giữ candidate pool + chunk policy bất biến để dễ đối chiếu.

---

## 5. Biomedical Lexical Evidence Engine [ĐỀ XUẤT]

### 5.1. Term importance

**Trong ý tưởng gốc:**

\[
I_0(t)=R(t)\cdot M(t),\quad R=\text{normalized IDF},\quad M=\text{medical specificity}
\]

**Biến thể khuyến nghị thử (không mặc định tốt hơn):**

\[
I(t)=\widetilde{\mathrm{IDF}}(t)\,[\varepsilon+(1-\varepsilon)M(t)]
\]

với `IDF_normalized, M in [0,1]`, `epsilon in (0,1)`; tránh loại hoàn toàn thuật ngữ khi entity extraction bỏ sót (`M=0`). Chỉ so sánh qua ablation:
- raw term count;
- IDF-only;
- IDF × medical specificity (gốc);
- epsilon-smoothed importance (biến thể).

**Triển khai:**
- IDF theo từng **ngôn ngữ và corpus snapshot**; thống nhất tokenizer của nhánh BM25 liên quan.
- Ưu tiên **multi-token entity span** (`ung thư vú`, `myocardial infarction`) thay vì đếm token rời rạc.
- Critical term phải dựa vào entity type và nội dung query, không chỉ rarity.
- `tau_I` là threshold *chưa được lựa chọn*; không tùy tiện hardcode theo intuition.

### 5.2. Các feature coverage

Với tập term/entity spans `T(q)`, trọng số `I(t) > 0` và hàm match rõ ràng:

\[
L_{exact}(q,d)=\frac{\sum_{t\in T(q)} I(t)\,\mathbf{1}[\mathrm{exact}(t,d)]}{\sum_{t\in T(q)}I(t)}
\]

\[
L_{concept}(q,d)=\frac{\sum_{t\in T(q)} I(t)\,\mathbf{1}[\mathrm{verified\_alias/concept}(t,d)]}{\sum_{t\in T(q)}I(t)}
\]

\[
C_{critical}(q,d)=\frac{\sum_{t\in T_{critical}(q)} I(t)\,\mathbf{1}[\mathrm{match}(t,d)]}{\sum_{t\in T_{critical}(q)}I(t)}
\]

**Lưu ý:**
- Exact vs concept cần lưu riêng; `verified_alias/concept` chỉ được bật nếu có dictionary / ontology đáng tin cậy, **không coi cosine cao là synonym**.
- Phải phân biệt `missing` với `0`: nếu không có critical entities, `critical_coverage = null` và `has_critical_terms = false`.
- Nếu denominator = 0, trả `null` / availability mask; **không chia 0, không tự gán coverage = 0**.
- Exact matching cần chuẩn hóa Unicode, case, khoảng trắng, biến thể ngôn ngữ; không normalize quá mức khiến BRCA1 ≡ BRCA2 hoặc xóa chỉ số đột biến.
- `L_high` không đồng nghĩa `P(relevant)` cao: BRCA1 có thể nằm trong bài viết về ung thư buồng trứng khi query hỏi ung thư vú.
- Có thể thêm relation/intent features sau này nhưng cần kiểm chứng riêng.

### 5.3. Local passage evidence

Tài liệu dài thường chứa nhiều entity không liên quan nhau. Do đó đánh giá cả title và chunk:

\[
L_{local}(q,d)=\max_{c\in\mathrm{Chunks}(d)}L_{exact}(q,c)
\]

\[
L^*(q,d)=\alpha\,L_{title}(q,d)+(1-\alpha)\,L_{local}(q,d)
\]

- `max` có thiên lệch theo số lượng chunk: cần so sánh `max`, `top-2 mean`, title-only, title+best-chunk.
- Mọi chunk text phải đọc từ nguồn chunk offset sẵn có; không tạo/chỉnh chunk phá invariant nguyên văn.
- Bắt đầu ở **subset candidates**: nếu quá tốn I/O, chỉ tính local features cho top-M nhất quán giữa các thí nghiệm.
- Tránh leakage: không dùng nhãn hidden leaderboard để chọn chunk.

### 5.4. Query-level evidence (V1)

Khác `L(q,d)`, query-level evidence mô tả chất lượng match của **cả pool lexical**:

\[
E_q = f\big(\{L_{exact}(q,d),C_{critical}(q,d),rank_B(q,d)\}_{d\in TopK_B(q)}\big)
\]

**V1 đơn giản:** weighted average của coverage ở top-K BM25, với weight giảm theo rank. `K`/hàm giảm trọng số phải đưa vào config và ablate. Không gọi `E_q` là calibrated probability of retrieval success.

### 5.5. Các test tối thiểu

- `BRCA1` khác `BRCA2`.
- `HCC` và `hepatocellular carcinoma`: exact khác, concept chỉ có nếu verified alias.
- Query không chứa medical entity; zero-weight term; empty document.
- VI phrase match, ZH segmentation/character n-gram test riêng.
- Token xuất hiện rải rác các chunk → full-doc match cao nhưng local coverage thấp.
- `coverage in [0,1] or null`, xác thực flags/missing.

---

## 6. BGE-M3 Sparse và SPLADE [ĐỀ XUẤT]

### 6.1. Tại sao thử BGE-M3 Sparse trước

BGE-M3 hỗ trợ cả **dense** và **lexical/sparse token weights**. Đây là cách thử learned lexical signal mà chưa cần thêm checkpoint độc lập.

**Không coi BGE-M3 Sparse là SPLADE:** BGE-M3 dùng contextual lexical token weights; SPLADE dùng MLM-style vocabulary expansion. Checkpoint SPLADE phổ biến thiên về tiếng Anh, cần xác thực với VI/ZH.

**Cảnh báo:** có dense embedding từ BGE-M3 **không đồng nghĩa** có sparse weights lưu trên đĩa. Agent phải kiểm tra artifact; nếu thiếu, encode lại **candidate pool** để lấy `lexical_weights`, không tự chạy full corpus.

### 6.2. Các bước

1. Xác định pool cố định (ví dụ union của top lists hiện tại, giới hạn kích thước theo tài nguyên thật).
2. Kiểm tra `model checkpoint`, tokenizer, phiên bản thư viện và định dạng lexical weights.
3. Encode query theo đúng ngôn ngữ (`q_vi`, `q_zh` nếu ZH; cân nhắc cross-lingual separately).
4. Encode candidate doc title / title+body / chunks theo các biến thể riêng; lưu cache theo `(model_version, corpus_hash, field, doc_id)`.
5. Sparse score trên các cặp được encode; tạo ranking `sparse_rank`.
6. Chạy **fixed RRF + sparse** trước adaptive fusion.
7. Đánh giá riêng VI và ZH; không kết luận sparse tốt chỉ vì có độ tương đồng cao với BM25.

**Không gộp nhầm missing scores:** document không được chấm sparse vì nằm ngoài sampled pool phải được đánh dấu `not_scored`; không suy diễn thành score 0 hoặc negative relevance.

### 6.3. Khi nào xem xét SPLADE độc lập?

Chỉ khi:
- Đã thấy vocabulary mismatch chưa được BM25/BGE sparse giải quyết;
- Có checkpoint hợp lệ, phù hợp ngôn ngữ và giới hạn tài nguyên/cuộc thi;
- Thí nghiệm subset cho thấy lợi ích so với `BGE sparse + fixed fusion`;
- Có phương án xử lý input dài hơn context window và chi phí indexing.

Giai đoạn đầu: ưu tiên EN (nếu corpus/metric cho phép) hoặc subset VI/ZH đã được kiểm chứng, **không indexing toàn bộ trước**.

---

## 7. Dynamic / Residual Fusion [ĐỀ XUẤT]

### 7.1. Vấn đề của gate gốc

Trong file ý tưởng:

\[
g(q,d)=\sigma\Big(\frac{L(q,d)-\tau_L}{T}\Big)
\]

\[
w_B=w_B^{low}+g(w_B^{high}-w_B^{low}),\quad
w_S=w_S^{high}-g(w_S^{high}-w_S^{low}),\quad
w_D=1-w_B-w_S
\]

**Rủi ro:** document có BM25 cao và lexical match cao nhưng sai ý có thể được *tăng điểm thêm*, tức khuếch đại false positives. Hơn nữa công thức cần kiểm tra `w_D >= 0`.

### 7.2. V1: query-level gate, không trực tiếp làm hard filter

\[
g_q=\sigma\Big(\frac{E_q-\tau_q}{T_q}\Big),\quad T_q>0
\]

\[
\mathbf w(q)=g_q\mathbf w^{lex}+(1-g_q)\mathbf w^{sem}
\]

Trong đó hai vector **không âm**, tổng bằng 1; có thể parameterize bằng softmax. V1 dùng query-level vì dễ kiểm chứng và ít gây vòng lặp tự củng cố ở từng doc hơn.

### 7.3. So sánh score giữa các retriever

Tránh cộng thẳng raw BM25, cosine, sparse dot-product, Qwen P(yes) do thang điểm khác nhau và `P(yes)` chưa chắc calibrated.

V1 dùng rank-based component:

\[
r_i(q,d)=\begin{cases}
\dfrac{k+1}{k+rank_i(q,d)},& \text{nếu ranked}\;
0,&\text{nếu thực sự không được retrieve}
\end{cases}
\]

`k` trong formula là hyperparameter kiểm chứng/tune, **không coi mặc định nào là `fuse.py` hiện tại**. Cần phân biệt *not retrieved* và *not scored*.

### 7.4. Residual adaptive fusion

\[
S_{new}(q,d)=(1-\lambda)\,\widetilde S_0(q,d)
+\lambda\Big[w_B(q)r_B(q,d)+w_S(q)r_S(q,d)+w_D(q)r_D(q,d)\Big]
\]

- `S_0`: kết quả xếp hạng baseline, được chuyển thành `S0_tilde` bằng **cùng rank-based mapping**.
- `lambda in [0,1]`: mức ảnh hưởng branch mới.
- `lambda = 0`: **ranking** phải trùng baseline (score numerical không nhất thiết giống file cũ).
- V1 có cả control `fixed`: dùng vector weight cố định nhưng giữ nguyên cách xây pool, rank mapping, candidate set.
- `B` có thể là rank của nhóm BM25 từ artifact cũ, `D` là nhóm Dense; cách tổng hợp các nhánh con **phải được cấu hình và ghi rõ**, không tùy tiện bỏ một nhánh đang có.
- Nếu chưa có sparse scores thì **không khởi tạo weight sparse rồi âm thầm nhân với 0**; chạy chế độ `BM25+Dense` rõ ràng.

### 7.5. V2 — chỉ khi V1 vượt fixed baseline

Thử document-specific local adjustment, chẳng hạn bounded residual:

\[
S_{v2}(q,d)=S_{v1}(q,d)+\eta\,h(L_{exact},L_{concept},C_{critical},L_{local})
\]

Với `eta` nhỏ/tune; không hard-filter theo critical coverage. Có thể thử query+document gate sau đó, nhưng phải đánh giá hard negatives và relation mismatch.

### 7.6. Tuning tránh overfit

Thứ tự thay đổi:
1. Freeze định nghĩa term evidence; đo correlations/quality.
2. Chọn fixed fusion baseline hợp lý và khóa lại.
3. Tune một số ít tham số (`tau_q`, `T_q`, `lambda`) trên **validation**.
4. Đánh giá trên holdout độc lập và xem từng language/failure mode.
5. Sau đó mới thử local gate, confidence/QPP features hoặc learned router.

Không cùng lúc grid-search mọi threshold, IDF weight, multi-view choices, gates, chunk policy và `p(gold)` trên một leaderboard nhỏ.

---

## 8. Medical dictionary expansion [PHASE SAU]

Ý tưởng gốc: semantic matching đến dictionary để thêm medical terms vào BM25. **Rủi ro:** cosine cao không chứng minh là synonym (BRCA1 ≠ BRCA2, hai thuốc cùng nhóm ≠ cùng hoạt chất).

**[ĐỀ XUẤT] Quy trình an toàn:**

```text
query
  -> entity extraction
  -> canonical entity matching / concept identifier
  -> verified synonyms/aliases (nếu ontology cho phép)
  -> q_lang_expanded = q_lang + weighted verified aliases
  -> BM25 branch only
```

- Tách query `q_vi`, `q_en`, `q_zh`, không trộn lexical features giữa ngôn ngữ không phù hợp.
- Tái sử dụng translation đã có; giữ tên gene/protein/mutation/drug khi cần.
- BM25 nhận expanded query; Dense/Sparse đầu tiên vẫn nhận bản không expansion để dễ ablate.
- Feature coverage từ **original terms** và **expanded aliases** phải ghi riêng, tránh tự tăng evidence vì tự thêm synonyms.
- Nguồn thuật ngữ có thể cân nhắc MeSH/UMLS hoặc dictionary được cung cấp; **kiểm tra giấy phép, phạm vi ngôn ngữ và độ phủ trước khi sử dụng**.
- Các chứng cứ/thuật ngữ không xác minh được thì không thêm vào production.

---

## 9. Benchmark, ground truth và evaluation

### 9.1. Không trộn ba cấp mục tiêu

| Loại thử nghiệm | Có thể thay đổi doc F2? | Có thể thay đổi chunk F2? |
|---|---|---|
| Chỉ reorder đúng cùng tập top-200 | Không, nếu doc F2 chấm theo tập ID | Có |
| Thay tập top-200 | Có | Có |
| Giữ doc, thay chunk selection | Không | Có |
| Thay phân bổ chunk | Không | Có |

**Không suy diễn cải thiện Doc F2 nếu chỉ thay rank mà giữ nguyên set**. Luật chấm chính thức cần xác minh.

### 9.2. Vấn đề dữ liệu đánh giá

`HANDOVER.md` ghi `p(gold)` fit từ **điểm tổng 41 bài đã chấm**, **không có item-level relevance labels trong 2 tài liệu nguồn**.

Bắt buộc phân biệt:
- `official` — metric từ leaderboard/BTC.
- `local_qrels` — nhãn relevance đã được kiểm chứng ở cấp item.
- `proxy` — similarity, lexical coverage, rank agreement, Qwen judgment (không phải ground truth).

Không báo cáo `F2` từ các proxy nếu chưa có định nghĩa nhãn và evaluator tương ứng.

### 9.3. Gợi ý validation set

Nếu chưa có qrels, **đề xuất** gán nhãn khoảng 100 queries đại diện cho 5 failure modes (mỗi nhóm có thể bắt đầu ~20, thay đổi theo phân phối thực tế):

1. Exact terminology.
2. Synonym/paraphrase.
3. Abbreviation/variant.
4. Multilingual mismatch.
5. Hard negatives / ambiguity / relation mismatch.

Với mỗi query, lấy candidates mà các retriever bất đồng. Nhãn phân tích (không đồng nhất mặc định với qrels BTC):
- `0`: không liên quan/sai entity.
- `1`: đúng chủ đề nhưng chưa trả lời được.
- `2`: chứa thông tin trả lời thực sự.

Có thể để LLM đề xuất nhãn, nhưng **phải audit các ca khó bằng người hoặc nguồn đáng tin**. Khóa holdout, không dùng holdout để tối ưu threshold.

### 9.4. Metrics nên xuất

- Nếu có official/local ground truth hợp lệ: Doc F2, Chunk F2, FINAL hoặc F2 mô phỏng (ghi rõ quy tắc).
- Recall@K, Precision@K, MRR/nDCG nếu có qrels thích hợp.
- `candidate_overlap`, `new_relevant_docs`, `false_positive_additions`, `top120_movement`, `rank_displacement`, `coverage_bins`.
- Báo cáo theo ngôn ngữ VI, ZH, EN (chỉ khi hợp lệ) và từng failure mode.
- Cost: số cặp encode, GPU time nếu đo được, peak VRAM/RAM, kích thước cache/index, I/O.
- Paired per-query comparisons; nếu đủ nhãn có thể bootstrap confidence intervals theo query.

### 9.5. Ablation matrix

| ID | Biến thể | Câu hỏi kiểm chứng |
|---|---|---|
| E0 | Original baseline | Tái lập ổn định? |
| E1 | Exact lexical coverage | Có mang tín hiệu ngoài BM25 không? |
| E2 | Entity/IDF weighted coverage | Có hơn raw count/IDF-only? |
| E3 | Critical entity coverage | Có giảm false positives medical? |
| E4 | Title + best-chunk evidence | Có hơn full-doc evidence? |
| E5 | BGE-M3 Sparse + **fixed** fusion | Sparse có bổ sung hiệu quả? |
| E6 | Query-level dynamic fusion | Có vượt fixed fusion cùng features? |
| E7 | Document-level local adjustment | Có thêm lợi ích hay khuếch đại bias? |
| E8 | Verified medical expansion | Tăng recall hữu ích hay tăng noise? |
| E9 | Independent SPLADE (conditional) | Có vượt BGE sparse phù hợp ngôn ngữ? |
| E10 | Chunk allocation adaptation | Có tăng chunk/FINAL thực sự? |

**Thứ tự bắt buộc:** E0 → E1–E4 → E5 → E6. E7–E10 chỉ khi chứng minh lợi ích hoặc có failure mode rõ ràng.

---

## 10. Kế hoạch thực hiện từng phase cho coding agent

### Phase 0 — Repo audit + baseline locking

**Mục tiêu:** biết repo thực có gì, tái lập snapshot an toàn.

**Công việc:**
- [ ] Đọc `HANDOVER.md`, idea markdown, `PROGRESS.md`, `METHODS.md`, `CLAUDE.md` nếu có trong repo.
- [ ] Kiểm tra `git status`, scripts, source-of-truth paths; không sửa luồng cũ.
- [ ] Kiểm tra yêu cầu mô hình, phiên bản dataset/corpus, rule nộp hiện hành.
- [ ] Kiểm kê data artifacts (hash, size, schema), kiểm tra thiếu file.
- [ ] Khi đủ dữ liệu: chạy `bash build_best.sh runs/best` trong môi trường phù hợp.
- [ ] Đối chiếu fingerprint `doc=c1e068422e5f`, `chunk=fd07f9fc029a`.
- [ ] Tạo `experiments/baseline_manifest.json` ghi snapshot/config/checksum/kết quả.

**Done:** fingerprint đúng hoặc báo rõ lý do không thể tái lập; không chỉnh sửa artifact baseline.

### Phase 1 — Feature-table interface và experiment harness

**Mục tiêu:** tách retrieval hiện tại ra bộ feature deterministic dùng cho ablation.

**Công việc:**
- [ ] Đọc schema JSONL/SQLite thật; tạo schema adapter chứ không tự đoán key.
- [ ] Quy chuẩn khóa `(query_id, doc_id)` và mapping ID/doc-language.
- [ ] Join `baseline_rank`, BM25 ranks, Dense ranks, Qwen scores, chunk ranks/metadata.
- [ ] Đánh dấu `not_retrieved`, `not_scored`, `missing_artifact` khác nhau.
- [ ] Lưu Parquet/JSONL có metadata và version.
- [ ] Xây runner dùng config, log seed, metrics và diffs.

**Done:** chạy E0 trên pool cố định; lambda=0 giữ nguyên thứ tự baseline; kiểm tra no duplicate/missing doc IDs.

### Phase 2 — Lexical Evidence Engine

**Mục tiêu:** tạo feature evidence có tính giải thích, không thêm mô hình lớn.

**Công việc:**
- [ ] Normalize entities từ query enriched hiện tại.
- [ ] Tính IDF per-language trên corpus đã freeze.
- [ ] Implement raw/IDF/medical importance alternatives.
- [ ] `exact_coverage`, `concept_coverage` (optional nếu verified aliases có sẵn), `critical_coverage`, title/local-chunk coverage.
- [ ] Tạo `has_critical_terms`, availability masks, normalization diagnostics.
- [ ] Unit tests về entity/translation/long-document và relation mismatch.
- [ ] Phân tích score distribution theo rank bins/language/failure modes.

**Done:** coverage hợp lệ, null semantics chính xác, feature table reproducible; có báo cáo E1–E4 (và nêu rõ thiếu qrels nếu chưa có).

### Phase 3 — Learned sparse branch

**Mục tiêu:** kiểm định complementarity so với BM25 trước khi dynamic fusion.

**Công việc:**
- [ ] Kiểm tra BGE-M3 checkpoint hiện có và khả năng lấy lexical weights.
- [ ] Encode candidate pool subset theo field và ngôn ngữ, cache artifact.
- [ ] Tạo sparse rank và score distribution.
- [ ] Thử BM25/Dense/Sparse fixed RRF theo cùng pool và compare E5 với E0/E1.
- [ ] Phân tích lexical-low queries và hard negatives riêng.

**Done:** cost đo được; rõ lợi ích/thiệt hại từng ngôn ngữ; chưa vội full-corpus index.

### Phase 4 — Query-adaptive residual fusion

**Mục tiêu:** kiểm chứng dynamic có hơn fixed trong điều kiện công bằng.

**Công việc:**
- [ ] Tính `E_q` trên topK BM25 pool không dùng ground truth.
- [ ] Parameterize `w_lex`, `w_sem` trên simplex; kiểm tra tổng weight = 1.
- [ ] Implement `g_q` và score residual với `lambda`.
- [ ] Bật/tắt `adaptive` và `fixed` bằng config.
- [ ] Tune nhỏ gọn trên val, freeze và chạy holdout.
- [ ] Diff từng document rank change; check regressions theo VI/ZH.

**Done:** E6 có báo cáo paired comparison vs E5 fixed; nếu không hơn thì **không default-enable**.

### Phase 5 — Optional expansion/discovery/local gate

**Chỉ triển khai nếu dữ liệu chỉ ra điểm nghẽn**.

- [ ] Local document-level adjustment (E7).
- [ ] Verified synonym expansion theo language (E8).
- [ ] SPLADE subset evaluation (E9).
- [ ] Nếu muốn tăng Doc F2 thật sự: build candidate discovery branch thay vì chỉ rerank cùng 200 documents.

**Done:** từng biến thể có ablation độc lập; không suy diễn tăng Doc F2 từ ranking-only experiment.

### Phase 6 — Submission-level validation

- [ ] Thử `rerank-only` + chính sách chunk gốc.
- [ ] Thử `candidate set change` riêng, nếu đã có chứng cứ.
- [ ] Thử chunk allocation changes riêng (E10).
- [ ] Bảo đảm 200 doc/query, ID integer, chunk text nguyên văn theo offset, kho được phép, ZIP <=100 MB.
- [ ] Chạy `audit.py`, regression tests, fingerprint/manifest cho submission mới.
- [ ] Lưu bảng Doc/Chunk/FINAL trên official evaluation nếu có; tránh tune trực tiếp liên tục trên leaderboard.

**Done:** submission hợp lệ; có so sánh công bằng; có khả năng rollback tức thì.

---

## 11. Cấu trúc mã nguồn mới khuyến nghị [ĐỀ XUẤT]

> Chỉ tạo các file này sau Phase 0 audit; có thể điều chỉnh cho phù hợp layout repo thực tế.

```text
src/
  adaptive_retrieval/
    __init__.py
    query_features.py
    entity_normalizer.py
    term_importance.py
    lexical_evidence.py
    sparse_encoder.py
    score_features.py
    adaptive_gate.py
    residual_fusion.py

experiments/
  build_feature_table.py
  compare_retrievers.py
  run_fusion_ablation.py
  analyze_failure_modes.py
  evaluate_local_qrels.py
  compare_submission.py

configs/
  adaptive_v1.yaml

tests/
  test_entity_matching.py
  test_lexical_evidence.py
  test_fusion_weights.py
  test_baseline_parity.py
  test_submission_integrity.py
```

### 11.1. Feature schema tối thiểu (logic, cần map sang schema nguồn thật)

```text
query_id                 string/int, theo dataset gốc
doc_id                   int cho submission; giữ nguyên ID mapping
lang                     enum vi/zh/en/unknown
baseline_rank            int or null
baseline_score           float or null
bm25_rank                int or null
dense_rank               int or null
qwen_score               float or null
chunk_dense_score        float or null
sparse_rank              int or null
sparse_score             float or null
exact_coverage           float [0,1] or null
concept_coverage         float [0,1] or null
critical_coverage        float [0,1] or null
best_chunk_coverage      float [0,1] or null
has_critical_terms       bool
feature_availability     structured masks
adaptive_score           float or null
new_rank                 int or null
experiment_id            string
corpus_version           string/hash
query_version            string/hash
```

### 11.2. Config ví dụ — CHƯA phải bộ hyperparameter đã được tune

```yaml
mode: baseline  # baseline | fixed | adaptive
corpus_manifest: null  # điền sau audit
candidate_pool: existing_fusion_pool
language_scopes: [vi, zh]
features:
  exact: true
  concept: false  # bật khi có verified ontology/alias
  critical: true
  local_passage: true
  idf_scope: per_language
sparse:
  enabled: false
  backend: bge_m3_lexical
  scope: candidate_only
fusion:
  method: residual_rank
  lambda: 0.0  # bảo toàn ranking baseline
  rank_k: null  # agent phải chọn/tune có ghi nhận
  gate: query_level
  tau_q: null
  temperature_q: null
  weights_lex: null
  weights_sem: null
evaluation:
  use_official_if_available: true
  forbid_pgold_as_label: true
  freeze_chunk_policy: true
```

Không hardcode ví dụ thành production config. **Fail-fast** nếu chạy `mode: adaptive` nhưng tham số cốt lõi là null, thiếu sparse feature đã khai báo, hoặc thiếu source artifacts.

---

## 12. Rủi ro và biện pháp giảm thiểu

| Rủi ro | Mức độ | Cách xử lý |
|---|---|---|
| Không có item-level relevance labels | Rất cao | Local qrels + holdout; báo cáo proxy có nhãn rõ |
| Overfit 41 lần chấm leaderboard / các run tương quan | Rất cao | Không fit learned router trên aggregate score ít dữ liệu |
| Lexical evidence củng cố false positive | Cao | Query-gate V1; hard-negative tests; bounded local adjustment |
| Translation sai gene/drug/mutation | Cao | Entity-preserving audit; so sánh nguyên bản và dịch |
| Concept alias sai (`BRCA1` vs `BRCA2`) | Cao | Verified dictionary, tránh fuzzy cosine-only expansion |
| Sparse checkpoint lệch miền/ngôn ngữ | Cao | VI/ZH ablation và benchmark theo corpus thực |
| Full-document term coincidence | Trung bình/cao | Local passage coverage, title evidence |
| Fusion scale không tương thích | Trung bình | RRF/rank-based trước raw score calibration |
| Missing score bị hiểu thành score 0 | Trung bình/cao | Availability masks, score provenance |
| Không tăng Doc F2 vì chỉ reorder same set | Cao | Tách retrieval/candidate-discovery khỏi reranking |
| Baseline/ZIP bị hỏng khi refactor | Cao | Không sửa file cũ; parity tests và `audit.py` |

---

## 13. Định nghĩa hoàn thành (Definition of Done)

### Nhóm bắt buộc

- [ ] Đã audit repository và đối chiếu file nguồn với code/data thật.
- [ ] Đã xác minh baseline; nếu dữ liệu thiếu thì có blocker report, **không giả vờ đã chạy**.
- [ ] Có tính năng bật/tắt module mới; tắt thì tái lập ranking baseline.
- [ ] Có feature table thống nhất `(query_id, doc_id)` và đủ provenance/missing masks.
- [ ] Có unit tests cho lexical/concept/critical/local evidence.
- [ ] Có E0 và các so sánh E1–E4 với baseline/ablation đơn giản.
- [ ] Có E5 fixed fusion trước khi chạy E6 adaptive.
- [ ] Mỗi cải tiến đều có config, metric, report, thất bại/regressions, cost và quyết định `keep/reject`.
- [ ] Submission (nếu xuất) tuân thủ schema + ZIP + offsets + audit.

### Điều kiện bật adaptive trong phiên bản tốt nhất

Chỉ đề xuất nâng baseline khi:
1. Có bằng chứng thực nghiệm trên dữ liệu đánh giá hợp lệ (không chỉ `p(gold)` hay score proxy).
2. Vượt fixed fusion trong kiểm định cùng candidate pool / cùng chunk policy.
3. Không có regression nghiêm trọng ở ngôn ngữ, loại entity, hoặc failure mode cốt lõi.
4. Có thể tái lập và rollback.

Không có bằng chứng thỏa các điều kiện trên → **giữ baseline** và ghi kết quả âm tính trung thực.

---

## 14. Agent nên bắt đầu ngay từ đâu?

**Thực hiện theo đúng thứ tự sau:**

1. **Phase 0**: liệt kê code/data thực tế và dựng `baseline_manifest`.
2. **Phase 1**: feature-table loader + regression/parity test.
3. **Phase 2**: triển khai lexical evidence và chạy E1–E4.
4. Sau khi có báo cáo E1–E4, quyết định có cần sparse branch không; không chạy ngay một job GPU nặng nếu chưa có lý do.
5. Chạy E5 (fixed), rồi E6 (adaptive), so sánh đúng cùng dữ liệu.
6. Giữ một bản report `EXPERIMENT_REPORT.md` gồm: config, input artifacts, metric thật/proxy, ablation và quyết định tiếp tục/dừng.

**Output yêu cầu từ agent ở lần triển khai đầu:**

```text
1. Repo audit & data inventory
2. Baseline reproduction/parity report
3. Detailed code-level implementation mapping (existing file -> new module)
4. Feature schema and deterministic tests
5. E1–E4 result table or explicit blocker report
6. Recommendation for E5 and resource estimate based on measured data
```

**Không triển khai SPLADE full-corpus, không train learned router, không cập nhật `p(gold)` hoặc submission policy trong lần triển khai đầu.**

---

## 15. Những thông tin còn thiếu — agent phải tự xác minh từ repository

- [ ] Nội dung đầy đủ `PROGRESS.md`, `METHODS.md`, `CLAUDE.md` và luật F2/FINAL chính thức.
- [ ] Có hay không phiên bản baseline/leaderboard mới hơn snapshot 15/10/2026.
- [ ] JSONL schemas thực sự của `queries_enriched`, `c_blendQB8*`, `qwen_all_h`, chunk scores.
- [ ] Tên các bảng/khóa/offset cụ thể của `corpus_new.sqlite`.
- [ ] K trong RRF hiện hành; exact implementation + normalization của từng `fuse.py` stage.
- [ ] Tokenizer, phrase matching và document ID mapping cho VI/ZH.
- [ ] Artifact BGE-M3 đã lưu dense-only hay có sparse lexical weights.
- [ ] Có hay không qrels thật (query-doc/chunk), hoặc nhãn validation có thể sử dụng.
- [ ] Hạ tầng hiện tại (GPU VRAM, CPU RAM, disk, thời gian chạy thực nghiệm).
- [ ] Rule corpus EN, model license/parameter restrictions và ngưỡng ZIP/format hiện hành.
- [ ] Độ tương thích license nếu dùng UMLS/MeSH hoặc một nguồn ontology ngoài.

Nếu chưa có những bằng chứng này, chỉ được viết mã theo interface với **mock fixtures cho test**, không được tuyên bố kết quả benchmark thật.

---

## 16. Tóm tắt quyết định cuối cùng

**Hướng triển khai được khuyến nghị:** `Existing Retrieval -> Medical Lexical Evidence -> BGE-M3 Sparse (optional) -> Fixed Fusion Control -> Query-Adaptive Residual Fusion -> Existing Chunk Allocation -> Submission`.

**Thành phần quan trọng nhất:** Lexical evidence có dự báo được độ tin cậy thực tế của BM25 hay không? Nếu không, gate động chỉ có nguy cơ cộng thêm độ phức tạp và overfit.

**Nguyên tắc nghiên cứu:** không mặc định dynamic fusion thắng fixed fusion; không mặc định sparse luôn cứu được vocabulary mismatch; không đồng nhất confidence, p(gold), cosine hoặc lexical coverage với ground-truth relevance.

**Tiêu chí thành công:** cải thiện có thể tái lập trên dữ liệu đánh giá hợp lệ, tuân thủ luật nộp, và không đánh đổi hiệu quả của pipeline đã chứng minh để lấy một kiến trúc phức tạp hơn.
