"""Integration checks for cache replay, score provenance and validation isolation."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from TXT.bear.contracts import HashMismatchError, RUNTIME_DIR, SchemaInvalidError
from TXT.bear.io import atomic_write_json, read_json, read_jsonl, write_jsonl
from TXT.bear.medical_runner import inspect_experiment, run_experiment
from TXT.tools.demo_medical_hypothesis import run_demo


class TestMedicalRunner(unittest.TestCase):
    def setUp(self):
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="medical_runner_test_", dir=RUNTIME_DIR)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _demo(self):
        root = self.root / "demo"
        result = run_demo(str(root))
        self.assertTrue(result["synthetic_only"])
        self.assertFalse(result["real_model_called"])
        self.assertFalse(result["quality_gain_established"])
        self.assertEqual(12, result["query_count"])
        return root

    def test_end_to_end_replay_is_model_free_and_reuses_stages(self):
        with patch("TXT.bear.medical_query._chat", side_effect=AssertionError("offline replay called a model")):
            root = self._demo()
            second = run_demo(str(root))
        self.assertTrue(all(stage["reused"] for stage in second["stages"].values()))
        split = read_json(root / "fit" / "splits.json")
        self.assertFalse(set(split["calibration"]) & set(split["tune"]))
        self.assertFalse(set(split["calibration"]) & set(split["holdout"]))
        for row in read_jsonl(root / "run" / "candidates.jsonl"):
            self.assertLessEqual(len(row["candidates"]), 3)
            self.assertTrue(all(0 <= item["score"] <= 1 for item in row["candidates"]))

    def test_external_partial_bm25_table_never_uses_index_fallback(self):
        root = self._demo()
        table = write_jsonl(self.root / "external_bm25.jsonl", [{"id": 1, "doc_id": "11", "score": 0.0}])
        config = read_json(root / "configs" / "cache.json")
        config.update(score_tables={"bm25": str(table)}, output_dir=str(self.root / "external_cache"))
        run_experiment("cache", config)
        record = next(read_jsonl(self.root / "external_cache" / "cache.jsonl"))
        docs = {candidate["doc_id"]: candidate for candidate in record["candidates"]}
        self.assertEqual(0.0, docs["11"]["scores"]["bm25"])
        self.assertIsNone(docs["12"]["scores"]["bm25"])
        self.assertIsNone(docs["11"]["scores"]["bm25_expanded"])
        self.assertFalse(record["query_scale_compatible"])
        self.assertEqual("source_artifact", record["bm25_recipe"])

    def test_changed_split_cannot_relabel_fit_queries_as_tune(self):
        root = self._demo()
        split = read_json(root / "fit" / "splits.json")
        split["calibration"], split["tune"] = split["tune"], split["calibration"]
        split_path = atomic_write_json(self.root / "bad_split.json", split)
        config = read_json(root / "configs" / "tune.json")
        config.update(split_path=str(split_path), output_dir=str(self.root / "bad_tune"))
        with self.assertRaisesRegex(SchemaInvalidError, "split differs"):
            run_experiment("tune", config)

    def test_artifact_tampering_is_detected_before_replay(self):
        root = self._demo()
        scores_path = root / "run" / "scores.jsonl"
        with scores_path.open("a", encoding="utf-8") as handle:
            handle.write("\n")
        config = read_json(root / "configs" / "run.json")
        with self.assertRaises(HashMismatchError):
            run_experiment("run", config)

    def test_document_terms_stage_resumes_per_document(self):
        root = self._demo()
        ids = atomic_write_json(self.root / "doc_ids.json", ["11"])
        config = {"schema_version": 1, "index": str(root / "synthetic_inputs" / "index.sqlite"),
                  "doc_ids_path": str(ids), "llm": {"model": "Qwen/Qwen3.5-9B", "num_parameters_b": 9},
                  "output_dir": str(self.root / "document_terms")}
        record = {"doc_id": "11", "terms": [], "scope": "diagnostic_term_candidates_only"}
        with patch("TXT.bear.medical_documents.extract_document", return_value=record) as model:
            first = run_experiment("document-terms", config)
            second = run_experiment("document-terms", config)
        self.assertEqual(1, model.call_count)
        self.assertEqual(1, first["document_count"])
        self.assertTrue(second["reused"])
        self.assertFalse(first["index_modified"])

    def test_prepare_dry_run_knows_both_actual_prompt_inputs(self):
        config = {"schema_version": 1, "queries": "TXT/inputs/definitely_missing_queries.jsonl",
                  "kb": "TXT/inputs/definitely_missing_kb.jsonl", "llm": {},
                  "output_dir": str(self.root / "preflight")}
        result = inspect_experiment("prepare", config)
        self.assertEqual(["queries", "kb"], result["missing_roles"])
        self.assertFalse(result["model_contacted"])


if __name__ == "__main__":
    unittest.main()
