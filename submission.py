"""Xuất bài nộp từ danh sách ứng viên: JSON -> ZIP, kèm kiểm tra bắt buộc.

Chỉ dùng stdlib (json, zipfile) - không thêm dependency.

Cách chấm rút gọn được:  F2 = 5g / (4G + k)
  g = số doc trả về mà đúng, G = số doc vàng, k = số doc trả về.
Thêm một doc có lợi khi xác suất liên quan p > F2/5. Không biết G lẫn p, nên `--topk`
là tham số để QUÉT bằng các lượt nộp (10 lượt/ngày), không phải hằng số đoán.

MƠ HỒ TRONG ĐẶC TẢ, chưa giải quyết: phần chữ của BTC nói `relevant_docs` và `doc_id` dùng
"trường `id` KIỂU SỐ NGUYÊN trong links_corpus.parquet", nhưng schema ghi `["<id_tài_liệu>"]`
và ví dụ ghi `["doc_id1", "doc_id2"]` - đều là chuỗi. Cách đọc hợp lý nhất: phần chữ đang nói
LẤY TỪ TRƯỜNG NÀO (cột `id`, vốn là số nguyên), không nói kiểu trong JSON.
=> Mặc định xuất CHUỖI (khớp schema và ví dụ). Dùng `--int-ids` để thử kiểu số nguyên.
Bài nộp sai định dạng KHÔNG bị tính vào quota, nên thử cả hai là miễn phí.

  # Bài nộp chỉ cấp document (chunk rỗng) - không cần crawl gì
  python submission.py --cands data/slug_rank.jsonl --topk 20 --out runs/sub_top20

  # Khi đã có store crawl về: kèm cả chunk
  python submission.py --cands data/slug_rank.jsonl --topk 20 --store data/corpus_new.sqlite \\
      --chunks-per-doc 1 --out runs/sub_top20_chunk

  python submission.py --demo        # self-check, không cần dữ liệu
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import zipfile

N_QUERIES = 1200          # đề cố định 1.200 câu; thiếu một câu là không được chấm


def load_candidates(path):
    """{qid: [(doc_id, score)]} đã xếp theo điểm giảm dần."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            cands = [(str(c["doc_id"]), float(c.get("score", 0.0))) for c in o["candidates"]]
            out[int(o["id"])] = sorted(cands, key=lambda t: -t[1])
    return out


def pick(cands, topk, min_score):
    """Cắt danh sách: theo topk, theo ngưỡng điểm, hoặc cả hai."""
    sel = cands if topk is None else cands[:topk]
    if min_score is not None:
        sel = [c for c in sel if c[1] >= min_score]
    return [doc_id for doc_id, _ in sel]


