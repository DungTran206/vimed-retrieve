# Handover v5 — BM25/dense fusion với SapBERT-XLMR

Cập nhật 22/10/2026. Đây là tài liệu tiếp nhận chính. [Proposal](TXT_Proposal.md) giải thích ý tưởng; [algorithm](BEAR_ALGORITHM.md) chốt công thức; [study](BEAR_REPLACEMENT_STUDY.md) quy định đối chứng; [PLAN](PLAN.md) ghi thứ tự công việc.

## 1. Quyết định hiện hành và trạng thái

Người dùng muốn giữ ý tưởng fusion BM25/dense, dùng SapBERT-XLMR để giảm bỏ sót cách gọi khác nhau, enrichment có dữ liệu ngoài và LLM chọn shortlist tùy chọn. Biến thể đầu giữ dense tổng quát rồi trộn SapBERT vào nhánh dense; λ=1 là ablation thay thế.

Đây là hypothesis cần triển khai/thử nghiệm. Agent tiếp nhận phải chạy phần đã được ủy quyền khi có inputs, ghi cả kết quả thuận/nghịch; hạn chế là cơ sở thiết kế đối chứng, không phải lý do từ chối thử. Thiếu input thì nêu đúng artifact thiếu và tiếp tục phần độc lập có thể chạy. Không bịa quality score, clinical facts, aliases, confidence hoặc provenance.

**Trạng thái cập nhật:** v5 đã triển khai với implementation version `medical_gate_sapbert_v2`. Sau khi dọn prose cũ, full TXT suite **173/173 tests qua** trong 43,921 giây; **10/10 legacy tests qua**. Mười templates preflight hợp schema và 72 tuning configs hợp lệ trong max_trials=96. Có synthetic semantic cache/replay và selector dùng mock endpoint. Chi tiết tại [report v5](reports/SAPBERT_V5_20261022.md), [preflight](reports/medical_v5_preflight_20261022.json), [results](reports/RESULTS.md) và [log](improvement_log.md). Đây là kiểm chứng kỹ thuật: chưa gọi endpoint/encoder thật, chưa tải checkpoint/dataset, chưa đo gain trên 593 query thật.

Hiện branch `Tung`. Người dùng sẽ tự tạo branch; khuyến nghị `exp/sapbert-xlmr` cho thử nghiệm. Git commit giữ mã nguồn; log/manifest ghi thực nghiệm; branch không sao lưu runtime bị ignore. Không tự tạo branch khi chưa được yêu cầu.

## 2. Sơ đồ và vai trò

```text
KB ngoài → kb-import → prepare(query LLM: concepts/tiers/enrichment)
corpus index + pre-fusion sources + prepared → cache
cache union hoặc explicit doc_ids → document-terms(document LLM)
cache + document_terms + encoder → sapbert-cache
                 ↓
         fit → tune → run → [select: LLM shortlist] → evaluate
```

BM25 khai thác term cụ thể và lexical overlap; generic dense bổ sung ý nghĩa câu/cách nói đời thường; SapBERT bổ sung entity/concept similarity đa ngôn ngữ. Vai trò bổ trợ, không tuyệt đối hoặc bảo đảm tăng điểm.

BF chỉ xếp/chọn union đã cache; SapBERT/selector không tìm được doc ngoài union. BR tìm corpus độc lập là experiment riêng. `include_index_candidates=false` giữ union khi so fusion; bật true thêm lexical candidates và phải báo scope pool thay đổi.

Legacy `TXT.bear.cli`, fixed lexical/evidence prototype và downstream control được giữ để kiểm chứng/code dependencies. V5 không tự thay native chunk selector, Qwen reranker, MaxP/p̂ hoặc exporter cũ. Evidence spans không phải native selected_chunks.

## 3. Lệnh, templates và artifacts

Chạy từ repository root:

```powershell
python -B -m TXT.bear.medical_cli --help
python -B -m TXT.bear.medical_cli demo --output-dir TXT/runtime/medical_v5_demo
```

