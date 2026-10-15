#!/usr/bin/env bash
# Embed doc vi mới (vi_text_delta2.sqlite) bằng BGE-M3, ghép vào emb_vi2/viB2 -> emb_vi3/viB3, xếp hạng lại 1.200 câu.
#   CUDA_VISIBLE_DEVICES=0 bash scripts/run_delta2.sh
set -e
cd "$(dirname "$0")/.."
export HF_HOME=$HOME/hf_cache PYTHONUTF8=1
PY=.venv/bin/python
[ -s data/emb_d2_t.npy ] || $PY -u dense.py --encode --db data/vi_text_delta2.sqlite --emb data/emb_d2_t --max-len 64 --batch ${BATCH:-512} --min-title 3 --min-body 0 --mem-fraction ${MEMF:-0.9}
[ -s data/emb_d2_b.npy ] || $PY -u dense.py --encode --db data/vi_text_delta2.sqlite --emb data/emb_d2_b --max-len 192 --batch ${BATCH:-512} --min-title 3 --min-body 0 --body-chars 600 --mem-fraction ${MEMF:-0.9}
$PY - <<'P'
import numpy as np, json
for old,new,out in (("data/emb_vi2","data/emb_d2_t","data/emb_vi3"),("data/emb_viB2","data/emb_d2_b","data/emb_viB3")):
    a=np.load(old+".npy"); b=np.load(new+".npy")
    ia=json.load(open(old+".ids.json")); ib=json.load(open(new+".ids.json"))
    assert a.shape[1]==b.shape[1] and len(ia)==len(a) and len(ib)==len(b)
    old_ids=set(map(str,ia)); keep=[i for i,d in enumerate(ib) if str(d) not in old_ids]   # doc đã có vector cũ thì bỏ bản mới
    print(out,"bỏ",len(ib)-len(keep),"id trùng",flush=True)
    b=b[keep]; ib=[ib[i] for i in keep]
    np.save(out+".npy",np.concatenate([a,b])); json.dump(ia+ib,open(out+".ids.json","w"))
    print(out,len(ia),"+",len(ib),flush=True)
P
$PY -u dense.py --rank --emb data/emb_vi3 --out data/dense_vi3_rank.jsonl --max-len 128 --topk 1000 --mem-fraction ${MEMF:-0.9}
$PY -u dense.py --rank --emb data/emb_viB3 --out data/dense_viB3_rank.jsonl --max-len 128 --topk 1000 --mem-fraction ${MEMF:-0.9}
echo DELTA2_DONE
