"""Bounded, label-free post-fusion document selection checks."""
import copy
import json
import unittest
from unittest.mock import patch

from TXT.bear.contracts import SchemaInvalidError
from TXT.bear.medical_selection import cherry_pick, validate_selection_config


def fixture():
    record = {"id": 1, "query": "query", "ranking": [
        {"doc_id": "a", "fused_score": 0.9}, {"doc_id": "b", "fused_score": 0.8},
        {"doc_id": "c", "fused_score": 0.7}], "selection": {"doc_ids": ["c", "a", "b"]},
        "gold": ["must-never-send"]}
    documents = [{"doc_id": name, "title": "title", "body": "body for " + name,
                  "labels": ["must-never-send"]} for name in "abc"]
    return record, documents


class TestMedicalSelection(unittest.TestCase):
    @patch("TXT.bear.medical_selection._chat")
    def test_selector_preserves_scores_order_and_sends_no_labels(self, chat):
        chat.return_value = ('{"selected_doc_ids":["c","a"]}', {"usage": {"total_tokens": 10}})
        record, documents = fixture()
        before = copy.deepcopy((record, documents))
        result = cherry_pick(record, documents, {}, {})
        self.assertEqual(result["doc_ids"], ["a", "c"])
        self.assertEqual((record, documents), before)
        payload = json.loads(chat.call_args.args[0][1]["content"])
        self.assertEqual(set(payload), {"query", "documents"})
        self.assertNotIn("must-never-send", json.dumps(payload))
        self.assertFalse(result["metadata"]["scores_modified"])

    @patch("TXT.bear.medical_selection._chat")
    def test_shortlist_is_bounded_and_prefix_truncation_is_logged(self, chat):
        chat.return_value = ('{"selected_doc_ids":["a"]}', {})
        record, documents = fixture()
        result = cherry_pick(record, documents, {}, {"max_candidates": 2, "document_max_chars": 7})
        payload = json.loads(chat.call_args.args[0][1]["content"])
        self.assertEqual(result["shortlist_doc_ids"], ["a", "b"])
        self.assertEqual(result["shortlist_removed_count"], 1)
        self.assertTrue(all(row["truncated"] for row in result["truncation"]))
        self.assertTrue(all(len(row["title"]) + len(row["body"]) == 7 for row in payload["documents"]))

    @patch("TXT.bear.medical_selection._chat")
    def test_minimum_fills_and_maximum_caps_by_original_scores(self, chat):
        record, documents = fixture()
        chat.return_value = ('{"selected_doc_ids":["c"]}', {})
        result = cherry_pick(record, documents, {}, {"min_docs": 2, "max_docs": 2})
        self.assertEqual(result["doc_ids"], ["a", "c"])
        self.assertEqual(result["fallback_added_doc_ids"], ["a"])
        chat.return_value = ('{"selected_doc_ids":["c","a","b"]}', {})
        result = cherry_pick(record, documents, {}, {"max_docs": 1})
        self.assertEqual(result["doc_ids"], ["a"])
        self.assertEqual(result["cap_removed_count"], 2)

    @patch("TXT.bear.medical_selection._chat")
    def test_rejects_invented_duplicate_ids_and_invalid_json(self, chat):
        record, documents = fixture()
        responses = ['{"selected_doc_ids":["invented"]}', '{"selected_doc_ids":["a","a"]}',
                     '```json\n{}\n```', '{"selected_doc_ids":[],"reason":"extra"}',
                     '{"selected_doc_ids":[],"selected_doc_ids":["a"]}']
        for response in responses:
            chat.return_value = (response, {})
            with self.subTest(response=response), self.assertRaises(SchemaInvalidError):
                cherry_pick(record, documents, {}, {})

    @patch("TXT.bear.medical_selection._chat")
    def test_may_select_none_and_empty_shortlists_skip_llm(self, chat):
        record, documents = fixture()
        chat.return_value = ('{"selected_doc_ids":[]}', {})
        self.assertEqual(cherry_pick(record, documents, {}, {})["doc_ids"], [])
        record["selection"]["doc_ids"] = []
        chat.reset_mock()
        result = cherry_pick(record, documents, {}, {"min_docs": 1})
        self.assertTrue(result["minimum_unmet"])
        self.assertTrue(result["metadata"]["skipped_empty_shortlist"])
        chat.assert_not_called()

    @patch("TXT.bear.medical_selection._chat")
    def test_only_already_selected_ids_enter_shortlist(self, chat):
        record, documents = fixture()
        record["selection"]["doc_ids"] = ["b", "c"]
        chat.return_value = ('{"selected_doc_ids":["a"]}', {})
        with self.assertRaisesRegex(SchemaInvalidError, "outside"):
            cherry_pick(record, documents, {}, {})

    def test_invalid_budgets_and_missing_document_text_fail(self):
        for config in ({"max_candidates": 0}, {"max_candidates": True}, {"min_docs": 3, "max_docs": 2},
                       {"document_max_chars": 0}, {"unknown": 1}, {"min_docs": 41}):
            with self.subTest(config=config), self.assertRaises(SchemaInvalidError):
                validate_selection_config(config)
        record, documents = fixture()
        with self.assertRaisesRegex(SchemaInvalidError, "Missing text"):
            cherry_pick(record, documents[:1], {}, {})
        with self.assertRaisesRegex(SchemaInvalidError, "unique"):
            cherry_pick(record, documents + documents[:1], {}, {})


if __name__ == "__main__":
    unittest.main()