Các stage nhận `--config`, mặc định inspect; thêm `--execute` để chạy thật. Inspect chỉ kiểm sơ bộ paths/schema, không chứng nhận checkpoint, endpoint, labels hoặc baseline parity. Demo offline/synthetic không chứng minh quality và không được gọi là đã dùng model thật.

Templates ở `TXT/configs/medical_hypothesis/`; paths mẫu chưa tự có dữ liệu. Bind config riêng dưới TXT, outputs mới dưới `TXT/runtime/medical_v5/` hoặc directory run riêng. Không ghi đè input hoặc completed artifacts; không ghi vào `TXT/inputs`.

| Stage | Config bắt buộc/đầu vào chính | Output chính |
|---|---|---|
| kb-import | source_path; canonical hoặc CMeIE có mapping | kb.jsonl |
| prepare | queries, kb, llm; prepared_input tùy chọn | prepared.jsonl; responses/<qid>.json |
| cache | prepared, index, sources; score_tables tùy chọn | cache.jsonl; queries/<qid>.json |
| document-terms | index, llm; **đúng một** trong cache/doc_ids_path | document_terms.jsonl; per-doc cache |
| sapbert-cache | cache, index, document_terms, encoder; embeddings_input tùy chọn | cache.jsonl; queries/; embeddings/; semantic_recipe.json |
| fit | semantic cache, validation, scoring; split/split_path | model.json; splits.json |
| tune | semantic cache, validation, model; grid hoặc trials | best_config.json; trials.jsonl; tuning.json |
| run | semantic cache, model/scoring, mode=medical/rrf | scores.jsonl; candidates.jsonl; scoring.json |
| select, tùy chọn | predictions=run/scores.jsonl, index, llm, selection | scores.jsonl; candidates.jsonl; responses/<qid>.json |
| evaluate | predictions, validation; split_path/split/query_ids | evaluation.json |

Mỗi stage có manifest.json với input/config/code identity, hashes và trạng thái. Raw cache và semantic cache đều tên cache.jsonl nhưng ở **output_dir khác nhau**. Fit/tune/run phải trỏ semantic cache khi dùng SapBERT; λ=0 có thể chạy đối chứng trên cùng semantic cache.

Inspect trước bằng lệnh không có --execute. Mẫu thứ tự chạy thật theo templates sau khi đã bind paths:

```powershell
python -B -m TXT.bear.medical_cli kb-import --config TXT/configs/medical_hypothesis/kb.template.json --execute
python -B -m TXT.bear.medical_cli prepare --config TXT/configs/medical_hypothesis/prepare.template.json --execute
python -B -m TXT.bear.medical_cli cache --config TXT/configs/medical_hypothesis/cache.template.json --execute
python -B -m TXT.bear.medical_cli document-terms --config TXT/configs/medical_hypothesis/document_terms.template.json --execute
python -B -m TXT.bear.medical_cli sapbert-cache --config TXT/configs/medical_hypothesis/sapbert_cache.template.json --execute
python -B -m TXT.bear.medical_cli fit --config TXT/configs/medical_hypothesis/fit.template.json --execute
python -B -m TXT.bear.medical_cli tune --config TXT/configs/medical_hypothesis/tune.template.json --execute
python -B -m TXT.bear.medical_cli run --config TXT/configs/medical_hypothesis/run.template.json --execute
```

Select/evaluate chạy sau run, theo predictions đã bind:

```powershell
python -B -m TXT.bear.medical_cli select --config TXT/configs/medical_hypothesis/select.template.json --execute
python -B -m TXT.bear.medical_cli evaluate --config TXT/configs/medical_hypothesis/evaluate.template.json --execute
```

Không nhầm candidates.jsonl với scores.jsonl đầy đủ ranking mà selector yêu cầu.

## 4. Input schemas và labels

Queries label-free:

```json
{"id": 1, "query": "Biểu hiện của bệnh A là gì?", "lang": "vi"}
```

