# Hai phần BEAR — cấu hình chạy

`retrieve` và `evidence-fuse` là hai lựa chọn độc lập, dùng chung index. Không chạy Retriever rồi bắt buộc chạy Fusion.

1. Copy các template, điền paths thật và chọn output_dir mới cho mỗi run. Corpus nhận SQLite table doc (doc_id hoặc id, body; tùy chọn title/lang) hoặc JSONL cùng trường. Queries JSONL có id/query, không chứa gold/not_gold/G.
2. Build index dùng chung:

       python -B -m TXT.bear.cli corpus-index --config TXT/configs/bear_parts/index.template.json --execute

3. Chạy phần thay retrieval:

       python -B -m TXT.bear.cli retrieve --config TXT/configs/bear_parts/retrieve.template.json --execute

4. Chạy riêng phần thay RRF, đọc các rankings nguồn gốc trước fusion:

       python -B -m TXT.bear.cli evidence-fuse --config TXT/configs/bear_parts/fuse.template.json --execute

Đổi --execute thành --dry-run để kiểm paths. Exit1/blocked_input của template khi thiếu dữ liệu là kết quả inventory; chưa chạy inference. File index cần được build trước bước3/4. Đã có output completed thì giữ immutable; dùng output_dir mới khi đổi inputs/config/code.

Hai template đều chọn VI/top300 để so cùng ngân sách. Đây là budget ứng viên trước rerank, không là số doc nộp cuối. Ngôn ngữ, top-k và snapshot cần thống nhất giữa baseline và hai phần thử.

Query đơn giản vẫn chạy nhưng ghi structured_status=unavailable. Để thử quan hệ tường minh, các cụm phải xuất hiện đúng thứ tự trong cùng câu query, ví dụ tổng hợp:

```json
{"id": 1, "query": "DrugA treats DiseaseB", "relations": [{"subject": "DrugA", "predicate": "treats", "object": "DiseaseB"}]}
```

Đây là placeholder kiểm phần mềm; không là nhãn y khoa hay parser tự động. `entities` tùy chọn nhận strings hoặc các object vi/text và views en/zh do caller cung cấp. Neo entity trong query không tự xác minh bản dịch. Không có semantic retrieval cho doc không chia sẻ token query/mapping với index; default VI, chưa bảo đảm substring retrieval cho chuỗi Hán liên tục.

Mỗi phần xuất candidates.jsonl, evidence.jsonl, diagnostics.json, manifest.json. Candidates có id/candidates[{doc_id,score}], đọc được bằng reranker hiện có. Evidence windows chỉ để giải thích, không thay chunk policy nộp bài. Giữ nguyên downstream control khi đo; Qwen cần chỉ rõ top-k phù hợp (CLI legacy mặc định150) và score doc mới nếu cache thiếu.

Chạy ví dụ không cần dữ liệu thật/model:

    python -B -m TXT.tools.demo_bear_parts

[Handover](../../TXT_handover.md) phân biệt B0/BR/BF; [báo cáo](../../reports/BEAR_PARTS_20261020.md) ghi phạm vi kiểm chứng và dữ liệu còn thiếu.
