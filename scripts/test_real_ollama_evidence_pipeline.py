"""End-to-end benchmark: real Ollama generation + real EvidenceVerifier/NLI.

Run from repository root:
  .venv\\Scripts\\python scripts\\test_real_ollama_evidence_pipeline.py

This script does not inject fake NLI, mock retrieval, or pass gold answers as context.
Ollama answers from the question alone; EvidenceVerifier independently retrieves from
EVIDENCE_CORPUS_PATH / data/articles_13083.json and uses its configured real NLI model.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CORPUS_PATH = Path(os.getenv("EVIDENCE_CORPUS_PATH", str(ROOT / "data" / "articles_13083.json")))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OUTPUT_PATH = ROOT / "real_ollama_evidence_benchmark.json"

# Every gold fact below is taken from article text in the supplied 145-article subset.
# Keep questions single-fact and answerable from one article wherever possible.
CASES = [
    {"id":"A01", "title":"Azeem Abdulai", "question":"Which position does Azeem Abdulai play?", "gold":"Defensive midfielder.", "expected":"SUPPORT"},
    {"id":"A02", "title":"Azeem Abdulai", "question":"Which national team does Azeem Abdulai represent?", "gold":"The Sierra Leone national team.", "expected":"SUPPORT"},
    {"id":"A03", "title":"Azeem Abdulai", "question":"On what date did Azeem Abdulai score his first goal for Swansea?", "gold":"13 August 2024.", "expected":"SUPPORT"},
    {"id":"B01", "title":"Bengali theatre", "question":"In which two regions is Bengali theatre produced mainly?", "gold":"West Bengal and Bangladesh.", "expected":"SUPPORT"},
    {"id":"B02", "title":"Bengali theatre", "question":"When did Bengali theatre begin as private entertainment?", "gold":"In the early 19th century.", "expected":"SUPPORT"},
    {"id":"D01", "title":"Diaguita", "question":"In which part of South America are the Diaguita Indigenous peoples primarily associated?", "gold":"The Chilean Norte Chico and the Argentine Northwest.", "expected":"SUPPORT"},
    {"id":"F01", "title":"2026 Fagersta school attack", "question":"On what date did the Fagersta school attack occur?", "gold":"21 August 2026.", "expected":"SUPPORT"},
    {"id":"F02", "title":"2026 Fagersta school attack", "question":"How many people were killed in the Fagersta school attack according to the article?", "gold":"One person was killed.", "expected":"SUPPORT"},
    {"id":"F03", "title":"2026 Fagersta school attack", "question":"What commission did the Swedish government announce plans to create on 24 August 2026?", "gold":"The School Violence Commission (Skoldådskommission).", "expected":"SUPPORT"},
    {"id":"P01", "title":"1099 papal election", "question":"On what date did the 1099 papal election take place?", "gold":"13 August 1099.", "expected":"SUPPORT"},
    {"id":"S01", "title":"2014 Seattle Pacific University shooting", "question":"How many people were killed in the 2014 Seattle Pacific University shooting?", "gold":"One person was killed.", "expected":"SUPPORT"},
    {"id":"G01", "title":"2012 Green Bay Packers season", "question":"What was the Green Bay Packers' regular-season win-loss record in 2012?", "gold":"11 wins and 5 losses.", "expected":"SUPPORT"},
    {"id":"N01", "title":"1948 Nobel Prize in Literature", "question":"Who received the 1948 Nobel Prize in Literature?", "gold":"T. S. Eliot.", "expected":"SUPPORT"},
    {"id":"Q01", "title":"2007 Tocopilla earthquake", "question":"On what date did the 2007 Tocopilla earthquake occur?", "gold":"14 November 2007.", "expected":"SUPPORT"},
    {"id":"C01", "title":"1951 English cricket season", "question":"Which county won the 1951 County Championship?", "gold":"Warwickshire.", "expected":"SUPPORT"},
    {"id":"C02", "title":"1951 English cricket season", "question":"How many matches did Warwickshire win in the 1951 County Championship?", "gold":"16 matches.", "expected":"SUPPORT"},
    {"id":"H01", "title":"American rubyspot", "question":"What is the scientific name of the American rubyspot?", "gold":"Hetaerina americana.", "expected":"SUPPORT"},
    {"id":"H02", "title":"American rubyspot", "question":"In what year was Hetaerina americana first formally described?", "gold":"1798.", "expected":"SUPPORT"},
    {"id":"R01", "title":"1922 Bridgman Convention", "question":"On what date was the 1922 Bridgman Convention raided?", "gold":"22 August 1922.", "expected":"SUPPORT"},
]

# These are deliberately wrong answers for negative-control runs. They are only run
# if --include-negative is supplied; expected REJECT means evidence must contradict them.
NEGATIVE_CASES = [
    {"id":"NEG01", "title":"Azeem Abdulai", "question":"Which national team does Azeem Abdulai represent?", "fixed_answer":"Scotland.", "gold":"Sierra Leone.", "expected":"REJECT"},
    {"id":"NEG02", "title":"1951 English cricket season", "question":"Which county won the 1951 County Championship?", "fixed_answer":"Yorkshire.", "gold":"Warwickshire.", "expected":"REJECT"},
    {"id":"NEG03", "title":"American rubyspot", "question":"In what year was Hetaerina americana first formally described?", "fixed_answer":"1898.", "gold":"1798.", "expected":"REJECT"},
    {"id":"NEG04", "title":"1099 papal election", "question":"On what date did the 1099 papal election take place?", "fixed_answer":"13 August 1098.", "gold":"13 August 1099.", "expected":"REJECT"},
]


class GenerationStatus(str, Enum):
    ANSWERED = "ANSWERED"
    ABSTAINED = "ABSTAINED"
    GENERATION_ERROR = "GENERATION_ERROR"


@dataclass
class GenerationOutcome:
    status: GenerationStatus
    answer: str | None
    metadata: dict[str, Any]
    error: str | None = None


_REFUSAL_ONLY = re.compile(
    r"^(?:sorry[,!]?\s+)?(?:i\s+(?:do not|don't|dont)\s+know|i(?:'m| am)\s+not\s+sure|"
    r"i\s+(?:cannot|can't|cant)\s+(?:answer(?:\s+reliably)?|determine(?:\s+reliably)?)|"
    r"i(?:'m| am)\s+(?:unable|not able)\s+to\s+(?:answer|determine)|"
    r"unable\s+to\s+(?:answer|determine)|i\s+cannot\s+provide\s+an?\s+answer)[.!\s]*$",
    re.IGNORECASE,
)


def parse_generation_response(raw: str, metadata: dict[str, Any] | None = None) -> GenerationOutcome:
    """Validate Ollama's structured response and separate abstention from errors."""
    meta = metadata or {}
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        text = str(raw).strip()
        if _REFUSAL_ONLY.fullmatch(text):
            return GenerationOutcome(GenerationStatus.ABSTAINED, None, meta)
        return GenerationOutcome(GenerationStatus.GENERATION_ERROR, None, meta,
                                 "Ollama response was not valid status/answer JSON")
    if not isinstance(value, dict) or value.get("status") not in {"ANSWERED", "ABSTAINED"}:
        return GenerationOutcome(GenerationStatus.GENERATION_ERROR, None, meta,
                                 "Ollama response has an invalid status schema")
    status = GenerationStatus(value["status"])
    answer = value.get("answer")
    if not isinstance(answer, str):
        return GenerationOutcome(GenerationStatus.GENERATION_ERROR, None, meta,
                                 "Ollama response answer must be a string")
    answer = answer.strip()
    if status is GenerationStatus.ABSTAINED:
        return GenerationOutcome(status, None, meta)
    if not answer:
        return GenerationOutcome(GenerationStatus.GENERATION_ERROR, None, meta,
                                 "Ollama returned ANSWERED with an empty answer")
    # Be tolerant of a refusal-only answer even if the model ignored the status.
    if _REFUSAL_ONLY.fullmatch(answer):
        return GenerationOutcome(GenerationStatus.ABSTAINED, None, meta)
    return GenerationOutcome(GenerationStatus.ANSWERED, answer, meta)


