# TXT Proposal — Tối ưu bước chọn cuối trên baseline Pipeline 0,391

> **Phiên bản nghiên cứu:** 3.1 · **Cập nhật:** 20/10/2026. Backend hiện có vẫn là **2.0.0**; lần cập nhật này chỉ thay tài liệu.
>
> **Quyết định mới:** lấy **baseline 0,391** theo file [Pipeline 0,391 - Miro.html](<../Pipeline 0,391 - Miro.html>) do người dùng chỉ định. Giữ kết quả L1/L4 trên 0,4076 làm lịch sử; không chuyển delta/CI của chúng sang baseline mới. Đo nút thắt từ đúng ranking/cache và recipe 0,391; chỉ thử một thay đổi nhỏ, tối đa hai cấu hình.
>
> [PLAN v3.1](PLAN.md) quy định công việc M0–M3; [ghi nhận baseline 0,391](reports/BASELINE_0391_20261020.md) nêu nguồn và phần chưa xác nhận; [TXT_handover.md](TXT_handover.md) ghi trạng thái bàn giao; [improvement_log.md](improvement_log.md) giữ lịch sử. Proposal trước vòng này được giữ nguyên tại [bản lưu ngày 20/10](archive/TXT_Proposal_before_pivot_20261020.md).

## 1. Bằng chứng lịch sử và lý do đổi hướng

**Baseline hiện hành là0,391.** Hai ảnh người dùng cung cấp đã được chuyển thành [PIPELINE_0391.md](PIPELINE_0391.md):300VI+40ZH trước rerank →Qwen4B/P(Yes)/MaxP/p̂ →threshold để trung bình160doc/query. Đây là policy threshold, không phải fixed-k160. Chưa có threshold cụ thể, MaxP/calibration recipe, policy chunk nộp, run ID và full metrics; không suy full-body từ “Lấy full” hoặc lấy400 làm cap VI.

Ý tưởng cũ thêm tín hiệu khớp thuật ngữ trên toàn thân bài (L1) hoặc trên đoạn tốt nhất trong bài (L4) vào điểm xếp hạng. Phép thử đã áp dụng trực tiếp lên bài 0,4076 được báo trước khi đổi baseline. Chúng là bằng chứng để dừng cấu hình đó, không phải phép đo trên 0,391; không ưu tiên chạy lại chỉ vì thay mốc.

Kết quả do người dùng chuyển từ AI chạy thực nghiệm, được ghi nhận là **REPORTED**, chưa được chạy lại trong checkout này:

| λ | Δ Doc F2 của L1 | Δ Doc F2 của L4 |
|---:|---:|---:|
| 0 | 0 — đối chứng | 0 — đối chứng |
| 0,02 | +0,0003 | +0,0004 |
| 0,05 | +0,0002 | +0,0001 |
| 0,10 | +0,0003 | +0,0003 |
| 0,20 | −0,0021 | −0,0018 |
| 0,35 | −0,0085 | −0,0081 |

Phép thử giữ số doc từng câu `k_q`, số doc ZH và cách xuất **một chunk là toàn bộ body cho mỗi doc**; chỉ thay lựa chọn trong làn VI trên pool 400, dùng features `full_v1`. Mức phủ được báo là **100%/99,6%**; chưa có đủ chi tiết để gán hai số này cho từng mẫu số hoặc từng họ feature. Theo báo cáo, các CI95 chạm 0 hoặc nằm phía âm; chưa có cận CI và bảng từng câu trong checkout. Các chênh lệch trên là **điểm Doc F2 tuyệt đối**, không phải phần trăm tăng và không phải Δ FINAL.

Điểm tốt nhất của L4 chỉ tăng 0,0004, chưa có bằng chứng ổn định; tăng λ còn làm điểm giảm rõ. Điều này đủ để **dừng đầu tư cho cấu hình L1/L4 hiện tại**, nhưng không chứng minh mọi tín hiệu y sinh hoặc mọi cách dùng passage đều vô ích.

Hai thông tin khác giúp bỏ công việc lặp lại:

- **REPORTED:** đã chạy đủ 1.200 câu, tái dựng `w045` khớp 100% và quan sát trung bình 5,5 doc thay đổi mỗi câu. N0/N1 cũ không còn là điều kiện phải làm lại trước khi nghiên cứu tiếp.
- Bài 0,4076 dùng full body; thông tin này chỉ thuộc lịch sử, chưa xác nhận policy chunk của 0,391. Không mở lại chunk study chỉ vì đổi baseline. Routing từng thử ngày 07/10 có mức tăng oracle khoảng 1,5% trên phép đo khi đó; đây là bằng chứng giảm ưu tiên N4, không phải cận trên cho mọi hệ thống sau này.

