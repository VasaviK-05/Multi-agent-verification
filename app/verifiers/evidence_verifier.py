"""Evidence-based verifier: FAISS retrieval + Natural Language Inference.

Pipeline, per claim in the answer:

    claim -> retrieve top-k chunks -> relevance gate -> topic gate -> NLI
    on each kept chunk (premise = chunk excerpt, hypothesis = claim) ->
    per-claim decision -> aggregate across claims

Three different scores appear in the output and must not be confused:
    retrieval_score   cosine similarity of the query and a chunk ("is this
                      chunk about the claim?")
    probabilities     NLI class probabilities for one chunk/claim pair
    score             the NLI probability of the label that decided the
                      final result (see ``SCORE_MEANING``)

Relevance gate (issue 6)
    FAISS always returns the nearest chunks. If the best hit is below
    ``min_retrieval_score`` the corpus has nothing on the claim and the
    verifier abstains instead of running NLI on unrelated text. Chunks
    further than ``retrieval_margin`` below the best hit are dropped so a
    distant neighbour (e.g. "Berlin is the capital of Germany" for a claim
    about France) cannot create a false contradiction.

    The default floor of 0.45 comes from a probe on the test corpus: claims
    the corpus covers retrieved their chunk at >= 0.78, while claims it
    does not cover ("capital of Japan", "Alan Turing") had nearest
    neighbours at 0.39-0.41 that the NLI model nonetheless labelled as
    0.999 contradictions. It is UNCALIBRATED for the full corpus and has to
    be re-fitted on labelled data.

Topic gate
    Embedding similarity of a whole chunk is a coarse topic signal: for
    "Who won the 2010 UEFA Europa League Final?" a "2008 SK Brann season"
    chunk that talks about the UEFA Cup and the league can sit within the
    retrieval margin of the right article. NLI then reads a premise about a
    different event as a confident contradiction, and that one chunk
    decides the claim. So before NLI, each kept chunk must be about the
    question's subject. Its anchors are the question's content terms after
    a trailing answer-format instruction is removed (the answer is what is
    being tested, so it is not an anchor; sentence claims from
    multi-sentence answers use their own terms), weighted by corpus IDF
    from ``EvidenceRetriever.term_weights``. A question term that never
    occurs in the corpus is still an anchor: no chunk contains it, so
    sharing only the common words is not enough. Coverage is measured on
    the chunk title and full text, not on the short NLI excerpt:
        every number in the question must appear (a year names the event)
        IDF-weighted anchor coverage >= ``min_topic_coverage``
        coverage >= best coverage among kept chunks - ``topic_margin``
    Chunks that fail are not sent to NLI and are listed in
    ``metadata["discarded_evidence"]`` with their coverage and missing
    terms. Both thresholds are UNCALIBRATED.

    A BM25 match (``lexical_hit``) may reach this gate even when its cosine
    is below ``min_retrieval_score``. The gate, not a lower cosine floor,
    is what keeps an off-topic keyword match away from NLI.

    When the question names a year, a title whose years are disjoint from
    that year is a different event and never reaches NLI. Sharing only
    numbers is not "about the subject". If any retrieved title already
    covers the question's year and event terms, other titles are not
    treated as on-topic merely because a local sentence mentions the event
    in passing. Required question numbers are checked on the title plus
    the selected premise windows, so an incidental year later in a long
    article does not count as covering the asked event.

Retrieval queries
    Template claims retrieve with the factual question alone so the answer
    under test cannot steer the first search. Sentence claims retrieve
    with the question and that claim together, using the claim as written.
    If the first pass has no on-topic chunk, a second public ``retrieve``
    call adds a compact claim-focused query (distinctive claim terms not
    already in the question). Results are merged by source identity,
    keeping the higher cosine. The original claim is what NLI scores.

Premises
    A chunk of up to ``LEGACY_PREMISE_SENTENCES`` sentences is one premise
    (its best-overlapping sentences). A longer chunk is checked through up
    to two windows for each of the ``max_premise_windows`` sentences that
    best match the claim and the question: the sentence with the one
    before it and with the one after it, prefixed with the article title
    so "It" and "The match" resolve. Matching (``match_score``) ignores
    the title's own words, keeps decimals whole ("7.7" is not "7.1") and
    weighs numbers double, so the window chosen for "...was 12 May 2010"
    is the sentence that has a date, not the opening sentence that repeats
    the title. Question terms are added to that score so a sentence about
    the asked event outranks a same-date sentence about a different event.
    A wider window is not used: extra sentences turn a clear entailment
    into a contradiction. An entailment that holds only with the title
    prefix is replaced by the bare window's result when the bare window
    contradicts: the prefix has then attached the title to a different
    referent ("This earthquake occurred near ... the magnitude 9.1
    earthquake of 1877"). Windows are scored by how directly they address
    the asked fact (term overlap, question year, and same-property
    values). NLI probability does not choose the window: a contradiction
    about another date or score cannot override a passage that states the
    requested property. An explicit same-property value match or mismatch
    is recorded as ``value_relation`` and can decide the claim when NLI is
    neutral or misaligned. This is not a calibrated numeric reasoner.
    Every window is kept in ``premise_windows``.

Relevance vs NLI
    Relevance is decided before a row can affect the claim, and never from
    an NLI label or probability. ``select_on_topic`` uses ``anchor_weights``,
    ``topic_coverage``, ``relation_entity_terms``, ``is_about_subject``,
    ``contains_unmodified_entity`` and ``extract_premises``. A chunk is
    relevant when it is about the asked subject, entity, relation or
    property, and (when the question supplies them) the same dates,
    numbers and event. A title that paraphrases the question, or a local
    passage that states the fact, can be relevant; a name-list or a
    different year or condition cannot. Sharing only generic words or
    numbers is not enough. Chunks that fail this gate are not sent to NLI.

Per-claim aggregation (issue 5)
    A chunk is a strong entailment / contradiction when that class is the
    argmax and its probability is >= ``min_nli_score``. Relevance is
    applied again here so an NLI score cannot promote an off-topic row:
        off-topic entailments are not support (``ignored_support``)
        off-topic contradictions are not contradictions
        (``ignored_contradictions``)
    Both ignored lists keep the original ``nli_label``, score, and reason.
    A contradiction is also discounted when another chunk of the same
    article strongly entails the claim with a higher ``match_score``. An
    article does not contradict itself; the less matching chunk is about a
    different detail. With equal match the two passages are a real
    conflict and both count.
    Then, using only relevant rows:
        strong entailment and strong contradiction -> UNSURE (conflict)
        strong entailment only                      -> SUPPORT
        strong contradiction only                   -> REJECT
        neither                                     -> UNSURE (neutral)
    Conflicts are reported, not resolved by picking the favourable side.
    Retrieving one relevant article is not enough: that article must still
    entail or contradict the specific claim.

Across claims (issue 7)
    all SUPPORT -> SUPPORT (confidence = weakest claim)
    any REJECT  -> REJECT  (confidence = strongest rejection)
    otherwise   -> UNSURE  (partial support / unchecked claims listed)

Provenance
    Every evidence row (evaluated, supporting, contradicting, ignored,
    discarded) carries the retriever's ``article_id``, ``article_key``,
    ``article_key_scope``, ``source_id`` and ``index_ref``; metadata carries
    ``corpus_version`` and ``index_version``. Field meanings are in
    evidence_retriever's docstring. Each claim has a ``claim_id``
    ("claim-0", ...); its ``claim_decisions`` entry lists the source_ids
    behind it by role in ``evidence_refs`` and names the
    ``deciding_source_id``, and every evidence row repeats the
    ``claim_id`` it was checked against.

Decision-layer hooks (unchanged)
    SUPPORT -> passed=True,  nli_label="entailment"
    REJECT  -> passed=False, nli_label="contradiction"
    UNSURE  -> passed=False, nli_label="neutral" (evidence was evaluated)
               or nli_label=None, score=0 (nothing relevant retrieved)
    Both UNSURE forms are abstentions for the decision layer.

All thresholds are UNCALIBRATED defaults and are echoed in metadata.
"""

from __future__ import annotations

import functools
import math
import re
import time
from typing import Any, Callable, Optional

from app.models.schemas import VerificationResult
from app.verifiers.base_verifier import (
    DECISION_REJECT,
    DECISION_SUPPORT,
    DECISION_UNSURE,
    BaseVerifier,
)
from app.verifiers.claim_generator import (
    SENTENCE_TEMPLATE,
    STATEMENT_TEMPLATE,
    ClaimGenerator,
    factual_question,
)
from app.verifiers.evidence_retriever import (
    STOPWORDS,
    EvidenceRetriever,
    content_terms,
    default_corpus_path,
)

NLI_LABELS = ("entailment", "contradiction", "neutral")
NLI_MODEL = "cross-encoder/nli-deberta-v3-small"
NO_EVIDENCE_REASON = "No evidence was retrieved."
NO_RELEVANT_EVIDENCE_REASON = "No sufficiently relevant evidence was retrieved."
OFF_SUBJECT_REASON = "article title is about a different subject than the question"
SAME_ARTICLE_REASON = "a passage of the same article that matches the claim better entails it"
# Machine-readable discard codes (``reason`` strings are kept for compatibility).
DISCARD_MISSING_EVENT_ID = "missing_event_identifier"
DISCARD_INSUFFICIENT_TOPIC = "insufficient_topic_evidence"
DISCARD_OFF_SUBJECT = "off_subject"
DISCARD_TOPIC_MARGIN = "topic_below_margin"
DISCARD_CANDIDATE_FOR_NLI = "candidate_retained_for_nli"
# Provenance copied from each retrieved chunk; see evidence_retriever's docstring.
SOURCE_FIELDS = ("article_id", "article_key", "article_key_scope", "source_id", "index_ref")

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_PREMISE_TERM = re.compile(r"\d+(?:[.,]\d+)*|[^\W\d_]+")
_CONDITION = re.compile(
    r"\b(?:at|after|under|during|before)\s+(?:the\s+)?([^\W\d_]{3,}(?:\s+[^\W\d_]{3,}){0,3})",
    re.IGNORECASE,
)
_CLAUSE_VERBS = frozenset(
    """
    is was are were be been being has have had do does did won wrote played
    occurred became defeated included remains contains lies held beat lost
    took made said
    """.split()
)
# Inquiry and property words name what is asked, not which event or entity.
_GENERIC_QUERY_TERMS = frozenset(
    """
    describe compare associated explain provide identify information outcome
    location duration warning question answer following including magnitude
    date score winner match time extra decided played country take place
    which where when used use
    """.split()
)
# Terms that name the requested property, rather than the event or subject.
_GENERIC_EVENT_TERMS = frozenset(
    """
    start starts ending ends date dates score scores record records vote
    percentage percent elected election pope regular season
    """.split()
)
# These identify the people or place, but are too broad to pair two dates as
# the same property (for example, an election date and a consecration date).
_GENERIC_PROPERTY_TERMS = frozenset({"bishop", "pope", "rome", "cardinal"})


