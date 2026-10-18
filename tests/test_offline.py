"""Test offline cho import package, truy vấn và dịch (không cần mạng hoặc GPU).
Chạy: python -m unittest discover tests"""
import importlib
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from query_processing import expand, pipeline, translate
from submit import submission

Q = "Metformin có gây thiếu vitamin B12 ở bệnh nhân đái tháo đường type 2 không?"
ENTS = [
    {"vi": "thiếu vitamin B12", "en": "vitamin B12 deficiency", "zh": "维生素B12缺乏"},
    {"vi": "đái tháo đường type 2", "en": "type 2 diabetes mellitus", "zh": "2型糖尿病"},
    {"vi": "suy thận", "en": "renal failure", "zh": "肾衰竭"},
    {"vi": "Metformin", "en": "metformin", "zh": "二甲双胍"},
]


class FakeBackend:
    def __init__(self, fn):
        self.fn, self.calls = fn, []

    def generate(self, convs):
        self.calls.extend(convs)
        return [self.fn(conv) for conv in convs]


class TestRestructuredImports(unittest.TestCase):
    def test_project_packages_import(self):
        modules = (
            "crawl.crawler", "index.bm25", "index.bm25_ent", "index.fuse",
            "rerank.chunk_rerank", "submit.score", "utils.audit", "utils.rate_limit",
            "query_processing.llm", "query_processing.expand", "query_processing.translate",
            "query_processing.pipeline",
        )
        for name in modules:
            with self.subTest(module=name):
                importlib.import_module(name)

    def test_chunk_selection_imports_index_package(self):
        with tempfile.TemporaryDirectory() as td:
            store = os.path.join(td, "store.sqlite")
            conn = sqlite3.connect(store)
            conn.execute("CREATE TABLE doc (doc_id TEXT, body TEXT)")
            conn.execute("CREATE TABLE chunk (chunk_id INTEGER PRIMARY KEY, doc_id TEXT, start INTEGER, end INTEGER)")
            body = "Đau đầu và sốt nhẹ."
            conn.execute("INSERT INTO doc VALUES ('1', ?)", (body,))
            conn.execute("INSERT INTO chunk (doc_id, start, end) VALUES ('1', 0, ?)", (len(body),))
            conn.commit()
            conn.close()

            chunks = submission.fetch_chunks(store, ["1"], 1, qtext="đau đầu")
            self.assertEqual(chunks, [{"doc_id": "1", "chunk_text": body}])

    def test_pipeline_jsonl_helpers(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "rows.jsonl")
            rows = [{"id": 1, "query": "câu hỏi"}]
            pipeline.write_jsonl(path, rows)
            self.assertEqual(pipeline.read_jsonl(path), rows)

    def test_cached_expansions_drop_obsolete_pubmed_queries(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "expansions.jsonl"
            pipeline.write_jsonl(path, [{
                "id": 1, "query": Q, "en": "question", "zh": "问题",
                "entities": [], "parse_ok": True, "pubmed_queries": ["obsolete"],
            }])
            rows = pipeline.stage_expand(SimpleNamespace(regen=False), [], Path(td))
            self.assertNotIn("pubmed_queries", rows[0])
            self.assertNotIn("pubmed_queries", pipeline.read_jsonl(path)[0])


class TestQueryExpansion(unittest.TestCase):
    def test_parse_think_fence_and_ignore_unknown_fields(self):
        text = ('<think>ẩn</think>```json\n'
                '{"en":"English question","zh":"中文问题",'
                '"entities":[{"vi":"đau đầu","en":"headache","zh":"头痛"}],'
                '"irrelevant":"ignored"}\n```')
        parsed = expand.parse_llm_output(text)
        self.assertTrue(parsed["parse_ok"])
        self.assertEqual(parsed["entities"][0]["en"], "headache")
        self.assertNotIn("pubmed_queries", parsed)

    def test_bad_json_and_salvage(self):
        self.assertFalse(expand.parse_llm_output("xin lỗi, tôi không biết")["parse_ok"])
        blob = ('{"en": "I have congestion and come"\n), "zh": "我有食管充血",'
                ' "entities": [{"vi": "thực quản", "en": "esophagus", "zh": "食管"}]}')
        with self.assertRaises(json.JSONDecodeError):
            json.loads(blob)
        parsed = expand.parse_llm_output(blob)
        self.assertTrue(parsed["parse_ok"])
        self.assertEqual(parsed["zh"], "我有食管充血")
        self.assertEqual(parsed["entities"][0]["en"], "esophagus")

    def test_expand_batch_has_no_pubmed_fields(self):
        output = json.dumps({"en": "Does metformin affect B12?", "zh": "二甲双胍影响B12吗？",
                             "entities": ENTS})
        backend = FakeBackend(lambda _: output)
        rows = expand.expand_queries(backend, [{"id": 1, "query": Q}])
        self.assertEqual(rows[0]["id"], 1)
        self.assertTrue(rows[0]["parse_ok"])
        self.assertNotIn("pubmed_queries", rows[0])


class TestTranslate(unittest.TestCase):
    def test_glossary_filters_and_sorts(self):
        glossary = translate.build_glossary(Q, ENTS, "zh")
        self.assertNotIn(("suy thận", "肾衰竭"), glossary)
        self.assertEqual(glossary[0][0], "đái tháo đường type 2")
        self.assertEqual(len(glossary), 3)

    def test_prompts_follow_model_card(self):
        en = translate.build_prompt(Q, "en", translate.build_glossary(Q, ENTS, "en"))
        self.assertTrue(en.startswith("Reference the following translations:"))
        self.assertIn("Metformin translates to metformin", en)
        zh = translate.build_prompt(Q, "zh", translate.build_glossary(Q, ENTS, "zh"))
        self.assertTrue(zh.startswith("参考下面的翻译："))
        self.assertIn("翻译为中文", zh)
        self.assertTrue(translate.build_prompt(Q, "en", []).startswith(
            "Translate the following text into English."))

    def test_translate_and_enrich(self):
        def fake(conv):
            content = conv[0]["content"]
            self.assertEqual(len(conv), 1)
            return "Does metformin cause B12 deficiency?" if "English" in content else "二甲双胍会导致B12缺乏吗？"

        expansions = [{"id": 2, "query": Q, "entities": ENTS,
                       "en": "draft en", "zh": "draft zh"}]
        translations = translate.translate_queries(FakeBackend(fake), expansions)
        enriched = translate.enrich(expansions, translations)
        self.assertEqual(enriched[0]["en"], "Does metformin cause B12 deficiency?")
        self.assertEqual(enriched[0]["translation_source"], "hy-mt2")
        self.assertNotIn("pubmed_queries", enriched[0])


if __name__ == "__main__":
    unittest.main()
