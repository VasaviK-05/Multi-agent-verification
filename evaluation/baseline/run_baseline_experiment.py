"""Run the existing baseline validation pipeline on the development set.

The orchestrator, selector, verifiers, and decision engine are used as
implemented. This script does not update reputation and does not edit
production verifier code.

Reputation isolation: a fresh in-memory ``ReputationManager`` is injected.
``validate`` does not learn. The default orchestrator constructor would
load persisted PostgreSQL reputation; this experiment does not, so prior
feedback cannot change selection or aggregation and nothing is written back.
At the uniform prior of 0.5, log-odds weights are zero and the decision
engine uses equal-weight aggregation.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.models.schemas import ValidationRequest
from app.orchestration.validation_orchestrator import ValidationOrchestrator
from app.reputation.reputation_manager import ReputationManager
from evaluation.baseline.adapters import (
    ELIGIBLE_BENCHMARKS,
    ExperimentInstance,
    SkippedExample,
    iter_dataset,
    prediction_matches,
)
from evaluation.baseline.metrics import summarize


DATASET_PATH = ROOT / "evaluation" / "datasets" / "unified" / "development.json"
DEFAULT_OUTPUT = ROOT / "evaluation" / "results" / "baseline"
SEED = 0


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise ValueError(f"{path} must contain a JSON list")
    return rows


def smoke_instances(items: list, example_limit: int) -> list:
    """First examples of FEVER, GSM8K, and HotpotQA, in that priority, file order."""
    wanted = {"FEVER": 2, "GSM8K": 2, "HotpotQA": 1}
    if example_limit != 5:
        wanted = {}
    chosen_ids: list[str] = []
    seen: set[str] = set()
    if wanted:
        counts = {name: 0 for name in wanted}
        for item in items:
            if not isinstance(item, ExperimentInstance):
                continue
            if item.benchmark not in counts or counts[item.benchmark] >= wanted[item.benchmark]:
                continue
            if item.example_id in seen:
                continue
            seen.add(item.example_id)
            chosen_ids.append(item.example_id)
            counts[item.benchmark] += 1
            if sum(counts.values()) >= example_limit:
                break
    else:
        for item in items:
            if isinstance(item, ExperimentInstance) and item.example_id not in seen:
                seen.add(item.example_id)
                chosen_ids.append(item.example_id)
                if len(chosen_ids) >= example_limit:
                    break
    chosen = set(chosen_ids)
    return [item for item in items if isinstance(item, ExperimentInstance) and item.example_id in chosen]


def load_completed_ids(jsonl_path: Path) -> set[str]:
    done = set()
    if not jsonl_path.exists():
        return done
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            instance_id = row.get("instance_id")
            if instance_id:
                done.add(instance_id)
    return done


def record_from_response(instance: ExperimentInstance, response, latency_ms: float) -> dict:
    audit = response.execution_audit or {}
    plan = audit.get("selection_plan") or {}
    results = []
    for result in response.results:
        metadata = result.metadata or {}
        results.append({
            "verifier_name": result.verifier_name,
            "score": result.score,
            "passed": result.passed,
            "decision": metadata.get("decision"),
            "reasoning": result.reasoning,
            "abstain_reason": metadata.get("abstain_reason"),
            "pipeline_role": metadata.get("pipeline_role"),
            "latency_ms": metadata.get("latency_ms"),
        })
    status = response.final_status
    abstained = status in {"uncertain", "unknown"}
    return {
        "instance_id": instance.instance_id,
        "example_id": instance.example_id,
        "benchmark": instance.benchmark,
        "task_type": instance.task_type,
        "question": instance.question,
        "candidate_answer": instance.candidate_answer,
        "candidate_index": instance.candidate_index,
        "candidate_source": instance.candidate_source,
        "gold_label": instance.gold_label,
        "gold_role": instance.gold_role,
        "framework_decision": status,
        "prediction_correct": prediction_matches(instance.gold_role, status),
        "abstained": abstained,
        "final_score": response.final_score,
        "signed_score": response.signed_score,
        "score_is_probability": False,
        "validation_id": response.validation_id,
        "domain": response.domain,
        "difficulty": response.difficulty,
        "early_stop_reason": response.early_stop_reason,
        "uncertainty_reasons": list(response.uncertainty_reasons or []),
        "selected_verifiers": list(plan.get("initial_selected") or []),
        "fallback_verifiers": list(plan.get("fallback") or []),
        "executed_verifiers": list(audit.get("attempted_verifiers") or []),
        "returned_verifiers": list(audit.get("returned_result_verifiers") or []),
        "unavailable_verifiers": audit.get("unavailable_verifiers") or [],
        "verifier_results": results,
        "verifier_calls": len(audit.get("attempted_verifiers") or []),
        "latency_ms": round(latency_ms, 3),
        "public_status_note": (
            "Framework final_status uses passed, failed, uncertain, and unknown. "
            "Verifier metadata.decision uses SUPPORT, REJECT, and UNSURE. "
            "Those vocabularies are not interchangeable."
        ),
        "evaluation_note": instance.evaluation_note,
        "context_characters": instance.extra.get("context_characters", len(instance.context or "")),
        "evidence_sentences_available": instance.extra.get("evidence_sentences_available"),
        "run_status": "completed",
        "error": None,
    }


def error_record(instance: ExperimentInstance, exc: BaseException, latency_ms: float) -> dict:
    return {
        "instance_id": instance.instance_id,
        "example_id": instance.example_id,
        "benchmark": instance.benchmark,
        "task_type": instance.task_type,
        "question": instance.question,
        "candidate_answer": instance.candidate_answer,
        "candidate_index": instance.candidate_index,
        "candidate_source": instance.candidate_source,
        "gold_label": instance.gold_label,
        "gold_role": instance.gold_role,
        "framework_decision": None,
        "prediction_correct": None,
        "abstained": None,
        "validation_id": None,
        "selected_verifiers": None,
        "executed_verifiers": None,
        "verifier_results": None,
        "verifier_calls": None,
        "latency_ms": round(latency_ms, 3),
        "evaluation_note": instance.evaluation_note,
        "run_status": "error",
        "error": {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        },
    }


def write_outputs(output_dir: Path, records: list[dict], skipped: list[dict], started_at: str, elapsed_s: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "baseline_results.json"
    csv_path = output_dir / "baseline_results.csv"
    summary_path = output_dir / "baseline_summary.json"
    errors_path = output_dir / "baseline_errors.json"

    results_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    fieldnames = [
        "instance_id", "example_id", "benchmark", "gold_label", "gold_role",
        "framework_decision", "prediction_correct", "abstained", "verifier_calls",
        "latency_ms", "validation_id", "selected_verifiers", "executed_verifiers",
        "run_status", "question", "candidate_answer",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            writer.writerow({
                key: json.dumps(row.get(key), ensure_ascii=False) if isinstance(row.get(key), (list, dict)) else row.get(key)
                for key in fieldnames
            })

    failed = [row for row in records if row.get("run_status") == "error"]
    summary = summarize(records, skipped=skipped)
    latencies = [
        row.get("latency_ms") for row in records
        if isinstance(row.get("latency_ms"), (int, float))
    ]
    summary["experiment"] = {
        "execution_mode": "baseline",
        "dataset": str(DATASET_PATH.relative_to(ROOT)).replace("\\", "/"),
        "seed": SEED,
        "reputation": "isolated cold-start ReputationManager prior alpha=1 beta=1; validate does not learn",
        "started_at": started_at,
        "wall_clock_seconds": round(elapsed_s, 3),
        "sum_instance_latency_ms": round(sum(latencies), 3) if latencies else 0,
        "eligible_benchmarks": list(ELIGIBLE_BENCHMARKS),
        "completed_instances": summary["completed"],
        "failed_instances": summary["failed"],
        "skipped_examples": summary["skipped"],
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    errors_path.write_text(json.dumps({
        "failed": [
            {
                "instance_id": row.get("instance_id"),
                "example_id": row.get("example_id"),
                "benchmark": row.get("benchmark"),
                "error": row.get("error"),
            }
            for row in failed
        ],
        "skipped": skipped,
    }, indent=2, ensure_ascii=False), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def run(output_dir: Path, instances: list[ExperimentInstance], skipped: list[dict]) -> None:
    random.seed(SEED)
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "baseline_results.jsonl"
    done = load_completed_ids(jsonl_path)
    started = time.strftime("%Y-%m-%dT%H:%M:%S")
    clock = time.perf_counter()

    pending = [item for item in instances if item.instance_id not in done]
    print(
        f"instances={len(instances)} already_recorded={len(done)} pending={len(pending)} skipped_examples={len(skipped)}",
        flush=True,
    )
    if pending:
        manager = ReputationManager()
        orchestrator = ValidationOrchestrator(
            reputation_manager=manager,
            execution_mode="baseline",
        )
        with jsonl_path.open("a", encoding="utf-8") as handle:
            for index, instance in enumerate(pending, start=1):
                request = ValidationRequest(
                    question=instance.question,
                    answer=instance.candidate_answer,
                    context=instance.context,
                )
                begin = time.perf_counter()
                try:
                    response = orchestrator.validate(request)
                    latency_ms = (time.perf_counter() - begin) * 1000
                    row = record_from_response(instance, response, latency_ms)
                except Exception as exc:
                    latency_ms = (time.perf_counter() - begin) * 1000
                    row = error_record(instance, exc, latency_ms)
                    print(
                        f"ERROR {instance.instance_id}: {type(exc).__name__}: {exc}",
                        flush=True,
                    )
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                if index == 1 or index % 25 == 0 or index == len(pending):
                    print(
                        f"[{index}/{len(pending)}] {instance.benchmark} {instance.instance_id} "
                        f"status={row.get('framework_decision')} latency_ms={row.get('latency_ms')}",
                        flush=True,
                    )

    records = read_jsonl(jsonl_path)
    elapsed = time.perf_counter() - clock
    write_outputs(output_dir, records, skipped, started, elapsed)
    print(f"wrote {output_dir}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Baseline validation experiment")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--smoke",
        type=int,
        default=0,
        help="Run a deterministic smoke subset. 5 selects 2 FEVER, 2 GSM8K, and 1 HotpotQA examples.",
    )
    args = parser.parse_args()
    rows = load_rows(args.dataset)
    items = list(iter_dataset(rows))
    skipped = [
        {"example_id": item.example_id, "benchmark": item.benchmark, "reason": item.reason}
        for item in items
        if isinstance(item, SkippedExample)
    ]
    instances = [item for item in items if isinstance(item, ExperimentInstance)]
    output = args.output
    if args.smoke:
        instances = smoke_instances(items, args.smoke)
        skipped = []
        output = args.output / "smoke"
    run(output, instances, skipped)


if __name__ == "__main__":
    main()