def premise_terms(text: str) -> set[str]:
    """Content terms for choosing premise windows. Decimals stay whole ("7.7", "9.1").

    Words follow ``content_terms`` (no stopwords, 3+ letters). Thousands
    separators are dropped ("15,000" -> "15000").
    """
    terms = set()
    for token in _PREMISE_TERM.findall(str(text).lower()):
        if token[0].isdigit():
            terms.add(token.replace(",", "").rstrip("."))
        elif len(token) >= 3 and token not in STOPWORDS:
            terms.add(token)
    return terms


_MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}
_MONTH_ALT = "|".join(sorted(_MONTHS, key=len, reverse=True))
_DATE_DMY = re.compile(
    rf"\b(\d{{1,2}})\s+({_MONTH_ALT})\s+(\d{{4}})\b",
    re.IGNORECASE,
)
_DATE_DMY_PARTIAL = re.compile(
    rf"\b(\d{{1,2}})\s+({_MONTH_ALT})\b",
    re.IGNORECASE,
)
_DATE_MDY = re.compile(
    rf"\b({_MONTH_ALT})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})\b",
    re.IGNORECASE,
)
_PERCENT = re.compile(r"\b(\d+(?:\.\d+)?)\s*%")
# Corpus extraction can preserve a dash, normalize it, or leave a replacement
# glyph where a dash was lost (for example ``2�3``).
_RECORD = re.compile(r"\b(\d{1,2})\s*[-‐‑‒–—−�]\s*(\d{1,2})\b")
_PLAIN_NUMBER = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\b")
_NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12,
}
_NUMBER_WORD = re.compile(r"\b(" + "|".join(_NUMBER_WORDS) + r")\b", re.IGNORECASE)
_CONTEXT_GENERIC = frozenset(
    """
    the answer following took take place held occurred said after before
    from with into onto onto than about
    """.split()
)
# Labels that mark a win-loss pair as a result, not an incidental score.
_RECORD_CUES = frozenset(
    """
    record records finish finished finishing compiled posted posting
    """.split()
)
_STREAK_CUES = frozenset({"straight", "consecutive", "streak"})
_RUNNING_RECORD_CUES = frozenset({"began", "dropped", "improved", "reached", "rose"})
_POSTSEASON_CUES = frozenset({"playoff", "playoffs", "divisional", "super", "bowl"})
_WHO_AUXILIARIES = frozenset(
    {"was", "were", "is", "are", "did", "does", "do", "has", "have", "had"}
)
_GENERIC_PROPER = frozenset(
    """
    university college school championship election season game games team
    mayor church shooting record final league county state republic kingdom
    president bishop pope what who when where which how
    """.split()
)


def _context_terms(text: str, start: int, end: int, radius: int = 96) -> set[str]:
    """Content terms near a value, bounded to its sentence for property pairing."""
    sentence_start = max(
        (text.rfind(mark, 0, start) for mark in ".!;\n"),
        default=-1,
    ) + 1
    stops = [position for mark in ".!;\n" if (position := text.find(mark, end)) >= 0]
    sentence_end = min(stops, default=len(text))
    left = max(sentence_start, start - radius)
    right = min(sentence_end, end + radius)
    excerpt = text[left:right]
    terms = content_terms(excerpt) - _CONTEXT_GENERIC
    # Preserve range connectors so two endpoints can be paired when the
    # question explicitly asks for a start and end date.
    terms.update(
        term for term in ("from", "to")
        if re.search(rf"\b{term}\b", excerpt, re.IGNORECASE)
    )
    return terms


def extract_quantities(text: str) -> list[dict]:
    """Dates, percents, win-loss records, and numbers with local context.

    This is a conservative span extractor, not a full temporal or numeric
    reasoner. Ranges, decimals, thousands separators, and common date
    orders are recognised; a number is never assumed to describe a claim
    just because it appears in the same passage.
    """
    source = str(text)
    found: list[dict] = []
    occupied: list[tuple[int, int]] = []

    def overlaps(start: int, end: int) -> bool:
        return any(not (end <= left or start >= right) for left, right in occupied)

    def add(kind: str, normalized, raw: str, start: int, end: int) -> None:
        if overlaps(start, end):
            return
        occupied.append((start, end))
        found.append(
            {
                "kind": kind,
                "normalized": normalized,
                "raw": raw,
                "context": _context_terms(source, start, end),
            }
        )

    for match in _DATE_DMY.finditer(source):
        add(
            "date",
            (int(match.group(3)), _MONTHS[match.group(2).lower()], int(match.group(1))),
            match.group(0),
            match.start(),
            match.end(),
        )
    for match in _DATE_DMY_PARTIAL.finditer(source):
        add(
            "date",
            (None, _MONTHS[match.group(2).lower()], int(match.group(1))),
            match.group(0),
            match.start(),
            match.end(),
        )
    for match in _DATE_MDY.finditer(source):
        add(
            "date",
            (int(match.group(3)), _MONTHS[match.group(1).lower()], int(match.group(2))),
            match.group(0),
            match.start(),
            match.end(),
        )
    for match in _PERCENT.finditer(source):
        add("percent", float(match.group(1)), match.group(0), match.start(), match.end())
    for match in _RECORD.finditer(source):
        add(
            "record",
            (int(match.group(1)), int(match.group(2))),
            match.group(0),
            match.start(),
            match.end(),
        )
    for match in _PLAIN_NUMBER.finditer(source):
        raw = match.group(1)
        if overlaps(match.start(), match.end()):
            continue
        if len(raw) == 4 and raw.isdigit() and 1000 <= int(raw) <= 2099:
            add("date", (int(raw), None, None), raw, match.start(), match.end())
            continue
        numeric = float(raw.replace(",", ""))
        add("number", numeric, raw, match.start(), match.end())
    for match in _NUMBER_WORD.finditer(source):
        add(
            "number",
            float(_NUMBER_WORDS[match.group(1).lower()]),
            match.group(0),
            match.start(),
            match.end(),
        )
    return found


def values_equal(left: dict, right: dict) -> bool:
    """True when ``right`` states every component ``left`` asserts.

    A year or month in evidence does not confirm a claimed day. Shared
    components that differ are not equal. Call with the claimed value on
    the left and the observed value on the right.
    """
    if left["kind"] != right["kind"]:
        return False
    if left["kind"] == "date":
        claimed_parts = 0
        matched_parts = 0
        for claimed, observed in zip(left["normalized"], right["normalized"]):
            if claimed is None:
                continue
            claimed_parts += 1
            if observed is None:
                continue
            if claimed != observed:
                return False
            matched_parts += 1
        return claimed_parts > 0 and matched_parts == claimed_parts
    if left["kind"] in {"number", "percent"}:
        return abs(float(left["normalized"]) - float(right["normalized"])) < 1e-6
    return left["normalized"] == right["normalized"]


def values_conflict(left: dict, right: dict) -> bool:
    """True when both values specify a component and those components differ.

    An omitted day or month is not a conflict. Call with the claimed value
    on the left and the observed value on the right.
    """
    if left["kind"] != right["kind"]:
        return False
    if left["kind"] == "date":
        for claimed, observed in zip(left["normalized"], right["normalized"]):
            if claimed is not None and observed is not None and claimed != observed:
                return True
        return False
    return not values_equal(left, right)


def property_cues(question: str, claim: str = "") -> set[str]:
    """Lowercase property words from the question and claim, not proper names."""
    cues: set[str] = set()
    for raw in re.findall(r"[A-Za-z]+", f"{factual_question(question)} {claim}"):
        if raw[:1].isupper() and raw.lower() not in _MONTHS:
            continue
        token = raw.lower()
        if (
            len(token) >= 4
            and token not in STOPWORDS
            and token not in _GENERIC_QUERY_TERMS
            and token not in _GENERIC_PROPERTY_TERMS
            and token not in _MONTHS
        ):
            cues.add(token)
    return cues


def same_property(left: dict, right: dict, question: str = "", claim: str = "") -> bool:
    """True when two quantities likely describe the same asked property.

    Both values must sit beside a shared property cue from the question or
    claim. Proper names are not cues, so two numbers that only share an
    entity are not treated as the same measurement. Two dates in one
    article are not the same property unless those cues appear beside both.
    """
    if left["kind"] != right["kind"]:
        return False
    if left["kind"] == "record":
        # A week-one or mid-season score shares "season" with a final record
        # without naming the same property. Both sides must look like a result,
        # not a winning streak counted beside a running total.
        if not (_RECORD_CUES & left["context"] and _RECORD_CUES & right["context"]):
            return False
        if _STREAK_CUES & left["context"] or _STREAK_CUES & right["context"]:
            return False
        if (
            "regular" in left["context"]
            and _POSTSEASON_CUES & right["context"]
        ) or (
            "regular" in right["context"]
            and _POSTSEASON_CUES & left["context"]
        ):
            return False
    cues = property_cues(question, claim)
    if (
        left["kind"] == right["kind"] == "date"
        and {"start", "dates"} <= cues
        and "to" in left["context"]
        and {"from", "to"} <= right["context"]
    ):
        return True
    if not cues:
        shared = {
            term
            for term in (left["context"] & right["context"])
            - _GENERIC_QUERY_TERMS
            - _GENERIC_PROPERTY_TERMS
            if not term.isdigit()
            and term not in _MONTHS
        }
        return bool(shared)
    if left["kind"] == "record" and "regular" in cues:
        # A running weekly record is not the final regular-season result.
        if (
            "regular" not in right["context"]
            and _RUNNING_RECORD_CUES & right["context"]
        ):
            return False
    return bool(cues & left["context"] and cues & right["context"] and (cues & left["context"] & right["context"]))


def asserted_quantities(claim: str, question: str = "") -> list[dict]:
    """Quantities the claim adds beyond the question; those are under test."""
    claimed = extract_quantities(claim)
    if not claimed:
        return []
    asked = {(item["kind"], item["normalized"]) for item in extract_quantities(factual_question(question))}
    return [item for item in claimed if (item["kind"], item["normalized"]) not in asked]


def value_relation(claim: str, passages: list[str], question: str = "") -> str:
    """Return ``match``, ``mismatch``, or ``none`` for claim vs passages.

    A mismatch is an explicit same-property value conflict. A supporting
    passage that simply omits the claimed value is ``none``, not a
    contradiction. If pairing is unreliable, this returns ``none``.
    Only values the claim adds beyond the question are tested, so an event
    year already in the question cannot count as support by itself.
    """
    claimed = asserted_quantities(claim, question)
    if not claimed:
        return "none"
    matched = False
    mismatched = False
    for passage in passages:
        observed_all = extract_quantities(passage)
        records = [item for item in observed_all if item["kind"] == "record"]
        skip_loose_records = len(records) >= 2
        for observed in observed_all:
            if observed["kind"] == "record" and skip_loose_records:
                if not (_RECORD_CUES - {"record", "records"}) & observed["context"]:
                    continue
            for item in claimed:
                if not same_property(item, observed, question, claim):
                    continue
                if values_equal(item, observed):
                    matched = True
                elif values_conflict(item, observed):
                    mismatched = True
    if mismatched and not matched:
        return "mismatch"
    if matched:
        return "match"
    return "none"


