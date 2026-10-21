# BEAR — Medical-gated fusion hypothesis

**Ý tưởng hiện hành:** LLM nhỏ phân tầng độ quan trọng concept trong query; mức khớp concept quan trọng ở document điều khiển BM25/dense. Score được chuẩn hóa, fusion thay RRF, threshold thích ứng thay top-K cố định. Query enrichment dùng KB bệnh → triệu chứng có nguồn Việt/Trung; raw features được cache để tune offline.

Đây là hypothesis người dùng muốn thử, chưa có kết luận tăng điểm baseline 0,391. Agent cần giúp chạy thử và lưu kết quả; phản biện được ghi nhưng không thay cho thực nghiệm được ủy quyền.

```text
KB + Qwen3.5-9B → query taxonomy/enrichment cache
BM25 original/enriched + dense → union/raw score/match cache
fit sigmoid → tune medical gate/fusion/threshold → run → evaluate
```

| Đọc | Nội dung |
|---|---|
| **[Handover](TXT_handover.md)** | Chỉ dẫn agent, commands/configs, inputs/outputs, cách tiếp tục khi thiếu input |
| **[Proposal](TXT_Proposal.md)** | Giải thích chi tiết ý tưởng, mục đích, taxonomy/enrichment/calibration/cache |
| [Algorithm](BEAR_ALGORITHM.md) | Công thức, semantics và invariants |
| [Study](BEAR_REPLACEMENT_STUDY.md) | Đối chứng, splits, metric/budget, phạm vi kết luận |
| [PLAN](PLAN.md) | Trình tự thực nghiệm và điều kiện từng stage |
| [Runbook](reports/RUNBOOK.md) | Lệnh hiện hành và legacy controls |
| [Prompts](prompts/) | Hợp đồng query analysis/enrichment có cấu trúc |
| [Configs](configs/medical_hypothesis/) | Templates cho workflow mới |
| [Pipeline 0,391](PIPELINE_0391.md) | Control từ sơ đồ, chưa đủ runtime linkage |
| [Results](reports/RESULTS.md), [log](improvement_log.md) | Kết quả và lịch sử thực tế |

Từ repository root, kiểm tra CLI và chạy demo kỹ thuật:

```powershell
python -B -m TXT.bear.medical_cli --help
python -B -m TXT.bear.medical_cli demo --output-dir TXT/runtime/medical_hypothesis_demo
```

Workflow mới dùng `python -B -m TXT.bear.medical_cli <stage> --config <path>` để inspect; thêm `--execute` để thực hiện. Không tự tải model/dataset. Các templates cần bind paths thật trước quality experiment.

**BR vẫn độc lập:** BEAR-Retriever tìm corpus/index và có thể ngoài baseline union; BEAR-Fusion mới chỉ chọn từ union. CLI prototype cũ `TXT.bear.cli corpus-index|retrieve|evidence-fuse` giữ riêng làm control. Source union, missing scores và corpus identity phải được giữ nguyên khi so fusion.

Native chunk selector/downstream control chưa đổi. Evidence refs không phải submission chunks. Legacy 2.0.0 fixed200/w045 và kết quả L1/L4/N0/N1 giữ lịch sử riêng. Unknown không tự là negative; query đã khai thác không pristine holdout. Không suy gain từ tests/demo hoặc từ việc có code.

Bản trước ở [archive v3.5](archive/README_v3_5_20261020.md).
