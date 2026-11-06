"""Development-only real-call feasibility pilot for research_v1.

This runner reads only Development inputs, writes versioned pilot outputs, and
never constructs policy-fitting artifacts. Actual verifier calls require the
locally pinned project adapter to pass its offline preflight.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.game.models import canonical_json, content_id
from evaluation.data_preparation import build_offline_examples as offline_adapter
from evaluation.data_preparation import run_verifier_attempts as attempt_runner
from evaluation.data_preparation.final_test_workflow import validate_readiness

PREPARED = ROOT / "evaluation/datasets/offline_examples/research_v1/development_prepared.jsonl"
RECONCILED = ROOT / "evaluation/datasets/reconciled_candidates/research_v1/development_candidates.jsonl"
DEFAULT_OUTPUT = ROOT / "evaluation/datasets/development_pilot/research_v1_feasibility_v2"
BENCHMARKS = ("GSM8K", "HotpotQA")
VERIFIERS = attempt_runner.VERIFIERS
VERSION = "research-v1-development-feasibility-pilot-v1"
STATUS_BOOL = {"verified_correct": True, "verified_incorrect": False}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_development_path(path: Path, expected_name: str) -> Path:
    resolved = path.resolve()
    if resolved.name.casefold() != expected_name.casefold() or any("final_test" in part.casefold() for part in resolved.parts):
        raise ValueError("Development pilot accepts only the named Development input artifact")
    return resolved


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path.name}:{line_no}") from exc
    return rows


def load_development_roster(prepared_path: Path = PREPARED, reconciled_path: Path = RECONCILED) -> dict:
    """Load only Development candidate inputs and labels; no History roster is opened."""
    prepared_path = _validate_development_path(prepared_path, "development_prepared.jsonl")
    reconciled_path = _validate_development_path(reconciled_path, "development_candidates.jsonl")
    prepared = read_jsonl(prepared_path)
    reconciled = read_jsonl(reconciled_path)
    source_by_id: dict[str, dict] = {}
    groups: dict[str, set[str]] = defaultdict(set)
    source_groups_by_benchmark: dict[str, set[str]] = defaultdict(set)
    labels_by_benchmark: Counter = Counter()
    source_candidates_by_benchmark: Counter = Counter()
    for source in reconciled:
        if source.get("partition") != "development":
            raise ValueError("Development candidate file contains a non-Development row")
        cid = source.get("candidate_id")
        if not cid or cid in source_by_id:
            raise ValueError("missing or duplicate Development candidate ID")
        status = source.get("correctness_status")
        if status not in {*STATUS_BOOL, "unresolved"}:
            raise ValueError(f"invalid label state for {cid}")
        method = source.get("validation_method")
        if not isinstance(method, str) or not method.strip():
            raise ValueError(f"missing label provenance for {cid}")
        if status in STATUS_BOOL:
            if not source.get("validation_basis") or not source.get("source_candidate_record"):
                raise ValueError(f"binary label lacks provenance for {cid}")
        elif source.get("answer_is_correct") is not None:
            raise ValueError(f"unresolved candidate has a binary label: {cid}")
        source_by_id[cid] = source
        groups[str(source.get("related_group_id"))].add(status)
        source_groups_by_benchmark[source["benchmark"]].add(str(source.get("related_group_id")))
        source_candidates_by_benchmark[source["benchmark"]] += 1
        labels_by_benchmark[f"{source['benchmark']}:{status}"] += 1

    attempted_rows: list[dict] = []
    attempted_ids: set[str] = set()
    for row in prepared:
        cid = row.get("candidate_id")
        if row.get("partition") != "development" or row.get("benchmark") not in BENCHMARKS:
            raise ValueError("prepared candidate is outside the Development benchmark roster")
        if not cid or cid in attempted_ids:
            raise ValueError("missing or duplicate prepared Development candidate ID")
        source = source_by_id.get(cid)
        if source is None or source.get("correctness_status") not in STATUS_BOOL:
            raise ValueError(f"prepared row has no matching binary Development label: {cid}")
        expected_label = STATUS_BOOL[source["correctness_status"]]
        actual_label = row.get("answer_is_correct")
        if type(actual_label) is not bool or actual_label is not expected_label:
            raise ValueError(f"invalid or inconsistent binary label for {cid}")
        if row.get("correctness_status") != source.get("correctness_status"):
            raise ValueError(f"prepared label state mismatch for {cid}")
        if row.get("question") != source.get("question") or row.get("candidate_answer") != source.get("candidate_answer"):
            raise ValueError(f"prepared input mismatch for {cid}")
        required = ("dataset_id", "question_id", "related_group_id", "benchmark", "question", "candidate_answer")
        if any(row.get(key) in (None, "") for key in required):
            raise ValueError(f"missing required pilot identity/input field for {cid}")
        if row.get("label_method") != offline_adapter.PREPARATION_LABEL_METHOD:
            raise ValueError(f"unsupported label method for {cid}")
        inp = attempt_runner.permitted_input(row)
        if inp[0] != row["benchmark"]:
            raise ValueError(f"verifier input benchmark mismatch for {cid}")
        clean = {key: row[key] for key in ("candidate_id", "dataset_id", "question_id", "related_group_id", "partition", "benchmark")}
        clean["verifier_input"] = {"question": inp[1], "candidate_answer": row["verifier_input"]["candidate_answer"], "context": inp[2]}
        clean["verifier_input_sha256"] = hashlib.sha256(canonical_json(clean["verifier_input"]).encode()).hexdigest()
        attempted_rows.append(clean)
        attempted_ids.add(cid)

    expected_labelled = {cid for cid, source in source_by_id.items() if source["correctness_status"] in STATUS_BOOL}
    if attempted_ids != expected_labelled:
        raise ValueError("prepared Development candidates do not equal the validated binary-label roster")
    unresolved = []
    for cid, source in source_by_id.items():
        if source["correctness_status"] == "unresolved":
            unresolved.append({"candidate_id": cid, "dataset_id": source["dataset_id"],
                               "related_group_id": source["related_group_id"], "partition": "development",
                               "benchmark": source["benchmark"], "correctness_status": "unresolved",
                               "disposition": "not_attempted_no_binary_label"})
    attempted_rows.sort(key=lambda r: (r["benchmark"], r["candidate_id"]))
    unresolved.sort(key=lambda r: (r["benchmark"], r["candidate_id"]))
    labels = {cid: {"correctness_status": source["correctness_status"], "answer_is_correct": STATUS_BOOL[source["correctness_status"]],
                    "label_method": offline_adapter.PREPARATION_LABEL_METHOD,
                    "validation_method": source["validation_method"],
                    "related_group_id": source["related_group_id"], "benchmark": source["benchmark"]}
               for cid, source in source_by_id.items() if source["correctness_status"] in STATUS_BOOL}
    labelled_groups_by_benchmark = {benchmark: len({row["related_group_id"] for row in attempted_rows if row["benchmark"] == benchmark})
                                    for benchmark in BENCHMARKS}
    return {"rows": attempted_rows, "unresolved": unresolved, "labels": labels,
            "source_candidate_count": len(source_by_id), "source_group_count": len(groups),
            "labelled_candidate_count": len(attempted_rows), "labelled_group_count": len({r["related_group_id"] for r in attempted_rows}),
            "groups_without_binary_candidates": sum(not (statuses & STATUS_BOOL.keys()) for statuses in groups.values()),
            "source_candidate_count_by_benchmark": dict(source_candidates_by_benchmark),
            "source_group_count_by_benchmark": {benchmark: len(source_groups_by_benchmark[benchmark]) for benchmark in BENCHMARKS},
            "label_counts_by_benchmark": dict(labels_by_benchmark),
            "labelled_candidates_by_benchmark": dict(Counter(row["benchmark"] for row in attempted_rows)),
            "labelled_groups_by_benchmark": labelled_groups_by_benchmark,
            "source_hashes": {"development_prepared.jsonl": sha256_file(prepared_path),
                              "development_candidates.jsonl": sha256_file(reconciled_path)}}


def _runtime_environment() -> dict:
    packages = {}
    for name in ("numpy", "pydantic", "sentence-transformers", "transformers", "torch", "faiss-cpu", "requests", "safetensors", "tokenizers"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"python": sys.version, "platform": platform.platform(), "architecture": platform.machine(),
            "logical_cpus": os.cpu_count(), "packages": packages,
            "thread_environment": {key: os.environ.get(key) for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")}}


def _write_new(output_dir: Path, files: dict[str, bytes]) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty pilot output: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        with (output_dir / name).open("xb") as stream:
            stream.write(data)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _write_hash_receipt(output_dir: Path) -> None:
    names = [name for name in ("pilot_manifest.json", "pilot_results.json", "attempts.jsonl", "unresolved_not_attempted.jsonl")
             if (output_dir / name).is_file()]
    receipt = {name: sha256_file(output_dir / name) for name in names}
    (output_dir / "artifact_sha256.json").write_bytes(_json_bytes(receipt))


def _adapter_preflight() -> tuple[Any, Path | None, dict]:
    raw = os.environ.get("VERIFIER_COLLECTION_ADAPTER_CONFIG")
    if not raw:
        return None, None, {"ready": False, "blockers": [{"resource": "adapter_configuration", "reason": "VERIFIER_COLLECTION_ADAPTER_CONFIG is unset", "owner": "resource/collection owner"}]}
    config_path = Path(raw).resolve()
    if not config_path.is_file():
        return None, config_path, {"ready": False, "blockers": [{"resource": "adapter_configuration", "reason": "configured adapter JSON does not exist", "owner": "resource/collection owner"}]}
    from app.benchmark.project_adapter import AdapterConfiguration, inspect_setup, read_json
    try:
        config = AdapterConfiguration.model_validate(read_json(config_path))
        return config, config_path, inspect_setup(config)
    except Exception as exc:
        return None, config_path, {"ready": False, "blockers": [{"resource": "adapter_configuration", "reason": f"{type(exc).__name__}: {exc}", "owner": "resource/collection owner"}]}


def _blocked_artifact(output_dir: Path, roster: dict, preflight: dict, config_path: Path | None) -> dict:
    readiness = validate_readiness(ROOT / "evaluation/config/protocol_readiness.yaml")
    manifest = {"version": VERSION, "status": "BLOCKED_PREFLIGHT", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "partition": "development", "final_test_accessed": False, "history_inputs_read": False,
                "source_hashes": roster["source_hashes"], "adapter_configuration_path": str(config_path) if config_path else None,
                "adapter_configuration_sha256": sha256_file(config_path) if config_path and config_path.is_file() else None,
                "runner_sha256": sha256_file(Path(__file__)),
                "attempt_runner_sha256": sha256_file(Path(attempt_runner.__file__)),
                "readiness_validator_sha256": sha256_file(ROOT / "evaluation/data_preparation/final_test_workflow.py"),
                "preflight": preflight, "runtime_environment": _runtime_environment(),
                "candidate_counts": {k: roster[k] for k in ("source_candidate_count", "source_group_count", "labelled_candidate_count", "labelled_group_count", "groups_without_binary_candidates",
                                                               "source_candidate_count_by_benchmark", "source_group_count_by_benchmark", "label_counts_by_benchmark",
                                                               "labelled_candidates_by_benchmark", "labelled_groups_by_benchmark")},
                "attempts_created": 0, "offline_examples_created": 0, "policy_fitting_ready": False,
                "readiness": {"exploratory_readiness": readiness["exploratory_readiness"], "confirmatory_readiness": readiness["confirmatory_readiness"]}}
    manifest["run_identity"] = content_id([VERSION, manifest["source_hashes"], manifest["adapter_configuration_sha256"],
                                            manifest["runner_sha256"], manifest["attempt_runner_sha256"], preflight])
    report = {"status": "BLOCKED_PREFLIGHT", "preflight_blockers": preflight.get("blockers", []),
              "dataset": "research_v1 Development", "candidate_counts": manifest["candidate_counts"],
              "groups_attempted": 0, "expected_verifier_calls": len(roster["rows"]) * len(VERIFIERS),
              "actual_verifier_calls": 0, "execution_results": "No verifier calls made; no simulated results substituted.",
              "verifier_availability": {verifier: {benchmark: "NOT EXECUTED: shared adapter configuration/preflight unavailable"
                                                    for benchmark in BENCHMARKS} for verifier in VERIFIERS},
              "unresolved_candidates_not_attempted": len(roster["unresolved"]), "offline_examples_created": 0,
              "policy_fitting_ready": False, "final_test_accessed": False, "readiness": manifest["readiness"]}
    _write_new(output_dir, {"pilot_manifest.json": _json_bytes(manifest), "pilot_results.json": _json_bytes(report)})
    _write_hash_receipt(output_dir)
    return report


def _decision(attempt: dict) -> str:
    if attempt["state"] in {"abstention", "unavailable", "failed", "missing"}:
        return "unresolved"
    report = json.loads(attempt["report_json"])
    decision = (report.get("metadata") or {}).get("decision")
    if decision == "SUPPORT":
        return "support"
    if decision == "REJECT":
        return "reject"
    if decision == "UNSURE":
        return "unresolved"
    return "support" if report.get("passed") else "reject"


def _duration_summary(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "mean_ms": None, "median_ms": None, "p95_ms": None, "total_ms": 0.0}
    ordered = sorted(values)
    return {"n": len(ordered), "mean_ms": statistics.mean(ordered), "median_ms": statistics.median(ordered),
            "p95_ms": ordered[min(len(ordered) - 1, int(0.95 * (len(ordered) - 1)))], "total_ms": sum(ordered)}


def analyze_attempts(roster: dict, records: dict, wall_seconds: float) -> dict:
    candidates = roster["rows"]
    expected = {(row["candidate_id"], verifier) for row in candidates for verifier in VERIFIERS}
    outcomes = {"directional": 0, "abstention": 0, "unavailable": 0, "failed": 0, "missing": 0}
    by_verifier: dict[str, dict] = {}
    durations_by_verifier: dict[str, list[float]] = defaultdict(list)
    for verifier in VERIFIERS:
        wrappers = [value for (cid, name), value in records.items() if name == verifier]
        states = Counter(wrapper["attempt"]["state"] for wrapper in wrappers)
        for state in outcomes:
            outcomes[state] += states[state]
        values = [float(row["duration_ms"]) for row in wrappers if isinstance(row.get("duration_ms"), (int, float)) and row["duration_ms"] >= 0]
        durations_by_verifier[verifier] = values
        by_verifier[verifier] = {"recorded_calls": len(wrappers), "states": {state: states[state] for state in outcomes},
                                 "runtime_ms": _duration_summary(values), "estimated_attempt_cost": None,
                                 "estimated_attempt_cost_status": "not supplied by direct-verifier runner"}
    label_map = roster["labels"]
    group_scores: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    decision_by_candidate: dict[str, dict[str, str]] = defaultdict(dict)
    for (cid, verifier), wrapper in records.items():
        if cid not in label_map:
            raise ValueError(f"attempt output has no validated Development label: {cid}")
        decision = _decision(wrapper["attempt"])
        decision_by_candidate[cid][verifier] = decision
        if decision in {"support", "reject"}:
            gold = label_map[cid]["answer_is_correct"]
            group_scores[verifier][label_map[cid]["related_group_id"]].append(int((decision == "support") == gold))
    group_summary = {}
    for verifier in VERIFIERS:
        means = [statistics.mean(values) for values in group_scores[verifier].values() if values]
        paired = [tuple(values[:2]) for values in group_scores[verifier].values() if len(values) >= 2]
        if len(paired) >= 2:
            xs, ys = zip(*paired)
            if statistics.pvariance(xs) and statistics.pvariance(ys):
                within_group_corr = statistics.correlation(xs, ys)
            else:
                within_group_corr = None
        else:
            within_group_corr = None
        group_summary[verifier] = {"groups_with_directional_labeled_outcomes": len(means),
                                   "variance_of_group_mean_correctness": statistics.pvariance(means) if len(means) > 1 else None,
                                   "groups_with_paired_candidate_outcomes": len(paired),
                                   "within_group_candidate_outcome_correlation": within_group_corr,
                                   "status": "descriptive Development estimate; not a power calculation"}
    disagreements = {}
    for index, left in enumerate(VERIFIERS):
        for right in VERIFIERS[index + 1:]:
            compared = disagree = 0
            for decisions in decision_by_candidate.values():
                a, b = decisions.get(left), decisions.get(right)
                if a in {"support", "reject"} and b in {"support", "reject"}:
                    compared += 1
                    disagree += int(a != b)
            disagreements[f"{left}__{right}"] = {"paired_directional_candidates": compared, "disagreements": disagree,
                "disagreement_rate": disagree / compared if compared else None}
    scheduled = len(expected)
    pending = expected - set(records)
    outcomes["missing"] = len(pending)
    groups = {row["related_group_id"] for row in candidates}
    attempted_groups = {row["related_group_id"] for row in candidates if any((row["candidate_id"], verifier) in records for verifier in VERIFIERS)}
    decision_outcomes = {}
    benchmark_calls = {}
    for verifier in VERIFIERS:
        decision_outcomes[verifier] = {key: sum(name == verifier and _decision(row["attempt"]) == value for (_, name), row in records.items())
                                       for key, value in (("support", "support"), ("reject", "reject"), ("unresolved", "unresolved"))}
        benchmark_calls[verifier] = {}
        for benchmark in BENCHMARKS:
            wrappers = [value for (cid, name), value in records.items() if name == verifier and label_map.get(cid, {}).get("benchmark") == benchmark]
            benchmark_calls[verifier][benchmark] = {"recorded": len(wrappers),
                "directional": sum(value["attempt"]["state"] == "directional" for value in wrappers),
                "abstention": sum(value["attempt"]["state"] == "abstention" for value in wrappers),
                "unavailable": sum(value["attempt"]["state"] == "unavailable" for value in wrappers),
                "failed": sum(value["attempt"]["state"] == "failed" for value in wrappers)}
    return {"status": "COMPLETED" if not pending else "INCOMPLETE", "dataset": "research_v1", "partition": "development",
            "source_candidate_count": roster["source_candidate_count"], "source_group_count": roster["source_group_count"],
            "labelled_candidate_count": roster["labelled_candidate_count"], "labelled_group_count": roster["labelled_group_count"],
            "source_candidate_count_by_benchmark": roster["source_candidate_count_by_benchmark"],
            "source_group_count_by_benchmark": roster["source_group_count_by_benchmark"],
            "label_counts_by_benchmark": roster["label_counts_by_benchmark"],
            "labelled_candidates_by_benchmark": roster["labelled_candidates_by_benchmark"],
            "labelled_groups_by_benchmark": roster["labelled_groups_by_benchmark"],
            "groups_attempted": len(attempted_groups), "attemptable_groups": len(groups),
            "unresolved_candidates_not_attempted": len(roster["unresolved"]), "scheduled_calls": scheduled,
            "recorded_calls": len(records), "missing_attempt_outputs": len(pending), "states_all_verifiers": outcomes,
            "verifiers": by_verifier, "coverage": {
                "returned_reports_over_scheduled": (outcomes["directional"] + outcomes["abstention"]) / scheduled if scheduled else None,
                "directional_decisions_over_scheduled": outcomes["directional"] / scheduled if scheduled else None,
                "denominator": scheduled}, "decision_outcomes": decision_outcomes,
            "verifier_calls_by_benchmark": benchmark_calls,
            "paired_disagreement": disagreements, "sample_size_planning": {
                "group_level_correctness_variance": group_summary,
                "within_group_dependence": "per-verifier Pearson correlation of correctness outcomes across paired candidates within Development groups, where at least two such groups have directional outputs; otherwise unavailable",
                "power_or_final_sample_size": "not computed; target confidence width or power and inferential assumptions are unapproved"},
            "runtime": {"wall_clock_seconds": wall_seconds,
                        "attempt_duration_ms_sum": sum(sum(values) for values in durations_by_verifier.values()),
                        "attempt_duration_by_verifier": {v: _duration_summary(durations_by_verifier[v]) for v in VERIFIERS},
                        "cost": "not measured; latency is not substituted for cost or research loss"},
            "offline_examples_created": 0, "policy_fitting_ready": False, "final_test_accessed": False}


def _load_records(path: Path) -> dict:
    result = {}
    if not path.exists():
        return result
    for wrapper in read_jsonl(path):
        key = (wrapper.get("candidate_id"), (wrapper.get("attempt") or {}).get("verifier_name"))
        if None in key or key in result:
            raise ValueError("missing/duplicate attempt output")
        result[key] = wrapper
    return result


def validate_output(output_dir: Path, roster: dict) -> dict:
    manifest = json.loads((output_dir / "pilot_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("partition") != "development" or manifest.get("final_test_accessed") is not False or manifest.get("history_inputs_read") is not False:
        raise ValueError("pilot manifest violates Development-only access boundary")
    if manifest.get("source_hashes") != roster["source_hashes"]:
        raise ValueError("Development source hashes changed")
    records = _load_records(output_dir / "attempts.jsonl")
    ids = {row["candidate_id"] for row in roster["rows"]}
    expected = {(cid, verifier) for cid in ids for verifier in VERIFIERS}
    if set(records) - expected:
        raise ValueError("attempt output includes an unknown/non-Development candidate or verifier")
    from app.game.offline.records import Attempt
    for key, wrapper in records.items():
        attempt = Attempt.model_validate(wrapper["attempt"])
        if wrapper.get("partition") != "development" or attempt.verifier_name != key[1]:
            raise ValueError("invalid attempt identity/partition")
        if attempt.configuration_id != manifest.get("execution_configuration_id"):
            raise ValueError("attempt resource configuration does not match manifest")
    return {"valid": True, "expected_calls": len(expected), "recorded_calls": len(records),
            "missing_calls": len(expected - set(records)), "unknown_calls": 0}


def run(output_dir: Path = DEFAULT_OUTPUT, prepared_path: Path = PREPARED, reconciled_path: Path = RECONCILED, *, resume: bool = False) -> dict:
    roster = load_development_roster(prepared_path, reconciled_path)
    if output_dir.exists() and not resume:
        raise FileExistsError("pilot output exists; use --resume only for the identical pinned run")
    config, config_path, preflight = _adapter_preflight()
    if not preflight.get("ready"):
        if resume:
            raise ValueError("cannot resume a blocked preflight artifact")
        return _blocked_artifact(output_dir, roster, preflight, config_path)

    from app.benchmark.project_adapter import create_verifiers
    verifiers, setup = create_verifiers()
    setup = attempt_runner.MeasurementSetup.model_validate(setup)
    pool = {verifier.name: verifier for verifier in verifiers}
    if set(pool) != set(VERIFIERS):
        raise RuntimeError("adapter did not construct exactly the four pinned verifiers")
    setup.resources.require_candidates(pool)
    manifest = {"version": VERSION, "partition": "development", "source_hashes": roster["source_hashes"],
                "adapter_configuration_sha256": sha256_file(config_path), "measurement_setup_fingerprint": setup.fingerprint,
                "execution_configuration_id": setup.resources.manifest_id, "resource_manifest": setup.resources.model_dump(mode="json"),
                "code_revision": setup.code_revision, "application_source_digest": setup.application_source_digest,
                "dependency_versions": setup.dependency_versions, "runtime_environment": setup.environment,
                "verifiers": list(VERIFIERS), "candidate_count": roster["labelled_candidate_count"],
                "group_count": roster["labelled_group_count"], "unresolved_candidate_count": len(roster["unresolved"]),
                "final_test_accessed": False, "history_inputs_read": False, "labels_or_gold_sent_to_verifiers": False,
                "offline_examples_created": 0, "policy_fitting_performed": False}
    manifest["run_identity"] = content_id([manifest, config_path.name])
    if output_dir.exists():
        prior = json.loads((output_dir / "pilot_manifest.json").read_text(encoding="utf-8"))
        if prior != manifest:
            raise ValueError("resume refused: Development inputs, configuration, resources, or code changed")
    else:
        output_dir.mkdir(parents=True)
        (output_dir / "pilot_manifest.json").write_bytes(_json_bytes(manifest))
        unresolved_bytes = b"".join((json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode() for row in roster["unresolved"])
        (output_dir / "unresolved_not_attempted.jsonl").write_bytes(unresolved_bytes)
    records = _load_records(output_dir / "attempts.jsonl")
    mode = "a" if (output_dir / "attempts.jsonl").exists() else "x"
    started = time.perf_counter()
    with (output_dir / "attempts.jsonl").open(mode, encoding="utf-8") as stream:
        for row in roster["rows"]:
            for name in VERIFIERS:
                if (row["candidate_id"], name) in records:
                    continue
                resource = next(item for item in setup.resources.verifiers if item.verifier_name == name)
                result = attempt_runner.record_one(row, pool[name], resource, setup.resources.manifest_id)
                stream.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
                stream.flush()
                records[(row["candidate_id"], name)] = result
    wall_seconds = time.perf_counter() - started
    integrity = validate_output(output_dir, roster)
    report = analyze_attempts(roster, records, wall_seconds)
    report["validation"] = integrity
    readiness = validate_readiness(ROOT / "evaluation/config/protocol_readiness.yaml")
    report["readiness"] = {key: value for key, value in readiness.items() if key != "observed_values"}
    (output_dir / "pilot_results.json").write_bytes(_json_bytes(report))
    _write_hash_receipt(output_dir)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "validate"))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prepared", type=Path, default=PREPARED)
    parser.add_argument("--reconciled", type=Path, default=RECONCILED)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    try:
        roster = load_development_roster(args.prepared, args.reconciled)
        result = run(args.output_dir, args.prepared, args.reconciled, resume=args.resume) if args.command == "run" else validate_output(args.output_dir, roster)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED_OR_INVALID", "error_type": type(exc).__name__, "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
