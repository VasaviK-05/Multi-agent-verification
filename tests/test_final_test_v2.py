"""Exploratory Development and Final Test v2: provenance, balance, exposure, leakage and isolation.

Fixture tests run everywhere; artifact tests run only where the Git-ignored datasets exist.
Final Test v2 labels are only aggregated, never printed.
"""

import json
import re

import pytest

from evaluation.data_preparation import build_exploratory_development as dev
from evaluation.data_preparation import build_final_test_v2 as ft2
from evaluation.data_preparation import build_offline_examples, run_verifier_attempts
from evaluation.data_preparation.final_test_workflow import (
    ROOT, context_hashes, final_test_gate, load_retirements, norm_question, read_jsonl,
)

LABEL_KEYS = {"label_class", "answer_is_correct", "correctness_status", "binary_label", "gold_answer", "generation",
              "label_source", "label_method", "label_provenance", "human_verified", "supporting_facts"}
CONFIG = {"seed": 7, "groups_per_benchmark": 2, "id_namespace": "ft2", "dataset_version": "fixture_v2"}


def row(role, gid, status, answer, gold, benchmark="GSM8K", question="How many apples are left?", source="gsm8k_train_1",
        **extra):
    return {"benchmark": benchmark, "question": question, "related_group_id": gid, "correctness_status": status,
            "candidate_answer": answer, "candidate_id": f"{source}::{answer}", "gold_answer": gold,
            "dataset_id": source, "partition": role, "validation_method": "fixture_check", **extra}


def hotpot_raw(question, answer, titles=("A", "B"), sentences=(["a0."], ["b0."])):
    return {"id": "abc", "question": question, "answer": answer, "type": "comparison",
            "context": {"title": list(titles), "sentences": [list(s) for s in sentences]},
            "supporting_facts": {"title": list(titles), "sent_id": [0, 0]},
            "_split": "validation", "_row_index": 3, "_row_sha256": "f" * 64}


def fixture_rows():
    return {
        "development": [row("development", "g1", "verified_correct", "10", "10"),
                        row("development", "g1", "unresolved", "11", "10"),
                        row("development", "h1", "verified_correct", "yes", "yes", benchmark="HotpotQA",
                            question="Are A and B both bands?", source="hotpot_abc")],
        "history": [row("history", "g2", "verified_correct", "5", "5", question="How many pears?", source="gsm8k_train_2"),
                    row("history", "g2", "verified_incorrect", "6", "5", question="How many pears?", source="gsm8k_train_2",
                        candidate_generation_provenance={"transformation": "gold + 1"}),
                    row("history", "g3", "unresolved", "3", "4", question="How many plums?", source="gsm8k_train_3")]}


def build():
    return dev.build_records(fixture_rows(), {"abc": hotpot_raw("Are A and B both bands?", "yes")})


def by_group(records, role):
    out = {}
    for r in records["labelled"][role]:
        out.setdefault(r["related_group_id"], {})[r["label_class"]] = r
    return out


def test_exploratory_pairs_and_provenance():
    records = build()
    assert build() == records
    development, history = by_group(records, "development"), by_group(records, "history")
    generated = development["g1"]["SYNTHETIC_INCORRECT"]
    assert generated["candidate_answer"] == "9" and generated["generation"]["transformation"] == "gold_minus_one"
    assert generated["generation"]["generated_by_this_version"] is True and generated["human_verified"] is False
    assert generated["generation"]["gold_answer"] == "10" and generated["generation"]["source_question_id"] == "GSM8K:gsm8k_train_1"
    kept = history["g2"]["SYNTHETIC_INCORRECT"]
    assert kept["candidate_answer"] == "6" and kept["generation"]["generated_by_this_version"] is False
    assert development["h1"]["SYNTHETIC_INCORRECT"]["candidate_answer"] == "no"
    assert development["h1"]["VERIFIED_CORRECT"]["supporting_facts"] == [["A", 0], ["B", 0]]
    assert all(r["candidate_id"].startswith("rx1-") for role in dev.ROLES for r in records["labelled"][role])


