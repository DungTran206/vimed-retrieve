"""Dịch câu hỏi tiếng Việt sang tiếng Anh và tiếng Trung bằng Hy-MT2-7B.

Thực thể y khoa do Qwen3.5 trích ở bước expand được đưa vào prompt dưới dạng bảng thuật ngữ
(tính năng "Terminology" trong model card Hy-MT2), để tên bệnh/thuốc được dịch nhất quán.
Prompt theo đúng mẫu của model card: prompt tiếng Anh cho đích tiếng Anh, prompt tiếng Trung
cho đích tiếng Trung, và không dùng system prompt.
"""
import logging

log = logging.getLogger(__name__)

# Tham số khuyến nghị cho Hy-MT2 1.8B/7B trong model card; thêm seed để tái lập được kết quả
MT_SAMPLING = {"temperature": 0.7, "top_p": 0.6, "top_k": 20, "repetition_penalty": 1.05,
               "max_tokens": 512, "seed": 0}
MT_SAMPLING_GREEDY = {"temperature": 0.0, "repetition_penalty": 1.05, "max_tokens": 512}

TARGETS = {
    "en": {
        "lang": "English",
        "line": "{src} translates to {tgt}",
        "plain": ("Translate the following text into {lang}. Note that you should only output "
                  "the translated result without any additional explanation:\n\n{text}"),
        "term": ("Reference the following translations:\n{glossary}\n\n"
                 "Translate the following text into {lang}. Note that you must ONLY output "
                 "the translated result without any additional explanation:\n\n{text}"),
    },
    "zh": {
        "lang": "中文",
        "line": "{src} 翻译成 {tgt}",
        "plain": "将以下文本翻译为{lang}，注意只需要输出翻译后的结果，不要额外解释：\n\n{text}",
        "term": "参考下面的翻译：\n{glossary}\n\n将以下文本翻译为{lang}，注意只需要输出翻译后的结果，不要额外解释：\n\n{text}",
    },
}


def build_glossary(query: str, entities: list[dict], tgt: str, max_terms: int = 8) -> list[tuple[str, str]]:
    """Chỉ giữ thuật ngữ mà phần tiếng Việt thực sự xuất hiện trong câu hỏi,
    để tránh đưa thuật ngữ LLM tự bịa vào bản dịch."""
    q = query.lower()
    out, seen = [], set()
    for e in entities:
        src = str(e.get("vi") or "").strip()
        dst = str(e.get(tgt) or "").strip()
        if not src or not dst or src.lower() not in q or src.lower() in seen:
            continue
        seen.add(src.lower())
        out.append((src, dst))
    # Thuật ngữ dài trước: tránh cụm ngắn "ăn" mất cụm dài chứa nó
    out.sort(key=lambda x: -len(x[0]))
    return out[:max_terms]


def build_prompt(query: str, tgt: str, glossary: list[tuple[str, str]]) -> str:
    t = TARGETS[tgt]
    if glossary:
        lines = "\n".join(t["line"].format(src=s, tgt=d) for s, d in glossary)
        return t["term"].format(glossary=lines, lang=t["lang"], text=query)
    return t["plain"].format(lang=t["lang"], text=query)


def clean_translation(text: str) -> str:
    text = (text or "").strip()
    # Câu hỏi chỉ một câu: gộp dòng nếu mô hình xuống dòng thừa
    return " ".join(line.strip() for line in text.splitlines() if line.strip())


def translate_queries(backend, expansions: list[dict], use_glossary: bool = True,
                      batch_size: int = 64) -> list[dict]:
    """expansions: đầu ra bước expand (cần 'id', 'query', 'entities')."""
    jobs = []  # (index, tgt, glossary, prompt)
    for i, exp in enumerate(expansions):
        for tgt in ("en", "zh"):
            gl = build_glossary(exp["query"], exp.get("entities", []), tgt) if use_glossary else []
            jobs.append((i, tgt, gl, build_prompt(exp["query"], tgt, gl)))

    results = [{"id": e["id"], "query": e["query"]} for e in expansions]
    for s in range(0, len(jobs), batch_size):
        batch = jobs[s:s + batch_size]
        texts = backend.generate([[{"role": "user", "content": j[3]}] for j in batch])
        for (i, tgt, gl, _), text in zip(batch, texts):
            results[i][tgt] = clean_translation(text)
            results[i][f"glossary_{tgt}"] = gl
    for r in results:
        for tgt in ("en", "zh"):
            if not r.get(tgt):
                log.warning("Câu %s: bản dịch %s rỗng.", r["id"], tgt)
    return results


def enrich(expansions: list[dict], translations: list[dict] | None) -> list[dict]:
    """Gộp thành một bản ghi/câu cho các bước sau. Ưu tiên bản dịch Hy-MT2,
    thiếu thì dùng bản dịch nháp của Qwen3.5."""
    tr = {t["id"]: t for t in (translations or [])}
    out = []
    for e in expansions:
        t = tr.get(e["id"], {})
        out.append({
            "id": e["id"],
            "query": e["query"],
            "en": t.get("en") or e.get("en", ""),
            "zh": t.get("zh") or e.get("zh", ""),
            "en_llm": e.get("en", ""),
            "zh_llm": e.get("zh", ""),
            "entities": e.get("entities", []),
            "translation_source": "hy-mt2" if t.get("en") else "llm",
        })
    return out
