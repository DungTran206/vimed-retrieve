"""Rerank bằng Qwen3-Reranker (causal LM chấm xác suất "yes"/"no"), theo đúng cách model card mô tả.

Khác `rerank.py` (cross-encoder bge): Qwen3-Reranker đọc prompt gồm chỉ dẫn + câu hỏi + tài liệu rồi
cho logit của token "yes" so với "no"; điểm = P(yes). Ghi dần từng câu vào `.partial` và chạy tiếp
được từ chỗ dừng (lần rerank trước chết giữa chừng, mất công làm lại).

    python qwen_rerank.py --cands data/qr_cands.jsonl --db data/qr_text.sqlite --out data/qwen_rr.jsonl
    python qwen_rerank.py --demo
"""
import argparse
import json
import os
import sqlite3
import sys
import time

MODEL = os.environ.get("QWEN_RR_MODEL", "Qwen/Qwen3-Reranker-4B")   # QWEN_RR_MODEL=Qwen/Qwen3-Reranker-8B để thử bản 8B
# Chỉ dẫn pointwise. KHÔNG đổi PREFIX/SUFFIX: đó là judge-template lúc fine-tune, quyết định vị trí
# chấm logit yes/no. Nội dung: chấm công dụng lâm sàng thật, loại doc chỉ lặp từ khoá (keyword
# spamming) và doc gần đúng nhưng sai đối tượng/biến thể (deceptive negatives).
# Không thêm persona ("You are a medical expert"): model đã judge-tune trên template này, persona
# chỉ dịch thang p(yes) chứ gần như không đổi thứ hạng (xem PROGRESS.md, chỉ dẫn nghiêm 12/10).
INSTRUCT = os.environ.get("QWEN_RR_INSTRUCT") or (
    "Given a patient's health question in Vietnamese and one candidate document "
    "(a medical Q&A, drug monograph, clinical guideline, or health article), decide "
    "whether the document provides the specific clinical information the question asks for. "
    "Judge clinical utility, not surface similarity.\n"
    'Answer "yes" only if the document gives the requested information for the same '
    "condition, drug, test, procedure or population the question is about, including when "
    "the document is written in English or Chinese while the question is in Vietnamese.\n"
    'Answer "no" if:\n'
    "- it only repeats keywords from the question, or mentions the same disease or drug in "
    "passing without answering it (keyword spamming);\n"
    "- it covers the same disease or drug but for a different population (child vs adult, "
    "pregnancy, elderly), a different subtype, stage or variant, an unrelated indication, or "
    "a contraindication or adverse outcome the question did not ask about;\n"
    "- it is too generic to resolve the question: general background, definitions, or an "
    "overview that never addresses the specific thing asked;\n"
    "- it is about a different topic entirely.")
PREFIX = ('<|im_start|>system\nJudge whether the Document meets the requirements based on the Query '
          'and the Instruct provided. Note that the answer can only be "yes" or "no".<|im_end|>\n'
          '<|im_start|>user\n')
SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
DOC_CHARS, QUERY_CHARS = 1000, 1200


def build(query, doc, doc_chars=None):
    dc = doc_chars if doc_chars is not None else DOC_CHARS
    return (PREFIX + f"<Instruct>: {INSTRUCT}\n<Query>: {query[:QUERY_CHARS]}\n<Document>: {doc[:dc]}"
            + SUFFIX)


def p_yes(logit_no, logit_yes):
    """P(yes) = softmax trên hai logit; tính ổn định số học."""
    import math
    m = max(logit_no, logit_yes)
    a, b = math.exp(logit_no - m), math.exp(logit_yes - m)
    return b / (a + b)


def doc_texts(db, ids):
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    out, ids = {}, list(ids)
    for i in range(0, len(ids), 900):
        part = ids[i:i + 900]
        for d, t, b in conn.execute(
                f"SELECT doc_id, ifnull(title,''), ifnull(body,'') FROM doc WHERE doc_id IN ({','.join('?' * len(part))})", part):
            out[str(d)] = (t + ". " + b).strip() if t else b
    return out


def load_model(device=None, mem_fraction=None):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    if dev.startswith("cuda") and mem_fraction:
        torch.cuda.set_per_process_memory_fraction(mem_fraction)
    tok = AutoTokenizer.from_pretrained(MODEL, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16).to(dev).eval()
    yes, no = tok.convert_tokens_to_ids("yes"), tok.convert_tokens_to_ids("no")
    assert yes != tok.unk_token_id and no != tok.unk_token_id, "không tìm thấy token yes/no"
    return tok, model, yes, no, dev


