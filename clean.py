"""Lọc dòng boilerplate lặp lại trong cùng domain. Theo `PIPELINE.md` §2 mục 3.

`trafilatura` đã bỏ nav/footer/ads, nhưng vẫn sót breadcrumb và danh sách "bài liên quan":

    medlatec.vn:  "Tin tức\\nChỉ số beta hCG...\\n- 31/08/2023 | Xét nghiệm beta BÀ RỊA..."
                   ^^^^^^^ breadcrumb        ^^^^^^^^^^^^^^^^^^ bài liên quan

Cách phát hiện, không hardcode: một dòng xuất hiện trong > `--min-df` tỉ lệ số trang của
CÙNG một domain thì gần như chắc là boilerplate. Nội dung thật không lặp lại ở 30% số trang.

Hai điều phải cẩn thận:
  1. `body` đổi thì **mọi offset chunk của doc đó sai** → phải XOÁ chunk của chúng, để
     `chunk.py` cắt lại.
  2. Dòng còn lại vẫn **nguyên văn** từng dòng. Việc nối các dòng không liền nhau thì
     `trafilatura` đã làm từ đầu (nó bỏ nav giữa các đoạn), nên không phát sinh vấn đề mới.
     Cách chấm cấp chunk dùng tiêu chí "chứa hoặc overlap đủ", không đòi khớp chuỗi tuyệt đối.

  python clean.py --analyze              # xem sẽ bỏ gì, KHÔNG sửa dữ liệu
  python clean.py --analyze --domain medlatec.vn
  python clean.py --apply                # sửa thật, rồi chạy `python chunk.py`
  python clean.py --demo
"""
import argparse
import collections
import sqlite3
import sys

DB = "data/corpus_new.sqlite"
# Ngưỡng đo trên dữ liệu thật ngày 01/10/2026. Ban đầu đặt 0,30 và TRƯỢT những ca rõ ràng:
#   laodong.vn   24,9% 'Thực hiện theo các bước sau để tắt tiện ích chặn quảng cáo'
#   medlatec.vn  29,9% 'Bác sĩ duyệt bài:BSCKI. Dương Ngọc Vân'
# Lý do 0,10 an toàn: boilerplate giống nhau TỪNG KÝ TỰ qua nhiều trang. Một câu nội dung
# thật xuất hiện y hệt trên 10% của 27.000 trang là gần như không thể.
MIN_DF = 0.10
MIN_DF_COUNT = 10    # sàn tuyệt đối: domain nhỏ thì 10% có thể chỉ là trùng hợp
MAX_LEN = 300        # dòng dài hơn thế thì khó là boilerplate
MIN_DOCS = 20        # domain ít hơn thế thì thống kê không đáng tin
MIN_BODY = 200       # sau khi lọc còn ít hơn thế thì GIỮ NGUYÊN, thà bẩn hơn mất

# Bảo vệ nội dung của CHÍNH trang đó. Khối "bài liên quan" ở các báo nhỏ chứa lead của bài
# khác; dòng đó là boilerplate trên 28 trang sidebar nhưng là NỘI DUNG trên trang của nó.
# Đo được trên phuyen.baodaklak.vn: 3/7 dòng bị gắn cờ nằm ở ~15-20% đầu body của một doc.
# Phân biệt bằng vị trí + độ dài: nav rác thì NGẮN ('30°C', 'Tây Ninh'), câu nội dung thì DÀI.
KEEP_HEAD_FRAC = 0.20    # 20% đầu body
KEEP_MIN_LEN = 60        # và dòng dài từ 60 ký tự -> coi là nội dung, giữ lại

# Blacklist được LƯU LẠI. Nếu không lưu, bộ lọc tự vô hiệu hoá: sau lần apply đầu các dòng
# boilerplate biến khỏi `body`, nên lần chạy sau `df` tụt dưới ngưỡng và doc mới crawl về
# không bao giờ được lọc. Mỗi lần chạy = phát hiện dòng MỚI + áp lại TOÀN BỘ danh sách cũ.
SCHEMA = """
CREATE TABLE IF NOT EXISTS boilerplate (
  domain TEXT NOT NULL, line TEXT NOT NULL, df REAL, n_doc INTEGER, found TEXT,
  PRIMARY KEY (domain, line)
);
"""


