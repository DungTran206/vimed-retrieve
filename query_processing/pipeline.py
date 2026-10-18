"""Điều phối các bước xử lý truy vấn đa ngôn ngữ, không gọi API ngoài."""
import argparse
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def stage_expand(args, queries, out_dir: Path):
    from .expand import LLM_CHAT_KWARGS, LLM_SAMPLING, expand_queries, parse_llm_output

    path = out_dir / "expansions.jsonl"
    if path.exists() and not args.regen:
        rows = read_jsonl(path)
        fixed = 0
        changed = False
        for row in rows:
            if "pubmed_queries" in row:
                row.pop("pubmed_queries")
                changed = True
            if not row.get("parse_ok") and row.get("raw"):
                parsed = parse_llm_output(row["raw"])
                if parsed["parse_ok"]:
                    row.update(parsed)
                    fixed += 1
        if fixed or changed:
            write_jsonl(path, rows)
            log.info("Cập nhật expansions: khôi phục %d câu, bỏ trường PubMed cũ", fixed)
        return rows

    from .llm import make_backend

    backend = make_backend(
        args.backend,
        args.llm_model,
        LLM_SAMPLING,
        quantization=args.quantization,
        load_in_4bit=args.load_in_4bit,
        text_only=True,
        chat_template_kwargs=LLM_CHAT_KWARGS,
        gpu_memory_utilization=args.gpu_mem,
    )
    partial = path.with_suffix(".partial")
    partial.unlink(missing_ok=True)
    rows = expand_queries(backend, queries, partial_path=partial)
    write_jsonl(path, rows)
    partial.unlink(missing_ok=True)
    return rows


def stage_translate(args, expansions, out_dir: Path):
    path = out_dir / "translations.jsonl"
    if path.exists() and not args.regen:
        return read_jsonl(path)

    from .llm import make_backend
    from .translate import MT_SAMPLING, MT_SAMPLING_GREEDY, translate_queries

    sampling = MT_SAMPLING_GREEDY if args.mt_greedy else MT_SAMPLING
    backend = make_backend(
        args.backend,
        args.mt_model,
        sampling,
        quantization=args.quantization,
        load_in_4bit=args.load_in_4bit,
        trust_remote_code=True,
        gpu_memory_utilization=args.gpu_mem,
    )
    rows = translate_queries(backend, expansions, use_glossary=args.use_glossary)
    write_jsonl(path, rows)
    return rows


def write_enriched(expansions, out_dir: Path):
    from .translate import enrich

    path = out_dir / "translations.jsonl"
    translations = read_jsonl(path) if path.exists() else None
    rows = enrich(expansions, translations)
    write_jsonl(out_dir / "queries_enriched.jsonl", rows)
    return rows


def main():
    parser = argparse.ArgumentParser(description="Xử lý câu hỏi và dịch đa ngôn ngữ")
    parser.add_argument("--queries", required=True, help="JSONL chứa {id, query}")
    parser.add_argument("--out", required=True, help="thư mục đầu ra")
    parser.add_argument("--stages", default="expand,translate",
                        help="chọn expand,translate; phân tách bằng dấu phẩy")
    parser.add_argument("--llm-model", default="Qwen/Qwen3.5-9B")
    parser.add_argument("--mt-model", default="tencent/Hy-MT2-7B")
    parser.add_argument("--backend", choices=["vllm", "hf"], default="vllm")
    parser.add_argument("--quantization", default=None)
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--gpu-mem", type=float, default=0.85)
    parser.add_argument("--no-glossary", dest="use_glossary", action="store_false")
    parser.add_argument("--mt-greedy", action="store_true")
    parser.add_argument("--regen", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stages = {stage.strip() for stage in args.stages.split(",") if stage.strip()}
    unknown = stages - {"expand", "translate"}
    if unknown:
        parser.error(f"stage không hợp lệ: {sorted(unknown)}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    queries = read_jsonl(args.queries)
    expansions_path = out_dir / "expansions.jsonl"
    if "expand" in stages:
        expansions = stage_expand(args, queries, out_dir)
    elif expansions_path.exists():
        expansions = read_jsonl(expansions_path)
    else:
        parser.error(f"Chưa có {expansions_path}; hãy chạy stage expand trước.")

    if "translate" in stages:
        stage_translate(args, expansions, out_dir)
    enriched = write_enriched(expansions, out_dir)
    log.info("Đã ghi %d câu vào %s", len(enriched), out_dir / "queries_enriched.jsonl")


if __name__ == "__main__":
    main()
