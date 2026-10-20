"""BEAR replacement for RRF: evidence ranking over a deduplicated source union."""
from collections.abc import Mapping

from .contracts import InputMissingError, SchemaInvalidError, validate_doc_id, validate_finite_number
from .retrieval import validate_budget


class BearFusion:
    """Rescore source candidates using the shared corpus evidence scorer.

    Source rank/score is provenance only, never a hidden RRF or tie-break feature.
    Unlike BearRetriever this component cannot introduce a doc outside the union.
    """
    stage = "bear_fusion"
    candidate_scope = "source_union"

    def __init__(self, index):
        self.index = index

    def fuse(self, query, sources, top_k=300, languages=None):
        validate_budget(top_k, languages)
        if not isinstance(sources, Mapping) or not sources:
            raise SchemaInvalidError("sources must be a nonempty mapping of names to ranked lists")
        provenance = {}
        for name, candidates in sources.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(candidates, (list, tuple)):
                raise SchemaInvalidError("Each source needs a nonempty name and an explicit candidate list")
            seen = set()
            for rank, item in enumerate(candidates, 1):
                if isinstance(item, Mapping):
                    doc_id = validate_doc_id(item.get("doc_id"))
                    score = validate_finite_number(item.get("score"), "source_score", allow_none=True)
                else:
                    doc_id, score = validate_doc_id(item), None
                if doc_id in seen:
                    raise SchemaInvalidError(f"Duplicate document {doc_id} in source {name}")
                seen.add(doc_id)
                provenance.setdefault(doc_id, {})[name] = {"rank": rank, "score": score}
        eligible = []
        for doc_id in sorted(provenance):
            doc = self.index.get_document(doc_id)
            if doc is None:
                raise InputMissingError(f"Source document absent from corpus index: {doc_id}")
            if languages is None or doc.get("lang") in languages:
                eligible.append(doc_id)
        rows = self.index.rank_documents(query, eligible, top_k=top_k)
        for row in rows:
            row["source_provenance"] = provenance[row["doc_id"]]
            row["union_size"] = len(provenance)
            row["eligible_union_size"] = len(eligible)
        return rows
