# Chuẩn bị thử BEAR doc/chunk và tài nguyên CPU/GPU —20/10/2026

**Kết luận:** tài liệu v3.3 đã đúng mục tiêu, nhưng **chưa sẵn chạy thử thuật toán BEAR mới end-to-end trong checkout này**. Còn thiếu implementation có cấu trúc/adapter và inputs baseline0,391. CPU có thể dùng cho nhánh tái sử dụng cache + feature nhẹ; không cần chạy lại Qwen chỉ vì pipeline có Qwen.

**Cập nhật từ người dùng:** có thể dùng máy GPU khác; chưa biết GPU/VRAM/RAM/hệ điều hành, chỉ được mô tả là cấu hình ổn. Có thể tiếp tục thiết kế/triển khai mà không chờ thông số này. Chưa kiểm kết nối, môi trường hoặc chạy model trên máy đó; chưa có ETA GPU. Checklist bàn giao và lý do cần từng phần ở §7.

## 1. Đã kiểm gì?

| Thành phần | Trạng thái quan sát |
|---|---|
| PLAN/proposal/BEAR_ALGORITHM/handover | Đã mô tả selected_docs + selected_chunks, B0/D1/C1/DC1; không thu hẹp thành audit/threshold |
| Package2.0.0 và CLI | CLI help chạy được; chưa có runner v3.3 doc/chunk hoàn chỉnh |
| Evidence hiện có | uniform_exact_v1; critical_mismatches còn placeholder list rỗng, chưa có parser relation/conflict mới |
| Pool/chunk/export cũ | Một số luồng yêu cầu200doc/query; không chạy thẳng baseline0,391 variable-k |
| data/ và inputs | data/ chỉ có .gitkeep; chưa có corpus/query/cache/0,391control tại các đường dẫn chuẩn |
| Root val.jsonl | Có file864.073byte; file presence không xác minh mọi nhãn âm là doc-negative thật |
| Các ZIP root | Lịch sử chưa nối0,391; không tự dùng prediction_result/x12m_ext10 làm control mới |

Các kết quả1.200câu/parityw045 đã được báo trước vẫn giữ; kiểm tra này chỉ xác định inputs/code của **phép thử mới**, không yêu cầu chạy lại N0/N1.

## 2. Preflight A0 thực sự đã chạy

Cấu hình [preflight_0391.template.json](../configs/bear_doc_chunk/preflight_0391.template.json) dùng CLI provenance hiện có, chỉ inventory6roles cần cho A0. Nó không chạy thuật toán hoặc xác nhận schema/metric.

    python -B -m TXT.bear.cli provenance --config TXT/configs/bear_doc_chunk/preflight_0391.template.json --dry-run

Kết quả lưu nguyên tại [bear_doc_chunk_preflight_20261020.json](bear_doc_chunk_preflight_20261020.json): **blocked_input**, exit1 theo thiết kế CLI khi thiếu input. Đây không phải lỗi cài đặt. Có btc_validation; thiếu5roles:

| Role | Cần cung cấp khi chạy |
|---|---|
| queries | Query text đúng snapshot; đường dẫn chuẩn data/queries.jsonl hiện thiếu |
| baseline_0391_predictions | Output doc/chunk của đúng bài0,391 và counts từng query |
| candidates_and_cached_scores | Ứng viên trước chọn cuối, ngôn ngữ/ranks/p̂ và score nguồn đã có để tái dùng |
| corpus | Body và native chunks/offsets đúng corpus; data/corpus_new.sqlite hiện thiếu |
| baseline_chunk_policy_and_refs | Policy/budget/chunk refs và mapping score chunk thực; không tự lấy allocationw045 |

Một file/manifest thực có thể đáp ứng nhiều role nếu đúng schema và snapshot; không yêu cầu nhân bản data. Structured extractor mới là **gap code riêng**, không được tính là đã sẵn chỉ vì đã bind files. Passage judgments/tokenizer/scorer chunk phù hợp còn cần nếu muốn đo officialChunkF2.

Khi dùng máy đã có cache, sao chép config sang tên mới rồi bind đường dẫn thật. Không thay null bằng hash/path giả hoặc coi inventory available là đã có runner/quality gain. Không tự chạy commands oldfixed200 để tạo bài thử0,391.

## 3. Khi nào chỉ cần CPU?