Điểm **0,4076** là số của bài tốt nhất theo người dùng; chưa có đủ bộ Doc/Chunk/P/R và artifact để tự suy ra các thành phần. Kết quả cũ **FINAL 0,3445** và `w045_TF` **0,3442** được giữ làm lịch sử, không dùng thay mốc hiện tại 0,391. Thiếu bản sao artifact trong checkout không phủ nhận phép thử đã chạy ở máy vận hành.

## 2. Hai giả thuyết, chỉ chọn một phép thử

### H_count — Số doc xuất còn chưa tối ưu

L1/L4 trên 0,4076 thay cách chọn doc nhưng giữ `k_q`; chúng chưa trả lời chính sách count nào hợp với **baseline 0,391**. Trước phép thử mới, đọc lịch sử recipe 0,391 để tránh lặp một hướng đã tối ưu. Giả thuyết chỉ đổi count trên cùng ranking có cơ chế F2 rõ: Với số doc đúng `g`, tổng doc đúng `G` và số doc xuất `k`:

```text
F2 = 5 × g / (4 × G + k)
```

Nếu thêm một doc có xác suất đúng `p`, kỳ vọng Doc F2 tăng khi `p > F2/5`. Đây là lý do cần đo phần đuôi của ranking trước khi mặc định giữ một số doc. Công thức không tự cung cấp xác suất đúng và không chứng minh tăng count sẽ tăng điểm.

**Ưu tiên hướng này nếu** lịch sử pipeline 0,391 cho thấy chính sách count chung chưa được tối ưu, ranking sâu hơn đã có đủ điểm, định dạng và kích thước bài nộp cho phép. Chỉ thử tối đa hai mức count chung đã chốt trước cho toàn bộ câu; không chọn count riêng theo nhãn từng câu. Nếu count đã được thử đủ, ghi lại kết quả và bỏ qua, không lặp lại vì tài liệu cũ chưa ghi rõ.

### H_pool — Doc đúng bị chặn trước bước chọn cuối

Nếu count đã được tối ưu, kiểm tra tài liệu đúng bị bỏ sót nằm ở đâu: **pool nguồn truy hồi**, **pool đã có điểm rerank** hay **tập doc được xuất**. Pool 400 là scope L1/L4 trên 0,4076, không xác định cap của baseline 0,391. Gọi cap thật của pipeline mới là `P0`; chỉ chọn cap lớn hơn sau khi đọc cache/score mới. Tài liệu lịch sử đã có nguồn trả top-1.000 và rerank một phần pool.

Chẩn đoán các positive đã biết mà baseline chưa chọn:

| Vị trí | Ý nghĩa | Hành động |
|---|---|---|
| Đã có đủ điểm trong pool chọn hiện tại | Nút thắt nằm ở ranking hoặc count | Xem H_count nếu chưa thử; không quét λ L1/L4 tiếp. |
| Ngoài cổng chọn hiện tại, trong cache sâu và có đủ điểm | Có cơ sở thử mở cổng/pool | Cân nhắc tối đa hai cap lớn hơn `P0`;400→800/1.000 chỉ là ví dụ nếu pipeline mới thực sự có `P0=400` và đủ cache. |
| Có trong pool nguồn nhưng thiếu điểm rerank cần thiết | Không thể giữ nguyên recipe chỉ bằng mở cap | Ghi là chưa khả dụng trong phép thử cache; không bù điểm thiếu bằng 0. |
| Chưa thấy trong cache khả dụng | Chưa có phương án rẻ để đưa vào | Không mở vòng embedding/reranking lớn trong kế hoạch này. |

Thống kê tách VI và ZH. Phép thử chỉ mở làn VI không giải quyết positive bỏ sót ở ZH. Tỷ lệ từ tập positive đã biết chỉ mô tả tập quan sát, không phải recall hay oracle đầy đủ của tất cả doc đúng.

Nếu M1 chỉ thấy vấn đề bên trong pool và không có tín hiệu mới độc lập ngoài L1/L4, không ép tạo thêm một họ fusion. Các nguồn PRF/HyDE/subquery và thay đổi dense đã có lịch sử thực nghiệm; không coi chúng là hướng mới chỉ vì đang đổi kế hoạch.

## 3. Dùng nhãn BTC thế nào

**Được dùng nhãn BTC để đánh giá offline.** Không yêu cầu gán tay lại 593 câu. Dữ liệu người vận hành báo ở `data/lb/val.jsonl`; checkout này có `val.jsonl` tại thư mục gốc. Khi chạy phải dùng đúng bản đã được đối chiếu, không giả định hai đường dẫn chứa nội dung giống nhau.

