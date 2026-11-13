"""Approved exploratory Development eligibility manifest.

Reads research_v1_exploratory_v1 only. It does not open Final Test labels, does
not modify the provisional eligibility audit, and does not authorize collection
or protocol freeze.

Shared History/Development reference paragraphs and supporting facts quarantine
the affected Development groups. Semantic duplicates are pairs at or above the
documented thresholds; pairs below those thresholds are not certified unrelated.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

from datasets import load_from_disk

from evaluation.data_preparation.build_exploratory_development import hotpot_source_id, load_raw_hotpot
from evaluation.data_preparation.build_verified_subset import normalize_numeric, replay_gsm_solution
from evaluation.data_preparation.exploratory_eligibility import _git_revision, _identity
from evaluation.data_preparation.final_test_workflow import (
    ROOT, canonical_bytes, context_hashes, jsonl_bytes, norm_question, read_jsonl, sha256_bytes, sha256_file,
)
from evaluation.data_preparation.label_classes import (
    HUMAN_VERIFIED_INCORRECT, PROTOCOL, SYNTHETIC_INCORRECT, UNRESOLVED, VERIFIED_CORRECT,
)

VERSION = "research_v1_exploratory_eligibility_approved_v1"
DATASET_VERSION = "research_v1_exploratory_v1"
SOURCE = ROOT / "evaluation/datasets/research_v1_exploratory" / DATASET_VERSION
OUTPUT = ROOT / "evaluation/artifacts/person1" / VERSION
LEAKAGE_PROTOCOL = "history_development_overlap_v1"
SEMANTIC_PROTOCOL = "normalized_token_jaccard_and_sequence_ratio_v1"
JACCARD_THRESHOLD = 0.80
SEQUENCE_THRESHOLD = 0.85
APPROVER = "Research Lead"
APPROVAL_DATE = "2026-11-13"
GSM_ID = re.compile(r"gsm8k_train_(\d+)$")
TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN.findall(text))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _one_per_group(rows: list[dict]) -> dict[str, dict]:
    chosen = {}
    for row in rows:
        chosen.setdefault(row["related_group_id"], row)
    return chosen


def _forbid(path: Path) -> None:
    text = str(path).replace("\\", "/").lower()
    if "final_test" in text or "_custodian" in text:
        raise RuntimeError(f"eligibility audit refused a Final Test path: {path}")


def _load_snapshot():
    _forbid(SOURCE)
    manifest_path = SOURCE / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dataset_version") != DATASET_VERSION:
        raise ValueError("source snapshot is not research_v1_exploratory_v1")
    labelled = {role: read_jsonl(SOURCE / f"{role}_candidates.jsonl") for role in ("history", "development")}
    unresolved = read_jsonl(SOURCE / "unresolved_candidates.jsonl")
    skipped = read_jsonl(SOURCE / "skipped_groups.jsonl")
    return manifest, labelled, unresolved, skipped


def _reference_checks(development: list[dict]) -> dict[str, dict]:
    """Re-check correct answers against local benchmark rows. Returns candidate_id -> result."""
    gsm_rows = [row for row in development if row["benchmark"] == "GSM8K" and row["label_class"] == VERIFIED_CORRECT]
    hot_rows = [row for row in development if row["benchmark"] == "HotpotQA" and row["label_class"] == VERIFIED_CORRECT]
    gsm = load_from_disk(str(ROOT / "evaluation/datasets/raw/gsm8k/train"))
    hot_ids = {hotpot_source_id(str((row.get("source") or {}).get("research_v1_dataset_id"))) for row in hot_rows}
    raw_hot = load_raw_hotpot(hot_ids, ROOT)
    results = {}
    for row in gsm_rows:
        source_id = str((row.get("source") or {}).get("research_v1_dataset_id"))
        match = GSM_ID.fullmatch(source_id)
        status = "failed"
        detail = "source id is not a GSM8K train index"
        if match:
            raw = gsm[int(match.group(1))]
            question_ok = norm_question(raw.get("question", "")) == norm_question(row["question"])
            replay = replay_gsm_solution(str(raw.get("answer", "")), str(row.get("gold_answer", "")))
            gold_ok = normalize_numeric(row.get("candidate_answer")) == normalize_numeric(row.get("gold_answer"))
            status = "passed" if question_ok and gold_ok and replay["status"] == "passed" else "failed"
            detail = "raw question, gold answer, and tagged-equation replay agree" if status == "passed" else "raw GSM8K check failed"
        results[row["candidate_id"]] = {"validation_status": status, "detail": detail, "method": "gsm8k_raw_train_replay_v1"}
    for row in hot_rows:
        source_id = hotpot_source_id(str((row.get("source") or {}).get("research_v1_dataset_id")))
        raw = raw_hot.get(source_id)
        status = "failed"
        detail = "raw HotpotQA row missing"
        if raw is not None:
            question_ok = norm_question(raw.get("question", "")) == norm_question(row["question"])
            answer_ok = str(raw.get("answer", "")).strip() == str(row.get("gold_answer", "")).strip()
            candidate_ok = str(row.get("candidate_answer", "")).strip() == str(row.get("gold_answer", "")).strip()
            status = "passed" if question_ok and answer_ok and candidate_ok else "failed"
            detail = "raw HotpotQA question and answer agree" if status == "passed" else "raw HotpotQA check failed"
        results[row["candidate_id"]] = {"validation_status": status, "detail": detail, "method": "hotpotqa_raw_source_match_v1"}
    for row in development:
        if row["label_class"] != SYNTHETIC_INCORRECT:
            continue
        distinct = str(row.get("candidate_answer", "")).strip() != str(row.get("gold_answer", "")).strip()
        synthetic_role = row.get("human_verified") is False and row.get("answer_is_correct") is False and bool(row.get("label_method"))
        status = "passed" if distinct and synthetic_role else "failed"
        results[row["candidate_id"]] = {
            "validation_status": status,
            "detail": "synthetic answer differs from gold and is not marked human-verified" if status == "passed" else "synthetic label check failed",
            "method": "synthetic_negative_role_v1",
        }
    return results


def _leakage(history: list[dict], development: list[dict]) -> dict:
    def index_hashes(rows):
        found = collections.defaultdict(set)
        for row in rows:
            for digest in context_hashes(row.get("evidence_context")):
                found[digest].add(row["related_group_id"])
        return found

    def index_facts(rows):
        found = collections.defaultdict(set)
        for row in rows:
            for title, sentence in row.get("supporting_facts") or []:
                found[f"{title}\0{sentence}"].add(row["related_group_id"])
        return found

    hist_para, dev_para = index_hashes(history), index_hashes(development)
    question_ids = collections.defaultdict(set)
    for row in history + development:
        if row.get("question_id"):
            question_ids[row["related_group_id"]].add(row["question_id"])
    shared_para = sorted(set(hist_para) & set(dev_para))
    paragraph_records = []
    quarantine = set()
    for digest in shared_para:
        hist_groups = sorted(hist_para[digest])
        dev_groups = sorted(dev_para[digest])
        quarantine.update(dev_groups)
        hist_questions = set().union(*(question_ids[group] for group in hist_groups))
        dev_questions = set().union(*(question_ids[group] for group in dev_groups))
        paragraph_records.append({
            "paragraph_sha256": digest, "history_groups": hist_groups, "development_groups": dev_groups,
            "same_question_id": bool(hist_questions & dev_questions),
            "adjudication": "distinct_questions_shared_hotpotqa_reference_paragraph",
            "eligibility_decision": "quarantine_development_groups",
            "rationale": "Normalized questions and question IDs differ. The shared text is HotpotQA reference context. Development groups are removed so the approved roster does not share that paragraph with History.",
        })
    hist_facts, dev_facts = index_facts(history), index_facts(development)
    fact_records = []
    for key in sorted(set(hist_facts) & set(dev_facts)):
        title, sentence = key.split("\0", 1)
        hist_groups = sorted(hist_facts[key])
        dev_groups = sorted(dev_facts[key])
        quarantine.update(dev_groups)
        fact_records.append({
            "supporting_fact": {"title": title, "sentence_index": int(sentence)},
            "history_groups": hist_groups, "development_groups": dev_groups,
            "adjudication": "distinct_questions_shared_supporting_fact",
            "eligibility_decision": "quarantine_development_groups",
            "rationale": "The same supporting-fact pointer occurs in History and Development. Those Development groups are quarantined with the shared-context rule.",
        })
    hist_q = _one_per_group(history)
    dev_q = _one_per_group(development)
    history_by_benchmark = collections.defaultdict(list)
    for gid, row in hist_q.items():
        text = norm_question(row["question"])
        history_by_benchmark[row["benchmark"]].append((gid, text, _tokens(text)))
    semantic_findings = []
    maxima = []
    for gid, row in sorted(dev_q.items()):
        text = norm_question(row["question"])
        tokens = _tokens(text)
        best = {"jaccard": 0.0, "sequence_ratio": 0.0, "history_group": None}
        for hid, htext, htokens in history_by_benchmark[row["benchmark"]]:
            jaccard = 1.0 if text == htext else _jaccard(tokens, htokens)
            if abs(len(text) - len(htext)) > max(40, int(0.5 * max(len(text), 1))) and jaccard < JACCARD_THRESHOLD:
                ratio = 0.0
            else:
                ratio = 1.0 if text == htext else SequenceMatcher(None, text, htext).ratio()
            if (jaccard, ratio) > (best["jaccard"], best["sequence_ratio"]):
                best = {"jaccard": jaccard, "sequence_ratio": ratio, "history_group": hid}
        maxima.append(best["sequence_ratio"])
        if best["jaccard"] >= JACCARD_THRESHOLD or best["sequence_ratio"] >= SEQUENCE_THRESHOLD or text == norm_question(hist_q[best["history_group"]]["question"]):
            semantic_findings.append({"development_group": gid, "history_group": best["history_group"],
                                      "benchmark": row["benchmark"], "jaccard": best["jaccard"],
                                      "sequence_ratio": best["sequence_ratio"], "adjudication": "unresolved"})
            quarantine.add(gid)
    reviewed = []
    for gid, row in sorted(dev_q.items()):
        text = norm_question(row["question"])
        for hid, htext, _htokens in history_by_benchmark[row["benchmark"]]:
            if abs(len(text) - len(htext)) > max(40, int(0.5 * max(len(text), 1))):
                continue
            ratio = SequenceMatcher(None, text, htext).ratio()
            if ratio >= 0.65:
                reviewed.append({"development_group": gid, "history_group": hid, "benchmark": row["benchmark"],
                                 "sequence_ratio": round(ratio, 4), "normalized_questions_equal": text == htext,
                                 "adjudication": "not_a_paraphrase_different_named_entities",
                                 "rationale": "Manually reviewed the closest pairs. They share a HotpotQA comparison template and name different entities."})
    exact = {}
    for key in ("related_group_id", "candidate_id", "question_id", "content_identity"):
        exact[key] = len({row.get(key) for row in history if row.get(key)} & {row.get(key) for row in development if row.get(key)})
    exact["normalized_question"] = len({norm_question(row["question"]) for row in history} & {norm_question(row["question"]) for row in development})
    exact["source_dataset_id"] = len({(row.get("source") or {}).get("research_v1_dataset_id") for row in history}
                                     & {(row.get("source") or {}).get("research_v1_dataset_id") for row in development})
    return {
        "protocol": LEAKAGE_PROTOCOL,
        "semantic_protocol": SEMANTIC_PROTOCOL,
        "semantic_thresholds": {"token_jaccard": JACCARD_THRESHOLD, "sequence_ratio": SEQUENCE_THRESHOLD},
        "semantic_clearance": "NOT_CLAIMED",
        "semantic_statement": "Zero pairs met the duplicate thresholds. Pairs below the thresholds were not all read. The scan does not prove that every lower-scoring pair is unrelated.",
        "exact_overlap": exact,
        "paragraph_hash_overlap_count": len(shared_para),
        "paragraph_records": paragraph_records,
        "supporting_fact_overlap_count": len(fact_records),
        "supporting_fact_records": fact_records,
        "quarantined_development_groups": sorted(quarantine),
        "semantic_findings_at_or_above_threshold": semantic_findings,
        "maximum_sequence_ratio": max(maxima) if maxima else 0.0,
        "manually_reviewed_pairs_at_or_above_0_65": reviewed,
    }


def build() -> dict:
    _manifest, labelled, unresolved, skipped = _load_snapshot()
    history, development = labelled["history"], labelled["development"]
    for row in history + development:
        if row.get("label_class") == HUMAN_VERIFIED_INCORRECT or row.get("human_verified") is True:
            raise ValueError("human-verified incorrect label appeared in the exploratory snapshot")
    leakage = _leakage(history, development)
    if any(leakage["exact_overlap"].values()):
        raise ValueError("exact History/Development identity overlap is not zero")
    if leakage["semantic_findings_at_or_above_threshold"]:
        raise ValueError("semantic findings at the duplicate threshold must be adjudicated before approval")
    references = _reference_checks(development)
    failed_groups = {row["related_group_id"] for row in development
                     if references.get(row["candidate_id"], {}).get("validation_status") != "passed"}
    quarantine = set(leakage["quarantined_development_groups"]) | failed_groups
    groups = collections.defaultdict(list)
    for row in development:
        groups[row["related_group_id"]].append(row)
    eligible, excluded, assignments, validations = [], [], [], []
    for gid, rows in sorted(groups.items()):
        classes = collections.Counter(row["label_class"] for row in rows)
        paired = classes[VERIFIED_CORRECT] == 1 and classes[SYNTHETIC_INCORRECT] == 1 and len(rows) == 2
        same_question = len({row["question_id"] for row in rows}) == 1 and len({norm_question(row["question"]) for row in rows}) == 1
        reasons = []
        if not paired or not same_question:
            reasons.append("group_not_exactly_one_correct_and_one_synthetic_incorrect")
        if gid in failed_groups:
            reasons.append("label_validation_failed")
        if gid in leakage["quarantined_development_groups"]:
            reasons.append("shared_history_reference_context")
        group_eligible = not reasons
        assignments.append({"related_group_id": gid, "benchmark": rows[0]["benchmark"], "question_id": rows[0]["question_id"],
                            "partition": "development", "label_classes": dict(sorted(classes.items())),
                            "eligible": group_eligible, "exclusion_reasons": reasons})
        for row in sorted(rows, key=lambda item: item["candidate_id"]):
            check = references[row["candidate_id"]]
            validations.append({"candidate_id": row["candidate_id"], "question_id": row["question_id"],
                                "related_group_id": gid, "benchmark": row["benchmark"],
                                "candidate_answer": row.get("candidate_answer"), "label_class": row["label_class"],
                                "label_source": row.get("label_source"), "label_method": row.get("label_method"),
                                "label_protocol": row.get("label_protocol"), "human_verified": row.get("human_verified"),
                                "source_dataset_id": (row.get("source") or {}).get("research_v1_dataset_id"),
                                "validation_status": check["validation_status"], "validation_method": check["method"],
                                "validation_detail": check["detail"], "eligible": group_eligible,
                                "exclusion_reasons": reasons})
            identity = _identity(row, eligible=group_eligible, reason=reasons[0] if reasons else "")
            identity["exclusion_reasons"] = reasons
            (eligible if group_eligible else excluded).append(identity)
    for row in unresolved:
        if row.get("partition") == "development":
            identity = _identity(row, eligible=False, reason="unresolved_not_a_binary_label")
            identity["exclusion_reasons"] = ["unresolved_not_a_binary_label"]
            excluded.append(identity)
            validations.append({
                "candidate_id": row.get("candidate_id"),
                "question_id": row.get("question_id"),
                "related_group_id": row.get("related_group_id"),
                "benchmark": row.get("benchmark"),
                "candidate_answer": row.get("candidate_answer"),
                "label_class": row.get("label_class"),
                "label_source": row.get("label_source"),
                "label_method": row.get("label_method"),
                "label_protocol": row.get("label_protocol"),
                "human_verified": row.get("human_verified"),
                "source_dataset_id": row.get("dataset_id"),
                "validation_status": "unresolved",
                "validation_method": "unresolved_excluded_from_binary_labels_v1",
                "validation_detail": "No binary label was assigned. The row stays unresolved and is excluded from binary-labelled evaluation.",
                "eligible": False,
                "exclusion_reasons": ["unresolved_not_a_binary_label"],
            })
    for row in skipped:
        if row.get("partition") == "development":
            excluded.append({"candidate_id": None, "related_group_id": row.get("related_group_id"), "partition": "development",
                             "benchmark": row.get("benchmark"), "dataset_version": DATASET_VERSION, "label_class": None,
                             "eligible": False, "exclusion_reason": row.get("reason", "skipped_group"),
                             "exclusion_reasons": [row.get("reason", "skipped_group")], "human_verified": False})
    by_benchmark = collections.defaultdict(collections.Counter)
    for row in eligible:
        by_benchmark[row["benchmark"]][row["label_class"]] += 1
    return {"eligible": eligible, "excluded": excluded, "assignments": assignments, "validations": validations,
            "leakage": leakage, "eligible_by_benchmark": {name: dict(counts) for name, counts in sorted(by_benchmark.items())},
            "eligible_groups": sum(row["eligible"] for row in assignments),
            "development_groups": len(assignments), "label_failures": len(failed_groups)}


def _package(result: dict) -> dict[str, bytes]:
    leakage = {key: value for key, value in result["leakage"].items()}
    return {
        "development_eligible.jsonl": jsonl_bytes(result["eligible"]),
        "development_excluded.jsonl": jsonl_bytes(result["excluded"]),
        "group_assignments.jsonl": jsonl_bytes(result["assignments"]),
        "label_validation.jsonl": jsonl_bytes(result["validations"]),
        "leakage_audit.json": canonical_bytes(leakage),
    }


def _manifest(result: dict, files: dict[str, bytes]) -> dict:
    counts = collections.Counter(row["validation_status"] for row in result["validations"])
    body = {
        "manifest_id": VERSION,
        "eligibility_version": VERSION,
        "approval": {"status": "APPROVED_BY_RESEARCH_LEAD", "approver": APPROVER, "approval_date": APPROVAL_DATE,
                     "scope": "Development eligibility for research_v1_exploratory_v1 only"},
        "approved": True,
        "frozen_protocol": False,
        "collection_authorized": False,
        "recording_authorized": False,
        "final_test_authorized": False,
        "does_not_authorize": ["verifier collection", "attempt recording", "protocol freeze", "Experiment 2 budgets",
                               "Final Test label release", "confirmatory evaluation", "policy fitting"],
        "dataset_version": DATASET_VERSION,
        "source_manifest": "evaluation/datasets/research_v1_exploratory/research_v1_exploratory_v1/manifest.json",
        "source_manifest_sha256": sha256_file(SOURCE / "manifest.json"),
        "eligibility_protocol": "paired_binary_group_v1",
        "leakage_protocol": LEAKAGE_PROTOCOL,
        "semantic_protocol": SEMANTIC_PROTOCOL,
        "label_protocol": PROTOCOL,
        "hash_algorithm": "SHA-256",
        "hash_definition": "SHA-256 of canonical JSON (sorted keys, indent 2, trailing newline) or canonical JSONL. eligibility_manifest_sha256 hashes the manifest body with that field removed. The complete-file SHA-256 of eligibility_manifest.json includes the body-hash field and is stored in eligibility_manifest.file_sha256.txt, not inside the JSON, because a digest stored inside the file would change the file.",
        "generator": "evaluation/data_preparation/exploratory_eligibility_approved.py",
        "generator_code_revision": _git_revision(),
        "not_the_research_v1_roster": "evaluation/datasets/person1/research_v1_person1_v1/development_eligible_candidates.jsonl",
        "provisional_audit_preserved": "research_v1_exploratory_eligibility_provisional_v1",
        "counts": {"provisionally_paired_groups_before_quarantine": result["development_groups"],
                   "eligible_candidates": len(result["eligible"]), "eligible_groups": result["eligible_groups"],
                   "excluded_rows": len(result["excluded"]), "eligible_by_benchmark": result["eligible_by_benchmark"],
                   "label_validation": dict(counts), "label_validation_failed_groups": result["label_failures"],
                   "quarantined_shared_context_groups": len(result["leakage"]["quarantined_development_groups"])},
        "exact_overlap": result["leakage"]["exact_overlap"],
        "paragraph_hash_overlap_count": result["leakage"]["paragraph_hash_overlap_count"],
        "supporting_fact_overlap_count": result["leakage"]["supporting_fact_overlap_count"],
        "semantic_findings_at_or_above_threshold": len(result["leakage"]["semantic_findings_at_or_above_threshold"]),
        "semantic_clearance": "NOT_CLAIMED",
        "maximum_sequence_ratio": result["leakage"]["maximum_sequence_ratio"],
        "output_sha256": {name: sha256_bytes(data) for name, data in sorted(files.items())},
    }
    body["eligibility_manifest_sha256"] = sha256_bytes(canonical_bytes({key: value for key, value in body.items()}))
    return body


def generate(output: Path = OUTPUT) -> dict:
    if any(part.lower() in {"final_test", "_custodian"} for part in output.parts):
        raise RuntimeError("refusing to write eligibility output into a Final Test path")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Refusing to overwrite an existing eligibility version")
    result = build()
    files = _package(result)
    manifest = _manifest(result, files)
    output.mkdir(parents=True, exist_ok=True)
    manifest_bytes = canonical_bytes(manifest)
    for name, data in {**files, "eligibility_manifest.json": manifest_bytes}.items():
        with (output / name).open("xb") as handle:
            handle.write(data)
    (output / "eligibility_manifest.file_sha256.txt").write_text(sha256_bytes(manifest_bytes) + "\n", encoding="utf-8")
    return manifest


def validate(output: Path = OUTPUT) -> dict:
    manifest = json.loads((output / "eligibility_manifest.json").read_text(encoding="utf-8"))
    if manifest["approval"]["status"] != "APPROVED_BY_RESEARCH_LEAD":
        raise ValueError("approval status changed")
    if manifest["collection_authorized"] is not False or manifest["frozen_protocol"] is not False or manifest["final_test_authorized"] is not False:
        raise ValueError("eligibility approval must not authorize collection, protocol freeze, or Final Test")
    mismatches = [name for name, digest in manifest["output_sha256"].items() if sha256_file(output / name) != digest]
    body = {key: value for key, value in manifest.items() if key != "eligibility_manifest_sha256"}
    manifest_bytes = canonical_bytes(manifest)
    recorded_file_hash = (output / "eligibility_manifest.file_sha256.txt").read_text(encoding="utf-8").strip()
    return {"manifest_id": manifest["manifest_id"], "approval": manifest["approval"],
            "eligibility_manifest_sha256": manifest["eligibility_manifest_sha256"],
            "eligibility_manifest_file_sha256": recorded_file_hash,
            "manifest_hash_matches_body": sha256_bytes(canonical_bytes(body)) == manifest["eligibility_manifest_sha256"],
            "manifest_file_hash_matches": recorded_file_hash == sha256_bytes(manifest_bytes),
            "stored_hash_mismatches": mismatches, "counts": manifest["counts"],
            "semantic_clearance": manifest["semantic_clearance"],
            "semantic_findings": manifest["semantic_findings_at_or_above_threshold"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"))
    args = parser.parse_args(argv)
    print(json.dumps(generate() if args.command == "generate" else validate(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
