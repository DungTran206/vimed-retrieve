# Triển khai hai phần BEAR — 20/10/2026

Đã triển khai prototype `corpus_parts_v1` với hai giao diện độc lập, dùng chung corpus index và evidence scorer. Chưa đánh giá relevance hoặc xác nhận parity với baseline 0,391.

| Phần | Đầu vào | Phạm vi kết quả |
|---|---|---|
| BEAR-Retriever | Query + corpus index | Các doc có token query hoặc entity mapping khai báo trong corpus; có thể ngoài mọi pool baseline |
| BEAR-Fusion | Query + rankings từng nguồn + cùng corpus index | Chỉ doc trong hợp nguồn; thay RRF bằng điểm evidence, không dùng ranks/score nguồn để tính điểm hoặc phá hòa |

Index SQLite chỉ đọc corpus nguồn, giữ dấu/số/identifier và offsets Unicode gốc. Scorer kết hợp BM25 với exact phrase evidence; quan hệ cần khai báo subject/predicate/object được neo trong query. Có giải thích các span, polarity và availability. Không có parser quan hệ y sinh tổng quát; query không có relations dùng nhánh lexical/entity với structured_status=unavailable. Entity mappings EN/ZH là nội dung caller cung cấp, không tự chứng nhận bản dịch. Scope mặc định là VI; index token Hán hiện chưa bảo đảm tìm các cụm con trong một chuỗi Hán liên tục.

Chunk refs có provenance `bear_window`, hashes và offsets, phục vụ giải thích điểm ứng viên. Chưa tích hợp thành native chunk selector hoặc submission mới. Trọng số prototype cố định, chưa được tuning/chứng minh gain.

## Kiểm chứng đã chạy

- `python -B -m unittest discover -s TXT/tests -t .`: **98/98 qua**, gồm 35 test mới cho index/evidence/hai runner và 63 test BEAR có trước.
- `python -B -m unittest tests.test_offline`: **10/10 qua**.
- CLI `corpus-index`, `retrieve`, `evidence-fuse` được thực thi trong integration tests; output đọc được bằng adapters hiện có và loader của RRF. Manifest kiểm input/config/code hash, resume và thay đổi input/output. Kiểm thêm paths tương đối khi chạy ngoài repo, phục hồi index sau gián đoạn, bảo toàn file không thuộc run, chặn WAL kể cả .SQLITE3 và từ chối source row thiếu danh sách candidates.
- Đã chạy `python -B -m TXT.tools.demo_bear_parts --output-dir TXT/runtime/bear_parts/demo_two_parts_final_20261020`. [Report thực](../runtime/bear_parts/demo_two_parts_final_20261020/comparison.json) và manifests nằm trong runtime. Fixture là các placeholder DrugA/DiseaseB, không là dữ liệu hay nhãn y khoa thật.

| Luồng demo | Thứ tự doc thực xuất |
|---|---|
| RRF control tổng hợp | a_reversed, b_supported |
| BEAR-Retriever | c_outside, b_supported |
| BEAR-Fusion | b_supported, a_reversed |

Ba kiểm tra scope đều qua: Retriever tìm được c_outside ngoài hợp nguồn; Fusion không thêm doc ngoài hợp; Fusion ưu tiên binding đúng thay vì thứ hạng nguồn. Kết quả này kiểm phần mềm, không là gain retrieval trên dữ liệu thật.

## Chạy trên dữ liệu thật

[Config mẫu](../configs/bear_parts/index.template.json), [retrieve](../configs/bear_parts/retrieve.template.json), [fusion](../configs/bear_parts/fuse.template.json) dùng các paths cần bind trên máy có dữ liệu. CLI dry-run đã xác nhận thiếu corpus cho build index; thiếu index/query cho retrieve; thiếu thêm ba rankings nguồn cho fusion. [Inventory thực](bear_parts_preflight_20261020.json) lưu kết quả theo từng lệnh. Dry-run chỉ kiểm hiện diện file.

Để so B0/BR/BF cần cùng corpus/query/ngôn ngữ/top-k và giữ cùng Qwen/MaxP/threshold/chunk policy downstream. BR tạo thẳng danh sách VI thay khối retrieval + fusion VI; BF giữ các nguồn VI và thay riêng fusion. Nhánh ZH lấy theo control. Doc mới cần chạy Qwen nếu cache chưa có. Chưa xác minh full recipe/artifacts baseline0,391 nên không gọi demo RRF là control0,391 tái lập.

Xem [handover](../TXT_handover.md) và [runbook](RUNBOOK.md). Không chạy GPU/model inference, tạo submission hoặc upload trong lượt triển khai này. Metric Doc/Chunk/FINAL và quality gain mới chưa có.
