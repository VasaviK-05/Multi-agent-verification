"""Label-free Experiment 1 preparation: Final Test contamination, Development balance, v2 pool plan.

Never opens custodian label directories and never loads raw ``answer`` or
``supporting_facts`` columns. Outputs are write-once; ``validate`` recomputes them.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Any, Iterable

from evaluation.data_preparation.final_test_workflow import (
    DEVELOPMENT, EXPOSURE_METHOD, HISTORY, ROOT, canonical_bytes, context_hashes, exposure_files,
    norm_question, read_records, sha256_bytes, sha256_file,
)

VERSION = "experiment1_preparation_v1"
OUTPUT = ROOT / "evaluation/datasets/experiment1_preparation" / VERSION
PROVISIONAL_DIR = ROOT / "evaluation/datasets/final_test_research_v1_eval_v1"
EXPOSED_FINAL_TEST_FILES = ("evaluation/datasets/unified/final_test.json", "evaluation/datasets/processed/final_test.json")
RAW = {("GSM8K", "train"): "evaluation/datasets/raw/gsm8k/train", ("GSM8K", "test"): "evaluation/datasets/raw/gsm8k/test",
       ("HotpotQA", "validation"): "evaluation/datasets/raw/hotpotqa/validation",
       ("HotpotQA", "train"): "evaluation/datasets/raw/hotpotqa/train"}
LABEL_FREE_COLUMNS = {"GSM8K": ["question"], "HotpotQA": ["id", "question", "context"]}
STATUSES = ("verified_correct", "verified_incorrect", "unresolved")


def relative(path: Path, root: Path = ROOT) -> str:
    return str(path.relative_to(root)).replace("\\", "/") if path.is_relative_to(root) else str(path)


def category(name: str) -> str:
    if name in EXPOSED_FINAL_TEST_FILES:
        return "exposed_final_test"
    if name.startswith("evaluation/results/baseline/"):
        return "baseline_outputs"
    if name.startswith("evaluation/results/"):
        return "verifier_outputs"
    if "development" in name:
        return "development_files"
    if "history" in name:
        return "history_files"
    return "other_derived_datasets"


def scan(files: Iterable[Path], root: Path = ROOT) -> tuple[dict[str, set[str]], set[str], dict[str, str]]:
    """Questions -> files, exact paragraph hashes, and per-file SHA-256 for every scanned file."""
    questions: dict[str, set[str]] = collections.defaultdict(set)
    contexts: set[str] = set()
    digests = {}
    for path in files:
        name = relative(path, root)
        digests[name] = sha256_file(path)
        for record in read_records(path):
            stack = [record]
            while stack:
                value = stack.pop()
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key == "question" and isinstance(item, str) and norm_question(item):
                            questions[norm_question(item)].add(name)
                        elif key in {"context", "evidence_context"}:
                            contexts |= context_hashes(item)
                        else:
                            stack.append(item)
                elif isinstance(value, list):
                    stack.extend(value)
    return dict(questions), contexts, digests


def contamination_audit(roster: Path, manifest: Path, index: dict[str, set[str]], digests: dict[str, str],
                        root: Path = ROOT) -> dict:
    """Content-level overlap of a frozen Final Test roster with every scanned file (question text only)."""
    groups = []
    totals = collections.Counter()
    for row in read_records(roster):
        benchmark = row["benchmark"]
        totals[benchmark] += 1
        files = sorted(index.get(norm_question(row["question"]), ()))
        if files:
            groups.append({"group_id": row["related_group_id"], "benchmark": benchmark,
                           "source_id": row["source_id"], "files": files})
    groups.sort(key=lambda g: g["group_id"])
    by_file: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    by_category: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for group in groups:
        for name in group["files"]:
            by_file[name][group["benchmark"]] += 1
        for name in {category(f) for f in group["files"]}:
            by_category[name][group["benchmark"]] += 1
    contaminated = collections.Counter(g["benchmark"] for g in groups)
    return {
        "method": EXPOSURE_METHOD,
        "target": {"evaluation_roster": relative(roster, root), "evaluation_roster_sha256": sha256_file(roster),
                   "manifest_sha256": json.loads(manifest.read_text(encoding="utf-8")).get("manifest_sha256"),
                   "groups_by_benchmark": dict(sorted(totals.items()))},
        "files_checked": len(digests), "file_sha256": dict(sorted(digests.items())),
        "contaminated_groups_by_benchmark": dict(sorted(contaminated.items())),
        "contaminated_group_count": len(groups),
        "clean_groups_by_benchmark": {b: totals[b] - contaminated[b] for b in sorted(totals)},
        "by_category": {k: dict(sorted(v.items())) for k, v in sorted(by_category.items())},
        "by_file": {k: dict(sorted(v.items())) for k, v in sorted(by_file.items())},
        "groups": groups,
        "verdict": "CONTAMINATED" if groups else "NO_EXACT_QUESTION_OVERLAP",
        "custodian_labels_opened": False,
        "limitations": ["Exact normalized question text; paraphrases are not detected.",
                        "Shared passages are reported for the v2 pool plan, not for this verdict."],
    }


def development_label_balance(paths: dict[str, Path], root: Path = ROOT) -> dict:
    """Candidate label counts per role and benchmark; flags benchmarks with no verified incorrect class."""
    roles = {}
    for role, path in sorted(paths.items()):
        counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        for row in read_records(path):
            counts[row["benchmark"]][row.get("correctness_status")] += 1
        roles[role] = {"path": relative(path, root), "sha256": sha256_file(path),
                       "counts": {b: {s: c[s] for s in STATUSES} for b, c in sorted(counts.items())}}
    lacking = {role: sorted(b for b, c in data["counts"].items() if not c["verified_incorrect"])
               for role, data in roles.items()}
    return {"roles": roles, "benchmarks_without_verified_incorrect": lacking,
            "binary_estimable_false_acceptance": {role: sorted(b for b, c in data["counts"].items()
                                                               if c["verified_correct"] and c["verified_incorrect"])
                                                  for role, data in roles.items()},
            "unresolved_policy": "excluded from binary metrics; never counted as incorrect"}


def pool(benchmark: str, split: str, rows: Iterable[dict], questions: dict[str, set[str]], contexts: set[str],
         seen: set[str]) -> dict:
    """Eligible label-free source rows: unexposed question, no exposed paragraph, no duplicate."""
    reasons = collections.Counter()
    eligible = []
    total = 0
    for index, row in enumerate(rows):
        total += 1
        normalized = norm_question(row["question"])
        source_id = str(row.get("id") or f"{benchmark.lower()}_{split}_{index:05d}")
        row_reasons = []
        if not normalized:
            row_reasons.append("empty_question")
        elif normalized in questions:
            row_reasons.append("previously_exposed_question")
        if normalized in seen:
            row_reasons.append("duplicate_normalized_question")
        if contexts and context_hashes(row.get("context")) & contexts:
            row_reasons.append("exposed_exact_paragraph")
        seen.add(normalized)
        reasons.update(row_reasons)
        if not row_reasons:
            eligible.append(source_id)
    return {"source_rows": total, "eligible": len(eligible), "excluded": total - len(eligible),
            "exclusion_reason_counts": dict(sorted(reasons.items())),
            "eligible_source_id_sha256": sha256_bytes(canonical_bytes(sorted(eligible)))}


def raw_rows(benchmark: str, split: str, root: Path = ROOT) -> Iterable[dict]:
    from datasets import load_from_disk
    dataset = load_from_disk(str(root / RAW[benchmark, split])).select_columns(LABEL_FREE_COLUMNS[benchmark])
    for batch in dataset.iter(batch_size=1000):
        for values in zip(*(batch[c] for c in LABEL_FREE_COLUMNS[benchmark])):
            yield dict(zip(LABEL_FREE_COLUMNS[benchmark], values))


def selection_plan(pools: dict, questions: dict[str, set[str]], contexts: set[str], digests: dict[str, str]) -> dict:
    return {
        "version": "final_test_v2_selection_plan_v1",
        "status": "PLAN_ONLY_NOT_BUILT_NOT_AUTHORIZED",
        "labels_accessed": False, "answer_columns_loaded": False,
        "exposure": {"method": EXPOSURE_METHOD, "files_checked": len(digests),
                     "file_list_sha256": sha256_bytes(canonical_bytes(sorted(digests))),
                     "exposed_normalized_questions": len(questions), "exposed_paragraph_hashes": len(contexts),
                     "includes_retired_provisional_final_test": any(n.startswith(relative(PROVISIONAL_DIR)) for n in digests)},
        "eligible_pools": pools,
        "candidate_design": {
            "unit": "question group; one benchmark-gold candidate plus one verified-incorrect candidate (paired)",
            "GSM8K_negative_rule": "existing gold+1 discrete-count rule with full worked-solution replay; PENDING APPROVAL for Final Test use",
            "HotpotQA_negative_rule": "none approved; requires blinded human adjudication or a newly approved rule",
            "groups_without_verified_negative": "PENDING DECISION: drop, or keep gold-only and report separately",
            "unresolved": "excluded from binary metrics and counted; never relabelled incorrect",
            "class_proportion": "follows from the paired design; no target prevalence is set",
            "sample_size": "PENDING an approved power or precision justification",
        },
        "procedure": [
            "Team approves candidate rules, GSM8K source split, sample size and custodian.",
            "Custodian rebuilds this pool from the recorded inputs and verifies eligible_source_id_sha256.",
            "Custodian removes within-pool shared paragraphs and supporting facts, then draws groups with a seed fixed before drawing.",
            "Custodian applies the approved negative rules; ineligible groups follow the approved decision.",
            "Builder writes a new version with a passing content-level exposure audit and separate custodian labels.",
            "Custodian prepares a FinalTestReservation from the roster; labels stay sealed until authorized.",
        ],
    }


def compute(root: Path = ROOT) -> dict[str, dict]:
    roster = PROVISIONAL_DIR / "evaluation_roster.jsonl"
    manifest = PROVISIONAL_DIR / "manifest.json"
    own = OUTPUT.parent
    audit_files = exposure_files(root, exclude=(PROVISIONAL_DIR, own))
    audit_index, _, audit_digests = scan(audit_files, root)
    audit = contamination_audit(roster, manifest, audit_index, audit_digests, root)
    balance = development_label_balance({"history": HISTORY, "development": DEVELOPMENT}, root)
    plan_files = exposure_files(root, exclude=(own,))
    questions, contexts, digests = scan(plan_files, root)
    pools: dict[str, dict] = {}
    for benchmark in ("GSM8K", "HotpotQA"):
        seen: set[str] = set()
        splits = ("test", "train") if benchmark == "GSM8K" else ("validation", "train")
        pools[benchmark] = {split: pool(benchmark, split, raw_rows(benchmark, split, root), questions,
                                        contexts if benchmark == "HotpotQA" else set(), seen) for split in splits}
    plan = selection_plan(pools, questions, contexts, digests)
    return {"final_test_contamination_audit.json": audit, "development_label_balance.json": balance,
            "final_test_v2_selection_plan.json": plan}


def generate(output: Path = OUTPUT) -> dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Refusing to overwrite existing Experiment 1 preparation output")
    results = compute()
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, value in results.items():
        data = canonical_bytes(value)
        with (output / name).open("xb") as handle:
            handle.write(data)
        hashes[name] = sha256_bytes(data)
    manifest = {"version": VERSION, "generator_sha256": sha256_file(Path(__file__)), "output_sha256": hashes}
    with (output / "manifest.json").open("xb") as handle:
        handle.write(canonical_bytes(manifest))
    return manifest


def validate(output: Path = OUTPUT) -> dict:
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    stored = {name: sha256_file(output / name) for name in manifest["output_sha256"]}
    recomputed = {name: sha256_bytes(canonical_bytes(value)) for name, value in compute().items()}
    return {"stored_hash_mismatches": sorted(n for n, h in stored.items() if h != manifest["output_sha256"][n]),
            "recomputed_mismatches": sorted(n for n, h in recomputed.items() if h != manifest["output_sha256"].get(n)),
            "generator_changed": sha256_file(Path(__file__)) != manifest["generator_sha256"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"))
    args = parser.parse_args(argv)
    result: Any = generate() if args.command == "generate" else validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "generate" or not any(result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
