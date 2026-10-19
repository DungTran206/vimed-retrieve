# TXT Proposal — Biomedical Evidence-Aware Retrieval

> **Mục đích:** đặc tả nghiên cứu và kế hoạch thực nghiệm để cải tiến hệ thống ViMed Retrieval bằng bằng chứng thuật ngữ y khoa, lựa chọn ứng viên và fusion thích ứng theo truy vấn.
>
> **Phiên bản:** 1.0 · **Ngày:** 19/10/2026 · **Ngôn ngữ:** tiếng Việt.
>
> **Đối tượng đọc:** người nghiên cứu, người triển khai và AI coding agent.
>
> **Trạng thái:** đề xuất chưa được benchmark. Tài liệu này không tuyên bố BEAR đã vượt baseline và không phải báo cáo kết quả thực nghiệm.
>
> **Phạm vi thay đổi của lần soạn tài liệu:** chỉ tạo proposal; các bước sửa code, tải dữ liệu, chạy GPU và xuất submission dưới đây là công việc trong kế hoạch.

## Mục lục

1. [Cách đọc và hợp đồng làm việc](#1-cách-đọc-và-hợp-đồng-làm-việc)
2. [Kết luận thiết kế và câu hỏi nghiên cứu](#2-kết-luận-thiết-kế-và-câu-hỏi-nghiên-cứu)
3. [Hiện trạng và bằng chứng đang có](#3-hiện-trạng-và-bằng-chứng-đang-có)
4. [Bài toán, ký hiệu và metric](#4-bài-toán-ký-hiệu-và-metric)
5. [Ba phạm vi can thiệp và candidate pool](#5-ba-phạm-vi-can-thiệp-và-candidate-pool)
6. [Kiến trúc tích hợp](#6-kiến-trúc-tích-hợp)
7. [Biomedical Evidence Engine](#7-biomedical-evidence-engine)
8. [Fixed và adaptive residual fusion](#8-fixed-và-adaptive-residual-fusion)
9. [Nhánh sparse và các mở rộng có điều kiện](#9-nhánh-sparse-và-các-mở-rộng-có-điều-kiện)
10. [Chunk selection và allocation](#10-chunk-selection-và-allocation)
11. [Thiết kế nhãn và đánh giá](#11-thiết-kế-nhãn-và-đánh-giá)
12. [Ma trận thực nghiệm](#12-ma-trận-thực-nghiệm)
13. [Lộ trình triển khai và điều kiện chuyển bước](#13-lộ-trình-triển-khai-và-điều-kiện-chuyển-bước)
14. [Hợp đồng dữ liệu và cấu trúc mã nguồn](#14-hợp-đồng-dữ-liệu-và-cấu-trúc-mã-nguồn)
15. [Cấu hình, thuật toán và lệnh dự kiến](#15-cấu-hình-thuật-toán-và-lệnh-dự-kiến)
16. [Kiểm thử, tài nguyên và vận hành](#16-kiểm-thử-tài-nguyên-và-vận-hành)
17. [Quy tắc quyết định và báo cáo](#17-quy-tắc-quyết-định-và-báo-cáo)
18. [Checklist giao việc cho AI agent](#18-checklist-giao-việc-cho-ai-agent)
19. [Nguồn và giới hạn của proposal](#19-nguồn-và-giới-hạn-của-proposal)

---

## 1. Cách đọc và hợp đồng làm việc

### 1.1. Lộ trình đọc

- **Người quyết định hướng nghiên cứu:** đọc mục 2–5, 11–13 và 17.
- **Người triển khai:** đọc toàn bộ, đặc biệt các hợp đồng tại mục 7–10 và 14–16.
- **AI agent lần đầu nhận việc:** thực hiện checklist mục 18; không suy diễn rằng các module, CLI hoặc artifact được đề xuất đã tồn tại.

### 1.2. Bốn mức độ chứng cứ

| Nhãn | Ý nghĩa |
|---|---|
| **CODE-VERIFIED** | Đã đối chiếu mã nguồn hoặc cấu trúc checkout khi soạn tài liệu. Không đồng nghĩa đã chạy trên dữ liệu thật. |
| **REPORTED** | Kết quả hoặc quy định được tài liệu dự án ghi nhận; chưa xác nhận độc lập bằng artifact hay đặc tả gốc. |
| **PROPOSED** | Thiết kế, cấu hình hoặc quy trình mới. Phải thực nghiệm trước khi sử dụng mặc định. |
| **UNRESOLVED** | Thiếu dữ liệu, thiếu nguồn gốc hoặc tồn tại mâu thuẫn cần giải quyết. |

Mọi báo cáo sau này phải giữ sự phân biệt này. Một unit test xanh không chứng minh chất lượng truy hồi tăng; một điểm lexical cao không phải nhãn relevance.

### 1.3. Quy tắc bắt buộc cho người và agent

1. Giữ nguyên artifact baseline. Không refit calibration, ghi đè corpus, clean lại body hoặc rechunk khi đang tái lập.
2. Kiểm tra schema thật trước khi code adapter. Ví dụ trong proposal chỉ là hợp đồng đích.
3. Tính năng mới có chế độ tắt hoàn toàn; chế độ tắt phải đi qua đường baseline đã khóa.
4. Không dùng điểm leaderboard tổng hợp, p(gold), cosine hay Qwen confidence làm nhãn vàng cho gate.
5. Không chạy lại crawl, embedding toàn corpus hoặc rerank lớn nếu artifact hiện có đủ trả lời câu hỏi thực nghiệm.
6. Mỗi experiment chỉ thay một cơ chế chính; giữ đối chứng có cùng pool, đầu vào và chính sách đánh giá.
7. Ghi đủ config, hash, seed, version, chi phí, missing data và kết quả âm tính.
8. Không tự động nâng baseline hoặc nộp leaderboard chỉ vì test kỹ thuật đã qua.
9. Không coi nội dung lịch sử trong README/METHODS/docstring là trạng thái hiện hành nếu PROGRESS và code đã đính chính.
10. Khi thiếu artifact, tạo báo cáo thiếu dữ liệu và có thể hoàn thành interface/test fixture độc lập; không dựng kết quả benchmark giả.

---

## 2. Kết luận thiết kế và câu hỏi nghiên cứu

### 2.1. Ý tưởng cốt lõi

Hệ thống hiện tại đã có nhiều retriever và reranker. Đề xuất này bổ sung khả năng giải thích **tại sao một tài liệu khớp hoặc không khớp các điều kiện quan trọng trong truy vấn y khoa**, sau đó kiểm tra liệu tín hiệu đó có cải thiện lựa chọn tài liệu và đoạn trích hay không.

Có ba bước suy luận khác nhau:

1. **Đo bằng chứng:** tài liệu có chứa đúng bệnh, thuốc, gene, biến thể, phân nhóm hoặc điều kiện mà query yêu cầu không? Các thành phần đó có nằm trong cùng đoạn không?
2. **Đo giá trị bổ sung:** bằng chứng này có giải thích relevance ngoài những gì BM25, dense, Qwen và baseline rank đã biết không?
3. **Quyết định cách dùng:** cộng evidence bằng trọng số cố định, dùng để chọn trọng số retriever theo query, hay chỉ áp dụng cho chunk selection?

Không bỏ qua bước 2 để đi thẳng tới một gate phức tạp.

### 2.2. Cơ chế trực giác

Query có tên biến thể chính xác hoặc phân nhóm rõ có thể cần lexical matching bảo toàn identifier. Query diễn đạt bằng triệu chứng hoặc dùng cách nói khác có thể cần dense/synonym matching hơn.

Nhưng đây chỉ là trực giác:

- Tên thực thể xuất hiện không chứng minh tài liệu trả lời đúng câu hỏi.
- Một bài dài có thể chứa tất cả từ khóa ở các đoạn không liên quan.
- Một query có nhiều từ hiếm vẫn có thể cần semantic retrieval vì corpus dùng tên khác.
- BM25 top-K vốn được chọn vì khớp từ. Coverage cao trong top-K có thể là hệ quả của retriever, chưa phải bằng chứng BM25 tốt hơn dense.

Vì vậy, gate cần dự báo **lợi thế tương đối giữa các cấu hình**, không chỉ dự báo mức khớp từ.

### 2.3. Các giả thuyết cần kiểm tra

| ID | Giả thuyết | Bằng chứng cần có | Khi nào bác bỏ hoặc tạm dừng |
|---|---|---|---|
| H1 | Evidence có thông tin bổ sung ngoài baseline rank và score hiện có. | Fixed residual dùng evidence cải thiện trên holdout; phân tích trong cùng rank/language bins. | Chỉ tương quan toàn cục nhưng mất tín hiệu sau khi kiểm soát rank/ngôn ngữ. |
| H2 | Local evidence hữu ích hơn chỉ đếm thực thể trong toàn doc. | Title/best-chunk variant vượt full-doc variant dưới cùng ngân sách. | Lợi ích biến mất khi kiểm soát độ dài/số chunk hoặc thấp hơn chi phí. |
| H3 | Evidence dự báo được khi nào lexical-centric tốt hơn semantic-centric. | Quan hệ ổn định giữa E(q) và chênh lệch utility của hai cấu hình trên dữ liệu chưa tune. | E(q) cao nhưng không dự báo hướng thắng; gate không hơn constant/shuffled control. |
| H4 | Adaptive fusion vượt fixed fusion mạnh nhất trong cùng điều kiện. | Paired comparison trên holdout, cùng features/pool/rank mapping/tuning budget. | Chỉ thắng fixed yếu, hoặc lợi ích không lặp lại ngoài dev. |
| H5 | BGE-M3 sparse bổ sung tín hiệu mà các nhánh hiện tại chưa có. | Fixed + sparse vượt fixed không sparse; số tài liệu đúng được thay vào lớn hơn số bị mất. | Chủ yếu lặp phiếu cho BM25/dense và làm hại kết quả. |
| H6 | Evidence hoặc score sẵn có giúp chọn chunk tốt hơn ở các tầng chưa dùng chunk_scores. | Chunk experiment độc lập, cùng doc set và allocation. | Chỉ tăng coverage proxy, không tăng chất lượng chunk theo nhãn phù hợp. |

### 2.4. Quyết định ưu tiên

**Ưu tiên đầu:** baseline/evaluator readiness → evidence tối giản → fixed controls → adaptive.

**Nhánh độc lập:** BGE-M3 sparse được thử khi đủ tài nguyên; không phải điều kiện bắt buộc trước khi kiểm tra gate BM25/dense.

**Sau cùng:** dictionary expansion, document-specific gate, discovery toàn kho, SPLADE riêng, fine-tuning.

Một kết quả tốt có thể là fixed evidence thắng nhưng adaptive không thắng. Khi đó giữ fixed evidence và báo cáo trung thực rằng query gate chưa mang lại lợi ích.

---

## 3. Hiện trạng và bằng chứng đang có

### 3.1. Baseline được bàn giao — REPORTED

Nguồn chính: [HANDOVER.md](HANDOVER.md).

| Thuộc tính | Snapshot 15/10/2026 |
|---|---|
| Bài nộp | w045_TF |
| Doc F2 | 0,3605 |
| Chunk F2 | 0,3279 |
| FINAL | 0,3442 |
| Fingerprint doc legacy | c1e068422e5f |
| Fingerprint chunk legacy | fd07f9fc029a |
| Số doc | 200/query |
| Query | 1.200 query tiếng Việt |
| Chunk | Offset trên body đã clean, khoảng 900 token |
| ZIP | LZMA; giới hạn được dự án ghi nhận là 100 MB |

Đây là snapshot có nguồn gốc rõ, không phải khẳng định điểm tốt nhất hiện tại. Root val_calib.py có tham chiếu các run 16–17/10 nhưng chưa đủ artifact để xác lập một baseline mới hơn.

Baseline doc tương ứng w045_zh38w_e120 có FINAL 0,3272. Thay đổi allocation bằng p(gold) đưa FINAL lên 0,3442, tức +0,017 điểm tuyệt đối. Đây là bằng chứng rằng tầng chunk cần được coi là mục tiêu nghiên cứu chính thức.

### 3.2. Pipeline đang có

~~~text
Query VI
  -> Qwen3.5-9B: entities + dịch EN/ZH
  -> BM25 slug / BM25F / BM25 entity
  -> BGE-M3 dense title / title+body prefix
  -> weighted RRF
  -> Qwen3-Reranker-4B + chunk-dense
  -> các ranking VI đã cache

Query VI và bản dịch ZH
  -> BGE-M3 + Qwen3-Embedding-8B trên corpus ZH
  -> RRF ZH

VI + ZH
  -> ghép danh sách + giữ thứ tự đầu theo ranking phụ
  -> lọc corpus + bù đủ 200
  -> p(gold) từ calibration đã fit
  -> chunk selection/allocation
  -> JSON + ZIP
~~~

RRF hiện tại dùng rank bắt đầu từ 1, mặc định k=60; tie-break bằng doc_id dạng chuỗi. Đây là thông tin CODE-VERIFIED trong [index/fuse.py](index/fuse.py).

### 3.3. Kết quả lịch sử cần kế thừa

| Kết quả | Cách hiểu đúng |
|---|---|
| Gate cũ: oracle theo query hơn fixed khoảng 1,56% trên nhãn bạc, +2,49 doc/query. | REPORTED tại PROGRESS ngày 07/10. Là bằng chứng cần hạ kỳ vọng; không phải trần trên qrels thật của BEAR mới. |
| Chọn chunk theo IDF từng thua khoảng 0,3%. | Feature lexical không tự động hữu ích. Cần so với score chunk hiện có và xét policy/corpus của từng thời điểm. |
| Chunk 400/450 token từng thua chunk khoảng 900 token. | Không mặc định cắt nhỏ giúp precision. Luật overlap và độ dài đoạn vàng ảnh hưởng mạnh. |
| Thêm nguồn tương quan cao có thể làm giảm điểm. | Sparse/evidence phải chứng minh giá trị bổ sung; không gộp chỉ vì có thêm một nhánh. |
| Đã có đính chính: cùng tập doc thì đổi thứ tự không tăng Doc F2 theo cách chấm theo tập. | Ưu tiên đính chính và kết quả đối chứng mới hơn các nhận định lịch sử trái ngược. |

Code silver_gate_test.py và PROPOSAL_ADAPTIVE_FUSION.md không có trong checkout khi soạn proposal. Không tuyên bố đã kiểm tra độc lập thiết kế hoặc tái lập số đo của gate cũ.

### 3.4. Những vấn đề đã xác minh từ checkout

| Vấn đề | Hệ quả | Công việc trước benchmark |
|---|---|---|
| data/ chỉ có .gitkeep. | Chưa tái lập baseline, chưa xác minh schema artifact thật hoặc qrels. | Lấy đúng gói handover, kiểm kê và hash. |
| scripts/build_best.sh đổi cwd vào scripts/ nhưng các đường dẫn sau đó giả định repo root. | Với layout hiện tại, đường dẫn data/index/submit bị lệch. | Sửa tối thiểu đường dẫn trong readiness task riêng; không đổi thuật toán. |
| Handover ghi lệnh ở root nhưng file hiện ở scripts/. | Không copy nguyên lệnh trong handover mà chưa kiểm tra layout. | Ghi lại lệnh chạy đã kiểm chứng. |
| submit/score.py dùng token overlap 0,5, không giữ thứ tự và không gắn gold info với doc_id. | Chưa tương đương luật LCS 0,40/cùng doc ghi trong PROGRESS. | Giữ tên proxy cho evaluator cũ; xây evaluator mới khi có đặc tả. |
| tok_vi loại số thuần và token 1 ký tự. | Type 1/type 2 có thể thành cùng token sequence; một số gene/đơn vị bị mất. | Matching evidence có quy tắc riêng; chưa đổi tokenizer baseline trong cùng phép thử. |
| Entity hiện chỉ có vi/en/zh, chưa có type/critical/confidence chuẩn. | M(t), critical entity và verified alias chưa có sẵn. | Thiết kế rule/annotation và availability; không tự gán type tin cậy. |
| Có hai val_calib.py khác nhau. | Đổi scorer hoặc refit có thể làm thay beta và baseline. | Khóa đúng scripts/val_calib.py cùng beta dùng cho snapshot. |
| Dense code hiện trả dense vectors qua SentenceTransformer. | Không có căn cứ rằng sparse lexical weights đã được lưu. | Audit artifact; nếu thiếu thì encode sparse subset. |

Root val_calib.py còn có biến thể MaxP và beta_m.json. Không thay nó cho scripts/val_calib.py khi tái lập chỉ vì tên file giống nhau.

### 3.5. Luật và phiên bản corpus

- CLAUDE.md ghi macro F2; plan cũ có câu ghi micro F2. Proposal chọn **macro làm giả định làm việc theo code/tài liệu dự án**, yêu cầu xác minh bằng đặc tả BTC trước khi gọi evaluator là official-like.
- PROGRESS ngày 12/10 ghi LCS token, chuẩn hóa NFKC/HTML entity/lowercase/whitespace, cùng query và doc, ngưỡng 0,40. Chưa có PDF gốc trong checkout để kiểm tra mọi chi tiết.
- Corpus từng đổi. Dataset card khi đối chiếu ghi 1.220.598 URL, trong khi snapshot nhật ký ghi 1.194.469 URL. Không tự cập nhật corpus của baseline theo bản mới nhất.
- Ngoại lệ vinmec trong filter hiện có là hành vi baseline được ghi nhận; không tự xóa hoặc mở rộng ngoại lệ khi làm parity. Tính hợp lệ hiện hành phải kiểm tra riêng.
- Theo CLAUDE.md, private chọn query từ cùng 1.200 query đã phát hành. Không mô tả private là một bộ câu hỏi hoàn toàn mới.
- Theo quy định dự án ghi nhận, mô hình tham gia pipeline/gán nhãn phải đáp ứng giới hạn mô hình mở và các điều kiện cuộc thi. AI agent soạn code/tài liệu không được dùng chính mình làm bộ sinh nhãn hoặc sinh query cho experiment nếu không hợp lệ.

---

## 4. Bài toán, ký hiệu và metric

### 4.1. Ký hiệu

| Ký hiệu | Ý nghĩa |
|---|---|
| q | Query gốc, cùng các bản dịch và concept được liên kết. |
| C(q) | Candidate pool được khóa cho một experiment. |
| D(q) | Tập document cuối cùng được chọn để nộp hoặc đánh giá. |
| G(q) | Tập document relevant theo bộ nhãn được chỉ định. |
| K_doc | Số document cuối cùng; mặc định baseline là 200. |
| R_i(q,d) | Rank của doc d trong nguồn i. |
| L(q,d) | Evidence về độ khớp thuật ngữ/điều kiện. Không phải probability. |
| E(q) | Evidence tổng hợp ở cấp query, từ các kết quả retrieval. |
| S_ref | Score tham chiếu bảo toàn thứ tự baseline/reference. |
| lambda | Mức can thiệp của residual fusion. |
| U(q, config) | Utility theo query, gắn với một metric và bộ nhãn cụ thể. |

### 4.2. Document metric

Với k=|D|, g=|D giao G|:

$$
P_q = g/k,\qquad R_q = g/|G|,\qquad
F_{2,q} = \frac{5P_qR_q}{4P_q+R_q}
        = \frac{5g}{4|G|+k}.
$$

Khi xác nhận chấm macro:

$$
F_{2,\mathrm{macro}}=\frac{1}{N}\sum_{q=1}^{N}F_{2,q}.
$$

Không tính F2 từ trung bình P và trung bình R rồi gọi đó là macro F2. Empty gold/empty prediction phải theo quy định evaluator đã khóa.

Thứ tự trong cùng D không xuất hiện trong công thức. Vì vậy, cùng 200 doc với thứ tự khác nhau không tự tăng Doc F2.

### 4.3. Chunk metric

Chunk phải trích nguyên văn từ body theo offset; relevance được kiểm tra với reference đúng query và doc.

Theo mô tả trong nhật ký:

$$
\mathrm{match}(c,g)=
\mathbf{1}\left[
\frac{\mathrm{LCS}(\mathrm{tokens}(c),\mathrm{tokens}(g))}
{|\mathrm{tokens}(g)|}\geq 0.40
\right].
$$

LCS giữ thứ tự token nhưng không cần liên tiếp. Trùng bag-of-words không tương đương LCS.

Những chi tiết chưa được phép tự đoán:

- Một doc có nhiều gold passages thì đơn vị recall là passage, nhóm thông tin hay đơn vị khác?
- Nhiều chunk cùng phủ một reference được tính precision/recall thế nào?
- Duplicate chunk, empty gold và tokenization được xử lý thế nào?
- Có giới hạn cứng độ dài chunk hay chỉ là khuyến nghị?

Khi chưa xác minh, báo cáo riêng match diagnostics hoặc local chunk metric; không gọi là official F2.

### 4.4. Ba loại kết quả được báo cáo

| Loại | Nguồn | Cách ghi |
|---|---|---|
| official | BTC/leaderboard | Điểm thật, submission ID, ngày, corpus và evaluator version nếu biết. |
| local_qrels | Nhãn item-level do người kiểm chứng hoặc nguồn hợp lệ | Metric trên tập nhãn cục bộ; nêu coverage và quy tắc relevance. |
| proxy | Cosine, Qwen confidence, coverage, rank agreement, silver labels | Chỉ số chẩn đoán. Không đổi tên thành gold F2. |

---

## 5. Ba phạm vi can thiệp và candidate pool

### 5.1. P200 — sắp lại cùng tập 200 doc

Khóa D_baseline(q), chỉ thay thứ tự bên trong.

**Đo được:** chất lượng đầu danh sách, sự thay đổi chunk được cấp theo rank, chunk outcomes.

**Không kết luận:** tăng Doc F2 hoặc candidate recall. Doc fingerprint theo tập phải giữ nguyên.

Đây là phép thử tích hợp ít rủi ro, không phải bằng chứng đầy đủ cho mục tiêu cải tiến document retrieval.

### 5.2. PLARGE — chọn lại top-200 từ pool lớn hiện có

Khóa một C_large(q) lớn hơn 200 từ các ranking đã cache. Mọi cấu hình được so sánh có cùng C_large.

Baseline giữ D_baseline; cấu hình mới có thể thay doc tại ranh giới top-200.

**Đo được:** thay đổi Doc P/F2 khi đủ nhãn, thay đổi số tài liệu relevant, chất lượng chunk downstream.

**Điểm quan trọng:** candidate pool không đổi nhưng recall của tập doc cuối vẫn có thể tăng. Không cần full-corpus discovery để có cải thiện này.

### 5.3. PNEW — tìm doc ngoài C_large

Chỉ làm sau khi có bằng chứng pool hiện tại thiếu tài liệu mà nhánh mới có thể tìm được.

Nguồn có thể là sparse toàn kho hoặc query expansion. Chi phí indexing và số doc được cứu phải được đánh giá riêng.

Thành công của sparse reranking trong C_large chưa chứng minh sparse có ích cho discovery ngoài pool.

### 5.4. Quy tắc dựng C_large

1. Xác định chính xác các ranking hiện có và cutoff của từng nguồn.
2. Union các top lists được chọn trong config; lọc theo corpus snapshot đã khóa.
3. Đảm bảo mọi doc trong D_baseline có mặt.
4. Nếu giới hạn pool, luôn giữ D_baseline trước; chọn phần bổ sung bằng ranking deeper đã khóa.
5. Lưu pool manifest riêng cho từng query, hash, nguồn đóng góp và lý do thiếu doc.
6. Không dùng nhãn để chọn doc vào pool thực nghiệm chính.

Pilot có thể bắt đầu C khoảng 400 doc/query, sau đó 1.000 nếu cần. Đây là ngân sách đề xuất, không phải kết quả tối ưu hoặc bằng chứng rằng đủ recall.

Không coi data/rp/q14_z38w_045.jsonl là deep pool nếu artifact đó chỉ có 200 doc/query. Phải audit c_blendQB8*, ranking ZH, ranking trung gian sâu và các filter thực tế.

### 5.5. Reference order khi thêm doc

Baseline chỉ định thứ tự cho 200 doc, không có baseline rank cho mọi doc bổ sung. V1 dùng reference minh bạch:

~~~text
reference_large =
    200 doc baseline theo đúng thứ tự đã xuất
    + doc còn lại trong C_large theo deeper ranking đã khóa.
~~~

- baseline_rank của doc mới vẫn là null.
- reference_rank được xác định cho toàn C_large.
- lambda=0 chọn đúng tập và thứ tự baseline, nếu có đủ 200 doc.
- Quy tắc reference phải giống nhau giữa fixed và adaptive.

Có thể thử reference khác sau này nhưng đó là một ablation riêng.

---

## 6. Kiến trúc tích hợp

~~~text
Frozen query/corpus/ranking/calibration artifacts
                     |
             Schema adapters + manifest
                     |
           Frozen P200 hoặc C_large
                     |
       +-------------+--------------------+
       |             |                    |
  Existing ranks   Medical evidence   Optional sparse
  and scores       / local passages  lexical weights
       |             |                    |
       +-------------+--------------------+
                     |
       Feature table + availability/provenance
                     |
       +-------------+--------------------+
       |             |                    |
   Baseline      Fixed controls       Adaptive gate
   bypass        and residuals       same components
       |             |                    |
       +-------------+--------------------+
                     |
       Rerank P200 hoặc reselect top-200
                     |
       Frozen chunk policy / explicit chunk experiment
                     |
          Integrity checks + local evaluation
                     |
       Report + keep/reject/inconclusive decision
~~~

Hai cấp fallback:

- **Baseline mode:** bypass toàn bộ logic mới, sử dụng artifact baseline nguyên trạng.
- **Experimental mode thiếu feature:** xử lý theo policy đã khai báo, có log; không âm thầm biến missing thành zero hay đổi phương pháp fusion.

Nếu artifact cốt lõi bị thiếu hoặc hash lệch, fail-fast. Nếu chỉ query không có entity, có thể fallback về fixed/baseline theo config đã khóa.

---

## 7. Biomedical Evidence Engine

### 7.1. Đơn vị đo: concept và protected span

Không coi một entity là một nhóm token rời không có quan hệ.

Ví dụ query:

> Metformin có làm tăng nguy cơ thiếu vitamin B12 ở người đái tháo đường type 2 không?

Các đơn vị có thể gồm:

- metformin;
- thiếu vitamin B12;
- đái tháo đường type 2;
- quan hệ cần trả lời: thuốc có làm tăng nguy cơ thiếu chất ở nhóm bệnh nhân đó hay không.

Ba entity cùng xuất hiện là evidence tốt hơn chỉ một entity. Nhưng chúng chưa đủ để chứng minh tài liệu trả lời quan hệ trên.

Một concept có nhiều alias vẫn chỉ đóng góp tối đa một lần vào numerator/denominator. Không tăng điểm chỉ vì đã thêm nhiều tên đồng nghĩa.

### 7.2. Chuẩn hóa và matching

**Matcher cho evidence** và **normalizer cho evaluator** là hai hợp đồng riêng.

Evidence matcher V1:

1. Chuẩn hóa Unicode có phiên bản, mặc định NFC; thu gọn whitespace.
2. Giữ dấu tiếng Việt trong exact evidence.
3. Bảo toàn chữ số, chữ cái ngắn, dấu thập phân, đơn vị và cấu trúc identifier.
4. Match theo boundary/span thích hợp; không để BRCA1 khớp BRCA10.
5. Tách exact và verified-alias match thành các feature riêng.
6. Case folding có thể dùng cho phrase phổ thông; identifier phải có quy tắc riêng và ghi provenance.
7. Không đồng nhất mg với mcg hoặc tự quy đổi liều nếu chưa có parser đơn vị được kiểm chứng.

Test bắt buộc:

~~~text
type 1 khác type 2
BRCA1 khác BRCA2 và BRCA10
BRAF V600E khác BRAF V600K
5 mg khác 5 mcg và 0,5 mg
PD-1 / PD-L1 không tự coi là cùng concept
HCC chỉ khớp tên đầy đủ khi alias đã được xác minh
~~~

**Không sửa tokenizer BM25 baseline đồng thời với việc thêm evidence.** Nếu muốn bảo toàn số trong BM25, tạo nhánh tokenizer mới và đánh giá riêng để phân biệt nguồn cải thiện.

### 7.3. Xử lý entity từ artifact hiện có

Entity extraction hiện chưa cung cấp type hoặc critical label chuẩn.

V1 cần adapter:

- Giữ query gốc và từng entity string gốc.
- Xác minh span VI có xuất hiện trong query hoặc đánh dấu không xác minh được.
- Giữ mapping concept VI–EN–ZH; không tự coi bản dịch là verified synonym.
- Đánh dấu parse lỗi, translation rỗng và entity lặp.
- Nếu không có entity hợp lệ, coverage là null và has_entities=false.

Critical entity có thể bắt đầu bằng protected spans được người kiểm tra trên pilot: identifier, biến thể, phân nhóm bệnh, liều hoặc đối tượng bệnh nhân bắt buộc. Rule tự động chỉ áp dụng trong phạm vi đã kiểm chứng.

Không dùng chữ viết hoa hoặc rarity đơn thuần làm bằng chứng rằng một term là gene hoặc critical.

### 7.4. Ba nhóm feature tối giản

| Nhóm | Feature | Câu hỏi |
|---|---|---|
| Entity | exact/concept coverage | Tài liệu có các concept mà query yêu cầu không? |
| Critical | critical coverage và từng mismatch | Có nhầm identifier, biến thể, phân nhóm hay điều kiện bắt buộc không? |
| Local | title/body/best-chunk coverage | Các concept có cùng xuất hiện trong vùng nội dung hữu ích không? |

V1 không cần tạo ngay một medical specificity score liên tục cho mọi token.

### 7.5. Trọng số term và IDF

Thử theo thứ tự:

1. Uniform concept weights: mỗi concept trọng số 1.
2. IDF weights theo ngôn ngữ/corpus snapshot.
3. Critical importance có rule rõ.
4. Medical specificity chỉ khi có nguồn định nghĩa và đánh giá được.

Với df(t) là số doc có match term/concept t, N là số doc hợp lệ của ngôn ngữ:

$$
\mathrm{IDF}(t)=\log\left(1+\frac{N-df(t)+0.5}{df(t)+0.5}\right).
$$

Nếu cần scale [0,1], có thể dùng:

$$
\widetilde{\mathrm{IDF}}(t)=
\frac{\mathrm{IDF}(t)}
{\log(1+(N+0.5)/0.5)}.
$$

Đây là lựa chọn PROPOSED; không gọi là IDF đã tune. N=0 hoặc df bất hợp lệ là lỗi dữ liệu.

DF của multi-token span phải tính theo span/concept matcher đã khai báo, không tự lấy trung bình DF token rồi gọi đó là phrase DF.

Có thể tính streaming cho tập vocabulary xuất hiện trong query. Không cần xây inverted index toàn kho chỉ để lấy các feature này.

Nếu sau này dùng medical specificity M(t), một biến thể là:

$$
I(t)=\widetilde{\mathrm{IDF}}(t)
[\epsilon+(1-\epsilon)M(t)],\quad 0<\epsilon<1.
$$

Chưa định nghĩa được M(t) thì không triển khai biến thể này. Không tự gán các mức 0,5/0,9 từ trực giác rồi coi là tín hiệu y khoa chuẩn.

### 7.6. Coverage

Với tập concept T(q) và trọng số I(t)>0:

$$
L_{\mathrm{exact}}(q,d)=
\frac{\sum_{t\in T(q)}I(t)\mathbf{1}[\mathrm{exact}(t,d)]}
{\sum_{t\in T(q)}I(t)}.
$$

Tương tự:

$$
L_{\mathrm{concept}}(q,d)=
\frac{\sum_t I(t)\mathbf{1}[\mathrm{exact\ or\ verified\ alias}(t,d)]}
{\sum_t I(t)}.
$$

Critical coverage chỉ tính trên T_critical:

$$
C_{\mathrm{critical}}(q,d)=
\frac{\sum_{t\in T_{\mathrm{critical}}}I(t)\mathbf{1}[\mathrm{match}(t,d)]}
{\sum_{t\in T_{\mathrm{critical}}}I(t)}.
$$

- Không có critical term: null, has_critical_terms=false.
- Có critical term nhưng không match: 0.
- Thiếu body hoặc thiếu mapping ngôn ngữ: null/missing, không tự kết luận không liên quan.
- Luôn lưu chi tiết matched/missing concept để con người kiểm tra.
- Không hard-filter doc vì critical coverage thấp trong V1.

### 7.7. Local evidence và thiên lệch độ dài

Tính cùng matcher trên title, toàn body và từng chunk từ offset có sẵn:

$$
L_{\mathrm{local,max}}(q,d)=\max_{c\in Chunks(d)}L(q,c).
$$

Có thể so với top-2 mean hoặc:

$$
L_{\mathrm{title+local}}=
\alpha L_{\mathrm{title}}+(1-\alpha)L_{\mathrm{local}}.
$$

Nếu doc chỉ có một chunk, top-2 mean lấy trung bình trên số chunk thực có; không thêm một chunk giả điểm 0.

Lưu số chunk, độ dài body và độ dài chunk. Max trên nhiều chunk có thể tăng do nhiều cơ hội match, nên phân tích trong các length/chunk-count bins.

Nếu chỉ đọc top-M chunk theo dense score, gọi feature đó là max_on_selected_chunks; không gọi là max_all_chunks. M phải cố định giữa các đối chứng.

Không thay body/chunk boundaries để tính evidence.

### 7.8. Ngôn ngữ và alias

- VI doc dùng query/entity VI.
- ZH doc dùng entity/bản dịch ZH phù hợp.
- EN chỉ mở khi corpus, nội dung và phạm vi đánh giá đã được xác minh.
- Concept chỉ tính vào cross-language denominator khi có mapping hợp lệ; ghi mapping_coverage để tránh điểm cao giả do bỏ mất nhiều concept.
- Mapping coverage quá thấp thì fallback, không suy ra lexical failure.
- Alias chỉ từ nguồn đã kiểm chứng. Similarity cao không đủ để xác nhận đồng nghĩa.

Một query có evidence VI thấp chưa nói được sparse ZH yếu. Không dùng một gate chung để thay toàn bộ tỷ trọng ngôn ngữ trong V1.

### 7.9. Relation và intent

Evidence V1 chưa giải quyết đầy đủ relation mismatch. Cần stress cases:

- cùng thuốc nhưng hỏi chỉ định so với chống chỉ định;
- cùng bệnh nhưng hỏi điều trị so với chẩn đoán;
- cùng thực thể nhưng khác nhóm tuổi, thai kỳ hoặc phân nhóm;
- phủ định hoặc so sánh hai phương án;
- tất cả từ khóa xuất hiện nhưng ở các đoạn độc lập.

Các case này là nhãn phân tích lỗi, không phải lời hứa rằng matcher exact sẽ xử lý được. Có thể thêm relation/intent feature sau khi thấy failure mode rõ và có nhãn.

---

## 8. Fixed và adaptive residual fusion

### 8.1. Rank components

V1 tránh cộng trực tiếp raw BM25, cosine, sparse dot product và Qwen probability.

Với rank bắt đầu 1:

$$
r_i(q,d)=\frac{k_{\mathrm{rrf}}+1}
{k_{\mathrm{rrf}}+R_i(q,d)}.
$$

k_rrf=60 là giá trị mặc định trong code hiện tại, không phải giá trị tối ưu đã chứng minh cho residual mới.

Rank trong nguồn là rank gốc của artifact, hay rank sau khi restrict về C(q), phải được chọn một cách nhất quán. V1 ưu tiên giữ rank nguồn và lưu source_cutoff; thay cách rank là một ablation khác.

Những trường hợp khác nhau:

- Ranked: có rank và score nếu artifact lưu.
- Not retrieved within cutoff: đóng góp rank component 0; không diễn giải là raw similarity 0 hoặc relevance 0.
- Not scored: không có evidence để gán rank component; phải dùng policy thiếu feature.
- Missing artifact: lỗi cấu hình/dữ liệu, không phải not retrieved.

Không renormalize weight riêng từng doc một cách âm thầm vì doc đó thiếu score; như vậy sẽ tạo thêm một document-level gate ngoài thiết kế.

### 8.2. Tách BM25 family và dense family

B có thể gồm slug/BM25F/meta/entity; D có thể gồm dense title/body/chunk.

Hai hướng hợp lệ:

1. Dùng ranking nhóm đã cache và biết nguồn gốc.
2. Gộp các nhánh con bằng fixed RRF đã khóa.

Không bỏ tùy ý một nhánh lexical hoặc dense của baseline. Qwen và tín hiệu ghép ZH vẫn nằm trong S_ref; residual bổ sung không được diễn giải là xây lại toàn baseline từ hai nguồn.

### 8.3. Control A — baseline bypass

Mode baseline đọc đúng artifact, scorer và policy đã khóa. Không tái tính score chỉ để tạo một baseline gần giống.

Trong experimental residual, lambda=0 cần bảo toàn reference ranking; baseline bypass vẫn là chuẩn đối chiếu cuối cùng.

### 8.4. Control B — fixed evidence residual

Kiểm tra evidence trước khi có query gate:

$$
S_{\mathrm{evidence}}=
(1-\lambda_e)r_{\mathrm{ref}}+\lambda_e Z(q,d).
$$

Z có thể là exact coverage, critical coverage hoặc local coverage trong các ablation tách riêng.

Các feature được kết hợp phải có scale xác định. Nếu feature không khả dụng, policy cố định phải được khai báo; tốt nhất thử feature trên subset đủ dữ liệu trước khi phối nhiều feature.

Mục đích: trả lời H1/H2. Nếu một fixed residual đơn giản đã không có ích, cần lý do rõ trước khi thêm gate.

### 8.5. Control C — fixed retriever fusion

$$
S_{\mathrm{fixed}}=
(1-\lambda)r_{\mathrm{ref}} + \lambda[w_Br_B+w_Dr_D].
$$

w_B,w_D không âm và tổng 1. Khi có sparse, thêm w_S và vẫn giữ tổng 1.

Fixed phải được tune đủ tốt trên dev với cùng ngân sách thử và cùng pool như adaptive. Không so adaptive nhiều tham số với một fixed cấu hình mặc định yếu.

### 8.6. Query-level evidence E(q)

Một khởi điểm ít tham số:

$$
E(q)=\frac{\sum_{d\in TopK_B(q)}a_dL_{\mathrm{exact}}(q,d)}
{\sum_{d\in TopK_B(q)}a_d},\qquad
a_d=\frac{1}{k_E+R_B(q,d)}.
$$

Chỉ dùng kết quả BM25 trước fusion; không tính lại topK theo output gate trong cùng lượt để tránh vòng lặp.

Critical/local evidence có thể thay L_exact trong từng ablation. Không ghép mọi biến thể ngay ở lần đầu.

- K và k_E nằm trong config.
- E không dùng qrels hoặc p(gold).
- Query không có concept hợp lệ: E=null, fallback fixed.
- Query dùng ít concept do translation thiếu: ghi availability và không đánh đồng với match yếu.

**Khi một số doc trong top-K thiếu feature:** đặt m_d=1 nếu feature hợp lệ, m_d=0 nếu missing. Lưu weighted availability:

$$
\gamma_q=\frac{\sum_d a_dm_d}{\sum_d a_d},\qquad
E_{\mathrm{valid}}(q)=\frac{\sum_d a_dm_dL(q,d)}{\sum_d a_dm_d}.
$$

Nếu không có doc hợp lệ thì E=null. V1 dùng policy nghiêm: chỉ route khi feature khả dụng cho toàn top-K đã lấy được; nếu không thì fallback fixed và báo gamma_q. Nguồn trả ít hơn K doc phải ghi actual_K, không thêm doc giả.

Có thể nới minimum availability trong ablation sau, nhưng threshold phải chọn trên dev và khóa trước holdout. Khi đó báo cả E_valid và gamma_q; không âm thầm bỏ doc thiếu khỏi denominator rồi coi coverage còn lại đại diện đầy đủ cho pool. Evidence 0 đã tính hợp lệ vẫn có m_d=1, khác với missing.

### 8.7. Gate

$$
g_q=\sigma\left(\frac{E(q)-\tau}{T}\right),\qquad T>0.
$$

$$
\mathbf w(q)=g_q\mathbf w^{lex}+(1-g_q)\mathbf w^{sem}.
$$

Hai endpoint vectors không âm, tổng 1. Với BM25/dense, có thể dùng endpoint lexical-centric và semantic-centric đối xứng. Giá trị cụ thể phải đăng ký trước trong config, không coi là trọng số đã tune.

$$
S_{\mathrm{adaptive}}=
(1-\lambda)r_{\mathrm{ref}} + \lambda\sum_iw_i(q)r_i(q,d).
$$

Gate cao nghĩa là tăng tỷ trọng lexical-centric theo thiết kế. Chỉ giữ chiều này nếu dữ liệu chứng minh E cao đi cùng lợi thế lexical; không đổi dấu sau khi nhìn holdout.

### 8.8. Đối chứng để biết gate có học đúng cơ chế

| Control | Mục đích |
|---|---|
| Constant gate tốt nhất | Adaptive có hơn việc luôn dùng một tỷ trọng không? |
| Gate từ query length/rarity đơn giản | Evidence có hơn một quy tắc rẻ hơn không? |
| Shuffled E giữa các query trong cùng language/length bins | Lợi ích có đến từ gắn evidence đúng query không? |
| E_exact so với E_local | Local evidence có cải thiện routing không? |
| Query-only evidence so với result-aware evidence | Giá trị đến từ query hay từ kết quả retrieval? |

Shuffling chỉ dùng như negative control; không chọn seed shuffle thuận lợi để báo cáo.

### 8.9. Oracle diagnostic và chênh lệch utility

Định nghĩa hai cấu hình lexical-centric A và semantic-centric B đã khóa:

$$
\Delta_q=U(q,A)-U(q,B).
$$

Kiểm tra E(q) có dự báo dấu hoặc thứ tự của Delta_q trên dữ liệu ngoài tuning không.

Oracle per-query chọn cấu hình có U cao nhất trong **một menu cấu hình cố định**. Nó chỉ là trần của menu đó trên bộ nhãn đó, không phải trần của mọi adaptive retriever.

- Oracle dùng nhãn nên tuyệt đối không đưa vào inference hoặc submission.
- Oracle trên silver labels chỉ là chẩn đoán proxy.
- Không dùng oracle để chọn từng doc rồi gọi đó là query gate.
- Nếu oracle của menu chỉ hơn fixed rất ít so với chi phí/độ bất định, tạm dừng learned routing.

### 8.10. Tuning có giới hạn

1. Chốt feature và pool trước.
2. Tune fixed trên dev.
3. Dùng menu nhỏ cho lambda, tau và T; endpoint vectors khóa trước.
4. Tau có thể lấy từ quantiles của E trên dev; không fit scaler/quantile trên holdout.
5. Giới hạn số config được đánh giá cho từng family; lưu cả config thua.
6. Freeze config trước khi mở holdout.

Không grid-search đồng thời tokenizer, IDF, alias, K, endpoints, gate, sparse fields, chunk length và allocation.

---

## 9. Nhánh sparse và các mở rộng có điều kiện

### 9.1. BGE-M3 sparse

BGE-M3 có đầu ra lexical weights, nhưng dense vectors hiện có không thể tự chuyển thành sparse weights.

Quy trình subset:

1. Audit checkpoint, revision, thư viện và artifact.
2. Lấy tập doc duy nhất từ C(q) của pilot; không encode lặp cùng doc theo từng query.
3. Encode field đã chọn: title hoặc title+body prefix hoặc chunk. Mỗi field là một biến thể riêng.
4. Encode query bằng cùng mô hình/tokenizer và view ngôn ngữ phù hợp.
5. Lưu lexical weights theo token ID và provenance.
6. Chấm lexical matching trên candidate pairs.
7. So fixed không sparse với fixed có sparse.
8. Chỉ thử adaptive ba nhánh khi sparse có lợi hoặc có failure mode đáng nghiên cứu.

Tài liệu chính thức có ví dụ return_sparse và lexical_weights: [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3).

Sparse lexical matching cần shared token IDs; query VI và doc ZH không có bảo đảm khớp từ chỉ vì mô hình đa ngôn ngữ. V1 dùng bản dịch cùng ngôn ngữ, audit entity preservation.

### 9.2. Cache và truncated input

Cache key tối thiểu:

~~~text
model_id + revision + tokenizer_version + library_version
+ corpus_hash + doc_id + body/field_hash
+ input_field + max_length + dtype + encoder_options
~~~

Lưu actual token count và truncation flag. Score trên title+prefix không được mô tả là đã đọc toàn tài liệu.

Nếu chỉ chấm sparse cho một subset, fixed/adaptive phải so trên cùng subset đủ feature hoặc có fallback đã khai báo. Không cho doc chưa chấm sparse điểm 0 rồi diễn giải là sparse không thích doc đó.

### 9.3. Medical dictionary expansion

Chỉ thử khi phân tích lỗi chứng minh synonym/abbreviation mismatch là nút thắt.

~~~text
Original query concept
  -> canonical concept ID hoặc verified mapping
  -> aliases theo ngôn ngữ
  -> weighted lexical expansion branch
  -> fixed fusion control
~~~

- Giữ evidence từ original concepts riêng với expanded alias matches.
- Không fuzzy-expand gene/thuốc chỉ vì cosine cao.
- Không coi cùng nhóm thuốc là cùng hoạt chất.
- Ghi nguồn và version từ điển, phạm vi ngôn ngữ, điều kiện sử dụng.
- Gắn expansion vào một nhánh lexical trước; không đổi mọi query view cùng lúc.

### 9.4. SPLADE, local gate và discovery

SPLADE độc lập chỉ được ưu tiên khi có checkpoint phù hợp ngôn ngữ, đúng điều kiện mô hình và benchmark subset cho thấy lợi thế so với BGE sparse.

Document-level gate hoặc bounded local adjustment chỉ thử sau query gate/fixed evidence, kèm hard negatives. Không hard-filter theo critical coverage trong vòng đầu.

Full-corpus discovery chỉ bắt đầu sau pilot có lý do rõ; thành công trên candidate reranking không đủ để suy ra lợi ích của indexing toàn kho.

---

## 10. Chunk selection và allocation

### 10.1. Baseline thực tế theo code — CODE-VERIFIED

Trong [submit/submission.py](submit/submission.py), với cấu hình handover:

| Tầng | Số chunk cơ sở | Cách chọn thực tế |
|---|---:|---|
| Rank 1–40 | Tối đa 2/doc | Có truyền chunk_scores. Doc có nhiều hơn 2 chunk được chọn theo score rồi xuất theo thứ tự gốc. |
| Rank 41–120 | Tối đa 1/doc | Không truyền chunk_scores ở lệnh gọi tầng này; không có qtext thì lấy chunk đầu. |
| Rank 121–200 được plan thêm | Theo plan, baseline là 1 | Không truyền chunk_scores; lấy chunk đầu nếu không qtext. |
| Top-120 bị plan=0 | 0 | Bỏ chunk, giữ nguyên doc trong relevant_docs. |

Ngoài ra:

- Nếu vừa có qtext vừa có chunk_scores, nhánh query matching chạy sau và ghi đè lựa chọn chunk.
- Plan n>0 chỉ thêm cho doc chưa có chunk, không tự đổi số chunk của doc đã có.
- Chunk idx trong score cần map đúng thứ tự chunk theo doc, không đồng nhất tùy tiện với chunk_id toàn cục.

Vì vậy, áp chunk_scores cho rank 41–120/đuôi là **một experiment mới**, không phải chỉnh sửa vô hại khi reproduce.

### 10.2. Giữ policy cố định nghĩa là gì?

Khi thử doc ranking:

- Giữ thuật toán, threshold p(gold), số chunk theo tầng, scorer và beta cố định.
- Ranking đổi thì doc nhận suất chunk có thể đổi. Đây là tác động downstream cần đo.
- Không đồng thời tune chunk length, allocation thresholds hoặc chunk scoring.

Giữ policy cố định **không có nghĩa** giữ mọi chunk output giống hệt khi rank thay đổi.

Khi muốn cô lập metric doc, có thể đánh giá doc-only trước. Submission ghép để tách hai tầng chỉ dùng khi phù hợp schema/quy định đã xác minh.

### 10.3. Các experiment chunk nên thử

1. **Existing score extension:** cùng doc set/allocation, dùng chunk_scores có sẵn cho tầng 41–120 và doc đuôi, nếu score coverage đủ.
2. **Lexical local selection:** chọn chunk theo evidence thay vì chunk đầu ở đúng các tầng đó.
3. **Fixed score combination:** kết hợp score chunk hiện có và evidence bằng control cố định.
4. **Allocation adaptation:** chỉ sau selection, mới kiểm tra có nên cấp thêm/bớt chunk dựa trên chất lượng dự kiến.

Trước mỗi experiment, báo tỷ lệ doc có hơn một chunk và có score đầy đủ. Nếu phần lớn doc chỉ có một chunk, khả năng cải thiện selection có thể nhỏ.

Không suy ra P(chunk relevant) bằng cách nhân p(gold) với một hằng số chưa kiểm chứng rồi coi là xác suất đã calibrate.

### 10.4. So sánh dưới cùng ngân sách chunk

Thay selector phải giữ nguyên số slot được phép ở từng doc, rồi báo số chunk thực xuất vì doc có thể thiếu chunk hoặc có chunk rỗng.

Thay allocation cần một trong hai protocol được đăng ký trước:

1. **Matched budget:** cùng tổng số slot/chunk hoặc cùng ngân sách token/ký tự được chỉ định, đồng thời cả hai đều dưới giới hạn ZIP.
2. **Budget frontier:** quét một menu ngân sách nhỏ, so metric tại ngân sách tương đương và báo đường trade-off chất lượng–chi phí.

Không chỉ so hai bài cùng dưới 100 MB nhưng một bài nộp nhiều chunk hơn rất nhiều rồi kết luận allocation thông minh hơn. Cũng không coi số ký tự bằng nhau là bảo đảm kích thước ZIP bằng nhau: compression phụ thuộc mức lặp và cấu hình.

Báo số chunk/query, số token/ký tự, tỷ lệ passage trùng/overlap, tỷ lệ doc có nhiều lựa chọn chunk, actual ZIP bytes và cấu hình nén. Dedupe hoặc đổi compression trong experiment cũng phải có đối chứng riêng.

---

## 11. Thiết kế nhãn và đánh giá

### 11.1. Câu hỏi cần trả lời trước khi gán nhãn

1. Có qrels chính thức hoặc reference chunks nào sử dụng được không?
2. Nhãn muốn đo đúng chủ đề hay chứa câu trả lời?
3. Annotation budget đủ phủ top-K hoặc chỉ đủ đánh giá các cặp thay thế?
4. Có thể khóa holdout theo query và kiểm soát query gần trùng không?
5. Có người hiểu y khoa và ngôn ngữ tương ứng để audit các ca khó không?

Không có nhãn thì có thể xây engine và kiểm tra tính đúng kỹ thuật, nhưng chưa thể khẳng định retrieval quality tăng.

### 11.2. Hai tập dữ liệu đánh giá khác nhau

**Representative sample:** lấy query theo phân phối thực, phục vụ ước lượng hiệu quả trung bình trong phạm vi mẫu.

**Stress set:** chủ động chọn identifier, synonym, relation mismatch, multilingual và long-document cases, phục vụ phân tích failure modes.

Không gộp mẫu cân bằng theo failure mode rồi gọi là ước lượng không chệch cho toàn bộ 1.200 query. Nếu tái trọng số, phải có sampling probabilities phù hợp.

### 11.3. Pilot đề xuất

- Khoảng 100 query là điểm bắt đầu về ngân sách, không phải bảo đảm đủ statistical power.
- Có thể dùng 60 dev và 40 holdout, split theo query group trước khi tune.
- Query gần trùng/cùng template nên ở cùng split.
- Tag failure mode có thể chồng lấn; không ép mọi query vào đúng một nhóm.
- Lưu query IDs và split hash; không đổi holdout sau khi thấy kết quả.

Nếu holdout quá nhỏ hoặc CI rộng, kết luận inconclusive và mở rộng đánh giá thay vì khẳng định adaptive thắng.

### 11.4. Nhãn document

Gợi ý ba mức:

| Grade | Ý nghĩa |
|---|---|
| 0 | Không liên quan, sai entity/điều kiện quan trọng hoặc không có nội dung phù hợp. |
| 1 | Đúng chủ đề nhưng chưa thấy thông tin trả lời yêu cầu chính. |
| 2 | Có đoạn nội dung hỗ trợ trả lời trực tiếp một yêu cầu của query. |

Lưu supporting offsets/passages và lý do, không chỉ một con số.

Binary relevance dùng grade>=1 hay grade=2 phải đăng ký trước theo câu hỏi nghiên cứu. Báo cáo được cả hai nhưng không chọn ngưỡng sau khi nhìn metric.

Ẩn tên retriever và score khi annotation. Audit một subset bằng hai người; xử lý bất đồng có biên bản.

LLM hợp lệ có thể hỗ trợ đề xuất nhãn, nhưng nhãn chưa audit phải ghi model-assisted/proxy. Không dùng chính retriever/reranker đang đánh giá làm gold judge duy nhất.

### 11.5. Pooling và incomplete judgments

Pooling từ top lists của nhiều hệ thống giúp tiết kiệm annotation nhưng vẫn có bias. Không coi unjudged là irrelevant trong phân tích chính.

Có ba mức khả năng đánh giá:

1. **Qrels đủ trong một universe đã định nghĩa:** đo metric trong universe đó; nêu rõ recall không phải recall toàn corpus.
2. **Đã đánh giá toàn bộ top-K của các hệ thống:** có thể đo precision@K trên bộ nhãn local; chưa suy ra full recall nếu thiếu G.
3. **Chỉ đánh giá các doc thay vào/thay ra:** dùng paired replacement analysis.

Không báo local Doc F2 hoặc Recall@200 đầy đủ chỉ từ 20–40 doc bất đồng/query.

### 11.6. Paired replacement analysis

Với A và B có cùng số doc k:

~~~text
added   = D_A \ D_B
removed = D_B \ D_A
~~~

Nếu mọi doc trong added và removed được gán nhãn theo cùng policy:

$$
\Delta g_q =
\#relevant(added)-\#relevant(removed).
$$

Common docs tự triệt tiêu nên không cần giả định nhãn cho chúng để tính Delta g.

$$
\Delta P_q=\Delta g_q/k.
$$

Đây là cách kiểm tra candidate reselection với chi phí annotation thấp hơn. Tuy nhiên:

- Không biết |G(q)| thì chưa tính đúng Delta F2 theo query.
- Tổng Delta g dương không bảo đảm macro F2 dương vì mẫu số mỗi query khác nhau.
- Holdout annotations phải được giữ kín với bước chọn config.
- Nếu chỉ có nhãn cho một phần differences, chỉ báo kết quả trên phần đã judged và coverage; không ngoại suy.

### 11.7. Nhãn chunk

Gold passage cần ít nhất query_id, doc_id, text hoặc offsets và nguồn.

- Người gán nhãn xác định thông tin cần thiết, không đơn giản chọn chunk có lexical score cao.
- Phân biệt gold passage phục vụ local evaluation với reference BTC chưa được cung cấp.
- Reference do local team tạo có thể khác độ dài/phạm vi của BTC; nêu rõ khi so sánh chunk policy.
- Không tune chunk length để khớp các local references đã được sinh từ chính chunker đang đánh giá.

### 11.8. Paired statistics và bất định

- Tính per-query differences, không chỉ trung bình hai run.
- Bootstrap/resample theo query hoặc query group, không coi các doc cùng query là mẫu độc lập.
- Lưu seed và số bootstrap samples trong config.
- Báo point estimate, CI, tỷ lệ query cải thiện/giảm và phân bố thay đổi.
- Phân tích VI/ZH, entity type, query length và doc length nhưng không chọn subgroup thuận lợi làm kết luận chung.
- Nếu có nhiều cấu hình/subgroup, phân biệt exploratory với confirmatory. Chọn cấu hình trên dev, khóa lại rồi dùng holdout để xác nhận; không chọn lại giữa A1/A2/S hoặc các threshold sau khi nhìn holdout.

Với annotation không đầy đủ, CI chỉ áp dụng cho metric đã xác định trên nhãn đó; CI không khắc phục pooling bias.

### 11.9. Chọn primary metric theo phạm vi

| Phạm vi | Primary metric có thể chọn | Điều không được làm |
|---|---|---|
| P200, chỉ đổi thứ tự | Chunk metric với reference hợp lệ; hoặc local precision ở đầu danh sách khi đã judged đầy đủ top-K. | Dùng Doc F2 của toàn 200 làm utility cho gate: đại lượng đó không thay đổi. |
| PLARGE, chọn lại 200 | Official/local Doc F2 khi đủ qrels; nếu nhãn thiếu, paired Delta P@200/Delta hits khi mọi doc thay vào/thay ra đã judged. | Tính F2 toàn corpus từ pooled judgments thiếu G. |
| Chunk-only | Local/official chunk metric dưới ngân sách đã khóa. | Gán gain do thêm chunk cho selector hoặc gate. |
| PNEW | Recall gain khi có nhãn đủ; nếu chưa đủ thì relevance của novel additions và paired selection gain có coverage rõ. | Dùng số doc mới hoặc diversity làm bằng chứng recall tăng. |

Đối với oracle và Delta utility trong mục 8.9, dùng đúng primary metric của phạm vi. Oracle P200 có thể tối ưu P@40 hoặc chunk utility; không dùng Doc F2 của cùng 200 vì mọi cấu hình đều hòa.

Nếu chỉ có replacement labels, tên metric phải giữ là Delta hits/Delta P theo policy nhãn local. Không đổi tên thành predicted official gain. Nếu primary metric chưa đo được, experiment chỉ có trạng thái diagnostic hoặc inconclusive.

### 11.10. Leaderboard

Chỉ dùng official runs để xác nhận một số cấu hình đã freeze, theo quota/quy định hiện hành.

Không dựa vào hàng loạt truy vấn điểm tổng để suy ngược nhãn từng item. Không gọi split tự tạo từ 1.200 query là official public/private split.

Fit p(gold) bằng aggregate score là cơ chế baseline được kế thừa, không phải phương pháp xây nhãn cho gate mới.

---

## 12. Ma trận thực nghiệm

Mỗi run phải có experiment ID, hypothesis, parent/control, pool ID, feature version, chunk policy và evaluation source.

| ID | Thay đổi chính | Đối chứng trực tiếp | Pool | Kết luận có thể rút ra |
|---|---|---|---|---|
| R0 | Baseline reproduction | Snapshot handover | P200 | Parity kỹ thuật và khả năng tái lập. |
| R1 | Evaluator/matcher contract tests | Quy tắc đã khóa | Fixtures/local gold | Tính đúng của công cụ đo; không phải gain retrieval. |
| L0 | Chỉ tính evidence, chưa đổi ranking | Baseline feature table | P200/PLARGE | Phân phối, missingness, hard negatives và giá trị phân biệt. |
| L1 | Uniform exact evidence residual | Baseline reference | Cùng pool | Exact evidence có ích không? |
| L2 | IDF thay uniform | L1 | Cùng pool | Rarity có giá trị bổ sung không? |
| L3 | Critical evidence | L1/L2 đã khóa | Cùng pool | Phân biệt identifier/điều kiện có giảm lỗi không? |
| L4 | Local/title evidence thay full-body evidence | Fixed evidence cùng trọng số/tuning budget | Cùng pool | Locality có giúp hay chỉ thiên lệch độ dài? |
| F0 | Fixed BM25/dense residual | Baseline reference | P200 và PLARGE tách riêng | Nhánh residual đơn giản có ích không? |
| O0 | Oracle menu A/B theo query | Best fixed trong menu | Dev hoặc diagnostic labeled split | Menu có headroom cho routing không? Không deploy. |
| A1 | Gate theo E_exact | Best fixed cùng components | Cùng pool với F0 | Adaptive có hơn constant fusion không? |
| A2 | Gate theo E_local | A1 và best fixed | Cùng pool | Local evidence có dự báo routing tốt hơn không? |
| A3 | Constant/query-only/shuffled gate controls | A1/A2 đã chọn trên dev | Cùng pool | Lợi ích có do evidence gắn đúng query không? |
| S1 | Fixed + BGE sparse | Fixed không sparse | Candidate subset đủ score | Sparse có bổ sung không? |
| S2 | Adaptive ba nhánh | Best fixed ba nhánh | Cùng pool/features với S1 | Gate ba nhánh có ích không? Chỉ khi đáng thử. |
| C1 | Chunk_scores mở rộng tới tầng 41–120/đuôi | Exact baseline chunk selection | Cùng doc set/allocation | Score sẵn có ở tầng mới có cải thiện selection không? |
| C2 | Local evidence chọn chunk | C1 hoặc baseline selection theo câu hỏi | Cùng doc set/allocation | Evidence có hơn existing score/chunk đầu không? |
| C3 | Allocation mới | Selection đã khóa | Cùng doc set/ngân sách hoặc budget frontier | Phân bổ chunk có thêm lợi ích không? |
| X1 | Verified alias lexical branch | Không expansion | Cùng C_large trước; discovery riêng sau | Synonym branch có cứu lỗi thực sự không? |
| X2 | Discovery ngoài C_large | Best candidate-only system | PNEW | Có tăng độ phủ đủ đáng chi phí không? |

### 12.1. Thứ tự thực hiện

~~~text
R0/R1
   -> L0
   -> L1/L2/L3/L4 và F0
   -> O0 + kiểm tra E dự báo Delta utility
   -> A1/A2/A3

Sau readiness, có thể làm nhánh riêng:
   -> C1/C2, giữ doc set
   -> S1 nếu có tài nguyên; S2 chỉ khi cần

Chỉ sau khi có failure mode:
   -> C3 / X1 / X2
~~~

Không bắt buộc S1 trước A1. Không bắt buộc adaptive thành công mới được giữ một fixed evidence hoặc chunk improvement hữu ích.

### 12.2. Chạy trên hai phạm vi

Nếu đủ artifact/nhãn, L/F/A có hai bản:

- suffix p200: kiểm tra thứ tự và chunk downstream;
- suffix plarge: kiểm tra chọn lại top-200.

Không trộn metric hai phạm vi vào cùng một dòng rồi gọi chung là reranking gain.

### 12.3. Bảng kết quả cần xuất

~~~text
run_id | control | pool_hash | eval_type | query_split
doc_metric | chunk_metric | replacement_delta
CI | judged_coverage | VI/ZH regressions
CPU/GPU time | peak RAM/VRAM | cache_size
decision | explanation
~~~

Nếu metric không tính được, ghi not_available với lý do; không điền 0.

---

## 13. Lộ trình triển khai và điều kiện chuyển bước

### Phase 0 — Readiness và baseline locking

**Công việc**

- Đọc lại tree, git status và các file hướng dẫn áp dụng.
- Kiểm kê artifact, model revision, query version và corpus snapshot.
- Giải quyết lỗi cwd của build script bằng thay đổi tối thiểu.
- Khóa exact scorer/calibration; không refit beta.
- Tái lập nếu đủ data, đối chiếu fingerprint legacy và provenance hash mới.
- Đối chiếu đặc tả macro/chunk với nguồn BTC.

**Đầu ra:** baseline_manifest.json, DATA_READINESS.md, EVALUATOR_CONTRACT.md và parity report.

**Điều kiện chuyển:** đã xác định cái gì tái lập được; nếu data thiếu vẫn có thể làm fixtures, nhưng benchmark thật chưa được bắt đầu.

### Phase 1 — Feature table và pool contracts

**Công việc**

- Adapter JSONL/SQLite thật.
- Freeze P200/C_large.
- Chuẩn hóa ID, rank provenance và availability masks.
- Ghi actual chunk mapping, scorer coverage và query translations.

**Đầu ra:** feature schema, pool manifest, data diagnostics.

**Điều kiện chuyển:** join không làm mất/nhân đôi doc; baseline bypass/parity đúng; không có key bị đoán sai.

### Phase 2 — Evidence tối giản

**Công việc**

- Exact protected-span matcher và uniform coverage.
- Critical spans trong phạm vi có thể xác minh.
- Title/local chunk evidence.
- IDF-only như một ablation; chưa cần medical specificity hoặc ontology lớn.
- Stress tests và kiểm tra lỗi type 1/type 2, identifier, relation mismatch.

**Đầu ra:** L0 report, evidence feature table và các case explanation.

**Điều kiện chuyển:** feature có semantics rõ, không missing giả thành zero, đủ cost diagnostics.

### Phase 3 — Nhãn local và fixed controls

**Công việc**

- Chốt representative/stress sample và splits.
- Gán nhãn/review theo ngân sách; đo judged coverage.
- Chạy L1–L4/F0, giữ nguyên chunk policy.
- Chọn fixed control trên dev; không nhìn holdout để tune.

**Đầu ra:** qrels/annotation ledger, fixed-control report.

**Điều kiện chuyển:** có metric hợp lệ hoặc kết luận rõ rằng chỉ đủ proxy; không chuyển sang khẳng định adaptive hiệu quả bằng proxy.

### Phase 4 — Kiểm tra routing rồi adaptive

**Công việc**

- O0 trên menu cố định.
- Phân tích E(q) và Delta utility.
- Tune menu nhỏ cho A1/A2 trên dev.
- Freeze và chạy holdout, constant/shuffled controls.

**Đầu ra:** paired adaptive-vs-fixed report, go/no-go.

**Điều kiện chuyển:** adaptive có lợi ích thực tiễn và bằng chứng ngoài tuning; nếu không, giữ best fixed.

### Phase 5 — Nhánh độc lập có điều kiện

- C1/C2: tận dụng chunk_scores/evidence ở tầng chưa dùng.
- S1: sparse subset và cost report; S2 nếu có lý do.
- X1/X2: chỉ khi failure analysis chỉ rõ synonym hoặc pool coverage bottleneck.

Mỗi nhánh có control và quyết định riêng; không gộp các gain thành một dự báo FINAL.

### Phase 6 — Tích hợp cuối và submission validation

- Ghép các thành phần đã được chọn; chạy interaction check vì gain riêng không chắc cộng được.
- Giữ một bản baseline rollback.
- Validate full 1.200 query, integer IDs, corpus membership, chunk provenance, ZIP.
- So official khi được phép và có đủ điều kiện.
- Hoàn thành report kể cả khi mọi nhánh mới bị reject.

---

## 14. Hợp đồng dữ liệu và cấu trúc mã nguồn

### 14.1. Bảng ánh xạ code hiện có sang phần mới

| File hiện có | Tái sử dụng | Phần mới đề xuất |
|---|---|---|
| query_processing/expand.py, translate.py | Query/entity/translation artifacts | Query adapter, source span và translation quality flags. |
| index/bm25.py, bm25_ent.py | Ranks, source config và tokenizer baseline | Matcher bảo toàn identifier; không sửa baseline tokenizer trong evidence experiment. |
| index/fuse.py | RRF contract và source ranks | Fixed/adaptive residual với config riêng. |
| index/hybrid_cands.py | Cách giữ doc set/thứ tự đầu | Pool adapter và explicit reference order. |
| index/dense.py, dense_chunks.py | Dense rank, score, best_idx và metadata | Sparse subset encoder nếu cần. |
| scripts/val_calib.py | Exact baseline scorer | Frozen adapter; không dùng output làm gold label. |
| submit/submission.py | Exporter và baseline chunk behavior | Experiment adapter, integrity validation và chunk selection riêng. |
| submit/score.py | Evaluator proxy lịch sử | Evaluator có contract/phiên bản mới khi xác minh được luật. |
| utils/audit.py | Corpus/offset checks hiện có | Bổ sung checks cho source artifacts, feature table và submission. |

### 14.2. Layout đề xuất

Không tạo toàn bộ skeleton ngay. Bắt đầu từ adapter, matcher và runner cần cho experiment đầu; tách thêm module khi thực sự dùng.

~~~text
adaptive_retrieval/
  adapters.py
  matching.py
  evidence.py
  fusion.py
  sparse.py                  # chỉ khi chạy S1
  chunk_experiments.py       # chỉ khi chạy C1/C2

evaluation/
  local_qrels.py
  chunk_lcs.py               # contract đã xác minh mới official-like
  paired.py

experiments/txt_bear/
  configs/
  manifests/
  reports/
  cli.py

tests/
  test_evidence_contract.py
  test_evaluation_contract.py
  test_fusion_contract.py
  test_baseline_integration.py
~~~

Layout này là PROPOSED, chưa tồn tại. Có thể điều chỉnh theo quy ước repo nhưng phải giữ các hợp đồng và đường baseline.

### 14.3. Feature table

Một dòng cho một cặp query/doc trong C(q). Khóa duy nhất là query_id, doc_id, pool_id, feature_version.

~~~text
query_id                  integer nội bộ theo dataset
doc_id                    string nội bộ nhất quán; integer khi export submission
pool_id / pool_hash
corpus_hash / query_hash / feature_version
lang / language_source
baseline_rank             nullable
reference_rank
source_ranks              map nguồn -> rank/cutoff
source_scores             map nguồn -> raw score + provenance
availability              map nguồn/feature -> trạng thái
exact_coverage            nullable float [0,1]
concept_coverage          nullable float [0,1]
critical_coverage         nullable float [0,1]
title_coverage            nullable float [0,1]
local_coverage            nullable float [0,1]
has_entities / has_critical_terms
translation_mapping_coverage
matched_concepts / missing_concepts
body_length / chunk_count
best_evidence_chunk       stable chunk reference, không phải text được sửa
sparse_score/rank         nullable; chỉ khi đã chấm
experiment_id / config_hash
~~~

Không đưa gold label vào inference table mặc định. Join qrels trong evaluation pipeline riêng để giảm nguy cơ dùng nhầm.

### 14.4. Query evidence table

Một dòng/query:

~~~text
query_id / query_group / language_view
entity_count / critical_count / query_length
parse_status / translation_status
E_value / E_feature_definition / E_topK / E_rank_weighting
E_availability / fallback_reason
gate_value / selected_weights / lambda
~~~

### 14.5. Qrels và passage references

~~~json
{
  "query_id": 17,
  "doc_id": "12345",
  "grade": 2,
  "label_policy_version": "local_v1",
  "annotator": "reviewer_a",
  "adjudication": "reviewed",
  "supporting_passages": [
    {"start": 120, "end": 360, "body_hash": "<sha256>"}
  ],
  "notes": "Chứa nội dung trả lời điều kiện chính của query."
}
~~~

Ví dụ là fixture minh họa, không phải nhãn cho query/doc thật. Không ghi fixture này vào dữ liệu benchmark.

### 14.6. Baseline manifest

~~~json
{
  "snapshot": "handover_2026_10_15",
  "status": "not_reproduced",
  "git_commit": null,
  "dirty_files": [],
  "artifacts": [],
  "baseline_scorer": "scripts/val_calib.py",
  "calibration_hash": null,
  "reported_scores": {
    "doc_f2": 0.3605,
    "chunk_f2": 0.3279,
    "final": 0.3442
  },
  "observed_scores": null,
  "legacy_fingerprints_expected": {
    "doc": "c1e068422e5f",
    "chunk": "fd07f9fc029a"
  },
  "legacy_fingerprints_observed": null,
  "ranking_sha256": null,
  "submission_provenance_sha256": null,
  "missing_artifacts": []
}
~~~

Chỉ đổi status khi thực sự chạy và kiểm tra.

Legacy fingerprint hiện không đủ kiểm tra mọi invariant: doc hash không thể hiện rank; chunk hash chỉ theo text chưa bảo vệ đầy đủ query/doc provenance. Giữ fingerprint cũ để parity, thêm canonical SHA-256 gồm query_id, doc_id, rank và chunk text/offset phù hợp.

SQLite phải là snapshot nhất quán. Không hash một database đang bị ghi rồi coi hash đó là phiên bản cố định; không tự checkpoint/ghi lại source DB để tiện audit.

### 14.7. Candidate export

Downstream đang nhận:

~~~json
{
  "id": 17,
  "candidates": [
    {"doc_id": "12345", "score": 0.99}
  ]
}
~~~

load_candidates sẽ sort lại theo score. Vì vậy:

- Export score phải bảo toàn thứ tự intended ranking.
- Lưu raw adaptive scores trong sidecar; có thể export monotonic rank scores theo contract đã khóa.
- Kiểm tra precision/rounding và tie-break; không tự thay cách export baseline.
- Không thêm key giải thích vào submission cuối nếu schema không cho phép.

---

## 15. Cấu hình, thuật toán và lệnh dự kiến

### 15.1. Cấu hình tối giản

~~~yaml
proposal_version: 1
experiment_id: null
mode: baseline                 # baseline | fixed_evidence | fixed | adaptive

inputs:
  baseline_manifest: null
  query_artifact: null
  corpus_snapshot: null
  pool_manifest: null
  source_manifest: null

pool:
  scope: p200                  # p200 | plarge | pnew
  output_docs: 200
  max_candidates: null
  preserve_baseline_members: true

evidence:
  matcher_version: protected_spans_v1
  weight_mode: uniform         # uniform | idf | verified_importance
  exact: true
  verified_alias: false
  critical: false              # bật khi có critical source được kiểm chứng
  local: false
  idf_snapshot: null
  missing_policy: explicit_mask

fusion:
  rank_k: 60
  rank_scope: source_original
  lambda: 0.0
  fixed_weights: null
  lexical_endpoint: null
  semantic_endpoint: null
  gate:
    feature: null
    topk: null
    rank_weight_k: null
    threshold: null
    temperature: null
    fallback: fixed

sparse:
  enabled: false
  model_revision: null
  field: null
  max_length: null
  cache_manifest: null

chunk:
  policy: frozen_handover
  calibration_manifest: null
  experiment: none

evaluation:
  source: diagnostics_only      # diagnostics_only | local_qrels | official
  label_policy: null
  evaluator_contract: null
  split_manifest: null
  bootstrap_seed: 42

runtime:
  seed: 42
  dry_run: true
  output_dir: null
~~~

Đây là config mẫu chưa chạy được experiment thật. Adaptive phải fail-fast nếu thiếu threshold/temperature/endpoints; sparse phải fail-fast nếu thiếu checkpoint/field/cache cần thiết.

Baseline không được phụ thuộc vào các tham số adaptive null. Dry-run chỉ validate và báo việc sẽ làm, không tự chạy GPU.

### 15.2. Thuật toán experimental runner

~~~text
1. Read config; reject unknown or inconsistent fields.
2. Verify manifest hashes, corpus/query versions and evaluator status.
3. If mode == baseline:
       use frozen baseline path;
       validate legacy + provenance fingerprints;
       stop after report/export requested.
4. Load the frozen candidate pool.
5. Join existing ranks/scores and explicit availability states.
6. Compute/load evidence with frozen matcher and field definitions.
7. If sparse enabled, require matching sparse cache and score coverage.
8. Build fixed or adaptive weights without reading qrels.
9. Apply identical residual/reference mapping.
10. Sort deterministically; keep same 200-set for p200,
    or select top-200 for plarge.
11. Export candidate ranking plus explanation sidecar.
12. Apply frozen chunk policy, unless this run is a named chunk experiment.
13. Run integrity checks.
14. Evaluation process separately loads allowed qrels.
15. Save metrics, paired diffs, cost, missingness and decision report.
~~~

### 15.3. CLI dự kiến

Các lệnh dưới đây là **interface đề xuất**, chưa có trong checkout. Agent phải triển khai rồi kiểm tra help/schema trước khi hướng dẫn người dùng chạy.

~~~powershell
python -m experiments.txt_bear.cli audit --config <config_path>
python -m experiments.txt_bear.cli features --config <config_path>
python -m experiments.txt_bear.cli run --config <config_path>
python -m experiments.txt_bear.cli evaluate --config <config_path>
python -m experiments.txt_bear.cli compare --baseline <run_id> --candidate <run_id>
~~~

Lệnh rebuild đã được sửa đường dẫn và kiểm chứng phải ghi trong baseline report riêng. Không copy lệnh bash cũ như thể script hiện đã sửa.

---

## 16. Kiểm thử, tài nguyên và vận hành

### 16.1. Kiểm thử có ý nghĩa

| Nhóm | Điều phải chứng minh |
|---|---|
| Matching | Không gộp type 1/type 2, gene/variant gần tên, liều/đơn vị; alias phải verified; empty/missing đúng semantics. |
| Local evidence | Từ khóa rải nhiều chunk khác với cùng chunk; max/top-2 có semantics rõ; offsets đúng snapshot. |
| Evaluator | Sai doc không match dù text giống; LCS giữ thứ tự; đúng ngưỡng; normalize/version; macro tính theo query. |
| Fusion | Weights không âm/tổng 1; T>0; lambda=0 parity; missing branch xử lý rõ; deterministic ties. |
| Baseline integration | chunk_scores chỉ áp dụng đúng tầng; qtext precedence; plan=0 không loại doc; plan>0 không overwrite chunk đã có. |
| Artifact contract | ID normalization, duplicate keys/docs, NaN/Inf, source hash/corpus mismatch, chunk mapping lệch. |
| Submission | Đủ query IDs, integer doc IDs, không duplicate doc, chunk đúng doc/body, corpus hợp lệ và ZIP đúng schema. |

Test với fixture bảo vệ cơ chế và lỗi đã thấy. Không viết hàng loạt test chỉ lặp lại công thức implementation mà không bắt được lỗi thực tế.

### 16.2. Quy mô và cách ước lượng tài nguyên

- 1.200 query x 200 doc = 240.000 candidate pairs.
- 1.200 query x 1.000 doc = tối đa 1.200.000 pairs trước các giới hạn/thiếu query.
- 100 query x 400 doc = khoảng 40.000 pairs cho pilot.

Pairs không phải số doc duy nhất. Sparse cache nên encode unique docs/chunks một lần.

Trước GPU job:

1. Đo N_unique_docs, N_chunks, độ dài token thực và truncation.
2. Benchmark một batch đại diện trên GPU được cấp.
3. Ước thời gian từ throughput đo được, cộng I/O và padding; ghi khoảng thay vì cam kết một số chính xác.
4. Ghi peak VRAM/RAM, disk cache và khả năng resume.
5. Nếu vượt ngân sách đã chọn, giảm subset hoặc báo quyết định; không tự tăng tới full corpus.

Không giả định VRAM 2 card được cộng thành một vùng nhớ. Hạ tầng từng được ghi là máy dùng chung; phải kiểm tra tài nguyên hiện tại, chọn device và không dừng tiến trình của người khác.

### 16.3. IDF và I/O

DF trên body có thể cần scan toàn corpus, dù chỉ tính cho query vocabulary. Đây là chi phí CPU/I/O cần đo, không phải miễn phí.

Batch đọc SQLite, cache body/features theo doc_id và hash, tránh một kết nối hoặc một SELECT cho từng pair. Không nạp toàn bộ corpus vào RAM chỉ để tính coverage.

### 16.4. Read-only và resume

- Source SQLite mở read-only.
- Feature/cache/output đặt ở đường dẫn experiment riêng.
- Chunk offset/body hash phải cùng snapshot.
- Resume theo khóa duy nhất và config hash; không append trùng record.
- Partial output không được coi là completed run.
- Thay model/matcher/config thì tạo cache version mới.

### 16.5. Chạy kiểm tra

Sau khi có thay đổi code, chạy tests phù hợp và bộ offline hiện có nếu môi trường đủ dependency:

~~~powershell
python -m unittest discover tests
~~~

Audit dữ liệu thật chỉ báo pass khi dữ liệu tồn tại và đã thực sự chạy. Không chuyển một test fixture xanh thành trạng thái real-data audit passed.

---

## 17. Quy tắc quyết định và báo cáo

### 17.1. Ba kết luận hợp lệ

| Quyết định | Điều kiện |
|---|---|
| keep | Có gain thực tiễn trên metric hợp lệ/holdout, kiểm tra kỹ thuật qua và chi phí chấp nhận được. |
| reject | Thua control, không có tín hiệu bổ sung hoặc gain không tương xứng chi phí trong mục tiêu đã chọn. |
| inconclusive | Thiếu nhãn, sample nhỏ, CI rộng, artifact không đủ hoặc evaluator chưa xác minh. |

Không đổi inconclusive thành reject chỉ vì chưa có data; cũng không đổi thành keep nhờ proxy đẹp.

### 17.2. Ngưỡng thành công

Trước confirmatory evaluation, ghi:

- primary metric;
- mức cải thiện nhỏ nhất đáng quan tâm;
- regression tolerance theo ngôn ngữ/failure mode;
- ngân sách tính toán và annotation;
- CI hoặc tiêu chuẩn paired comparison;
- số lần nhìn holdout/official score cho phép trong protocol.

Không đặt một con số gain bắt buộc trong proposal rồi gọi là đã có căn cứ. Mức đáng quan tâm phụ thuộc baseline, noise và chi phí đo được.

### 17.3. Điều kiện giữ adaptive

Adaptive chỉ được chọn khi:

1. Vượt best fixed đủ mạnh dùng cùng components/pool.
2. Không dựa vào hidden labels, p(gold) làm gold hoặc holdout tuning.
3. E(q) có bằng chứng gắn với lợi thế tương đối, hoặc các controls đủ để loại giải thích giả.
4. Kết quả ngoài dev không có regression nghiêm trọng trong phạm vi đã đánh giá.
5. Có cost report, reproducibility và fallback.

Nếu fixed evidence thắng nhưng adaptive không thắng, chọn fixed evidence. Nếu chunk experiment thắng độc lập, giữ nó mà không gán gain đó cho gate.

### 17.4. Những cách kết luận không được dùng

- Coverage tăng nên Doc F2 chắc tăng.
- Qwen tự chấm cao nên retriever mới đúng hơn.
- Cùng 200 doc nhưng đổi thứ tự nên recall document tăng.
- Sparse gần BM25 hơn nên sparse tốt hơn.
- Silver oracle thấp nên mọi adaptive method đều không có khả năng.
- Local manual labels khác leaderboard nên chắc chắn BTC có pooling bias.
- Mỗi nhánh riêng tăng một ít nên ghép lại sẽ cộng tất cả gain.

Pooling bias là giả thuyết có thể phân tích, không phải kết luận chỉ từ một model mạnh hơn nhưng điểm thấp hơn.

### 17.5. Mẫu report

~~~text
Experiment ID / hypothesis / status

1. Câu hỏi và thay đổi duy nhất
2. Parent/control và lý do chọn
3. Artifact versions/hashes, pool, query split, model/matcher/evaluator
4. Feature availability và annotation coverage
5. Metric thật/local/proxy; paired estimate và CI nếu hợp lệ
6. Những query/doc được thêm và mất; hard negatives
7. Chunk impact tách với document impact
8. CPU/GPU/RAM/VRAM/disk/annotation cost
9. Regressions, bất định và giới hạn kết luận
10. Quyết định keep/reject/inconclusive
11. Experiment tiếp theo được dữ liệu hiện tại hỗ trợ
~~~

---

## 18. Checklist giao việc cho AI agent

### 18.1. Việc đầu tiên khi bắt đầu triển khai

- [ ] Đọc proposal này, HANDOVER, CLAUDE và các mục PROGRESS liên quan.
- [ ] Kiểm tra hướng dẫn repo, git status; giữ nguyên các thay đổi có sẵn của người dùng.
- [ ] Không tự tạo toàn bộ kiến trúc hoặc chạy job nặng.
- [ ] Lập inventory và báo artifact nào thiếu.
- [ ] Xác nhận exact baseline scorer/beta, pool và corpus version.
- [ ] Nêu rõ luật evaluator đã được xác minh tới đâu.
- [ ] Chọn một phạm vi experiment: P200, PLARGE hoặc chunk-only.

### 18.2. Deliverables vòng triển khai đầu

1. DATA_READINESS.md: artifact, schema đã xác minh, blocker cụ thể.
2. baseline_manifest.json: reported/observed tách riêng; không giả reproduction.
3. EVALUATOR_CONTRACT.md: macro/chunk rules, phần chưa biết và các test.
4. Adapter + evidence matcher tối giản, có availability/provenance.
5. Feature table pilot hoặc explicit missing-data report.
6. Baseline parity tests và stress tests liên quan.
7. L0 report; nếu đủ nhãn thì thêm một fixed residual experiment.
8. Đề xuất next step dựa trên số đo, không tự động chạy hết ma trận.

### 18.3. Chưa làm trong vòng đầu

- [ ] Không train learned router/reranker mới.
- [ ] Không full-corpus sparse indexing hoặc crawl thêm.
- [ ] Không refit p(gold) của snapshot.
- [ ] Không đổi chunk boundaries, tokenizer BM25 và allocation cùng lúc.
- [ ] Không dùng closed LLM làm nhãn/sinh dữ liệu cho experiment.
- [ ] Không nâng baseline hoặc nộp leaderboard chỉ từ proxy/unit tests.

### 18.4. Definition of Done cho toàn đề xuất

- [ ] Baseline tái lập được hoặc có blocker report có bằng chứng.
- [ ] Feature/evaluator contracts rõ và được kiểm thử.
- [ ] Fixed controls được so công bằng.
- [ ] Adaptive có kết luận keep/reject/inconclusive từ dữ liệu phù hợp.
- [ ] Sparse/chunk/expansion được báo cáo như nhánh độc lập nếu có chạy.
- [ ] Mỗi gain có artifact/config/metric/cost và giới hạn.
- [ ] Tích hợp cuối có interaction check, integrity checks và rollback.
- [ ] Báo cáo kết quả âm tính được lưu đầy đủ.

---

## 19. Nguồn và giới hạn của proposal

### 19.1. Nguồn nội bộ

- [HANDOVER.md](HANDOVER.md): snapshot baseline và artifacts.
- [BIOMEDICAL_ADAPTIVE_RETRIEVAL_AGENT_PLAN.md](BIOMEDICAL_ADAPTIVE_RETRIEVAL_AGENT_PLAN.md): plan BEAR trước đó.
- [CLAUDE.md](CLAUDE.md): bối cảnh, luật ghi nhận, hạ tầng và đính chính.
- [PROGRESS.md](PROGRESS.md): lịch sử đo; chú ý ngày 07/10, 12–15/10 và các đính chính.
- [METHODS.md](METHODS.md): cơ chế/phương pháp lịch sử; không thay thế snapshot mới.
- [PIPELINE.md](PIPELINE.md): thiết kế pipeline và lịch sử quyết định.
- [index/fuse.py](index/fuse.py), [index/bm25.py](index/bm25.py), [index/bm25_ent.py](index/bm25_ent.py).
- [index/dense.py](index/dense.py), [index/dense_chunks.py](index/dense_chunks.py).
- [query_processing/expand.py](query_processing/expand.py), [query_processing/translate.py](query_processing/translate.py).
- [scripts/build_best.sh](scripts/build_best.sh), [scripts/val_calib.py](scripts/val_calib.py), [val_calib.py](val_calib.py).
- [submit/submission.py](submit/submission.py), [submit/score.py](submit/score.py), [utils/audit.py](utils/audit.py).

File biomedical_multilingual_hybrid_retrieval_project.md được plan cũ dẫn chiếu không có trong checkout khi soạn. Proposal này không tuyên bố đã đọc file đó.

### 19.2. Nguồn kỹ thuật bên ngoài

- [BGE-M3 model card và sparse API chính thức](https://huggingface.co/BAAI/bge-m3).
- [M3-Embedding paper](https://arxiv.org/abs/2402.03216): dense/sparse/multi-vector và multilingual retrieval.
- [ViBioMIR dataset card](https://huggingface.co/datasets/AIGuruTinix/ViBioMIR): query/corpus schema và dữ liệu công bố.

Các trang ngoài có thể thay đổi. Khi thực nghiệm phải pin revision/snapshot; nguồn trực tuyến không thay thế đặc tả BTC đã khóa cho một lượt chấm.

### 19.3. Giới hạn hiện tại

Chưa có corpus/ranking/calibration artifacts thật trong checkout để tái lập. Chưa có qrels đầy đủ hoặc PDF luật chấm gốc để kiểm tra độc lập. Chưa benchmark evidence, sparse hay adaptive mới.

Mọi công thức, interface và lộ trình mới là thiết kế có thể kiểm chứng. Giá trị của BEAR sẽ được quyết định bởi việc evidence có cải thiện lựa chọn tài liệu/đoạn và có dự báo đúng lợi thế giữa retriever trên dữ liệu ngoài tuning hay không.
