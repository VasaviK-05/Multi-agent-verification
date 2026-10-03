"""Deterministic rule-based verifier.

No model is involved. A question is matched against a small set of
regular-expression patterns; the first match decides which rule runs.
Coverage is narrow by design and listed in ``SUPPORTED_RULES``. A
question that matches no pattern is reported as ``rule="unsupported"``,
which the decision layer reads as an abstention, not a rejection. An
equivalent question phrased outside the listed patterns will be
unsupported; the verifier does not attempt general arithmetic or factual
coverage.

Two kinds of rule (issue 10)
    factual     The rule computes the expected answer itself (arithmetic,
                comparisons, the adult-status rule, "is X a valid <format>?").
                Pass means the answer is correct; fail means it is wrong.
    structural  The rule checks only that the answer is well-formed or in
                range (probability/percentage bounds, email/URL/date/ID
                format, JSON schema). Fail means the answer cannot be
                right. Pass means nothing about correctness: 70 is a valid
                percentage even when the right value is 40.

    ``metadata["rule_kind"]`` names the kind. ``metadata["decision"]``:
        factual pass      -> SUPPORT
        factual fail      -> REJECT
        structural fail   -> REJECT
        structural pass   -> UNSURE   (validity only)
        unsupported       -> UNSURE
    ``passed`` and ``metadata["rule"]`` keep their historical meaning
    (``passed`` = the check succeeded) because the decision layer reads
    them; it currently counts a structural pass as a pass vote and should
    consume ``decision`` instead.

Numeric policy (issue 11)
    Operands and answers are parsed with ``decimal.Decimal`` from their
    text, so 0.1 + 0.2 equals 0.3 and large integers are exact. ``+ - *``
    use exact equality. ``/`` is compared after rounding the exact quotient
    to the number of decimal places in the answer (for 1/3, answers 0.3
    and 0.33 pass; 0.34 and 0.3333334 do not). The policy is echoed in
    ``metadata["comparison_policy"]``.

``score`` is the deterministic outcome bit (1 pass, 0 fail). It is not a
probability.
"""

from __future__ import annotations

import json
import re
import time
from decimal import ROUND_HALF_UP, Decimal, DivisionByZero, InvalidOperation, localcontext
from typing import Optional

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import (
    DECISION_REJECT,
    DECISION_SUPPORT,
    DECISION_UNSURE,
    BaseVerifier,
)

FACTUAL = "factual"
STRUCTURAL = "structural"

# rule name -> (kind, example question)
SUPPORTED_RULES: dict[str, tuple[str, str]] = {
    "arithmetic_addition": (FACTUAL, "What is 25 + 17?"),
    "arithmetic_subtraction": (FACTUAL, "What is 25 - 17?"),
    "arithmetic_multiplication": (FACTUAL, "What is 6 * 7?"),
    "arithmetic_division": (FACTUAL, "What is 10 / 4?"),
    "greater_than": (FACTUAL, "Is 10 greater than 5?"),
    "less_than": (FACTUAL, "Is 5 less than 10?"),
    "equality": (FACTUAL, "Is 10 equal to 10?"),
    "adult_status": (FACTUAL, "If age is 20, is the person an adult?"),
    "format_validity": (FACTUAL, "Is user@example.com a valid email?"),
    "probability_range": (STRUCTURAL, "What is the probability of an event?"),
    "percentage_range": (STRUCTURAL, "What is the percentage?"),
    "email_regex": (STRUCTURAL, "Provide an email address."),
    "url_regex": (STRUCTURAL, "Provide a URL."),
    "date_regex": (STRUCTURAL, "Provide a date."),
    "id_regex": (STRUCTURAL, "Provide an ID."),
    "json_structure": (STRUCTURAL, "Return the answer as JSON."),
}

_NUMBER = r"-?\d+(?:\.\d+)?"
_OPERATOR = r"(\+|-|\*|x|×|/|÷)"
_ARITHMETIC_PREFIX = r"(?:what is|what's|calculate|compute|evaluate)\s+"

