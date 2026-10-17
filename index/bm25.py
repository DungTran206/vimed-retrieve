"""BM25F có trọng số theo trường, trên nội dung đã crawl. Theo `PIPELINE.md` §4a.

Biến 127k tài liệu đang nằm chết trong store thành tín hiệu xếp hạng. Trước file này, bộ
xếp hạng duy nhất là `slug_bm25.py` - chỉ đọc chuỗi URL, không đọc một chữ nào của trang.

**BM25F**, không phải "BM25 từng trường rồi cộng điểm": gộp tần suất từ các trường TRƯỚC khi
đưa vào hàm bão hoà. Cộng điểm sau sẽ cho một từ xuất hiện 1 lần ở 4 trường điểm cao hơn một
từ xuất hiện 10 lần ở 1 trường, vì mỗi trường tự bão hoà riêng.

    tf*(t,d) = Σ_f  w_f · tf(t, d_f) / (1 - b + b·len_f/avglen_f)
    score    = Σ_t  idf(t) · tf*(t,d) / (k1 + tf*(t,d))

Trọng số mặc định: `title` 3,0 · `tags` 2,0 · `descr` 1,5 · `body` 1,0.
Lý do `title` cao nhất: với site Q&A, title **chính là câu hỏi bệnh nhân** (đo được: 99,9%
doc có title), nên khớp query↔title là khớp câu hỏi với câu hỏi, không phải câu hỏi với tài liệu.
**Các trọng số này là PHỎNG ĐOÁN, chưa đo** - quét chúng trên leaderboard khi có thời gian.

**STREAMING hai lượt** từ SQLite, không `fetchall()`: máy local 11,7 GB RAM, và `chunk.py`
từng bị kill vì nạp hết body vào RAM. Bộ nhớ ở đây là O(số query × topk), không phụ thuộc
kích thước corpus.

Tách từ theo ngôn ngữ:
  vi  bỏ dấu + tách theo khoảng trắng (dùng lại `slug_bm25`)
  zh  **bigram ký tự** - cách chuẩn cho CJK trong IR (Lucene CJKAnalyzer làm vậy), tránh
      thêm dependency `jieba` và từ điển của nó

  python bm25.py --topk 1000                      # -> data/bm25_rank.jsonl
  python bm25.py --queries-zh runs/public/translations.jsonl   # khi đã có bản dịch
  python bm25.py --demo
"""
import argparse
import collections
import heapq
import json
import math
import os
import re
import sqlite3
import sys
import unicodedata

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from index.slug_bm25 import tokenize as _tok_fold  # bỏ dấu + tách khoảng trắng (đúng cho slug URL)

# GIỮ DẤU cho nội dung trang và câu hỏi. Bỏ dấu là đúng với slug (URL là ASCII) nhưng SAI với văn bản
# tiếng Việt: đo trên 120.000 doc, 36,7% token của 1.200 câu hỏi và 37,8% lần xuất hiện trong văn bản
# rơi vào nhóm bị gộp nhầm (`dau` = đau/đầu/dấu, `da` = đã/da/đa, `nhan` = nhân/nhận/nhãn): câu hỏi về
# "đau" khớp doc nói về "đầu". BM25F bỏ dấu cho P@34 chỉ 0,1198 (blend của ta 0,2774).
KEEP_DIACRITICS = False
_WORD = re.compile(r"[^\W_]+")


def tok_vi(s):
    if not KEEP_DIACRITICS:
        return _tok_fold(s)
    s = unicodedata.normalize("NFC", s or "").lower()
    return [t for t in _WORD.findall(s) if len(t) > 1 and not t.isdigit()]

DB = "data/corpus_new.sqlite"
K1, B = 1.5, 0.75
WEIGHTS = {"title": 3.0, "tags": 2.0, "descr": 1.5, "body": 1.0}
FIELDS = ("title", "descr", "tags", "body")
HAN = re.compile(r"[一-鿿]")


