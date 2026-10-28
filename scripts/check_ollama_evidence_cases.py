
import os
import sys
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CORPUS = ROOT / "data" / "articles_13083.json"
INDEX_DIR = CORPUS.parent / "evidence_index" / CORPUS.stem
OUTPUT = ROOT / "real_ollama_evidence_results.json"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

QUESTIONS = [
    "At what temperature does water boil at sea level?",
    "What is 25 + 17?",
    "What was the date of the 2010 UEFA Europa League final? Answer only in YYYY-MM-DD format.",
    "Compare the location, date, winner, final score, and extra-time outcome of the 2010 UEFA Europa League final.",
    "Describe the location, magnitude, duration, aftershocks, and tsunami warning associated with the 2007 Tocopilla earthquake.",
    "Who won the 2010 UEFA Europa League final, what was the score, and was the match decided in extra time?",
    "Who won the 2010 FIFA World Cup?",
]


def to_json(value):
    if hasattr(value, "model_dump"):
        return to_json(value.model_dump())
    if hasattr(value, "dict"):
        return to_json(value.dict())
    if isinstance(value, dict):
        return {str(k): to_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json(v) for v in value]
    if hasattr(value, "__dict__"):
        return to_json(vars(value))
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def save_results(results):
    OUTPUT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def check_ollama():
    request = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))

    installed = [m.get("name", "") for m in data.get("models", [])]
    if OLLAMA_MODEL not in installed:
        raise RuntimeError(
            f"Model {OLLAMA_MODEL!r} is not installed. Available models: {installed}"
        )


def generate_answer(question):
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Answer the question directly and concisely. "
                    "Do not invent facts. If unsure, say so."
                ),
            },
            {"role": "user", "content": question},
        ],
        "options": {"temperature": 0},
    }

    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        data = json.loads(response.read().decode("utf-8"))

    answer = data.get("message", {}).get("content", "").strip()
    if not answer:
        raise RuntimeError(f"Ollama returned an empty answer: {data}")

    return {
        "model": data.get("model", OLLAMA_MODEL),
        "answer": answer,
        "done_reason": data.get("done_reason"),
    }


def main():
    if not CORPUS.is_file():
        raise FileNotFoundError(f"Corpus not found: {CORPUS}")

    artifacts = [
        INDEX_DIR / "faiss.index",
        INDEX_DIR / "chunks.json",
        INDEX_DIR / "manifest.json",
    ]
    missing = [str(p) for p in artifacts if not p.is_file()]
    if missing:
        raise RuntimeError(
            "Existing index artifacts are missing. Refusing to build an index:\n"
            + "\n".join(missing)
        )

    check_ollama()

    # Import only the evidence retrieval and evidence verification components.
    from app.verifiers.evidence_retriever import EvidenceRetriever
    from app.verifiers.evidence_verifier import EvidenceVerifier

    # Block index creation if the retriever decides the existing index is stale.
    original_build_index = EvidenceRetriever.build_index

    def refuse_rebuild(self, *args, **kwargs):
        raise RuntimeError(
            "Index rebuild blocked. The existing index is missing or stale. "
            "No rebuild was performed by this script."
        )

    EvidenceRetriever.build_index = refuse_rebuild
    try:
        retriever = EvidenceRetriever(corpus_path=str(CORPUS))
    finally:
        EvidenceRetriever.build_index = original_build_index

    results = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "ollama_model": OLLAMA_MODEL,
        "corpus": str(CORPUS),
        "index_dir": str(INDEX_DIR),
        "index_rebuild_requested": False,
        "scope": ["evidence retrieval", "evidence verification", "NLI"],
        "cases": [],
    }

    # Log the exact retrieval calls made inside the verifier.
    retrieval_log = []
    original_retrieve = retriever.retrieve

    def logged_retrieve(query, *args, **kwargs):
        passages = original_retrieve(query, *args, **kwargs)
        entry = {
            "query": query,
            "args": to_json(args),
            "kwargs": to_json(kwargs),
            "passages": to_json(passages),
        }
        retrieval_log.append(entry)

        print("\n  RETRIEVAL QUERY:", query)
        print("  RETRIEVED PASSAGES:")
        print(json.dumps(entry["passages"], indent=2, ensure_ascii=False))
        return passages

    retriever.retrieve = logged_retrieve

    verifier = EvidenceVerifier(retriever=retriever)

    # Capture raw outputs from the real NLI pipeline.
    nli_log = []
    original_nli = verifier.nli

    def logged_nli(inputs, *args, **kwargs):
        output = original_nli(inputs, *args, **kwargs)
        entry = {
            "input": to_json(inputs),
            "raw_output": to_json(output),
        }
        nli_log.append(entry)

        print("\n  NLI INPUT:")
        print(json.dumps(entry["input"], indent=2, ensure_ascii=False))
        print("  RAW NLI OUTPUT:")
        print(json.dumps(entry["raw_output"], indent=2, ensure_ascii=False))
        return output

    verifier.nli = logged_nli

    for case_id, question in enumerate(QUESTIONS, start=1):
        print(f"\n{'=' * 72}")
        print(f"CASE {case_id}: {question}")
        print("=" * 72)

        case = {
            "case_id": case_id,
            "question": question,
            "ollama": None,
            "retrieval_calls": [],
            "nli_calls": [],
            "verification": None,
            "error": None,
        }

        retrieval_start = len(retrieval_log)
        nli_start = len(nli_log)

        try:
            # Generate a fresh answer; do not use a hardcoded expected answer.
            generated = generate_answer(question)
            case["ollama"] = generated

            print("\nOLLAMA MODEL:", generated["model"])
            print("OLLAMA ANSWER:", generated["answer"])

            # No supplied context: verification must retrieve its own evidence.
            verification = verifier.verify(
                question=question,
                answer=generated["answer"],
                context=None,
            )

            case["verification"] = to_json(verification)

            print("\nFINAL EVIDENCE VERIFICATION:")
            print(
                json.dumps(
                    case["verification"],
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )
            )

        except Exception as exc:
            case["error"] = f"{type(exc).__name__}: {exc}"
            print("\nCASE ERROR:", case["error"])

        finally:
            case["retrieval_calls"] = retrieval_log[retrieval_start:]
            case["nli_calls"] = nli_log[nli_start:]
            results["cases"].append(case)
            save_results(results)

    print(f"\nResults saved to: {OUTPUT}")
    print("\nCASE SUMMARY:")
    for case in results["cases"]:
        print(
            f"Case {case['case_id']}: "
            f"error={case['error'] or 'None'}"
        )


if __name__ == "__main__":
    main()
