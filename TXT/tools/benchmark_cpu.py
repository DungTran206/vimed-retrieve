"""Measure the existing exact-evidence CPU kernel, never the proposed BEAR algorithm.

Run from the repository root with ``python -B -m TXT.tools.benchmark_cpu``.
Synthetic repeated texts exclude corpus I/O, structured extraction, evaluation,
and export. Their throughput is not an end-to-end runtime estimate.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import statistics
import time

from TXT.bear.adapters import ChunkRef
from TXT.bear.evidence import document_evidence
from TXT.bear.io import assert_valid_output_path, atomic_write_json
from TXT.bear.matching import ConceptRecord


def environment():
    data = {"python": platform.python_version(), "logical_threads": os.cpu_count(),
            "benchmark_threads": 1, "cpu": platform.processor(),
            "total_ram_gib": None, "available_ram_gib": None}
    if os.name != "nt":
        return data
    from ctypes import wintypes
    import winreg

    class MemoryStatus(ctypes.Structure):
        _fields_ = [("length", wintypes.DWORD), ("load", wintypes.DWORD)] + [
            (name, ctypes.c_ulonglong) for name in
            ("total_physical", "available_physical", "total_page", "available_page",
             "total_virtual", "available_virtual", "extended_virtual")]

    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        data.update(total_ram_gib=round(status.total_physical / 2**30, 2),
                    available_ram_gib=round(status.available_physical / 2**30, 2))
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            data["cpu"] = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    except OSError:
        pass
    return data


def measure(body_characters, seconds, repeats, pair_count):
    phrases = ["BRCA1", "BRCA2", "PD-1", "PD-L1", "5 mg", "type 1",
               "ung th\u01b0", "b\u1ec7nh nh\u00e2n"]
    concepts = [ConceptRecord(1, f"c{i}", phrase, phrase.lower(), [i],
                "verified_in_query", {"vi": phrase}, [], i < 2)
                for i, phrase in enumerate(phrases)]
    paragraph = ("BRCA1 BRCA10 PD-1 PD-L1 5 mg 0,5 mg type 1. "
                 "Ung th\u01b0 \u1edf b\u1ec7nh nh\u00e2n. "
                 "Evidence paragraph with clinical context and treatment response. ")
    body = (paragraph * (body_characters // len(paragraph) + 1))[:body_characters]
    refs = [ChunkRef("synthetic", "1", "synthetic", idx, idx, idx, start,
                    min(start + 1000, len(body)), "synthetic")
            for idx, start in enumerate(range(0, len(body), 1000))]
    doc = {"title": "BRCA1 treatment study", "body": body, "lang": "vi"}
    document_evidence(concepts, doc, refs)
    samples = []
    for _ in range(repeats):
        count, started = 0, time.perf_counter()
        while time.perf_counter() - started < seconds:
            document_evidence(concepts, doc, refs)
            count += 1
        elapsed = time.perf_counter() - started
        samples.append({"seconds": round(elapsed, 4), "pairs": count,
                        "pairs_per_second": round(count / elapsed, 2)})
    rate = statistics.median(row["pairs_per_second"] for row in samples)
    return {"body_characters": body_characters, "chunks_per_document": len(refs),
            "concepts_per_query": len(concepts), "samples": samples,
            "median_pairs_per_second": rate,
            "projected_kernel_minutes": round(pair_count / rate / 60, 2)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-chars", nargs="+", type=int, default=[4000, 20000, 80000])
    parser.add_argument("--sample-seconds", type=float, default=0.65)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=1200)
    parser.add_argument("--candidate-docs", type=int, default=340)
    parser.add_argument("--output", help="Optional JSON output under TXT only")
    args = parser.parse_args(argv)
    import math
    if (not math.isfinite(args.sample_seconds) or args.sample_seconds <= 0
            or min(args.body_chars + [args.repeats, args.query_count, args.candidate_docs]) <= 0):
        parser.error("Sizes, counts and sample-seconds must be finite positive values")
    output = None
    if args.output:
        output = Path(args.output).resolve()
        assert_valid_output_path(output)
    pair_count = args.query_count * args.candidate_docs
    result = {
        "scope": "legacy_exact_evidence_cpu_kernel_only",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": environment(),
        "assumptions": {"query_count": args.query_count,
                        "candidate_docs_per_query": args.candidate_docs,
                        "projected_pair_count": pair_count,
                        "repeated_synthetic_text": True, "chunk_characters": 1000,
                        "overlapping_chunks": False, "new_structured_bear": False},
        "end_to_end_runtime_estimate": None,
        "excluded": ["corpus/cache I/O", "new structured feature extraction",
                     "document/chunk selectors", "bootstrap and chunk evaluation",
                     "JSON serialization and ZIP export", "all model inference"],
        "scenarios": [measure(n, args.sample_seconds, args.repeats, pair_count)
                      for n in args.body_chars],
    }
    if output:
        atomic_write_json(output, result)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
