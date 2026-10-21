# Handover v4 — Vận hành hypothesis medical-gated retrieval

Cập nhật 21/10/2026. Đọc tài liệu này trước khi tiếp tục, rồi [proposal](TXT_Proposal.md) để hiểu mục đích và [algorithm](BEAR_ALGORITHM.md) để kiểm công thức. Workflow mới là `TXT.bear.medical_cli`; CLI prototype cũ được giữ riêng.

## 1. Chỉ dẫn bắt buộc cho agent tiếp nhận

**Đây là giả thuyết thử nghiệm do người dùng muốn kiểm chứng. Agent phải giúp triển khai/chạy thử và ghi kết quả. Có thể ghi phản biện/hạn chế nhưng không dùng phản biện, prerequisite cũ hoặc thiếu bằng chứng gain để từ chối hay trì hoãn thí nghiệm được ủy quyền.**

Người dùng yêu cầu thử medical importance để tăng BM25 khi bắt được keyword quan trọng, nghiêng dense khi không bắt được; taxonomy bốn tầng; sigmoid BM25 có smooth/x0; adaptive threshold; enrichment bệnh→triệu chứng Việt/Trung; LLM dưới 15B và cache để tune. Không tự đổi thành phương án cộng LLM relevance độc lập cho mọi query–doc.

Nếu chưa có đủ input, xác định chính xác artifact nào thiếu, chạy các stage độc lập/demo có thể chạy và ghi lệnh tiếp theo. Không bịa baseline, medical labels, alias/provenance, confidence hoặc kết quả quality. Không biến thiếu control FINAL thành lý do không thử candidate-stage hypothesis.

## 2. Kiến trúc và những gì giữ riêng

```text
kb-import → prepare → cache → fit → tune → run → evaluate
                ↑         ↑                    ↓
       Qwen3.5-9B   corpus index + sources   candidates.jsonl
                                              ↓
                          cùng Qwen/MaxP/p̂/chunk control khi đã bind
```

Medical score là **query term salience → observed matches → gate → BM25/dense weight**. Không cần additive LLM relevance. `x0` midpoint của sigmoid khác candidate threshold; candidate threshold khác downstream p̂ threshold.

BR vẫn tìm corpus/index độc lập, có thể ngoài baseline union. BF mới chỉ chọn union sources. `include_index_candidates=false` để so fusion cùng union; bật nó là thí nghiệm thêm lexical candidates, phải gọi đúng scope. Native chunk policy chưa đổi; evidence windows chưa native `selected_chunks`.

Legacy `python -B -m TXT.bear.cli corpus-index|retrieve|evidence-fuse` và templates `configs/bear_parts/` là prototype/control riêng, vẫn fixed lexical/evidence recipe cũ. `medical_cli` không lén thay default cũ. Legacy 2.0.0 fixed200/w045 cũng không phải recipe v4.

## 3. Lệnh khởi động và demo

Chạy từ repository root, ví dụ `D:\hackathon\vimed-retrieve`. Python có sẵn đủ chạy demo offline, không cần endpoint/model download.

```powershell
python -B -m TXT.bear.medical_cli --help
python -B -m TXT.bear.medical_cli demo --output-dir TXT/runtime/medical_hypothesis_demo
```

Demo dùng corpus/KB/labels synthetic để kiểm đường chạy, calibration/tune/replay. Đây không phải quality experiment trên 593 query thật, không gọi Qwen, không tái lập 0,391. Khi đổi code/config/input, chọn output_dir mới thay vì đè run cũ.

Các stage có `--config`; mặc định inspect/dry-run. **Chỉ thêm `--execute` khi muốn chạy thật.** Inspect chỉ báo presence/config sơ bộ, không chứng nhận nội dung/schema/model/parity đã đúng.

