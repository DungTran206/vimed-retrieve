# Runbook — BEAR-Retriever và BEAR-Fusion

## Hiện hành 22/10/2026 — v5 SapBERT-XLMR

Điểm tiếp nhận là [handover v5](../TXT_handover.md), [templates](../configs/medical_hypothesis/README.md) và [report triển khai](SAPBERT_V5_20261022.md). Workflow hiện hành:

```text
kb-import → prepare → cache → document-terms → sapbert-cache
          → fit → tune → run → [select tùy chọn] → evaluate
```

Từ repository root, inspect bằng `python -B -m TXT.bear.medical_cli <stage> --config <path>`; chỉ thêm `--execute` khi đã bind input thật. SapBERT dùng `sapbert_cache.template.json`; selector dùng `select.template.json`. Outputs mặc định mới dưới `TXT/runtime/medical_v5/`, mỗi recipe/input/code khác dùng output_dir mới.

Lexical gate giữ exact/source aliases; dense mới trộn generic/SapBERT với λ=0,30 ước lượng. Fit chỉ học BM25 sigmoid. Full raw scores/cosines cho phép tune không gọi lại LLM/encoder. Selector chỉ chọn subset shortlist của run và cần corpus identity khớp.

Kiểm chứng kỹ thuật cuối sau cleanup: full TXT suite 173/173 tests qua, 10/10 legacy tests qua. Mười templates được preflight; 72 tuning configs hợp lệ trong max_trials=96. Chưa gọi model thật/đo quality gain. Lệnh và chi tiết đầy đủ theo handover; các đoạn bên dưới giữ recipe lịch sử/control, không thay v5.

## Lịch sử 21/10/2026 — hypothesis medical gate v4

Tại phiên bản v4, workflow medical gate đã có code chạy. Handover/proposal hiện đã được v5 thay thế; [report v4](MEDICAL_HYPOTHESIS_20261021.md) giữ kết quả kỹ thuật thời điểm đó.

```powershell
python -B -m TXT.bear.medical_cli demo --output-dir TXT/runtime/medical_hypothesis_demo
python -B -m TXT.bear.medical_cli prepare --config TXT/configs/medical_hypothesis/prepare.template.json
```

Stage thật: `kb-import → prepare → cache → fit → tune → run → evaluate`; thêm `--execute` sau khi bind input paths. Nhánh tùy chọn `document-terms` trích terms có offsets trong tài liệu. Templates: [medical_hypothesis](../configs/medical_hypothesis/README.md). LLM Qwen3.5-9B qua endpoint; demo và sweep từ cache không gọi model. `fit` chỉ fit BM25 sigmoid trên calibration queries; `tune` không đọc holdout labels để chọn config.

Run mới stream cache theo query, không nạp mọi spans/candidate của toàn bộ tập vào RAM. Tune giữ IDs/selection metrics thay vì toàn bộ ranking diagnostics của mọi trial. Khi code/input thay đổi, dùng output_dir mới; không sửa hash để ép reuse. Những lệnh bên dưới là workflow corpus_parts_v1/control lịch sử, vẫn dùng được riêng.

Các mục đánh số bên dưới là prototype corpus_parts_v1 theo kế hoạch v3.5, hai paths dùng chung index/scorer, chưa quality evaluation 0,391. Kế hoạch đã được thay bằng v5; [cleanup](CLEANUP_20261022.md) ghi cách xem snapshots cũ.

## 1. Demo chạy ngay

```powershell
python -B -m TXT.tools.demo_bear_parts
```

[Demo](../tools/demo_bear_parts.py) tạo corpus synthetic, index/BR/BF/RRF_control và comparison.json. Đây là engineering-only, không đo baseline/relevance gain. Xem [báo cáo triển khai](BEAR_PARTS_20261020.md) và [inventory thật](bear_parts_preflight_20261020.json).

## 2. Bind inputs thật và build index

Điền [index config](../configs/bear_parts/index.template.json), [retrieve config](../configs/bear_parts/retrieve.template.json), [fusion config](../configs/bear_parts/fuse.template.json) đúng schema. Cùng corpus/query/lang/top-k cho comparison, output dưới TXT, không đè nguồn/completed run.

Index cần corpus snapshot; Retriever cần index/queries, không baseline pool; Fusion thêm source rankings trước RRF. Explicit relations phải neo query; thiếu relations thì lexical-only. Templates chưa baseline linkage, không giả score/control khi thiếu input.

```powershell
python -B -m TXT.bear.cli corpus-index --config TXT/configs/bear_parts/index.template.json --dry-run
python -B -m TXT.bear.cli corpus-index --config TXT/configs/bear_parts/index.template.json --execute
```

Chỉ execute khi inputs thật đã bind. Corpus readonly, stdlib không tải model; kiểm index manifest rồi dùng cùng snapshot cho BR/BF.

## 3. BR — Corpus retrieval độc lập

```powershell
python -B -m TXT.bear.cli retrieve --config TXT/configs/bear_parts/retrieve.template.json --dry-run
python -B -m TXT.bear.cli retrieve --config TXT/configs/bear_parts/retrieve.template.json --execute
```

BR thay đầu ra generator+fusion VI, có thể tìm doc ngoài union baseline. Giữ ZH/downstream control. Không old pool/run fixed200 để giả BR.

## 4. BF — Fusion thay RRF

```powershell
python -B -m TXT.bear.cli evidence-fuse --config TXT/configs/bear_parts/fuse.template.json --dry-run
python -B -m TXT.bear.cli evidence-fuse --config TXT/configs/bear_parts/fuse.template.json --execute
```

Giữ source generators, output subset union của query. BEAR-only không RRF score chính; residual augmentation khác study. BF không prerequisite BR.

## 5. Kiểm output/downstream

Hai inference paths xuất candidates.jsonl/evidence.jsonl/manifest.json trong output_dir. Kiểm id,candidates[{doc_id,score}], đủ query universe, dedup/top-k/scope, manifest identities/version/counts. BF không doc ngoài union; BR đối chiếu docs mới ngoài baseline union.

Chunk refs/bear_window diagnostic, chưa native selected_chunks/submission selector. Relation rules explicit subject/predicate/object/cùng-câu/thứ-tự/polarity chưa full biomedical NLP. Mặc định VI có cấu hình, chưa ZH recall parity; giữ ZH baseline.

B0=baseline retrieval+RRF, BR=Retriever, BF=baseline retrieval+Fusion. Cùng top-k/lang/corpus/query/ZH/Qwen/MaxP/p̂/threshold/chunk policy. Truyền reranker top-k rõ, tránh default thấp hơn budget. Doc mới cache thiếu phải score đúng recipe; không gán 0/bỏ doc/áp p̂ threshold lên BEAR score. Chưa linked recipe thì chưa baseline parity. Model-free candidates chưa end-to-end CPU.

## 6. Đánh giá và gaps

Ghi build/index size/latency/RAM/availability/lexical-only/overlap/changed docs/coverage và Qwen bổ sung. Đủ judgments/scorer mới paired Doc/Chunk/FINAL đúng semantics/query universe/CI/sensitivity. Unknown/weak not_gold không tự âm, không suy FINAL từ ΔDoc/cộng gain BR+BF.

D1/DC1/R1/C1/native chunk selector/exporter later/legacy; joint optional sau bằng chứng từng phần. Chưa gain/rerun baseline 0,391. [Readiness cũ](EXPERIMENT_READINESS_20261020.md) là snapshot input lịch sử, benchmark CPU exact cũ không ETA prototype. GPU của người dùng có thể phục vụ model downstream khi cần.
