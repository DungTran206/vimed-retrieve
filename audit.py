"""Kiểm tra toàn chuỗi trên DỮ LIỆU THẬT, từng tầng một, báo PASS/FAIL.

Khác với `--demo` của từng script (kiểm bất biến trên dữ liệu giả, chạy trong 2 ms),
file này soi chính `data/corpus.sqlite` và bài nộp sinh ra từ nó. Mục đích: biết chắc
từng tầng đúng trước khi xây tầng trên.

  CRAWL      -> doc lưu đúng? metadata có? trích lỗi có giữ HTML? domain chặn có bị gọi?
  CHUNK      -> offset hợp lệ? nguyên văn? phủ hết? đúng budget token?
  SUBMISSION -> đủ 1.200 id? kiểu doc_id? chunk khớp store? ZIP đúng?
  SCORE      -> tự chấm bài nộp bằng nhãn vàng dựng từ chính nó, phải ra F2 = 1,0

  python audit.py                 # kiểm tất cả
  python audit.py --stage chunk   # một tầng
"""
import argparse
import json
import re
import sqlite3
import sys
import tempfile
import os

DB = "data/corpus.sqlite"
_fails = []


def check(cond, name, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))
    if not cond:
        _fails.append(name)
    return cond


def info(name, value):
    print(f"        {name}: {value}")


# ------------------------------------------------------------------ CRAWL

def audit_crawl(conn):
    print("\n=== TẦNG 1: CRAWL ===")
    n_doc, = conn.execute("SELECT count(*) FROM doc").fetchone()
    n_ok, = conn.execute("SELECT count(*) FROM doc WHERE length(body)>=200").fetchone()
    if not check(n_doc > 0, "store có dữ liệu", f"{n_doc:,} doc"):
        return
    info("doc dùng được", f"{n_ok:,}/{n_doc:,} ({n_ok/n_doc*100:.1f}%)")

    # doc_id phải khớp queue, không được tự sinh
    orphan, = conn.execute(
        "SELECT count(*) FROM doc WHERE doc_id NOT IN (SELECT doc_id FROM queue)").fetchone()
    check(orphan == 0, "mọi doc_id đều có trong queue", f"{orphan} mồ côi")

    # Trạng thái queue phải nhất quán với nội dung doc
    bad, = conn.execute(
        "SELECT count(*) FROM queue q JOIN doc d USING(doc_id) "
        "WHERE (q.state=1) != (length(d.body)>=200)").fetchone()
    check(bad == 0, "state=DONE khớp với body đủ dài", f"{bad} lệch")

    # Domain đã biết là chặn thì KHÔNG được tốn request
    from crawler import BLOCKED
    qs = ",".join("?" * len(BLOCKED))
    wasted, = conn.execute(
        f"SELECT count(*) FROM doc WHERE domain IN ({qs})", list(BLOCKED)).fetchone()
    check(wasted == 0, "không gọi request tới domain đã biết bị chặn", f"{wasted} lượt")

    # HTTP 200 nhưng trích rỗng -> PHẢI giữ raw_html để viết parser
    lost, = conn.execute("SELECT count(*) FROM doc WHERE status=200 AND length(body)<200 "
                         "AND raw_html IS NULL").fetchone()
    check(lost == 0, "trích lỗi đều giữ raw_html (khỏi crawl lại)", f"{lost} mất")

    # Metadata: title là tín hiệu xếp hạng mạnh nhất, phải gần như luôn có
    row = conn.execute("SELECT sum(title!=''), sum(descr!=''), sum(tags IS NOT NULL), "
                       "sum(pub_date IS NOT NULL) FROM doc WHERE length(body)>=200").fetchone()
    t, d, g, p = (x or 0 for x in row)
    info("metadata", f"title {t/n_ok*100:.0f}% | descr {d/n_ok*100:.0f}% | "
                     f"tags {g/n_ok*100:.0f}% | date {p/n_ok*100:.0f}%")
    check(t / n_ok > 0.9, "title có ≥90% doc", f"{t/n_ok*100:.1f}%")

    # body phải đã chuẩn hoá: không khoảng trắng kép ngang, không '\r'
    raw = conn.execute("SELECT count(*) FROM doc WHERE body LIKE '%  %' OR body LIKE '%'||char(13)||'%' "
                       "OR body LIKE char(10)||' %'").fetchone()[0]
    check(raw == 0, "body đã chuẩn hoá khoảng trắng", f"{raw} doc còn sót")

    # lang phải luôn được gán, và khớp với tỉ lệ ký tự Hán
    nolang, = conn.execute("SELECT count(*) FROM doc WHERE length(body)>=200 "
                           "AND (lang IS NULL OR lang='')").fetchone()
    check(nolang == 0, "mọi doc dùng được đều có lang", f"{nolang} thiếu")
    from crawler import detect_lang
    mism = 0
    for lang, body, dom in conn.execute("SELECT lang, body, domain FROM doc "
                                        "WHERE length(body)>=200 ORDER BY random() LIMIT 200"):
        mism += detect_lang(body, dom) != lang
    check(mism == 0, "lang khớp khi tính lại (mẫu 200)", f"{mism} lệch")

    # simhash: phải có với doc dùng được, và phát hiện được bản trùng
    nosh, = conn.execute("SELECT count(*) FROM doc WHERE length(body)>=200 "
                         "AND simhash=0").fetchone()
    check(nosh == 0, "mọi doc dùng được đều có simhash", f"{nosh} thiếu")
    dup, = conn.execute("SELECT count(*) FROM (SELECT simhash FROM doc "
                        "WHERE length(body)>=200 GROUP BY simhash HAVING count(*)>1)").fetchone()
    info("nhóm simhash trùng", f"{dup} nhóm (gom để embed chung, KHÔNG xoá doc_id)")


