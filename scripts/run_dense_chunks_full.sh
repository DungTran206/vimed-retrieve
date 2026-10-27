#!/usr/bin/env bash
# Chunk-dense TOÀN KHO vi: 2 phần (s0,s1) encode SONG SONG trên 2 GPU, rồi tìm top chunk cho 1.200 câu trên toàn bộ vector.
set -u
cd "$(dirname "$0")/.."
export HF_HOME=$HOME/hf_cache PYTHONUTF8=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=.venv/bin/python
enc() {  # $1=phần  $2=GPU
  [ -s data/emb_chunk_s$1.npy ] && return 0
  CUDA_VISIBLE_DEVICES=$2 $PY -u -m index.dense_chunks --encode --offsets data/chunk_offsets_s$1.sqlite --bodies data/vi_full.sqlite \
      --out data/emb_chunk_s$1 --batch 32 --max-len 1024 > data/chunkfull_s$1.log 2>&1
}
enc 0 0 &
enc 1 1 &
wait
[ -s data/emb_chunk_s0.npy ] && [ -s data/emb_chunk_s1.npy ] || { echo "ENCODE_FAIL"; exit 1; }
CUDA_VISIBLE_DEVICES=0 $PY -u -m index.dense_chunks --rank-full --queries data/queries.jsonl --rank-out data/dense_chunk_full_rank.jsonl --topn 1000 > data/chunkfull_rank.log 2>&1
echo CHUNKFULL_DONE
