"""Run both BEAR parts on invented phrase fixtures, without models or real relevance labels.

    python -B -m TXT.tools.demo_bear_parts

The resulting report checks candidate scope and API wiring, never retrieval quality.
"""
import argparse
import uuid

from index.fuse import rrf
from TXT.bear.contracts import SchemaInvalidError
from TXT.bear.io import (assert_valid_output_path, atomic_write_json, read_jsonl,
                         resolve_repo_path, write_jsonl)
from TXT.bear.parts_runner import run_parts


def demo(output_dir=None):
    output_dir = output_dir or ("TXT/runtime/bear_parts/demo_" + uuid.uuid4().hex[:10])
    root = assert_valid_output_path(resolve_repo_path(output_dir))
    if root.exists():
        raise SchemaInvalidError("Choose a fresh demo directory; previous artifacts are immutable")
    root.mkdir(parents=True)
    corpus, queries = root / "corpus.jsonl", root / "queries.jsonl"
    write_jsonl(corpus, [
        {"doc_id": "a_reversed", "lang": "vi", "body": "DiseaseB treats DrugA."},
        {"doc_id": "b_supported", "lang": "vi", "body": "DrugA treats DiseaseB."},
        {"doc_id": "c_outside", "lang": "vi", "body": "DrugA treats DiseaseB. DrugA treats DiseaseB."}])
    write_jsonl(queries, [{"id": 1, "query": "DrugA treats DiseaseB", "relations": [
        {"subject": "DrugA", "predicate": "treats", "object": "DiseaseB"}]}])
    source_ranks = {1: ["a_reversed", "b_supported"]}
    source_paths = {}
    for name in ("lexical_source", "dense_source"):
        path = root / (name + ".jsonl")
        write_jsonl(path, [{"id": 1, "candidates": [
            {"doc_id": "a_reversed", "score": 100}, {"doc_id": "b_supported", "score": 1}]}])
        source_paths[name] = str(path)
    baseline = rrf([(name, source_ranks, 1) for name in source_paths], k=60, topk=2)
    baseline_path = write_jsonl(root / "rrf_control.jsonl", [{"id": 1, "candidates": [
        {"doc_id": doc_id, "score": score} for score, doc_id in baseline[1]]}])
    index_cfg = {"schema_version": 1, "corpus": str(corpus), "chunk_chars": 1200,
                 "output_dir": str(root / "index")}
    configs = {"corpus-index": index_cfg}
    common = {"schema_version": 1, "index": str(root / "index" / "index.sqlite"),
              "queries": str(queries), "top_k": 2, "languages": ["vi"]}
    configs["retrieve"] = common | {"output_dir": str(root / "retrieve")}
    configs["evidence-fuse"] = common | {"sources": source_paths, "output_dir": str(root / "fuse")}
    for command, cfg in configs.items():
        atomic_write_json(root / (command + ".json"), cfg)
        run_parts(cfg, command)
    def ids(path):
        return [item["doc_id"] for item in next(read_jsonl(path))["candidates"]]
    outputs = {"rrf_control": ids(baseline_path),
               "bear_retrieval": ids(root / "retrieve" / "candidates.jsonl"),
               "bear_fusion": ids(root / "fuse" / "candidates.jsonl")}
    checks = {"retrieval_finds_document_outside_source_union": "c_outside" in outputs["bear_retrieval"],
              "fusion_stays_in_source_union": set(outputs["bear_fusion"]) <= set(source_ranks[1]),
              "fusion_changes_rrf_order_using_explicit_relation": outputs["bear_fusion"][0] == "b_supported"}
    if not all(checks.values()):
        raise AssertionError(checks)
    report = {"evidence_level": "SYNTHETIC_ENGINEERING_SMOKE", "outputs": outputs,
              "checks": checks, "reported_baseline_0391_parity_verified": False,
              "quality_evaluated": False, "quality_gain": None,
              "note": "DrugA/DiseaseB are invented placeholders; this checks software, not medical relevance.",
              "output_dir": str(root)}
    atomic_write_json(root / "comparison.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir")
    result = demo(parser.parse_args().output_dir)
    print("Synthetic scope checks passed; report: " + result["output_dir"] + "/comparison.json")
