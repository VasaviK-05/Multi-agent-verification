"""Final Test v2 (exploratory): fresh, unexposed groups with paired gold and synthetic-incorrect candidates.

Writes two directories:
- evaluation side: a blind roster (no label, gold, supporting-fact or generation fields), the
  manifest, leakage and isolation audits, a label-free FinalTestReservation and custody
  preparation notes;
- custodian side: the labels, a class-format audit and an integrity receipt.

Labels are SYNTHETIC_INCORRECT or VERIFIED_CORRECT under the provisional automated protocol.
Nothing here authorizes label release, verifier recordings or confirmatory Experiment 1. The
retired provisional Final Test is read only as question/context text for exclusion; its
custodian labels are never opened. Labels are never printed.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

import yaml

from app.game.models import content_id
from app.game.offline.records import FinalTestReservation, ReservedExample
from evaluation.data_preparation.build_exploratory_development import OUTPUT as EXPLORATORY_DIR, raw_hotpot_context
from evaluation.data_preparation.build_research_dataset import SOURCE_VERSION
from evaluation.data_preparation.experiment1_preparation import OUTPUT as PREPARATION_DIR
from evaluation.data_preparation.final_test_workflow import (
    DEVELOPMENT, HISTORY, ROOT, _hotpot_support_valid, canonical_bytes, context_hashes, exposure_audit,
    exposure_files, final_test_gate, jsonl_bytes, load_retirements, norm_question, read_jsonl, read_records,
    sha256_bytes, sha256_file, validate_artifacts, group_id,
)
from evaluation.data_preparation.label_classes import (
    HUMAN_VERIFIED_INCORRECT, PROTOCOL, SYNTHETIC_INCORRECT, UNRESOLVED, VERIFIED_CORRECT, label_fields,
)
from evaluation.data_preparation.synthetic_negatives import (
    GENERATOR_VERSION, gsm8k_negative, gsm8k_quality_flags, hotpotqa_negative, opaque_id, surface_feature_summary,
)

CONFIG = ROOT / "evaluation/config/final_test_v2_exploratory.yaml"
PLAN = PREPARATION_DIR / "final_test_v2_selection_plan.json"
RETIRED_ROSTER = ROOT / "evaluation/datasets/final_test_research_v1_eval_v1/evaluation_roster.jsonl"
GSM8K_TEST = ROOT / "evaluation/datasets/raw/gsm8k/test"
BENCHMARKS = ("GSM8K", "HotpotQA")
ROSTER_FIELDS = ("candidate_id", "related_group_id", "split_identity", "partition", "benchmark", "question_id",
                 "source_id", "question", "candidate_answer", "evidence_context", "dataset_version")
FORBIDDEN_ROSTER_KEYS = {"gold_answer", "label_class", "answer_is_correct", "correctness_status", "binary_label",
                         "supporting_facts", "generation", "transformation", "label_source", "label_method",
                         "label_provenance", "human_verified", "question_type", "validation_id"}
EVALUATION_FILES = ("evaluation_roster.jsonl", "manifest.json", "leakage_audit.json", "isolation_audit.json",
                    "final_test_reservation.json", "custody_preparation.json")
CUSTODIAN_FILES = ("labels.jsonl", "manifest.json", "class_format_audit.json", "integrity_receipt.json")


def load_config(path: Path = CONFIG) -> dict:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if config.get("human_approval") != "DEFERRED" or config.get("label_protocol") != PROTOCOL:
        raise ValueError("Final Test v2 config must keep human approval DEFERRED under the provisional protocol")
    return config


def relative(path: Path, root: Path = ROOT) -> str:
    return str(path.relative_to(root)).replace("\\", "/") if path.is_relative_to(root) else str(path)


def fact_keys(value) -> set[str]:
    """Supporting-fact references (title, sentence id) in any of the repository's storage shapes."""
    found = set()
    if isinstance(value, dict) and isinstance(value.get("title"), list):
        found |= {f"{t}\0{s}" for t, s in zip(value["title"], value.get("sent_id", value.get("sentence_id", [])))}
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                found.add(f"{item[0]}\0{item[1]}")
            elif isinstance(item, dict) and "title" in item:
                found.add(f"{item['title']}\0{item.get('sent_id', item.get('sentence_id'))}")
    return found