| Công việc | CPU/GPU |
|---|---|
| Đọc corpus/cache, kiểm spans/identifiers bằng rule nhẹ, tính evidence, fusion, chọn doc/chunk | CPU được, sau khi có implementation/inputs tương ứng |
| Chấm DocF2/paired statistics từ judgments có sẵn | CPU được; chunk evaluator có thể tốn nhiều hơn tùy scorer |
| Tái dùng embeddings và điểm Qwen/MaxP/p̂ đã cache | Không cần gọi lại model |
| Dùng LLM/model mới để trích relation/intent chưa có cache | Phải đo riêng; không thể áp ETA của kernel rule-based |
| Chạy lại Qwen reranker/embedding toàn bộ pipeline | Nên dùng máy GPU; thời gian CPU chưa đo trong lượt này |

Nhánh CPU-first vẫn phải tạo doc và chunk. Feature nhẹ đầu tiên phải khác uniform L1/L4, có identity/role/điều kiện đã xác minh và availability/fallback; không đổi tên coverage rồi gọi là structured evidence. Quan hệ ngữ nghĩa phức tạp không được giả là đã hiểu bằng vài regex.

## 4. Phép đo CPU có thể tái lập

Máy đo: **11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz**, 8luồng logic, RAM7.8GiB; Python3.13.1. RAM available tại thời điểm chạy khoảng0.7GiB, không phải mức trống cố định.

Chạy **một luồng**,8concept/query, chunk1.000ký tự không overlap, body lặp tổng hợp. Mỗi scenario3mẫu khoảng0,65giây. Đo hàm document_evidence **exact/body/local cũ**, không phải structured BEAR mới. [JSON số đo](cpu_kernel_benchmark_20261020.json), [script](../tools/benchmark_cpu.py).

| Body/doc | Chunk/doc | Query–doc/giây, median | Ngoại suy kernel cho408.000cặp |
|---|---:|---:|---:|
| 4,000 ký tự | 4 | 725.6 | 9.4 phút |
| 20,000 ký tự | 20 | 173.6 | 39.2 phút |
| 80,000 ký tự | 80 | 44.5 | 152.8 phút |

408.000=1.200×340 theo cap trong ảnh, **không phải số pair runtime đã xác nhận**. Repeated texts/cache warm và chưa có I/O corpus khiến số này không đại diện full corpus. Không chia thời gian cho8luồng vì chưa benchmark scaling.

Chưa tính: đọc corpus/cache thật, feature relation/conflict mới, selectors, bootstrap/scorer chunk, JSON/ZIP và mọi model inference. **ETA end-to-end vẫn null**. Những số trên chỉ cho thấy kernel CPU nhẹ nằm ở mức phút đến vài giờ theo độ dài text.

Để lên lịch tạm cho nhánh nhẹ đã có cache, có thể dành **khoảng1–4giờ cho một vòng full**, nhưng đây chỉ là ngân sách dự phòng, **chưa phải ETA được kiểm**; scorer chunk nặng/model mới hoặc thiếu RAM có thể vượt mức đó. Không bao gồm thời gian viết phần code còn thiếu và chuẩn bị dữ liệu.

## 5. Chốt thời gian bằng20query thật

1. Sau A0/A1 và selectors chạy được, chọn20query đại diện, có bài ngắn/dài, VI/ZH, nhiều/ít chunks và đúng candidate counts.
2. Đo riêng I/O, evidence, selector, evaluation và export. Lưu tổng pair/chunk/ký tự, walltime và peakRAM; không chỉ đếm số query.
3. Ước lượng full theo pair/ký tự/chunk của tập thật; tách chi phí cố định/ZIP và official scorer. Query dị biệt cần nhiều size bins, không chỉ nhân một query nhanh nhất lên1.200.
4. Cache evidence một lần cho B0/D1/C1/DC1 khi cùng feature; không quét lại text bốn lần không cần thiết.

8GiBRAM có thể làm pilot streaming, nhưng mức trống lúc đo dưới1GiB cần giảm tải ứng dụng khác và đọc theo query/shard; không nạp toàn corpus/featurematrix. Khởi đầu1worker; chỉ tăng sau đo RAM/throughput.

## 6. Lệnh kiểm tra CPU

Từ repo root, không tải model hoặc gọi GPU:

    python -B -m TXT.tools.benchmark_cpu --output TXT/runtime/bear_doc_chunk/cpu_probe_new.json

Output mới dùng tên/path mới khi đo lại. Script chỉ đo kernel cũ, không chạy A2/A3 hoặc báo gain. Các bước triển khai tiếp ở [PLAN](../PLAN.md), [runbook](RUNBOOK.md), [handover](../TXT_handover.md).

## 7. Máy GPU đã có: còn thiếu gì và ai chuẩn bị?

