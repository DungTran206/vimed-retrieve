"""Pipeline 4 bước, mỗi bước ghi file riêng nên có thể chạy lại từng bước:

  1. expand    : Qwen3.5-9B  -> thực thể y khoa + truy vấn PubMed     (expansions.jsonl)
  2. translate : Hy-MT2-7B   -> bản dịch en/zh có bảng thuật ngữ      (translations.jsonl)
  3. search    : truy vấn    -> PMID ứng viên cho từng câu hỏi        (candidates.jsonl)
  4. fetch     : PMID        -> tiêu đề + abstract                    (pubmed_corpus.jsonl)

Sau expand/translate luôn ghi queries_enriched.jsonl: bản ghi đầy đủ mỗi câu cho các bước sau.
Hai bước dùng GPU nên chạy trong hai process riêng (xem run_all.sh).
"""
import argparse
import json
import logging
import os
from pathlib import Path

from .fetch import fetch_articles
from .http import HttpClient
from .search import esearch, europepmc_search, is_pubmed_syntax

log = logging.getLogger("pubmed_module")


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def merge_hits(result_lists: list[dict], k: int = 60, max_candidates: int = 300) -> list[dict]:
    """Gộp PMID từ nhiều truy vấn/nguồn bằng Reciprocal Rank Fusion.
    result_lists: [{"src": "ncbi"/"epmc", "q": idx, "pmids": [...]}]"""
    agg: dict[str, dict] = {}
    for res in result_lists:
        for rank, pmid in enumerate(res["pmids"], start=1):
            c = agg.setdefault(pmid, {"pmid": pmid, "rrf": 0.0, "hits": []})
            c["rrf"] += 1.0 / (k + rank)
            c["hits"].append({"src": res["src"], "q": res["q"], "rank": rank})
    ranked = sorted(agg.values(), key=lambda c: -c["rrf"])
    for c in ranked:
        c["rrf"] = round(c["rrf"], 6)
    return ranked[:max_candidates]


def stage_expand(args, queries, out_dir: Path) -> list[dict]:
    from .query_gen import (LLM_CHAT_KWARGS, LLM_SAMPLING, expand_queries,
                             parse_llm_output)
    path = out_dir / "expansions.jsonl"
    if path.exists() and not args.regen:
        log.info("Dùng lại %s (thêm --regen để sinh lại)", path)
        rows = read_jsonl(path)
        # Parser được cải tiến SAU khi file đã sinh: vá lại từ `raw` đã lưu, khỏi gọi LLM
        # (1.200 câu mất ~4 giờ trên backend hf, còn vá lại thì tức thì).
        fixed = 0
        for r in rows:
            if not r.get("parse_ok") and r.get("raw"):
                again = parse_llm_output(r["raw"])
                if again["parse_ok"]:
                    r.update(again)
                    fixed += 1
        if fixed:
            write_jsonl(path, rows)
            log.info("Vá lại %d câu từ `raw` bằng parser mới (không gọi LLM)", fixed)
        return rows
    from .llm import make_backend
    backend = make_backend(args.backend, args.llm_model, LLM_SAMPLING,
                           quantization=args.quantization, load_in_4bit=args.load_in_4bit,
                           text_only=True, chat_template_kwargs=LLM_CHAT_KWARGS,
                           gpu_memory_utilization=args.gpu_mem)
    partial = path.with_suffix(".partial")
    partial.unlink(missing_ok=True)
    rows = expand_queries(backend, queries, partial_path=partial)
    write_jsonl(path, rows)
    partial.unlink(missing_ok=True)      # đã có file đầy đủ thì bỏ bản ghi dần
    bad = [r["id"] for r in rows if not r.get("parse_ok")]
    log.info("Đã sinh truy vấn cho %d câu; %d câu cần kiểm tra lại: %s", len(rows), len(bad), bad[:20])
    return rows


def stage_translate(args, expansions, out_dir: Path) -> list[dict]:
    path = out_dir / "translations.jsonl"
    if path.exists() and not args.regen:
        log.info("Dùng lại %s (thêm --regen để dịch lại)", path)
        return read_jsonl(path)
    from .llm import make_backend
    from .translate import MT_SAMPLING, MT_SAMPLING_GREEDY, translate_queries
    sampling = MT_SAMPLING_GREEDY if args.mt_greedy else MT_SAMPLING
    backend = make_backend(args.backend, args.mt_model, sampling,
                           quantization=args.quantization, load_in_4bit=args.load_in_4bit,
                           trust_remote_code=True, gpu_memory_utilization=args.gpu_mem)
    rows = translate_queries(backend, expansions, use_glossary=args.use_glossary)
    write_jsonl(path, rows)
    log.info("Đã dịch %d câu.", len(rows))
    return rows


def write_enriched(expansions, out_dir: Path):
    from .translate import enrich
    tpath = out_dir / "translations.jsonl"
    translations = read_jsonl(tpath) if tpath.exists() else None
    rows = enrich(expansions, translations)
    write_jsonl(out_dir / "queries_enriched.jsonl", rows)
    n_mt = sum(r["translation_source"] == "hy-mt2" for r in rows)
    log.info("queries_enriched.jsonl: %d câu (%d dùng bản dịch Hy-MT2).", len(rows), n_mt)


