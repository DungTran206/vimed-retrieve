# Setup hai máy: local (GPU 8 GB) + máy GPU (50 GB)

## 0. Chia việc

| Việc | Máy | Lý do |
| --- | --- | --- |
| Tải dataset, thống kê URL (`profile_dataset.py`) | Local | CPU, vài phút |
| Crawl 4,4 triệu URL, làm sạch HTML | Local (hoặc cả hai) | Cần mạng + ổ đĩa, không cần GPU |
| Gọi PubMed (search, fetch) | Local | Bị giới hạn bởi rate limit API |
| Chia chunk, BM25, gộp điểm, cắt ngưỡng, xuất file nộp | Local | CPU + RAM |
| Embedding câu hỏi, rerank vài chục cặp khi debug | Local | BGE-M3 / reranker fp16 chỉ cần khoảng 1–2 GB VRAM |
| **Qwen3.5-9B (expand), Hy-MT2-7B (dịch)** | **GPU 50 GB** | Không vừa thoải mái trong 8 GB |
| **Embedding toàn bộ corpus** | **GPU 50 GB** | Hàng triệu đến hàng chục triệu chunk |
| **Rerank hàng loạt** (1.200 câu × hàng trăm ứng viên) | **GPU 50 GB** | Hàng trăm nghìn cặp |
| **Fine-tune reranker/embedding, sinh dữ liệu bằng teacher lớn** | **GPU 50 GB** | Bắt buộc có GPU lớn |

Nguyên tắc: **máy GPU chỉ nhận file vào, chạy theo lô, trả file ra.** Mọi điều phối nằm ở máy local; hai máy trao đổi bằng `scripts/sync.sh`.

```
LOCAL                                   GPU 50 GB
data/queries.jsonl  ── push ──►   remote_run_llm.sh  (expand + translate)
                    ◄── pull ──   runs/public/queries_enriched.jsonl
search + fetch PubMed, crawl, BM25
chunks / ứng viên   ── push ──►   embedding / rerank / fine-tune
                    ◄── pull ──   *.npy, điểm rerank, models/<checkpoint>
```

---

## 1. Máy local (GPU 8 GB)

Máy local là **Windows + PowerShell 5**, chưa có WSL → không dùng được `&&`, `source`,
`export`, `bash`, `rsync`. Mọi lệnh phía local trong file này là cú pháp PowerShell.

```powershell
cd D:\dung\ai_guru\vimed
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# PowerShell chặn script? Set-ExecutionPolicy -Scope Process RemoteSigned
# Cài torch bản CUDA khớp driver (xem lệnh chính xác tại pytorch.org), ví dụ:
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r env/requirements-local.txt
python -m unittest discover tests              # phải OK hết 12 test

python profile_dataset.py                      # tạo data/queries.jsonl + thống kê URL
```

Khoá PubMed — đặt vĩnh viễn cho user, chỉ làm một lần (terminal mở sau đó mới thấy):

```powershell
[Environment]::SetEnvironmentVariable("NCBI_API_KEY", "...", "User")
[Environment]::SetEnvironmentVariable("NCBI_EMAIL",   "...", "User")
# dùng ngay trong phiên hiện tại:
$env:NCBI_API_KEY = "..."; $env:NCBI_EMAIL = "..."
```

Kiểm tra nhanh phần PubMed (không cần GPU). PowerShell nối dòng bằng backtick, không phải `\`:

```powershell
python -m pipelines.pubmed --queries examples/sample_queries.jsonl `
    --out examples/manual_run --stages search,fetch
```

---

## 2. Kết nối SSH (làm một lần trên máy local)

```powershell
ssh-keygen -t ed25519                     # nếu chưa có khoá; Enter qua hết
# Windows không có ssh-copy-id → đẩy khoá công khai bằng tay:
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh -p 22 user@IP_MAY_GPU "mkdir -p ~/.ssh; cat >> ~/.ssh/authorized_keys"
```

Thêm vào `%USERPROFILE%\.ssh\config`:

```
Host gpu50
    HostName IP_MAY_GPU
    User user
    Port 22
    ServerAliveInterval 60
```

Giờ `ssh gpu50` là vào được. Chuyển file bằng **`scp`** (có sẵn trên Windows 10/11).
`scripts/sync.sh` cần bash + rsync nên chỉ chạy được từ Linux/WSL → trên máy này bỏ qua nó.

```powershell
# ĐẨY LÊN: chạy từ thư mục CHA của vimed, để trên máy GPU thành ~/vimed
cd D:\dung\ai_guru
scp -P 22 -r vimed user@IP_MAY_GPU:~/

# KÉO VỀ: kết quả của một lần chạy
scp -P 22 -r user@IP_MAY_GPU:~/vimed/runs/public .\vimed\runs\
```

File từ Windows mang theo CRLF. Trên máy GPU nếu gặp `$'\r': command not found`:

```bash
sed -i 's/\r$//' scripts/*.sh
```

---

## 3. Máy GPU 50 GB

### 3.1 Cài môi trường (một lần, khoảng 15–30 phút)

```bash
ssh gpu50
sudo apt install -y tmux                  # nếu chưa có
tmux new -s vimed                         # mọi việc dài chạy trong tmux
cd ~/vimed

echo 'export HF_HOME=$HOME/hf_cache' >> ~/.bashrc
echo 'export NCBI_API_KEY=...'       >> ~/.bashrc   # nếu muốn chạy PubMed trên máy này
source ~/.bashrc

bash scripts/remote_setup.sh
```

Script tạo **hai môi trường riêng**, vì vLLM tự ghim phiên bản transformers, còn Hy-MT2 và các thư viện huấn luyện cần transformers ≥ 5.6:

