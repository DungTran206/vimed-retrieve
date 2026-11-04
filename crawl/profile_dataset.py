"""Tải ViBioMIR, xuất câu hỏi JSONL cho query_processing, và thống kê danh sách URL
để lên kế hoạch crawl. Không cần GPU.

  pip install pandas pyarrow huggingface_hub
  python profile_dataset.py            # kết quả trong thư mục data/
"""
import collections
import json
import os
import urllib.parse

import pandas as pd
from huggingface_hub import hf_hub_download

REPO = "AIGuruTinix/ViBioMIR"
REV = "71be0e1239a19dfd7a717e2bc13e3bec21bd0334"   # bản HF dùng cho bài nộp (1.220.598 URL)
OUT = "data"
os.makedirs(OUT, exist_ok=True)


def load(name):
    return pd.read_parquet(hf_hub_download(REPO, name, repo_type="dataset", revision=REV))


def domain(url: str) -> str:
    try:
        host = urllib.parse.urlsplit(url.strip()).netloc.lower().split("@")[-1].split(":")[0]
    except ValueError:
        return "<invalid>"
    return host[4:] if host.startswith("www.") else (host or "<empty>")


def extension(url: str) -> str:
    path = urllib.parse.urlsplit(url).path.lower()
    last = path.rsplit("/", 1)[-1]
    return last.rsplit(".", 1)[-1] if "." in last and len(last.rsplit(".", 1)[-1]) <= 5 else "<none>"


print("=" * 70, "\nQUERIES")
q = load("query.parquet")
words = q["query"].str.split().str.len()
print(f"Số câu: {len(q)} | id {q['id'].min()}–{q['id'].max()} | id trùng: {q['id'].duplicated().sum()}")
print(f"Số từ: min {words.min()}, trung vị {words.median():.0f}, P95 {words.quantile(.95):.0f}, max {words.max()}")
with open(f"{OUT}/queries.jsonl", "w", encoding="utf-8") as f:
    for r in q.itertuples():
        f.write(json.dumps({"id": int(r.id), "query": r.query}, ensure_ascii=False) + "\n")
print(f"Đã ghi {OUT}/queries.jsonl")
print("Ví dụ:")
for r in q.sample(5, random_state=0).itertuples():
    print(f"  [{r.id}] {r.query[:150]}")

print("=" * 70, "\nCORPUS (danh sách URL)")
c = load("links_corpus_vi_en_zh.parquet")
ids = c["id"]
print(f"Số dòng: {len(c):,} | id {ids.min():,}–{ids.max():,} | id duy nhất: {ids.nunique():,}")
print(f"Số id bị thiếu trong khoảng: {ids.max() - ids.min() + 1 - ids.nunique():,}")
print(f"URL trùng nhau: {c['url'].duplicated().sum():,}")
c["domain"] = c["url"].map(domain)
c["ext"] = c["url"].map(extension)
c["scheme"] = c["url"].str.split(":", n=1).str[0].str.lower()

dom = c["domain"].value_counts()
cum = dom.cumsum() / len(c)
print(f"\nSố domain: {len(dom):,}")
for p in (0.5, 0.8, 0.9, 0.95, 0.99):
    print(f"  {int(p*100)}% URL nằm trong {int((cum < p).sum()) + 1} domain đầu")
print("\nTop 40 domain:")
for d, n in dom.head(40).items():
    print(f"  {n:>10,}  {cum[d]*100:5.1f}%  {d}")

tld = c["domain"].str.rsplit(".", n=1).str[-1].value_counts()
print("\nTLD:", {k: int(v) for k, v in tld.head(12).items()})
print("Scheme:", {k: int(v) for k, v in c["scheme"].value_counts().items()})
print("Đuôi file:", {k: int(v) for k, v in c["ext"].value_counts().head(12).items()})

# Lưu thống kê + mẫu URL mỗi domain lớn để viết parser riêng
dom.rename("count").to_frame().assign(cum_pct=(cum * 100).round(2)).to_csv(f"{OUT}/domain_stats.csv")
samples = {d: c.loc[c["domain"] == d, "url"].sample(min(3, n), random_state=0).tolist()
           for d, n in dom.head(40).items()}
with open(f"{OUT}/domain_samples.json", "w", encoding="utf-8") as f:
    json.dump(samples, f, ensure_ascii=False, indent=1)
print(f"\nĐã ghi {OUT}/domain_stats.csv và {OUT}/domain_samples.json")

print("=" * 70, "\nƯỚC LƯỢNG THỜI GIAN CRAWL TOÀN BỘ")
for rate in (5, 20, 50, 100):
    print(f"  {rate:>3} trang/giây tổng  →  {len(c) / rate / 3600:6.1f} giờ")
