"""Development evidence corpus and historical-evidence recovery.

Reads the approved Development roster and HotpotQA reference paragraphs.
Does not open Final Test labels, does not modify data/, and does not approve
a corpus freeze.
"""
from __future__ import annotations

import collections
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.verifiers.evidence_retriever import EvidenceRetriever, file_sha256
from evaluation.data_preparation.final_test_workflow import (
    ROOT, canonical_bytes, context_hashes, jsonl_bytes, read_jsonl, sha256_bytes, sha256_file,
)

VERSION = "development_evidence_corpus_v1"
OUTPUT = ROOT / "evaluation/artifacts/person1" / VERSION
RECOVERY = ROOT / "evaluation/artifacts/person1/historical_evidence_recovery_v1"
ELIGIBLE = ROOT / "evaluation/artifacts/person1/research_v1_exploratory_eligibility_approved_v1/development_eligible.jsonl"
SNAPSHOT = ROOT / "evaluation/datasets/research_v1_exploratory/research_v1_exploratory_v1"
HOTPOT_RELEASE = "hotpotqa/hotpot_qa distractor@1908d6afbbead072334abe2965f91bd2709910ab"
EMBEDDING_MODEL = EvidenceRetriever.EMBEDDING_MODEL
RELEVANCE_COSINE = 0.78
TOP_K = 5
TOKEN = re.compile(r"[a-z0-9]+")
GIT_INDEX_COMMIT = "be52b30c65afdd64a39b7e954d0af4ea32741f9a"


def _forbid(path: Path) -> None:
    text = str(path).replace("\\", "/").lower()
    if "final_test" in text or "_custodian" in text:
        raise RuntimeError(f"refusing a Final Test path: {path}")


def _norm_title(value: str) -> str:
    return "".join(TOKEN.findall(str(value).replace("_", " ").lower()))


def _wiki_url(title: str) -> str:
    return "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_"), safe="()_,")


def _git_show(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def _recover_misnamed_index() -> dict:
    """Recover the git index whose directory name says 13083 but whose manifest does not."""
    destination = RECOVERY / "recovered/data/articles_13083_index"
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for name in ("manifest.json", "chunks.json", "faiss.index"):
        data = _git_show(GIT_INDEX_COMMIT, f"data/articles_13083_index/{name}")
        target = destination / name
        if not target.exists():
            target.write_bytes(data)
        records.append({"path": f"data/articles_13083_index/{name}", "sha256": sha256_bytes(target.read_bytes()),
                        "bytes": target.stat().st_size})
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    return {"status": "ORIGINAL_RECOVERED", "recovered_to": str(destination.relative_to(ROOT)).replace("\\", "/"),
            "source_commit": GIT_INDEX_COMMIT, "source_commit_date": "2026-10-23T22:02:26+05:30",
            "original_paths": [row["path"] for row in records], "files": records,
            "manifest_corpus_sha256": manifest.get("corpus_sha256"), "manifest_index_version": manifest.get("index_version"),
            "manifest_corpus_path": manifest.get("corpus_path"),
            "identity_note": "The directory is named articles_13083_index. Its manifest records test_evidence_corpus.json, corpus SHA-256 0170d64b…, and index idx-62d878fbb62f. It is not the 13,083-article corpus or idx-6d28c9c49dac."}


def _file_record(path: Path, expected: str | None, status_if_match: str) -> dict:
    if not path.exists():
        return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "status": "NOT_RECOVERABLE_FROM_AVAILABLE_EVIDENCE",
                "expected_sha256": expected, "reason": "Path is absent from the working tree and from git objects searched for this name."}
    digest = sha256_file(path)
    status = status_if_match if expected is None or digest == expected else "CONFLICTING_PROVENANCE"
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "status": status, "sha256": digest,
            "bytes": path.stat().st_size, "expected_sha256": expected, "git_blob": "NOT_IN_GIT_HISTORY"}


