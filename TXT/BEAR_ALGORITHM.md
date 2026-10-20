# BEAR — Thuật toán retrieval doc và chunk trên baseline0,391

Cập nhật20/10/2026, theo đính chính mục tiêu của người dùng. **BEAR phải tạo ra doc và chunk**, không dừng ở audit hoặc tuning threshold. Đây là đặc tả thuật toán `PROPOSED`; package hiện có vẫn2.0.0, chưa triển khai đầy đủ cơ chế dưới đây hoặc đo gain.

## 1. Vai trò và hai đầu ra

BEAR là retrieval hai tầng. Giai đoạn đầu tái dùng BM25/dense/fusion/reranker của [pipeline0,391](PIPELINE_0391.md) để sinh ứng viên và điểm nền. Giai đoạn sau dùng bằng chứng y sinh để chọn doc và trích chunk. Phiên bản pilot không tuyên bố tìm được doc ngoài pool đang có.

```text
Query + corpus + ranks/scores baseline
  → ứng viên doc và native chunks
  → biểu diễn yêu cầu y sinh của query
  → evidence có vị trí/quan hệ cho từng chunk
  ├─ BEAR Doc Selector → danh sách doc được chọn/xếp hạng
  └─ BEAR Chunk Selector → chunk nguyên văn cho các doc đã chọn
  → output doc/chunk tương thích submission
```

| Đầu ra | Nội dung tối thiểu |
|---|---|
| `selected_docs` | qid, doc_id, rank, baseline_score, bear_score, evidence_status, fallback_reason |
| `selected_chunks` | qid, doc_id, chunk/native-window ref, start/end, nguyên văn hoặc text hash, evidence_score, selection_reason |

Audit và explanations là thông tin kèm theo. Output chỉ có flags/report mà không có doc/chunk được chọn **chưa đạt mục tiêu BEAR**.

## 2. Biểu diễn query và bằng chứng

Biểu diễn yêu cầu thành các thành phần có nguồn: thực thể/identifier, quan hệ hoặc ý định cần trả lời, đối tượng/điều kiện, liều/đơn vị nếu query nêu. Mỗi thành phần có span gốc, mapping/alias đã kiểm và availability. Không giả định hiện đã có parser đáng tin cho tất cả các thành phần.

Với một chunk `c`, tính feature có cấu trúc:

- **Support:** chunk hỗ trợ cùng thực thể và cùng quan hệ/điều kiện mà query yêu cầu, với spans/role mapping làm căn cứ.
- **Conflict cục bộ:** khác identifier/biến thể hoặc điều kiện rõ ràng trong ngữ cảnh đang so. Không coi mọi lần nhắc identifier khác trong một bài dài là xung đột của cả doc.
- **Availability:** computed/no-match khác unknown. Thiếu parser, mapping hoặc ngữ cảnh không tự chuyển thành mismatch/điểm âm.

Ví dụ cơ chế cần phân biệt: query yêu cầu `BRCA1`, một đoạn chỉ nói về `BRCA10`; query hỏi quan hệ A→B, doc chỉ nhắc A/B ở các đoạn khác nhau. Đây là yêu cầu kỹ thuật cần kiểm chứng, không phải bộ nhãn y khoa tự tạo.

**Khác L1/L4:** không chỉ đếm đủ entity trong body hoặc lấy coverage lớn nhất trong một chunk. Tín hiệu đề xuất phải thể hiện identity/role/điều kiện và có đối chứng ngoài uniform coverage. Nếu chưa xây được feature đó thì chưa được gọi là đã thực hiện thuật toán mới.

## 3. Điểm chunk và điểm doc — công thức đề xuất

Gọi `b(q,d)` là điểm nền baseline qua phép biến đổi cố định `T0`; `u(q,c)` là chunk score nền nếu có mapping hợp lệ. Không tự coi p̂ là xác suất đã calibrated hoặc giả score của chunk chưa được chấm.

```text
e(q,c)   = support_structured(q,c) − β × conflict_local(q,c)
s_doc    = b(q,d) + α × aggregate_valid_evidence({e(q,c): c thuộc d})
s_chunk  = u(q,c) + γ × e(q,c)
```

Đây là họ thuật toán cần triển khai, chưa có α/β/γ hay `T0` đã chọn. Pilot chỉ dùng **một feature có cấu trúc đã được xác minh**, một cấu hình cố định cho từng selector; không mở grid tất cả trọng số/feature cùng lúc. Tách thiếu feature khỏi giá trị0.

Aggregation doc phải dựa trên ngữ cảnh phù hợp; một đoạn khác chủ đề không tự làm hỏng một đoạn trả lời đúng. Nếu chọn max evidence, kiểm thiên lệch body dài/nhiều chunk; không gọi local max mới là cải tiến chỉ vì tên khác L4.

Nếu `u` thiếu, chỉ được dùng evidence-only chunk selector như một nhánh công khai với đối chứng tương ứng; không điền u=0 rồi tuyên bố đã giữ cùng mô hình nền. Nếu evidence chưa đủ tin cậy, fallback về selector baseline cho đúng scope đã khai báo.

