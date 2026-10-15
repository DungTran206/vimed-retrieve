#!/usr/bin/env bash
# Chờ một GPU còn trống >= 14 GB (máy dùng chung) rồi chạy Qwen chấm batch 2; resume theo .partial nếu chết.
cd "$(dirname "$0")/.."
export HF_HOME=$HOME/hf_cache PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
for try in $(seq 1 200); do
  gpu=$(nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' '$3-$2>=14000 {print $1; exit}')
  if [ -n "$gpu" ]; then
    echo "$(date) chạy trên GPU $gpu (lần $try)"
    CUDA_VISIBLE_DEVICES=$gpu .venv/bin/python -u qwen_rerank.py --cands data/qr_cands_h.jsonl --db data/qr_text_h.sqlite --out data/qwen_h.jsonl --topk 400 --doc-chars 1000 --max-len 1024 --batch 16 --mem-fraction 0.9 && { echo QWEN_H_DONE; exit 0; }
    echo "$(date) chết, thử lại"
  fi
  sleep 60
done
echo QWEN_H_GIVEUP