def walk_exposure(files: Iterable[Path], root: Path = ROOT) -> dict:
    """Normalized questions (with the files holding them), exact paragraph hashes and supporting facts."""
    questions: dict[str, set[str]] = collections.defaultdict(set)
    contexts: set[str] = set()
    facts: set[str] = set()
    names = []
    for path in files:
        name = relative(path, root)
        names.append(name)
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
                        elif key == "supporting_facts":
                            facts |= fact_keys(item)
                        else:
                            stack.append(item)
                elif isinstance(value, list):
                    stack.extend(value)
    return {"questions": dict(questions), "contexts": contexts, "facts": facts, "files": sorted(names)}


def eligibility(benchmark: str, rows: Iterable[tuple[str, dict]], exposure: dict, seen: set[str],
                use_facts: bool) -> tuple[list[str], collections.Counter]:
    """Same rule as experiment1_preparation.pool, optionally adding exposed supporting facts."""
    eligible, reasons = [], collections.Counter()
    for source_id, row in rows:
        normalized = norm_question(row["question"])
        row_reasons = []
        if not normalized:
            row_reasons.append("empty_question")
        elif normalized in exposure["questions"]:
            row_reasons.append("previously_exposed_question")
        if normalized in seen:
            row_reasons.append("duplicate_normalized_question")
        if benchmark == "HotpotQA" and context_hashes(row.get("context")) & exposure["contexts"]:
            row_reasons.append("exposed_exact_paragraph")
        if use_facts and benchmark == "HotpotQA" and fact_keys(row.get("supporting_facts")) & exposure["facts"]:
            row_reasons.append("exposed_supporting_fact")
        seen.add(normalized)
        reasons.update(row_reasons)
        if not row_reasons:
            eligible.append(source_id)
    return eligible, reasons


def load_rows(path: Path) -> list[dict]:
    from datasets import load_from_disk
    return [dict(row) for row in load_from_disk(str(path))]


def plan_source_id(benchmark: str, split: str, index: int, row: dict) -> str:
    return str(row["id"]) if benchmark == "HotpotQA" else f"gsm8k_{split}_{index:05d}"


def gsm8k_gold(answer: str) -> str:
    return answer.split("####")[-1].strip()


def rank(seed: int, benchmark: str, source_id: str) -> str:
    return hashlib.sha256(f"{seed}|{benchmark}|{source_id}".encode()).hexdigest()


