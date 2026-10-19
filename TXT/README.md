# Biomedical Evidence-Aware Retrieval

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