def tok_zh(s):
    """Bigram ký tự Hán + token latin/số (tên thuốc, chỉ số xét nghiệm).

    Tiếng Trung không có khoảng trắng nên không tách từ được bằng regex. Bigram là cách
    chuẩn trong IR cho CJK: '糖尿病' -> '糖尿', '尿病'. Hiệu quả gần bằng tách từ thật mà
    không cần từ điển.
    """
    if not s:
        return []
    out = [m.group() for m in re.finditer(r"[a-z0-9]{2,}", s.lower())]
    han = HAN.findall(s)
    # Bigram chỉ nối các ký tự Hán LIỀN NHAU trong văn bản gốc, không nối qua dấu câu
    for run in re.findall(r"[一-鿿]+", s):
        out += [run[i:i + 2] for i in range(len(run) - 1)] or [run]
    return out


def tok(s, lang):
    return tok_zh(s) if lang == "zh" else tok_vi(s)


def doc_fields(row):
    """(title, descr, tags, body) từ một dòng doc. `tags` là JSON -> nối thành chuỗi."""
    title, descr, tags, body = row
    if tags:
        try:
            tags = " ".join(json.loads(tags))
        except Exception:
            pass
    return title or "", descr or "", tags or "", body or ""


def load_queries(path, zh_path=None):
    """{qid: {'vi': [token], 'zh': [token]}}. `zh` rỗng nếu chưa có bản dịch."""
    qs = {}
    for line in open(path, encoding="utf-8"):
        o = json.loads(line)
        qs[int(o["id"])] = {"vi": tok_vi(o["query"]), "zh": []}
    if zh_path:
        n = 0
        for line in open(zh_path, encoding="utf-8"):
            o = json.loads(line)
            qid = int(o["id"])
            text = o.get("zh") or o.get("query_zh") or ""
            if qid in qs and text:
                qs[qid]["zh"] = tok_zh(text)
                n += 1
        print(f"Nạp bản dịch tiếng Trung cho {n}/{len(qs)} câu")
    else:
        # Không có bản dịch: vẫn khớp được token latin/số trong query (tên thuốc, chỉ số)
        for qid, d in qs.items():
            d["zh"] = [t for t in tok_zh(" ".join(d["vi"])) if not HAN.search(t)]
    return qs


def rank(conn, queries, topk=1000, weights=None, k1=K1, b=B, batch=5000):
    """BM25F streaming hai lượt. Trả {qid: [(score, doc_id)]} giảm dần."""
    w = dict(WEIGHTS, **(weights or {}))
    # term -> các query dùng nó, tách theo ngôn ngữ (token zh không khớp doc vi và ngược lại)
    term_qs = {"vi": collections.defaultdict(list), "zh": collections.defaultdict(list)}
    for qid, d in queries.items():
        for lang in ("vi", "zh"):
            for t in set(d[lang]):
                term_qs[lang][t].append(qid)

    sel = "SELECT lang, title, descr, tags, body FROM doc WHERE length(body)>=200"
    # ---- Lượt 1: df của riêng term trong query, và độ dài trung bình từng trường
    df = {"vi": collections.Counter(), "zh": collections.Counter()}
    flen = collections.Counter()
    ndoc = collections.Counter()
    rd = conn.cursor()
    rd.arraysize = 500
    rd.execute(sel)
    for lang, *rest in rd:
        lang = lang if lang in ("vi", "zh") else "vi"
        ndoc[lang] += 1
        seen = set()
        for fname, text in zip(FIELDS, doc_fields(rest)):
            ts = tok(text, lang)
            flen[(lang, fname)] += len(ts)
            seen |= set(ts)
        for t in seen & term_qs[lang].keys():
            df[lang][t] += 1
    n_all = sum(ndoc.values())
    if not n_all:
        return {}
    avg = {(l, f): (flen[(l, f)] / ndoc[l] if ndoc[l] else 1.0)
           for l in ("vi", "zh") for f in FIELDS}
    idf = {l: {t: math.log(1 + (ndoc[l] - k + 0.5) / (k + 0.5)) for t, k in df[l].items()}
           for l in ("vi", "zh")}
    print(f"Lượt 1: {n_all:,} doc (vi {ndoc['vi']:,} / zh {ndoc['zh']:,}) | "
          f"term trong query: vi {len(df['vi']):,}, zh {len(df['zh']):,}")

    # ---- Lượt 2: cho điểm doc-at-a-time, giữ top-k mỗi query bằng heap nhỏ nhất
    heaps = {qid: [] for qid in queries}
    rd2 = conn.cursor()
    rd2.arraysize = 500
    rd2.execute("SELECT doc_id, lang, title, descr, tags, body FROM doc WHERE length(body)>=200")
    seen_doc = 0
    for doc_id, lang, *rest in rd2:
        seen_doc += 1
        lang = lang if lang in ("vi", "zh") else "vi"
        tq, di = term_qs[lang], idf[lang]
        if not tq:
            continue
        # tf* gộp các trường TRƯỚC khi bão hoà (đó là điểm khác của BM25F)
        tfs = collections.defaultdict(float)
        for fname, text in zip(FIELDS, doc_fields(rest)):
            ts = tok(text, lang)
            if not ts:
                continue
            norm = 1 - b + b * len(ts) / max(avg[(lang, fname)], 1e-9)
            wf = w[fname] / norm
            cnt = collections.Counter(ts)
            for t, c in cnt.items():
                if t in di:
                    tfs[t] += wf * c
        if not tfs:
            continue
        scores = collections.defaultdict(float)
        for t, tf in tfs.items():
            part = di[t] * tf / (k1 + tf)
            for qid in tq[t]:
                scores[qid] += part
        for qid, sc in scores.items():
            h = heaps[qid]
            if len(h) < topk:
                heapq.heappush(h, (sc, doc_id))
            elif sc > h[0][0]:
                heapq.heapreplace(h, (sc, doc_id))
        if seen_doc % 20000 == 0:
            print(f"  lượt 2: {seen_doc:,} doc")
    return {qid: sorted(h, reverse=True) for qid, h in heaps.items()}


