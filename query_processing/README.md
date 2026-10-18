# Xử lý câu hỏi

Package này xử lý câu hỏi đầu vào trước khi truy hồi, không gọi API bên ngoài:

- `expand.py`: dùng Qwen để trích thực thể y khoa và tạo bản dịch nháp tiếng Anh/Trung.
- `translate.py`: dịch câu hỏi bằng Hy-MT2, có bảng thuật ngữ.
- `llm.py`: backend vLLM/Transformers dùng chung.
- `pipeline.py`: điều phối expand + translate và ghi `queries_enriched.jsonl`.

Chạy trên file truy vấn JSONL:

```bash
python -m query_processing.pipeline --queries data/queries.jsonl --out runs/public
```

Các bước truy hồi sử dụng nội dung có sẵn trong dataset ViBioMIR; workflow này
không tải tài liệu PubMed qua API.
