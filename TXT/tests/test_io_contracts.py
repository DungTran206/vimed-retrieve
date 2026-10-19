"""Unit tests for BEAR I/O contracts, boundary enforcement, and validation rules."""

from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

from TXT.bear.cli import main
from TXT.bear.contracts import (
    ERROR_OUTPUT_OUTSIDE_TXT,
    ERROR_SCHEMA_INVALID,
    INPUTS_DIR,
    REPO_ROOT,
    TXT_DIR,
    OutputOutsideTXTError,
    SchemaInvalidError,
    reject_duplicate_keys,
    validate_doc_id,
    validate_finite_number,
    validate_query_id,
)
from TXT.bear.io import (
    assert_valid_output_path,
    atomic_write_json,
    atomic_write_text,
    canonical_json_dumps,
    canonical_sha256,
    load_config,
    read_json,
    read_jsonl,
    write_jsonl,
)


class TestIOContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = TXT_DIR / "runtime" / "tmp" / "test_io"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def test_output_path_boundaries(self) -> None:
        # Valid path under TXT
        valid_dest = self.tmp_dir / "valid_file.json"
        resolved = assert_valid_output_path(valid_dest)
        self.assertEqual(resolved, valid_dest.resolve())

        # Path outside TXT (e.g. repo root)
        outside_path = REPO_ROOT / "outside.txt"
        with self.assertRaises(OutputOutsideTXTError) as ctx:
            assert_valid_output_path(outside_path)
        self.assertEqual(ctx.exception.code, ERROR_OUTPUT_OUTSIDE_TXT)

        # Path traversal escape ../
        escape_path = TXT_DIR / ".." / "data" / "escaped.txt"
        with self.assertRaises(OutputOutsideTXTError):
            assert_valid_output_path(escape_path)

        # Prefix similarity bypass attack: TXT_other must be rejected
        txt_other = REPO_ROOT / "TXT_other" / "file.txt"
        with self.assertRaises(OutputOutsideTXTError):
            assert_valid_output_path(txt_other)

        # Writing directly to TXT directory root as a file
        with self.assertRaises(OutputOutsideTXTError):
            assert_valid_output_path(TXT_DIR)

        # Writing into TXT/inputs/ (read-only)
        inside_inputs = INPUTS_DIR / "new_file.txt"
        with self.assertRaises(OutputOutsideTXTError):
            assert_valid_output_path(inside_inputs)

        # Collision with input path
        dummy_input = self.tmp_dir / "input.sqlite"
        dummy_output = self.tmp_dir / "input.sqlite"
        with self.assertRaises(OutputOutsideTXTError):
            assert_valid_output_path(dummy_output, input_paths=[dummy_input])

    def test_atomic_writes_and_cleanup(self) -> None:
        target = self.tmp_dir / "atomic_test.txt"
        content = "Hello BEAR\nLine 2"
        written = atomic_write_text(target, content)
        self.assertTrue(written.is_file())
        self.assertEqual(written.read_text(encoding="utf-8"), content)
        
        # Verify no lingering .partial file
        partial = target.with_name(f"{target.name}.partial")
        self.assertFalse(partial.exists())

        # JSON atomic write
        target_json = self.tmp_dir / "atomic_test.json"
        data = {"b": 2, "a": 1}
        atomic_write_json(target_json, data)
        self.assertTrue(target_json.is_file())
        # Canonical order: "a" then "b"
        content_json = target_json.read_text(encoding="utf-8")
        self.assertIn('"a": 1', content_json)

    def test_duplicate_json_keys_rejection(self) -> None:
        raw_json = '{"key": 1, "key": 2}'
        with self.assertRaises(SchemaInvalidError):
            json.loads(raw_json, object_pairs_hook=reject_duplicate_keys)

        file_path = self.tmp_dir / "duplicate_keys.json"
        atomic_write_text(file_path, raw_json)
        with self.assertRaises(SchemaInvalidError):
            read_json(file_path)

    def test_finite_number_validation(self) -> None:
        # Valid numbers
        self.assertEqual(validate_finite_number(42, "num"), 42.0)
        self.assertEqual(validate_finite_number(3.1415, "num"), 3.1415)
        self.assertIsNone(validate_finite_number(None, "num", allow_none=True))

        # Disallow None if allow_none=False
        with self.assertRaises(SchemaInvalidError):
            validate_finite_number(None, "num", allow_none=False)

        # Reject booleans (bool is subclass of int in Python)
        with self.assertRaises(SchemaInvalidError):
            validate_finite_number(True, "num")
        with self.assertRaises(SchemaInvalidError):
            validate_finite_number(False, "num")

        # Reject NaN and Infs
        with self.assertRaises(SchemaInvalidError):
            validate_finite_number(float("nan"), "num")
        with self.assertRaises(SchemaInvalidError):
            validate_finite_number(float("inf"), "num")
        with self.assertRaises(SchemaInvalidError):
            validate_finite_number(float("-inf"), "num")

        # Reject string representations
        with self.assertRaises(SchemaInvalidError):
            validate_finite_number("123", "num")

        # Range bounds
        with self.assertRaises(SchemaInvalidError):
            validate_finite_number(-1.0, "num", min_val=0.0)
        with self.assertRaises(SchemaInvalidError):
            validate_finite_number(105.0, "num", max_val=100.0)

    def test_id_validation(self) -> None:
        # Query ID
        self.assertEqual(validate_query_id(1), 1)
        self.assertEqual(validate_query_id("100"), 100)
        with self.assertRaises(SchemaInvalidError):
            validate_query_id(0)
        with self.assertRaises(SchemaInvalidError):
            validate_query_id(-5)
        with self.assertRaises(SchemaInvalidError):
            validate_query_id(True)
        with self.assertRaises(SchemaInvalidError):
            validate_query_id("abc")

        # Doc ID
        self.assertEqual(validate_doc_id("12345"), "12345")
        self.assertEqual(validate_doc_id(12345), "12345")
        with self.assertRaises(SchemaInvalidError):
            validate_doc_id("")
        with self.assertRaises(SchemaInvalidError):
            validate_doc_id("   ")
        with self.assertRaises(SchemaInvalidError):
            validate_doc_id(" 123 ")  # padding rejected
        with self.assertRaises(SchemaInvalidError):
            validate_doc_id("12.3")  # decimal float rejected

    def test_jsonl_streaming(self) -> None:
        jsonl_path = self.tmp_dir / "stream_test.jsonl"
        rows = [{"query_id": 1, "doc_id": "d1"}, {"query_id": 2, "doc_id": "d2"}]
        write_jsonl(jsonl_path, rows)
        
        loaded = list(read_jsonl(jsonl_path))
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["query_id"], 1)

        # Malformed line error reporting
        bad_jsonl_path = self.tmp_dir / "bad.jsonl"
        atomic_write_text(bad_jsonl_path, '{"a": 1}\n{not_json}\n')
        with self.assertRaises(SchemaInvalidError) as ctx:
            list(read_jsonl(bad_jsonl_path))
        self.assertIn(":2", str(ctx.exception))

    def test_cli_help(self) -> None:
        # Calling without args prints help and returns 0
        exit_code = main([])
        self.assertEqual(exit_code, 0)
        # Calling with --help raises SystemExit(0)
        with self.assertRaises(SystemExit) as ctx:
            main(["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
