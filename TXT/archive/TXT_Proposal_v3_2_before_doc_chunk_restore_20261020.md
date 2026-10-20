# TXT Proposal — BEAR trên baseline Pipeline 0,391

> **Phiên bản nghiên cứu:** 3.2 · **Cập nhật:** 20/10/2026. Backend BEAR vẫn là **2.0.0**. Đây là cập nhật kế hoạch và tài liệu, chưa phải kết quả tăng điểm hoặc runner mới.
>
> **Baseline do người dùng chọn:** **0,391**. **Ý tưởng được người dùng xác nhận:** BEAR hiện có — dùng bằng chứng y sinh để hiểu và xử lý phần lỗi còn sót. Vòng này ưu tiên một phép thử **threshold cuối** từ cache; BEAR cung cấp phân tích lỗi nhỏ, không chặn phép thử và không mở lại L1/L4.
>
> [PLAN v3.2](PLAN.md) quy định việc M0–M3; [PIPELINE_0391.md](PIPELINE_0391.md) chép hai ảnh Miro; [đặc tả máy đọc](specs/pipeline_0391.json) phân biệt giá trị đã biết/chưa biết, **không phải config chạy**. [Handover](TXT_handover.md) và [log](improvement_log.md) ghi trạng thái và lịch sử.

## 1. Baseline và ý tưởng của người dùng gặp nhau ở đâu

Pipeline được đọc từ ảnh, chưa đối chiếu toàn bộ với code/run:

```text
VI: BM25F + dense đầu bài + dense chunking
    mỗi nguồn top 1000 → gộp khoảng 2200 doc/query → RRF k=60 → top 300 VI
ZH: BGE-M3 + Qwen3-8B, query VI gốc và query dịch ZH
    RRF weights 1 / 1 / 0.3 / 0.3 → 400 doc → top 40 ZH
300 VI + 40 ZH → 340 ứng viên trước rerank
    → Qwen reranker 4B → P(Yes) → MaxP → p̂ → threshold cuối
    → mục tiêu trung bình 160 doc/query theo ảnh
```

**300/40 là quota ứng viên, không phải quota đầu ra cuối.** 400 thuộc bước trung gian ZH; không phải cap VI. 160 là số doc trung bình sau threshold, không phải top-k cố định. Chưa có công thức MaxP, cách tính `p̂`, threshold thực, phạm vi theo query hoặc policy chunk nộp; không suy full-body từ chữ “Lấy full”. Model giữ nguyên cách ghi trong ảnh; checkpoint và vai trò nhãn “Embed - Qwen 3.5-9B” còn cần đối chiếu. Xem [bản đọc pipeline](PIPELINE_0391.md).

BEAR đề xuất bảo toàn thuật ngữ/identifier, xem bằng chứng cùng nằm trong một đoạn hay rải khắp bài, và kiểm tra liệu evidence giúp chọn giữa các nguồn lexical/dense. Khi ghép với baseline mới, cần nhận ra những phần đã có:

| Phần ý tưởng | Baseline đã có | Cách dùng tiếp trong vòng này |
|---|---|---|
| Khớp thuật ngữ y sinh | BM25F nhiều trường và reranker | Giữ matching bảo toàn identifier để phân tích lỗi; không cộng coverage mặc định. |
| Bằng chứng ở cấp đoạn | Dense chunking và bước MaxP sau reranker | Kiểm tra lỗi cụ thể trước khi thêm tín hiệu đoạn. Không đồng nhất aggregation dense chunk với MaxP khi chưa biết công thức. |
| Tận dụng lexical và semantic | Fusion các nguồn, rồi Qwen reranker | Giữ nguyên làm control; chưa mở adaptive fusion/router. |
| Số doc phù hợp với mỗi câu | Chọn bằng threshold trên `p̂` | Thử threshold toàn cục nếu recipe xác nhận đúng cơ chế và lịch sử chưa thử đủ. |
| Tránh đúng từ nhưng sai ý | Reranker có thể đã xử lý một phần; mức còn lại chưa đo | Phân tích identifier, phủ định, quan hệ và đối tượng trên mẫu nhỏ; không tự tạo nhãn vàng. |

