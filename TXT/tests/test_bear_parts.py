"""Two separate candidate stages on synthetic corpora; these are not quality gains."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from index.fuse import load, rrf
from TXT.bear.adapters import read_rank_source
from TXT.bear.artifacts import verify_manifest
from TXT.bear.config import validate_config
from TXT.bear.contracts import (HashMismatchError, InputMissingError, SchemaInvalidError,
                                TXT_DIR, REPO_ROOT)
from TXT.bear.corpus_index import CorpusIndex, build_index
from TXT.bear.evidence_fusion import BearFusion
from TXT.bear.io import atomic_write_json, read_json, read_jsonl, sha256_file, write_jsonl
from TXT.bear.parts_runner import inspect_parts, run_parts
from TXT.bear.retrieval import BearRetriever


class TestBearParts(unittest.TestCase):
    def setUp(self):
        parent = TXT_DIR / "runtime" / "tmp"
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="parts_", dir=parent)
        self.root = Path(self.temp.name)
        self.corpus = self.root / "corpus.jsonl"
        write_jsonl(self.corpus, [
            {"doc_id": "a", "lang": "vi", "body": "DiseaseB treats DrugA."},
            {"doc_id": "b", "lang": "vi", "body": "DrugA treats DiseaseB."},
            {"doc_id": "outside", "lang": "vi", "body": "DrugA treats DiseaseB. DrugA treats DiseaseB."},
            {"doc_id": "en", "lang": "en", "body": "DrugA treats DiseaseB."}])
        self.query = {"id": 1, "query": "DrugA treats DiseaseB", "relations": [
            {"subject": "DrugA", "predicate": "treats", "object": "DiseaseB"}]}
        self.queries = self.root / "queries.jsonl"
        write_jsonl(self.queries, [self.query])
        self.index = self.root / "index.sqlite"
        build_index(self.corpus, self.index)
        self.source = self.root / "source.jsonl"
        write_jsonl(self.source, [{"id": 1, "candidates": [
            {"doc_id": "a", "score": 100}, {"doc_id": "b", "score": 1}]}])

    def tearDown(self):
        assert self.root.resolve().is_relative_to((TXT_DIR / "runtime" / "tmp").resolve())
        self.temp.cleanup()

    def config(self, command):
        cfg = {"schema_version": 1, "index": str(self.index), "queries": str(self.queries),
               "top_k": 3, "languages": ["vi"], "output_dir": str(self.root / command)}
        if command == "evidence-fuse":
            cfg["sources"] = {"a": str(self.source), "b": str(self.source)}
        return cfg

    def test_retrieval_and_fusion_have_different_candidate_scopes(self):
        with CorpusIndex(self.index) as index:
            retrieved = BearRetriever(index).retrieve(self.query, top_k=3, languages=["vi"])
            fused = BearFusion(index).fuse(self.query, {"a": ["a", "b"], "b": ["a", "b"]}, top_k=3)
        self.assertIn("outside", {row["doc_id"] for row in retrieved})
        self.assertEqual({row["doc_id"] for row in fused}, {"a", "b"})
        self.assertEqual(fused[0]["doc_id"], "b")
        control = rrf([("a", {1: ["a", "b"]}, 1), ("b", {1: ["a", "b"]}, 1)])
        self.assertEqual(control[1][0][1], "a")

    def test_source_score_and_order_are_provenance_not_fusion_features(self):
        with CorpusIndex(self.index) as index:
            fusion = BearFusion(index)
            first = fusion.fuse(self.query, {"one": [{"doc_id": "a", "score": 1e9}, "b"]})
            second = fusion.fuse(self.query, {"renamed": ["b", {"doc_id": "a", "score": -100}]})
        self.assertEqual([(r["doc_id"], r["score"]) for r in first],
                         [(r["doc_id"], r["score"]) for r in second])

    def test_runner_outputs_roundtrip_and_completed_runs_are_immutable(self):
        before = sha256_file(self.corpus)
        for command in ("retrieve", "evidence-fuse"):
            cfg = self.config(command)
            validate_config(cfg, command)
            self.assertEqual(inspect_parts(cfg, command)["status"], "inputs_present_unverified")
            result = run_parts(cfg, command)
            self.assertFalse(result["quality_evaluated"])
            self.assertEqual(result, run_parts(cfg, command))
            root = Path(cfg["output_dir"])
            self.assertEqual(list(load(root / "candidates.jsonl")), [1])
            self.assertEqual(next(read_rank_source(root / "candidates.jsonl")).query_id, 1)
            self.assertTrue(list(read_jsonl(root / "evidence.jsonl")))
            verify_manifest(root / "manifest.json")
            with self.assertRaises(HashMismatchError):
                run_parts(cfg | {"top_k": 1}, command)
        self.assertEqual(sha256_file(self.corpus), before)

    def test_missing_source_queries_and_unknown_documents_fail(self):
        with CorpusIndex(self.index) as index:
            fusion = BearFusion(index)
            with self.assertRaises(InputMissingError):
                fusion.fuse(self.query, {"one": ["unknown"]})
            with self.assertRaises(SchemaInvalidError):
                fusion.fuse(self.query, {"one": ["a", "a"]})
        write_jsonl(self.source, [{"id": 2, "candidates": []}])
        with self.assertRaises(SchemaInvalidError):
            run_parts(self.config("evidence-fuse"), "evidence-fuse")

    def test_empty_source_is_distinct_from_absent_query(self):
        write_jsonl(self.source, [{"id": 1, "candidates": []}])
        cfg = self.config("evidence-fuse")
        run_parts(cfg, "evidence-fuse")
        self.assertEqual(next(read_jsonl(Path(cfg["output_dir"]) / "candidates.jsonl"))["candidates"], [])

    def test_malformed_source_row_is_not_silently_an_empty_ranking(self):
        for number, row in enumerate(({"id": 1}, {"id": 1, "candidates": None},
                                      {"id": 1, "candidates": [], "docs": []})):
            write_jsonl(self.source, [row])
            with self.assertRaises(SchemaInvalidError):
                run_parts(self.config("evidence-fuse") | {"output_dir": str(self.root / f"bad-source-{number}")},
                          "evidence-fuse")

    def test_repo_relative_corpus_path_works_outside_repo(self):
        cfg = {"schema_version": 1, "corpus": str(self.corpus.relative_to(REPO_ROOT)),
               "output_dir": str(self.root / "cwd-index")}
        original = os.getcwd()
        try:
            os.chdir(self.root)
            result = run_parts(cfg, "corpus-index")
        finally:
            os.chdir(original)
        self.assertEqual(result["status"], "completed")

    def test_interrupted_index_run_rebuilds_only_its_bound_partial_artifact(self):
        cfg = {"schema_version": 1, "corpus": str(self.corpus),
               "output_dir": str(self.root / "resumable-index")}
        run_parts(cfg, "corpus-index")
        manifest_path = Path(cfg["output_dir"]) / "manifest.json"
        partial = read_json(manifest_path) | {"status": "partial", "artifacts": []}
        atomic_write_json(manifest_path, partial)
        result = run_parts(cfg, "corpus-index")
        self.assertEqual(result["status"], "completed")
        verify_manifest(manifest_path)

    def test_index_builder_preserves_existing_unbound_file(self):
        root = self.root / "unbound-index"
        root.mkdir()
        target = root / "index.sqlite"
        target.write_bytes(b'preserve this unrelated file')
        cfg = {"schema_version": 1, "corpus": str(self.corpus), "output_dir": str(root)}
        for _ in range(2):
            with self.assertRaises(FileExistsError):
                run_parts(cfg, "corpus-index")
        self.assertEqual(target.read_bytes(), b'preserve this unrelated file')
        self.assertFalse((root / "manifest.json").exists())

    def test_sqlite3_wal_prevents_completed_run_cache_reuse(self):
        index = self.root / "snapshot.SQLITE3"
        index.write_bytes(self.index.read_bytes())
        cfg = self.config("retrieve") | {"index": str(index)}
        run_parts(cfg, "retrieve")
        Path(str(index) + "-wal").write_bytes(b'pending transaction')
        with self.assertRaises(SchemaInvalidError):
            run_parts(cfg, "retrieve")

    def test_no_gold_allowed_in_inference_and_no_labels_in_config(self):
        write_jsonl(self.queries, [self.query | {"gold": ["outside"]}])
        with self.assertRaises(SchemaInvalidError):
            run_parts(self.config("retrieve"), "retrieve")
        with self.assertRaises(SchemaInvalidError):
            validate_config(self.config("retrieve") | {"qrels": "val.jsonl"}, "retrieve")

    def test_budget_validation_and_dry_run_missing_roles(self):
        for top_k in (True, 0, -1):
            with self.assertRaises(SchemaInvalidError):
                validate_config(self.config("retrieve") | {"top_k": top_k}, "retrieve")
        cfg = self.config("retrieve") | {"index": str(self.root / "missing.sqlite")}
        self.assertEqual(inspect_parts(cfg, "retrieve")["missing_roles"], ["index"])

    def test_cli_executes_both_components_and_index_without_heavy_imports(self):
        cfg = {"schema_version": 1, "corpus": str(self.corpus), "chunk_chars": 1200,
               "output_dir": str(self.root / "cli-index")}
        for command, data in (("corpus-index", cfg), ("retrieve", self.config("retrieve")),
                              ("evidence-fuse", self.config("evidence-fuse"))):
            path = self.root / (command + ".json")
            path.write_text(json.dumps(data), encoding="utf-8")
            script = ("import sys; from TXT.bear.cli import main; "
                      f"rc=main({[command, '--config', str(path), '--execute']!r}); "
                      "assert not {'numpy','torch','transformers','pandas'} & set(sys.modules); sys.exit(rc)")
            process = subprocess.run([sys.executable, "-B", "-c", script], cwd=REPO_ROOT,
                                     capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads(process.stdout)["status"], "completed")


if __name__ == "__main__":
    unittest.main()