# ------------------------------------------------------------------ CHUNK

def audit_chunk(conn):
    print("\n=== TẦNG 2: CHUNK ===")
    n, = conn.execute("SELECT count(*) FROM chunk").fetchone()
    nd, = conn.execute("SELECT count(DISTINCT doc_id) FROM chunk").fetchone()
    if not check(n > 0, "có chunk", f"{n:,} chunk / {nd:,} doc"):
        return
    info("chunk/doc", f"{n/nd:.2f}")

    # Mọi doc dùng được phải được cắt - bỏ sót là mất recall
    miss, = conn.execute("SELECT count(*) FROM doc WHERE length(body)>=200 "
                         "AND doc_id NOT IN (SELECT doc_id FROM chunk)").fetchone()
    check(miss == 0, "mọi doc dùng được đều có chunk", f"{miss} doc bị bỏ sót")

    # Chunk không được trỏ tới doc không tồn tại
    orph, = conn.execute("SELECT count(*) FROM chunk WHERE doc_id NOT IN "
                         "(SELECT doc_id FROM doc)").fetchone()
    check(orph == 0, "không có chunk mồ côi", f"{orph}")

    # BẤT BIẾN CỐT TỬ: offset hợp lệ và cắt ra không rỗng - kiểm TOÀN BỘ, không lấy mẫu
    bad = conn.execute(
        "SELECT count(*) FROM chunk c JOIN doc d USING(doc_id) "
        "WHERE c.start<0 OR c.end<=c.start OR c.end>length(d.body)").fetchone()[0]
    check(bad == 0, "offset mọi chunk nằm trong body (toàn bộ)", f"{bad} sai")
    empty = conn.execute(
        "SELECT count(*) FROM chunk c JOIN doc d USING(doc_id) "
        "WHERE trim(substr(d.body, c.start+1, c.end-c.start))=''").fetchone()[0]
    check(empty == 0, "không chunk nào rỗng (toàn bộ)", f"{empty}")

    # n_chars phải khớp end-start
    wrong, = conn.execute("SELECT count(*) FROM chunk WHERE n_chars != end-start").fetchone()
    check(wrong == 0, "n_chars khớp end-start", f"{wrong}")

    # ord không được trùng trong cùng doc
    dupord, = conn.execute("SELECT count(*) FROM (SELECT doc_id,ord FROM chunk "
                           "GROUP BY doc_id,ord HAVING count(*)>1)").fetchone()
    check(dupord == 0, "ord duy nhất trong mỗi doc", f"{dupord}")

    # Độ phủ: hợp các chunk phải chứa gần hết body
    from chunk import CHARS_PER_TOKEN, TARGET_TOKENS
    low = []
    for doc_id, body in conn.execute("SELECT doc_id, body FROM doc WHERE length(body)>=200 "
                                     "ORDER BY random() LIMIT 300"):
        spans = conn.execute("SELECT start,end FROM chunk WHERE doc_id=?", (doc_id,)).fetchall()
        cov = len({i for s, e in spans for i in range(s, e)})
        if cov < len(re.sub(r"\s", "", body)) * 0.95:
            low.append(doc_id)
    check(not low, "độ phủ ≥95% (mẫu 300 doc)", f"{len(low)} doc thấp: {low[:3]}")

    # Budget token: đề khuyến nghị <= ~1.024
    over = []
    for lang, cpt in CHARS_PER_TOKEN.items():
        lim = int(1024 * cpt)
        k, = conn.execute("SELECT count(*) FROM chunk c JOIN doc d USING(doc_id) "
                          "WHERE d.lang=? AND c.n_chars>?", (lang, lim)).fetchone()
        tot, = conn.execute("SELECT count(*) FROM chunk c JOIN doc d USING(doc_id) "
                            "WHERE d.lang=?", (lang,)).fetchone()
        if tot:
            info(f"chunk {lang} vượt 1024 token", f"{k}/{tot} (ngưỡng {lim:,} ký tự)")
            over.append(k)
    check(sum(over) == 0, "không chunk nào vượt ~1.024 token", f"{sum(over)} chunk")

    # Chồng lấn: phải có, nếu không thì phần thông tin bị cắt đứt giữa hai chunk
    multi = conn.execute(
        "SELECT doc_id FROM chunk GROUP BY doc_id HAVING count(*)>1 "
        "ORDER BY random() LIMIT 50").fetchall()
    if multi:
        nover = 0
        for doc_id, in multi:
            sp = conn.execute("SELECT start,end FROM chunk WHERE doc_id=? ORDER BY ord",
                              (doc_id,)).fetchall()
            nover += any(sp[i + 1][0] < sp[i][1] for i in range(len(sp) - 1))
        check(nover == len(multi), "doc nhiều chunk đều có chồng lấn",
              f"{nover}/{len(multi)}")


