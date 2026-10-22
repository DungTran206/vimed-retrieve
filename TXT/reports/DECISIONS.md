# Quyết định hiện hành — BEAR v5

Cập nhật 22/10/2026. Theo [handover](../TXT_handover.md), [algorithm](../BEAR_ALGORITHM.md), [study](../BEAR_REPLACEMENT_STUDY.md) và [report v5](SAPBERT_V5_20261022.md):

| Quyết định v5 | Ý nghĩa |
|---|---|
| Giữ BM25/dense fusion và lexical medical gate | Sap similarity không biến thành lexical match hoặc source-backed alias |
| Kết hợp generic dense và SapBERT-XLMR | λ=0,30 ước lượng; λ=0/1 là đối chứng giữ/thay dense |
| Enrichment từ KB có nguồn | LLM chỉ chọn whitelist, cap 8 terms/256 candidates; không tự sinh fact |
| Trích literal terms một lần/document | Exact spans và corpus identity, dùng lại cho nhiều queries |
| Full raw cosine/score cache | Tune tham số offline, không chạy lại LLM/encoder |
| LLM shortlist selector tùy chọn | Chỉ chọn subset có identity hợp lệ; đo riêng chi phí và mất recall |
| Chưa promote baseline | Tests/preflight không chứng minh gain trên 593 query thật |

Branch hiện `Tung`; người dùng tự tạo branch thử nghiệm. Giữ results/provenance và completed artifacts; prose snapshots cũ dọn theo [cleanup](CLEANUP_20261022.md).

## Quyết định lịch sử 20/10/2026 — prototype hai phần

Bảng dưới ghi quyết định của kế hoạch v3.5 tại thời điểm đó; workflow hiện hành theo v5 phía trên.

| Quyết định | Ý nghĩa |
|---|---|
| Giữ cả Retriever/Fusion | Hai search spaces, không thừa |
| Retriever tìm corpus/index độc lập | Có thể lấy doc ngoài union, không baseline pool |
| Fusion thay RRF trên dedup union | Không thêm docs ngoài union của query |
| Shared index/scorer | Tránh hai engine trùng/lệch nhau |
| B0/BR/BF chính | BR thay đầu ra generator+fusion VI, BF chỉ RRF; cùng lang/top-k/corpus/query/ZH/downstream |
| Bỏ F1-first/S1-deferred | Hai nghiên cứu độc lập, D1/DC1/R1/C1 không chặn Retriever |
| Prototype corpus_parts_v1 | Stdlib BM25/explicit relation rules, chưa full biomedical NLP |
| Không relations thì lexical-only | Không gọi lexical score là hiểu relation/intent |
| Chunk refs/bear_window diagnostic | Chưa native selected_chunks/submission selector |
| Legacy 2.0.0 riêng | Fixed200/w045 runner không giả BR/BF |
| 0,391 là control | Chưa đủ runtime linkage/parity, chưa rerun/quality gain |
| Cùng downstream/budget | Doc mới cần Qwen thật, không gán 0/bỏ doc/áp p̂ threshold lên BEAR score |
| Joint optional sau bằng chứng | Không cộng gain hoặc giữ phần gây hại chỉ đủ module |
| Labels offline | Unknown/weak not_gold không tự âm, evidence không gold |
| L1/L4 giữ scope cũ | Không đổi tên coverage để thử lại/claim gain |
| Không tải model trong prototype | Không đồng nghĩa Qwen end-to-end chạy CPU; chưa ZH recall parity |

[Log](../improvement_log.md) giữ lịch sử. v3.5 thay ưu tiên F1 và trì hoãn Retriever của v3.4. [PLAN v3.2](CLEANUP_20261022.md) threshold-only đã được thay. Nguồn/completed artifacts chỉ đọc; output mới dưới TXT.
