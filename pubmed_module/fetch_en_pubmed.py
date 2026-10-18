"""Lấy 240.000 bài PubMed của kho mới (cột id của parquet = doc_id; PMID trong URL) từ Europe PMC (resultType=core), có resume.
    python -m pubmed_module.fetch_en_pubmed [--limit N]    ->  data/en_pubmed.sqlite (doc_id, pmid, title, abstract, journal, year, mesh)"""
import argparse, json, re, sqlite3, threading, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
TAG = re.compile(r"<[^>]+>")


def fetch(pmids, tries=6):
    q = "SRC:MED AND (" + " OR ".join(f"EXT_ID:{p}" for p in pmids) + ")"
    qs = urllib.parse.urlencode({"query": q, "format": "json", "resultType": "core", "pageSize": 100})
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{URL}?{qs}", headers={"User-Agent": "vimed-research/1.0"}), timeout=60) as r:
                return json.loads(r.read().decode("utf-8")).get("resultList", {}).get("result", [])
        except Exception as e:
            time.sleep(2 ** t)
    return None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int); ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--db", default="data/en_pubmed.sqlite"); ap.add_argument("--batch", type=int, default=80)
    a = ap.parse_args()
    N = pd.read_parquet("data/vibiomir_new/links_corpus_vi_en_zh.parquet")
    N = N[N.url.str.contains("pubmed.ncbi.nlm.nih.gov")].copy()
    N["pmid"] = N.url.str.extract(r"/(\d+)/?$")[0]
    N = N.dropna(subset=["pmid"])
    if a.limit: N = N.head(a.limit)
    conn = sqlite3.connect(a.db, check_same_thread=False)
    conn.execute("create table if not exists doc(doc_id text primary key, pmid text, title text, abstract text, journal text, year text, mesh text, found int)")
    done = {r[0] for r in conn.execute("select pmid from doc")}
    todo = [(r.id, r.pmid) for r in N.itertuples() if r.pmid not in done]
    print(f"PubMed trong kho mới: {len(N):,} | đã có {len(done):,} | cần lấy {len(todo):,}", flush=True)
    lock = threading.Lock(); stats = {"ok": 0, "miss": 0, "fail": 0, "n": 0}; t0 = time.time()
    id_of = {p: i for i, p in todo}
    batches = [[p for _, p in todo[i:i + a.batch]] for i in range(0, len(todo), a.batch)]

    def work(b):
        res = fetch(b)
        rows = []
        if res is None:
            with lock: stats["fail"] += len(b); stats["n"] += 1
            return
        got = {}
        for r in res:
            pm = str(r.get("pmid") or r.get("id") or "")
            if pm in id_of:
                mesh = "; ".join(m.get("descriptorName", "") for m in (r.get("meshHeadingList", {}) or {}).get("meshHeading", []))
                got[pm] = (id_of[pm], pm, TAG.sub("", r.get("title") or "").strip(), TAG.sub("", r.get("abstractText") or "").strip(),
                           ((r.get("journalInfo") or {}).get("journal") or {}).get("title") or r.get("journalTitle") or "", str(r.get("pubYear") or ""), mesh, 1)
        for p in b:
            rows.append(got.get(p) or (id_of[p], p, "", "", "", "", "", 0))
        with lock:
            conn.executemany("insert or replace into doc values (?,?,?,?,?,?,?,?)", rows); conn.commit()
            stats["ok"] += len(got); stats["miss"] += len(b) - len(got); stats["n"] += 1
            if stats["n"] % 20 == 0:
                print(f"{stats['n']}/{len(batches)} lô | có {stats['ok']:,} | không thấy {stats['miss']:,} | lỗi {stats['fail']:,} | {time.time() - t0:.0f}s", flush=True)

    with ThreadPoolExecutor(a.workers) as ex: list(ex.map(work, batches))
    print("EN_FETCH_DONE", stats, flush=True)


if __name__ == "__main__":
    main()
