"""Evaluator arithmetic/identity tests, not claims of analyzer accuracy."""
import json
import pytest
from app.analysis.evaluate_context import DEFAULT_FIXTURE, evaluate


def test_evaluator_reports_independently_counted_metrics_and_fallback_rate():
    cases = [
        {"id": "a", "expected": {"domain": "general", "domain_status": "clear", "verification_types": ["direct_fact"], "difficulty": "easy"}},
        {"id": "b", "expected": {"domain": "medical", "domain_status": "clear", "verification_types": ["arithmetic"], "difficulty": None}},
    ]
    outputs = [
        {"id": "b", "analysis": {"domain": "general", "domain_status": "unknown", "verification_types": [], "difficulty": "hard", "analysis_method": "heuristic_fallback"}},
        {"id": "a", "analysis": {"domain": "general", "domain_status": "clear", "verification_types": ["direct_fact", "consistency"], "difficulty": "easy", "analysis_method": "ollama"}},
    ]
    result = evaluate(cases, outputs)
    assert result["domain_accuracy"] == result["domain_status_accuracy"] == .5
    assert result["verification_type_precision_micro"] == result["verification_type_recall_micro"] == .5
    assert result["difficulty_band_agreement"] == 1 and result["difficulty_labeled_cases"] == 1
    assert result["fallback_rate"] == .5
    assert result["type_counts"] == {"true_positive": 1, "false_positive": 1, "false_negative": 1}
    for invalid in [outputs[:1], outputs + [outputs[0]]]:
        with pytest.raises(ValueError, match="IDs"): evaluate(cases, invalid)


def test_unknown_types_do_not_produce_perfect_precision_or_recall():
    case = {"id": "ambiguous", "expected": {"domain": "general", "domain_status": "unknown", "verification_types": [], "difficulty": None}}
    output = {"id": "ambiguous", "analysis": {"domain": "general", "domain_status": "unknown", "verification_types": [], "difficulty": "easy", "analysis_method": "heuristic"}}
    result = evaluate([case], [output])
    assert result["verification_type_precision_micro"] is None
    assert result["verification_type_recall_micro"] is None
    assert result["difficulty_band_agreement"] is None


def test_fixture_is_explicitly_semantic_and_covers_required_categories():
    fixture = json.loads(DEFAULT_FIXTURE.read_text())
    assert fixture["label_kind"] == "human_authored_semantic_expectations"
    assert {case["id"] for case in fixture["cases"]} == {
        "factual", "arithmetic", "code_only", "code_answer", "specialist", "mixed", "ambiguous", "multi_obligation", "long_simple", "short_difficult"}


@pytest.fixture
def valid_evaluation():
    case = {"id": "example", "question": "What is 2 + 2?", "expected": {
        "domain": "general", "domain_status": "clear", "verification_types": ["arithmetic"], "difficulty": "easy"}}
    output = {"id": "example", "analysis": {
        "domain": "general", "domain_status": "clear", "verification_types": ["arithmetic"],
        "difficulty": "easy", "analysis_method": "heuristic"}}
    return [case], [output]


@pytest.mark.parametrize("side", [0, 1])
@pytest.mark.parametrize("invalid", [None, {}, "not a list", [None], [[]]])
def test_invalid_collection_and_record_structure_is_value_error(valid_evaluation, side, invalid):
    args = list(valid_evaluation)
    args[side] = invalid
    with pytest.raises(ValueError, match="cases|outputs"):
        evaluate(*args)


@pytest.mark.parametrize("side", [0, 1])
@pytest.mark.parametrize("invalid_id", [None, "", "   ", True, 1, [], {}])
def test_ids_are_nonempty_strings(valid_evaluation, side, invalid_id):
    valid_evaluation[side][0]["id"] = invalid_id
    with pytest.raises(ValueError, match=r"\.id.*nonempty string"):
        evaluate(*valid_evaluation)


@pytest.mark.parametrize("side", [0, 1])
@pytest.mark.parametrize("field", ["id", "payload", "domain", "domain_status", "verification_types", "difficulty"])
def test_missing_required_fields_have_context(valid_evaluation, side, field):
    key = "expected" if side == 0 else "analysis"
    row = valid_evaluation[side][0]
    if field == "id": del row["id"]
    elif field == "payload": del row[key]
    else: del row[key][field]
    with pytest.raises(ValueError, match="id" if field == "id" else "example") as error:
        evaluate(*valid_evaluation)
    assert (key if field == "payload" else field) in str(error.value)


@pytest.mark.parametrize("side", [0, 1])
@pytest.mark.parametrize("payload", [None, [], "object required"])
def test_payload_must_be_an_object(valid_evaluation, side, payload):
    key = "expected" if side == 0 else "analysis"
    valid_evaluation[side][0][key] = payload
    with pytest.raises(ValueError, match=f"example.*{key}"):
        evaluate(*valid_evaluation)


