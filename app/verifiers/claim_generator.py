"""Generate declarative claims from questions and answers.

NLI models compare a premise with a declarative hypothesis, so a short
answer such as "Paris" is rewritten into a sentence using a question
template. Coverage is deliberately narrow and listed in
``SUPPORTED_PATTERNS``; anything else becomes one statement that names the
question and the answer, without an ``Answer:`` label.

An answer that is already a clause ("William Shakespeare wrote Romeo and
Juliet.") is used as written (template ``statement``); wrapping it in a
question template would repeat the question inside it. A clause joined
by "and" plus a verb ("... on 14 November 2007 and had a magnitude of
7.7.") holds two facts and is split, the second clause taking the
first's subject.

A trailing instruction such as "Answer only in YYYY-MM-DD format", an
inline one ("... in YYYY-MM-DD format") and an imperative opening
("Provide the date of ...") are removed or rephrased before templates and
anchors are built. Those words tell the
generator how to write, and the evidence passage is not expected to
contain them. An ISO date in the answer ("2010-05-12") is written the way
encyclopedic text writes it ("12 May 2010"), so NLI compares like with
like.

Multi-sentence answers hold several claims. ``generate_claims`` returns one
claim per sentence so each can be retrieved and checked on its own; a
passage that supports one sentence says nothing about the others. A later
sentence that opens with a pronoun ("It had a magnitude of 9.1.") is
ambiguous on its own: NLI can match "It" to any magnitude-9.1 event in the
passage. Its ``hypothesis`` therefore names the first sentence's subject
("The 2007 Tocopilla earthquake had a magnitude of 9.1."); ``claim`` keeps
the sentence as written for reporting.
"""

from __future__ import annotations

import calendar
import re

# (template name, compiled pattern) in match order.
SUPPORTED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("capital", re.compile(r"what is the capital of (.+?)\??$", re.IGNORECASE)),
    ("who", re.compile(r"who (.+?)\??$", re.IGNORECASE)),
    ("process", re.compile(r"at what (.+?) (?:does|do|did) (.+?)\??$", re.IGNORECASE)),
    ("attribute", re.compile(r"what (was|were|are) (?:the |a |an )?(.+?)\??$", re.IGNORECASE)),
    ("attribute", re.compile(r"what (is) the (.+?)\??$", re.IGNORECASE)),
    ("definition", re.compile(r"what is (.+?)\??$", re.IGNORECASE)),
)

FALLBACK_TEMPLATE = "fallback"
SENTENCE_TEMPLATE = "sentence"
STATEMENT_TEMPLATE = "statement"

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
# A format instruction follows the question. It is not part of the fact.
_INSTRUCTION_TAIL = re.compile(
    r"(?:[.?!]\s*)(?:please\s+)?(?:answer|reply|respond|return|write|output|give|provide)\b.*$",
    re.IGNORECASE | re.DOTALL,
)
# An inline format instruction: "in YYYY-MM-DD format", "(YYYY-MM-DD)", "in ISO format".
_FORMAT_MASK = r"[ymd]{1,4}(?:[-/.][ymd]{1,4})+"
_INLINE_FORMAT = re.compile(
    rf"\s*,?\s*\(?\b(?:in|using|as)\s+(?:the\s+|an?\s+)?(?:{_FORMAT_MASK}\s+|[\w-]+\s+)?format\b"
    rf"(?:\s*[:\-]?\s*{_FORMAT_MASK})?\)?|\s*\(\s*{_FORMAT_MASK}\s*\)",
    re.IGNORECASE,
)
# "Provide the date of X" asks the same as "What is the date of X?".
_IMPERATIVE = re.compile(
    r"^(?:please\s+)?(?:provide|give|state|tell|name|identify|find|return|write|output)"
    r"(?:\s+me)?\s+(the\s+.+?)[.?!]?$",
    re.IGNORECASE | re.DOTALL,
)
_COORDINATION = re.compile(r",?\s+and\s+")


_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

_PRONOUNS = frozenset({"it", "he", "she", "they", "this", "these"})
_POSSESSIVES = frozenset({"its", "his", "her", "their"})
_NOT_SUBJECTS = _PRONOUNS | _POSSESSIVES | {"there", "here"}
# Finite verbs that end a sentence's subject. Regular past forms ("occurred",
# "defeated") are recognised by their "-ed" ending instead.
_FINITE_VERBS = frozenset(
    """
    is was are were has had have will would can could did does do became becomes
    began begins won wins wrote writes lies lay lasted made makes took takes led
    beat lost held built ran came went gave found saw said told kept left met
    paid sent spent stood struck taught brought fought caught sold drew grew
    knew threw flew rose fell hit set shot leads remains contains
    """.split()
)
_ARTICLES = frozenset({"the", "a", "an"})


def _is_finite_verb(word: str, previous: str) -> bool:
    bare = word.strip(",;:").lower()
    if bare in _FINITE_VERBS:
        return True
    return (
        len(bare) > 3
        and bare.endswith("ed")
        and word[:1].islower()
        and previous.lower() not in _ARTICLES
    )


def subject_of(sentence: str) -> str | None:
    """Words before the first finite verb, or None when that is a pronoun or absent."""
    words = sentence.split()
    for index in range(1, len(words)):
        if _is_finite_verb(words[index], words[index - 1]):
            subject = " ".join(words[:index]).strip(",")
            if subject.split()[0].lower() in _NOT_SUBJECTS:
                return None
            return subject
    return None


def resolve_pronoun(sentence: str, subject: str | None) -> str:
    """Replace a leading pronoun or possessive with ``subject``; otherwise return unchanged."""
    if not subject:
        return sentence
    first, _, rest = sentence.partition(" ")
    lowered = first.lower()
    if lowered in _PRONOUNS and rest:
        return f"{subject} {rest}"
    if lowered in _POSSESSIVES and rest:
        return f"{subject}'s {rest}"
    return sentence


