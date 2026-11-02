"""Dataset adapters for the baseline validation experiment.

These functions only reshape one development-set example into the existing
``ValidationRequest`` fields. They do not call verifiers and they do not
change benchmark files.
"""

from __future__ import annotations

from dataclasses import dataclass, field


ELIGIBLE_BENCHMARKS = ("FEVER", "HotpotQA", "GSM8K")
SKIPPED_BENCHMARKS = {
    "MultiNLI": (
        "MultiNLI is a premise/hypothesis entailment task. The validation "
        "interface scores whether a candidate answer is acceptable for a "
        "question. Mapping the hypothesis to an answer and the premise to "
        "reference context would score semantic similarity, which is not "
        "NLI correctness. The example is skipped rather than forced into "
        "that mapping."
    ),
}


@dataclass(frozen=True)
class ExperimentInstance:
    example_id: str
    instance_id: str
    benchmark: str
    task_type: str | None
    question: str
    candidate_answer: str
    context: str | None
    gold_label: str
    gold_role: str
    candidate_index: int | None = None
    candidate_source: str | None = None
    evaluation_note: str | None = None
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SkippedExample:
    example_id: str
    benchmark: str
    reason: str


def hotpot_context(example: dict) -> str | None:
    """Join only this example's own paragraphs. Distractors stay included."""
    paragraphs = example.get("context") or []
    blocks = []
    for paragraph in paragraphs:
        if not isinstance(paragraph, dict):
            continue
        title = str(paragraph.get("title") or "").strip()
        text = str(paragraph.get("text") or "").strip()
        if not title and not text:
            continue
        blocks.append(f"{title}\n{text}".strip())
    if not blocks:
        return None
    return "\n\n".join(blocks)


def iter_dataset(rows: list[dict]):
    """Yield ``ExperimentInstance`` or ``SkippedExample`` in file order."""
    for row in rows:
        benchmark = row.get("benchmark")
        example_id = str(row.get("id"))
        if benchmark in SKIPPED_BENCHMARKS:
            yield SkippedExample(example_id, benchmark, SKIPPED_BENCHMARKS[benchmark])
            continue
        if benchmark == "FEVER":
            yield from _fever(row)
            continue
        if benchmark == "GSM8K":
            yield from _candidates(row, context=None)
            continue
        if benchmark == "HotpotQA":
            yield from _candidates(row, context=hotpot_context(row))
            continue
        yield SkippedExample(
            example_id,
            str(benchmark),
            f"No adapter is defined for benchmark {benchmark!r}.",
        )


def _fever(row: dict):
    claim = str(row.get("claim") or "").strip()
    label = row.get("label")
    if not claim or label not in {"SUPPORTS", "REFUTES", "NOT ENOUGH INFO"}:
        yield SkippedExample(
            str(row.get("id")),
            "FEVER",
            "FEVER example is missing a claim or has an unrecognized label.",
        )
        return
    if label == "SUPPORTS":
        role = "accept"
    elif label == "REFUTES":
        role = "reject"
    else:
        role = "abstain"
    note = (
        "The claim is both the analyzed question and the candidate answer. "
        "A statement answer is verified as that statement by the existing "
        "claim generator. The dataset stores Wikipedia titles and sentence "
        "ids, not evidence sentences, and those titles are not assumed to "
        "be present in the configured retrieval corpus. No evidence text "
        "is copied into context."
    )
    yield ExperimentInstance(
        example_id=str(row["id"]),
        instance_id=str(row["id"]),
        benchmark="FEVER",
        task_type=row.get("task_type"),
        question=claim,
        candidate_answer=claim,
        context=None,
        gold_label=label,
        gold_role=role,
        evaluation_note=note,
        extra={
            "evidence_url_count": len(row.get("evidence_urls") or []),
            "evidence_sentences_available": False,
        },
    )


def _candidates(row: dict, context: str | None):
    benchmark = row["benchmark"]
    candidates = row.get("candidate_answers")
    if not isinstance(candidates, list) or not candidates:
        yield SkippedExample(
            str(row.get("id")),
            benchmark,
            "Example has no candidate_answers list.",
        )
        return
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict) or "answer" not in candidate:
            yield SkippedExample(
                str(row.get("id")),
                benchmark,
                f"candidate_answers[{index}] has no answer.",
            )
            continue
        expected = candidate.get("expected_correct")
        if not isinstance(expected, bool):
            yield SkippedExample(
                str(row.get("id")),
                benchmark,
                f"candidate_answers[{index}] has no boolean expected_correct.",
            )
            continue
        yield ExperimentInstance(
            example_id=str(row["id"]),
            instance_id=f"{row['id']}::candidate_{index}",
            benchmark=benchmark,
            task_type=row.get("task_type"),
            question=str(row.get("question") or ""),
            candidate_answer=str(candidate["answer"]),
            context=context,
            gold_label="correct_candidate" if expected else "incorrect_candidate",
            gold_role="accept" if expected else "reject",
            candidate_index=index,
            candidate_source=candidate.get("source"),
            evaluation_note=(
                "HotpotQA context is this example's own paragraphs, including "
                "distractors. The evidence verifier does not read request "
                "context; it retrieves from the configured corpus."
                if benchmark == "HotpotQA"
                else "GSM8K uses the question and one stored candidate answer. "
                "Context is null because the example has no reference passage."
            ),
            extra={
                "gold_answer": row.get("gold_answer"),
                "context_characters": len(context) if context else 0,
            },
        )


def prediction_matches(gold_role: str, framework_status: str) -> bool:
    """Score a framework status against an adapter gold role.

    ``uncertain`` and ``unknown`` are abstentions. They match only a gold
    abstention. They are not treated as rejection.
    """
    abstained = framework_status in {"uncertain", "unknown"}
    if gold_role == "abstain":
        return abstained
    if abstained:
        return False
    if gold_role == "accept":
        return framework_status == "passed"
    if gold_role == "reject":
        return framework_status == "failed"
    raise ValueError(f"unknown gold role {gold_role!r}")