def recovery_inventory(misnamed: dict) -> dict:
    appointment = ROOT / "evaluation/config/final_test_v2_custodian_appointment.json"
    appointment_body = json.loads(appointment.read_text(encoding="utf-8"))
    return {
        "record_type": "historical_evidence_recovery_v1",
        "label": "RECOVERY_INVENTORY",
        "final_test_labels_opened": False,
        "artifacts": [
            _file_record(ROOT / "data/articles_13083.json",
                         "b26539d013201a0435884098ae8bd3544342d0a815964bf104b9524808e9bfa8",
                         "ORIGINAL_VERIFIED_IN_PLACE"),
            _file_record(ROOT / "data/evidence_index/articles_13083/manifest.json", None, "ORIGINAL_VERIFIED_IN_PLACE"),
            _file_record(ROOT / "data/evidence_corpus.json",
                         "668b48aa59c758d6e5d082f9d07b9c544730c545ae3af36728e68a0144ec6ec5",
                         "ORIGINAL_VERIFIED_IN_PLACE"),
            _file_record(ROOT / "data/evidence_index/evidence_corpus/manifest.json", None, "ORIGINAL_VERIFIED_IN_PLACE"),
            _file_record(ROOT / "data/test_evidence_corpus.json",
                         "0170d64b697dab9bbeb91e2f935b6bcad862ae8bb55958beea712ccf1e424795",
                         "ORIGINAL_VERIFIED_IN_PLACE"),
            {"artifact": "execution_source_custody_zip", "status": "NOT_RECOVERABLE_FROM_AVAILABLE_EVIDENCE",
             "searched": ["git rev-list --all --objects for .zip", "working tree *.zip", "evaluation/docs.zip"],
             "found": "No custody ZIP blob or working-tree ZIP. No recovery archive was created because no original execution-source records for that ZIP were found.",
             "not_created": "ORIGINAL_CUSTODY_ZIP"},
            {"artifact": "verifier_collection_adapter_configuration", "status": "NOT_RECOVERABLE_FROM_AVAILABLE_EVIDENCE",
             "environment": "VERIFIER_COLLECTION_ADAPTER_CONFIG was not used. No reviewed local adapter JSON was found.",
             "templates_are_not_historical_runs": ["docs/verifier_project_adapter.template.json", "docs/arithmetic_adapter.template.json"],
             "unknown_parameters": ["embedding_snapshot", "nli_snapshot", "index_receipt", "service_observation", "hardware", "collection timestamp"]},
            {"artifact": "final_test_evaluation_authorization", "status": "NOT_FOUND",
             "cannot_reconstruct_as_approval": True,
             "appointment_path": "evaluation/config/final_test_v2_custodian_appointment.json",
             "appointment_sha256": sha256_file(appointment),
             "evaluation_authorization": appointment_body.get("evaluation_authorization"),
             "label_release": appointment_body.get("label_release")},
            {"artifact": "git_articles_13083_index", **misnamed},
        ],
    }


def _load_questions() -> tuple[list[dict], set[str]]:
    eligible = read_jsonl(ELIGIBLE)
    groups = collections.defaultdict(list)
    for row in eligible:
        groups[row["related_group_id"]].append(row)
    by_group = {}
    for path in (SNAPSHOT / "development_candidates.jsonl",):
        _forbid(path)
        for row in read_jsonl(path):
            if row["related_group_id"] in groups and row["related_group_id"] not in by_group:
                by_group[row["related_group_id"]] = row
    history_hashes = set()
    for row in read_jsonl(SNAPSHOT / "history_candidates.jsonl"):
        history_hashes |= context_hashes(row.get("evidence_context"))
    questions = []
    for gid, members in sorted(groups.items()):
        source = by_group[gid]
        questions.append({
            "question_id": source["question_id"],
            "related_group_id": gid,
            "benchmark": source["benchmark"],
            "question": source["question"],
            "evidence_context": source.get("evidence_context") or [],
            "supporting_facts": source.get("supporting_facts") or [],
            "source_dataset_id": (source.get("source") or {}).get("research_v1_dataset_id"),
            "candidate_answers": sorted({str(row.get("candidate_answer", "")) for row in members}),
            "gold_answer": str(source.get("gold_answer", "")),
            "label_classes": sorted({member["label_class"] for member in members}),
        })
    return questions, history_hashes


def _articles(questions: list[dict], history_hashes: set[str]) -> tuple[list[dict], list[dict], dict]:
    articles = {}
    provenance = []
    excluded_overlap = []
    for question in questions:
        if question["benchmark"] != "HotpotQA":
            continue
        support = {_norm_title(title) for title, _sentence in question["supporting_facts"]}
        for paragraph in question["evidence_context"]:
            title = str(paragraph.get("title", ""))
            text = str(paragraph.get("text", ""))
            if not text.strip():
                continue
            hashes = context_hashes([paragraph])
            if hashes & history_hashes:
                excluded_overlap.append({"question_id": question["question_id"], "title": title, "reason": "shared_history_paragraph_hash"})
                continue
            digest = sha256_bytes(f"{title}\0{text}".encode("utf-8"))
            article_id = "hotpot-para-" + digest[:16]
            slot = articles.setdefault(article_id, {"id": article_id, "title": title, "text": text, "url": _wiki_url(title)})
            if slot["text"] != text or slot["title"] != title:
                raise ValueError("article id collision with different text")
            provenance.append({"article_id": article_id, "question_id": question["question_id"],
                               "related_group_id": question["related_group_id"], "title": title,
                               "text_sha256": sha256_bytes(text.encode("utf-8")),
                               "role": "supporting_fact_title" if _norm_title(title) in support else "benchmark_distractor_paragraph",
                               "source_dataset_id": question["source_dataset_id"]})
    ordered = [articles[key] for key in sorted(articles)]
    return ordered, provenance, {"excluded_history_overlap_paragraphs": excluded_overlap,
                                 "history_overlap_count": len(excluded_overlap)}