def demo():
    """Self-check: BM25F gộp trước khi bão hoà, trọng số có tác dụng, tách từ zh đúng."""
    global KEEP_DIACRITICS
    # Giữ dấu: "đau" và "đầu" PHẢI là hai token khác nhau; bỏ dấu thì trùng (đúng cho slug URL)
    KEEP_DIACRITICS = False
    assert tok_vi("đau đầu") == ["dau", "dau"], tok_vi("đau đầu")
    KEEP_DIACRITICS = True
    assert tok_vi("Đau đầu, dạ dày 12") == ["đau", "đầu", "dạ", "dày"], tok_vi("Đau đầu, dạ dày 12")
    assert tok_vi("") == [] and tok_vi(None) == []
    KEEP_DIACRITICS = False
    # Tách từ tiếng Trung: bigram, không nối qua dấu câu
    assert tok_zh("糖尿病") == ["糖尿", "尿病"], tok_zh("糖尿病")
    assert tok_zh("甲,乙") == ["甲", "乙"], tok_zh("甲,乙")
    assert "metformin" in tok_zh("服用 metformin 二甲双胍")
    assert tok_zh("") == [] and tok_zh(None) == []
    # Token zh của query tiếng Việt chỉ còn latin/số -> không khớp bừa vào doc tiếng Trung
    assert not any(HAN.search(t) for t in tok_zh("viem da day metformin 500mg"))

    # tags JSON được nối thành chuỗi
    assert doc_fields(("T", "D", '["a","b"]', "B")) == ("T", "D", "a b", "B")
    assert doc_fields((None, None, None, None)) == ("", "", "", "")
    assert doc_fields(("T", "D", "khong-phai-json", "B"))[2] == "khong-phai-json"

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE doc (doc_id TEXT PRIMARY KEY, lang TEXT, title TEXT, "
                 "descr TEXT, tags TEXT, body TEXT)")
    pad = " ".join(f"tu nen {i}" for i in range(60))     # cho body đủ dài qua ngưỡng 200
    rows = [
        # d1: từ khoá ở TITLE          d2: cùng từ khoá nhưng ở BODY
        ("d1", "vi", "viem da day trot xung huyet", "", None, pad),
        ("d2", "vi", "chu de khac han", "", None, "viem da day trot xung huyet " + pad),
        ("d3", "vi", "hoan toan khong lien quan", "", None, pad),
        ("d4", "zh", "糖尿病空腹血糖高吗", "", None, "糖尿病患者的空腹血糖目标 " + pad),
    ]
    conn.executemany("INSERT INTO doc VALUES (?,?,?,?,?,?)", rows)
    conn.commit()

    qs = {1: {"vi": tok_vi("viêm dạ dày trợt xung huyết"), "zh": []}}
    out = rank(conn, qs, topk=10)
    got = [d for _, d in out[1]]
    assert got[0] == "d1", f"title phải thắng body khi trọng số title cao hơn: {got}"
    assert "d2" in got and "d3" not in got, got

    # Hạ trọng số title xuống dưới body -> thứ tự phải ĐẢO
    out2 = rank(conn, qs, topk=10, weights={"title": 0.2})
    got2 = [d for _, d in out2[1]]
    assert got2[0] == "d2", f"đổi trọng số phải đổi thứ tự: {got2}"

    # Query tiếng Trung khớp doc tiếng Trung, KHÔNG khớp doc tiếng Việt
    qz = {1: {"vi": [], "zh": tok_zh("糖尿病空腹血糖")}}
    oz = rank(conn, qz, topk=10)
    gz = [d for _, d in oz[1]]
    assert gz == ["d4"], f"chỉ doc zh được khớp: {gz}"

    # Query không khớp gì -> rỗng, không crash
    assert rank(conn, {1: {"vi": tok_vi("xyzzy qwerty"), "zh": []}}, topk=10)[1] == []
    # Bộ nhớ: topk nhỏ phải giới hạn đúng số kết quả
    assert len(rank(conn, qs, topk=1)[1]) == 1
    print("demo OK")