def select(benchmark: str, split: str, rows: list[dict], eligible: list[str], config: dict) -> tuple[list[dict], dict]:
    """Seeded order over eligible rows; take the first N that pass within-sample checks and get a negative."""
    by_id = {plan_source_id(benchmark, split, i, row): (i, row) for i, row in enumerate(rows)}
    ordered = sorted(eligible, key=lambda s: rank(config["seed"], benchmark, s))
    target = int(config["groups_per_benchmark"])
    chosen, skipped = [], collections.Counter()
    used_paragraphs: set[str] = set()
    used_facts: set[str] = set()
    considered = 0
    for plan_id in ordered:
        if len(chosen) == target:
            break
        considered += 1
        index, row = by_id[plan_id]
        question = str(row["question"])
        gid = group_id(benchmark, question)
        if benchmark == "GSM8K":
            gold = gsm8k_gold(row["answer"])
            negative = gsm8k_negative(gold, [gold])
            if negative is None or negative["transformation"] != "gold_plus_one":
                skipped["gold_plus_one_not_formable"] += 1
                continue
            context, facts, question_type, flags = [], [], None, gsm8k_quality_flags(question)
            source_id = f"gsm8k_{split}_{index}"
        else:
            valid, _ = _hotpot_support_valid(row)
            if not valid:
                skipped["supporting_facts_do_not_map_to_context"] += 1
                continue
            paragraphs = context_hashes(row["context"])
            pairs = fact_keys(row["supporting_facts"])
            if paragraphs & used_paragraphs or pairs & used_facts:
                skipped["shares_paragraph_or_supporting_fact_within_sample"] += 1
                continue
            gold = str(row["answer"])
            context, facts = raw_hotpot_context(row)
            question_type, flags = row.get("type"), {}
            negative = hotpotqa_negative(gold, question=question, question_type=question_type, context=context,
                                         supporting_titles=[f[0] for f in facts], key=gid, taken=[gold])
            if negative is None:
                skipped["no_synthetic_negative"] += 1
                continue
            used_paragraphs |= paragraphs
            used_facts |= pairs
            source_id = str(row["id"])
        chosen.append({"benchmark": benchmark, "group_id": gid, "question": question, "gold": gold,
                       "negative": negative, "context": context, "facts": facts, "question_type": question_type,
                       "flags": flags, "source_id": source_id, "question_id": f"{benchmark}:{source_id}",
                       "source": {"split": split, "row_index": index, "row_sha256": sha256_bytes(canonical_bytes(row)),
                                  "plan_source_id": plan_id}})
    if len(chosen) < target:
        raise ValueError(f"{benchmark}: only {len(chosen)} of {target} groups available")
    return chosen, {"eligible": len(eligible), "considered": considered, "selected": len(chosen),
                    "skipped_while_selecting": dict(sorted(skipped.items()))}


def candidate_rows(group: dict, config: dict) -> list[tuple[dict, dict]]:
    namespace, version = config["id_namespace"], config["dataset_version"]
    out = []
    for label_class, answer in ((VERIFIED_CORRECT, group["gold"]), (SYNTHETIC_INCORRECT, group["negative"]["answer"])):
        candidate_id = opaque_id(namespace, group["group_id"], answer)
        roster = {"candidate_id": candidate_id, "related_group_id": group["group_id"],
                  "split_identity": group["group_id"], "partition": "final_test", "benchmark": group["benchmark"],
                  "question_id": group["question_id"], "source_id": group["source_id"], "question": group["question"],
                  "candidate_answer": answer, "evidence_context": group["context"], "dataset_version": version}
        if label_class == VERIFIED_CORRECT:
            generation = None
            fields = label_fields(VERIFIED_CORRECT, label_source=f"benchmark_gold:{group['benchmark']}",
                                  label_method="raw_benchmark_gold_answer",
                                  provenance={"source": group["source"]})
        else:
            transformation = group["negative"]["transformation"]
            generation = {"generator": GENERATOR_VERSION, "transformation": transformation, "gold_answer": group["gold"],
                          "source_question_id": group["question_id"], "quality_flags": group["flags"],
                          **({"delta": group["negative"]["delta"]} if "delta" in group["negative"] else {})}
            fields = label_fields(SYNTHETIC_INCORRECT, label_source=f"{GENERATOR_VERSION}:{group['benchmark'].lower()}",
                                  label_method=transformation,
                                  provenance={"rule": transformation, "source": group["source"]})
        label = {"candidate_id": candidate_id, "related_group_id": group["group_id"], "benchmark": group["benchmark"],
                 "question_id": group["question_id"], "partition": "final_test", "dataset_version": version,
                 "gold_answer": group["gold"], "supporting_facts": group["facts"], "question_type": group["question_type"],
                 "correctness_status": label_class.lower(), "binary_label": fields["answer_is_correct"],
                 "content_identity": content_id([group["question"], answer, None]),
                 "validation_id": f"{namespace}-v-{rank(config['seed'], 'validation', candidate_id)[:24]}",
                 "generation": generation, **fields}
        out.append((roster, label))
    if out[0][0]["candidate_id"] == out[1][0]["candidate_id"]:
        raise ValueError(f"Candidate ID collision in {group['group_id']}")
    return sorted(out, key=lambda pair: pair[0]["candidate_id"])