@functools.lru_cache(maxsize=1)
def default_nli_pipeline() -> Any:
    """Process-wide NLI pipeline shared by the evidence and confidence verifiers.

    Loading the cross-encoder twice costs several hundred MB; both verifiers
    call this when no ``nli`` is injected. ``top_k=None`` returns every label
    so callers can read all three probabilities.
    """
    from transformers import pipeline

    return pipeline("text-classification", model=NLI_MODEL, top_k=None)


def normalize_nli_label(label: str) -> str:
    """Map a model label string onto entailment / contradiction / neutral.

    Raises ``ValueError`` for labels that match none of them (for example
    ``LABEL_0``), so a model with an unexpected label set fails loudly
    instead of being read as neutral.
    """
    lowered = str(label).strip().lower()
    if "entail" in lowered:
        return "entailment"
    if "contradict" in lowered:
        return "contradiction"
    if "neutral" in lowered:
        return "neutral"
    raise ValueError(f"Unrecognised NLI label {label!r}; expected one of {NLI_LABELS}")


def parse_nli_output(raw: Any) -> tuple[dict[str, float], str]:
    """Normalise a text-classification pipeline output for one input.

    Accepts the shapes different Transformers versions produce for a
    single ``{"text", "text_pair"}`` input:
        dict                      -> top label only
        list[dict]                -> all labels (``top_k=None``) or one
        list[list[dict]]          -> batch of one input
    Returns ``({label: probability}, shape_name)``.
    """
    if isinstance(raw, dict):
        rows, shape = [raw], "dict"
    elif isinstance(raw, list) and raw and isinstance(raw[0], list):
        rows, shape = raw[0], "list[list[dict]]"
    elif isinstance(raw, list):
        rows, shape = raw, "list[dict]"
    else:
        raise ValueError(f"Unexpected NLI output type {type(raw).__name__}")

    probabilities: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict) or "label" not in row or "score" not in row:
            raise ValueError(f"Unexpected NLI output row {row!r}")
        probabilities[normalize_nli_label(row["label"])] = float(row["score"])
    if not probabilities:
        raise ValueError("NLI output contained no labels")
    return probabilities, shape


