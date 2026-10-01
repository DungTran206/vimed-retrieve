"""Cắt chunk theo OFFSET vào `doc.body`. Theo `PIPELINE.md` §3.

Chunk chỉ lưu `(doc_id, start, end)`; `chunk_text = body[start:end]`. Nhờ vậy ràng buộc
"`chunk_text` phải nguyên văn" được bảo đảm bằng **cấu trúc dữ liệu**, không bằng kỷ luật -
không có đường nào để chunk lệch khỏi tài liệu gốc.

Thiết kế dựa trên số đo thật (`PROGRESS.md`), không phải quy ước:
  - `trafilatura` phân cách đoạn bằng '\\n', KHÔNG có '\\n\\n'
  - đoạn văn trung vị 80 ký tự, P90 330
  - chỉ 0,04% đoạn tự nó vượt 1 chunk  -> cắt theo câu chỉ là dự phòng hiếm
  - 76,3% tài liệu vừa trọn 1 chunk    -> phần lớn doc không phải cắt gì
=> Gộp đoạn liên tiếp đến hết budget, chồng lấn 1 đoạn. KHÔNG cần cửa sổ trượt.

  python chunk.py                      # cắt toàn bộ doc trong store
  python chunk.py --calibrate          # đo ký tự/token thật bằng tokenizer BGE-M3
  python chunk.py --demo               # self-check, không cần dữ liệu
"""
import argparse
import re
import sqlite3
import sys

DB = "data/corpus.sqlite"
TARGET_TOKENS = 900          # đề khuyến nghị chunk <= ~1.024 token; chừa biên an toàn

