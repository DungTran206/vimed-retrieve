# PLAN v3.5 — Hai phần BEAR độc lập

Cập nhật 20/10/2026. **Retriever tìm corpus/index; Fusion chọn source union để thay RRF.** Không thừa: một phần thay khả năng tìm tài liệu, phần kia thay cách chọn ứng viên đã tìm. Prototype corpus_parts_v1 dùng shared index/scorer, có đường chạy kỹ thuật; quality chưa đánh giá.

## 1. Mục tiêu

So B0/BR/BF cùng corpus/query/lang/top-k/downstream. Không giới hạn Retriever trong pool baseline, không buộc F1-first/S1-deferred. [Algorithm](BEAR_ALGORITHM.md), [study](BEAR_REPLACEMENT_STUDY.md), [handover](TXT_handover.md) là hiện hành.

Dài hạn vẫn doc/chunk retrieval. Candidates/evidence refs chưa hoàn tất selected_chunks/submission exporter.

## 2. Control và lịch sử

0,391 là score người dùng báo, chưa đủ metric/run/config linkage. Sơ đồ khoảng 300 VI + 40 ZH trước rerank, threshold cho mean khoảng 160 docs/query; chưa là runtime counts/quotas cuối.

L1/L4 trên 0,4076 giữ best ΔDocF2 +0.0003/+0.0004, CI95 chạm 0/âm theo báo cáo, không chạy coverage lại bằng tên khác. N0/N1 w045 đã có kết quả được báo, không làm lại prerequisite. Không áp policy baseline khác cho 0,391.

## 3. Kiến trúc và output

Shared corpus_index.py/structured_evidence.py phục vụ retrieval.py/evidence_fusion.py. Retriever lookup corpus độc lập, Fusion chấm dedup union không thêm docs. Parts_runner.py nối CLI/config/manifest.

CLI corpus-index/retrieve/evidence-fuse có --config và --dry-run/--execute. [Templates](configs/bear_parts/) riêng. Hai inference paths xuất candidates.jsonl/evidence.jsonl/manifest.json; schema id,candidates[{doc_id,score}] tương thích reranker. Chunk refs/bear_window là diagnostic.

### 3.3. Giới hạn ghi

Thay đổi/output mới dưới TXT; legacy/corpus/nhãn nguồn/completed artifacts chỉ đọc. Không ghi TXT/inputs hoặc đè inputs. Index riêng giữ identity snapshot. Không tải model trong prototype.

## 4. Cơ chế và giới hạn

Shared stdlib lexical index/BM25, mặc định VI có cấu hình. Scorer dùng protected phrases neo query, explicit subject/predicate/object, same-sentence/order/polarity rules. Không relations thì lexical-only; chưa general NLP/biomedical semantics.

Fusion BEAR-only không dùng RRF làm score chính. Source rankings xác định union/provenance. Shared engine tránh lặp code, hai search spaces khác. Han tokenization chưa bảo đảm ZH recall parity, giữ ZH baseline khi so VI.

## 5. Inputs theo phần

Index cần corpus; Retriever cần index/queries/evidence input theo config, không baseline pool. Fusion thêm source rankings trước RRF. Inference không cần labels/final predictions; quality cần control/judgments/scorer đúng snapshot.

[Readiness cũ](reports/EXPERIMENT_READINESS_20261020.md) thiếu corpus/queries/artifacts tại paths chuẩn. Có val.jsonl chưa đủ so; bind paths thật, không dựng control/scores giả.

### 5.3. Error codes và thiếu input

Giữ INPUT_MISSING/HASH_MISMATCH/SCHEMA_INVALID/BASELINE_PARITY_FAILED/FEATURE_UNAVAILABLE/LABEL_COVERAGE_INSUFFICIENT/EVALUATOR_UNVERIFIED/OUTPUT_OUTSIDE_TXT theo code. Ghi file/scope thiếu, không giả hashes/annotators/scores/judgments. Dry-run chưa chứng nhận schema/parity/quality đầy đủ.

## 6. IDs/chunks/nhãn

Giữ query/doc namespace, dedup, finite scores, deterministic order, frozen corpus/query/config/index version. Evidence body[start:end] nguyên văn, Unicode end-exclusive, identity/hash kiểm được; diagnostic refs chưa là submission chunks.

Labels chỉ train/dev/evaluation theo protocol, không chọn doc bằng đáp án query. Unknown không negative, chunk-derived not_gold có thể âm giả. Agent không tự gán relevance y khoa. Giữ [evaluator contract](reports/EVALUATOR_CONTRACT.md).

## 7. Legacy riêng