def main():
    global KEEP_DIACRITICS
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--queries", default="data/queries.jsonl")
    ap.add_argument("--queries-zh", default=None,
                    help="JSONL {id, zh} từ Hy-MT2. Thiếu thì phía tiếng Trung chỉ khớp "
                         "được token latin/số (tên thuốc, chỉ số xét nghiệm)")
    ap.add_argument("--topk", type=int, default=1000)
    ap.add_argument("--out", default="data/bm25_rank.jsonl")
    ap.add_argument("--w-title", type=float, default=WEIGHTS["title"])
    ap.add_argument("--w-tags", type=float, default=WEIGHTS["tags"])
    ap.add_argument("--w-descr", type=float, default=WEIGHTS["descr"])
    ap.add_argument("--w-body", type=float, default=WEIGHTS["body"])
    ap.add_argument("--keep-diacritics", action="store_true",
                    help="giữ dấu tiếng Việt cho nội dung trang và câu hỏi (mặc định bỏ dấu như slug)")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    demo()
    if a.keep_diacritics:
        KEEP_DIACRITICS = True
        print("Giữ dấu tiếng Việt: BẬT (nội dung trang và câu hỏi)")

    qs = load_queries(a.queries, a.queries_zh)
    print(f"Nạp {len(qs)} câu hỏi")
    conn = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    w = {"title": a.w_title, "tags": a.w_tags, "descr": a.w_descr, "body": a.w_body}
    print(f"Trọng số: {w}")
    ranked = rank(conn, qs, a.topk, w)

    with open(a.out, "w", encoding="utf-8") as f:
        for qid in sorted(qs):
            hits = [{"doc_id": d, "score": round(s, 4)} for s, d in ranked.get(qid, [])]
            f.write(json.dumps({"id": qid, "candidates": hits}, ensure_ascii=False) + "\n")
    nz = sum(1 for qid in qs if ranked.get(qid))
    tot = sum(len(ranked.get(qid, [])) for qid in qs)
    print(f"Đã ghi {a.out} | câu có ứng viên: {nz}/{len(qs)} | "
          f"trung bình {tot/max(len(qs),1):.0f} ứng viên/câu")


if __name__ == "__main__":
    sys.exit(main())
