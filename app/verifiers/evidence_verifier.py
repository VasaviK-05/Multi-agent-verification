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

Premises
    A chunk of up to ``LEGACY_PREMISE_SENTENCES`` sentences is one premise
    (its best-overlapping sentences). A longer chunk is checked through up
    to two windows for each of the ``max_premise_windows`` sentences that
    best match the claim: the sentence with the one before it and with the
    one after it, prefixed with the article title so "It" and "The match"
    resolve. Matching (``match_score``) ignores the title's own words, keeps
    decimals whole ("7.7" is not "7.1") and weighs numbers double, so the
    window chosen for "...was 12 May 2010" is the sentence that has a date,
    not the opening sentence that repeats the title. A wider window is not
    used: extra sentences turn a clear entailment into a contradiction.
    An entailment that holds only with the title prefix is replaced by the
    bare window's result when the bare window contradicts: the prefix has
    then attached the title to a different referent ("This earthquake
    occurred near ... the magnitude 9.1 earthquake of 1877"). Within one
    chunk an entailing window decides; otherwise the strongest
    contradicting window; otherwise the most entailing one. Every window is
    kept in ``premise_windows``.

Per-claim aggregation (issue 5)
    A chunk is a strong entailment / contradiction when that class is the
    argmax and its probability is >= ``min_nli_score``. A contradiction is
    discounted (listed in ``ignored_contradictions``, never silently) when
        the article's title is not about the question: it has content
        words that occur in neither the question nor the answer (a song
        called "(Just Like) Romeo and Juliet", a "2012-13" season for a
        2010 question, "African coral reefs" for boiling water). NLI reads
        a passage about a different subject as a confident contradiction;
        an entailment from such a passage still counts, because a passage
        that states the claim states it whatever its main subject is.
        another chunk of the same article strongly entails the claim with
        a higher ``match_score``. An article does not contradict itself;
        the less matching chunk is about a different detail (a referee's
        other match, a trophy ceremony). With equal match the two passages
        are a real conflict and both count.
    Then:
        strong entailment and strong contradiction -> UNSURE (conflict)
        strong entailment only                      -> SUPPORT
        strong contradiction only                   -> REJECT
        neither                                     -> UNSURE (neutral)
    Conflicts are reported, not resolved by picking the favourable side.

Across claims (issue 7)
    all SUPPORT -> SUPPORT (confidence = weakest claim)
    any REJECT  -> REJECT  (confidence = strongest rejection)
    otherwise   -> UNSURE  (partial support / unchecked claims listed)

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
from app.verifiers.claim_generator import SENTENCE_TEMPLATE, ClaimGenerator, factual_question
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

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_PREMISE_TERM = re.compile(r"\d+(?:[.,]\d+)*|[^\W\d_]+")


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

    def extract_relevant_sentences(self, text: str, claim: str, max_sentences: int = 3) -> str:
        """Pick the chunk sentences with most word overlap with the claim.

        Chunks can exceed the NLI model's input length; this keeps the
        premise short and on-topic. Falls back to the chunk head when no
        sentence shares a word with the claim.
        """
        sentences = re.split(r"(?<=[.!?])\s+", text)
        claim_words = {w.lower() for w in re.findall(r"\b\w+\b", claim)}

        scored = []
        for sentence in sentences:
            words = {w.lower() for w in re.findall(r"\b\w+\b", sentence)}
            overlap = len(claim_words & words)
            if overlap > 0:
                scored.append((overlap, sentence.strip()))
        scored.sort(key=lambda item: item[0], reverse=True)
        selected = [sentence for _, sentence in scored[:max_sentences]]
        return " ".join(selected) if selected else text[:1500]

    def extract_premises(self, evidence: dict, claim: str) -> list[str]:
        """NLI premises for one chunk: one for a short chunk, windows for a long one."""
        text = str(evidence.get("text", ""))
        sentences = [s.strip() for s in _SENTENCE_BOUNDARY.split(text) if s.strip()]
        if len(sentences) <= self.LEGACY_PREMISE_SENTENCES:
            return [self.extract_relevant_sentences(text, claim)]

        title = str(evidence.get("title") or "").strip()
        scored = []
        for position, sentence in enumerate(sentences):
            score = self.match_score(claim, title, sentence)
            if score:
                scored.append((score, -position, position))
        if not scored:
            return [self.extract_relevant_sentences(text, claim)]
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
        self, evidence: dict, claim: str, premise: str | list[str] | None = None
    ) -> dict:
        """Run NLI for one chunk/claim pair and return a flat evidence row.

        ``premise`` may be one premise or several windows of the chunk; see
        the module docstring for how a window is chosen.
        """
        if premise is None:
            premises = self.extract_premises(evidence, claim)
        elif isinstance(premise, str):
            premises = [premise]
        else:
            premises = list(premise) or [self.extract_relevant_sentences(evidence["text"], claim)]

        title = str(evidence.get("title") or "").strip()
        prefix = f"{title}. " if title else ""
        windows = []
        for text in premises:
            window = self._nli_window(text, claim)
            if prefix and text.startswith(prefix) and self._is_strong(window, "entailment"):
                bare = self._nli_window(text[len(prefix) :], claim)
                if self._is_strong(bare, "contradiction"):
                    window = {**bare, "premise": text, "title_dependent": True}
            windows.append(window)
        chosen = self._choose_window(windows)
        label = chosen["nli_label"]
        body = chosen["premise"][len(prefix) :] if prefix and chosen["premise"].startswith(prefix) else chosen["premise"]
        return {
            "title": evidence.get("title"),
            "chunk_id": evidence.get("chunk_id"),
            "url": evidence.get("url"),
            "retrieval_score": float(evidence["score"]),
            "relevant_evidence": chosen["premise"],
            "match_score": self.match_score(claim, title, body),
            "nli_label": label,
            "nli_score": chosen["probabilities"][label],
            "probabilities": chosen["probabilities"],
            "nli_output_shape": chosen["nli_output_shape"],
            "premise_windows": [
                {
                    "premise": w["premise"],
                    "nli_label": w["nli_label"],
                    "probabilities": w["probabilities"],
                    "title_dependent": w.get("title_dependent", False),
                }
                for w in windows
            ],
        }

    def _nli_window(self, premise: str, claim: str) -> dict:
        probabilities, shape = parse_nli_output(self.nli({"text": premise, "text_pair": claim}))
        return {
            "premise": premise,
            "nli_label": max(probabilities, key=probabilities.get),
            "probabilities": probabilities,
            "nli_output_shape": shape,
        }

    def _is_strong(self, window: dict, label: str) -> bool:
        return window["nli_label"] == label and window["probabilities"].get(label, 0.0) >= self.min_nli_score

    def _choose_window(self, windows: list[dict]) -> dict:
        entailing = [w for w in windows if self._is_strong(w, "entailment")]
        if entailing:
            return max(entailing, key=lambda w: w["probabilities"]["entailment"])
        contradicting = [w for w in windows if self._is_strong(w, "contradiction")]
        if contradicting:
            return max(contradicting, key=lambda w: w["probabilities"]["contradiction"])
        return max(windows, key=lambda w: w["probabilities"].get("entailment", 0.0))

    @staticmethod
    def is_about_subject(evidence: dict, subject_terms: set[str]) -> bool:
        """True when every content word of the article title occurs in the question or answer.

        A title with no content words gives no signal and counts as on subject.
        """
        title_terms = content_terms(evidence.get("title") or "")
        return not title_terms or title_terms <= subject_terms

    # ------------------------------------------------------------------
    # Relevance and aggregation
    # ------------------------------------------------------------------

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

    def select_on_topic(
        self, question: str, claim: str, kept: list[dict], template: str = ""
    ) -> tuple[list[tuple[dict, list[str], dict]], list[dict]]:
        """Split kept chunks into (on-topic (evidence, premises, topic), discarded briefs).

        Only numbers from the question are required: a number in the answer
        is a value under test, and evidence with a different value must
        still reach NLI to be able to contradict it.
        """
        anchors = self.anchor_weights(question, claim, template)
        required_numbers = {
            term for term in content_terms(factual_question(question)) if term.isdigit()
        } & set(anchors)
        candidates = []
        for evidence in kept:
            premise = self.extract_premises(evidence, claim)
            topic = self.topic_coverage(
                anchors, required_numbers, evidence, evidence.get("text", "")
            )
            candidates.append((evidence, premise, topic))

        passing = [
            c for c in candidates
            if not c[2]["missing_numbers"] and c[2]["topic_coverage"] >= self.min_topic_coverage
        ]
        best = max((c[2]["topic_coverage"] for c in passing), default=0.0)
        on_topic = [c for c in passing if c[2]["topic_coverage"] >= best - self.topic_margin]

        discarded = [
            {
                "title": evidence.get("title"),
                "chunk_id": evidence.get("chunk_id"),
                "retrieval_score": float(evidence["score"]),
                **topic,
                "reason": self._discard_reason(topic, best),
            }
            for evidence, _, topic in candidates
            if not any(evidence is kept_evidence for kept_evidence, _, _ in on_topic)
        ]
        return on_topic, discarded

    def _discard_reason(self, topic: dict, best: float) -> str:
        if topic["missing_numbers"]:
            return f"missing number(s) from the question: {', '.join(topic['missing_numbers'])}"
        if topic["topic_coverage"] < self.min_topic_coverage:
            return f"topic coverage {topic['topic_coverage']:.2f} below {self.min_topic_coverage:.2f}"
        return f"topic coverage {topic['topic_coverage']:.2f} more than {self.topic_margin:.2f} below best {best:.2f}"

    def _strong(self, rows: list[dict], label: str) -> list[dict]:
        return [
            row
            for row in rows
            if row["nli_label"] == label and row["probabilities"].get(label, 0.0) >= self.min_nli_score
        ]

    @staticmethod
    def _article_key(row: dict) -> Any:
        return row.get("url") or row.get("title")

    def aggregate_chunks(self, rows: list[dict]) -> dict:
        """Per-claim decision from the NLI rows of its kept chunks."""
        supporting = self._strong(rows, "entailment")
        best_support_match: dict[Any, int] = {}
        for row in supporting:
            key = self._article_key(row)
            best_support_match[key] = max(best_support_match.get(key, -1), row.get("match_score", 0))
        contradicting: list[dict] = []
        ignored: list[dict] = []
        for row in self._strong(rows, "contradiction"):
            if not row.get("about_subject", True):
                ignored.append({**self._brief(row), "reason": OFF_SUBJECT_REASON})
            elif best_support_match.get(self._article_key(row), -1) > row.get("match_score", 0):
                ignored.append({**self._brief(row), "reason": SAME_ARTICLE_REASON})
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
            }
        return {
            "decision": DECISION_UNSURE,
            "unsure_reason": "neutral",
            "confidence": 0.0,
            "deciding": None,
            "supporting": [],
            "contradicting": [],
            "ignored_contradictions": ignored,
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
        subject_terms = content_terms(factual_question(question)) | content_terms(answer)

        for position, item in enumerate(claims):
            claim = item.get("hypothesis") or item["claim"]
            query = f"{factual_question(question)} {claim}"

            t0 = time.perf_counter()
            retrieved = self.retriever.retrieve(query, k=self.top_k)
            retrieval_ms += (time.perf_counter() - t0) * 1000
            any_retrieved = any_retrieved or bool(retrieved)

            best_score = max((r["score"] for r in retrieved), default=None)
            kept = self.select_relevant(retrieved)
            on_topic, discarded = (
                self.select_on_topic(question, claim, kept, item["template"]) if kept else ([], [])
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
                        "evidence": [],
                        "discarded": discarded,
                    }
                )
                continue

            t0 = time.perf_counter()
            rows = [
                {
                    **self.score_evidence(evidence, claim, premise),
                    **topic,
                    "about_subject": self.is_about_subject(evidence, subject_terms | content_terms(claim)),
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
            {"claim_index": c["index"], **{k: v for k, v in row.items()}}
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
            "claims": [c["claim"] for c in claim_results],
            "claim_decisions": [
                {
                    "claim": c["claim"],
                    "hypothesis": c.get("hypothesis", c["claim"]),
                    "template": c["template"],
                    "decision": c["decision"],
                    "confidence": c["confidence"],
                    "unsure_reason": c["unsure_reason"],
                    "best_retrieval_score": c["best_retrieval_score"],
                }
                for c in claim_results
            ],
            "unchecked_claims": unchecked,
            "supporting": [self._brief(r) for c in claim_results for r in c["supporting"]],
            "contradicting": [self._brief(r) for c in claim_results for r in c["contradicting"]],
            "ignored_contradictions": [
                {"claim_index": c["index"], **row}
                for c in claim_results
                for row in c.get("ignored_contradictions", [])
            ],
            "evaluated_evidence": evaluated_evidence,
            "discarded_evidence": [
                {"claim_index": c["index"], **row} for c in claim_results for row in c["discarded"]
            ],
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
    def _brief(row: dict) -> dict:
        return {
            "title": row["title"],
            "chunk_id": row["chunk_id"],
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
