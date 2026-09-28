"""Generate factual claims from questions and answers."""

import re


class ClaimGenerator:
    """Converts common question-answer patterns into factual claims."""

    def generate(self, question: str, answer: str) -> str:
        """Generate a declarative claim from a question and answer."""

        question = question.strip()
        answer = answer.strip()

        # Capital questions
        match = re.match(
            r"what is the capital of (.+)\?",
            question,
            re.IGNORECASE,
        )

        if match:
            country = match.group(1).strip()
            return f"The capital of {country} is {answer}."

        # Who questions
        match = re.match(
            r"who (.+)\?",
            question,
            re.IGNORECASE,
        )

        if match:
            subject = match.group(1).strip()
            return f"{answer} {subject}."

        # Definition questions
        match = re.match(
            r"what is (.+)\?",
            question,
            re.IGNORECASE,
        )

        if match:
            subject = match.group(1).strip()
            return f"{subject} is {answer}."

        # Fallback
        return f"{question.rstrip('?')}. Answer: {answer}."