def test_unresolved_candidates_stay_separate_and_are_never_relabelled():
    records = build()
    assert [(r["related_group_id"], r["candidate_answer"], r["label_class"], r["answer_is_correct"])
            for r in records["unresolved"]] == [("g1", "11", "UNRESOLVED", None), ("g3", "3", "UNRESOLVED", None)]
    labelled_answers = {(r["related_group_id"], r["candidate_answer"]) for role in dev.ROLES for r in records["labelled"][role]}
    assert ("g1", "11") not in labelled_answers
    assert records["skipped"] == [{"partition": "history", "related_group_id": "g3", "benchmark": "GSM8K",
                                   "reason": "no_verified_gold"}]


def test_blind_verifier_inputs_carry_no_label_or_generation_fields():
    records = build()
    blind = [r for role in dev.ROLES for r in records["blind"][role]]
    assert {tuple(r) for r in blind} == {dev.BLIND_FIELDS}
    assert not LABEL_KEYS & set().union(*map(set, blind))


def test_exploratory_split_integrity_is_enforced(tmp_path):
    rows = fixture_rows()
    rows["history"].append(row("history", "g1", "verified_correct", "10", "10"))
    with pytest.raises(ValueError, match="spans History and Development"):
        dev.build_records(rows, {"abc": hotpot_raw("Are A and B both bands?", "yes")})
    rows = fixture_rows()
    rows["history"].append(row("history", "g9", "verified_correct", "10", "10"))
    with pytest.raises(ValueError, match="History/Development leakage"):
        dev.audit(dev.build_records(rows, {"abc": hotpot_raw("Are A and B both bands?", "yes")}), tmp_path)
    report = dev.audit(build(), tmp_path)
    assert report["label_balance"]["development"]["GSM8K"]["paired_groups"] == 1
    assert report["label_balance"]["development"]["GSM8K"]["UNRESOLVED"] == 1
    assert report["human_verified_labels"] == 0


def test_inconsistent_raw_hotpotqa_record_is_skipped():
    records = dev.build_records(fixture_rows(), {"abc": hotpot_raw("A different question?", "yes")})
    assert {"partition": "development", "related_group_id": "h1", "benchmark": "HotpotQA",
            "reason": "raw_hotpotqa_record_missing_or_inconsistent"} in records["skipped"]


def test_v2_eligibility_excludes_exposed_and_duplicate_rows():
    seen_paragraph = context_hashes({"title": ["P"], "sentences": [["seen."]]})
    exposure = {"questions": {norm_question("Seen question?"): {"f"}}, "contexts": seen_paragraph, "facts": {"F\x000"}}
    mk = lambda q, title, sent: {"question": q, "context": {"title": [title], "sentences": [[sent]]},
                                 "supporting_facts": {"title": [title], "sent_id": [0]}}
    rows = [("1", mk("Seen question?", "X", "x.")), ("2", mk("Fresh?", "P", "seen.")), ("3", mk("Other?", "F", "f.")),
            ("4", mk("Clean?", "C", "c.")), ("5", mk("clean", "D", "d."))]
    eligible, reasons = ft2.eligibility("HotpotQA", rows, exposure, set(), use_facts=True)
    assert eligible == ["4"]
    assert reasons == {"previously_exposed_question": 1, "exposed_exact_paragraph": 1, "exposed_supporting_fact": 1,
                       "duplicate_normalized_question": 1}


def hotpot_source(i, titles, answer="yes"):
    return {"id": f"h{i}", "question": f"Question {i}?", "answer": answer, "type": "comparison",
            "context": {"title": list(titles), "sentences": [[f"{t} text."] for t in titles]},
            "supporting_facts": {"title": list(titles), "sent_id": [0] * len(titles)}}


