"""Auditable phrase evidence for the two BEAR replacement experiments.

This is an exact, conservative matcher, not a semantic relation extractor. Raw
queries receive lexical/entity evidence. Relation evidence is available only
when callers provide subject/predicate/object phrases anchored in the query.
Every document span uses Python character offsets in the original body.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any


EVIDENCE_VERSION = "anchored_phrase_local_negation_v1"
_NEGATIONS = ("not", "no", "never", "neither", "without", "cannot", "can't", "doesn't",
              "don't", "didn't", "isn't", "aren't", "wasn't", "weren't", "won't",
              "không", "chẳng", "chưa", "chả")
_CLAUSE = re.compile(r"[,;:]|\b(?:and|or|but|whereas|however|although|và|hoặc|nhưng|còn|tuy nhiên)\b", re.UNICODE)


@dataclass(frozen=True)
class _Text:
    raw: str
    normalized: str
    offsets: tuple[tuple[int, int], ...]

    def span(self, start: int, end: int, base: int = 0) -> dict[str, Any]:
        lo, hi = self.offsets[start][0], self.offsets[end - 1][1]
        return {"start": lo + base, "end": hi + base, "text": self.raw[lo:hi]}


def _hangul_join(cluster: str, char: str) -> bool:
    current = unicodedata.normalize("NFC", cluster)
    if len(current) != 1:
        return False
    left, right = ord(current), ord(char)
    return ((0x1100 <= left <= 0x1112 and 0x1161 <= right <= 0x1175)
            or (0xAC00 <= left <= 0xD7A3 and (left - 0xAC00) % 28 == 0
                and 0x11A8 <= right <= 0x11C2))


def _text(raw: str) -> _Text:
    """NFC/lower/whitespace normalization with a map back to original text."""
    parts: list[str] = []
    positions: list[tuple[int, int]] = []
    i = 0
    while i < len(raw):
        j = i + 1
        while j < len(raw) and (unicodedata.combining(raw[j]) or _hangul_join(raw[i:j], raw[j])):
            j += 1
        part = unicodedata.normalize("NFC", raw[i:j])
        parts.append(part)
        positions.extend([(i, j)] * len(part))
        i = j
    composed = "".join(parts)
    lowered = composed.lower()
    lower_positions = [pos for char, pos in zip(composed, positions) for _ in char.lower()]
    out: list[str] = []
    mapped: list[tuple[int, int]] = []
    for char, pos in zip(lowered, lower_positions):
        if char.isspace():
            if out and out[-1] == " ":
                mapped[-1] = (mapped[-1][0], pos[1])
            elif out:
                out.append(" ")
                mapped.append(pos)
        else:
            out.append(char)
            mapped.append(pos)
    if out and out[-1] == " ":
        out.pop()
        mapped.pop()
    return _Text(raw, "".join(out), tuple(mapped))


def tokenize(text: str) -> list[str]:
    """Return exact NFC lowercase tokens, preserving accents, IDs and decimals."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    # A Unicode mark that cannot compose under NFC remains part of its token.
    # Python's re \w omits such marks, so scan Unicode categories explicitly.
    normalized = _text(text).normalized
    tokens, index = [], 0
    while index < len(normalized):
        if not _word(normalized[index]):
            index += 1
            continue
        start = index
        index += 1
        while index < len(normalized):
            char = normalized[index]
            if _word(char):
                index += 1
            elif (char in "-\u2010\u2011" and index + 1 < len(normalized)
                  and _word(normalized[index + 1])):
                index += 1
            elif (char in ".," and index + 1 < len(normalized)
                  and normalized[index - 1].isdigit() and normalized[index + 1].isdigit()):
                index += 1
            else:
                break
        tokens.append(normalized[start:index])
    return tokens


def query_text(query: str | Mapping[str, Any]) -> str:
    """Read the original query only; evaluation labels are never inspected."""
    if isinstance(query, str):
        return query
    if not isinstance(query, Mapping):
        raise TypeError("query must be a string or mapping")
    for key in ("query", "text", "query_text", "question", "vi"):
        value = query.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _word(char: str) -> bool:
    return bool(char) and (char.isalnum() or char == "_" or unicodedata.category(char).startswith("M"))


def _han(char: str) -> bool:
    return bool(char) and (0x3400 <= ord(char) <= 0x9FFF or 0x20000 <= ord(char) <= 0x2FA1F)


