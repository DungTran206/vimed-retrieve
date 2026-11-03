#!/usr/bin/env bash
# Dựng lại bài nộp từ dữ liệu trung gian trên Drive (README §5.1) rồi so sha256 JSON với bản đã nộp.
#   bash scripts/build_submission.sh              # → runs/z80gbm3q_v09x_ov_p1152_m2.zip (~45 phút, CPU; nén cần ≥ 4 GiB RAM trống)
#   PY=python bash scripts/build_submission.sh    # chọn trình thông dịch khác (mặc định: python)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-python}
export PYTHONUTF8=1
EXPECT=89c7dd84d108daa6b57d52d1baf1ee93c80b9690be726b060c10310c8f3df357
VC="--tau 0.09 --scope all --overlap --recal gbm3q --cut pack --merge"
OUT=runs/z80gbm3q_v09x_ov_p1152_m2

$PY -m baseline.cands --n-zh 80 --out data/clean_cands_z80.jsonl
$PY -m baseline.select_docs --cands data/clean_cands_z80.jsonl \
    --scores data/cc_scores.jsonl data/ccq_a_scores.jsonl data/ccq_b_scores.jsonl data/z80base_scores.jsonl \
    --docs 160 --out data/val/docs_z80base160.json --dump data/val/z80base_scores.json
$PY -m baseline.recal_docs --mode full --tag dfull
$PY -m baseline.ltr_feats
$PY -m baseline.ltr_docs --mode gbm3 --cut-q
rm -f $OUT.json $OUT.zip $OUT.zip.part
$PY -m baseline.value_chunks build $VC

GOT=$($PY -c "import hashlib,sys; h=hashlib.sha256(); f=open(sys.argv[1],'rb'); [h.update(b) for b in iter(lambda: f.read(1<<24), b'')]; print(h.hexdigest())" $OUT.json)
if [ "$GOT" != "$EXPECT" ]; then
  echo "JSON sha256 $GOT KHÁC bản đã nộp $EXPECT"; exit 1
fi
echo "JSON trùng bản đã nộp ($EXPECT)"
$PY -m baseline.value_chunks compress $VC
$PY -m baseline.value_chunks verify $VC
echo "XONG: $OUT.zip"
