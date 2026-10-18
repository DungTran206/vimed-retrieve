# METHODS.md: các phương pháp đang dùng và đang thử, giải thích sâu

Viết 07/10/2026 để người mới (và bài working notes) hiểu **từng phương pháp làm gì, vì sao, đã đo ra sao, đang ở trạng thái nào**.
Số đo gốc nằm ở `PROGRESS.md` (§2 nhật ký, §2b bảng lượt nộp); file này là bản đọc để hiểu, không thay sổ số đo.
Quy ước trạng thái: ✅ đang dùng trong bài tốt nhất · ❌ đã đo, thua/không đáng · ⏳ đang chạy hoặc chờ điểm · 💡 chưa làm.

**Điểm hiện tại (public LB): FINAL 0,2682** = (doc F2 0,2956 + chunk F2 0,2408) / 2, k=200. Bài: `runs/blendQB3x_cr.zip`.

---

## 0. Luật chấm quyết định mọi thiết kế

- **Doc F2 = 5g/(4G+k)** (g = doc đúng trong k doc nộp, G = số nhãn vàng, đo được G ≈ 70/câu). Thêm một doc chỉ có lợi nếu xác suất đúng p > F2/5 ≈ 0,06.
- **Điểm doc chỉ phụ thuộc TẬP doc nộp**, không phụ thuộc thứ tự (đã chứng minh: cùng tập → P/R y hệt). Thứ tự chỉ quan trọng cho tầng chunk, vì chunk lấy từ các doc đầu danh sách.
- **FINAL = (doc F2 + chunk F2) / 2**, hai tầng **độc lập tuyệt đối** (đã xác nhận hai lần bằng bài ghép). Nên tối ưu từng tầng riêng, rồi ghép.
- **Trần lý thuyết:** pool hiện tại chứa 61% nhãn (~43 doc vàng/câu). Dù rerank hoàn hảo, doc F2 ở k=200 chỉ ≤ 5×43/(280+200) ≈ **0,45**. Muốn FINAL 0,5 cần pool recall ~0,85 VÀ rerank gần hoàn hảo VÀ chunk F2 ~0,5: không khả thi bằng cách làm hiện tại.
- Chunk: bộ chấm ưu ái chunk **dài** (900 token thắng 400 token rất xa), `chunk_text` phải nguyên văn → lưu offset `(doc_id, start, end)`, không lưu text.
- `doc_id` trong JSON phải là **số nguyên**; ZIP ≤ **100 MB** (bài tốt nhất ~90–94 MB, đây là ràng buộc cứng của tầng chunk).

---

## 1. Kho dữ liệu (store)

| Nguồn | Trạng thái | Ghi chú |
|---|---|---|
| Tiếng Việt (747k URL) | ✅ ~689k doc dùng được, `data/corpus_vifull.sqlite` (đã `clean.py` + `chunk.py`), `data/vi_slim.sqlite` cho truy vấn | ~51k URL Long Châu `prio=0` chưa cào: **đo 07/10 có nhãn (P 0,0174) → đang crawl nốt** |
| Tiếng Trung (3,38M URL) | store GPU `~/vimed/data/corpus.sqlite` = bản local `data/corpus_gpu_shard0.sqlite` (1,43M doc, 42,2%); shard 2/5 của I2 (`data/queue_zh1.sqlite`) +297k doc → ~51% | zh chỉ ~2,6–4% nhãn: **không đáng đầu tư thêm** |
| Tiếng Anh/PubMed | ✅ Đã tích hợp trong ViBioMIR | Không cần tải riêng hoặc gọi API PubMed |

Thứ tự chuỗi dữ liệu bắt buộc: `crawler.py → clean.py --apply → chunk.py → audit.py`.

---

## 2. Truy hồi vòng 1: năm nguồn + RRF → "pool F"

Mỗi nguồn trả top-1000 doc cho mỗi câu; gộp bằng **RRF** (`index/fuse.py`): `score(d) = Σ_nguồn w / (60 + rank)`.

