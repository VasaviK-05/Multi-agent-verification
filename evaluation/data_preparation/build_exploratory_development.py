"""Exploratory History/Development version with paired synthetic incorrect candidates.

Reads research_v1 History/Development candidates and writes a new immutable version:
- labelled candidate files (VERIFIED_CORRECT and SYNTHETIC_INCORRECT, with provenance);
- blind verifier-input files with no label, generation or source-candidate fields;
- the research_v1 UNRESOLVED candidates, carried over separately and never relabelled.

research_v1 itself is not modified. No Final Test file is read except question text
for the exposure audit, and custodian label directories are never opened.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Iterable

from app.game.models import content_id
from evaluation.data_preparation.final_test_workflow import (
    DEVELOPMENT, HISTORY, ROOT, canonical_bytes, context_hashes, exposure_index, jsonl_bytes, norm_question,
    read_jsonl, sha256_bytes, sha256_file,
)
from evaluation.data_preparation.label_classes import (
    PROTOCOL, SYNTHETIC_INCORRECT, UNRESOLVED, VERIFIED_CORRECT, label_fields, research_v1_class,
)
from evaluation.data_preparation.synthetic_negatives import (
    GENERATOR_VERSION, gsm8k_negative, gsm8k_quality_flags, hotpotqa_negative, opaque_id, surface_feature_summary,
)

VERSION = "research_v1_exploratory_v1"
OUTPUT = ROOT / "evaluation/datasets/research_v1_exploratory" / VERSION
ID_NAMESPACE = "rx1"
ROLES = ("history", "development")
RAW_HOTPOT = {"validation": "evaluation/datasets/raw/hotpotqa/validation", "train": "evaluation/datasets/raw/hotpotqa/train"}
EXPOSED_FINAL_TEST = ("evaluation/datasets/unified/final_test.json", "evaluation/datasets/processed/final_test.json",
                      "evaluation/datasets/final_test_research_v1_eval_v1/evaluation_roster.jsonl")
BLIND_FIELDS = ("candidate_id", "related_group_id", "split_identity", "partition", "benchmark", "question_id",
                "question", "candidate_answer", "evidence_context")


def raw_hotpot_context(row: dict) -> tuple[list[dict], list[list]]:
    context = row.get("context") or {}
    paragraphs = [{"title": str(t), "text": " ".join(str(s) for s in sentences)}
                  for t, sentences in zip(context.get("title", []), context.get("sentences", []))]
    facts = row.get("supporting_facts") or {}
    pairs = [[str(t), int(s)] for t, s in zip(facts.get("title", []), facts.get("sent_id", facts.get("sentence_id", [])))]
    return paragraphs, pairs


def hotpot_source_id(dataset_id: str) -> str:
    for prefix in ("hotpot_", "hotpotqa_", "hotpotqa:"):
        if dataset_id.lower().startswith(prefix):
            return dataset_id[len(prefix):]
    return dataset_id


def load_raw_hotpot(ids: set[str], root: Path = ROOT) -> dict[str, dict]:
    from datasets import load_from_disk
    found: dict[str, dict] = {}
    for split, relative in RAW_HOTPOT.items():
        dataset = load_from_disk(str(root / relative))
        for index, row in enumerate(dataset):
            if row["id"] in ids and row["id"] not in found:
                found[row["id"]] = {**row, "_split": split, "_row_index": index,
                                    "_row_sha256": sha256_bytes(canonical_bytes(row))}
        if len(found) == len(ids):
            break
    return found


def research_v1_transformation(row: dict) -> str:
    nested = row.get("source_candidate_record") or {}
    for holder in (row.get("candidate_generation_provenance"), (row.get("reconciliation") or {}).get("evidence_provenance"),
                   nested.get("evidence_provenance"), nested.get("candidate_generation_provenance")):
        if isinstance(holder, dict) and holder.get("transformation"):
            return str(holder["transformation"])
    basis = (row.get("reconciliation") or {}).get("validation_basis") or {}
    if basis.get("construction_version"):
        return str(basis["construction_version"])
    if row.get("candidate_generation_method"):
        return str(row["candidate_generation_method"])
    raise ValueError(f"research_v1 negative {row['candidate_id']} has no recorded transformation")


def _groups(rows_by_role: dict[str, list[dict]]) -> dict[tuple[str, str], list[dict]]:
    groups: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for role, rows in rows_by_role.items():
        for row in rows:
            if row.get("partition", role) != role:
                raise ValueError("Candidate partition differs from its file role")
            groups[role, row["related_group_id"]].append(row)
    owners: dict[str, str] = {}
    for role, gid in groups:
        if owners.setdefault(gid, role) != role:
            raise ValueError(f"Group {gid} spans History and Development")
    return dict(sorted(groups.items()))


def _record(role: str, gid: str, benchmark: str, question_id: str, question: str, answer: str, context: list,
            extra: dict, label: dict) -> tuple[dict, dict]:
    blind = {"candidate_id": opaque_id(ID_NAMESPACE, gid, answer), "related_group_id": gid, "split_identity": gid,
             "partition": role, "benchmark": benchmark, "question_id": question_id, "question": question,
             "candidate_answer": answer, "evidence_context": context}
    labelled = {**blind, "dataset_version": VERSION, "content_identity": content_id([question, answer, None]),
                **extra, **label}
    return labelled, blind


def build_records(rows_by_role: dict[str, list[dict]], raw_hotpot: dict[str, dict]) -> dict:
    labelled = {role: [] for role in ROLES}
    blind = {role: [] for role in ROLES}
    unresolved, skipped = [], []
    for (role, gid), rows in _groups(rows_by_role).items():
        benchmark, question = rows[0]["benchmark"], rows[0]["question"]
        for row in sorted((r for r in rows if research_v1_class(r) == UNRESOLVED), key=lambda r: r["candidate_id"]):
            unresolved.append({**row, "label_class": UNRESOLVED, "label_protocol": PROTOCOL, "answer_is_correct": None})
        correct = sorted((r for r in rows if research_v1_class(r) == VERIFIED_CORRECT), key=lambda r: r["candidate_id"])
        negatives = sorted((r for r in rows if research_v1_class(r) == SYNTHETIC_INCORRECT), key=lambda r: r["candidate_id"])
        if not correct:
            skipped.append({"partition": role, "related_group_id": gid, "benchmark": benchmark, "reason": "no_verified_gold"})
            continue
        gold = correct[0]["gold_answer"]
        source_id = str(rows[0]["dataset_id"])
        context, facts, question_type, source = [], [], None, {"research_v1_dataset_id": source_id}
        if benchmark == "HotpotQA":
            raw = raw_hotpot.get(hotpot_source_id(source_id))
            if raw is None or norm_question(raw["question"]) != norm_question(question) or raw["answer"].strip() != gold.strip():
                skipped.append({"partition": role, "related_group_id": gid, "benchmark": benchmark,
                                "reason": "raw_hotpotqa_record_missing_or_inconsistent"})
                continue
            context, facts = raw_hotpot_context(raw)
            question_type = raw.get("type")
            source.update(raw_split=raw["_split"], raw_row_index=raw["_row_index"], raw_row_sha256=raw["_row_sha256"])
        question_id = f"{benchmark}:{source_id}"
        common = {"gold_answer": gold, "supporting_facts": facts, "question_type": question_type, "source": source}
        group = []
        for row in correct:
            group.append(_record(role, gid, benchmark, question_id, question, row["candidate_answer"], context,
                {**common, "source_candidate_id": row["candidate_id"], "generation": None},
                label_fields(VERIFIED_CORRECT, label_source="research_v1:benchmark_gold_source_match",
                             label_method=row.get("validation_method") or "benchmark_gold_source_match",
                             provenance={"research_v1_correctness_status": row["correctness_status"]})))
        for row in negatives:
            generation = {"generator": "research_v1_controlled_negative_candidates", "generated_by_this_version": False,
                          "transformation": research_v1_transformation(row)}
            group.append(_record(role, gid, benchmark, question_id, question, row["candidate_answer"], context,
                {**common, "source_candidate_id": row["candidate_id"], "generation": generation},
                label_fields(SYNTHETIC_INCORRECT, label_source="research_v1:controlled_negative_transformation",
                             label_method=row.get("validation_method") or "controlled_negative_transformation",
                             provenance={"research_v1_correctness_status": row["correctness_status"]})))
        if not negatives:
            taken = [r["candidate_answer"] for r in rows]
            if benchmark == "GSM8K":
                negative = gsm8k_negative(gold, taken)
                flags = gsm8k_quality_flags(question)
            else:
                negative = hotpotqa_negative(gold, question=question, question_type=question_type, context=context,
                                             supporting_titles=[f[0] for f in facts], key=gid, taken=taken)
                flags = {}
            if negative is None:
                skipped.append({"partition": role, "related_group_id": gid, "benchmark": benchmark,
                                "reason": "no_synthetic_negative_generated_gold_kept_unpaired"})
            else:
                generation = {"generator": GENERATOR_VERSION, "generated_by_this_version": True,
                              "transformation": negative["transformation"], "gold_answer": gold,
                              "source_question_id": question_id, "quality_flags": flags,
                              **({"delta": negative["delta"]} if "delta" in negative else {})}
                group.append(_record(role, gid, benchmark, question_id, question, negative["answer"], context,
                    {**common, "source_candidate_id": None, "generation": generation},
                    label_fields(SYNTHETIC_INCORRECT, label_source=f"{GENERATOR_VERSION}:{benchmark.lower()}",
                                 label_method=negative["transformation"],
                                 provenance={"rule": negative["transformation"], "inputs": ["gold_answer", "question",
                                             "context_titles", "supporting_fact_titles", "question_type"]})))
        ids = [g[0]["candidate_id"] for g in group]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate candidate answer within group {gid}")
        for record, blind_row in sorted(group, key=lambda g: g[0]["candidate_id"]):
            labelled[role].append(record)
            blind[role].append(blind_row)
    return {"labelled": labelled, "blind": blind, "unresolved": unresolved, "skipped": skipped}


def _identities(rows: Iterable[dict]) -> dict[str, set[str]]:
    out = {k: set() for k in ("group_ids", "question_ids", "normalized_questions", "candidate_ids",
                              "content_identities", "paragraph_hashes", "supporting_facts")}
    for row in rows:
        out["group_ids"].add(row["related_group_id"])
        out["question_ids"].add(row["question_id"])
        out["normalized_questions"].add(norm_question(row["question"]))
        out["candidate_ids"].add(row["candidate_id"])
        out["content_identities"].add(row["content_identity"])
        out["paragraph_hashes"] |= context_hashes(row.get("evidence_context"))
        out["supporting_facts"] |= {f"{t}\0{s}" for t, s in row.get("supporting_facts") or []}
    return out


def audit(records: dict, root: Path = ROOT) -> dict:
    history, development = (_identities(records["labelled"][r]) for r in ROLES)
    overlaps = {k: len(history[k] & development[k]) for k in history}
    strict = ("group_ids", "question_ids", "normalized_questions", "candidate_ids", "content_identities")
    if any(overlaps[k] for k in strict):
        raise ValueError("History/Development leakage: " + json.dumps({k: overlaps[k] for k in strict}))
    exposed_files = [root / p for p in EXPOSED_FINAL_TEST if (root / p).exists()]
    exposed = exposure_index(exposed_files, root)
    # Informational: these old files are retired or exposed and will never be scored. The
    # binding check is that Final Test v2 excludes every question here (build_final_test_v2).
    final_overlap = {role: {name: sum(name in exposed.get(norm_question(q), ()) for q in
                                      {r["question"] for r in records["labelled"][role]})
                            for name in EXPOSED_FINAL_TEST} for role in ROLES}
    balance = {}
    for role in ROLES:
        counts = collections.defaultdict(collections.Counter)
        for row in records["labelled"][role]:
            counts[row["benchmark"]][row["label_class"]] += 1
        for row in records["unresolved"]:
            if row["partition"] == role:
                counts[row["benchmark"]][UNRESOLVED] += 1
        groups = collections.defaultdict(lambda: collections.defaultdict(set))
        for row in records["labelled"][role]:
            groups[row["benchmark"]][row["related_group_id"]].add(row["label_class"])
        balance[role] = {b: {**{c: counts[b][c] for c in (VERIFIED_CORRECT, SYNTHETIC_INCORRECT,
                                                         "HUMAN_VERIFIED_INCORRECT", UNRESOLVED)},
                             "groups": len(groups[b]),
                             "paired_groups": sum(len(v) == 2 for v in groups[b].values()),
                             "generated_by_this_version": sum(1 for r in records["labelled"][role]
                                                              if r["benchmark"] == b and (r["generation"] or {}).get("generated_by_this_version"))}
                         for b in sorted(counts)}
    transformations = collections.Counter((r["benchmark"], r["generation"]["transformation"])
                                          for role in ROLES for r in records["labelled"][role] if r["generation"])
    blind_keys = {tuple(sorted(r)) for role in ROLES for r in records["blind"][role]}
    return {"history_development_overlap": overlaps,
            "history_development_overlap_note": "paragraph and supporting-fact overlap is inherited from research_v1 (conditional pass); identity overlaps must be 0",
            "exposed_final_test_question_overlap": final_overlap,
            "exposed_final_test_files_checked": [str(p.relative_to(root)).replace("\\", "/") for p in exposed_files],
            "label_balance": balance,
            "transformation_counts": {f"{b}:{t}": n for (b, t), n in sorted(transformations.items())},
            "skipped_groups": dict(collections.Counter(f"{s['partition']}:{s['benchmark']}:{s['reason']}" for s in records["skipped"])),
            "verifier_input_fields": sorted(blind_keys.pop()) if len(blind_keys) == 1 else "INCONSISTENT",
            "surface_features": surface_feature_summary([(r["benchmark"], r["label_class"], r["candidate_answer"])
                                                         for role in ROLES for r in records["labelled"][role]]),
            "human_verified_labels": 0}


def compute(root: Path = ROOT) -> dict[str, bytes]:
    rows_by_role = {"history": read_jsonl(HISTORY), "development": read_jsonl(DEVELOPMENT)}
    ids = {hotpot_source_id(str(r["dataset_id"])) for rows in rows_by_role.values() for r in rows if r["benchmark"] == "HotpotQA"}
    records = build_records(rows_by_role, load_raw_hotpot(ids, root))
    report = audit(records, root)
    files = {f"{role}_candidates.jsonl": jsonl_bytes(records["labelled"][role]) for role in ROLES}
    files |= {f"{role}_verifier_inputs.jsonl": jsonl_bytes(records["blind"][role]) for role in ROLES}
    files["unresolved_candidates.jsonl"] = jsonl_bytes(records["unresolved"])
    files["skipped_groups.jsonl"] = jsonl_bytes(records["skipped"])
    files["audit.json"] = canonical_bytes(report)
    return files


def manifest_for(files: dict[str, bytes], root: Path = ROOT) -> dict:
    report = json.loads(files["audit.json"])
    return {"dataset_version": VERSION, "parent_version": "research_v1", "label_protocol": PROTOCOL,
            "status": "EXPLORATORY_PROVISIONAL_LABELS", "human_verified_labels": 0,
            "human_approval": "DEFERRED", "human_adjudication": "DEFERRED",
            "generator_sha256": sha256_file(Path(__file__)),
            "dependency_sha256": {name: sha256_file(root / "evaluation/data_preparation" / name)
                                  for name in ("synthetic_negatives.py", "label_classes.py")},
            "input_sha256": {str(p.relative_to(root)).replace("\\", "/"): sha256_file(p) for p in (HISTORY, DEVELOPMENT)},
            "output_sha256": {name: sha256_bytes(data) for name, data in sorted(files.items())},
            "label_balance": report["label_balance"], "final_test_read": False}


def generate(output: Path = OUTPUT) -> dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Refusing to overwrite an existing dataset version")
    files = compute()
    manifest = manifest_for(files)
    output.mkdir(parents=True, exist_ok=True)
    for name, data in {**files, "manifest.json": canonical_bytes(manifest)}.items():
        with (output / name).open("xb") as handle:
            handle.write(data)
    return manifest


def validate(output: Path = OUTPUT) -> dict:
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    stored = {n: sha256_file(output / n) for n in manifest["output_sha256"]}
    recomputed = {n: sha256_bytes(d) for n, d in compute().items()}
    return {"stored_hash_mismatches": sorted(n for n, h in stored.items() if h != manifest["output_sha256"][n]),
            "recomputed_mismatches": sorted(n for n, h in recomputed.items() if h != manifest["output_sha256"].get(n)),
            "input_changes": sorted(p for p, h in manifest["input_sha256"].items() if sha256_file(ROOT / p) != h)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("generate", "validate"))
    args = parser.parse_args(argv)
    result = generate() if args.command == "generate" else validate()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if args.command == "generate" or not any(result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
