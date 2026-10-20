import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from agent_retrieval import review_borderline
from agent_retrieval.review_borderline import (
    apply_reviews,
    build_prompt,
    choose_borderline,
    parse_decision,
)


class TestBorderlineReview(unittest.TestCase):
    def test_picks_candidates_closest_to_cutoff(self):
        rows = [
            {"doc_id": "a", "p_hat": 0.05},
            {"doc_id": "b", "p_hat": 0.119},
            {"doc_id": "c", "p_hat": 0.121},
            {"doc_id": "d", "p_hat": 0.8},
        ]
        self.assertEqual(
            [r["doc_id"] for r in choose_borderline(rows, 0.12, 2)], ["b", "c"]
        )

    def test_parses_only_supported_decisions(self):
        self.assertEqual(
            parse_decision('<think>check</think>{"decision":"topic_only"}'),
            "topic_only",
        )
        with self.assertRaises(ValueError):
            parse_decision('{"decision":"maybe"}')

    def test_reviews_override_only_clear_baseline_decisions(self):
        rows = [
            {"doc_id": "1", "p_hat": 0.9},
            {"doc_id": "2", "p_hat": 0.8},
            {"doc_id": "3", "p_hat": 0.2},
            {"doc_id": "4", "p_hat": 0.1},
        ]
        result = apply_reviews(
            ["1", "2"], rows,
            {"1": "topic_only", "3": "relevant", "4": "uncertain"},
        )
        self.assertEqual(result, ["2", "3"])

    def test_prompt_contains_full_body_and_relevance_rule(self):
        prompt = build_prompt("câu hỏi", {
            "title": "Tiêu đề", "descr": "Mô tả", "tags": "tag",
            "lang": "vi", "domain": "example.vn", "body": "Toàn bộ nội dung",
        })
        self.assertIn("Toàn bộ nội dung", prompt)
        self.assertIn("chỉ cùng bệnh/chủ đề", prompt)
        self.assertIn("câu hỏi", prompt)

    def test_run_promotes_llm_relevant_doc_near_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            base = os.path.join(td, "base.json")
            confidence = os.path.join(td, "confidence.json")
            queries = os.path.join(td, "queries.jsonl")
            db = os.path.join(td, "docs.sqlite")
            out = os.path.join(td, "reviewed.json")
            with open(base, "w", encoding="utf-8") as f:
                json.dump({"1": ["1"]}, f)
            with open(confidence, "w", encoding="utf-8") as f:
                json.dump({"threshold": 0.5, "queries": {"1": [
                    {"doc_id": "1", "p_hat": 0.52},
                    {"doc_id": "2", "p_hat": 0.49},
                    {"doc_id": "3", "p_hat": 0.9},
                ]}}, f)
            with open(queries, "w", encoding="utf-8") as f:
                f.write(json.dumps({"id": 1, "query": "câu hỏi"}, ensure_ascii=False) + "\n")
            conn = sqlite3.connect(db)
            conn.execute("CREATE TABLE doc (doc_id TEXT, title TEXT, descr TEXT, tags TEXT, lang TEXT, domain TEXT, body TEXT)")
            conn.executemany("INSERT INTO doc VALUES (?, '', '', '', 'vi', 'test', 'body')",
                             [("1",), ("2",), ("3",)])
            conn.commit()
            conn.close()
            with patch.object(review_borderline, "load_model", return_value=(None, None, None)), \
                    patch.object(review_borderline, "judge", return_value=("relevant", "judged")):
                review_borderline.run(base, confidence, queries, db, out, 1, "fake", 32)
            with open(out, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"1": ["1", "2"]})


if __name__ == "__main__":
    unittest.main()
