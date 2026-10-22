"""Semantic cache checks use declared synthetic vectors, never model downloads."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from TXT.bear.contracts import HashMismatchError, RUNTIME_DIR, SchemaInvalidError
from TXT.bear.corpus_index import build_index
from TXT.bear.io import atomic_write_json, canonical_sha256, read_json, read_jsonl, write_jsonl
from TXT.bear.medical_semantic import build_semantic_cache, validate_encoder_config


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class TestMedicalSemantic(unittest.TestCase):
    def setUp(self):
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="medical_semantic_", dir=RUNTIME_DIR)
        self.root = Path(self.temp.name)
        self.encoder = {"revision": "a" * 40}
        self.documents = [{"doc_id": "1", "lang": "zh", "title": "", "body": "发热和咳嗽"},
                          {"doc_id": "2", "lang": "vi", "title": "", "body": "không có triệu chứng"}]
        corpus = write_jsonl(self.root / "corpus.jsonl", self.documents)
        build_index(corpus, self.root / "index.sqlite")
        self.original_matches = [{"concept_id": "fever", "match": 0, "spans": []}]
        self.base = [{"id": 1, "query": "sốt", "lang": "vi", "concepts": [
            {"concept_id": "fever", "text": "sốt", "origin": "query", "kind": "symptom", "tier": 4},
            {"concept_id": "expanded", "text": "ignored expansion", "origin": "enrichment", "kind": "symptom", "tier": 1}],
            "candidates": [{"doc_id": doc["doc_id"], "lang": doc["lang"], "scores": {"dense_head": 0.3},
                            "body_sha256": _sha(doc["body"]), "concept_matches": self.original_matches}
                           for doc in self.documents]}]
        self.extractions = [self._extraction(self.documents[0], [
            {"text": "发热", "field": "body", "anchor": {"start": 0, "end": 2},
             "kind": "symptom", "assertion": "affirmed"},
            {"text": "咳嗽", "field": "body", "anchor": {"start": 3, "end": 5},
             "kind": "symptom", "assertion": "affirmed"}])]
        self.config = {"cache": str(self.root / "base.jsonl"), "index": str(self.root / "index.sqlite"),
                       "document_terms": str(self.root / "terms.jsonl"), "encoder": self.encoder,
                       "embeddings_input": str(self.root / "vectors.jsonl")}
        self.vectors = [self._embedding("sốt", [2, 0]), self._embedding("发热", [3, 0]),
                        self._embedding("咳嗽", [0, 5])]
        self._write_inputs()

    def tearDown(self):
        self.temp.cleanup()

    def _embedding(self, text, values, **extra):
        return {"text": text, "embedding": values, "encoder": self.encoder,
                "provenance": {"synthetic": True, "purpose": "unit-test geometry only"},
                "token_count": 4, "truncated": False, **extra}

    def _extraction(self, doc, terms):
        return {"doc_id": doc["doc_id"], "lang": doc["lang"], "title_sha256": _sha(doc["title"]),
                "body_sha256": _sha(doc["body"]), "terms": terms, "truncated": False,
                "windows": [{"field": "body", "start": 0, "end": len(doc["body"]), "original_length": len(doc["body"])}]}

    def _write_inputs(self):
        write_jsonl(self.config["cache"], self.base)
        write_jsonl(self.config["document_terms"], self.extractions)
        write_jsonl(self.config["embeddings_input"], self.vectors)

    def _run(self):
        return build_semantic_cache(self.config, self.root / "semantic")

    def _rows(self):
        return list(read_jsonl(self.root / "semantic" / "cache.jsonl"))

    def test_multilingual_cosines_preserve_gate_and_missing_evidence(self):
        with patch("TXT.bear.medical_semantic._TransformerEncoder", side_effect=AssertionError("Model loaded")):
            artifacts, report = self._run()
        row = self._rows()[0]
        candidate, missing = row["candidates"]
        matrix = candidate["sapbert_matches"]
        self.assertEqual([entry["concept_id"] for entry in matrix], ["fever"])
        self.assertAlmostEqual(matrix[0]["similarities"][0]["cosine"], 1)
        self.assertAlmostEqual(matrix[0]["similarities"][1]["cosine"], 0)
        self.assertEqual(candidate["concept_matches"], self.original_matches)
        self.assertEqual(candidate["scores"], self.base[0]["candidates"][0]["scores"])
        self.assertTrue(candidate["score_available"]["sapbert"])
        self.assertFalse(missing["score_available"]["sapbert"])
        self.assertEqual(missing["sapbert_unavailable_reason"], "missing_document_terms")
        self.assertIsNone(missing["sapbert_extraction"])
        self.assertEqual(report["new_text_embeddings"], 3)
        self.assertEqual(report["semantic_available_count"], 1)
        self.assertFalse(report["model_contacted"])
        self.assertIn(self.root / "semantic" / "semantic_recipe.json", artifacts)

    def test_empty_reviewed_terms_and_no_eligible_concepts_remain_missing(self):
        self.extractions[0]["terms"] = []
        self._write_inputs()
        self._run()
        candidate = self._rows()[0]["candidates"][0]
        self.assertEqual(candidate["sapbert_matches"], [])
        self.assertEqual(candidate["sapbert_unavailable_reason"], "empty_extracted_terms")
        self.assertFalse(candidate["score_available"]["sapbert"])
        other_config = {**self.config, "cache": str(self.root / "empty_concepts.jsonl")}
        empty_concepts = {**self.base[0], "concepts": []}
        write_jsonl(other_config["cache"], [empty_concepts])
        build_semantic_cache(other_config, self.root / "empty_semantic")
        row = next(read_jsonl(self.root / "empty_semantic" / "cache.jsonl"))
        self.assertEqual(row["candidates"][0]["sapbert_unavailable_reason"], "no_eligible_query_concepts")

    def test_hash_and_span_mismatch_fail_before_using_vectors(self):
        for mismatch in ("hash", "span", "candidate"):
            with self.subTest(mismatch=mismatch):
                self.extractions[0]["body_sha256"] = _sha(self.documents[0]["body"])
                self.extractions[0]["terms"][0]["anchor"]["end"] = 2
                self.base[0]["candidates"][0]["body_sha256"] = _sha(self.documents[0]["body"])
                if mismatch == "hash":
                    self.extractions[0]["body_sha256"] = "wrong"
                elif mismatch == "span":
                    self.extractions[0]["terms"][0]["anchor"]["end"] = 3
                else:
                    self.base[0]["candidates"][0]["body_sha256"] = "wrong"
                self._write_inputs()
                with self.assertRaises((HashMismatchError, SchemaInvalidError)):
                    build_semantic_cache(self.config, self.root / f"bad_{mismatch}")

    def test_resume_reuses_query_and_unique_vectors_without_model_calls(self):
        self._run()
        with patch("TXT.bear.medical_semantic._TransformerEncoder", side_effect=AssertionError("Model loaded")):
            _, report = self._run()
        self.assertEqual(report["reused_queries"], 1)
        self.assertEqual(report["new_text_embeddings"], 0)
        self.assertEqual(report["reused_text_embeddings"], 3)
        self.assertEqual(report["embedding_dimension"], 2)

    def test_encoder_path_encodes_each_unique_text_once_across_queries(self):
        expected = {row["text"]: row["embedding"] for row in self.vectors}

        class OfflineEncoder:
            def __init__(self, config):
                self.calls = 0

            def encode(self, texts):
                self.calls += 1
                return [{"embedding": expected[text], "token_count": 4, "truncated": False} for text in texts]

        self.config.pop("embeddings_input")
        second = {**self.base[0], "id": 2}
        write_jsonl(self.config["cache"], [self.base[0], second])
        with patch("TXT.bear.medical_semantic._TransformerEncoder", OfflineEncoder):
            _, report = self._run()
        self.assertEqual(report["encoder_batches"], 1)
        self.assertEqual(report["new_text_embeddings"], 3)
        self.assertEqual(report["reused_text_embeddings"], 3)
        self.assertTrue(report["model_contacted"])
        with patch("TXT.bear.medical_semantic._TransformerEncoder", side_effect=AssertionError("Model loaded")):
            _, resumed = self._run()
        self.assertFalse(resumed["model_contacted"])
        self.assertEqual(resumed["reused_queries"], 2)

    def test_recipe_change_cannot_reuse_old_vectors(self):
        self._run()
        self.config["encoder"] = {**self.encoder, "max_length": 128}
        with self.assertRaisesRegex(HashMismatchError, "recipe changed"):
            self._run()

    def test_index_and_title_metadata_mismatch_fail_before_any_encoder(self):
        for mismatch in ("index", "title"):
            with self.subTest(mismatch=mismatch):
                second = {**self.base[0], "id": 2,
                          "candidates": [dict(candidate) for candidate in self.base[0]["candidates"]]}
                if mismatch == "index":
                    second["index_sha256"] = "wrong-index"
                else:
                    second["candidates"][0]["title_sha256"] = "wrong-title"
                write_jsonl(self.config["cache"], [self.base[0], second])
                config = {key: value for key, value in self.config.items() if key != "embeddings_input"}
                with patch("TXT.bear.medical_semantic._TransformerEncoder", side_effect=AssertionError("Model loaded")):
                    with self.assertRaises(HashMismatchError):
                        build_semantic_cache(config, self.root / f"metadata_{mismatch}")

    def test_imported_sapbert_score_conflict_fails_before_any_encoder(self):
        second = {**self.base[0], "id": 2,
                  "candidates": [{**self.base[0]["candidates"][0], "scores": {"sapbert": 0.7}}]}
        write_jsonl(self.config["cache"], [self.base[0], second])
        config = {key: value for key, value in self.config.items() if key != "embeddings_input"}
        with patch("TXT.bear.medical_semantic._TransformerEncoder", side_effect=AssertionError("Model loaded")):
            with self.assertRaisesRegex(SchemaInvalidError, "already has scores.sapbert"):
                build_semantic_cache(config, self.root / "conflict")

    def test_missing_vector_on_partial_resume_never_reencodes(self):
        self._run()
        next((self.root / "semantic" / "embeddings").glob("*.json")).unlink()
        with patch("TXT.bear.medical_semantic._TransformerEncoder", side_effect=AssertionError("Model loaded")):
            with self.assertRaisesRegex(HashMismatchError, "vector referenced.*missing"):
                self._run()

    def test_vector_tampering_and_non_normalized_cached_vector_are_rejected(self):
        self._run()
        vector_path = next((self.root / "semantic" / "embeddings").glob("*.json"))
        payload = read_json(vector_path)
        payload["embedding"] = [4, 0]
        atomic_write_json(vector_path, payload)
        with self.assertRaises(HashMismatchError):
            self._run()
        payload.pop("sha256")
        payload["sha256"] = canonical_sha256(payload)
        atomic_write_json(vector_path, payload)
        with self.assertRaisesRegex(SchemaInvalidError, "not L2 normalized"):
            self._run()

    def test_invalid_precomputed_vectors_and_provenance_are_rejected(self):
        invalid = [([0, 0], {}), ([1], {}), ([1, float("inf")], {}),
                   ([1, 0], {"provenance": {}}), ([1, 0], {"encoder": {"revision": "b" * 40}})]
        for number, (vector, extra) in enumerate(invalid):
            with self.subTest(number=number):
                # Put the invalid row after a valid row so dimension checking is exercised.
                records = [self._embedding("sốt", [1, 0]), self._embedding("发热", vector, **extra)]
                # io deliberately disallows nonfinite JSON; write it raw for parser rejection.
                if any(not isinstance(value, (float, int)) or value == float("inf") for value in vector):
                    path = Path(self.config["embeddings_input"])
                    path.write_text('{"text":"x","embedding":[Infinity]}\n', encoding="utf-8")
                else:
                    write_jsonl(self.config["embeddings_input"], records)
                with self.assertRaises((SchemaInvalidError, HashMismatchError)):
                    build_semantic_cache(self.config, self.root / f"invalid_{number}")

    def test_duplicate_precomputed_text_and_missing_text_are_rejected(self):
        self.vectors.append(self.vectors[0])
        self._write_inputs()
        with self.assertRaisesRegex(SchemaInvalidError, "unique"):
            build_semantic_cache(self.config, self.root / "duplicates")
        self.vectors = self.vectors[:1]
        self._write_inputs()
        with self.assertRaisesRegex(SchemaInvalidError, "missing for literal text"):
            build_semantic_cache(self.config, self.root / "missing")

    def test_truncation_is_explicit_and_preserved(self):
        self.vectors[0].update(token_count=100, truncated=True)
        self._write_inputs()
        with self.assertRaisesRegex(SchemaInvalidError, "exceeds max_length"):
            build_semantic_cache(self.config, self.root / "overflow")
        self.config["encoder"] = {**self.encoder, "overflow": "truncate"}
        for row in self.vectors:
            row["encoder"] = self.config["encoder"]
        self._write_inputs()
        self._run()
        self.assertTrue(self._rows()[0]["sapbert_embeddings"]["sốt"]["truncated"])

    def test_local_snapshot_placeholder_is_validated_only_at_execution(self):
        config = {"local_path": str(self.root / "absent_snapshot")}
        normalized = validate_encoder_config(config)
        self.assertEqual(normalized["pooling"], "cls")
        self.config["encoder"] = config
        with self.assertRaises(FileNotFoundError):
            self._run()
        with self.assertRaises(SchemaInvalidError):
            validate_encoder_config({"revision": "main"})


if __name__ == "__main__":
    unittest.main()
