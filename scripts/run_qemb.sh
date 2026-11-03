#!/usr/bin/env bash
# Qwen3-Embedding-4B trên TITLE kho vi → data/dense_q4t_rank.jsonl (một trong 12 danh sách đặc trưng của baseline.ltr_feats).
# Đầu vào: data/vi_text.sqlite + data/vi_text_delta.sqlite (doc_id, title, body của kho vi; lấy từ Drive).
#   CUDA_VISIBLE_DEVICES=0 bash scripts/run_qemb.sh        # ~45 phút trên một RTX 4090
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
export HF_HOME=${HF_HOME:-$HOME/.cache/huggingface} PYTHONUTF8=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
M=Qwen/Qwen3-Embedding-4B
INS="Instruct: Given a Vietnamese patient health question, retrieve medical articles and Q&A whose title matches the question
Query:"
for part in vi_text vi_text_delta; do
  [ -s data/emb_q4t_$part.npy ] || $PY -u -m index.dense --encode --model $M --db data/$part.sqlite --emb data/emb_q4t_$part \
      --max-len 64 --batch 128 --min-title 3 --min-body 0 --mem-fraction 0.6
done
$PY - <<'P'
import numpy as np, json
parts=["data/emb_q4t_vi_text","data/emb_q4t_vi_text_delta"]
E=[np.load(p+".npy") for p in parts]; I=[json.load(open(p+".ids.json")) for p in parts]
np.save("data/emb_q4t.npy",np.concatenate(E)); json.dump(I[0]+I[1],open("data/emb_q4t.ids.json","w"))
print("emb_q4t",sum(len(i) for i in I),flush=True)
P
$PY -u -m index.dense --rank --model $M --emb data/emb_q4t --out data/dense_q4t_rank.jsonl --query-instruct "$INS" \
    --max-len 256 --topk 1000 --mem-fraction 0.6
echo QEMB_DONE