def prior_identities(path: Path) -> dict[str, set[str]]:
    out = {k: set() for k in ("group_ids", "question_ids", "normalized_questions", "candidate_ids",
                              "content_identities", "validation_ids", "paragraph_hashes", "supporting_facts")}
    if not path.exists():
        return out
    for row in read_records(path):
        exposure = walk_exposure_record(row)
        out["paragraph_hashes"] |= exposure["contexts"]
        out["supporting_facts"] |= exposure["facts"]
        out["group_ids"] |= {str(row[k]) for k in ("related_group_id", "split_identity") if row.get(k)}
        if row.get("question_id"):
            out["question_ids"].add(str(row["question_id"]))
        if row.get("benchmark") and row.get("dataset_id"):
            out["question_ids"].add(f"{row['benchmark']}:{row['dataset_id']}")
        if row.get("question"):
            out["normalized_questions"].add(norm_question(row["question"]))
        if row.get("candidate_id"):
            out["candidate_ids"].add(str(row["candidate_id"]))
        if row.get("question") and row.get("candidate_answer") is not None:
            out["content_identities"].add(content_id([row["question"], row["candidate_answer"], None]))
        if row.get("content_identity"):
            out["content_identities"].add(str(row["content_identity"]))
        if row.get("validation_id"):
            out["validation_ids"].add(str(row["validation_id"]))
    return out


def walk_exposure_record(record) -> dict:
    contexts, facts, stack = set(), set(), [record]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"context", "evidence_context"}:
                    contexts |= context_hashes(item)
                elif key == "supporting_facts":
                    facts |= fact_keys(item)
                else:
                    stack.append(item)
        elif isinstance(value, list):
            stack.extend(value)
    return {"contexts": contexts, "facts": facts}


def prior_files(root: Path = ROOT) -> dict[str, Path]:
    files = {"research_v1:history": HISTORY, "research_v1:development": DEVELOPMENT,
             "retired_final_test_v1:evaluation_roster": RETIRED_ROSTER}
    for name in ("history_candidates.jsonl", "development_candidates.jsonl", "unresolved_candidates.jsonl"):
        files[f"{EXPLORATORY_DIR.name}:{name}"] = EXPLORATORY_DIR / name
    return files


