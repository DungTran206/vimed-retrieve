#!/usr/bin/env bash
# Pilot: BGE-M3 trên chunk của doc trong pool H top-400, rồi xếp hạng lại theo chunk khớp nhất.
set -e
cd "$(dirname "$0")/.."
export HF_HOME=$HOME/hf_cache PYTHONUTF8=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=.venv/bin/python
[ -s data/emb_chunk_pilot.npy ] || $PY -u dense_chunks.py --encode --offsets data/chunk_offsets.sqlite --bodies data/vi_full.sqlite --out data/emb_chunk_pilot --batch 32 --max-len 1024
$PY -u dense_chunks.py --rank --out data/emb_chunk_pilot --cands data/f_H.jsonl --topn 400 --rank-out data/dense_chunk_pilot_rank.jsonl
echo CHUNKPILOT_DONE
