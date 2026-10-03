from app.verifiers.rule_verifier import RuleVerifier


# ============================================================
# Numerical verification
# ============================================================

def test_basic_numeric_equality():
    verifier = RuleVerifier()

    result = verifier.verify(
        "What is 10 + 20?",
        "30",
    )

    assert result.passed is True
    assert result.metadata["rule"] == "arithmetic_addition"


def test_wrong_numeric_answer():
    verifier = RuleVerifier()

    result = verifier.verify(
        "What is 10 + 20?",
        "25",
    )

    assert result.passed is False


def test_numeric_comparison_true():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Is 10 greater than 5?",
        "Yes",
    )

    assert result.passed is True


def test_numeric_comparison_false():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Is 5 greater than 10?",
        "Yes",
    )

    assert result.passed is False


def test_numeric_equality_true():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Is 10 equal to 10?",
        "Yes",
    )

    assert result.passed is True


def test_numeric_equality_false():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Is 10 equal to 20?",
        "Yes",
    )

    assert result.passed is False


# ============================================================
# Range verification
# ============================================================

def test_valid_probability():
    verifier = RuleVerifier()

    result = verifier.verify(
        "What is the probability of an event?",
        "0.7",
    )

    assert result.passed is True
    assert result.metadata["rule"] == "probability_range"


def test_invalid_probability():
    verifier = RuleVerifier()

    result = verifier.verify(
        "What is the probability of an event?",
        "1.4",
    )

    assert result.passed is False


def test_valid_percentage():
    verifier = RuleVerifier()

    result = verifier.verify(
        "What is the percentage?",
        "75",
    )

    assert result.passed is True
    assert result.metadata["rule"] == "percentage_range"


def test_invalid_percentage():
    verifier = RuleVerifier()

    result = verifier.verify(
        "What is the percentage?",
        "120",
    )

    assert result.passed is False


# ============================================================
# Regex verification
# ============================================================

def test_valid_email():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Provide an email address.",
        "student@example.com",
    )

    assert result.passed is True


def test_invalid_email():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Provide an email address.",
        "student@example",
    )

    assert result.passed is False


def test_valid_url():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Provide a URL.",
        "https://example.com",
    )

    assert result.passed is True


def test_invalid_url():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Provide a URL.",
        "example.com",
    )

    assert result.passed is False


def test_valid_date():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Provide a date.",
        "2026-09-28",
    )

    assert result.passed is True


def test_invalid_date():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Provide a date.",
        "28-09-2026",
    )

    assert result.passed is False


def test_valid_id():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Provide an ID.",
        "USER-123",
    )

    assert result.passed is True


def test_invalid_id():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Provide an ID.",
        "USER 123",
    )

    assert result.passed is False


# ============================================================
# Structured JSON verification
# ============================================================

def test_valid_json():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Return the answer as JSON.",
        '{"name": "Alice", "age": 20}',
    )

    assert result.passed is True
    assert result.metadata["rule"] == "json_structure"


def test_json_missing_field():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Return the answer as JSON.",
        '{"name": "Alice"}',
    )

    assert result.passed is False


def test_json_wrong_type():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Return the answer as JSON.",
        '{"name": "Alice", "age": "twenty"}',
    )

    assert result.passed is False


def test_json_invalid_age():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Return the answer as JSON.",
        '{"name": "Alice", "age": 150}',
    )

    assert result.passed is False


# ============================================================
# Logical verification
# ============================================================

def test_adult_status_true():
    verifier = RuleVerifier()

    result = verifier.verify(
        "If age is 20, is the person an adult?",
        "Yes",
    )

    assert result.passed is True


def test_adult_status_false():
    verifier = RuleVerifier()

    result = verifier.verify(
        "If age is 15, is the person an adult?",
        "Yes",
    )

    assert result.passed is False


def test_adult_status_correct_no():
    verifier = RuleVerifier()

    result = verifier.verify(
        "If age is 15, is the person an adult?",
        "No",
    )

    assert result.passed is True


# ============================================================
# Unsupported rule
# ============================================================

def test_unsupported_question():
    verifier = RuleVerifier()

    result = verifier.verify(
        "Who is the president of France?",
        "Someone",
    )

    assert result.passed is False
    assert result.metadata["rule"] == "unsupported"
    assert result.metadata["decision"] == "UNSURE"
    assert result.metadata["rule_kind"] is None


# ============================================================
# Numeric policy (issue 11)
# ============================================================

def test_decimal_addition_is_exact():
    result = RuleVerifier().verify("What is 0.1 + 0.2?", "0.3")
    assert result.passed is True
    assert result.metadata["expected"] == 0.3
    assert result.metadata["expected_exact"] == "0.3"
    assert result.metadata["comparison_policy"] == "exact Decimal equality"


def test_large_integer_addition_is_exact():
    result = RuleVerifier().verify(
        "What is 100000000000000000000 + 1?",
        "100000000000000000001",
    )
    assert result.passed is True
    assert result.metadata["expected"] == 10**20 + 1


