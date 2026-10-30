"""Generation outcomes stay separate from factual verification decisions."""

from scripts.test_real_ollama_evidence_pipeline import (
    GenerationStatus,
    parse_generation_response,
    verify_generation,
)


class VerifierSpy:
    def __init__(self):
        self.calls = []

    def verify(self, **kwargs):
        self.calls.append(kwargs)
        return {"decision": "REJECT"}


def test_explicit_abstention_bypasses_evidence_verification():
    outcome = parse_generation_response('{"status":"ABSTAINED","answer":""}')
    verifier = VerifierSpy()
    assert outcome.status is GenerationStatus.ABSTAINED
    assert verify_generation(verifier, "question", outcome) is None
    assert verifier.calls == []


def test_valid_answer_with_uncertainty_language_is_not_keyword_rejected():
    outcome = parse_generation_response(
        '{"status":"ANSWERED","answer":"The report says, \'I am not sure\', before naming the result."}'
    )
    assert outcome.status is GenerationStatus.ANSWERED
    assert outcome.answer.startswith("The report")


def test_refusal_only_phrases_are_abstentions_but_malformed_data_is_error():
    for phrase in ("I'm not sure.", "I don't know", "I cannot answer reliably."):
        assert parse_generation_response(phrase).status is GenerationStatus.ABSTAINED
    malformed = parse_generation_response('{"status":"ANSWERED","answer":12}')
    verifier = VerifierSpy()
    assert malformed.status is GenerationStatus.GENERATION_ERROR
    assert verify_generation(verifier, "question", malformed) is None
    assert verifier.calls == []


def test_generation_error_is_distinct_from_abstention_and_rejection():
    outcome = parse_generation_response("{broken")
    verifier = VerifierSpy()
    assert outcome.status is GenerationStatus.GENERATION_ERROR
    assert outcome.status is not GenerationStatus.ABSTAINED
    assert verify_generation(verifier, "question", outcome) is None
    assert verifier.calls == []


def test_answer_is_the_only_generation_outcome_sent_to_verifier():
    outcome = parse_generation_response('{"status":"ANSWERED","answer":"T. S. Eliot."}')
    verifier = VerifierSpy()
    assert verify_generation(verifier, "who?", outcome) == {"decision": "REJECT"}
    assert verifier.calls == [{"question": "who?", "answer": "T. S. Eliot.", "context": None}]
