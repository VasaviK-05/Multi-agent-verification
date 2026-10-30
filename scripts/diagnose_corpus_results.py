
import json
import sys
from pathlib import Path
from collections import Counter

def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python -m scripts.diagnose_corpus_results "
            "corpus_evidence_test_results.json"
        )
        raise SystemExit(1)

    results_path = Path(sys.argv[1])
    if not results_path.exists():
        raise SystemExit(f"Results file not found: {results_path}")

    data = json.loads(results_path.read_text(encoding="utf-8"))
    cases = data.get("cases", [])

    if not cases:
        raise SystemExit("No 'cases' list found in the JSON file.")

    output = []
    total = len(cases)
    passed = sum(
        c.get("passed", c.get("result_passed", False))
        for c in cases
    )

    output += [
        "=" * 78,
        "CORPUS EVIDENCE DIAGNOSTIC REPORT",
        "=" * 78,
        f"Input: {results_path.resolve()}",
        f"Cases: {total}",
        f"Correct decisions: {passed}/{total} ({passed / total:.1%})",
        "",
        "CASE-BY-CASE ANALYSIS",
        "-" * 78,
    ]

    stage_counts = Counter()
    failures = []

    for case in cases:
        case_id = case.get("case_id", "?")
        question = case.get("question", "")
        expected = case.get("expected_decision", "?")
        actual = case.get("actual_decision", "?")
        passed_case = case.get(
            "passed", case.get("result_passed", False)
        )

        claims = case.get("claim_decisions") or []
        evidence = case.get("evaluated_evidence") or []

        if not evidence:
            for claim in claims:
                evidence.extend(claim.get("evaluated_evidence") or [])

        discarded = case.get("discarded_evidence") or []
        if isinstance(discarded, dict):
            discarded = list(discarded.values())

        if passed_case:
            diagnosis = "DECISION MATCH"
        elif not evidence:
            diagnosis = "NO EVALUATED EVIDENCE: inspect retrieval/filtering"
        elif any(
            e.get("value_relation") in ("match", "mismatch")
            for e in evidence
        ):
            diagnosis = "FACT/NLI/AGGREGATION: inspect value_relation overrides"
        else:
            diagnosis = "NLI/AGGREGATION: inspect premise and probabilities"

        stage_counts[diagnosis] += 1

        if not passed_case:
            failures.append(case_id)

        output += [
            "",
            f"[{case_id}] {'PASS' if passed_case else 'FAIL'}",
            f"Question: {question}",
            f"Expected: {expected} | Actual: {actual}",
            f"Initial diagnosis: {diagnosis}",
        ]

        if not claims:
            claims = [{}]

        for claim in claims:
            output.append(
                "Claim decision: "
                f"{claim.get('decision', actual)} | "
                f"reason={claim.get('unsure_reason')} | "
                f"best_retrieval_score={claim.get('best_retrieval_score')}"
            )

        output.append(f"Evaluated evidence rows: {len(evidence)}")

        for i, e in enumerate(evidence, 1):
            probs = e.get("probabilities") or {}
            output += [
                f"  Evidence {i}: {e.get('title', '?')}",
                f"    source: {e.get('source_id', '?')}",
                f"    retrieval_score: {e.get('retrieval_score')}",
                f"    relevant: {e.get('about_subject', 'not recorded')}",
                f"    discard_code: {e.get('discard_code')}",
                f"    topic_coverage: {e.get('topic_coverage')}",
                f"    missing_numbers: {e.get('missing_numbers')}",
                f"    value_relation: {e.get('value_relation')}",
                f"    NLI: {e.get('nli_label')} "
                f"(score={e.get('nli_score')})",
                f"    probabilities: {probs}",
                f"    premise: {e.get('relevant_evidence', '')}",
            ]

            windows = e.get("premise_windows") or []
            if windows:
                output.append("    Premise-window predictions:")
                for w in windows:
                    output.append(
                        f"      label={w.get('nli_label')}, "
                        f"probabilities={w.get('probabilities')}, "
                        f"value_relation={w.get('value_relation')}"
                    )
                    output.append(
                        f"      text={w.get('premise', '')}"
                    )

        output.append(f"Discarded evidence rows: {len(discarded)}")
        for item in discarded[:10]:
            if isinstance(item, dict):
                output.append(
                    "  Discarded: "
                    f"title={item.get('title', '?')} | "
                    f"reason={item.get('discard_code', item.get('reason', '?'))} | "
                    f"score={item.get('retrieval_score', item.get('score', '?'))}"
                )
            else:
                output.append(f"  Discarded reference: {item}")

    output += [
        "",
        "=" * 78,
        "SUMMARY",
        "=" * 78,
        f"Failed case IDs: {', '.join(failures) or 'None'}",
        "",
        "Initial diagnosis counts (overlapping root causes are possible):",
    ]

    for label, count in stage_counts.most_common():
        output.append(f"  {count}: {label}")

    output += [
        "",
        "IMPORTANT:",
        "These are triage hints, not definitive root-cause labels.",
        "A correct article title does not prove the correct fact was evaluated.",
        "Inspect the premise, its probabilities, and the final decision path.",
        "If evidence rows are absent, check the full candidate/discard metadata",
        "before concluding that retrieval itself failed.",
    ]

    report_path = results_path.with_name(
        results_path.stem + "_diagnostic.txt"
    )
    report_path.write_text("\n".join(output), encoding="utf-8")

    print(f"Cases: {total}")
    print(f"Correct decisions: {passed}/{total} ({passed / total:.1%})")
    print(f"Failed IDs: {', '.join(failures)}")
    print(f"Diagnostic report saved to: {report_path.resolve()}")


if __name__ == "__main__":
    main()
