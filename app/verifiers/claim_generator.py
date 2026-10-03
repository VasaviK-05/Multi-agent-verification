"""Generate declarative claims from questions and answers.

NLI models compare a premise with a declarative hypothesis, so a short
answer such as "Paris" is rewritten into a sentence using a question
template. Coverage is deliberately narrow and listed in
``SUPPORTED_PATTERNS``; anything else uses a generic fallback that keeps
the question and answer verbatim.

Multi-sentence answers hold several claims. ``generate_claims`` returns one
claim per sentence so each can be retrieved and checked on its own; a
passage that supports one sentence says nothing about the others.
"""

from __future__ import annotations

import re

# (template name, compiled pattern) in match order.
SUPPORTED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("capital", re.compile(r"what is the capital of (.+?)\??$", re.IGNORECASE)),
    ("who", re.compile(r"who (.+?)\??$", re.IGNORECASE)),
    ("definition", re.compile(r"what is (.+?)\??$", re.IGNORECASE)),
)

FALLBACK_TEMPLATE = "fallback"
SENTENCE_TEMPLATE = "sentence"

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


class ClaimGenerator:
    """Converts common question-answer patterns into factual claims."""

    def generate_with_template(self, question: str, answer: str) -> tuple[str, str]:
        """Return (claim, template name) for a single-claim answer."""
        question = question.strip()
        answer = answer.strip().rstrip(".")

        for template, pattern in SUPPORTED_PATTERNS:
            match = pattern.match(question)
            if not match:
                continue
            subject = match.group(1).strip()
            if template == "capital":
                return f"The capital of {subject} is {answer}.", template
            if template == "who":
                if self._answer_names_subject(answer, subject):
                    # "Who was Alan Turing?" / "Alan Turing was a mathematician."
                    return f"{answer}.", template
                return f"{answer} {subject}.", template
            if template == "definition":
                if answer.lower().startswith(subject.lower()):
                    # "What is Python?" / "Python is a programming language."
                    return f"{answer}.", template
                return f"{subject} is {answer}.", template

        return f"{question.rstrip('?')}. Answer: {answer}.", FALLBACK_TEMPLATE

    def generate(self, question: str, answer: str) -> str:
        """Generate a declarative claim from a question and answer."""
        return self.generate_with_template(question, answer)[0]

    def generate_claims(self, question: str, answer: str) -> list[dict]:
        """Return one ``{"claim", "template"}`` per sentence of the answer.

        A single-sentence answer is passed through the question templates.
        A multi-sentence answer is split; each sentence is already
        declarative and is used verbatim with template ``sentence``.
        """
        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(answer.strip()) if s.strip()]
        if len(sentences) <= 1:
            claim, template = self.generate_with_template(question, answer)
            return [{"claim": claim, "template": template}]
        return [{"claim": sentence, "template": SENTENCE_TEMPLATE} for sentence in sentences]

    @staticmethod
    def _answer_names_subject(answer: str, subject: str) -> bool:
        """True when the answer already restates the questioned entity.

        ``subject`` for a "who" question is e.g. "was Alan Turing"; the
        entity is the text after the leading verb.
        """
        words = subject.split()
        entity = " ".join(words[1:]) if len(words) > 1 else subject
        return bool(entity) and answer.lower().startswith(entity.lower())
