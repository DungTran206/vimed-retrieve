# Triển khai medical importance hypothesis — 21/10/2026

Đã cập nhật [proposal](../TXT_Proposal.md), [handover](../TXT_handover.md), algorithm, PLAN, study và README theo yêu cầu hiện hành. Sáu bản v3.5 giữ tại archive. Đây là hypothesis người dùng muốn kiểm chứng; agent tiếp nhận phải giúp chạy các stage khả dụng, ghi hạn chế/kết quả và không lấy phản biện thay cho thử nghiệm.

## Code đã có và trạng thái thực thi

| Phần | Hiện thực | Đã kiểm |
|---|---|---|
| KB | Canonical VI/ZH concept IDs/aliases, relation/source/context; CMeIE adapter cần concept map | Fixtures; chưa nhập KB thật |
| Query LLM | Qwen3.5-9B (<15B), local HTTP, nonthinking, literal anchors, taxonomy bốn tầng, chọn expansion từ whitelist | Mock HTTP/schema; chưa gọi model thật |
| Importance | Hard tier hoặc expected value từ đầy đủ backend label probabilities có provenance | Unit tests; không dùng confidence model tự viết |
| Match | Exact NFC phrase/alias groups, bảo toàn IDs/số và offsets, Han boundaries | Unit tests; không claim general clinical relation understanding |
| Scoring | G=sum(a²×match)/sum(a), original concepts, optional required cap, bounded BM25/dense alpha | Unit tests và demo |
| Normalization | BM25 sigmoid x0/T, raw/query-scale; original/expanded blend; dense affine/configured sigmoid | Unit tests và demo; fit stage chỉ học BM25 |
| Selection | Global/tier-bucket threshold, min/max budget, top-K control, pass/fallback/cap logs | Unit tests và demo |
| Val | Native val/binary qrels, disjoint grouped queries, exposure metadata, judged-only calibration, finite replay menu | Real schema/inventory + synthetic fit/tune; chưa fit real candidates |
| Cache | Raw scores, masks, term spans, source ranks, hashes, per-query/per-document resume; scoring stream theo query | Replay/tamper/partial-external-score/split tests |
| Doc terms | Optional LLM extraction với literal title/body spans, assertion và explicit truncation | Mock HTTP/unit + runner integration; chưa cập nhật index |

Trong cache mặc định, BM25 được tính lại bằng BEAR index cho query original và expanded trên cùng union. Đây không phải cùng score recipe BM25F lịch sử. External BM25/source table có thể được chọn riêng; missing vẫn null, không vá bằng index score khác recipe. Query-scale normalization bị chặn khi scale không tương thích external BM25.

## Những kiểm tra thực sự đã chạy

```powershell
python -B -m unittest discover -s TXT/tests -t .
python -B -m unittest discover -s tests -v
python -B -m TXT.bear.medical_cli demo --output-dir TXT/runtime/medical_hypothesis_demo
python -B -m TXT.bear.medical_cli prepare --config TXT/configs/medical_hypothesis/prepare.template.json
git diff --check
```

Kết quả: **136 TXT tests + 10 legacy tests đạt**; 38 medical tests nằm trong 136, không cộng trùng. Demo offline 12 synthetic queries chạy đủ kb-import/prepare/cache/fit/tune/run/evaluate và RRF control, có fixture labels hoàn chỉnh; tests kiểm lần chạy sau reuse cache và không gọi LLM. Không dùng metric fixture để suy gain y khoa. Demo summary: `TXT/runtime/medical_hypothesis_demo/demo_summary.json` (runtime ignored).

Prepare template inspect trả blocked_input với queries và KB còn thiếu tại paths mẫu; không gọi endpoint. Tám template hợp schema và có inventory thiếu input tại [preflight JSON](medical_hypothesis_preflight_20261021.json). Handover có script xuất query label-free từ val và cách bind index output thật; không cần sửa nguồn val/corpus.

## Dữ liệu thật và việc còn lại khi chạy quality experiment

- Val hiện diện: 593 queries, 22.091 gold entries, 66.547 not_gold entries, 20.186 gold_unseen, không query có complete=true. Native not_gold được dùng theo nhãn file cung cấp; nếu là weak/chunk-derived phải ghi assumption/sensitivity, không gọi clinical gold.
- KB Việt/Trung cụ thể chưa nhập và chưa được xác minh sạch. [Source inventory](../data_sources/medical_sources.json) ghi CMeIE/OpenCMKG, canonical schema và phần cần mapping; không tự tạo dữ liệu/IDs/dịch để giả đủ inputs.
- Chưa có prepared real queries, corpus index và pre-RRF source rankings/scores ở paths mẫu. Cần bind source artifacts hoặc chạy retrieval thật; không điền score 0 cho missing.
- Endpoint Qwen9B chưa được gọi, không tải weights hoặc cài dependency. Actual full class-probability acquisition không được giả lập: default HTTP prepare chỉ tạo hard tiers; expected mode nhận record đã có backend probabilities/provenance được kiểm.
- Doc-term extraction hiện là diagnostic artifact, chưa tự index alias/concept hoặc retrieve vòng hai. Native selected_chunks/submission exporter vẫn thuộc downstream control.
- Không rerun baseline 0,391, không có real retrieval gain, không upload/submit. Những thiếu hụt này hướng dẫn stage cần bind; không phải lệnh dừng hypothesis hoặc yêu cầu làm lại L1/L4/N0/N1 cũ.

Code hashes: [inventory](../manifests/medical_hypothesis_code_inventory.json). Đường vận hành cụ thể và prompts: [handover](../TXT_handover.md).
