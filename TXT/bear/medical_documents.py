"""Optional, cacheable extraction of literally anchored document term candidates.

This stage supplies literal terms to sapbert-cache without changing the index
or lexical gate. Extraction alone does not change rankings or recall.
Assertion labels are model annotations for inspection, not validated diagnoses.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .contracts import SchemaInvalidError, reject_duplicate_keys, validate_doc_id
from .io import canonical_sha256, resolve_repo_path
from .medical_query import KINDS, _chat, validate_llm_config
from .medical_kb import LANGUAGES

ASSERTIONS = {"affirmed", "negated", "uncertain", "historical"}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _windows(document: Mapping[str, Any], config: Mapping[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    limit = config.get("document_max_chars", 24000)
    overflow = config.get("document_overflow", "error")
    if type(limit) is not int or limit <= 0 or overflow not in {"error", "prefix"}:
        raise SchemaInvalidError("document_max_chars must be positive; document_overflow must be error or prefix")
    length = len(document["title"]) + len(document["body"])
    if length > limit and overflow == "error":
        raise SchemaInvalidError(f"Document has {length} characters, over document_max_chars={limit}; explicitly select document_overflow=prefix or increase the reviewed prompt budget")
    remaining = limit
    windows = []
    for field in ("title", "body"):
        original = document[field]
        end = min(len(original), remaining)
        if end:
            windows.append({"field": field, "start": 0, "end": end,
                            "original_length": len(original), "text": original[:end]})
        remaining -= end
    return windows, length > limit


def extract_document(document: Mapping[str, Any], llm_config: Mapping[str, Any]) -> dict[str, Any]:
    """One <15B LLM call/document, anchored terms and a complete cache identity.

    Input: doc_id, title/body strings, lang=vi|zh|en. The default sends full text up
    to 24,000 characters, rejecting larger inputs. Opt-in prefix truncation saves
    explicit source windows and cannot be interpreted as whole-document coverage.
    """
    config = validate_llm_config(llm_config)
    doc_id = validate_doc_id(document.get("doc_id"))
    title, body = document.get("title", ""), document.get("body")
    lang = document.get("lang")
    if not isinstance(title, str) or not isinstance(body, str) or not (title.strip() or body.strip()):
        raise SchemaInvalidError("Document extraction requires nonempty title/body strings")
    if lang not in LANGUAGES:
        raise SchemaInvalidError("Document extraction lang must be vi, zh or en")
    original = {"title": title, "body": body}
    windows, truncated = _windows(original, config)
    prompt_path = (resolve_repo_path(config["document_prompt_path"]) if config.get("document_prompt_path")
                   else Path(__file__).resolve().parent.parent / "prompts" / "medical_document_terms.txt")
    prompt = prompt_path.read_text(encoding="utf-8")
    payload = {"doc_id": doc_id, "lang": lang, "windows": windows, "truncated": truncated}
    raw, response_metadata = _chat([{"role": "system", "content": prompt},
                                   {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}], config)
    try:
        parsed = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, TypeError) as exc:
        raise SchemaInvalidError("Document term LLM must return one JSON object without Markdown") from exc
    if not isinstance(parsed, dict) or not isinstance(parsed.get("terms"), list):
        raise SchemaInvalidError("Document term response requires a terms list")
    by_field = {window["field"]: window for window in windows}
    terms, seen = [], set()
    for term in parsed["terms"]:
        if not isinstance(term, dict):
            raise SchemaInvalidError("Document terms must be objects")
        text, field = term.get("text"), term.get("field")
        kind, assertion = term.get("kind"), term.get("assertion")
        if not isinstance(field, str) or field not in by_field or not isinstance(text, str) or not text.strip():
            raise SchemaInvalidError("Document candidate needs literal text and an observed field")
        if not isinstance(kind, str) or kind not in KINDS - {"intent"} or not isinstance(assertion, str) or assertion not in ASSERTIONS:
            raise SchemaInvalidError("Document candidate has an invalid kind/assertion")
        window = by_field[field]
        anchor = term.get("anchor")
        if anchor is None:
            first = window["text"].find(text)
            if first < 0 or window["text"].find(text, first + 1) >= 0:
                raise SchemaInvalidError("Unanchored or ambiguous repeated candidate; provide exact original-field offsets")
            start, end = window["start"] + first, window["start"] + first + len(text)
        elif isinstance(anchor, dict):
            start, end = anchor.get("start"), anchor.get("end")
        else:
            raise SchemaInvalidError("Document anchor must be an object")
        if type(start) is not int or type(end) is not int or not window["start"] <= start < end <= window["end"] or original[field][start:end] != text:
            raise SchemaInvalidError("Document candidate anchor does not exactly slice the supplied original field/window")
        key = (field, start, end)
        if key in seen:
            raise SchemaInvalidError("Duplicate document candidate anchor; emit each occurrence once")
        seen.add(key)
        terms.append({"text": text, "field": field, "kind": kind, "assertion": assertion,
                      "anchor": {"start": start, "end": end}, "origin": "document_literal"})
    hashes = {"title_sha256": _sha(title), "body_sha256": _sha(body)}
    return {"schema_version": 1, "doc_id": doc_id, "lang": lang,
            "terms": sorted(terms, key=lambda term: (term["field"], term["anchor"]["start"], term["anchor"]["end"])),
            "scope": "diagnostic_term_candidates_only", "truncated": truncated,
            "windows": [{key: value for key, value in window.items() if key != "text"} for window in windows],
            **hashes,
            "metadata": {"method": "medical_document_terms_v1", "model": config["model"],
                         "num_parameters_b": config["num_parameters_b"],
                         "prompt_sha256": _sha(prompt), "document_sha256": canonical_sha256(hashes),
                         "input_sha256": canonical_sha256(payload), "llm_raw_output": raw,
                         "response": response_metadata,
                         "llm_config": {key: value for key, value in config.items() if key != "api_key"},
                         "index_modified": False, "recall_improvement_verified": False}}
