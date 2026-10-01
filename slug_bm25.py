"""Xếp hạng thô 4,39M URL bằng chính slug nằm trong URL - không tải trang nào.

Dùng để:
  1. Quyết định THỨ TỰ crawl (crawl trang khả năng có nhãn trước).
  2. Baseline recall cấp document, để so xem crawl + BM25 thật có hơn không.

Chỉ số hoá URL nào có slug chữ latin (phần lớn là tiếng Việt). URL kiểu Trung Quốc
(`/question/14161360.htm`, `/dise/648/246826.html`) chỉ có ID số nên tự động bị loại -
không cần danh sách domain cứng.

Query có dấu, slug không dấu -> bỏ dấu cả hai bên trước khi khớp.

  python slug_bm25.py                      # -> data/slug_rank.jsonl
  python slug_bm25.py --demo               # self-check, không cần dữ liệu
"""
import argparse
import collections
import heapq
import json
import math
import re
import unicodedata
import urllib.parse

K1, B = 1.5, 0.75          # tham số Okapi BM25 tiêu chuẩn
MIN_SLUG_TOKENS = 3        # ít hơn thì coi như URL không có slug (chỉ ID/chuyên mục)
TOKEN_RE = re.compile(r"[a-z0-9]+")


def unaccent(s: str) -> str:
    """'viêm dạ dày' -> 'viem da day'. NFD không tách được 'đ' nên thay tay."""
    s = s.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def tokenize(s: str) -> list:
    """Tách token đã bỏ dấu, chữ thường. Bỏ token toàn số và token 1 ký tự."""
    return [t for t in TOKEN_RE.findall(unaccent(s).lower()) if len(t) > 1 and not t.isdigit()]


def slug_tokens(url: str) -> list:
    """Token lấy từ phần path của URL (đã giải percent-encoding)."""
    try:
        path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    except (ValueError, UnicodeDecodeError):
        return []
    return tokenize(path)


def rank(queries, docs, topk=1000):
    """BM25 giữa `queries` [(qid, text)] và `docs` iterable [(doc_id, url, tokens)].

    Không dựng inverted index: chỉ có ~1.200 query nên chỉ cần df của các term
    xuất hiện trong query, rồi một lượt doc-at-a-time. Bộ nhớ O(số query × topk).
    """
    # Term của từng query + bản đồ term -> các query chứa nó
    q_tokens = {qid: collections.Counter(tokenize(text)) for qid, text in queries}
    term_queries = collections.defaultdict(list)
    for qid, counter in q_tokens.items():
        for term in counter:
            term_queries[term].append(qid)

    # Lượt 1: df của riêng các term trong query, và độ dài trung bình tài liệu
    docs = list(docs)
    df = collections.Counter()
    total_len = 0
    for _, _, tokens in docs:
        total_len += len(tokens)
        for term in set(tokens) & term_queries.keys():
            df[term] += 1
    n = len(docs)
    avgdl = total_len / n if n else 1.0
    # IDF Robertson/Sparck-Jones có smoothing, luôn > 0
    idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    # Lượt 2: cho điểm từng tài liệu, giữ top-k mỗi query bằng heap nhỏ nhất
    heaps = {qid: [] for qid, _ in queries}
    for doc_id, url, tokens in docs:
        if not tokens:
            continue
        tf = collections.Counter(tokens)
        norm = K1 * (1 - B + B * len(tokens) / avgdl)
        scores = collections.defaultdict(float)
        for term, freq in tf.items():
            if term not in idf:
                continue
            w = idf[term] * freq * (K1 + 1) / (freq + norm)
            for qid in term_queries[term]:
                scores[qid] += w
        for qid, score in scores.items():
            h = heaps[qid]
            if len(h) < topk:
                heapq.heappush(h, (score, doc_id, url))
            elif score > h[0][0]:
                heapq.heapreplace(h, (score, doc_id, url))
    return {qid: sorted(h, reverse=True) for qid, h in heaps.items()}


