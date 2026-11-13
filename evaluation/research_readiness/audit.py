"""Dataset, corpus, and Final Test metadata audits.

Final Test label files are not opened. Identifier overlap is counted and
the identifiers themselves are not returned.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from evaluation.data_preparation.final_test_workflow import sha256_file
from evaluation.research_readiness.canonical import (
    CANONICAL_CORPUS,
    CANONICAL_CORPUS_SHA256,
    CANONICAL_INDEX_DIR,
    ELIGIBILITY_BODY_SHA256,
    ELIGIBILITY_MANIFEST,
    ELIGIBLE_CANDIDATES,
    ELIGIBLE_GROUPS,
    FINAL_TEST_CONTENT_HASH,
    FINAL_TEST_MANIFEST,
    GSM8K_GROUPS,
    HISTORICAL_CORPORA,
    HOTPOTQA_GROUPS,
    INDEX_CHUNKS_SHA256,
    INDEX_FAISS_SHA256,
    INDEX_MANIFEST_SHA256,
    ROOT,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ids_from_jsonl(path: Path, field: str) -> set[str]:
    found = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            value = row.get(field)
            if isinstance(value, str):
                found.add(value)
    return found


def audit_datasets(root: Path | None = None) -> dict:
    root = root or ROOT
    blockers = []
    unified = {}
    for name, expected in (("history", 8000), ("development", 2000), ("final_test", 2000)):
        path = root / "evaluation" / "datasets" / "unified" / f"{name}.json"
        if not path.is_file():
            unified[name] = {"present": False}
            blockers.append(f"unified {name} file is missing")
            continue
        rows = json.loads(path.read_text(encoding="utf-8"))
        counts = Counter(row.get("benchmark") for row in rows)
        unified[name] = {"rows": len(rows), "benchmarks": dict(counts)}
        if len(rows) != expected:
            blockers.append(f"unified {name} row count is {len(rows)}")
    history_ids = {row.get("id") for row in json.loads((root / "evaluation/datasets/unified/history.json").read_text(encoding="utf-8"))}
    development_ids = {row.get("id") for row in json.loads((root / "evaluation/datasets/unified/development.json").read_text(encoding="utf-8"))}
    final_ids = {row.get("id") for row in json.loads((root / "evaluation/datasets/unified/final_test.json").read_text(encoding="utf-8"))}
    unified_overlap = {
        "history_development": len(history_ids & development_ids),
        "history_final_test": len(history_ids & final_ids),
        "development_final_test": len(development_ids & final_ids),
    }
    if any(unified_overlap.values()):
        blockers.append("unified partition ids overlap")

    manifest_path = root / ELIGIBILITY_MANIFEST
    manifest = _load(manifest_path)
    counts = manifest.get("counts") or {}
    by_benchmark = counts.get("eligible_by_benchmark") or {}
    if counts.get("eligible_candidates") != ELIGIBLE_CANDIDATES or counts.get("eligible_groups") != ELIGIBLE_GROUPS:
        blockers.append("approved eligibility counts changed")
    hotpot = by_benchmark.get("HotpotQA") or {}
    gsm = by_benchmark.get("GSM8K") or {}
    if hotpot.get("VERIFIED_CORRECT") != HOTPOTQA_GROUPS or hotpot.get("SYNTHETIC_INCORRECT") != HOTPOTQA_GROUPS:
        blockers.append("HotpotQA eligible pairs are not the quarantined 185")
    if gsm.get("VERIFIED_CORRECT") != GSM8K_GROUPS or gsm.get("SYNTHETIC_INCORRECT") != GSM8K_GROUPS:
        blockers.append("GSM8K eligible pairs are not 187")
    if manifest.get("approval", {}).get("status") != "APPROVED_BY_RESEARCH_LEAD":
        blockers.append("eligibility approval status changed")
    if manifest.get("collection_authorized") is not False or manifest.get("final_test_authorized") is not False:
        blockers.append("eligibility manifest grants collection or Final Test")
    if manifest.get("eligibility_manifest_sha256") != ELIGIBILITY_BODY_SHA256:
        blockers.append("eligibility body hash changed")
    exact = manifest.get("exact_overlap") or {}
    if any(value != 0 for value in exact.values()):
        blockers.append("eligibility exact overlap is not zero")

    eligible_ids = _ids_from_jsonl(root / "evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/development_eligible.jsonl", "candidate_id")
    final_manifest = _load(root / FINAL_TEST_MANIFEST)
    sealed_ids = set(final_manifest.get("candidate_ids") or [])
    sealed_overlap = len(eligible_ids & sealed_ids)
    if sealed_overlap:
        blockers.append("eligible candidate ids overlap sealed Final Test ids")
    if final_manifest.get("status") != "NOT_AUTHORIZED" or final_manifest.get("enabled") is not False:
        blockers.append("Final Test manifest is not sealed")
    if final_manifest.get("manifest_sha256") != FINAL_TEST_CONTENT_HASH:
        blockers.append("Final Test manifest hash changed")

    return {
        "unified": unified,
        "unified_id_overlap": unified_overlap,
        "eligibility": {
            "candidates": counts.get("eligible_candidates"),
            "groups": counts.get("eligible_groups"),
            "gsm8k_groups": gsm.get("VERIFIED_CORRECT"),
            "hotpotqa_groups": hotpot.get("VERIFIED_CORRECT"),
            "approval_status": manifest.get("approval", {}).get("status"),
            "collection_authorized": manifest.get("collection_authorized"),
            "exact_overlap": exact,
            "semantic_clearance": manifest.get("semantic_clearance"),
        },
        "sealed_final_test_id_overlap": sealed_overlap,
        "unresolved_policy": "UNRESOLVED labels are not converted to verified labels by this audit.",
        "blockers": blockers,
    }


def audit_corpus(root: Path | None = None) -> dict:
    root = root or ROOT
    blockers = []
    corpus = root / CANONICAL_CORPUS
    corpus_hash = sha256_file(corpus) if corpus.is_file() else None
    if corpus_hash != CANONICAL_CORPUS_SHA256:
        blockers.append("canonical corpus hash mismatch")
    index = root / CANONICAL_INDEX_DIR
    hashes = {
        "manifest.json": sha256_file(index / "manifest.json") if (index / "manifest.json").is_file() else None,
        "chunks.json": sha256_file(index / "chunks.json") if (index / "chunks.json").is_file() else None,
        "faiss.index": sha256_file(index / "faiss.index") if (index / "faiss.index").is_file() else None,
    }
    expected = {
        "manifest.json": INDEX_MANIFEST_SHA256,
        "chunks.json": INDEX_CHUNKS_SHA256,
        "faiss.index": INDEX_FAISS_SHA256,
    }
    if hashes != expected:
        blockers.append("index file hash mismatch")
    stored = _load(index / "manifest.json")
    if stored.get("corpus_sha256") != CANONICAL_CORPUS_SHA256:
        blockers.append("index manifest is not bound to the canonical corpus")

    coverage_counts = Counter()
    hotpot_any_gate = 0
    hotpot_rows = 0
    gsm_rows = 0
    coverage_path = root / "evaluation/artifacts/person1/development_evidence_corpus_v1/coverage_new_corpus.jsonl"
    with coverage_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            benchmark = row.get("benchmark")
            if benchmark == "HotpotQA":
                hotpot_rows += 1
                if row.get("any_hit_above_0_78") is True:
                    hotpot_any_gate += 1
            elif benchmark == "GSM8K":
                gsm_rows += 1
            coverage_counts[row.get("retrieval_status") or "unspecified"] += 1
    if hotpot_rows != HOTPOTQA_GROUPS or gsm_rows != GSM8K_GROUPS:
        blockers.append("coverage file does not match the approved roster")

    historical = {}
    for relative, expected_hash in HISTORICAL_CORPORA.items():
        path = root / relative
        historical[relative] = {
            "role": "HISTORICAL_NOT_CANONICAL",
            "present": path.is_file(),
            "matches_recorded_hash": path.is_file() and sha256_file(path) == expected_hash,
        }
    return {
        "canonical_corpus": CANONICAL_CORPUS,
        "corpus_sha256": corpus_hash,
        "index_hashes": hashes,
        "index_bound_to_corpus": stored.get("corpus_sha256") == CANONICAL_CORPUS_SHA256,
        "retriever_not_instantiated": True,
        "hotpotqa_questions": hotpot_rows,
        "hotpotqa_any_chunk_at_or_above_0_78": hotpot_any_gate,
        "gsm8k_questions": gsm_rows,
        "retrieval_status_counts": dict(coverage_counts),
        "fever_in_canonical_source": False,
        "historical_corpora": historical,
        "suitability": "Retrieval hits are not evidence sufficiency or answer correctness.",
        "blockers": blockers,
    }


def audit_final_test_metadata(root: Path | None = None) -> dict:
    root = root or ROOT
    manifest = _load(root / FINAL_TEST_MANIFEST)
    allowed = (
        "dataset_version", "partition", "status", "enabled", "group_count", "candidate_count",
        "evaluation_authorization", "label_release", "confirmatory_use", "custody_status",
        "custody_independence", "human_approval", "human_adjudication", "human_verified_labels",
        "retired_final_test_reused", "manifest_sha256",
    )
    metadata = {key: manifest.get(key) for key in allowed}
    exposure = manifest.get("exposure_audit") if isinstance(manifest.get("exposure_audit"), dict) else {}
    leakage = manifest.get("leakage_audit") if isinstance(manifest.get("leakage_audit"), dict) else {}
    blockers = []
    if metadata.get("status") != "NOT_AUTHORIZED" or metadata.get("enabled") is not False:
        blockers.append("Final Test is not sealed")
    if metadata.get("label_release") != "NOT_AUTHORIZED" or metadata.get("confirmatory_use") != "NOT_AUTHORIZED":
        blockers.append("Final Test release or scoring is marked authorized")
    if metadata.get("custody_independence") == "INDEPENDENT":
        blockers.append("independent custody was declared without new evidence")
    if metadata.get("manifest_sha256") != FINAL_TEST_CONTENT_HASH:
        blockers.append("Final Test content hash changed")
    label_file = manifest.get("label_file_sha256")
    return {
        "metadata": metadata,
        "label_file_opened": False,
        "label_file_sha256_recorded": isinstance(label_file, str) and len(label_file) == 64,
        "exposure_passed": exposure.get("passed"),
        "exposure_overlapping_groups": exposure.get("overlapping_group_count"),
        "leakage_passed": leakage.get("passed"),
        "blockers": blockers,
    }
