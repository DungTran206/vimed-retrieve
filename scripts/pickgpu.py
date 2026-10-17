"""In chỉ số GPU còn trống >= GB đối số (dùng torch vì nvidia-smi có thể hỏng khi driver lệch phiên bản). Không in gì nếu không có."""
import sys
import torch
need = float(sys.argv[1]) * 1024 ** 3
for i in range(torch.cuda.device_count()):
    free, _ = torch.cuda.mem_get_info(i)
    if free >= need:
        print(i); break