| Môi trường | Dùng cho |
| --- | --- |
| `.venv-vllm` | Qwen3.5-9B, và Hy-MT2-7B nếu vLLM hỗ trợ |
| `.venv-train` | BGE-M3, reranker, fine-tune, Hy-MT2 qua transformers (dự phòng) |

**tmux:** thoát mà không dừng chương trình bằng `Ctrl+b` rồi `d`; quay lại bằng `tmux a -t vimed`. Mất kết nối SSH thì chương trình vẫn chạy tiếp.

### 3.2 Tải mô hình (khoảng 37 GB)

```bash
bash scripts/download_models.sh
```

| Mô hình | Phát hành | Kích thước | Vai trò |
| --- | --- | --- | --- |
| Qwen/Qwen3.5-9B | 2/3/2026 | ~9B | Hiểu câu hỏi, sinh truy vấn PubMed |
| tencent/Hy-MT2-7B | 21/5/2026 | ~7B | Dịch vi → en/zh |
| BAAI/bge-m3 | 1/2024 | 568M | Embedding đa ngôn ngữ (dense + sparse) |
| BAAI/bge-reranker-v2-m3 | 3/2024 | 568M | Reranker cross-encoder |

Tất cả đều ≤ 15B và phát hành trước 1/8/2026. Giữ bảng này để khai báo với BTC.

### 3.3 Kiểm tra từng mô hình

```bash
mkdir -p runs
bash scripts/remote_check.sh 2>&1 | tee runs/remote_check.log
```

Kết quả mong đợi ở cuối log:

```
===== TỔNG KẾT
  llm     OK
  mt      OK (vLLM)            ← hoặc "OK (transformers, dùng MT_BACKEND=hf)"
  embed   OK
  rerank  OK
```

Mỗi kiểm tra in ra kết quả cụ thể để đọc bằng mắt: truy vấn PubMed sinh ra, bản dịch en/zh, điểm tương đồng (đoạn tiếng Anh và tiếng Trung đúng chủ đề phải điểm cao hơn đoạn về sỏi thận). Gửi file `runs/remote_check.log` nếu có mục nào lỗi.

---

## 4. Quy trình hằng ngày

**Chạy LLM cho 1.200 câu public:**

```powershell
# --- LOCAL (PowerShell): đẩy code + data/queries.jsonl lên
cd D:\dung\ai_guru
scp -P 22 -r vimed user@IP_MAY_GPU:~/
ssh gpu50
```

```bash
# --- MÁY GPU (bash, trong tmux)
tmux a -t vimed
cd ~/vimed
bash scripts/remote_run_llm.sh data/queries.jsonl runs/public
#   (nếu Hy-MT2 chỉ chạy được bằng transformers: thêm MT_BACKEND=hf ở đầu lệnh)
```

```powershell
# --- LOCAL, khi máy GPU xong: kéo kết quả về rồi gọi PubMed
cd D:\dung\ai_guru
scp -P 22 -r user@IP_MAY_GPU:~/vimed/runs/public .\vimed\runs\
cd .\vimed
python -m pipelines.pubmed --queries data/queries.jsonl --out runs/public --stages search,fetch
```

Bước search/fetch đọc `expansions.jsonl` đã kéo về, nên chạy ở local được, không cần GPU.

**Private test (1/11):** lặp lại y hệt với thư mục `runs/private`.

**Fine-tune:** chạy trên máy GPU, lưu checkpoint vào `models/<tên>`, rồi kéo về local bằng `scp -P 22 -r user@IP_MAY_GPU:~/vimed/models .\vimed\`. Giữ checkpoint ở chế độ private, không công khai lên Hugging Face.

---

## 5. Ngân sách VRAM trên máy 50 GB

| Tác vụ | VRAM ước tính |
| --- | --- |
| Qwen3.5-9B bf16 trên vLLM | ~19 GB trọng số; vLLM chiếm tới `--gpu-mem` × 50 GB cho KV cache |
| Hy-MT2-7B bf16 | ~15 GB trọng số |
| BGE-M3 / reranker fp16 | ~1–2 GB + batch |
| Teacher lớn để sinh dữ liệu (sau này), vd. bản 27B ở FP8 | ~28 GB |

Chạy mỗi mô hình trong một process riêng (các script đã làm vậy). Muốn chạy song song hai việc, giảm `--gpu-mem` xuống khoảng 0.45 cho mỗi việc.

---

## 6. Xử lý sự cố

| Lỗi | Cách xử lý |
| --- | --- |
| `torch không thấy GPU` | `nvidia-smi` phải chạy được; driver quá cũ so với bản CUDA của torch thì cập nhật driver |
| vLLM báo kiến trúc không hỗ trợ (Qwen3.5) | Qwen3.5-9B cần vLLM ≥ 0.17.0: `uv pip install --python .venv-vllm/bin/python -U vllm --torch-backend=auto` |
| Hy-MT2 lỗi trên vLLM | Dùng `MT_BACKEND=hf` (chạy qua `.venv-train`) |
| `CUDA out of memory` | Giảm `--gpu-mem`; kiểm tra không còn process cũ: `nvidia-smi`, rồi `kill <PID>` |
| Tải mô hình bị ngắt | Chạy lại `download_models.sh`, phần đã tải được giữ nguyên |
| `rsync: command not found` | Máy local Windows không có rsync → dùng `scp` (§2). `scripts/sync.sh` chỉ dành cho Linux/WSL |
| PowerShell báo `&&` không hợp lệ | PS5 không có `&&`; tách hai dòng, hoặc `lệnh1; if ($?) { lệnh2 }` |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope Process RemoteSigned` rồi activate lại |
| Mất SSH giữa chừng | Vào lại, `tmux a -t vimed`; chương trình vẫn đang chạy |