def fetch_chunks(store, doc_ids, per_doc, qtext=None, chunk_scores=None):
    """Lấy chunk NGUYÊN VĂN từ store: chunk_text = body[start:end].

    Không bao giờ lấy từ title/description - đo được title nằm nguyên văn trong body
    chỉ 43%, nên chúng chỉ dùng để xếp hạng.

    `qtext`: nếu có, doc nhiều hơn `per_doc` chunk thì chọn chunk KHỚP câu hỏi nhất (tổng IDF
    các từ câu hỏi có mặt trong chunk, IDF tính trên các chunk của chính danh sách này) thay vì
    lấy những chunk đầu. Chunk vẫn là lát nguyên văn của body.
    """
    if not doc_ids:
        return []
    conn = sqlite3.connect(f"file:{store}?mode=ro", uri=True)
    qs = ",".join("?" * len(doc_ids))
    rows = conn.execute(
        f"SELECT c.doc_id, c.start, c.end, d.body FROM chunk c JOIN doc d USING(doc_id) "
        f"WHERE c.doc_id IN ({qs}) ORDER BY c.doc_id, c.chunk_id", doc_ids).fetchall()
    conn.close()
    by_doc = {}
    for doc_id, start, end, body in rows:
        text = body[start:end]
        if text.strip():
            by_doc.setdefault(doc_id, []).append(text)
    pick_idx = {d: list(range(min(per_doc, len(t)))) for d, t in by_doc.items()}
    for d, sc in (chunk_scores or {}).items():          # điểm Qwen từng chunk: lấy per_doc chunk cao nhất, giữ thứ tự gốc
        n = len(by_doc.get(d, []))
        if n > per_doc:
            pick_idx[d] = sorted(sorted(range(n), key=lambda i: (-sc.get(i, -1.0), i))[:per_doc])
    if qtext:
        import math
        import bm25
        bm25.KEEP_DIACRITICS = True
        qt = set(bm25.tok_vi(qtext))
        toks = {d: [set(bm25.tok_vi(x)) & qt for x in t] for d, t in by_doc.items()}
        n = sum(len(v) for v in toks.values()) or 1
        df = {}
        for v in toks.values():
            for ts in v:
                for t in ts:
                    df[t] = df.get(t, 0) + 1
        idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        for d, v in toks.items():
            if len(v) > per_doc:
                sc = [sum(idf[t] for t in ts) for ts in v]
                best = sorted(range(len(v)), key=lambda i: (-sc[i], i))[:per_doc]
                pick_idx[d] = sorted(best)
    out = []
    for doc_id in doc_ids:                       # giữ thứ tự hạng của doc
        for i in pick_idx.get(doc_id, []):
            text = by_doc[doc_id][i]
            out.append({"doc_id": str(doc_id), "chunk_text": text})
    return out


def validate(records, n_queries=N_QUERIES, id_type=str):
    """Kiểm những lỗi làm bài nộp KHÔNG ĐƯỢC CHẤM. Sai thì dừng, không cảnh báo suông.

    `id_type`: str (mặc định) hoặc int - xem ghi chú về mơ hồ kiểu doc_id ở đầu file.
    """
    errs = []
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        errs.append("có id trùng nhau")
    missing = set(range(1, n_queries + 1)) - set(ids)
    if missing:
        errs.append(f"thiếu {len(missing)} id, ví dụ {sorted(missing)[:5]}")
    extra = set(ids) - set(range(1, n_queries + 1))
    if extra:
        errs.append(f"có {len(extra)} id lạ, ví dụ {sorted(extra)[:5]}")
    for r in records:
        if set(r) != {"id", "relevant_docs", "relevant_chunks"}:
            errs.append(f"id {r['id']}: sai tên trường {sorted(r)}")
            break
        if not all(type(d) is id_type for d in r["relevant_docs"]):
            errs.append(f"id {r['id']}: doc_id phải cùng kiểu {id_type.__name__}")
            break
        for c in r["relevant_chunks"]:
            # `chunk_order` là trường TUỲ CHỌN theo đặc tả; nếu có thì phải là int >= 0
            if not {"doc_id", "chunk_text"} <= set(c) <= {"doc_id", "chunk_text", "chunk_order"}:
                errs.append(f"id {r['id']}: chunk sai tên trường {sorted(c)}")
                break
            if type(c["doc_id"]) is not id_type:
                errs.append(f"id {r['id']}: chunk doc_id phải cùng kiểu với relevant_docs")
                break
            if "chunk_order" in c and (type(c["chunk_order"]) is not int
                                       or c["chunk_order"] < 0):
                errs.append(f"id {r['id']}: chunk_order phải là số nguyên không âm")
                break
    return errs


def fingerprint(records):
    """Vân tay (doc, chunk): doc theo TẬP doc mỗi câu (thứ tự không ảnh hưởng điểm doc),
    chunk theo văn bản có thứ tự. Hai bài cùng vân tay thì cùng điểm ở tầng đó."""
    h = lambda o: hashlib.sha1(json.dumps(o, ensure_ascii=False).encode()).hexdigest()[:12]
    return (h([[r["id"], sorted(r["relevant_docs"])] for r in records]),
            h([[r["id"], [c["chunk_text"] for c in r["relevant_chunks"]]] for r in records]))


