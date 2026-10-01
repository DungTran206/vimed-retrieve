#!/usr/bin/env bash
# Cài môi trường trên máy GPU 50 GB. Chạy MỘT lần, từ thư mục gốc dự án:
#   bash scripts/remote_setup.sh
# Tạo hai môi trường riêng để tránh xung đột phiên bản transformers:
#   .venv-vllm  : vLLM (Qwen3.5-9B, Hy-MT2-7B nếu vLLM hỗ trợ)
#   .venv-train : transformers>=5.6 + sentence-transformers + FlagEmbedding + peft
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== GPU"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
echo "== Ổ đĩa (cần >= 100 GB trống cho mô hình + dữ liệu)"
df -h .

if ! command -v uv >/dev/null 2>&1; then
  echo "== Cài uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "== .venv-vllm"
uv venv .venv-vllm --python 3.12
uv pip install --python .venv-vllm/bin/python -U "vllm>=0.17.0" --torch-backend=auto
uv pip install --python .venv-vllm/bin/python requests pandas pyarrow huggingface_hub tqdm

echo "== .venv-train"
uv venv .venv-train --python 3.12
uv pip install --python .venv-train/bin/python torch --torch-backend=auto
uv pip install --python .venv-train/bin/python -r env/requirements-train.txt

echo "== Kiểm tra nhanh"
.venv-vllm/bin/python -c "import vllm, torch; print('vllm', vllm.__version__, '| torch', torch.__version__, '| cuda', torch.cuda.is_available())"
.venv-train/bin/python -c "import transformers, torch; print('transformers', transformers.__version__, '| cuda', torch.cuda.is_available())"
.venv-train/bin/python -m unittest discover tests

cat << 'MSG'

Xong. Bước tiếp theo:
  1. Đặt chỗ lưu mô hình (nếu chưa):  echo 'export HF_HOME=$HOME/hf_cache' >> ~/.bashrc && source ~/.bashrc
  2. Tải mô hình:                      bash scripts/download_models.sh
  3. Kiểm tra từng mô hình:            bash scripts/remote_check.sh
MSG