BEAR giữ vai trò tìm **tín hiệu bổ sung có thể kiểm chứng**, thay vì mặc định mọi tín hiệu y sinh đều phải cộng vào điểm baseline.

## 2. Bằng chứng đã có và giới hạn kết luận

**Baseline làm việc là 0,391 theo người dùng.** Chưa có bộ Doc/Chunk/P/R, run ID và scoring artifact đủ để phân rã con số này. Không dùng scalar 0,391 làm Doc F2 hoặc tự suy metric thành phần. Việc đổi mốc từ 0,4076 chưa phải phép so regression cùng điều kiện. Xem [ghi nhận baseline](reports/BASELINE_0391_20261020.md).

L1/L4 đã được nguồn chạy thí nghiệm báo trên bài **0,4076**: chỉ thay lựa chọn VI trong pool 400, giữ `k_q`, số doc ZH và một chunk toàn body/doc. Best Δ Doc F2 của L1 là **+0,0003**, L4 là **+0,0004**; các CI95 được báo chạm 0 hoặc âm. Tăng λ làm point estimate giảm rõ. Coverage được báo **100% / 99,6%**, nhưng chưa có mẫu số chi tiết hoặc cận CI trong checkout. Bảng đầy đủ tại [báo cáo L1/L4](reports/L1_L4_20261020.md).

**Không nộp các cấu hình đó, đóng tuning L1/L4 hiện tại.** Không chuyển delta/CI hoặc full-body policy sang 0,391, không chạy lại chỉ vì đổi baseline. Kết quả này chưa bác bỏ mọi cách dùng identifier, quan hệ hoặc ý định; cũng chưa cho lý do mở grid evidence khác ngay.

Các việc đã có đáp án được giữ lại để tránh làm lại:

- **REPORTED:** đã chạy đủ 1.200 câu, dựng lại `w045` khớp 100%, bài thay trung bình 5,5 doc/câu. N0/N1 cũ không còn là prerequisite phải chạy lại.
- Routing từng có oracle tăng khoảng 1,5% trong phép đo ngày 07/10. Đây là lý do giảm ưu tiên routing, chưa phải cận trên cho mọi hệ thống về sau.
- Kết quả **0,3445**, `w045_TF` **0,3442**, bài **0,4076** và phần mềm 2.0.0 được giữ trong lịch sử; không dùng thay recipe hiện tại.

Thiếu bản sao artifact ở checkout không phủ nhận kết quả bên ngoài. Ghi rõ phần thiếu, không biến việc chép lại artifact thành vòng thủ tục trước khi đo.

## 3. H_tau — Threshold cuối còn dư địa

Ảnh cho thấy baseline đã chọn doc bằng threshold trên `p̂`. Phép thử gần với cơ chế gốc nhất là thay **threshold cuối**, giữ nguyên cách tính điểm và ứng viên.

Trước khi mở phép thử, đọc recipe và lịch sử tuning để xác nhận:

1. Có một threshold chung `τ0`, hoặc tham số chung tương đương được code định nghĩa rõ. Nếu là policy theo query/ngôn ngữ hoặc phạm vi còn chưa rõ, không tự đổi thành threshold chung rồi gọi đó là cùng control.
2. Cache điểm cuối `p̂` tái tạo được tập doc baseline với đúng phép so sánh, ties và xử lý thiếu điểm. Không refit calibration hoặc đổi loại điểm để ép khớp.
3. Threshold chưa được thử đủ trong lịch sử. Nếu đã tối ưu, ghi lại và bỏ qua; không lặp lại vì tài liệu thiếu một bảng.

Nếu đủ điều kiện, chỉ thử **một họ H_tau**, control `τ0` và tối đa hai threshold mới. Đặt `K̄0` là số doc trung bình thực tế của control trên query universe đã chốt. Từ **cache điểm không đọc nhãn**, chọn trước:

| Candidate | Hướng threshold | Mục tiêu số doc trung bình **tổng VI + ZH** |
|---|---|---:|
| Control | `τ0` thực của baseline | `K̄0` đo từ control |
| Bớt doc | Cao hơn `τ0` | Xấp xỉ `0,85 × K̄0` |
| Thêm doc | Thấp hơn `τ0` | Xấp xỉ `1,15 × K̄0` |

