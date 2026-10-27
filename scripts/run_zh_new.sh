#!/usr/bin/env bash
# zh kho mới (14/10): embed TOÀN BỘ 228k doc zh kho mới đã clean (data/zh_text_new.sqlite, title + 600 ký tự đầu, BGE-M3),
# thay hàng tương ứng trong emb_zhC2 -> emb_zhC3, xếp hạng lại 1.200 câu bằng câu vi, câu dịch zh và 109 câu dịch đã vá.
#   CUDA_VISIBLE_DEVICES=1 bash scripts/run_zh_new.sh
set -euo pipefail
cd "$(dirname "$0")/.."
export HF_HOME=$HOME/hf_cache PYTHONUTF8=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=.venv/bin/python
[ -s data/emb_zhE.npy ] || $PY -u -m index.dense --encode --db data/zh_text_new.sqlite --emb data/emb_zhE --max-len 256 --batch 256 --min-title 3 --min-body 0 --body-chars 600 --mem-fraction 0.9
$PY - <<'P'
import numpy as np, json
a=np.load("data/emb_zhC2.npy"); b=np.load("data/emb_zhE.npy")
ia=json.load(open("data/emb_zhC2.ids.json")); ib=json.load(open("data/emb_zhE.ids.json"))
# emb_zhE = TOÀN BỘ zh kho mới từ văn bản đã clean -> thay hàng cũ (chưa clean) của emb_zhC2
new=set(map(str,ib)); keep=[i for i,d in enumerate(ia) if str(d) not in new]
np.save("data/emb_zhC3.npy",np.concatenate([a[keep],b.astype(a.dtype)])); json.dump([ia[i] for i in keep]+ib,open("data/emb_zhC3.ids.json","w"))
print("emb_zhC3: giữ",len(keep),"cũ + ",len(ib),"mã hoá lại/mới",flush=True)
P
for Q in queries:vi queries_zhq:zhq queries_zhq109:zhq109; do
  $PY -u -m index.dense --rank --emb data/emb_zhC3 --queries data/${Q%%:*}.jsonl --out data/dense_zhC3_${Q##*:}_rank.jsonl --max-len 256 --topk 1000 --mem-fraction 0.9
done
echo ZHNEW_DONE