GPU phục vụ inference khi A1 dùng model trích bằng chứng mới hoặc khi cache baseline thiếu. Việc có GPU không thay thế code selector, corpus hoặc output đối chứng. Không yêu cầu dựng lại pipeline từ đầu nếu còn cache đúng run.

### Dữ liệu lấy từ máy đã chạy baseline0,391

Đây là nội dung tối thiểu cần bàn giao, **không phải schema CLI đã triển khai**. Tên file có thể khác; dùng đường dẫn thật hoặc copy dữ liệu, không bắt nhân bản một nguồn cho nhiều role.

| Mục còn thiếu tại checkout | Nội dung cần có | Vì sao cần |
|---|---|---|
| Queries | qid và query nguyên văn đúng snapshot | Trích yêu cầu của query; nối đúng với doc, predictions và nhãn |
| Corpus | doc_id, title/body và ngôn ngữ; chunks/offsets hoặc quy tắc tạo window có thể kiểm | Tính bằng chứng trên nội dung thật và xuất chunk nguyên văn đúng doc |
| Output baseline0,391 | Danh sách doc/chunk thực xuất theo qid, thứ tự, số lượng; run/config tương ứng nếu có | Có control B0; biết k thực từng query và budget để đo thay đổi công bằng |
| Candidates và điểm cache | Pool trước chọn cuối, qid/doc_id/ngôn ngữ, điểm nền thực dùng; giữ ranks/score nguồn và mapping score chunk nếu có | Có doc thay thế ngoài tập đã nộp; tái dùng điểm đã tính thay vì chạy lại model |
| Policy chunk baseline | Chunk refs đã xuất, slots/budget, cách chọn/chia chunk và mapping vào body | C1 giữ đúng budget và chỉ thay selector; tránh lấy policy w045 hoặc giả chunk=body |

Không bắt chuyển dense vectors/index nếu scores/cache đủ cho pilot rerank trên pool hiện có. Không bắt chuyển mọi score trung gian nếu adapter đã có đủ đầu vào cần thiết; phải ghi rõ điểm nào dùng và điểm nào không có. Thiếu score nền chunk có thể mở nhánh evidence-only được khai báo, không giả đã có u(q,c).

### Code là phần agent cần triển khai

1. **A0:** adapter nối các input thật và hỗ trợ variable-k/native chunks; bỏ assumptions fixed200 trong đường chạy mới. Bypass đối chiếu với output0,391 đã có, không làm lại N0/N1w045.
2. **A1:** một cơ chế bằng chứng có identity/role/điều kiện và local support/conflict, kèm spans/availability/fallback. Chốt cách tính hoặc model/checkpoint nếu cần; uniform coverage và placeholder list rỗng chưa đáp ứng.
3. **A2/A3:** Doc Selector và Chunk Selector tạo selected_docs/selected_chunks thật, nối exporter. Fixture chỉ kiểm đúng cơ chế, không chứng minh gain.
4. **A4:** runner B0/D1/C1/DC1, metric và báo cáo added/removed/fallback/budget. Có thể làm D1 hoặc C1 trước khi nhánh kia đủ dữ liệu; không buộc chờ joint.

Người dùng không cần tự viết các phần này hoặc gán tay lại593query. Agent có thể phát triển phần độc lập ngay; adapter cuối và phép đo trên dữ liệu thật cần sample/schema thật rồi full inputs.

### Nhãn và chấm điểm

Root val.jsonl đã có và được phép dùng offline với hạn chế semantics đã ghi. Nhãn không cần cho inference; cần để biết thuật toán có tăng điểm. Muốn báo official ChunkF2/FINAL cần xác nhận passage judgments và scorer/tokenizer đúng semantics. Nếu chưa đủ, vẫn chạy inference/DocF2 trong scope hợp lệ và ghi rõ chunk chỉ là diagnostic, không tự suy FINAL.

### Chuẩn bị trên máy GPU

Chuyển cùng phiên bản code TXT và bộ dữ liệu đúng snapshot. Khi truy cập được máy, kiểm backend/driver, GPU/VRAM/RAM, môi trường Python và dependencies của model thực dùng. Nếu gọi model, cần checkpoint/revision, prompt/preprocessing, precision, giới hạn đầu vào và batch; các nhãn Qwen trong ảnh chưa đủ để cài đúng pipeline. Nếu replay cache, chưa cần tái dựng toàn bộ môi trường model baseline.

Chạy smoke nhỏ để kiểm mapping/output và model load nếu có, sau đó đo20query thật rồi mới full. Chưa có thông số máy hay checkpoint nên không ấn định VRAM tối thiểu, batch hoặc thời gian GPU. Số CPU ở §4 chỉ giữ giá trị tham khảo cho kernel đã đo.
