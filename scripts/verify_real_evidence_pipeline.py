import argparse
import json
import sys
import tempfile
import time
import traceback
import warnings
from pathlib import Path

from app.verifiers.evidence_retriever import EvidenceRetriever, file_sha256
from app.verifiers.evidence_verifier import EvidenceVerifier

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "articles_13083.json"

CASES = [
    {
        "name": "Known answer: Hamlet",
        "question": "Who wrote Hamlet?",
        "answer": "William Shakespeare",
    },
    {
        "name": "Wrong answer: Hamlet",
        "question": "Who wrote Hamlet?",
        "answer": "Charles Dickens",
    },
    {
        "name": "Known answer: France",
        "question": "What is the capital of France?",
        "answer": "Paris",
    },
    {
        "name": "Wrong answer: France",
        "question": "What is the capital of France?",
        "answer": "London",
    },
    {
        "name": "Potentially unsupported topic",
        "question": "What is the capital of Atlantis?",
        "answer": "Poseidon City",
    },
]

def configure_utf8() -> None:
    """Make redirected and interactive Windows streams preserve Unicode."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="strict")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="Print complete verifier metadata.")
    parser.add_argument("--json-log", type=Path, help="Write complete UTF-8 diagnostic records.")
    return parser.parse_args(argv)


def _brief_evidence(row):
    return {
        "title": row.get("title"),
        "article_id": row.get("article_id"),
        "chunk_id": row.get("chunk_id"),
        "score": round(float(row.get("score", row.get("retrieval_score", 0.0))), 4),
        "topic_coverage": row.get("topic_coverage"),
        "about_subject": row.get("about_subject"),
        "nli_label": row.get("nli_label"),
        "nli_score": row.get("nli_score"),
        "reason": row.get("reason"),
    }


def _write_json_log(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _validate_fresh_index(retriever, index_dir: Path, temp_root: Path) -> dict:
    resolved = index_dir.resolve()
    if temp_root.resolve() not in resolved.parents:
        raise AssertionError("Diagnostic index is not inside its temporary directory")
    if retriever.index_dir.resolve() != resolved:
        raise AssertionError("Retriever did not use the requested temporary index")
    if retriever.index.ntotal != len(retriever.chunks):
        raise AssertionError("FAISS vector count does not match chunk metadata count")
    dimensions = int(retriever.index.d)
    expected_dimensions = int(retriever.model.get_sentence_embedding_dimension())
    if dimensions != expected_dimensions:
        raise AssertionError(
            f"FAISS dimension {dimensions} does not match embedding dimension {expected_dimensions}"
        )
    chunk_ids = [chunk.get("chunk_id") for chunk in retriever.chunks]
    if chunk_ids != list(range(len(retriever.chunks))):
        raise AssertionError("Chunk metadata IDs are not contiguous and index-aligned")
    manifest = json.loads(retriever.manifest_path.read_text(encoding="utf-8"))
    if manifest.get("corpus_sha256") != file_sha256(CORPUS):
        raise AssertionError("Temporary index manifest has the wrong corpus hash")
    return {
        "index_directory": str(resolved),
        "temporary": True,
        "chunk_count": len(retriever.chunks),
        "vector_count": int(retriever.index.ntotal),
        "embedding_dimensions": dimensions,
        "embedding_model": retriever.EMBEDDING_MODEL,
        "nli_model": EvidenceVerifier.NLI_MODEL,
        "corpus_version": retriever.corpus_version,
        "index_version": retriever.index_version,
        "manifest": manifest,
    }


def run_diagnostic(args) -> bool:
    print("=" * 72)
    print("REAL EVIDENCE RETRIEVAL + REAL NLI DIAGNOSTIC")
    print("=" * 72)
    if not CORPUS.is_file():
        raise FileNotFoundError(f"Corpus not found: {CORPUS}")
    print("Corpus:", CORPUS)
    print("Corpus size:", f"{CORPUS.stat().st_size:,}", "bytes")

    records = []
    completed = failures = 0
    with tempfile.TemporaryDirectory(prefix="real_evidence_check_") as temp:
        temp_root = Path(temp)
        index_dir = temp_root / "fresh_index"
        print("\nBuilding a fresh index from the real corpus...")
        retriever = EvidenceRetriever(corpus_path=str(CORPUS), index_dir=str(index_dir))
        integrity = _validate_fresh_index(retriever, index_dir, temp_root)
        print(json.dumps(integrity, indent=2, ensure_ascii=False))

        print("\nLoading the real EvidenceVerifier and NLI model...")
        verifier = EvidenceVerifier(retriever=retriever)
        for case in CASES:
            print("\n" + "=" * 72)
            print("CASE:", case["name"])
            print("Question:", case["question"])
            print("Answer:", case["answer"])
            started = time.perf_counter()
            try:
                with warnings.catch_warnings(record=True) as seen_warnings:
                    warnings.simplefilter("always")
                    retrieved = retriever.retrieve(case["question"], k=5)
                    result = verifier.verify(case["question"], case["answer"])
                metadata = result.metadata
                evaluated = metadata.get("evaluated_evidence", [])
                discarded = metadata.get("discarded_evidence", [])
                summary = {
                    "status": metadata.get("decision"),
                    "score": result.score,
                    "retrieved": [_brief_evidence(row) for row in retrieved],
                    "evaluated_count": len(evaluated),
                    "discarded_count": len(discarded),
                    "evaluated": [_brief_evidence(row) for row in evaluated],
                    "discarded": [_brief_evidence(row) for row in discarded],
                    "runtime_ms": round((time.perf_counter() - started) * 1000, 2),
                    "warnings": [str(item.message) for item in seen_warnings],
                }
                record = {
                    "case": case,
                    "completed": True,
                    "summary": summary,
                    "retrieved": retrieved,
                    "result": {
                        "passed": result.passed,
                        "score": result.score,
                        "reasoning": result.reasoning,
                        "metadata": metadata,
                    },
                }
                completed += 1
                print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
                if args.verbose:
                    print(json.dumps(record, indent=2, ensure_ascii=False, default=str))
            except Exception as exc:
                failures += 1
                record = {
                    "case": case,
                    "completed": False,
                    "exception": f"{type(exc).__name__}: {exc}",
                    "runtime_ms": round((time.perf_counter() - started) * 1000, 2),
                }
                print(f"ERROR: {record['exception']}", file=sys.stderr)
                traceback.print_exc()
            records.append(record)

        print("\n" + "=" * 72)
        state = "COMPLETED" if completed == len(CASES) else "PARTIAL"
        print(f"DIAGNOSTIC {state}: {completed}/{len(CASES)} cases completed; {failures} failed")
        print("All attempted retrieval and verification calls used real components.")
        print("The temporary rebuilt index will now be removed safely.")
        print("=" * 72)
        if args.json_log:
            _write_json_log(
                args.json_log,
                {"integrity": integrity, "completed": completed, "failures": failures, "cases": records},
            )
    return failures == 0 and completed == len(CASES)


def main(argv=None) -> int:
    configure_utf8()
    args = parse_args(argv)
    try:
        return 0 if run_diagnostic(args) else 1
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
