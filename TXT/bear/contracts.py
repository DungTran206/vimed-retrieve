"""Data contracts, error codes, and strict validation primitives for BEAR."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

# Canonical error codes specified in PLAN.md §5.3
ERROR_INPUT_MISSING = "INPUT_MISSING"
ERROR_HASH_MISMATCH = "HASH_MISMATCH"
ERROR_SCHEMA_INVALID = "SCHEMA_INVALID"
ERROR_BASELINE_PARITY_FAILED = "BASELINE_PARITY_FAILED"
ERROR_FEATURE_UNAVAILABLE = "FEATURE_UNAVAILABLE"
ERROR_LABEL_COVERAGE_INSUFFICIENT = "LABEL_COVERAGE_INSUFFICIENT"
ERROR_EVALUATOR_UNVERIFIED = "EVALUATOR_UNVERIFIED"
ERROR_OUTPUT_OUTSIDE_TXT = "OUTPUT_OUTSIDE_TXT"

# Standard repository directory layout
TXT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = TXT_DIR.parent
INPUTS_DIR = TXT_DIR / "inputs"
RUNTIME_DIR = TXT_DIR / "runtime"
REPORTS_DIR = TXT_DIR / "reports"
MANIFESTS_DIR = TXT_DIR / "manifests"
CONFIGS_DIR = TXT_DIR / "configs"


class BearError(Exception):
    """Base exception for all BEAR failures with an explicit error code."""

    def __init__(self, message: str, code: str = ERROR_SCHEMA_INVALID, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.details = dict(details or {})


class InputMissingError(BearError):
    def __init__(self, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message, code=ERROR_INPUT_MISSING, details=details)


class HashMismatchError(BearError):
    def __init__(self, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message, code=ERROR_HASH_MISMATCH, details=details)


class SchemaInvalidError(BearError):
    def __init__(self, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message, code=ERROR_SCHEMA_INVALID, details=details)


class BaselineParityFailedError(BearError):
    def __init__(self, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message, code=ERROR_BASELINE_PARITY_FAILED, details=details)


class FeatureUnavailableError(BearError):
    def __init__(self, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message, code=ERROR_FEATURE_UNAVAILABLE, details=details)


class LabelCoverageInsufficientError(BearError):
    def __init__(self, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message, code=ERROR_LABEL_COVERAGE_INSUFFICIENT, details=details)


class EvaluatorUnverifiedError(BearError):
    def __init__(self, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message, code=ERROR_EVALUATOR_UNVERIFIED, details=details)


class OutputOutsideTXTError(BearError):
    def __init__(self, message: str, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message, code=ERROR_OUTPUT_OUTSIDE_TXT, details=details)


def reject_duplicate_keys(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    """JSON object_pairs_hook that raises SchemaInvalidError on duplicate keys."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SchemaInvalidError(f"Duplicate key '{key}' encountered in JSON object")
        result[key] = value
    return result


def validate_finite_number(
    val: Any,
    field_name: str,
    allow_none: bool = False,
    min_val: float | None = None,
    max_val: float | None = None,
) -> float | None:
    """Validate that val is a strictly finite number (not bool, NaN, or Inf)."""
    if val is None:
        if allow_none:
            return None
        raise SchemaInvalidError(f"Field '{field_name}' cannot be None")

    # In Python, bool is a subclass of int: reject bool explicitly
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise SchemaInvalidError(
            f"Field '{field_name}' must be a finite number, got {type(val).__name__}: {val!r}"
        )

    val_f = float(val)
    if not math.isfinite(val_f):
        raise SchemaInvalidError(f"Field '{field_name}' must be finite, got non-finite: {val_f}")

    if min_val is not None and val_f < min_val:
        raise SchemaInvalidError(f"Field '{field_name}' = {val_f} is below minimum {min_val}")
    if max_val is not None and val_f > max_val:
        raise SchemaInvalidError(f"Field '{field_name}' = {val_f} exceeds maximum {max_val}")

    return val_f


def validate_doc_id(doc_id: Any, field_name: str = "doc_id") -> str:
    """Validate document ID representation: non-empty string, no whitespace padding, no float syntax."""
    if not isinstance(doc_id, str):
        if isinstance(doc_id, int) and not isinstance(doc_id, bool):
            doc_id = str(doc_id)
        else:
            raise SchemaInvalidError(
                f"{field_name} must be a valid string identifier, got {type(doc_id).__name__}: {doc_id!r}"
            )
    clean = doc_id.strip()
    if not clean:
        raise SchemaInvalidError(f"{field_name} cannot be empty or pure whitespace")
    if clean != doc_id:
        raise SchemaInvalidError(f"{field_name} '{doc_id}' has leading or trailing whitespace")
    if "." in clean:
        raise SchemaInvalidError(f"{field_name} '{doc_id}' contains invalid decimal point format")
    if clean.isdecimal() and (not clean.isascii() or str(int(clean)) != clean or int(clean) <= 0):
        raise SchemaInvalidError(f"{field_name}: ID số phải canonical, không nhận '{clean}'")
    return clean


def validate_query_id(qid: Any, field_name: str = "query_id") -> int:
    """Validate query ID: positive integer, not bool, not float."""
    if isinstance(qid, bool) or not isinstance(qid, int):
        if isinstance(qid, str) and qid.isdigit():
            qid = int(qid)
        else:
            raise SchemaInvalidError(
                f"{field_name} must be an integer, got {type(qid).__name__}: {qid!r}"
            )
    if qid <= 0:
        raise SchemaInvalidError(f"{field_name} must be positive, got {qid}")
    return qid


@dataclass(frozen=True)
class RankedDoc:
    """Single ranked document representation with rank and raw score."""
    query_id: int
    doc_id: str
    rank: int
    score: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_query_id(self.query_id)
        validate_doc_id(self.doc_id)
        if self.rank < 1:
            raise SchemaInvalidError(f"rank must be >= 1, got {self.rank}")
        validate_finite_number(self.score, "score")

