"""Test dữ liệu tổng hợp; không phải benchmark trên corpus/labels thật."""
import copy
import sqlite3
import subprocess
import sys
import unittest
from TXT.bear.artifacts import file_identity, verify_manifest
from TXT.bear.config import validate_config
from TXT.bear.contracts import SchemaInvalidError, HashMismatchError, REPO_ROOT
from TXT.bear.features import create_pools, compute_features, inference
from TXT.bear.integrity import build_with_refs, validate_records
from TXT.bear.io import atomic_write_json, atomic_write_text, read_json, read_jsonl, sha256_file, write_jsonl
from TXT.bear.audit import run_audit
from TXT.bear.evaluate_runner import evaluate
from TXT.bear.experiments import freeze
from TXT.tests.fixtures import get_fixture_dir, create_synthetic_corpus_db


class TestRunnerIntegrity(unittest.TestCase):
    def setUp(self):
        # Root riêng mỗi lần: completed manifest thực sự immutable giữa lần test.
        import uuid
        self.root = get_fixture_dir("runner_" + uuid.uuid4().hex[:8])

    def test_config_unknown_nested_type_and_nonfinite_rejected(self):
        for cfg in ({"schema_version": 1, "inputs": {}, "runtime": {"dry_run": "yes"}},
                    {"schema_version": 1, "inputs": {"corpus": {"path": None, "typo": True}}}):
            with self.assertRaises(SchemaInvalidError):
                validate_config(cfg, "audit")
        bad = self.root / "nan.json"
        atomic_write_text(bad, '{"x":NaN}')
        with self.assertRaises(SchemaInvalidError):
            read_json(bad)

    def test_audit_hash_mismatch_never_ready(self):
        data = self.root / "source.json"
        atomic_write_json(data, {"hello": 1})
        cfg = {"schema_version": 1, "inputs": {"x": {"path": str(data), "expected_sha256": "0" * 64}},
               "outputs": {"input_manifest": str(self.root / "inputs.json"),
                           "baseline_manifest": str(self.root / "baseline.json"),
                           "readiness_report": str(self.root / "readiness.md")}}
        path = self.root / "audit.json"
        atomic_write_json(path, cfg)
        result, code = run_audit(path)
        self.assertEqual(code, 1)
        self.assertEqual(result["invalid_roles"], ["x"])

    def test_help_does_not_import_heavy_modules(self):
        script = "import sys; from TXT.bear.cli import main; main(['--help'])"
        # argparse SystemExit ngắt script, nên kiểm import bằng catching exit.
        script = "import sys\nfrom TXT.bear.cli import main\ntry: main(['--help'])\nexcept SystemExit: pass\nassert not set(('numpy','torch','pandas','transformers')) & set(sys.modules)"
        p = subprocess.run([sys.executable, "-B", "-c", script], cwd=REPO_ROOT, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr.decode())

    def test_pool_features_inference_resume_and_tamper(self):
        body = "Bệnh viêm phổi. Điều trị viêm phổi."
        corpus = self.root / "corpus.sqlite"
        create_synthetic_corpus_db(corpus, [{"id": str(i), "body": body if i == 201 else "Tài liệu khác", "lang": "zh" if i == 2 else "vi"} for i in range(1, 202)],
            [{"chunk_id": i, "doc_id": str(i), "ord": 0, "start": 0, "end": len(body) if i == 201 else len("Tài liệu khác")} for i in range(1, 202)])
        base, deep = self.root / "base.jsonl", self.root / "deep.jsonl"
        write_jsonl(base, [{"id": 1, "candidates": list(range(1, 201))}])
        write_jsonl(deep, [{"id": 1, "candidates": list(range(1, 202))}])
        membership = self.root / "membership.json"
        atomic_write_json(membership, [str(i) for i in range(1, 202)])
        pc = {"schema_version": 1, "baseline": str(base), "deeper": str(deep), "corpus": str(corpus),
              "membership": str(membership), "scope": "plarge", "output_dir": str(self.root / "pool")}
        create_pools(pc)
        q, e = self.root / "query.jsonl", self.root / "entities.jsonl"
        write_jsonl(q, [{"id": 1, "query": "viêm phổi"}])
        write_jsonl(e, [{"id": 1, "entities": [{"vi": "viêm phổi"}]}])
        fc = {"schema_version": 1, "pool_manifest": str(self.root / "pool/manifest.json"),
              "queries": str(q), "enriched_queries": str(e), "corpus": str(corpus), "output_dir": str(self.root / "features")}
        compute_features(fc)
        rc = {"schema_version": 1, "run_id": "fixture", "pool_manifest": pc["output_dir"] + "/manifest.json",
              "feature_manifest": fc["output_dir"] + "/manifest.json", "mode": "fixed_evidence", "lambda": 1,
              "output_dir": str(self.root / "run")}
        first = inference(rc)
        self.assertEqual(first, inference(rc))
        output = next(read_jsonl(self.root / "run/candidates.jsonl"))["candidates"]
        self.assertEqual(output[0]["doc_id"], "201")
        self.assertEqual(output[1]["doc_id"], "2")
        rc2 = rc | {"lambda": .2}
        with self.assertRaises(HashMismatchError):
            inference(rc2)
        atomic_write_text(self.root / "run/candidates.jsonl", "tampered")
        with self.assertRaises(HashMismatchError):
            verify_manifest(self.root / "run/manifest.json")

    def test_chunk_tiers_match_original_exporter(self):
        corpus = self.root / "native.sqlite"
        body = "AA  BBCCDD"
        docs = [{"id": str(i), "body": body} for i in range(1, 201)]
        chunks = [{"chunk_id": 10*i+j, "doc_id": str(i), "ord": 20-j, "start": s, "end": e}
                  for i in range(1, 201) for j, (s, e) in enumerate(((0,2), (2,4), (4,6), (6,8), (8,10)))]
        create_synthetic_corpus_db(corpus, docs, chunks)
        with sqlite3.connect(corpus) as conn:
            conn.execute("ALTER TABLE doc RENAME COLUMN id TO doc_id")
        ranking = {1: [str(i) for i in range(1, 201)]}
        scores = {1: {"1": {0: .1, 1: .2, 2: .8, 3: .9}, "41": {3: 99}}}
        plans = {1: {"2": 0, "121": 1, "1": 1}}
        records, refs = build_with_refs(ranking, corpus, scores, plans, sha256_file(corpus))
        from submit.submission import build
        expected = build({1: [(d, 200-i) for i, d in enumerate(ranking[1])]}, 200, None,
                         str(corpus), 2, n_queries=1, id_type=int, chunk_from_top=40,
                         extra_one=120, chunk_scores=scores, chunk_plan=plans)
        self.assertEqual(records, expected)
        validate_records(records, refs, corpus, n_queries=1)
        damaged = copy.deepcopy(records)
        damaged[0]["relevant_chunks"][0]["chunk_text"] = "rewrite"
        with self.assertRaises(SchemaInvalidError):
            validate_records(damaged, refs, corpus, n_queries=1)

    def test_partial_labels_return_inconclusive_and_review_guard(self):
        run = self.root / "run"
        write_jsonl(run / "candidates.jsonl", [{"id": 1, "candidates": ["1", "2"]}])
        labels, split = self.root / "labels.jsonl", self.root / "split.json"
        atomic_write_json(split, {"dev": [1], "query_groups": {"1": 1}})
        write_jsonl(labels, [{"query_id": 1, "doc_id": "1", "grade": 2,
                             "adjudication": "reviewed", "annotator": "synthetic_fixture",
                             "label_policy_version": "fixture"}])
        cfg = {"qrels_path": str(labels), "qrels_hash": sha256_file(labels), "split_manifest": str(split),
               "split_hash": sha256_file(split), "split": "dev", "primary_metric": "precision_at_k", "k": 2,
               "label_policy_version": "fixture", "coverage": "complete_topk", "output_dir": str(self.root / "eval")}
        result = evaluate(cfg, run)
        self.assertEqual(result["status"], "inconclusive")
        self.assertIsNone(result["metric"])

    def test_holdout_requires_frozen_candidate_and_refuses_second_exposure(self):
        from TXT.bear.artifacts import start_run, complete_run
        run, manifest, _ = start_run(str(self.root / "candidate"), {"fixture": True}, [])
        path = write_jsonl(run / "candidates.jsonl", [{"id": 1, "candidates": ["1"]}])
        complete_run(run, manifest, [path])
        split = self.root / "split.json"
        atomic_write_json(split, {"dev": [2], "holdout": [1], "query_groups": {"1": 1, "2": 2}, "confirmatory_eligible": True})
        labels = self.root / "holdout.jsonl"
        write_jsonl(labels, [{"query_id": 1, "doc_id": "1", "grade": 2, "annotator": "fixture", "adjudication": "reviewed", "label_policy_version": "fixture"}])
        dev = self.root / "dev.json"
        atomic_write_json(dev, {"status": "available", "split": "dev", "candidate_sha256": sha256_file(path)})
        protocol = self.root / "protocol.json"
        atomic_write_json(protocol, {"split_manifest": str(split), "selected_dev_report": str(dev), "controls": [], "cost_ceiling_seconds": 100})
        freeze(run, protocol)
        cfg = {"qrels_path": str(labels), "qrels_hash": sha256_file(labels), "split_manifest": str(split),
               "split_hash": sha256_file(split), "split": "holdout", "primary_metric": "precision_at_k", "k": 1,
               "label_policy_version": "fixture", "coverage": "complete_topk", "output_dir": str(self.root / "holdout_eval"),
               "frozen_candidate": str(run / "frozen.json")}
        self.assertEqual(evaluate(cfg, run)["status"], "available")
        with self.assertRaises(SchemaInvalidError):
            evaluate(cfg, run)

    def test_reproduce_missing_inputs_and_tuning_menu_are_honest(self):
        from TXT.bear.cli import main
        from TXT.bear.tuning import tune
        self.assertEqual(main(["reproduce", "--config", "TXT/configs/reproduce.json", "--dry-run"]), 1)
        result = tune("TXT/configs/tune_l1.json", "TXT/configs/menus_v1.json")
        self.assertEqual(result["trials"], 6)
        with self.assertRaises(SchemaInvalidError):
            tune("TXT/configs/tune_l1.json", "TXT/configs/menus_v1.json", split="holdout")

    def test_c1_partial_score_falls_back_and_c2_offsets_preserved(self):
        from TXT.bear.adapters import ChunkRef
        from TXT.bear.chunk_experiments import select_chunks
        refs = [ChunkRef("test", "1", "test", i, i, i, i*2, i*2+2, "test") for i in range(3)]
        selected, reason = select_chunks(refs, 1, 41, scores={0: .1, 1: .5})
        self.assertEqual(selected, refs[:1])
        self.assertEqual(reason, "incomplete_feature_first_chunk")
        selected, _ = select_chunks(refs, 1, 41, "C2", evidence={0: 0, 1: 0, 2: 1})
        self.assertEqual(selected[0].exporter_idx, 2)