| Stage | Template | Output chính dưới output_dir |
|---|---|---|
| kb-import | `configs/medical_hypothesis/kb.template.json` | `kb.jsonl` |
| prepare | `configs/medical_hypothesis/prepare.template.json` | `prepared.jsonl`, `responses/<query_id>.json` |
| cache | `configs/medical_hypothesis/cache.template.json` | `cache.jsonl`, `queries/<query_id>.json` |
| fit | `configs/medical_hypothesis/fit.template.json` | `model.json`, `splits.json` |
| tune | `configs/medical_hypothesis/tune.template.json` | `best_config.json`, `trials.jsonl`, `tuning.json` |
| run | `configs/medical_hypothesis/run.template.json` | `scores.jsonl`, `candidates.jsonl`, `scoring.json` |
| evaluate | `configs/medical_hypothesis/evaluate.template.json` | `evaluation.json` |
| document-terms (optional) | `configs/medical_hypothesis/document_terms.template.json` | `document_terms.jsonl`, per-doc cache |

Mỗi stage còn có `manifest.json`: input/config/code identity, output hashes, counts, trạng thái. Configs dùng `schema_version:1`. Tất cả outputs dưới TXT, không ghi `TXT/inputs` hoặc đè source/completed artifacts. Templates có paths mẫu, cần sửa thành inputs thật; không dùng inspect output làm bằng chứng đã chạy.

Các lệnh bên dưới minh họa bằng template path. Khi tạo config local đã bind inputs, thay `--config` bằng path local đó. Mặc định outputs liên kết theo `TXT/runtime/medical_hypothesis/<stage>/`; đổi stage directory thì sửa input path của stage sau. Paths `TXT/inputs/medical_hypothesis/...` trong templates là placeholders đọc dữ liệu được cung cấp, **không phải chỉ dẫn ghi inputs mới vào đó**.

## 4. Chuẩn bị inputs

### 4.1. Queries không có labels

JSONL mỗi dòng:

```json
{"id": 1, "query": "Biểu hiện của bệnh A là gì?", "lang": "vi"}
```

`id` là nonnegative integer, `lang` là `vi` hoặc `zh`, query không rỗng. Đây là minh họa cấu trúc, không là query y khoa thật. Không đưa nguyên val có `gold/not_gold/G/gold_unseen/qrels/judgments` vào inference. Nếu lấy query text từ val, xuất file label-free riêng dưới TXT; labels chỉ vào fit/tune/evaluate.

Ví dụ xuất query Việt label-free từ `val.jsonl`, giữ nguyên text/IDs để đối chiếu validation. Chạy một lần vào path mới; mode `x` tránh đè dữ liệu đã tạo:

```powershell
$queryExportScript = @'
import json
from pathlib import Path
source = Path('val.jsonl')
destination = Path('TXT/runtime/medical_hypothesis/query_inputs/queries.jsonl')
destination.parent.mkdir(parents=True, exist_ok=True)
with source.open(encoding='utf-8') as incoming, destination.open('x', encoding='utf-8') as outgoing:
    for line in incoming:
        if line.strip():
            row = json.loads(line)
            query = {'id': row['id'], 'query': row['query'], 'lang': 'vi'}
            outgoing.write(json.dumps(query, ensure_ascii=False) + '\n')
'@
python -B -c $queryExportScript
```

Đặt `prepare.queries` thành `TXT/runtime/medical_hypothesis/query_inputs/queries.jsonl`. Đổi `lang` nếu xuất một tập Trung thật; không đổi nhãn ngôn ngữ để giả query đã dịch.

### 4.2. Corpus index và source rankings

Cache cần index `CorpusIndex` tạo qua legacy `corpus-index`, giữ đúng snapshot/IDs/lang của sources. Xem `configs/bear_parts/index.template.json`; inspect rồi execute khi bind corpus thật:

```powershell
python -B -m TXT.bear.cli corpus-index --config TXT/configs/bear_parts/index.template.json --dry-run
python -B -m TXT.bear.cli corpus-index --config TXT/configs/bear_parts/index.template.json --execute
```

Index template đọc `data/corpus_new.sqlite` và tạo **`TXT/runtime/bear_parts/index_001/index.sqlite`**. Nếu dùng output đó, sửa `cache.index` và `document-terms.index` về đúng path này; templates medical đang để placeholder `TXT/inputs/medical_hypothesis/index.sqlite`, không phải output được tạo tự động. Có thể đổi index output_dir sang directory runtime mới rồi trỏ consumer vào `<output_dir>/index.sqlite`; không cần chuyển index vào TXT/inputs.

