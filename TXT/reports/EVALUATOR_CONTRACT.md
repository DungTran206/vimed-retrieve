# Hợp đồng đánh giá — cập nhật 20/10/2026

Áp dụng cho [PLAN v3.3](../PLAN.md). Baseline hiện hành là **Pipeline 0,391**, xem [hồ sơ baseline](BASELINE_0391_20261020.md) và [bản đọc từ ảnh](../PIPELINE_0391.md). Điểm 0.391 chưa xác nhận tên metric. A0 nối đúng prediction/candidates/scores/chunks và scorer của control; không lấy metric/hits0,4076 thay0,391. [Thuật toán BEAR](../BEAR_ALGORITHM.md) được đánh giá riêng doc, chunk và joint.

## 1. Nguồn nhãn được chấp nhận

Nhãn BTC có nguồn rõ được dùng đánh giá offline; không bắt buộc chuyển thành nhãn người gán tay. Không giả `annotator/adjudication=reviewed` để ép file vào schema runner cũ.

Người vận hành báo `data/lb/val.jsonl`; checkout có [val.jsonl](../../val.jsonl), chưa xác nhận hai file cùng bytes/snapshot. Các trường: `id/query/G/gold/not_gold/gold_unseen`.

| Trạng thái doc | Cách dùng |
|---|---|
| Positive đã biết trong gold | Đánh giá/chẩn đoán theo nguồn thực có |
| Negative là doc judgment trực tiếp, đã xác minh nghĩa | Có thể dùng như doc negative |
| not_gold suy từ chunk không overlap ≥ 0.4 | Weak negative; có thể là gold doc, cần sensitivity |
| ID không có judgment | Unknown; không tự gán 0 |
| gold_unseen | Số đếm, không cung cấp danh tính doc để chọn/loại |

Local val: 593 qid, 205 câu có `G−len(gold)−gold_unseen>0`, tổng 305. Đây là kiểm số đếm, không định danh false negatives hoặc chứng minh cơ chế tạo file. Ước lượng sai lệch ±0.0002 do người chạy báo chưa phải bound/CI.

## 2. Macro Doc F2 khi số doc thay đổi

Với mỗi query, `F2_q=5*g_q/(4*G_q+k_q)`; macro là mean theo đúng query universe và empty-gold policy của control. Không tính F2 từ mean P/mean R. `k_q` là số doc được xuất thực của query đó; không ép bằng 160 hoặc 200.

Nếu biết tổng `G_q` thật và judgments đầy đủ cho docs dự đoán, có thể tính F2 chính xác dù không có ID mọi gold ngoài prediction. Nếu chỉ biết positive list không đầy đủ, không coi phần thiếu là negative để tuyên bố exact F2.

Nếu một phép thử đổi k (count/threshold hoặc joint không cố định budget), Đặt `D0=4*G+k0`, `D1=4*G+k1`, `Δg=g1−g0` cho cùng query:

```text
ΔF2 = 5 * (g1/D1 − g0/D0)
     = 5 * [g0*(1/D1 − 1/D0) + Δg/D1]
```

Do đó, **chỉ biết nhãn các doc thêm/bớt chưa đủ** nếu `g0` chưa chắc chắn: thay mẫu số làm cả hits trên những doc giữ nguyên ảnh hưởng ΔF2. Cần hits control đáng tin từ đúng scoring artifact hoặc judgments đủ cho hai prediction sets. Nếu không, phải đưa bất định của `g0`, kể cả doc giữ nguyên có weak/unknown label, vào sensitivity. Công thức fixed-k `5*Δg/(4G+k)` chỉ dùng khi thật sự `k1=k0`.

## 3. Incomplete judgments và sensitivity

Lưu coverage true judgments, weak negatives và unknown cho cả control/candidate; tách changed docs để xem đóng góp. Point estimate dùng file val có noise phải gọi là estimate. Tái dùng per-query hits control chỉ khi đã liên kết đúng baseline 0.391, query universe và snapshot.

Sensitivity xét weak-negative/unknown thực ra là positive trong cả doc thay đổi và doc giữ nguyên. Chỉ giới hạn số lỗi/query khi có bound có chứng cứ cho cùng snapshot; không mặc định tổng 305 hoặc ±0.0002 là ngân sách lỗi. Bootstrap đo biến động query, không sửa label bias.

Không đủ judgments/bound thì kết luận `inconclusive` cho phần cần chúng; vẫn chạy được chẩn đoán known positives và audit BEAR. Review bổ sung chỉ tập doc quyết định kết quả nếu cần, không buộc gán lại toàn 593 câu. Cờ BEAR về identifier, negation, relation, dose, population hoặc bằng chứng ở nhiều đoạn không phải nhãn relevance; không dùng như gold/hard filter.

## 4. Ba tầng metric

| Tầng | Được báo | Giới hạn |
|---|---|---|
| Legacy proxy | Smoke/substring hoặc token overlap | Không gọi official F2/LCS |
| Local diagnostic | Known-positive coverage, paired Doc F2 estimate, token-LCS có tên tokenizer | Không biến incomplete/noisy labels thành exact ground truth |
| Official artifact / reproduction | Metric đọc từ artifact có provenance, hoặc candidate chấm bằng scorer đúng semantics | Parse một archive không chứng minh đã tái lập scorer candidate |

Local passage match: cùng qid/doc và `LCS(pred_tokens,gold_tokens)/len(gold_tokens)≥0.40`, giữ thứ tự token. `local_whitespace_lcs_v1` không phải official tokenizer.

Một chunk toàn body/doc không làm Chunk F2 mặc nhiên bằng Doc F2. Đây là policy đã được báo của bài 0.4076; policy chunk của 0.391 chưa xác nhận. Chưa có scorer Chunk/FINAL đúng thì ghi null, không suy FINAL từ ΔDoc. Archive có Doc F2 0.407343... chưa liên kết với bài 0.4076 hoặc baseline 0.391.

## 5. Ablation doc/chunk và quyết định

B0baseline, D1BEARdoc với chunk policy nền, C1BEARchunk với doc set/order/slots/token budget baseline, DC1joint. Tối đa3candidate mới và1control cho một pilot đã khóa, không thêm weight grids. D1 cố định k thực từng query để cô lập tập doc; đổi order cùng tập không tăng DocF2. D1-VI phải ghi scope và fallback non-VI.

C1 phải nối selected chunk refs tới text/offset thực xuất. Không quy gain do thêm slots/token cho selector. Nếu full-body duy nhất không có lựa chọn dưới cùng budget thì ghi scope không có headroom; không suy điều này từ ảnh0,391 hoặc bài0,4076.

Chấm riêng DocF2/ChunkF2 và joint/FINAL đúng evaluator; local LCS chỉ diagnostic khi chưa có tokenizer/spec chính thức. Evidence features/support/conflict được phép tham gia score BEAR trong pilot nhưng không được coi là gold hoặc phán quyết y khoa đã xác nhận.

Threshold study v3.2 là control phụ/operating-point tuning, không là kế hoạch chính hoặc tiêu chí hoàn tất BEAR. Khi score thay thang, không dùngτ0 gốc máy móc. Không chọn doc/chunk/threshold riêng query bằng gold.

Paired CI/sensitivity theo cùng query universe;593câu đã khai thác không là holdout mới. Giữ baseline nếu không có gain đáng tin, metric coverage hoặc integrity. L1/L4 cũ vẫn đóng đúng scope. Code2.0/release200 chưa mặc nhiên triển khai đặc tả mới; lượt tài liệu này chưa có implementation hoặc benchmark mới.

