#!/usr/bin/env bash
# BM25F (có dấu) và BM25 entity trên kho vi ĐẦY ĐỦ (vi_full.sqlite), chạy SONG SONG.
#   bash scripts/run_bm25_full.sh        # trên máy GPU (nhiều lõi CPU, không dùng GPU)
set -u
cd "$(dirname "$0")/.."
export PYTHONUTF8=1
PY=.venv/bin/python
DB=data/vi_full.sqlite
$PY -m index.bm25 --demo > /dev/null || { echo "bm25 demo lỗi"; exit 1; }
nohup $PY -u -m index.bm25 --db $DB --keep-diacritics --out data/bm25d3_rank.jsonl > data/bm25d3_rank.log 2>&1 &
nohup $PY -u -m index.bm25_ent --db $DB --workers 8 --out data/bm25ent3_rank.jsonl > data/bm25ent3.log 2>&1 &
wait
echo BM25_FULL_DONE