Package 2.0.0/pool/run/export còn fixed200/w045/manual-qrels, không phải BR/BF. Baseline.py/R0 giữ recipe/fingerprints/allocation/calibration8 cũ. Không sửa nguồn/completed artifacts để ép tương thích. Corpus_parts_v1 là version mới riêng.

## 8. Giả thuyết

- H_retrieve: tìm ứng viên tốt hơn baseline cùng budget, kể cả ngoài union cũ.
- H_fuse: chọn top-k tốt hơn RRF trong cùng union/generators/downstream.
- H_chunk: hướng sau, chọn native chunks cùng docs/slots/text budget có ích không.
- H_joint: chỉ ghép sau bằng chứng độc lập, đo tương tác, không cộng gain.

### 8.3. Protected matcher và semantics

Giữ dấu/số/boundaries: BRCA1≠BRCA10, type 1≠type 2, mg≠mcg. Explicit phrases/relations neo query, aliases cần nguồn/mapping. Same-sentence/order/polarity rules chưa là parser y sinh đầy đủ. Evidence là feature, không gold.

## 9. Đối chứng chính

| Run | VI candidate stage | Sau candidate stage |
|---|---|---|
| B0 | Baseline retrieval + RRF | Downstream baseline |
| BR | BEAR-Retriever corpus/index | Cùng downstream |
| BF | Baseline retrieval + BEAR-Fusion | Cùng downstream |

Cùng top-k/lang/corpus/query/budget, giữ ZH control. BR thay đầu ra generator+fusion VI, BF chỉ fusion. Độc lập, mỗi phần một config khai báo, không grid/BF prerequisite.

D1/DC1/R1/C1 later/legacy; giới hạn 3 candidates/1 control cũ chỉ áp selector pilot đó, không chặn BR/BF. Joint optional sau bằng chứng từng phần, threshold-only là operating-point study phụ.

## 10. Đánh giá

Candidate known-positive coverage cùng depth; labels thiếu không true Recall. BR báo docs ngoài union, BF changed top-k/union membership. Ghi build/index size/latency/RAM/availability/lexical-only/Qwen bổ sung.

Giữ Qwen/MaxP/p̂/threshold/chunk policy. Doc mới cache thiếu score đúng recipe, không gán 0/bỏ doc/áp p̂ threshold lên BEAR score. Candidate top-k khác final variable-k; không ép cuối 160/200.

Đủ labels/scorer mới paired Doc/Chunk/FINAL, CI/sensitivity. Không suy FINAL từ ΔDoc hoặc cộng gain. BTC labels offline, 593 query đã dùng không holdout mới. Chưa bằng chứng thì giữ control/chưa rõ.

## 11. Trạng thái và việc còn lại

| Phần | Trạng thái kỹ thuật | Cần trước quality |
|---|---|---|
| Shared index/scorer | Corpus_parts_v1 lexical + explicit relation rules | Kiểm scope/rules dữ liệu thật |
| Retriever | Corpus/index → candidates, không baseline pool | Inputs thật/B0 cùng budget/downstream |
| Fusion | Source union → candidates thay RRF | Rankings trước fusion/RRF recipe thật |
| CLI/templates/manifests | Ba lệnh nối runner | Bind snapshot/integrity |
| Native chunk selector/exporter | Chưa hoàn tất selected_chunks | Budget/export policy/scorer thật |
| Quality evaluation | Chưa chạy BR/BF trên 0,391 | Judgments/scorer/cache/downstream linkage |

Engineering checks: outside-union doc chỉ Retriever tìm được; Fusion subset union; RRF không lén làm score; protected relations/polarity/IDs/refs/output bounds/corpus readonly/artifact identity đúng. [Demo](tools/demo_bear_parts.py) chỉ minh họa kỹ thuật.

## 12. Vận hành

Prototype không tải model/không cần GPU. Downstream Qwen mới có thể cần GPU; model-free candidate stage không bảo đảm end-to-end CPU. Chưa ETA toàn hệ thống; benchmark kernel CPU cũ không đại diện runtime mới.

Chưa input/parity linkage 0,391, chưa rerun/gain. [Runbook](reports/RUNBOOK.md) dùng lệnh runner thật.

## 13. Bước tiếp

Bind corpus/query/source rankings, build index, dry-run rồi execute BR/BF độc lập. Kiểm candidates/docs mới/union, nối cùng downstream, ghi metrics/limitations vào results/log. Joint sau bằng chứng từng phần.

## 14. Lịch sử

v3.5 bỏ F1-first/S1-deferred, tách hai module theo người dùng. v3.3/v3.4 khôi phục doc/chunk goal, v3.2 threshold-only đã thay. [Archive](archive/PLAN_v3_2_before_doc_chunk_restore_20261020.md), [log](improvement_log.md) giữ lịch sử/kết quả cũ.
