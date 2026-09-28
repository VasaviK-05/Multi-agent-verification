from app.verifiers.evidence_verifier import EvidenceVerifier


TEST_CORPUS = "data/test_evidence_corpus.json"


def test_correct_capital_answer():
    verifier = EvidenceVerifier(corpus_path=TEST_CORPUS)

    result = verifier.verify(
        "What is the capital of France?",
        "Paris",
    )

    assert result.passed is True
    assert result.metadata["nli_label"] == "entailment"


def test_wrong_capital_answer():
    verifier = EvidenceVerifier(corpus_path=TEST_CORPUS)

    result = verifier.verify(
        "What is the capital of France?",
        "London",
    )

    assert result.passed is False
    assert result.metadata["nli_label"] == "contradiction"


def test_definition_answer():
    verifier = EvidenceVerifier(corpus_path=TEST_CORPUS)

    result = verifier.verify(
        "What is Python?",
        "a programming language",
    )

    assert result.passed is True
    assert result.metadata["nli_label"] == "entailment"


def test_who_question():
    verifier = EvidenceVerifier(corpus_path=TEST_CORPUS)

    result = verifier.verify(
        "Who developed the theory of relativity?",
        "Albert Einstein",
    )

    assert result.passed is True
    assert result.metadata["nli_label"] == "entailment"


def test_unrelated_answer():
    verifier = EvidenceVerifier(corpus_path=TEST_CORPUS)

    result = verifier.verify(
        "What is the capital of France?",
        "Bananas are yellow",
    )

    assert result.passed is False
    assert result.metadata["nli_label"] in {
        "neutral",
        "contradiction",
    }