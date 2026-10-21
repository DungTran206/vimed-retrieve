# PLAN v4 — Thử medical-gated scoring và adaptive selection

Cập nhật 21/10/2026. Ý tưởng người dùng muốn kiểm chứng là contextual medical salience → observed concept matches → tăng vai trò BM25 khi lexical evidence quan trọng mạnh, tăng dense khi yếu; sigmoid calibration, adaptive threshold và source-backed enrichment cùng cache offline hỗ trợ thực nghiệm.

## 1. Chỉ dẫn ưu tiên

Đây là hypothesis được người dùng yêu cầu thử. Agent phải tiếp tục triển khai/chạy phần có thể chạy và ghi kết quả. Có thể phản biện nhưng không dùng phản biện, lack of prior gain hay prerequisite cũ để trì hoãn experiment được ủy quyền. Thiếu inputs thì báo đúng artifact còn thiếu, chạy demo/available stages; không bịa score hoặc baseline parity.

Canonical docs: [proposal](TXT_Proposal.md), [handover](TXT_handover.md), [algorithm](BEAR_ALGORITHM.md), [study](BEAR_REPLACEMENT_STUDY.md). Workflow mới `TXT.bear.medical_cli`; CLI prototype cũ vẫn là control riêng.

## 2. Các phần cần thử

| Phần | Cấu hình khởi tạo | Điều cần đo |
|---|---|---|
| Query LLM | Qwen/Qwen3.5-9B, dưới 15B, một call/query | JSON/schema/span validity, taxonomy consistency, latency |
| Taxonomy | 4 tiers `[0.05,0.30,0.70,1.00]` | Hard labels vs actual class-probability expectation nếu có |
| Enrichment | KB Việt/Trung disease→symptom, provenance | Alias-only/disease-symptom vs original, recall và drift |
| Calibration | BM25 sigmoid x0/temperature, raw/query_scale | Held-out calibration và retrieval; global vs nhóm khi đủ support |
| Gate/fusion | Absolute salience-weighted observed matches → bounded alpha | Fixed vs adaptive fusion cùng union/budget |
| Selection | Global threshold rồi tier-bucket threshold | Chất lượng cùng mean budget, p95/max candidates và cost |
| Cache | Raw sources/matches/tier labels/probs/identity | Tune không cần LLM/retrieval lại khi inputs không đổi |

`x0` là sigmoid midpoint; final threshold là parameter khác. LLM salience hỗ trợ BM25/dense routing, không phải bắt buộc additive LLM relevance.

## 3. Thứ tự vận hành

1. Inspect current inputs/configs. Bind corpus index, queries, raw pre-fusion sources, labels và intended splits. Ghi rõ source nào chưa có complete union scores.
2. Import normalized KB có provenance; giữ Vietnamese mappings chưa duyệt ở trạng thái đúng. Không coi CMeIE/OpenCMKG là clinical gold mặc định.
3. Prepare query concepts/tiers/expansions qua endpoint Qwen 9B hoặc trusted saved model outputs. Prompts rõ trong `TXT/prompts/`.
4. Cache union/raw BM25 original+expanded/dense/missing masks/observed matches và identities. Chọn depth rộng để offline sweep không bị top-K cũ bó hẹp.
5. Fit sigmoid trên calibration queries có explicit positives/negatives. Không gán unjudged là negative.
6. Tune tier scores/alpha/enrichment/threshold trên tuning queries, lưu search space và mọi trial. Dùng global trước rồi adaptive buckets nếu đủ support.
7. Run config đã khóa trên holdout hoặc explicit exploratory split; export candidates tương thích downstream.
8. Evaluate coverage/selection/cost trên judgments đúng semantics. Chạy cùng Qwen/MaxP/p̂/native chunk control khi đã bind đúng recipes/cache.
9. Report cả gain/loss, missingness, nguồn KB, confidence availability, splits/candidate budget và việc chưa chạy. Không tổng quát từ demo sang baseline.

## 4. Đối chứng tối thiểu

So B0 RRF+top-K, M0 fixed calibrated fusion+top-K, M1 medical-gated+top-K, M2 medical-gated+global threshold, M3 tier-bucket threshold. Enrichment và expected-tier confidence là ablations sau/cùng recipe được khóa, không được gộp mọi thay đổi rồi quy gain cho taxonomy.

Không yêu cầu chứng minh gain trước khi chạy biến thể mới. Có thể chạy experiment đã được ủy quyền ngay khi inputs cần cho chính experiment đó có đủ. Budget matching để so chất lượng cần số docs trung bình/tổng gần nhau; một experiment chủ động đổi budget phải báo cost curve.

## 5. BR/BF và downstream

BR tìm corpus/index độc lập, có thể ngoài union baseline. BF chỉ chọn union nguồn; model-gated fusion cập nhật BF. Không buộc BR chờ BF hoặc ngược lại. Joint là experiment riêng, không cộng gain hai phần.

Giữ language/corpus/query snapshots; nếu thí nghiệm VI thì giữ nhánh ZH control. Đưa KB Trung vào enrichment không đồng nghĩa ZH retrieval đã parity. Han tokenization prototype vẫn cần kiểm riêng.

Downstream Qwen checkpoint/prompt/preprocessing, MaxP/p̂/calibration/threshold/chunk policy giữ control. Document mới thiếu Qwen score cần inference đúng recipe, không gán 0/bỏ doc/đổi score fusion thành Qwen. Diagnostic evidence windows chưa native chunks.

## 6. Dữ liệu, splits và identity

Chia theo query: calibration/tuning/holdout. Nếu val đã khai thác thì ghi exploratory/development, không gọi pristine holdout. Qrels unknown/chunk-derived not_gold không tự là negative. Calibration probability cần explicit negatives và population/sampling rõ; positive-only vẫn đo known-positive coverage được.

Lưu query/doc namespace, hashes corpus/index/KB/model/prompt/config và deterministic order. Source absence trong truncated lists khác score 0. Đổi expansion/depth/matcher/model có invalidation rõ; cache cũ không đánh giá docs ngoài union.

## 7. Giới hạn ghi và lịch sử

Outputs mới dưới TXT, không đè source corpus/labels hoặc completed artifacts. Không ghi vào `TXT/inputs`. Model server/download được vận hành rõ riêng, không tự tải trong import package/demo.

0,391 là control người dùng báo; counts khoảng 300 VI + 40 ZH và mean cuối khoảng 160 từ sơ đồ chưa phải runtime xác minh. L1/L4 scope 0,4076 và N0/N1 giữ kết quả cũ, không làm lại prerequisite bằng tên mới.

Code/tests/demo mới chỉ xác nhận engineering behavior; quality/end-to-end cần input linkage và scorer thật. Xem results/log để biết checks đã thực sự chạy, không lấy danh sách việc ở PLAN làm bằng chứng hoàn tất.

[Archive v3.5](archive/PLAN_v3_5_20261020.md) giữ phiên bản trước.
