# EVALUATOR CONTRACT — Biomedical Evidence-Aware Retrieval (BEAR)

> Ngày thiết lập: **19/10/2026**. Quy định nghiêm ngặt ba tầng evaluator nhằm ngăn chặn việc ngộ nhận proxy/local metric thành điểm chính thức BTC.

## 1. Ba tầng Evaluator (§10.1)

| Tầng | Tên & Phạm vi | Triển khai được | Không được khẳng định |
|---|---|---|---|
| **Lớp 1** | **Legacy Proxy** (`submit.score`) | Chạy hàm kiểm tra nhanh substring / bag-of-words token overlap của baseline cũ; smoke check định dạng. | Không phải LCS token, không phải luật chấm official của BTC, không phản ánh F2 chính thức. |
| **Lớp 2** | **Local Diagnostic & Evaluator** (`evaluation.py`) | - Token sequence LCS với không gian O(min(m, n)) memory.<br>- Doc P@K, macro Doc F2 trên complete universe đã đóng băng.<br>- Paired replacement $\Delta P@200$ có completeness guard (bắt buộc judged toàn bộ added/removed docs). | Không suy diễn Recall hay F2 toàn corpus khi nhãn incomplete. Không gọi `local_whitespace_lcs_v1` là `official_chunk_f2`. |
| **Lớp 3** | **Runtime / Official Reproduction** | Parse và tái kiểm tra macro F2 từ artifact `scoring_result.zip` trên 593/600 queries có gold > 0. | Chưa có file tokenizer chính thức (`/app/program/tokenizer.json`) trong repo nên không tự ý gán nhãn official tương đương. |

---

## 2. Công thức Chuẩn hóa (§10.2 & §10.3)

### 2.1. Document F2 Macro
- Với mỗi query $q$:
  $$F_2(q) = \frac{5 \cdot g_q}{4 \cdot G_q + k_q}$$
  trong đó $g_q$ là số relevant docs retrieved, $G_q$ là tổng số gold docs, $k_q$ là số docs retrieved.
- **Chính sách Empty-Gold**: Theo quan sát từ `scoring_result.zip`, `macro_empty_gold = "excluded"`, chỉ tính trung bình trên các query có $G_q > 0$. Macro $F_2 = \frac{1}{|Q_{G>0}|} \sum_{q \in Q_{G>0}} F_2(q)$.
- Nghiêm cấm tính $F_2$ từ trung bình Precision và trung bình Recall:
  $$F_2(\text{mean}(P), \text{mean}(R)) \neq \text{mean}(F_2(q))$$

### 2.2. Token LCS Diagnostic cho Passages
- Điều kiện match diagnostic:
  $$\text{match} = (\text{qid}_{\text{pred}} == \text{qid}_{\text{gold}}) \land (\text{doc}_{\text{pred}} == \text{doc}_{\text{gold}}) \land \left(\frac{\text{LCS}(\text{pred\_tokens}, \text{gold\_tokens})}{|\text{gold\_tokens}|} \ge 0.40\right)$$
- Bảo toàn thứ tự token (sequence alignment), không phải bag-of-tokens.

### 2.3. Paired Replacement Completeness Guard
- So sánh hai hệ thống $A$ và $B$ tại cùng độ sâu $k=200$:
  $$\text{added} = A \setminus B, \quad \text{removed} = B \setminus A$$
- **Bắt buộc**: Toàn bộ documents trong $\text{added} \cup \text{removed}$ phải có ground-truth judgment. Nếu thiếu dù chỉ 1 doc, trả về trạng thái `not_available` kèm danh sách unjudged docs, tuyệt đối không gán nhãn 0 ngầm.
- Nếu đầy đủ:
  $$\Delta \text{hits} = \sum_{d \in \text{added}} \mathbb{I}(d \in \text{Rel}) - \sum_{d \in \text{removed}} \mathbb{I}(d \in \text{Rel}), \quad \Delta P@200 = \frac{\Delta \text{hits}}{200}$$

