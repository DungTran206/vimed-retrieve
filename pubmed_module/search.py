"""Tìm PMID qua NCBI ESearch và Europe PMC (giới hạn ở nguồn MED = PubMed)."""
import json
import logging

from .http import HttpClient

log = logging.getLogger(__name__)

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EPMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def esearch(client: HttpClient, term: str, retmax: int = 100,
            api_key: str | None = None, email: str | None = None) -> dict:
    """Trả về {"pmids": [...], "count": int, "translation": str}. Lỗi -> danh sách rỗng."""
    params = {
        "db": "pubmed",
        "term": term,
        "retmax": retmax,
        "retmode": "json",
        "sort": "relevance",  # Best Match
        "tool": "vimed-retrieval",
    }
    if api_key:
        params["api_key"] = api_key
    if email:
        params["email"] = email
    try:
        data = json.loads(client.get_text(ESEARCH_URL, params, limiter="ncbi"))
    except Exception as e:  # mạng lỗi, JSON hỏng...
        log.warning("ESearch lỗi với '%s': %s", term, e)
        return {"pmids": [], "count": 0, "translation": "", "error": str(e)}
    r = data.get("esearchresult", {})
    out = {
        "pmids": [str(p) for p in r.get("idlist", [])],
        "count": int(r.get("count", 0) or 0),
        # Cách PubMed thực sự hiểu truy vấn (hữu ích để debug MeSH mapping)
        "translation": r.get("querytranslation", ""),
    }
    if "ERROR" in r or "errorlist" in r:
        out["error"] = r.get("ERROR") or r.get("errorlist")
    return out


def is_pubmed_syntax(term: str) -> bool:
    """Truy vấn có field tag kiểu PubMed ([MeSH Terms], [tiab]...) thì không gửi sang Europe PMC,
    vì Europe PMC dùng cú pháp khác."""
    return "[" in term and "]" in term


def europepmc_search(client: HttpClient, term: str, page_size: int = 100) -> dict:
    params = {
        "query": f"SRC:MED AND ({term})",
        "format": "json",
        "pageSize": min(page_size, 1000),
        "resultType": "lite",
    }
    try:
        data = json.loads(client.get_text(EPMC_URL, params, limiter="epmc"))
    except Exception as e:
        log.warning("Europe PMC lỗi với '%s': %s", term, e)
        return {"pmids": [], "count": 0, "error": str(e)}
    results = data.get("resultList", {}).get("result", [])
    pmids = [str(x["pmid"]) for x in results if x.get("source") == "MED" and x.get("pmid")]
    return {"pmids": pmids, "count": int(data.get("hitCount", 0) or 0)}