ARITHMETIC_PATTERNS = (
    # What is 25 + 17?   Calculate 6 * 7.   Compute 10 / 4
    re.compile(rf"{_ARITHMETIC_PREFIX}({_NUMBER})\s*{_OPERATOR}\s*({_NUMBER})\s*[?.]?", re.IGNORECASE),
    # 25 + 17 = ?   25 + 17 =
    re.compile(rf"({_NUMBER})\s*{_OPERATOR}\s*({_NUMBER})\s*=\s*\??", re.IGNORECASE),
)
WORD_ARITHMETIC_PATTERNS = (
    ("+", re.compile(rf"{_ARITHMETIC_PREFIX}the sum of ({_NUMBER}) and ({_NUMBER})\s*[?.]?", re.IGNORECASE)),
    ("-", re.compile(rf"{_ARITHMETIC_PREFIX}the difference between ({_NUMBER}) and ({_NUMBER})\s*[?.]?", re.IGNORECASE)),
    ("*", re.compile(rf"{_ARITHMETIC_PREFIX}the product of ({_NUMBER}) and ({_NUMBER})\s*[?.]?", re.IGNORECASE)),
)
OPERATOR_RULES = {
    "+": "arithmetic_addition",
    "-": "arithmetic_subtraction",
    "*": "arithmetic_multiplication",
    "x": "arithmetic_multiplication",
    "×": "arithmetic_multiplication",
    "/": "arithmetic_division",
    "÷": "arithmetic_division",
}

COMPARISON_PATTERNS = (
    ("greater_than", re.compile(rf"is\s+({_NUMBER})\s+(?:greater|larger|bigger|more)\s+than\s+({_NUMBER})\s*\??", re.IGNORECASE)),
    ("less_than", re.compile(rf"is\s+({_NUMBER})\s+(?:less|smaller)\s+than\s+({_NUMBER})\s*\??", re.IGNORECASE)),
    ("equality", re.compile(rf"is\s+({_NUMBER})\s+equal\s+to\s+({_NUMBER})\s*\??", re.IGNORECASE)),
)

ADULT_PATTERN = re.compile(r"if\s+age\s+is\s+(\d+),?\s+is\s+the\s+person\s+an\s+adult\??", re.IGNORECASE)

FORMAT_PATTERNS: dict[str, str] = {
    "email": r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
    "url": r"^https?://[^\s]+$",
    "date": r"^\d{4}-\d{2}-\d{2}$",
    "id": r"^[A-Za-z0-9_-]+$",
}
RANGE_BOUNDS: dict[str, tuple[int, int]] = {
    "probability": (0, 1),
    "percentage": (0, 100),
}
FORMAT_VALIDITY_PATTERN = re.compile(
    r"is\s+(?:the\s+)?[\"']?(?P<value>\S+?)[\"']?\s+a\s+valid\s+"
    r"(?P<format>email|e-mail|url|date|id|probability|percentage)(?:\s+address)?\s*\??",
    re.IGNORECASE,
)

COMPARISON_POLICY = {
    "arithmetic_addition": "exact Decimal equality",
    "arithmetic_subtraction": "exact Decimal equality",
    "arithmetic_multiplication": "exact Decimal equality",
    "arithmetic_division": "exact quotient rounded half-up to the answer's decimal places",
}


