# BEAR — Hai nghiên cứu Retriever và Fusion

Cập nhật 20/10/2026 theo [PLAN v3.5](PLAN.md). **Giữ cả hai vì không trùng bài toán:** Retriever tìm corpus/index, Fusion thay RRF trong union. Corpus_parts_v1 có prototype kỹ thuật, chưa quality evaluation/gain 0,391.

## 1. Đối chứng

| Run | VI candidate stage | Cố định |
|---|---|---|
| B0 | Baseline retrievers → RRF | Corpus/query/lang/top-k/ZH/downstream |
| BR | Query → BEAR-Retriever corpus/index | Cùng corpus/query/lang/top-k/ZH/downstream |
| BF | Baseline retrievers → union → BEAR-Fusion | Cùng source rankings/union control RRF, top-k/ZH/downstream |

BR thay đầu ra generator+fusion VI, có thể tìm doc ngoài union baseline. BF chỉ thay RRF/top-k, không cứu doc mọi nguồn đã bỏ. Độc lập, không bắt BF trước hoặc chờ R1/C1. Shared engine tránh lặp code, search spaces khác nhau.

Mặc định VI có cấu hình; scope mới cần control chung và kiểm mappings. Han tokenization chưa bảo đảm ZH recall parity, giữ ZH baseline. Số 2.200/300/40/340 từ [sơ đồ](PIPELINE_0391.md) chưa là runtime counts xác minh.

## 2. BR — Thay candidate retrieval

Query/index corpus trong scope → lexical BM25 lookup → evidence ranking. Không baseline pool làm selectable docs. Fixture cần doc phù hợp ngoài mọi source union mà Retriever vẫn tìm được.

So B0 candidates cùng top-k/lang/corpus/query: known-positive coverage, overlap, doc mới ngoài union/downstream changes. Ghi build/index size/search/evidence/Qwen bổ sung riêng. Không claim lexical prototype tương đương dense model hoặc đã thắng quality.

## 3. BF — Thay RRF

Giữ rankings trước fusion, dedup doc/query, evidence ranking đúng union. Không dùng top-k sau RRF làm giả full union. Source ranks/scores giữ provenance, không lén thành RRF score chính.

RRF control cần đúng weights/k/ties/depth thật; chưa xác minh chưa B0 parity. BF subset union cùng top-k, index chỉ cung cấp text/evidence không bù doc ngoài union. Báo changed top-k/added/removed/union membership. RRF+evidence residual nếu thử là augmentation ablation riêng.

## 4. Engine và outputs chung

Stdlib index/BM25/scorer corpus_parts_v1: protected phrases neo query, explicit subject/predicate/object, same-sentence/order/polarity rules. Không relations thì lexical-only; chưa general NLP/full biomedical semantics.

CLI [runbook](reports/RUNBOOK.md): corpus-index/retrieve/evidence-fuse, [templates](configs/bear_parts/). Inference xuất candidates.jsonl/evidence.jsonl/manifest.json; schema id,candidates[{doc_id,score}]. Chunk refs/bear_window diagnostic, chưa native submission selector.

Không labels inference/model download. Demo/tests synthetic không chứng minh gain. Version mới riêng legacy 2.0.0 fixed200/w045.

## 5. Downstream

Giữ Qwen checkpoint/prompt/preprocessing/MaxP/p̂/calibration/threshold/precision/ties/chunk policy. Candidate top-k explicit tránh default thấp hơn. Doc mới cache thiếu phải inference đúng recipe, không gán 0/bỏ doc/đổi score nguồn thay Qwen.

Threshold control chỉ giữ khi downstream phép tính đúng định nghĩa; không áp p̂ threshold lên evidence score. Chưa linkage recipe thật chỉ candidate-stage engineering, chưa final parity/FINAL. Model-free candidates không đồng nghĩa downstream CPU.

## 6. Inputs và đánh giá

| Dữ liệu | Cần cho |
|---|---|
| Corpus/query snapshot/lang | Index và BR/BF |
| Rankings trước RRF | BF/control RRF |
| Candidates baseline cùng depth | Candidate comparison |
| Qwen cache/model recipe/MaxP/p̂/selection/chunk policy | Cùng downstream |
| Judgments/scorer/split đúng semantics | Relevance/doc/chunk/FINAL |

Preflight cũ thiếu corpus/queries/artifacts 0,391 ở paths chuẩn, val.jsonl hiện diện. Prototype không tự linkage; chưa rerun baseline/quality BR/BF.

Known-positive coverage khi labels thiếu không true Recall. Unknown/chunk-derived not_gold không tự âm. Giữ query universe, availability/lexical-only/fallback/cost. Paired Doc/Chunk/FINAL cần scorer/CI/sensitivity đúng; không đổi budget tạo lợi thế/suy FINAL từ ΔDoc/cộng gain hai phần.

## 7. Later/legacy

F1 cũ tương ứng fusion scope BF; S1 cũ thay một nguồn, khác BR thay đầu ra cả khối VI. D1/DC1 pool pilot, R1 reranker, C1 chunk cùng budget: later/legacy, không prerequisite BR/BF.

Joint optional sau kết quả độc lập/config khóa, đo tương tác thật. Không giữ phần gây hại để đủ module. Hai implementation hợp kiến trúc chưa đồng nghĩa cả hai thắng quality.
