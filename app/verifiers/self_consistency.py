"""Self-consistency judgments for the confidence verifier.

The confidence verifier counts judgments; this module produces them from
nothing but a question and an answer, so the verifier can act on its own
in the pipeline like the other three.

Pipeline
    1. Sample N independent regenerations of the answer from the generator
       (``OllamaSampler``: same model as ``/generate-answer``, short-answer
       prompt, temperature > 0, distinct seeds).
    2. Label each regeneration against the candidate answer
       (``AgreementLabeler``):
         - numeric answers: exact ``Decimal`` comparison
         - short answers: normalised containment ("paris" in "paris, france")
         - otherwise: NLI with premise = regeneration, hypothesis = claim
           (entailment -> support, contradiction -> reject, neutral -> unsure)
    3. Return the label list. ``SelfConsistencyJudge.last_trace`` keeps the
       samples, per-sample labels and timings for the verifier's metadata.

What agreement means
    Agreement is a stability signal from one model. A model can be
    consistently wrong, so a high agreement is not evidence of correctness
    on its own; the decision layer weighs it against the other verifiers.

Failure handling
    Network or generator failures propagate as ``JudgmentSourceError`` so the
    verifier can abstain explicitly instead of counting an empty list.
"""

from __future__ import annotations

import os
import re
import time
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Optional

from app.verifiers.claim_generator import ClaimGenerator
from app.verifiers.evidence_verifier import parse_nli_output

Sampler = Callable[[str, int], list[str]]

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
DEFAULT_N_SAMPLES = 5
DEFAULT_TEMPERATURE = 0.8

SHORT_ANSWER_PROMPT = (
    "Answer the question with a short, direct answer only. "
    "Do not explain.\n\nQuestion: {question}\nAnswer:"
)

NLI_TO_JUDGMENT = {
    "entailment": "support",
    "contradiction": "reject",
    "neutral": "unsure",
}

_ARTICLES = re.compile(r"\b(the|a|an)\b")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


class JudgmentSourceError(RuntimeError):
    """The sampler could not produce regenerations (generator down, timeout, bad reply)."""


def normalize_text(text: str) -> str:
    """Lowercase, drop punctuation and articles, collapse whitespace."""
    lowered = re.sub(r"[^\w\s]", " ", str(text).lower())
    return " ".join(_ARTICLES.sub(" ", lowered).split())


def extract_number(text: str) -> Optional[Decimal]:
    """Return the single number in ``text``; ``None`` when there is not exactly one."""
    found = _NUMBER.findall(str(text).replace(",", ""))
    if len(found) != 1:
        return None
    try:
        return Decimal(found[0])
    except InvalidOperation:
        return None


class OllamaSampler:
    """Draw N regenerations from a local Ollama model.

    Uses a short-answer prompt (agreement is judged on "Paris", not on a
    paragraph) and a distinct ``seed`` per sample so the N calls differ even
    when the model is confident. Configuration follows ``llm_service.py``:
    ``OLLAMA_URL`` and ``OLLAMA_MODEL`` environment variables.
    """

    def __init__(
        self,
        url: str | None = None,
        model: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        timeout: float = 60.0,
    ) -> None:
        self.url = url or os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL)
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        self.temperature = temperature
        self.timeout = timeout

    def __call__(self, question: str, n: int) -> list[str]:
        import requests

        samples: list[str] = []
        for seed in range(n):
            try:
                response = requests.post(
                    self.url,
                    json={
                        "model": self.model,
                        "prompt": SHORT_ANSWER_PROMPT.format(question=question.strip()),
                        "stream": False,
                        "options": {"temperature": self.temperature, "seed": seed},
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                text = response.json().get("response")
            except (requests.RequestException, ValueError) as exc:
                raise JudgmentSourceError(f"{self.model} at {self.url}: {exc}") from exc
            samples.append((text or "").strip())
        return samples


class AgreementLabeler:
    """Decide whether one regeneration agrees with the candidate answer."""

    def __init__(
        self,
        nli: Callable[[dict], Any] | None = None,
        min_nli_score: float = 0.50,
        short_answer_words: int = 5,
        max_premise_chars: int = 1500,
    ) -> None:
        self._nli = nli
        self.min_nli_score = min_nli_score
        self.short_answer_words = short_answer_words
        self.max_premise_chars = max_premise_chars
        self.claim_generator = ClaimGenerator()

    @property
    def nli(self) -> Callable[[dict], Any]:
        if self._nli is None:
            from app.verifiers.evidence_verifier import default_nli_pipeline

            self._nli = default_nli_pipeline()
        return self._nli

    def label(self, sample: str, question: str, answer: str, claim: str) -> dict:
        """Return ``{"label", "method", ...}`` for one regeneration."""
        sample_norm = normalize_text(sample)
        answer_norm = normalize_text(answer)
        if not sample_norm:
            return {"label": "unsure", "method": "empty_sample"}

        answer_number = extract_number(answer)
        if answer_number is not None and len(answer_norm.split()) <= self.short_answer_words:
            sample_number = extract_number(sample)
            if sample_number is not None:
                agree = sample_number == answer_number
                return {"label": "support" if agree else "reject", "method": "numeric"}

        if answer_norm and len(answer_norm.split()) <= self.short_answer_words:
            if answer_norm in sample_norm or sample_norm in answer_norm:
                return {"label": "support", "method": "string_match"}

        return self._nli_label(sample, question, claim)

    def _nli_label(self, sample: str, question: str, claim: str) -> dict:
        # A one-word regeneration ("Paris") is turned into a sentence so the
        # premise is declarative, like the hypothesis.
        if len(sample.split()) <= self.short_answer_words:
            premise = self.claim_generator.generate(question, sample)
        else:
            premise = sample[: self.max_premise_chars]
        probabilities, _ = parse_nli_output(self.nli({"text": premise, "text_pair": claim}))
        best = max(probabilities, key=probabilities.get)
        row = {"method": "nli", "premise": premise, "nli": probabilities}
        if probabilities[best] < self.min_nli_score:
            row["label"] = "unsure"
        else:
            row["label"] = NLI_TO_JUDGMENT[best]
        return row


class SelfConsistencyJudge:
    """``(question, answer) -> list[str]`` judgment provider built on regeneration agreement."""

    def __init__(
        self,
        sampler: Sampler | None = None,
        labeler: AgreementLabeler | None = None,
        n_samples: int = DEFAULT_N_SAMPLES,
    ) -> None:
        if n_samples < 1:
            raise ValueError("n_samples must be at least 1")
        self.sampler = sampler or OllamaSampler()
        self.labeler = labeler or AgreementLabeler()
        self.n_samples = n_samples
        self.last_trace: dict = {}

    @property
    def source_name(self) -> str:
        return "self_consistency"

    def __call__(self, question: str, answer: str) -> list[str]:
        start = time.perf_counter()
        samples = self.sampler(question, self.n_samples)
        sampled_at = time.perf_counter()

        claim = self.labeler.claim_generator.generate(question, answer)
        rows = [
            {"sample": sample, **self.labeler.label(sample, question, answer, claim)}
            for sample in samples
        ]
        done = time.perf_counter()

        self.last_trace = {
            "n_samples": self.n_samples,
            "claim": claim,
            "samples": rows,
            "generator_model": getattr(self.sampler, "model", None),
            "temperature": getattr(self.sampler, "temperature", None),
            "latency_breakdown_ms": {
                "sampling": round((sampled_at - start) * 1000, 2),
                "labeling": round((done - sampled_at) * 1000, 2),
            },
        }
        return [row["label"] for row in rows]
