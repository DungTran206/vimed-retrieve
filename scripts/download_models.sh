#!/usr/bin/env bash
# Tải đúng revision các mô hình bài nộp dùng về HF_HOME (khoảng 60 GB). Chạy được lại nếu bị ngắt.
#   bash scripts/download_models.sh            # tất cả
#   bash scripts/download_models.sh llm        # chỉ Qwen3.5-9B + Hy-MT2-7B (xử lý câu hỏi)
#   bash scripts/download_models.sh embed      # chỉ embedding + reranker
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv-train/bin/python
echo "HF_HOME=${HF_HOME:-~/.cache/huggingface (mặc định)}"

# Tên mô hình@revision — ngày phát hành, kích thước, giấy phép (khai báo với BTC)
LLM=(  "Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a"              # 2026-03-02, ~9B,  Apache-2.0
       "tencent/Hy-MT2-7B@9b0eb4e8f001def3e5ff6469a0ac96fdb39ec223" )          # 2026-05-21, ~7B,  Apache-2.0
EMB=(  "BAAI/bge-m3@9a0624b896d81da7492a910ffa53731274b6cf3d"                   # 2024-01,    568M, MIT
       "Qwen/Qwen3-Reranker-4B@22e683669bc0f0bd69640a1354a6d0aebcfeede5"        # 2025-06,    4B,   Apache-2.0
       "Qwen/Qwen3-Embedding-8B@1d8ad4ca9b3dd8059ad90a75d4983776a23d44af"       # 2025-06,    8B,   Apache-2.0
       "Qwen/Qwen3-Embedding-4B@5cf2132abc99cad020ac570b19d031efec650f2b" )     # 2025-06,    4B,   Apache-2.0

case "${1:-all}" in
  llm)   MODELS=("${LLM[@]}") ;;
  embed) MODELS=("${EMB[@]}") ;;
  *)     MODELS=("${LLM[@]}" "${EMB[@]}") ;;
esac

for m in "${MODELS[@]}"; do
  echo "== $m"
  $PY -c "from huggingface_hub import snapshot_download as s; print(s('${m%@*}', revision='${m#*@}'))"
done
echo "Xong."