def _contamination(questions: list[dict], articles: list[dict]) -> dict:
    by_question = {row["question_id"]: row for row in questions if row["benchmark"] == "HotpotQA"}
    counts = collections.Counter()
    for question in by_question.values():
        texts = [str(item.get("text", "")) for item in question["evidence_context"]]
        gold = question["gold_answer"].strip()
        for label, answer in zip(question["label_classes"], question["candidate_answers"], strict=False):
            pass
        gold_hit = len(gold) >= 4 and any(gold.casefold() in text.casefold() for text in texts)
        counts["gold_answer_string_occurs_in_own_reference_paragraph"] += int(gold_hit)
        counts["gold_answer_shorter_than_4_characters"] += int(len(gold) < 4)
        for answer in question["candidate_answers"]:
            cleaned = answer.strip()
            if len(cleaned) < 4:
                counts["candidate_answer_shorter_than_4_characters"] += 1
                continue
            if any(cleaned.casefold() in text.casefold() for text in texts):
                counts["candidate_answer_string_occurs_in_own_reference_paragraph"] += 1
    counts["articles"] = len(articles)
    counts["corpus_contains_answer_fields"] = 0
    return {"method": "casefold_substring_length_at_least_4_against_the_question_own_paragraphs",
            "counts": dict(counts), "questions_checked": len(by_question),
            "statement": "Answer strings were not copied into corpus fields. A substring hit means the benchmark paragraph already contains that string. Short answers are counted separately and are not treated as field embedding."}


def _title_sets() -> dict[str, set[str]]:
    found = {}
    for name in ("articles_13083.json", "evidence_corpus.json"):
        path = ROOT / "data" / name
        _forbid(path)
        rows = json.loads(path.read_text(encoding="utf-8"))
        found[name] = {_norm_title(row.get("title", "")) for row in rows}
        del rows
    return found