Một doc đúng có thể không có chunk overlap ≥ 0,4 trong lần nộp, rồi bị quá trình dựng file ghi thành `not_gold`. Do đó **“có nhãn” chưa đủ để khẳng định mọi negative đều là phán quyết relevance ở mức doc**. Cần phân biệt positive đã xác nhận, negative thực sự ở mức doc, negative suy ra từ chunk và doc chưa biết nhãn.

Quan sát trực tiếp trên `val.jsonl` trong checkout: 593 câu; 205 dòng có `G != len(gold) + gold_unseen`; tổng phần thiếu là 305, tức khoảng **0,514 doc/câu**. Các số này phù hợp về quy mô với cảnh báo khoảng 0,5 doc/câu, nhưng không xác định doc nào sai nhãn hoặc chứng minh nguyên nhân. Mức **±0,0002** trong báo cáo là ước lượng chưa được kiểm độc lập, không phải cận sai số bảo đảm. Bootstrap theo câu cũng không tự sửa được lỗi nhãn có hệ thống.

Nếu giữ `k_q`, chênh lệch mỗi câu có dạng:

```text
ΔF2_q = 5 × Δg_q / (4 × G_q + k_q)
```

Nếu thử H_count thì `k_q` thay đổi: tính lại F2 của mỗi bên bằng công thức đầy đủ, không dùng công thức fixed-k. Không cần biết danh tính mọi doc đúng trong corpus nếu `G_q` và relevance của các doc dự đoán đã biết đúng. Khi doc thêm/bớt còn nhãn yếu hoặc chưa biết, phải báo coverage và phân tích độ nhạy tương ứng; không biến chúng thành negative để có một con số đầy đủ giả tạo.

Nhãn dùng để chấm và phân tích lỗi. Cấu hình production không được đọc `gold`, `not_gold` hay chọn doc/count/λ riêng cho từng câu theo đáp án. 593 câu đã được dùng trong quá trình chọn hướng, nên không mô tả chúng như một holdout hoàn toàn chưa nhìn thấy.

## 4. Phép thử M0–M3

| Bước | Việc cần làm | Kết quả tối thiểu và điểm dừng |
|---|---|---|
| **M0 — Dùng đúng cách chấm** | Dùng evaluator và đầu ra baseline 0,391 ở máy vận hành; xác nhận `G_q`, `k_q`, nguồn nhãn và cách xử lý doc thay đổi. Chỉ bổ sung adapter mỏng nếu thật sự thiếu. | Một ghi chú ngắn về metric/nhãn và đối chứng. Không làm lại toàn bộ N0/N1, không chờ gán tay 593 câu. Không lấy metric/hits/control của 0,4076 thay0,391 hoặc ép Doc F2 bằng scalar chưa rõ metric. |
| **M1 — Đo nút thắt** | Kiểm tra lịch sử count của bài tốt nhất; tách pool nguồn/rerank/tập xuất; đếm positive bỏ sót, rank, ngôn ngữ và cache/score thực sự có sẵn. | Một bảng headroom quan sát được. Chọn H_count, hoặc H_pool nếu có bằng chứng phù hợp; không có cơ hội khả dụng thì dừng. |
| **M2 — Một giả thuyết có đối chứng** | Baseline cộng tối đa hai biến thể của **cùng một cơ chế**. H_count giữ ranking, recipe và policy chunk của0,391, chỉ đổi count VI theo luật chung nếu có làn VI phù hợp. H_pool giữ recipe, calibration, `k_q`, quota và chunk policy mới, chỉ đổi cổng/pool có điểm sẵn. | Ghi rõ biến can thiệp và kết quả cả hai biến thể. Không thử cả hai họ rồi mở grid; không tạo điểm giả hoặc dùng nhãn chọn doc khi inference. |
| **M3 — Chọn hoặc dừng** | So sánh theo cùng câu: paired Δ Doc F2, CI, nhãn chưa chắc và độ nhạy; chấm Chunk/FINAL bằng scorer phù hợp nếu có. | Chọn tối đa một candidate có bằng chứng tốt để cân nhắc nộp; còn bất định hoặc không tăng thì giữ baseline0,391 và ghi kết quả âm tính. |