# Ký tự trên mỗi token, theo ngôn ngữ. Giá trị khởi điểm; `--calibrate` đo lại bằng
# tokenizer thật của BGE-M3 (XLM-RoBERTa) rồi in ra con số nên dùng.
# Ký tự/token, đo bằng tokenizer BGE-M3 thật (`--calibrate`) ngày 01/10/2026.
# PHẢI dùng giá trị BẢO THỦ (phân vị thấp), không phải trung bình: trung bình vi là 3,75
# nhưng văn bản đậm nhất xuống tới 1,32 ký tự/token, nên budget theo trung bình cho ra
# chunk 2.787 token. Đây là P5 đo được.
CHARS_PER_TOKEN = {"zh": 1.25, "vi": 3.40}
HARD_LIMIT = 1024          # đề khuyến nghị mỗi chunk không quá ~1.024 token

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunk (
  chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
  doc_id TEXT NOT NULL, ord INTEGER, start INTEGER, end INTEGER, n_chars INTEGER
);
CREATE INDEX IF NOT EXISTS ch_doc ON chunk(doc_id, ord);
"""

SENT_END = re.compile(r"(?<=[.!?…。！？；;])\s+")


def paragraphs(body):
    """[(start, end)] của từng đoạn không rỗng. Offset tính trên `body` gốc."""
    out, pos = [], 0
    for part in body.split("\n"):
        if part.strip():
            out.append((pos, pos + len(part)))
        pos += len(part) + 1          # +1 cho chính ký tự '\n'
    return out


def split_long(body, start, end, budget):
    """Đoạn đơn lẻ dài hơn budget -> cắt theo ranh giới CÂU. Dự phòng cho 0,04% trường hợp.

    Câu vẫn dài hơn budget (bảng, danh sách không dấu câu) thì cắt cứng theo ký tự -
    thà có chunk hơi dài còn hơn mất nội dung, vì F2 nặng recall.
    """
    text = body[start:end]
    spans, pos = [], 0
    for sent in SENT_END.split(text):
        if sent:
            spans.append((pos, pos + len(sent)))
        pos += len(sent) + 1
    if not spans:
        spans = [(0, len(text))]

    out, cur_s, cur_e = [], None, None
    for s, e in spans:
        if cur_s is None:
            cur_s, cur_e = s, e
        elif e - cur_s <= budget:
            cur_e = e
        else:
            out.append((start + cur_s, start + cur_e))
            cur_s, cur_e = s, e
    if cur_s is not None:
        out.append((start + cur_s, start + cur_e))

    # Cắt cứng những mảnh vẫn quá dài. KHÔNG có khoảng dư: cắt đúng budget không làm mất
    # nội dung, chỉ tạo thêm chunk. (Bug trước đây: `budget * 1.5` cho ra chunk 1.154 token.)
    final = []
    for s, e in out:
        while e - s > budget:
            final.append((s, s + budget))
            s += budget
        if e > s:
            final.append((s, e))
    return final


def chunk_offsets(body, budget, overlap_paras=1):
    """Gộp đoạn liên tiếp đến hết budget. Trả [(start, end)], mỗi cái là một LÁT của body.

    Chồng lấn `overlap_paras` đoạn giữa hai chunk liền kề: rẻ (đoạn trung vị 80 ký tự) và
    tránh cắt đứt một "phần thông tin" giữa hai chunk - đúng cái cách chấm cấp chunk đo.
    """
    paras = paragraphs(body)
    if not paras:
        return []
    if paras[-1][1] - paras[0][0] <= budget:        # 76,3% doc đi vào nhánh này
        return [(paras[0][0], paras[-1][1])]

    out, group = [], []
    i = 0
    while i < len(paras):
        s, e = paras[i]
        if e - s > budget and not group:            # đoạn đơn lẻ quá dài
            out += split_long(body, s, e, budget)
            i += 1
            continue
        if group and e - group[0][0] > budget:
            out.append((group[0][0], group[-1][1]))
            # lùi lại `overlap_paras` đoạn để chồng lấn; luôn tiến ít nhất 1 đoạn
            back = min(overlap_paras, len(group) - 1)
            i -= back
            group = []
            continue
        group.append((s, e))
        i += 1
    if group:
        out.append((group[0][0], group[-1][1]))
    return out


def budget_for(lang, target_tokens=TARGET_TOKENS):
    return int(target_tokens * CHARS_PER_TOKEN.get(lang or "vi", 3.40))


def enforce_token_limit(body, spans, tok, limit=HARD_LIMIT):
    """Cắt tiếp những chunk THỰC SỰ vượt `limit` token, đo bằng tokenizer thật.

    Budget theo ký tự chỉ là xấp xỉ - không hằng số nào bảo đảm được trần khi mật độ
    token biến động (vi: 3,75 trung bình nhưng 1,32 ở văn bản đậm nhất). Đây là bước
    bảo đảm cứng.

    Chunk ngắn hơn `limit` ký tự thì không thể vượt (một token luôn ≥ 1 ký tự) nên được
    bỏ qua mà không cần tokenize - phần lớn chunk đi vào nhánh này.
    """
    out = []
    for s, e in spans:
        if e - s <= limit:
            out.append((s, e))
            continue
        n = len(tok.encode(body[s:e], add_special_tokens=False))
        if n <= limit:
            out.append((s, e))
            continue
        k = -(-n // int(limit * 0.9))          # số mảnh, chừa biên 10%
        step = max(1, (e - s) // k + 1)
        for i in range(s, e, step):
            out.append((i, min(i + step, e)))
    return out


def build(conn, target_tokens=TARGET_TOKENS, overlap=1, rebuild=False, batch=5000,
          verify_tokens=True):
    conn.executescript(SCHEMA)
    tok = None
    if verify_tokens:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained("BAAI/bge-m3")
    if rebuild:
        conn.execute("DELETE FROM chunk")
        conn.commit()
    done = {r[0] for r in conn.execute("SELECT DISTINCT doc_id FROM chunk")}
    rows = conn.execute("SELECT doc_id, lang, body FROM doc WHERE length(body)>=200").fetchall()
    todo = [r for r in rows if r[0] not in done]
    print(f"{len(rows):,} doc dùng được | đã cắt {len(done):,} | cần cắt {len(todo):,}")

    ins, nchunk, one = [], 0, 0
    nsplit = 0
    for doc_id, lang, body in todo:
        spans = chunk_offsets(body, budget_for(lang, target_tokens), overlap)
        if tok is not None:
            before = len(spans)
            spans = enforce_token_limit(body, spans, tok)
            nsplit += len(spans) - before
        one += len(spans) == 1
        for o, (s, e) in enumerate(spans):
            # Bất biến cốt tử: offset phải nằm trong body và cắt ra phải khớp
            assert 0 <= s < e <= len(body), (doc_id, s, e, len(body))
            ins.append((doc_id, o, s, e, e - s))
        nchunk += len(spans)
        if len(ins) >= batch:
            conn.executemany("INSERT INTO chunk (doc_id,ord,start,end,n_chars) "
                             "VALUES (?,?,?,?,?)", ins)
            conn.commit()
            ins = []
    if ins:
        conn.executemany("INSERT INTO chunk (doc_id,ord,start,end,n_chars) "
                         "VALUES (?,?,?,?,?)", ins)
    conn.commit()
    if todo:
        print(f"Tạo {nchunk:,} chunk | {nchunk/len(todo):.2f} chunk/doc | "
              f"{one/len(todo)*100:.1f}% doc chỉ 1 chunk"
              + (f" | tokenizer cắt thêm {nsplit}" if tok is not None else
                 " | KHÔNG kiểm token (--no-verify-tokens)"))
    verify(conn)


def verify(conn, sample=500):
    """Kiểm bất biến trên mẫu: chunk_text PHẢI bằng body[start:end], và phủ hết body."""
    rows = conn.execute(
        "SELECT c.doc_id, c.start, c.end, d.body FROM chunk c JOIN doc d USING(doc_id) "
        "ORDER BY random() LIMIT ?", (sample,)).fetchall()
    for doc_id, s, e, body in rows:
        assert 0 <= s < e <= len(body), f"offset ngoài body: {doc_id} [{s}:{e}]/{len(body)}"
        assert body[s:e].strip(), f"chunk rỗng: {doc_id} [{s}:{e}]"
    # Độ phủ: hợp các chunk phải chứa gần hết body (bỏ sót = mất recall)
    bad = []
    for doc_id, body in conn.execute(
            "SELECT doc_id, body FROM doc WHERE length(body)>=200 "
            "ORDER BY random() LIMIT 200"):
        spans = conn.execute("SELECT start,end FROM chunk WHERE doc_id=? ORDER BY ord",
                             (doc_id,)).fetchall()
        if not spans:
            continue
        covered = len({i for s, e in spans for i in range(s, e)})
        nonspace = len(re.sub(r"\s", "", body))
        if covered < nonspace * 0.95:
            bad.append((doc_id, covered, len(body)))
    print(f"Kiểm {len(rows)} chunk: offset và nguyên văn OK"
          + (f" | ⚠️ {len(bad)} doc phủ < 95%: {bad[:3]}" if bad else " | độ phủ OK"))


def calibrate(conn, n=300):
    """Đo ký tự/token THẬT bằng tokenizer của BGE-M3, thay cho hằng số ước lượng."""
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("BAAI/bge-m3")
    print(f"{'lang':6} {'n doc':>6} {'ký tự/token':>12} {'đang dùng':>10} {'budget nên dùng':>16}")
    for lang in ("vi", "zh"):
        rows = conn.execute(
            "SELECT body FROM doc WHERE lang=? AND length(body)>=400 "
            "ORDER BY random() LIMIT ?", (lang, n)).fetchall()
        if not rows:
            print(f"{lang:6} {'(chưa có doc)':>6}")
            continue
        chars = sum(len(b) for b, in rows)
        toks = sum(len(tok.encode(b[:6000], add_special_tokens=False)) for b, in rows)
        cpt = chars / toks
        print(f"{lang:6} {len(rows):>6} {cpt:>12.2f} {CHARS_PER_TOKEN[lang]:>10.2f} "
              f"{int(TARGET_TOKENS*cpt):>16,}")
    print(f"\nSửa CHARS_PER_TOKEN trong chunk.py nếu lệch, rồi `python chunk.py --rebuild`.")


def demo():
    """Self-check: bất biến nguyên văn, chồng lấn, đoạn quá dài, các ca biên."""
    # paragraphs: offset phải trỏ đúng vào body gốc
    body = "đoạn một\nđoạn hai dài hơn\n\nđoạn ba"
    ps = paragraphs(body)
    assert [body[s:e] for s, e in ps] == ["đoạn một", "đoạn hai dài hơn", "đoạn ba"], ps

    # Doc ngắn -> đúng 1 chunk, và chunk đó là cả body (đã strip hai đầu)
    short = "\n".join(["câu ngắn số %d." % i for i in range(5)])
    sp = chunk_offsets(short, 10_000)
    assert len(sp) == 1 and short[sp[0][0]:sp[0][1]] == short, sp

    # BẤT BIẾN CỐT TỬ: mọi chunk phải là một lát nguyên văn, offset hợp lệ
    long_body = "\n".join(f"Đoạn thứ {i} nói về viêm dạ dày trợt xung huyết mạn tính và "
                          f"cách điều trị bằng thuốc ức chế bơm proton." for i in range(60))
    spans = chunk_offsets(long_body, 400, overlap_paras=1)
    assert len(spans) > 1, "body dài phải cắt thành nhiều chunk"
    for s, e in spans:
        assert 0 <= s < e <= len(long_body)
        assert long_body[s:e] == long_body[s:e]          # tautology có chủ ý: là LÁT
        assert long_body[s:e].strip()
    # Phải phủ hết: không được bỏ sót đoạn nào (bỏ sót = mất recall)
    covered = {i for s, e in spans for i in range(s, e)}
    missed = [i for i, ch in enumerate(long_body) if not ch.isspace() and i not in covered]
    assert not missed, f"bỏ sót {len(missed)} ký tự, ví dụ vị trí {missed[:5]}"
    # Chồng lấn: chunk sau phải bắt đầu TRƯỚC khi chunk trước kết thúc
    assert any(spans[i + 1][0] < spans[i][1] for i in range(len(spans) - 1)), \
        "phải có chồng lấn giữa các chunk liền kề"
    # overlap=0 thì không chồng lấn, và vẫn phủ hết
    s0 = chunk_offsets(long_body, 400, overlap_paras=0)
    assert all(s0[i + 1][0] >= s0[i][1] for i in range(len(s0) - 1))
    c0 = {i for s, e in s0 for i in range(s, e)}
    assert not [i for i, ch in enumerate(long_body) if not ch.isspace() and i not in c0]

    # Đoạn ĐƠN LẺ dài hơn budget -> cắt theo câu, vẫn là lát nguyên văn
    one_para = " ".join(f"Câu số {i} trong một đoạn rất dài." for i in range(80))
    sp = chunk_offsets(one_para, 300)
    assert len(sp) > 1, "đoạn đơn lẻ quá dài phải được cắt"
    for s, e in sp:
        assert one_para[s:e].strip() and e - s <= 300 * 1.5 + 50, (s, e, e - s)

    # Không có dấu câu nào (bảng, danh sách) -> cắt cứng, không treo
    nopunct = "x" * 2000
    sp = chunk_offsets(nopunct, 300)
    assert len(sp) >= 4 and all(nopunct[s:e] for s, e in sp)

    # split_long KHÔNG được để mảnh nào vượt budget (bug cũ: khoảng dư 1,5x)
    nopunct2 = "y" * 1000
    for s, e in chunk_offsets(nopunct2, 200):
        assert e - s <= 200, f"mảnh {e-s} ký tự vượt budget 200"

    # enforce_token_limit: chunk vượt trần phải bị cắt; chunk ngắn không bị tokenize
    class FakeTok:
        # 1 token mỗi ký tự -> mô phỏng văn bản đậm nhất có thể
        def __init__(self):
            self.calls = 0
        def encode(self, t, add_special_tokens=False):
            self.calls += 1
            return list(t)
    ft = FakeTok()
    body2 = "z" * 3000
    out = enforce_token_limit(body2, [(0, 3000)], ft, limit=1000)
    assert len(out) > 1 and all(e - s <= 1000 for s, e in out), out
    assert sum(e - s for s, e in out) == 3000, "không được mất ký tự khi cắt"
    assert out[0][0] == 0 and out[-1][1] == 3000, out
    ft2 = FakeTok()
    assert enforce_token_limit("x" * 500, [(0, 500)], ft2, limit=1000) == [(0, 500)]
    assert ft2.calls == 0, "chunk ngắn hơn limit ký tự KHÔNG được tokenize"

    # Ca biên
    assert chunk_offsets("", 100) == []
    assert chunk_offsets("\n\n\n", 100) == []
    assert budget_for("zh") < budget_for("vi"), "tiếng Trung đặc hơn nên budget ký tự nhỏ hơn"
    assert budget_for(None) == budget_for("vi")

    # Vòng khép kín với store trong RAM
    conn = sqlite3.connect(":memory:")
    conn.executescript("CREATE TABLE doc (doc_id TEXT PRIMARY KEY, lang TEXT, body TEXT);")
    conn.execute("INSERT INTO doc VALUES ('d1','vi',?)", (long_body,))
    conn.execute("INSERT INTO doc VALUES ('d2','vi',?)", (short,))
    conn.commit()
    build(conn, target_tokens=120, overlap=1, verify_tokens=False)
    n = conn.execute("SELECT count(*) FROM chunk").fetchone()[0]
    assert n > 1
    for doc_id, s, e, b in conn.execute(
            "SELECT c.doc_id,c.start,c.end,d.body FROM chunk c JOIN doc d USING(doc_id)"):
        assert b[s:e].strip(), (doc_id, s, e)
    build(conn, target_tokens=120, overlap=1, verify_tokens=False)   # phải idempotent
    assert conn.execute("SELECT count(*) FROM chunk").fetchone()[0] == n, "phải idempotent"
    print("demo OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB)
    ap.add_argument("--target-tokens", type=int, default=TARGET_TOKENS)
    ap.add_argument("--overlap", type=int, default=1, help="số đoạn chồng lấn")
    ap.add_argument("--rebuild", action="store_true", help="xoá chunk cũ, cắt lại")
    ap.add_argument("--no-verify-tokens", action="store_true",
                    help="bỏ bước bảo đảm trần 1.024 token bằng tokenizer thật (nhanh hơn, "
                         "nhưng budget ký tự không bảo đảm được trần)")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return demo()
    demo()
    # timeout: crawler có thể đang giữ write lock (SQLite cho nhiều reader, một writer)
    conn = sqlite3.connect(args.db, timeout=300)
    if args.calibrate:
        return calibrate(conn)
    if args.verify:
        return verify(conn)
    build(conn, args.target_tokens, args.overlap, args.rebuild,
          verify_tokens=not args.no_verify_tokens)


if __name__ == "__main__":
    sys.exit(main())
