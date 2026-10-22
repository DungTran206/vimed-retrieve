"""Validated, provenance-preserving disease-to-symptom data adapters.

No medical facts or concept identifiers are generated here. The optional CMeIE
adapter requires a separately reviewed concept map: entity mentions in a relation
extraction dataset are not, by themselves, a normalized medical knowledge base.
"""

from __future__ import annotations

import copy
import unicodedata
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import SchemaInvalidError
from .io import read_json, read_jsonl, resolve_repo_path, write_jsonl

LANGUAGES = ("vi", "zh", "en")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchemaInvalidError(f"{field} must be a nonempty string")
    return unicodedata.normalize("NFC", value.strip())


def validate_concept(value: Any, field: str = "concept") -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise SchemaInvalidError(f"{field} must be an object")
    concept_id = _text(value.get("concept_id"), f"{field}.concept_id")
    labels = value.get("labels")
    aliases = value.get("aliases", {})
    if not isinstance(labels, Mapping) or not labels or set(labels) - set(LANGUAGES):
        raise SchemaInvalidError(f"{field}.labels needs supported vi/zh/en labels")
    if not isinstance(aliases, Mapping) or set(aliases) - set(LANGUAGES):
        raise SchemaInvalidError(f"{field}.aliases supports vi, zh and en")
    clean_labels = {lang: _text(text, f"{field}.labels.{lang}") for lang, text in labels.items()}
    clean_aliases = {}
    for lang in LANGUAGES:
        terms = aliases.get(lang, [])
        if not isinstance(terms, list):
            raise SchemaInvalidError(f"{field}.aliases.{lang} must be a list")
        cleaned = [_text(term, f"{field}.aliases.{lang}") for term in terms]
        if len(set(term.casefold() for term in cleaned)) != len(cleaned):
            raise SchemaInvalidError(f"{field}.aliases.{lang} has duplicates")
        clean_aliases[lang] = cleaned
    return {"concept_id": concept_id, "labels": clean_labels, "aliases": clean_aliases}


