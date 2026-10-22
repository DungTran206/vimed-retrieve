"""Behavioral checks for the experimental medical gate and score selection."""
import copy
import unittest

from TXT.bear.medical_scoring import (
    importance, medical_gate, normalize_bm25, normalize_dense,
    score_record, select_ranked, sigmoid, validate_scoring_config,
)


def concept(tier=4, **extra):
    return {"concept_id": "disease", "origin": "query", "tier": tier,
            "required": False, **extra}


def fixture(tier=4):
    return {"id": 1, "query": "example", "concepts": [concept(tier)], "candidates": [
        {"doc_id": "a", "scores": {"bm25": 2, "dense_head": 0.2, "dense_chunk": 0.2},
         "concept_matches": [{"concept_id": "disease", "match": 1}]},
        {"doc_id": "b", "scores": {"bm25": -2, "dense_head": 0.8, "dense_chunk": 0.8},
         "concept_matches": [{"concept_id": "disease", "match": 0}]},
    ]}


class TestMedicalScoring(unittest.TestCase):
    def test_config_typos_and_bad_disabled_branches_fail_before_replay(self):
        configs = [
            {"alpha_mni": 0.2},
            {"selection": {"threshold_by_tier": {"4": 0.2}}},
            {"bm25": {"smoth": 0.2}},
            {"dense": {"head": {"method": "affine", "temperature": 1}}},
            {"dense": {"head_weight": 0, "chunk_weight": 0}},
            {"required_cap": 1},
            {"tier_scores": [0.5, 0.2, 0.8, 1]},
            {"selection": {"max_docs": -1}},
            {"selection": {"thresholds_by_tier": {"0": 0.1, 0: 0.2}}},
        ]
        for config in configs:
            with self.subTest(config=config), self.assertRaises(ValueError):
                score_record({"id": 1, "concepts": [], "candidates": []}, config)
        self.assertEqual(validate_scoring_config({}), {})

    def test_absolute_importance_does_not_cancel_in_coverage(self):
        matches = [{"concept_id": "disease", "match": 1}]
        self.assertAlmostEqual(medical_gate([concept(1)], matches, {})["gate"], 0.05)
        self.assertAlmostEqual(medical_gate([concept(4)], matches, {})["gate"], 1.0)

    def test_gate_ignores_enrichment_and_deduplicates_document_alias_matches(self):
        concepts = [concept(2), concept(4, concept_id="extra", origin="enrichment")]
        matched = [{"concept_id": "disease", "match": 0.4},
                   {"concept_id": "disease", "match": 0.6},
                   {"concept_id": "extra", "match": 1}]
        result = medical_gate(concepts, matched, {})
        self.assertAlmostEqual(result["gate"], 0.18)
        self.assertEqual(result["max_original_tier"], 2)
        with self.assertRaises(ValueError):
            medical_gate([concept(), concept()], matched, {})

    def test_missing_required_concept_caps_gate(self):
        concepts = [concept(), concept(4, concept_id="age", required=True)]
        result = medical_gate(concepts, [{"concept_id": "disease", "match": 1}], {})
        self.assertEqual(result["gate"], 0)
        self.assertEqual(result["uncapped_gate"], 0.5)

    def test_expected_salience_uses_entire_distribution(self):
        item = concept(4, probabilities=[0, 0, 0.5, 0.5], probability_method="backend_label_logits",
                       probability_provenance={"backend": "test", "model": "fixture"})
        self.assertAlmostEqual(importance(item, {"tier_mode": "expected"}), 0.85)
        with self.assertRaises(ValueError):
            importance(concept(), {"tier_mode": "expected"})
        with self.assertRaises(ValueError):
            importance(concept(probabilities=[0, 0, 0, 1]), {"tier_mode": "expected"})

    def test_normalization_extremes_and_temperature(self):
        self.assertEqual(sigmoid(-10000), 0)
        self.assertEqual(sigmoid(10000), 1)
        self.assertEqual(normalize_bm25(8, {"x0": 4, "temperature": 1, "pretransform": "query_scale"}, 2), 0.5)
        self.assertEqual(normalize_dense(5, {"low": -1, "high": 1}), 1)
        with self.assertRaises(ValueError):
            normalize_bm25(1, {"temperature": 0})
        with self.assertRaisesRegex(ValueError, "unrelated index scale"):
            normalize_bm25(1, {"pretransform": "query_scale"}, 2, query_scale_compatible=False)

    def test_gate_changes_lexical_weight_and_keeps_dense_floor(self):
        low = score_record(fixture(1), {})
        high = score_record(fixture(4), {})
        a_low = next(row for row in low["ranking"] if row["doc_id"] == "a")
        a_high = next(row for row in high["ranking"] if row["doc_id"] == "a")
        self.assertGreater(a_high["alpha_effective"], a_low["alpha_effective"])
        self.assertLessEqual(a_high["alpha_effective"], 0.9)
        self.assertGreater(a_high["fused_score"], a_low["fused_score"])

    def test_missing_scores_renormalize_available_sources_without_zero_imputation(self):
        record = fixture()
        record["candidates"] = [record["candidates"][0]]
        record["candidates"][0]["scores"] = {"bm25": None, "dense_head": None, "dense_chunk": 0.6}
        result = score_record(record, {})["ranking"][0]
        self.assertAlmostEqual(result["fused_score"], 0.8)
        self.assertEqual(result["alpha_effective"], 0)
        self.assertEqual(result["missing_scores"], ["bm25", "dense_head"])
        with self.assertRaises(ValueError):
            score_record(record, {"missing_scores": "error"})
        record["candidates"][0]["scores"] = {"bm25": 1}
        with self.assertRaises(ValueError):
            score_record(record, {})
        self.assertEqual(score_record(record, {"allow_bm25_only": True})["ranking"][0]["alpha_effective"], 1)

    def test_external_bm25_scale_guard_and_threshold_zero_bucket(self):
        record = fixture()
        record["query_scale_compatible"] = False
        with self.assertRaisesRegex(ValueError, "unrelated index scale"):
            score_record(record, {"bm25": {"pretransform": "query_scale"}})
        self.assertTrue(score_record(record, {"bm25": {"pretransform": "raw"}})["ranking"])
        selection = select_ranked([{"doc_id": "a", "fused_score": 0.6}], [],
                                  {"threshold": 0.9, "thresholds_by_tier": {"0": 0.5}})
        self.assertEqual(selection["doc_ids"], ["a"])

    def test_threshold_fallback_cap_and_query_bucket(self):
        ranking = [{"doc_id": str(i), "fused_score": value} for i, value in enumerate([0.9, 0.7, 0.3])]
        result = select_ranked(ranking, [concept()], {
            "threshold": 0.1, "thresholds_by_tier": {"4": 0.8}, "min_docs": 2, "max_docs": 2})
        self.assertEqual(result["doc_ids"], ["0", "1"])
        self.assertEqual(result["above_threshold_count"], 1)
        self.assertEqual(result["fallback_added_count"], 1)
        self.assertEqual(result["tier_bucket"], 4)
        capped = select_ranked(ranking, [], {"threshold": 0, "max_docs": 1})
        self.assertEqual(capped["cap_removed_count"], 2)

    def test_expansion_blend_and_missing_policy_are_explicit(self):
        record = fixture()
        for row in record["candidates"]:
            row["scores"]["bm25_expanded"] = 6
        config = {"bm25": {"enrichment_weight": 0.5}}
        original = copy.deepcopy(record)
        result = score_record(record, config)
        first = next(row for row in result["ranking"] if row["doc_id"] == "a")
        self.assertEqual(first["bm25_raw_blend"], 4)
        self.assertEqual(record, original)
        del record["candidates"][0]["scores"]["bm25_expanded"]
        with self.assertRaises(ValueError):
            score_record(record, config)

    def test_sapbert_zero_weight_preserves_original_fusion_and_gate(self):
        record = fixture()
        baseline = score_record(record, {})
        result = score_record(record, {"sapbert": {"weight": 0}, "missing_scores": "error"})
        self.assertEqual(result, baseline)
        self.assertEqual(result["score_schema"], "medical-gate-v1")

    def test_sapbert_replacement_disables_generic_dense_missing_checks(self):
        record = fixture()
        record["candidates"] = [record["candidates"][0]]
        record["candidates"][0]["scores"] = {"bm25": 2, "sapbert": 0.55}
        result = score_record(record, {"sapbert": {"weight": 1}, "missing_scores": "error"})
        row = result["ranking"][0]
        self.assertIsNone(row["generic_dense_normalized"])
        self.assertAlmostEqual(row["dense_normalized"], 0.5)
        self.assertEqual(row["dense_branch_weights"], {"generic_dense": 0, "sapbert": 1})
        self.assertEqual(result["score_schema"], "medical-gate-v2")

    def test_intermediate_sapbert_weight_combines_normalized_branches(self):
        record = fixture()
        for row in record["candidates"]:
            row["scores"]["sapbert"] = 0.9
        row = next(row for row in score_record(record, {"sapbert": {"weight": 0.25}})["ranking"] if row["doc_id"] == "a")
        self.assertAlmostEqual(row["generic_dense_normalized"], 0.6)
        self.assertAlmostEqual(row["sapbert_normalized"], 1)
        self.assertAlmostEqual(row["dense_normalized"], 0.7)
        self.assertAlmostEqual(row["fused_score"], row["alpha_requested"] * row["bm25_normalized"] + (1 - row["alpha_requested"]) * 0.7)

    def test_sapbert_matrix_importance_weights_originals_and_missing_as_zero(self):
        record = fixture()
        record["concepts"].extend([concept(2, concept_id="support"), concept(4, concept_id="exp", origin="enrichment")])
        candidate = record["candidates"][1]
        candidate["sapbert_matches"] = [
            {"concept_id": "disease", "similarities": [{"text": "alias", "cosine": 0.9}]},
            {"concept_id": "exp", "similarities": [{"text": "expansion", "cosine": 1}]},
        ]
        record["candidates"] = [candidate]
        row = score_record(record, {"sapbert": {"weight": 1}})["ranking"][0]
        self.assertAlmostEqual(row["sapbert_normalized"], 1 / 1.3)
        self.assertEqual(row["medical_gate"]["gate"], 0)
        self.assertEqual(row["alpha_requested"], 0.1)
        self.assertEqual(row["sapbert_diagnostics"]["ignored_concept_ids"], ["exp"])

    def test_sapbert_missing_sources_renormalize_or_raise(self):
        record = fixture()
        result = score_record(record, {"sapbert": {"weight": 0.5}})
        self.assertEqual(result["ranking"][0]["dense_branch_weights"], {"generic_dense": 1, "sapbert": 0})
        self.assertIn("sapbert", result["ranking"][0]["missing_scores"])
        with self.assertRaisesRegex(ValueError, "sapbert"):
            score_record(record, {"sapbert": {"weight": 0.5}, "missing_scores": "error"})
        record["candidates"] = [{"doc_id": "a", "scores": {"bm25": 2, "sapbert": 0.9}}]
        row = score_record(record, {"sapbert": {"weight": 0.5}})["ranking"][0]
        self.assertEqual(row["dense_branch_weights"], {"generic_dense": 0, "sapbert": 1})
        with self.assertRaisesRegex(ValueError, "dense_head"):
            score_record(record, {"sapbert": {"weight": 0.5}, "missing_scores": "error"})

    def test_empty_or_expansion_only_matrix_is_missing_evidence(self):
        record = fixture()
        record["candidates"] = [record["candidates"][0]]
        for matrix in ([], [{"concept_id": "exp", "similarities": [{"text": "term", "cosine": 0.9}]}]):
            record["candidates"][0]["sapbert_matches"] = matrix
            with self.subTest(matrix=matrix), self.assertRaisesRegex(ValueError, "sapbert"):
                score_record(record, {"sapbert": {"weight": 1}, "missing_scores": "error"})

    def test_sapbert_matrix_max_and_custom_sigmoid(self):
        record = fixture()
        record["candidates"] = [record["candidates"][0]]
        record["candidates"][0]["sapbert_matches"] = [{"concept_id": "disease", "similarities": [
            {"text": "lower", "cosine": -0.2}, {"text": "higher", "cosine": 0.4}]}]
        row = score_record(record, {"sapbert": {"weight": 1, "method": "sigmoid", "x0": 0.4, "temperature": 0.1}})["ranking"][0]
        self.assertEqual(row["sapbert_normalized"], 0.5)
        self.assertEqual(row["sapbert_diagnostics"]["concepts"][0]["best_term"]["text"], "higher")

    def test_sapbert_repeated_spans_count_once_and_intent_is_not_semantic_denominator(self):
        record = fixture()
        record["concepts"].append(concept(4, concept_id="intent", kind="intent"))
        candidate = record["candidates"][0]
        candidate["sapbert_matches"] = [{"concept_id": "disease", "similarities": [{
            "text": "term", "cosine": 0.9, "field": "body", "anchor": {"start": 0, "end": 4},
            "anchors": [{"start": 0, "end": 4}, {"start": 20, "end": 24}],
            "kind": "disease", "assertion": "affirmed"}]}]
        record["candidates"] = [candidate]
        row = score_record(record, {"sapbert": {"weight": 1}})["ranking"][0]
        self.assertEqual(row["sapbert_normalized"], 1)
        self.assertEqual(len(row["sapbert_diagnostics"]["concepts"]), 1)
        self.assertEqual(len(row["sapbert_diagnostics"]["concepts"][0]["best_term"]["anchors"]), 2)
        self.assertEqual(row["medical_gate"]["original_concept_count"], 2)
        self.assertEqual(row["medical_gate"]["gate"], 0.5)

    def test_sapbert_repeated_anchors_validate_spans_field_duplicates_and_primary(self):
        record = fixture()
        record["candidates"] = [record["candidates"][0]]
        invalid = [[], [{"start": -1, "end": 3}], [{"start": 4, "end": 4}],
                   [{"start": 0, "end": 4, "field": "title"}],
                   [{"start": 0, "end": 4}, {"start": 0, "end": 4}],
                   [{"start": 20, "end": 24}]]
        for anchors in invalid:
            record["candidates"][0]["sapbert_matches"] = [{"concept_id": "disease", "similarities": [{
                "text": "term", "cosine": 0.9, "field": "body", "anchor": {"start": 0, "end": 4},
                "anchors": anchors}]}]
            with self.subTest(anchors=anchors), self.assertRaises(ValueError):
                score_record(record, {"sapbert": {"weight": 1}})

    def test_invalid_sapbert_configs_and_duplicate_matrices_fail(self):
        configs = [{"weigth": 0.5}, {"weight": True}, {"weight": -0.1},
                   {"weight": 0.5, "low": 0.9, "high": 0.2},
                   {"weight": 0.5, "method": "sigmoid", "low": 0.2}]
        for config in configs:
            with self.subTest(config=config), self.assertRaises(ValueError):
                score_record(fixture(), {"sapbert": config})
        record = fixture()
        record["candidates"] = [record["candidates"][0]]
        matrices = [
            [{"concept_id": "disease", "similarities": [{"text": "a", "cosine": 1.1}]}],
            [{"concept_id": "disease", "similarities": [{"text": "a", "cosine": float("nan")}]}],
            [{"concept_id": "disease", "similarities": []}] * 2,
            [{"concept_id": "disease", "similarities": [{"text": "a", "cosine": 0.8}] * 2}],
        ]
        for matrix in matrices:
            record["candidates"][0]["sapbert_matches"] = matrix
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                score_record(record, {"sapbert": {"weight": 1}})


if __name__ == "__main__":
    unittest.main()
