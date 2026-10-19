"""Unit tests for BEAR protected span matching, entity extraction, and boundary matrix."""

from __future__ import annotations

import unicodedata
import unittest

from TXT.bear.matching import (
    ConceptRecord,
    build_protected_pattern,
    build_query_concepts,
    compute_concept_set_hash,
    match_concept_in_text,
    normalize_text,
)


class TestMatchingEvidence(unittest.TestCase):
    def test_unicode_and_vietnamese_normalization(self) -> None:
        # NFD text (decomposed combining marks) should match NFC text
        nfc_text = "viêm phổi thùy"
        nfd_text = unicodedata.normalize("NFD", nfc_text)
        self.assertNotEqual(nfc_text, nfd_text)
        self.assertEqual(normalize_text(nfd_text), normalize_text(nfc_text))

        # Whitespace and newlines collapse
        raw_text = "ung\n\t thư    phổi\n"
        self.assertEqual(normalize_text(raw_text), "ung thư phổi")

        # Accents preserved (does not match unaccented)
        pat = build_protected_pattern("viêm phổi")
        self.assertTrue(pat.search(normalize_text("Bệnh nhân viêm phổi nặng")))
        self.assertFalse(pat.search(normalize_text("Benh nhan viem phoi nang")))

    def test_protected_atoms_dose_and_decimals(self) -> None:
        pat_5mg = build_protected_pattern("5 mg")

        # Positive matches
        self.assertTrue(pat_5mg.search("uống 5 mg mỗi ngày"))
        self.assertTrue(pat_5mg.search("viên nén 5 mg."))

        # Negative boundary protections per §8.3
        self.assertFalse(pat_5mg.search("uống 0,5 mg mỗi ngày"))  # comma decimal
        self.assertFalse(pat_5mg.search("uống 0.5 mg mỗi ngày"))  # dot decimal
        self.assertFalse(pat_5mg.search("uống 15 mg mỗi ngày"))   # prefix digit
        self.assertFalse(pat_5mg.search("uống 55 mg mỗi ngày"))
        self.assertFalse(pat_5mg.search("uống 5 mcg mỗi ngày"))   # different unit

    def test_protected_atoms_subtypes_and_identifiers(self) -> None:
        # type 1 vs type 2
        pat_type1 = build_protected_pattern("type 1")
        self.assertTrue(pat_type1.search("đái tháo đường type 1"))
        self.assertFalse(pat_type1.search("đái tháo đường type 2"))
        self.assertFalse(pat_type1.search("đái tháo đường type 10"))

        # BRCA1 vs BRCA10 vs BRCA2
        pat_brca1 = build_protected_pattern("BRCA1")
        self.assertTrue(pat_brca1.search("đột biến gen BRCA1 dương tính"))
        self.assertFalse(pat_brca1.search("đột biến gen BRCA10 dương tính"))
        self.assertFalse(pat_brca1.search("đột biến gen BRCA2 dương tính"))

        # BRAF V600E vs BRAF V600K
        pat_v600e = build_protected_pattern("BRAF V600E")
        self.assertTrue(pat_v600e.search("phát hiện đột biến BRAF V600E"))
        self.assertFalse(pat_v600e.search("phát hiện đột biến BRAF V600K"))

        # PD-1 vs PD-L1 vs PD-10
        pat_pd1 = build_protected_pattern("PD-1")
        self.assertTrue(pat_pd1.search("thuốc ức chế PD-1 hiệu quả"))
        self.assertFalse(pat_pd1.search("thuốc ức chế PD-L1 hiệu quả"))
        self.assertFalse(pat_pd1.search("thuốc ức chế PD-10 hiệu quả"))

    def test_cjk_han_matching(self) -> None:
        pat_zh = build_protected_pattern("肺癌")
        self.assertTrue(pat_zh.search("这是肺癌治疗的指南"))
        self.assertFalse(pat_zh.search("这是肝癌治疗的指南"))

    def test_concept_dedup_and_deterministic_hash(self) -> None:
        q_text = "điều trị ung thư phổi và ung thư phổi di căn"
        raw_entities_1 = [
            {"vi": "ung thư phổi", "en": "lung cancer"},
            {"vi": "ung thư phổi", "en": "lung neoplasms"},  # duplicate span
            {"vi": "ung thư gan", "en": "liver cancer"},     # not in query
        ]
        concepts_1 = build_query_concepts(1, q_text, raw_entities_1)

        # "ung thư phổi" deduplicated to 1 concept, indices=[0, 1], status=verified_in_query
        # "ung thư gan" has status=not_in_query
        self.assertEqual(len(concepts_1), 2)
        c_lung = next(c for c in concepts_1 if c.normalized_vi == "ung thư phổi")
        self.assertEqual(c_lung.vi_span_status, "verified_in_query")
        self.assertEqual(c_lung.source_entity_indices, [0, 1])

        c_liver = next(c for c in concepts_1 if c.normalized_vi == "ung thư gan")
        self.assertEqual(c_liver.vi_span_status, "not_in_query")

        # Reversed entity input order must yield exact same concept_set_hash
        raw_entities_2 = list(reversed(raw_entities_1))
        concepts_2 = build_query_concepts(1, q_text, raw_entities_2)
        
        hash1 = compute_concept_set_hash(concepts_1)
        hash2 = compute_concept_set_hash(concepts_2)
        self.assertEqual(hash1, hash2)

    def test_alias_matching_controls(self) -> None:
        concept = ConceptRecord(
            query_id=1,
            concept_id="q1:test_hcc",
            original_vi="ung thư biểu mô tế bào gan",
            normalized_vi="ung thư biểu mô tế bào gan",
            source_entity_indices=[0],
            vi_span_status="verified_in_query",
            verified_aliases=["HCC", "ung thư gan nguyên phát"],
        )

        text_with_alias_only = "Phác đồ điều trị HCC giai đoạn muộn"

        # When aliases=False (default V1): no match
        res_no_alias = match_concept_in_text(concept, text_with_alias_only, enable_aliases=False)
        self.assertFalse(res_no_alias.matched)

        # When aliases=True: matches as alias
        res_alias = match_concept_in_text(concept, text_with_alias_only, enable_aliases=True)
        self.assertTrue(res_alias.matched)
        self.assertEqual(res_alias.match_type, "alias")
        self.assertEqual(res_alias.matched_phrase, "hcc")


if __name__ == "__main__":
    unittest.main()