| # | Nguồn | File | w | Ý tưởng |
|---|---|---|---|---|
| 1 | **Slug BM25** | `slug_bm25.py` | 1 | URL tiếng Việt chứa nguyên tiêu đề → BM25 trên slug, không cần crawl. Nguồn duy nhất trả được doc chưa crawl |
| 2 | **BM25F có dấu** (+ biến thể meta) | `bm25.py --keep-diacritics` | 1 | BM25 theo trường: title 3× / tags 2× / descr 1,5× / body 1×. Site Q&A có title = câu hỏi bệnh nhân → khớp câu hỏi với câu hỏi. Bỏ dấu cũ thua bản có dấu |
| 3 | **Dense title** | `dense.py` (BGE-M3) → `emb_vi2` | **2,5** | Embed title của 686k doc vi |
| 4 | **Dense nội dung** | `dense.py --body-chars 600` → `emb_viB2` | **2,5** | Embed title + 600 ký tự đầu body. Hai nguồn dense bầu cho gần như cùng doc nhưng vẫn thêm doc mới |
| 5 | **BM25 entity** | `bm25_ent.py` | 1 | Qwen3.5 trích thực thể y khoa → BM25 trên cụm từ khoá + bigram |

Bài học đã đo:
- Nguồn thứ 2 (BM25F) cho +22% doc F2, nguồn thứ 3 chỉ +2,6%; nguồn **cùng họ** (tương quan 82%) còn làm hại. Mỗi nguồn mới phải **khác loại**.
- **Dense là đòn lớn nhất** (+32,8% cả hai tầng). Quét trọng số dense: 1,0→0,1705 · 1,5→0,1799 · **2,5→0,1845** · 4,0→0,1822 · chỉ dense→0,1680 · không dense→0,1284. Một đỉnh, nên w=2,5.
- Lệch trọng số về slug hay meta (×2) đều hại: w ngang nhau là tốt.
- Recall pool ở k=1000: D 0,5613 → E 0,6045 (phủ đủ kho vi) → **F 0,6108** (+entity).

---

## 3. Rerank: Qwen3-Reranker-4B ✅

`qwen_rerank.py`. Mô hình `Qwen/Qwen3-Reranker-4B` (Apache-2.0, 06/2025, 4B) đọc prompt gồm chỉ dẫn + câu hỏi + tài liệu (title + ~1000 ký tự đầu), điểm = **P("yes") so với P("no")** ở token cuối (chỉ tính `lm_head` cho vị trí cuối để khỏi hết VRAM).
- Chấm **top-400** của pool F (≈ 25 cặp/s/4090). Trộn **RRF(Qwen w2, vòng 1 w1)**, cắt top-200.
- Chấm sâu có **lợi suất giảm**: top 100→250: doc +4,2%; 250→400: doc +1,4%. Không chấm thêm.
- Qwen thắng bge-reranker-v2-m3 rõ (chunk +10,5%); **trộn thêm bge thì thua Qwen một mình**.
- Điểm Qwen bão hoà (nhiều doc 0,9+) nên ngưỡng cố định theo P(yes) không dùng được.

---

## 4. Tầng chunk ✅

`chunk.py` + `submission.py`. Chunk ~900 token (gộp đoạn liên tiếp cắt theo `\n`, chồng lấn 1 đoạn). 76% doc vừa trọn 1 chunk.
- Công thức nộp: **2 chunk × 40 doc đầu + 1 chunk × doc hạng 41–70** (`--chunks-per-doc 2 --chunk-from-top 40 --extra-one 70`). Hơn 2×64: chunk thứ hai của doc hạng 41–64 đóng góp ~0 recall.
- **Chọn chunk bằng Qwen** (`chunk_rerank.py`, `--chunk-scores`): chấm mọi chunk của doc top-40 có ≥3 chunk (36.568 chunk), lấy 2 chunk điểm cao nhất. Kết quả **+0,25% chunk F2** (4,1% chunk đổi): đúng dự báo vì ít doc có chỗ để chọn.
- ❌ Chọn chunk theo trùng từ khoá (IDF): −0,3%. ❌ Chunk 400 token: thua nặng (0,0624 vs 0,1765).
- ZIP 100 MB giới hạn số chunk; ý tưởng 💡 nén LZMA/BZIP2 để nhét thêm chunk (chưa biết server đọc được không; lợi nhỏ: +9,6% chunk chỉ +1,9% chunk F2).

---

## 5. Các hướng mở rộng pool đã đo (đều để tìm nhãn bị bỏ sót)

Cách đo thống nhất: bài **"chỉ doc mới"**: 150 doc/câu hạng cao của nguồn thử mà **không** nằm trong pool F top-1000, chunk rỗng. `DOCS_RECALL` của bài = phần nhãn nguồn đó cứu thêm ngoài pool (mốc pool 0,6108).

