"""Build and gate a fresh, group-disjoint Final Test roster.

The evaluation roster contains no correctness labels or gold answers. Custodian
labels are written separately and can only be read through the audited accessor.
This is a procedural filesystem boundary, not an OS security boundary: the
custodian must keep the label directory outside ordinary researcher access.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml
from datasets import load_from_disk

ROOT = Path(__file__).resolve().parents[2]
EXPOSED_FINAL_TEST = ROOT / "evaluation/datasets/unified/final_test.json"
HISTORY = ROOT / "evaluation/datasets/reconciled_candidates/research_v1/history_candidates.jsonl"
DEVELOPMENT = ROOT / "evaluation/datasets/reconciled_candidates/research_v1/development_candidates.jsonl"
RETIREMENTS = ROOT / "evaluation/config/final_test_retirements.json"
EXPOSURE_ROOTS = ("evaluation/datasets", "evaluation/results", "data/test_benchmark.jsonl")
EXPOSURE_METHOD = "normalized_question_text_v1"
CONFIRMATORY_USE_FORBIDDEN = "PERMANENTLY_FORBIDDEN"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def jsonl_bytes(rows: Iterable[dict]) -> bytes:
    return b"".join((json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode() for x in rows)


def norm_question(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def group_id(benchmark: str, question: str) -> str:
    normalized = norm_question(question)
    if not normalized:
        raise ValueError("Missing/empty normalized question")
    return f"{benchmark.lower()}-q-{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"


def context_hashes(context: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(context, str):
        if context.strip():
            found.add(sha256_bytes(context.encode("utf-8")))
    elif isinstance(context, list):
        for item in context:
            if isinstance(item, str):
                found |= context_hashes(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if text:
                    found.add(sha256_bytes(str(text).encode("utf-8")))
                if item.get("title") and text:
                    found.add(sha256_bytes((str(item["title"]) + "\0" + str(text)).encode("utf-8")))
    elif isinstance(context, dict):
        titles = context.get("title")
        sentences = context.get("sentences")
        if isinstance(titles, list) and isinstance(sentences, list):
            for title, rows in zip(titles, sentences):
                text = " ".join(str(x) for x in rows) if isinstance(rows, list) else str(rows)
                if text.strip():
                    found.add(sha256_bytes(text.encode("utf-8")))
                    if title:
                        found.add(sha256_bytes((str(title) + "\0" + text).encode("utf-8")))
        for key in ("text", "paragraphs", "context"):
            if key in context:
                found |= context_hashes(context[key])
    return found


def _required(row: dict, key: str, label: str) -> str:
    value = row.get(key)
    if value is None or not str(value).strip():
        raise ValueError(f"Missing {label}: {key}")
    return str(value)


def _identity_sets(rows: list[dict], partition: str) -> dict[str, set[str]]:
    out = {key: set() for key in ("question_ids", "source_ids", "group_ids", "candidate_ids", "questions", "contexts", "supporting_facts", "donors")}
    group_assignment: dict[str, str] = {}
    norm_assignment: dict[str, str] = {}
    for row in rows:
        benchmark = _required(row, "benchmark", "benchmark")
        question = _required(row, "question", "question")
        nested = row.get("source_candidate_record") or {}
        original = row.get("original_unified_source_record") or nested.get("original_unified_source_record", {})
        prov = row.get("evidence_provenance") or nested.get("evidence_provenance") or original.get("evidence_provenance") or {}
        if benchmark == "HotpotQA":
            if not (row.get("context") or row.get("evidence_context") or original.get("context") or nested.get("context") or prov.get("context_hashes") or prov.get("paragraph_hashes")):
                raise ValueError(f"Missing HotpotQA context/source hashes in {partition}")
            if "supporting_facts" not in row and "supporting_facts" not in original and "supporting_facts" not in nested and not prov.get("supporting_facts"):
                raise ValueError(f"Missing HotpotQA supporting-fact provenance in {partition}")
        raw_ids = [row.get("dataset_id"), row.get("question_id"), row.get("source_id"),
                   prov.get("source_id"), original.get("id")]
        raw_ids = [str(value).strip() for value in raw_ids if value is not None and str(value).strip()]
        qid = row.get("dataset_id") or row.get("question_id") or row.get("source_id") or prov.get("source_id")
        source_id = row.get("source_id") or prov.get("source_id") or row.get("dataset_id") or row.get("question_id")
        gid = row.get("related_group_id") or row.get("group_id")
        cid = row.get("candidate_id")
        if not qid or not source_id or not gid or not cid:
            raise ValueError(f"Missing required question/source/group/candidate ID in {partition}")
        normalized = norm_question(question)
        if not normalized:
            raise ValueError(f"Missing normalized question in {partition}")
        expected_gid = group_id(benchmark, question)
        if str(gid) != expected_gid:
            raise ValueError(f"Group ID does not match question in {partition}: {gid}")
        old = group_assignment.setdefault(str(gid), partition)
        if old != partition:
            raise ValueError("Cross-partition group overlap")
        norm_assignment.setdefault(normalized, partition)
        for raw_id in raw_ids:
            out["question_ids"].add(raw_id)
            out["source_ids"].add(raw_id)
            lowered = raw_id.casefold()
            for prefix in ("hotpotqa:", "hotpotqa_", "hotpot_", "gsm8k:"):
                if lowered.startswith(prefix):
                    out["question_ids"].add(lowered[len(prefix):])
                    out["source_ids"].add(lowered[len(prefix):])
        out["question_ids"].add(str(qid)); out["source_ids"].add(str(source_id))
        out["group_ids"].add(str(gid)); out["candidate_ids"].add(str(cid)); out["questions"].add(normalized)
        out["contexts"] |= context_hashes(row.get("context") or row.get("evidence_context") or original.get("context") or nested.get("context"))
        facts = row.get("supporting_facts") or original.get("supporting_facts") or nested.get("supporting_facts") or prov.get("supporting_facts") or []
        if isinstance(facts, dict) and isinstance(facts.get("title"), list):
            sentence_ids = facts.get("sentence_id", facts.get("sent_id", []))
            facts = list(zip(facts["title"], sentence_ids))
        for fact in facts:
            if isinstance(fact, (list, tuple)) and len(fact) >= 2:
                out["supporting_facts"].add(f"{fact[0]}\0{fact[1]}")
            elif isinstance(fact, dict) and fact.get("title") is not None and fact.get("sentence_id") is not None:
                out["supporting_facts"].add(f"{fact['title']}\0{fact['sentence_id']}")
        candidate_source = row.get("candidate_source") or nested.get("candidate_source")
        if partition == "final_test" and candidate_source == "synthetic_cross_example_answer" and not prov.get("donor_dataset_id"):
            raise ValueError(f"Missing HotpotQA donor/source provenance in {partition}")
        if prov.get("donor_dataset_id"):
            out["donors"].add(str(prov["donor_dataset_id"]))
        recorded_hashes = prov.get("context_hashes") or prov.get("paragraph_hashes", [])
        if isinstance(recorded_hashes, list):
            out["contexts"].update(str(value) for value in recorded_hashes if value)
    return out


def audit_leakage(proposed: list[dict], history: list[dict], development: list[dict]) -> dict:
    """Fail closed on missing identity fields and any exact cross-partition leak."""
    test = _identity_sets(proposed, "final_test")
    hist = _identity_sets(history, "history")
    dev = _identity_sets(development, "development")
    prior = {k: hist[k] | dev[k] for k in hist}
    overlaps = _leakage_overlap_values(test, prior)
    summary = {k: len(v) for k, v in overlaps.items()}
    leaks = {k: v for k, v in overlaps.items() if v}
    if leaks:
        raise ValueError("Final Test leakage detected: " + ", ".join(f"{k}={len(v)}" for k, v in leaks.items()))
    missing_donors = sum(1 for row in history + development
                         if row.get("benchmark") == "HotpotQA"
                         and (row.get("candidate_source") or (row.get("source_candidate_record") or {}).get("candidate_source")) == "synthetic_cross_example_answer"
                         and not ((row.get("evidence_provenance") or (row.get("source_candidate_record") or {}).get("evidence_provenance") or {}).get("donor_dataset_id")))
    return {"passed": True, "comparisons": summary, "semantic_paraphrase_leakage": "NOT AUDITED",
            "prior_borrowed_candidates_missing_donor_provenance": missing_donors,
            "limitations": ["Exact normalized question comparison does not identify semantic or paraphrase duplicates.",
                            "Some unresolved borrowed History/Development candidate records lack donor IDs; those records were not assigned a donor identity by this audit."]}


def iter_question_texts(value: Any) -> Iterable[str]:
    """Yield every string stored under a ``question`` key, at any nesting depth."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "question" and isinstance(item, str):
                yield item
            else:
                yield from iter_question_texts(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_question_texts(item)


def read_records(path: Path) -> Iterable[Any]:
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)
    else:
        yield json.loads(path.read_text(encoding="utf-8"))