ID nonnegative integer duy nhất, text không rỗng; vi/zh/en được hỗ trợ, ngôn ngữ khác cần adapter. Ví dụ này chỉ minh họa schema. Không truyền gold/not_gold/G/gold_unseen/qrels/judgments vào prepare/cache/selector. Nếu lấy text từ val, xuất JSONL label-free vào path runtime mới và giữ nguyên IDs/query/lang; labels chỉ vào fit/tune/evaluate.

Corpus index dùng `CorpusIndex` từ CLI cũ:

```powershell
python -B -m TXT.bear.cli corpus-index --config TXT/configs/bear_parts/index.template.json --dry-run
python -B -m TXT.bear.cli corpus-index --config TXT/configs/bear_parts/index.template.json --execute
```

SQLite source có doc với doc_id hoặc id và body; title/lang nếu có. JSONL corpus cũng được adapter hỗ trợ. Bind cache.index, document-terms.index, sapbert-cache.index và select.index về **cùng index.sqlite/corpus snapshot**. Template index cũ có output riêng; không giả định nó tạo index ở paths medical mẫu. Corpus schema khác cần export/adapt riêng, không sửa nguồn để ép chạy.

Source ranking JSONL trước RRF:

```json
{"id":1,"candidates":[{"doc_id":"123","score":8.2},{"doc_id":"456","score":4.1}]}
```

Mỗi source phủ query universe, IDs không trùng, doc IDs tồn tại trong index. Raw scores dùng fusion; source rank/membership dùng provenance và RRF control. Top-K source absence là missing, không phải raw 0. score_tables cung cấp **rescore thật trên union** nếu có:

```json
{"id":1,"doc_id":"123","score":0.71}
```

Validation có thể là qrels `{id,qrels:{doc_id:0|1},total_gold,complete}`, pairwise `{query_id,doc_id,relevance}` hoặc native `{id,gold,not_gold,G,gold_unseen}`. Native gold→1, supplied not_gold→0 theo file; không biến phần còn lại thành âm.

Inventory đã ghi cho val: 593 query, 22.091 gold entries, 66.547 not_gold entries, 20.186 gold_unseen; không query nào complete=true. Counts không chứng minh relevance completeness. Default known_positive_recall; unknown không negative. Nếu not_gold là weak/chunk-derived thì ghi assumption/sensitivity. F2 proxy phải opt-in và ghi rõ tên, không gọi official full DocF2.

## 5. KB ngoài và enrichment

