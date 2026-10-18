"""Test offline cho các hàm parse và gộp kết quả (không cần mạng, không cần GPU).
Chạy: python -m unittest discover tests"""
import importlib
import json
import os
import sqlite3
import tempfile
import unittest

from submit import submission
from pubmed_module.fetch import parse_biocjson, parse_efetch_xml, epmc_fetch, strip_tags
from pipelines.pubmed import merge_hits
from query_processing.query_gen import parse_llm_output, fallback_queries
from pubmed_module.search import is_pubmed_syntax

DOC = {"id": "26739349", "passages": [
    {"infons": {"type": "title"}, "offset": 0, "text": "Kidney stones and obstruction."},
    {"infons": {"type": "abstract"}, "offset": 31, "text": "Background text. Results text."}]}


class TestRestructuredImports(unittest.TestCase):
    def test_project_packages_import(self):
        modules = (
            "crawl.crawler", "index.bm25", "index.bm25_ent", "index.fuse", "rerank.chunk_rerank",
            "submit.score", "utils.audit", "utils.rate_limit",
            "query_processing.llm", "query_processing.query_gen", "query_processing.translate",
            "pipelines.pubmed",
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


class TestBioC(unittest.TestCase):
    def test_pubtator3_wrapper(self):
        out = parse_biocjson(json.dumps({"PubTator3": [DOC]}))
        self.assertEqual(out["26739349"]["title"], "Kidney stones and obstruction.")
        self.assertIn("Results text.", out["26739349"]["abstract"])

    def test_list_and_jsonl(self):
        self.assertIn("26739349", parse_biocjson(json.dumps([DOC])))
        self.assertIn("26739349", parse_biocjson(json.dumps(DOC) + "\n" + json.dumps(DOC)))

    def test_empty(self):
        self.assertEqual(parse_biocjson(""), {})
        self.assertEqual(parse_biocjson("not json"), {})


class TestEFetch(unittest.TestCase):
    def test_structured_abstract(self):
        xml = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article>
        <ArticleTitle>A <i>study</i> of stones</ArticleTitle><Abstract>
        <AbstractText Label="BACKGROUND">Bg.</AbstractText><AbstractText Label="RESULTS">Res.</AbstractText>
        </Abstract></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>"""
        out = parse_efetch_xml(xml)
        self.assertEqual(out["123"]["title"], "A study of stones")
        self.assertEqual(out["123"]["abstract"], "BACKGROUND: Bg.\nRESULTS: Res.")


class TestEuropePMC(unittest.TestCase):
    """Europe PMC là nguồn nội dung thực tế đang dùng: NCBI chặn IP (đo 01/10/2026)."""

    class FakeClient:
        """Trả JSON cố định, ghi lại params để kiểm cú pháp truy vấn."""

        def __init__(self, payload):
            self.payload, self.calls = payload, []

        def get_text(self, url, params, limiter, use_cache=True):
            self.calls.append(params)
            return json.dumps(self.payload)

    def test_strip_tags_giu_nguyen_chu(self):
        # Abstract Europe PMC chèn thẻ tiêu đề mục; bỏ thẻ, KHÔNG viết lại chữ
        self.assertEqual(strip_tags("<h4>Objectives</h4>Guidelines recommend screening."),
                         "Objectives\nGuidelines recommend screening.")
        self.assertEqual(strip_tags(""), "")
        self.assertEqual(strip_tags(None), "")
        self.assertEqual(strip_tags("không có thẻ nào"), "không có thẻ nào")

    def test_parse_va_cu_phap_truy_van(self):
        c = self.FakeClient({"resultList": {"result": [
            {"pmid": "42567282", "title": "Metformin and B12.",
             "abstractText": "<h4>Aim</h4>Đo tỉ lệ."},
            {"pmid": "42504166", "title": "Chỉ có title."},
            {"pmid": "", "title": "Thiếu pmid, phải bị bỏ"},
            {"pmid": "999", "title": "", "abstractText": ""},   # rỗng cả hai -> bỏ
        ]}})
        got = epmc_fetch(c, ["42567282", "42504166", "", "999"])
        self.assertEqual(set(got), {"42567282", "42504166"})
        self.assertEqual(got["42567282"]["source"], "europepmc")
        self.assertEqual(got["42567282"]["abstract"], "Aim\nĐo tỉ lệ.")
        self.assertEqual(got["42504166"]["abstract"], "")
        # Phải giới hạn ở PubMed và hỏi đúng các PMID được yêu cầu
        q = c.calls[0]["query"]
        self.assertIn("SRC:MED", q)
        self.assertIn("EXT_ID:42567282", q)
        self.assertEqual(c.calls[0]["resultType"], "core")

    def test_chia_batch_25(self):
        c = self.FakeClient({"resultList": {"result": []}})
        epmc_fetch(c, [str(i) for i in range(60)])
        self.assertEqual(len(c.calls), 3)          # 25 + 25 + 10

    def test_loi_mang_khong_lam_crash(self):
        class Boom:
            def get_text(self, *a, **k):
                raise RuntimeError("mạng lỗi")
        self.assertEqual(epmc_fetch(Boom(), ["1"]), {})


class TestLLMParse(unittest.TestCase):
    def test_think_and_fence(self):
        text = '<think>hmm</think>```json\n{"en":"Q","zh":"问","entities":[{"en":"x"}],' \
               '"pubmed_queries":["a b","A B","c d",""]}\n```'
        p = parse_llm_output(text)
        self.assertTrue(p["parse_ok"])
        self.assertEqual(p["pubmed_queries"], ["a b", "c d"])  # bỏ trùng + rỗng

    def test_garbage_and_fallback(self):
        p = parse_llm_output("xin lỗi, tôi không biết")
        self.assertFalse(p["parse_ok"])
        self.assertEqual(fallback_queries({"en": "Q", "entities": [{"en": "a"}, {"en": "b"}]}), ["Q", "a b"])

    def test_salvage_json_hong_cu_phap(self):
        """JSON hỏng cú pháp vẫn phải vớt được zh + entities.

        Mẫu lấy từ output thật của Qwen3.5-9B lượng tử 4-bit (03/10): 17,2% câu có một dấu
        `)` và newline chen vào sau dấu nháy đóng. Mất `zh` là mất đúng thứ nhánh tiếng
        Trung cần, nên không được trả rỗng khi `json.loads` thất bại.
        """
        blob = ('{"en": "I have congestion and come"\n)", "zh": "我有食管充血",'
                ' "entities": [{"vi": "thực quản", "en": "esophagus", "zh": "食管"}],'
                ' "pubmed_queries": ["esophageal congestion", "peptic ulcer scar"]}')
        with self.assertRaises(json.JSONDecodeError):      # mẫu phải thật là hỏng
            json.loads(blob)
        p = parse_llm_output(blob)
        self.assertTrue(p["parse_ok"])
        self.assertEqual(p["zh"], "我有食管充血")
        self.assertEqual(p["entities"], [{"vi": "thực quản", "en": "esophagus", "zh": "食管"}])
        self.assertEqual(p["pubmed_queries"], ["esophageal congestion", "peptic ulcer scar"])


class TestMerge(unittest.TestCase):
    def test_rrf(self):
        res = merge_hits([{"src": "ncbi", "q": 0, "pmids": ["1", "2"]},
                          {"src": "epmc", "q": 0, "pmids": ["2", "3"]}])
        self.assertEqual(res[0]["pmid"], "2")  # xuất hiện ở cả hai nguồn
        self.assertEqual(len(res[0]["hits"]), 2)

    def test_syntax(self):
        self.assertTrue(is_pubmed_syntax('"Kidney Calculi"[MeSH Terms]'))
        self.assertFalse(is_pubmed_syntax("kidney stone obstruction"))


if __name__ == "__main__":
    unittest.main()


# ---------- Bước dịch Hy-MT2 và luồng expand/translate với backend giả ----------
from query_processing.query_gen import expand_queries, build_messages
from query_processing.translate import build_glossary, build_prompt, enrich, translate_queries

Q = "Metformin có gây thiếu vitamin B12 ở bệnh nhân đái tháo đường type 2 không?"
ENTS = [{"vi": "thiếu vitamin B12", "en": "vitamin B12 deficiency", "zh": "维生素B12缺乏"},
        {"vi": "đái tháo đường type 2", "en": "type 2 diabetes mellitus", "zh": "2型糖尿病"},
        {"vi": "suy thận", "en": "renal failure", "zh": "肾衰竭"},  # không có trong câu -> bỏ
        {"vi": "Metformin", "en": "metformin", "zh": "二甲双胍"}]


class FakeBackend:
    def __init__(self, fn):
        self.fn, self.calls = fn, []

    def generate(self, convs):
        self.calls.extend(convs)
        return [self.fn(c) for c in convs]


class TestTranslate(unittest.TestCase):
    def test_glossary_filters_and_sorts(self):
        gl = build_glossary(Q, ENTS, "zh")
        self.assertNotIn(("suy thận", "肾衰竭"), gl)
        self.assertEqual(gl[0][0], "đái tháo đường type 2")  # dài nhất trước
        self.assertEqual(len(gl), 3)

    def test_prompts_follow_model_card(self):
        p_en = build_prompt(Q, "en", build_glossary(Q, ENTS, "en"))
        self.assertTrue(p_en.startswith("Reference the following translations:"))
        self.assertIn("Metformin translates to metformin", p_en)
        p_zh = build_prompt(Q, "zh", build_glossary(Q, ENTS, "zh"))
        self.assertTrue(p_zh.startswith("参考下面的翻译："))
        self.assertIn("翻译为中文", p_zh)
        self.assertTrue(build_prompt(Q, "en", []).startswith("Translate the following text into English."))

    def test_translate_and_enrich(self):
        def fake(conv):
            content = conv[0]["content"]
            self.assertEqual(len(conv), 1)  # không có system prompt
            return "  Does metformin cause B12 deficiency?\n" if "English" in content else "二甲双胍会导致B12缺乏吗？"
        exps = [{"id": 2, "query": Q, "entities": ENTS, "en": "draft en", "zh": "draft zh",
                 "pubmed_queries": ["metformin b12"]},
                {"id": 3, "query": "Câu khác", "entities": [], "en": "draft3", "zh": "",
                 "pubmed_queries": []}]
        tr = translate_queries(FakeBackend(fake), exps[:1])
        self.assertEqual(tr[0]["en"], "Does metformin cause B12 deficiency?")
        rows = enrich(exps, tr)
        self.assertEqual(rows[0]["translation_source"], "hy-mt2")
        self.assertEqual(rows[0]["en_llm"], "draft en")
        self.assertEqual(rows[1]["en"], "draft3")  # không có bản Hy-MT2 -> dùng bản nháp
        self.assertEqual(rows[1]["translation_source"], "llm")


class TestExpandFlow(unittest.TestCase):
    def test_expand_with_fallback(self):
        good = json.dumps({"en": "E", "zh": "Z", "entities": ENTS, "pubmed_queries": ["q1", "q2"]})
        outs = iter([good, "không phải JSON"])
        be = FakeBackend(lambda c: next(outs))
        rows = expand_queries(be, [{"id": 1, "query": Q}, {"id": 2, "query": "x"}])
        self.assertEqual(rows[0]["pubmed_queries"], ["q1", "q2"])
        self.assertFalse(rows[1]["parse_ok"])
        self.assertEqual(be.calls[0], build_messages(Q))