def exposure_files(root: Path = ROOT, exclude: Iterable[Path] = (), roots: Iterable[str] = EXPOSURE_ROOTS) -> list[Path]:
    """Every JSON/JSONL record file that may have been read, run or reviewed.

    Custodian label directories are never opened; they hold no question text that
    is absent from their evaluation roster.
    """
    excluded = [Path(p).resolve() for p in exclude]
    found = set()
    for relative in roots:
        base = root / relative
        candidates = [base] if base.is_file() else base.rglob("*") if base.is_dir() else []
        for path in candidates:
            if path.suffix not in {".json", ".jsonl"} or not path.is_file() or "_custodian" in path.parts:
                continue
            resolved = path.resolve()
            if any(resolved == e or e in resolved.parents for e in excluded):
                continue
            found.add(path)
    return sorted(found)


def exposure_index(files: Iterable[Path], root: Path = ROOT) -> dict[str, set[str]]:
    """Map normalized question text to the repository-relative files containing it."""
    index: dict[str, set[str]] = collections.defaultdict(set)
    for path in files:
        name = str(path.relative_to(root)).replace("\\", "/") if path.is_relative_to(root) else str(path)
        for record in read_records(path):
            for question in iter_question_texts(record):
                normalized = norm_question(question)
                if normalized:
                    index[normalized].add(name)
    return dict(index)


def exposure_reasons(row: dict, index: dict[str, set[str]]) -> list[str]:
    return ["previously_exposed_question"] if norm_question(row.get("question", "")) in index else []


def exposure_audit(rows: list[dict], index: dict[str, set[str]], files: list[Path], root: Path = ROOT) -> dict:
    """Content-level exposure of a roster against every scanned record file."""
    overlaps: dict[str, list[str]] = {}
    for row in rows:
        sources = index.get(norm_question(row.get("question", "")))
        if sources:
            overlaps[str(row.get("related_group_id"))] = sorted(sources)
    names = [str(p.relative_to(root)).replace("\\", "/") if p.is_relative_to(root) else str(p) for p in files]
    return {"method": EXPOSURE_METHOD, "passed": not overlaps, "files_checked": len(names),
            "file_list_sha256": sha256_bytes(canonical_bytes(names)),
            "overlapping_group_count": len(overlaps),
            "overlap_counts_by_file": dict(sorted(collections.Counter(s for v in overlaps.values() for s in v).items())),
            "limitations": ["Exact normalized question text only; paraphrases and shared passages are not detected."]}


