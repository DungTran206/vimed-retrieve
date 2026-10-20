# Handover — BEAR-Retriever và BEAR-Fusion

Cập nhật 20/10/2026, [PLAN v3.5](PLAN.md). **BEAR có hai phần khác nhau, được triển khai ở mức prototype corpus_parts_v1: Retriever tìm corpus/index; Fusion chọn trong union để thay RRF.** Hai phần dùng chung index/evidence scorer. Chưa đánh giá chất lượng trên baseline 0,391.

## 1. Hai phần và vị trí thay thế

| Phần | Đầu vào → đầu ra | Giới hạn |
|---|---|---|
| **BEAR-Retriever / BR** | Query + corpus index → ranked candidates | Tìm độc lập trong scope ngôn ngữ; có thể tìm doc ngoài mọi pool baseline |
| **BEAR-Fusion / BF** | Query + source rankings → dedup union → ranked candidates | Thay RRF, không thêm doc ngoài union của query |

```text
B0: Query → retrieval baseline → RRF          → cùng downstream
BR: Query → BEAR-Retriever                    → cùng downstream
BF: Query → retrieval baseline → BEAR-Fusion  → cùng downstream
```

Trong nghiên cứu VI, BR thay đầu ra cả khối sinh ứng viên + fusion VI; BF chỉ thay fusion VI. Giữ nhánh ZH theo control. Cùng corpus/query/lang/top-k/downstream. BR đo khả năng tìm tài liệu, BF đo chọn/gộp ứng viên đã có; không bắt BF trước BR hoặc chờ pilot doc/chunk cũ.

## 2. Code, cấu hình và chạy thử

- [corpus_index.py](bear/corpus_index.py): shared lexical index từ corpus chỉ đọc.
- [structured_evidence.py](bear/structured_evidence.py): scorer chung, protected phrases và quan hệ tường minh.
- [retrieval.py](bear/retrieval.py), [evidence_fusion.py](bear/evidence_fusion.py): hai thuật toán riêng.
- [parts_runner.py](bear/parts_runner.py), [cli.py](bear/cli.py): I/O, manifest và CLI.

| Lệnh | Config mẫu |
|---|---|
| corpus-index | [index.template.json](configs/bear_parts/index.template.json) |
| retrieve | [retrieve.template.json](configs/bear_parts/retrieve.template.json) |
| evidence-fuse | [fuse.template.json](configs/bear_parts/fuse.template.json) |

Dùng `python -B -m TXT.bear.cli <lệnh> --config <path> --dry-run`; thay bằng `--execute` khi bind inputs thật. [Runbook](reports/RUNBOOK.md) có trình tự. Templates chưa là linkage baseline đã xác minh.

Có [demo synthetic](tools/demo_bear_parts.py): `python -B -m TXT.tools.demo_bear_parts`. Demo xuất BR, BF, RRF_control và comparison.json; chỉ chứng minh kỹ thuật, không đánh giá baseline 0,391. [Báo cáo triển khai](reports/BEAR_PARTS_20261020.md) và [inventory hiện tại](reports/bear_parts_preflight_20261020.json) ghi kiểm chứng thực.

Retrieve/Fusion xuất candidates.jsonl, evidence.jsonl và manifest.json dưới output_dir. Candidate có `id` và `candidates[{doc_id, score}]`, tương thích reranker. **Chunk refs/bear_window trong evidence là diagnostic, chưa phải native selected_chunks hoặc submission chunk selector.**

## 3. Prototype và giới hạn

Index/search dùng stdlib lexical BM25, title weight 2, k1=1.2, b=0.75; score prototype phối hợp 0.6 lexical + 0.4 evidence. Chưa chứng minh tối ưu hoặc calibrated probability. Không tải model.

Scorer nhận phrases neo trong query và explicit subject/predicate/object với polarity; rules so thứ tự/cùng câu. Không có relations thì lexical-only/entity evidence, với structured_status=unavailable. Chưa có parser NLP tổng quát hay ngữ nghĩa y sinh đầy đủ; không diễn giải lexical score thành relation/intent đã hiểu.

Mặc định languages=["vi"], scope có cấu hình. Tokenization Han chưa bảo đảm Chinese substring lookup/recall parity; nghiên cứu VI giữ nhánh ZH baseline. Model-free candidate stage không đồng nghĩa Qwen/downstream chạy CPU.

**Legacy riêng:** package/runner 2.0.0 cũ còn fixed200/w045/residual fusion/C1C2 scaffolding; không dùng pool/run/export cũ để giả BR/BF. Corpus_parts_v1 là version prototype riêng.

## 4. Đối chứng và bước tiếp

Bind corpus/query/source rankings đúng snapshot; khóa top-k/lang/corpus/query/downstream. Candidate top-k khác output variable-k cuối, không ép 160/200. Đo coverage cùng depth, BR doc mới ngoài union, BF changed top-k, build/index size/latency/RAM/availability/lexical-only rate.

Giữ Qwen checkpoint/prompt/preprocessing, MaxP/p̂/threshold/chunk policy control. Doc mới thiếu cache phải score đúng recipe; không gán 0/bỏ doc hoặc áp p̂ threshold lên BEAR score. Chỉ chấm Doc/Chunk/FINAL khi đủ judgments/scorer đúng semantics.

BTC labels offline, không đọc tại inference. Unknown/chunk-derived not_gold không tự âm; 593 query đã khai thác không thành holdout mới. Không suy FINAL từ ΔDoc hoặc cộng gain BR+BF. Joint optional sau kết quả độc lập. D1/DC1/R1/C1/native chunk selector/exporter là later/legacy, không chặn Retriever.

## 5. Dữ liệu và lịch sử

0,391 là score người dùng báo; sơ đồ khoảng 300 VI + 40 ZH trước rerank, threshold cho mean khoảng 160 docs/query. Chưa đủ run/config/scorer/chunk policy linkage; không coi counts sơ đồ là runtime đã đo.

[Preflight cũ](reports/bear_doc_chunk_preflight_20261020.json), [readiness](reports/EXPERIMENT_READINESS_20261020.md) thiếu corpus/queries/artifacts baseline ở paths chuẩn; val.jsonl hiện diện. Đó là snapshot lịch sử, prototype không tự làm input xuất hiện. Chưa rerun baseline hoặc quality evaluation BR/BF.

L1/L4 trên 0,4076 giữ best ΔDocF2 +0.0003/+0.0004, CI95 chạm 0/âm theo báo cáo; không chạy lại coverage bằng tên khác. N0/N1 w045 đã có kết quả được báo, không làm lại prerequisite. Output mới dưới TXT, nguồn/completed artifacts chỉ đọc. Máy GPU người dùng có thể dùng cho downstream models khi cần, chưa có ETA toàn hệ thống.

Đọc [algorithm](BEAR_ALGORITHM.md), [study](BEAR_REPLACEMENT_STUDY.md), [PLAN](PLAN.md), [log](improvement_log.md), [results](reports/RESULTS.md).
