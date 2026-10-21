"""Tests for attributed expansion, contextual taxonomy, and exact concept gates."""

from __future__ import annotations

import copy
import io
import json
import tempfile
import unicodedata
import unittest
from pathlib import Path
from unittest.mock import patch

from TXT.bear.contracts import SchemaInvalidError
from TXT.bear.medical_kb import import_kb, load_kb, validate_kb
from TXT.bear.medical_documents import extract_document
from TXT.bear.medical_query import (
    _chat, find_term_spans, match_concepts, prepare_query, validate_llm_config, validate_prepared,
)


def fixture_kb():
    # Deliberately synthetic fixtures: these labels and relationships are not
    # clinical data and are never shipped as a usable medical knowledge base.
    return [{"disease": {"concept_id": "test:disease", "labels": {"vi": "bệnh thử A", "zh": "测试病甲"},
                          "aliases": {"vi": ["A-test"], "zh": []}},
             "symptom": {"concept_id": "test:symptom", "labels": {"vi": "triệu chứng thử", "zh": "测试表现"},
                         "aliases": {"vi": [], "zh": []}},
             "relation": "has_symptom", "source": {"name": "synthetic unit fixture", "record_id": "1"}}]


def model_json(intent="symptoms", text="bệnh thử A", concept_id="test:disease"):
    return {"intent": [intent], "concepts": [{"concept_id": concept_id, "text": text,
            "kind": "disease", "tier": 4, "required": True}], "selected_expansion_ids": []}


