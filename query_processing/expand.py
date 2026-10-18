"""Dùng LLM mở để trích thực thể y khoa và tạo bản dịch nháp cho câu hỏi.

Đầu ra mỗi câu hỏi gồm bản dịch `en`/`zh` và danh sách `entities` đa ngôn ngữ.
"""
import json
import logging
import re
import time

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a biomedical information specialist. You receive a medical question in Vietnamese.
Return ONLY one JSON object, no explanation, no markdown, with these keys:

"en": faithful English translation of the question.
"zh": faithful Simplified Chinese translation of the question.
"entities": list of the key medical concepts in the question, each as {"vi": ..., "en": ..., "zh": ...}.
  "vi" must be copied exactly as it is written in the question.
  Use standard biomedical terminology in English and Simplified Chinese.
  Keep drug, gene, protein, mutation names and abbreviations exactly as written; add the full form if an abbreviation is used.
Use concise, standard biomedical terminology. Preserve the meaning of the question and do not invent facts."""

FEW_SHOT_USER = "Cần làm gì đối với tình trạng tắc nghẽn đường tiết niệu do sỏi thận?"
FEW_SHOT_ASSISTANT = json.dumps({
    "en": "What should be done for urinary tract obstruction caused by kidney stones?",
    "zh": "对于肾结石引起的尿路梗阻应该怎么处理？",
    "entities": [
        {"vi": "sỏi thận", "en": "kidney calculi", "zh": "肾结石"},
        {"vi": "tắc nghẽn đường tiết niệu", "en": "urinary tract obstruction", "zh": "尿路梗阻"},
    ],
}, ensure_ascii=False)


def build_messages(query_vi: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": FEW_SHOT_USER},
        {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
        {"role": "user", "content": query_vi},
    ]


def salvage_json(blob: str):
    """Vớt từng khoá khi JSON sai cú pháp. Trả None nếu không vớt được gì.

    Qwen3.5-9B lượng tử 4-bit sinh JSON hỏng cú pháp ở 17,2% câu (đo 03/10, 11/64 câu):
    nó chèn ký tự lạ giữa chuỗi (một dấu `)` và newline ngay sau dấu nháy đóng), dù JSON vẫn
    ĐỦ (raw 1.357 ký tự, kết thúc bằng `]}`) nên KHÔNG phải lỗi `max_tokens`. `json.loads`
    thất bại là mất CẢ bản dịch zh lẫn thực thể - đúng hai thứ nhánh tiếng Trung cần - trong
    khi đọc theo từng khoá thì vẫn lấy được.
    """
    def one(key):
        m = re.search(rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"', blob)
        if not m:
            return ""
        try:
            return json.loads('"' + m.group(1) + '"')
        except json.JSONDecodeError:
            return m.group(1)

    ents = []
    ea = re.search(r'"entities"\s*:\s*\[(.*?)\]', blob, re.S)
    if ea:
        for om in re.finditer(r"\{[^{}]*\}", ea.group(1)):
            try:
                o = json.loads(om.group(0))
            except json.JSONDecodeError:
                continue
            if isinstance(o, dict):
                ents.append(o)
    en, zh = one("en"), one("zh")
    if not (en or zh or ents):
        return None
    return {"en": en, "zh": zh, "entities": ents}


def parse_llm_output(text: str) -> dict:
    """Parse JSON một cách chịu lỗi. Luôn trả về đủ key; 'parse_ok' báo có parse được không."""
    empty = {"en": "", "zh": "", "entities": [], "parse_ok": False}
    if not text:
        return empty
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)  # Qwen3 thinking block, nếu có
    text = re.sub(r"```(?:json)?", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return empty
    try:
        obj = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        obj = salvage_json(text[start:end + 1])      # vớt theo khoá, xem salvage_json
        if obj is None:
            return empty
    if not isinstance(obj, dict):
        return empty

    entities = [e for e in (obj.get("entities") or []) if isinstance(e, dict)]
    en = str(obj.get("en") or "").strip()
    zh = str(obj.get("zh") or "").strip()
    return {
        "en": en,
        "zh": zh,
        "entities": entities,
        "parse_ok": bool(en or zh or entities),
    }


# Greedy decoding: JSON ổn định và tái lập được giữa các lần chạy (quan trọng cho private test)
# max_tokens 768 cắt mất JSON của câu dài: đo 03/10 trên 64 câu đầu, 11 câu (17,2%) bị lỗi
# phân tích cú pháp; các câu đó có độ dài trung vị 57 từ so với 20 từ của cả batch. Một câu 283 từ
# cần ~1.000 token cho en + zh + 20 thực thể × 3 ngôn ngữ. Greedy decode
# dừng ở EOS nên nới trần không làm câu ngắn chậm hơn.
LLM_SAMPLING = {"temperature": 0.0, "max_tokens": 2048}
# Qwen3/Qwen3.5: tắt thinking để trả JSON trực tiếp (Qwen3.5 Small đã tắt sẵn, truyền thêm cho chắc)
LLM_CHAT_KWARGS = {"enable_thinking": False}


def expand_queries(backend, items: list[dict], batch_size: int = 64,
                   partial_path=None) -> list[dict]:
    """items: [{"id", "query"}] -> [{"id", "query", "en", "zh", "entities", "parse_ok"}]

    `partial_path`: ghi dần sau mỗi batch và log tốc độ. Backend `hf` sinh TUẦN TỰ từng câu
    (vLLM thì batch), nên 1.200 câu có thể mất nhiều giờ: ghi một lần ở cuối thì job chết là
    mất sạch, và không cách nào biết còn bao lâu.
    """
    results = []
    t0 = time.monotonic()
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        texts = backend.generate([build_messages(x["query"]) for x in batch])
        for item, text in zip(batch, texts):
            parsed = parse_llm_output(text)
            if not parsed["parse_ok"]:
                log.warning("Câu %s: LLM không trả về bản dịch hoặc thực thể hợp lệ.", item["id"])
            results.append({"id": item["id"], "query": item["query"], **parsed, "raw": text})
        if partial_path:
            with open(partial_path, "a", encoding="utf-8") as f:
                for r in results[-len(batch):]:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        done, el = len(results), time.monotonic() - t0
        log.info("expand %d/%d câu | %.1f s/câu | còn ~%.0f phút",
                 done, len(items), el / done, (len(items) - done) * el / done / 60)
    return results