def _matches(phrase: str, view: _Text, low: int = 0, high: int | None = None) -> list[tuple[int, int]]:
    term = _text(phrase).normalized
    if not term:
        return []
    high = len(view.normalized) if high is None else high
    target, found = view.normalized, []
    pos = low
    while pos < high:
        start = target.find(term, pos, high)
        if start < 0:
            break
        end = start + len(term)
        before = target[start - 1] if start else ""
        after = target[end] if end < len(target) else ""
        left_ok = not (_word(term[0]) and not _han(term[0])
                       and (_word(before) or before in "-\u2010\u2011" and bool(before)))
        right_ok = not (_word(term[-1]) and not _han(term[-1])
                        and (_word(after) or after in "-\u2010\u2011" and bool(after)))
        if term[0].isdigit() and before in ".," and start > 1 and target[start - 2].isdigit():
            left_ok = False
        if term[-1].isdigit() and after in ".," and end + 1 < len(target) and target[end + 1].isdigit():
            right_ok = False
        if left_ok and right_ok:
            found.append((start, end))
        pos = start + 1
    return found


def _entities(query: str | Mapping[str, Any], original: _Text) -> tuple[list[dict], list[dict]]:
    supplied = query.get("entities", []) if isinstance(query, Mapping) else []
    if not isinstance(supplied, (list, tuple)):
        return [], [{"reason": "entities_must_be_a_list"}]
    accepted, rejected, seen = [], [], set()
    for index, item in enumerate(supplied):
        anchor = item if isinstance(item, str) else (item.get("vi") or item.get("text")) if isinstance(item, Mapping) else None
        if not isinstance(anchor, str) or not anchor.strip():
            rejected.append({"index": index, "reason": "missing_query_anchor"})
            continue
        anchors = _matches(anchor, original)
        if not anchors:
            rejected.append({"index": index, "anchor": anchor, "reason": "not_anchored_in_query"})
            continue
        key = _text(anchor).normalized
        if key in seen:
            continue
        seen.add(key)
        views = {"vi": anchor}
        if isinstance(item, Mapping):
            views.update({lang: item[lang] for lang in ("en", "zh")
                          if isinstance(item.get(lang), str) and item[lang].strip()})
        accepted.append({"anchor": anchor, "views": views,
                         "query_spans": [original.span(*span) for span in anchors]})
    return accepted, rejected


def query_terms(query: str | Mapping[str, Any]) -> list[str]:
    """Terms for corpus lookup, including only query-anchored entity mappings."""
    original = _text(query_text(query))
    entities, _ = _entities(query, original)
    terms = tokenize(original.raw)
    for entity in entities:
        for phrase in entity["views"].values():
            terms.extend(tokenize(phrase))
    return list(dict.fromkeys(terms))


def _sentences(view: _Text) -> list[tuple[int, int]]:
    ranges, start, target = [], 0, view.normalized
    for index, char in enumerate(target):
        raw_lo, raw_hi = view.offsets[index]
        newline = char == " " and any(c in view.raw[raw_lo:raw_hi] for c in "\r\n")
        decimal = char == "." and index > 0 and index + 1 < len(target) and target[index - 1].isdigit() and target[index + 1].isdigit()
        if newline or char in "!?。！？;" or char == "." and not decimal:
            if start < index:
                ranges.append((start, index))
            start = index + 1
    if start < len(target):
        ranges.append((start, len(target)))
    return ranges


def _negation(view: _Text, subject: tuple[int, int], predicate: tuple[int, int]) -> list[tuple[int, int]]:
    # Scope starts at the bound subject, ends with the bound predicate, and
    # cannot borrow a negation from an earlier sentence or another assertion.
    low, high = subject[1], predicate[1]
    gap = view.normalized[low:predicate[0]]
    conjunctions = list(re.finditer(r"\b(?:and|or|và|hoặc)\b", gap))
    if conjunctions:
        low += conjunctions[-1].end()
    spans = []
    for marker in _NEGATIONS:
        for span in _matches(marker, view, low, high):
            tail = view.normalized[span[1]:high].lstrip()
            if marker == "not" and tail.startswith("only") or marker == "không" and tail.startswith("chỉ"):
                continue
            spans.append(span)
    return sorted(set(spans))


