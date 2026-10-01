"""Lấy tiêu đề + abstract theo PMID.

Chuỗi dự phòng: PubTator -> NCBI EFetch -> **Europe PMC**.

Hai nguồn đầu đều thuộc NCBI. Đo ngày 01/10/2026: NCBI **chặn ở tầng IP** từ máy này
(mọi endpoint trả HTTP 200 nhưng redirect sang misuse.ncbi.nlm.nih.gov/error/abuse.shtml,
UA browser cũng không thoát) → PubTator và EFetch cùng trả 0 bài. Europe PMC
(`resultType=core`) vẫn chạy tốt và trả cả title lẫn abstract, nên nó là nguồn
thực tế đang dùng. Giữ hai nguồn NCBI vì chúng hoạt động khi có API key hoặc IP khác.
"""
import json
import logging
import re
import xml.etree.ElementTree as ET

from .http import HttpClient, KVStore

log = logging.getLogger(__name__)

PUBTATOR_URLS = [
    "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson",
    "https://www.ncbi.nlm.nih.gov/research/pubtator-api/publications/export/biocjson",  # URL trong đề
]
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
EPMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def parse_biocjson(text: str) -> dict[str, dict]:
    """Chấp nhận cả 3 dạng: {"PubTator3": [...]}, một list JSON, hoặc JSON-lines."""
    text = (text or "").strip()
    if not text:
        return {}
    docs = []
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            docs = obj
        elif isinstance(obj, dict):
            docs = obj.get("PubTator3") or obj.get("documents") or ([obj] if "passages" in obj else [])
    except json.JSONDecodeError:
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    docs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    out = {}
    for d in docs:
        pmid = str(d.get("pmid") or d.get("id") or "").strip()
        titles, abstracts = [], []
        for p in d.get("passages", []):
            ptype = str((p.get("infons") or {}).get("type", "")).lower()
            txt = (p.get("text") or "").strip()
            if not txt:
                continue
            if ptype in ("title", "front"):
                titles.append(txt)
            elif ptype.startswith("abstract"):
                abstracts.append(txt)
        if pmid and (titles or abstracts):
            out[pmid] = {
                "pmid": pmid,
                "title": " ".join(titles),
                "abstract": "\n".join(abstracts),
                "source": "pubtator",
            }
    return out


def parse_efetch_xml(text: str) -> dict[str, dict]:
    out = {}
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        log.warning("EFetch XML lỗi: %s", e)
        return out
    for art in root.iter("PubmedArticle"):
        pmid = (art.findtext("./MedlineCitation/PMID") or "").strip()
        title_el = art.find(".//Article/ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else ""
        parts = []
        for at in art.findall(".//Article/Abstract/AbstractText"):
            txt = "".join(at.itertext()).strip()
            if not txt:
                continue
            label = at.get("Label")
            parts.append(f"{label}: {txt}" if label else txt)
        if pmid and (title or parts):
            out[pmid] = {"pmid": pmid, "title": title, "abstract": "\n".join(parts), "source": "efetch"}
    return out


def pubtator_fetch(client: HttpClient, pmids: list[str]) -> dict[str, dict]:
    for url in PUBTATOR_URLS:
        try:
            text = client.get_text(url, {"pmids": ",".join(pmids)}, limiter="pubtator", use_cache=False)
            got = parse_biocjson(text)
            if got:
                return got
        except Exception as e:
            log.warning("PubTator lỗi (%s): %s", url, e)
    return {}


def efetch(client: HttpClient, pmids: list[str], api_key: str | None = None,
           email: str | None = None) -> dict[str, dict]:
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "rettype": "abstract",
              "tool": "vimed-retrieval"}
    if api_key:
        params["api_key"] = api_key
    if email:
        params["email"] = email
    try:
        return parse_efetch_xml(client.get_text(EFETCH_URL, params, limiter="ncbi", use_cache=False))
    except Exception as e:
        log.warning("EFetch lỗi: %s", e)
        return {}


def strip_tags(s: str) -> str:
    """Abstract của Europe PMC có chèn thẻ tiêu đề mục (<h4>Objectives</h4>).

    Bỏ thẻ, giữ nguyên chữ - giống như trích text từ HTML ở phần crawl. Không viết lại gì,
    vì `chunk_text` phải nguyên văn.
    """
    return re.sub(r"\s+\n", "\n", re.sub(r"<[^>]+>", "\n", s or "")).strip()


def epmc_fetch(client: HttpClient, pmids: list[str]) -> dict[str, dict]:
    """Lấy title + abstract theo PMID từ Europe PMC (nguồn MED = PubMed).

    Dùng được khi NCBI chặn IP. Batch nhỏ hơn hai nguồn kia vì PMID nằm trong query string.
    """
    out = {}
    for batch in _chunks(pmids, 25):
        q = " OR ".join(f"EXT_ID:{p}" for p in batch)
        params = {"query": f"SRC:MED AND ({q})", "format": "json",
                  "pageSize": len(batch), "resultType": "core"}
        try:
            data = json.loads(client.get_text(EPMC_URL, params, limiter="epmc"))
        except Exception as e:
            log.warning("Europe PMC fetch lỗi: %s", e)
            continue
        for it in data.get("resultList", {}).get("result", []):
            pmid = str(it.get("pmid") or "").strip()
            title = (it.get("title") or "").strip()
            abstract = strip_tags(it.get("abstractText"))
            if pmid and (title or abstract):
                out[pmid] = {"pmid": pmid, "title": title, "abstract": abstract,
                             "source": "europepmc"}
    return out


def fetch_articles(client: HttpClient, store: KVStore, pmids: list[str], batch_size: int = 100,
                   api_key: str | None = None, email: str | None = None) -> dict[str, dict]:
    """Lấy bài, lưu từng bài vào store để lần chạy sau không tải lại."""
    uniq = list(dict.fromkeys(str(p) for p in pmids))
    need = [p for p in uniq if store.get(f"article:{p}") is None]
    log.info("Cần tải %d / %d PMID", len(need), len(uniq))

    for i, batch in enumerate(_chunks(need, batch_size)):
        got = pubtator_fetch(client, batch)
        missing = [p for p in batch if p not in got]
        if missing:
            got.update(efetch(client, missing, api_key, email))
        # Cả hai nguồn trên đều của NCBI; nếu NCBI chặn IP thì Europe PMC gánh toàn bộ
        missing = [p for p in batch if p not in got]
        if missing:
            got.update(epmc_fetch(client, missing))
        for pmid, art in got.items():
            store.set(f"article:{pmid}", json.dumps(art, ensure_ascii=False))
        still = [p for p in batch if p not in got]
        if still:
            log.info("Batch %d: %d PMID không có nội dung (vd. %s)", i, len(still), still[:3])

    out = {}
    for p in uniq:
        raw = store.get(f"article:{p}")
        if raw:
            out[p] = json.loads(raw)
    return out