Input SQLite cần bảng `doc` có `doc_id` hoặc `id` và `body`, thêm title/lang nếu có. JSONL corpus cũng dùng được với doc_id/id, body/title/lang. Medical matching cần lang vi/zh đúng scope. Nếu corpus snapshot dùng schema khác, export/adapt rồi build index riêng; không sửa corpus nguồn để ép chạy.

Mỗi source JSONL phải phủ đúng query universe, không trùng query/doc:

```json
{"id": 1, "candidates": [{"doc_id": "123", "score": 8.2}, {"doc_id": "456", "score": 4.1}]}
```

Giữ nguồn **trước RRF**, không lấy top-K sau RRF giả làm union rộng. `sources` là map source name→path. Ranks dùng provenance và control RRF; raw scores dùng fusion khi nguồn được chọn.

Dense muốn đầy đủ score trên union có thể dùng `score_tables` map `dense_head`/`dense_chunk`→JSONL:

```json
{"id": 1, "doc_id": "123", "score": 0.71}
```

Một doc không xuất hiện trong truncated source là missing, không tự 0. `score_tables` là cách cung cấp rescore thật, không phải yêu cầu điền 0. Corpus/index thiếu doc trong source sẽ được báo lỗi, không âm thầm drop để làm đẹp kết quả.

### 4.3. Validation judgments

Định dạng explicit qrels:

```json
{"id": 1, "qrels": {"123": 1, "456": 0}, "total_gold": 1, "complete": false}
```

Hoặc pairwise JSONL `{query_id,doc_id,relevance:0|1}`. Adapter cũng nhận native `{id,gold,not_gold,G,gold_unseen}`: gold→1, supplied not_gold→0 theo semantics file, phần không có judgment vẫn unknown. **Adapter không xác nhận not_gold là clinical gold**; nếu negatives có nguồn chunk-derived/weak, ghi assumption và chạy sensitivity hoặc dùng reviewed explicit qrels. Không tự biến mọi doc ngoài gold thành negative.

Inventory hiện kiểm được: 593 query, 22.091 gold entries, 66.547 not_gold entries, 20.186 gold_unseen, không query nào `complete=true`. Đây là counts của file, không phải corpus-level relevance completeness. Mặc định tune/evaluate dùng known-positive recall; không gọi true DocF2 trên judgments thiếu. `allow_incomplete_f2`/proxy chỉ dùng khi chủ động thử và phải ghi rõ giả định.

## 5. Import KB bệnh → triệu chứng