Hai tỷ lệ là menu đề xuất, chưa phải mức tối ưu. **Không thay `K̄0` bằng 160** trước khi đo. Với ties/điểm rời rạc, chọn mức khả thi gần mục tiêu theo quy tắc chốt trước, ghi count đạt được; không mở thêm candidate để đuổi đúng count. Candidate không đổi output hoặc không hợp lệ được ghi bỏ qua, không tự mở rộng menu. Không chọn threshold riêng từng câu theo đáp án.

Giữ nguyên corpus/query snapshot; retrieval và dịch; quota ứng viên 300VI/40ZH theo recipe thực đã xác nhận; RRF; reranker; MaxP; cách tính `p̂`; ties; policy chunk và exporter tương ứng. Chỉ threshold cuối thay đổi. **Số VI/ZH cuối có thể đổi**; không thêm ràng buộc giữ số ZH hoặc nhân count riêng VI. Kiểm giới hạn hợp lệ của submission trước khi chạy.

Không cần mặc định `p̂` đã calibrated để thử threshold trên điểm cố định. Với số doc đúng `g`, tổng doc đúng `G` và số doc xuất `k`, Doc F2 mỗi câu có dạng:

```text
F2_q = 5 × g_q / (4 × G_q + k_q)
```

Công thức giải thích vì sao phải chấm cả số doc đúng và count sau thay ngưỡng. Nó chưa chứng minh ngưỡng cao hoặc thấp sẽ tốt hơn.

## 4. BEAR trong vòng này — Phân tích lỗi nhỏ, không sửa điểm

Trong M1, lấy mẫu nhỏ các ca sát ngưỡng theo quy tắc dựa trên score đã chốt. Giới hạn trước thời gian hoặc số mẫu; không yêu cầu gán tay lại 593 câu hoặc đợi model extraction mới. Chưa có text/mapping đáng tin thì ghi `unknown` và tiếp tục phần threshold có đủ dữ liệu.

| Nhóm cần tìm | Ví dụ cần phân biệt | Evidence có thể ghi |
|---|---|---|
| Identifier/biến thể | BRCA1 và BRCA2; hai biến thể khác nhau | Span nguyên văn query/doc, identifier khớp/khác, nguồn mapping. |
| Phủ định | Có và không có một điều kiện | Span phủ định; phạm vi chưa rõ ghi `unknown`. |
| Quan hệ/ý định | Chỉ định/chống chỉ định; chẩn đoán/điều trị | Span hỗ trợ nhận xét và nhóm lỗi phân tích. |
| Đối tượng | Trẻ em/người lớn; thai kỳ; phân nhóm bệnh | Span điều kiện ở query/doc; phần thiếu chưa đồng nghĩa không liên quan. |
| Đồng xuất hiện | Từ khóa cùng đoạn hay rải các đoạn | Đoạn/offset sẵn có và availability; không tạo lại corpus/chunk. |

Một ghi chú gồm query/doc ID, span/chunk reference, cờ hoặc nhận xét và mức chưa chắc là đủ. Tách **relevance từ BTC** với **nhãn mô tả lỗi do phân tích**. Exact match, cosine, cờ phủ định, nhận xét AI hoặc `p̂` đều không phải nhãn vàng. Chữ viết hoa/độ hiếm chưa chứng minh entity type hay criticality; verified alias cần nguồn đã kiểm.

Mục đích là tìm evidence có thể bổ sung ngoài baseline, không chứng minh giả thuyết từ vài ví dụ thuận mắt. Không dùng cờ này hard-filter, cộng điểm hoặc định tuyến trong H_tau; không suy cùng thực thể đã trả lời đúng câu hỏi y khoa.

Sau vòng hiện tại, chỉ cân nhắc một pilot **khác L1/L4** nếu một loại lỗi lặp lại, có cách đo đáng tin và có tín hiệu khả dụng mà rank/score hiện tại chưa thể hiện. Pilot chỉ thay **một feature/cơ chế** với matched control riêng; đây là đề xuất tương lai, không mở kèm H_tau. Adaptive fusion, sparse mới, dictionary expansion và model mới giữ backlog có điều kiện.

## 5. Nhãn BTC và chấm thay đổi count

