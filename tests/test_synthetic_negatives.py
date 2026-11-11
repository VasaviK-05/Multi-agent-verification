"""Synthetic negative generation and label provenance. Fixtures only; no empirical claims."""

import pytest

from app.game.offline.records import Example, label_composition
from app.game.research.readiness import check_readiness
from evaluation.data_preparation import label_classes as lc
from evaluation.data_preparation import synthetic_negatives as sn
from tests.test_game_research import REVISION, study

CONTEXT = [{"title": "Alpha Band", "text": "Alpha Band is a group."},
           {"title": "Beta Records (label)", "text": "Beta Records is a label."},
           {"title": "Gamma City", "text": "Gamma City is a city."},
           {"title": "Delta River", "text": "Delta River flows."}]


def test_gsm8k_negative_is_gold_plus_one_and_keeps_format():
    assert sn.gsm8k_negative("18") == {"answer": "19", "transformation": "gold_plus_one", "delta": 1}
    assert sn.gsm8k_negative("1,000")["answer"] == "1,001"
    assert sn.gsm8k_negative("3.50")["answer"] == "4.50"
    assert sn.gsm8k_negative("$5")["answer"] == "$6"
    assert sn.gsm8k_negative("not a number") is None
    assert [sn.gsm8k_negative("72", ["72"]) for _ in range(3)] == [sn.gsm8k_negative("72", ["72"])] * 3


def test_gsm8k_negative_avoids_existing_group_answers_and_sign_changes():
    # gold+1 already present (for example as an UNRESOLVED candidate) must never be relabelled.
    assert sn.gsm8k_negative("10", ["11"]) == {"answer": "9", "transformation": "gold_minus_one", "delta": -1}
    assert sn.gsm8k_negative("0", ["1"]) == {"answer": "2", "transformation": "gold_plus_two", "delta": 2}
    assert sn.gsm8k_negative("10", ["11", "9", "12"]) is None


def test_gsm8k_quality_flags():
    assert sn.gsm8k_quality_flags("How many apples are left?") == {"how_many_question": True,
                                                                   "rounding_or_ratio_cue_present": False}
    assert sn.gsm8k_quality_flags("What percentage is left, roughly?")["rounding_or_ratio_cue_present"] is True


def test_hotpotqa_transformation_order():
    neg = lambda gold, **kw: sn.hotpotqa_negative(gold, question=kw.get("q", "Which one?"),
                                                  question_type=kw.get("t", "bridge"), context=CONTEXT,
                                                  supporting_titles=kw.get("s", ["Alpha Band", "Gamma City"]),
                                                  key="g1", taken=kw.get("taken", ()))
    assert neg("yes") == {"answer": "no", "transformation": "yes_no_complement"}
    assert neg("No", t="comparison") == {"answer": "Yes", "transformation": "yes_no_complement"}
    assert neg("Alpha Band", t="comparison") == {"answer": "Gamma City", "transformation": "comparison_other_entity"}
    assert neg("1,999 people") == {"answer": "2,000 people", "transformation": "numeric_increment"}
    distractor = neg("Somebody Else")
    assert distractor["transformation"] == "distractor_paragraph_title"
    assert distractor["answer"] in {"Beta Records", "Delta River"}
    assert neg("Somebody Else") == distractor


def test_hotpotqa_distractor_excludes_support_gold_overlap_and_question_titles():
    out = sn.hotpotqa_negative("Delta Force", question="Is Beta Records famous?", question_type="bridge",
                               context=CONTEXT, supporting_titles=["Alpha Band", "Gamma City"], key="k")
    assert out is None
    assert sn.hotpotqa_negative("x", question="q", question_type="bridge", context=[], supporting_titles=[], key="k") is None


def test_opaque_ids_hide_class_and_are_stable():
    a = sn.opaque_id("ft2", "group-1", "19")
    assert a == sn.opaque_id("ft2", "group-1", " 19 ") and a != sn.opaque_id("rx1", "group-1", "19")
    assert a.startswith("ft2-") and len(a) == 24 and "incorrect" not in a and "gold" not in a


def test_label_fields_never_claim_human_verification_without_a_record():
    synthetic = lc.label_fields(lc.SYNTHETIC_INCORRECT, label_source="gen", label_method="gold_plus_one", provenance={})
    assert synthetic["answer_is_correct"] is False and synthetic["human_verified"] is False
    assert synthetic["example_label_method"] == "synthetic_transformation"
    with pytest.raises(ValueError, match="human review record"):
        lc.label_fields(lc.HUMAN_VERIFIED_INCORRECT, label_source="h", label_method="m", provenance={})
    with pytest.raises(ValueError, match="Only HUMAN_VERIFIED_INCORRECT"):
        lc.label_fields(lc.SYNTHETIC_INCORRECT, label_source="g", label_method="m", provenance={},
                        human_review_record={"reviewer": "x"})
    assert lc.label_fields(lc.UNRESOLVED, label_source="s", label_method="m", provenance={})["answer_is_correct"] is None


def test_research_v1_classes():
    assert lc.research_v1_class({"correctness_status": "verified_correct"}) == lc.VERIFIED_CORRECT
    assert lc.research_v1_class({"correctness_status": "verified_incorrect"}) == lc.SYNTHETIC_INCORRECT
    assert lc.research_v1_class({"correctness_status": "unresolved"}) == lc.UNRESOLVED
    assert lc.research_v1_class({"correctness_status": "verified_incorrect",
                                 "human_review_record": {"r": 1}}) == lc.HUMAN_VERIFIED_INCORRECT


def _example(**updates):
    spec = study()
    data = spec.manifest.partition("development").examples[0].model_dump()
    return Example(**{**data, **updates})


def test_example_label_class_and_synthetic_contract():
    assert _example().label_class == "VERIFIED_CORRECT"
    synthetic = _example(answer_is_correct=False, label_method="synthetic_transformation")
    assert synthetic.label_class == "SYNTHETIC_INCORRECT"
    assert _example(answer_is_correct=False, label_method="independent_human").label_class == "HUMAN_VERIFIED_INCORRECT"
    with pytest.raises(ValueError, match="incorrect answers only"):
        _example(label_method="synthetic_transformation")
    assert label_composition([_example(), synthetic, synthetic]) == (("VERIFIED_CORRECT", 1), ("SYNTHETIC_INCORRECT", 2))


def test_readiness_reports_label_composition_per_role():
    report = check_readiness(study(), actual_code_revision=REVISION)
    assert {(role, name) for role, name, _ in report.label_composition} == {
        ("history", "VERIFIED_CORRECT"), ("development", "VERIFIED_CORRECT"), ("final_test", "VERIFIED_CORRECT")}
