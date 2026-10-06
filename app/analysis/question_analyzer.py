"""Question analyzer: keyword heuristic, with an optional Ollama classification.

``QuestionAnalyzer().analyze(question)`` still returns ``QuestionAnalysis``
with ``domain``, ``difficulty``, and ``difficulty_score``. The default mode
is the original heuristic so existing callers stay on that path.

Ollama mode is explicit. This module does not load a ``.env`` file and does
not call the answer generator. See docs/analyzer_setup.md.

The selector reads ``verification_types`` as a suitability hint. Reputation
and decision scoring do not directly read the added metadata.
"""

from __future__ import annotations

import math
import os
from typing import Mapping, Protocol
from urllib.parse import urlparse

import httpx

from app.analysis.heuristic import (
    EASY_MAX,
    FEATURE_WEIGHTS,
    MEDIUM_MAX,
    heuristic_analysis,
)
from app.analysis.model_assessment import (
    AnalyzerResponseError,
    ModelAssessment,
    build_generate_body,
    parse_envelope,
    validate_assessment,
)
from app.analysis.models import QuestionAnalysis

__all__ = [
    "EASY_MAX",
    "FEATURE_WEIGHTS",
    "MEDIUM_MAX",
    "QuestionAnalysis",
    "QuestionAnalyzer",
]

_DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
_DEFAULT_MODEL = "llama3.2:3b"
_DEFAULT_TIMEOUT_SECONDS = 15.0
_MODES = frozenset({"heuristic", "ollama"})


class _GenerateClient(Protocol):
    def post(self, url: str, *, json: dict, timeout: float) -> httpx.Response:
        """POST one generate request. Implementations must not retry."""


class QuestionAnalyzer:
    """Classify a question with the heuristic or with one Ollama call."""

    def __init__(
        self,
        *,
        mode: str | None = None,
        ollama_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        client: _GenerateClient | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        env = os.environ if environ is None else environ
        self.mode = _resolve_mode(mode, env)
        self.ollama_url = _resolve_url(ollama_url, env)
        self.model = _resolve_model(model, env)
        self.timeout_seconds = _resolve_timeout(timeout_seconds, env)
        self._client = client

    def analyze(self, question: str) -> QuestionAnalysis:
        """Return domain, difficulty, and difficulty_score for ``question``.

        Blank text raises ``ValueError``. A non-string raises ``TypeError``.
        Both happen before any network call. Ollama failures that are
        transport, HTTP, or schema problems return the heuristic result
        with ``analysis_method`` ``heuristic_fallback``.
        """
        if not isinstance(question, str):
            raise TypeError("question must be a string")
        if question.strip() == "":
            raise ValueError("question must not be blank")
        if self.mode == "heuristic":
            return heuristic_analysis(question)
        try:
            assessment = self._assess(question)
        except httpx.TimeoutException:
            return _fallback(question, "timeout")
        except httpx.HTTPError:
            return _fallback(question, "http_error")
        except AnalyzerResponseError as exc:
            return _fallback(question, exc.code)
        return _from_assessment(assessment)

    def _assess(self, question: str) -> ModelAssessment:
        body = build_generate_body(question, self.model)
        response = self._post(body)
        if response.status_code < 200 or response.status_code >= 300:
            raise httpx.HTTPStatusError(
                "analyzer request failed",
                request=httpx.Request("POST", self.ollama_url),
                response=response,
            )
        try:
            envelope = response.json()
        except (ValueError, RecursionError):
            # httpx raises JSONDecodeError, a ValueError, for a non-JSON body.
            raise AnalyzerResponseError("malformed_envelope") from None
        return validate_assessment(parse_envelope(envelope))

    def _post(self, body: dict) -> httpx.Response:
        if self._client is not None:
            return self._client.post(
                self.ollama_url,
                json=body,
                timeout=self.timeout_seconds,
            )
        with httpx.Client(timeout=self.timeout_seconds) as client:
            return client.post(self.ollama_url, json=body)


def _fallback(question: str, reason: str) -> QuestionAnalysis:
    return heuristic_analysis(
        question,
        analysis_method="heuristic_fallback",
        fallback_reason=reason,
    )


def _from_assessment(assessment: ModelAssessment) -> QuestionAnalysis:
    return QuestionAnalysis(
        domain=assessment.domain,
        difficulty=assessment.band(),
        difficulty_score=assessment.score(),
        subject=assessment.subject,
        domain_candidates=list(assessment.domain_candidates),
        domain_status=assessment.domain_status,
        verification_types=list(assessment.verification_types),
        analysis_method="ollama",
        fallback_reason=None,
        rubric_ratings={
            "reasoning_depth": assessment.reasoning_depth,
            "evidence_burden": assessment.evidence_burden,
            "constraint_interactions": assessment.constraint_interactions,
        },
    )


def _resolve_mode(mode: str | None, env: Mapping[str, str]) -> str:
    if mode is not None:
        chosen = mode.strip().lower()
    elif "ANALYZER_MODE" in env:
        chosen = env["ANALYZER_MODE"].strip().lower()
    else:
        chosen = "heuristic"
    if chosen not in _MODES:
        raise ValueError("ANALYZER_MODE must be 'heuristic' or 'ollama'")
    return chosen


def _resolve_url(url: str | None, env: Mapping[str, str]) -> str:
    chosen = url if url is not None else env.get("OLLAMA_URL", _DEFAULT_OLLAMA_URL)
    if not isinstance(chosen, str):
        raise ValueError("OLLAMA_URL must be an http(s) URL")
    chosen = chosen.strip()
    parsed = urlparse(chosen)
    if parsed.scheme not in {"http", "https"} or parsed.netloc == "":
        raise ValueError("OLLAMA_URL must be an http(s) URL")
    return chosen


def _resolve_model(model: str | None, env: Mapping[str, str]) -> str:
    if model is not None:
        chosen = model.strip()
    else:
        chosen = _blank_as_missing(env.get("ANALYZER_MODEL"))
        if chosen is None:
            chosen = _blank_as_missing(env.get("OLLAMA_MODEL")) or _DEFAULT_MODEL
    if chosen == "":
        raise ValueError("ANALYZER_MODEL must be a non-empty model name")
    return chosen


def _resolve_timeout(timeout_seconds: float | None, env: Mapping[str, str]) -> float:
    if timeout_seconds is not None:
        value = float(timeout_seconds)
    elif "ANALYZER_TIMEOUT_SECONDS" in env:
        raw = env["ANALYZER_TIMEOUT_SECONDS"].strip()
        try:
            value = float(raw)
        except ValueError:
            raise ValueError(
                "ANALYZER_TIMEOUT_SECONDS must be a positive finite number"
            ) from None
    else:
        value = _DEFAULT_TIMEOUT_SECONDS
    if not math.isfinite(value) or value <= 0:
        raise ValueError("ANALYZER_TIMEOUT_SECONDS must be a positive finite number")
    return value


def _blank_as_missing(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if stripped == "":
        return None
    return stripped
