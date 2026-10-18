# Xử lý câu hỏi

Package này chứa các bước áp dụng lên truy vấn trước khi truy hồi:

- `query_gen.py`: dùng Qwen để trích thực thể y khoa, dịch nháp và sinh các truy vấn PubMed.
- `translate.py`: dịch câu hỏi sang tiếng Anh/Trung bằng Hy-MT2, có bảng thuật ngữ.
- `llm.py`: backend vLLM/Transformers dùng chung cho các bước trên.

Các module không gọi API PubMed. Workflow phối hợp xử lý câu hỏi với tìm kiếm/tải
bài được đặt tại `pipelines/pubmed.py`; tích hợp dịch vụ PubMed nằm ở `pubmed_module/`.