def stage_search(args, expansions, client, out_dir: Path) -> list[dict]:
    path = out_dir / "candidates.jsonl"
    rows = []
    for n, exp in enumerate(expansions, 1):
        result_lists, search_log = [], []
        for qi, term in enumerate(exp["pubmed_queries"]):
            if args.use_ncbi:
                r = esearch(client, term, retmax=args.retmax, api_key=args.api_key, email=args.email)
                result_lists.append({"src": "ncbi", "q": qi, "pmids": r["pmids"]})
                search_log.append({"src": "ncbi", "q": qi, "term": term, "count": r["count"],
                                   "n": len(r["pmids"]), "translation": r.get("translation", ""),
                                   "error": r.get("error")})
            if args.use_epmc and not is_pubmed_syntax(term):
                r = europepmc_search(client, term, page_size=args.retmax)
                result_lists.append({"src": "epmc", "q": qi, "pmids": r["pmids"]})
                search_log.append({"src": "epmc", "q": qi, "term": term, "count": r["count"],
                                   "n": len(r["pmids"]), "error": r.get("error")})
        cands = merge_hits(result_lists, max_candidates=args.max_candidates)
        rows.append({"id": exp["id"], "candidates": cands, "search_log": search_log})
        if not cands:
            log.warning("Câu %s: không tìm được PMID nào.", exp["id"])
        if n % 20 == 0:
            log.info("search: %d / %d câu", n, len(expansions))
    write_jsonl(path, rows)
    return rows


def stage_fetch(args, candidates, client, out_dir: Path):
    all_pmids = [c["pmid"] for row in candidates for c in row["candidates"]]
    articles = fetch_articles(client, client.cache, all_pmids, api_key=args.api_key, email=args.email)
    write_jsonl(out_dir / "pubmed_corpus.jsonl", articles.values())
    log.info("Corpus tiếng Anh: %d bài (từ %d PMID duy nhất)", len(articles), len(set(all_pmids)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", required=True, help="JSONL {id, query}")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stages", default="expand,search,fetch",
                    help="tập con của expand,translate,search,fetch (phân tách bằng dấu phẩy)")
    ap.add_argument("--llm-model", "--model", dest="llm_model", default="Qwen/Qwen3.5-9B")
    ap.add_argument("--mt-model", default="tencent/Hy-MT2-7B")
    ap.add_argument("--backend", choices=["vllm", "hf"], default="vllm")
    ap.add_argument("--quantization", default=None, help="vd. fp8/awq, cho vLLM")
    ap.add_argument("--load-in-4bit", action="store_true", help="cho backend hf")
    ap.add_argument("--gpu-mem", type=float, default=0.85, help="tỉ lệ VRAM vLLM được dùng")
    ap.add_argument("--no-glossary", dest="use_glossary", action="store_false",
                    help="dịch không kèm bảng thuật ngữ (để so sánh)")
    ap.add_argument("--mt-greedy", action="store_true", help="dịch bằng greedy decoding")
    ap.add_argument("--regen", action="store_true", help="chạy lại expand/translate dù đã có file")
    ap.add_argument("--retmax", type=int, default=100, help="số PMID mỗi truy vấn con")
    ap.add_argument("--max-candidates", type=int, default=300, help="số PMID giữ lại mỗi câu")
    ap.add_argument("--no-epmc", dest="use_epmc", action="store_false")
    ap.add_argument("--no-ncbi", dest="use_ncbi", action="store_false",
                    help="bỏ NCBI ESearch (IP bị chặn thì mỗi câu tốn thêm retry)")
    ap.add_argument("--api-key", default=os.environ.get("NCBI_API_KEY"))
    ap.add_argument("--email", default=os.environ.get("NCBI_EMAIL"))
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stages = set(s.strip() for s in args.stages.split(",") if s.strip())
    unknown = stages - {"expand", "translate", "search", "fetch"}
    if unknown:
        ap.error(f"stage không hợp lệ: {unknown}")

    queries = read_jsonl(args.queries)
    exp_path = out_dir / "expansions.jsonl"
    if "expand" in stages:
        expansions = stage_expand(args, queries, out_dir)
    elif exp_path.exists():
        expansions = read_jsonl(exp_path)
    else:
        ap.error(f"Chưa có {exp_path}: hãy chạy stage expand trước (hoặc tự viết file này).")

    if "translate" in stages:
        stage_translate(args, expansions, out_dir)
    write_enriched(expansions, out_dir)

    if not stages & {"search", "fetch"}:
        return
    client = HttpClient(str(out_dir / "cache.sqlite"))
    # NCBI: 3 req/s không có key, 10 req/s có key. Để dư một chút cho an toàn.
    client.add_limiter("ncbi", 9 if args.api_key else 2.5)
    client.add_limiter("epmc", 5)
    client.add_limiter("pubtator", 2.5)
    if not args.api_key:
        log.warning("Chưa có NCBI_API_KEY: ESearch sẽ chạy chậm (~3 request/giây).")

    candidates = stage_search(args, expansions, client, out_dir) if "search" in stages \
        else read_jsonl(out_dir / "candidates.jsonl")
    if "fetch" in stages:
        stage_fetch(args, candidates, client, out_dir)


if __name__ == "__main__":
    main()
