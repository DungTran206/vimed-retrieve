#!/usr/bin/env bash
# Chạy hai bước xử lý truy vấn dùng LLM trên máy GPU.
#   bash scripts/remote_run_llm.sh data/queries.jsonl runs/public
# Nếu remote_check báo Hy-MT2 chỉ chạy được bằng transformers:
#   MT_BACKEND=hf bash scripts/remote_run_llm.sh data/queries.jsonl runs/public
set -euo pipefail
cd "$(dirname "$0")/.."
Q=${1:?Thiếu file câu hỏi}; OUT=${2:?Thiếu thư mục đầu ra}; shift 2

echo "== expand (Qwen3.5-9B, vLLM)"
.venv-vllm/bin/python -m query_processing.pipeline --queries "$Q" --out "$OUT" --stages expand "$@"

echo "== translate (Hy-MT2-7B, ${MT_BACKEND:-vllm})"
if [ "${MT_BACKEND:-vllm}" = "hf" ]; then
  .venv-train/bin/python -m query_processing.pipeline --queries "$Q" --out "$OUT" --stages translate --backend hf "$@"
else
  .venv-vllm/bin/python -m query_processing.pipeline --queries "$Q" --out "$OUT" --stages translate "$@"
fi
echo "Xong: $OUT/expansions.jsonl, $OUT/translations.jsonl, $OUT/queries_enriched.jsonl"
