"""Differential compatibility tests for baseline calibration and recipe helpers against legacy code."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path

from TXT.bear.baseline import (
    build_head_hybrid,
    filter_and_refill_candidates,
    make_plan_from_calibrated_p,
    score_frozen_calibration,
)
from TXT.bear.contracts import REPO_ROOT
from TXT.bear.io import atomic_write_json, atomic_write_text, write_jsonl
from TXT.tests.fixtures import get_fixture_dir


class TestBaselineCompat(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_dir = get_fixture_dir("baseline_compat")

    def test_differential_calibration_scorer(self) -> None:
        """Run original scripts/val_calib.py --score in a fixture environment and assert exact parity."""
        # 1. Setup fixture directory structure required by scripts/val_calib.py
        data_dir = self.fixture_dir / "data"
        val_dir = data_dir / "val"
        val_dir.mkdir(parents=True, exist_ok=True)

        beta_vals = [-1.5, 0.4, 0.2, 0.8, -0.1, -0.5, 0.3, 0.1]
        atomic_write_json(val_dir / "beta.json", beta_vals)

        # Qwen scores
        qwen_file = data_dir / "qwen_all_h.jsonl"
        write_jsonl(qwen_file, [
            {"id": 1, "candidates": [{"doc_id": "d1", "score": 0.85}, {"doc_id": "d2", "score": 0.0001}]},
            {"id": 2, "candidates": [{"doc_id": "d3", "score": 0.9999}]},
        ])

        # Chunk dense scores
        chunk_dense_file = data_dir / "dense_chunk_full_rank.jsonl"
        write_jsonl(chunk_dense_file, [
            {"id": 1, "candidates": [{"doc_id": "d1", "score": 0.75}]},
            {"id": 2, "candidates": [{"doc_id": "d4", "score": 0.50}]},
        ])

        # ZH scores
        zh_vi_file = data_dir / "dense_zhC3_vi_rank.jsonl"
        write_jsonl(zh_vi_file, [
            {"id": 1, "candidates": [{"doc_id": "d5", "score": 0.60}]},
        ])
        zh_zhq_file = data_dir / "dense_zhC3_zhq_rank.jsonl"
        write_jsonl(zh_zhq_file, [
            {"id": 1, "candidates": [{"doc_id": "d5", "score": 0.65}]},
        ])

        # Corpus database with table doc(doc_id, lang)
        db_path = data_dir / "corpus_new.sqlite"
        if db_path.exists():
            db_path.unlink()
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE doc (doc_id TEXT, lang TEXT)")
        conn.executemany("INSERT INTO doc VALUES (?, ?)", [
            ("d1", "vi"),
            ("d2", "vi"),
            ("d3", "vi"),
            ("d4", "vi"),
            ("d5", "zh"),
            ("d6", "vi"),
        ])
        conn.commit()
        conn.close()

        # Candidates to score
        cands_path = self.fixture_dir / "cands.jsonl"
        write_jsonl(cands_path, [
            {"id": 1, "candidates": [{"doc_id": "d1"}, {"doc_id": "d2"}, {"doc_id": "d5"}, {"doc_id": "d6"}]},
            {"id": 2, "candidates": [{"doc_id": "d3"}, {"doc_id": "d4"}]},
        ])

        legacy_out = self.fixture_dir / "legacy_out.jsonl"
        if legacy_out.exists():
            legacy_out.unlink()

        # 2. Run original script in fixture_dir
        script_abs = (REPO_ROOT / "scripts" / "val_calib.py").resolve()
        res = subprocess.run(
            [sys.executable, "-B", str(script_abs), "--score", str(cands_path), str(legacy_out)],
            cwd=str(self.fixture_dir),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Legacy script failed: {res.stderr}")
        self.assertTrue(legacy_out.exists())

        # Read legacy outputs
        legacy_data = {}
        for line in legacy_out.read_text(encoding="utf-8").strip().splitlines():
            row = json.loads(line)
            legacy_data[row["id"]] = {c["doc_id"]: c["p"] for c in row["candidates"]}

        # 3. Run BEAR score_frozen_calibration
        source_bundle = {
            "qwen_doc_scores": {
                1: {"d1": 0.85, "d2": 0.0001},
                2: {"d3": 0.9999},
            },
            "chunk_dense": {
                1: {"d1": 0.75},
                2: {"d4": 0.50},
            },
            "zh_bge_vi": {
                1: {"d5": 0.60},
            },
            "zh_bge_zh": {
                1: {"d5": 0.65},
            },
        }
        ranking = {
            1: ["d1", "d2", "d5", "d6"],
            2: ["d3", "d4"],
        }
        doc_langs = {"d1": "vi", "d2": "vi", "d3": "vi", "d4": "vi", "d5": "zh", "d6": "vi"}

        adapter_res = score_frozen_calibration(ranking, source_bundle, beta_vals, doc_langs)

        # 4. Assert exact equality
        self.assertEqual(set(legacy_data.keys()), set(adapter_res.keys()))
        for qid, cands in adapter_res.items():
            for c in cands:
                doc = c["doc_id"]
                p_adapter = c["p"]
                p_legacy = legacy_data[qid][doc]
                self.assertEqual(
                    p_adapter,
                    p_legacy,
                    f"Mismatch at qid={qid}, doc={doc}: adapter={p_adapter} vs legacy={p_legacy}",
                )

    def test_plan_from_calibrated_p_thresholds(self) -> None:
        cands = [
            {"doc_id": "d_drop", "p": 0.0399},   # idx 0 (< 120) and p < 0.04 -> plan 0
            {"doc_id": "d_keep", "p": 0.0400},   # idx 1 (< 120) and p >= 0.04 -> no plan
        ] + [{"doc_id": f"d_{i}", "p": 0.03} for i in range(2, 120)] + [
            {"doc_id": "d_add", "p": 0.0500},    # idx 120 (>= 120) and p >= 0.05 -> plan 1
            {"doc_id": "d_not_add", "p": 0.0499},# idx 121 (>= 120) and p < 0.05 -> no plan
        ]

        plan = make_plan_from_calibrated_p(1, cands)
        self.assertEqual(plan["d_drop"], 0)
        self.assertNotIn("d_keep", plan)
        self.assertEqual(plan["d_add"], 1)
        self.assertNotIn("d_not_add", plan)

    def test_build_head_hybrid_logic(self) -> None:
        base = [f"b_{i}" for i in range(250)]
        # Alt has intersection with base and some docs outside base
        alt = [f"b_{i}" for i in range(50, 100)] + ["outside_1", "outside_2"] + [f"b_{i}" for i in range(10, 30)]
        hybrid = build_head_hybrid(base, alt, max_head=60, alt_scan=100)

        # Head should contain elements of alt that are in base[:200]
        self.assertEqual(len(hybrid), 200)
        # First elements of hybrid must come from alt
        self.assertEqual(hybrid[0], "b_50")
        self.assertEqual(hybrid[49], "b_99")
        self.assertEqual(hybrid[50], "b_10")
        # Ensure no duplicates
        self.assertEqual(len(set(hybrid)), 200)

    def test_filter_and_refill_candidates(self) -> None:
        candidates = ["c1", "c2", "c3", "c4"]
        deep_pool = ["c1", "c2", "c3", "c4", "c5", "c6", "c7"]
        eligible_ids = {"c1", "c3", "c5", "c7"}
        vinmec_ids = {"c4"}

        result = filter_and_refill_candidates(
            candidates,
            deep_pool,
            eligible_ids,
            vinmec_ids,
            target_count=4,
        )
        # c1 (eligible), c3 (eligible), c4 (vinmec), then refill c5 (eligible)
        self.assertEqual(result, ["c1", "c3", "c4", "c5"])


if __name__ == "__main__":
    unittest.main()