def load_retirements(path: Path = RETIREMENTS) -> dict[str, dict]:
    """Retired Final Test manifests keyed by manifest SHA-256; malformed entries fail closed."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != "final_test_retirement_registry_v1":
        raise ValueError("Unsupported Final Test retirement registry version")
    entries: dict[str, dict] = {}
    for entry in data.get("retired", []):
        digest = str(entry.get("manifest_sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", digest) or digest in entries:
            raise ValueError("Retirement entries require unique manifest SHA-256 values")
        if entry.get("confirmatory_use") != CONFIRMATORY_USE_FORBIDDEN or not str(entry.get("reason", "")).strip():
            raise ValueError("Retirement entries must forbid confirmatory use and state a reason")
        entries[digest] = entry
    return entries


def _leakage_overlap_values(test: dict[str, set[str]], prior: dict[str, set[str]]) -> dict[str, set[str]]:
    overlaps = {key: test[key] & prior[key] for key in test}
    overlaps["donor_source_ids"] = test["donors"] & (prior["source_ids"] | prior["question_ids"])
    return overlaps


def _source_revision_matches(dataset_dir: Path, benchmark: str, source_version: str) -> bool:
    info = json.loads((dataset_dir / "dataset_info.json").read_text(encoding="utf-8"))
    if benchmark == "GSM8K":
        expected_name, expected_config = "gsm8k", "main"
    else:
        expected_name, expected_config = "hotpot_qa", "distractor"
    return (info.get("dataset_name") == expected_name and info.get("config_name") == expected_config
            and source_version.split("@")[-1] in json.dumps(info.get("download_checksums", {})))


def _hotpot_support_valid(source: dict) -> tuple[bool, str]:
    answer = str(source.get("answer", "")).strip()
    if not answer:
        return False, "empty benchmark answer"
    context = source.get("context") or {}
    titles, sentences = context.get("title"), context.get("sentences")
    facts = source.get("supporting_facts") or {}
    fact_titles, fact_ids = facts.get("title"), facts.get("sent_id", facts.get("sentence_id"))
    if not isinstance(titles, list) or not isinstance(sentences, list) or not isinstance(fact_titles, list) or not isinstance(fact_ids, list) or not fact_titles:
        return False, "missing context or supporting-fact references"
    pages = {str(title): rows for title, rows in zip(titles, sentences)}
    for title, sentence_id in zip(fact_titles, fact_ids):
        rows = pages.get(str(title))
        if not isinstance(rows, list) or not isinstance(sentence_id, int) or sentence_id < 0 or sentence_id >= len(rows) or not str(rows[sentence_id]).strip():
            return False, "supporting-fact reference does not map to source context"
    return True, "benchmark answer and supporting-fact references preserved from source"


def _make_source_record(benchmark: str, source: dict, row_index: int, source_version: str) -> tuple[dict, dict]:
    question = str(source.get("question", ""))
    if not question.strip():
        raise ValueError(f"{benchmark} source row {row_index} has no question")
    if benchmark == "GSM8K":
        source_id = str(source.get("id") or f"gsm8k_test_{row_index:04d}")
        raw_answer = str(source.get("answer", ""))
        if "####" not in raw_answer or not raw_answer.split("####", 1)[1].strip():
            status, method, reason, answer = "unresolved", "gsm8k_final_answer_marker_check", "missing or empty #### final answer", ""
        else:
            answer = raw_answer.split("####", 1)[1].strip()
            from evaluation.data_preparation.build_verified_subset import normalize_numeric
            if normalize_numeric(answer) is None:
                status, method, reason = "unresolved", "gsm8k_final_answer_marker_check", "final answer is not parseable under numeric normalization"
            else:
                status, method, reason = "verified_correct", "gsm8k_source_final_answer_marker_match", None
        context, facts = [], []
    else:
        source_id = str(source.get("id", "")).strip()
        if not source_id:
            raise ValueError(f"HotpotQA validation row {row_index} has no source ID")
        answer = str(source.get("answer", "")).strip()
        context_source = source.get("context") or {}
        context = [{"title": str(title), "text": " ".join(str(x) for x in sentences)}
                   for title, sentences in zip(context_source.get("title", []), context_source.get("sentences", []))]
        facts_source = source.get("supporting_facts") or {}
        facts = list(zip(facts_source.get("title", []), facts_source.get("sent_id", facts_source.get("sentence_id", []))))
        valid, reason = _hotpot_support_valid(source)
        status, method = ("verified_correct", "hotpotqa_source_answer_and_supporting_fact_reference_match") if valid else ("unresolved", "hotpotqa_source_answer_support_provenance_check")
    source_version_text = source_version
    source_digest = sha256_bytes(canonical_bytes(source))
    provenance = {"method": method, "source_dataset": "openai/gsm8k" if benchmark == "GSM8K" else "hotpotqa/hotpot_qa",
                  "source_version": source_version_text, "source_split": "test" if benchmark == "GSM8K" else "validation",
                  "source_id": source_id, "source_row_index": row_index,
                  "source_row_sha256": source_digest, "answer_field": "answer",
                  "answer_sha256": sha256_bytes(answer.encode("utf-8")) if answer else None,
                  "human_adjudicated": False, "unresolved_reason": reason}
    rows, labels = _source_candidates(benchmark, source_version, source_id, question,
        [(answer, "benchmark_gold", status, provenance)], context, facts, row_index)
    row, label = rows[0], labels[0]
    row["source_dataset"] = provenance["source_dataset"]
    row["source_split"] = provenance["source_split"]
    row["candidate_generation_policy"] = "benchmark_gold_only_v1"
    label["validation_method"] = method
    label["unresolved_reason"] = reason
    return row, label


def validate_partition(roster: list[dict], labels: list[dict], expected_sizes: dict[str, int]) -> dict:
    if len(roster) == 0 or not expected_sizes or any(int(v) <= 0 for v in expected_sizes.values()):
        raise ValueError("Explicit positive per-benchmark sample sizes are required")
    if any(row.get("benchmark") not in expected_sizes for row in roster):
        raise ValueError("Unapproved benchmark in roster")
    for benchmark, expected in expected_sizes.items():
        n = len({r["related_group_id"] for r in roster if r["benchmark"] == benchmark})
        if n != int(expected):
            raise ValueError(f"{benchmark} group count {n} != configured {expected}")
    groups: dict[str, str] = {}
    split_groups: dict[str, str] = {}
    normalized: set[tuple[str, str]] = set()
    candidates = set()
    context_owner: dict[str, str] = {}
    support_owner: dict[str, str] = {}
    for row in roster:
        for key in ("source_version", "source_id", "question_id", "related_group_id", "candidate_id", "question", "candidate_answer", "label_provenance"):
            _required(row, key, "roster provenance")
        if row["label_provenance"] == "human_adjudicated" and not row.get("human_review_record"):
            raise ValueError("Human-adjudicated label claim lacks review record")
        gid = str(row["related_group_id"])
        if gid in groups and groups[gid] != row["benchmark"]:
            raise ValueError("Candidate-level split/group leakage")
        groups[gid] = row["benchmark"]
        if row.get("partition") is not None:
            previous_partition = split_groups.setdefault(gid, str(row["partition"]))
            if previous_partition != str(row["partition"]):
                raise ValueError("Candidate-level split leakage: one group assigned to multiple partitions")
        key = (row["benchmark"], norm_question(row["question"]))
        if key in normalized:
            raise ValueError("Duplicate normalized questions in proposed Final Test")
        normalized.add(key)
        if row["candidate_id"] in candidates:
            raise ValueError("Duplicate candidate ID")
        candidates.add(row["candidate_id"])
        if row.get("correctness_status") == "unresolved" and row.get("label") in {False, 0, "incorrect", "reject"}:
            raise ValueError("Unresolved candidate converted to negative")
        identity = _identity_sets([row], "final_test")
        for value in identity["contexts"]:
            owner = context_owner.setdefault(value, gid)
            if owner != gid:
                raise ValueError("Shared exact context across Final Test question groups")
        for value in identity["supporting_facts"]:
            owner = support_owner.setdefault(value, gid)
            if owner != gid:
                raise ValueError("Shared supporting fact across Final Test question groups")
    label_ids = {r.get("candidate_id") for r in labels}
    if label_ids != candidates:
        raise ValueError("Custodian label file candidate roster mismatch")
    for label in labels:
        if not label.get("label_provenance"):
            raise ValueError("Missing label provenance")
        if label.get("correctness_status") == "unresolved" and label.get("binary_label") is not None:
            raise ValueError("Unresolved candidate must have null binary label")
        if label.get("human_adjudicated") and not label.get("human_review_record"):
            raise ValueError("Human-adjudicated label lacks review record")
    return {"passed": True, "group_counts": {b: len({r['related_group_id'] for r in roster if r['benchmark'] == b}) for b in expected_sizes}, "candidate_count": len(roster), "unresolved_count": sum(x.get("correctness_status") == "unresolved" for x in labels)}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _source_candidates(benchmark: str, source_version: str, source_id: str, question: str, candidates: list[tuple[str, str, str, Any]], context: Any = None, facts: Any = None, source_row_index: int | None = None) -> tuple[list[dict], list[dict]]:
    gid = group_id(benchmark, question)
    roster, labels = [], []
    for index, (answer, method, status, provenance) in enumerate(candidates):
        cid = f"{benchmark.lower()}:{source_id}:candidate_{index}"
        base = {"benchmark": benchmark, "source_version": source_version, "source_id": source_id, "question_id": source_id,
                "related_group_id": gid, "candidate_id": cid, "question": question, "candidate_answer": answer,
                "source_row_index": source_row_index, "candidate_generation_method": method, "context": context or [], "supporting_facts": facts or []}
        label = {"candidate_id": cid, "gold_answer": answer if index == 0 else None,
                 "correctness_status": status, "binary_label": True if status == "verified_correct" else None,
                 "label_provenance": provenance, "human_adjudicated": False}
        roster.append({k: v for k, v in base.items() if k not in {"context", "supporting_facts"}} | {"evidence_context": context or [], "supporting_facts": facts or []})
        labels.append(label)
    return roster, labels


def build(config_path: Path) -> dict:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if config.get("previously_exposed_final_test_reuse") is not False:
        raise ValueError("Config must explicitly set previously_exposed_final_test_reuse: false")
    sources = config["source_paths"]
    configured_paths = {b: (ROOT / Path(value)).resolve() for b, value in sources.items()}
    if any(p == EXPOSED_FINAL_TEST.resolve() or (p.name == "final_test.json" and "unified" in p.parts) for p in configured_paths.values()):
        raise ValueError("Previously exposed final_test.json is ineligible")
    source_splits = config.get("source_splits", {})
    if source_splits != {"GSM8K": "test", "HotpotQA": "validation"}:
        raise ValueError("Fresh source splits must explicitly be GSM8K test and HotpotQA validation")
    paths = {b: configured_paths[b] for b in ("GSM8K", "HotpotQA")}
    versions = config.get("source_versions", {})
    if set(versions) != {"GSM8K", "HotpotQA"}:
        raise ValueError("Pinned GSM8K and HotpotQA source versions are required")
    source_rows = {benchmark: list(load_from_disk(str(path))) for benchmark, path in paths.items()}
    for benchmark, path in paths.items():
        if not versions.get(benchmark):
            raise ValueError(f"Missing approved source version for {benchmark}")
        if not _source_revision_matches(path, benchmark, versions[benchmark]):
            raise ValueError(f"{benchmark} local dataset metadata does not match pinned source revision")
    all_rows: dict[str, list[dict]] = {benchmark: [] for benchmark in versions}
    all_labels: dict[str, dict] = {}
    for benchmark, rows in source_rows.items():
        for row_index, source in enumerate(rows):
            row, label = _make_source_record(benchmark, source, row_index, versions[benchmark])
            all_rows[benchmark].append(row)
            all_labels[row["candidate_id"]] = label
    history = read_jsonl(HISTORY); development = read_jsonl(DEVELOPMENT)
    history_sets = _identity_sets(history, "history")
    development_sets = _identity_sets(development, "development")
    prior_sets = {key: history_sets[key] | development_sets[key] for key in history_sets}
    output = (ROOT / config["output"]).resolve()
    label_dir = (ROOT / config["custodian_label_output"]).resolve()
    scanned = exposure_files(exclude=(output, label_dir))
    exposed = exposure_index(scanned)
    seed = int(config.get("seed", 20261107))
    exclusion_reasons: dict[str, list[str]] = {}
    clean_pool: dict[str, list[dict]] = {benchmark: [] for benchmark in versions}
    seen_norm = {benchmark: set() for benchmark in versions}
    for benchmark in versions:
        rows = all_rows[benchmark]
        random.Random(seed + (0 if benchmark == "GSM8K" else 1)).shuffle(rows)
        seen_source_ids: set[str] = set()
        for row in rows:
            reasons = []
            normalized = norm_question(row["question"])
            if normalized in seen_norm[benchmark]:
                reasons.append("duplicate_normalized_fresh_source_question")
            if row["source_id"] in seen_source_ids:
                reasons.append("duplicate_fresh_source_id")
            seen_norm[benchmark].add(normalized)
            seen_source_ids.add(row["source_id"])
            current = _identity_sets([row], "final_test_candidate_pool")
            overlaps = _leakage_overlap_values(current, prior_sets)
            reasons.extend(f"history_development_overlap:{key}" for key, values in overlaps.items() if values)
            reasons.extend(exposure_reasons(row, exposed))
            if reasons:
                exclusion_reasons[row["related_group_id"]] = reasons
            else:
                clean_pool[benchmark].append(row)
    # Greedy seeded selection keeps exact paragraph and supporting-fact identities
    # unique across Final Test groups, then balances both benchmarks at the
    # largest feasible common count up to the full GSM8K test population.
    no_internal_context: dict[str, list[dict]] = {benchmark: [] for benchmark in versions}
    used_contexts: set[str] = set()
    used_facts: set[str] = set()
    combined_pool = [(benchmark, row) for benchmark in versions for row in clean_pool[benchmark]]
    random.Random(seed).shuffle(combined_pool)
    for benchmark, row in combined_pool:
        identities = _identity_sets([row], "final_test_candidate_pool")
        if identities["contexts"] & used_contexts:
            exclusion_reasons[row["related_group_id"]] = ["within_final_test_exact_context_overlap"]
            continue
        if identities["supporting_facts"] & used_facts:
            exclusion_reasons[row["related_group_id"]] = ["within_final_test_supporting_fact_overlap"]
            continue
        no_internal_context[benchmark].append(row)
        used_contexts.update(identities["contexts"])
        used_facts.update(identities["supporting_facts"])
    cap = int(config.get("sample_size", {}).get("per_benchmark_cap", 0))
    if cap <= 0:
        raise ValueError("A positive provisional per_benchmark_cap is required")
    balanced_count = min(cap, *(len(no_internal_context[b]) for b in versions))
    if balanced_count <= 0:
        raise ValueError("No balanced exact-leakage-clean fresh groups are available")
    selected_by_benchmark = {}
    roster: list[dict] = []
    labels: list[dict] = []
    for benchmark in versions:
        pool = sorted(no_internal_context[benchmark], key=lambda row: row["candidate_id"])
        random.Random(seed + (17 if benchmark == "GSM8K" else 29)).shuffle(pool)
        selected_by_benchmark[benchmark] = pool[:balanced_count]
        for row in selected_by_benchmark[benchmark]:
            label = all_labels[row["candidate_id"]]
            roster.append(row)
            labels.append(label)
    sizes = {benchmark: balanced_count for benchmark in versions}
    audit_rows = [{**row, "label_provenance": all_labels[row["candidate_id"]]["label_provenance"],
                   "correctness_status": all_labels[row["candidate_id"]]["correctness_status"]} for row in roster]
    audit = audit_leakage(roster, history, development)
    exposure = exposure_audit(roster, exposed, scanned)
    if not exposure["passed"]:
        raise ValueError("Final Test exposure detected: " + str(exposure["overlapping_group_count"]))
    summary = validate_partition(audit_rows, labels, sizes)
    audit["within_final_test_exact_context_overlap_groups"] = 0
    audit["within_final_test_supporting_fact_overlap_groups"] = 0
    audit["source_pool_counts"] = {b: len(source_rows[b]) for b in versions}
    audit["cross_history_development_exclusion_counts"] = {
        b: sum(any(reason.startswith("history_development_overlap:") for reason in reasons)
               for group, reasons in exclusion_reasons.items()
               if group.startswith("gsm8k-" if b == "GSM8K" else "hotpotqa-")) for b in versions}
    audit["within_final_test_context_exclusion_counts"] = {
        b: sum(any(reason.startswith("within_final_test_") for reason in reasons)
               for group, reasons in exclusion_reasons.items()
               if group.startswith("gsm8k-" if b == "GSM8K" else "hotpotqa-")) for b in versions}
    if output.exists() and any(output.iterdir()) or label_dir.exists() and any(label_dir.iterdir()):
        raise FileExistsError("Refusing to overwrite non-empty versioned Final Test output")
    if output == label_dir or output in label_dir.parents or label_dir in output.parents:
        raise ValueError("Evaluation roster and custodian labels must use separate directories")
    input_hashes = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path)
                    for path in paths.values()
                    for path in sorted(path.iterdir()) if path.is_file()}
    input_hashes[str(HISTORY.relative_to(ROOT)).replace("\\", "/")] = sha256_file(HISTORY)
    input_hashes[str(DEVELOPMENT.relative_to(ROOT)).replace("\\", "/")] = sha256_file(DEVELOPMENT)
    roster_data = jsonl_bytes(roster)
    label_data = jsonl_bytes(labels)
    audit_data = canonical_bytes(audit)
    label_counts = {status: sum(label["correctness_status"] == status for label in labels)
                    for status in ("verified_correct", "verified_incorrect", "unresolved")}
    candidate_ids = [row["candidate_id"] for row in roster]
    source_ids = [row["source_id"] for row in roster]
    group_ids = [row["related_group_id"] for row in roster]
    question_roster_hash = sha256_bytes(canonical_bytes([(row["question_id"], norm_question(row["question"])) for row in roster]))
    candidate_roster_hash = sha256_bytes(canonical_bytes([(row["candidate_id"], row["related_group_id"], row["benchmark"]) for row in roster]))
    config_sha = sha256_file(config_path)
    generator_sha = sha256_file(Path(__file__))
    output_hashes = {"evaluation_roster.jsonl": sha256_bytes(roster_data), "leakage_audit.json": sha256_bytes(audit_data)}
    custody_status = {"human_custodian": None, "human_custody_status": "PENDING_NO_INDEPENDENT_CUSTODIAN",
                      "storage_location": str(label_dir), "access_policy": "NOT_AUTHORIZED; code-level authorization required; OS boundary must be independently verified",
                      "authorization_status": "NOT_AUTHORIZED", "os_access_control": "NOT_ESTABLISHED_BY_GENERATOR"}
    manifest_core = {
        "dataset_name": "research_v1_fresh_benchmark_gold_candidates",
        "dataset_version": str(config.get("dataset_version", "research_v1_final_test_provisional_v1")),
        "research_protocol_version": str(config.get("research_protocol_version", "research_objective_v1")),
        "generator_version": "final_test_workflow_v2",
        "partition": "final_test", "enabled": False, "status": "NOT_AUTHORIZED", "freeze_status": "PROVISIONALLY_FROZEN_AFTER_HASH_AND_AUDIT",
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "seed": seed, "sample_size_strategy": config["sample_size"],
        "sample_size_rationale": "Provisional operational allocation: equal benchmark counts capped at the full fresh GSM8K test population and reduced only by fail-closed exact leakage/context exclusions. No power/effect-size calculation or confirmatory guarantee is claimed.",
        "source_dataset_names": {"GSM8K": "openai/gsm8k", "HotpotQA": "hotpotqa/hotpot_qa"},
        "source_versions": versions, "source_splits": source_splits, "source_sha256": input_hashes,
        "evaluation_roster_path": str(output / "evaluation_roster.jsonl"),
        "source_ids": source_ids, "question_ids": [row["question_id"] for row in roster], "group_ids": group_ids, "candidate_ids": candidate_ids,
        "source_pool_counts": audit["source_pool_counts"], "group_counts": summary["group_counts"],
        "candidate_counts": {b: sum(row["benchmark"] == b for row in roster) for b in versions},
        "candidate_count": len(roster),
        "label_counts": {b: {status: sum(row["benchmark"] == b and label["correctness_status"] == status
                                          for row, label in zip(roster, labels)) for status in label_counts} for b in versions},
        "combined_label_counts": label_counts, "candidate_generation_policy": "benchmark_gold_only_v1",
        "label_validation_policy": {"GSM8K": "exact #### source answer extraction plus numeric parse check; malformed values unresolved",
                                   "HotpotQA": "benchmark answer plus source supporting-fact title/sentence references mapped to source context; failed mapping unresolved",
                                   "human_adjudication_claimed": False},
        "label_provenance_counts": {"benchmark_gold_source_validation": len(labels)},
        "question_roster_sha256": question_roster_hash, "candidate_roster_sha256": candidate_roster_hash,
        "evaluation_roster_sha256": output_hashes["evaluation_roster.jsonl"],
        "label_file_sha256": sha256_bytes(label_data), "output_sha256": output_hashes,
        "generator_sha256": generator_sha, "configuration_sha256": config_sha,
        "leakage_audit": audit, "leakage_audit_sha256": sha256_bytes(audit_data),
        "excluded_group_count": len(exclusion_reasons), "exclusion_reason_counts": dict(collections.Counter(reason for reasons in exclusion_reasons.values() for reason in reasons)),
        "excluded_groups": [{"group_id": group,
                             "source_id": next((row["source_id"] for benchmark_rows in all_rows.values()
                                                for row in benchmark_rows if row["related_group_id"] == group), None),
                             "reasons": reasons} for group, reasons in sorted(exclusion_reasons.items())],
        "exposure_audit": exposure,
        "previously_exposed_final_test_reused": not exposure["passed"], "human_adjudication_claimed": False,
        "custody": custody_status, "known_limitations": ["semantic and paraphrase leakage not audited",
            "all candidates are benchmark-gold; no verified incorrect class is present",
            "shared context exclusions are exact-text only",
            "sample size is provisional, not statistically powered",
            "human custodian and OS-level label protection are not established"],
        "final_test_accessed_before_build": False
    }
    manifest_core["manifest_sha256"] = sha256_bytes(canonical_bytes(manifest_core))
    manifest_data = canonical_bytes(manifest_core)
    # Manifest is copied into both locations; no label payload is included in it.
    roster_files = {"evaluation_roster.jsonl": roster_data, "leakage_audit.json": audit_data, "manifest.json": manifest_data}
    label_files = {"custodian_labels.jsonl": label_data, "manifest.json": manifest_data}
    for path, files in ((output, roster_files), (label_dir, label_files)):
        path.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            with (path / name).open("xb") as f: f.write(data)
    receipt = {"evaluation_roster.jsonl": sha256_file(output / "evaluation_roster.jsonl"),
               "leakage_audit.json": sha256_file(output / "leakage_audit.json"),
               "evaluation_manifest.json": sha256_file(output / "manifest.json"),
               "custodian_labels.jsonl": sha256_file(label_dir / "custodian_labels.jsonl"),
               "custodian_manifest.json": sha256_file(label_dir / "manifest.json")}
    (output / "integrity_receipt.json").write_bytes(canonical_bytes(receipt))
    (label_dir / "integrity_receipt.json").write_bytes(canonical_bytes(receipt))
    return {"passed": True, "status": "NOT_AUTHORIZED", "summary": summary, "leakage": audit,
            "manifest_sha256": manifest_core["manifest_sha256"], "paths": {"evaluation": str(output), "custodian": str(label_dir)},
            "integrity_receipt": receipt, "excluded_group_count": len(exclusion_reasons)}


def read_custodian_labels(label_file: Path, authorization_file: Path, access_log: Path, *, person: str, purpose: str, expected_manifest_sha256: str, retirements: Path = RETIREMENTS, role: str | None = None) -> list[dict]:
    """Access labels only after explicit authorization; log before reading payload.

    A custodian appointment is not authorization. Verifier developers and Development
    experiment runners are refused before any label file is opened.
    """
    from evaluation.data_preparation.final_test_custody import DENIED_ROLES, denied_activities, is_appointment, release_block
    from evaluation.research_readiness.v2_authorization import refuse_sealed_label_without_release
    refuse_sealed_label_without_release(label_file)
    if not person.strip() or not purpose.strip():
        raise PermissionError("Named person and evaluation purpose are required")
    if role in DENIED_ROLES:
        raise PermissionError("Final Test labels are withheld: role_denied")
    if denied_activities(purpose):
        raise PermissionError("Final Test labels are withheld: activity_denied")
    if expected_manifest_sha256 in load_retirements(retirements):
        raise PermissionError("Final Test is retired; label access for evaluation is permanently denied")
    auth = json.loads(authorization_file.read_text(encoding="utf-8"))
    if is_appointment(auth):
        raise PermissionError("Custodian appointment is not evaluation authorization")
    if auth.get("approved") is not True or auth.get("person") != person or auth.get("purpose") != purpose or auth.get("manifest_sha256") != expected_manifest_sha256:
        raise PermissionError("Final Test label access is not authorized")
    manifest_file = label_file.parent / "manifest.json"
    if not manifest_file.is_file():
        raise PermissionError("Final Test manifest is missing; label access denied")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("manifest_sha256") != expected_manifest_sha256:
        raise PermissionError("Final Test manifest identity mismatch; label access denied")
    blocked = release_block(manifest, auth, role=role, purpose=purpose)
    if blocked:
        raise PermissionError(f"Final Test labels are withheld: {blocked}")
    roster_file = Path(manifest.get("evaluation_roster_path", ""))
    if roster_file.parts and not roster_file.is_absolute():
        roster_file = ROOT / roster_file
    if not roster_file.is_file():
        raise PermissionError("Final Test evaluation roster is unavailable; label access denied")
    validate_artifacts(roster_file, label_file, manifest_file)
    event = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "person": person, "purpose": purpose,
             "manifest_sha256": expected_manifest_sha256, "label_file_sha256": sha256_file(label_file), "authorization_sha256": sha256_file(authorization_file)}
    access_log.parent.mkdir(parents=True, exist_ok=True)
    with access_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")
        f.flush()
    return read_jsonl(label_file)


def validate_artifacts(roster_file: Path, label_file: Path, manifest_file: Path) -> dict:
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    expected = manifest.get("manifest_sha256")
    core = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    if sha256_bytes(canonical_bytes(core)) != expected:
        raise ValueError("Manifest hash mismatch")
    if sha256_file(roster_file) != manifest.get("evaluation_roster_sha256"):
        raise ValueError("Evaluation roster hash mismatch")
    if sha256_file(label_file) != manifest.get("label_file_sha256"):
        raise ValueError("Custodian label hash mismatch")
    if manifest.get("partition") == "final_test" and (manifest.get("status") != "NOT_AUTHORIZED" or manifest.get("enabled") is not False):
        raise ValueError("Final Test must remain unauthorized and disabled")
    for relative, digest in manifest.get("source_sha256", {}).items():
        source = ROOT / relative
        if not source.is_file() or sha256_file(source) != digest:
            raise ValueError(f"Final Test source hash mismatch: {relative}")
    audit_path = manifest_file.parent / "leakage_audit.json"
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit.get("passed") is not True or sha256_file(audit_path) != manifest.get("leakage_audit_sha256"):
            raise ValueError("Final Test leakage audit integrity/status mismatch")
    elif manifest.get("partition") == "final_test" and not manifest.get("leakage_audit"):
        raise ValueError("Final Test leakage audit file is missing")
    roster = read_jsonl(roster_file)
    labels = read_jsonl(label_file)
    manifest_audit = manifest.get("leakage_audit")
    if manifest.get("partition") == "final_test":
        if not isinstance(manifest_audit, dict) or manifest_audit.get("passed") is not True:
            raise ValueError("Final Test manifest lacks a passing leakage audit")
        if sha256_bytes(canonical_bytes(manifest_audit)) != manifest.get("leakage_audit_sha256"):
            raise ValueError("Final Test manifest leakage audit hash mismatch")
        required_audit_sources = {str(HISTORY.relative_to(ROOT)).replace("\\", "/"),
                                  str(DEVELOPMENT.relative_to(ROOT)).replace("\\", "/")}
        if required_audit_sources.issubset(manifest.get("source_sha256", {})):
            current_audit = audit_leakage(roster, read_jsonl(HISTORY), read_jsonl(DEVELOPMENT))
            if current_audit.get("comparisons") != manifest_audit.get("comparisons"):
                raise ValueError("Current History/Development leakage comparison differs from frozen audit")
    if len(roster) != manifest.get("candidate_count", len(roster)) or len(labels) != len(roster):
        raise ValueError("Final Test roster/label count mismatch")
    if {row.get("candidate_id") for row in roster} != {row.get("candidate_id") for row in labels}:
        raise ValueError("Final Test labels do not match evaluation candidate IDs")
    if manifest.get("candidate_ids") and set(manifest["candidate_ids"]) != {row.get("candidate_id") for row in roster}:
        raise ValueError("Final Test manifest candidate IDs differ from roster")
    if any(row.get("correctness_status") == "unresolved" and row.get("binary_label") is not None for row in labels):
        raise ValueError("Unresolved Final Test candidate has binary label")
    return {"passed": True, "manifest_sha256": expected, "evaluation_roster_sha256": manifest["evaluation_roster_sha256"], "label_file_sha256": manifest["label_file_sha256"]}


CORRECT_LABEL_KEYS = ("verified_correct", "VERIFIED_CORRECT")
INCORRECT_LABEL_KEYS = {"verified_incorrect": "legacy_unspecified", "HUMAN_VERIFIED_INCORRECT": "human_verified",
                        "SYNTHETIC_INCORRECT": "synthetic"}


def label_basis(values: dict | None) -> dict:
    """Correct/incorrect totals for one benchmark, keeping synthetic and human-verified negatives apart."""
    values = values or {}
    by_source = {source: int(values.get(key) or 0) for key, source in INCORRECT_LABEL_KEYS.items()}
    return {"correct": sum(int(values.get(k) or 0) for k in CORRECT_LABEL_KEYS),
            "incorrect": sum(by_source.values()), "incorrect_by_label_source": by_source}


def final_test_gate(manifest: dict, authorization: dict | None, retirements: dict[str, dict]) -> tuple[str, list[str]]:
    """Confirmatory Final Test status from the frozen manifest plus a separate authorization record.

    The manifest stays NOT_AUTHORIZED forever (``validate_artifacts`` enforces it), so
    approval can only come from an external record bound to the manifest hash.
    """
    if not manifest:
        return "BLOCKED", ["no_final_test_manifest"]
    reasons = []
    digest = manifest.get("manifest_sha256")
    core = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    if not digest or sha256_bytes(canonical_bytes(core)) != digest:
        reasons.append("manifest_hash_mismatch")
    if digest in retirements:
        reasons.append("retired_permanently_forbidden_for_confirmatory_use")
    if manifest.get("partition") != "final_test" or manifest.get("status") != "NOT_AUTHORIZED" or manifest.get("enabled") is not False:
        reasons.append("manifest_not_a_frozen_unauthorized_final_test")
    counts = manifest.get("label_counts") or {}
    if not counts:
        reasons.append("missing_label_counts")
    for benchmark, values in sorted(counts.items()):
        basis = label_basis(values)
        for side in ("correct", "incorrect"):
            if not basis[side]:
                reasons.append(f"no_{side}_candidates:{benchmark}")
    exposure = manifest.get("exposure_audit")
    if not isinstance(exposure, dict) or exposure.get("method") != EXPOSURE_METHOD or exposure.get("passed") is not True:
        reasons.append("missing_passing_content_level_exposure_audit")
    if reasons:
        return "BLOCKED", reasons
    from evaluation.data_preparation.final_test_custody import CUSTODY_STATUS, is_appointment
    pending = []
    if manifest.get("evaluation_authorization") == "PENDING":
        pending.append("evaluation_authorization_pending")
    if not authorization:
        pending.append("no_confirmatory_authorization_record")
    elif is_appointment(authorization):
        pending.append("custodian_appointment_is_not_evaluation_authorization")
    elif (authorization.get("approved") is not True or authorization.get("manifest_sha256") != digest
            or not str(authorization.get("approver", "")).strip() or not str(authorization.get("custodian", "")).strip()):
        return "BLOCKED", ["authorization_record_incomplete_or_mismatched"]
    elif manifest.get("custody_status") == CUSTODY_STATUS and authorization.get("protocol_frozen") is not True:
        pending.append("protocol_not_frozen")
    if pending:
        return "NOT APPROVED", pending
    return "APPROVED", []


def validate_readiness(config_path: Path, manifest_path: Path | None = None, authorization_path: Path | None = None,
                       retirements: Path = RETIREMENTS) -> dict:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path and manifest_path.exists() else {}
    authorization = json.loads(authorization_path.read_text(encoding="utf-8")) if authorization_path and authorization_path.exists() else None
    final_status, final_reasons = final_test_gate(manifest, authorization, load_retirements(retirements))
    checks = {
        "approved_benchmark_population": config.get("approved_benchmarks"), "source_versions": config.get("source_versions"),
        "candidate_label_policy": config.get("candidate_label_policy"), "label_audit_and_limitations": config.get("label_audit"),
        "verifier_eligibility_by_benchmark": config.get("verifier_eligibility"), "evidence_corpus_index_retriever_embedding_hashes": config.get("evidence_configuration"),
        "loss_configuration": config.get("loss_configuration"), "threshold_configuration": config.get("threshold_configuration"),
        "resource_budget": config.get("resource_budget"), "attack_scenarios": config.get("attack_scenarios"), "metrics_outcomes": config.get("metrics_outcomes"),
        "statistical_analysis_plan": config.get("statistical_analysis_plan"), "development_pilot_completion": config.get("development_pilot"),
        "sample_size_justification": config.get("sample_size_justification"), "attempts_availability": config.get("attempts"),
        "offline_examples_availability": config.get("offline_examples"), "policy_fitting_readiness": config.get("policy_fitting_ready"),
        "dataset_license_citation_status": config.get("license_citation_status")}
    statuses = {k: ("APPROVED" if v is True or isinstance(v, dict) and v.get("approved") is True else "BLOCKED" if v is None or v is False or v == {} else "NOT APPROVED") for k, v in checks.items()}
    # Missing data cannot be cleared by sign-off alone.
    for key, field in (("development_pilot_completion", "completed"), ("attempts_availability", "complete_count"),
                       ("offline_examples_availability", "complete_count")):
        if not (isinstance(checks[key], dict) and checks[key].get(field)):
            statuses[key] = "BLOCKED"
    statuses["final_test_partition_and_custody"] = final_status
    checks["final_test_partition_and_custody"] = manifest.get("status") if manifest else None
    label_bases = {b: label_basis(v) for b, v in sorted((manifest.get("label_counts") or {}).items())}
    return {"exploratory_readiness": "LIMITED" if any(v in {"BLOCKED", "NOT APPROVED"} for v in statuses.values()) else "READY", "confirmatory_readiness": "BLOCKED" if any(v != "APPROVED" for v in statuses.values()) else "READY", "checks": statuses, "observed_values": checks, "final_test_gate_reasons": final_reasons,
            "final_test_custody_status": manifest.get("custody_status"),
            "final_test_evaluation_authorization": manifest.get("evaluation_authorization"),
            "final_test_label_basis": label_bases,
            "final_test_negatives_synthetic_only": bool(label_bases) and all(
                v["incorrect"] and v["incorrect_by_label_source"]["synthetic"] == v["incorrect"] for v in label_bases.values())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build"); b.add_argument("--config", type=Path, required=True)
    r = sub.add_parser("readiness"); r.add_argument("--config", type=Path, required=True); r.add_argument("--manifest", type=Path)
    r.add_argument("--authorization", type=Path)
    args = parser.parse_args()
    result = build(args.config) if args.command == "build" else validate_readiness(args.config, args.manifest, args.authorization)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
