"""Bước 6: chọn chunk theo GIÁ TRỊ — cắt body[:10000] thành mảnh rồi chỉ giữ mảnh có p̂_doc × π ≥ τ; xuất JSON + ZIP.

π = P(mảnh khớp đoạn vàng | doc vàng), khớp từ điểm tổng leaderboard của 7 bài nộp (luật chấm chunk từ 23/10):
đoạn vàng là ô k của lưới N token XLM-R (bge-m3, văn bản đã chuẩn hoá), 30% N=640 / 70% N=1152, P(k) ∝ 0,8^k;
mảnh khớp khi LCS ≥ 0,4·|vàng| VÀ ≥ 0,4·|mảnh|, LCS ≈ giao + 0,11·min(phần dư hai bên).
--cut s5000: chia đều ≤ 5.000 ký tự (zh 1.860); --cut pack: ghép dòng tới trần 1.152 token (bài nộp dùng pack).
--scope set: chỉ doc trong relevant_docs, mỗi doc giữ ít nhất mảnh có π lớn nhất.
--scope all: thêm mảnh của cả 380 ứng viên (doc ngoài relevant_docs) nếu đạt ngưỡng.
--tau-extra: ngưỡng riêng cho doc ngoài relevant_docs (p̂ đánh giá cao ~2× doc ngoài tập đã fit; mặc định = --tau).
--overlap: hai mảnh liền kề cùng được giữ thì nới ranh giới qua nhau như overlap_v1 (≤5% mảnh ngắn hơn, ≤200 ký tự).
relevant_docs giữ nguyên (doc F2 không đổi). Không dùng nhãn, không GPU.

--merge (với --cut pack): mỗi doc chọn bằng quy hoạch động các khoảng rời nhau gồm 1 hoặc 2 mảnh liền kề (gộp thành MỘT
  chunk: đoạn vàng ở mảnh nào cũng còn ≥ 40% chunk gộp nên đỡ tốn chunk), tối đa Σ(p̂·π − τ); π = TB hai giả thuyết.
  (--recal <tag> đọc tập doc + p̂ do baseline.recal_docs hoặc baseline.ltr_docs ghi ra)

Bài nộp (FINAL public 0,4201), build → compress (≥ 4 GiB RAM trống) → verify (đọc lại ZIP, so từng câu):
  python -m baseline.value_chunks build --tau 0.09 --scope all --overlap --recal gbm3q --cut pack --merge
"""
import argparse
from array import array
import bisect
import hashlib
import html
import json
import os
from pathlib import Path
import pickle
import re
import sqlite3
import unicodedata
import zipfile

from submit import submission