# ------------------------------------------------------------------ SUBMISSION

def audit_submission(conn, db_path):
    print("\n=== TẦNG 3: SUBMISSION ===")
    import zipfile
    from submission import build, load_candidates, validate, write_zip

    cands = load_candidates("data/slug_rank.jsonl")
    check(len(cands) == 1200, "nạp đủ 1.200 câu ứng viên", f"{len(cands)}")

    for id_type in (str, int):
        name = id_type.__name__
        recs = build(cands, 20, None, db_path, 2, id_type=id_type)
        errs = validate(recs, id_type=id_type)
        check(not errs, f"[{name}] bài nộp hợp lệ", "; ".join(errs[:2]))
        check(len(recs) == 1200 and {r["id"] for r in recs} == set(range(1, 1201)),
              f"[{name}] đủ id 1..1200")
        check(all(type(d) is id_type for r in recs for d in r["relevant_docs"]),
              f"[{name}] relevant_docs đúng kiểu {name}")
        check(all(type(c["doc_id"]) is id_type for r in recs for c in r["relevant_chunks"]),
              f"[{name}] chunk.doc_id đúng kiểu {name}")
        # Câu không có ứng viên vẫn phải có trường, với danh sách rỗng
        check(all("relevant_docs" in r and "relevant_chunks" in r for r in recs),
              f"[{name}] mọi câu đều có cả hai trường")

        # chunk_text PHẢI nguyên văn trong body của chính doc đó
        nbad = nchk = 0
        for r in recs:
            for c in r["relevant_chunks"]:
                row = conn.execute("SELECT body FROM doc WHERE doc_id=?",
                                   (str(c["doc_id"]),)).fetchone()
                nchk += 1
                if not row or c["chunk_text"] not in row[0]:
                    nbad += 1
        check(nbad == 0, f"[{name}] chunk_text nguyên văn trong store",
              f"{nbad}/{nchk} lệch")
        # chunk phải thuộc doc có trong relevant_docs
        stray = sum(1 for r in recs for c in r["relevant_chunks"]
                    if c["doc_id"] not in r["relevant_docs"])
        check(stray == 0, f"[{name}] chunk chỉ thuộc doc đã khai", f"{stray}")

        with tempfile.TemporaryDirectory() as td:
            js, zp = write_zip(recs, os.path.join(td, f"a_{name}"))
            with zipfile.ZipFile(zp) as z:
                names = z.namelist()
                back = json.loads(z.read(names[0]))
            check(names == [os.path.basename(js)], f"[{name}] ZIP đúng 1 file, không thư mục con",
                  str(names))
            check(back == recs, f"[{name}] nội dung trong ZIP khớp bản gốc")
        info(f"[{name}] thống kê",
             f"{sum(len(r['relevant_docs']) for r in recs):,} doc, "
             f"{sum(len(r['relevant_chunks']) for r in recs):,} chunk, "
             f"{sum(1 for r in recs if r['relevant_chunks'])} câu có chunk")
    return build(cands, 20, None, db_path, 2)