def test_integral_decimal_answer_matches_integer_result():
    result = RuleVerifier().verify("What is 25 + 17?", "42.0")
    assert result.passed is True
    assert result.metadata["expected"] == 42
    assert result.metadata["actual"] == 42


def test_expected_and_actual_stay_numeric():
    result = RuleVerifier().verify("What is 2+2?", "5")
    assert result.metadata["expected"] == 4
    assert result.metadata["actual"] == 5
    assert isinstance(result.metadata["expected"], int)


def test_division_is_compared_at_the_answers_precision():
    verifier = RuleVerifier()
    assert verifier.verify("What is 1 / 3?", "0.33").passed is True
    assert verifier.verify("What is 1 / 3?", "0.34").passed is False
    assert verifier.verify("What is 10 / 4?", "2.5").passed is True
    assert verifier.verify("What is 1 / 0?", "0").passed is False


# ============================================================
# Pattern coverage (issue 9)
# ============================================================

def test_other_operators_and_paraphrases():
    verifier = RuleVerifier()
    cases = [
        ("What is 25 - 17?", "8", "arithmetic_subtraction"),
        ("Calculate 6 * 7.", "42", "arithmetic_multiplication"),
        ("Compute 6 x 7", "42", "arithmetic_multiplication"),
        ("25 + 17 = ?", "42", "arithmetic_addition"),
        ("What is the sum of 3 and 4?", "7", "arithmetic_addition"),
        ("What is the product of 3 and 4?", "12", "arithmetic_multiplication"),
        ("Is 5 less than 10?", "yes", "less_than"),
        ("Is 10 larger than 5?", "true", "greater_than"),
    ]
    for question, answer, rule in cases:
        result = verifier.verify(question, answer)
        assert result.passed is True, question
        assert result.metadata["rule"] == rule, question
        assert result.metadata["rule_kind"] == "factual"


def test_unlisted_phrasing_is_unsupported_not_rejected():
    result = RuleVerifier().verify("Add twenty-five and seventeen.", "42")
    assert result.metadata["rule"] == "unsupported"
    assert result.metadata["decision"] == "UNSURE"


# ============================================================
# Structural vs factual (issue 10)
# ============================================================

def test_structural_pass_is_validity_only():
    result = RuleVerifier().verify("What is the percentage?", "70")
    assert result.passed is True
    assert result.metadata["rule"] == "percentage_range"
    assert result.metadata["rule_kind"] == "structural"
    assert result.metadata["decision"] == "UNSURE"
    assert "does not establish" in result.reasoning


def test_structural_fail_is_a_rejection():
    result = RuleVerifier().verify("What is the probability of an event?", "1.4")
    assert result.passed is False
    assert result.metadata["rule_kind"] == "structural"
    assert result.metadata["decision"] == "REJECT"


def test_format_and_json_passes_are_structural():
    verifier = RuleVerifier()
    for question, answer in [
        ("Provide an email address.", "student@example.com"),
        ("Provide a URL.", "https://example.com"),
        ("Return the answer as JSON.", '{"name": "Alice", "age": 20}'),
    ]:
        result = verifier.verify(question, answer)
        assert result.passed is True
        assert result.metadata["rule_kind"] == "structural"
        assert result.metadata["decision"] == "UNSURE"


def test_factual_pass_and_fail_decisions():
    verifier = RuleVerifier()
    assert verifier.verify("What is 2+2?", "4").metadata["decision"] == "SUPPORT"
    assert verifier.verify("What is 2+2?", "5").metadata["decision"] == "REJECT"
    assert verifier.verify("If age is 20, is the person an adult?", "Yes").metadata["decision"] == "SUPPORT"


def test_validity_question_makes_validity_the_fact():
    verifier = RuleVerifier()

    valid = verifier.verify("Is user@example.com a valid email?", "Yes")
    assert valid.passed is True
    assert valid.metadata["rule"] == "format_validity"
    assert valid.metadata["rule_kind"] == "factual"
    assert valid.metadata["decision"] == "SUPPORT"

    wrong = verifier.verify("Is user@example a valid email?", "Yes")
    assert wrong.passed is False
    assert wrong.metadata["decision"] == "REJECT"

    probability = verifier.verify("Is 1.4 a valid probability?", "No")
    assert probability.passed is True
    assert probability.metadata["expected"] is False


def test_score_meaning_and_decision_are_always_present():
    verifier = RuleVerifier()
    for question, answer in [
        ("What is 2+2?", "4"),
        ("What is the percentage?", "70"),
        ("Who is the president of France?", "Someone"),
    ]:
        result = verifier.verify(question, answer)
        assert result.metadata["decision"] in {"SUPPORT", "REJECT", "UNSURE"}
        assert "Not a probability" in result.metadata["score_meaning"]