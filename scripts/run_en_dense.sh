#!/usr/bin/env bash
# Dense cho 240.000 bài PubMed (title + abstract, BGE-M3), xếp hạng bằng câu hỏi VI gốc và bản dịch EN.
cd "$(dirname "$0")/.."
export HF_HOME=$HOME/hf_cache PYTHONUTF8=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=.venv/bin/python
g=$($PY pickgpu.py 6 | tail -1); echo "GPU $g"
export CUDA_VISIBLE_DEVICES=$g
[ -s data/emb_en.npy ] || $PY -u dense.py --encode --db data/en_text.sqlite --emb data/emb_en --max-len 384 --batch 64 --min-title 3 --min-body 50 --body-chars 1500 --mem-fraction 0.5
$PY -u dense.py --rank --emb data/emb_en --queries data/queries.jsonl --out data/dense_en_vi_rank.jsonl --max-len 256 --topk 1000 --mem-fraction 0.5
$PY -u dense.py --rank --emb data/emb_en --queries data/queries_en.jsonl --out data/dense_en_en_rank.jsonl --max-len 256 --topk 1000 --mem-fraction 0.5
echo ENDENSE_DONE
