"""Engineering fixtures for corpus-independent BEAR retrieval, not IR results."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
import unicodedata
from pathlib import Path

from TXT.bear.contracts import OutputOutsideTXTError, SchemaInvalidError, TXT_DIR
from TXT.bear.corpus_index import CorpusIndex, body_chunks, build_index


class TestCorpusIndex(unittest.TestCase):
    def setUp(self):
        parent = TXT_DIR / "runtime" / "tmp"
        parent.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="corpus_index_", dir=parent)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / "corpus.jsonl"
        self.index = self.directory / "index.sqlite"

    def tearDown(self):
        self.temporary.cleanup()

    def _write(self, documents):
        self.source.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in documents), encoding="utf-8")

    def test_search_has_no_baseline_pool_and_scores_all_matches(self):
        # The matching document does not need to occur in a baseline list.
        self._write([
            {"doc_id": "baseline", "lang": "vi", "body": "unrelated text"},
            {"doc_id": "independent", "lang": "vi", "body": "BRCA1 treatment evidence"},
            {"doc_id": "wrong_gene", "lang": "vi", "body": "BRCA10"},
        ])
        metadata = build_index(self.source, self.index)
        self.assertEqual(metadata["document_count"], 3)
        self.assertEqual(metadata["languages"], {"vi": 3})
        with CorpusIndex(self.index) as index:
            rows = index.search("BRCA1")
            self.assertEqual([row["doc_id"] for row in rows], ["independent"])
            self.assertEqual(rows[0], index.score_document("BRCA1", "independent"))
            self.assertEqual(rows[0], index.rank_documents("BRCA1", ["independent"])[0])
            self.assertEqual(index.search("not_in_any_document"), [])

    def test_language_filter_applies_before_truncation_and_ties_are_stable(self):
        self._write([
            {"doc_id": "a_en", "lang": "en", "body": "BRCA1"},
            {"doc_id": "b_vi", "lang": "vi", "body": "BRCA1"},
            {"doc_id": "c_vi", "lang": "vi", "body": "BRCA1"},
        ])
        build_index(self.source, self.index)
        with CorpusIndex(self.index) as index:
            self.assertEqual(index.search("BRCA1", top_k=1)[0]["doc_id"], "a_en")
            self.assertEqual(index.search("BRCA1", top_k=1, languages=("vi",))[0]["doc_id"], "b_vi")
            self.assertEqual([row["doc_id"] for row in index.search("BRCA1", languages=("vi",))], ["b_vi", "c_vi"])
            self.assertEqual(index.search("BRCA1", languages=()), [])
            with self.assertRaises(SchemaInvalidError):
                index.search("BRCA1", top_k=True)
            with self.assertRaises(SchemaInvalidError):
                index.search("BRCA1", languages="vi")

    def test_unicode_offsets_and_strict_accents_are_preserved(self):
        body = "  " + unicodedata.normalize("NFD", "viêm phổi") + ".\n\nBRCA1 điều trị. "
        self._write([{"doc_id": "unicode", "lang": "vi", "body": body}])
        build_index(self.source, self.index, chunk_chars=20)
        with CorpusIndex(self.index) as index:
            self.assertEqual(index.get_document("unicode")["body"], body)
            self.assertEqual(index.search("viem phoi"), [])
            row = index.search("viêm phổi")[0]
            self.assertEqual(row["doc_id"], "unicode")
            refs = index.get_refs("unicode")
            self.assertTrue(refs)
            for ref in refs:
                self.assertTrue(0 <= ref["start"] < ref["end"] <= len(body))
                self.assertTrue(body[ref["start"]:ref["end"]].strip())
                self.assertEqual(ref["ref_kind"], "bear_window")
                self.assertEqual(ref["corpus_hash"], index.metadata["corpus_hash"])
                self.assertEqual(ref["body_sha256"], hashlib.sha256(body.encode("utf-8")).hexdigest())
                self.assertEqual(ref["text_sha256"], hashlib.sha256(body[ref["start"]:ref["end"]].encode("utf-8")).hexdigest())
            ref = row["best_evidence_chunk_ref"]
            self.assertIsNotNone(ref)
            self.assertIn("viêm", unicodedata.normalize("NFC", body[ref["start"]:ref["end"]]))

    def test_sqlite_doc_id_and_id_adapters_are_readonly(self):
        for identifier in ("doc_id", "id"):
            with self.subTest(identifier=identifier):
                source = self.directory / (identifier + ".sqlite")
                connection = sqlite3.connect(source)
                connection.execute(f"CREATE TABLE doc ({identifier} TEXT PRIMARY KEY, body TEXT, lang TEXT)")
                connection.execute("INSERT INTO doc VALUES ('sqlite','BRCA1','vi')")
                connection.commit()
                connection.close()
                before = hashlib.sha256(source.read_bytes()).hexdigest()
                index_path = self.directory / (identifier + "_index.sqlite")
                build_index(source, index_path)
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
                with CorpusIndex(index_path) as index:
                    self.assertEqual(index.search("BRCA1")[0]["doc_id"], "sqlite")
                    with self.assertRaises(sqlite3.OperationalError):
                        index.connection.execute("DELETE FROM documents")

    def test_invalid_or_duplicate_ids_fail_without_replacing_old_index(self):
        self._write([{"doc_id": "original", "body": "BRCA1"}])
        build_index(self.source, self.index)
        before = self.index.read_bytes()
        invalid_cases = [
            [{"doc_id": " bad", "body": "text"}],
            [{"doc_id": "same", "body": "one"}, {"doc_id": "same", "body": "two"}],
            [{"doc_id": "valid", "body": 123}],
            [{"doc_id": "valid", "id": "other", "body": "text"}],
        ]
        for rows in invalid_cases:
            with self.subTest(rows=rows):
                self._write(rows)
                with self.assertRaises(SchemaInvalidError):
                    build_index(self.source, self.index, overwrite=True)
                self.assertEqual(self.index.read_bytes(), before)
        self.assertEqual(list(self.directory.glob("*.partial")), [])

    def test_missing_and_empty_text_and_unknown_ids(self):
        self._write([
            {"doc_id": "missing", "lang": "vi", "body": None},
            {"doc_id": "empty", "lang": "vi", "body": ""},
        ])
        build_index(self.source, self.index)
        with CorpusIndex(self.index) as index:
            self.assertEqual(index.search("BRCA1"), [])
            self.assertIsNone(index.get_document("missing")["body"])
            self.assertEqual(index.get_document("empty")["body"], "")
            self.assertEqual(index.get_refs("missing"), [])
            self.assertEqual(index.score_document("BRCA1", "missing")["score"], 0)
            self.assertIsNone(index.get_document("unknown"))
            with self.assertRaises(KeyError):
                index.rank_documents("BRCA1", ["unknown"])

    def test_output_bounds_and_input_collision(self):
        self._write([{"doc_id": "valid", "body": "BRCA1"}])
        for target in (TXT_DIR.parent / "forbidden.sqlite", TXT_DIR / "inputs" / "forbidden.sqlite", self.source):
            with self.subTest(target=target), self.assertRaises(OutputOutsideTXTError):
                build_index(self.source, target)
        build_index(self.source, self.index)
        with self.assertRaises(FileExistsError):
            build_index(self.source, self.index)

    def test_empty_corpus_and_wal_sidecars_are_rejected(self):
        self.source.write_text("", encoding="utf-8")
        with self.assertRaises(SchemaInvalidError):
            build_index(self.source, self.index)
        sqlite_source = self.directory / "corpus.sqlite3"
        connection = sqlite3.connect(sqlite_source)
        connection.execute("CREATE TABLE doc (doc_id TEXT PRIMARY KEY, body TEXT)")
        connection.execute("INSERT INTO doc VALUES ('d','BRCA1')")
        connection.commit()
        connection.close()
        sidecar = sqlite_source.with_name(sqlite_source.name + "-wal")
        sidecar.write_bytes(b"")
        with self.assertRaises(SchemaInvalidError):
            build_index(sqlite_source, self.index)
        sidecar.unlink()
        build_index(sqlite_source, self.index)
        index_sidecar = self.index.with_name(self.index.name + "-wal")
        index_sidecar.write_bytes(b"")
        with self.assertRaises(SchemaInvalidError):
            CorpusIndex(self.index)

    def test_inference_does_not_use_labels(self):
        documents = [{"doc_id": "d", "body": "BRCA1", "labels": ["relevant"]}]
        self._write(documents)
        first = build_index(self.source, self.index)
        with CorpusIndex(self.index) as index:
            first_rows = index.search({"text": "BRCA1", "labels": {"d": 0}})
        documents[0]["labels"] = ["irrelevant"]
        self._write(documents)
        second = build_index(self.source, self.index, overwrite=True)
        self.assertEqual(first["corpus_hash"], second["corpus_hash"])
        with CorpusIndex(self.index) as index:
            self.assertEqual(first_rows, index.search({"text": "BRCA1", "labels": {"d": 1}}))

    def test_chunk_builder_keeps_original_body_intervals(self):
        body = " \nSentence one.\nSentence two is much longer.\n Last sentence. "
        refs = body_chunks(body, "d", chunk_chars=15)
        self.assertEqual("".join(body[ref["start"]:ref["end"]] for ref in refs).replace(" ", "").replace("\n", ""),
                         body.replace(" ", "").replace("\n", ""))
        self.assertTrue(all(ref["end"] - ref["start"] <= 15 for ref in refs))
        self.assertEqual(body_chunks(None, "d"), [])
        with self.assertRaises(SchemaInvalidError):
            body_chunks("x", "d", chunk_chars=0)


if __name__ == "__main__":
    unittest.main()
