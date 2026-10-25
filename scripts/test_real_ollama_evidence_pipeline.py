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
import sys
import time
import urllib.error
import urllib.request
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


def ollama_generate(question: str) -> tuple[str, dict[str, Any]]:
    prompt = (
        "Answer the factual question in one concise sentence. "
        "If you do not know, say you are not sure. Do not invent sources.\n\n"
        f"Question: {question}\nAnswer:"
    )
    payload = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                          "options": {"temperature": 0}}).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach Ollama at {OLLAMA_URL}. Start Ollama and pull {OLLAMA_MODEL}. Details: {exc}") from exc
    answer = str(data.get("response", "")).strip()
    if not answer:
        raise RuntimeError(f"Ollama returned an empty answer: {data}")
    return answer, {"model": data.get("model", OLLAMA_MODEL), "done_reason": data.get("done_reason"),
                    "total_duration": data.get("total_duration"), "prompt_eval_count": data.get("prompt_eval_count"),
                    "eval_count": data.get("eval_count")}


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
            answer, ollama_meta = ollama_generate(case["question"])
            result = verifier.verify(question=case["question"], answer=answer, context=None)
            result_data = as_dict(result)
            record = {**case, "ollama_answer": answer, "ollama_metadata": ollama_meta,
                      "verifier_result": result_data, "error": None}
            print(f"  Ollama: {answer}")
            print(f"  Verifier: {json.dumps(result_data, ensure_ascii=False, default=str)[:1200]}")
        except Exception as exc:
            record = {**case, "ollama_answer": None, "ollama_metadata": None,
                      "verifier_result": None, "error": f"{type(exc).__name__}: {exc}"}
            print(f"  ERROR: {record['error']}")
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
        "cases": records,
    }
    out = OUTPUT_PATH
    if out.exists():
        stamp = time.strftime("%Y%m%d-%H%M%S")
        out = out.with_name(f"{out.stem}_{stamp}{out.suffix}")
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nSaved results: {out}")
    print(f"Completed: {len(records) - summary['errors']}/{len(records)}; errors: {summary['errors']}")
    print("Note: inspect each verifier decision against the article text; Ollama answers are generated live and can vary.")
    return 1 if summary["errors"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
