"""Record real verifier calls for prepared History/Development candidates.

This runner never constructs offline Example/TrainingManifest objects and never
reads label fields. It only sends the explicit verifier_input payload to the
existing locally pinned project adapter.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.decision.vote_normalization import is_abstention
from app.game.models import canonical_json, content_id
from app.game.offline.calibration import MeasurementSetup
from app.game.offline.records import Attempt
from app.game.offline.timing import TimedVerifier
from app.game.resource_provenance import ResourceManifest
from app.models.schemas import VerificationResult
from app.selection.models import VerifierUnavailable

PREPARED_DIR = ROOT / "evaluation/datasets/offline_examples/research_v1"
DEFAULT_OUTPUT = ROOT / "evaluation/datasets/verifier_attempts/research_v1"
VERIFIERS = ("semantic", "evidence", "rule", "confidence")
ADAPTERS = {"semantic": "semantic_v1", "evidence": "evidence_v1",
            "rule": "rule_v1", "confidence": "confidence_v1"}
PARTITIONS = ("history", "development")
VERSION = "research-v1-verifier-attempts-v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def jsonl_rows(path: Path):
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{number}") from exc


def permitted_input(row: dict) -> tuple[str, str, str | None]:
    """Read only benchmark/question/answer/context from verifier_input."""
    value = row.get("verifier_input")
    if not isinstance(value, dict):
        raise ValueError("prepared labelled row has no verifier_input")
    benchmark = value.get("benchmark")
    question = value.get("question")
    answer = value.get("candidate_answer")
    context = value.get("evidence_context")
    if benchmark not in {"GSM8K", "HotpotQA"} or not isinstance(question, str) or not question.strip():
        raise ValueError("verifier_input has invalid benchmark/question")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("verifier_input has invalid candidate answer")
    if context in (None, [], ""):
        normalized_context = None
    elif isinstance(context, str):
        normalized_context = context
    elif isinstance(context, list) and all(isinstance(x, str) for x in context):
        normalized_context = "\n\n".join(context)
    elif isinstance(context, list) and all(isinstance(x, dict) for x in context):
        # The prepared HotpotQA context is structured. Send only its textual
        # content and title; omit source paths and other provenance metadata.
        passages = []
        for item in context:
            text = item.get("text") or item.get("sentence_text_extracted")
            if text is not None and not isinstance(text, str):
                raise ValueError("structured evidence context contains non-text passage content")
            title = item.get("title")
            if title is not None and not isinstance(title, str):
                raise ValueError("structured evidence context contains a non-text title")
            passages.append((f"{title}\n{text}" if title and text else title or text or "").strip())
        normalized_context = "\n\n".join(p for p in passages if p) or None
    else:
        raise ValueError("verifier_input evidence_context must be text or a list of text")
    return benchmark, question, normalized_context


def load_roster(prepared_dir: Path):
    """Load H/D IDs and explicit inputs; unresolved rows remain a no-input ledger."""
    rows, unresolved = [], []
    paths = {"history": prepared_dir / "history_prepared.jsonl",
             "development": prepared_dir / "development_prepared.jsonl"}
    unresolved_path = prepared_dir / "excluded_unresolved.jsonl"
    all_ids, groups = set(), {}
    for partition, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        for source in jsonl_rows(path):
            # Only these metadata fields and verifier_input are read. In particular,
            # label, gold, solution, trace, and provenance fields are never used.
            fields = {key: source.get(key) for key in
                      ("candidate_id", "dataset_id", "question_id", "related_group_id", "partition", "benchmark")}
            candidate_id = fields["candidate_id"]
            if not candidate_id or candidate_id in all_ids:
                raise ValueError(f"missing or duplicate candidate ID: {candidate_id}")
            if fields["partition"] != partition or fields["benchmark"] not in {"GSM8K", "HotpotQA"}:
                raise ValueError(f"partition/benchmark mismatch for {candidate_id}")
            group_key = fields["benchmark"], fields["related_group_id"]
            old = groups.setdefault(group_key, partition)
            if old != partition:
                raise ValueError(f"History/Development group leakage: {group_key}")
            benchmark, question, context = permitted_input(source)
            if benchmark != fields["benchmark"]:
                raise ValueError(f"verifier_input benchmark mismatch: {candidate_id}")
            fields["verifier_input"] = {"question": question, "candidate_answer": source["verifier_input"]["candidate_answer"],
                                         "context": context}
            fields["verifier_input_sha256"] = hashlib.sha256(canonical_json(fields["verifier_input"]).encode()).hexdigest()
            rows.append(fields)
            all_ids.add(candidate_id)
    if unresolved_path.is_file():
        for source in jsonl_rows(unresolved_path):
            # Preserve unresolved identity and partition without creating verifier input.
            fields = {key: source.get(key) for key in
                      ("candidate_id", "dataset_id", "related_group_id", "partition", "benchmark",
                       "candidate_answer", "correctness_status")}
            if not fields["candidate_id"] or fields["candidate_id"] in all_ids:
                raise ValueError("missing/duplicate unresolved candidate ID")
            if fields["partition"] not in PARTITIONS or fields["benchmark"] not in {"GSM8K", "HotpotQA"}:
                raise ValueError("unresolved candidate is outside History/Development")
            if fields["correctness_status"] != "unresolved":
                raise ValueError("excluded-unresolved input contains a non-unresolved status")
            fields["question_id"] = f"{fields['benchmark']}:{fields['dataset_id']}"
            group_key = fields["benchmark"], fields["related_group_id"]
            old = groups.setdefault(group_key, fields["partition"])
            if old != fields["partition"]:
                raise ValueError(f"History/Development group leakage: {group_key}")
            unresolved.append({**fields, "disposition": "not_attempted_no_prepared_verifier_input"})
            all_ids.add(fields["candidate_id"])
    rows.sort(key=lambda r: (r["partition"], r["benchmark"], r["candidate_id"]))
    unresolved.sort(key=lambda r: (r["partition"], r["benchmark"], r["candidate_id"]))
    return rows, unresolved


def build_manifest(prepared_dir: Path, setup: MeasurementSetup, config_path: Path, rows, unresolved):
    inputs = [prepared_dir / "history_prepared.jsonl", prepared_dir / "development_prepared.jsonl",
              prepared_dir / "excluded_unresolved.jsonl"]
    return {
        "version": VERSION,
        "execution_configuration_id": setup.resources.manifest_id,
        "measurement_setup_fingerprint": setup.fingerprint,
        "resource_manifest": setup.resources.model_dump(mode="json"),
        "source_files": {display_path(p): sha256_file(p) for p in inputs},
        "adapter_configuration_sha256": sha256_file(config_path),
        "code_revision": setup.code_revision,
        "application_source_digest": setup.application_source_digest,
        "runtime_environment": setup.environment,
        "dependency_versions": setup.dependency_versions,
        "verifiers": list(VERIFIERS),
        "adapter_versions": ADAPTERS,
        "candidate_count_with_verifier_input": len(rows),
        "unresolved_candidate_count_not_attempted": len(unresolved),
        "candidate_roster_sha256": content_id([(r["candidate_id"], r["partition"], r["related_group_id"],
                                                  r["verifier_input_sha256"]) for r in rows]),
        "final_test_accessed": False,
        "labels_or_gold_sent_to_verifiers": False,
        "offline_examples_constructed": 0,
        "policy_fitting_performed": False,
    }


def read_jsonl_map(path: Path):
    result = {}
    if not path.exists():
        return result
    for row in jsonl_rows(path):
        key = row["candidate_id"], row["attempt"]["verifier_name"]
        if key in result:
            raise ValueError(f"duplicate completed attempt {key}")
        attempt = Attempt.model_validate(row["attempt"])
        result[key] = {**row, "attempt": attempt.model_dump(mode="json")}
    return result


def record_one(row, verifier, resource, configuration_id):
    verifier_name = verifier.name
    candidate_id = row["candidate_id"]
    execution_id = content_id([VERSION, candidate_id])
    durations = []
    timed = TimedVerifier(verifier, durations)
    state, report_json, error = "failed", None, None
    timing_status = "failure"
    started = time.perf_counter()
    try:
        raw = timed.verify(row["verifier_input"]["question"], row["verifier_input"]["candidate_answer"],
                           row["verifier_input"]["context"])
        if not isinstance(raw, VerificationResult):
            raise TypeError("verifier returned a non-VerificationResult")
        if raw.verifier_name != verifier_name:
            raise ValueError("verifier report identity mismatch")
        state = "abstention" if is_abstention(raw) else "directional"
        report_json = raw.model_dump_json()
        timing_status = "returned"
    except VerifierUnavailable as exc:
        state = "unavailable"
        timing_status = "failure"
        error = {"type": type(exc).__name__, "message": str(exc)}
    except TimeoutError as exc:
        state = "failed"
        timing_status = "timeout"
        error = {"type": type(exc).__name__, "message": str(exc)}
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as exc:
        state = "failed"
        error = {"type": type(exc).__name__, "message": str(exc)}
    duration_ms = durations[0] if durations else (time.perf_counter() - started) * 1000.0
    provenance = canonical_json({"runner": VERSION, "adapter": ADAPTERS[verifier_name],
                                 "candidate_id": candidate_id, "input_sha256": row["verifier_input_sha256"],
                                 "outcome": state, "error": error})
    attempt = Attempt(verifier_name=verifier_name, state=state, report_json=report_json,
                      execution_id=execution_id, configuration_id=configuration_id,
                      report_provenance=provenance, adapter=ADAPTERS[verifier_name],
                      observed_resources_json=canonical_json(resource.model_dump(mode="json")))
    return {"candidate_id": candidate_id, "dataset_id": row["dataset_id"],
            "question_id": row["question_id"], "related_group_id": row["related_group_id"],
            "benchmark": row["benchmark"], "partition": row["partition"],
            "verifier_input_sha256": row["verifier_input_sha256"],
            "duration_ms": duration_ms, "timing_status": timing_status,
            "attempt": attempt.model_dump(mode="json")}


def validate_output(output_dir: Path, prepared_dir: Path):
    rows, unresolved = load_roster(prepared_dir)
    manifest = json.loads((output_dir / "execution_manifest.json").read_text(encoding="utf-8"))
    expected_source_files = {display_path(p): sha256_file(p) for p in
        (prepared_dir / "history_prepared.jsonl", prepared_dir / "development_prepared.jsonl",
         prepared_dir / "excluded_unresolved.jsonl")}
    if manifest["source_files"] != expected_source_files:
        raise ValueError("prepared source files changed since execution manifest creation")
    if manifest["final_test_accessed"] or manifest["labels_or_gold_sent_to_verifiers"]:
        raise ValueError("manifest violates protected-input boundary")
    records = read_jsonl_map(output_dir / "attempts.jsonl")
    expected = {(r["candidate_id"], name) for r in rows for name in VERIFIERS}
    if set(records) - expected:
        raise ValueError("attempt output contains unknown candidate/verifier")
    identities = {r["candidate_id"]: r for r in rows}
    for key, wrapper in records.items():
        attempt = Attempt.model_validate(wrapper["attempt"])
        r = identities[key[0]]
        for field in ("dataset_id", "question_id", "related_group_id", "benchmark", "partition"):
            if wrapper[field] != r[field]:
                raise ValueError(f"attempt identity mismatch for {key}: {field}")
        if attempt.configuration_id != manifest["execution_configuration_id"]:
            raise ValueError("attempt configuration does not match manifest")
        if attempt.adapter != ADAPTERS[key[1]]:
            raise ValueError("attempt adapter mismatch")
        if wrapper["duration_ms"] < 0:
            raise ValueError("negative measured duration")
    unresolved_out = list(jsonl_rows(output_dir / "unresolved_not_attempted.jsonl"))
    if unresolved_out != unresolved:
        raise ValueError("unresolved candidate ledger differs from prepared inputs")
    summary = {"valid": True, "expected_attempts": len(expected), "recorded_attempts": len(records),
               "candidates_with_verifier_input": len(rows), "unresolved_not_attempted": len(unresolved),
               "attempts_by_verifier": {v: sum(k[1] == v for k in records) for v in VERIFIERS},
               "failures_by_verifier": {v: sum(k[1] == v and x["attempt"]["state"] in {"failed", "unavailable"}
                                                   for k, x in records.items()) for v in VERIFIERS},
               "returned_reports_by_verifier": {v: sum(k[1] == v and x["attempt"]["state"] in {"directional", "abstention"}
                                                         for k, x in records.items()) for v in VERIFIERS},
               "pending_attempts": len(expected - set(records)),
               "offline_examples_constructed": 0, "final_test_accessed": False}
    return summary


def run(prepared_dir: Path, output_dir: Path, *, resume=False):
    rows, unresolved = load_roster(prepared_dir)
    config_raw = os.environ.get("VERIFIER_COLLECTION_ADAPTER_CONFIG")
    if not config_raw or not Path(config_raw).is_file():
        raise RuntimeError("VERIFIER_COLLECTION_ADAPTER_CONFIG must point to a reviewed, locally pinned project adapter JSON")
    config_path = Path(config_raw).resolve()
    from app.benchmark.project_adapter import (AdapterConfiguration, create_verifiers,
                                                inspect_setup, read_json)
    config = AdapterConfiguration.model_validate(read_json(config_path))
    preflight = inspect_setup(config)
    if not preflight.get("ready"):
        raise RuntimeError("verifier resource preflight failed: " + json.dumps(preflight.get("blockers"), sort_keys=True))
    verifiers, setup = create_verifiers()
    setup = MeasurementSetup.model_validate(setup)
    pool = {v.name: v for v in verifiers}
    if set(pool) != set(VERIFIERS):
        raise RuntimeError("project adapter did not construct exactly the four required verifiers")
    resource_manifest = setup.resources
    resource_manifest.require_candidates(pool)
    manifest = build_manifest(prepared_dir, setup, config_path, rows, unresolved)
    if output_dir.exists():
        if not resume:
            raise FileExistsError("output exists; pass --resume to continue the same run")
        old = json.loads((output_dir / "execution_manifest.json").read_text(encoding="utf-8"))
        if old != manifest:
            raise ValueError("resume refused: source/resource/code manifest changed")
    else:
        output_dir.mkdir(parents=True)
        (output_dir / "execution_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        with (output_dir / "unresolved_not_attempted.jsonl").open("x", encoding="utf-8") as f:
            for row in unresolved:
                f.write(json.dumps(row, sort_keys=True, separators=(",", ":"))+"\n")
    records = read_jsonl_map(output_dir / "attempts.jsonl")
    mode = "a" if (output_dir / "attempts.jsonl").exists() else "x"
    with (output_dir / "attempts.jsonl").open(mode, encoding="utf-8") as stream:
        for row in rows:
            for name in VERIFIERS:
                if (row["candidate_id"], name) in records:
                    continue
                attempt_row = record_one(row, pool[name], next(x for x in resource_manifest.verifiers if x.verifier_name == name),
                                         resource_manifest.manifest_id)
                stream.write(json.dumps(attempt_row, sort_keys=True, separators=(",", ":"))+"\n")
                stream.flush()
                records[(row["candidate_id"], name)] = attempt_row
    summary = validate_output(output_dir, prepared_dir)
    (output_dir / "validation_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "validate"))
    parser.add_argument("--prepared-dir", type=Path, default=PREPARED_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            print(json.dumps(validate_output(args.output_dir, args.prepared_dir), indent=2))
        else:
            print(json.dumps(run(args.prepared_dir, args.output_dir, resume=args.resume), indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"valid_or_complete": False, "error_type": type(exc).__name__, "message": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