def _parse_decimal(text: str) -> Optional[Decimal]:
    try:
        value = Decimal(text.strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        return None
    if not value.is_finite():
        return None
    return value


def _decimal_places(value: Decimal) -> int:
    exponent = value.as_tuple().exponent
    return -exponent if isinstance(exponent, int) and exponent < 0 else 0


def _jsonable(value: Decimal) -> int | float:
    """int when integral, else float, for metadata consumers and tests."""
    if value == value.to_integral_value():
        return int(value)
    return float(value)


class RuleVerifier(BaseVerifier):
    """Validates answers using deterministic rules."""

    SCORE_MEANING = "Deterministic rule outcome bit: 1 when the check passed, 0 when it failed. Not a probability."

    @property
    def name(self) -> str:
        return "rule"

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        self._start = time.perf_counter()
        question = question.strip()
        answer = answer.strip()
        question_lower = question.lower()

        for check in (
            self._arithmetic,
            self._comparison,
            self._format_validity,
            self._adult_status,
            self._probability_range,
            self._percentage_range,
            self._format_regex,
            self._json_structure,
        ):
            result = check(question, question_lower, answer)
            if result is not None:
                return result

        return self._emit(
            passed=False,
            reasoning="No supported deterministic rule matched the question.",
            rule="unsupported",
            kind=None,
        )

    # ------------------------------------------------------------------
    # Factual rules
    # ------------------------------------------------------------------

    def _arithmetic(self, question: str, question_lower: str, answer: str) -> Optional[VerificationResult]:
        operands: tuple[str, str, str] | None = None
        for pattern in ARITHMETIC_PATTERNS:
            match = pattern.fullmatch(question)
            if match:
                operands = (match.group(1), match.group(2), match.group(3))
                break
        if operands is None:
            for operator, pattern in WORD_ARITHMETIC_PATTERNS:
                match = pattern.fullmatch(question)
                if match:
                    operands = (match.group(1), operator, match.group(2))
                    break
        if operands is None:
            return None

        first_text, operator, second_text = operands
        operator = operator.lower()
        rule = OPERATOR_RULES[operator]
        first, second = _parse_decimal(first_text), _parse_decimal(second_text)
        if first is None or second is None:
            return None

        actual = _parse_decimal(answer)
        if actual is None:
            return self._emit(False, "Answer is not a valid number.", rule, FACTUAL, provided=answer)

        with localcontext() as ctx:
            ctx.prec = 50
            if rule == "arithmetic_addition":
                expected = first + second
            elif rule == "arithmetic_subtraction":
                expected = first - second
            elif rule == "arithmetic_multiplication":
                expected = first * second
            else:
                try:
                    expected = first / second
                except (DivisionByZero, ZeroDivisionError, InvalidOperation):
                    return self._emit(False, "Division by zero has no numeric answer.", rule, FACTUAL, provided=answer)

            if rule == "arithmetic_division":
                places = _decimal_places(actual)
                quantum = Decimal(1).scaleb(-places)
                compared = expected.quantize(quantum, rounding=ROUND_HALF_UP)
            else:
                compared = expected
            passed = compared == actual

        return self._emit(
            passed=passed,
            reasoning=f"Expected {compared.normalize():f}; received {actual.normalize():f}.",
            rule=rule,
            kind=FACTUAL,
            expected=_jsonable(compared),
            actual=_jsonable(actual),
            expected_exact=f"{expected.normalize():f}",
            actual_exact=f"{actual.normalize():f}",
            comparison_policy=COMPARISON_POLICY[rule],
        )

    def _comparison(self, question: str, question_lower: str, answer: str) -> Optional[VerificationResult]:
        for rule, pattern in COMPARISON_PATTERNS:
            match = pattern.fullmatch(question)
            if not match:
                continue
            first, second = _parse_decimal(match.group(1)), _parse_decimal(match.group(2))
            if first is None or second is None:
                return None
            if rule == "greater_than":
                expected, symbol = first > second, ">"
            elif rule == "less_than":
                expected, symbol = first < second, "<"
            else:
                expected, symbol = first == second, "=="
            actual = self._parse_boolean_answer(answer)
            if actual is None:
                return self._emit(False, "Answer must be Yes/No or True/False.", rule, FACTUAL, expected=expected, provided=answer)
            return self._emit(
                passed=actual == expected,
                reasoning=f"Rule evaluation: {first.normalize():f} {symbol} {second.normalize():f} is {expected}. Answer was {answer}.",
                rule=rule,
                kind=FACTUAL,
                expected=expected,
                actual=actual,
            )
        return None

    def _format_validity(self, question: str, question_lower: str, answer: str) -> Optional[VerificationResult]:
        """'Is X a valid email?' asks about validity, so validity is the fact."""
        match = FORMAT_VALIDITY_PATTERN.fullmatch(question)
        if not match:
            return None
        fmt = match.group("format").lower().replace("e-mail", "email")
        value = match.group("value")
        if fmt in RANGE_BOUNDS:
            low, high = RANGE_BOUNDS[fmt]
            number = _parse_decimal(value.rstrip("%"))
            expected = number is not None and Decimal(low) <= number <= Decimal(high)
        else:
            expected = bool(re.fullmatch(FORMAT_PATTERNS[fmt], value))
        actual = self._parse_boolean_answer(answer)
        if actual is None:
            return self._emit(False, "Answer must be Yes/No or True/False.", "format_validity", FACTUAL, expected=expected, provided=answer)
        return self._emit(
            passed=actual == expected,
            reasoning=f"'{value}' {'matches' if expected else 'does not match'} the {fmt} format, so the correct answer is {expected}. Answer was {answer}.",
            rule="format_validity",
            kind=FACTUAL,
            format=fmt,
            value=value,
            expected=expected,
            actual=actual,
        )

    def _adult_status(self, question: str, question_lower: str, answer: str) -> Optional[VerificationResult]:
        match = ADULT_PATTERN.fullmatch(question)
        if not match:
            return None
        age = int(match.group(1))
        expected = age >= 18
        actual = self._parse_boolean_answer(answer)
        if actual is None:
            return self._emit(False, "Answer must be Yes/No or True/False.", "adult_status", FACTUAL, expected=expected)
        return self._emit(
            passed=actual == expected,
            reasoning=f"Age {age} gives adult status {expected}. Answer was {answer}.",
            rule="adult_status",
            kind=FACTUAL,
            age=age,
            expected=expected,
            actual=actual,
        )

    # ------------------------------------------------------------------
    # Structural rules
    # ------------------------------------------------------------------

    def _probability_range(self, question: str, question_lower: str, answer: str) -> Optional[VerificationResult]:
        if "probability" not in question_lower:
            return None
        value = _parse_decimal(answer)
        if value is None:
            return self._emit(False, "Probability must be numeric.", "probability_range", STRUCTURAL, provided=answer)
        passed = Decimal(0) <= value <= Decimal(1)
        return self._emit(
            passed=passed,
            reasoning=self._range_reasoning("Probability", value, 0, 1, passed),
            rule="probability_range",
            kind=STRUCTURAL,
            minimum=0,
            maximum=1,
            actual=_jsonable(value),
        )

    def _percentage_range(self, question: str, question_lower: str, answer: str) -> Optional[VerificationResult]:
        if "percentage" not in question_lower and "percent" not in question_lower:
            return None
        value = _parse_decimal(answer.rstrip("%"))
        if value is None:
            return self._emit(False, "Percentage must be numeric.", "percentage_range", STRUCTURAL, provided=answer)
        passed = Decimal(0) <= value <= Decimal(100)
        return self._emit(
            passed=passed,
            reasoning=self._range_reasoning("Percentage", value, 0, 100, passed),
            rule="percentage_range",
            kind=STRUCTURAL,
            minimum=0,
            maximum=100,
            actual=_jsonable(value),
        )

    def _format_regex(self, question: str, question_lower: str, answer: str) -> Optional[VerificationResult]:
        if "email" in question_lower or "e-mail" in question_lower:
            fmt, label = "email", "email format"
        elif "url" in question_lower:
            fmt, label = "url", "URL format"
        elif "date" in question_lower:
            fmt, label = "date", "YYYY-MM-DD format"
        elif re.search(r"\bid\b", question_lower):
            fmt, label = "id", "ID format"
        else:
            return None
        pattern = FORMAT_PATTERNS[fmt]
        passed = bool(re.fullmatch(pattern, answer))
        return self._emit(
            passed=passed,
            reasoning=(
                f"Answer matches the expected {label}. Format validity only; this does not establish that the value is correct."
                if passed
                else f"Answer does not match the expected {label}."
            ),
            rule=f"{fmt}_regex",
            kind=STRUCTURAL,
            pattern=pattern,
        )

    def _json_structure(self, question: str, question_lower: str, answer: str) -> Optional[VerificationResult]:
        if "json" not in question_lower:
            return None
        rule = "json_structure"
        try:
            data = json.loads(answer)
        except json.JSONDecodeError:
            return self._emit(False, "Answer is not valid JSON.", rule, STRUCTURAL)
        if not isinstance(data, dict):
            return self._emit(False, "JSON answer must be an object.", rule, STRUCTURAL)

        required_fields = {"name", "age"}
        missing = sorted(required_fields - set(data))
        if missing:
            return self._emit(False, f"Missing required fields: {missing}.", rule, STRUCTURAL, missing_fields=missing)
        if not isinstance(data["name"], str):
            return self._emit(False, "The 'name' field must be a string.", rule, STRUCTURAL)
        if not isinstance(data["age"], int) or isinstance(data["age"], bool):
            return self._emit(False, "The 'age' field must be an integer.", rule, STRUCTURAL)
        if not 0 <= data["age"] <= 120:
            return self._emit(False, "The 'age' field must be between 0 and 120.", rule, STRUCTURAL, age=data["age"])
        return self._emit(
            passed=True,
            reasoning="JSON structure and field constraints are valid. Schema validity only; this does not establish that the values are correct.",
            rule=rule,
            kind=STRUCTURAL,
            required_fields=sorted(required_fields),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _range_reasoning(label: str, value: Decimal, low: int, high: int, passed: bool) -> str:
        shown = f"{value.normalize():f}"
        if passed:
            return (
                f"{label} value {shown} lies within {low} and {high}. "
                "Range validity only; this does not establish that the value is correct."
            )
        return f"{label} value {shown} must be between {low} and {high}."

    @staticmethod
    def _parse_boolean_answer(answer: str) -> Optional[bool]:
        """Convert Yes/No or True/False to a boolean."""
        normalized = answer.lower().strip(" .!?")
        if normalized in {"yes", "true"}:
            return True
        if normalized in {"no", "false"}:
            return False
        return None

    def _emit(
        self,
        passed: bool,
        reasoning: str,
        rule: str,
        kind: str | None,
        **metadata,
    ) -> VerificationResult:
        if rule == "unsupported":
            decision = DECISION_UNSURE
        elif not passed:
            decision = DECISION_REJECT
        elif kind == FACTUAL:
            decision = DECISION_SUPPORT
        else:
            decision = DECISION_UNSURE  # structural pass: validity only
        latency_ms = (time.perf_counter() - getattr(self, "_start", time.perf_counter())) * 1000
        return VerificationResult(
            verifier_name=self.name,
            score=1.0 if passed else 0.0,
            passed=passed,
            reasoning=reasoning,
            metadata={
                "rule": rule,
                "rule_kind": kind,
                "decision": decision,
                "score_meaning": self.SCORE_MEANING,
                "latency_ms": round(latency_ms, 2),
                **metadata,
            },
        )

    # Backwards-compatible helpers used by older callers/tests.
    def _result(self, passed: bool, reasoning: str, rule: str, **metadata) -> VerificationResult:
        kind = SUPPORTED_RULES.get(rule, (None, ""))[0]
        return self._emit(passed, reasoning, rule, kind, **metadata)

    def _fail(self, reasoning: str, rule: str, **metadata) -> VerificationResult:
        kind = SUPPORTED_RULES.get(rule, (None, ""))[0]
        return self._emit(False, reasoning, rule, kind, **metadata)