**Được dùng nhãn BTC có nguồn rõ để đánh giá offline.** Không bắt buộc thay bằng nhãn người gán tay. Người chạy báo `data/lb/val.jsonl`; checkout có [val.jsonl](../val.jsonl) ở root. Dùng snapshot đã đối chiếu, không mặc định hai đường dẫn là cùng file.

Tách positive đã xác nhận, negative trực tiếp mức doc, negative suy từ chunk và unknown. Doc vàng không có chunk overlap ≥0,4 có thể đã bị quá trình dựng file ghi thành `not_gold`; không coi mọi `not_gold` là âm đáng tin. Quan sát local: **593 câu**, **205 dòng** thiếu trong đẳng thức `G = len(gold) + gold_unseen`; tổng thiếu **305**, trung bình **0,514 doc/câu**. Chưa xác định doc nào sai hoặc chứng minh nguyên nhân. Ước lượng **±0,0002** được nguồn báo chưa phải bound bảo đảm; bootstrap không tự sửa lỗi nhãn hệ thống.

H_tau làm `k_q` đổi, nên chấm đầy đủ cả control/candidate:

```text
ΔF2_q = 5 × g1_q / (4 × G_q + k1_q)
       − 5 × g0_q / (4 × G_q + k0_q)
```

Không dùng công thức fixed-k `5Δg/(4G+k)`. Nếu `g1 = g0 + added_hits − removed_hits` mà `g0` chưa chắc, bất định của **doc giữ nguyên** cũng ảnh hưởng delta do hai mẫu số khác nhau. Sensitivity phải xét nguồn nhãn của control và candidate, thay vì chỉ kiểm doc thêm/bớt rồi gọi delta chính xác.

Không cần danh tính mọi doc đúng trong corpus nếu `G_q` và relevance của doc dự đoán đã biết đúng. Nhãn yếu/unknown chưa giải quyết thì báo coverage và khoảng kết quả theo giả định rõ; không tự gán âm. Giữ cùng query universe; không bỏ riêng câu candidate khó chấm.

593 câu đã dùng trong chọn hướng, không gọi chúng là holdout chưa nhìn thấy. Nhãn dùng chấm và phân tích; config suy luận không đọc `gold`/`not_gold` hoặc chọn doc/threshold theo nhãn từng câu.

## 6. M0–M3 và giới hạn vòng thử

| Bước | Việc cần làm | Kết quả tối thiểu |
|---|---|---|
| **M0 — Nối đúng control** | Đọc recipe/scorer/cache 0,391; xác nhận metric, phạm vi threshold, phép so sánh/ties và replay `τ0` từ `p̂`. | Ghi chú control và phần chưa biết. Dùng máy có artifact; không chạy lại N0/N1 hoặc ép scalar 0,391 thành Doc F2. |
| **M1 — Kiểm tra dư địa** | Xem lịch sử tuning ngưỡng, count thực và khả năng thay ngưỡng từ cache. Audit BEAR nhỏ sát ngưỡng nếu text sẵn. | Chọn ≤2 threshold từ phân phối score không đọc nhãn, hoặc ghi chưa đủ điều kiện/đã thử và dừng. Audit không là prerequisite độc lập. |
| **M2 — Chỉ H_tau** | Chấm control và tối đa hai candidate đã khóa; giữ retrieval/rerank/MaxP/`p̂`/chunks. | Một bảng metric, count VI/ZH/tổng, doc đổi, độ phủ nhãn và chi phí. Không thêm count VI, mở pool hoặc evidence grid. |
| **M3 — Chọn hoặc dừng** | So paired Δ Doc F2, CI, số câu tăng/giảm và sensitivity; chấm Chunk/FINAL bằng scorer phù hợp nếu có. | Tối đa một candidate đủ bằng chứng để cân nhắc nộp; chưa rõ/không tăng thì giữ baseline và ghi kết quả âm tính. |

CI sau chọn cấu hình trên cùng tập mô tả bất định, không bảo đảm tăng public/private. Quy tắc promote và ngân sách theo [PLAN](PLAN.md): cần bằng chứng tăng ổn định, sensitivity không đảo hướng và output hợp lệ; không nộp chỉ vì điểm nhích rất nhỏ.

