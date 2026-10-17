"""BM25F trên CỤM TỪ KHOÁ (entity do Qwen trích) + bigram từ, chạy đa tiến trình.

Khác `bm25.py`: (1) câu hỏi chỉ gồm các cụm entity (nhiễu thấp hơn câu gốc dài), (2) thêm token
bigram từ ("dạ dày") ở CẢ doc lẫn câu hỏi nên cụm từ khớp nguyên cụm được thưởng IDF cao,
(3) chia doc theo khoảng rowid cho nhiều tiến trình (bm25.py chạy một luồng, 2 lượt tokenize).
Dùng lại tokenizer/trọng số trường/công thức của `bm25.py`. Chỉ cho tiếng Việt (store vi_slim).

    python bm25_ent.py --db data/vi_slim.sqlite --workers 5 --out data/bm25ent_rank.jsonl
    python bm25_ent.py --demo
"""
import argparse
import collections
import heapq
import json
import math
import sqlite3
from multiprocessing import Pool

import bm25

FIRST = {}
SEL = "SELECT doc_id, title, descr, tags, body FROM doc WHERE rowid BETWEEN ? AND ? AND length(body)>=200"


def terms(ts):
    """Unigram + bigram từ liền kề."""
    return ts + [a + " " + b for a, b in zip(ts, ts[1:])]


def doc_terms(text, vocab):
    """Chỉ giữ token thuộc vocab của câu hỏi. Bigram chỉ ghép khi từ đầu nằm trong vocab bigram
    (tránh nối chuỗi cho mọi cặp từ của cả bài: đó là phần tốn nhất)."""
    ts = bm25.tok_vi(text)
    first = FIRST.get(id(vocab))
    if first is None:
        first = FIRST[id(vocab)] = {t.split(" ")[0] for t in vocab if " " in t}
    return [t for t in ts if t in vocab] + [
        b for a, c in zip(ts, ts[1:]) if a in first and (b := a + " " + c) in vocab]


def init(db, vocab_, term_qs_):
    global CONN, VOCAB, TERM_QS
    bm25.KEEP_DIACRITICS = True
    CONN = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    VOCAB, TERM_QS = vocab_, term_qs_


def pass1(rng):
    df, flen, n = collections.Counter(), collections.Counter(), 0
    for _id, *rest in CONN.execute(SEL, rng):
        n += 1
        seen = set()
        for f, text in zip(bm25.FIELDS, bm25.doc_fields(rest)):
            flen[f] += len(bm25.tok_vi(text))          # độ dài trường tính theo từ đơn, như bm25.py
            seen.update(doc_terms(text, VOCAB))
        df.update(seen)
    return df, flen, n


def pass2(args):
    rng, idf, avg, topk = args
    heaps = {}
    for doc_id, *rest in CONN.execute(SEL, rng):
        tfs = collections.defaultdict(float)
        for f, text in zip(bm25.FIELDS, bm25.doc_fields(rest)):
            ln = len(bm25.tok_vi(text))
            if not ln:
                continue
            wf = bm25.WEIGHTS[f] / (1 - bm25.B + bm25.B * ln / max(avg[f], 1e-9))
            for t, c in collections.Counter(doc_terms(text, VOCAB)).items():
                tfs[t] += wf * c
        scores = collections.defaultdict(float)
        for t, tf in tfs.items():
            part = idf[t] * tf / (bm25.K1 + tf)
            for q in TERM_QS[t]:
                scores[q] += part
        for q, sc in scores.items():
            h = heaps.setdefault(q, [])
            if len(h) < topk:
                heapq.heappush(h, (sc, doc_id))
            elif sc > h[0][0]:
                heapq.heapreplace(h, (sc, doc_id))
    return heaps


def load_entities(path):
    """{qid: set term} từ các cụm entity 'vi'. Câu không có entity -> không có nguồn này."""
    bm25.KEEP_DIACRITICS = True
    out = {}
    for line in open(path, encoding="utf-8"):
        o = json.loads(line)
        ts = set()
        for e in o.get("entities") or []:
            ts.update(terms(bm25.tok_vi(e.get("vi", "") if isinstance(e, dict) else str(e))))
        if ts:
            out[int(o["id"])] = ts
    return out


def run(db, ents, workers, topk):
    term_qs = collections.defaultdict(list)
    for q, ts in ents.items():
        for t in ts:
            term_qs[t].append(q)
    vocab = frozenset(term_qs)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    lo, hi = conn.execute("SELECT min(rowid), max(rowid) FROM doc").fetchone()
    step = (hi - lo + 1) // (workers * 4) + 1               # 4 mảnh/worker để cân tải
    rngs = [(a, min(a + step - 1, hi)) for a in range(lo, hi + 1, step)]
    with Pool(workers, init, (db, vocab, dict(term_qs))) as pool:
        df, flen, n = collections.Counter(), collections.Counter(), 0
        for d, fl, k in pool.imap_unordered(pass1, rngs):
            df.update(d); flen.update(fl); n += k
        avg = {f: flen[f] / n for f in bm25.FIELDS}
        idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        print(f"Lượt 1: {n:,} doc | term trong câu hỏi có mặt ở kho: {len(idf):,}/{len(vocab):,}", flush=True)
        heaps = collections.defaultdict(list)
        for h in pool.imap_unordered(pass2, [(r, idf, avg, topk) for r in rngs]):
            for q, items in h.items():
                heaps[q] = heapq.nlargest(topk, heaps[q] + items)
    return heaps


def demo():
    bm25.KEEP_DIACRITICS = True
    assert terms(["dạ", "dày"]) == ["dạ", "dày", "dạ dày"]
    assert doc_terms("Viêm dạ dày", frozenset({"dạ dày", "xyz"})) == ["dạ dày"]
    assert sorted(doc_terms("dạ dày dạ", frozenset({"dạ dày", "dạ"}))) == ["dạ", "dạ", "dạ dày"]
    print("demo OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/vi_slim.sqlite")
    ap.add_argument("--queries", default="data/queries_enriched.jsonl")
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--topk", type=int, default=1000)
    ap.add_argument("--out", default="data/bm25ent_rank.jsonl")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    demo()
    if not a.demo:
        ents = load_entities(a.queries)
        print(f"{len(ents)} câu có entity", flush=True)
        h = run(a.db, ents, a.workers, a.topk)
        with open(a.out, "w", encoding="utf-8") as f:
            for q in sorted(ents):
                cands = [{"doc_id": d, "score": round(s, 6)} for s, d in sorted(h.get(q, []), reverse=True)]
                f.write(json.dumps({"id": q, "candidates": cands}, ensure_ascii=False) + "\n")
        print(f"-> {a.out}")