def find_boilerplate(bodies, min_df=MIN_DF, max_len=MAX_LEN, min_count=MIN_DF_COUNT):
    """Trả {dòng: tỉ lệ df} cho một domain.

    Đếm theo DOCUMENT FREQUENCY (số trang chứa dòng đó), không phải tổng số lần xuất hiện -
    một dòng lặp 50 lần trong một trang không phải boilerplate của domain.

    Cần vượt CẢ HAI: tỉ lệ > `min_df` và số trang >= `min_count`. Sàn tuyệt đối để domain
    nhỏ (20 doc) không bị nhận lầm vì trùng hợp.
    """
    n = len(bodies)
    df = collections.Counter()
    for b in bodies:
        for line in {L.strip() for L in b.split("\n") if L.strip()}:
            if len(line) <= max_len:
                df[line] += 1
    return {line: k / n for line, k in df.items()
            if k / n > min_df and k >= min_count}


def strip_lines(body, bad, min_body=MIN_BODY, head_frac=KEEP_HEAD_FRAC,
                keep_min_len=KEEP_MIN_LEN):
    """Bỏ các dòng trong `bad`. Trả None nếu không đổi hoặc kết quả quá ngắn.

    GIỮ LẠI dòng dài (>= `keep_min_len`) nằm trong `head_frac` đầu body: ở trang này nó
    gần như chắc là nội dung thật, dù trên trang khác nó chỉ là mục "bài liên quan".
    Dòng ngắn thì bỏ ở mọi vị trí - nav/breadcrumb/widget đều ngắn.
    """
    head = len(body) * head_frac
    keep, pos = [], 0
    for L in body.split("\n"):
        st = L.strip()
        protected = pos < head and len(st) >= keep_min_len
        if st not in bad or protected:
            keep.append(L)
        pos += len(L) + 1
    out = "\n".join(keep).strip()
    if out == body or len(out) < min_body:
        return None
    return out


def domains(conn, only=None):
    q = ("SELECT domain, count(*) FROM doc WHERE length(body)>=? GROUP BY domain "
         "HAVING count(*)>=? ORDER BY 2 DESC")
    rows = conn.execute(q, (MIN_BODY, MIN_DOCS)).fetchall()
    return [r for r in rows if not only or r[0] == only]


def load_known(conn, dom):
    """Blacklist đã lưu của một domain."""
    try:
        return {r[0] for r in conn.execute(
            "SELECT line FROM boilerplate WHERE domain=?", (dom,))}
    except sqlite3.OperationalError:
        return set()


def run(conn, apply=False, only=None, min_df=MIN_DF, max_len=MAX_LEN, top=12):
    conn.executescript(SCHEMA)
    doms = domains(conn, only)
    if not doms:
        print(f"Không có domain nào đủ {MIN_DOCS} doc" + (f" (lọc: {only})" if only else ""))
        return
    print(f"{len(doms)} domain có ≥{MIN_DOCS} doc. Ngưỡng: dòng xuất hiện ở >{min_df:.0%} trang\n")
    tot_doc = tot_cut = tot_bytes = 0
    report = []
    for dom, ndoc in doms:
        rows = conn.execute("SELECT doc_id, body FROM doc WHERE domain=? AND length(body)>=?",
                            (dom, MIN_BODY)).fetchall()
        found = find_boilerplate([b for _, b in rows], min_df, max_len)
        known = load_known(conn, dom)
        # Áp CẢ dòng mới phát hiện LẪN dòng đã lưu từ lần trước
        bad = set(found) | known
        if not bad:
            continue
        if apply and found:
            conn.executemany(
                "INSERT OR REPLACE INTO boilerplate (domain,line,df,n_doc,found) "
                "VALUES (?,?,?,?,datetime('now'))",
                [(dom, L, d, ndoc) for L, d in found.items()])
        changed, saved = [], 0
        for doc_id, body in rows:
            out = strip_lines(body, bad)
            if out is not None:
                changed.append((out, doc_id))
                saved += len(body) - len(out)
        if not changed:
            continue
        report.append((saved, dom, ndoc, len(changed), len(bad),
                       sorted(bad, key=len, reverse=True)[:3], len(known)))
        tot_doc += len(changed)
        tot_cut += len(bad)
        tot_bytes += saved
        if apply:
            # XOÁ chunk TRƯỚC khi đổi body: body đổi thì offset cũ sai
            ids = [d for _, d in changed]
            for i in range(0, len(ids), 500):
                part = ids[i:i + 500]
                qs = ",".join("?" * len(part))
                conn.execute(f"DELETE FROM chunk WHERE doc_id IN ({qs})", part)
            conn.executemany("UPDATE doc SET body=? WHERE doc_id=?", changed)
            conn.commit()

    report.sort(reverse=True)
    print(f"{'byte bỏ':>11} {'domain':<30} {'doc sửa':>9} {'dòng':>5} {'(cũ)':>5}  ví dụ")
    for saved, dom, ndoc, nch, nbad, ex, nknown in report[:top]:
        print(f"{saved:>11,} {dom:<30} {nch:>5,}/{ndoc:<4,} {nbad:>5} {nknown:>5}  "
              + " | ".join(repr(e[:36]) for e in ex[:2]))
    if len(report) > top:
        print(f"  ... và {len(report)-top} domain nữa")
    print(f"\nTổng: {tot_doc:,} doc sửa | {tot_cut:,} dòng boilerplate | "
          f"{tot_bytes/1024**2:.1f} MB bỏ đi")
    if apply:
        nbl, = conn.execute("SELECT count(*) FROM boilerplate").fetchone()
        print(f"Blacklist đã lưu: {nbl:,} dòng (dùng lại cho doc crawl về sau)")
        left, = conn.execute("SELECT count(*) FROM chunk").fetchone()
        print(f"Đã sửa. chunk còn {left:,} (đã xoá chunk của doc bị sửa)")
        print("→ Chạy `python chunk.py` để cắt lại, rồi `python audit.py`")
    else:
        print("Chưa sửa gì (chế độ --analyze). Dùng --apply để sửa thật.")


