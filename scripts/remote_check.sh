#!/usr/bin/env bash
# Kiểm tra lần lượt 4 mô hình, mỗi mô hình một process. Chạy từ thư mục gốc:
#   bash scripts/remote_check.sh 2>&1 | tee runs/remote_check.log
cd "$(dirname "$0")/.."
VLLM=.venv-vllm/bin/python
TRAIN=.venv-train/bin/python
declare -A RESULT

$VLLM scripts/remote_check.py llm && RESULT[llm]=OK || RESULT[llm]=LỖI

if $VLLM scripts/remote_check.py mt; then
  RESULT[mt]="OK (vLLM)"
else
  echo ">> Hy-MT2 chưa chạy được bằng vLLM, thử transformers..."
  $TRAIN scripts/remote_check.py mt --hf && RESULT[mt]="OK (transformers, dùng MT_BACKEND=hf)" || RESULT[mt]=LỖI
fi

$TRAIN scripts/remote_check.py embed  && RESULT[embed]=OK  || RESULT[embed]=LỖI
$TRAIN scripts/remote_check.py rerank && RESULT[rerank]=OK || RESULT[rerank]=LỖI

echo; echo "===== TỔNG KẾT"
for k in llm mt embed rerank; do printf "  %-7s %s\n" "$k" "${RESULT[$k]}"; done
