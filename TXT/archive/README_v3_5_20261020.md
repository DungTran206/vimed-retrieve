# BEAR — Hai phần retrieval riêng biệt

**BEAR-Retriever tìm trên corpus/index. BEAR-Fusion thay RRF trên union các nguồn.** Hai phần dùng chung index/evidence scorer, giải quyết hai bài toán khác nhau nên giữ cả hai.

```text
B0: retrieval baseline → RRF          → downstream control
BR: BEAR-Retriever                    → downstream control
BF: retrieval baseline → BEAR-Fusion → downstream control
```

Scope VI: BR thay đầu ra generator + fusion VI; BF chỉ thay fusion. Giữ cùng corpus/query/lang/top-k/downstream và nhánh ZH control. Retriever có thể tìm doc ngoài union baseline; Fusion không thể.

**20/10/2026:** [PLAN v3.5](PLAN.md) có prototype corpus_parts_v1 dùng stdlib lexical BM25/scorer chung. Explicit relations subject/predicate/object phải neo trong query; rules cùng-câu/thứ-tự/polarity chưa là NLP y sinh tổng quát. Không relations thì lexical-only. Chưa quality gain hoặc parity baseline 0,391.

| Đọc | Nội dung |
|---|---|
| **[Handover](TXT_handover.md)** | Hai phần, code/output/gaps hiện hành |
| [Algorithm](BEAR_ALGORITHM.md) | Contracts và evidence prototype |
| [Study](BEAR_REPLACEMENT_STUDY.md) | B0/BR/BF và cách đo |
| [Runbook](reports/RUNBOOK.md) | corpus-index/retrieve/evidence-fuse và demo |
| [Proposal](TXT_Proposal.md), [PLAN](PLAN.md) | Giả thuyết và việc tiếp |
| [Pipeline](PIPELINE_0391.md), [JSON](specs/pipeline_0391.json) | Baseline từ ảnh, chưa đủ linkage runtime |
| [Log](improvement_log.md), [Results](reports/RESULTS.md) | Lịch sử/bằng chứng kiểm tra |

[Templates](configs/bear_parts/) riêng; [demo synthetic](tools/demo_bear_parts.py) chạy bằng `python -B -m TXT.tools.demo_bear_parts`. Candidates tương thích reranker; evidence chunk refs diagnostic chưa là selected_chunks submission.

Legacy 2.0.0 fixed200/w045 giữ riêng. D1/DC1/R1/C1 là later/legacy, không chặn BR/BF. Không tải model/rerun baseline hoặc claim gain. Mặc định VI, không claim ZH parity; model-free prototype chưa bảo đảm downstream CPU. BTC labels offline, unknown không tự âm.