def demo():
    """Self-check: bắt đúng boilerplate, không chạm nội dung, không làm hỏng doc."""
    # 10 trang cùng domain: dòng "Trang chu" và "Lien he" có ở mọi trang
    bodies = [f"Trang chu\nNoi dung rieng cua bai {i} rat dai va khac nhau.\nLien he"
              for i in range(10)]
    bad = find_boilerplate(bodies, min_count=5)
    assert set(bad) == {"Trang chu", "Lien he"}, bad

    # Dòng chỉ có ở 2/10 trang -> KHÔNG phải boilerplate (2/10 = 20% > 10% nhưng 2 < min_count)
    bodies2 = bodies[:8] + ["Trang chu\nDong la\nLien he"] * 2
    assert "Dong la" not in find_boilerplate(bodies2, min_count=5)

    # SÀN TUYỆT ĐỐI: 20% nhưng chỉ 2 trang -> không bắt (domain nhỏ, có thể trùng hợp)
    small = ["A\nrieng %d" % i for i in range(8)] + ["A\nB"] * 2
    assert "B" not in find_boilerplate(small, min_df=0.1, min_count=5)
    # Cùng tỉ lệ nhưng đủ số trang -> bắt
    big = ["A\nrieng %d" % i for i in range(80)] + ["A\nB"] * 20
    assert "B" in find_boilerplate(big, min_df=0.1, min_count=10)

    # Ngưỡng 0,10 phải bắt được ca thật từng bị trượt ở 0,30
    real = ["Vui long cho phep quang cao xuat hien\nbai %d" % i if i < 25
            else "bai rieng %d" % i for i in range(100)]
    assert "Vui long cho phep quang cao xuat hien" in find_boilerplate(real)

    # Đếm theo document frequency: lặp 50 lần trong MỘT trang không phải boilerplate
    one = ["X\n" * 50 + "noi dung"] + ["khac nhau %d" % i for i in range(9)]
    assert "X" not in find_boilerplate(one), find_boilerplate(one)

    # Dòng quá dài không bị coi là boilerplate
    longline = "L" * 400
    assert longline not in find_boilerplate([f"{longline}\nbai {i}" for i in range(10)])

    # strip_lines: bỏ đúng, giữ nguyên văn từng dòng còn lại
    body = "Trang chu\nViem da day trot xung huyet man tinh la tinh trang niem mac bi viem.\nLien he"
    out = strip_lines(body, {"Trang chu", "Lien he"}, min_body=10)
    assert out == "Viem da day trot xung huyet man tinh la tinh trang niem mac bi viem.", out
    assert out in body.replace("\n", "\n"), "từng dòng còn lại phải nguyên văn"

    # BẢO VỆ: câu DÀI ở đầu body phải được giữ dù nằm trong blacklist
    lead = "Day la cau mo dau rat dai cua chinh bai bao nay, dai hon sau muoi ky tu."
    b = lead + "\n" + "x" * 500 + "\n" + lead
    out = strip_lines(b, {lead}, min_body=10)
    assert out.startswith(lead), "câu dài ở đầu phải được giữ"
    assert out.count(lead) == 1, f"bản ở cuối (sidebar) phải bị bỏ: {out.count(lead)}"

    # Dòng NGẮN thì bỏ ở mọi vị trí, kể cả đầu body
    b2 = "30°C\n" + "y" * 500 + "\n30°C"
    out2 = strip_lines(b2, {"30°C"}, min_body=10)
    assert "30°C" not in out2, out2

    # Không đổi gì -> None
    assert strip_lines("abc\ndef", {"xyz"}, min_body=1) is None
    # Lọc xong quá ngắn -> None (thà bẩn hơn mất nội dung)
    assert strip_lines("Trang chu\nngan", {"Trang chu"}, min_body=200) is None

    # Vòng khép kín trên store trong RAM, có kiểm chunk bị xoá
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
      CREATE TABLE doc (doc_id TEXT PRIMARY KEY, domain TEXT, body TEXT);
      CREATE TABLE chunk (chunk_id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT,
                          ord INT, start INT, end INT, n_chars INT);""")
    for i in range(25):
        b = f"Tin tuc\n{'Noi dung bai %d ' % i * 20}\nBai lien quan"
        conn.execute("INSERT INTO doc VALUES (?,?,?)", (str(i), "d.vn", b))
        conn.execute("INSERT INTO chunk (doc_id,ord,start,end,n_chars) VALUES (?,0,0,?,?)",
                     (str(i), len(b), len(b)))
    conn.commit()
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        run(conn, apply=True)
    b0, = conn.execute("SELECT body FROM doc WHERE doc_id='0'").fetchone()
    assert "Tin tuc" not in b0 and "Bai lien quan" not in b0, b0[:80]
    assert "Noi dung bai 0" in b0
    nch, = conn.execute("SELECT count(*) FROM chunk").fetchone()
    assert nch == 0, f"phải xoá hết chunk của doc bị sửa, còn {nch}"

    # BLACKLIST PHẢI ĐƯỢC LƯU: nếu không, bộ lọc tự vô hiệu hoá ở lần chạy sau
    bl = {r[0] for r in conn.execute("SELECT line FROM boilerplate")}
    assert "Tin tuc" in bl and "Bai lien quan" in bl, bl
    # Thêm 1 doc MỚI còn boilerplate; nó là thiểu số nên df tụt dưới ngưỡng,
    # nhưng blacklist đã lưu phải vẫn lọc được nó
    conn.execute("INSERT INTO doc VALUES ('new','d.vn',?)",
                 ("Tin tuc\n" + "Noi dung bai moi " * 20 + "\nBai lien quan",))
    conn.commit()
    with contextlib.redirect_stdout(_io.StringIO()):
        run(conn, apply=True)
    nb, = conn.execute("SELECT body FROM doc WHERE doc_id='new'").fetchone()
    assert "Tin tuc" not in nb and "Bai lien quan" not in nb, \
        "doc mới phải được lọc bằng blacklist đã lưu, dù df của nó dưới ngưỡng"
    assert "Noi dung bai moi" in nb
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--analyze", action="store_true", help="chỉ xem, không sửa")
    ap.add_argument("--apply", action="store_true", help="sửa body + xoá chunk liên quan")
    ap.add_argument("--domain", default=None, help="chỉ một domain")
    ap.add_argument("--min-df", type=float, default=MIN_DF)
    ap.add_argument("--max-len", type=int, default=MAX_LEN)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    demo()
    if not (a.analyze or a.apply):
        sys.exit("Phải cho --analyze (xem trước) hoặc --apply (sửa thật)")
    conn = sqlite3.connect(a.db, timeout=300)
    run(conn, apply=a.apply, only=a.domain, min_df=a.min_df, max_len=a.max_len)


if __name__ == "__main__":
    sys.exit(main())
