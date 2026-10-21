"""One-call medical query preparation and deterministic concept matching.

LLM tiers describe importance in the original query, not document relevance.
Expansion is selected from attributed KB records; generated aliases and model
self-reported confidence are never accepted as evidence or token probabilities.
"""

from __future__ import annotations

import copy
import json
import math
import os
import re
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import SchemaInvalidError, reject_duplicate_keys
from .io import canonical_sha256, resolve_repo_path
from .medical_kb import LANGUAGES, concept_terms, validate_kb

DEFAULT_MODEL = "Qwen/Qwen3.5-9B"
TIER_SCORES = (0.05, 0.30, 0.70, 1.00)
INTENTS = {"symptoms", "causes", "diagnosis", "treatment", "dosage", "contraindications",
           "interactions", "adverse_effects", "prognosis", "prevention", "general", "unknown"}
KINDS = {"disease", "symptom", "drug", "population", "subtype", "constraint", "intent", "other"}
PROBABILITY_METHODS = {"backend_label_logits", "backend_label_probabilities"}
_PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


def _han(character: str) -> bool:
    code = ord(character)
    return 0x3400 <= code <= 0x9FFF or 0x20000 <= code <= 0x323AF


def _normalized_offsets(text: str) -> tuple[str, list[tuple[int, int]]]:
    """NFC + casefold while mapping each normalized codepoint to original spans."""
    normalized = []
    offsets = []
    index = 0
    while index < len(text):
        end = index + 1
        while end < len(text) and unicodedata.combining(text[end]):
            end += 1
        segment = unicodedata.normalize("NFC", text[index:end]).casefold()
        normalized.append(segment)
        offsets.extend([(index, end)] * len(segment))
        index = end
    return "".join(normalized), offsets


def find_term_spans(text: str, term: str) -> list[dict[str, Any]]:
    """Exact NFC/casefold phrase matches; Latin/digit boundaries, Han adjacency.

    Diacritics and punctuation remain significant. Unlike substring search,
    BRCA1 cannot match BRCA10 and a Vietnamese word cannot match inside another.
    Returned offsets always slice the original, possibly decomposed Unicode text.
    """
    haystack, offsets = _normalized_offsets(text)
    needle = unicodedata.normalize("NFC", term).casefold()
    if not needle:
        return []
    result = []
    for match in re.finditer(re.escape(needle), haystack):
        start, end = match.span()
        first, last = needle[0], needle[-1]
        if first.isalnum() and not _han(first) and start:
            prev = haystack[start - 1]
            if (prev.isalnum() or prev == "_") and not _han(prev):
                continue
            if first.isdigit() and prev in ",." and start > 1 and haystack[start - 2].isdigit():
                continue
        if last.isalnum() and not _han(last) and end < len(haystack):
            after = haystack[end]
            if (after.isalnum() or after == "_") and not _han(after):
                continue
            if last.isdigit() and after in ",." and end + 1 < len(haystack) and haystack[end + 1].isdigit():
                continue
        original_start, original_end = offsets[start][0], offsets[end - 1][1]
        result.append({"start": original_start, "end": original_end,
                       "text": text[original_start:original_end]})
    return result


def _aliases(concept: Mapping[str, Any]) -> dict[str, list[str]]:
    return {lang: concept_terms(concept, lang) for lang in LANGUAGES}