def validate_kb(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Canonical rows: disease, symptom, has_symptom relation, source provenance."""
    clean_rows = []
    concepts: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise SchemaInvalidError(f"KB row {index} must be an object")
        disease = validate_concept(row.get("disease"), f"row[{index}].disease")
        symptom = validate_concept(row.get("symptom"), f"row[{index}].symptom")
        if disease["concept_id"] == symptom["concept_id"]:
            raise SchemaInvalidError(f"KB row {index}: disease and symptom IDs must differ")
        if row.get("relation") != "has_symptom":
            raise SchemaInvalidError(f"KB row {index}: relation must be has_symptom")
        source = row.get("source")
        if not isinstance(source, Mapping):
            raise SchemaInvalidError(f"KB row {index}: source provenance is required")
        source = copy.deepcopy(dict(source))
        for key in ("name", "record_id"):
            source[key] = _text(source.get(key), f"row[{index}].source.{key}")
        for concept in (disease, symptom):
            cid = concept["concept_id"]
            if cid in concepts and concepts[cid] != concept:
                raise SchemaInvalidError(f"Inconsistent labels/aliases for concept ID {cid}")
            concepts[cid] = concept
        result = {"disease": disease, "symptom": symptom,
                  "relation": "has_symptom", "source": source}
        for optional in ("context", "frequency", "provenance"):
            if optional in row:
                result[optional] = copy.deepcopy(row[optional])
        clean_rows.append(result)
    return clean_rows


def load_kb(path: str | Path) -> list[dict[str, Any]]:
    """Read canonical JSONL and reject unnormalized/unattributed records."""
    return validate_kb(list(read_jsonl(resolve_repo_path(path))))


def concept_terms(concept: Mapping[str, Any], lang: str | None = None) -> list[str]:
    languages = (lang,) if lang else LANGUAGES
    terms = []
    for language in languages:
        label = concept["labels"].get(language)
        if label:
            terms.append(label)
        terms.extend(concept["aliases"].get(language, []))
    return list(dict.fromkeys(terms))


def _import_cmeie(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Convert only explicitly configured symptom predicates + mapped concepts.

    concept_map_path is JSON list of canonical concepts with a kind field
    (disease|symptom). No IDs, translations, aliases or relation facts are inferred.
    Ambiguous mentions and unmapped symptom relations fail instead of being lost.
    """
    mapping = read_json(resolve_repo_path(config["concept_map_path"]))
    if not isinstance(mapping, list):
        raise SchemaInvalidError("CMeIE concept map must be a JSON list")
    by_mention: dict[tuple[str, str], dict[str, Any]] = {}
    for index, row in enumerate(mapping):
        concept = validate_concept(row, f"concept_map[{index}]")
        kind = row.get("kind")
        if kind not in ("disease", "symptom"):
            raise SchemaInvalidError("Concept map kind must be disease or symptom")
        for mention in concept_terms(concept, "zh"):
            key = (kind, mention.casefold())
            if key in by_mention and by_mention[key] != concept:
                raise SchemaInvalidError(f"Ambiguous CMeIE mention: {mention}")
            by_mention[key] = concept
    predicates = config.get("symptom_predicates", ["临床表现"])
    if not isinstance(predicates, list) or not predicates or not all(isinstance(v, str) for v in predicates):
        raise SchemaInvalidError("symptom_predicates must be a nonempty list")
    source = config.get("source", {})
    if not isinstance(source, Mapping) or not source.get("name"):
        raise SchemaInvalidError("CMeIE import requires source.name")
    rows = []
    for index, record in enumerate(read_jsonl(resolve_repo_path(config["source_path"]))):
        for spo_index, spo in enumerate(record.get("spo_list", [])):
            if spo.get("predicate") not in predicates:
                continue
            subject = _text(spo.get("subject"), "spo.subject")
            obj = spo.get("object")
            symptom_mention = obj.get("@value") if isinstance(obj, Mapping) else obj
            symptom_mention = _text(symptom_mention, "spo.object")
            try:
                disease = by_mention[("disease", subject.casefold())]
                symptom = by_mention[("symptom", symptom_mention.casefold())]
            except KeyError as exc:
                raise SchemaInvalidError(f"Unmapped CMeIE relation at row {index}, spo {spo_index}; review concept map") from exc
            source_record = dict(source)
            source_record["record_id"] = str(record.get("id", index)) + f":spo:{spo_index}"
            rows.append({"disease": disease, "symptom": symptom, "relation": "has_symptom",
                         "source": source_record,
                         "provenance": {"adapter": "cmeie", "predicate": spo["predicate"],
                                        "evidence_text": record.get("text", ""),
                                        "source_mentions": [subject, symptom_mention]}})
    return validate_kb(rows)


def import_kb(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Import canonical JSONL or CMeIE; optionally write under TXT only.

    Required: source_path, format (canonical|cmeie). CMeIE additionally requires
    concept_map_path and source.name. output_path is optional; inputs never mutate.
    An empty result is an error unless allow_empty=true is explicitly supplied.
    """
    kind = config.get("format", "canonical")
    if kind == "canonical":
        rows = load_kb(config["source_path"])
    elif kind == "cmeie":
        rows = _import_cmeie(config)
    else:
        raise SchemaInvalidError(f"Unknown medical KB format: {kind}")
    if not rows and not config.get("allow_empty", False):
        raise SchemaInvalidError("KB import produced no relations; check mapping and predicates")
    if config.get("output_path"):
        inputs = [resolve_repo_path(config["source_path"])]
        if config.get("concept_map_path"):
            inputs.append(resolve_repo_path(config["concept_map_path"]))
        write_jsonl(resolve_repo_path(config["output_path"]), rows, input_paths=inputs)
    return rows