class _BigLZMA(zipfile.LZMACompressor):
    """LZMA từ điển LỚN: 34% văn bản chunk lặp giữa các câu (cùng doc cho nhiều câu), bzip2 (khối 900 KB)
    và LZMA mặc định (8 MB) không thấy được; từ điển 768 MB thì thấy. Đo trên blendQB13af_e120:
    bzip2 95,5 MB / LZMA 8 MB 91,4 MB / LZMA 640 MB 54,8 MB. Bên giải nén cần RAM ~ cỡ từ điển."""
    DICT = 768 << 20

    def _init(self):
        import lzma
        import struct
        f = {"id": lzma.FILTER_LZMA1, "preset": 6, "dict_size": self.DICT}
        props = lzma._encode_filter_properties(f)
        self._comp = lzma.LZMACompressor(lzma.FORMAT_RAW, filters=[f])
        return struct.pack("<BBH", 9, 4, len(props)) + props


def write_zip(records, out_prefix, method="deflate"):
    """ZIP chứa ĐÚNG MỘT file json, không nằm trong thư mục con."""
    os.makedirs(os.path.dirname(out_prefix) or ".", exist_ok=True)
    js, zp = out_prefix + ".json", out_prefix + ".zip"
    with open(js, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, separators=(",", ":"))
    # bzip2 đã được leaderboard chấp nhận (07/10, blendQB3x_3k_300_bzip2) và nhỏ hơn deflate ~35%
    kw = {"bzip2": (zipfile.ZIP_BZIP2, 9), "deflate": (zipfile.ZIP_DEFLATED, 9),
          "lzma": (zipfile.ZIP_LZMA, None)}[method]
    orig = zipfile.LZMACompressor
    zipfile.LZMACompressor = _BigLZMA          # zipfile tạo compressor qua tên này
    try:
        with zipfile.ZipFile(zp, "w", kw[0], compresslevel=kw[1]) as z:
            z.write(js, arcname=os.path.basename(js))
    finally:
        zipfile.LZMACompressor = orig
    with zipfile.ZipFile(zp) as z:
        names = z.namelist()
    assert names == [os.path.basename(js)], f"ZIP phải chứa đúng 1 file, đang có {names}"
    return js, zp


def load_chunk_scores(path):
    """{qid: {doc_id(str): {idx: điểm}}} từ chunk_scores.jsonl"""
    out = {}
    for l in open(path, encoding="utf-8"):
        r = json.loads(l)
        out.setdefault(r["id"], {}).setdefault(str(r["doc_id"]), {})[r["idx"]] = r["score"]
    return out


def load_queries(path):
    return {int(json.loads(l)["id"]): json.loads(l)["query"] for l in open(path, encoding="utf-8")}


def build(cands, topk, min_score, store, per_doc, n_queries=N_QUERIES, id_type=str,
          chunk_from_top=None, extra_one=None, queries=None, chunk_scores=None):
    """`chunk_from_top`: chỉ lấy chunk từ M doc ĐẦU, dù `relevant_docs` vẫn trả đủ topk.

    Hai tầng được chấm ĐỘC LẬP nên tối ưu riêng được. Đo trên leaderboard: DOCS_PRECISION
    là 0,1154 ở k=20 nhưng chỉ 0,0419 ở k=200 - chunk từ top-20 có khả năng trúng cao gấp
    2,75 lần. Nộp chunk cho cả 200 doc nghĩa là ~96% chunk đến từ doc không phải nhãn vàng,
    chắc chắn vô ích và chỉ làm loãng precision. Cũng giảm file từ 253 MB xuống ~50 MB.
    """
    records = []
    for qid in range(1, n_queries + 1):
        docs = pick(cands.get(qid, []), topk, min_score)
        src = docs[:chunk_from_top] if chunk_from_top else docs
        qt = (queries or {}).get(qid)
        chunks = fetch_chunks(store, src, per_doc, qt, (chunk_scores or {}).get(qid)) if store else []
        if store and extra_one and chunk_from_top:
            # tầng 2: doc hạng chunk_from_top..extra_one chỉ lấy 1 chunk (rộng hơn, mỏng hơn)
            chunks += fetch_chunks(store, docs[chunk_from_top:extra_one], 1, qt)
        if id_type is int:
            docs = [int(d) for d in docs]
            chunks = [dict(c, doc_id=int(c["doc_id"])) for c in chunks]
        records.append({"id": qid, "relevant_docs": docs, "relevant_chunks": chunks})
    return records


