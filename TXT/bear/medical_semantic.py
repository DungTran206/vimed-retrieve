"""Resumable SapBERT similarities between query concepts and literal document terms.

This stage adds independent semantic evidence. It never edits lexical concept
matches, uses labels, retrieves extra documents, or assigns relevance targets.
The transformer backend is optional and imported only when vectors are absent.
"""
from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Any, Mapping

from .contracts import HashMismatchError, SchemaInvalidError, validate_doc_id
from .corpus_index import CorpusIndex
from .io import (assert_valid_output_path, atomic_write_json, canonical_sha256,
                 read_json, read_jsonl, resolve_repo_path, sha256_file, write_jsonl)
from .medical_cache import iter_checked_records
from .medical_documents import ASSERTIONS
from .medical_query import KINDS

DEFAULT_MODEL = "cambridgeltl/SapBERT-UMLS-2020AB-all-lang-from-XLMR"
SEMANTIC_VERSION = "sapbert_literal_terms_v1"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_encoder_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Require immutable weights and the CLS/L2 recipe, without loading a model."""
    if not isinstance(config, Mapping):
        raise SchemaInvalidError("encoder must be an object")
    allowed = {"model", "revision", "local_path", "pooling", "l2_normalize", "max_length",
               "batch_size", "local_files_only", "overflow", "device"}
    if set(config) - allowed:
        raise SchemaInvalidError(f"Unknown encoder keys: {sorted(set(config) - allowed)}")
    result = {"model": DEFAULT_MODEL, "revision": None, "local_path": None,
              "pooling": "cls", "l2_normalize": True, "max_length": 64,
              "batch_size": 64, "local_files_only": True, "overflow": "error", "device": "cpu"}
    result.update(config)
    if not isinstance(result["model"], str) or not result["model"].strip():
        raise SchemaInvalidError("encoder.model must be nonempty")
    if result["pooling"] != "cls" or result["l2_normalize"] is not True:
        raise SchemaInvalidError("SapBERT requires CLS before pooler and l2_normalize=true")
    for name in ("max_length", "batch_size"):
        if type(result[name]) is not int or result[name] <= 0:
            raise SchemaInvalidError(f"encoder.{name} must be a positive integer")
    if result["max_length"] < 3:
        raise SchemaInvalidError("encoder.max_length must allow content and special tokens")
    if type(result["local_files_only"]) is not bool:
        raise SchemaInvalidError("encoder.local_files_only must be a boolean")
    if result["overflow"] not in {"error", "truncate"}:
        raise SchemaInvalidError("encoder.overflow must be error or truncate")
    if not isinstance(result["device"], str) or not result["device"].strip():
        raise SchemaInvalidError("encoder.device must be nonempty")
    revision = result["revision"]
    if revision is not None and (not isinstance(revision, str) or re.fullmatch(r"[a-fA-F0-9]{40}", revision) is None):
        raise SchemaInvalidError("encoder.revision must be an immutable 40-character commit SHA")
    if result["local_path"] is None:
        if revision is None:
            raise SchemaInvalidError("Set an immutable encoder.revision or an explicit local_path snapshot")
    else:
        if not isinstance(result["local_path"], (str, Path)) or not str(result["local_path"]).strip():
            raise SchemaInvalidError("encoder.local_path must be a nonempty snapshot path")
        local = resolve_repo_path(result["local_path"])
        result["local_path"] = str(local)
    return result


def _encoder_identity(encoder: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(encoder)
    if encoder["local_path"]:
        local = Path(encoder["local_path"])
        if not local.is_dir():
            raise FileNotFoundError(f"Encoder local snapshot is absent: {local}")
        files = {str(path.relative_to(local)).replace("\\", "/"): sha256_file(path)
                 for path in sorted(local.rglob("*")) if path.is_file()}
        if not files:
            raise SchemaInvalidError("Encoder local snapshot is empty")
        result["local_snapshot_sha256"] = canonical_sha256(files)
    return result


def _vector(value: Any, dimension: int | None = None) -> list[float]:
    if not isinstance(value, list) or not value:
        raise SchemaInvalidError("Embedding must be a nonempty list")
    if any(type(item) not in (int, float) or not math.isfinite(item) for item in value):
        raise SchemaInvalidError("Embedding values must be finite numbers")
    if dimension is not None and len(value) != dimension:
        raise SchemaInvalidError("Embedding dimension mismatch")
    # Scale first so valid large finite values cannot overflow the norm.
    scale = max(abs(item) for item in value)
    if scale == 0:
        raise SchemaInvalidError("Zero embedding is not allowed")
    scaled = [item / scale for item in value]
    norm = math.sqrt(sum(item * item for item in scaled))
    return [item / norm for item in scaled]


def _token_metadata(row: Mapping[str, Any], encoder: Mapping[str, Any]) -> dict[str, Any]:
    count, truncated = row.get("token_count"), row.get("truncated")
    if type(count) is not int or count <= 0 or type(truncated) is not bool:
        raise SchemaInvalidError("Precomputed embeddings need positive token_count and boolean truncated metadata")
    expected = count > encoder["max_length"]
    if truncated != expected:
        raise SchemaInvalidError("Embedding truncation metadata disagrees with token_count/max_length")
    if truncated and encoder["overflow"] == "error":
        raise SchemaInvalidError("Embedding text exceeds max_length; explicitly choose encoder.overflow=truncate")
    return {"token_count": count, "truncated": truncated}


class _TransformerEncoder:
    """Lazy optional backend: the CLS hidden state, before the pooler."""

    def __init__(self, config: Mapping[str, Any]):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.config = config
        location = config["local_path"] or config["model"]
        options = {"local_files_only": config["local_files_only"]}
        if not config["local_path"]:
            options["revision"] = config["revision"]
        self.tokenizer = AutoTokenizer.from_pretrained(location, **options)
        self.model = AutoModel.from_pretrained(location, **options).to(config["device"])
        self.model.eval()
        self.calls = 0

    def encode(self, texts: list[str]) -> list[dict[str, Any]]:
        lengths = self.tokenizer(texts, truncation=False, padding=False, add_special_tokens=True)["input_ids"]
        metadata = [{"token_count": len(tokens), "truncated": len(tokens) > self.config["max_length"]}
                    for tokens in lengths]
        if self.config["overflow"] == "error" and any(item["truncated"] for item in metadata):
            raise SchemaInvalidError("SapBERT text exceeds max_length; increase budget or explicitly choose overflow=truncate")
        inputs = self.tokenizer(texts, padding=True, truncation=True,
                                max_length=self.config["max_length"], return_tensors="pt")
        inputs = {key: value.to(self.config["device"]) for key, value in inputs.items()}
        with self.torch.inference_mode():
            vectors = self.model(**inputs).last_hidden_state[:, 0, :].detach().cpu().tolist()
        self.calls += 1
        return [{"embedding": vector, **item} for vector, item in zip(vectors, metadata)]


class _Vectors:
    def __init__(self, root: Path, encoder: Mapping[str, Any], encoder_identity: Mapping[str, Any], supplied):
        self.root, self.encoder = root, encoder
        self.recipe_hash = canonical_sha256(encoder_identity)
        self.supplied = None if supplied is None else {}
        self.dimension = None
        self.paths: set[Path] = set()
        self.backend = None
        self.new_vectors = 0
        self.reused_vectors = 0
        if supplied is not None:
            recipes = {}
            for row in read_jsonl(supplied):
                text = row.get("text")
                if not isinstance(text, str) or not text.strip() or text in self.supplied:
                    raise SchemaInvalidError("Precomputed embeddings require unique nonempty literal text")
                raw_encoder = row.get("encoder")
                key = canonical_sha256(raw_encoder)
                if key not in recipes:
                    recipes[key] = validate_encoder_config(raw_encoder)
                if recipes[key] != encoder:
                    raise HashMismatchError("Precomputed embedding encoder recipe differs from requested encoder")
                provenance = row.get("provenance")
                if not isinstance(provenance, dict) or not provenance:
                    raise SchemaInvalidError("Precomputed embeddings require explicit nonempty provenance")
                vector = _vector(row.get("embedding"), self.dimension)
                self.dimension = len(vector)
                self.supplied[text] = {"embedding": vector, "provenance": provenance,
                                       **_token_metadata(row, encoder)}

    def get_many(self, texts: set[str]) -> dict[str, dict[str, Any]]:
        result, missing = {}, []
        for text in sorted(texts):
            path = self.root / "embeddings" / f"{_sha(text)}.json"
            if path.exists():
                payload = read_json(path)
                digest = payload.pop("sha256", None)
                if digest != canonical_sha256(payload) or payload.get("text") != text or payload.get("encoder_sha256") != self.recipe_hash:
                    raise HashMismatchError("Cached text embedding identity/content changed")
                if not isinstance(payload.get("provenance"), dict) or not payload["provenance"]:
                    raise SchemaInvalidError("Cached embeddings require nonempty provenance")
                vector = _vector(payload["embedding"], self.dimension)
                if not math.isclose(math.sqrt(sum(value * value for value in payload["embedding"])), 1.0, abs_tol=1e-6):
                    raise SchemaInvalidError("Cached embedding is not L2 normalized")
                self.dimension = len(vector)
                _token_metadata(payload, self.encoder)
                payload["embedding"] = vector
                result[text] = payload
                self.paths.add(path)
                self.reused_vectors += 1
            else:
                missing.append(text)
        for offset in range(0, len(missing), self.encoder["batch_size"]):
            batch = missing[offset:offset + self.encoder["batch_size"]]
            if self.supplied is not None:
                absent = [text for text in batch if text not in self.supplied]
                if absent:
                    raise SchemaInvalidError(f"Precomputed embedding missing for literal text: {absent[0]!r}")
                rows = [self.supplied[text] for text in batch]
            else:
                if self.backend is None:
                    self.backend = _TransformerEncoder(self.encoder)
                rows = self.backend.encode(batch)
            if len(rows) != len(batch):
                raise SchemaInvalidError("Encoder returned an incorrect number of vectors")
            for text, row in zip(batch, rows):
                vector = _vector(row["embedding"], self.dimension)
                self.dimension = len(vector)
                payload = {"text": text, "encoder_sha256": self.recipe_hash, "embedding": vector,
                           "provenance": row.get("provenance", {"method": "transformers_cls_before_pooler"}),
                           **_token_metadata(row, self.encoder)}
                payload["sha256"] = canonical_sha256(payload)
                path = atomic_write_json(self.root / "embeddings" / f"{_sha(text)}.json", payload)
                self.paths.add(path)
                self.new_vectors += 1
                result[text] = payload
        return result


def _document_terms(path: Path, index: CorpusIndex) -> dict[str, dict[str, Any]]:
    documents = {}
    for row in iter_checked_records(path):
        did = validate_doc_id(row.get("doc_id"))
        if did in documents:
            raise SchemaInvalidError(f"Duplicate document extraction: {did}")
        document = index.get_document(did)
        if document is None:
            raise SchemaInvalidError(f"Extraction document absent from corpus snapshot: {did}")
        if row.get("lang") != document["lang"]:
            raise HashMismatchError(f"Extraction language differs from corpus: {did}")
        for field in ("title", "body"):
            if row.get(field + "_sha256") != _sha(document[field]):
                raise HashMismatchError(f"Extraction {field} hash differs from corpus: {did}")
        if type(row.get("truncated")) is not bool or not isinstance(row.get("windows"), list):
            raise SchemaInvalidError("Document extraction requires explicit truncated/windows metadata")
        windows = {}
        for window in row["windows"]:
            field, start, end = window.get("field"), window.get("start"), window.get("end")
            if (field not in {"body", "title"} or field in windows or type(start) is not int
                    or type(end) is not int or not 0 <= start < end <= len(document[field])
                    or window.get("original_length") != len(document[field])):
                raise SchemaInvalidError("Extraction window does not match original corpus field")
            windows[field] = window
        observed = sum(window["end"] - window["start"] for window in windows.values())
        whole = len(document["title"]) + len(document["body"])
        if (observed < whole) != row["truncated"]:
            raise SchemaInvalidError("Extraction truncated metadata disagrees with observed windows")
        if not isinstance(row.get("terms"), list):
            raise SchemaInvalidError("Document extraction terms must be a list")
        unique, occurrences = {}, set()
        for term in row["terms"]:
            if not isinstance(term, dict):
                raise SchemaInvalidError("Document extraction term must be an object")
            text, field = term.get("text"), term.get("field")
            anchor = term.get("anchor", {})
            if not isinstance(anchor, dict):
                raise SchemaInvalidError("Document term anchor must be an object")
            start, end = anchor.get("start"), anchor.get("end")
            if (not isinstance(text, str) or not text.strip() or field not in windows
                    or type(start) is not int or type(end) is not int
                    or not windows[field]["start"] <= start < end <= windows[field]["end"]
                    or document[field][start:end] != text):
                raise SchemaInvalidError("Document term span is not literal in the extraction window")
            if term.get("kind") not in KINDS - {"intent"} or term.get("assertion") not in ASSERTIONS:
                raise SchemaInvalidError("Invalid document term kind/assertion")
            occurrence = (field, start, end)
            if occurrence in occurrences:
                raise SchemaInvalidError("Duplicate document term anchor")
            occurrences.add(occurrence)
            key = (text, field, term["kind"], term["assertion"])
            if key not in unique:
                unique[key] = {"text": text, "field": field, "anchor": {"start": start, "end": end},
                               "kind": term["kind"], "assertion": term["assertion"], "anchors": []}
            unique[key]["anchors"].append({"start": start, "end": end})
        documents[did] = {**row, "terms": list(unique.values())}
    return documents


def _concepts(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    result, seen = [], set()
    for concept in row.get("concepts", []):
        if concept.get("origin") != "query":
            continue
        identity, text = concept.get("concept_id"), concept.get("text")
        if not isinstance(identity, str) or not identity or identity in seen:
            raise SchemaInvalidError("Original query concept IDs must be nonempty and unique")
        seen.add(identity)
        if not isinstance(text, str) or not text.strip():
            raise SchemaInvalidError("Original query concept requires literal nonempty text")
        if concept.get("kind") != "intent":
            result.append(concept)
    return result


def _validate_base(path: Path, index: CorpusIndex, index_sha256: str) -> None:
    """Check the complete input before a later bad record can waste encoding."""
    ids = set()
    for row in iter_checked_records(path):
        qid = row.get("id")
        if type(qid) is not int or qid < 0 or qid in ids:
            raise SchemaInvalidError("Base cache query IDs must be unique nonnegative integers")
        ids.add(qid)
        if "index_sha256" in row and row["index_sha256"] != index_sha256:
            raise HashMismatchError("Base cache index fingerprint differs from semantic corpus snapshot")
        _concepts(row)
        seen_docs = set()
        for candidate in row.get("candidates", []):
            if candidate.get("scores", {}).get("sapbert") is not None:
                raise SchemaInvalidError("Base cache already has scores.sapbert; use imported scores or semantic matrices, not both")
            did = validate_doc_id(candidate.get("doc_id"))
            if did in seen_docs:
                raise SchemaInvalidError("Duplicate base cache candidate")
            seen_docs.add(did)
            document = index.get_document(did)
            if document is None:
                raise SchemaInvalidError(f"Candidate absent from corpus snapshot: {did}")
            if candidate.get("body_sha256") != document["body_sha256"]:
                raise HashMismatchError(f"Candidate body hash differs from corpus: {did}")
            if "title_sha256" in candidate and candidate["title_sha256"] != _sha(document["title"]):
                raise HashMismatchError(f"Candidate title hash differs from corpus: {did}")
            if candidate.get("lang") != document["lang"]:
                raise HashMismatchError(f"Candidate language differs from corpus: {did}")


def build_semantic_cache(config: Mapping[str, Any], root: Path) -> tuple[list[Path], dict[str, Any]]:
    """Add raw cosine matrices to a checked base cache, preserving lexical gates.

    Precomputed JSONL rows require ``text, embedding, encoder, provenance,
    token_count, truncated``. ``encoder`` uses the same public config as this
    stage; token_count is the full untruncated length including special tokens.
    Missing document extraction is explicit unavailable evidence, never zero.
    """
    root = assert_valid_output_path(root)
    encoder = validate_encoder_config(config.get("encoder", {}))
    encoder_identity = _encoder_identity(encoder)
    inputs = {name: {"path": str(resolve_repo_path(config[name])),
                     "sha256": sha256_file(resolve_repo_path(config[name]))}
              for name in ("cache", "index", "document_terms", "embeddings_input") if config.get(name)}
    recipe = {"version": SEMANTIC_VERSION, "encoder": encoder_identity, "inputs": inputs,
              "candidate_scope": "base_cache_only", "lexical_gate_modified": False}
    recipe_path = root / "semantic_recipe.json"
    if recipe_path.exists() and read_json(recipe_path) != recipe:
        raise HashMismatchError("Semantic recipe changed; use a fresh output_dir")
    atomic_write_json(recipe_path, recipe)
    vectors = _Vectors(root, encoder, encoder_identity, resolve_repo_path(config.get("embeddings_input")))
    paths, ids = [], set()
    counts = {"query_count": 0, "candidate_count": 0, "semantic_available_count": 0,
              "missing_document_terms_count": 0, "truncated_extraction_count": 0,
              "reused_queries": 0}
    with CorpusIndex(resolve_repo_path(config["index"])) as index:
        documents = _document_terms(resolve_repo_path(config["document_terms"]), index)
        _validate_base(resolve_repo_path(config["cache"]), index, inputs["index"]["sha256"])
        for row in iter_checked_records(config["cache"]):
            qid = row.get("id")
            if type(qid) is not int or qid in ids:
                raise SchemaInvalidError("Base cache query IDs must be unique integers")
            ids.add(qid)
            concepts = _concepts(row)
            path = root / "queries" / f"{qid}.json"
            row_identity = canonical_sha256(row)
            counts["query_count"] += 1
            if path.exists():
                cached = read_json(path)
                if cached.get("sapbert_recipe") != recipe or cached.get("sapbert_input_sha256") != row_identity:
                    raise HashMismatchError("Cached semantic query identity changed")
                integrity = cached.pop("sapbert_output_sha256", None)
                if integrity != canonical_sha256(cached):
                    raise HashMismatchError("Cached semantic query content changed")
                cached["sapbert_output_sha256"] = integrity
                # A partial resume must still verify every vector used by this query.
                referenced = set(cached.get("sapbert_embeddings", {}))
                if any(not (root / "embeddings" / f"{_sha(text)}.json").is_file() for text in referenced):
                    raise HashMismatchError("A vector referenced by the resumed semantic query is missing")
                vectors.get_many(referenced)
                counts["reused_queries"] += 1
            else:
                if "sapbert_recipe" in row:
                    raise SchemaInvalidError("Supply a base cache without preexisting SapBERT evidence")
                candidates, texts = [], set()
                for candidate in row.get("candidates", []):
                    did = validate_doc_id(candidate.get("doc_id"))
                    terms = documents.get(did, {}).get("terms", [])
                    if terms and concepts:
                        texts.update(concept["text"] for concept in concepts)
                        texts.update(term["text"] for term in terms)
                    candidates.append((candidate, terms))
                embeddings = vectors.get_many(texts)
                annotated = []
                for candidate, terms in candidates:
                    did = candidate["doc_id"]
                    matrix = []
                    if terms and concepts:
                        for concept in concepts:
                            source = embeddings[concept["text"]]["embedding"]
                            similarities = [{**term, "cosine": max(-1.0, min(1.0, sum(a * b for a, b in zip(
                                source, embeddings[term["text"]]["embedding"]))))} for term in terms]
                            matrix.append({"concept_id": concept["concept_id"], "similarities": similarities})
                    extraction = documents.get(did)
                    evidence = ({key: extraction[key] for key in ("truncated", "windows", "body_sha256", "title_sha256")}
                                if extraction else None)
                    annotated.append({**candidate, "sapbert_matches": matrix,
                                      "score_available": {**candidate.get("score_available", {}), "sapbert": bool(matrix)},
                                      "sapbert_extraction": evidence,
                                      "sapbert_unavailable_reason": (None if matrix else "missing_document_terms" if extraction is None
                                                                     else "no_eligible_query_concepts" if not concepts else "empty_extracted_terms")})
                cached = {**row, "candidates": annotated, "sapbert_recipe": recipe,
                          "sapbert_input_sha256": row_identity,
                          "sapbert_embeddings": {text: {"token_count": item["token_count"], "truncated": item["truncated"]}
                                                 for text, item in embeddings.items()}}
                cached["sapbert_output_sha256"] = canonical_sha256(cached)
                atomic_write_json(path, cached)
            counts["candidate_count"] += len(cached["candidates"])
            counts["semantic_available_count"] += sum(bool(candidate["sapbert_matches"]) for candidate in cached["candidates"])
            counts["missing_document_terms_count"] += sum(candidate["sapbert_extraction"] is None for candidate in cached["candidates"])
            counts["truncated_extraction_count"] += sum(bool(candidate.get("sapbert_extraction", {}).get("truncated"))
                                                       for candidate in cached["candidates"] if candidate.get("sapbert_extraction"))
            paths.append(path)
    output = write_jsonl(root / "cache.jsonl", (read_json(path) for path in paths))
    # Include all persisted vectors even when a resumed query bypassed get_many.
    vector_paths = sorted((root / "embeddings").glob("*.json"))
    details = {**counts, "encoder": encoder_identity, "embedding_dimension": vectors.dimension,
               "new_text_embeddings": vectors.new_vectors, "reused_text_embeddings": vectors.reused_vectors,
               "encoder_batches": vectors.backend.calls if vectors.backend else 0,
               "model_contacted": vectors.backend is not None, "lexical_gate_modified": False,
               "candidate_scope": "base_cache_only", "score_absence_is_not_zero": True,
               "quality_gain_established": False}
    return [output, recipe_path, *paths, *vector_paths], details