def _search_saved_index(index_dir: Path, model: SentenceTransformer, queries: list[str]) -> list[list[dict]]:
    manifest = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("embedding_model") != EMBEDDING_MODEL:
        raise ValueError("saved index embedding model differs from the retriever")
    index = faiss.read_index(str(index_dir / "faiss.index"))
    chunks = json.loads((index_dir / "chunks.json").read_text(encoding="utf-8"))
    encoded = model.encode(queries, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
    encoded = np.ascontiguousarray(encoded, dtype=np.float32)
    faiss.normalize_L2(encoded)
    k = min(TOP_K, index.ntotal)
    scores, indices = index.search(encoded, k)
    results = []
    for row_scores, row_ids in zip(scores, indices):
        hits = []
        for score, index_id in zip(row_scores, row_ids):
            if int(index_id) < 0:
                continue
            chunk = chunks[int(index_id)]
            hits.append({"score": float(score), "title": chunk.get("title", ""), "article_id": chunk.get("article_id"),
                         "chunk_id": chunk.get("chunk_id"), "above_relevance_gate": float(score) >= RELEVANCE_COSINE})
        results.append(hits)
    del chunks
    return results


def _search_new(retriever: EvidenceRetriever, queries: list[str]) -> list[list[dict]]:
    results = []
    for query in queries:
        hits = []
        for row in retriever.retrieve(query, k=TOP_K):
            hits.append({"score": row["score"], "title": row["title"], "article_id": row.get("article_id"),
                         "source_id": row.get("source_id"), "chunk_id": row.get("chunk_id"),
                         "above_relevance_gate": row["score"] >= RELEVANCE_COSINE, "lexical_hit": row.get("lexical_hit")})
        results.append(hits)
    return results


def _coverage_row(question: dict, hits: list[dict], corpus_titles: set[str], existing_titles: dict[str, set[str]]) -> dict:
    support = [title for title, _sentence in question["supporting_facts"]]
    support_norm = {_norm_title(title) for title in support}
    retrieved_norm = {_norm_title(hit["title"]) for hit in hits}
    if question["benchmark"] != "HotpotQA":
        status = "not_applicable_arithmetic_no_external_evidence_required"
        relevant = None
    elif support_norm & retrieved_norm:
        status = "supporting_title_retrieved"
        relevant = True
    else:
        status = "retrieval_miss_no_supporting_title_in_top_k"
        relevant = False
    return {
        "question_id": question["question_id"],
        "related_group_id": question["related_group_id"],
        "benchmark": question["benchmark"],
        "required_supporting_titles": support,
        "new_corpus_contains_all_supporting_titles": bool(support_norm) and support_norm <= corpus_titles,
        "articles_13083_contains_all_supporting_titles": bool(support_norm) and support_norm <= existing_titles["articles_13083.json"],
        "evidence_corpus_500_contains_all_supporting_titles": bool(support_norm) and support_norm <= existing_titles["evidence_corpus.json"],
        "retrieval_status": status,
        "relevant_evidence_retrieved": relevant,
        "retrieved": [{key: hit[key] for key in ("article_id", "title", "score", "above_relevance_gate") if key in hit} for hit in hits],
        "max_cosine": max((hit["score"] for hit in hits), default=None),
        "any_hit_above_0_78": any(hit["above_relevance_gate"] for hit in hits),
    }


def prepare() -> dict:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise FileExistsError("Refusing to overwrite the development evidence corpus version")
    questions, history_hashes = _load_questions()
    articles, provenance, overlap = _articles(questions, history_hashes)
    contamination = _contamination(questions, articles)
    if any("candidate_answer" in article or "gold_answer" in article for article in articles):
        raise ValueError("answer fields entered the corpus")
    existing_titles = _title_sets()
    model = SentenceTransformer(EMBEDDING_MODEL)
    existing_hits = {
        "articles_13083": _search_saved_index(ROOT / "data/evidence_index/articles_13083", model,
                                              [row["question"] for row in questions]),
        "evidence_corpus_500": _search_saved_index(ROOT / "data/evidence_index/evidence_corpus", model,
                                                   [row["question"] for row in questions]),
    }
    OUTPUT.mkdir(parents=True)
    corpus_path = OUTPUT / "corpus.json"
    corpus_path.write_bytes(canonical_bytes(articles))
    retriever = EvidenceRetriever(str(corpus_path), model=model, chunk_size=500)
    new_hits = _search_new(retriever, [row["question"] for row in questions])
    corpus_titles = {_norm_title(article["title"]) for article in articles}
    coverage = [_coverage_row(question, hits, corpus_titles, existing_titles)
                for question, hits in zip(questions, new_hits)]
    existing_coverage = {
        name: [_coverage_row(question, hits, corpus_titles, existing_titles) for question, hits in zip(questions, rows)]
        for name, rows in existing_hits.items()
    }
    def tally(rows: list[dict], benchmark: str) -> dict:
        chosen = [row for row in rows if row["benchmark"] == benchmark]
        retrieved = sum(row["relevant_evidence_retrieved"] is True for row in chosen)
        present = sum(row["new_corpus_contains_all_supporting_titles"] for row in chosen)
        return {"questions": len(chosen), "supporting_title_retrieved": retrieved,
                "all_supporting_titles_present_in_new_corpus": present}
    hotpot_new = tally(coverage, "HotpotQA")
    summary = {
        "corpus_version": VERSION,
        "eligible_questions": len(questions),
        "eligible_by_benchmark": dict(collections.Counter(row["benchmark"] for row in questions)),
        "new_corpus_articles": len(articles),
        "hotpotqa_new_corpus": hotpot_new,
        "hotpotqa_existing_title_presence": {
            "articles_13083_all_supporting_titles": sum(row["articles_13083_contains_all_supporting_titles"] for row in coverage if row["benchmark"] == "HotpotQA"),
            "evidence_corpus_500_all_supporting_titles": sum(row["evidence_corpus_500_contains_all_supporting_titles"] for row in coverage if row["benchmark"] == "HotpotQA"),
        },
        "hotpotqa_existing_retrieval": {
            name: sum(row["relevant_evidence_retrieved"] is True for row in rows if row["benchmark"] == "HotpotQA")
            for name, rows in existing_coverage.items()
        },
        "gsm8k_retrieval_status": "not_applicable_arithmetic_no_external_evidence_required",
        "history_overlap": overlap,
        "contamination": contamination,
        "index_version": retriever.index_version,
        "corpus_sha256": file_sha256(corpus_path),
        "embedding_model": EMBEDDING_MODEL,
        "top_k": TOP_K,
        "relevance_cosine_gate": RELEVANCE_COSINE,
        "query": "question text only",
        "freeze": {"status": "PROPOSAL_NOT_APPROVED", "approved": False, "approver": None, "collection_authorized": False},
    }
    files = {
        "source_provenance.jsonl": jsonl_bytes(sorted(provenance, key=lambda row: (row["article_id"], row["question_id"]))),
        "coverage_new_corpus.jsonl": jsonl_bytes(coverage),
        "coverage_articles_13083.jsonl": jsonl_bytes(existing_coverage["articles_13083"]),
        "coverage_evidence_corpus_500.jsonl": jsonl_bytes(existing_coverage["evidence_corpus_500"]),
        "leakage_audit.json": canonical_bytes({"history_overlap": overlap, "contamination": contamination,
                                               "final_test_labels_opened": False,
                                               "final_test_questions_used": False,
                                               "answer_fields_in_corpus": False}),
    }
    manifest = {
        "corpus_version": VERSION,
        "status": "PROPOSAL_NOT_APPROVED",
        "approved": False,
        "frozen": False,
        "collection_authorized": False,
        "final_test_authorized": False,
        "source_roster": "research_v1_exploratory_eligibility_approved_v1",
        "source_snapshot": "research_v1_exploratory_v1",
        "hotpot_release": HOTPOT_RELEASE,
        "inclusion_rule": "Every non-empty reference paragraph on an eligible HotpotQA Development question is included. Distractors stay. Paragraphs whose hash matches History are excluded. GSM8K solutions are not included. Candidate answers and gold answers are not corpus fields.",
        "url_status": "DERIVED_FROM_TITLE_NOT_FETCHED",
        "publication_date": "UNKNOWN",
        "web_retrieval_date": None,
        "chunk_size": 500,
        "embedding_model": EMBEDDING_MODEL,
        "index_version": retriever.index_version,
        "summary": summary,
    }
    files["source_manifest.json"] = canonical_bytes(manifest)
    for name, data in files.items():
        (OUTPUT / name).write_bytes(data)
    summary["output_sha256"] = {name: sha256_file(OUTPUT / name) for name in sorted(files)}
    summary["output_sha256"]["corpus.json"] = summary["corpus_sha256"]
    misnamed = _recover_misnamed_index()
    inventory = recovery_inventory(misnamed)
    recovery_dir = RECOVERY
    recovery_dir.mkdir(parents=True, exist_ok=True)
    (recovery_dir / "recovery_inventory.json").write_bytes(canonical_bytes(inventory))
    (OUTPUT / "preparation_summary.json").write_bytes(canonical_bytes(summary))
    return summary


def validate() -> dict:
    summary = json.loads((OUTPUT / "preparation_summary.json").read_text(encoding="utf-8"))
    corpus = json.loads((OUTPUT / "corpus.json").read_text(encoding="utf-8"))
    if any(set(article) - {"id", "title", "text", "url"} for article in corpus):
        raise ValueError("corpus article contains a field other than id, title, text, and url")
    if sha256_file(OUTPUT / "corpus.json") != summary["corpus_sha256"]:
        raise ValueError("corpus hash changed")
    mismatches = [name for name, digest in summary["output_sha256"].items() if sha256_file(OUTPUT / name) != digest]
    if mismatches:
        raise ValueError(f"stored hash mismatch: {mismatches}")
    if summary["history_overlap"]["history_overlap_count"] != 0:
        raise ValueError("history overlap was not zero")
    if summary["freeze"]["approved"] is not False or summary["freeze"]["collection_authorized"] is not False:
        raise ValueError("corpus freeze flags changed")
    inventory = json.loads((RECOVERY / "recovery_inventory.json").read_text(encoding="utf-8"))
    if inventory["final_test_labels_opened"] is not False:
        raise ValueError("recovery inventory claims Final Test labels were opened")
    return {"corpus_articles": len(corpus), "corpus_sha256": summary["corpus_sha256"],
            "index_version": summary["index_version"],
            "recovery_statuses": {row.get("path", row.get("artifact")): row["status"] for row in inventory["artifacts"]}}


def main(argv: list[str] | None = None) -> int:
    command = (argv or ["prepare"])[0]
    if command == "validate":
        print(json.dumps(validate(), indent=2, sort_keys=True))
    elif command == "prepare":
        print(json.dumps(prepare(), indent=2, sort_keys=True))
    else:
        raise SystemExit("command must be prepare or validate")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