@pytest.mark.parametrize("field,value", [
    ("domain", "geography"), ("domain", []), ("domain_status", "certain"),
    ("difficulty", "impossible"), ("difficulty", False),
    ("verification_types", "arithmetic"), ("verification_types", ["unsupported"]),
    ("verification_types", [True]), ("verification_types", [[]]),
])
@pytest.mark.parametrize("side", [0, 1])
def test_invalid_expected_and_actual_labels_identify_case_and_field(valid_evaluation, side, field, value):
    key = "expected" if side == 0 else "analysis"
    valid_evaluation[side][0][key][field] = value
    with pytest.raises(ValueError, match=f"example.*{key}.*{field}"):
        evaluate(*valid_evaluation)


def test_actual_method_and_difficulty_are_required(valid_evaluation):
    actual = valid_evaluation[1][0]["analysis"]
    del actual["analysis_method"]
    with pytest.raises(ValueError, match="example.*analysis_method"):
        evaluate(*valid_evaluation)
    actual["analysis_method"] = "heuristic"
    actual["difficulty"] = None
    with pytest.raises(ValueError, match="example.*difficulty"):
        evaluate(*valid_evaluation)


def test_duplicates_remain_set_based_and_ids_remain_unique(valid_evaluation):
    cases, outputs = valid_evaluation
    cases[0]["expected"]["verification_types"] *= 2
    outputs[0]["analysis"]["verification_types"] *= 3
    assert evaluate(cases, outputs)["type_counts"] == {"true_positive": 1, "false_positive": 0, "false_negative": 0}
    with pytest.raises(ValueError, match="example.*IDs"):
        evaluate(cases * 2, outputs)
    with pytest.raises(ValueError, match="example.*IDs"):
        evaluate(cases, outputs * 2)


@pytest.mark.parametrize("exists", [False, True])
@pytest.mark.parametrize("invalid_side", ["expected", "actual", "fixture", "question"])
def test_rejected_cli_input_cannot_create_or_overwrite_capture(valid_evaluation, tmp_path, monkeypatch, exists, invalid_side):
    import sys
    from app.analysis.evaluate_context import main
    cases, outputs = valid_evaluation
    fixture = {"fixture_version": "test", "cases": cases}
    if invalid_side == "expected": cases[0]["expected"]["domain"] = "invalid"
    elif invalid_side == "actual": outputs[0]["analysis"]["domain"] = "invalid"
    elif invalid_side == "fixture": fixture = []
    else: del cases[0]["question"]
    fixture_path, outputs_path, capture = [tmp_path / name for name in ["fixture.json", "outputs.json", "capture.json"]]
    fixture_path.write_text(json.dumps(fixture))
    outputs_path.write_text(json.dumps(outputs))
    if exists: capture.write_bytes(b"preserve this capture")
    argv = ["evaluate_context", "--fixture", str(fixture_path), "--save-outputs", str(capture)]
    if invalid_side != "question": argv += ["--outputs", str(outputs_path)]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(ValueError): main()
    assert capture.read_bytes() == b"preserve this capture" if exists else not capture.exists()


def test_valid_cli_saves_only_after_metrics_pass(valid_evaluation, tmp_path, monkeypatch, capsys):
    import sys
    from app.analysis.evaluate_context import main
    cases, outputs = valid_evaluation
    fixture, supplied, capture = [tmp_path / name for name in ["fixture.json", "outputs.json", "capture.json"]]
    fixture.write_text(json.dumps({"fixture_version": "test", "cases": cases}))
    supplied.write_text(json.dumps(outputs))
    monkeypatch.setattr(sys, "argv", ["evaluate_context", "--fixture", str(fixture), "--outputs", str(supplied), "--save-outputs", str(capture)])
    main()
    assert json.loads(capture.read_text()) == outputs
    assert json.loads(capsys.readouterr().out)["metrics"]["domain_accuracy"] == 1


def test_length_contrasts_have_explicit_human_rubric_rationale():
    cases = {case["id"]: case for case in json.loads(DEFAULT_FIXTURE.read_text())["cases"]}
    assert len(cases) == 10
    long, short = cases["long_simple"], cases["short_difficult"]
    assert len(long["question"].split()) > 40 and len(short["question"].split()) < 10
    assert long["expected"]["difficulty"] == "easy" and short["expected"]["difficulty"] == "hard"
    for case, total in [(long, 0), (short, 5)]:
        rubric = case["difficulty_rationale"]
        assert sum(rubric[key] for key in ("reasoning_depth", "evidence_burden", "constraint_interactions")) == total
        assert rubric["explanation"]
