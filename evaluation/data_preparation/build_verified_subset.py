"""Build a reproducible, provenance-aware History/Development candidate subset.

Final Test JSON and raw GSM8K test / HotpotQA validation records are never
opened. HotpotQA Development context is taken from the existing unified
Development artifact because its upstream validation file also supplies
identities used by the exposed Final Test partition.
"""

from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import operator
import random
import re
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Any

from datasets import load_from_disk


ROOT = Path(__file__).resolve().parents[2]
UNIFIED = ROOT / "evaluation/datasets/unified"
ADJUDICATION = ROOT / "evaluation/datasets/adjudication/v1"
RAW = ROOT / "evaluation/datasets/raw"
DEFAULT_SEED = 20261104
DEFAULT_OUTPUT = ROOT / f"evaluation/datasets/verified_subset/v1_seed_{DEFAULT_SEED}"
PARTITIONS = ("history", "development")
BENCHMARKS = ("GSM8K", "HotpotQA")
TARGET_QUESTIONS = 100
PARTITION_QUOTA = {"history": 80, "development": 20}
VALID_STATUSES = {"verified_correct", "verified_incorrect", "unresolved"}
SOURCE_VERSION = {
    "GSM8K": "openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866",
    "HotpotQA": "hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab",
}
GSM_ID = re.compile(r"gsm8k_(train|test)_(\d+)$")
FINAL_ANSWER = re.compile(r"####\s*(-?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:/[1-9]\d*)?)")
ARITHMETIC_ANNOTATION = re.compile(r"<<([^<>]+)>>")
TOKEN_RE = re.compile(r"\b\w+\b", re.UNICODE)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_paths(paths: list[Path]) -> dict[str, str]:
    return {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in paths}


def read_jsonl_prefix(path: Path, count: int = 5000) -> tuple[list[dict], str]:
    rows: list[dict] = []
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for line_no in range(1, count + 1):
            raw = handle.readline()
            if not raw:
                raise ValueError(f"{path} ended before expected History/Development prefix line {line_no}")
            digest.update(raw)
            rows.append(json.loads(raw))
    counts = collections.Counter(row.get("partition") for row in rows)
    if counts != {"history": 4000, "development": 1000}:
        raise ValueError(f"Unexpected History/Development boundary in {path}: {dict(counts)}")
    return rows, digest.hexdigest()