class MedicalQueryTests(unittest.TestCase):
    def test_document_candidates_preserve_negation_exact_offsets_and_http_scope(self):
        body = "Không có triệu chứng thử. Có biểu hiện khác."
        start = body.index("triệu chứng thử")
        raw = {"terms": [{"text": "triệu chứng thử", "field": "body", "kind": "symptom",
                          "assertion": "negated", "anchor": {"start": start, "end": start + len("triệu chứng thử")}}]}
        response = {"model": "Qwen/Qwen3.5-9B", "choices": [{"message": {"content": json.dumps(raw, ensure_ascii=False)}}]}
        with patch("TXT.bear.medical_query.urllib.request.urlopen", return_value=io.StringIO(json.dumps(response))) as request:
            result = extract_document({"doc_id": "test:doc", "title": "", "body": body, "lang": "vi"}, {})
        self.assertEqual(request.call_count, 1)
        term = result["terms"][0]
        self.assertEqual(body[term["anchor"]["start"]:term["anchor"]["end"]], term["text"])
        self.assertEqual(term["assertion"], "negated")
        self.assertFalse(result["truncated"])
        self.assertEqual(result["scope"], "diagnostic_term_candidates_only")
        self.assertFalse(result["metadata"]["index_modified"])

    def test_document_truncation_is_explicit_and_candidates_cannot_come_from_unseen_text(self):
        document = {"doc_id": "test:doc", "title": "", "body": "0123456789 bệnh thử A", "lang": "vi"}
        with patch("TXT.bear.medical_documents._chat") as chat:
            with self.assertRaises(SchemaInvalidError):
                extract_document(document, {"document_max_chars": 10})
            chat.assert_not_called()
        with patch("TXT.bear.medical_documents._chat", return_value=(json.dumps({"terms": []}), {})):
            result = extract_document(document, {"document_max_chars": 10, "document_overflow": "prefix"})
        self.assertTrue(result["truncated"])
        self.assertEqual(result["windows"][0], {"field": "body", "start": 0, "end": 10, "original_length": len(document["body"])})
        invented = {"terms": [{"text": "bệnh thử A", "field": "body", "kind": "disease", "assertion": "affirmed"}]}
        with patch("TXT.bear.medical_documents._chat", return_value=(json.dumps(invented), {})):
            with self.assertRaises(SchemaInvalidError):
                extract_document(document, {"document_max_chars": 10, "document_overflow": "prefix"})
        repeated = {"terms": [{"text": "A", "field": "body", "kind": "disease", "assertion": "affirmed"}]}
        with patch("TXT.bear.medical_documents._chat", return_value=(json.dumps(repeated), {})):
            with self.assertRaises(SchemaInvalidError):
                extract_document({**document, "body": "A rồi A"}, {})

    def test_http_payload_disables_thinking_and_checks_served_model(self):
        response = {"model": "Qwen/Qwen3.5-9B", "choices": [{"message": {"content": "{}"}}]}
        with patch("TXT.bear.medical_query.urllib.request.urlopen", return_value=io.StringIO(json.dumps(response))) as request:
            raw, metadata = _chat([], validate_llm_config({}))
        payload = json.loads(request.call_args.args[0].data)
        self.assertFalse(payload["chat_template_kwargs"]["enable_thinking"])
        self.assertEqual(raw, "{}")
        self.assertEqual(metadata["served_model"], "Qwen/Qwen3.5-9B")
        response["model"] = "unreviewed-large-model"
        with patch("TXT.bear.medical_query.urllib.request.urlopen", return_value=io.StringIO(json.dumps(response))):
            with self.assertRaises(SchemaInvalidError):
                _chat([], validate_llm_config({}))

    def prepared(self, response=None, kb=None, query="Triệu chứng của bệnh thử A?"):
        response = response or model_json()
        with patch("TXT.bear.medical_query._chat", return_value=(json.dumps(response, ensure_ascii=False),
                                                                 {"probability_method": "hard_tier"})):
            return prepare_query({"id": 7, "query": query, "lang": "vi"}, kb if kb is not None else fixture_kb(), {})

    def test_kb_requires_provenance_ids_and_consistent_concepts(self):
        rows = fixture_kb()
        self.assertEqual(validate_kb(rows)[0]["disease"]["concept_id"], "test:disease")
        for key in ("source", "disease"):
            broken = copy.deepcopy(rows)
            broken[0].pop(key)
            with self.assertRaises(SchemaInvalidError):
                validate_kb(broken)
        inconsistent = copy.deepcopy(rows) + copy.deepcopy(rows)
        inconsistent[1]["disease"]["labels"]["vi"] = "khác"
        with self.assertRaises(SchemaInvalidError):
            validate_kb(inconsistent)

    def test_canonical_and_cmeie_import_do_not_create_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            canonical = root / "kb.jsonl"
            canonical.write_text(json.dumps(fixture_kb()[0], ensure_ascii=False) + "\n", encoding="utf-8")
            self.assertEqual(load_kb(canonical)[0]["source"]["record_id"], "1")
            concepts = [dict(fixture_kb()[0][key], kind=key) for key in ("disease", "symptom")]
            concept_map = root / "map.json"
            concept_map.write_text(json.dumps(concepts, ensure_ascii=False), encoding="utf-8")
            source = root / "source.jsonl"
            record = {"text": "synthetic", "spo_list": [{"predicate": "临床表现", "subject": "测试病甲",
                                                          "object": {"@value": "测试表现"}}]}
            source.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
            config = {"format": "cmeie", "source_path": str(source), "concept_map_path": str(concept_map),
                      "source": {"name": "synthetic fixture"}}
            rows = import_kb(config)
            self.assertEqual(rows[0]["symptom"]["concept_id"], "test:symptom")
            record["spo_list"][0]["object"]["@value"] = "unmapped"
            source.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
            with self.assertRaises(SchemaInvalidError):
                import_kb(config)

    def test_prepare_keeps_literal_query_and_kb_expansion_separate(self):
        captured = {}

        def fake_chat(messages, config):
            # Inspect actual prompt whitelist instead of making up an allowed ID.
            content = messages[1]["content"]
            begin = content.index("{\n") if "{\n" in content else content.index("{\"original_query\"")
            payload, _ = json.JSONDecoder().raw_decode(content[begin:])
            captured.update(payload)
            response = model_json()
            response["selected_expansion_ids"] = [payload["kb_expansion_whitelist"][0]["expansion_id"]]
            response["concepts"][0]["confidence"] = 0.99  # Must never become token confidence.
            response["concepts"][0]["probabilities"] = [0, 0, 0, 1]
            return json.dumps(response, ensure_ascii=False), {"probability_method": "hard_tier"}

        with patch("TXT.bear.medical_query._chat", side_effect=fake_chat) as chat:
            result = prepare_query({"id": 1, "query": "Triệu chứng bệnh thử A", "lang": "vi"}, fixture_kb(), {})
        self.assertEqual(chat.call_count, 1)
        self.assertEqual(result["concepts"][0]["origin"], "query")
        self.assertIsNone(result["concepts"][0]["probabilities"])
        self.assertEqual(result["expansion_terms"][0]["origin"], "kb")
        self.assertEqual(result["expansion_terms"][0]["source"]["name"], "synthetic unit fixture")
        self.assertEqual(result["metadata"]["model"], "Qwen/Qwen3.5-9B")
        matches = match_concepts(result, "Chỉ triệu chứng thử")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["match"], 0)  # Expansion cannot masquerade as original evidence.

    def test_unanchored_fabricated_and_duplicate_llm_concepts_rejected(self):
        response = model_json(text="not in query")
        with self.assertRaises(SchemaInvalidError):
            self.prepared(response)
        response = model_json(concept_id="made-up")
        with self.assertRaises(SchemaInvalidError):
            self.prepared(response)
        response = model_json()
        response["concepts"] *= 2
        with self.assertRaises(SchemaInvalidError):
            self.prepared(response)
        response = model_json()
        response["selected_expansion_ids"] = ["invented-expansion"]
        with self.assertRaises(SchemaInvalidError):
            self.prepared(response)

    def test_reverse_diagnosis_is_not_offered_and_wrong_intent_is_rejected(self):
        captured = {}

        def fake_chat(messages, config):
            content = messages[1]["content"]
            payload, _ = json.JSONDecoder().raw_decode(content[content.index("{\"original_query\""):])
            captured.update(payload)
            return json.dumps({"intent": ["diagnosis"], "concepts": [], "selected_expansion_ids": []}), {}

        with patch("TXT.bear.medical_query._chat", side_effect=fake_chat):
            prepare_query({"id": 1, "query": "triệu chứng thử là bệnh gì", "lang": "vi"}, fixture_kb(), {})
        self.assertEqual(captured["kb_expansion_whitelist"], [])

        def wrong_intent(messages, config):
            content = messages[1]["content"]
            payload, _ = json.JSONDecoder().raw_decode(content[content.index("{\"original_query\""):])
            response = model_json(intent="dosage")
            response["selected_expansion_ids"] = [payload["kb_expansion_whitelist"][0]["expansion_id"]]
            return json.dumps(response), {}

        with patch("TXT.bear.medical_query._chat", side_effect=wrong_intent):
            with self.assertRaises(SchemaInvalidError):
                prepare_query({"id": 1, "query": "liều cho bệnh thử A", "lang": "vi"}, fixture_kb(), {})

    def test_anchor_alias_probability_provenance_and_model_size_guards(self):
        prepared = self.prepared()
        self.assertEqual(prepared["query"][prepared["concepts"][0]["anchor"]["start"]:
                                           prepared["concepts"][0]["anchor"]["end"]], "bệnh thử A")
        for mutate in (lambda x: x["concepts"][0]["anchor"].update(start=0),
                       lambda x: x["concepts"][0].update(probabilities=[0, 0, 0, 1], probability_method="self_report")):
            broken = copy.deepcopy(prepared)
            mutate(broken)
            with self.assertRaises(SchemaInvalidError):
                validate_prepared(broken)
        for config in ({"model": "big", "num_parameters_b": 15}, {"model": "unknown"},
                       {"num_parameters_b": True}, {"num_parameters_b": float("nan")}):
            with self.assertRaises(SchemaInvalidError):
                validate_llm_config(config)
        imported = copy.deepcopy(prepared)
        imported["concepts"][0].update(probabilities=[0.1, 0.2, 0.3, 0.4],
                                      probability_method="backend_label_logits",
                                      probability_provenance={"artifact": "backend-labels.jsonl", "sha256": "fixture"})
        self.assertEqual(validate_prepared(imported)["concepts"][0]["probabilities"], [0.1, 0.2, 0.3, 0.4])
        fabricated_alias = copy.deepcopy(prepared)
        fabricated_alias["concepts"][0]["aliases"]["vi"].append("fabricated alias")
        with self.assertRaises(SchemaInvalidError):
            validate_prepared(fabricated_alias, kb_rows=fixture_kb())
        labeled = dict(prepared, gold=["doc:1"])
        with self.assertRaises(SchemaInvalidError):
            validate_prepared(labeled)

    def test_match_boundaries_han_alias_grouping_and_original_unicode_offsets(self):
        self.assertEqual(find_term_spans("BRCA10", "BRCA1"), [])
        self.assertEqual(find_term_spans("15 mg; 0.5 mg; 0,5 mg", "5 mg"), [])
        self.assertEqual(len(find_term_spans("15 mg; 5 mg", "5 mg")), 1)
        self.assertEqual(find_term_spans("bệnh ábệnh", "bệnh"), [{"start": 0, "end": 4, "text": "bệnh"}])
        han = "患者测试病甲表现"
        self.assertEqual(len(find_term_spans(han, "测试病甲")), 1)
        prepared = self.prepared()
        body = "Mở đầu " + unicodedata.normalize("NFD", "BỆNH THỬ A") + ". A-test."
        matches = match_concepts(prepared, {"id": "bệnh thử A", "body": body, "title": "测试病甲"})
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["match"], 1)
        self.assertEqual(len(matches[0]["spans"]), 3)
        for span in matches[0]["spans"]:
            original = {"body": body, "title": "测试病甲"}[span["field"]]
            self.assertEqual(original[span["start"]:span["end"]], span["text"])
        self.assertEqual(match_concepts(prepared, {"body": "", "body_sha256": "bệnh thử A",
                                                   "body_hash": "A-test"})[0]["match"], 0)


if __name__ == "__main__":
    unittest.main()
