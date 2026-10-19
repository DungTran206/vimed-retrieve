"""C1/C2 giữ slot, giữ text; C3 cần study ngân sách riêng."""
from .contracts import SchemaInvalidError
from .integrity import select_legacy


def select_chunks(refs, slots, rank, experiment="C1", scores=None, evidence=None):
    if experiment not in ("C1", "C2"):
        raise SchemaInvalidError("Chỉ C1/C2; C3 chưa được đăng ký budget frontier")
    if type(slots) is not int or slots < 0:
        raise SchemaInvalidError("slots không hợp lệ")
    if rank <= 40:
        return select_legacy(refs, slots, scores), "legacy_head"
    values = scores if experiment == "C1" else evidence
    if values is None or any(r.exporter_idx not in values or values[r.exporter_idx] is None for r in refs):
        return refs[:slots], "incomplete_feature_first_chunk"
    chosen = sorted(refs, key=lambda r: (-values[r.exporter_idx], r.exporter_idx))[:slots]
    return sorted(chosen, key=lambda r: (r.start, r.end, r.chunk_id_native)), "complete_feature"