Nguồn Trung ứng viên: [CMeIE](https://github.com/CBLUEbenchmark/CBLUE#cmeie), [OpenCMKG](https://github.com/RuiqingDing/OpenCMKG). Chúng không tự là clinical gold. Nguồn Việt chuẩn hóa đầy đủ chưa được xác minh; nhập dữ liệu có sẵn hoặc mapping nhãn Việt có ghi trạng thái duyệt.

Canonical JSONL gồm:

```json
{"disease":{"concept_id":"D001","labels":{"vi":"Bệnh A","zh":"疾病甲"},"aliases":{"vi":[],"zh":[]}},"symptom":{"concept_id":"S001","labels":{"vi":"Biểu hiện B","zh":"表现乙"},"aliases":{"vi":[],"zh":[]}},"relation":"has_symptom","source":{"name":"EXAMPLE_ONLY","record_id":"row-1"}}
```

Đây là record minh họa, không chứa sự kiện y khoa để dùng retrieval thật. Mỗi concept ID phải có labels/aliases nhất quán; source tối thiểu `name,record_id`, nên có URL/version/license/status. Giữ frequency/context/provenance nếu có. Đừng trộn complication/adverse-effect vào has_symptom mà không audit quan hệ.

`kb-import` nhận `source_path`, `format:canonical|cmeie`. Với CMeIE cần `concept_map_path` JSON list canonical concepts kèm `kind:disease|symptom`, source.name và tùy chọn `symptom_predicates` (mặc định `临床表现`). Mentions chưa map/ambiguous sẽ báo lỗi để rà mapping; adapter không tự phát minh IDs/dịch/aliases. OpenCMKG cần export về canonical schema trước; chưa có downloader/import trực tiếp mọi format của OpenCMKG.

```powershell
python -B -m TXT.bear.medical_cli kb-import --config TXT/configs/medical_hypothesis/kb.template.json
python -B -m TXT.bear.medical_cli kb-import --config TXT/configs/medical_hypothesis/kb.template.json --execute
```

## 6. LLM 9B và prompts

Default `Qwen/Qwen3.5-9B`. Override model phải có metadata `num_parameters_b` thực, lớn hơn 0 và nhỏ hơn 15. Model này phục vụ query-role, không tự thay reranker. Code client gọi endpoint tương thích `/v1/chat/completions`, không tải/chạy model server tự động.

Trên GPU host Linux/WSL đã cài runtime tương thích và **đã có checkpoint local**, ví dụ lệnh server:

```bash
vllm serve /path/to/existing/Qwen3.5-9B --served-model-name Qwen/Qwen3.5-9B --host 127.0.0.1 --port 8000
```

Đây là ví dụ vận hành endpoint, chưa là benchmark hay cam kết version vLLM/GPU cụ thể. Chọn runtime hỗ trợ checkpoint theo [model card](https://huggingface.co/Qwen/Qwen3.5-9B). Nếu GPU ở máy khác, đặt `llm.base_url`/auth theo endpoint thật. Config mặc định `http://127.0.0.1:8000/v1`, temperature 0, JSON mode, thinking tắt. Nếu server không hỗ trợ option thì chỉnh rõ llm config, không đổi model lén.

API key nếu cần đặt trong environment variable, config chỉ dùng `api_key_env`, không chép secret vào JSON/cache. Server alias phải khớp model response; dùng `expected_served_model` cho alias đã kiểm đúng <15B.

Prompts canonical:

- [medical_query_system.txt](prompts/medical_query_system.txt): định nghĩa intent/tier, source whitelist, original anchors, không sinh confidence/facts.
- [medical_query_user.txt](prompts/medical_query_user.txt): payload gồm query, language, named diseases và candidate expansions.

Model trả `intent`, `concepts`, `selected_expansion_ids`. Code kiểm exact query text, thêm spans/KB provenance và tạo `prepared.jsonl`. Không có đủ KB label cùng ngôn ngữ thì không tự dịch; expansion chỉ được chọn từ whitelist, gắn disease có thật trong query.

LLM call mặc định trả hard tiers; `probabilities:null`. Muốn `tier_mode:expected`, phải import bốn class probabilities/logits thực kèm `probability_method` và `probability_provenance`; không dùng confidence tự sinh. **Bật expected mà thiếu thông tin sẽ báo lỗi**, không âm thầm giả probabilities.

```powershell
python -B -m TXT.bear.medical_cli prepare --config TXT/configs/medical_hypothesis/prepare.template.json
python -B -m TXT.bear.medical_cli prepare --config TXT/configs/medical_hypothesis/prepare.template.json --execute
```

`prepare` cần `queries,kb,llm`. `prepared_input` tùy chọn cho saved outputs đáng tin, đã đúng schema/query IDs/KB; mode này không gọi API. Không biến fixture tự gán tiers thành tuyên bố “đã chạy LLM thật”. Stage resume theo query: `responses/<id>.json`.

## 7. Tạo feature cache đủ rộng

`cache` cần `prepared,index,sources`. Chọn một trong hai BM25 recipes:

- Prototype index: đặt `bm25_source:null`, `bm25_expanded_source:null`; code tính cùng lexical BM25 recipe trên mọi union doc cho query gốc và expanded, kể cả true zero. Có original/expanded query scale tương ứng để audit.
- External baseline BM25F: đặt `bm25_source` tên source thật, hoặc score_tables. Không tự vá expanded score bằng BM25 prototype khác recipe. Để thử enrichment phải cung cấp expanded BM25 từ đúng recipe; nếu chưa có, weight=0 hoặc fallback `missing_expanded:original` có log. External source không được chia bằng scale index không tương thích; dùng raw.

`include_index_candidates:false` giữ source union cho BF. Bật true thêm candidates từ lexical lookup gốc/expanded theo `lookup_top_k,expanded_top_k`; report đây là scope thay đổi. Default languages vi không tự kiểm chứng Chinese recall parity; nghiên cứu VI giữ ZH control.

```powershell
python -B -m TXT.bear.medical_cli cache --config TXT/configs/medical_hypothesis/cache.template.json
python -B -m TXT.bear.medical_cli cache --config TXT/configs/medical_hypothesis/cache.template.json --execute
```

Cache giữ query analysis, BM25 raw gốc/enriched, dense scores, masks, source ranks/membership, RRF control score, concept match spans và corpus hashes. Mỗi query có file riêng để resume. Không chỉ lưu fused score hoặc top-300 cuối; union nhỏ sẽ giới hạn mọi sweep sau.

## 8. Fit sigmoid và splits

`fit` cần `cache,validation,scoring`. `split` có `seed,calibration_fraction,tune_fraction,previously_observed_ids,exposure_status`; hoặc cung cấp `split_path` có query IDs tách biệt ở `calibration,tune,holdout`. Grouping giữ các normalized query giống nhau cùng split. Template ghi `previously_observed_ids:all,exposure_status:recorded` vì val hiện có đã khai thác; chỉ sửa khi có lịch sử exposure thật để chứng minh.

```powershell
python -B -m TXT.bear.medical_cli fit --config TXT/configs/medical_hypothesis/fit.template.json
python -B -m TXT.bear.medical_cli fit --config TXT/configs/medical_hypothesis/fit.template.json --execute
```

Stage hiện fit **BM25 sigmoid** từ judged candidates ở calibration split; x0/temperature và split lưu `model.json`. Dense có affine/sigmoid config riêng; fit stage không tự học dense calibrator. Nếu muốn fitted dense parameters cần chuẩn bị đúng protocol rồi khai báo, không báo chúng là learned khi chỉ đặt tay.

Scoring khởi tạo quan trọng:

```json
{
  "tier_scores": [0.05, 0.30, 0.70, 1.00],
  "tier_mode": "hard",
  "required_cap": true,
  "alpha_min": 0.10,
  "alpha_max": 0.85,
  "dense_floor": 0.10,
  "bm25": {"pretransform":"raw","x0":0.0,"temperature":1.0,"enrichment_weight":0.0,"missing_expanded":"error"},
  "dense": {"head_weight":0.5,"chunk_weight":0.5,"head":{"method":"affine","low":-1.0,"high":1.0},"chunk":{"method":"affine","low":-1.0,"high":1.0}},
  "missing_scores":"available",
  "allow_bm25_only":false,
  "selection":{"mode":"threshold","threshold":0.5,"thresholds_by_tier":{},"min_docs":0,"max_docs":300,"top_k":300}
}
```

`x0=0,T=1` và affine -1..1 ở ví dụ chỉ là init/smoke, **chưa fit**. Dense domain phải đúng nguồn thật. `query_scale` chỉ dùng khi score recipe tương thích index scale; code từ chối chia external BM25 bằng unrelated scale. `alpha_max≤1−dense_floor`; không đặt sai rồi chờ code tự clamp.

Fit cần đủ hai lớp trong judged calibration candidates. Nếu thiếu, report exact labels/scope; vẫn có thể chạy descriptive inference/demo, không dựng negatives. Native val positives/negatives là assumption của file, cần ghi weak-label sensitivity nếu có. Previously observed nên ghi thật, ví dụ `"all"` nếu toàn val đã dùng; query-disjoint retrospective split không xóa exposure cũ.

## 9. Tune offline và adaptive threshold

`tune` cần `cache,validation,model`; model là `fit/model.json`. Chọn `trials` list scoring overrides **hoặc** `grid` dotted keys, không cả hai. Ví dụ:

```json
{"grid":{"selection.threshold":[0.35,0.45,0.55],"alpha_max":[0.65,0.85]},"objective":"known_positive_recall","max_mean_docs":300,"allow_incomplete_f2":false}
```

Đoạn trên là phần cấu hình, không là full stage config. Với tier thresholds có thể dùng trial:

```json
{"selection":{"threshold":0.5,"thresholds_by_tier":{"4":0.45,"3":0.5}}}
```

Bucket lấy max hard tier của original concepts; không concepts là bucket 0. Mặc định global fallback. `min_docs` bù và `max_docs` cap có counts riêng; số docs/query thay đổi là chủ đích. Nếu phần lớn query tier4, bucket này ít phân biệt được query: vẫn chạy và ghi phân bố, không tự đổi taxonomy để tạo gain.

```powershell
python -B -m TXT.bear.medical_cli tune --config TXT/configs/medical_hypothesis/tune.template.json
python -B -m TXT.bear.medical_cli tune --config TXT/configs/medical_hypothesis/tune.template.json --execute
```

Objective hiện hỗ trợ `known_positive_recall`, `macro_doc_f2` khi nhãn đủ, hoặc `known_positive_f2_proxy` explicit. Giới hạn `max_trials` mặc định 4096 để grid có chủ đích. Tune dùng tuning queries; đổi `enrichment_weight/pretransform` sẽ re-fit BM25 trên calibration queries **chỉ**, không gọi LLM/retrieval. Lưu tất cả trials và winner, holdout chưa đọc.

`tune.split_path` phải có **cùng query assignments** như fitted model; đổi split thì tạo fit mới. Model còn bound với feature recipe/index/source mappings, nên không đem calibrator từ prototype BM25 sang external BM25F hoặc index khác. Chỉ đổi tham số fusion/threshold được replay trên cache tương thích; recipe thay đổi cần fit mới.

So global với tier thresholds ở cùng mean budget, cùng Kmin/Kmax và downstream; không gọi việc đưa thêm nhiều docs là gain scoring. Sweep points cần rộng vừa đủ, lưu toàn bộ để tái lập.

## 10. Run và evaluate

`run` dùng `cache`, `model` tùy chọn (`tune/best_config.json` hoặc fit model), `scoring` overrides tùy chọn, `mode:medical|rrf`, `query_ids` tùy chọn. Không đọc validation labels.

```powershell
python -B -m TXT.bear.medical_cli run --config TXT/configs/medical_hypothesis/run.template.json
python -B -m TXT.bear.medical_cli run --config TXT/configs/medical_hypothesis/run.template.json --execute
python -B -m TXT.bear.medical_cli evaluate --config TXT/configs/medical_hypothesis/evaluate.template.json
python -B -m TXT.bear.medical_cli evaluate --config TXT/configs/medical_hypothesis/evaluate.template.json --execute
```

`mode:rrf` dùng cached source membership/ranks và ép top-K selection. Phải bind `rrf_k,rrf_weights` đúng recipe khi cache; nếu chưa xác minh không gọi baseline parity. `mode:medical` dùng calibrated gate/fusion/selection. Sau fit, đổi recipe BM25 bằng run override bị từ chối; dùng fit/tune để calibrate recipe mới.

`run` mặc định xuất tất cả cached query IDs; `evaluate` dùng split_path để chọn subset holdout. Nếu muốn chỉ export holdout candidates, cung cấp `run.query_ids` lấy từ chính fitted splits; không lấy IDs từ một cách chia mới.

`scores.jsonl` giữ full ranking, component normalized scores, requested/effective alpha, gate details và selection diagnostics. `candidates.jsonl` chỉ selected docs, tương thích adapter:

```json
{"id": 1, "candidates": [{"doc_id": "123", "score": 0.75}]}
```

`evaluate` nhận predictions là scores.jsonl hoặc candidates.jsonl, validation, `split_path` và `split:holdout` (hoặc calibration/tune để diagnostic có tên đúng). Thiếu split file thì report retrospective all-predictions, không tự holdout. Outputs chỉ **candidate-stage diagnostics**, không official Chunk/FINAL scorer. Không suy FINAL từ coverage gain.

Thử B0/M0/M1/M2/M3 theo [study](BEAR_REPLACEMENT_STUDY.md). Cùng downstream thật cần Qwen checkpoint/prompt/preprocessing/MaxP/p̂/threshold/chunk policy/cache; doc mới thiếu score phải chạy đúng recipe, không gán 0/bỏ doc/áp p̂ threshold lên fusion score.

## 11. Optional document term candidates

Ý tưởng cũ trong chat được giữ thành experiment riêng: LLM đọc document, trích term candidates có đoạn nguyên văn để tìm những cách diễn đạt query expansion bỏ sót. CLI `document-terms` dùng index, JSON list doc IDs và llm config; prompt `prompts/medical_document_terms.txt`. Cần exact title/body spans và assertion status, lưu `document_terms.jsonl` cùng provenance và resume theo doc.

```powershell
python -B -m TXT.bear.medical_cli document-terms --config TXT/configs/medical_hypothesis/document_terms.template.json
python -B -m TXT.bear.medical_cli document-terms --config TXT/configs/medical_hypothesis/document_terms.template.json --execute
```

Config dùng `schema_version:1,index,doc_ids_path,llm,output_dir`; doc_ids_path là JSON list strings, ví dụ `["123","456"]`. `llm.document_max_chars` mặc định 24.000; document dài hơn báo lỗi, hoặc opt-in `document_overflow:prefix` để trích phần đầu có đánh dấu truncated/source windows. Không báo full-document coverage khi chỉ gửi prefix. Prompt [medical_document_terms.txt](prompts/medical_document_terms.txt) chỉ cho trích text đã thấy; assertion `affirmed|negated|uncertain|historical` là annotation của model, chưa gold.

Per-doc resume lưu `responses/<sha256(doc_id)>.json`; `document_terms.jsonl` là tập gộp cuối. Tên digest tránh dùng doc IDs có dấu phân cách làm filesystem paths.

Đây là diagnostic extraction, chưa tự index aliases, chưa tự thêm concept vào query hay retrieve vòng hai. Muốn tăng recall ngoài union phải thêm bước document indexing/expansion trước retrieval hoặc second retrieval có config riêng. Trích lại từ đã có trong body không tự thêm vocabulary cho BM25; lợi ích có thể là phrase/alias/concept normalization và weighting.

## 12. Cache invalidation và xử lý lỗi

- Không đổi inputs/config/code rồi reuse cùng output_dir. Manifest identity khác sẽ báo mismatch; chọn directory run mới, giữ kết quả cũ để so.
- Resume partial đúng cùng recipe: prepare theo query, cache theo query; completed stages được hash-verify trước reuse. Không sửa tay cache để làm hash khớp.
- Đổi tier weights/alpha/threshold: reuse cache, tạo tune/run output mới. Đổi bm25 enrichment weight/pretransform: re-fit calibration từ raw cache; terms mới thì retrieve/cache lại.
- Đổi model/prompt/KB/query: prepare lại phần liên quan, cache match/retrieval tương ứng. Đổi corpus/index/alias matcher: cache lại; top-K cũ không đủ đánh giá docs ngoài union.
- Missing input/schema/hash/model endpoint: ghi error thật và missing role. Không dùng model lớn hơn 15B hoặc fake output làm fallback. Nếu endpoint chưa chạy, trusted saved model outputs hoặc demo là đường độc lập có thể thử.
- Nếu missing dense toàn bộ, default sẽ báo lỗi; `allow_bm25_only:true` là ablation rõ, không còn đầy đủ hypothesis BM25↔dense. Missing một source theo available-policy có log effective weights.

## 13. Báo cáo và trạng thái cuối mỗi lần làm

Ghi config/inputs/splits/hashes, model endpoint có thật được gọi không, KB nguồn/coverage, actual confidence availability, counts/missingness/budgets, metric đúng scope, runtimes và limitations. Report test/demo riêng real validation. Chỉ đánh dấu quality experiment hoàn tất khi đã chạy thực; không dùng task checklist làm bằng chứng gain.

0,391 và counts sơ đồ chưa được tự tái lập bởi workflow này. L1/L4/N0/N1 giữ lịch sử; không yêu cầu làm lại chúng trước hypothesis v4. BR/BF độc lập; native chunk selector là công việc riêng.

Code liên quan: `medical_cli.py`, `medical_runner.py`, `medical_cache.py`, `medical_query.py`, `medical_kb.py`, `medical_documents.py`, `medical_scoring.py`, `medical_validation.py` dưới [bear/](bear/). Xem [results](reports/RESULTS.md), [runbook](reports/RUNBOOK.md), [log](improvement_log.md) để biết những lệnh/tests thực sự đã chạy. Phiên bản trước ở [archive](archive/TXT_handover_v3_5_20261020.md).