def test_v2_selection_is_seeded_and_drops_within_sample_shared_paragraphs():
    rows = [hotpot_source(0, ["S", "T0"]), hotpot_source(1, ["S", "T1"]), hotpot_source(2, ["U", "T2"]),
            hotpot_source(3, ["V", "T3"])]
    ids, three = ["h0", "h1", "h2", "h3"], {**CONFIG, "groups_per_benchmark": 3}
    chosen, summary = ft2.select("HotpotQA", "validation", rows, ids, three)
    assert len(chosen) == 3 and len({g["source_id"] for g in chosen} & {"h0", "h1"}) == 1
    assert set(summary["skipped_while_selecting"]) <= {"shares_paragraph_or_supporting_fact_within_sample"}
    assert ft2.select("HotpotQA", "validation", rows, ids, three)[0] == chosen
    with pytest.raises(ValueError, match="only 1 of 2"):
        ft2.select("HotpotQA", "validation", rows[:2], ["h0", "h1"], CONFIG)
    gsm = [{"question": "How many cats?", "answer": "work\n#### 18"}, {"question": "How many dogs?", "answer": "#### 4"}]
    chosen, _ = ft2.select("GSM8K", "train", gsm, ["gsm8k_train_00000", "gsm8k_train_00001"], CONFIG)
    assert sorted((g["gold"], g["negative"]["answer"], g["negative"]["transformation"]) for g in chosen) == [
        ("18", "19", "gold_plus_one"), ("4", "5", "gold_plus_one")]
    assert {g["question_id"] for g in chosen} == {"GSM8K:gsm8k_train_0", "GSM8K:gsm8k_train_1"}


def test_v2_roster_is_blind_and_classes_are_indistinguishable_by_keys():
    groups, _ = ft2.select("HotpotQA", "validation", [hotpot_source(0, ["S", "T0"]), hotpot_source(2, ["U", "T2"])],
                           ["h0", "h2"], CONFIG)
    pairs = [p for g in groups for p in ft2.candidate_rows(g, CONFIG)]
    roster, labels = [p[0] for p in pairs], [p[1] for p in pairs]
    assert {tuple(r) for r in roster} == {ft2.ROSTER_FIELDS}
    assert not ft2.FORBIDDEN_ROSTER_KEYS & set().union(*map(set, roster))
    assert all(re.fullmatch(r"ft2-[0-9a-f]{20}", r["candidate_id"]) for r in roster)
    assert sorted(l["label_class"] for l in labels) == ["SYNTHETIC_INCORRECT"] * 2 + ["VERIFIED_CORRECT"] * 2
    assert all(l["human_verified"] is False and l["human_review_record"] is None for l in labels)
    assert all(l["binary_label"] is (l["label_class"] == "VERIFIED_CORRECT") for l in labels)
    assert ft2.isolation_audit(roster, CONFIG)["passed"]
    leaked = [{**roster[0], "gold_answer": "x"}] + roster[1:]
    assert not ft2.isolation_audit(leaked, CONFIG)["passed"]


def test_prior_identity_scan_detects_overlap(tmp_path):
    prior = tmp_path / "prior.jsonl"
    prior.write_text(json.dumps({"question": "Question 0?", "candidate_answer": "yes", "related_group_id": "g",
                                 "nested": {"context": {"title": ["S"], "sentences": [["S text."]]},
                                            "supporting_facts": [["S", 0]]}}) + "\n", encoding="utf-8")
    found = ft2.prior_identities(prior)
    assert norm_question("Question 0?") in found["normalized_questions"]
    assert context_hashes({"title": ["S"], "sentences": [["S text."]]}) <= found["paragraph_hashes"]
    assert "S\x000" in found["supporting_facts"] and len(found["content_identities"]) == 1


def test_verifier_recording_and_offline_inputs_exclude_final_test():
    assert "final_test" not in run_verifier_attempts.PARTITIONS
    assert "final_test" not in build_offline_examples.PARTITIONS


EXPLORATORY = dev.OUTPUT
V2_EVAL = ROOT / "evaluation/datasets/final_test_research_v1_eval_v2"
V2_CUSTODIAN = ROOT / "evaluation/datasets/_custodian/final_test_research_v1_v2"
needs_exploratory = pytest.mark.skipif(not (EXPLORATORY / "manifest.json").exists(), reason="exploratory dataset absent")
needs_v2 = pytest.mark.skipif(not (V2_EVAL / "manifest.json").exists(), reason="Final Test v2 absent")