def _bindings(view: _Text, subject: str, predicate: str, object_: str) -> list[dict]:
    found = []
    for low, high in _sentences(view):
        all_predicates = _matches(predicate, view, low, high)
        for subj in _matches(subject, view, low, high):
            for pred in all_predicates:
                if pred[0] < subj[1]:
                    continue
                for obj in _matches(object_, view, pred[1], high):
                    # Crossing an independent clause is not evidence of the
                    # supplied binding, even if all three words occur nearby.
                    between = view.normalized[subj[1]:pred[0]] + " " + view.normalized[pred[1]:obj[0]]
                    if _CLAUSE.search(between):
                        continue
                    if any(subj[1] <= other[0] < pred[0] or pred[1] <= other[0] < obj[0]
                           for other in all_predicates):
                        continue
                    negations = _negation(view, subj, pred)
                    found.append({"subject": subj, "predicate": pred, "object": obj,
                                  "sentence": (low, high), "negations": negations,
                                  "polarity": "negative" if negations else "positive"})
    return found


def _polarity(value: Any) -> str | None:
    if value is True:
        return "positive"
    if value is False:
        return "negative"
    if isinstance(value, str):
        value = value.lower().strip()
        if value in ("positive", "affirmed", "affirmative", "+"):
            return "positive"
        if value in ("negative", "negated", "-"):
            return "negative"
    return None


def _relations(query: str | Mapping[str, Any], original: _Text) -> tuple[list[dict], list[dict], bool]:
    supplied = query.get("relations", []) if isinstance(query, Mapping) else []
    if not isinstance(supplied, (list, tuple)):
        return [], [{"reason": "relations_must_be_a_list"}], True
    valid, invalid = [], []
    for index, item in enumerate(supplied):
        if not isinstance(item, Mapping) or any(not isinstance(item.get(role), str) or not item[role].strip()
                                                for role in ("subject", "predicate", "object")):
            invalid.append({"index": index, "status": "invalid", "reason": "roles_must_be_nonempty_phrases"})
            continue
        binding = _bindings(original, item["subject"], item["predicate"], item["object"])
        if not binding:
            invalid.append({"index": index, "status": "invalid", "reason": "roles_not_anchored_in_order_in_query_sentence"})
            continue
        polarity = _polarity(item["polarity"]) if "polarity" in item else binding[0]["polarity"]
        if polarity is None:
            invalid.append({"index": index, "status": "invalid", "reason": "invalid_polarity"})
            continue
        if not any(b["polarity"] == polarity for b in binding):
            invalid.append({"index": index, "status": "invalid", "reason": "polarity_disagrees_with_query_binding"})
            continue
        valid.append({"index": index, **{role: item[role] for role in ("subject", "predicate", "object")},
                      "polarity": polarity,
                      "query_binding": next(b for b in binding if b["polarity"] == polarity)})
    return valid, invalid, bool(supplied)


def _explain_binding(binding: dict, view: _Text, base: int = 0) -> dict:
    return {**{role: view.span(*binding[role], base) for role in ("subject", "predicate", "object", "sentence")},
            "polarity": binding["polarity"],
            "negation_spans": [view.span(*span, base) for span in binding["negations"]]}


def _analyse(original: _Text, entities: list[dict], relations: list[dict], body: str,
             language: str | None, base: int = 0) -> dict:
    view = _text(body)
    terms = list(dict.fromkeys(tokenize(original.raw)))
    term_hits = {term: _matches(term, view) for term in terms}
    lexical = sum(bool(hits) for hits in term_hits.values()) / len(terms) if terms else 0.0
    entity_results = []
    for entity in entities:
        # A mapped view is permitted only after its source anchor was verified.
        phrase = entity["views"].get(language, entity["anchor"])
        hits = _matches(phrase, view)
        entity_results.append({"anchor": entity["anchor"], "matched_phrase": phrase,
                               "query_spans": entity["query_spans"], "matched": bool(hits),
                               "spans": [view.span(*hit, base) for hit in hits]})
    entity_cov = sum(item["matched"] for item in entity_results) / len(entity_results) if entity_results else None
    results = []
    for relation in relations:
        bindings = _bindings(view, relation["subject"], relation["predicate"], relation["object"])
        supporting = [b for b in bindings if b["polarity"] == relation["polarity"]]
        conflicting = [b for b in bindings if b["polarity"] != relation["polarity"]]
        status = "mixed" if supporting and conflicting else "supported" if supporting else "conflict" if conflicting else "missing"
        results.append({"index": relation["index"], "subject": relation["subject"],
                        "predicate": relation["predicate"], "object": relation["object"],
                        "expected_polarity": relation["polarity"], "status": status,
                        "query_binding": _explain_binding(relation["query_binding"], original),
                        "supporting_bindings": [_explain_binding(b, view, base) for b in supporting],
                        "conflicting_bindings": [_explain_binding(b, view, base) for b in conflicting]})
    support = sum(bool(r["supporting_bindings"]) for r in results) / len(results) if results else 0.0
    conflict = sum(bool(r["conflicting_bindings"]) for r in results) / len(results) if results else 0.0
    effective_conflict = sum(bool(r["conflicting_bindings"]) and not r["supporting_bindings"]
                             for r in results) / len(results) if results else 0.0
    basic = lexical if entity_cov is None else 0.4 * lexical + 0.6 * entity_cov
    # A document may contain contrary statements in separate passages. Preserve
    # both explanations, while allowing its supporting passage to be retrieved.
    score = 0.5 * basic + 0.5 * support - 0.5 * effective_conflict if relations else basic
    return {"evidence_score": max(0.0, min(1.0, score)), "lexical_coverage": lexical,
            "entity_coverage": entity_cov, "entity_results": entity_results,
            "relation_support": support, "relation_conflict": conflict,
            "effective_relation_conflict": effective_conflict, "relation_results": results,
            "matched_terms": [term for term, hits in term_hits.items() if hits],
            "matched_spans": [{"term": term, **view.span(*span, base)}
                              for term, hits in term_hits.items() for span in hits]}