def pieces(t, L):
    """Chia text dài thành mảnh ≈ đều, mỗi mảnh ~≤ L ký tự, cắt ở xuống dòng gần điểm chia (±L/4), không có thì cắt cứng.
    Mảnh là lát cắt của t nên vẫn nguyên văn (bài s5000: L = 5.000 ký tự vi / 1.860 zh)."""
    if not L or len(t) <= L:
        return [(0, len(t))]
    k = -(-len(t) // L)
    cut = [0]
    for j in range(1, k):
        x = round(len(t) * j / k)
        a, b = t.rfind("\n", max(cut[-1] + 1, x - L // 4), x), t.find("\n", x, x + L // 4)
        n = min((m for m in (a, b) if m >= 0), key=lambda m: abs(m - x), default=-1)
        cut.append(n + 1 if n >= 0 else x)
    cut.append(len(t))
    return [(a, b) for a, b in zip(cut, cut[1:]) if t[a:b].strip()]


def expanded_pair(text, cut):
    """Nới ranh giới hai mảnh liền kề qua nhau ≤5% mảnh ngắn hơn (≤200 ký tự), ưu tiên hết câu/đoạn (bài overlap_v1)."""
    assert 0 < cut < len(text)
    width = min(200, max(1, min(cut, len(text) - cut) // 20))
    lo, hi = cut - width, cut + width
    boundaries = [lo + m.end() for m in re.finditer(
        r"\n|[.!?](?:[ \t]+|(?=\n|$))|[。！？]", text[lo:hi])]
    left = min((p for p in boundaries if lo <= p < cut), default=lo)
    right = max((p for p in boundaries if cut < p <= hi), default=hi)
    if left == lo:                            # không có ranh giới câu: tránh xẻ từ tiếng Việt khi có khoảng trắng
        p = text.find(" ", lo, cut)
        if 0 <= p < cut - 1:
            left = p + 1
    if right == hi:
        p = text.rfind(" ", cut + 1, hi)
        if p > cut:
            right = p
    assert 0 <= left < cut < right <= len(text)
    return (0, right), (left, len(text))

DOCS = Path("data/val/docs_z80base160.json")
SCORES = Path("data/val/z80base_scores.json")
DOC_FP = "9acf4a3bb1be"
CACHE = Path("data/value_chunks/doc_T.json")
MAX_CHARS, SPLIT, SPLIT_ZH = 10000, 5000, 1860
FIT = {"mix": [[640, 0.3], [1152, 0.7]], "w": 0.8, "nu": 0.11, "thr": 0.4}
_ws = re.compile(r"\s+")


def norm(t):
    """Chuẩn hoá như bộ chấm BTC: NFKC, HTML entity, chữ thường, gộp khoảng trắng."""
    return _ws.sub(" ", unicodedata.normalize("NFKC", html.unescape(t)).lower()).strip()


def gold_cells(T, fit=FIT):
    """[(đầu, cuối, xác suất)] các ô có thể là đoạn vàng của doc dài T token."""
    out = []
    for N, m in fit["mix"]:
        K = max(1, -(-T // N))
        wt = [fit["w"] ** k for k in range(K)]
        z = sum(wt)
        out += [(k * N, min((k + 1) * N, T), m * x / z) for k, x in enumerate(wt)]
    return out


def passes(a, b, s, e, fit=FIT):
    g, p = e - s, b - a
    i = max(0, min(b, e) - max(a, s))
    lcs = i + fit["nu"] * min(p - i, g - i)
    return lcs >= fit["thr"] * g and lcs >= fit["thr"] * p


def piece_pi(spans, n_chars, T10, T):
    """π cho từng mảnh (vị trí ký tự trong body[:10000]) — quy ra token theo tỉ lệ T10/n_chars."""
    r = T10 / max(n_chars, 1)
    cells = gold_cells(max(T, T10, 1))
    return [sum(pk for s, e, pk in cells if passes(round(a * r), round(b * r), s, e)) for a, b in spans]


def keep_idx(pis, p, tau, in_set):
    keep = [i for i, x in enumerate(pis) if p * x >= tau]
    if not keep and in_set and pis:
        keep = [max(range(len(pis)), key=lambda i: pis[i])]
    return keep


def overlap_spans(t, sp, keep):
    """Lát (start, end) của các mảnh được giữ; hai mảnh giữ liền kề thì nới ranh giới qua nhau (expanded_pair)."""
    out = {i: list(sp[i]) for i in keep}
    for i in keep:
        j = i + 1
        if j in out and sp[i][1] == sp[j][0]:
            a = sp[i][0]
            (_, right), (left, _) = expanded_pair(t[a:sp[j][1]], sp[i][1] - a)
            out[i][1], out[j][0] = a + right, a + left
    return [tuple(out[i]) for i in keep]


# --cut pack: cắt GIỐNG BTC — ghép dòng liên tiếp tới trần PACK_CUT token (giả thuyết khớp nhất 7 bài sau 23/10:
# đoạn vàng = 0,8×ghép-1152 + 0,2×ghép-768, vị trí đều). π của mảnh tính theo giả thuyết đó.
PACK_CUT = 1152
PACK = {"mix": [[1152, 0.8], [768, 0.2]]}
LINES = Path("data/value_chunks/doc_lines.pkl")


def line_bounds(b, starts):
    """Token và ký tự đầu mỗi dòng khác rỗng của body b (starts = ký tự đầu mỗi token của norm(b)); phần tử cuối = hết."""
    toks, chrs, pos, c = [], [], 0, 0
    for ln in b.split("\n"):
        nl = norm(ln)
        if nl:
            toks.append(bisect.bisect_left(starts, pos))
            chrs.append(c)
            pos += len(nl) + 1
        c += len(ln) + 1
    return toks + [len(starts)], chrs + [len(b)]


def pack_spans(toks, chrs, M):
    """Ghép dòng liên tiếp tới trần M token, dòng quá dài thì cắt cứng: [(tok đầu, tok cuối, ký tự đầu, ký tự cuối)]."""
    out, s_t, s_c = [], 0, 0
    for i in range(1, len(toks)):
        if toks[i] - s_t > M and toks[i - 1] > s_t:
            out.append((s_t, toks[i - 1], s_c, chrs[i - 1]))
            s_t, s_c = toks[i - 1], chrs[i - 1]
        while toks[i] - s_t > M and toks[i - 1] <= s_t:
            t2 = s_t + M
            c2 = chrs[i - 1] + (t2 - toks[i - 1]) * (chrs[i] - chrs[i - 1]) // max(toks[i] - toks[i - 1], 1)
            c2 = min(max(c2, s_c + 1), chrs[i])
            out.append((s_t, t2, s_c, c2))
            s_t, s_c = t2, c2
    if toks[-1] > s_t or not out:
        out.append((s_t, toks[-1], s_c, chrs[-1]))
    return out


def pack_pi(toks, chrs, spans_tok):
    """π cho từng mảnh (khoảng token) dưới giả thuyết ghép dòng, vị trí đều."""
    cells = []
    for M, m in PACK["mix"]:
        cs = pack_spans(toks, chrs, M)
        cells += [(s, e, m / len(cs)) for s, e, _, _ in cs]
    return [sum(pk for s, e, pk in cells if passes(a, b, s, e)) for a, b in spans_tok]


def merge_pi(toks, chrs, spans_tok, T10):
    """π cho --merge: TB hai giả thuyết (ghép dòng PACK, lưới FIT), đoạn vàng chỉ trong T10 token đầu
    (file chấm cũ: 100% đoạn vàng nằm trong body[:10000]); mỗi giả thuyết chuẩn hoá lại về tổng 1."""
    pk_ = []
    for M, m in PACK["mix"]:
        cs = pack_spans(toks, chrs, M)
        pk_ += [(s, min(e, T10), m / len(cs)) for s, e, _, _ in cs if s < T10]
    z = sum(x for _, _, x in pk_) or 1.0
    cells = [(s, e, 0.5 * x / z) for s, e, x in pk_] + [(s, e, 0.5 * x) for s, e, x in gold_cells(max(T10, 1))]
    return [sum(pk for s, e, pk in cells if passes(a, b, s, e)) for a, b in spans_tok]


def merge_plan(pis1, pis2, p, tau, in_set):
    """--merge: chọn các khoảng RỜI NHAU, mỗi khoảng = 1 mảnh hoặc 2 mảnh liền kề gộp thành MỘT chunk, tối đa
    Σ(p̂·π − τ) bằng quy hoạch động. pis1[i] = π mảnh i, pis2[i] = π của mảnh i gộp i+1. Trả [(i, j)]: mảnh i..j-1.
    Doc trong tập không giữ khoảng nào thì ép giữ khoảng có π lớn nhất (như keep_idx)."""
    n = len(pis1)
    best, how = [0.0] * (n + 1), [0] * (n + 1)
    for i in range(1, n + 1):
        best[i] = best[i - 1]
        for g, pi in ((1, pis1[i - 1]), (2, pis2[i - 2] if i >= 2 else None)):
            if pi is not None and best[i - g] + p * pi - tau > best[i]:
                best[i], how[i] = best[i - g] + p * pi - tau, g
    out, i = [], n
    while i > 0:
        if how[i]:
            out.append((i - how[i], i))
            i -= how[i]
        else:
            i -= 1
    if not out and in_set and n:
        cand = [((i, i + g), (pis1 if g == 1 else pis2)[i]) for i in range(n) for g in (1, 2) if i + g <= n]
        out = [max(cand, key=lambda x: x[1])[0]]
    return out[::-1]


class LineCache:
    """Ranh giới dòng (token, ký tự) mỗi doc, cache dạng array để nhẹ RAM."""

    def __init__(self):
        self.d = pickle.loads(LINES.read_bytes()) if LINES.exists() else {}
        self.tk = None
        self.dirty = False

    def get(self, bodies):
        miss = [d for d in bodies if d not in self.d]
        if miss:
            if self.tk is None:
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                from transformers import AutoTokenizer
                self.tk = AutoTokenizer.from_pretrained("BAAI/bge-m3")
            enc = self.tk([norm(bodies[d]) for d in miss], add_special_tokens=False, return_offsets_mapping=True)
            for d, offs in zip(miss, enc["offset_mapping"]):
                toks, chrs = line_bounds(bodies[d], [s for s, _ in offs])
                self.d[d] = (array("i", toks), array("i", chrs))
            self.dirty = True
        return {d: self.d[d] for d in bodies}

    def save(self):
        if self.dirty:
            LINES.parent.mkdir(parents=True, exist_ok=True)
            tmp = LINES.with_suffix(".part")
            tmp.write_bytes(pickle.dumps(self.d))
            tmp.replace(LINES)
            self.dirty = False


def out_path(c):
    ex = f"e{round(c['tau_extra'] * 100):02d}" if c["scope"] == "all" and c["tau_extra"] != c["tau"] else ""
    return Path(f"runs/{c.get('prefix', 'z80base160')}_v{round(c['tau'] * 100):02d}{'x' if c['scope'] == 'all' else ''}{ex}"
                f"{'_ov' if c['overlap'] else ''}{f'_p{PACK_CUT}' if c.get('cut') == 'pack' else ''}"
                f"{'_m2' if c.get('merge') else ''}")


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


class Lengths:
    """Độ dài token XLM-R (T10 = body[:10000], T = cả body) mỗi doc, cache ra file dùng chung giữa các bài."""

    def __init__(self):
        self.d = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
        self.tk = None
        self.dirty = False

    def get(self, bodies):
        miss = [d for d in bodies if d not in self.d]
        if miss:
            if self.tk is None:
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                from transformers import AutoTokenizer
                self.tk = AutoTokenizer.from_pretrained("BAAI/bge-m3")
            e10 = self.tk([norm(bodies[d][:MAX_CHARS]) for d in miss], add_special_tokens=False)["input_ids"]
            ef = self.tk([norm(bodies[d]) for d in miss], add_special_tokens=False)["input_ids"]
            for d, x, y in zip(miss, e10, ef):
                self.d[d] = [len(x), len(y)]
            self.dirty = True
        return {d: self.d[d] for d in bodies}

    def save(self):
        if self.dirty:
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            tmp = CACHE.with_suffix(".part")
            tmp.write_text(json.dumps(self.d), encoding="utf-8")
            tmp.replace(CACHE)
            self.dirty = False


def rows(c, lengths):
    """Sinh (bản ghi, thống kê) cho từng câu 1..1200 — tất định, dùng chung cho build và verify."""
    tau, tau_x = c["tau"], c["tau_extra"]
    D = json.loads(Path(c.get("docs", DOCS)).read_text(encoding="utf-8"))
    S = json.loads(Path(c.get("scores", SCORES)).read_text(encoding="utf-8"))
    con = sqlite3.connect("file:data/corpus_new.sqlite?mode=ro", uri=True)
    pack = c.get("cut") == "pack"
    lines = LineCache() if pack else None
    for q in range(1, 1201):
        ds = [str(d) for d in D[str(q)]]
        ph = {str(d): p for d, p in S[str(q)]}
        inset = set(ds)
        extra = [d for d, p in sorted(ph.items(), key=lambda x: (-x[1], x[0])) if d not in inset and p >= tau_x] \
            if c["scope"] == "all" else []
        want = ds + extra
        info = {}
        for i in range(0, len(want), 900):
            p_ = want[i:i + 900]
            info.update({d: (b or "", l) for d, b, l in con.execute(
                f"SELECT doc_id, body, lang FROM doc WHERE doc_id IN ({','.join('?' * len(p_))})", p_)})
        bodies = {d: info[d][0] for d in want if d in info and info[d][0].strip()}
        L = lengths.get(bodies)
        LB = lines.get(bodies) if pack else None
        ch, st = [], {"chunks_set": 0, "chunks_extra": 0, "docs_extra": 0, "chars": 0, "pieces_all": 0}
        for d in want:
            if d not in bodies:
                continue
            t = bodies[d][:MAX_CHARS]
            if pack:
                toks, chrs = LB[d]
                T10 = L[d][0]
                sel = [(ts, min(te, T10), cs, min(ce, MAX_CHARS)) for ts, te, cs, ce in pack_spans(toks, chrs, PACK_CUT)
                       if cs < MAX_CHARS and t[cs:min(ce, MAX_CHARS)].strip()]
                sp = [(cs, ce) for _, _, cs, ce in sel]
                if not c.get("merge"):
                    pis = pack_pi(toks, chrs, [(ts, te) for ts, te, _, _ in sel])
            else:
                sp = pieces(t, SPLIT_ZH if info[d][1] == "zh" else SPLIT)
                pis = piece_pi(sp, len(t), *L[d])
            st["pieces_all"] += len(sp) if d in inset else 0
            if c.get("merge"):                       # khoảng gộp thay cho mảnh; giữ hết các khoảng được chọn
                tk = [(ts, te) for ts, te, _, _ in sel]
                pis1 = merge_pi(toks, chrs, tk, T10)
                pis2 = merge_pi(toks, chrs, [(a[0], b[1]) for a, b in zip(tk, tk[1:])], T10)
                grp = merge_plan(pis1, pis2, ph.get(d, 0.0), tau if d in inset else tau_x, d in inset)
                sp = [(sel[i][2], sel[j - 1][3]) for i, j in grp]
                keep = list(range(len(sp)))
            else:
                keep = keep_idx(pis, ph.get(d, 0.0), tau if d in inset else tau_x, d in inset)
            for a, b in (overlap_spans(t, sp, keep) if c["overlap"] else [sp[i] for i in keep]):
                ch.append({"doc_id": int(d), "chunk_text": t[a:b]})
                st["chars"] += b - a
            st["chunks_set" if d in inset else "chunks_extra"] += len(keep)
            st["docs_extra"] += d not in inset and bool(keep)
        yield {"id": q, "relevant_docs": [int(d) for d in ds], "relevant_chunks": ch}, st
    con.close()
    if pack:
        lines.save()


def build(c):
    out = out_path(c)
    dest, report = out.with_suffix(".json"), out.with_suffix(".check.json")
    assert not any(p.exists() for p in (dest, out.with_suffix(".zip"), report)), f"{out} đã có, không ghi đè"
    lengths = Lengths()
    tot = {"queries": 0, "docs": 0, "chunks_set": 0, "chunks_extra": 0, "docs_extra": 0, "chars": 0, "pieces_all": 0}
    skel = []
    with open(str(dest) + ".part", "x", encoding="utf-8") as f:
        f.write("[")
        for rec, st in rows(c, lengths):
            assert not submission.validate([{**rec, "id": 1}], n_queries=1, id_type=int)
            f.write(("," if tot["queries"] else "") + json.dumps(rec, ensure_ascii=False, separators=(",", ":")))
            skel.append({**rec, "relevant_chunks": []})
            tot["queries"] += 1
            tot["docs"] += len(rec["relevant_docs"])
            for k in st:
                tot[k] += st[k]
            if tot["queries"] % 100 == 0:
                lengths.save()
                print(tot, flush=True)
        f.write("]")
    lengths.save()
    fp = submission.fingerprint(skel)[0]
    assert tot["queries"] == 1200 and (fp == DOC_FP or "docs" in c), "tập doc lệch z80base160"
    Path(str(dest) + ".part").replace(dest)
    tot.update(config={"docs": str(DOCS), "scores": str(SCORES), **c, "fit": FIT, "max_chars": MAX_CHARS,
                       "split": SPLIT, "split_zh": SPLIT_ZH, "uses_labels": "docs" in c, "uses_gpu": False},
               doc_fingerprint=fp, json_bytes=dest.stat().st_size, json_sha256=sha256(dest), pending_zip=True)
    report.write_text(json.dumps(tot, ensure_ascii=False, indent=2), encoding="utf-8")
    print("BUILD_DONE", json.dumps(tot, ensure_ascii=False), flush=True)


def compress(c):
    import psutil
    assert psutil.virtual_memory().available >= 4 * 1024 ** 3, "Cần ít nhất 4 GiB RAM trống để nén local"
    out = out_path(c)
    dest = out.with_suffix(".zip")
    assert not dest.exists() and not Path(str(dest) + ".part").exists()
    submission.zip_json(str(out.with_suffix(".json")), str(dest), "lzma")
    print("ZIP_DONE", dest.stat().st_size, flush=True)


def verify(c):
    import ijson
    out = out_path(c)
    dest, report_p = out.with_suffix(".zip"), out.with_suffix(".check.json")
    report = json.loads(report_p.read_text(encoding="utf-8"))
    assert all(report["config"].get(k) == v for k, v in c.items()), "cấu hình lệch file kiểm"
    assert sha256(out.with_suffix(".json")) == report["json_sha256"]
    assert dest.stat().st_size < 100_000_000, "ZIP vượt 100 MB, chưa sẵn sàng nộp"
    lengths = Lengths()
    n = chunks = 0
    skel = []
    with zipfile.ZipFile(dest) as z:
        names = z.namelist()
        assert names == [out.with_suffix(".json").name], f"ZIP phải chứa đúng 1 file: {names}"
        with z.open(names[0]) as f:            # đọc hết luồng → zipfile tự kiểm CRC
            for got, (exp, _) in zip(ijson.items(f, "item"), rows(c, lengths)):
                assert got == exp, f"lệch bài xuất ở câu {exp['id']}"
                n += 1
                chunks += len(got["relevant_chunks"])
                skel.append({**got, "relevant_chunks": []})
    assert n == 1200 and chunks == report["chunks_set"] + report["chunks_extra"]
    assert not submission.validate(skel, id_type=int) and submission.fingerprint(skel)[0] == report["doc_fingerprint"]
    report.update(pending_zip=False, crc_ok=True, verbatim_all_chunks=True, same_docs_and_order=True,
                  zip_bytes=dest.stat().st_size, zip_sha256=sha256(dest),
                  compression={"method": "LZMA", "dict_mib": 768, "preset": 6})
    report_p.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("VALUE_READY", json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=("build", "compress", "verify"))
    ap.add_argument("--tau", type=float, required=True)
    ap.add_argument("--scope", choices=("set", "all"), required=True)
    ap.add_argument("--tau-extra", type=float)
    ap.add_argument("--overlap", action="store_true")
    ap.add_argument("--merge", action="store_true",
                    help="(cần --cut pack) gộp 2 mảnh liền kề thành 1 chunk khi lợi hơn, π = TB ghép dòng/lưới trong T10")
    ap.add_argument("--recal", help="tag của baseline.recal_docs: dùng data/val/docs_recal_<tag>.json + recal_<tag>_scores.json")
    ap.add_argument("--cut", choices=("s5000", "pack"), default="s5000",
                    help="s5000: chia đều ≤5.000/1.860 ký tự; pack: ghép dòng tới trần 1.152 token như BTC")
    a = ap.parse_args()
    c = {"tau": a.tau, "scope": a.scope, "tau_extra": a.tau if a.tau_extra is None else a.tau_extra, "overlap": a.overlap}
    if a.cut == "pack":
        c["cut"] = "pack"
    if a.merge:
        assert a.cut == "pack", "--merge cần --cut pack"
        c["merge"] = True
    if a.recal:
        c.update(docs=f"data/val/docs_recal_{a.recal}.json", scores=f"data/val/recal_{a.recal}_scores.json",
                 prefix=f"z80{a.recal}")
    globals()[a.step](c)
