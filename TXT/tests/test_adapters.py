"""Unit tests for BEAR adapters, chunk mappings, and SQLite read-only invariants."""

from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from TXT.bear.adapters import (
    load_chunk_refs,
    map_runtime_doc_id,
    read_chunk_scores,
    read_docs_readonly,
    read_queries,
    read_rank_source,
)
from TXT.bear.contracts import ERROR_SCHEMA_INVALID, SchemaInvalidError
from TXT.bear.io import write_jsonl
from TXT.tests.fixtures import (
    create_synthetic_chunk_scores,
    create_synthetic_corpus_db,
    create_synthetic_rank_source,
    get_fixture_dir,
)


class TestAdapters(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_dir = get_fixture_dir("adapters")

    def test_rank_source_preserves_order_and_ties(self) -> None:
        # Two candidates with tied score 0.5; array rank must preserve original order
        src_file = self.fixture_dir / "tied_rank.jsonl"
        create_synthetic_rank_source(
            src_file,
            [{
                "query_id": 1,
                "candidates": [
                    {"doc_id": "doc_first", "score": 0.5},
                    {"doc_id": "doc_second", "score": 0.5},
                    {"doc_id": "doc_zero", "score": 0.0},
                    {"doc_id": "doc_none", "score": None},
                ],
            }],
        )

        queries = list(read_rank_source(src_file))
        self.assertEqual(len(queries), 1)
        q = queries[0]
        self.assertEqual(q.query_id, 1)
        self.assertEqual(len(q.items), 4)

        # Positions preserved
        self.assertEqual(q.items[0].doc_id, "doc_first")
        self.assertEqual(q.items[0].rank, 1)
        self.assertEqual(q.items[0].score, 0.5)

        self.assertEqual(q.items[1].doc_id, "doc_second")
        self.assertEqual(q.items[1].rank, 2)
        self.assertEqual(q.items[1].score, 0.5)

        # 0.0 is distinct from None
        self.assertEqual(q.items[2].score, 0.0)
        self.assertIsNone(q.items[3].score)

    def test_rank_source_duplicate_doc_rejected(self) -> None:
        dup_file = self.fixture_dir / "dup_rank.jsonl"
        create_synthetic_rank_source(
            dup_file,
            [{
                "query_id": 1,
                "candidates": [
                    {"doc_id": "doc_1", "score": 0.9},
                    {"doc_id": "doc_1", "score": 0.8},
                ],
            }],
        )
        with self.assertRaises(SchemaInvalidError):
            list(read_rank_source(dup_file))

    def test_runtime_doc_id_mapping(self) -> None:
        self.assertEqual(map_runtime_doc_id("corpus:279834"), "279834")
        with self.assertRaises(SchemaInvalidError):
            map_runtime_doc_id("unknown:279834")
        with self.assertRaises(SchemaInvalidError):
            map_runtime_doc_id("corpus:")

    def test_corpus_db_readonly_and_batching(self) -> None:
        db_path = self.fixture_dir / "test_corpus.sqlite"
        docs = [
            {"id": "d1", "title": "Doc 1", "body": "Body one content", "lang": "vi", "domain": "vinmec.com"},
            {"id": "d2", "title": "Doc 2", "body": "Body two content", "lang": "vi", "domain": "vinmec.com"},
            {"id": "d3", "title": "Doc 3", "body": "Body three content", "lang": "zh", "domain": "zh.com"},
        ]
        create_synthetic_corpus_db(db_path, docs)

        # Test reading in batch size of 2
        results = list(read_docs_readonly(db_path, ["d1", "d2", "d3"], batch_size=2))
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].doc_id, "d1")
        self.assertEqual(results[0].domain, "vinmec.com")
        self.assertTrue(len(results[0].body_sha256) == 64)

        # Test read-only enforcement: attempting to write should raise OperationalError
        uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        with self.assertRaises(sqlite3.OperationalError):
            conn.execute("UPDATE doc SET title = 'mutated' WHERE id = 'd1'")
        conn.close()

    def test_chunk_refs_empty_slice_discarded_and_repeated_text(self) -> None:
        db_path = self.fixture_dir / "chunk_corpus.sqlite"
        # Body with repeated word 'viêm gan' at different offsets
        body = "Bệnh viêm gan B và điều trị viêm gan B mạn tính."
        # First 'viêm gan': offset 5 to 13
        # Second 'viêm gan': offset 27 to 35
        docs = [{"id": "d10", "title": "Gan", "body": body, "lang": "vi", "domain": "vinmec.com"}]
        chunks = [
            {"chunk_id": 101, "doc_id": "d10", "ord": 0, "start": 0, "end": 20},     # valid
            {"chunk_id": 102, "doc_id": "d10", "ord": 1, "start": 20, "end": 20},    # empty slice -> should be dropped
            {"chunk_id": 103, "doc_id": "d10", "ord": 2, "start": 25, "end": len(body)}, # valid
        ]
        create_synthetic_corpus_db(db_path, docs, chunks)

        refs = load_chunk_refs(db_path, ["d10"])
        self.assertIn("d10", refs)
        d10_refs = refs["d10"]
        # Empty slice chunk 102 dropped, so exactly 2 chunks remain
        self.assertEqual(len(d10_refs), 2)

        # exporter_idx starts at 0 and increments strictly
        self.assertEqual(d10_refs[0].chunk_id_native, 101)
        self.assertEqual(d10_refs[0].exporter_idx, 0)
        self.assertEqual(d10_refs[1].chunk_id_native, 103)
        self.assertEqual(d10_refs[1].exporter_idx, 1)

    def test_chunk_scores_duplicate_detection(self) -> None:
        file_path = self.fixture_dir / "dup_chunk_scores.jsonl"
        create_synthetic_chunk_scores(
            file_path,
            [
                {"query_id": 1, "doc_id": "d1", "chunk_idx": 0, "score": 0.8},
                {"query_id": 1, "doc_id": "d1", "chunk_idx": 0, "score": 0.7},  # duplicate key
            ],
        )
        with self.assertRaises(SchemaInvalidError):
            list(read_chunk_scores(file_path))

    def test_query_reading_and_enrichment(self) -> None:
        q_path = self.fixture_dir / "queries.jsonl"
        write_jsonl(q_path, [
            {"id": 1, "query": "điều trị ung thư phổi"},
            {"id": 2, "query": "liều dùng paracetamol"},
        ])

        eq_path = self.fixture_dir / "enriched.jsonl"
        write_jsonl(eq_path, [
            {
                "id": 1,
                "entities": [{"vi": "ung thư phổi", "en": "lung cancer", "zh": "肺癌"}],
                "parse_status": "verified",
                "en": "treatment of lung cancer",
                "zh": "肺癌治疗",
            }
        ])

        records = read_queries(q_path, eq_path)
        self.assertEqual(len(records), 2)
        q1 = records[1]
        self.assertEqual(q1.parse_status, "verified")
        self.assertEqual(q1.language_views["en"], "treatment of lung cancer")
        self.assertEqual(len(q1.entities), 1)

        q2 = records[2]
        self.assertEqual(q2.parse_status, "unknown")
        self.assertEqual(len(q2.entities), 0)


if __name__ == "__main__":
    unittest.main()

