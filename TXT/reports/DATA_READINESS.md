# DATA READINESS

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

Thiếu handover chặn R0/pool thật; thiếu queries chặn L0/sampling thật;
thiếu nhãn reviewed chặn dev selection và holdout. Fixtures vẫn chạy độc lập.