def score_pairs(tok, model, yes, no, dev, pairs, batch=16, max_len=1536, doc_chars=None):
    """pairs: [(query, doc)] -> [P(yes)], sắp theo độ dài để giảm padding rồi trả đúng thứ tự gốc.
    Hết VRAM thì tự chia đôi lô (lần chạy trước chết giữa chừng vì OOM ở lô dài)."""
    import torch
    texts = [build(q, d, doc_chars=doc_chars) for q, d in pairs]
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    out = [0.0] * len(texts)
    # Mốc soát cắt cụt. truncation=True cắt từ BÊN PHẢI nên nếu prompt dài quá max_len thì mất
    # luôn SUFFIX -> chấm logit ở sai vị trí, điểm thành rác mà không báo gì.
    tail = torch.tensor(tok(SUFFIX, add_special_tokens=False)["input_ids"])

    def run(idx):
        oom = False
        try:
            with torch.no_grad():
                enc = tok([texts[i] for i in idx], padding=True, truncation=True, max_length=max_len,
                          return_tensors="pt").to(dev)
                ids = enc["input_ids"]
                bad = (ids[:, -tail.numel():] != tail.to(ids.device)).any(dim=1)
                assert not bad.any(), (
                    f"{int(bad.sum())}/{len(idx)} prompt bị cắt cụt mất SUFFIX (yes/no chấm sai vị trí): "
                    f"giảm --doc-chars hoặc tăng --max-len (đang là {max_len})")
                # chỉ lm_head cho token CUỐI: logits mọi vị trí tốn batch×độ dài×151k float
                h = model.model(**enc).last_hidden_state[:, -1, :]
                lg = model.lm_head(h)
                two = torch.stack([lg[:, no], lg[:, yes]], dim=1).float()
                for i, p in zip(idx, torch.softmax(two, dim=1)[:, 1].tolist()):
                    out[i] = p
        except torch.OutOfMemoryError:
            oom = True
        if oom:
            # thử lại NGOÀI khối except: trong khối đó traceback còn giữ tensor nên empty_cache không giải phóng được gì
            torch.cuda.empty_cache()
            if len(idx) == 1:
                raise RuntimeError("hết VRAM ngay cả với 1 cặp")
            mid = len(idx) // 2
            run(idx[:mid])
            run(idx[mid:])

    for s in range(0, len(order), batch):
        run(order[s:s + batch])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", default="data/qr_cands.jsonl")
    ap.add_argument("--queries", default="data/queries.jsonl")
    ap.add_argument("--db", default="data/qr_text.sqlite")
    ap.add_argument("--out", default="data/qwen_rr.jsonl")
    ap.add_argument("--topk", type=int, default=150)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--doc-chars", type=int, default=3000)
    ap.add_argument("--max-len", type=int, default=2048)
    ap.add_argument("--mem-fraction", type=float, default=None)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    demo()
    if a.demo:
        return
    qtext = {}
    for l in open(a.queries, encoding="utf-8"):
        o = json.loads(l)
        qtext[o["id"]] = o["query"]
    cands = [json.loads(l) for l in open(a.cands, encoding="utf-8")]
    if a.limit:
        cands = cands[:a.limit]
    part = a.out + ".partial"
    done = set()
    if os.path.exists(part):
        for l in open(part, encoding="utf-8"):
            try:
                done.add(json.loads(l)["id"])
            except Exception:
                pass                       # dòng cuối có thể cụt khi tiến trình chết
    todo = [c for c in cands if c["id"] not in done]
    print(f"{len(done)} câu đã xong, còn {len(todo)}", flush=True)
    if todo:
        ids = {str(c["doc_id"]) for r in todo for c in r["candidates"][:a.topk]}
        texts = doc_texts(a.db, ids)
        print(f"text cho {len(texts)}/{len(ids)} doc (đọc tối đa {a.doc_chars} ký tự)", flush=True)
        tok, model, yes, no, dev = load_model(mem_fraction=a.mem_fraction)
        t0 = time.time()
        with open(part, "a", encoding="utf-8") as pf:
            for n, r in enumerate(todo, 1):
                cs = [str(c["doc_id"]) for c in r["candidates"][:a.topk]]
                have = [d for d in cs if d in texts]
                sc = score_pairs(tok, model, yes, no, dev, [(qtext[r["id"]], texts[d]) for d in have],
                                 batch=a.batch, max_len=a.max_len, doc_chars=a.doc_chars)
                rows = [{"doc_id": d, "score": round(s, 6)} for d, s in zip(have, sc)]
                rows.sort(key=lambda x: -x["score"])
                pf.write(json.dumps({"id": r["id"], "candidates": rows}, ensure_ascii=False) + "\n")
                pf.flush()
                if n % 10 == 0:
                    el = time.time() - t0
                    print(f"  {n}/{len(todo)} câu | {el / n:.1f}s/câu | còn ~{el / n * (len(todo) - n) / 60:.0f} phút", flush=True)
    rows = {}
    for l in open(part, encoding="utf-8"):
        try:
            o = json.loads(l)
            rows[o["id"]] = o
        except Exception:
            pass
    with open(a.out, "w", encoding="utf-8") as f:
        for c in cands:
            if c["id"] in rows:
                f.write(json.dumps(rows[c["id"]], ensure_ascii=False) + "\n")
    print(f"-> {a.out} | {len(rows)} câu")


def demo():
    import math
    # SUFFIX là hợp đồng với model: đổi nó là chấm logit ở sai vị trí. Khoá lại bằng assert.
    assert SUFFIX == "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    s = build("đau dạ dày", "Viêm dạ dày. " + "x" * 5000, doc_chars=1000)
    assert s.startswith(PREFIX) and s.endswith(SUFFIX) and len(s) < 2700, "doc phải bị cắt"
    assert abs(p_yes(0.0, 0.0) - 0.5) < 1e-9 and p_yes(-50.0, 50.0) > 0.999999
    assert 0.0 <= p_yes(1000.0, -1000.0) < 1e-9, "không được tràn số"
    print("demo OK")


if __name__ == "__main__":
    main()
