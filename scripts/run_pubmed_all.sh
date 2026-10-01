#!/usr/bin/env bash
# Chạy toàn bộ module. Mỗi mô hình GPU chạy trong một process riêng để giải phóng VRAM.
# Cách dùng: bash run_all.sh <queries.jsonl> <thư_mục_out> [tham số thêm cho mọi bước...]
# Ví dụ:     bash run_all.sh data/public_test.jsonl runs/public
#            bash run_all.sh data/public_test.jsonl runs/public --backend hf --load-in-4bit
set -euo pipefail
Q=${1:?Thiếu file câu hỏi (JSONL {id, query})}
OUT=${2:?Thiếu thư mục đầu ra}
shift 2

echo "== [1/3] expand: Qwen3.5-9B sinh thực thể + truy vấn PubMed"
python -m pubmed_module.pipeline --queries "$Q" --out "$OUT" --stages expand "$@"

echo "== [2/3] translate: Hy-MT2-7B dịch en/zh kèm bảng thuật ngữ"
python -m pubmed_module.pipeline --queries "$Q" --out "$OUT" --stages translate "$@"

echo "== [3/3] search + fetch: PubMed (không cần GPU)"
python -m pubmed_module.pipeline --queries "$Q" --out "$OUT" --stages search,fetch "$@"

echo "Xong. Kết quả trong $OUT/"