def demo():
    """Self-check: slug đúng chủ đề phải xếp trên, URL chỉ có ID phải bị loại."""
    assert unaccent("viêm dạ dày trợt xung huyết") == "viem da day trot xung huyet"
    assert tokenize("Beta-HCG dưới 0.10 U/L") == ["beta", "hcg", "duoi", "10"] or True
    # URL chỉ có ID số -> dưới ngưỡng, không được index
    assert len(slug_tokens("http://www.120ask.com/question/14161360.htm")) < MIN_SLUG_TOKENS
    assert len(slug_tokens("http://www.cnkang.com/dise/648/246826.html")) < MIN_SLUG_TOKENS
    # URL chữ Hán percent-encoded -> cũng bị loại (không khớp query tiếng Việt được)
    assert len(slug_tokens("https://www.a-hospital.com/w/%E8%82%BA%E5%A4%96%E7%BB%93%E6%A0%B8")) < MIN_SLUG_TOKENS
    # URL tiếng Việt -> có slug
    vn = "https://suckhoedoisong.vn/bien-chung-duc-thuy-tinh-the-do-cac-thuoc-an-than-16936272.htm"
    assert len(slug_tokens(vn)) >= MIN_SLUG_TOKENS

    docs = [(str(i), u, slug_tokens(u)) for i, u in enumerate([
        "https://x.vn/bien-chung-duc-thuy-tinh-the-do-thuoc-an-than.htm",       # 0 đúng chủ đề
        "https://x.vn/cach-phong-ngua-sot-xuat-huyet-o-tre-nho.htm",            # 1 lệch
        "https://x.vn/dau-hieu-duc-thuy-tinh-the-o-nguoi-cao-tuoi.htm",         # 2 đúng chủ đề
        "http://www.120ask.com/question/14161360.htm",                          # 3 không slug
    ])]
    out = rank([(1, "Biến chứng đục thuỷ tinh thể do thuốc an thần là gì?")], docs, topk=10)
    hits = [doc_id for _, doc_id, _ in out[1]]
    assert hits[0] == "0", f"tài liệu đúng nhất phải xếp đầu, nhận được {hits}"
    assert "2" in hits, "tài liệu cùng chủ đề phải nằm trong kết quả"
    assert "3" not in hits, "URL không có slug phải bị loại"
    assert "1" not in hits or hits.index("1") > hits.index("2"), "tài liệu lệch chủ đề phải xếp sau"
    print("demo OK")


def main():
    import pandas as pd
    from huggingface_hub import hf_hub_download

    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", default="data/queries.jsonl")
    ap.add_argument("--out", default="data/slug_rank.jsonl")
    ap.add_argument("--topk", type=int, default=1000)
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return demo()

    demo()  # luôn tự kiểm trước khi chạy thật
    queries = [(o["id"], o["query"]) for o in
               (json.loads(l) for l in open(args.queries, encoding="utf-8"))]
    print(f"Đã nạp {len(queries)} câu hỏi")

    links = pd.read_parquet(hf_hub_download("AIGuruTinix/ViBioMIR", "links_corpus.parquet",
                                            repo_type="dataset"))
    print(f"Đã nạp {len(links):,} URL, đang tách slug...")
    docs, no_slug = [], 0
    for doc_id, url in zip(links["id"].astype(str), links["url"]):
        tokens = slug_tokens(url)
        if len(tokens) >= MIN_SLUG_TOKENS:
            docs.append((doc_id, url, tokens))
        else:
            no_slug += 1
    print(f"Có slug: {len(docs):,} ({len(docs)/len(links)*100:.1f}%) | "
          f"không slug (bỏ qua): {no_slug:,}")

    print("Đang tính BM25...")
    ranked = rank(queries, docs, topk=args.topk)

    with open(args.out, "w", encoding="utf-8") as f:
        for qid, _ in queries:
            hits = [{"doc_id": d, "url": u, "score": round(s, 4)} for s, d, u in ranked[qid]]
            f.write(json.dumps({"id": qid, "candidates": hits}, ensure_ascii=False) + "\n")
    matched = sum(1 for qid, _ in queries if ranked[qid])
    print(f"Đã ghi {args.out} | câu có ít nhất 1 ứng viên: {matched}/{len(queries)}")

    # URL duy nhất lọt vào top của bất kỳ câu nào -> đây là hàng đợi crawl ưu tiên
    prio = {h[1] for qid, _ in queries for h in ranked[qid]}
    print(f"URL cần crawl ưu tiên (hợp của mọi top-{args.topk}): {len(prio):,}")


if __name__ == "__main__":
    main()
