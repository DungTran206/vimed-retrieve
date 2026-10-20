# DATA READINESS

> **Lịch sử checkout 19/10, không phải readiness vòng mới.** Kế hoạch hiện hành là [PLAN v3.3](../PLAN.md), baseline [Pipeline 0,391](BASELINE_0391_20261020.md). Kiến trúc đã được chuyển từ ảnh sang [Markdown](../PIPELINE_0391.md) và [spec tham chiếu không thực thi](../specs/pipeline_0391.json); chưa liên kết recipe/cache/control runtime. Người dùng đã báo N0/N1 thực chạy và L1/L4 trên 0.4076; thiếu roles bên dưới chỉ mô tả snapshot cũ, không bắt chạy lại hoặc gán nhãn tay. Nhãn BTC được đánh giá đúng semantics; xem [evaluator contract](EVALUATOR_CONTRACT.md). Không sửa manifest cũ.

## Inputs tối thiểu của vòng hiện hành

A0 cần control prediction/corpus/query, candidates và scores, native chunk refs/budget/exporter cùng scorer/judgments đúng baseline. Threshold/MaxP/p̂ là phần policy baseline cần nối đúng, không là nghiên cứu chính thay cho BEAR. Không bắt đủ mọi roles w045 nếu cache phù hợp đã có. 300VI+40ZH là candidate caps trong ảnh; mean160 chưa phải k thực từng query.

Hướng A0–A4 hiện hành xây adapter, structured evidence, doc selector và chunk selector theo [BEAR_ALGORITHM](../BEAR_ALGORITHM.md). D1/C1 có input riêng; không buộc một nhánh chờ nhánh kia hoặc nhận đủ roles w045. Threshold study v3.2 là hỗ trợ, không là prerequisite hay kế hoạch chính. Phải có selected_docs/selected_chunks thực khi nghiệm thu, không chỉ audit.

Local scripts calibration MAXP beta8/10 chưa được liên kết với 0.391; không tự refit hoặc lấy chúng thay recipe mới. Runner reviewed/fixed-k và exporter 200 cũ chưa triển khai nghiên cứu này. Inputs label coverage cần đủ cho hits control hoặc uncertainty variable-k, kể cả docs giữ nguyên.

## Kiểm tra A0 mới —20/10/2026

[JSON inventory](bear_doc_chunk_preflight_20261020.json) có6roles:thiếu5roles queries/control0,391/candidates+scores/corpus/chunkpolicy+refs; btc_validation hiện diện. [Readiness/CPU](EXPERIMENT_READINESS_20261020.md) tách file presence khỏi schema/linkage/labels và implementation A1–A3. Không đồng nhất với22roles w045 lịch sử dưới đây.

## Snapshot lịch sử

Trạng thái: `blocked_input`; thiếu 22/22 roles.

| Role | Path | Status |
|---|---|---|
| corpus | data/corpus_new.sqlite | missing |
| vi_base | data/rp/c_blendQB8.jsonl | missing |
| vi_alt | data/rp/c_blendQB8w05.jsonl | missing |
| zh_bge_vi | data/dense_zhC3_vi_rank.jsonl | missing |
| zh_bge_zh | data/dense_zhC3_zhq_rank.jsonl | missing |
| zh_bge_patch | data/dense_zhC3_zhq109_rank.jsonl | missing |
| zh_q8_vi | data/dense_zhQ8_vi_rank.jsonl | missing |
| zh_q8_zh | data/dense_zhQ8_zhq_rank.jsonl | missing |
| zh_q8_patch | data/dense_zhQ8_zhq109_rank.jsonl | missing |
| membership | data/vibiomir_new/links_corpus_vi_en_zh.parquet | missing |
| chunk_scores | data/chunk_scores_mix.jsonl | missing |
| qwen_doc_scores | data/qwen_all_h.jsonl | missing |
| chunk_dense | data/dense_chunk_full_rank.jsonl | missing |
| beta | data/val/beta.json | missing |
| queries | data/queries.jsonl | missing |
| enriched_queries | data/queries_enriched.jsonl | missing |
| lexical_sources | None | missing |
| dense_sources | None | missing |
| qrels | None | missing |
| passages | None | missing |
| tokenizer | None | missing |
| scorer_spec | None | missing |

Archives chỉ là ARTIFACT_OBSERVED, chưa liên kết với w045.
Macro checks và IDs đã quan sát nằm trong input manifest; không dùng feedback làm qrels.

Các dòng thiếu input và quy tắc “không dùng feedback làm qrels” phía trên thuộc workflow cũ: không dựng doc labels từ aggregate score. Chúng không cấm dùng doc judgments BTC thực có để đánh giá. Không ép file val thành reviewed-manual qrels; dùng scorer baseline mới hoặc adapter phù hợp theo PLAN v3.3.
