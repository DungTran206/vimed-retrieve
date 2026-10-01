"""Dùng LLM mở (chạy local) để dịch câu hỏi tiếng Việt và sinh truy vấn PubMed.

Đầu ra mỗi câu hỏi:
{
  "en": "...",                 # bản dịch nháp tiếng Anh (dự phòng nếu không chạy bước dịch Hy-MT2)
  "zh": "...",                 # bản dịch nháp tiếng Trung giản thể
  "entities": [{"vi","en","zh"}],
  "pubmed_queries": ["...", ...]
}
"""
import json
import logging
import re

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a biomedical information specialist. You receive a medical question in Vietnamese.
Return ONLY one JSON object, no explanation, no markdown, with these keys:

"en": faithful English translation of the question.
"zh": faithful Simplified Chinese translation of the question.
"entities": list of the key medical concepts in the question, each as {"vi": ..., "en": ..., "zh": ...}.
  "vi" must be copied exactly as it is written in the question.
  Use standard medical terminology (English: MeSH-style names where possible; Chinese: standard Simplified Chinese medical terms).
  Keep drug, gene, protein, mutation names and abbreviations exactly as written; add the full form if an abbreviation is used.
"pubmed_queries": 3 to 5 English search queries for PubMed:
  1. A short keyword query with the core concepts (2-6 words).
  2. A query using synonyms or alternative terminology for the same concepts.
  3. One query using PubMed syntax with field tags such as [MeSH Terms] or [tiab] and AND/OR.
     Only use a MeSH heading if you are confident it exists; otherwise use [tiab].
  4-5. If the question has several distinct aspects (e.g. cause and treatment), one keyword query per aspect.
  Do not include question words or filler such as "what", "should", "how to". Do not invent facts."""

FEW_SHOT_USER = "Cần làm gì đối với tình trạng tắc nghẽn đường tiết niệu do sỏi thận?"
FEW_SHOT_ASSISTANT = json.dumps({
    "en": "What should be done for urinary tract obstruction caused by kidney stones?",
    "zh": "对于肾结石引起的尿路梗阻应该怎么处理？",
    "entities": [
        {"vi": "sỏi thận", "en": "kidney calculi", "zh": "肾结石"},
        {"vi": "tắc nghẽn đường tiết niệu", "en": "urinary tract obstruction", "zh": "尿路梗阻"},
    ],
    "pubmed_queries": [
        "kidney stone urinary obstruction management",
        "obstructive urolithiasis decompression treatment",
        "(\"Kidney Calculi\"[MeSH Terms] OR \"Ureteral Calculi\"[MeSH Terms]) AND \"Ureteral Obstruction\"[MeSH Terms]",
        "obstructing ureteral stone ureteral stent percutaneous nephrostomy",
    ],
}, ensure_ascii=False)


def build_messages(query_vi: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": FEW_SHOT_USER},
        {"role": "assistant", "content": FEW_SHOT_ASSISTANT},
        {"role": "user", "content": query_vi},
    ]


def parse_llm_output(text: str, max_queries: int = 6) -> dict:
    """Parse JSON một cách chịu lỗi. Luôn trả về đủ key; 'parse_ok' báo có parse được không."""
    empty = {"en": "", "zh": "", "entities": [], "pubmed_queries": [], "parse_ok": False}
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
        return empty
    if not isinstance(obj, dict):
        return empty

    queries = []
    for q in obj.get("pubmed_queries") or []:
        if isinstance(q, str):
            q = " ".join(q.split())
            if q and q.lower() not in {x.lower() for x in queries}:
                queries.append(q)
    entities = [e for e in (obj.get("entities") or []) if isinstance(e, dict)]
    return {
        "en": str(obj.get("en") or "").strip(),
        "zh": str(obj.get("zh") or "").strip(),
        "entities": entities,
        "pubmed_queries": queries[:max_queries],
        "parse_ok": bool(queries),
    }


def fallback_queries(parsed: dict) -> list[str]:
    """Nếu LLM không sinh được truy vấn hợp lệ: dùng bản dịch tiếng Anh và tên thực thể."""
    qs = []
    if parsed.get("en"):
        qs.append(parsed["en"])
    ents = [e.get("en") for e in parsed.get("entities", []) if e.get("en")]
    if ents:
        qs.append(" ".join(ents))
    return qs


# Greedy decoding: JSON ổn định và tái lập được giữa các lần chạy (quan trọng cho private test)
LLM_SAMPLING = {"temperature": 0.0, "max_tokens": 768}
# Qwen3/Qwen3.5: tắt thinking để trả JSON trực tiếp (Qwen3.5 Small đã tắt sẵn, truyền thêm cho chắc)
LLM_CHAT_KWARGS = {"enable_thinking": False}


def expand_queries(backend, items: list[dict], batch_size: int = 64) -> list[dict]:
    """items: [{"id", "query"}] -> [{"id", "query", "en", "zh", "entities", "pubmed_queries", "parse_ok"}]"""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        texts = backend.generate([build_messages(x["query"]) for x in batch])
        for item, text in zip(batch, texts):
            parsed = parse_llm_output(text)
            if not parsed["pubmed_queries"]:
                parsed["pubmed_queries"] = fallback_queries(parsed)
                log.warning("Câu %s: LLM không sinh được truy vấn hợp lệ, dùng fallback.", item["id"])
            results.append({"id": item["id"], "query": item["query"], **parsed, "raw": text})
    return results
