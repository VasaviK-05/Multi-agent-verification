"""Deterministic rule-based verifier."""

import json
import re
from typing import Optional

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import BaseVerifier


class RuleVerifier(BaseVerifier):
    """Validates answers using deterministic rules."""

    @property
    def name(self) -> str:
        return "rule"

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:

        question = question.strip()
        answer = answer.strip()

        # =========================================================
        # 1. NUMERICAL VERIFICATION
        # =========================================================

        # ---------------------------------------------------------
        # Addition
        # Example:
        # What is 25 + 17? -> 42
        # ---------------------------------------------------------
        match = re.fullmatch(
            r"what is\s+(-?\d+(?:\.\d+)?)\s*\+\s*"
            r"(-?\d+(?:\.\d+)?)\??",
            question,
            re.IGNORECASE,
        )

        if match:
            first = float(match.group(1))
            second = float(match.group(2))
            expected = first + second

            try:
                actual = float(answer)
            except ValueError:
                return self._fail(
                    "Answer is not a valid number.",
                    "arithmetic_addition",
                    expected=expected,
                    provided=answer,
                )

            passed = actual == expected

            return self._result(
                passed=passed,
                reasoning=f"Expected {expected:g}; received {actual:g}.",
                rule="arithmetic_addition",
                expected=expected,
                actual=actual,
            )

        # ---------------------------------------------------------
        # Greater-than comparison
        # Example:
        # Is 10 greater than 5? -> Yes
        # ---------------------------------------------------------
        match = re.fullmatch(
            r"is\s+(-?\d+(?:\.\d+)?)\s+greater\s+than\s+"
            r"(-?\d+(?:\.\d+)?)\??",
            question,
            re.IGNORECASE,
        )

        if match:
            first = float(match.group(1))
            second = float(match.group(2))

            expected = first > second

            actual = self._parse_boolean_answer(answer)

            if actual is None:
                return self._fail(
                    "Answer must be Yes/No or True/False.",
                    "greater_than",
                    expected=expected,
                    provided=answer,
                )

            passed = actual == expected

            return self._result(
                passed=passed,
                reasoning=(
                    f"Rule evaluation: {first:g} > {second:g} "
                    f"is {expected}. Answer was {answer}."
                ),
                rule="greater_than",
                expected=expected,
                actual=actual,
            )

        # ---------------------------------------------------------
        # Equality comparison
        # Example:
        # Is 10 equal to 10? -> Yes
        # ---------------------------------------------------------
        match = re.fullmatch(
            r"is\s+(-?\d+(?:\.\d+)?)\s+equal\s+to\s+"
            r"(-?\d+(?:\.\d+)?)\??",
            question,
            re.IGNORECASE,
        )

        if match:
            first = float(match.group(1))
            second = float(match.group(2))

            expected = first == second

            actual = self._parse_boolean_answer(answer)

            if actual is None:
                return self._fail(
                    "Answer must be Yes/No or True/False.",
                    "equality",
                    expected=expected,
                    provided=answer,
                )

            passed = actual == expected

            return self._result(
                passed=passed,
                reasoning=(
                    f"Rule evaluation: {first:g} == {second:g} "
                    f"is {expected}. Answer was {answer}."
                ),
                rule="equality",
                expected=expected,
                actual=actual,
            )

        # =========================================================
        # 2. RANGE VERIFICATION
        # =========================================================

        # ---------------------------------------------------------
        # Probability: 0 <= value <= 1
        # ---------------------------------------------------------
        if "probability" in question.lower():

            try:
                value = float(answer)
            except ValueError:
                return self._fail(
                    "Probability must be numeric.",
                    "probability_range",
                    provided=answer,
                )

            passed = 0 <= value <= 1

            return self._result(
                passed=passed,
                reasoning=(
                    f"Probability value {value} must be between "
                    f"0 and 1."
                ),
                rule="probability_range",
                minimum=0,
                maximum=1,
                actual=value,
            )

        # ---------------------------------------------------------
        # Percentage: 0 <= value <= 100
        # ---------------------------------------------------------
        if "percentage" in question.lower():

            try:
                value = float(answer)
            except ValueError:
                return self._fail(
                    "Percentage must be numeric.",
                    "percentage_range",
                    provided=answer,
                )

            passed = 0 <= value <= 100

            return self._result(
                passed=passed,
                reasoning=(
                    f"Percentage value {value} must be between "
                    f"0 and 100."
                ),
                rule="percentage_range",
                minimum=0,
                maximum=100,
                actual=value,
            )

        # =========================================================
        # 3. REGEX VERIFICATION
        # =========================================================

        question_lower = question.lower()

        # ---------------------------------------------------------
        # Email
        # ---------------------------------------------------------
        if "email" in question_lower:

            pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            passed = bool(re.fullmatch(pattern, answer))

            return self._result(
                passed=passed,
                reasoning=(
                    "Answer matches the expected email format."
                    if passed
                    else "Answer does not match the expected email format."
                ),
                rule="email_regex",
                pattern=pattern,
            )

        # ---------------------------------------------------------
        # URL
        # ---------------------------------------------------------
        if "url" in question_lower:

            pattern = r"^https?://[^\s]+$"
            passed = bool(re.fullmatch(pattern, answer))

            return self._result(
                passed=passed,
                reasoning=(
                    "Answer matches the expected URL format."
                    if passed
                    else "Answer does not match the expected URL format."
                ),
                rule="url_regex",
                pattern=pattern,
            )

        # ---------------------------------------------------------
        # Date: YYYY-MM-DD
        # ---------------------------------------------------------
        if "date" in question_lower:

            pattern = r"^\d{4}-\d{2}-\d{2}$"
            passed = bool(re.fullmatch(pattern, answer))

            return self._result(
                passed=passed,
                reasoning=(
                    "Answer matches YYYY-MM-DD format."
                    if passed
                    else "Answer does not match YYYY-MM-DD format."
                ),
                rule="date_regex",
                pattern=pattern,
            )

        # ---------------------------------------------------------
        # ID: simple alphanumeric identifier
        # Example: USER-123
        # ---------------------------------------------------------
        if re.search(r"\bid\b", question_lower):

            pattern = r"^[A-Za-z0-9_-]+$"
            passed = bool(re.fullmatch(pattern, answer))

            return self._result(
                passed=passed,
                reasoning=(
                    "Answer matches the expected ID format."
                    if passed
                    else "Answer does not match the expected ID format."
                ),
                rule="id_regex",
                pattern=pattern,
            )

        # =========================================================
        # 4. STRUCTURED JSON VERIFICATION
        # =========================================================

        if "json" in question_lower:

            try:
                data = json.loads(answer)
            except json.JSONDecodeError:
                return self._fail(
                    "Answer is not valid JSON.",
                    "json_structure",
                )

            if not isinstance(data, dict):
                return self._fail(
                    "JSON answer must be an object.",
                    "json_structure",
                )

            required_fields = {"name", "age"}

            missing_fields = required_fields - set(data.keys())

            if missing_fields:
                return self._fail(
                    f"Missing required fields: {sorted(missing_fields)}.",
                    "json_structure",
                    missing_fields=sorted(missing_fields),
                )

            if not isinstance(data["name"], str):
                return self._fail(
                    "The 'name' field must be a string.",
                    "json_structure",
                )

            if not isinstance(data["age"], int):
                return self._fail(
                    "The 'age' field must be an integer.",
                    "json_structure",
                )

            if not 0 <= data["age"] <= 120:
                return self._fail(
                    "The 'age' field must be between 0 and 120.",
                    "json_structure",
                    age=data["age"],
                )

            return self._result(
                passed=True,
                reasoning="JSON structure and field constraints are valid.",
                rule="json_structure",
                required_fields=sorted(required_fields),
            )

        # =========================================================
        # 5. LOGICAL RULES
        # =========================================================

        # ---------------------------------------------------------
        # Adult status
        #
        # Rule:
        # age < 18 -> adult_status must be false
        # age >= 18 -> adult_status must be true
        #
        # Expected question format:
        # "If age is 20, is the person an adult?"
        # ---------------------------------------------------------
        match = re.fullmatch(
            r"if\s+age\s+is\s+(\d+),?\s+is\s+the\s+person\s+an\s+adult\??",
            question,
            re.IGNORECASE,
        )

        if match:
            age = int(match.group(1))
            expected = age >= 18

            actual = self._parse_boolean_answer(answer)

            if actual is None:
                return self._fail(
                    "Answer must be Yes/No or True/False.",
                    "adult_status",
                    expected=expected,
                )

            passed = actual == expected

            return self._result(
                passed=passed,
                reasoning=(
                    f"Age {age} gives adult status {expected}. "
                    f"Answer was {answer}."
                ),
                rule="adult_status",
                age=age,
                expected=expected,
                actual=actual,
            )

        # ---------------------------------------------------------
        # No supported rule
        # ---------------------------------------------------------

        return self._fail(
            "No supported deterministic rule matched the question.",
            "unsupported",
        )

    # =============================================================
    # Helper methods
    # =============================================================

    @staticmethod
    def _parse_boolean_answer(answer: str) -> Optional[bool]:
        """Convert Yes/No or True/False to a boolean."""

        normalized = answer.lower().strip(" .!?")

        if normalized in {"yes", "true"}:
            return True

        if normalized in {"no", "false"}:
            return False

        return None

    def _result(
        self,
        passed: bool,
        reasoning: str,
        rule: str,
        **metadata,
    ) -> VerificationResult:
        """Create a successful or failed verification result."""

        return VerificationResult(
            verifier_name=self.name,
            score=1.0 if passed else 0.0,
            passed=passed,
            reasoning=reasoning,
            metadata={
                "rule": rule,
                **metadata,
            },
        )

    def _fail(
        self,
        reasoning: str,
        rule: str,
        **metadata,
    ) -> VerificationResult:
        """Create a failed verification result."""

        return VerificationResult(
            verifier_name=self.name,
            score=0.0,
            passed=False,
            reasoning=reasoning,
            metadata={
                "rule": rule,
                **metadata,
            },
        )