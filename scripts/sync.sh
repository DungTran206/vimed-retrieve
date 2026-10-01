#!/usr/bin/env bash
# Đồng bộ giữa máy local và máy GPU qua rsync/SSH. Cấu hình trong .env.sync.
#   bash scripts/sync.sh push            # đẩy code + data/ lên máy GPU
#   bash scripts/sync.sh pull            # kéo runs/ (kết quả) về máy local
#   bash scripts/sync.sh pull models     # kéo models/ (weight đã fine-tune) về
#   bash scripts/sync.sh push-runs NAME  # đẩy runs/NAME lên (vd. kết quả PubMed cần rerank)
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env.sync ] || { echo "Thiếu .env.sync: cp .env.sync.example .env.sync rồi sửa"; exit 1; }
source .env.sync
SSH="ssh -p ${SSH_PORT:-22}"
RS=(rsync -avz --partial --progress -e "$SSH")

case "${1:-}" in
  push)
    $SSH "$REMOTE" "mkdir -p $REMOTE_DIR"
    "${RS[@]}" --exclude '.venv*' --exclude 'hf_cache/' --exclude 'runs/' --exclude 'models/' \
      --exclude '__pycache__/' --exclude '*.sqlite' --exclude '.env.sync' ./ "$REMOTE:$REMOTE_DIR/" ;;
  pull)
    DIR=${2:-runs}; mkdir -p "$DIR"
    "${RS[@]}" "$REMOTE:$REMOTE_DIR/$DIR/" "./$DIR/" ;;
  push-runs)
    NAME=${2:?Thiếu tên thư mục trong runs/}
    "${RS[@]}" "./runs/$NAME/" "$REMOTE:$REMOTE_DIR/runs/$NAME/" ;;
  *) sed -n '2,7p' "$0"; exit 1 ;;
esac