**H_pool chỉ là backlog.** Sau này nếu thấy positive bị chặn trước rerank, tách đúng pool nguồn VI khoảng 2.200, cổng VI 300, cổng ZH 40 và pool ghép 340. Mở cổng thường cần điểm Qwen chưa có; cache retrieval sâu chưa đồng nghĩa có rerank score. Không bù điểm thiếu bằng 0 rồi gọi là cùng recipe. Không thử H_pool trong vòng H_tau hoặc tự chuyển khi H_tau âm tính; cần quyết định sau kết quả.

Không mở chunk study chỉ vì chưa biết chunk policy; đối chiếu recipe để giữ đúng baseline. Không đồng nhất Δ Doc F2 với Δ FINAL. Thiếu scorer/metric phù hợp thì báo đúng phạm vi, không suy thành điểm nộp mới.

## 7. Vì sao bản này tốt hơn bản trước

| Trước đây | Sau cập nhật | Lợi ích thực tế |
|---|---|---|
| Nhân count riêng VI, giữ ZH cuối | Đổi đúng threshold cuối khi recipe xác nhận | Gắn phép thử với pipeline; không áp quota đầu vào thành quota đầu ra. |
| Dễ coi dense chunk/MaxP là phần cần thêm | Ghi rõ baseline đã có | Tìm tín hiệu còn thiếu thay vì triển khai lại. |
| BEAR chủ yếu cộng coverage hoặc gate | Tìm lỗi identifier/quan hệ/phủ định/đối tượng trước | Giữ ý tưởng y sinh nhưng yêu cầu lỗi và tín hiệu cụ thể; không mở lại nhánh âm tính. |
| Có thể thử count và pool hoặc thêm thủ tục | Một họ H_tau, tối đa hai cấu hình; audit nhỏ không chặn | Dễ đo từ cache và dừng nếu không tăng. |
| Sensitivity chỉ nhìn doc thay đổi | Xét bất định `g0` khi count thay đổi | Tránh độ chính xác giả từ negative yếu và mẫu số khác nhau. |

Đây là cải tiến về cách đặt phép thử, hiểu baseline và bàn giao. **Chưa có benchmark chứng minh bản cập nhật tăng điểm.** Agent sau phải phân biệt thông tin ảnh, kết quả được báo và thiết kế chưa chạy.

## 8. Thời gian, triển khai và lịch sử

Theo mốc public **31/10 do người dùng cung cấp**, ưu tiên vòng ngắn: khoảng nửa buổi xác nhận control/cách chấm và một buổi máy cho H_tau nếu cache đủ; quyết định ngay khi có số. Mốc thời gian không thay điều kiện dữ liệu hoặc thông báo BTC mà người vận hành đang có. Không kéo dài nhánh âm tính chỉ vì còn ngày.

Runner BEAR 2.0.0 phục vụ hợp đồng cũ; một số nhánh giả định k200, manual-reviewed qrels hoặc allocation B00. Chưa thể nói chúng chạy thẳng recipe 0,391. Ưu tiên evaluator/exporter và cache đúng pipeline; chỉ bổ sung adapter nhỏ khi cần. JSON đặc tả là tài liệu máy đọc, không phải runner/config đã kiểm trên dữ liệu thật. Lượt cập nhật này không sửa model, corpus, offsets, calibration hay artifact baseline; không chạy benchmark hoặc submission.

Kết quả bên ngoài ghi **REPORTED**; phần đã đọc trực tiếp ghi **ARTIFACT_OBSERVED**; thiết kế chưa chạy ghi **PROPOSED**. Không tạo metadata hoặc nhãn giả để đổi trạng thái thành “verified”. Một config, một bảng kết quả và một mục log là đủ cho phép thử thực tế.

Lịch sử H1–H6, N0–N5 và hợp đồng kỹ thuật nằm ở [proposal trước pivot](archive/TXT_Proposal_before_pivot_20261020.md), [thiết kế BEAR gốc](BIOMEDICAL_ADAPTIVE_RETRIEVAL_AGENT_PLAN.md) và [nghiệm thu code v2](reports/next_round/V2_IMPLEMENTATION.md). Dùng M0–M3 của [PLAN hiện hành](PLAN.md) để giao việc mới.