# ------------------------------------------------------------------ SCORE

def audit_score(recs):
    print("\n=== TẦNG 4: SCORE ===")
    from score import score, f2, covers

    # Tự chấm: nhãn vàng dựng từ chính bài nộp -> phải ra P=R=F2=1
    gold = [{"id": r["id"], "relevant_docs": r["relevant_docs"],
             "info": [c["chunk_text"] for c in r["relevant_chunks"]]}
            for r in recs if r["relevant_docs"] and r["relevant_chunks"]][:200]
    if not check(len(gold) > 0, "có câu để tự chấm", f"{len(gold)} câu"):
        return
    m = score(recs, gold)
    check(abs(m["P_doc"] - 1) < 1e-9 and abs(m["R_doc"] - 1) < 1e-9,
          "tự chấm cấp document = 1,0", f"P {m['P_doc']:.4f} R {m['R_doc']:.4f}")
    check(abs(m["F2_chunk"] - 1) < 1e-9,
          "tự chấm cấp chunk = 1,0", f"P {m['P_chunk']:.4f} R {m['R_chunk']:.4f}")

    # Nhãn vàng rỗng hoàn toàn -> phải ra 0, không crash, không chia cho 0
    empty = [{"id": g["id"], "relevant_docs": ["khong-ton-tai"], "info": ["xyzzy qwerty"]}
             for g in gold[:20]]
    m0 = score(recs, empty)
    check(m0["F2_doc"] == 0 and m0["F2_chunk"] == 0, "nhãn sai hoàn toàn -> 0 điểm")

    # F2 phải ưu tiên recall gấp 4, và khớp dạng rút gọn 5g/(4G+k)
    check(f2(0.2, 0.8) > f2(0.8, 0.2), "F2 ưu tiên recall")
    ok = all(abs(f2(g/k, g/G) - 5*g/(4*G+k)) < 1e-12
             for g, G, k in ((3, 5, 10), (1, 1, 1), (7, 20, 50), (2, 3, 4)))
    check(ok, "F2 khớp dạng rút gọn 5g/(4G+k)")

    # covers: chứa nguyên văn và overlap đủ
    check(covers("bệnh viêm dạ dày trợt xung huyết mạn tính", "viêm dạ dày trợt"),
          "covers: nhận ra đoạn chứa nguyên văn")
    check(not covers("cách phòng ngừa sốt xuất huyết", "viêm dạ dày trợt xung huyết"),
          "covers: không nhận sai đoạn lệch chủ đề")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--stage", choices=["crawl", "chunk", "submission", "score"], default=None)
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    recs = None
    if args.stage in (None, "crawl"):
        audit_crawl(conn)
    if args.stage in (None, "chunk"):
        audit_chunk(conn)
    if args.stage in (None, "submission"):
        recs = audit_submission(conn, args.db)
    if args.stage in (None, "score") and recs:
        audit_score(recs)
    print("\n" + "=" * 60)
    if _fails:
        print(f"{len(_fails)} MỤC FAIL:")
        for f in _fails:
            print(f"  - {f}")
        return 1
    print("TẤT CẢ PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