H_count chỉ mở khi recipe xác nhận làn VI; dùng đúng menu của PLAN: `c ∈ {0.85, 1.00, 1.15}`, `nVI'_q = round_half_up(c × nVI_q)`. Giữ danh sách và thứ tự ZH/non-VI; chọn prefix VI từ ranking cũ đã khớp baseline. Control `c=1.00` phải tái tạo đúng tập doc baseline0,391 và chunk policy tương ứng, không chỉ đúng count. Không đủ ranking hoặc vượt giới hạn thì bỏ candidate và ghi lý do, không clamp riêng từng câu. Không đồng thời thử chiến lược ZH mới. Với H_pool, cả count lẫn quota giữ nguyên từng câu. Hai hướng dùng cùng query universe, body, tie-break và cách chấm; chỉ chọn một hướng trong vòng này.

Nếu dữ liệu cần thiết không có ở checkout, dùng máy đang có baseline/cache; không biến việc sao chép toàn bộ artifact thành một vòng nghiên cứu riêng. Nếu cache thực sự thiếu ranking hoặc điểm cần thiết, ghi nhận điều kiện chưa đạt và dừng vòng nhỏ thay vì tự phát sinh một job GPU lớn.

## 5. Cách quyết định có nên nộp

Một mức tăng rất nhỏ, CI chạm 0 và không bền khi xét lại nhãn yếu chưa đủ lý do nộp. Báo cáo ít nhất: Δ trung bình theo câu, CI paired, số câu tăng/giảm, số doc thay đổi, tỷ lệ doc thay đổi có phán quyết đáng tin và kết quả độ nhạy. Nếu không đủ nhãn để kết luận, ghi “chưa xác định”, không ghi “đã tăng”.

Quy tắc quyết định theo PLAN §10.6 và ngân sách tối đa hai cấu hình phải được chốt trước M2. Nếu cân nhắc hai mức count hoặc cap, công khai cả hai kết quả. CI sau khi chọn cấu hình trên chính tập này không phải bảo đảm tăng điểm public hoặc private.

Policy chunk của0,391 chưa được xác nhận; không lấy full-body của0,4076 làm giả định. **Không đồng nhất Δ Doc F2 với Δ FINAL**. Chỉ báo FINAL mới khi có đủ cách chấm hoặc kết quả nộp thật. Giữ nguyên artifact baseline0,391 và các run lịch sử để quay lại đúng mốc.

## 6. Thời gian và phạm vi

Theo mốc public **31/10 do người dùng cung cấp**, lịch ưu tiên là:

- **20–22/10:** M0–M1, sau đó M2 nếu có cơ sở; mục tiêu khoảng nửa buổi làm rõ cách chấm và một buổi máy cho phép thử từ cache.
- **23/10:** quyết định tiếp tục hay dừng dựa trên số đo. Không kéo dài nhánh âm tính chỉ vì còn ngày.
- **24–30/10:** chỉ xử lý candidate có triển vọng và kiểm tra output thực tế; nếu không có, giữ baseline0,391 và hoàn tất bàn giao.
- **31/10:** mốc public dự kiến; giờ chốt và quy định theo thông báo BTC mà người vận hành đang có.

Không ưu tiên vòng này: mở lại L1/L4, N0/N1 đã có đáp án, chunk study chưa có lỗi cụ thể từ recipe mới, routing chưa có tín hiệu mới, embedding lại corpus hoặc sweep trọng số rộng. Ghi chép chỉ cần một cấu hình, một bảng kết quả và một mục log cho mỗi phép thử thực tế.

## 7. Ranh giới triển khai và lịch sử

Runner BEAR 2.0.0 hiện có triển khai hợp đồng nghiên cứu cũ và fixtures; một số nhánh giả định top-200, nhãn reviewed hoặc allocation cũ. Chúng **chưa tự động tương thích** với `k_q`, chunk policy và exporter của baseline0,391 khi chưa đối chiếu recipe. Vòng mới ưu tiên evaluator/exporter của đúng pipeline0,391 ở máy vận hành; chỉ sửa adapter hoặc code khi có yêu cầu triển khai cụ thể. Không gọi exporter cũ rồi coi đó là bản tái tạo bài tốt nhất.

Không sửa corpus, offsets, calibration hoặc artifact baseline để khớp ý tưởng mới. Kết quả thực nghiệm bên ngoài ghi **REPORTED**; điều đã xem trực tiếp trong repo ghi **ARTIFACT_OBSERVED**; giả thuyết và phép thử chưa chạy ghi **PROPOSED**.

Đặc tả BEAR trước đây, H1–H6, N0–N5 và hợp đồng kỹ thuật được lưu trong [proposal trước pivot](archive/TXT_Proposal_before_pivot_20261020.md) và [báo cáo triển khai v2](reports/next_round/V2_IMPLEMENTATION.md). Chúng phục vụ tra lịch sử và hiểu mã hiện có; công việc tiếp theo theo M0–M3 trong [PLAN hiện hành](PLAN.md).