| Hướng | Cách làm | File | Kết quả |
|---|---|---|---|
| ❌ **HyDE** | Qwen3.5-9B viết 2–3 câu trả lời giả định → BGE-M3 trên `emb_viB2` | `hyde.py`, `scripts/run_hyde.sh` | `qhyde` (câu hỏi + giả định) DOCS_R **0,0084**, `hyde` thuần **0,0068** |
| ❌ **Qwen3-Embedding-4B title** | Embed title bằng Qwen3-Embedding-4B (MTEB 70,6 vs 63,0), query có tiền tố Instruct | `scripts/run_qemb.sh` | DOCS_R **0,0080**; 73 doc/câu ngoài pool nhưng bắt nhãn bạc kém BGE |
| ❌ (yếu) **PRF (Rocchio dense)** | Trung bình vector top-20 sau Qwen → tìm láng giềng trong kho vi | `prf.py` | DOCS_R **0,0108** / P 0,0061: tốt nhất trong các nguồn mở rộng nhưng vẫn ~1% pool; 50 doc/câu ngoài pool, trùng 98/200 với top-200 hiện tại |
| ⏳→❌? **Tách ý con** | Qwen3.5-9B tách câu thành ≤4 câu con, BGE-M3 xếp hạng từng ý, RRF theo ý | `decompose.py`, `scripts/run_subq.sh` | Chạy xong 07/10. Qwen tách **quá tay**: 827/1200 câu ra đủ 4 ý (kể cả câu ngắn, 153 câu giữ nguyên). Offline: bắt nhãn bạc **thấp hơn** câu gốc (body 99,8 vs 115,8; title 80,6 vs 91,2); 33–35 doc/câu ngoài pool. Bài `diag_novel_subq_k150` đã dựng nhưng **chưa nộp** (dự báo ~0,008 như HyDE) |
| ✅ (tín hiệu tốt nhất) **Crawl nốt doc vi chưa cào** | Doc vi state≠1 xếp theo slug (Long Châu 51k URL chưa cào + blog pharmacity lỗi) | `crawler.py --domains nhathuoclongchau.com.vn`, `diag_uncrawled_vi_k150` | DOCS_P **0,0174**, DOCS_R **0,0181**: cao nhất mọi nguồn mở rộng, ~1,2 nhãn/câu. Đang crawl (thử 300 URL: 298/298 thành công) |
| ❌ **Adaptive Gated Fusion** (đề xuất `PROPOSAL_ADAPTIVE_FUSION.md`) | Gate sigmoid theo độ hiếm từ vựng để chọn trọng số BM25/dense từng câu | `silver_gate_test.py` | Oracle theo từng câu chỉ hơn trọng số chung +1,56% (nhãn bạc) → bỏ |
| ❌ **zh** | dense title zh, BM25F zh (query đã dịch) trộn vào vòng 1 | `dense.py`, `bm25.py` trên store GPU | thua: g_zh 0,32–0,54 doc/câu so với precision biên vi 0,03; zh chỉ ~2,6% nhãn ở độ phủ ~35% |

**Cảnh báo phương pháp:** "nhãn bạc" (top-200 của bài hiện tại) chỉ chứa doc đã ở pool, nên **không đo được recall mới**; chỉ dùng để loại sớm và so các cấu hình trong pool. Recall mới chỉ đo được bằng lượt nộp.

Bốn nguồn dense/entity cho 0,008–0,011 DOCS_R → pool chạm tường với phương pháp dense; nhãn còn thiếu khác loại với thứ embedding bắt được (PRF tốt nhất, 0,0108, vẫn thấp). Chờ tách ý con để chốt.

---

## 6. Rủi ro & cách làm việc với lượt nộp

- Public 10 lượt/ngày; **private chỉ 5 lượt tổng**. Dùng public để chốt cấu hình, giữ 2–3 bài đã dựng sẵn cho private (ZIP < 100 MB).
- Private dùng đúng 1.200 câu này; dùng leaderboard để chọn cấu hình và đo nhóm lớn. **Không dò nhãn từng doc** (có thể bị coi là lạm dụng; chưa hỏi BTC).
- `load_candidates()` **sắp lại ứng viên theo điểm giảm dần** → file tự ghép phải có điểm giảm đều theo vị trí (đã mất 1 lượt vì lỗi này).
- Vân tay (`fingerprint` trong `submission.py`): doc theo **tập**, chunk theo văn bản có thứ tự; ghi cùng điểm để biết hai bài có thật sự khác nhau.

