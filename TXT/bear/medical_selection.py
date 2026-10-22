"""Bounded optional LLM document selection after deterministic score fusion.

The LLM may select only from the existing selected documents. Scores and their
relative order are never rewritten. Labels and relevance judgments are never
included in the prompt; document/query strings are untrusted source data.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import SchemaInvalidError, reject_duplicate_keys, validate_doc_id
from .io import canonical_sha256, resolve_repo_path
from .medical_query import _chat, validate_llm_config
from .medical_scoring import finite


def validate_selection_config(config: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(config, Mapping):
        raise SchemaInvalidError("LLM selection config must be an object")
    extra = set(config) - {"max_candidates", "document_max_chars", "min_docs", "max_docs", "prompt_path"}
    if extra:
        raise SchemaInvalidError(f"Unknown LLM selection config keys: {sorted(map(str, extra))}")
    for key, default, minimum in (("max_candidates", 40, 1), ("document_max_chars", 2000, 1),
                                  ("min_docs", 0, 0), ("max_docs", 40, 0)):
        value = config.get(key, default)
        if type(value) is not int or value < minimum:
            raise SchemaInvalidError(f"LLM selection {key} must be an integer >= {minimum}")
    if config.get("min_docs", 0) > config.get("max_docs", 40):
        raise SchemaInvalidError("LLM selection min_docs cannot exceed max_docs")
    if config.get("min_docs", 0) > config.get("max_candidates", 40):
        raise SchemaInvalidError("LLM selection min_docs cannot exceed max_candidates")
    if "prompt_path" in config and (not isinstance(config["prompt_path"], str) or not config["prompt_path"]):
        raise SchemaInvalidError("LLM selection prompt_path must be nonempty")
    return config


def cherry_pick(record: Mapping[str, Any], documents: Sequence[Mapping[str, Any]],
                llm_config: Mapping[str, Any], config: Mapping[str, Any]) -> dict[str, Any]:
    """Select from a bounded score-ordered shortlist; return selection metadata.

    `record` is a score_record result. `documents` contains doc_id/title/body.
    Empty shortlists skip the endpoint. Invalid responses raise an error rather
    than silently substituting another selector. Valid undersized selections
    are filled deterministically from the original score order when requested.
    """
    validate_selection_config(config)
    llm = validate_llm_config(llm_config)
    query = record.get("query")
    if not isinstance(query, str) or not query.strip():
        raise SchemaInvalidError("LLM selection requires nonempty query text")
    ranking = record.get("ranking")
    selected = record.get("selection", {}).get("doc_ids")
    if not isinstance(ranking, list) or not isinstance(selected, list):
        raise SchemaInvalidError("LLM selection requires ranking and selection.doc_ids lists")
    selected_ids = [validate_doc_id(identity) for identity in selected]
    if len(set(selected_ids)) != len(selected_ids):
        raise SchemaInvalidError("Original selected document IDs must be unique")
    ranked_ids = []
    for row in ranking:
        if not isinstance(row, Mapping):
            raise SchemaInvalidError("Ranking rows must be objects")
        ranked_ids.append(validate_doc_id(row.get("doc_id")))
        finite(row.get("fused_score", row.get("score")), "fusion score")
    if len(set(ranked_ids)) != len(ranked_ids) or set(selected_ids) - set(ranked_ids):
        raise SchemaInvalidError("Selected IDs must belong to a ranking with unique IDs")
    ordered = sorted(ranking, key=lambda row: (-finite(row.get("fused_score", row.get("score")), "fusion score"), row["doc_id"]))
    selected_set = set(selected_ids)
    shortlist = [row for row in ordered if row["doc_id"] in selected_set][:config.get("max_candidates", 40)]
    shortlist_ids = [row["doc_id"] for row in shortlist]
    by_id = {}
    for document in documents:
        if not isinstance(document, Mapping):
            raise SchemaInvalidError("Selection documents must be objects")
        identity = validate_doc_id(document.get("doc_id"))
        if identity in by_id:
            raise SchemaInvalidError("Selection documents must have unique doc_ids")
        by_id[identity] = document
    if set(shortlist_ids) - set(by_id):
        raise SchemaInvalidError("Missing text for shortlisted selection documents")
    prompt_path = (resolve_repo_path(config["prompt_path"]) if config.get("prompt_path") else
                   resolve_repo_path(llm["selection_prompt_path"]) if llm.get("selection_prompt_path") else
                   Path(__file__).resolve().parent.parent / "prompts" / "medical_selection.txt")
    prompt = prompt_path.read_text(encoding="utf-8")
    limit = config.get("document_max_chars", 2000)
    payload_documents, truncation = [], []
    for row in shortlist:
        identity = row["doc_id"]
        document = by_id[identity]
        title, body = document.get("title", ""), document.get("body", "")
        if not isinstance(title, str) or not isinstance(body, str) or not (title.strip() or body.strip()):
            raise SchemaInvalidError("Selection requires nonempty title/body strings")
        title_end = min(len(title), limit)
        body_end = min(len(body), limit - title_end)
        truncated = title_end < len(title) or body_end < len(body)
        payload_documents.append({"doc_id": identity, "title": title[:title_end], "body": body[:body_end],
                                  "truncated": truncated})
        truncation.append({"doc_id": identity, "truncated": truncated,
                           "title_original_chars": len(title), "body_original_chars": len(body),
                           "title_sent_chars": title_end, "body_sent_chars": body_end})
    payload = {"query": query, "documents": payload_documents}
    raw, response = None, None
    if shortlist:
        raw, response = _chat([{"role": "system", "content": prompt},
                               {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}], llm)
        try:
            parsed = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
        except (json.JSONDecodeError, TypeError) as exc:
            raise SchemaInvalidError("Selection LLM must return one JSON object without Markdown") from exc
        if not isinstance(parsed, dict) or set(parsed) != {"selected_doc_ids"} or not isinstance(parsed["selected_doc_ids"], list):
            raise SchemaInvalidError("Selection response must contain only a selected_doc_ids list")
        picked = [validate_doc_id(identity) for identity in parsed["selected_doc_ids"]]
        if len(set(picked)) != len(picked):
            raise SchemaInvalidError("Selection LLM returned duplicate document IDs")
        if set(picked) - set(shortlist_ids):
            raise SchemaInvalidError("Selection LLM returned IDs outside the supplied shortlist")
    else:
        picked = []
    picked_set = set(picked)
    ordered_picks = [identity for identity in shortlist_ids if identity in picked_set]
    minimum, maximum = config.get("min_docs", 0), config.get("max_docs", 40)
    filled = []
    if len(ordered_picks) < minimum:
        for identity in shortlist_ids:
            if identity not in picked_set:
                picked_set.add(identity)
                filled.append(identity)
                if len(picked_set) >= minimum:
                    break
        ordered_picks = [identity for identity in shortlist_ids if identity in picked_set]
    before_cap = len(ordered_picks)
    final_ids = ordered_picks[:maximum]
    return {"mode": "llm_cherry_pick", "doc_ids": final_ids, "selected_count": len(final_ids),
            "candidate_count": len(shortlist_ids), "shortlist_doc_ids": shortlist_ids,
            "original_selected_count": len(selected_ids), "llm_selected_doc_ids": picked,
            "shortlist_removed_count": len(selected_ids) - len(shortlist_ids),
            "fallback_added_count": len(filled), "fallback_added_doc_ids": filled,
            "cap_removed_count": before_cap - len(final_ids), "before_cap_count": before_cap,
            "minimum_unmet": len(final_ids) < minimum, "truncation": truncation,
            "metadata": {"method": "medical_selection_v1", "model": llm["model"],
                         "num_parameters_b": llm["num_parameters_b"],
                         "input_sha256": canonical_sha256(payload),
                         "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                         "config": dict(config), "llm_raw_output": raw, "response": response,
                         "skipped_empty_shortlist": not shortlist, "scores_modified": False}}