def verify_generation(verifier: Any, question: str, outcome: GenerationOutcome) -> Any:
    """Only factual answers enter evidence verification."""
    if outcome.status is not GenerationStatus.ANSWERED:
        return None
    return verifier.verify(question=question, answer=outcome.answer, context=None)


def ollama_generate(question: str) -> GenerationOutcome:
    prompt = (
        "Answer the factual question with a concise, direct answer. Do not guess or invent facts. "
        "If you cannot answer reliably, explicitly abstain. Return only JSON with status and answer. "
        'Use status "ANSWERED" when providing a factual answer, or "ABSTAINED" when abstaining. '
        'For ABSTAINED, set answer to an empty string.\n\n'
        f"Question: {question}"
    )
    response_schema = {"type": "object", "properties": {
        "status": {"type": "string", "enum": ["ANSWERED", "ABSTAINED"]},
        "answer": {"type": "string"}}, "required": ["status", "answer"], "additionalProperties": False}
    payload = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                          "format": response_schema, "options": {"temperature": 0}}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return GenerationOutcome(GenerationStatus.GENERATION_ERROR, None, {},
                                 f"Cannot obtain a valid Ollama response at {OLLAMA_URL}: {exc}")
    if not isinstance(data, dict):
        return GenerationOutcome(GenerationStatus.GENERATION_ERROR, None, {},
                                 "Ollama returned a non-object API response")
    metadata = {"model": data.get("model", OLLAMA_MODEL), "done_reason": data.get("done_reason"),
                    "total_duration": data.get("total_duration"), "prompt_eval_count": data.get("prompt_eval_count"),
                    "eval_count": data.get("eval_count")}
    return parse_generation_response(data.get("response", ""), metadata)


