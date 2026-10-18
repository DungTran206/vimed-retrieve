"""Kiểm tra từng mô hình trên máy GPU bằng một ví dụ nhỏ. Mỗi lần chạy MỘT kiểm tra
(để VRAM được giải phóng giữa các mô hình); remote_check.sh gọi lần lượt tất cả.

  .venv-vllm/bin/python  scripts/remote_check.py llm
  .venv-vllm/bin/python  scripts/remote_check.py mt          # Hy-MT2 qua vLLM
  .venv-train/bin/python scripts/remote_check.py mt --hf     # Hy-MT2 qua transformers
  .venv-train/bin/python scripts/remote_check.py embed
  .venv-train/bin/python scripts/remote_check.py rerank
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

Q = "Metformin có gây thiếu vitamin B12 ở bệnh nhân đái tháo đường type 2 không?"
PASSAGES = [
    "Long-term metformin use is associated with vitamin B12 deficiency in patients with type 2 diabetes.",
    "长期服用二甲双胍与2型糖尿病患者维生素B12缺乏有关。",
    "Sỏi thận có thể gây tắc nghẽn đường tiết niệu và cần được can thiệp kịp thời.",
]


def gpu_info():
    import torch
    if not torch.cuda.is_available():
        sys.exit("LỖI: torch không thấy GPU (kiểm tra driver/CUDA).")
    free, total = torch.cuda.mem_get_info()
    print(f"GPU: {torch.cuda.get_device_name(0)} | trống {free/2**30:.1f} / {total/2**30:.1f} GB")


def check_llm(model, gpu_mem):
    from query_processing.llm import make_backend
    from query_processing.expand import LLM_CHAT_KWARGS, LLM_SAMPLING, build_messages, parse_llm_output
    be = make_backend("vllm", model, LLM_SAMPLING, text_only=True,
                      chat_template_kwargs=LLM_CHAT_KWARGS, gpu_memory_utilization=gpu_mem)
    t = time.time()
    out = be.generate([build_messages(Q)] * 8)  # 8 câu một lô để đo thông lượng
    p = parse_llm_output(out[0])
    print(f"8 câu trong {time.time()-t:.1f}s | parse_ok={p['parse_ok']}")

    print("entities:", p["entities"])
    return p["parse_ok"]


def check_mt(model, use_hf, gpu_mem):
    from query_processing.llm import make_backend
    from query_processing.translate import MT_SAMPLING, build_glossary, build_prompt
    ents = [{"vi": "thiếu vitamin B12", "en": "vitamin B12 deficiency", "zh": "维生素B12缺乏"},
            {"vi": "đái tháo đường type 2", "en": "type 2 diabetes mellitus", "zh": "2型糖尿病"}]
    be = make_backend("hf" if use_hf else "vllm", model, MT_SAMPLING, trust_remote_code=True,
                      gpu_memory_utilization=gpu_mem)
    convs = [[{"role": "user", "content": build_prompt(Q, t, build_glossary(Q, ents, t))}] for t in ("en", "zh")]
    t = time.time()
    en, zh = be.generate(convs)
    print(f"{time.time()-t:.1f}s\n  en: {en.strip()}\n  zh: {zh.strip()}")
    return bool(en.strip() and zh.strip())


def check_embed(model):
    import torch
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(model, device="cuda", model_kwargs={"torch_dtype": torch.float16})
    t = time.time()
    qv = m.encode([Q], normalize_embeddings=True)
    pv = m.encode(PASSAGES, normalize_embeddings=True)
    sims = (qv @ pv.T)[0]
    print(f"{time.time()-t:.2f}s | dim={qv.shape[1]}")
    for s, p in zip(sims, PASSAGES):
        print(f"  {s:.3f}  {p[:60]}")
    # Hai đoạn đúng (Anh, Trung) phải cao hơn đoạn sai (sỏi thận)
    return min(sims[0], sims[1]) > sims[2]


def check_rerank(model):
    import torch
    from sentence_transformers import CrossEncoder
    m = CrossEncoder(model, device="cuda", model_kwargs={"torch_dtype": torch.float16})
    t = time.time()
    scores = m.predict([(Q, p) for p in PASSAGES])
    print(f"{time.time()-t:.2f}s")
    for s, p in zip(scores, PASSAGES):
        print(f"  {float(s):.3f}  {p[:60]}")
    return min(scores[0], scores[1]) > scores[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("check", choices=["llm", "mt", "embed", "rerank"])
    ap.add_argument("--model")
    ap.add_argument("--hf", action="store_true", help="mt: dùng transformers thay vì vLLM")
    ap.add_argument("--gpu-mem", type=float, default=0.85)
    a = ap.parse_args()
    defaults = {"llm": "Qwen/Qwen3.5-9B", "mt": "tencent/Hy-MT2-7B",
                "embed": "BAAI/bge-m3", "rerank": "BAAI/bge-reranker-v2-m3"}
    model = a.model or defaults[a.check]
    print(f"===== {a.check}: {model}")
    gpu_info()
    ok = {"llm": lambda: check_llm(model, a.gpu_mem),
          "mt": lambda: check_mt(model, a.hf, a.gpu_mem),
          "embed": lambda: check_embed(model),
          "rerank": lambda: check_rerank(model)}[a.check]()
    print("KẾT QUẢ:", "OK" if ok else "CÓ VẤN ĐỀ, xem đầu ra phía trên")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
