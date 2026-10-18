"""Backend chạy LLM local, dùng chung cho Qwen3.5 (hiểu câu hỏi) và Hy-MT2 (dịch).

Mỗi lần chạy pipeline chỉ nạp MỘT mô hình, nên chạy từng stage trong process riêng
(xem run_all.sh) để GPU được giải phóng hoàn toàn giữa các mô hình.
"""
import logging

log = logging.getLogger(__name__)


class VLLMChat:
    def __init__(self, model: str, sampling: dict, max_model_len: int = 4096,
                 gpu_memory_utilization: float = 0.85, quantization: str | None = None,
                 trust_remote_code: bool = False, text_only: bool = False,
                 chat_template_kwargs: dict | None = None):
        from vllm import LLM, SamplingParams
        kwargs = dict(model=model, max_model_len=max_model_len,
                      gpu_memory_utilization=gpu_memory_utilization,
                      quantization=quantization, trust_remote_code=trust_remote_code)
        if text_only:
            # Qwen3.5 là mô hình đa phương thức: tắt đầu vào ảnh/video để tiết kiệm VRAM
            kwargs["limit_mm_per_prompt"] = {"image": 0, "video": 0}
        try:
            self.llm = LLM(**kwargs)
        except Exception as e:
            if "limit_mm_per_prompt" not in kwargs:
                raise
            log.warning("Không đặt được limit_mm_per_prompt (%s), thử lại không có nó.", e)
            kwargs.pop("limit_mm_per_prompt")
            self.llm = LLM(**kwargs)
        self.params = SamplingParams(**sampling)
        self.chat_template_kwargs = chat_template_kwargs

    def generate(self, conversations: list[list[dict]]) -> list[str]:
        kw = {"chat_template_kwargs": self.chat_template_kwargs} if self.chat_template_kwargs else {}
        outs = self.llm.chat(conversations, self.params, **kw)
        return [o.outputs[0].text for o in outs]


class HFChat:
    """Dự phòng khi không cài được vLLM. Chậm hơn nhiều (sinh tuần tự từng câu)."""

    def __init__(self, model: str, sampling: dict, load_in_4bit: bool = False,
                 trust_remote_code: bool = False, chat_template_kwargs: dict | None = None):
        import torch
        from transformers import AutoTokenizer
        self.torch = torch
        kwargs = {"device_map": "auto", "dtype": "auto", "trust_remote_code": trust_remote_code}
        if load_in_4bit:
            from transformers import BitsAndBytesConfig
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
        self.tok = AutoTokenizer.from_pretrained(model, trust_remote_code=trust_remote_code)
        try:
            from transformers import AutoModelForCausalLM
            self.model = AutoModelForCausalLM.from_pretrained(model, **kwargs)
        except (ValueError, KeyError):
            # Một số mô hình đa phương thức (vd. Qwen3.5) cần lớp image-text-to-text
            from transformers import AutoModelForImageTextToText
            self.model = AutoModelForImageTextToText.from_pretrained(model, **kwargs)
        self.model.eval()
        self.chat_template_kwargs = chat_template_kwargs or {}

        t = sampling.get("temperature", 0.0)
        self.gen_kwargs = {"max_new_tokens": sampling.get("max_tokens", 768)}
        if t and t > 0:
            self.gen_kwargs.update(do_sample=True, temperature=t,
                                   top_p=sampling.get("top_p", 1.0),
                                   top_k=sampling.get("top_k", 50))
        else:
            self.gen_kwargs["do_sample"] = False
        if sampling.get("repetition_penalty"):
            self.gen_kwargs["repetition_penalty"] = sampling["repetition_penalty"]

    def generate(self, conversations: list[list[dict]]) -> list[str]:
        outs = []
        for msgs in conversations:
            prompt = self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                                                  **self.chat_template_kwargs)
            inputs = self.tok(prompt, return_tensors="pt").to(self.model.device)
            with self.torch.no_grad():
                gen = self.model.generate(**inputs, **self.gen_kwargs)
            outs.append(self.tok.decode(gen[0][inputs["input_ids"].shape[1]:],
                                        skip_special_tokens=True))
        return outs


def make_backend(kind: str, model: str, sampling: dict, *, quantization=None, load_in_4bit=False,
                 trust_remote_code=False, text_only=False, chat_template_kwargs=None,
                 gpu_memory_utilization=0.85, max_model_len=4096):
    if kind == "vllm":
        return VLLMChat(model, sampling, max_model_len=max_model_len,
                        gpu_memory_utilization=gpu_memory_utilization, quantization=quantization,
                        trust_remote_code=trust_remote_code, text_only=text_only,
                        chat_template_kwargs=chat_template_kwargs)
    return HFChat(model, sampling, load_in_4bit=load_in_4bit, trust_remote_code=trust_remote_code,
                  chat_template_kwargs=chat_template_kwargs)