def _candidates(query: str, lang: str, rows: Sequence[Mapping[str, Any]],
                max_candidates: int) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Only forward disease->symptom edges from a literally named disease."""
    named_diseases = {}
    expansions = {}
    for row in rows:
        disease = row["disease"]
        if not any(find_term_spans(query, term) for term in concept_terms(disease)):
            continue
        named_diseases[disease["concept_id"]] = disease
        symptom = row["symptom"]
        label = symptom["labels"].get(lang)
        if not label:  # Never silently add Chinese terms to a Vietnamese corpus query.
            continue
        expansion = {"concept_id": symptom["concept_id"], "text": label, "lang": lang,
                     "origin": "kb", "relation": "has_symptom",
                     "disease_id": disease["concept_id"], "source": row["source"],
                     "aliases": _aliases(symptom)}
        for key in ("context", "frequency", "provenance"):
            if key in row:
                expansion[key] = row[key]
        expansion_id = "exp:" + canonical_sha256(expansion)
        expansions[expansion_id] = {"expansion_id": expansion_id, **expansion}
    if len(expansions) > max_candidates:
        raise SchemaInvalidError(f"KB lookup returned {len(expansions)} candidates, over max_kb_candidates={max_candidates}; review data or raise the explicit prompt budget")
    ordered = [expansions[key] for key in sorted(expansions)]
    return ordered, named_diseases


def validate_llm_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Require an explicit <15B declaration for any model override."""
    result = dict(config)
    model = result.get("model", DEFAULT_MODEL)
    count = result.get("num_parameters_b", 9 if model == DEFAULT_MODEL else None)
    if isinstance(count, bool) or not isinstance(count, (int, float)) or not math.isfinite(count) or not 0 < count < 15:
        raise SchemaInvalidError("LLM num_parameters_b must explicitly be >0 and <15 (model overrides require this metadata)")
    result.update(model=model, num_parameters_b=count)
    return result


