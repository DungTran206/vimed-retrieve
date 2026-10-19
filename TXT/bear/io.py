"""Input/Output helpers, path bounds enforcement, atomic writes, and canonical hashing."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .contracts import (
    ERROR_OUTPUT_OUTSIDE_TXT,
    ERROR_SCHEMA_INVALID,
    INPUTS_DIR,
    REPO_ROOT,
    TXT_DIR,
    OutputOutsideTXTError,
    SchemaInvalidError,
    reject_duplicate_keys,
)


def assert_valid_output_path(target_path: Path | str, input_paths: Sequence[Path | str] = ()) -> Path:
    """Enforce that target_path resolves strictly under REPO_ROOT/TXT and not in inputs or colliding with inputs.
    
    Rules per PLAN.md §3.3:
    1. Must resolve and reside under REPO_ROOT/TXT.
    2. Must not equal REPO_ROOT/TXT or REPO_ROOT itself.
    3. Prefix comparison like 'TXT_other' is rejected by using Path.is_relative_to.
    4. Must not be inside TXT/inputs/ (read-only destination for external inputs).
    5. Must not collide with any input_path.
    """
    path_obj = Path(target_path).resolve()
    resolved_txt = TXT_DIR.resolve()
    resolved_inputs = INPUTS_DIR.resolve()

    # Rule 1 & 3: Must be inside TXT
    try:
        is_rel = path_obj.is_relative_to(resolved_txt)
    except AttributeError:
        # Fallback for older python, though Python 3.9+ supports is_relative_to
        try:
            path_obj.relative_to(resolved_txt)
            is_rel = True
        except ValueError:
            is_rel = False

    if not is_rel:
        raise OutputOutsideTXTError(
            f"Output path '{path_obj}' is outside TXT directory '{resolved_txt}'",
            details={"target_path": str(path_obj), "txt_dir": str(resolved_txt)},
        )

    # Rule 2: Cannot be the TXT directory itself
    if path_obj == resolved_txt:
        raise OutputOutsideTXTError(
            f"Output path cannot be the root TXT directory itself: '{path_obj}'",
            details={"target_path": str(path_obj)},
        )

    # Rule 4: Cannot write into TXT/inputs/
    try:
        in_inputs = path_obj.is_relative_to(resolved_inputs)
    except AttributeError:
        try:
            path_obj.relative_to(resolved_inputs)
            in_inputs = True
        except ValueError:
            in_inputs = False

    if in_inputs:
        raise OutputOutsideTXTError(
            f"Output path '{path_obj}' cannot be placed inside read-only inputs directory '{resolved_inputs}'",
            details={"target_path": str(path_obj), "inputs_dir": str(resolved_inputs)},
        )

    # Rule 5: Cannot collide with input paths
    for inp in input_paths:
        if inp is None:
            continue
        inp_resolved = Path(inp).resolve()
        if path_obj == inp_resolved:
            raise OutputOutsideTXTError(
                f"Output path '{path_obj}' collides directly with input path '{inp_resolved}'",
                details={"target_path": str(path_obj), "input_path": str(inp_resolved)},
            )

    return path_obj


def resolve_repo_path(path_val: str | Path | None) -> Path | None:
    """Resolve a path relative to REPO_ROOT if it is relative; None stays None."""
    if path_val is None:
        return None
    p = Path(path_val)
    if p.is_absolute():
        return p.resolve()
    return (REPO_ROOT / p).resolve()


def canonical_json_dumps(obj: Any, indent: int | None = None) -> str:
    """Serialize object to strictly canonical JSON (no NaN, sorted keys, explicit separators)."""
    if indent is None:
        return json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    return json.dumps(
        obj,
        sort_keys=True,
        indent=indent,
        ensure_ascii=False,
        allow_nan=False,
    )


def canonical_sha256(obj: Any) -> str:
    """Return hex SHA-256 of canonical UTF-8 JSON representation."""
    canonical_str = canonical_json_dumps(obj)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def sha256_file(file_path: Path | str, chunk_size: int = 65536) -> str:
    """Compute SHA-256 checksum of a file by streaming chunks."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hashing: {path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_text(target_path: Path | str, content: str, encoding: str = "utf-8", input_paths: Sequence[Path | str] = ()) -> Path:
    """Write text atomically by writing to a .partial file in the same directory and renaming."""
    dest = assert_valid_output_path(target_path, input_paths=input_paths)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest.with_name(f"{dest.name}.partial")
    
    with open(temp_path, "w", encoding=encoding, newline="\n") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())

    os.replace(temp_path, dest)
    return dest


def atomic_write_json(target_path: Path | str, data: Any, indent: int | None = 2, input_paths: Sequence[Path | str] = ()) -> Path:
    """Write JSON data atomically."""
    content = canonical_json_dumps(data, indent=indent)
    return atomic_write_text(target_path, content, input_paths=input_paths)


def read_json(file_path: Path | str) -> Any:
    """Read JSON file with duplicate key rejection and error reporting with path."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        return json.loads(content, object_pairs_hook=reject_duplicate_keys, parse_constant=_reject_constant, parse_float=_finite_float)
    except json.JSONDecodeError as e:
        raise SchemaInvalidError(f"JSON decode error in {path}:{e.lineno}:{e.colno} - {e.msg}")


def read_jsonl(file_path: Path | str) -> Iterator[dict[str, Any]]:
    """Stream read JSONL file line by line with line-numbered error reporting."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"JSONL file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                row = json.loads(line_str, object_pairs_hook=reject_duplicate_keys, parse_constant=_reject_constant, parse_float=_finite_float)
            except json.JSONDecodeError as e:
                raise SchemaInvalidError(f"Invalid JSON at {path}:{line_no} - {e.msg}")
            if not isinstance(row, dict):
                raise SchemaInvalidError(f"Row at {path}:{line_no} must be a JSON object, got {type(row).__name__}")
            yield row


def write_jsonl(target_path: Path | str, rows: Iterable[Mapping[str, Any]], input_paths: Sequence[Path | str] = ()) -> Path:
    """Write rows to a JSONL file atomically."""
    dest = assert_valid_output_path(target_path, input_paths=input_paths)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest.with_name(f"{dest.name}.partial")
    
    with open(temp_path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            line = canonical_json_dumps(row)
            f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())

    os.replace(temp_path, dest)
    return dest


def load_config(config_path: Path | str) -> dict[str, Any]:
    """Load and perform baseline structural checks on a configuration file."""
    path = resolve_repo_path(config_path)
    cfg = read_json(path)
    if not isinstance(cfg, dict):
        raise SchemaInvalidError(f"Configuration root in {path} must be a JSON object")
    if "schema_version" not in cfg:
        raise SchemaInvalidError(f"Configuration in {path} missing required 'schema_version'")
    if type(cfg["schema_version"]) is not int or cfg["schema_version"] != 1:
        raise SchemaInvalidError(f"Unsupported schema_version {cfg['schema_version']} in {path}; expected 1")
    return cfg


def _reject_constant(value: str) -> None:
    raise SchemaInvalidError(f"JSON không cho phép {value}")


def _finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise SchemaInvalidError(f"JSON float vượt miền hữu hạn: {value}")
    return result

