# BEAR — Retriever và Fusion, prototype corpus_parts_v1

Cập nhật 20/10/2026 theo [PLAN v3.5](PLAN.md). **Hai module dùng chung engine nhưng thay hai vị trí khác nhau.** Prototype kỹ thuật đã có; chưa quality evaluation baseline 0,391 hoặc hoàn tất biomedical semantics/doc–chunk submission.

## 1. Hợp đồng hai phần

| | BEAR-Retriever | BEAR-Fusion |
|---|---|---|
| Input | Query, corpus index, lang, top-k | Query, source rankings, index/corpus, lang, top-k |
| Search space | Corpus index trong scope | Dedup union theo query |
| Công việc | Lexical lookup → evidence ranking | Evidence ranking union thay RRF |
| Doc ngoài baseline union | Có thể tìm | Không được thêm |
| Cần baseline pool | Không | Cần source rankings để tạo union |

Retriever tìm độc lập; Fusion lấy rankings làm membership/provenance union, BEAR-only không dùng RRF làm score chính. Shared scorer không làm hai phần trùng nhau vì search spaces khác.

Code: [corpus_index.py](bear/corpus_index.py), [structured_evidence.py](bear/structured_evidence.py), [retrieval.py](bear/retrieval.py), [evidence_fusion.py](bear/evidence_fusion.py), [parts_runner.py](bear/parts_runner.py). Legacy fusion.py/pool/run thuộc residual/fixed200 2.0.0, giữ riêng.

## 2. Index và lookup

Shared stdlib lexical index/BM25 đọc snapshot SQLite mà không sửa corpus, giữ IDs/text/metadata/ngôn ngữ. Retriever lookup corpus scope rồi chấm evidence, không cần rankings baseline. Fusion chỉ chấm union nguồn; không nhận top-k sau RRF làm giả union đầy đủ, không lấy doc ngoài union để bù.

Mặc định languages=["vi"], scope có cấu hình. Han tokenization chưa bảo đảm arbitrary Chinese substring lookup/recall parity. Nghiên cứu VI giữ ZH baseline, chưa claim multilingual parity.

BM25 hiện dùng title weight 2, k1=1.2, b=0.75. Ranking prototype phối hợp 0.6 lexical + 0.4 evidence, chưa chứng minh tối ưu hoặc calibrated probability.

## 3. Evidence chung và semantic scope

- Protected phrases neo trong query, bảo toàn identifiers/số/đơn vị: BRCA1 khác BRCA10, 5 mg khác 15 mg.
- Relations khai báo explicit subject/predicate/object với polarity, components neo trong query. Rules so matching/thứ tự trong cùng câu/ngữ cảnh.
- Không có relations thì lexical-only. Raw queries không tự được parse relation/intent đầy đủ.
- Chưa có general NLP parser/ontology mapper/full biomedical semantics cho indication/condition/population. Rule polarity không thay hiểu phủ định tổng quát.
- No-match/mapping thiếu khác conflict đã quan sát. Evidence/spans không phải relevance gold, không tự hard-filter y khoa.

Shared scorer giữ BR/BF nhất quán; semantic quality cần kiểm dữ liệu thật, không suy từ fixture pass.

## 4. Output và downstream

Retrieve/Fusion xuất candidates.jsonl, evidence.jsonl, manifest.json dưới output_dir:

```json
{"id": 1, "candidates": [{"doc_id": "123", "score": 0.75}]}
```

Giữ IDs/query universe, finite scores, dedup, deterministic order. Manifest gắn inputs/config/version/counts. Refs có corpus/body/offset kiểm được; body windows đánh dấu bear_window là **diagnostic, chưa native selected_chunks/submission selector**.

Candidates đi qua cùng Qwen/MaxP/p̂/threshold/chunk policy control. Truyền đúng top-k; default thấp hơn làm đổi budget. Doc mới thiếu cache cần score bổ sung đúng recipe, không gán 0/bỏ doc/áp p̂ threshold lên BEAR score. Model-free candidate stage chưa có nghĩa end-to-end Qwen chỉ cần CPU.

## 5. Đối chứng và hướng sau

```text
B0: query → retrieval baseline → RRF          → downstream control
BR: query → BEAR-Retriever                    → downstream control
BF: query → retrieval baseline → BEAR-Fusion → downstream control
```

Scope VI: BR thay đầu ra generator + fusion; BF chỉ thay RRF. Cùng top-k/lang/corpus/query/downstream, giữ ZH control. Hai nghiên cứu độc lập, không buộc BF trước BR. [Study](BEAR_REPLACEMENT_STUDY.md) quy định đo.

D1/DC1 pool selectors, R1 thay reranker, C1 chọn chunk là later/legacy, không thay tên BR/BF. Native selector/exporter cần phát triển với budget tương ứng. Có evidence ref chưa chứng minh chunk submission đã đổi.

## 6. Kiểm tra và trạng thái

Engineering tests: Retriever lấy doc ngoài union; Fusion luôn subset union; không lén RRF làm BEAR score; IO/IDs/refs/bounds/corpus readonly đúng. [Demo synthetic](tools/demo_bear_parts.py) chạy BR/BF/RRF_control, chỉ chứng minh kỹ thuật.

Cần inputs/control/source rankings đúng snapshot và downstream/judgments/scorer liên kết trước quality evaluation. Chưa rerun 0,391/đo gain BR/BF, không tải model. L1/L4 giữ kết luận scope cũ.
