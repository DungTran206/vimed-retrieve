#!/usr/bin/env bash
# Qwen3-Embedding-8B cho 226k doc zh kho mới (title + 600 ký tự, cắt 256 token như BGE), chia 2 nửa chạy song song 2 GPU,
# rồi xếp hạng 1.200 câu (câu vi gốc / câu dịch zh / 109 câu dịch đã vá). Tự CHỜ tới khi card đủ trống (máy dùng chung).
#   bash scripts/run_zh_q8.sh        (log: data/zh_q8.log)
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONUTF8=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True CUDA_DEVICE_ORDER=PCI_BUS_ID HF_HOME=$HOME/.cache/huggingface
PY=.venv/bin/python
M=Qwen/Qwen3-Embedding-8B
NEED=20000                                   # MiB trống tối thiểu mỗi card (8B fp16 ~16 GB + lô)
free_gpus() { nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader,nounits | awk -F', ' -v n=$NEED '$3-$2>=n {print $1}'; }
$PY - <<'P'
import sqlite3, os
src = sqlite3.connect("data/zh_text_new.sqlite")
for k in (0, 1):
    p = f"data/zh_text_new_p{k}.sqlite"
    if os.path.exists(p): continue
    d = sqlite3.connect(p); d.execute("create table doc(doc_id text, title text, body text)")
    d.executemany("insert into doc values (?,?,?)", src.execute("select doc_id,title,body from doc where rowid % 2 = ?", (k,)))
    d.commit(); print(p, d.execute("select count(*) from doc").fetchone()[0], flush=True)
P
enc() {  # $1 = phần, $2 = GPU
  [ -s data/emb_zhQ8_p$1.npy ] || CUDA_VISIBLE_DEVICES=$2 $PY -u -m index.dense --encode --model $M --db data/zh_text_new_p$1.sqlite \
      --emb data/emb_zhQ8_p$1 --max-len 256 --batch 64 --min-title 3 --min-body 0 --body-chars 600
}
todo=(); for k in 0 1; do [ -s data/emb_zhQ8_p$k.npy ] || todo+=($k); done
pids=()
while [ ${#todo[@]} -gt 0 ]; do
  g=($(free_gpus))
  if [ ${#g[@]} -eq 0 ]; then echo "$(date +%H:%M) chờ GPU trống ≥${NEED} MiB"; sleep 300; continue; fi
  for gi in "${g[@]}"; do
    [ ${#todo[@]} -eq 0 ] && break
    k=${todo[0]}; todo=("${todo[@]:1}")
    echo "$(date +%H:%M) phần $k -> GPU $gi"; ( enc $k $gi > data/zh_q8_p$k.log 2>&1 ) & pids+=($!); sleep 120
  done
done
wait "${pids[@]}"
$PY - <<'P'
import numpy as np, json
E=[np.load(f"data/emb_zhQ8_p{k}.npy") for k in (0,1)]; I=[json.load(open(f"data/emb_zhQ8_p{k}.ids.json")) for k in (0,1)]
np.save("data/emb_zhQ8.npy",np.concatenate(E)); json.dump(I[0]+I[1],open("data/emb_zhQ8.ids.json","w")); print("emb_zhQ8",sum(map(len,I)),flush=True)
P
INS_VI="Instruct: Given a Vietnamese patient health question, retrieve Chinese medical Q&A posts or articles that answer it
Query:"
INS_ZH="Instruct: Given a patient health question, retrieve medical Q&A posts or articles that answer it
Query:"
g=$(free_gpus | head -1); while [ -z "$g" ]; do sleep 300; g=$(free_gpus | head -1); done
export CUDA_VISIBLE_DEVICES=$g
$PY -u -m index.dense --rank --model $M --emb data/emb_zhQ8 --queries data/queries.jsonl --out data/dense_zhQ8_vi_rank.jsonl --query-instruct "$INS_VI" --max-len 256 --topk 1000
$PY -u -m index.dense --rank --model $M --emb data/emb_zhQ8 --queries data/queries_zhq.jsonl --out data/dense_zhQ8_zhq_rank.jsonl --query-instruct "$INS_ZH" --max-len 256 --topk 1000
$PY -u -m index.dense --rank --model $M --emb data/emb_zhQ8 --queries data/queries_zhq109.jsonl --out data/dense_zhQ8_zhq109_rank.jsonl --query-instruct "$INS_ZH" --max-len 256 --topk 1000
echo ZHQ8_DONE
