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