## 7. Hướng đi còn lại (xếp theo kỳ vọng, 07/10)

1. Hoàn tất PRF và tách ý con (chờ điểm / chờ GPU). Nếu có nguồn ≥ 0,02 DOCS_R: rerank doc mới bằng Qwen rồi đưa vào danh sách.
2. **Rerank mạnh hơn:** Qwen3-Reranker-8B (hợp lệ ≤15B), ensemble reranker/prompt. 💡 chưa làm; ước tính vài % doc F2, ~6 giờ GPU cho top-250.
3. **Định lượng nhãn bị mất theo nhóm** (domain, doc chưa crawl) bằng bài thăm dò. 💡
4. **Chưng cất teacher >15B** để fine-tune reranker (được phép khi huấn luyện). Rủi ro: không có nhãn vàng. 💡
5. Working notes paper (`PROGRESS.md` + file này là nguyên liệu; kết quả âm tính HyDE/gate/Qwen3-Emb là phần có giá trị).

## 8. Rà soát lỗ hổng (07/10/2026, số đo trên dữ liệu thật)

| # | Phát hiện | Số đo | Hệ quả / việc làm |
|---|---|---|---|
| 1 | **Reranker và dense chỉ thấy phần đầu doc** (✅ đã thử Qwen 3.000 ký tự 08/10: KHÔNG hơn 1.000, P@50 0,0787 vs 0,0791) | Qwen đọc title + 1000 ký tự, BGE dense title + 600 ký tự; thân bài trong top-200 trung vị **4.165 ký tự**, P90 6.823; **96% doc top-200 dài hơn 1000 ký tự** | Nhãn nằm sâu bị bỏ sót khi xếp hạng. Thử: Qwen đọc 2.500–3.000 ký tự hoặc chunk tốt nhất; dense cấp chunk. Đo bằng bài top-50 trên tập con câu |
| 2 | **Nén ZIP tốt hơn → nhét thêm chunk trong 100 MB** ✅ **bzip2 được server chấp nhận (07/10)**; `submission.py --zip-method bzip2` | Trên 40 MB mẫu: bzip2 = 0,65×, LZMA = 0,63× dung lượng deflate (6,6 / 6,3 / 10,1 MB) | Cùng trần 100 MB có thể chứa ~1,5× chunk. Chưa biết server chấm đọc được bzip2/LZMA không; bài lỗi định dạng không tính quota. Thử trước bằng chính bài tốt nhất (nếu điểm y hệt thì mở rộng độ sâu chunk) |
| 3 | **Bản sao** | Doc cùng title với top-40 mà ngoài top-200: 2,7/câu. Trùng body nguyên văn: phần lớn là **laodong.vn: 4.364 doc dùng chung MỘT body 747 ký tự** (rác/boilerplate, trích nội dung hỏng) | Thêm bản sao title: lợi nhỏ (~+1–2% ước tính). laodong: crawl/trích lại; chunk của các doc này vô nghĩa (hiện chỉ 0,63 doc/câu ở top-40) |
| 4 | **Qwen "dễ tính" hơn nhãn vàng** | Qwen P(yes) > 0,5 cho ~130 doc/câu, > 0,9 cho ~32 doc/câu, trong khi G ≈ 70 | Nhãn vàng hẹp hơn "liên quan chủ đề"; thêm tín hiệu "có câu trả lời" có thể tăng precision. Không dùng ngưỡng P(yes) cố định |
| 5 | **G gần như hằng số?** | Suy G từ P/R của 5 bài khác nhau: 69,5 · 68,7 · 70,5 · 69,9 (zh-only, k=1000, pool D, pool F) | Nếu mỗi câu ~70 nhãn thì cắt k theo câu vô ích (khớp Meng 2024). Giả thuyết: nhãn = danh sách cố định từ hệ thống tham chiếu của BTC (chưa xác nhận) |
| 6 | **Không có rò rỉ** | Chỉ 18/1200 câu hỏi trùng title doc vi y hệt; cả 18 nằm hạng 1 trong top-200 | Không có lối tắt "câu hỏi = title" |
| 7 | **Điểm Qwen không bão hoà** | P(yes) > 0,99 chỉ 0,4% cặp; điểm trùng nhau trong top-100 TB 15/câu (bản sao cùng văn bản) | Lưu điểm 6 chữ số là đủ |
