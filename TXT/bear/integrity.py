"""Chunk nguyên văn, sidecar offsets, kiểm records thật và ZIP readback."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import zipfile
from .adapters import load_chunk_refs, read_chunk_scores
from .artifacts import corpus_connection, read_corpus_batch
from .contracts import SchemaInvalidError
from .io import assert_valid_output_path, read_json, sha256_file


def load_legacy_chunk_scores(path):
    scores = {}
    for item in read_chunk_scores(path):
        scores.setdefault(item.query_id, {}).setdefault(item.doc_id, {})[item.chunk_idx] = item.score
    return scores


def select_legacy(refs, count, scores=None):
    if len(refs) > count and scores:
        selected = sorted(range(len(refs)), key=lambda i: (-scores.get(i, -1), i))[:count]
        return [refs[i] for i in sorted(selected)]
    return refs[:count]


def build_with_refs(ranking, corpus, scores, plans, corpus_hash):
    records, sidecar = [], []
    with corpus_connection(corpus) as conn:
        for qid, docs in sorted(ranking.items()):
            refs = load_chunk_refs(conn, docs, corpus_hash)
            bodies = read_corpus_batch(conn, docs)
            chosen = []
            for i, doc in enumerate(docs[:120]):
                chosen.extend(select_legacy(refs.get(doc, []), 2 if i < 40 else 1,
                                           scores.get(qid, {}).get(doc) if i < 40 else None))
            plan = plans.get(qid, {})
            chosen = [r for r in chosen if plan.get(r.doc_id, 1) > 0]
            have = {r.doc_id for r in chosen}
            for doc in docs:
                if plan.get(doc, 0) > 0 and doc not in have:
                    chosen.extend(refs.get(doc, [])[:plan[doc]])
            chunks = []
            for pos, ref in enumerate(chosen):
                chunks.append({"doc_id": int(ref.doc_id),
                               "chunk_text": bodies[ref.doc_id]["body"][ref.start:ref.end]})
                sidecar.append({"query_id": qid, "doc_rank": docs.index(ref.doc_id) + 1,
                                "output_position": pos, **asdict(ref)})
            records.append({"id": qid, "relevant_docs": [int(d) for d in docs], "relevant_chunks": chunks})
    return records, sidecar


def validate_records(records, sidecar, corpus, n_queries=1200, output_docs=200):
    from submit.submission import validate
    errors = validate(records, n_queries=n_queries, id_type=int)
    if errors:
        raise SchemaInvalidError("; ".join(errors))
    refs = {(r["query_id"], r["output_position"]): r for r in sidecar}
    if len(refs) != len(sidecar):
        raise SchemaInvalidError("Duplicate provenance key")
    expected_keys = set()
    with corpus_connection(corpus) as conn:
        for record in records:
            docs = record["relevant_docs"]
            if len(docs) != output_docs or len(set(docs)) != len(docs) or any(type(d) is not int or d <= 0 for d in docs):
                raise SchemaInvalidError(f"qid {record['id']}: sai số lượng/IDs")
            bodies = read_corpus_batch(conn, [str(d) for d in docs])
            if len(bodies) != len(docs):
                raise SchemaInvalidError("Doc ngoài corpus")
            previous_offsets = {}
            for pos, chunk in enumerate(record["relevant_chunks"]):
                key = record["id"], pos
                expected_keys.add(key)
                ref = refs.get(key)
                doc = str(chunk["doc_id"])
                if int(doc) not in docs or ref is None or ref["doc_id"] != doc:
                    raise SchemaInvalidError("Chunk thiếu provenance hoặc doc không thuộc ranking")
                body = bodies[doc]["body"]
                if ref["mapping_status"] != "verified" or not 0 <= ref["start"] < ref["end"] <= len(body):
                    raise SchemaInvalidError("Chunk mapping/offset sai")
                if hashlib.sha256(body.encode()).hexdigest() != ref["body_sha256"]:
                    raise SchemaInvalidError("Body hash lệch")
                text = body[ref["start"]:ref["end"]]
                if text != chunk["chunk_text"] or hashlib.sha256(text.encode()).hexdigest() != ref["text_sha256"]:
                    raise SchemaInvalidError("Chunk text/hash lệch slice")
                if doc in previous_offsets and ref["start"] < previous_offsets[doc]:
                    raise SchemaInvalidError("Chunk không theo thứ tự offset")
                previous_offsets[doc] = ref["start"]
    if set(refs) != expected_keys:
        raise SchemaInvalidError("Sidecar thừa refs")
    return {"queries": len(records), "chunks": len(sidecar), "status": "verified"}


def package_zip(records, prefix):
    prefix = assert_valid_output_path(prefix)
    from submit.submission import write_zip
    js, zp = write_zip(records, str(prefix), method="lzma")
    with zipfile.ZipFile(zp) as archive:
        if archive.namelist() != [Path(js).name] or archive.testzip() is not None:
            raise SchemaInvalidError("ZIP corrupt hoặc sai thành viên")
        # So bytes theo luồng, không giữ thêm một bản records trong RAM.
        with archive.open(Path(js).name) as source:
            digest = hashlib.sha256()
            while block := source.read(1024 * 1024):
                digest.update(block)
        if digest.hexdigest() != sha256_file(js):
            raise SchemaInvalidError("ZIP readback khác JSON")
    if Path(zp).stat().st_size >= 100_000_000:
        raise SchemaInvalidError("ZIP vượt conservative limit <100,000,000 bytes")
    return [Path(js), Path(zp)]


def legacy_readonly_audit(corpus):
    """Gọi audit_chunk trực tiếp; slim store thiếu schema không bị migrate."""
    import contextlib
    import io
    from .artifacts import corpus_schema
    from utils import audit
    with corpus_connection(corpus) as conn:
        _, tables = corpus_schema(conn)
        if not {"doc_id", "body", "lang"} <= set(tables["doc"]) or not {
            "chunk_id", "doc_id", "start", "end", "ord", "n_chars"} <= set(tables["chunk"]):
            return {"status": "schema_unavailable", "crawl_audit": "not_applicable"}
        before = len(audit._fails)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            audit.audit_chunk(conn)
        failures = audit._fails[before:]
        return {"status": "failed" if failures else "passed", "failures": failures,
                "log": output.getvalue(), "crawl_audit": "not_run_full_crawler_schema_required",
                "submission_audit": "final_records_checked_by_BEAR_integrity"}
