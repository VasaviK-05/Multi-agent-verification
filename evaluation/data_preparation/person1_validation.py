"""Person 1 dataset/split validation and Development roster generation for research_v1.

Reads research_v1 History/Development candidates, the provisional Final Test
evaluation roster and manifests, and existing result files. The Final Test
custodian label payload is never parsed: only its byte hash is compared.

    python -m evaluation.data_preparation.person1_validation generate [--output DIR]
    python -m evaluation.data_preparation.person1_validation validate [--output DIR]

`generate` refuses an existing output directory. Any change to rosters, labels,
membership or hashes requires a new versioned output directory.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
import typing
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / "evaluation/datasets"
RECONCILED = DATASETS / "reconciled_candidates/research_v1"
PREPARED = DATASETS / "offline_examples/research_v1"
FINAL_EVAL = DATASETS / "final_test_research_v1_eval_v1"
FINAL_CUSTODIAN = DATASETS / "_custodian/final_test_research_v1_v1"
DEFAULT_OUTPUT = DATASETS / "person1/research_v1_person1_v1"
VERSION = "research_v1_person1_v1"
ORDERING_SALT = {"person2_cost_collection": "research_v1/person2_cost_collection_order/v1",
                 "live_runtime_validation": "research_v1/live_runtime_validation_order/v1"}

BENCHMARKS = ("GSM8K", "HotpotQA")
PARTITIONS = ("history", "development")
STATUSES = ("verified_correct", "verified_incorrect", "unresolved")
BINARY = {"verified_correct": True, "verified_incorrect": False}
SOURCE_VERSIONS = {
    "GSM8K": "openai/gsm8k main@740312add88f781978c0658806c59bc2815b9866",
    "HotpotQA": "hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab",
}
EVIDENCE_CORPORA = {
    "data/articles_13083.json": "b26539d013201a0435884098ae8bd3544342d0a815964bf104b9524808e9bfa8",
    "data/evidence_corpus.json": "668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5",
}
# Counts frozen in research_v1 manifests and the Person 1 leakage audit; recomputed, never assumed.
EXPECTED = {
    "groups": 1000, "candidates": 2050,
    "candidates_by_benchmark": {"GSM8K": 1000, "HotpotQA": 1050},
    "candidates_by_partition": {"history": 1240, "development": 810},
    "labels": {"verified_correct": 964, "verified_incorrect": 215, "unresolved": 871},
    "hotpot_generation": {"benchmark_gold": 500, "synthetic_cross_example_answer": 500,
                          "explicit_negation_of_context_supported_benchmark_answer": 50},
    "prepared": {"history": 701, "development": 478}, "excluded_unresolved": 871,
    "development_eligible_groups": 387, "development_groups_without_binary": 13,
    "hotpot_context_leakage": {"context_hashes": 25, "paragraph_texts": 14, "titles": 14, "supporting_facts": 2},
    "final_test_groups": {"GSM8K": 1319, "HotpotQA": 1319}, "final_test_candidates": 2638,
}
FINAL_TEST_LABEL_FIELDS = {"correctness_status", "answer_is_correct", "gold_answer", "binary_label", "expected_correct", "label"}
RESULT_FILES = ("evaluation/results/rule_gsm8k_results.json", "evaluation/results/evidence_hotpotqa_results.json",
                "evaluation/results/baseline/baseline_results.jsonl")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def jsonl_bytes(rows: Iterable[dict]) -> bytes:
    return b"".join((json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode() for r in rows)


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def check(name: str, status: str, evidence: Any, *, detail: str = "") -> dict:
    if status not in {"PASS", "FAIL", "BLOCKED", "NOT APPLICABLE"}:
        raise ValueError(status)
    return {"check": name, "status": status, "evidence": evidence, "detail": detail}


def _nested(row: dict) -> dict:
    return row.get("source_candidate_record") or {}


def _provenance(row: dict) -> dict:
    nested = _nested(row)
    return ((row.get("validation_basis") or {}).get("evidence_provenance") or nested.get("evidence_provenance") or {})


def load_research_v1(directory: Path = RECONCILED) -> dict[str, list[dict]]:
    return {p: read_jsonl(directory / f"{p}_candidates.jsonl") for p in PARTITIONS}


# --- research_v1 composition, duplicates, provenance -------------------------------------------

def composition(rows: dict[str, list[dict]]) -> dict:
    from evaluation.data_preparation.final_test_workflow import group_id
    allrows = [r for p in PARTITIONS for r in rows[p]]
    out: dict[str, Any] = {
        "candidates": len(allrows),
        "candidates_by_benchmark": dict(collections.Counter(r["benchmark"] for r in allrows)),
        "candidates_by_partition": {p: len(rows[p]) for p in PARTITIONS},
        "labels": {s: sum(r["correctness_status"] == s for r in allrows) for s in STATUSES},
        "labels_by_partition_benchmark": {f"{p}:{b}": {s: sum(r["benchmark"] == b and r["correctness_status"] == s for r in rows[p])
                                                      for s in STATUSES} for p in PARTITIONS for b in BENCHMARKS},
        "groups": len({r["related_group_id"] for r in allrows}),
        "groups_by_partition_benchmark": {f"{p}:{b}": len({r["related_group_id"] for r in rows[p] if r["benchmark"] == b})
                                          for p in PARTITIONS for b in BENCHMARKS},
        "generation_methods": {b: dict(collections.Counter(r["candidate_generation_method"] for r in allrows if r["benchmark"] == b))
                               for b in BENCHMARKS},
        "unknown_statuses": sorted({r["correctness_status"] for r in allrows} - set(STATUSES)),
    }
    candidate_ids = [r["candidate_id"] for r in allrows]
    group_partition: dict[str, set[str]] = collections.defaultdict(set)
    group_question: dict[str, set[str]] = collections.defaultdict(set)
    for p in PARTITIONS:
        for r in rows[p]:
            if r.get("partition") != p:
                raise ValueError(f"record partition field differs from file partition: {r['candidate_id']}")
            group_partition[r["related_group_id"]].add(p)
            group_question[r["related_group_id"]].add(r["dataset_id"])
    out["duplicates"] = {
        "duplicate_candidate_ids": len(candidate_ids) - len(set(candidate_ids)),
        "groups_in_multiple_partitions": sum(len(v) > 1 for v in group_partition.values()),
        "groups_with_multiple_source_questions": sum(len(v) > 1 for v in group_question.values()),
        "stored_group_id_mismatches": sum(r["related_group_id"] != group_id(r["benchmark"], r["question"]) for r in allrows),
    }
    out["provenance"] = {
        "source_version_mismatches": sum(r.get("dataset_version") != SOURCE_VERSIONS[r["benchmark"]] for r in allrows),
        "binary_without_validation_method": sum(r["correctness_status"] in BINARY and not r.get("validation_method") for r in allrows),
        "unresolved_without_reason": sum(r["correctness_status"] == "unresolved"
                                         and not ((r.get("validation_basis") or {}).get("unresolved_reason") or _nested(r).get("unresolved_reason"))
                                         for r in allrows),
        "human_review_claimed": sum(bool(_nested(r).get("independent_human_review")) for r in allrows),
    }
    return out


def prepared_consistency(rows: dict[str, list[dict]], prepared_dir: Path = PREPARED) -> dict:
    status = {r["candidate_id"]: r["correctness_status"] for p in PARTITIONS for r in rows[p]}
    out: dict[str, Any] = {"prepared": {}, "label_mismatches": 0, "prepared_not_binary": 0, "binary_missing_from_prepared": 0}
    for p in PARTITIONS:
        prepared = read_jsonl(prepared_dir / f"{p}_prepared.jsonl")
        out["prepared"][p] = len(prepared)
        ids = {r["candidate_id"] for r in prepared}
        for r in prepared:
            s = status.get(r["candidate_id"])
            if s not in BINARY:
                out["prepared_not_binary"] += 1
            elif r.get("answer_is_correct") is not BINARY[s]:
                out["label_mismatches"] += 1
        out["binary_missing_from_prepared"] += sum(1 for r in rows[p] if r["correctness_status"] in BINARY and r["candidate_id"] not in ids)
    excluded = read_jsonl(prepared_dir / "excluded_unresolved.jsonl")
    out["excluded_unresolved"] = len(excluded)
    out["excluded_not_unresolved"] = sum(status.get(r["candidate_id"]) != "unresolved" for r in excluded)
    out["excluded_with_binary_label"] = sum(r.get("answer_is_correct") is not None for r in excluded)
    return out


def recorded_hashes(manifest_path: Path = RECONCILED / "manifest.json") -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches = []
    for directory, key in ((RECONCILED, "output_sha256"), (PREPARED, "offline_output_sha256")):
        for name, digest in manifest.get(key, {}).items():
            path = directory / name
            if not path.is_file() or sha256_file(path) != digest:
                mismatches.append(rel(path))
    for relative, digest in manifest.get("source_sha256", {}).items():
        path = ROOT / relative
        if not path.is_file() or sha256_file(path) != digest:
            mismatches.append(relative)
    core = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    from evaluation.data_preparation.build_research_dataset import json_bytes
    self_hash_ok = any(sha256_bytes(fn(core)) == manifest.get("manifest_sha256") for fn in (json_bytes, canonical_bytes))
    return {"checked_files": len(manifest.get("output_sha256", {})) + len(manifest.get("offline_output_sha256", {})) + len(manifest.get("source_sha256", {})),
            "mismatches": mismatches, "manifest_sha256": manifest.get("manifest_sha256"), "manifest_self_hash_verified": self_hash_ok,
            "final_test_records_or_identities_accessed": manifest.get("final_test_records_or_identities_accessed"),
            "policy_fitting_ready": manifest.get("policy_fitting_ready"), "attempt_records": manifest.get("attempt_records"),
            "complete_offline_examples": manifest.get("complete_offline_examples")}


# --- History/Development leakage ----------------------------------------------------------------

def _hotpot_sets(rows: list[dict]) -> dict[str, dict[str, set[str]]]:
    """Per value, the set of groups carrying it, so shared values can be attributed to groups."""
    sets: dict[str, dict[str, set[str]]] = {k: collections.defaultdict(set) for k in ("context_hashes", "paragraph_texts", "titles", "supporting_facts")}
    for r in rows:
        if r["benchmark"] != "HotpotQA":
            continue
        g = r["related_group_id"]
        prov = _provenance(r)
        original = _nested(r).get("original_unified_source_record") or {}
        for h in prov.get("context_hashes") or []:
            sets["context_hashes"][h].add(g)
        for item in original.get("context") or []:
            if isinstance(item, dict) and item.get("text"):
                sets["paragraph_texts"][sha256_bytes(str(item["text"]).encode())].add(g)
                if item.get("title"):
                    sets["titles"][str(item["title"])].add(g)
        for fact in prov.get("supporting_facts") or original.get("supporting_facts") or []:
            if isinstance(fact, dict):
                sets["supporting_facts"][f"{fact.get('title')}\0{fact.get('sentence_id')}"].add(g)
    return sets


def history_development_leakage(rows: dict[str, list[dict]]) -> dict:
    from evaluation.data_preparation.final_test_workflow import norm_question
    identity = {}
    for b in BENCHMARKS:
        h = [r for r in rows["history"] if r["benchmark"] == b]
        d = [r for r in rows["development"] if r["benchmark"] == b]
        fields = {"group_ids": lambda r: r["related_group_id"], "dataset_ids": lambda r: r["dataset_id"],
                  "candidate_ids": lambda r: r["candidate_id"], "raw_questions": lambda r: r["question"],
                  "normalized_questions": lambda r: norm_question(r["question"]),
                  "source_ids": lambda r: _provenance(r).get("source_id")}
        identity[b] = {k: len({f(r) for r in h if f(r)} & {f(r) for r in d if f(r)}) for k, f in fields.items()}
        donors_h = {_provenance(r).get("donor_dataset_id") for r in h} - {None}
        donors_d = {_provenance(r).get("donor_dataset_id") for r in d} - {None}
        identity[b]["donor_cross_partition"] = len(donors_h & {r["dataset_id"] for r in d}) + len(donors_d & {r["dataset_id"] for r in h})
    hs, ds = _hotpot_sets(rows["history"]), _hotpot_sets(rows["development"])
    context = {}
    for key in hs:
        shared = set(hs[key]) & set(ds[key])
        context[key] = {"shared_values": len(shared),
                        "history_groups": len(set().union(*(hs[key][v] for v in shared))) if shared else 0,
                        "development_groups": len(set().union(*(ds[key][v] for v in shared))) if shared else 0}
    shared_facts = sorted(v.replace("\0", "#") for v in set(hs["supporting_facts"]) & set(ds["supporting_facts"]))
    return {"identity_overlaps": identity, "hotpot_context_overlaps": context, "shared_supporting_facts": shared_facts,
            "semantic_paraphrase_leakage": "NOT AUDITED"}


# --- Development rosters ------------------------------------------------------------------------

def _order_key(salt: str, value: str) -> str:
    return sha256_bytes(f"{salt}\0{value}".encode())


def development_rosters(rows: dict[str, list[dict]]) -> dict[str, list[dict]]:
    dev = rows["development"]
    by_group: dict[str, list[dict]] = collections.defaultdict(list)
    for r in dev:
        by_group[r["related_group_id"]].append(r)
    groups, ineligible, candidates = [], [], []
    for g in sorted(by_group):
        members = sorted(by_group[g], key=lambda r: r["candidate_id"])
        counts = collections.Counter(r["correctness_status"] for r in members)
        entry = {"related_group_id": g, "benchmark": members[0]["benchmark"], "dataset_id": members[0]["dataset_id"],
                 "candidate_count": len(members), **{s: counts.get(s, 0) for s in STATUSES}}
        binary = [r for r in members if r["correctness_status"] in BINARY]
        if binary:
            groups.append({**entry, "eligible_candidate_count": len(binary)})
            candidates.extend({"candidate_id": r["candidate_id"], "related_group_id": g, "benchmark": r["benchmark"],
                               "dataset_id": r["dataset_id"], "correctness_status": r["correctness_status"],
                               "answer_is_correct": BINARY[r["correctness_status"]],
                               "candidate_generation_method": r["candidate_generation_method"],
                               "validation_method": r.get("validation_method")} for r in binary)
        else:
            ineligible.append({**entry, "reason": "no_binary_labelled_candidate"})
    return {"groups": groups, "candidates": candidates, "ineligible_groups": ineligible}


def ordered_group_roster(eligible_groups: list[dict], eligible_candidates: list[dict], salt: str) -> list[dict]:
    """Groups ordered by salted hash, alternating benchmarks; every prefix stays group-complete and near-balanced.

    The order uses only identifiers, never labels or outcomes. Roster size is not chosen here.
    """
    queues = {b: sorted((g for g in eligible_groups if g["benchmark"] == b), key=lambda g: _order_key(salt, g["related_group_id"]))
              for b in BENCHMARKS}
    members: dict[str, list[dict]] = collections.defaultdict(list)
    for c in eligible_candidates:
        members[c["related_group_id"]].append(c)
    out, rank = [], 0
    for i in range(max(len(q) for q in queues.values())):
        for b in BENCHMARKS:
            if i < len(queues[b]):
                g = queues[b][i]
                rank += 1
                for c in sorted(members[g["related_group_id"]], key=lambda c: c["candidate_id"]):
                    out.append({"group_rank": rank, "related_group_id": g["related_group_id"], "benchmark": b,
                                "candidate_id": c["candidate_id"], "order_key": _order_key(salt, g["related_group_id"])})
    return out


def unresolved_queue(rows: dict[str, list[dict]]) -> list[dict]:
    queue = []
    for p in PARTITIONS:
        for r in rows[p]:
            if r["correctness_status"] != "unresolved":
                continue
            basis = r.get("validation_basis") or {}
            queue.append({"candidate_id": r["candidate_id"], "related_group_id": r["related_group_id"], "benchmark": r["benchmark"],
                          "partition": p, "dataset_id": r["dataset_id"], "candidate_generation_method": r["candidate_generation_method"],
                          "unresolved_reason": basis.get("unresolved_reason") or _nested(r).get("unresolved_reason"),
                          "review_status": "PENDING_INDEPENDENT_HUMAN_REVIEW", "assigned_label": None, "reviewer": None})
    return sorted(queue, key=lambda q: (q["partition"], q["benchmark"], q["candidate_id"]))


# --- Final Test isolation (label payload is never parsed) --------------------------------------

def final_test_isolation(rows: dict[str, list[dict]], eval_dir: Path = FINAL_EVAL, custodian_dir: Path = FINAL_CUSTODIAN) -> dict:
    from evaluation.data_preparation.final_test_workflow import audit_leakage, canonical_bytes as ft_canonical
    manifest_path = eval_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    core = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    roster = read_jsonl(eval_dir / "evaluation_roster.jsonl")
    receipt = json.loads((eval_dir / "integrity_receipt.json").read_text(encoding="utf-8"))
    label_file = custodian_dir / "custodian_labels.jsonl"
    audit_file = eval_dir / "leakage_audit.json"
    out = {
        "manifest_sha256": manifest.get("manifest_sha256"),
        "manifest_self_hash_verified": sha256_bytes(ft_canonical(core)) == manifest.get("manifest_sha256"),
        "custodian_manifest_identical": sha256_file(custodian_dir / "manifest.json") == sha256_file(manifest_path),
        "evaluation_roster_hash_verified": sha256_file(eval_dir / "evaluation_roster.jsonl") == manifest.get("evaluation_roster_sha256"),
        "label_payload_byte_hash_verified": sha256_file(label_file) == manifest.get("label_file_sha256"),
        "label_payload_parsed": False,
        "leakage_audit_hash_verified": sha256_file(audit_file) == manifest.get("leakage_audit_sha256"),
        "integrity_receipt_verified": receipt == json.loads((custodian_dir / "integrity_receipt.json").read_text(encoding="utf-8")) and all(
            sha256_file(p) == receipt[k] for k, p in (("evaluation_roster.jsonl", eval_dir / "evaluation_roster.jsonl"),
                                                      ("leakage_audit.json", audit_file), ("evaluation_manifest.json", manifest_path),
                                                      ("custodian_labels.jsonl", label_file), ("custodian_manifest.json", custodian_dir / "manifest.json"))),
        "source_hash_mismatches": [k for k, v in manifest.get("source_sha256", {}).items() if not (ROOT / k).is_file() or sha256_file(ROOT / k) != v],
        "status": manifest.get("status"), "enabled": manifest.get("enabled"), "freeze_status": manifest.get("freeze_status"),
        "custody": manifest.get("custody"),
        "roster_rows": len(roster),
        "roster_groups": {b: len({r["related_group_id"] for r in roster if r["benchmark"] == b}) for b in BENCHMARKS},
        "roster_candidates": {b: sum(r["benchmark"] == b for r in roster) for b in BENCHMARKS},
        "roster_generation_methods": dict(collections.Counter(r["candidate_generation_method"] for r in roster)),
        "roster_duplicate_candidate_ids": len(roster) - len({r["candidate_id"] for r in roster}),
        "roster_duplicate_groups": len(roster) - len({r["related_group_id"] for r in roster}),
        "roster_label_fields_present": sorted(FINAL_TEST_LABEL_FIELDS & set().union(*(r.keys() for r in roster))),
        "roster_source_splits": dict(collections.Counter(f"{r['benchmark']}:{r['source_split']}" for r in roster)),
        "roster_source_version_mismatches": sum(r["source_version"] != SOURCE_VERSIONS[r["benchmark"]] for r in roster),
        "manifest_ids_match_roster": set(manifest.get("candidate_ids", [])) == {r["candidate_id"] for r in roster}
                                     and set(manifest.get("group_ids", [])) == {r["related_group_id"] for r in roster},
        "manifest_aggregate_label_counts": manifest.get("combined_label_counts"),
    }
    current = audit_leakage(roster, rows["history"], rows["development"])
    out["recomputed_leakage_comparisons"] = current["comparisons"]
    out["recomputed_matches_frozen_audit"] = current["comparisons"] == (manifest.get("leakage_audit") or {}).get("comparisons")
    return out


# --- Teammate result compatibility (read-only) -------------------------------------------------

def _result_ids(path: Path) -> list[str]:
    if path.suffix == ".jsonl":
        return [r.get("example_id") for r in read_jsonl(path)]
    data = json.loads(path.read_text(encoding="utf-8"))
    return [r.get("example_id") or r.get("id") for r in data.get("results", [])]


def teammate_compatibility(rows: dict[str, list[dict]], final_roster: list[dict]) -> dict:
    history_ids = {r["dataset_id"] for r in rows["history"]}
    development_ids = {r["dataset_id"] for r in rows["development"]}
    final_ids = {r["question_id"] for r in final_roster} | {r["source_id"] for r in final_roster}
    report = {"seven_hundred_result_artifact_identified": False, "files": {}}
    for relative in RESULT_FILES:
        path = ROOT / relative
        if not path.is_file():
            report["files"][relative] = {"present": False}
            continue
        ids = [i for i in _result_ids(path) if i]
        unique = set(ids)
        report["files"][relative] = {
            "present": True, "sha256": sha256_file(path), "rows": len(ids), "unique_question_ids": len(unique),
            "overlap_research_v1_history_questions": len(unique & history_ids),
            "overlap_research_v1_development_questions": len(unique & development_ids),
            "overlap_final_test_questions": len(unique & final_ids),
        }
    report["note"] = ("No result artifact with ~700 rows and an owner record was found in evaluation/results, "
                      "dataset directories, git branches inspected, or the application database. Files are read only.")
    return report


# --- Experiment input contracts -----------------------------------------------------------------

def attack_kinds() -> list[str]:
    from app.game.offline.attacks import Attack
    return list(typing.get_args(Attack.model_fields["kind"].annotation))


def estimability(rows: dict[str, list[dict]]) -> dict:
    out = {}
    for p in PARTITIONS:
        for b in BENCHMARKS:
            c = collections.Counter(r["correctness_status"] for r in rows[p] if r["benchmark"] == b)
            out[f"{p}:{b}"] = {
                "false_acceptance_rate": "ESTIMABLE_AFTER_ATTEMPTS" if c["verified_incorrect"] else "NOT ESTIMABLE: 0 verified incorrect candidates",
                "false_rejection_rate": "ESTIMABLE_AFTER_ATTEMPTS" if c["verified_correct"] else "NOT ESTIMABLE: 0 verified correct candidates",
                "coverage_abstention_selective_risk": "ESTIMABLE_AFTER_ATTEMPTS; selective risk undefined when coverage is zero",
                "validation_loss": "BLOCKED: requires approved loss weights and verifier Attempts",
                "estimated_attempt_cost": "BLOCKED: requires Person 2 cost schedule",
                "worst_case_expected_loss": "BLOCKED: requires Attempts, approved loss, attack specification and policies",
                "verified_correct": c["verified_correct"], "verified_incorrect": c["verified_incorrect"], "unresolved": c["unresolved"],
            }
    return out


def experiment_contracts(roster_hashes: dict, rows: dict[str, list[dict]], final_manifest_sha256: str) -> dict:
    pending = {"value": None, "status": "PENDING_APPROVAL"}
    common = {"history_input": "evaluation/datasets/offline_examples/research_v1/history_prepared.jsonl",
              "development_input": "evaluation/datasets/offline_examples/research_v1/development_prepared.jsonl",
              "development_eligible_candidates_sha256": roster_hashes["development_eligible_candidates.jsonl"],
              "unit_of_resampling": "related_group_id", "unresolved_candidates": "excluded; never scored as incorrect",
              "final_test": {"manifest_sha256": final_manifest_sha256, "status": "NOT_AUTHORIZED",
                             "use": "frozen single evaluation only after approvals; never for tuning, fitting, thresholds, reputation or configuration"},
              "required_recorded_fields_per_attempt": ["candidate_id", "verifier_name", "execution_state", "report", "estimated_attempt_cost",
                                                       "resource_manifest_identity"],
              "loss_configuration": pending, "decision_threshold": pending, "minimum_contributors": pending,
              "coverage_constraint": pending}
    return {
        "version": VERSION, "dataset_version": "research_v1", "estimability": estimability(rows),
        "experiments": {
            "1_clean_and_attacked": {**common, "attack_scenarios": attack_kinds(), "attack_specification_version": "report_corruption_v1",
                                     "attack_labels_in_dataset": "none; attacks are replay transformations of recorded Attempts",
                                     "methods": ["full_minimax", "uniform", "deterministic_minimax", "clean_development",
                                                 "fixed_reputation_weighted", "fixed_dependency_group", "coverage_aware_greedy"]},
            "2_budget_sensitivity": {**common, "budgets": {"values": None, "minimum_count": 3, "units": "Person 2 cost units",
                                                         "status": "PENDING_APPROVAL"}},
            "3_aggregation_and_dependency_ablation": {**common, "aggregations": ["reputation_weighted", "dependency_group"],
                                                      "dependency_labels_in_dataset": "none; dependency structure comes from the verifier registry",
                                                      "correlated_failure_labels": "none; not fabricated"},
            "4_live_runtime_validation": {**common, "roster": "live_runtime_validation_order.jsonl",
                                          "roster_sha256": roster_hashes["live_runtime_validation_order.jsonl"],
                                          "size": pending, "partition": "development",
                                          "blocker": "VERIFIER_COLLECTION_ADAPTER_CONFIG unset; no verifier execution possible"},
        },
    }


# --- Orchestration ------------------------------------------------------------------------------

def evaluate() -> tuple[list[dict], dict[str, bytes], dict]:
    rows = load_research_v1()
    comp = composition(rows)
    prep = prepared_consistency(rows)
    hashes = recorded_hashes()
    leak = history_development_leakage(rows)
    ft = final_test_isolation(rows)
    final_roster = read_jsonl(FINAL_EVAL / "evaluation_roster.jsonl")
    rosters = development_rosters(rows)
    cost_order = ordered_group_roster(rosters["groups"], rosters["candidates"], ORDERING_SALT["person2_cost_collection"])
    live_order = ordered_group_roster(rosters["groups"], rosters["candidates"], ORDERING_SALT["live_runtime_validation"])
    queue = unresolved_queue(rows)
    teammate = teammate_compatibility(rows, final_roster)
    corpora = {k: (sha256_file(ROOT / k) if (ROOT / k).is_file() else None) for k in EVIDENCE_CORPORA}

    files = {
        "development_eligible_groups.jsonl": jsonl_bytes(rosters["groups"]),
        "development_eligible_candidates.jsonl": jsonl_bytes(rosters["candidates"]),
        "development_ineligible_groups.jsonl": jsonl_bytes(rosters["ineligible_groups"]),
        "person2_cost_collection_order.jsonl": jsonl_bytes(cost_order),
        "live_runtime_validation_order.jsonl": jsonl_bytes(live_order),
        "unresolved_review_queue.jsonl": jsonl_bytes(queue),
    }
    roster_hashes = {k: sha256_bytes(v) for k, v in files.items()}
    files["experiment_contracts.json"] = canonical_bytes(experiment_contracts(roster_hashes, rows, ft["manifest_sha256"]))
    files["teammate_compatibility.json"] = canonical_bytes(teammate)

    e = EXPECTED
    ident = leak["identity_overlaps"]
    ctx = {k: v["shared_values"] for k, v in leak["hotpot_context_overlaps"].items()}
    dev_final = {r["candidate_id"] for r in rosters["candidates"]} & {r["candidate_id"] for r in final_roster}
    checks = [
        check("research_v1 composition", "PASS" if (comp["groups"], comp["candidates"], comp["candidates_by_benchmark"], comp["candidates_by_partition"], comp["labels"])
              == (e["groups"], e["candidates"], e["candidates_by_benchmark"], e["candidates_by_partition"], e["labels"]) and not comp["unknown_statuses"] else "FAIL",
              {k: comp[k] for k in ("groups", "candidates", "candidates_by_benchmark", "candidates_by_partition", "labels")}),
        check("HotpotQA candidate generation", "PASS" if comp["generation_methods"]["HotpotQA"] == e["hotpot_generation"] else "FAIL", comp["generation_methods"]),
        check("duplicate IDs and group integrity", "PASS" if not any(comp["duplicates"].values()) else "FAIL", comp["duplicates"]),
        check("source provenance", "PASS" if not any(comp["provenance"][k] for k in ("source_version_mismatches", "binary_without_validation_method", "unresolved_without_reason")) else "FAIL",
              comp["provenance"]),
        check("evidence corpus identity", "PASS" if corpora == EVIDENCE_CORPORA else "FAIL", corpora),
        check("prepared labelled candidates", "PASS" if prep["prepared"] == e["prepared"] and prep["excluded_unresolved"] == e["excluded_unresolved"]
              and not (prep["label_mismatches"] or prep["prepared_not_binary"] or prep["binary_missing_from_prepared"] or prep["excluded_not_unresolved"] or prep["excluded_with_binary_label"]) else "FAIL", prep),
        check("research_v1 manifest hashes", "PASS" if not hashes["mismatches"] and hashes["manifest_self_hash_verified"] else "FAIL", hashes),
        check("History/Development identity leakage", "PASS" if not any(v for b in ident.values() for v in b.values()) else "FAIL", ident),
        check("HotpotQA shared-context counts reproduced", "PASS" if ctx == e["hotpot_context_leakage"] else "FAIL",
              {"counts": leak["hotpot_context_overlaps"], "shared_supporting_facts": leak["shared_supporting_facts"]},
              detail="Reproduction of the documented conditional-pass finding; the overlap itself is a documented limitation."),
        check("Development eligible roster", "PASS" if len(rosters["groups"]) == e["development_eligible_groups"] and len(rosters["ineligible_groups"]) == e["development_groups_without_binary"]
              and len(rosters["candidates"]) == e["prepared"]["development"] else "FAIL",
              {"eligible_groups": len(rosters["groups"]), "ineligible_groups": len(rosters["ineligible_groups"]), "eligible_candidates": len(rosters["candidates"])}),
        check("ordered rosters are label-free and group-complete", "PASS" if all(not ({"correctness_status", "answer_is_correct"} & set(r)) for r in cost_order + live_order)
              and len(cost_order) == len(live_order) == len(rosters["candidates"]) else "FAIL", {"rows": len(cost_order)}),
        check("unresolved review queue", "PASS" if len(queue) == e["labels"]["unresolved"] and all(q["assigned_label"] is None for q in queue) else "FAIL",
              dict(collections.Counter(f"{q['partition']}:{q['benchmark']}" for q in queue))),
        check("Final Test integrity hashes", "PASS" if all(ft[k] for k in ("manifest_self_hash_verified", "custodian_manifest_identical", "evaluation_roster_hash_verified",
              "label_payload_byte_hash_verified", "leakage_audit_hash_verified", "integrity_receipt_verified", "manifest_ids_match_roster")) and not ft["source_hash_mismatches"] else "FAIL",
              {k: ft[k] for k in ("manifest_sha256", "manifest_self_hash_verified", "evaluation_roster_hash_verified", "label_payload_byte_hash_verified",
                                  "label_payload_parsed", "integrity_receipt_verified", "source_hash_mismatches")}),
        check("Final Test composition", "PASS" if ft["roster_groups"] == e["final_test_groups"] and ft["roster_rows"] == e["final_test_candidates"]
              and ft["roster_generation_methods"] == {"benchmark_gold": e["final_test_candidates"]} and not ft["roster_duplicate_candidate_ids"]
              and not ft["roster_duplicate_groups"] and not ft["roster_source_version_mismatches"] else "FAIL",
              {k: ft[k] for k in ("roster_groups", "roster_candidates", "roster_generation_methods", "roster_source_splits")}),
        check("Final Test leakage against History/Development", "PASS" if ft["recomputed_matches_frozen_audit"] and not any(ft["recomputed_leakage_comparisons"].values()) and not dev_final else "FAIL",
              {"recomputed": ft["recomputed_leakage_comparisons"], "development_roster_final_overlap": len(dev_final)}),
        check("Final Test evaluation roster carries no label fields", "PASS" if not ft["roster_label_fields_present"] else "FAIL", ft["roster_label_fields_present"],
              detail="All roster candidates are benchmark-gold, so candidate_answer equals the gold answer; the roster is not answer-blind."),
        check("Final Test disabled and unauthorized", "PASS" if ft["status"] == "NOT_AUTHORIZED" and ft["enabled"] is False else "FAIL", {"status": ft["status"], "enabled": ft["enabled"]}),
        check("Final Test independent custody", "BLOCKED", ft["custody"], detail="No named custodian; OS-level protection not established."),
        check("teammate 700-result compatibility", "BLOCKED", {k: v.get("rows") for k, v in teammate["files"].items()}, detail=teammate["note"]),
        check("policy-fitting / experiment readiness", "BLOCKED", {k: hashes[k] for k in ("attempt_records", "complete_offline_examples", "policy_fitting_ready")},
              detail="No verifier Attempts; adapter configuration unset."),
    ]
    summary = {"version": VERSION, "checks": checks, "status_counts": dict(collections.Counter(c["status"] for c in checks)),
               "composition": comp, "leakage": leak, "final_test": {k: v for k, v in ft.items() if k != "custody"}, "prepared": prep}
    return checks, files, summary


def _receipt(files: dict[str, bytes], summary_bytes: bytes) -> dict:
    inputs = [RECONCILED / "history_candidates.jsonl", RECONCILED / "development_candidates.jsonl", RECONCILED / "manifest.json",
              PREPARED / "history_prepared.jsonl", PREPARED / "development_prepared.jsonl", PREPARED / "excluded_unresolved.jsonl",
              FINAL_EVAL / "evaluation_roster.jsonl", FINAL_EVAL / "manifest.json"]
    return {"version": VERSION, "generator_sha256": sha256_file(Path(__file__)),
            "input_sha256": {rel(p): sha256_file(p) for p in inputs},
            "output_sha256": {**{k: sha256_bytes(v) for k, v in files.items()}, "validation_summary.json": sha256_bytes(summary_bytes)},
            "ordering_salts": ORDERING_SALT, "final_test_label_payload_parsed": False}


def generate(output: Path = DEFAULT_OUTPUT) -> dict:
    if output.exists():
        raise FileExistsError(f"{output} exists; create a new versioned directory instead of overwriting")
    checks, files, summary = evaluate()
    summary_bytes = canonical_bytes(summary)
    receipt = _receipt(files, summary_bytes)
    output.mkdir(parents=True)
    for name, data in {**files, "validation_summary.json": summary_bytes, "manifest.json": canonical_bytes(receipt)}.items():
        with (output / name).open("xb") as f:
            f.write(data)
    return {"output": rel(output), "status_counts": summary["status_counts"], "failed": [c["check"] for c in checks if c["status"] == "FAIL"]}


def validate(output: Path = DEFAULT_OUTPUT) -> dict:
    """Recompute every artifact and compare with the frozen receipt; generated_at-free so it is exact."""
    receipt = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    checks, files, summary = evaluate()
    current = _receipt(files, canonical_bytes(summary))
    stored_mismatch = [k for k, v in receipt["output_sha256"].items() if not (output / k).is_file() or sha256_file(output / k) != v]
    recomputed_mismatch = [k for k in receipt["output_sha256"] if receipt["output_sha256"][k] != current["output_sha256"].get(k)]
    input_changes = [k for k in receipt["input_sha256"] if receipt["input_sha256"][k] != current["input_sha256"].get(k)]
    return {"output": rel(output), "status_counts": summary["status_counts"], "failed": [c["check"] for c in checks if c["status"] == "FAIL"],
            "stored_file_hash_mismatches": stored_mismatch, "recomputed_output_mismatches": recomputed_mismatch,
            "input_hash_changes": input_changes, "generator_changed": receipt["generator_sha256"] != current["generator_sha256"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("generate", "validate"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    result = generate(args.output) if args.command == "generate" else validate(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["failed"] or result.get("stored_file_hash_mismatches") or result.get("recomputed_output_mismatches"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