class EvidenceVerifier(BaseVerifier):
    """Verifies each claim of an answer against retrieved evidence using NLI."""

    NLI_MODEL = NLI_MODEL
    # Chunks this short are judged as one premise, as before windows existed.
    LEGACY_PREMISE_SENTENCES = 3

    SCORE_MEANING = (
        "NLI probability of the label that decided the result (entailment for "
        "SUPPORT, contradiction for REJECT) on the deciding evidence chunk; 0 for "
        "UNSURE. A class probability from one model, not a calibrated probability "
        "that the answer is correct."
    )

    def __init__(
        self,
        corpus_path: str | None = None,
        top_k: int = 3,
        min_retrieval_score: float = 0.45,
        retrieval_margin: float = 0.15,
        min_nli_score: float = 0.50,
        min_topic_coverage: float = 0.50,
        topic_margin: float = 0.30,
        max_premise_windows: int = 3,
        max_premise_chars: int = 1500,
        retriever: EvidenceRetriever | None = None,
        nli: Callable[[dict], Any] | None = None,
    ) -> None:
        if corpus_path is None:
            corpus_path = default_corpus_path()
        self.retriever = retriever or EvidenceRetriever(corpus_path=corpus_path)
        self.top_k = top_k
        self.min_retrieval_score = min_retrieval_score
        self.retrieval_margin = retrieval_margin
        self.min_nli_score = min_nli_score
        self.min_topic_coverage = min_topic_coverage
        self.topic_margin = topic_margin
        self.max_premise_windows = max_premise_windows
        self.max_premise_chars = max_premise_chars
        self.claim_generator = ClaimGenerator()

        if nli is None:
            nli = default_nli_pipeline()
        self.nli = nli
        self.nli_tokenizer = getattr(nli, "tokenizer", None)
        self.nli_max_length = self._nli_max_length(nli)
        self.nli_label_map = self._check_label_map(nli)

    @property
    def name(self) -> str:
        return "evidence"

    # ------------------------------------------------------------------
    # NLI helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_label_map(nli: Any) -> dict[str, str] | None:
        """Verify the model's id2label covers the three NLI classes, if visible."""
        config = getattr(getattr(nli, "model", None), "config", None)
        id2label = getattr(config, "id2label", None)
        if not id2label:
            return None
        mapping = {str(label): normalize_nli_label(label) for label in id2label.values()}
        missing = set(NLI_LABELS) - set(mapping.values())
        if missing:
            raise ValueError(f"NLI model labels {list(id2label.values())} do not cover {sorted(missing)}")
        return mapping

    def extract_relevant_sentences(
        self,
        text: str,
        claim: str,
        max_sentences: int = 3,
        question: str | None = None,
    ) -> str:
        """Pick the chunk sentences with most word overlap with the claim.

        Chunks can exceed the NLI model's input length; this keeps the
        premise short and on-topic. Falls back to the chunk head when no
        sentence shares a word with the claim. Question terms, when given,
        count toward overlap so a passage about the asked event is preferred
        over a same-word sentence about a different event.
        """
        sentences = re.split(r"(?<=[.!?])\s+", text)
        claim_words = {w.lower() for w in re.findall(r"\b\w+\b", claim)}
        if question:
            claim_words |= {w.lower() for w in re.findall(r"\b\w+\b", factual_question(question))}

        scored = []
        for sentence in sentences:
            words = {w.lower() for w in re.findall(r"\b\w+\b", sentence)}
            overlap = len(claim_words & words)
            if overlap > 0:
                scored.append((overlap, sentence.strip()))
        scored.sort(key=lambda item: item[0], reverse=True)
        selected = [sentence for _, sentence in scored[:max_sentences]]
        return " ".join(selected) if selected else text[:1500]

    def extract_premises(
        self, evidence: dict, claim: str, question: str | None = None
    ) -> list[str]:
        """NLI premises for one chunk: one for a short chunk, windows for a long one."""
        text = str(evidence.get("text", ""))
        # Corpus headings and paragraph breaks are meaningful event boundaries.
        # Keeping them separate prevents an adjacent section's date or result
        # from contaminating a premise about the preceding fact.
        sentences = [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+|\n+", text)
            if s.strip()
        ]
        if len(sentences) <= self.LEGACY_PREMISE_SENTENCES:
            return [self.extract_relevant_sentences(text, claim, question=question)]

        title = str(evidence.get("title") or "").strip()
        asked = factual_question(question) if question else ""
        asked_years = self._year_terms(asked) if asked else set()
        asserted = asserted_quantities(claim, asked) if asked else extract_quantities(claim)
        scored = []
        for position, sentence in enumerate(sentences):
            score = self.match_score(claim, title, sentence)
            if asked:
                score += self.match_score(asked, title, sentence)
            if asked_years and asked_years & content_terms(sentence):
                score += 3
            if asserted:
                observed = extract_quantities(sentence)
                if any(
                    same_property(item, found, asked, claim) and values_equal(item, found)
                    for item in asserted
                    for found in observed
                ):
                    score += 6
                elif any(
                    same_property(item, found, asked, claim)
                    for item in asserted
                    for found in observed
                ):
                    score += 3
            if score:
                scored.append((score, -position, position))
        if not scored:
            return [self.extract_relevant_sentences(text, claim, question=question)]
        scored.sort(reverse=True)

        windows: list[str] = []
        spans: list[tuple[int, int]] = []
        for _, _, position in scored[: self.max_premise_windows]:
            for span in ((max(position - 1, 0), position + 1), (position, min(position + 2, len(sentences)))):
                if span in spans:
                    continue
                spans.append(span)
                body = " ".join(sentences[span[0] : span[1]])
                if title and not body.lower().startswith(title.lower()):
                    body = f"{title}. {body}"
                windows.append(body[: self.max_premise_chars])
        return windows

    @staticmethod
    def match_score(claim: str, title: str, text: str) -> int:
        """Claim terms found in ``text``, ignoring the title's own words; numbers count double."""
        claim_terms = premise_terms(claim)
        distinctive = (claim_terms - premise_terms(title)) or claim_terms
        return sum(2 if term[0].isdigit() else 1 for term in distinctive & premise_terms(text))

    def score_evidence(
        self,
        evidence: dict,
        claim: str,
        premise: str | list[str] | None = None,
        question: str | None = None,
        template: str = "",
    ) -> dict:
        """Run NLI for one chunk/claim pair and return a flat evidence row.

        ``premise`` may be one premise or several windows of the chunk; see
        the module docstring for how a window is chosen.
        """
        if premise is None:
            premises = self.extract_premises(evidence, claim, question)
        elif isinstance(premise, str):
            premises = [premise]
        else:
            premises = list(premise) or [
                self.extract_relevant_sentences(evidence["text"], claim, question=question)
            ]

        title = str(evidence.get("title") or "").strip()
        prefix = f"{title}. " if title else ""
        windows = []
        for text in premises:
            for bounded in self._token_windows(text, claim):
                window = self._nli_window(bounded, claim)
                if prefix and bounded.startswith(prefix) and self._is_strong(window, "entailment"):
                    bare = self._nli_window(bounded[len(prefix) :], claim)
                    if self._is_strong(bare, "contradiction"):
                        window = {**bare, "premise": bounded, "title_dependent": True}
                windows.append(window)
        chosen = self._choose_window(windows, question=question, title=title, claim=claim)
        label = chosen["nli_label"]
        body = chosen["premise"][len(prefix) :] if prefix and chosen["premise"].startswith(prefix) else chosen["premise"]
        asked = factual_question(question) if question else ""
        relation = chosen.get("value_relation") or value_relation(
            claim, [self._bare_premise(chosen["premise"], title)], asked
        )
        names = self._claim_added_names(claim, asked)
        quantity_kinds = sorted(
            {item["kind"] for item in asserted_quantities(claim, asked)}
        )
        names_present = (not names) or any(
            re.search(rf"\b{re.escape(name)}\b", chosen["premise"], re.IGNORECASE)
            for name in names
        )
        office = self._office_phrase(asked)
        holder = self._office_holder(chosen["premise"], office) if office else None
        office_holder_consistent = holder is None or any(
            name.lower() in holder.lower() for name in names
        )
        relation_template = "who" if question and factual_question(question).lower().startswith("who ") else template
        relation_terms, _ = self.relation_entity_terms(question or "", relation_template)
        bare_terms = premise_terms(self._bare_premise(chosen["premise"], title))
        # A relation word in the title only ("papal election") does not make a
        # nearby sentence about succession evidence for the act of electing.
        required_relation_terms = {
            term for term in relation_terms if len(term) >= 4 and not term.isdigit()
        }
        relation_aligned = not required_relation_terms or required_relation_terms <= bare_terms
        claim_property_terms = property_cues(asked, claim)
        quantity_scope_aligned = not (
            "record" in quantity_kinds
            and "regular" in claim_property_terms
            and _POSTSEASON_CUES & bare_terms
        )
        return {
            "title": evidence.get("title"),
            "chunk_id": evidence.get("chunk_id"),
            "url": evidence.get("url"),
            **self.source_ref(evidence),
            "retrieval_score": float(evidence["score"]),
            "relevant_evidence": chosen["premise"],
            "match_score": self.match_score(claim, title, body),
            "fact_score": chosen.get("fact_score"),
            "value_relation": relation,
            "quantity_kinds": quantity_kinds,
            "quantity_scope_aligned": quantity_scope_aligned,
            "claim_names_in_premise": names_present,
            "office_holder_consistent": office_holder_consistent,
            "relation_aligned": relation_aligned,
            "nli_label": label,
            "nli_score": chosen["probabilities"][label],
            "probabilities": chosen["probabilities"],
            "nli_output_shape": chosen["nli_output_shape"],
            "premise_windows": [
                {
                    "premise": w["premise"],
                    "nli_label": w["nli_label"],
                    "probabilities": w["probabilities"],
                    "token_count": w.get("token_count"),
                    "title_dependent": w.get("title_dependent", False),
                    "fact_score": w.get("fact_score"),
                    "value_relation": w.get("value_relation"),
                }
                for w in windows
            ],
        }

    @staticmethod
    def source_ref(evidence: dict) -> dict:
        """The chunk's provenance fields; None for any the retriever did not supply."""
        return {field: evidence.get(field) for field in SOURCE_FIELDS}

    @staticmethod
    def _nli_max_length(nli: Any) -> int | None:
        """Return the smallest usable tokenizer/model input limit."""
        tokenizer = getattr(nli, "tokenizer", None)
        config = getattr(getattr(nli, "model", None), "config", None)
        candidates = [
            getattr(tokenizer, "model_max_length", None),
            getattr(config, "max_position_embeddings", None),
        ]
        usable = [
            int(value) for value in candidates
            if isinstance(value, (int, float)) and 2 < value < 1_000_000
        ]
        return min(usable) if usable else None

    def _token_windows(self, premise: str, claim: str) -> list[str]:
        """Split a premise into overlapping windows that fit with the claim."""
        tokenizer = self.nli_tokenizer
        limit = self.nli_max_length
        if tokenizer is None or limit is None:
            return [premise]

        backend = getattr(tokenizer, "backend_tokenizer", None)
        if backend is not None:
            claim_tokens = list(backend.encode(claim, add_special_tokens=False).ids)
            premise_encoding = backend.encode(premise, add_special_tokens=False)
            premise_tokens = list(premise_encoding.ids)
            offsets = list(premise_encoding.offsets)
        else:
            claim_tokens = tokenizer.tokenize(claim)
            premise_tokens = tokenizer.tokenize(premise)
            offsets = None
        special = int(tokenizer.num_special_tokens_to_add(pair=True))
        budget = limit - len(claim_tokens) - special
        if budget < 1:
            raise ValueError(
                f"NLI claim requires {len(claim_tokens) + special} tokens, "
                f"which leaves no premise capacity within model limit {limit}."
            )

        if len(premise_tokens) <= budget:
            return [premise]

        overlap = min(32, max(1, budget // 8))
        step = max(1, budget - overlap)
        windows = []
        for start in range(0, len(premise_tokens), step):
            tokens = premise_tokens[start : start + budget]
            if not tokens:
                break
            if offsets:
                first, last = offsets[start], offsets[start + len(tokens) - 1]
                windows.append(premise[first[0] : last[1]])
            else:
                windows.append(tokenizer.convert_tokens_to_string(tokens))
            if start + budget >= len(premise_tokens):
                break
        return windows

    def _nli_window(self, premise: str, claim: str) -> dict:
        inputs = {"text": premise, "text_pair": claim}
        token_count = None
        if self.nli_tokenizer is not None and self.nli_max_length is not None:
            encoded = self.nli_tokenizer(
                premise,
                claim,
                add_special_tokens=True,
                truncation=False,
            )
            token_count = len(encoded["input_ids"])
            if token_count > self.nli_max_length:
                raise AssertionError(
                    f"NLI pair has {token_count} tokens; model limit is {self.nli_max_length}"
                )
        probabilities, shape = parse_nli_output(self.nli(inputs))
        return {
            "premise": premise,
            "nli_label": max(probabilities, key=probabilities.get),
            "probabilities": probabilities,
            "nli_output_shape": shape,
            "token_count": token_count,
        }

    def _is_strong(self, window: dict, label: str) -> bool:
        return window["nli_label"] == label and window["probabilities"].get(label, 0.0) >= self.min_nli_score

    def _bare_premise(self, premise: str, title: str | None) -> str:
        prefix = f"{title}. " if title else ""
        if prefix and premise.startswith(prefix):
            return premise[len(prefix) :]
        return premise

    def _fact_score(
        self,
        premise: str,
        claim: str,
        question: str | None,
        title: str | None,
    ) -> int:
        """How directly a window addresses the asked fact, independent of NLI."""
        bare = self._bare_premise(premise, title)
        score = self.match_score(claim, title or "", bare)
        asked = factual_question(question) if question else ""
        if asked:
            score += self.match_score(asked, title or "", bare)
            if self._year_terms(asked) & content_terms(bare):
                score += 2
        relation = value_relation(claim, [bare], asked)
        if relation == "match":
            score += 6
        elif relation == "mismatch":
            score += 3
        return score

    def _choose_window(
        self,
        windows: list[dict],
        question: str | None = None,
        title: str | None = None,
        claim: str | None = None,
    ) -> dict:
        """Pick the window that addresses the asked fact, then apply NLI.

        NLI probability does not decide relevance. A high-confidence
        contradiction about another date, score, or event cannot override a
        window that states the requested property. Direct same-property
        support and contradiction both remain eligible.
        """
        if not windows:
            raise ValueError("NLI produced no windows to choose from")
        asked = factual_question(question) if question else ""
        for window in windows:
            window["fact_score"] = self._fact_score(
                window["premise"], claim or "", question, title
            )
            window["value_relation"] = value_relation(
                claim or "", [self._bare_premise(window["premise"], title)], asked
            )
        best_fact = max(window["fact_score"] for window in windows)
        focused = [window for window in windows if window["fact_score"] >= best_fact - 3]
        if not focused:
            focused = windows

        matches = [window for window in focused if window["value_relation"] == "match"]
        mismatches = [window for window in focused if window["value_relation"] == "mismatch"]
        if matches and not mismatches:
            return max(matches, key=lambda w: (w["fact_score"], w["probabilities"].get("entailment", 0.0)))
        if mismatches and not matches:
            return max(
                mismatches,
                key=lambda w: (w["fact_score"], w["probabilities"].get("contradiction", 0.0)),
            )

        entailing = [w for w in focused if self._is_strong(w, "entailment")]
        contradicting = [w for w in focused if self._is_strong(w, "contradiction")]
        if entailing and not contradicting:
            return max(entailing, key=lambda w: (w["fact_score"], w["probabilities"]["entailment"]))
        if contradicting and not entailing:
            return max(
                contradicting,
                key=lambda w: (w["fact_score"], w["probabilities"]["contradiction"]),
            )
        if entailing and contradicting:
            best_e = max(entailing, key=lambda w: w["fact_score"])
            best_c = max(contradicting, key=lambda w: w["fact_score"])
            if best_e["fact_score"] != best_c["fact_score"]:
                return best_e if best_e["fact_score"] > best_c["fact_score"] else best_c
            return best_e
        return max(focused, key=lambda w: (w["fact_score"], w["probabilities"].get("entailment", 0.0)))

    @staticmethod
    def is_about_subject(evidence: dict, subject_terms: set[str]) -> bool:
        """True when one local passage establishes the question's subject.

        A title must cover all subject terms to establish relevance alone.
        Otherwise the supplied passage must cover a majority with at least
        two matches. Callers pass individual premise windows, not the full
        article, so unrelated sentences cannot jointly satisfy the relation.
        """
        title_terms = content_terms(evidence.get("title") or "")
        non_digit_subject = {term for term in subject_terms if not term.isdigit()}
        if subject_terms and subject_terms <= title_terms and non_digit_subject:
            return True
        body_terms = content_terms(evidence.get("text") or "")
        shared = body_terms & subject_terms
        if not (shared & non_digit_subject):
            return False
        return len(shared) >= 2 and len(shared) / max(len(subject_terms), 1) > 0.5

    @staticmethod
    def relation_entity_terms(question: str, template: str) -> tuple[set[str], str | None]:
        """Return relation terms and the requested entity for supported fact templates."""
        cleaned = factual_question(question).strip().rstrip("?")
        if template == "capital":
            match = re.match(r"what is the capital of (.+)$", cleaned, re.IGNORECASE)
            if match:
                return {"capital"}, match.group(1).strip()
        if template == "who":
            match = re.match(r"who (.+)$", cleaned, re.IGNORECASE)
            if match:
                words = match.group(1).split()
                while words and words[0].lower() in _WHO_AUXILIARIES:
                    words = words[1:]
                relation = content_terms(words[0]) if words else set()
                entity = " ".join(words[1:]).strip() if len(words) > 1 else None
                if entity and (
                    EvidenceVerifier._year_terms(entity)
                    or len(entity.split()) > 4
                ):
                    entity = None
                return relation, entity
        if template == "process":
            match = re.match(r"at what (.+?) (?:does|do|did) (.+)$", cleaned, re.IGNORECASE)
            if match:
                return content_terms(match.group(1)), match.group(2).strip()
        if template == "attribute":
            match = re.match(
                r"what (?:was|were|are|is) (?:the |a |an )?(.+)$",
                cleaned,
                re.IGNORECASE,
            )
            if match:
                rest = match.group(1).strip()
                of_split = re.match(r"(.+?) of (.+)$", rest, re.IGNORECASE)
                if of_split:
                    entity = of_split.group(2).strip()
                    entity = re.sub(r"^(?:the\s+)", "", entity, flags=re.IGNORECASE)
                    entity = entity.replace("’", "'")
                    if "'s" in entity:
                        entity = entity.split("'s", 1)[0].strip()
                    elif re.search(r"s'\s", entity, re.IGNORECASE):
                        entity = re.split(r"(?<=s)'\s", entity, maxsplit=1, flags=re.IGNORECASE)[0].strip()
                    return content_terms(of_split.group(1)), entity
                possessive = re.match(
                    r"(?:the\s+)?(.+?)[’']s\s+(.+?)(?:\s+in\s+\d{4})?$",
                    rest,
                    re.IGNORECASE,
                )
                if possessive:
                    return content_terms(possessive.group(2)), possessive.group(1).strip()
                return content_terms(rest), None
        return set(), None

    @staticmethod
    def contains_unmodified_entity(text: str, entity: str | None) -> bool:
        """Match an entity phrase without treating a longer proper name as identical."""
        if not entity:
            return True
        pattern = re.compile(rf"\b{re.escape(entity)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            prefix = text[: match.start()]
            if prefix.endswith("-"):
                continue
            previous = re.findall(r"[^\W\d_]+", prefix)
            if previous and entity[:1].isupper():
                if previous[-1][:1].isupper():
                    continue
                if (
                    previous[-1].lower() in {"de", "del", "la", "le", "of", "the"}
                    and len(previous) > 1
                    and previous[-2][:1].isupper()
                ):
                    continue
            return True
        return False

    @staticmethod
    def _year_terms(text: str) -> set[str]:
        """Four-digit years in ``text``. Used to tell one dated event from another."""
        years = set()
        for term in content_terms(text):
            if term.isdigit() and len(term) == 4:
                value = int(term)
                if 1000 <= value <= 2099:
                    years.add(term)
        return years

    def _event_terms(self, question: str) -> set[str]:
        """Distinctive non-numeric question terms that name an event or entity.

        Generic request and property words are dropped so a long descriptive
        question is not required to appear almost verbatim in the title.
        When the retriever exposes IDF weights, only terms at or above the
        median weight are kept.
        """
        terms = {
            term
            for term in content_terms(factual_question(question))
            if not term.isdigit()
            and len(term) >= 4
            and term not in _GENERIC_QUERY_TERMS
            and term not in _GENERIC_EVENT_TERMS
        }
        weigh = getattr(self.retriever, "term_weights", None)
        if weigh is None or not terms:
            return terms
        weights = dict(weigh(terms))
        if not weights:
            return terms
        ranked = sorted(weights.values())
        median = ranked[len(ranked) // 2]
        distinctive = {term for term, weight in weights.items() if weight >= median}
        return distinctive or terms

    @staticmethod
    def _terms_related(left: str, right: str) -> bool:
        """True for identical tokens or a shared stem of at least five letters."""
        if left == right:
            return True
        if min(len(left), len(right)) < 4:
            return False
        if left.startswith(right) or right.startswith(left):
            return True
        shared = 0
        for a, b in zip(left, right):
            if a != b:
                break
            shared += 1
        return shared >= 5

    @staticmethod
    def _term_overlap(needed: set[str], present: set[str]) -> int:
        """Count needed terms that appear in ``present`` or share a stem."""
        matched = 0
        for term in needed:
            if any(EvidenceVerifier._terms_related(term, other) for other in present):
                matched += 1
        return matched

    @staticmethod
    def _title_covers_event(title: str, question_years: set[str], event_terms: set[str]) -> bool:
        """True when the title itself names the asked year and event."""
        terms = content_terms(title)
        if question_years and not (question_years & terms):
            return False
        if not event_terms:
            return bool(question_years & terms)
        needed = max(1, (len(event_terms) + 1) // 2)
        return EvidenceVerifier._term_overlap(event_terms, terms) >= needed

    @staticmethod
    def _title_names_other_event(
        title: str,
        question: str,
        question_years: set[str],
        event_terms: set[str],
    ) -> bool:
        """True when the title names a different dated event than the question."""
        if not question_years:
            return False
        title_years = EvidenceVerifier._year_terms(title)
        if title_years and title_years.isdisjoint(question_years):
            return True
        if EvidenceVerifier._title_covers_event(title, question_years, event_terms):
            return False
        extra = {
            term
            for term in content_terms(title) - content_terms(factual_question(question))
            if not term.isdigit() and len(term) >= 4
        }
        return len(extra) >= 2 and not (event_terms & content_terms(title))

    @staticmethod
    def _local_covers_event(
        title: str,
        sentences: list[str],
        question_years: set[str],
        event_terms: set[str],
    ) -> bool:
        """True when title plus one local sentence names the asked event."""
        title_terms = content_terms(title)
        needed = max(1, (len(event_terms) + 1) // 2) if event_terms else 0
        windows = sentences or [""]
        for sentence in windows:
            if EvidenceVerifier._looks_like_name_list(sentence):
                continue
            terms = title_terms | content_terms(sentence)
            if question_years and not (question_years & terms):
                continue
            if not event_terms or EvidenceVerifier._term_overlap(event_terms, terms) >= needed:
                return True
        return False

    @staticmethod
    def _looks_like_name_list(sentence: str) -> bool:
        """True for a caption-like run of names with no clause verb."""
        tokens = re.findall(r"[A-Za-z0-9]+", sentence)
        if len(tokens) < 6:
            return False
        capped = sum(1 for token in tokens if token[:1].isupper())
        if capped / len(tokens) < 0.45:
            return False
        return not ({token.lower() for token in tokens} & _CLAUSE_VERBS)

    @staticmethod
    def _condition_phrases(text: str) -> list[str]:
        return [match.group(0).lower() for match in _CONDITION.finditer(str(text))]

    @staticmethod
    def _conditions_conflict(question: str, title: str, local: str) -> bool:
        """True when question and evidence name disjoint setting phrases."""
        asked = [
            content_terms(phrase)
            for phrase in EvidenceVerifier._condition_phrases(factual_question(question))
        ]
        asked = [terms for terms in asked if terms]
        if not asked:
            return False
        found = [
            content_terms(phrase)
            for phrase in EvidenceVerifier._condition_phrases(f"{title} {local}")
        ]
        found = [terms for terms in found if terms]
        if not found:
            return False
        return not any(left & right for left in asked for right in found)

    def _retrieval_query(self, question: str, claim: str, template: str) -> str:
        """First-pass query: question alone for templates, question+claim for sentences."""
        base = factual_question(question)
        if template == SENTENCE_TEMPLATE:
            return f"{base} {claim}".strip()
        return base

    @staticmethod
    def _contextualize_claim(question: str, answer: str, claim: str, template: str) -> str:
        """Repair answer fragments and generic fallback claims using the question predicate."""
        asked = factual_question(question).strip().rstrip("?")
        answer = str(answer).strip().rstrip(".")
        if template == "fallback":
            where = re.fullmatch(r"where did (.+?) take place", asked, re.IGNORECASE)
            if where:
                return f"The {where.group(1)} took place at {answer}."
            when = re.fullmatch(r"when was (.+)", asked, re.IGNORECASE)
            if when:
                event = re.fullmatch(
                    r"(.+?)\s+(consecrated|born|founded|held|elected|crowned|"
                    r"established|opened|completed|built|created)(.*)",
                    when.group(1),
                    re.IGNORECASE,
                )
                if event:
                    subject, verb, detail = event.groups()
                    return f"{subject} was {verb}{detail} on {answer}."
                return f"{when.group(1)} was on {answer}."
        if template == STATEMENT_TEMPLATE:
            who = re.fullmatch(r"who was (.+)", asked, re.IGNORECASE)
            if who and " was " not in answer.lower():
                return f"{answer}, was {who.group(1)}."
        return claim

    @staticmethod
    def _office_phrase(question: str) -> str | None:
        """Role phrase such as ``mayor of toronto`` when the question names one."""
        match = re.search(
            r"\b((?:mayor|president|governor|senator|premier)\s+of\s+[A-Z][A-Za-z]+)",
            factual_question(question),
            re.IGNORECASE,
        )
        return match.group(1).lower() if match else None

    @staticmethod
    def _office_holder(passage: str, office: str) -> str | None:
        """Nearest first-last name before an office phrase in ``passage``."""
        idx = passage.lower().find(office)
        if idx < 0:
            return None
        prior = passage[max(0, idx - 80) : idx]
        names = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+", prior)
        return names[-1] if names else None

    @staticmethod
    def _claim_added_names(claim: str, question: str) -> list[str]:
        """Proper names the claim adds beyond the question."""
        asked = content_terms(factual_question(question))
        names: list[str] = []
        seen: set[str] = set()
        for raw in re.findall(r"[A-Za-z][A-Za-z'-]+", str(claim)):
            token = raw.lower()
            if (
                token in seen
                or token in asked
                or token in STOPWORDS
                or token in _MONTHS
                or len(token) < 4
                or not raw[:1].isupper()
            ):
                continue
            names.append(raw)
            seen.add(token)
        return names

    def _claim_focus_terms(self, claim: str, question: str) -> list[str]:
        """Compact claim terms that add an information need: names and years.

        Extra common words dilute the subject, so only capitalized names and
        asserted numeric values (including non-year quantities) that are not
        already in the question are kept. Answer terms are used only on this
        second pass; the initial search remains answer independent.
        """
        question_terms = content_terms(question)
        extras: list[str] = []
        seen: set[str] = set()
        for raw in re.findall(r"[A-Za-z0-9]+", str(claim)):
            token = raw.lower()
            if token in seen or token in question_terms or token in STOPWORDS:
                continue
            is_number = token.isdigit()
            is_name = raw[:1].isupper() and len(token) >= 3
            if not (is_number or is_name):
                continue
            extras.append(raw)
            seen.add(token)
            if len(extras) >= 5:
                break
        return extras

    def _fallback_retrieval_query(self, question: str, claim: str, used_query: str) -> str | None:
        """Claim-focused query used only when the first pass has no on-topic hit."""
        base = factual_question(question)
        extras = self._claim_focus_terms(claim, base)
        # Preserve paired values such as 11-5 as one retrieval token; a
        # split query for 11 5 loses the meaning of a win-loss record.
        for quantity in extract_quantities(claim):
            if quantity["kind"] == "record" and quantity["raw"] not in extras:
                extras.append(quantity["raw"])
        # Month names in date claims are useful retrieval anchors but are not
        # capitalized names in every claim template (for example, "14 August").
        for month in re.findall(r"\b[A-Za-z]+\b", claim):
            if month.lower() in _MONTHS and month.lower() not in content_terms(base):
                if month not in extras:
                    extras.append(month)
        if not extras:
            return None
        focused = f"{base} {' '.join(extras)}"
        return None if focused == used_query else focused

    @staticmethod
    def _candidate_key(row: dict) -> tuple:
        return (
            row.get("source_id")
            or row.get("article_key")
            or row.get("url")
            or row.get("title"),
            row.get("chunk_id"),
        )

    def _build_pipeline_trace(
        self,
        retrieved: list[dict],
        kept: list[dict],
        on_topic: list[tuple[dict, list[str], dict]],
        discarded: list[dict],
    ) -> list[dict]:
        """Per-candidate retrieval and relevance stages for one claim."""
        kept_keys = {self._candidate_key(row) for row in kept}
        on_keys = {self._candidate_key(row) for row, _, _ in on_topic}
        discard_codes = {
            row.get("source_id") or row.get("title"): row.get("discard_code")
            for row in discarded
        }
        trace: list[dict] = []
        seen: set[tuple] = set()
        for row in retrieved:
            key = self._candidate_key(row)
            if key in seen:
                continue
            seen.add(key)
            source_id = row.get("source_id")
            trace.append(
                {
                    **self.source_ref(row),
                    "title": row.get("title"),
                    "chunk_id": row.get("chunk_id"),
                    "retrieval_score": float(row["score"]),
                    "passed_select_relevant": key in kept_keys,
                    "passed_on_topic": key in on_keys,
                    "nli_executed": key in on_keys,
                    "discard_code": discard_codes.get(source_id or row.get("title")),
                }
            )
        return trace

    def _merge_retrieved(self, *groups: list[dict]) -> list[dict]:
        """Deduplicate public retrieve() rows by source, keeping the higher cosine."""
        best: dict[tuple, dict] = {}
        for rows in groups:
            for row in rows:
                key = self._candidate_key(row)
                current = best.get(key)
                if current is None or float(row["score"]) > float(current["score"]):
                    best[key] = row
        return sorted(best.values(), key=lambda row: float(row["score"]), reverse=True)

    # ------------------------------------------------------------------
    # Relevance and aggregation
    # ------------------------------------------------------------------

    @staticmethod
    def _essential_question_names(
        question: str, entity: str | None, event_terms: set[str]
    ) -> list[str]:
        """Distinctive names that identify the subject, not every capitalized word."""
        fq = factual_question(question)
        names: list[str] = []
        seen: set[str] = set()
        for phrase in re.findall(
            r"\b[A-Z][a-z]+(?:\s+(?:[A-Z][a-z]+|[A-Z][A-Za-z'-]+))+|\b[A-Z][a-z]{4,}\b",
            fq,
        ):
            key = phrase.lower()
            if key in seen or key in _GENERIC_PROPER:
                continue
            parts = phrase.split()
            if len(parts) >= 2 or key in event_terms:
                names.append(phrase if len(parts) >= 2 else parts[0])
                seen.add(key)
        if entity and len(entity.split()) <= 5 and not any(ch.isdigit() for ch in entity):
            for word in entity.split():
                if word[:1].isupper() and word.lower() not in _GENERIC_PROPER:
                    token = word.lower()
                    if token not in seen:
                        names.append(word)
                        seen.add(token)
        return names

    @staticmethod
    def _event_identifier_ok(
        topic: dict, question_years: set[str], title: str, article_text: str
    ) -> bool:
        """True when event years need not appear in the selected premise windows."""
        if not question_years:
            return True
        if topic.get("event_consistent"):
            return True
        identifiers = content_terms(f"{title} {article_text}")
        if question_years & identifiers:
            return True
        return not topic.get("missing_event_identifiers")

    def _topic_gate_passes(self, topic: dict, question_years: set[str]) -> bool:
        """Lexical coverage is one signal; strong subject evidence can compensate."""
        if topic["topic_coverage"] >= self.min_topic_coverage:
            return True
        if question_years and topic.get("title_covers_event"):
            return True
        basis = topic.get("eligibility_basis")
        if basis in ("lexical_subject", "article_title", "article_text"):
            return bool(topic.get("about_subject"))
        if basis == "semantic_relevance" and topic.get("event_consistent"):
            return topic["topic_coverage"] >= max(0.35, self.min_topic_coverage - 0.15)
        return False

    def select_relevant(self, retrieved: list[dict]) -> list[dict]:
        """Keep dense hits above the floor, plus keyword hits for the topic gate.

        The cosine floor and margin are unchanged. A ``lexical_hit`` is also
        kept when the best embedding score never reaches the floor, so a
        passage the keyword index found is still judged by topic coverage
        and, if it passes, by NLI. Hits without ``lexical_hit`` follow the
        cosine rule only.
        """
        if not retrieved:
            return []
        best = max(item["score"] for item in retrieved)
        if best >= self.min_retrieval_score:
            cutoff = best - self.retrieval_margin
            dense = [item for item in retrieved if item["score"] >= cutoff]
        else:
            dense = []
        seen = {id(item) for item in dense}
        lexical = [
            item
            for item in retrieved
            if item.get("lexical_hit") and id(item) not in seen
        ]
        return dense + lexical

    def anchor_weights(self, question: str, claim: str, template: str) -> dict[str, float]:
        """IDF-weighted subject terms the evidence must be about.

        A claim built from a question template contains the answer under
        test, so its anchors are the question's terms. A sentence claim
        (from a multi-sentence answer) may be about something the question
        does not name ("It lies on the Seine."), so its own terms are used.
        """
        source = claim if template == SENTENCE_TEMPLATE else factual_question(question)
        terms = content_terms(source) or content_terms(claim)
        weigh = getattr(self.retriever, "term_weights", None)
        if weigh is None:
            return {term: 1.0 for term in terms}
        weights = dict(weigh(terms))
        # A term missing from every chunk cannot be covered. Count it anyway,
        # at the IDF it would have with document frequency 0, so a chunk that
        # only shares the remaining common words does not look on-topic.
        chunks = getattr(self.retriever, "chunks", None)
        if chunks is not None:
            absent = math.log(1 + max(len(chunks), 1))
            for term in terms:
                weights.setdefault(term, absent)
        return weights

    @staticmethod
    def topic_coverage(
        anchors: dict[str, float], required_numbers: set[str], evidence: dict, premise: str
    ) -> dict:
        """Coverage of the anchors by the chunk title + text, and required numbers it lacks."""
        present = content_terms(f"{evidence.get('title', '')} {premise}")
        total = sum(anchors.values())
        covered = sum(weight for term, weight in anchors.items() if term in present)
        return {
            "topic_coverage": covered / total if total > 0 else 1.0,
            "missing_anchor_terms": sorted(term for term in anchors if term not in present),
            "missing_numbers": sorted(term for term in required_numbers if term not in present),
        }

    def _assess_relevance(
        self,
        question: str,
        claim: str,
        evidence: dict,
        premise: list[str],
        template: str,
        anchors: dict[str, float],
        required_numbers: set[str],
        subject_terms: set[str],
        relation_terms: set[str],
        entity: str | None,
        question_years: set[str],
        event_terms: set[str],
    ) -> dict:
        """Independent relevance of one chunk. Does not read NLI outputs."""
        topic = self.topic_coverage(
            anchors, required_numbers, evidence, evidence.get("text", "")
        )
        title = str(evidence.get("title") or "").strip()
        prefix = f"{title}. " if title else ""
        bare_windows = [
            window[len(prefix) :] if prefix and window.startswith(prefix) else window
            for window in premise
        ]
        local_present = content_terms(f"{title} {' '.join(premise)}")
        identifier_terms = content_terms(f"{title} {evidence.get('text', '')}")
        topic["missing_numbers"] = sorted(
            term for term in required_numbers if term not in local_present
        )
        topic["missing_event_identifiers"] = sorted(
            term for term in required_numbers if term not in identifier_terms
        )
        local_sentences = [
            sentence.strip()
            for window in bare_windows
            for sentence in _SENTENCE_BOUNDARY.split(window)
            if sentence.strip()
        ]
        local_text = " ".join(bare_windows)
        local_terms = content_terms(local_text)
        article_text = f"{title} {evidence.get('text', '')}"
        lexical_subject = any(
            self.contains_unmodified_entity(sentence, entity)
            and (
                (bool(relation_terms) and relation_terms <= content_terms(sentence))
                or self.is_about_subject(
                    {**evidence, "title": "", "text": sentence}, subject_terms
                )
            )
            for sentence in local_sentences
        )
        if entity:
            if template == "capital":
                entity_present = self.contains_unmodified_entity(article_text, entity)
            else:
                entity_present = self.contains_unmodified_entity(
                    article_text, entity
                ) or bool(
                    re.search(
                        rf"\b{re.escape(entity)}\b", article_text, re.IGNORECASE
                    )
                )
        else:
            entity_present = True
        title_covers_event = bool(question_years) and self._title_covers_event(
            title, question_years, event_terms
        )
        article_terms = content_terms(article_text)
        article_covers_event = bool(event_terms) and self._term_overlap(
            event_terms, article_terms
        ) >= max(1, (len(event_terms) + 1) // 2)
        essential_names = self._essential_question_names(question, entity, event_terms)
        if essential_names and article_covers_event:
            article_covers_event = all(
                re.search(rf"\b{re.escape(name)}\b", article_text, re.IGNORECASE)
                for name in essential_names
            )
        if entity and article_covers_event:
            article_covers_event = self.contains_unmodified_entity(article_text, entity)
        year_mismatch = self._title_names_other_event(
            title, question, question_years, event_terms
        )
        local_covers_event = (not question_years) or self._local_covers_event(
            title, local_sentences, question_years, event_terms
        )
        condition_mismatch = self._conditions_conflict(question, title, local_text)
        semantic_subject = (
            not year_mismatch
            and not condition_mismatch
            and float(evidence["score"]) >= self.min_retrieval_score
            and topic["topic_coverage"] >= self.min_topic_coverage
            and entity_present
        )
        about_subject = (
            not year_mismatch
            and not condition_mismatch
            and (
                lexical_subject
                or semantic_subject
                or title_covers_event
                or article_covers_event
            )
        )
        if (
            question_years
            and not local_covers_event
            and not title_covers_event
            and not article_covers_event
        ):
            about_subject = False
        if (
            about_subject
            and essential_names
            and not lexical_subject
            and not all(
                re.search(rf"\b{re.escape(name)}\b", article_text, re.IGNORECASE)
                for name in essential_names
            )
        ):
            about_subject = False
        if about_subject and lexical_subject:
            basis = "lexical_subject"
        elif about_subject and semantic_subject:
            basis = "semantic_relevance"
        elif about_subject and title_covers_event:
            basis = "article_title"
        elif about_subject and article_covers_event:
            basis = "article_text"
        else:
            basis = None
        topic.update(
            {
                "about_subject": about_subject,
                "title_covers_event": title_covers_event,
                "article_covers_event": article_covers_event,
                "entity_consistent": entity_present,
                "event_consistent": (
                    (not question_years)
                    or local_covers_event
                    or title_covers_event
                    or article_covers_event
                ),
                "condition_consistent": not condition_mismatch,
                "eligibility_basis": basis,
            }
        )
        return topic

    def select_on_topic(
        self, question: str, claim: str, kept: list[dict], template: str = ""
    ) -> tuple[list[tuple[dict, list[str], dict]], list[dict]]:
        """Split kept chunks into (on-topic (evidence, premises, topic), discarded briefs).

        Relevance is computed before NLI. Only numbers from the question are
        required: a number in the answer is a value under test, and evidence
        with a different value must still reach NLI to be able to contradict it.
        """
        anchors = self.anchor_weights(question, claim, template)
        subject_terms = content_terms(
            claim if template == SENTENCE_TEMPLATE else factual_question(question)
        )
        relation_terms, entity = self.relation_entity_terms(question, template)
        required_numbers = {
            term for term in content_terms(factual_question(question)) if term.isdigit()
        } & set(anchors)
        question_years = self._year_terms(factual_question(question))
        event_terms = self._event_terms(question)
        candidates = []
        for evidence in kept:
            premise = self.extract_premises(evidence, claim, question)
            topic = self._assess_relevance(
                question,
                claim,
                evidence,
                premise,
                template,
                anchors,
                required_numbers,
                subject_terms,
                relation_terms,
                entity,
                question_years,
                event_terms,
            )
            candidates.append((evidence, premise, topic))

        passing = []
        for evidence, premise, topic in candidates:
            article_text = str(evidence.get("text") or "")
            title = str(evidence.get("title") or "")
            if not topic["about_subject"]:
                continue
            if not self._event_identifier_ok(topic, question_years, title, article_text):
                continue
            if not self._topic_gate_passes(topic, question_years):
                continue
            topic["discard_code"] = DISCARD_CANDIDATE_FOR_NLI
            passing.append((evidence, premise, topic))
        best = max((c[2]["topic_coverage"] for c in passing), default=0.0)
        on_topic = []
        for candidate in passing:
            coverage = candidate[2]["topic_coverage"]
            if (
                coverage >= best - self.topic_margin
                or (question_years and candidate[2].get("title_covers_event"))
            ):
                on_topic.append(candidate)

        discarded = []
        for evidence, _, topic in candidates:
            if any(evidence is kept_evidence for kept_evidence, _, _ in on_topic):
                continue
            title = str(evidence.get("title") or "")
            article_text = str(evidence.get("text") or "")
            reason, discard_code = self._discard_reason(
                topic, best, question_years, title, article_text
            )
            discarded.append(
                {
                    "title": evidence.get("title"),
                    "chunk_id": evidence.get("chunk_id"),
                    "url": evidence.get("url"),
                    **self.source_ref(evidence),
                    "retrieval_score": float(evidence["score"]),
                    **topic,
                    "reason": reason,
                    "discard_code": discard_code,
                }
            )
        return on_topic, discarded

    def _discard_reason(
        self,
        topic: dict,
        best: float,
        question_years: set[str],
        title: str,
        article_text: str,
    ) -> tuple[str, str]:
        """Return (human-readable reason, machine-readable discard_code)."""
        if not topic.get("about_subject", True):
            return OFF_SUBJECT_REASON, DISCARD_OFF_SUBJECT
        if not self._event_identifier_ok(
            topic, question_years, title, article_text
        ) and topic.get("missing_event_identifiers"):
            missing = ", ".join(topic["missing_event_identifiers"])
            return (
                f"missing event identifier(s) from the question: {missing}",
                DISCARD_MISSING_EVENT_ID,
            )
        if not self._topic_gate_passes(topic, question_years):
            return (
                f"topic coverage {topic['topic_coverage']:.2f} below "
                f"{self.min_topic_coverage:.2f}",
                DISCARD_INSUFFICIENT_TOPIC,
            )
        return (
            f"topic coverage {topic['topic_coverage']:.2f} more than "
            f"{self.topic_margin:.2f} below best {best:.2f}",
            DISCARD_TOPIC_MARGIN,
        )

    def _strong(self, rows: list[dict], label: str) -> list[dict]:
        return [
            row
            for row in rows
            if row["nli_label"] == label and row["probabilities"].get(label, 0.0) >= self.min_nli_score
        ]

    @staticmethod
    def _article_key(row: dict) -> Any:
        return row.get("url") or row.get("title")

    @staticmethod
    def _row_is_relevant(row: dict) -> bool:
        """Relevance flag set before NLI. An NLI label never fills this in."""
        return bool(row.get("about_subject"))

    def _ignored_nli(self, row: dict, reason: str) -> dict:
        """Diagnostic row that keeps the original NLI label and score."""
        return {**self._brief(row), "reason": reason, "about_subject": row.get("about_subject")}

    def _effective_signal(self, row: dict) -> str | None:
        """Map a relevant row to support, contradiction, or neither.

        An explicit same-property value match or mismatch is independent of
        NLI and is not a calibrated probability. NLI is used only when no
        reliable property-value pairing exists.
        """
        relation = row.get("value_relation")
        if relation == "mismatch":
            if (
                "record" in row.get("quantity_kinds", [])
                and not row.get("quantity_scope_aligned", True)
            ):
                return None
            return "contradiction"
        if relation == "match":
            return "entailment"
        # Numeric and temporal NLI labels are unsafe when the passage has no
        # same-property value association. Leave those cases unresolved.
        if {"date", "record"} & set(row.get("quantity_kinds", [])):
            return None
        if row["nli_label"] == "entailment" and row["probabilities"].get("entailment", 0.0) >= self.min_nli_score:
            if (
                row.get("claim_names_in_premise", True)
                and row.get("office_holder_consistent", True)
                and row.get("relation_aligned", True)
            ):
                return "entailment"
            return None
        if row["nli_label"] == "contradiction" and row["probabilities"].get("contradiction", 0.0) >= self.min_nli_score:
            return "contradiction"
        return None

    @staticmethod
    def _row_fact_score(row: dict) -> int:
        score = row.get("fact_score")
        if score is not None:
            return int(score)
        return int(row.get("match_score", 0))

    def _same_article_contradiction_discountable(
        self, row: dict, supporters: list[dict]
    ) -> bool:
        """True only when support plausibly concerns a different detail than ``row``."""
        if row.get("value_relation") == "mismatch":
            return False
        row_score = self._row_fact_score(row)
        for support in supporters:
            if support.get("value_relation") == "match":
                return True
            # When the NLI contradiction window does not express the asked
            # relation, a relation-aligned supporting passage from that same
            # article shows the contradiction concerned another fact.
            if not row.get("relation_aligned", True) and support.get("relation_aligned", True):
                return True
            # A window in the same article that states the claim's added
            # names while this contradiction omits them addresses the answer
            # directly; the other window concerns a different detail.
            if support.get("claim_names_in_premise") and not row.get("claim_names_in_premise"):
                return True
            support_score = self._row_fact_score(support)
            if support_score > row_score:
                return True
            if (
                support_score == row_score
                and row.get("value_relation") in {None, "none"}
                and support.get("nli_label") == "entailment"
                and support.get("probabilities", {}).get("entailment", 0.0)
                >= self.min_nli_score
                and support.get("claim_names_in_premise")
                and not row.get("claim_names_in_premise")
            ):
                return True
        return False

    def aggregate_chunks(self, rows: list[dict]) -> dict:
        """Per-claim decision from relevant rows only."""
        ignored_support: list[dict] = []
        ignored: list[dict] = []
        supporting: list[dict] = []
        contradicting: list[dict] = []
        for row in rows:
            signal = self._effective_signal(row)
            if signal == "entailment":
                if not self._row_is_relevant(row):
                    ignored_support.append(self._ignored_nli(row, OFF_SUBJECT_REASON))
                else:
                    supporting.append(row)
        for row in rows:
            signal = self._effective_signal(row)
            if signal != "contradiction":
                continue
            if not self._row_is_relevant(row):
                ignored.append(self._ignored_nli(row, OFF_SUBJECT_REASON))
                continue
            article_key = self._article_key(row)
            same_article = [
                support
                for support in supporting
                if self._article_key(support) == article_key
            ]
            if self._same_article_contradiction_discountable(row, same_article):
                ignored.append(self._ignored_nli(row, SAME_ARTICLE_REASON))
            else:
                contradicting.append(row)

        if supporting and contradicting:
            return {
                "decision": DECISION_UNSURE,
                "unsure_reason": "conflict",
                "confidence": 0.0,
                "deciding": None,
                "supporting": supporting,
                "contradicting": contradicting,
                "ignored_contradictions": ignored,
                "ignored_support": ignored_support,
            }
        if supporting:
            best = max(supporting, key=lambda row: row["probabilities"]["entailment"])
            return {
                "decision": DECISION_SUPPORT,
                "unsure_reason": None,
                "confidence": best["probabilities"]["entailment"],
                "deciding": best,
                "supporting": supporting,
                "contradicting": [],
                "ignored_contradictions": ignored,
                "ignored_support": ignored_support,
            }
        if contradicting:
            best = max(contradicting, key=lambda row: row["probabilities"]["contradiction"])
            return {
                "decision": DECISION_REJECT,
                "unsure_reason": None,
                "confidence": best["probabilities"]["contradiction"],
                "deciding": best,
                "supporting": [],
                "contradicting": contradicting,
                "ignored_contradictions": ignored,
                "ignored_support": ignored_support,
            }
        return {
            "decision": DECISION_UNSURE,
            "unsure_reason": "neutral",
            "confidence": 0.0,
            "deciding": None,
            "supporting": [],
            "contradicting": [],
            "ignored_contradictions": ignored,
            "ignored_support": ignored_support,
        }

    @staticmethod
    def aggregate_claims(claim_results: list[dict]) -> tuple[str, float, str | None, dict | None]:
        """Return (decision, confidence, unsure_reason, deciding claim result)."""
        if claim_results and all(c["decision"] == DECISION_SUPPORT for c in claim_results):
            weakest = min(claim_results, key=lambda c: c["confidence"])
            return DECISION_SUPPORT, weakest["confidence"], None, weakest

        rejections = [c for c in claim_results if c["decision"] == DECISION_REJECT]
        if rejections:
            strongest = max(rejections, key=lambda c: c["confidence"])
            return DECISION_REJECT, strongest["confidence"], None, strongest

        reasons = {c["unsure_reason"] for c in claim_results if c["decision"] == DECISION_UNSURE}
        if any(c["decision"] == DECISION_SUPPORT for c in claim_results):
            reason = "partial_support"
        elif reasons == {"no_relevant_evidence"}:
            reason = "no_relevant_evidence"
        elif "conflict" in reasons:
            reason = "conflict"
        else:
            reason = "neutral"
        return DECISION_UNSURE, 0.0, reason, None

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        start = time.perf_counter()
        retrieval_ms = 0.0
        nli_ms = 0.0

        claims = self.claim_generator.generate_claims(question, answer)
        claim_results: list[dict] = []
        any_retrieved = False

        for position, item in enumerate(claims):
            claim = item.get("hypothesis") or item["claim"]
            claim = self._contextualize_claim(
                question, answer, claim, item["template"]
            )
            query = self._retrieval_query(question, claim, item["template"])

            t0 = time.perf_counter()
            retrieved = self.retriever.retrieve(query, k=self.top_k)
            retrieval_ms += (time.perf_counter() - t0) * 1000
            any_retrieved = any_retrieved or bool(retrieved)

            best_score = max((r["score"] for r in retrieved), default=None)
            kept = self.select_relevant(retrieved)
            on_topic, discarded = (
                self.select_on_topic(question, claim, kept, item["template"]) if kept else ([], [])
            )
            candidate_pipeline = self._build_pipeline_trace(
                retrieved, kept, on_topic, discarded
            )
            fallback = self._fallback_retrieval_query(question, claim, query)
            answer_anchors = set(self._claim_focus_terms(claim, factual_question(question)))
            answer_anchors.update(
                month.lower()
                for month in re.findall(r"\b[A-Za-z]+\b", claim)
                if month.lower() in _MONTHS
                and month.lower() not in content_terms(factual_question(question))
            )
            anchor_missing = bool(answer_anchors) and not any(
                answer_anchors <= premise_terms(" ".join(premises))
                for _, premises, _ in on_topic
            )
            needs_answer_focused_search = (
                item["template"] != "who" and anchor_missing
            )
            if (not on_topic or needs_answer_focused_search) and fallback:
                t0 = time.perf_counter()
                extra = self.retriever.retrieve(fallback, k=self.top_k)
                retrieval_ms += (time.perf_counter() - t0) * 1000
                # Band each retrieve() call on its own scores so a stronger
                # off-topic first pass cannot drop a weaker on-topic fallback.
                extra_kept = self.select_relevant(extra)
                retrieved = self._merge_retrieved(retrieved, extra)
                kept = self._merge_retrieved(kept, extra_kept)
                any_retrieved = any_retrieved or bool(retrieved)
                best_score = max((r["score"] for r in retrieved), default=None)
                on_topic, discarded = (
                    self.select_on_topic(question, claim, kept, item["template"])
                    if kept
                    else ([], [])
                )
                candidate_pipeline = self._build_pipeline_trace(
                    retrieved, kept, on_topic, discarded
                )
            if not on_topic:
                claim_results.append(
                    {
                        "index": position,
                        "claim": item["claim"],
                        "hypothesis": claim,
                        "template": item["template"],
                        "decision": DECISION_UNSURE,
                        "unsure_reason": "no_relevant_evidence",
                        "confidence": 0.0,
                        "best_retrieval_score": best_score,
                        "deciding": None,
                        "supporting": [],
                        "contradicting": [],
                        "ignored_contradictions": [],
                        "ignored_support": [],
                        "evidence": [],
                        "discarded": discarded,
                        "candidate_pipeline": candidate_pipeline,
                        "retrieved_count": len(retrieved),
                    }
                )
                continue

            t0 = time.perf_counter()
            rows = [
                {
                    **self.score_evidence(
                        evidence, claim, premise, question=question, template=item["template"]
                    ),
                    **topic,
                }
                for evidence, premise, topic in on_topic
            ]
            nli_ms += (time.perf_counter() - t0) * 1000

            aggregated = self.aggregate_chunks(rows)
            aggregated.update(
                {
                    "index": position,
                    "claim": item["claim"],
                    "hypothesis": claim,
                    "template": item["template"],
                    "best_retrieval_score": best_score,
                    "evidence": rows,
                    "discarded": discarded,
                    "candidate_pipeline": candidate_pipeline,
                    "retrieved_count": len(retrieved),
                }
            )
            claim_results.append(aggregated)

        decision, confidence, unsure_reason, deciding_claim = self.aggregate_claims(claim_results)
        total_ms = (time.perf_counter() - start) * 1000
        return self._build_result(
            decision=decision,
            confidence=confidence,
            unsure_reason=unsure_reason,
            deciding_claim=deciding_claim,
            claim_results=claim_results,
            any_retrieved=any_retrieved,
            latency={"retrieval": retrieval_ms, "nli": nli_ms, "total": total_ms},
        )

    def _build_result(
        self,
        *,
        decision: str,
        confidence: float,
        unsure_reason: str | None,
        deciding_claim: dict | None,
        claim_results: list[dict],
        any_retrieved: bool,
        latency: dict[str, float],
    ) -> VerificationResult:
        evaluated_evidence = [
            {"claim_index": c["index"], "claim_id": self.claim_id(c["index"]), **row}
            for c in claim_results
            for row in c["evidence"]
        ]
        evidence_evaluated = bool(evaluated_evidence)

        if decision == DECISION_SUPPORT:
            nli_label, passed = "entailment", True
        elif decision == DECISION_REJECT:
            nli_label, passed = "contradiction", False
        elif evidence_evaluated:
            nli_label, passed = "neutral", False
        else:
            nli_label, passed = None, False

        deciding_row = deciding_claim["deciding"] if deciding_claim else None
        unchecked = [c["claim"] for c in claim_results if c["unsure_reason"] == "no_relevant_evidence"]
        reasoning = self._reasoning(decision, unsure_reason, deciding_claim, claim_results, any_retrieved)

        metadata = {
            "decision": decision,
            "score_meaning": self.SCORE_MEANING,
            "nli_label": nli_label,
            "nli_model": self.NLI_MODEL,
            "nli_output_shape": evaluated_evidence[0]["nli_output_shape"] if evaluated_evidence else None,
            "unsure_reason": unsure_reason,
            "top_k": self.top_k,
            "min_retrieval_score": self.min_retrieval_score,
            "retrieval_margin": self.retrieval_margin,
            "min_nli_score": self.min_nli_score,
            "min_topic_coverage": self.min_topic_coverage,
            "topic_margin": self.topic_margin,
            "max_premise_windows": self.max_premise_windows,
            "thresholds_calibrated": False,
            "corpus_version": getattr(self.retriever, "corpus_version", None),
            "index_version": getattr(self.retriever, "index_version", None),
            "claims": [c["claim"] for c in claim_results],
            "claim_decisions": [self._claim_decision(c) for c in claim_results],
            "unchecked_claims": unchecked,
            "supporting": [
                {**self._claim_tag(c), **self._brief(r)} for c in claim_results for r in c["supporting"]
            ],
            "contradicting": [
                {**self._claim_tag(c), **self._brief(r)} for c in claim_results for r in c["contradicting"]
            ],
            "ignored_contradictions": [
                {**self._claim_tag(c), **row}
                for c in claim_results
                for row in c.get("ignored_contradictions", [])
            ],
            "ignored_support": [
                {**self._claim_tag(c), **row}
                for c in claim_results
                for row in c.get("ignored_support", [])
            ],
            "evaluated_evidence": evaluated_evidence,
            "discarded_evidence": [
                {**self._claim_tag(c), **row} for c in claim_results for row in c["discarded"]
            ],
            "candidate_pipeline": [
                {**self._claim_tag(c), **row}
                for c in claim_results
                for row in c.get("candidate_pipeline", [])
            ],
            "retrieved_counts": [
                {
                    **self._claim_tag(c),
                    "retrieved_count": c.get("retrieved_count", 0),
                }
                for c in claim_results
            ],
            "deciding_claim_id": self.claim_id(deciding_claim["index"]) if deciding_claim else None,
            "evidence_source_id": deciding_row.get("source_id") if deciding_row else None,
            "evidence_title": deciding_row["title"] if deciding_row else None,
            "evidence_chunk_id": deciding_row["chunk_id"] if deciding_row else None,
            "retrieval_score": deciding_row["retrieval_score"] if deciding_row else None,
            "best_retrieval_score": max(
                (c["best_retrieval_score"] for c in claim_results if c["best_retrieval_score"] is not None),
                default=None,
            ),
            "latency_ms": round(latency["total"], 2),
            "latency_breakdown_ms": {k: round(v, 2) for k, v in latency.items()},
        }
        return VerificationResult(
            verifier_name=self.name,
            score=min(max(float(confidence), 0.0), 1.0),
            passed=passed,
            reasoning=reasoning,
            metadata=metadata,
        )

    @staticmethod
    def claim_id(index: int) -> str:
        """Identifier of the claim at ``index`` within one verify() result."""
        return f"claim-{index}"

    def _claim_tag(self, claim_result: dict) -> dict:
        return {"claim_index": claim_result["index"], "claim_id": self.claim_id(claim_result["index"])}

    def _claim_decision(self, c: dict) -> dict:
        """One claim's decision with the source_ids of the evidence behind it.

        ``evidence_refs`` lists every evidence row this claim's decision was
        made from or set aside, by role; ``deciding_source_id`` is the row
        that set the claim's confidence (None when the claim is UNSURE).
        """

        def ids(rows: list[dict]) -> list:
            return [row.get("source_id") for row in rows]

        deciding = c.get("deciding")
        return {
            **self._claim_tag(c),
            "claim": c["claim"],
            "hypothesis": c.get("hypothesis", c["claim"]),
            "template": c["template"],
            "decision": c["decision"],
            "confidence": c["confidence"],
            "unsure_reason": c["unsure_reason"],
            "best_retrieval_score": c["best_retrieval_score"],
            "deciding_source_id": deciding.get("source_id") if deciding else None,
            "evidence_refs": {
                "supporting": ids(c.get("supporting", [])),
                "contradicting": ids(c.get("contradicting", [])),
                "ignored_contradictions": ids(c.get("ignored_contradictions", [])),
                "ignored_support": ids(c.get("ignored_support", [])),
                "evaluated": ids(c.get("evidence", [])),
                "discarded": ids(c.get("discarded", [])),
            },
        }

    @staticmethod
    def _brief(row: dict) -> dict:
        return {
            "title": row["title"],
            "chunk_id": row["chunk_id"],
            "url": row.get("url"),
            **EvidenceVerifier.source_ref(row),
            "retrieval_score": row["retrieval_score"],
            "topic_coverage": row.get("topic_coverage"),
            "nli_label": row["nli_label"],
            "nli_score": row["nli_score"],
            "excerpt": row["relevant_evidence"][:300],
        }

    @staticmethod
    def _reasoning(
        decision: str,
        unsure_reason: str | None,
        deciding_claim: dict | None,
        claim_results: list[dict],
        any_retrieved: bool,
    ) -> str:
        n = len(claim_results)
        if decision == DECISION_SUPPORT:
            row = deciding_claim["deciding"]
            return (
                f"NLI result: entailment. Retrieved evidence entails "
                f"{'the claim' if n == 1 else f'all {n} claims'}. "
                f"Evidence: {row['title']}. Claim: {deciding_claim['claim']} "
                f"NLI confidence: {row['probabilities']['entailment']:.4f}."
            )
        if decision == DECISION_REJECT:
            row = deciding_claim["deciding"]
            return (
                f"NLI result: contradiction. Retrieved evidence contradicts the claim. "
                f"Evidence: {row['title']}. Claim: {deciding_claim['claim']} "
                f"NLI confidence: {row['probabilities']['contradiction']:.4f}."
            )
        if unsure_reason == "no_relevant_evidence":
            return NO_RELEVANT_EVIDENCE_REASON if any_retrieved else NO_EVIDENCE_REASON
        if unsure_reason == "conflict":
            return (
                "NLI result: neutral (conflict). Retrieved evidence both entails and "
                "contradicts the claim; see supporting and contradicting in metadata."
            )
        if unsure_reason == "partial_support":
            unchecked = [c["claim"] for c in claim_results if c["decision"] != DECISION_SUPPORT]
            return (
                "NLI result: neutral (partial support). Some claims are entailed, but "
                f"{len(unchecked)} of {n} could not be established: {' | '.join(unchecked)}"
            )
        return "NLI result: neutral. Retrieved evidence neither entails nor contradicts the claim."
