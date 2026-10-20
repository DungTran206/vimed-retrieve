# TXT Proposal v3.5 — BEAR-Retriever và BEAR-Fusion

Cập nhật 20/10/2026. **Hai phần khác bài toán:** Retriever tìm corpus; Fusion chọn trong ứng viên các nguồn đã tìm. Shared index/scorer tránh hai engine trùng nhau.

## 1. Giả thuyết và đối chứng

| Phần | Giả thuyết | Search space |
|---|---|---|
| BEAR-Retriever / BR | Tìm ứng viên tốt hơn baseline cùng top-k | Corpus/index trong scope, có thể ngoài union baseline |
| BEAR-Fusion / BF | Chọn top-k tốt hơn RRF cùng nguồn | Dedup source union, không thêm doc ngoài union |

```text
B0: retrieval baseline → RRF          → downstream control
BR: BEAR-Retriever                    → downstream control
BF: retrieval baseline → BEAR-Fusion → downstream control
```

Scope VI: BR thay đầu ra generator+fusion, BF chỉ thay RRF. Cùng corpus/query/lang/top-k/ZH/downstream. Không buộc BF trước BR; joint chỉ sau bằng chứng từng phần.

## 2. Prototype corpus_parts_v1

Shared stdlib lexical index/BM25 đọc corpus snapshot, không sửa nguồn. Retriever lookup độc lập, Fusion lấy rankings xác định union rồi chấm evidence. Protected phrases neo query, relations subject/predicate/object khai báo explicit, same-sentence/order/polarity rules.

Không relations thì lexical-only; chưa NLP y sinh tổng quát/full relation/indication/condition semantics. Mặc định VI có cấu hình; không ZH recall parity, giữ ZH baseline. Model-free candidate prototype chưa đồng nghĩa downstream Qwen CPU.

CLI corpus-index/retrieve/evidence-fuse có [templates](configs/bear_parts/) và [runbook](reports/RUNBOOK.md). Output candidates tương thích reranker, evidence/manifest. Chunk refs/bear_window diagnostic, chưa native submission selector. [Algorithm](BEAR_ALGORITHM.md), [handover](TXT_handover.md) nêu code/contracts/gaps.

## 3. Đánh giá

Candidate coverage cùng depth/scope; BR doc ngoài union, BF changed top-k trong union. Doc mới cần Qwen cache/inference đúng recipe, giữ MaxP/p̂/threshold/chunk policy và top-k rõ. Không áp p̂ threshold lên BEAR score.

Doc/Chunk/FINAL cần judgments/scorer đúng semantics. BTC labels offline; unknown/weak chunk-derived not_gold không tự âm. Query đã khai thác không holdout mới. Không suy FINAL từ ΔDoc/cộng gain BR+BF.

L1/L4 cũ giữ kết luận scope 0,4076, không thử uniform coverage lại bằng tên mới. Fixture/demo chỉ chứng minh kỹ thuật, explicit relations chưa tự chứng minh relevance có ích.

## 4. Mục tiêu dài hạn và trạng thái

BEAR vẫn hướng tới docs/chunks bằng chứng. D1/DC1/R1/C1 là later/legacy cho pool selector/reranker/native chunk selection cùng budget; không chặn BR/BF. Diagnostic ref chưa chunk submission.

0,391 là control người dùng chọn, run/config/scorer/corpus/chunk policy chưa đủ linkage. Prototype engineering đã có, chưa quality evaluation/parity, không tải model/rerun baseline. Legacy 2.0.0 fixed200/w045 giữ riêng.

[PLAN v3.5](PLAN.md): bind inputs thật, chạy hai phần độc lập, nối cùng downstream rồi đánh giá. [Study](BEAR_REPLACEMENT_STUDY.md) thay F1-first/S1-deferred bằng BR/BF ngang hàng.
