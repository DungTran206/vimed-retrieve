"""BEAR 2.0 synthetic end-to-end invariants; no relevance benchmark claims."""
import copy
import hashlib
import unittest
import uuid
from TXT.tests.fixtures import get_fixture_dir, create_synthetic_corpus_db
from TXT.bear.io import atomic_write_json, read_json, read_jsonl, write_jsonl, sha256_file
from TXT.bear.artifacts import verify_manifest, file_identity
from TXT.bear.contracts import SchemaInvalidError, HashMismatchError
from TXT.bear.features import create_pools, compute_features, inference
from TXT.bear.application_audit import audit_application
from TXT.bear.chunk_study import run_chunk_study
from TXT.bear.chunk_evaluation import evaluate_chunks
from TXT.bear.evaluate_runner import evaluate
from TXT.bear.experiments import freeze
from TXT.bear.provenance import inspect_provenance
from TXT.bear.routing_diagnostics import routing_statistics
from TXT.bear.tuning import evidence_menu, tune


class TestV2(unittest.TestCase):
    def setUp(self):
        self.root = get_fixture_dir("v2_" + uuid.uuid4().hex[:8])

    def pipeline(self):
        corpus = self.root / "corpus.sqlite"
        docs, chunks = [], []
        for i in range(1, 202):
            body = "noise target" if i == 41 else "target" if i == 201 else "noise word" if i == 200 else "noise"
            docs.append({"id": str(i), "body": body, "lang": "zh" if i == 2 else "vi"})
            ranges = ((0, 5), (6, 12)) if i == 41 else ((0, len(body)),)
            chunks += [{"chunk_id": 10*i+j, "doc_id": str(i), "ord": j, "start": a, "end": b}
                       for j, (a, b) in enumerate(ranges)]
        create_synthetic_corpus_db(corpus, docs, chunks)
        base, deep, membership = self.root / "base.jsonl", self.root / "deep.jsonl", self.root / "members.json"
        write_jsonl(base, [{"id": q, "candidates": list(range(1, 201))} for q in range(1, 5)])
        write_jsonl(deep, [{"id": q, "candidates": list(range(1, 202))} for q in range(1, 5)])
        atomic_write_json(membership, [str(i) for i in range(1, 202)])
        create_pools({"schema_version": 1, "baseline": str(base), "deeper": str(deep), "corpus": str(corpus),
                      "membership": str(membership), "cap": 201, "scope": "plarge", "output_dir": str(self.root / "pool")})
        query, entities, selected = self.root / "query.jsonl", self.root / "entities.jsonl", self.root / "selected.json"
        words = {1: "target", 2: "noise", 3: "target", 4: "word"}
        write_jsonl(query, [{"id": q, "query": word} for q, word in words.items()])
        write_jsonl(entities, [{"id": q, "entities": [{"vi": word}]} for q, word in words.items()])
        atomic_write_json(selected, [1, 2, 4])
        fc = {"schema_version": 1, "pool_manifest": str(self.root / "pool/manifest.json"), "queries": str(query),
              "enriched_queries": str(entities), "query_ids_path": str(selected), "corpus": str(corpus),
              "output_dir": str(self.root / "features")}
        compute_features(fc)
        rc = {"schema_version": 1, "run_id": "fixture", "pool_manifest": fc["pool_manifest"],
              "feature_manifest": str(self.root / "features/manifest.json"), "mode": "fixed_evidence",
              "feature_name": "body_coverage", "lambda": 1, "output_dir": str(self.root / "run")}
        inference(rc)
        inference(rc | {"mode": "baseline", "lambda": 0, "output_dir": str(self.root / "baseline")})
        return corpus, rc

    def chunk_pipeline(self, experiment="C1"):
        corpus, rc = self.pipeline()
        allocation, scores = self.root / "allocation.jsonl", self.root / "scores.jsonl"
        write_jsonl(allocation, [{"id": q, "candidates": [{"doc_id": str(i), "p": .1} for i in range(1, 201)]}
                                for q in range(1, 5)])
        write_jsonl(scores, [{"id": q, "doc_id": "41", "idx": j, "score": s}
                            for q in range(1, 5) for j, s in enumerate((.1, .9))])
        selected = self.root / "chunk_ids.json"
        atomic_write_json(selected, [1, 4])
        cfg = {"schema_version": 1, "ranking_dir": str(self.root / "baseline"), "corpus": str(corpus),
               "allocation": str(allocation), "chunk_scores": str(scores), "experiment": experiment,
               "feature_manifest": rc["feature_manifest"], "query_ids_path": str(selected),
               "output_dir": str(self.root / "chunks")}
        run_chunk_study(cfg)
        return cfg, corpus

    def passage_config(self, corpus):
        split, passages = self.root / "split.json", self.root / "passages.jsonl"
        atomic_write_json(split, {"dev": [1], "holdout": [4], "query_groups": {"1": 1, "4": 4}, "confirmatory_eligible": True})
        body_hash = hashlib.sha256(b"noise target").hexdigest()
        write_jsonl(passages, [{"query_id": q, "doc_id": "41", "start": 6, "end": 12,
            "body_sha256": body_hash, "reference_source": "synthetic_fixture", "annotator": "synthetic_fixture",
            "adjudication": "reviewed", "label_policy_version": "fixture"} for q in (1, 4)])
        return {"schema_version": 1, "corpus": str(corpus), "passages": str(passages), "passages_hash": sha256_file(passages),
                "split_manifest": str(split), "split_hash": sha256_file(split), "split": "dev",
                "primary_metric": "local_passage_recall", "coverage": "complete_local_passages",
                "label_policy_version": "fixture", "bootstrap_samples": 30,
                "output_dir": str(self.root / "chunk_eval")}

    def test_audit_distinguishes_partial_noop_reorder_replacement_and_frozen_zh(self):
        _, rc = self.pipeline()
        cfg = {"run_dir": str(self.root / "run"), "baseline": str(self.root / "base.jsonl"),
               "output_dir": str(self.root / "audit")}
        audit_application(cfg)
        rows = {r["query_id"]: r for r in read_jsonl(self.root / "audit/per_query.jsonl")}
        self.assertTrue(rows[1]["changed_docset"])
        self.assertIn("201", rows[1]["added"])
        self.assertTrue(rows[2]["applied"])
        self.assertFalse(rows[2]["changed_order"])
        self.assertEqual(rows[3]["fallback_reason"], "evidence_unavailable")
        self.assertFalse(rows[3]["feature_present"])
        self.assertTrue(rows[4]["changed_order"])
        self.assertFalse(rows[4]["changed_docset"])
        self.assertIsNone(rows[1]["score_coverage_added"])
        for row in read_jsonl(self.root / "run/candidates.jsonl"):
            self.assertEqual(row["candidates"][1]["doc_id"], "2")

    def test_audit_refuses_fabricated_output_even_with_resealed_manifest(self):
        self.pipeline()
        manifest = read_json(self.root / "run/manifest.json")
        details = list(read_jsonl(self.root / "run/ranking_details.jsonl"))
        details[0]["fallback_reason"] = "fabricated"
        path = write_jsonl(self.root / "run/ranking_details.jsonl", details)
        manifest["artifacts"] = [file_identity(i["path"]) for i in manifest["artifacts"]]
        atomic_write_json(self.root / "run/manifest.json", manifest)
        with self.assertRaises(SchemaInvalidError):
            audit_application({"run_dir": str(self.root / "run"), "output_dir": str(self.root / "audit")})

    def test_provenance_unknown_inputs_do_not_create_fake_linkage(self):
        cfg = {"schema_version": 1, "inputs": {"submission": {"path": None}},
               "reported": {"FINAL_SCORE": .3445}, "output_dir": str(self.root / "provenance")}
        report = inspect_provenance(cfg)
        self.assertEqual(report["status"], "blocked_input")
        self.assertEqual(report["submission_linkage"], "unresolved")
        self.assertIsNone(report["observed_metrics"])
        self.assertFalse((self.root / "provenance").exists())
        inspect_provenance(cfg, execute=True)
        self.assertEqual(read_json(self.root / "provenance/provenance.json")["reported"]["FINAL_SCORE"], .3445)

    def test_combined_body_local_menu_runs_all_twelve_without_selecting_unlabelled_best(self):
        _, rc = self.pipeline()
        base = self.root / "run_config.json"
        atomic_write_json(base, rc)
        menu, protocol = self.root / "menus.json", self.root / "study.json"
        atomic_write_json(menu, {"L1": evidence_menu("L1"), "L4": evidence_menu("L4")})
        atomic_write_json(protocol, {"schema_version": 1, "study_id": "fixture_body_local", "family": "L1_L4",
            "run_config": str(base), "evaluation_config": None, "output_dir": str(self.root / "study")})
        self.assertEqual(tune(protocol, menu)["trials"], 12)
        tune(protocol, menu, execute=True)
        trials = read_json(self.root / "study/trials.json")
        self.assertEqual(len(trials), 12)
        self.assertEqual({t["feature_name"] for t in trials}, {"body_coverage", "local_max_all"})
        self.assertEqual(read_json(self.root / "study/selection.json")["status"], "inconclusive")
        from TXT.bear.io import atomic_write_text
        atomic_write_text(self.root / "study/L4_1/candidates.jsonl", "tampered")
        with self.assertRaises(HashMismatchError):
            tune(protocol, menu, execute=True)

    def test_c1_changes_tail_selector_preserves_slots_and_arbitrary_pilot_qids(self):
        cfg, corpus = self.chunk_pipeline()
        manifest = verify_manifest(self.root / "chunks/manifest.json")
        self.assertEqual(manifest["integrity"]["queries"], 2)
        old = [r for r in read_jsonl(self.root / "chunks/control_chunk_refs.jsonl") if r["doc_id"] == "41"]
        new = [r for r in read_jsonl(self.root / "chunks/chunk_refs.jsonl") if r["doc_id"] == "41"]
        self.assertEqual([r["exporter_idx"] for r in old], [0, 0])
        self.assertEqual([r["exporter_idx"] for r in new], [1, 1])
        self.assertEqual(manifest["candidate_kind"], "chunk")

    def test_c2_uses_exact_native_features_not_document_body_scores(self):
        cfg, corpus = self.chunk_pipeline("C2")
        selected = [r for r in read_jsonl(self.root / "chunks/chunk_refs.jsonl") if r["doc_id"] == "41"]
        self.assertEqual([(r["query_id"], r["exporter_idx"]) for r in selected], [(1, 1), (4, 0)])

    def test_chunk_diagnostic_freezes_records_and_consumes_holdout_only_once(self):
        _, corpus = self.chunk_pipeline()
        cfg = self.passage_config(corpus)
        result = evaluate_chunks(cfg, self.root / "chunks")
        self.assertEqual(result["metric"], 1)
        self.assertEqual(result["paired"]["mean_delta"], 1)
        self.assertFalse(result["official_equivalent"])
        protocol = self.root / "protocol.json"
        atomic_write_json(protocol, {"split_manifest": cfg["split_manifest"],
            "selected_dev_report": str(self.root / "chunk_eval/evaluation.json"), "controls": [],
            "cost_ceiling_seconds": 100, "primary_metric": "local_passage_recall"})
        freeze(self.root / "chunks", protocol)
        hc = cfg | {"split": "holdout", "frozen_candidate": str(self.root / "chunks/frozen.json"),
                    "output_dir": str(self.root / "holdout")}
        self.assertEqual(evaluate_chunks(hc, self.root / "chunks", preflight_only=True)["status"], "ready")
        self.assertFalse((self.root / "chunks/holdout_exposure.json").exists())
        self.assertEqual(evaluate_chunks(hc, self.root / "chunks")["metric"], 1)
        with self.assertRaises(SchemaInvalidError):
            evaluate_chunks(hc, self.root / "chunks")

    def test_chunk_freeze_rejects_document_only_selection(self):
        _, corpus = self.chunk_pipeline()
        cfg = self.passage_config(corpus)
        report = self.root / "doc_only.json"
        atomic_write_json(report, {"status": "available", "split": "dev",
                                 "candidate_sha256": sha256_file(self.root / "chunks/candidates.jsonl")})
        protocol = self.root / "protocol.json"
        atomic_write_json(protocol, {"split_manifest": cfg["split_manifest"], "selected_dev_report": str(report),
                                   "controls": [], "cost_ceiling_seconds": 100})
        with self.assertRaises(SchemaInvalidError):
            freeze(self.root / "chunks", protocol)

    def test_release_keeps_studied_chunks_and_rejects_changed_slots(self):
        from TXT.bear.release import selected_release_records
        cfg, corpus = self.chunk_pipeline()
        root = self.root / "chunks"
        manifest = verify_manifest(root / "manifest.json")
        control = read_json(root / "control_records.json")
        refs = list(read_jsonl(root / "control_chunk_refs.jsonl"))
        ranking = {r["id"]: [str(d) for d in r["relevant_docs"]] for r in control}
        records, selected = selected_release_records(manifest, root, sha256_file(corpus), ranking, control, refs)
        chunks = [c["chunk_text"] for c in records[0]["relevant_chunks"] if c["doc_id"] == 41]
        self.assertEqual(chunks, ["target"])
        self.assertNotEqual(records, control)
        write_jsonl(root / "chunk_refs.jsonl", selected[:-1])
        with self.assertRaises(SchemaInvalidError):
            selected_release_records(manifest, root, sha256_file(corpus), ranking, control, refs)

    def test_partial_chunk_scores_fallback_but_unknown_namespace_is_rejected(self):
        cfg, corpus = self.chunk_pipeline()
        partial = self.root / "partial_scores.jsonl"
        write_jsonl(partial, [{"id": q, "doc_id": "41", "idx": 0, "score": .1} for q in (1, 4)])
        run_chunk_study(cfg | {"chunk_scores": str(partial), "output_dir": str(self.root / "partial")})
        selected = [r for r in read_jsonl(self.root / "partial/chunk_refs.jsonl") if r["doc_id"] == "41"]
        self.assertEqual([r["exporter_idx"] for r in selected], [0, 0])
        write_jsonl(partial, [{"id": 1, "doc_id": "41", "idx": 999, "score": .8}])
        with self.assertRaises(SchemaInvalidError):
            run_chunk_study(cfg | {"chunk_scores": str(partial), "output_dir": str(self.root / "bad_namespace")})

    def test_chunk_study_refuses_different_corpus_snapshot(self):
        cfg, corpus = self.chunk_pipeline()
        other = self.root / "other.sqlite"
        create_synthetic_corpus_db(other, [{"id": "1", "body": "changed"}], [])
        with self.assertRaises(SchemaInvalidError):
            run_chunk_study(cfg | {"corpus": str(other), "output_dir": str(self.root / "wrong_corpus")})

    def test_chunk_tamper_after_freeze_is_detected_before_exposure(self):
        _, corpus = self.chunk_pipeline()
        cfg = self.passage_config(corpus)
        evaluate_chunks(cfg, self.root / "chunks")
        protocol = self.root / "protocol.json"
        atomic_write_json(protocol, {"split_manifest": cfg["split_manifest"],
            "selected_dev_report": str(self.root / "chunk_eval/evaluation.json"), "controls": [], "cost_ceiling_seconds": 100})
        freeze(self.root / "chunks", protocol)
        records = read_json(self.root / "chunks/records.json")
        records[0]["relevant_chunks"][0]["chunk_text"] = "rewritten"
        atomic_write_json(self.root / "chunks/records.json", records)
        with self.assertRaises(HashMismatchError):
            evaluate_chunks(cfg | {"split": "holdout", "frozen_candidate": str(self.root / "chunks/frozen.json")}, self.root / "chunks")
        self.assertFalse((self.root / "chunks/holdout_exposure.json").exists())

    def test_precision_at_k_has_actual_paired_control_deltas(self):
        self.pipeline()
        labels, split = self.root / "labels.jsonl", self.root / "split.json"
        write_jsonl(labels, [{"query_id": 1, "doc_id": d, "grade": g, "annotator": "synthetic_fixture",
            "adjudication": "reviewed", "label_policy_version": "fixture"} for d, g in (("41", 2), ("1", 0))])
        atomic_write_json(split, {"dev": [1], "query_groups": {"1": 1}})
        cfg = {"qrels_path": str(labels), "qrels_hash": sha256_file(labels), "split_manifest": str(split),
               "split_hash": sha256_file(split), "split": "dev", "primary_metric": "precision_at_k", "k": 1,
               "coverage": "complete_topk", "label_policy_version": "fixture", "bootstrap_samples": 30,
               "output_dir": str(self.root / "paired_eval")}
        result = evaluate(cfg, self.root / "run", self.root / "baseline")
        self.assertEqual(result["paired"]["mean_delta"], 1)

    def test_invalid_or_incomplete_document_holdout_does_not_consume_exposure(self):
        self.pipeline()
        split, labels, dev, protocol = [self.root / name for name in ("split.json", "labels.jsonl", "dev.json", "protocol.json")]
        atomic_write_json(split, {"dev": [2], "holdout": [1], "query_groups": {"1": 1}, "confirmatory_eligible": True})
        write_jsonl(labels, [{"query_id": 1, "doc_id": "1", "grade": 2, "annotator": "synthetic_fixture",
            "adjudication": "reviewed", "label_policy_version": "fixture"}])
        atomic_write_json(dev, {"status": "available", "split": "dev",
                               "candidate_sha256": sha256_file(self.root / "baseline/candidates.jsonl")})
        atomic_write_json(protocol, {"split_manifest": str(split), "selected_dev_report": str(dev), "controls": [], "cost_ceiling_seconds": 100})
        freeze(self.root / "baseline", protocol)
        cfg = {"qrels_path": str(labels), "qrels_hash": sha256_file(labels), "split_manifest": str(split),
               "split_hash": sha256_file(split), "split": "holdout", "primary_metric": "precision_at_k", "k": 200,
               "label_policy_version": "fixture", "coverage": "complete_topk", "frozen_candidate": str(self.root / "baseline/frozen.json"),
               "output_dir": str(self.root / "holdout")}
        for bad in (cfg | {"primary_metric": "typo"}, cfg):
            with self.assertRaises(SchemaInvalidError):
                evaluate(bad, self.root / "baseline")
            self.assertFalse((self.root / "baseline/holdout_exposure.json").exists())
        self.assertEqual(evaluate(cfg, self.root / "baseline", preflight_only=True)["status"], "inconclusive")

    def test_routing_oracle_is_dev_diagnostic_and_shuffles_are_reproducible(self):
        args = ({1: 1, 2: 0, 3: 1}, {1: 0, 2: 1, 3: 0}, {1: .5, 2: .5, 3: .5},
                {1: .9, 2: .1, 3: .8}, {1: 5, 2: 2, 3: 5}, {1: ("vi", "short"), 2: ("vi", "short"), 3: ("vi", "short")})
        result = routing_statistics(*args)
        self.assertEqual(result["oracle_headroom"], .5)
        self.assertEqual(result, routing_statistics(*args))
        self.assertEqual([c["seed"] for c in result["shuffled_controls"]], [11, 23, 37, 53, 71])
        with self.assertRaises(SchemaInvalidError):
            routing_statistics({1: 1}, {2: 0}, {1: 0}, {}, {}, {})


if __name__ == "__main__":
    unittest.main()