## 4. Chọn doc: thay doc thật, không chỉ đổi thứ tự

Pilot D1 giữ `k_q` bằng số doc baseline thực xuất ở từng query để cô lập **chất lượng tập doc**. Sau khi xếp lại ứng viên bằng `s_doc`, chọn lại doc theo budget đó. Cùng tập doc chỉ đổi thứ tự không tạo gain Doc F2; phải báo added/removed và số query thật sự thay đổi.

Nếu pilot chỉ có evidence/mapping đáng tin cho VI, khai báo **D1-VI**: giữ doc non-VI baseline, chọn lại đúng số VI baseline từ các ứng viên VI có sẵn. Đây là đối chứng có chủ đích, không khẳng định baseline có quota ZH cuối. Bản đa ngôn ngữ chỉ mở khi evidence/alias đủ để so công bằng.

Trong scope can thiệp, nếu selectable candidates thiếu feature/mapping cần thiết thì dùng baseline fallback đã khai báo; không loại doc thiếu feature để tự nâng điểm. Không mặc định200doc/query, top160 cố định hoặc cap400VI.

Tối ưu count/threshold sau đó là nghiên cứu selection-budget riêng. Nếu chuyển score sang thang BEAR thì không tái dùng τ₀ một cách máy móc; cần xác định operating point mới và đo trên cùng protocol. Tuning threshold không thay cho việc chứng minh D1 chọn doc tốt hơn.

## 5. Chọn chunk: tạo bằng chứng nguyên văn

Với mỗi doc đã có suất, dùng `s_chunk` để chọn chunk/window thực sự liên quan đến yêu cầu query. Ràng buộc: đúng doc/corpus, offsets Unicode end-exclusive, text nguyên văn, native ref hoặc window mapping đã xác minh.

Pilot C1 giữ **doc set, thứ tự, slots và ngân sách chunk/token thực của control**, chỉ đổi selector. Không tăng điểm bằng cách xuất nhiều text hơn rồi quy cho evidence. Nếu baseline chỉ có một full-body chunk và không có lựa chọn khác dưới cùng budget thì ghi chunk pilot không có headroom; không ép cắt nhỏ hoặc suy điều này từ ảnh.

Chunk dùng tính feature, chunk được chọn và chunk được exporter xuất phải liên kết được. Một `best_evidence_chunk_ref` trong report mà release ghi đè sang chunk khác chưa phải C1 hoạt động trong submission.

## 6. Bốn đối chứng để chứng minh thuật toán

| Run | Doc selector | Chunk selector | Câu hỏi |
|---|---|---|---|
| B0 | Baseline0,391 | Baseline0,391 | Control |
| D1 | BEAR | Baseline policy | BEAR có chọn tập doc tốt hơn không? |
| C1 | Baseline doc set/order | BEAR, cùng budget | BEAR có chọn chunk tốt hơn không? |
| DC1 | BEAR | BEAR | Hai phần ghép lại có tăng metric cuối không? |

Đây là **tối đa3candidate mới và1control** khi đủ dữ liệu, không phải3grid tuning. D1/C1 có thể phát triển độc lập; joint cần hai selector và exporter tương thích. Nếu một phần không có gain, vẫn giữ phần kia nếu được chứng minh độc lập. Không buộc adaptive routing phải thành công.

Doc primary: paired Doc F2 khi có judgments đáng tin. Chunk primary: metric chunk đúng scorer/semantics khi có; local LCS chỉ là diagnostic. Joint: metric doc/chunk và FINAL thực đo, không suy ΔFINAL từ ΔDoc. Nhãn BTC dùng offline; unknown/weak negative không tự thành âm.

## 7. Mức sẵn sàng của code

Code2.0 có protected matcher, body/local/critical coverage, chunk refs, fusion và C1/C2 scaffolding. **Chưa đủ** để nói đã có cấu trúc quan hệ/intent, conflict scorer hoặc selector mới đúng đặc tả này. `critical_mismatches` hiện có chỗ trả list rỗng; không xem đó là detector đã hoạt động.

Các luồng pool/export còn ràng buộc w045/fixed200; cần adapter đúng baseline0,391 và output variable-k/native chunks. Không sửa corpus, beta hoặc dữ liệu nguồn để khớp đặc tả. Chưa có command `bear-doc-chunk` được nghiệm thu; không tạo CLI giả trong runbook.

## 8. Nguồn quyết định

[Proposal](TXT_Proposal.md) giải thích giả thuyết; [PLAN v3.3](PLAN.md) giao việc xây thuật toán; [handover](TXT_handover.md) nói phần đã có/chưa có. [Log](improvement_log.md) ghi D06 đính chính việc thu hẹp BEAR thành audit trong v3.2. L1/L4 cũ vẫn đóng đúng phạm vi; vai trò doc/chunk retrieval của BEAR được khôi phục.
