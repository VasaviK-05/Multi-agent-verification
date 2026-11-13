"""Read-only Development corpus and eligibility checks. Does not open Final Test labels."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "evaluation/artifacts/person1/development_evidence_corpus_v1/corpus.json"
INDEX = ROOT / "evaluation/artifacts/person1/development_evidence_corpus_v1/evidence_index/corpus/manifest.json"
ELIGIBILITY = ROOT / "evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/eligibility_manifest.json"
EXPECTED_CORPUS = "f76c6ce19661e2fdae44f87f126825d8efc4b3edb3fa1b381d0130c7f82e5e2b"
EXPECTED_INDEX = "idx-c1dc6980912b"
EXPECTED_ELIGIBILITY = "f2cc0fd108b961bf4795767df4f90e92d7fa0f418ef9865d0206f32d7b45282d"
INDEX_FILES = {
    "manifest.json": "2a7ce5a45101e26c73bd4a8c3255d4c743166b24e9339f4d8f5fe983a9ab8521",
    "chunks.json": "1d207b208905a3ce3a85c4c567ecc5cc8b24106d43964ebda046a7da51963bc7",
    "faiss.index": "037e4923b2c69c86b5f7fb83c8589c6b89ed7fe714d7cbb70581a7700aacb7d8",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2) + "\n").encode("utf-8")


def audit() -> dict:
    if any("final_test" in path.as_posix().lower() for path in (CORPUS, INDEX, ELIGIBILITY)):
        raise RuntimeError("refusing a Final Test path")
    corpus_bytes = CORPUS.read_bytes()
    articles = json.loads(corpus_bytes)
    identifiers = [row["id"] for row in articles]
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    eligibility = json.loads(ELIGIBILITY.read_text(encoding="utf-8"))
    body = {key: value for key, value in eligibility.items() if key != "eligibility_manifest_sha256"}
    folder = ELIGIBILITY.parent
    output_hashes = {}
    for name, expected in (eligibility.get("output_sha256") or {}).items():
        path = folder / name
        output_hashes[name] = {"present": path.is_file(), "matches_manifest": path.is_file() and _sha256(path) == expected}
    group_path = folder / "group_assignments.jsonl"
    group_ids = set()
    group_lines = 0
    if group_path.is_file():
        for line in group_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            group_lines += 1
            row = json.loads(line)
            for key in ("related_group_id", "group_id", "question_group_id"):
                if row.get(key):
                    group_ids.add(row[key])
                    break
    group_count = len(group_ids) if group_ids else group_lines
    eligible_groups = set()
    ineligible_groups = set()
    if group_path.is_file():
        for line in group_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            target = eligible_groups if row.get("eligible") is True else ineligible_groups
            if row.get("related_group_id"):
                target.add(row["related_group_id"])
    output_lf_matches = {}
    for name, expected in (eligibility.get("output_sha256") or {}).items():
        path = folder / name
        if not path.is_file():
            output_lf_matches[name] = False
            continue
        normalized = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        output_lf_matches[name] = hashlib.sha256(normalized).hexdigest() == expected
    index_hashes = {}
    for name, expected in INDEX_FILES.items():
        path = INDEX.parent / name
        index_hashes[name] = path.is_file() and _sha256(path) == expected
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    return {
        "labels_opened": False,
        "final_test_accessed": False,
        "corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(),
        "corpus_sha256_matches": hashlib.sha256(corpus_bytes).hexdigest() == EXPECTED_CORPUS,
        "cr_byte_count": corpus_bytes.count(b"\r"),
        "article_count": len(articles),
        "unique_article_ids": len(set(identifiers)),
        "article_ids_sorted": identifiers == sorted(identifiers),
        "index_version": index.get("index_version"),
        "index_version_matches": index.get("index_version") == EXPECTED_INDEX,
        "index_corpus_sha256_matches": index.get("corpus_sha256") == EXPECTED_CORPUS,
        "index_file_hashes_match": index_hashes,
        "eligibility_body_sha256": hashlib.sha256(_canonical(body)).hexdigest(),
        "eligibility_body_matches": hashlib.sha256(_canonical(body)).hexdigest() == EXPECTED_ELIGIBILITY,
        "eligible_groups_recorded": (eligibility.get("counts") or {}).get("eligible_groups"),
        "eligible_candidates_recorded": (eligibility.get("counts") or {}).get("eligible_candidates"),
        "group_assignment_count": group_count,
        "eligible_group_ids": len(eligible_groups),
        "ineligible_group_ids": len(ineligible_groups),
        "eligible_and_ineligible_overlap": len(eligible_groups & ineligible_groups),
        "output_lf_normalized_hashes_match": output_lf_matches,
        "output_hash_note": "Working-tree JSONL files contain CR bytes. Their LF-normalized SHA-256 matches the manifest. The files were not rewritten.",
        "output_hashes": output_hashes,
        "leakage_clearance": "NOT_CLAIMED",
        "recorded_corpus_limitation": "The corpus approval template says gold-answer strings remain in reference paragraphs and the corpus is not leakage-free.",
        "git_commit": revision,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "hardware": "UNKNOWN",
    }


def main() -> int:
    report = audit()
    destination = ROOT / "evaluation/experiments/experiment3/manifests/corpus_audit.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("corpus_sha256_matches", "cr_byte_count", "unique_article_ids", "eligible_groups_recorded", "eligible_group_ids", "ineligible_group_ids", "git_commit")}))
    required = (
        report["corpus_sha256_matches"] and report["cr_byte_count"] == 0 and report["unique_article_ids"] == 1844
        and report["article_ids_sorted"] and report["index_version_matches"] and report["index_corpus_sha256_matches"]
        and all(report["index_file_hashes_match"].values()) and report["eligibility_body_matches"]
        and report["eligible_groups_recorded"] == 372 and report["eligible_group_ids"] == 372
        and report["ineligible_group_ids"] == 15 and report["eligible_and_ineligible_overlap"] == 0
        and all(report["output_lf_normalized_hashes_match"].values())
    )
    return 0 if required else 1


if __name__ == "__main__":
    raise SystemExit(main())
