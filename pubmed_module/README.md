# PubMed API module

Package này chỉ chứa phần tích hợp với các dịch vụ PubMed/Europe PMC:

- `http.py`: HTTP client, retry và cache SQLite.
- `utils/rate_limit.py`: giới hạn tốc độ dùng chung với crawler.
- `search.py`: tìm PMID qua NCBI ESearch và Europe PMC.
- `fetch.py`: lấy title/abstract theo PMID qua PubTator, EFetch và Europe PMC.
- `fetch_en_pubmed.py`: tác vụ tải corpus PubMed hàng loạt từ Europe PMC.

Các bước xử lý câu hỏi nằm trong `query_processing/`; CLI điều phối toàn luồng
nằm trong `pipelines/pubmed.py`. Xem `pipelines/README.md` để chạy workflow.