def demo():
    """Self-check: cắt danh sách, kiểm tra, ZIP, và công thức F2 = 5g/(4G+k)."""
    import tempfile
    cands = {1: [("10", 9.0), ("11", 5.0), ("12", 1.0)], 2: [("20", 3.0)]}
    assert pick(cands[1], 2, None) == ["10", "11"]
    assert pick(cands[1], None, 4.0) == ["10", "11"], "ngưỡng điểm phải lọc đúng"
    assert pick(cands[1], 2, 6.0) == ["10"], "topk và ngưỡng phải áp dụng cùng nhau"
    assert pick([], 5, None) == []

    # chunk_from_top: relevant_docs vẫn đủ topk, nhưng chunk chỉ từ M doc đầu
    cc = {1: [("10", 9.0), ("11", 5.0), ("12", 1.0)]}
    r2 = build(cc, 3, None, None, 1, n_queries=1, chunk_from_top=1)
    assert r2[0]["relevant_docs"] == ["10", "11", "12"], r2
    assert r2[0]["relevant_chunks"] == []      # không có store nên rỗng, nhưng docs vẫn đủ

    recs = build(cands, 2, None, None, 1, n_queries=2)
    assert len(recs) == 2 and recs[1] == {"id": 2, "relevant_docs": ["20"],
                                         "relevant_chunks": []}
    assert validate(recs, n_queries=2) == []
    # Câu không có ứng viên vẫn phải có trường, với danh sách rỗng
    assert build({}, 5, None, None, 1, n_queries=2)[0] == {
        "id": 1, "relevant_docs": [], "relevant_chunks": []}

    # Phải BẮT được các lỗi làm bài nộp bị loại
    assert validate(recs, n_queries=3), "phải phát hiện thiếu id"
    bad = [{"id": 1, "relevant_docs": [10], "relevant_chunks": []}]
    assert validate(bad, n_queries=1), "phải bắt doc_id sai kiểu"
    assert validate(bad, n_queries=1, id_type=int) == [], "--int-ids thì số nguyên là hợp lệ"

    # --int-ids chuyển cả relevant_docs lẫn doc_id trong chunk
    ri = build(cands, 2, None, None, 1, n_queries=1, id_type=int)
    assert ri[0]["relevant_docs"] == [10, 11], ri
    assert validate(ri, n_queries=1, id_type=int) == []

    # `chunk_order` là tuỳ chọn: có thì phải int >= 0, không có cũng hợp lệ
    ok = [{"id": 1, "relevant_docs": ["1"],
           "relevant_chunks": [{"doc_id": "1", "chunk_text": "x", "chunk_order": 0}]}]
    assert validate(ok, n_queries=1) == [], validate(ok, n_queries=1)
    for bad_order in (-1, "0", 1.5):
        b = [{"id": 1, "relevant_docs": ["1"],
              "relevant_chunks": [{"doc_id": "1", "chunk_text": "x",
                                   "chunk_order": bad_order}]}]
        assert validate(b, n_queries=1), f"phải bắt chunk_order={bad_order!r}"
    b = [{"id": 1, "relevant_docs": ["1"],
          "relevant_chunks": [{"doc_id": "1", "chunk_text": "x", "lạ": 1}]}]
    assert validate(b, n_queries=1), "phải bắt trường lạ trong chunk"

    with tempfile.TemporaryDirectory() as d:
        js, zp = write_zip(recs, os.path.join(d, "sub"))
        with zipfile.ZipFile(zp) as z:
            back = json.loads(z.read(os.path.basename(js)))
        assert back == recs, "nội dung trong ZIP phải khớp"

    # Công thức F2 rút gọn phải khớp định nghĩa gốc 5PR/(4P+R)
    for g, G, k in ((3, 5, 10), (1, 1, 1), (7, 20, 50), (2, 3, 4)):
        P, R = g / k, g / G
        assert abs(5 * P * R / (4 * P + R) - 5 * g / (4 * G + k)) < 1e-12
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", default="data/slug_rank.jsonl",
                    help="JSONL {id, candidates:[{doc_id, score}]}")
    ap.add_argument("--topk", type=int, default=None, help="lấy N doc đầu mỗi câu")
    ap.add_argument("--min-score", type=float, default=None, help="ngưỡng điểm")
    ap.add_argument("--store", default=None, help="SQLite corpus; thiếu thì chunk rỗng")
    ap.add_argument("--chunks-per-doc", type=int, default=1)
    ap.add_argument("--chunk-from-top", type=int, default=None, metavar="M",
                    help="chỉ lấy chunk từ M doc đầu (relevant_docs vẫn trả đủ --topk). "
                         "Precision chunk cao hơn vì doc hạng cao dễ là nhãn vàng hơn")
    ap.add_argument("--extra-one", type=int, default=None, metavar="N",
                    help="doc hạng (chunk-from-top, N] lấy thêm 1 chunk mỗi doc")
    ap.add_argument("--zip-method", choices=["deflate", "bzip2", "lzma"], default="deflate",
                    help="bzip2 nhỏ hơn ~35% (đã được leaderboard chấp nhận 07/10) -> nhét được ~1,5x chunk dưới trần 100 MB")
    ap.add_argument("--chunk-scores", default=None, metavar="chunk_scores.jsonl",
                    help="điểm Qwen từng chunk (chunk_rerank.py): doc có >per_doc chunk thì lấy chunk điểm cao nhất")
    ap.add_argument("--chunk-query", default=None, metavar="QUERIES.jsonl",
                    help="chọn chunk KHỚP câu hỏi nhất trong mỗi doc thay vì những chunk đầu")
    ap.add_argument("--int-ids", action="store_true",
                    help="xuất doc_id kiểu số nguyên thay vì chuỗi (xem ghi chú đầu file)")
    ap.add_argument("--out", default="runs/submission")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return demo()
    demo()
    if args.topk is None and args.min_score is None:
        sys.exit("Phải cho --topk hoặc --min-score (xem công thức F2 ở đầu file)")

    id_type = int if args.int_ids else str
    cands = load_candidates(args.cands)
    print(f"Nạp ứng viên cho {len(cands)} câu từ {args.cands} "
          f"| doc_id kiểu {id_type.__name__}")
    records = build(cands, args.topk, args.min_score, args.store, args.chunks_per_doc,
                    id_type=id_type, chunk_from_top=args.chunk_from_top, extra_one=args.extra_one,
                    queries=load_queries(args.chunk_query) if args.chunk_query else None,
                    chunk_scores=load_chunk_scores(args.chunk_scores) if args.chunk_scores else None)

    errs = validate(records, id_type=id_type)
    if errs:
        sys.exit("BÀI NỘP KHÔNG HỢP LỆ:\n  " + "\n  ".join(errs))

    nd = sum(len(r["relevant_docs"]) for r in records)
    nc = sum(len(r["relevant_chunks"]) for r in records)
    empty = sum(1 for r in records if not r["relevant_docs"])
    js, zp = write_zip(records, args.out, args.zip_method)
    print(f"Hợp lệ: đủ {len(records)} câu | {nd:,} doc ({nd/len(records):.1f}/câu) | "
          f"{nc:,} chunk | {empty} câu rỗng")
    fd, fc = fingerprint(records)
    print(f"-> {js}\n-> {zp}  ({os.path.getsize(zp)/1024:.0f} KB)  ← nộp file này")
    print(f"vân tay: doc={fd} chunk={fc}  (ghi vào PROGRESS.md §2b cùng với điểm)")
    if nc == 0:
        print("LƯU Ý: chunk rỗng -> mất toàn bộ điểm cấp chunk. Cần --store sau khi crawl.")


if __name__ == "__main__":
    sys.exit(main())
