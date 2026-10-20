import unittest

from agent_retrieval.select_metadata import build_prompt, parse_selection


class TestMetadataSelection(unittest.TestCase):
    def test_parse_selection_ignores_thinking_and_accepts_integer_ids(self):
        answer = '<think>reasoning</think>{"selected_ids":[12,"34"]}'
        self.assertEqual(parse_selection(answer, {"12", "34", "56"}, 2), ["12", "34"])

    def test_rejects_ids_outside_candidate_pool(self):
        with self.assertRaisesRegex(ValueError, "ngoài danh sách"):
            parse_selection('{"selected_ids":[99]}', {"12", "34"}, 1)

    def test_rejects_wrong_count_and_duplicates(self):
        with self.assertRaisesRegex(ValueError, "Cần 2 doc"):
            parse_selection('{"selected_ids":["12"]}', {"12", "34"}, 2)
        with self.assertRaisesRegex(ValueError, "trùng"):
            parse_selection('{"selected_ids":["12","12"]}', {"12", "34"}, 2)

    def test_prompt_contains_metadata_but_not_document_body(self):
        prompt = build_prompt("câu hỏi", [("12", {"title": "Tiêu đề"})])
        self.assertIn("Tiêu đề", prompt)
        self.assertIn("câu hỏi", prompt)
        self.assertNotIn("body", prompt)


if __name__ == "__main__":
    unittest.main()