def norm_question(text: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def normalize_numeric(value: object) -> Fraction | None:
    """Parse integer, signed, comma-grouped, decimal, or fraction notation exactly."""
    text = str(value).strip().replace("−", "-").replace("$", "").replace(" ", "")
    if text.startswith("+"):
        text = text[1:]
    if "," in text:
        if not re.fullmatch(r"-?(?:\d{1,3}(?:,\d{3})+)(?:\.\d+)?(?:/[1-9]\d*)?", text):
            return None
        text = text.replace(",", "")
    try:
        if re.fullmatch(r"-?\d+/[1-9]\d*", text):
            numerator, denominator = text.split("/", 1)
            return Fraction(int(numerator), int(denominator))
        if re.fullmatch(r"-?(?:\d+(?:\.\d*)?|\.\d+)", text):
            return Fraction(Decimal(text))
    except (ValueError, InvalidOperation, ZeroDivisionError):
        return None
    return None


BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def eval_fraction_node(node: ast.AST) -> Fraction:
    if isinstance(node, ast.Expression):
        return eval_fraction_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Fraction(Decimal(str(node.value)))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = eval_fraction_node(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
        left = eval_fraction_node(node.left)
        right = eval_fraction_node(node.right)
        if isinstance(node.op, ast.Pow) and right.denominator != 1:
            raise ValueError("non-integer exponent")
        return BIN_OPS[type(node.op)](left, right)
    raise ValueError(f"unsupported arithmetic expression node: {type(node).__name__}")


def evaluate_arithmetic_expression(expression: str) -> Fraction:
    text = expression.replace("$", "").replace(",", "").replace("×", "*")
    text = re.sub(r"(?<=\d)[xX](?=\d)", "*", text)
    tree = ast.parse(text.strip(), mode="eval")
    return eval_fraction_node(tree)


def replay_gsm_solution(solution: str, gold: str) -> dict:
    annotations = ARITHMETIC_ANNOTATION.findall(solution)
    checked: list[dict] = []
    failures: list[dict] = []
    unsupported: list[dict] = []
    for annotation in annotations:
        if "=" not in annotation:
            unsupported.append({"annotation": annotation, "reason": "missing equality"})
            continue
        expression, stated_result = annotation.rsplit("=", 1)
        try:
            computed = evaluate_arithmetic_expression(expression)
            stated = normalize_numeric(stated_result)
            if stated is None:
                unsupported.append({"annotation": annotation, "reason": "unparseable stated result"})
            elif computed != stated:
                failures.append({"annotation": annotation, "computed": str(computed), "stated": str(stated)})
            else:
                checked.append({"expression": expression.strip(), "computed_result": str(computed)})
        except (ArithmeticError, SyntaxError, ValueError, InvalidOperation, ZeroDivisionError) as exc:
            unsupported.append({"annotation": annotation, "reason": str(exc)})
    match = FINAL_ANSWER.search(solution)
    final = normalize_numeric(match.group(1)) if match else None
    last_result = Fraction(checked[-1]["computed_result"]) if checked else None
    source_gold = normalize_numeric(gold)
    all_checks_pass = bool(annotations) and not failures and not unsupported and len(checked) == len(annotations)
    final_confirmed = all_checks_pass and final is not None and final == source_gold and last_result == source_gold
    return {
        "method": "independent_exact_arithmetic_replay_of_GSM8K_tagged_equations",
        "equation_count": len(annotations),
        "equations_checked": len(checked),
        "equations_failed": failures,
        "equations_unsupported": unsupported,
        "final_answer_marker_present": match is not None,
        "final_marker_equals_source_gold": final is not None and final == source_gold,
        "last_checked_equation_equals_source_gold": last_result is not None and last_result == source_gold,
        "status": "passed" if final_confirmed else "incomplete_or_failed",
        "checked_equations": checked,
    }


def hotpot_normalize(text: object) -> str:
    value = str(text).lower()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\b(a|an|the)\b", " ", value)
    return " ".join(value.split())


def token_f1(candidate: object, gold: object) -> float:
    pred = TOKEN_RE.findall(hotpot_normalize(candidate))
    ref = TOKEN_RE.findall(hotpot_normalize(gold))
    if not pred or not ref:
        return float(pred == ref)
    common = collections.Counter(pred) & collections.Counter(ref)
    overlap = sum(common.values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(pred)
    recall = overlap / len(ref)
    return 2 * precision * recall / (precision + recall)


def candidate_groups(rows: list[dict], benchmark: str) -> dict[str, dict]:
    groups: dict[str, dict] = {}
    for row in rows:
        key = norm_question(row.get("question"))
        if not key:
            raise ValueError(f"{benchmark} record has empty normalized question: {row.get('id')}")
        old = groups.get(key)
        if old is None or str(row["id"]) < str(old["id"]):
            groups[key] = row
    return groups


def choose_questions(rows_by_partition: dict[str, list[dict]], benchmark: str, seed: int) -> list[dict]:
    # Exact-normalized duplicate questions form one group across both partitions.
    all_groups: dict[str, dict] = {}
    for partition in PARTITIONS:
        for key, row in candidate_groups(rows_by_partition[partition], benchmark).items():
            current = all_groups.get(key)
            # Keep the first eligible partition in a deterministic order; candidate
            # variants remain together as the single selected question record.
            if current is None:
                all_groups[key] = {"partition": partition, "row": row, "group_id": key}
    pools = {
        partition: sorted(
            [entry for entry in all_groups.values() if entry["partition"] == partition],
            key=lambda entry: str(entry["row"]["id"]),
        )
        for partition in PARTITIONS
    }
    requested = dict(PARTITION_QUOTA)
    actual: dict[str, list[dict]] = {partition: [] for partition in PARTITIONS}
    for offset, partition in enumerate(PARTITIONS):
        n = min(requested[partition], len(pools[partition]))
        actual[partition] = random.Random(seed + offset).sample(pools[partition], n)
    missing = TARGET_QUESTIONS - sum(map(len, actual.values()))
    if missing > 0:
        selected_keys = {entry["group_id"] for items in actual.values() for entry in items}
        remainder = sorted(
            [entry for items in pools.values() for entry in items if entry["group_id"] not in selected_keys],
            key=lambda entry: (entry["partition"], str(entry["row"]["id"])),
        )
        extra = random.Random(seed + 97).sample(remainder, min(missing, len(remainder)))
        for entry in extra:
            actual[entry["partition"]].append(entry)
    chosen = [entry for partition in PARTITIONS for entry in actual[partition]]
    chosen.sort(key=lambda entry: (entry["partition"], str(entry["row"]["id"])))
    if len(chosen) > TARGET_QUESTIONS:
        chosen = chosen[:TARGET_QUESTIONS]
    return chosen


def read_unified_hdev() -> dict[str, dict[str, list[dict]]]:
    result = {benchmark: {partition: [] for partition in PARTITIONS} for benchmark in BENCHMARKS}
    for partition in PARTITIONS:
        path = UNIFIED / f"{partition}.json"
        rows = json.loads(path.read_text(encoding="utf-8"))
        for row in rows:
            if row.get("benchmark") in BENCHMARKS:
                result[row["benchmark"]][partition].append(row)
    return result


def load_adjudication_prefixes() -> tuple[dict[str, dict], dict[str, str]]:
    records: dict[str, dict] = {}
    prefix_hashes: dict[str, str] = {}
    for dataset in ("gsm8k", "hotpotqa"):
        rows, digest = read_jsonl_prefix(ADJUDICATION / f"{dataset}_adjudications.jsonl")
        prefix_hashes[dataset] = digest
        for row in rows:
            cid = row.get("candidate_id")
            if cid in records:
                raise ValueError(f"Duplicate candidate ID in adjudication prefix: {cid}")
            records[cid] = row
    return records, prefix_hashes


def make_supporting_evidence(row: dict, source_path: str) -> tuple[list[dict], bool]:
    contexts = row.get("context") or []
    by_title: dict[str, dict] = {str(item.get("title")): item for item in contexts if item.get("title")}
    facts = row.get("supporting_facts") or []
    evidence: list[dict] = []
    refs_available = bool(facts)
    for fact in facts:
        title = str(fact.get("title", ""))
        paragraph = by_title.get(title)
        if paragraph is None or not paragraph.get("text"):
            refs_available = False
            evidence.append({
                "kind": "supporting_fact_reference_unmatched_to_context",
                "title": title,
                "sentence_id": fact.get("sentence_id"),
                "source_path": source_path,
                "text": None,
            })
        else:
            evidence.append({
                "kind": "benchmark_context_paragraph_for_supporting_fact",
                "title": title,
                "sentence_id": fact.get("sentence_id"),
                "source_path": source_path,
                "text": paragraph["text"],
                "sentence_text_extracted": False,
            })
    return evidence, refs_available


def source_hashes(prefix_hashes: dict[str, str]) -> dict:
    gsm_train_dir = RAW / "gsm8k/train"
    hotpot_train_dir = RAW / "hotpotqa/train"
    paths = [
        UNIFIED / "history.json", UNIFIED / "development.json",
        *sorted((gsm_train_dir).glob("*")),
        *sorted((hotpot_train_dir).glob("*")),
    ]
    return {
        "files": hash_paths([path for path in paths if path.is_file()]),
        "adjudication_history_development_prefix_sha256": prefix_hashes,
    }


def build_records(chosen: dict[str, list[dict]], adjudication: dict[str, dict]) -> tuple[dict[str, list[dict]], dict]:
    gsm_raw = load_from_disk(str(RAW / "gsm8k/train"))
    hotpot_raw = load_from_disk(str(RAW / "hotpotqa/train"))
    hotpot_train_by_id = {str(row["id"]): row for row in hotpot_raw}
    output = {"gsm8k": [], "hotpotqa": []}
    skipped: list[dict] = []
    arithmetic_stats = collections.Counter()
    hotpot_stats = collections.Counter()

    for benchmark, dataset_key in (("GSM8K", "gsm8k"), ("HotpotQA", "hotpotqa")):
        for selected in chosen[benchmark]:
            example = selected["row"]
            partition = selected["partition"]
            source_path = f"evaluation/datasets/unified/{partition}.json"
            candidates = example.get("candidate_answers") or []
            if len(candidates) != 2:
                skipped.append({"dataset_id": example.get("id"), "benchmark": benchmark, "reason": "expected two candidate variants"})
                continue
            if len({str(c.get("answer")) for c in candidates}) != 2:
                skipped.append({"dataset_id": example.get("id"), "benchmark": benchmark, "reason": "candidate answer variants duplicate"})
                continue
            if benchmark == "GSM8K":
                match = GSM_ID.fullmatch(str(example.get("id", "")))
                if not match or match.group(1) != "train":
                    raise ValueError(f"Unexpected non-train GSM8K source ID in History/Development: {example.get('id')}")
                source_index = int(match.group(2))
                source = gsm_raw[source_index]
                if source.get("question") != example.get("question"):
                    raise ValueError(f"GSM8K question/source mismatch at {example['id']}")
                raw_solution = str(source["answer"])
                final_match = FINAL_ANSWER.search(raw_solution)
                if not final_match:
                    replay = {"status": "incomplete_or_failed", "reason": "source solution lacks final answer marker"}
                    gold = str(example.get("gold_answer", ""))
                else:
                    gold = final_match.group(1).replace(",", "")
                    replay = replay_gsm_solution(raw_solution, gold)
                if normalize_numeric(gold) != normalize_numeric(example.get("gold_answer")):
                    raise ValueError(f"GSM8K unified gold/source answer mismatch at {example['id']}")
                question_evidence = {
                    "kind": "original_GSM8K_worked_solution",
                    "source_path": "evaluation/datasets/raw/gsm8k/train",
                    "source_split": "train",
                    "source_row_index": source_index,
                    "final_answer_marker": final_match.group(0) if final_match else None,
                    "solution_sha256": hashlib.sha256(raw_solution.encode("utf-8")).hexdigest(),
                    "arithmetic_replay": replay,
                }
                gold_value = normalize_numeric(gold)
                for candidate_index, candidate in enumerate(candidates):
                    candidate_id = f"{example['id']}::candidate_{candidate_index}"
                    candidate_audit = adjudication.get(candidate_id)
                    expected_audit_status = "verified_correct" if candidate.get("source") == "benchmark_gold" else "unresolved"
                    if (
                        not candidate_audit
                        or candidate_audit.get("partition") != partition
                        or candidate_audit.get("source_id") != f"train:{source_index}"
                        or candidate_audit.get("adjudication_status") != expected_audit_status
                        or normalize_numeric(candidate_audit.get("source_gold_answer")) != normalize_numeric(gold)
                    ):
                        raise ValueError(f"Missing or inconsistent safe-prefix adjudication provenance for {candidate_id}")
                    answer = str(candidate.get("answer", ""))
                    candidate_value = normalize_numeric(answer)
                    same_as_verified_result = replay.get("status") == "passed" and candidate_value == gold_value
                    source_gold_candidate = candidate.get("source") == "benchmark_gold"
                    if same_as_verified_result:
                        status = "verified_correct"
                        method = "benchmark_source_match_plus_independent_arithmetic_replay"
                        rationale = "Candidate is numerically equivalent to the source final answer; all tagged worked-solution equations were independently recomputed and the final checked result matches. This confirms the benchmark answer and arithmetic consistency, not an independent human re-solve of the word-problem interpretation."
                        certainty = "high_for_benchmark_numeric_answer"
                        unresolved_reason = None
                    else:
                        status = "unresolved"
                        method = "numeric_normalization_and_worked_solution_arithmetic_diagnostic"
                        rationale = "Candidate differs from the benchmark/source-derived numeric result or the displayed derivation could not be fully replayed. Numeric difference and candidate construction alone do not establish semantic incorrectness; no independent human decision was entered."
                        certainty = "not_established"
                        unresolved_reason = "requires independent semantic review or complete arithmetic evidence"
                    evidence = [question_evidence]
                    record = {
                        "candidate_id": candidate_id,
                        "dataset_id": str(example["id"]),
                        "benchmark": benchmark,
                        "dataset_version": SOURCE_VERSION[benchmark],
                        "partition": partition,
                        "question": example["question"],
                        "candidate_answer": answer,
                        "candidate_source": candidate.get("source"),
                        "candidate_generation_method": candidate.get("source"),
                        "gold_answer": gold,
                        "correctness_status": status,
                        "validation_method": method,
                        "validation_basis": "benchmark-source match and exact arithmetic replay of displayed equations" if status == "verified_correct" else "diagnostic only; no incorrectness inference",
                        "validation_evidence": evidence,
                        "evidence_provenance": {
                            "source_file": source_path,
                            "raw_source_path": "evaluation/datasets/raw/gsm8k/train",
                            "source_split": "train",
                            "source_row_index": source_index,
                            "source_solution_sha256": question_evidence["solution_sha256"],
                        },
                        "validation_rationale": rationale,
                        "validation_confidence_category": certainty,
                        "unresolved_reason": unresolved_reason,
                        "numeric_candidate_equals_gold": candidate_value is not None and candidate_value == gold_value,
                        "numeric_normalization": {"candidate_fraction": str(candidate_value) if candidate_value is not None else None, "gold_fraction": str(gold_value) if gold_value is not None else None},
                        "independent_human_review": False,
                        "source_candidate_index": candidate_index,
                        "related_group_id": f"gsm8k-q-{hashlib.sha256(selected['group_id'].encode()).hexdigest()[:16]}",
                    }
                    output[dataset_key].append(record)
                    arithmetic_stats[f"{status}:{candidate.get('source')}"] += 1
            else:
                source_id = str(example.get("id", "")).removeprefix("hotpot_")
                source_gold = str(example.get("gold_answer", ""))
                if partition == "history":
                    source = hotpot_train_by_id.get(source_id)
                    if source is None:
                        raise ValueError(f"HotpotQA History ID missing from raw train source: {source_id}")
                    if source.get("question") != example.get("question") or str(source.get("answer", "")) != source_gold:
                        raise ValueError(f"HotpotQA History source mismatch: {source_id}")
                    raw_context = source.get("context") or {}
                    raw_titles = raw_context.get("title") or []
                    raw_sentences = raw_context.get("sentences") or []
                    context = [{"title": title, "text": " ".join(sentences)} for title, sentences in zip(raw_titles, raw_sentences)]
                    support = [{"title": title, "sentence_id": sentence_id} for title, sentence_id in zip((source.get("supporting_facts") or {}).get("title", []), (source.get("supporting_facts") or {}).get("sent_id", []))]
                    unified_context = example.get("context") or []
                    if context != unified_context or support != (example.get("supporting_facts") or []):
                        raise ValueError(f"HotpotQA History context/support mismatch with raw source: {source_id}")
                    evidence_source = "evaluation/datasets/raw/hotpotqa/train"
                else:
                    # This exact development record is used instead of loading
                    # the mixed upstream validation split, which contains rows
                    # represented in the exposed Final Test partition.
                    source = None
                    context = example.get("context") or []
                    support = example.get("supporting_facts") or []
                    evidence_source = source_path
                    source_gold_record = adjudication.get(f"{example['id']}::candidate_0")
                    if not source_gold_record or source_gold_record.get("source_gold_answer") is None or hotpot_normalize(source_gold_record["source_gold_answer"]) != hotpot_normalize(source_gold):
                        raise ValueError(f"HotpotQA Development source-answer provenance mismatch: {source_id}")
                evidence, supports_available = make_supporting_evidence({"context": context, "supporting_facts": support}, evidence_source)
                if not evidence or not supports_available:
                    evidence_status = "supporting_fact_context_incomplete"
                else:
                    evidence_status = "supporting_fact_context_present"
                for candidate_index, candidate in enumerate(candidates):
                    candidate_id = f"{example['id']}::candidate_{candidate_index}"
                    candidate_audit = adjudication.get(candidate_id)
                    expected_audit_status = "verified_correct" if candidate.get("source") == "benchmark_gold" else "unresolved"
                    if (
                        not candidate_audit
                        or candidate_audit.get("partition") != partition
                        or candidate_audit.get("source_id") != source_id
                        or candidate_audit.get("adjudication_status") != expected_audit_status
                        or hotpot_normalize(candidate_audit.get("source_gold_answer")) != hotpot_normalize(source_gold)
                    ):
                        raise ValueError(f"Missing safe-prefix source provenance for {candidate_id}")
                    answer = str(candidate.get("answer", ""))
                    exact_match = hotpot_normalize(answer) == hotpot_normalize(source_gold)
                    f1 = token_f1(answer, source_gold)
                    source_gold_match = candidate.get("source") == "benchmark_gold" and exact_match
                    coincidental_gold_match = candidate.get("source") != "benchmark_gold" and exact_match
                    if (source_gold_match or coincidental_gold_match) and supports_available:
                        status = "verified_correct"
                        method = "benchmark_source_answer_match_with_supporting_context_provenance"
                        rationale = "Candidate matches the canonical HotpotQA source answer under the documented normalization, and all supplied supporting-fact titles map to non-empty benchmark context paragraphs. This is benchmark-source verification with context provenance, not an independent human semantic adjudication."
                        certainty = "high_for_benchmark_answer_match"
                        unresolved_reason = None
                    else:
                        status = "unresolved"
                        method = "normalized_exact_match_and_token_f1_diagnostics"
                        rationale = "Exact match and token F1 are diagnostic comparisons only. A mismatch or low F1 does not prove factual incorrectness; no independent human semantic judgment was entered."
                        certainty = "not_established"
                        unresolved_reason = "requires independent question-conditioned factual adjudication" if not exact_match else "supporting context/fact provenance incomplete"
                    record = {
                        "candidate_id": candidate_id,
                        "dataset_id": str(example["id"]),
                        "benchmark": benchmark,
                        "dataset_version": SOURCE_VERSION[benchmark],
                        "partition": partition,
                        "question": example["question"],
                        "candidate_answer": answer,
                        "candidate_source": candidate.get("source"),
                        "candidate_generation_method": candidate.get("source"),
                        "gold_answer": source_gold,
                        "correctness_status": status,
                        "validation_method": method,
                        "validation_basis": "benchmark source-answer match; paragraph evidence availability recorded separately" if status == "verified_correct" else "diagnostic only; no incorrectness inference",
                        "validation_evidence": evidence,
                        "evidence_provenance": {
                            "source_file": source_path,
                            "raw_source_path": "evaluation/datasets/raw/hotpotqa/train" if partition == "history" else "existing unified Development record; raw mixed validation split deliberately not opened",
                            "source_id": source_id,
                            "source_split": "train" if partition == "history" else "validation (identified from existing preprocessing provenance; records not reopened)",
                            "context_hashes": [hashlib.sha256(str(item.get("text", "")).encode("utf-8")).hexdigest() for item in context],
                            "supporting_facts": support,
                            "supporting_context_status": evidence_status,
                        },
                        "validation_rationale": rationale,
                        "validation_confidence_category": certainty,
                        "unresolved_reason": unresolved_reason,
                        "diagnostics": {
                            "normalized_exact_match_to_gold": exact_match,
                            "token_f1_to_gold": round(f1, 8),
                            "metrics_are_diagnostic_not_label_rules": True,
                        },
                        "independent_human_review": False,
                        "source_candidate_index": candidate_index,
                        "related_group_id": f"hotpotqa-q-{hashlib.sha256(selected['group_id'].encode()).hexdigest()[:16]}",
                    }
                    output[dataset_key].append(record)
                    hotpot_stats[f"{status}:{candidate.get('source')}"] += 1
    return output, {"gsm8k": dict(arithmetic_stats), "hotpotqa": dict(hotpot_stats), "skipped_examples": skipped}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize(records: dict[str, list[dict]], selected: dict[str, list[dict]], seed: int, diagnostics: dict) -> dict:
    summary: dict[str, Any] = {"seed": seed, "benchmarks": {}, "combined": {"questions": 0, "candidates": 0, "statuses": {status: 0 for status in sorted(VALID_STATUSES)}}}
    for dataset, rows in records.items():
        questions = selected["GSM8K" if dataset == "gsm8k" else "HotpotQA"]
        statuses = collections.Counter(row["correctness_status"] for row in rows)
        partitions = collections.Counter(row["partition"] for row in rows)
        source_counts = collections.Counter(row["candidate_source"] for row in rows)
        if dataset == "gsm8k":
            question_rows = [row for row in rows if row.get("source_candidate_index") == 0]
            validation_diagnostics = {
                "questions_with_complete_arithmetic_replay": sum(row["validation_evidence"][0].get("arithmetic_replay", {}).get("status") == "passed" for row in question_rows),
                "questions_with_incomplete_or_unlinked_arithmetic_replay": sum(row["validation_evidence"][0].get("arithmetic_replay", {}).get("status") != "passed" for row in question_rows),
                "generated_candidates_left_unresolved": sum(row.get("candidate_source") == "synthetic_numeric_perturbation" and row.get("correctness_status") == "unresolved" for row in rows),
                "verified_incorrect_by_automated_checks": 0,
            }
        else:
            borrowed = [row for row in rows if row.get("candidate_source") == "synthetic_cross_example_answer"]
            validation_diagnostics = {
                "condition": "benchmark_context_assisted; not shared-corpus retrieval",
                "borrowed_candidates_exact_match_to_gold": sum(row["diagnostics"]["normalized_exact_match_to_gold"] for row in borrowed),
                "borrowed_candidate_mean_token_f1": round(sum(row["diagnostics"]["token_f1_to_gold"] for row in borrowed) / len(borrowed), 8) if borrowed else None,
                "borrowed_candidates_left_unresolved": sum(row["correctness_status"] == "unresolved" for row in borrowed),
                "verified_incorrect_by_automated_checks": 0,
            }
        summary["benchmarks"][dataset] = {
            "questions_selected": len(questions),
            "candidates": len(rows),
            "verified_correct": statuses.get("verified_correct", 0),
            "verified_incorrect": statuses.get("verified_incorrect", 0),
            "unresolved": statuses.get("unresolved", 0),
            "partition_question_counts": dict(collections.Counter(item["partition"] for item in questions)),
            "partition_candidate_counts": dict(partitions),
            "candidate_generation_method_counts": dict(source_counts),
            "validation_method_counts": dict(collections.Counter(row["validation_method"] for row in rows)),
            "diagnostic_counts": diagnostics.get(dataset),
            "validation_diagnostics": validation_diagnostics,
        }
        summary["combined"]["questions"] += len(questions)
        summary["combined"]["candidates"] += len(rows)
        for status, count in statuses.items():
            summary["combined"]["statuses"][status] = summary["combined"]["statuses"].get(status, 0) + count
    return summary


def validate_output(directory: Path) -> dict:
    manifest = json.loads((directory / "subset_manifest.json").read_text(encoding="utf-8"))
    gsm = read_jsonl(directory / "gsm8k_verified.jsonl")
    hotpot = read_jsonl(directory / "hotpotqa_verified.jsonl")
    by_dataset = {"gsm8k": gsm, "hotpotqa": hotpot}
    all_ids: list[str] = []
    result = {"passed": True, "checks": {}, "benchmarks": {}}
    source_pool = read_unified_hdev()
    deterministic_selection_matches_seed = {}
    for offset, benchmark in enumerate(BENCHMARKS):
        reproduced = choose_questions(source_pool[benchmark], benchmark, manifest["random_seed"] + offset * 10)
        reproduced_ids = [str(entry["row"]["id"]) for entry in reproduced]
        deterministic_selection_matches_seed[benchmark.lower()] = reproduced_ids == manifest["selected_question_ids"][benchmark]
        if not deterministic_selection_matches_seed[benchmark.lower()]:
            raise ValueError(f"{benchmark}: selected IDs are not reproducible from the manifest seed")
    for dataset, rows in by_dataset.items():
        candidate_ids = [row.get("candidate_id") for row in rows]
        dataset_ids = [row.get("dataset_id") for row in rows]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError(f"{dataset}: duplicate candidate IDs")
        question_ids = list(dict.fromkeys(dataset_ids))
        expected_questions = manifest["selected_question_counts"]["GSM8K" if dataset == "gsm8k" else "HotpotQA"]
        if len(question_ids) != expected_questions:
            raise ValueError(f"{dataset}: selected question count differs from manifest")
        if any(count != 2 for count in collections.Counter(dataset_ids).values()):
            raise ValueError(f"{dataset}: each selected question must retain both candidate variants")
        group_ids = [row.get("related_group_id") for row in rows]
        groups_by_question = {row["dataset_id"]: row.get("related_group_id") for row in rows}
        if len(set(groups_by_question.values())) != len(groups_by_question):
            raise ValueError(f"{dataset}: duplicate exact-question group selected")
        expected_candidate_ids = manifest["selected_candidate_ids"][dataset]
        if candidate_ids != expected_candidate_ids:
            raise ValueError(f"{dataset}: candidate IDs differ from manifest")
        if any(row.get("partition") not in PARTITIONS for row in rows):
            raise ValueError(f"{dataset}: Final Test/unknown partition present")
        if any(row.get("correctness_status") not in VALID_STATUSES for row in rows):
            raise ValueError(f"{dataset}: invalid correctness status")
        for row in rows:
            if not row.get("dataset_id") or not row.get("dataset_version") or not row.get("evidence_provenance"):
                raise ValueError(f"{row.get('candidate_id')}: missing source provenance")
            if row["correctness_status"] == "verified_incorrect" and row.get("candidate_source") != "benchmark_gold":
                raise ValueError(f"{row.get('candidate_id')}: synthetic/borrowed candidate cannot be automatically marked incorrect")
            if row["correctness_status"].startswith("verified_") and not (row.get("validation_evidence") and row.get("validation_rationale") and row.get("validation_method")):
                raise ValueError(f"{row.get('candidate_id')}: verified label lacks evidence/method/rationale")
            if row["correctness_status"] == "unresolved" and row.get("unresolved_reason") is None:
                raise ValueError(f"{row.get('candidate_id')}: unresolved reason missing")
        all_ids.extend(candidate_ids)
        result["benchmarks"][dataset] = {
            "questions": len(question_ids),
            "candidates": len(rows),
            "verified_correct": sum(r["correctness_status"] == "verified_correct" for r in rows),
            "verified_incorrect": sum(r["correctness_status"] == "verified_incorrect" for r in rows),
            "unresolved": sum(r["correctness_status"] == "unresolved" for r in rows),
            "partition_questions": manifest["selected_partition_counts"]["GSM8K" if dataset == "gsm8k" else "HotpotQA"],
        }
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Candidate IDs overlap between benchmarks")
    if manifest.get("final_test_included") is not False or manifest.get("final_test_records_read") is not False:
        raise ValueError("Manifest does not confirm Final Test exclusion/non-access")
    result["checks"] = {
        "candidate_ids_unique": True,
        "question_groups_unique_and_two_variants_retained": True,
        "history_development_only": True,
        "final_test_read": False,
        "verified_labels_have_basis": True,
        "unresolved_not_counted_incorrect": True,
        "synthetic_not_automatically_incorrect": True,
        "source_provenance_present": True,
        "deterministic_selection_matches_seed": deterministic_selection_matches_seed,
            "selected_ids_match_manifest": {
            "gsm8k": list(dict.fromkeys(row["dataset_id"] for row in gsm)) == manifest["selected_question_ids"]["GSM8K"] and [row["candidate_id"] for row in gsm] == manifest["selected_candidate_ids"]["gsm8k"],
            "hotpotqa": list(dict.fromkeys(row["dataset_id"] for row in hotpot)) == manifest["selected_question_ids"]["HotpotQA"] and [row["candidate_id"] for row in hotpot] == manifest["selected_candidate_ids"]["hotpotqa"],
        },
    }
    if not all(result["checks"]["selected_ids_match_manifest"].values()):
        raise ValueError("Output question IDs do not match the manifest selection")
    return result


def build(seed: int, output_dir: Path) -> dict:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty subset directory: {output_dir}")
    unified = read_unified_hdev()
    adjudication, prefix_hashes = load_adjudication_prefixes()
    selected = {
        benchmark: choose_questions(unified[benchmark], benchmark, seed + offset * 10)
        for offset, benchmark in enumerate(BENCHMARKS)
    }
    # No Final Test partition path is constructed or opened in this workflow.
    built, diagnostics = build_records(selected, adjudication)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "gsm8k_verified.jsonl", built["gsm8k"])
    write_jsonl(output_dir / "hotpotqa_verified.jsonl", built["hotpotqa"])
    selected_ids = {
        benchmark: [str(entry["row"]["id"]) for entry in selected[benchmark]]
        for benchmark in BENCHMARKS
    }
    partition_counts = {
        benchmark: dict(collections.Counter(entry["partition"] for entry in selected[benchmark]))
        for benchmark in BENCHMARKS
    }
    manifest = {
        "subset_version": "verified-candidate-subset-v1",
        "created_date": date.today().isoformat(),
        "random_seed": seed,
        "target_questions_per_benchmark": TARGET_QUESTIONS,
        "selection_method": "partition-stratified random sample without replacement from exact-normalized-question groups; target 80 History and 20 Development per benchmark; group variants remain together",
        "selected_question_counts": {benchmark: len(selected[benchmark]) for benchmark in BENCHMARKS},
        "selected_partition_counts": partition_counts,
        "selected_question_ids": selected_ids,
        "selected_candidate_ids": {dataset: [row["candidate_id"] for row in rows] for dataset, rows in built.items()},
        "candidate_counts": {dataset: len(rows) for dataset, rows in built.items()},
        "candidate_methods": {
            "GSM8K": {"benchmark_gold", "synthetic_numeric_perturbation"},
            "HotpotQA": {"benchmark_gold", "synthetic_cross_example_answer"},
        },
        "related_grouping": "exact normalized question within benchmark across History and Development; broader semantic/source-document relatedness is not fully identifiable in current unified schema",
        "partitions_allowed": list(PARTITIONS),
        "final_test_included": False,
        "final_test_records_read": False,
        "source_paths": {
            "unified_history": "evaluation/datasets/unified/history.json",
            "unified_development": "evaluation/datasets/unified/development.json",
            "gsm8k_raw_train_only": "evaluation/datasets/raw/gsm8k/train",
            "hotpotqa_raw_train_only": "evaluation/datasets/raw/hotpotqa/train",
            "hotpotqa_development_context": "existing unified Development rows; raw mixed validation split not opened",
            "candidate_adjudication_source": "evaluation/datasets/adjudication/v1/{gsm8k,hotpotqa}_adjudications.jsonl (first 5,000 History/Development records only)",
        },
        "source_versions": SOURCE_VERSION,
        "source_hashes": source_hashes(prefix_hashes),
        "validation_policy": {
            "benchmark_source_match_is_not_human_adjudication": True,
            "synthetic_or_borrowed_nonmatch_stays_unresolved": True,
            "hotpot_condition": "benchmark-context-assisted; not shared-corpus retrieval",
            "framework_used_as_judge": False,
        },
        "skipped_examples": diagnostics["skipped_examples"],
    }
    manifest["candidate_methods"] = {
        "GSM8K": ["benchmark_gold", "synthetic_numeric_perturbation"],
        "HotpotQA": ["benchmark_gold", "synthetic_cross_example_answer"],
    }
    (output_dir / "subset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = summarize(built, selected, seed, diagnostics)
    (output_dir / "validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readme = README
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    validation = validate_output(output_dir)
    validation["arithmetic_replay"] = {
        "GSM8K_candidates": len(built["gsm8k"]),
        "GSM8K_solution_replay_passed_questions": len({r["dataset_id"] for r in built["gsm8k"] if r["validation_evidence"][0].get("arithmetic_replay", {}).get("status") == "passed"}),
        "HotpotQA_context_assisted": True,
        "hotpot_exact_match_and_token_f1_are_diagnostic_only": True,
    }
    (output_dir / "validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "quality_check.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return validation


README = """# Provenance-aware verified candidate subset\n\nThis directory contains a reproducible History/Development subset for GSM8K and HotpotQA. Candidate status is `verified_correct`, `verified_incorrect`, or `unresolved`. Benchmark-source matching is documented separately from independent human review. Synthetic/borrowed candidates that are not independently established remain unresolved; no candidate is labeled incorrect solely because it differs from gold.\n\nGSM8K uses the raw training worked solution and an exact-rational replay of its tagged arithmetic equations. This checks the source derivation's arithmetic consistency; it does not claim independent human re-solving of every word-problem interpretation. HotpotQA uses the per-question benchmark context and supporting facts. Exact match and token F1 are diagnostics only. This is benchmark-context-assisted evaluation, not retrieval from the shared 13,083-article corpus.\n\n`subset_manifest.json` records seed, selected IDs, partition counts, source versions and hashes. `validation_summary.json` reports candidate label and method counts. `quality_check.json` contains structural validation results. Final Test records were not read or selected.\n"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    build_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--subset-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.command == "build":
        result = build(args.seed, args.output_dir)
    else:
        result = validate_output(args.subset_dir)
        summary_records = {
            "gsm8k": read_jsonl(args.subset_dir / "gsm8k_verified.jsonl"),
            "hotpotqa": read_jsonl(args.subset_dir / "hotpotqa_verified.jsonl"),
        }
        manifest = json.loads((args.subset_dir / "subset_manifest.json").read_text(encoding="utf-8"))
        selected_records = {
            "GSM8K": [{"id": item, "partition": part} for part, ids in manifest["selected_partition_counts"]["GSM8K"].items() for item in manifest["selected_question_ids"]["GSM8K"] if any(row["dataset_id"] == item and row["partition"] == part for row in summary_records["gsm8k"])],
            "HotpotQA": [{"id": item, "partition": part} for part, ids in manifest["selected_partition_counts"]["HotpotQA"].items() for item in manifest["selected_question_ids"]["HotpotQA"] if any(row["dataset_id"] == item and row["partition"] == part for row in summary_records["hotpotqa"])],
        }
        diagnostics = {}
        for dataset, rows in summary_records.items():
            if dataset == "gsm8k":
                diagnostics[dataset] = dict(collections.Counter(f"{row['correctness_status']}:{row['candidate_source']}" for row in rows))
            else:
                diagnostics[dataset] = dict(collections.Counter(f"{row['correctness_status']}:{row['candidate_source']}" for row in rows))
        refreshed = summarize(summary_records, selected_records, manifest["random_seed"], diagnostics)
        (args.subset_dir / "validation_summary.json").write_text(json.dumps(refreshed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.subset_dir / "quality_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
