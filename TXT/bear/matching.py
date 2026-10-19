"""Protected biomedical span matcher, concept extraction, and deterministic boundary rules."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .contracts import SchemaInvalidError, validate_doc_id, validate_query_id


def normalize_text(text: str, preserve_case: bool = False) -> str:
    """Normalize text using Unicode NFC and collapsed whitespace.
    
    Preserves Vietnamese accents. Does not drop hyphens or punctuation.
    """
    if not text:
        return ""
    # 1. Unicode NFC composition
    nfc = unicodedata.normalize("NFC", text)
    # 2. Collapse whitespace (newlines, tabs, multiple spaces -> single space)
    cleaned = re.sub(r"\s+", " ", nfc).strip()
    if not preserve_case:
        cleaned = cleaned.lower()
    return cleaned


def is_han_character(ch: str) -> bool:
    """Check if character is a CJK ideograph."""
    code = ord(ch)
    return (
        (0x4E00 <= code <= 0x9FFF) or
        (0x3400 <= code <= 0x4DBF) or
        (0x20000 <= code <= 0x2A6DF)
    )


def build_protected_pattern(phrase: str) -> re.Pattern[str]:
    """Compile regex with strict boundaries around protected atoms (digits, units, identifiers).
    
    Guarantees per PLAN.md §8.3:
    - '5 mg' will NOT match '0,5 mg', '15 mg', or '0.5 mg' (negative lookbehind on digits/decimal separators).
    - 'BRCA1' will NOT match 'BRCA10' or 'BRCA2' (negative lookahead/behind on alphanumeric).
    - 'type 1' will NOT match 'type 2'.
    - 'PD-1' will NOT match 'PD-L1'.
    - Han character phrases match without Latin word boundaries.
    """
    norm_phrase = normalize_text(phrase, preserve_case=False)
    if not norm_phrase:
        raise SchemaInvalidError("Cannot build matcher pattern for empty phrase")

    # Escape literal regex characters
    escaped = re.escape(norm_phrase)
    
    first_char = norm_phrase[0]
    last_char = norm_phrase[-1]

    # Boundary checks:
    # If starting with digit: must not be preceded by digits or decimal commas/dots
    if is_han_character(first_char):
        prefix_boundary = ""
    elif first_char.isdigit():
        prefix_boundary = r"(?<![0-9,\.])"
    elif first_char.isalnum():
        prefix_boundary = r"(?<![A-Za-z0-9_])"
    elif is_han_character(first_char):
        prefix_boundary = ""
    else:
        prefix_boundary = ""

    # If ending with digit: must not be followed by digits or decimal commas/dots
    if is_han_character(last_char):
        suffix_boundary = ""
    elif last_char.isdigit():
        suffix_boundary = r"(?![A-Za-z0-9_]|[,.][0-9])"
    elif last_char.isalnum():
        suffix_boundary = r"(?![A-Za-z0-9_])"
    elif is_han_character(last_char):
        suffix_boundary = ""
    else:
        suffix_boundary = ""

    pattern_str = f"{prefix_boundary}{escaped}{suffix_boundary}"
    return re.compile(pattern_str, flags=re.UNICODE | re.IGNORECASE)


@dataclass(frozen=True)
class ConceptRecord:
    """Canonical query concept with verification provenance."""
    query_id: int
    concept_id: str
    original_vi: str
    normalized_vi: str
    source_entity_indices: list[int]
    vi_span_status: str  # verified_in_query | not_in_query
    views: dict[str, str] = field(default_factory=dict)
    verified_aliases: list[str] = field(default_factory=list)
    critical: bool = False

    def __post_init__(self) -> None:
        validate_query_id(self.query_id)


@dataclass(frozen=True)
class MatchExplanation:
    """Result of matching a concept against text."""
    concept_id: str
    matched: bool
    match_type: str | None = None  # exact | alias | None
    matched_phrase: str | None = None


def build_query_concepts(
    query_id: int,
    query_text: str,
    raw_entities: Sequence[Mapping[str, Any]],
) -> list[ConceptRecord]:
    """Extract and deduplicate concepts from raw query entities with NFC normalization.
    
    Rejects hallucinated entities (not present in query_text) from active denominator.
    """
    validate_query_id(query_id)
    norm_query = normalize_text(query_text)

    concepts_by_key: dict[str, list[tuple[int, Mapping[str, Any]]]] = {}
    for idx, ent in enumerate(raw_entities):
        vi_raw = str(ent.get("vi") or ent.get("text") or "").strip()
        if not vi_raw:
            continue
        norm_vi = normalize_text(vi_raw)
        if not norm_vi:
            continue
        if norm_vi not in concepts_by_key:
            concepts_by_key[norm_vi] = []
        concepts_by_key[norm_vi].append((idx, ent))

    # Sort keys for deterministic concept IDs
    sorted_keys = sorted(concepts_by_key.keys())
    result: list[ConceptRecord] = []

    for norm_vi in sorted_keys:
        entries = concepts_by_key[norm_vi]
        indices = [idx for idx, _ in entries]
        from .io import canonical_json_dumps
        # Chọn deterministic khi nhiều entity cùng span có bản dịch khác nhau.
        primary_ent = min((entry for _, entry in entries), key=canonical_json_dumps)

        orig_vi = str(primary_ent.get("vi") or primary_ent.get("text") or "").strip()
        views: dict[str, str] = {"vi": orig_vi}
        if "en" in primary_ent and primary_ent["en"]:
            views["en"] = str(primary_ent["en"])
        if "zh" in primary_ent and primary_ent["zh"]:
            views["zh"] = str(primary_ent["zh"])

        # Check if span is actually present in normalized query
        # Use word/atom boundary search
        try:
            pattern = build_protected_pattern(norm_vi)
            in_query = bool(pattern.search(norm_query))
        except Exception:
            in_query = norm_vi in norm_query

        vi_span_status = "verified_in_query" if in_query else "not_in_query"
        
        # Concept ID: q<qid>:<sha256(norm_vi)[:16]>
        cid = f"q{query_id}:{hashlib.sha256(norm_vi.encode('utf-8')).hexdigest()[:16]}"

        result.append(ConceptRecord(
            query_id=query_id,
            concept_id=cid,
            original_vi=orig_vi,
            normalized_vi=norm_vi,
            source_entity_indices=indices,
            vi_span_status=vi_span_status,
            views=views,
            verified_aliases=[a["text"] for a in primary_ent.get("verified_aliases", [])
                              if isinstance(a, dict) and a.get("reviewer") and a.get("source")
                              and a.get("version") and isinstance(a.get("text"), str)],
            critical=primary_ent.get("critical") is True and bool(primary_ent.get("critical_source")),
        ))

    return result


def compute_concept_set_hash(concepts: Sequence[ConceptRecord]) -> str:
    """Compute canonical hash of an active concept set invariant to input order."""
    # Filter active verified concepts and sort deterministically
    active = sorted(
        [c for c in concepts if c.vi_span_status == "verified_in_query"],
        key=lambda c: c.normalized_vi,
    )
    from .io import canonical_sha256
    return canonical_sha256({"matcher_version": "nfc_lower_space_protected_v2", "concepts": [
        {"id": c.concept_id, "text": c.normalized_vi, "views": c.views,
         "aliases": sorted(c.verified_aliases), "critical": c.critical} for c in active]})


def match_concept_in_text(
    concept: ConceptRecord,
    text: str,
    enable_aliases: bool = False,
) -> MatchExplanation:
    """Match a concept against text using strict protected patterns.
    
    Guarantees:
    - Multiple aliases match at most once.
    - Exact match has priority over alias.
    """
    if not text:
        return MatchExplanation(concept_id=concept.concept_id, matched=False)

    norm_target = normalize_text(text)
    
    # 1. Exact match on normalized VI span
    pattern = build_protected_pattern(concept.normalized_vi)
    if pattern.search(norm_target):
        return MatchExplanation(
            concept_id=concept.concept_id,
            matched=True,
            match_type="exact",
            matched_phrase=concept.normalized_vi,
        )

    # 2. Verified aliases match if enabled
    if enable_aliases and concept.verified_aliases:
        for alias in concept.verified_aliases:
            norm_alias = normalize_text(alias)
            if not norm_alias:
                continue
            alias_pat = build_protected_pattern(norm_alias)
            if alias_pat.search(norm_target):
                return MatchExplanation(
                    concept_id=concept.concept_id,
                    matched=True,
                    match_type="alias",
                    matched_phrase=norm_alias,
                )

    return MatchExplanation(concept_id=concept.concept_id, matched=False)
