"""Invariants về scope, lane, source rank và missingness."""
import unittest
from TXT.bear.contracts import SchemaInvalidError
from TXT.bear.pools import build_pool, route_support
from TXT.bear.fusion import rank_query, rank_component, query_gate
from TXT.bear.evidence import coverage, query_evidence
from TXT.bear.matching import build_query_concepts, compute_concept_set_hash
from TXT.bear.experiments import split_queries, fixed_menu, select_dev


class TestPoolsFusion(unittest.TestCase):
    def setUp(self):
        self.base = [str(i) for i in range(1, 201)]
        self.lang = {d: "vi" for d in self.base + ["201", "202", "203"]}
        self.lang["2"] = self.lang["202"] = "zh"
        self.pool = build_pool(self.base, ["201", "202"], [], self.lang, set(self.lang))

    def test_baseline_first_extras_language_and_original_rank(self):
        self.assertEqual([r["doc_id"] for r in self.pool["reference"][:200]], self.base)
        self.assertEqual(self.pool["selectable_extra_vi_count"], 1)
        self.assertEqual(self.pool["reference"][-1]["reference_rank"], 202)
        self.assertIsNone(self.pool["reference"][-1]["baseline_rank"])
        support = route_support(["202", "203", "1"], self.lang, set(self.lang))
        self.assertEqual(support["docs"][0], {"doc_id": "203", "source_rank": 2})
        self.assertNotIn("203", [r["doc_id"] for r in self.pool["reference"]])

    def test_pool_conflict_and_baseline_duplicate_fail(self):
        with self.assertRaises(SchemaInvalidError):
            build_pool(self.base, [], [], self.lang, set(self.base[1:]))
        with self.assertRaises(SchemaInvalidError):
            build_pool(["1"] * 200, [], [], self.lang, set(self.lang))

    def test_lambda_zero_bypasses_all_features(self):
        docs, details = rank_query(self.pool, {}, {"mode": "adaptive", "lambda": 0})
        self.assertEqual(docs, self.base)
        self.assertTrue(details["bypass"])

    def test_vi_selection_keeps_non_vi_slot(self):
        features = {r["doc_id"]: {"body_coverage": int(r["doc_id"] == "201"), "mapping_coverage": 1}
                    for r in self.pool["reference"]}
        docs, _ = rank_query(self.pool, features, {"mode": "fixed_evidence", "lambda": 1})
        self.assertEqual(docs[0], "201")
        self.assertEqual(docs[1], "2")
        self.assertEqual(len(set(docs)), 200)
        self.assertNotIn("202", docs)

    def test_p200_preserves_set_and_null_falls_back_whole_query(self):
        pool = build_pool(self.base, [], [], self.lang, set(self.lang), scope="p200")
        f = {d: {"body_coverage": 0, "mapping_coverage": 1} for d in self.base}
        f["1"]["body_coverage"] = None
        docs, details = rank_query(pool, f, {"mode": "fixed_evidence", "lambda": .2})
        self.assertEqual(docs, self.base)
        self.assertEqual(details["fallback_reason"], "evidence_unavailable")

    def test_source_availability_and_gate_validation(self):
        self.assertEqual(rank_component(None, "not_retrieved"), 0)
        self.assertIsNone(rank_component(None, "not_scored"))
        self.assertEqual(rank_component(120, "ranked"), 61 / 180)
        self.assertGreater(query_gate(.8, .5, .1), query_gate(.2, .5, .1))
        with self.assertRaises(SchemaInvalidError):
            query_gate(.5, .5, 0)

    def test_route_zero_valid_missing_not_zero(self):
        support = {"docs": [{"doc_id": "1", "source_rank": 1}, {"doc_id": "3", "source_rank": 3}],
                   "requested_K": 20, "support_hash": "test", "unverified_language": []}
        f = {"1": {"body_coverage": 0, "mapping_coverage": 1}, "3": {"body_coverage": 1, "mapping_coverage": 1}}
        valid = query_evidence(support, f)
        self.assertTrue(valid["route_eligible"])
        del f["3"]
        partial = query_evidence(support, f)
        self.assertFalse(partial["route_eligible"])
        self.assertIsNone(partial["E"])
        self.assertEqual(partial["E_valid"], 0)

    def test_multilingual_denominator_hash_and_no_automatic_critical(self):
        c = build_query_concepts(1, "ung thư phổi và gan", [{"vi": "ung thư phổi", "zh": "肺癌", "critical": True}, {"vi": "gan"}])
        r = coverage(c, "这是肺癌治疗", "zh")
        self.assertEqual(r["coverage"], 1)
        self.assertEqual(r["mapping_coverage"], .5)
        self.assertFalse(c[0].critical)
        c2 = build_query_concepts(1, "ung thư phổi và gan", [{"vi": "ung thư phổi", "zh": "肺部癌症"}, {"vi": "gan"}])
        self.assertNotEqual(compute_concept_set_hash(c), compute_concept_set_hash(c2))

    def test_srs_group_split_no_leakage(self):
        queries = {i: f"query {i}" for i in range(1, 121)}
        queries[2] = queries[1]
        a = split_queries(queries)
        self.assertEqual(a, split_queries(queries))
        self.assertEqual(len(a["sampled_ids"]), 100)
        gd = {a["query_groups"][str(q)] for q in a["dev"]}
        gh = {a["query_groups"][str(q)] for q in a["holdout"]}
        self.assertFalse(gd & gh)

    def test_fixed_budget_and_selection_requires_all_trials(self):
        self.assertEqual(len(fixed_menu()), 18)
        with self.assertRaises(SchemaInvalidError):
            select_dev([{"status": "inconclusive"}])
