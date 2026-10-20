"""BEAR candidate generation from the corpus index, independent of source rankings."""
from .contracts import SchemaInvalidError


PARTS_VERSION = "corpus_parts_v1"


def validate_budget(top_k, languages=None):
    if type(top_k) is not int or top_k < 1:
        raise SchemaInvalidError("top_k must be a positive integer")
    if languages is not None and (not isinstance(languages, (list, tuple)) or not languages
            or any(not isinstance(lang, str) or not lang.strip() for lang in languages)
            or len(set(languages)) != len(languages)):
        raise SchemaInvalidError("languages must be a nonempty list of unique language codes")


class BearRetriever:
    """Search all indexed corpus documents matching the query, then rank by evidence.

    No baseline pool or rank source is accepted. The index owns the shared scoring
    definition also used by BearFusion; neither API imposes fixed200 or final quotas.
    """
    stage = "bear_retrieval"
    candidate_scope = "corpus"

    def __init__(self, index):
        self.index = index

    def retrieve(self, query, top_k=300, languages=None):
        validate_budget(top_k, languages)
        return self.index.search(query, top_k=top_k, languages=languages)
