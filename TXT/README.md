# Biomedical Evidence-Aware Retrieval

Backend hiện tại: **2.0.0**. Bắt đầu với [v2 runbook](configs/next_round/README.md) và [báo cáo triển khai](reports/next_round/V2_IMPLEMENTATION.md). Đã kiểm63tests BEAR +10legacy; benchmark thật còn thiếu snapshot/nhãn. Adaptive production vẫn gated.

Triển khai theo [PLAN.md](PLAN.md), mọi code và output nằm trong TXT.

- [Trạng thái từng task](reports/IMPLEMENTATION_STATUS.md)
- [Lệnh chạy và cấu hình](reports/RUNBOOK.md)
- [Kết quả kiểm chứng](reports/RESULTS.md)
- [Giới hạn còn lại](reports/KNOWN_LIMITATIONS.md)

```powershell
python -B -m TXT.bear.cli --help
python -B -m unittest discover -s TXT/tests -t . -v
```

Đã có luồng CPU và fixtures; dữ liệu thật chưa sẵn sàng. Không coi test xanh là baseline reproduction hoặc quality gain.
