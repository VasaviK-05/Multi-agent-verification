"""Offline contract checks; these are not semantic performance evidence."""
from dataclasses import asdict
import json
import math

import httpx
import pytest
from fastapi.encoders import jsonable_encoder

from app.analysis.models import QuestionAnalysis
from app.analysis.question_analyzer import QuestionAnalyzer
from app.analysis.research_context import build_research_context
from app.analysis.model_assessment import VERIFICATION_TYPES, RUBRIC_FIELDS
from tests.test_question_analyzer_ollama import FakeClient, _response, _payload


def test_old_construction_and_detached_canonical_context():
    legacy = QuestionAnalysis("general", "easy", .1)
    assert legacy.research_context is None
    legacy.verification_types = ["consistency", "arithmetic", "consistency", "direct_fact"]
    before = asdict(legacy)
    context = build_research_context(legacy)
    assert asdict(legacy) == before
    assert context.verification_requirements == ["direct_fact", "arithmetic", "consistency"]
    assert context.requirements_known is True
    assert set(context.requirement_weights) == set(VERIFICATION_TYPES)
    assert all(context.requirement_weights[k] == (1/3 if k in context.verification_requirements else 0)
               for k in VERIFICATION_TYPES)
    assert all(math.isfinite(v) and 0 <= v <= 1 for v in context.requirement_weights.values())
    assert sum(context.requirement_weights.values()) == pytest.approx(1)
    context.verification_requirements.clear()
    assert legacy.verification_types == before["verification_types"]


def test_heuristic_unknown_and_known_contexts_serialize_without_api_changes():
    analyzer = QuestionAnalyzer(environ={})
    unknown = analyzer.analyze("What is it?")
    known = analyzer.analyze("Who wrote Hamlet?")
    assert unknown.research_context.verification_requirements == []
    assert unknown.research_context.requirements_known is False
    assert set(unknown.research_context.requirement_weights.values()) == {0.0}
    assert known.research_context.requirement_weights["direct_fact"] == 1
    assert known.research_context.normalized_rubric is None
    assert known.research_context.scoring_version == "heuristic_surface_features_v1"
    assert known.research_context.domain_status == known.domain_status
    assert known.research_context.analysis_method == "heuristic"
    assert json.loads(json.dumps(jsonable_encoder(known))) == asdict(known)


def test_ollama_rubric_is_normalized_without_an_extra_call_or_schema_fields():
    client = FakeClient(_response(_payload(reasoning_depth=0, evidence_burden=1, constraint_interactions=2)))
    analysis = QuestionAnalyzer(mode="ollama", client=client, environ={}).analyze("What is 2 + 2?")
    context = analysis.research_context
    assert context.normalized_rubric == dict(zip(RUBRIC_FIELDS, [0., .5, 1.]))
    assert context.scoring_version == "rubric_sum_over_six_v1"
    assert context.analysis_method == "ollama"
    assert len(client.calls) == 1
    assert "research_context" not in client.calls[0]["json"]["format"]["properties"]
    context.normalized_rubric["reasoning_depth"] = 1
    assert analysis.rubric_ratings["reasoning_depth"] == 0
    other = build_research_context(analysis)
    assert other.normalized_rubric["reasoning_depth"] == 0
    context.requirement_weights["arithmetic"] = 0
    assert other.requirement_weights["arithmetic"] == 1


@pytest.mark.parametrize("kind,reason", [
    ("timeout", "timeout"), ("http", "http_error"),
    ("envelope", "malformed_envelope"), ("schema", "invalid_schema"),
    ("routing", "invalid_routing"),
])
def test_every_expected_failure_builds_context_after_final_fallback_hints(kind, reason):
    question = "Write a Python function to sort a list and provide the answer to 2 + 2."
    if kind == "timeout": client = FakeClient(error=httpx.ReadTimeout("test"))
    elif kind == "http": client = FakeClient(_response(status=503))
    elif kind == "envelope": client = FakeClient(httpx.Response(200, json=[]))
    elif kind == "schema": client = FakeClient(_response({}))
    else:
        question = "Write a Python function that adds two integers."
        client = FakeClient(_response(_payload(verification_types=["arithmetic"])))
    analysis = QuestionAnalyzer(mode="ollama", client=client, environ={}).analyze(question)
    context = analysis.research_context
    assert analysis.fallback_reason == reason
    assert context.analysis_method == "heuristic_fallback"
    assert context.scoring_version == "heuristic_surface_features_v1"
    assert context.normalized_rubric is None
    assert context.verification_requirements == ([] if kind == "routing" else ["arithmetic"])
    assert context.requirements_known is (kind != "routing")
    assert len(client.calls) == 1


def test_every_output_has_fresh_containers_and_legacy_routing_is_unchanged():
    analyzer = QuestionAnalyzer(environ={})
    first, second = [analyzer.analyze("What is 2 + 2?") for _ in range(2)]
    assert first.difficulty_score == .12 and first.difficulty == "easy"
    assert first.verification_types == ["arithmetic"] and first.domain == "general"
    first.research_context.verification_requirements.append("direct_fact")
    first.research_context.requirement_weights["arithmetic"] = 0
    first.verification_types.clear()
    assert second.verification_types == ["arithmetic"]
    assert second.research_context.verification_requirements == ["arithmetic"]
    assert second.research_context.requirement_weights["arithmetic"] == 1