def factual_question(question: str) -> str:
    """Question text without answer-format instructions, as a question.

    A trailing instruction ("Answer only in YYYY-MM-DD format.") and an
    inline one ("... in YYYY-MM-DD format") are removed, and an imperative
    request ("Provide the date of X") is asked as "What is the date of X?".
    """
    text = str(question).strip()
    cleaned = _INLINE_FORMAT.sub("", _INSTRUCTION_TAIL.sub("", text)).strip()
    imperative = _IMPERATIVE.match(cleaned)
    if imperative:
        cleaned = f"What is {imperative.group(1).strip()}?"
    return cleaned or text


def is_statement(answer: str) -> bool:
    """True when the answer is already a clause with its own finite verb."""
    words = str(answer).split()
    return len(words) >= 3 and any(
        _is_finite_verb(words[index], words[index - 1]) for index in range(1, len(words))
    )


def split_coordinated(sentence: str, subject: str | None) -> list[str]:
    """Split "S did A and did B." into "S did A." and "S did B.".

    Only an "and" followed by a finite verb starts a new clause, so "Romeo
    and Juliet" or "3 minutes and 35 seconds" stay whole. The new clause
    takes ``subject``; without one the sentence is returned unchanged.
    """
    if not subject:
        return [sentence]
    parts: list[str] = []
    start = 0
    for match in _COORDINATION.finditer(sentence):
        following = sentence[match.end() :].split(" ", 1)[0]
        if _is_finite_verb(following, "and"):
            parts.append(sentence[start : match.start()])
            start = match.end()
    if not parts:
        return [sentence]
    parts.append(sentence[start:])
    clauses = [parts[0].strip().rstrip(".!?") + "."]
    clauses += [f"{subject} {part.strip().rstrip('.!?')}." for part in parts[1:]]
    return clauses


def spell_out_dates(text: str) -> str:
    """Rewrite valid ISO dates (YYYY-MM-DD) as "D Month YYYY"; leave anything else as is."""

    def replace(match: re.Match[str]) -> str:
        year, month, day = (int(group) for group in match.groups())
        if not 1 <= month <= 12 or not 1 <= day <= calendar.monthrange(year, month)[1]:
            return match.group(0)
        return f"{day} {calendar.month_name[month]} {year}"

    return _ISO_DATE.sub(replace, str(text))


class ClaimGenerator:
    """Converts common question-answer patterns into factual claims."""

    def generate_with_template(self, question: str, answer: str) -> tuple[str, str]:
        """Return (claim, template name) for a single-claim answer."""
        question = factual_question(question)
        answer = spell_out_dates(answer.strip()).rstrip(".")
        if is_statement(answer):
            # "William Shakespeare wrote Romeo and Juliet." is already a claim;
            # a template would repeat the question inside it.
            return f"{answer}.", STATEMENT_TEMPLATE

        for template, pattern in SUPPORTED_PATTERNS:
            match = pattern.match(question)
            if not match:
                continue
            if template == "process":
                aspect = match.group(1).strip()
                subject = match.group(2).strip()
                return f"The {aspect} at which {subject} is {answer}.", template
            if template == "attribute":
                verb = match.group(1).lower()
                subject = match.group(2).strip()
                if self._answer_names_subject(answer, subject):
                    return f"{answer}.", template
                return f"The {subject} {verb} {answer}.", template
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

        stated = question.rstrip("?").strip()
        return f'The answer to "{stated}" is {answer}.', FALLBACK_TEMPLATE

    def generate(self, question: str, answer: str) -> str:
        """Generate a declarative claim from a question and answer."""
        return self.generate_with_template(question, answer)[0]

    def generate_claims(self, question: str, answer: str) -> list[dict]:
        """Return one ``{"claim", "template", "hypothesis"}`` per sentence of the answer.

        A single-sentence answer is passed through the question templates.
        A multi-sentence answer is split; each sentence is already
        declarative and is used verbatim with template ``sentence``.
        ``hypothesis`` is the text to retrieve and test with NLI: the claim,
        with a leading pronoun replaced by the first sentence's subject.
        """
        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(answer.strip()) if s.strip()]
        if len(sentences) <= 1:
            claim, template = self.generate_with_template(question, answer)
            clauses = split_coordinated(claim, subject_of(claim)) if template == STATEMENT_TEMPLATE else [claim]
            if len(clauses) == 1:
                return [{"claim": claim, "template": template, "hypothesis": claim}]
            return [{"claim": c, "template": SENTENCE_TEMPLATE, "hypothesis": c} for c in clauses]
        subject = subject_of(sentences[0])
        claims = []
        for position, sentence in enumerate(sentences):
            text = spell_out_dates(sentence)
            resolved = text if position == 0 else resolve_pronoun(text, subject)
            own_subject = subject_of(resolved) or subject
            clauses = split_coordinated(resolved, own_subject)
            if len(clauses) == 1:
                claims.append({"claim": text, "template": SENTENCE_TEMPLATE, "hypothesis": resolved})
                continue
            for clause in clauses:
                claims.append({"claim": clause, "template": SENTENCE_TEMPLATE, "hypothesis": clause})
        return claims

    @staticmethod
    def _answer_names_subject(answer: str, subject: str) -> bool:
        """True when the answer already restates the questioned entity.

        ``subject`` for a "who" question is e.g. "was Alan Turing"; the
        entity is the text after the leading verb.
        """
        words = subject.split()
        entity = " ".join(words[1:]) if len(words) > 1 else subject
        return bool(entity) and answer.lower().startswith(entity.lower())