def as_dict(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict") and callable(value.dict):
        return value.dict()
    if hasattr(value, "__dict__"):
        return {k: v for k, v in vars(value).items() if not k.startswith("_")}
    return value


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-negative", action="store_true", help="also verify four deliberately wrong answers")
    parser.add_argument("--limit", type=int, default=0, help="run only first N positive cases (0 = all)")
    args = parser.parse_args()

    if not CORPUS_PATH.exists():
        print(f"ERROR: corpus not found: {CORPUS_PATH}")
        return 2

    # Import the project's actual verifier. Do not pass an injected NLI callable:
    # EvidenceVerifier therefore constructs its configured transformers NLI model.
    from app.verifiers.evidence_verifier import EvidenceVerifier
    verifier = EvidenceVerifier(corpus_path=str(CORPUS_PATH))
    nli_name = getattr(verifier, "NLI_MODEL", "configured by EvidenceVerifier")
    print(f"Corpus: {CORPUS_PATH}")
    print(f"Ollama: {OLLAMA_MODEL} @ {OLLAMA_URL}")
    print(f"Real NLI model configured by EvidenceVerifier: {nli_name}")
    print("Fake NLI / fake retrieval: NOT USED")

    cases = CASES[:args.limit] if args.limit > 0 else list(CASES)
    records: list[dict[str, Any]] = []
    for idx, case in enumerate(cases, 1):
        print(f"\n[{idx}/{len(cases)}] {case['id']} — {case['question']}")
        try:
            generation = ollama_generate(case["question"])
        except Exception as exc:
            generation = GenerationOutcome(GenerationStatus.GENERATION_ERROR, None, {},
                                           f"{type(exc).__name__}: {exc}")
        result_data = None
        verification_error = None
        if generation.status is GenerationStatus.ANSWERED:
            try:
                result_data = as_dict(verify_generation(verifier, case["question"], generation))
            except Exception as exc:
                verification_error = f"{type(exc).__name__}: {exc}"
        record = {**case, "generation_status": generation.status.value,
                  "ollama_answer": generation.answer, "ollama_metadata": generation.metadata,
                  "verifier_result": result_data, "generation_error": generation.error,
                  "verification_error": verification_error, "error": verification_error}
        print(f"  Generation: {generation.status.value}" + (f" — {generation.answer}" if generation.answer else ""))
        if result_data is not None:
            print(f"  Verifier: {json.dumps(result_data, ensure_ascii=False, default=str)[:1200]}")
        elif generation.error:
            print(f"  Generation error: {generation.error}")
        elif verification_error:
            print(f"  Verification error: {verification_error}")
        records.append(record)
        time.sleep(0.1)

    if args.include_negative:
        for case in NEGATIVE_CASES:
            print(f"\n[negative] {case['id']} — {case['question']}")
            try:
                result = verifier.verify(question=case["question"], answer=case["fixed_answer"], context=None)
                record = {**case, "ollama_answer": case["fixed_answer"], "ollama_metadata": {"mode":"fixed negative control"},
                          "verifier_result": as_dict(result), "error": None}
                print(f"  Fixed false answer: {case['fixed_answer']}")
                print(f"  Verifier: {json.dumps(record['verifier_result'], ensure_ascii=False, default=str)[:1200]}")
            except Exception as exc:
                record = {**case, "ollama_answer": case["fixed_answer"], "verifier_result": None,
                          "error": f"{type(exc).__name__}: {exc}"}
                print(f"  ERROR: {record['error']}")
            records.append(record)

    summary = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "corpus_path": str(CORPUS_PATH), "ollama_url": OLLAMA_URL, "ollama_model": OLLAMA_MODEL,
        "nli_model": nli_name, "fake_nli_used": False, "fake_retrieval_used": False,
        "total_cases": len(records), "errors": sum(r.get("error") is not None for r in records),
        "generation_counts": {status.value: sum(r.get("generation_status") == status.value for r in records)
                              for status in GenerationStatus},
        "verification_counts": {label: sum((r.get("verifier_result") or {}).get("metadata", {}).get("decision") == label
                                            for r in records) for label in ("SUPPORT", "REJECT", "UNSURE")},
        "verification_eligible": sum(r.get("generation_status") == GenerationStatus.ANSWERED.value and r.get("expected") in {"SUPPORT", "REJECT"} for r in records),
        "cases": records,
    }
    denominator = len(cases)
    generated = summary["generation_counts"][GenerationStatus.ANSWERED.value]
    abstained = summary["generation_counts"][GenerationStatus.ABSTAINED.value]
    generation_errors = summary["generation_counts"][GenerationStatus.GENERATION_ERROR.value]
    eligible = [r for r in records if r.get("generation_status") == GenerationStatus.ANSWERED.value
                and r.get("expected") in {"SUPPORT", "REJECT"} and r.get("verifier_result")]
    correct = sum((r["verifier_result"].get("metadata", {}).get("decision") == r["expected"]) for r in eligible)
    summary.update({
        "generated_answers": generated,
        "abstentions": abstained,
        "generation_errors": generation_errors,
        "generation_rates": {
            "answered": generated / denominator if denominator else 0.0,
            "abstained": abstained / denominator if denominator else 0.0,
            "generation_error": generation_errors / denominator if denominator else 0.0,
        },
        "verification_accuracy": {"correct": correct, "eligible": len(eligible),
                                  "rate": correct / len(eligible) if eligible else None},
        "incorrect_rejections": sum(r["verifier_result"].get("metadata", {}).get("decision") == "REJECT"
                                    and r.get("expected") == "SUPPORT" for r in eligible),
        "insufficient_evidence": sum(r["verifier_result"].get("metadata", {}).get("decision") == "UNSURE"
                                     for r in eligible),
    })
    out = OUTPUT_PATH
    if out.exists():
        stamp = f"{time.strftime('%Y%m%d-%H%M%S')}-{time.time_ns()}"
        out = out.with_name(f"{out.stem}_{stamp}{out.suffix}")
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nSaved results: {out}")
    print(f"Completed: {len(records) - summary['errors']}/{len(records)}; errors: {summary['errors']}")
    print("Note: inspect each verifier decision against the article text; Ollama answers are generated live and can vary.")
    return 1 if summary["errors"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
