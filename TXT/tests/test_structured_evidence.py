"""Behavioral checks for anchored relation evidence and original body offsets."""

from __future__ import annotations

import unicodedata
import unittest

from TXT.bear.structured_evidence import query_terms, query_text, score_evidence, tokenize


def relation_query(text="aspirin prevents stroke", **relation):
    return {"query": text, "relations": [{"subject": "aspirin", "predicate": "prevents",
                                          "object": "stroke", **relation}]}


class StructuredEvidenceTests(unittest.TestCase):
    def assert_body_spans(self, result, body):
        for span in result["matched_spans"]:
            self.assertEqual(body[span["start"]:span["end"]], span["text"])
        for entity in result["entity_results"]:
            for span in entity["spans"]:
                self.assertEqual(body[span["start"]:span["end"]], span["text"])
        for relation in result["relation_results"]:
            for binding in relation["supporting_bindings"] + relation["conflicting_bindings"]:
                for role in ("subject", "predicate", "object", "sentence"):
                    span = binding[role]
                    self.assertEqual(body[span["start"]:span["end"]], span["text"])
                for span in binding["negation_spans"]:
                    self.assertEqual(body[span["start"]:span["end"]], span["text"])

    def test_ordered_relation_requires_its_actual_role_binding(self):
        query = relation_query()
        good = score_evidence(query, "Aspirin prevents stroke.")
        reverse = score_evidence(query, "Stroke prevents aspirin.")
        missing = score_evidence(query, "Aspirin prevents headache.")
        split = score_evidence(query, "Aspirin prevents headache. Stroke is another disease.")
        self.assertEqual(good["structured_status"], "available")
        self.assertEqual(good["relation_support"], 1)
        for result in (reverse, missing, split):
            self.assertEqual(result["relation_support"], 0)
            self.assertEqual(result["relation_conflict"], 0)
            self.assertEqual(result["relation_results"][0]["status"], "missing")
            self.assertLess(result["evidence_score"], good["evidence_score"])

    def test_conflict_requires_same_binding_and_local_negation(self):
        query = relation_query()
        conflict = score_evidence(query, "Aspirin does not prevents stroke.")
        unrelated = score_evidence(query, "Ibuprofen does not prevents headache. Aspirin prevents stroke.")
        following = score_evidence(query, "Aspirin prevents stroke but it does not help sleep.")
        mixed = score_evidence(query, "Aspirin prevents stroke. Aspirin does not prevents stroke.")
        self.assertEqual(conflict["relation_conflict"], 1)
        self.assertEqual(conflict["relation_support"], 0)
        self.assertEqual(conflict["relation_results"][0]["conflicting_bindings"][0]["negation_spans"][0]["text"], "not")
        for result in (unrelated, following):
            self.assertEqual(result["relation_support"], 1)
            self.assertEqual(result["relation_conflict"], 0)
        self.assertEqual(mixed["relation_results"][0]["status"], "mixed")
        self.assertEqual(mixed["relation_conflict"], 1)
        self.assertEqual(mixed["effective_relation_conflict"], 0)
        self.assertEqual(mixed["evidence_score"], unrelated["evidence_score"])
        self.assertGreater(mixed["evidence_score"], conflict["evidence_score"])

    def test_vietnamese_negation_and_expected_negative_relation(self):
        query = {"query": "thuốc A không gây xuất huyết", "relations": [
            {"subject": "thuốc A", "predicate": "gây", "object": "xuất huyết"}]}
        negative = score_evidence(query, "Thuốc A không gây xuất huyết.")
        positive = score_evidence(query, "Thuốc A gây xuất huyết.")
        self.assertEqual(negative["relation_support"], 1)
        self.assertEqual(positive["relation_conflict"], 1)
        self.assertEqual(positive["relation_results"][0]["expected_polarity"], "negative")
        self.assertEqual(score_evidence(relation_query(), "Aspirin not only prevents stroke.")["relation_support"], 1)

    def test_invalid_unanchored_or_reversed_query_relations_do_not_score(self):
        for query in (relation_query("aspirin treats headache"),
                      relation_query("stroke prevents aspirin"),
                      relation_query("aspirin prevents. stroke"),
                      relation_query(polarity="negative")):
            result = score_evidence(query, "aspirin prevents stroke")
            self.assertEqual(result["structured_status"], "invalid")
            self.assertEqual(result["relation_count"], 0)
            self.assertTrue(result["invalid_relations"])
            self.assertEqual(result["relation_support"], 0)
            self.assertEqual(result["relation_conflict"], 0)

    def test_unicode_original_offsets_survive_nfd_and_whitespace(self):
        query = {"query": "thuốc A gây viêm phổi", "entities": ["viêm phổi"], "relations": [
            {"subject": "thuốc A", "predicate": "gây", "object": "viêm phổi"}]}
        body = "Mở đầu. " + unicodedata.normalize("NFD", "Thuốc A gây viêm") + "\t  " + unicodedata.normalize("NFD", "phổi.")
        result = score_evidence(query, body)
        self.assertEqual(result["relation_support"], 1)
        self.assertEqual(result["entity_coverage"], 1)
        self.assert_body_spans(result, body)
        span = result["entity_results"][0]["spans"][0]
        self.assertIn("\t  ", span["text"])
        self.assertEqual(unicodedata.normalize("NFC", span["text"]).replace("\t  ", " "), "viêm phổi")

    def test_raw_query_is_explicitly_lexical_fallback(self):
        raw = score_evidence("aspirin prevents stroke", "Aspirin prevents stroke.")
        self.assertEqual(raw["structured_status"], "unavailable")
        self.assertEqual(raw["relation_results"], [])
        self.assertEqual(raw["lexical_coverage"], 1)
        self.assertEqual(raw["evidence_score"], 1)
        self.assertEqual(score_evidence("aspirin", {"body": None})["evidence_score"], 0)
        self.assertEqual(score_evidence("aspirin", {"body": None})["evidence_status"], "missing_text")

    def test_protected_tokens_and_ordinary_unicode_boundaries(self):
        self.assertEqual(tokenize("PD-1 BRCA1 0.5 0,5 viêm phổi"), ["pd-1", "brca1", "0.5", "0,5", "viêm", "phổi"])
        for phrase, body in (("BRCA1", "BRCA10"), ("type 1", "type 2"), ("5 mg", "15 mg"),
                             ("5 mg", "0.5 mg"), ("5 mg", "0,5 mg"), ("PD-1", "PD-10"),
                             ("viêm", "xviêm"), ("viêm", "viêmy"), ("viêm", "viem")):
            query = {"query": phrase, "entities": [phrase]}
            result = score_evidence(query, body)
            self.assertEqual(result["entity_coverage"], 0, (phrase, body))
        decimal = score_evidence("5", "0.5 and 0,5 and 15")
        self.assertEqual(decimal["lexical_coverage"], 0)

    def test_entity_mapping_must_be_anchored_and_labels_are_ignored(self):
        query = {"query": "ung thư phổi", "entities": [
            {"vi": "ung thư phổi", "en": "lung cancer"},
            {"vi": "ung thư gan", "en": "liver cancer"}], "labels": ["liver cancer"]}
        result = score_evidence(query, {"body": "Lung cancer therapy.", "lang": "en"})
        self.assertEqual(result["entity_count"], 1)
        self.assertEqual(result["entity_coverage"], 1)
        self.assertEqual(len(result["invalid_entities"]), 1)
        self.assertIn("lung", query_terms(query))
        self.assertNotIn("liver", query_terms(query))
        other = score_evidence({**query, "labels": ["a completely different judgment"]}, {"body": "Lung cancer therapy.", "lang": "en"})
        self.assertEqual(result, other)
        self.assertEqual(query_text(query), "ung thư phổi")

    def test_best_chunk_is_local_and_spans_remain_original_body_offsets(self):
        body = "Aspirin was tested. Aspirin prevents stroke."
        split = body.index("Aspirin", 1)
        refs = [{"doc_id": "d1", "chunk_id_native": "a", "start": 0, "end": split},
                {"doc_id": "d1", "chunk_id_native": "b", "start": split, "end": len(body)}]
        result = score_evidence(relation_query(), {"doc_id": "d1", "body": body}, refs)
        self.assertEqual(result["best_evidence_chunk_ref"], refs[1])
        for chunk in result["chunk_features"]:
            self.assert_body_spans(chunk, body)
        result = score_evidence("aspirin", {"doc_id": "d1", "body": body}, [
            {"doc_id": "other", "start": 0, "end": 8}, {"doc_id": "d1", "start": 0, "end": 1000}])
        self.assertIsNone(result["best_evidence_chunk_ref"])
        self.assertEqual(len(result["invalid_chunk_refs"]), 2)

    def test_no_relation_across_newlines_or_independent_clauses(self):
        for body in ("Aspirin prevents\nstroke", "Aspirin does not help, ibuprofen prevents stroke",
                     "Aspirin is useful but ibuprofen prevents stroke"):
            result = score_evidence(relation_query(), body)
            self.assertEqual(result["relation_support"], 0)
            self.assertEqual(result["relation_conflict"], 0)

    def test_repeated_predicates_cannot_bind_different_assertions(self):
        query = {"query": "A treats C", "relations": [
            {"subject": "A", "predicate": "treats", "object": "C"}]}
        for body in ("A treats B and D treats C", "A treats B and D not treats C",
                     "A treats B D treats C", "A treats B D not treats C"):
            result = score_evidence(query, body)
            self.assertEqual(result["relation_support"], 0, body)
            self.assertEqual(result["relation_conflict"], 0, body)
        self.assertEqual(score_evidence(query, "A treats B and A treats C")["relation_support"], 1)

    def test_uncomposed_unicode_marks_remain_exact_tokens(self):
        marked = "a\u20dd"  # enclosing circle has no NFC-composed equivalent
        self.assertEqual(tokenize(marked), [marked])
        self.assertEqual(score_evidence(marked, marked)["lexical_coverage"], 1)
        self.assertEqual(score_evidence("a", marked)["lexical_coverage"], 0)


if __name__ == "__main__":
    unittest.main()