@needs_exploratory
def test_exploratory_artifact_balance_and_label_sources():
    manifest = json.loads((EXPLORATORY / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["human_verified_labels"] == 0 and manifest["human_approval"] == "DEFERRED"
    balance = manifest["label_balance"]
    assert {b: (v["VERIFIED_CORRECT"], v["SYNTHETIC_INCORRECT"], v["UNRESOLVED"], v["paired_groups"])
            for b, v in balance["development"].items()} == {"GSM8K": (187, 187, 122, 187), "HotpotQA": (200, 200, 210, 200)}
    assert {b: (v["VERIFIED_CORRECT"], v["SYNTHETIC_INCORRECT"], v["UNRESOLVED"], v["paired_groups"])
            for b, v in balance["history"].items()} == {"GSM8K": (277, 277, 199, 277), "HotpotQA": (300, 299, 340, 299)}
    for role in dev.ROLES:
        labelled = read_jsonl(EXPLORATORY / f"{role}_candidates.jsonl")
        assert {r["label_class"] for r in labelled} == {"VERIFIED_CORRECT", "SYNTHETIC_INCORRECT"}
        assert not any(r["human_verified"] for r in labelled)
        assert all(r["example_label_method"] == "synthetic_transformation" for r in labelled
                   if r["label_class"] == "SYNTHETIC_INCORRECT")
        blind = read_jsonl(EXPLORATORY / f"{role}_verifier_inputs.jsonl")
        assert not LABEL_KEYS & set().union(*map(set, blind))
    assert {r["label_class"] for r in read_jsonl(EXPLORATORY / "unresolved_candidates.jsonl")} == {"UNRESOLVED"}


@needs_exploratory
def test_exploratory_artifact_reproduces():
    assert not any(dev.validate().values())


@needs_v2
def test_final_test_v2_artifact_integrity_and_gate():
    result = ft2.validate(recompute=False)
    assert result["gate"][0] == "NOT APPROVED"
    assert "evaluation_authorization_pending" in result["gate"][1]
    assert result["stored_hash_mismatches"] == [] and result["artifacts"]["passed"]
    manifest = json.loads((V2_EVAL / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "NOT_AUTHORIZED" and manifest["enabled"] is False
    assert manifest["custody_status"] == "DESIGNATED_CUSTODIAN_IS_DATASET_CREATOR"
    assert manifest["custody_independence"] == "NOT_INDEPENDENT"
    assert manifest["evaluation_authorization"] == "PENDING" and manifest["label_release"] == "NOT_AUTHORIZED"
    assert manifest["human_verified_labels"] == 0
    assert manifest["exposure_audit"]["passed"] and manifest["leakage_audit"]["passed"]
    assert manifest["retired_final_test_reused"] is False and manifest["manifest_sha256"] not in load_retirements()
    assert all(v["VERIFIED_CORRECT"] == v["SYNTHETIC_INCORRECT"] == 300 and v["HUMAN_VERIFIED_INCORRECT"] == 0
               for v in manifest["label_counts"].values())
    assert final_test_gate(manifest, None, load_retirements()) == (
        "NOT APPROVED", ["evaluation_authorization_pending", "no_confirmatory_authorization_record"])
    assert all(r["eligible_source_id_sha256_matches_plan"] for r in manifest["selection_plan_reproduction"].values())


@needs_v2
def test_final_test_v2_is_disjoint_from_every_development_identity():
    roster = read_jsonl(V2_EVAL / "evaluation_roster.jsonl")
    reservation = json.loads((V2_EVAL / "final_test_reservation.json").read_text(encoding="utf-8"))
    assert {e["example_id"] for e in reservation["examples"]} == {r["candidate_id"] for r in roster}
    assert not any(k in e for e in reservation["examples"] for k in ("answer_is_correct", "label_class", "answer"))
    v2_questions = {norm_question(r["question"]) for r in roster}
    v2_groups = {r["related_group_id"] for r in roster}
    v2_content = {e["content_identity"] for e in reservation["examples"]}
    for path in (EXPLORATORY / "history_candidates.jsonl", EXPLORATORY / "development_candidates.jsonl",
                 EXPLORATORY / "unresolved_candidates.jsonl"):
        if path.exists():
            rows = read_jsonl(path)
            assert not v2_questions & {norm_question(r["question"]) for r in rows}
            assert not v2_groups & {r["related_group_id"] for r in rows}
            assert not v2_content & {r.get("content_identity") for r in rows}
    assert not ft2.FORBIDDEN_ROSTER_KEYS & set().union(*map(set, roster))