Nguồn ứng viên Trung: [CMeIE](https://github.com/CBLUEbenchmark/CBLUE#cmeie), [OpenCMKG](https://github.com/RuiqingDing/OpenCMKG). Có nguồn không tự đồng nghĩa clinical gold. Nguồn Việt/English tự có cần mapping/canonical schema và trạng thái duyệt. Không coi model multilingual là khả năng import mọi ngôn ngữ/format.

Canonical record minh họa:

```json
{"disease":{"concept_id":"D001","labels":{"vi":"Bệnh A","zh":"疾病甲"},"aliases":{"vi":[],"zh":[]}},"symptom":{"concept_id":"S001","labels":{"vi":"Biểu hiện B","zh":"表现乙"},"aliases":{"vi":[],"zh":[]}},"relation":"has_symptom","source":{"name":"EXAMPLE_ONLY","record_id":"row-1"}}
```

Không dùng record minh họa làm medical fact. Giữ concept IDs/labels/aliases nhất quán và source name/record_id; nên thêm URL/version/license/mapping status. Alias đồng nghĩa khác disease→symptom liên quan.

`kb-import` nhận format canonical hoặc cmeie. CMeIE cần concept_map_path có kind disease/symptom và source metadata; unmapped/ambiguous mention phải được xử lý thật. OpenCMKG cần export canonical, chưa tự download/convert mọi schema.

Query LLM chỉ chọn selected_expansion_ids thuộc whitelist theo bệnh neo trong query. Intent symptoms/general mới xem symptom expansion; dose/treatment/contraindication/interaction có chặn phù hợp. Label expansion theo language query, không tự dịch khi thiếu. Initial llm.max_kb_candidates=256; llm.max_expansion_terms=8, kiểm cả generated/imported prepared records. Vượt cap thì rà/bind budget rõ, không silent invent/truncate KB.

KB bổ sung vocabulary/relations cho enrichment; document ngoài muốn xuất hiện trong retrieval phải đi qua corpus/index, không chỉ import KB.

## 6. Query/document LLM và endpoint

Initial `Qwen/Qwen3.5-9B`, metadata num_parameters_b=9; override phải là model thật 0<B<15. Client dùng endpoint tương thích /v1/chat/completions; không tự tải checkpoint hoặc chạy server. Bind base_url/served-model alias theo endpoint thật; model alias không tự chứng minh đúng checkpoint.

Config chỉ giữ api_key_env khi cần, không chép secrets vào files/cache. Query/doc/selector prompts là source-controlled files dưới [prompts](prompts/). Hard tiers mặc định; expected mode cần backend_label_logits/backend_label_probabilities và probability_provenance thật.

Prepare resume responses/<qid>.json; prepared_input nhập outputs đã đúng schema/query/KB có provenance để không gọi API lại. Synthetic tiers không được gọi là LLM inference thật.

Document-terms có thể lấy unique IDs từ `cache` union hoặc `doc_ids_path` JSON list strings, đúng một trong hai. Model trích literal term, field/anchor, kind và assertion affirmed/negated/uncertain/historical; kiểm spans exact trước khi cache. Initial document_max_chars=24.000, document_overflow=error; prefix là opt-in có windows/truncated, không được báo full-document coverage khi chỉ đọc prefix.

Term extraction không tự sửa lexical gate/index; v5 semantic stage tiêu thụ terms để tính SapBERT. LLM không được thêm synonym/fact không thấy trong text.

## 7. SapBERT cache và encoder identity

Model mục tiêu: [cambridgeltl/SapBERT-UMLS-2020AB-all-lang-from-XLMR](https://huggingface.co/cambridgeltl/SapBERT-UMLS-2020AB-all-lang-from-XLMR); nền tảng entity linking đa ngôn ngữ trong [paper](https://aclanthology.org/2021.acl-short.72/). Chưa có benchmark chứng minh phù hợp corpus này.

Config encoder nhận model, revision hoặc local_path, pooling=cls, l2_normalize=true, max_length=64, batch_size=64, local_files_only=true, overflow=error và device đã chọn. revision phải immutable commit SHA; revision=null chỉ hợp lệ khi có local_path snapshot rõ. local_path trong template là placeholder phải bind checkpoint thật. Không tự tải model khi thiếu.

Backend Transformers/PyTorch chỉ cần khi encode thật; import package/demo/feature replay không được kéo model về. Embeddings_input là đường import vectors có metadata/provenance, không biến fixture vectors thành model output thật. Giữ dimension/token_count/truncated phù hợp recipe. Nếu encoder.local_path được đặt, snapshot đó vẫn phải hiện diện và được hash kể cả khi import embeddings. Muốn import embeddings không có checkpoint local cần local_path=null và revision SHA pin thật, khớp provenance vectors.

Semantic cache kiểm corpus hashes/literal spans rồi encode concept/term duy nhất; giữ full cosine matrix, embedding identities và semantic_recipe. Khi terms vượt max_length mặc định error; truncate là opt-in có log. Thay checkpoint/tokenization/max_length/pooling/truncation sẽ invalid embeddings.

## 8. Công thức và tham số

```text
G_lexical = Σ_i a_i² m_i / Σ_i a_i, có optional required_cap
α = α_min + (α_max − α_min) G_lexical
B = (1 − w) B_original + w B_enriched
z_B = sigmoid((u_B − x0) / T)
D_generic = 0,50 z_H + 0,50 z_C
S_sap = Σ_i a_i max_j normalize(cosine_i_j) / Σ_i a_i  # i loại kind=intent
D_new = (1 − λ) D_generic + λ S_sap
F = α z_B + (1 − α) D_new
```

Mẫu số gate bằng 0 thì G=0. Với SapBERT, không có eligible original concept, tổng importance=0 hoặc không có actual term pair thì S_sap là missing. Khi đã có pair hợp lệ, concept riêng thiếu comparison đóng góp 0 trong trung bình. Available-policy renormalize các dense branches còn bật/có thật; λ=1 tắt generic nên không tự có generic fallback. Missing/error và BM25-only policy phải giữ rõ.

SapBERT không đi vào lexical m_i/G. α là tỷ trọng BM25: tăng α không chắc tăng F, bởi dF/dα=z_B−D_new. Gate cao nhưng BM25 thấp vẫn có thể làm điểm giảm. Source-backed alias/exact gate và semantic similarity evidence giữ riêng ở biến thể đầu.

**Mọi giá trị ở cột initial là ước lượng khởi tạo**, trừ recipe được ghi là cố định. Tune ranges là menu đề xuất, cần chọn grid nhỏ/có max_trials; không khẳng định đã sweep toàn tích Descartes.

| Tham số | Initial | Menu/range đề xuất | Tính lại khi đổi |
|---|---|---|---|
| Tier generic/supporting/discriminative/decisive | 0,05/0,30/0,70/1,00 | Đổi có thứ tự, ví dụ supporting 0,2–0,4; discriminative 0,6–0,8 | Gate/Sap aggregation/replay; không LLM |
| tier_mode | hard | hard; expected chỉ có probabilities thật | Replay nếu cache đủ probabilities |
| required_cap | true | false/true | Gate/replay |
| alpha_min | 0,10 | 0,05/0,10/0,20 | Replay |
| alpha_max | 0,85 | 0,65/0,75/0,85 | Replay |
| dense_floor | 0,10 | 0,10/0,15; alpha_max≤1−floor | Replay |
| BM25 enrichment_weight w | 0,25 | 0/0,25/0,50 | Refit BM25 calibration + replay từ raw scores |
| BM25 pretransform | query_scale cho prototype; raw cho external | raw/query_scale đúng recipe | Refit calibration + replay |
| BM25 x0/T | Template 0,30/0,15 trước fit | Fit calibration; T>0, không coi init là learned | Refit từ raw cache |
| Generic head/chunk weights | 0,50/0,50 | 0,25/0,75; 0,50/0,50; 0,75/0,25 | Replay |
| Generic affine low/high | −1/1 cho cosine | Theo domain source thật; fit riêng nếu muốn | Replay từ raw |
| Sap weight λ | 0,30 | 0/0,15/0,30/0,50/1 | Replay |
| Sap affine low/high | 0,20/0,90 | low 0/0,20/0,40; high 0,80/0,90/1, low<high | Full-matrix replay; không encode |
| Candidate threshold | 0,50 | 0,40/0,50/0,60; mở rộng theo budget | Replay |
| min_docs/max_docs/top_k | 0/400/300 ở template | So min=0/40; max/budget 100–400 theo control | Replay; chưa là quota baseline |
| missing_scores/allow_bm25_only | available/false | available/error; BM25-only opt-in ablation | Replay; ghi effective weights |
| include_index_candidates | false | false/true là scope experiment khác | Pool/retrieval/features cho docs mới |
| RRF k/source weights | 60; mỗi source 1 trong template | Bind đúng recipe control, không tune rồi gọi parity | RRF replay từ ranks; không model |
| Query/document/selector LLM | Qwen3.5-9B; temperature=0 | Checkpoint khác thật dưới 15B là ablation | LLM stage và downstream cache |
| LLM max_tokens/timeout/thinking/JSON | 2.048/120s/false/true | Theo endpoint/context; không bảo đảm đủ context | LLM stage; prompt/response identity |
| Query max_expansion_terms | 8 | 0/4/8/12 | Prepare/expanded retrieval/cache đổi |
| Query max_kb_candidates | 256 | 128/256 theo token budget | Prepare; không tự thay whitelist sau inference |
| lookup_top_k/expanded_top_k | 1.000/1.000 khi bật index candidates | 500/1.000/2.000 theo headroom | Retrieval/cache và features cho doc mới |
| Encoder CLS/L2 | cls/true | Cố định recipe v5 | Embeddings/matrix nếu đổi recipe tương lai |
| Encoder max_length/batch_size | 64/64 | length 64/128 nếu cần; batch theo RAM/VRAM | Length đổi encode; batch kiểm identity/cache theo config |
| Document LLM chars/overflow | 24.000/error | Prefix opt-in hoặc tăng theo runtime | Document LLM terms + downstream semantic |
| Selector max_candidates | 40 | 20/40/80 theo context | Selector LLM cache |
| Selector document_max_chars | 2.000 | 1.000/2.000/4.000 | Selector LLM cache |
| Selector min_docs/max_docs | 0/40 | min 0/5; max theo shortlist/budget | Selector stage, giữ chosen IDs/response |
| Split seed/calibration/tune | 391/0,40/0,40 | Khóa trước thử; phần còn lại holdout | Fit/tune/eval, không model feature inference |
| Fit l2/max_iter/tolerance | 0,0001/200/1e−8 | Chỉnh khi convergence/data cần; giữ protocol | Refit BM25 |
| Tune objective/max_mean_docs | known_positive_recall/300 | Budget theo control; F2 proxy phải opt-in | Tune/eval numerical |
| max_trials | Theo template đã khóa | Ít nhất số tổ hợp grid thực; bắt đầu menu nhỏ | Giới hạn numerical sweep, không LLM |

Sap transform config `sapbert:{weight:0.30,method:"affine",low:0.20,high:0.90}`. Fit stage hiện học **BM25 sigmoid**; Sap affine được ước lượng/tune retrieval objective, chưa probability calibrator học từ labels. F cũng chưa là final relevance probability.

## 9. Chi phí và cache: bước nào chạy lại?

| Công việc | Nút thắt | Cache/tái dùng | Invalidation chính |
|---|---|---|---|
| KB import | I/O/mapping | Canonical KB + source hash | Source/schema/mapping |
| Query LLM | Endpoint tokens/calls theo query | Một response/query | Query/model/prompt/KB/whitelist/caps |
| Document LLM | Tokens theo unique document, có thể lớn | Một extraction/doc; dùng cho nhiều query | Corpus text/model/prompt/windows |
| Retrieval/BM25 raw | Index/search/rescore | Union/source/raw scores/ranks/masks | Query/expansion/index/recipe/depth |
| Sap embeddings | Encoder forward/RAM/VRAM | Unique concept/term vectors | Checkpoint/tokenizer/text/max_length/overflow |
| Concept–term cosine matrix | Số cặp và disk | Full raw matrix theo union | Vectors/concepts/document terms/pool |
| Fit/tune/fusion/threshold | CPU đọc cache và numerical replay | Trials/model/rankings | Tham số/split/labels; không LLM/encoder |
| LLM select | Tokens theo shortlist và snippets | Per-query selection/response | Candidate set/corpus/prompt/model/budget |
| Evaluation | Labeled metrics/I/O | Evaluation report | Predictions/labels/split/scorer |

Cache tránh chạy lại phần đắt trong sweep; không biến lần chạy đầu thành miễn phí. Document LLM trên union lớn có thể là chi phí chính; bắt đầu subset có phạm vi rõ, đo unique docs/token counts/runtime rồi mở rộng. Chưa có model/hardware benchmark thật nên không quy đổi thành giờ GPU đáng tin.

Thay λ/alpha/threshold có thể đổi shortlist. Tune xong mới chạy selector cho config đã khóa; không gọi selector mỗi trial. Có thể tái dùng chosen IDs chỉ khi candidate/prompt/corpus identity vẫn đúng; không tự tái dùng semantic decision cho ngữ cảnh khác.

## 10. Fit, tune, run và evaluate

Fit cần đủ hai lớp judged candidates trên calibration split. Chỉ labels do file cung cấp; thiếu negatives thì báo scope và chạy descriptive inference/demo được, không dựng negatives. Chia normalized query groups vào calibration/tune/holdout, không overlap. Template ghi previously_observed_ids=all, exposure_status=recorded vì val đã khai thác; chia lại không làm pristine.

Tune nhận trials hoặc grid dotted keys, không cả hai; lưu toàn bộ search/trials/budget/objective. Với w/pretransform đổi, runner refit BM25 trên calibration split từ cached raw scores. Đổi λ/Sap affine/tier/alpha/threshold không cần LLM/encoder/retrieval lại nếu cache đủ.

Run nhận best_config.json như model và semantic cache cùng recipe; mode=rrf dùng source ranks/membership đúng control recipe. Không gọi baseline parity nếu k/weights/ties/source snapshots chưa xác minh. scores.jsonl giữ full ranking/components/gate/effective weights/selection; candidates.jsonl chỉ selected docs:

```json
{"id":1,"candidates":[{"doc_id":"123","score":0.75}]}
```

Evaluate từ run hoặc select outputs; chỉ định split_path/split và query_ids thuộc split đó. Không vô tình đánh giá toàn universe rồi gọi holdout. Default metric là known-positive recall do incomplete judgments. Downstream Doc/Chunk/FINAL cần scorer đúng contract, không tự suy từ candidate score.

## 11. Selector tùy chọn

`select` yêu cầu full run/scores.jsonl, index cùng snapshot, llm và selection config. Scored rows phải có index_sha256 khớp select.index; predictions cũ thiếu identity cần chạy lại run từ cache, đây là bước rẻ và không gọi model. Lấy các selected IDs theo fusion order rồi giới hạn max_candidates. LLM response chỉ `{"selected_doc_ids":["..."]}`, không tự thêm IDs/rerank/rewrite scores.

Code kiểm duplicate/out-of-shortlist IDs, giữ score order, áp deterministic min-fill rồi cap; empty shortlist bỏ endpoint call. Lưu responses/<qid>.json, scores/candidates và metadata snippet truncation/cache identity. Invalid response phải báo lỗi, không âm thầm dùng selector khác.

Ban đầu tối đa 40×2.000 ký tự/query có thể là prompt đáng kể; max chars không phải token budget bảo đảm. Đo token/context theo endpoint thật và giảm shortlist/chars khi cần. Missing text hoặc vượt context không được coi là đã đánh giá đủ docs.

## 12. Giới hạn cần giữ khi bàn giao

- Source union là trần của BF; re-score không tăng pool recall.
- No-match/missing/unknown-label khác nhau; không gán 0/negative để ép fit.
- Cosine tương tự không tự là synonym/clinical fact; SapBERT không thay toàn bộ nghĩa câu trong biến thể đầu.
- Qwen query/document/selector khác downstream reranker; chưa tự thay checkpoint/prompt/recipe control.
- Candidate threshold khác sigmoid x0 và downstream p̂ threshold.
- Native chunk policy/exporter chưa đổi; evidence refs chưa submission chunks.
- Completed artifacts immutable; stage/config/input/code đổi chọn output_dir mới.
- Branch không giữ runtime bị ignore; hash không khôi phục source text, cần commit và backup artifacts.
- Prose cũ dọn theo [cleanup](reports/CLEANUP_20261022.md); giữ [baseline spec](PIPELINE_0391.md), [evaluator contract](reports/EVALUATOR_CONTRACT.md), [results](reports/RESULTS.md) và [log](improvement_log.md).

Agent tiếp nhận bắt đầu bằng kiểm config/input hiện có, chạy stage nhỏ có đủ dữ liệu và cập nhật kết quả thực. Không lấy tài liệu kế hoạch hoặc synthetic demo làm bằng chứng đã chạy experiment thật.
