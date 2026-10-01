#!/usr/bin/env bash
# Tải trước mọi mô hình về HF_HOME (khoảng 37 GB). Chạy được lại nếu bị ngắt.
#   bash scripts/download_models.sh            # tất cả
#   bash scripts/download_models.sh embed      # chỉ embedding + reranker
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv-train/bin/python
echo "HF_HOME=${HF_HOME:-~/.cache/huggingface (mặc định)}"

# Tên mô hình | ngày phát hành | kích thước (ghi lại để khai báo với BTC)
LLM=(  "Qwen/Qwen3.5-9B"           # 2026-03-02, ~9B,   Apache-2.0
       "tencent/Hy-MT2-7B" )       # 2026-05-21, ~7B,   Apache-2.0
EMB=(  "BAAI/bge-m3"               # 2024-01,    568M,  MIT
       "BAAI/bge-reranker-v2-m3" ) # 2024-03,    568M,  Apache-2.0

case "${1:-all}" in
  llm)   MODELS=("${LLM[@]}") ;;
  embed) MODELS=("${EMB[@]}") ;;
  *)     MODELS=("${LLM[@]}" "${EMB[@]}") ;;
esac

for m in "${MODELS[@]}"; do
  echo "== $m"
  $PY -c "from huggingface_hub import snapshot_download as s; print(s('$m'))"
done
echo "Xong."