def leakage_audit(labels: list[dict], roster: list[dict], root: Path = ROOT) -> dict:
    test = {"group_ids": {r["related_group_id"] for r in roster}, "question_ids": {r["question_id"] for r in roster},
            "normalized_questions": {norm_question(r["question"]) for r in roster},
            "candidate_ids": {r["candidate_id"] for r in roster},
            "content_identities": {l["content_identity"] for l in labels},
            "validation_ids": {l["validation_id"] for l in labels},
            "paragraph_hashes": set().union(*(context_hashes(r["evidence_context"]) for r in roster)),
            "supporting_facts": set().union(*(fact_keys(l["supporting_facts"]) for l in labels))}
    comparisons, missing = {}, []
    for name, path in prior_files(root).items():
        if not path.exists():
            missing.append(name)
            continue
        prior = prior_identities(path)
        comparisons[name] = {"sha256": sha256_file(path), "overlaps": {k: len(test[k] & prior[k]) for k in test}}
    passed = not missing and all(not any(c["overlaps"].values()) for c in comparisons.values())
    return {"method": "final_test_v2_identity_disjointness_v1", "passed": passed, "missing_prior_files": missing,
            "fields": sorted(test), "comparisons": comparisons,
            "within_test": {"groups_sharing_paragraphs": 0, "groups_sharing_supporting_facts": 0,
                            "duplicate_normalized_questions": len(roster) // 2 - len(test["normalized_questions"])},
            "custodian_labels_of_retired_final_test_opened": False}


def isolation_audit(roster: list[dict], config: dict) -> dict:
    key_sets = {tuple(sorted(r)) for r in roster}
    pattern = re.compile(rf"^{re.escape(config['id_namespace'])}-[0-9a-f]{{20}}$")
    checks = {"roster_key_sets": len(key_sets),
              "forbidden_keys_present": sorted(FORBIDDEN_ROSTER_KEYS & set().union(*map(set, key_sets))),
              "all_ids_opaque": all(pattern.match(r["candidate_id"]) for r in roster),
              "all_partition_final_test": all(r["partition"] == "final_test" for r in roster),
              "two_candidates_per_group": set(collections.Counter(r["related_group_id"] for r in roster).values()) == {2}}
    passed = (checks["roster_key_sets"] == 1 and not checks["forbidden_keys_present"] and checks["all_ids_opaque"]
              and checks["all_partition_final_test"] and checks["two_candidates_per_group"])
    return {"passed": passed, "checks": checks, "roster_fields": list(ROSTER_FIELDS),
            "excluded_from": ["policy fitting", "verifier recordings", "tuning", "policy selection"],
            "enforcement": ["run_verifier_attempts and build_offline_examples accept only history/development partitions",
                            "run_development_feasibility_pilot rejects any path containing final_test",
                            "TrainingManifest rejects History/Development examples sharing example, group, question, "
                            "content or validation IDs with the FinalTestReservation"]}


def class_format_audit(roster: list[dict], labels: list[dict]) -> dict:
    by_id = {l["candidate_id"]: l for l in labels}
    first_correct = collections.Counter()
    groups = collections.Counter()
    seen = set()
    for row in roster:
        if row["related_group_id"] in seen:
            continue
        seen.add(row["related_group_id"])
        groups[row["benchmark"]] += 1
        first_correct[row["benchmark"]] += by_id[row["candidate_id"]]["label_class"] == VERIFIED_CORRECT
    transformations = collections.Counter((l["benchmark"], l["generation"]["transformation"]) for l in labels if l["generation"])
    flags = collections.Counter((k, v) for l in labels if l["generation"] for k, v in l["generation"]["quality_flags"].items())
    return {"surface_features": surface_feature_summary([(r["benchmark"], by_id[r["candidate_id"]]["label_class"],
                                                          r["candidate_answer"]) for r in roster]),
            "correct_candidate_sorted_first_rate": {b: round(first_correct[b] / groups[b], 4) for b in sorted(groups)},
            "transformation_counts": {f"{b}:{t}": n for (b, t), n in sorted(transformations.items())},
            "gsm8k_quality_flags": {f"{k}={v}": n for (k, v), n in sorted(flags.items())},
            "known_residual_signals": [
                "GSM8K negatives are always gold+1, so within a group the larger number is the incorrect candidate; "
                "verifiers judge candidates one at a time, but any method comparing a group's candidates can exploit this.",
                "HotpotQA distractor-title negatives are entity names from the evidence context and can differ in "
                "answer type from the gold (see surface_features)."]}


def raw_source_hashes(config: dict, root: Path = ROOT) -> dict[str, str]:
    out = {}
    for source in config["sources"].values():
        for path in sorted((root / source["path"]).rglob("*")):
            if path.is_file():
                out[relative(path, root)] = sha256_file(path)
    return out


def compute(root: Path = ROOT, config_path: Path = CONFIG) -> dict[tuple[str, str], bytes]:
    config = load_config(config_path)
    evaluation_dir, custodian_dir = root / config["paths"]["evaluation"], root / config["paths"]["custodian"]
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    own = (evaluation_dir, custodian_dir)
    plan_files = exposure_files(root, exclude=(PREPARATION_DIR.parent, EXPLORATORY_DIR, *own))
    current_files = exposure_files(root, exclude=own)
    plan_exposure = walk_exposure(plan_files, root)
    current = walk_exposure(current_files, root)

    gsm_test = [(plan_source_id("GSM8K", "test", i, r), r) for i, r in enumerate(load_rows(root / "evaluation/datasets/raw/gsm8k/test"))]
    reproduction, selection, groups = {}, {}, []
    for benchmark in BENCHMARKS:
        source = config["sources"][benchmark]
        rows = load_rows(root / source["path"])
        indexed = [(plan_source_id(benchmark, source["split"], i, r), r) for i, r in enumerate(rows)]
        seen_plan = set()
        seen_current = set()
        if benchmark == "GSM8K":
            eligibility(benchmark, gsm_test, plan_exposure, seen_plan, use_facts=False)
            eligibility(benchmark, gsm_test, current, seen_current, use_facts=True)
        plan_ids, _ = eligibility(benchmark, indexed, plan_exposure, seen_plan, use_facts=False)
        expected = plan["eligible_pools"][benchmark][source["split"]]["eligible_source_id_sha256"]
        reproduction[benchmark] = {"plan_eligible": plan["eligible_pools"][benchmark][source["split"]]["eligible"],
                                   "reproduced_eligible": len(plan_ids),
                                   "eligible_source_id_sha256_matches_plan": sha256_bytes(canonical_bytes(sorted(plan_ids))) == expected}
        eligible, reasons = eligibility(benchmark, indexed, current, seen_current, use_facts=True)
        chosen, summary = select(benchmark, source["split"], rows, eligible, config)
        selection[benchmark] = {"split": source["split"], "source_rows": len(rows),
                                "exclusion_reason_counts": dict(sorted(reasons.items())),
                                "eligible_source_id_sha256": sha256_bytes(canonical_bytes(sorted(eligible))), **summary}
        groups.extend(chosen)

    pairs = [pair for group in sorted(groups, key=lambda g: g["group_id"]) for pair in candidate_rows(group, config)]
    roster = [p[0] for p in pairs]
    labels = [p[1] for p in pairs]
    if [tuple(r) for r in roster] != [ROSTER_FIELDS] * len(roster):
        raise ValueError("Roster rows must carry exactly the blind roster fields")
    exposure = exposure_audit(roster, current["questions"], current_files, root)
    exposure["paragraph_overlap_groups"] = sum(bool(context_hashes(r["evidence_context"]) & current["contexts"]) for r in roster) // 2
    exposure["passed"] = exposure["passed"] and exposure["paragraph_overlap_groups"] == 0
    leakage = leakage_audit(labels, roster, root)
    isolation = isolation_audit(roster, config)
    if not (exposure["passed"] and leakage["passed"] and isolation["passed"]):
        raise ValueError("Final Test v2 failed exposure, leakage or isolation audit: "
                         + json.dumps({"exposure": exposure["passed"], "leakage": leakage["passed"],
                                       "isolation": isolation["passed"]}))
    reservation = FinalTestReservation(
        version="final_test_reservation_v1", role="final_test", dataset_id=config["dataset_version"],
        custody_record=config["custody_record"],
        examples=tuple(ReservedExample(example_id=l["candidate_id"], split_identity=l["related_group_id"],
                                       question_id=l["question_id"], content_identity=l["content_identity"],
                                       validation_id=l["validation_id"]) for l in labels))
    roster_bytes, label_bytes = jsonl_bytes(roster), jsonl_bytes(labels)
    reservation_bytes = canonical_bytes(reservation.model_dump(mode="json"))
    label_counts = {b: {c: sum(l["benchmark"] == b and l["label_class"] == c for l in labels)
                        for c in (VERIFIED_CORRECT, SYNTHETIC_INCORRECT, HUMAN_VERIFIED_INCORRECT, UNRESOLVED)}
                    for b in BENCHMARKS}
    module_dir = Path(__file__).resolve().parent
    manifest = {
        "dataset_version": config["dataset_version"], "partition": "final_test", "status": "NOT_AUTHORIZED",
        "enabled": False, "label_protocol": PROTOCOL, "human_verified_labels": 0,
        "human_approval": "DEFERRED", "human_adjudication": "DEFERRED",
        "custody_status": "PENDING_NO_INDEPENDENT_CUSTODIAN", "confirmatory_use": "NOT_AUTHORIZED",
        "label_basis": "VERIFIED_CORRECT = raw benchmark gold; SYNTHETIC_INCORRECT = deterministic transformation; "
                       "no human verification",
        "seed": config["seed"], "config_path": relative(config_path, root), "config_sha256": sha256_file(config_path),
        "generator_sha256": sha256_file(Path(__file__)),
        "dependency_sha256": {name: sha256_file(module_dir / name) for name in
                              ("synthetic_negatives.py", "label_classes.py", "final_test_workflow.py",
                               "build_exploratory_development.py")},
        "source_versions": {b: SOURCE_VERSION[b] for b in BENCHMARKS},
        "source_sha256": raw_source_hashes(config, root),
        "prior_partition_sha256": {name: c["sha256"] for name, c in leakage["comparisons"].items()},
        "retired_final_test_reused": False,
        "evaluation_roster_path": f"{config['paths']['evaluation']}/evaluation_roster.jsonl",
        "evaluation_roster_sha256": sha256_bytes(roster_bytes), "label_file_sha256": sha256_bytes(label_bytes),
        "reservation_sha256": sha256_bytes(reservation_bytes),
        "candidate_count": len(roster), "group_count": len(groups),
        "candidate_ids": sorted(r["candidate_id"] for r in roster),
        "label_counts": label_counts,
        "combined_label_counts": {c: sum(v[c] for v in label_counts.values()) for c in label_counts["GSM8K"]},
        "exposure_audit": exposure, "leakage_audit": leakage, "leakage_audit_sha256": sha256_bytes(canonical_bytes(leakage)),
        "isolation_audit_sha256": sha256_bytes(canonical_bytes(isolation)),
        "selection": selection, "selection_plan_reproduction": reproduction,
        "forbidden_uses": config["forbidden_uses"],
    }
    manifest["manifest_sha256"] = sha256_bytes(canonical_bytes(manifest))
    manifest_bytes = canonical_bytes(manifest)
    custody = {"status": "PENDING_NO_INDEPENDENT_CUSTODIAN", "custodian": None, "approver": None,
               "custody_record": config["custody_record"], "manifest_sha256": manifest["manifest_sha256"],
               "label_file": f"{config['paths']['custodian']}/labels.jsonl", "label_file_sha256": manifest["label_file_sha256"],
               "label_release": "NOT_AUTHORIZED", "human_approval": "DEFERRED", "human_adjudication": "DEFERRED",
               "access_control": "none; the labels sit in a Git-ignored directory of the same workspace. This is "
                                 "custody preparation, not custody, and gives no operating-system protection.",
               "forbidden_uses": config["forbidden_uses"],
               "required_before_confirmatory_use": [
                   "an independent custodian takes the label file and verifies label_file_sha256",
                   "human approval of the synthetic-negative protocol, or human adjudication of the negatives",
                   "an authorization record (approved, manifest_sha256, approver, custodian) passed to "
                   "final_test_workflow readiness --authorization"]}
    format_audit = class_format_audit(roster, labels)
    evaluation = {"evaluation_roster.jsonl": roster_bytes, "manifest.json": manifest_bytes,
                  "leakage_audit.json": canonical_bytes(leakage), "isolation_audit.json": canonical_bytes(isolation),
                  "final_test_reservation.json": reservation_bytes, "custody_preparation.json": canonical_bytes(custody)}
    custodian = {"labels.jsonl": label_bytes, "manifest.json": manifest_bytes,
                 "class_format_audit.json": canonical_bytes(format_audit)}
    receipt = {"manifest_sha256": manifest["manifest_sha256"],
               "evaluation_files": {n: sha256_bytes(b) for n, b in evaluation.items()},
               "custodian_files": {n: sha256_bytes(b) for n, b in custodian.items()}}
    custodian["integrity_receipt.json"] = canonical_bytes(receipt)
    return {**{("evaluation", n): b for n, b in evaluation.items()}, **{("custodian", n): b for n, b in custodian.items()}}


def directories(config: dict, root: Path = ROOT) -> dict[str, Path]:
    return {"evaluation": root / config["paths"]["evaluation"], "custodian": root / config["paths"]["custodian"]}


def summary(manifest: dict) -> dict:
    """Label-free summary safe to print."""
    return {"dataset_version": manifest["dataset_version"], "manifest_sha256": manifest["manifest_sha256"],
            "status": manifest["status"], "custody_status": manifest["custody_status"],
            "group_count": manifest["group_count"], "candidate_count": manifest["candidate_count"],
            "label_counts": manifest["label_counts"], "selection": manifest["selection"],
            "selection_plan_reproduction": manifest["selection_plan_reproduction"],
            "exposure_audit_passed": manifest["exposure_audit"]["passed"],
            "leakage_audit_passed": manifest["leakage_audit"]["passed"]}


def generate(root: Path = ROOT, config_path: Path = CONFIG) -> dict:
    config = load_config(config_path)
    dirs = directories(config, root)
    for path in dirs.values():
        if path.exists() and any(path.iterdir()):
            raise FileExistsError(f"{relative(path, root)} already exists; Final Test versions are write-once")
    files = compute(root, config_path)
    for (side, name), data in files.items():
        dirs[side].mkdir(parents=True, exist_ok=True)
        with (dirs[side] / name).open("xb") as handle:
            handle.write(data)
    return summary(json.loads(files["evaluation", "manifest.json"]))


def validate(root: Path = ROOT, config_path: Path = CONFIG, recompute: bool = True) -> dict:
    config = load_config(config_path)
    dirs = directories(config, root)
    receipt = json.loads((dirs["custodian"] / "integrity_receipt.json").read_text(encoding="utf-8"))
    stored = [f"{side}:{name}" for side, key in (("evaluation", "evaluation_files"), ("custodian", "custodian_files"))
              for name, digest in receipt[key].items() if sha256_file(dirs[side] / name) != digest]
    manifest_path = dirs["evaluation"] / "manifest.json"
    artifacts = validate_artifacts(dirs["evaluation"] / "evaluation_roster.jsonl", dirs["custodian"] / "labels.jsonl",
                                   manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (dirs["custodian"] / "manifest.json").read_bytes() != manifest_path.read_bytes():
        raise ValueError("Custodian manifest copy differs from the evaluation manifest")
    reservation = FinalTestReservation.model_validate_json((dirs["evaluation"] / "final_test_reservation.json").read_text(encoding="utf-8"))
    roster = read_jsonl(dirs["evaluation"] / "evaluation_roster.jsonl")
    if {e.example_id for e in reservation.examples} != {r["candidate_id"] for r in roster}:
        raise ValueError("Reservation examples differ from the roster")
    if not isolation_audit(roster, config)["passed"]:
        raise ValueError("Roster fails the isolation audit")
    gate = final_test_gate(manifest, None, load_retirements())
    mismatches = []
    if recompute:
        mismatches = [f"{side}:{name}" for (side, name), data in compute(root, config_path).items()
                      if (dirs[side] / name).read_bytes() != data]
    return {"stored_hash_mismatches": stored, "recomputed_mismatches": mismatches, "artifacts": artifacts,
            "reservation_examples": len(reservation.examples), "gate": list(gate),
            "manifest_retired": manifest["manifest_sha256"] in load_retirements()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("dry-run", "generate", "validate"))
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args(argv)
    if args.command == "dry-run":
        result = summary(json.loads(compute(ROOT, args.config)["evaluation", "manifest.json"]))
    elif args.command == "generate":
        result = generate(ROOT, args.config)
    else:
        result = validate(ROOT, args.config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if args.command != "validate" or not (result["stored_hash_mismatches"] or result["recomputed_mismatches"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