def score_evidence(query: str | Mapping[str, Any], document: str | Mapping[str, Any], refs: Sequence = ()) -> dict:
    """Score exact body evidence and return its original-text explanations.

    ``relations`` optionally contains ``subject``, ``predicate``, ``object`` and
    ``polarity`` (positive/negative). With no polarity, local query negation
    determines it. Missing/reversed/split bindings are missing, never conflict.
    ``entities`` accepts strings or mappings with query-anchored vi/text and
    optional en/zh views. No evaluation labels or relevance judgments are read.
    """
    if isinstance(document, str):
        body, language, doc_id = document, None, None
    elif isinstance(document, Mapping):
        body = document.get("body", document.get("text", ""))
        language = document.get("lang", document.get("language"))
        doc_id = document.get("doc_id", document.get("id"))
    else:
        raise TypeError("document must be a string or mapping")
    missing_text = body is None
    if missing_text:
        body = ""
    if not isinstance(body, str):
        raise TypeError("document body must be a string")
    original = _text(query_text(query))
    entities, invalid_entities = _entities(query, original)
    relations, invalid_relations, supplied_relations = _relations(query, original)
    result = _analyse(original, entities, relations, body, language)
    result.update({"evidence_version": EVIDENCE_VERSION,
                   "structured_status": "available" if relations else "invalid" if supplied_relations else "unavailable",
                   "structured_note": "exact ordered phrase bindings with local negation; no semantic parsing",
                   "invalid_entities": invalid_entities, "invalid_relations": invalid_relations,
                   "relation_count": len(relations), "entity_count": len(entities),
                   "evidence_status": "missing_text" if missing_text else "computed" if body else "empty_text",
                   "body_length": len(body), "chunk_features": [], "invalid_chunk_refs": [],
                   "best_evidence_chunk_ref": None})
    for index, ref in enumerate(refs):
        item = asdict(ref) if is_dataclass(ref) and not isinstance(ref, type) else dict(ref) if isinstance(ref, Mapping) else None
        if item is None:
            result["invalid_chunk_refs"].append({"index": index, "reason": "ref_must_be_a_mapping"})
            continue
        lo, hi = item.get("start"), item.get("end")
        valid_offsets = (isinstance(lo, int) and not isinstance(lo, bool) and isinstance(hi, int)
                         and not isinstance(hi, bool) and 0 <= lo < hi <= len(body))
        if not valid_offsets or doc_id is not None and str(item.get("doc_id")) != str(doc_id):
            result["invalid_chunk_refs"].append({"index": index, "reason": "invalid_offsets_or_document"})
            continue
        chunk = _analyse(original, entities, relations, body[lo:hi], language, lo)
        result["chunk_features"].append({"ref": item, **chunk})
    if result["chunk_features"]:
        best = min(result["chunk_features"], key=lambda c: (-c["evidence_score"], -c["relation_support"],
                   c["relation_conflict"], c["ref"]["start"], c["ref"]["end"], str(c["ref"].get("chunk_id_native", ""))))
        result["best_evidence_chunk_ref"] = best["ref"]
    return result
