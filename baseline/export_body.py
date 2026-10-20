"""Baseline GỌN — bước 4: bài nộp, mỗi doc đúng 1 chunk = body[:10000] (nguyên văn), nén LZMA từ điển lớn.

Ghi JSON theo luồng (không giữ 1,1 GB trong RAM), nén ra .zip.part rồi mới đổi tên (không bao giờ có ZIP dở mang tên thật).
doc_id là SỐ NGUYÊN (chuỗi → chấm 0). Doc body rỗng: vẫn trong relevant_docs, không có chunk.
  python -m baseline.export_body data/val/docs_clean160.json runs/clean160_body
"""
import json
import os
import sqlite3
import sys
import zipfile

from submit import submission


def write_json(docs_path, out, max_chars=10000):
    D = {int(q): v for q, v in json.load(open(docs_path)).items()}
    assert len(D) == 1200, "thiếu câu"
    c = sqlite3.connect("file:data/corpus_new.sqlite?mode=ro", uri=True)
    n = 0
    with open(out, "w", encoding="utf-8") as f:
        f.write("[")
        for j, q in enumerate(sorted(D)):
            ds = [str(d) for d in D[q]]
            body = {}
            for i in range(0, len(ds), 900):
                p = ds[i:i + 900]
                body.update(dict(c.execute(f"SELECT doc_id, body FROM doc WHERE doc_id IN ({','.join('?' * len(p))})", p)))
            rec = {"id": q, "relevant_docs": [int(d) for d in ds],
                   "relevant_chunks": [{"doc_id": int(d), "chunk_text": body[d][:max_chars]} for d in ds if (body.get(d) or "").strip()]}
            n += len(rec["relevant_chunks"])
            f.write(("," if j else "") + json.dumps(rec, ensure_ascii=False, separators=(",", ":")))
        f.write("]")
    print(f"-> {out} · {n / len(D):.1f} chunk/câu")


def zip_lzma(js, zp):
    orig = zipfile.LZMACompressor
    zipfile.LZMACompressor = submission._BigLZMA     # từ điển 768 MB: thấy được chunk lặp giữa các câu (1,1 GB → ~96 MB)
    try:
        with zipfile.ZipFile(zp + ".part", "w", zipfile.ZIP_LZMA) as z:
            z.write(js, arcname=os.path.basename(js))
    finally:
        zipfile.LZMACompressor = orig
    with zipfile.ZipFile(zp + ".part") as z:
        assert z.namelist() == [os.path.basename(js)] and z.testzip() is None
    os.replace(zp + ".part", zp)
    print(f"-> {zp} · {os.path.getsize(zp) / 2 ** 20:.1f} MB")


if __name__ == "__main__":
    docs, out = sys.argv[1], sys.argv[2]
    write_json(docs, out + ".json")
    zip_lzma(out + ".json", out + ".zip")
