#!/usr/bin/env bash
# Dựng bài nộp từ dữ liệu trung gian trên Drive và nhãn giả Qwen3-32B.
#   bash scripts/build_submission.sh              # → runs/z80gbm3q_v09x_ov_p1152_m2.zip (~45 phút, CPU; nén cần ≥ 4 GiB RAM trống)
#   PY=python bash scripts/build_submission.sh    # chọn trình thông dịch khác (mặc định: python)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
export PYTHONUTF8=1
LABELS='C:/Users/DumgTran/Downloads/val_fixed.jsonl'
VC="--tau 0.09 --scope all --overlap --recal gbm3q --cut pack --merge"
OUT=runs/z80gbm3q_v09x_ov_p1152_m2

$PY -m baseline.cands --n-zh 80 --out data/clean_cands_z80.jsonl
$PY -m baseline.select_docs --cands data/clean_cands_z80.jsonl \
    --scores data/cc_scores.jsonl data/ccq_a_scores.jsonl data/ccq_b_scores.jsonl data/z80base_scores.jsonl \
    --labels "$LABELS" --docs 160 --out data/val/docs_z80base160.json --dump data/val/z80base_scores.json
$PY -m baseline.recal_docs --mode full --tag dfull --labels "$LABELS"
$PY -m baseline.ltr_feats
$PY -m baseline.ltr_docs --mode gbm3 --cut-q --labels "$LABELS"
rm -f $OUT.json $OUT.zip $OUT.zip.part
$PY -m baseline.value_chunks build $VC

GOT=$($PY -c "import hashlib,sys; h=hashlib.sha256(); f=open(sys.argv[1],'rb'); [h.update(b) for b in iter(lambda: f.read(1<<24), b'')]; print(h.hexdigest())" $OUT.json)
echo "JSON sha256 $GOT"
$PY -m baseline.value_chunks compress $VC
$PY -m baseline.value_chunks verify $VC
echo "XONG: $OUT.zip"