def _chat(messages: list[dict[str, str]], config: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    base_url = config.get("base_url", "http://127.0.0.1:8000/v1")
    if not isinstance(base_url, str) or not base_url.startswith(("http://", "https://")):
        raise SchemaInvalidError("LLM base_url must be an OpenAI-compatible HTTP(S) endpoint")
    payload = {"model": config["model"], "messages": messages, "temperature": 0,
               "max_tokens": config.get("max_tokens", 2048),
               "chat_template_kwargs": {"enable_thinking": config.get("enable_thinking", False)}}
    if config.get("json_mode", True):
        payload["response_format"] = {"type": "json_object"}
    headers = {"Content-Type": "application/json"}
    api_key_env = config.get("api_key_env")
    if api_key_env:
        key = os.environ.get(api_key_env)
        if not key:
            raise SchemaInvalidError(f"LLM credential environment variable is unset: {api_key_env}")
        headers["Authorization"] = "Bearer " + key
    request = urllib.request.Request(base_url.rstrip("/") + "/chat/completions",
                                     data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=config.get("timeout_seconds", 120)) as response:
            result = json.load(response, object_pairs_hook=reject_duplicate_keys)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise SchemaInvalidError(f"Medical query LLM endpoint failed: {type(exc).__name__}; verify endpoint/model, no fallback facts were generated") from exc
    if not isinstance(result, dict):
        raise SchemaInvalidError("LLM endpoint response must be a JSON object")
    served_model = result.get("model")
    expected_served_model = config.get("expected_served_model", config["model"])
    if served_model is not None and served_model != expected_served_model:
        raise SchemaInvalidError(f"LLM endpoint served model {served_model!r}, expected {expected_served_model!r}; verify the <15B deployment and explicitly configure expected_served_model for a reviewed server alias")
    try:
        raw = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise SchemaInvalidError("LLM response has no choices[0].message.content") from exc
    if not isinstance(raw, str):
        raise SchemaInvalidError("LLM content must be a JSON string")
    # No extraction of the model's generated confidence. Most chat endpoints do
    # not return full candidate-label probabilities for this structured task.
    return raw, {"response_id": result.get("id"), "served_model": result.get("model"),
                 "usage": result.get("usage"), "probability_method": "hard_tier"}


def validate_prepared(record: Mapping[str, Any], kb_rows: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Validate import/cache records without coercing invalid anchors or scores.

    Supply kb_rows at import/preparation boundaries to verify actual aliases,
    expansion selections and their hashes, rather than merely their provenance
    structure. Without the KB this validator can only check the declared source.
    """
    result = copy.deepcopy(dict(record))
    if set(result) & {"gold", "not_gold", "G", "gold_unseen", "qrels", "judgments", "label", "labels"}:
        raise SchemaInvalidError("Prepared inference queries must be label-free; use validation labels only in fit/tune/evaluate")
    verified_rows = validate_kb(kb_rows) if kb_rows is not None else None
    kb_concepts = ({concept["concept_id"]: concept for row in verified_rows
                    for concept in (row["disease"], row["symptom"])} if verified_rows is not None else {})
    if type(result.get("id")) is not int or result["id"] < 0:
        raise SchemaInvalidError("Prepared query id must be a nonnegative integer")
    query = result.get("query")
    if not isinstance(query, str) or not query.strip():
        raise SchemaInvalidError("Prepared query must contain nonempty query text")
    if result.get("lang") not in LANGUAGES:
        raise SchemaInvalidError("Prepared query lang must be vi or zh")
    intents = result.get("intent")
    if not isinstance(intents, list) or not intents or any(not isinstance(intent, str) or intent not in INTENTS for intent in intents):
        raise SchemaInvalidError("Prepared query intent must use the defined retrieval intent labels")
    concepts = result.get("concepts")
    expansions = result.get("expansion_terms", [])
    if not isinstance(concepts, list) or not isinstance(expansions, list):
        raise SchemaInvalidError("concepts and expansion_terms must be lists")
    seen = set()
    for concept in concepts:
        if not isinstance(concept, dict):
            raise SchemaInvalidError("Every query concept must be an object")
        cid = concept.get("concept_id")
        if not isinstance(cid, str) or not cid.strip() or cid in seen:
            raise SchemaInvalidError("Query concept IDs must be nonempty and unique")
        seen.add(cid)
        text, anchor = concept.get("text"), concept.get("anchor")
        if not isinstance(text, str) or not text or not isinstance(anchor, dict):
            raise SchemaInvalidError(f"Concept {cid} needs literal text and anchor")
        start, end = anchor.get("start"), anchor.get("end")
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(query) or query[start:end] != text:
            raise SchemaInvalidError(f"Concept {cid} anchor does not exactly slice original query")
        if concept.get("origin") != "query" or concept.get("kind") not in KINDS:
            raise SchemaInvalidError(f"Concept {cid} has invalid origin/kind")
        if type(concept.get("tier")) is not int or not 1 <= concept["tier"] <= 4:
            raise SchemaInvalidError(f"Concept {cid} tier must be integer 1..4")
        if type(concept.get("required")) is not bool:
            raise SchemaInvalidError(f"Concept {cid} required must be boolean")
        aliases = concept.get("aliases", {})
        if not isinstance(aliases, dict) or set(aliases) - set(LANGUAGES):
            raise SchemaInvalidError(f"Concept {cid} aliases must be grouped by vi/zh")
        for terms in aliases.values():
            if not isinstance(terms, list) or any(not isinstance(term, str) or not term.strip() for term in terms):
                raise SchemaInvalidError(f"Concept {cid} aliases must be lists of nonempty strings")
        extra_aliases = [term for terms in aliases.values() for term in terms if term != text]
        alias_provenance = concept.get("alias_provenance")
        if extra_aliases and (not isinstance(alias_provenance, dict)
                              or alias_provenance.get("kind") != "canonical_kb"
                              or alias_provenance.get("concept_id") != cid
                              or not isinstance(alias_provenance.get("kb_sha256"), str)
                              or not re.fullmatch(r"[0-9a-f]{64}", alias_provenance["kb_sha256"])):
            raise SchemaInvalidError(f"Concept {cid} nonliteral aliases need canonical KB provenance")
        if verified_rows is not None and alias_provenance:
            if cid not in kb_concepts or aliases != _aliases(kb_concepts[cid]) or alias_provenance.get("kb_sha256") != canonical_sha256(verified_rows):
                raise SchemaInvalidError(f"Concept {cid} aliases/provenance do not match the supplied KB")
            if unicodedata.normalize("NFC", text).casefold() not in {unicodedata.normalize("NFC", term).casefold() for term in concept_terms(kb_concepts[cid])}:
                raise SchemaInvalidError(f"Concept {cid} literal query text is not a verified KB label/alias")
        probs = concept.get("probabilities")
        if probs is not None:
            if concept.get("probability_method") not in PROBABILITY_METHODS or not isinstance(concept.get("probability_provenance"), dict) or not concept["probability_provenance"]:
                raise SchemaInvalidError(f"Concept {cid}: probabilities require actual backend label probability/logit provenance")
            if not isinstance(probs, list) or len(probs) != 4 or any(isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1 for p in probs) or not math.isclose(sum(probs), 1, abs_tol=1e-6):
                raise SchemaInvalidError(f"Concept {cid}: probabilities must be four finite values summing to 1")
    expansion_ids = set()
    for expansion in expansions:
        if not isinstance(expansion, dict):
            raise SchemaInvalidError("Every expansion must be an object")
        eid = expansion.get("expansion_id")
        if not isinstance(eid, str) or not eid or eid in expansion_ids:
            raise SchemaInvalidError("Expansion IDs must be present and unique")
        expansion_ids.add(eid)
        source = expansion.get("source")
        if expansion.get("origin") != "kb" or expansion.get("relation") != "has_symptom" or not isinstance(source, dict) or not source.get("name") or not source.get("record_id"):
            raise SchemaInvalidError("Expansions must have KB relation and source provenance")
        query_diseases = {concept["concept_id"] for concept in concepts if concept["kind"] == "disease"}
        if expansion.get("disease_id") not in query_diseases or expansion.get("lang") != result["lang"]:
            raise SchemaInvalidError("Expansion must originate from an anchored query disease and match query language")
        if not isinstance(expansion.get("concept_id"), str) or not isinstance(expansion.get("text"), str) or not expansion["text"].strip():
            raise SchemaInvalidError("Expansion requires a symptom concept ID and nonempty text")
    if verified_rows is not None:
        whitelist_rows, _ = _candidates(query, result["lang"], verified_rows, max(1, len(verified_rows)))
        whitelist = {row["expansion_id"]: row for row in whitelist_rows}
        for expansion in expansions:
            if expansion["expansion_id"] not in whitelist or expansion != whitelist[expansion["expansion_id"]]:
                raise SchemaInvalidError("Imported expansion does not exactly match an attributed KB candidate")
    return result


def prepare_query(query_record: Mapping[str, Any], kb_rows: Sequence[Mapping[str, Any]],
                  llm_config: Mapping[str, Any]) -> dict[str, Any]:
    """Call configured <15B model once; build a validated, cacheable query record.

    Required query fields: id (int), query (str), lang (vi|zh). No model is loaded or
    downloaded automatically. Caller owns caching/resume and endpoint lifecycle.
    """
    query = query_record.get("query")
    lang = query_record.get("lang", "vi")
    if not isinstance(query, str) or not query.strip() or lang not in LANGUAGES:
        raise SchemaInvalidError("Query preparation requires nonempty query and vi/zh lang")
    config = validate_llm_config(llm_config)
    rows = validate_kb(kb_rows)
    max_candidates = config.get("max_kb_candidates", 256)
    if type(max_candidates) is not int or max_candidates <= 0:
        raise SchemaInvalidError("max_kb_candidates must be a positive integer")
    candidates, diseases = _candidates(query, lang, rows, max_candidates)
    system_path = resolve_repo_path(config["system_prompt_path"]) if config.get("system_prompt_path") else _PROMPTS / "medical_query_system.txt"
    user_path = resolve_repo_path(config["user_prompt_path"]) if config.get("user_prompt_path") else _PROMPTS / "medical_query_user.txt"
    system = system_path.read_text(encoding="utf-8")
    template = user_path.read_text(encoding="utf-8")
    payload = {"original_query": query, "lang": lang, "named_kb_diseases": list(diseases.values()),
               "kb_expansion_whitelist": candidates}
    user = template.replace("{payload}", json.dumps(payload, ensure_ascii=False))
    raw, response_metadata = _chat([{"role": "system", "content": system},
                                    {"role": "user", "content": user}], config)
    try:
        parsed = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, TypeError) as exc:
        raise SchemaInvalidError("LLM must return one valid JSON object without Markdown") from exc
    if not isinstance(parsed, dict) or not isinstance(parsed.get("concepts"), list):
        raise SchemaInvalidError("LLM response requires a concepts list")
    concepts = []
    for concept in parsed["concepts"]:
        if not isinstance(concept, dict):
            raise SchemaInvalidError("LLM concepts must be objects")
        text = concept.get("text")
        if not isinstance(text, str) or not text or text not in query:
            raise SchemaInvalidError("LLM concept must be copied literally from original query")
        cid = concept.get("concept_id")
        kb_concept = diseases.get(cid) if isinstance(cid, str) else None
        if cid is not None and kb_concept is None:
            raise SchemaInvalidError("LLM concept ID is not an offered, named disease ID")
        if kb_concept and not any(unicodedata.normalize("NFC", text).casefold() == unicodedata.normalize("NFC", term).casefold() for term in concept_terms(kb_concept)):
            raise SchemaInvalidError("LLM attached KB concept ID to an unverified alias")
        cid = cid or "query:" + canonical_sha256({"text": unicodedata.normalize("NFC", text).casefold()})[:24]
        start = query.find(text)
        aliases = _aliases(kb_concept) if kb_concept else {language: ([text] if language == lang else []) for language in LANGUAGES}
        entry = {"concept_id": cid, "text": text, "kind": concept.get("kind"),
                 "origin": "query", "tier": concept.get("tier"), "required": concept.get("required"),
                 "probabilities": None, "probability_method": "hard_tier",
                 "aliases": aliases, "anchor": {"start": start, "end": start + len(text)}}
        if kb_concept:
            if entry["kind"] != "disease":
                raise SchemaInvalidError("A named KB disease ID must have kind=disease")
            entry["alias_provenance"] = {"kind": "canonical_kb", "concept_id": cid,
                                          "kb_sha256": canonical_sha256(rows)}
        concepts.append(entry)
    selected = parsed.get("selected_expansion_ids", [])
    if not isinstance(selected, list) or any(not isinstance(eid, str) for eid in selected) or len(set(selected)) != len(selected):
        raise SchemaInvalidError("selected_expansion_ids must be a list of unique whitelist IDs")
    whitelist = {candidate["expansion_id"]: candidate for candidate in candidates}
    if any(eid not in whitelist for eid in selected):
        raise SchemaInvalidError("LLM selected a nonwhitelisted expansion ID")
    intents = parsed.get("intent")
    # This first experiment permits forward symptom enrichment only when the
    # query explicitly asks about manifestations or a general disease overview.
    forbidden = {"dosage", "treatment", "contraindications", "interactions"}
    if selected and (not isinstance(intents, list) or not set(intents) & {"symptoms", "general"} or set(intents) & forbidden):
        raise SchemaInvalidError("Symptom expansion is not allowed for this query intent")
    prepared = {"schema_version": 1, "id": query_record.get("id"), "query": query,
                "lang": lang, "intent": intents, "concepts": concepts,
                "expansion_terms": [whitelist[eid] for eid in selected],
                "metadata": {"method": "medical_query_taxonomy_v1", "model": config["model"],
                             "num_parameters_b": config["num_parameters_b"],
                             "kb_sha256": canonical_sha256(rows),
                             "prompt_sha256": canonical_sha256({"system": system, "user_template": template}),
                             "input_sha256": canonical_sha256(payload),
                             "llm_raw_output": raw, "response": response_metadata,
                             "llm_config": {key: value for key, value in config.items() if key != "api_key"}}}
    return validate_prepared(prepared, kb_rows=rows)


def match_concepts(prepared: Mapping[str, Any], document: str | Mapping[str, Any]) -> list[dict[str, Any]]:
    """Match each original-query concept once across caller-supplied text fields.

    Expansions are intentionally excluded from the importance gate. Use their
    separate origin/provenance if a later experiment gives them lower authority.
    Mapping inputs use title/body only; identifiers and hashes never count as
    evidence. Pass a plain string to match a different caller-selected text field.
    """
    prepared = validate_prepared(prepared)
    if isinstance(document, str):
        fields = {"body": document}
    elif isinstance(document, Mapping):
        fields = {key: value for key, value in document.items()
                  if key in {"title", "body"} and isinstance(value, str)}
    else:
        raise SchemaInvalidError("Document must be text or an object with text fields")
    results = []
    for concept in prepared["concepts"]:
        aliases = [concept["text"]] + [term for terms in concept.get("aliases", {}).values() for term in terms]
        spans = {}
        for field, text in fields.items():
            for alias in set(aliases):
                for span in find_term_spans(text, alias):
                    spans[(field, span["start"], span["end"])] = {"field": field, **span}
        ordered = [spans[key] for key in sorted(spans)]
        results.append({"concept_id": concept["concept_id"], "match": int(bool(ordered)), "spans": ordered})
    return results
