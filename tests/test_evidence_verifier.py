"""Evidence verifier tests.

The first part uses a fake retriever and a fake NLI callable so the
aggregation logic, relevance gate, and output-shape handling run in
milliseconds. The second part loads the real models once and checks the
tiny ``data/test_evidence_corpus.json`` end to end.
"""

import pytest

from app.verifiers.evidence_verifier import (
    NO_RELEVANT_EVIDENCE_REASON,
    EvidenceVerifier,
    normalize_nli_label,
    parse_nli_output,
)

TEST_CORPUS = "data/test_evidence_corpus.json"


# ----------------------------------------------------------------------
# Fakes
# ----------------------------------------------------------------------

class FakeRetriever:
    """Returns a fixed ranked list regardless of the query."""

    def __init__(self, results=None, by_query=None) -> None:
        self.results = results or []
        self.by_query = by_query or {}
        self.queries: list[str] = []

    def retrieve(self, query: str, k: int = 3):
        self.queries.append(query)
        for needle, results in self.by_query.items():
            if needle in query:
                return list(results[:k])
        return list(self.results[:k])


def chunk(title: str, text: str, score: float, chunk_id: int = 0) -> dict:
    return {"title": title, "text": text, "url": f"https://example.org/{title}", "chunk_id": chunk_id, "score": score}


class FakeNLI:
    """Maps premise text -> probabilities; emits a configurable output shape."""

    def __init__(self, table: dict[str, dict[str, float]], shape: str = "list[list[dict]]") -> None:
        self.table = table
        self.shape = shape

    def __call__(self, inputs: dict):
        premise = inputs["text"]
        probs = next(v for k, v in self.table.items() if k in premise)
        rows = [{"label": label, "score": score} for label, score in probs.items()]
        if self.shape == "list[list[dict]]":
            return [rows]
        if self.shape == "list[dict]":
            return rows
        if self.shape == "dict":
            return max(rows, key=lambda row: row["score"])
        raise AssertionError(self.shape)


ENTAILS = {"entailment": 0.95, "neutral": 0.04, "contradiction": 0.01}
CONTRADICTS = {"contradiction": 0.93, "neutral": 0.05, "entailment": 0.02}
NEUTRAL = {"neutral": 0.90, "entailment": 0.06, "contradiction": 0.04}


def make_verifier(retriever, nli, **kwargs) -> EvidenceVerifier:
    return EvidenceVerifier(retriever=retriever, nli=nli, **kwargs)


# ----------------------------------------------------------------------
# Output-shape handling (issue 8)
# ----------------------------------------------------------------------

def test_parse_nli_output_accepts_each_shape():
    rows = [{"label": "entailment", "score": 0.7}, {"label": "neutral", "score": 0.2}, {"label": "contradiction", "score": 0.1}]
    for raw, shape in ((rows, "list[dict]"), ([rows], "list[list[dict]]"), (rows[0], "dict")):
        probabilities, seen = parse_nli_output(raw)
        assert seen == shape
        assert probabilities["entailment"] == pytest.approx(0.7)


def test_labels_are_normalised_case_insensitively():
    assert normalize_nli_label("ENTAILMENT") == "entailment"
    assert normalize_nli_label("Contradiction") == "contradiction"
    assert normalize_nli_label("neutral") == "neutral"
    with pytest.raises(ValueError):
        normalize_nli_label("LABEL_0")


@pytest.mark.parametrize("shape", ["list[list[dict]]", "list[dict]", "dict"])
def test_verifier_handles_every_pipeline_shape(shape):
    retriever = FakeRetriever([chunk("France", "Paris is the capital of France.", 0.85)])
    verifier = make_verifier(retriever, FakeNLI({"Paris": ENTAILS}, shape=shape))

    result = verifier.verify("What is the capital of France?", "Paris")

    assert result.passed is True
    assert result.metadata["nli_label"] == "entailment"
    assert result.metadata["nli_output_shape"] == shape


# ----------------------------------------------------------------------
# Relevance gate (issue 6)
# ----------------------------------------------------------------------

def test_best_hit_below_floor_abstains_without_running_nli():
    retriever = FakeRetriever([chunk("India", "New Delhi is the capital of India.", 0.20)])
    calls = []

    def nli(inputs):
        calls.append(inputs)
        return [[{"label": "contradiction", "score": 0.99}]]

    result = make_verifier(retriever, nli, min_retrieval_score=0.30).verify("What is the capital of Japan?", "Tokyo")

    assert calls == []
    assert result.passed is False
    assert result.score == 0.0
    assert result.metadata["nli_label"] is None
    assert result.metadata["decision"] == "UNSURE"
    assert result.metadata["unsure_reason"] == "no_relevant_evidence"
    assert result.metadata["best_retrieval_score"] == pytest.approx(0.20)
    assert result.reasoning == NO_RELEVANT_EVIDENCE_REASON


def test_empty_retrieval_abstains():
    result = make_verifier(FakeRetriever([]), FakeNLI({})).verify("q", "a")
    assert result.passed is False
    assert result.score == 0.0
    assert result.metadata["nli_label"] is None
    assert result.reasoning == "No evidence was retrieved."


def test_distant_neighbour_cannot_create_a_false_contradiction():
    retriever = FakeRetriever(
        [
            chunk("France", "Paris is the capital of France.", 0.83),
            chunk("Paris", "Paris is the capital and largest city of France.", 0.78),
            chunk("Germany", "Berlin is the capital of Germany.", 0.36),
        ]
    )
    nli = FakeNLI({"Paris": ENTAILS, "Berlin": CONTRADICTS})

    result = make_verifier(retriever, nli, retrieval_margin=0.15).verify("What is the capital of France?", "Paris")

    assert result.passed is True
    assert result.metadata["decision"] == "SUPPORT"
    assert [e["title"] for e in result.metadata["evaluated_evidence"]] == ["France", "Paris"]
    assert result.metadata["contradicting"] == []


# ----------------------------------------------------------------------
# Topic gate (UEFA / SK Brann regression)
# ----------------------------------------------------------------------

UEFA_QUESTION = "Who won the 2010 UEFA Europa League Final?"
UEFA_FINAL = chunk(
    "2010 UEFA Europa League Final",
    "The 2010 UEFA Europa League Final was played in Hamburg. Atletico Madrid won the final "
    "against Fulham 2-1 after extra time.",
    0.74,
)
BRANN_2008 = chunk(
    "2008 SK Brann season",
    "Brann won the league and entered the UEFA Cup, but were eliminated by Hamburg in the "
    "group stage. Fulham were not among their opponents.",
    0.66,
)


class WeightedFakeRetriever(FakeRetriever):
    """FakeRetriever with fixed IDF-like weights (rare names weigh more than 'league')."""

    WEIGHTS = {"2010": 2.0, "uefa": 3.0, "europa": 4.0, "league": 1.0, "final": 1.0, "won": 0.5}

    def term_weights(self, terms):
        return {t: self.WEIGHTS.get(t, 1.0) for t in terms}


def test_off_topic_chunk_cannot_contradict_when_right_article_supports():
    retriever = WeightedFakeRetriever([UEFA_FINAL, BRANN_2008])
    nli = FakeNLI({"Atletico": ENTAILS, "Brann": CONTRADICTS})

    result = make_verifier(retriever, nli).verify(UEFA_QUESTION, "Atletico Madrid")

    assert result.metadata["decision"] == "SUPPORT"
    assert result.passed is True
    assert result.metadata["contradicting"] == []
    assert [e["title"] for e in result.metadata["evaluated_evidence"]] == ["2010 UEFA Europa League Final"]
    discarded = result.metadata["discarded_evidence"]
    assert [d["title"] for d in discarded] == ["2008 SK Brann season"]
    assert discarded[0]["missing_numbers"] == ["2010"]


def test_off_topic_chunk_alone_abstains_instead_of_rejecting():
    retriever = WeightedFakeRetriever([BRANN_2008])
    calls = []

    def nli(inputs):
        calls.append(inputs)
        return [[{"label": "contradiction", "score": 0.99}]]

    result = make_verifier(retriever, nli).verify(UEFA_QUESTION, "Fulham")

    assert calls == []  # NLI never sees the off-topic premise
    assert result.metadata["decision"] == "UNSURE"
    assert result.metadata["unsure_reason"] == "no_relevant_evidence"
    assert result.metadata["nli_label"] is None
    assert result.score == 0.0


def test_right_article_can_still_reject_a_wrong_answer():
    retriever = WeightedFakeRetriever([UEFA_FINAL, BRANN_2008])
    nli = FakeNLI({"Atletico": CONTRADICTS, "Brann": ENTAILS})

    result = make_verifier(retriever, nli).verify(UEFA_QUESTION, "Fulham")

    assert result.metadata["decision"] == "REJECT"
    assert result.metadata["evidence_title"] == "2010 UEFA Europa League Final"
    assert result.metadata["supporting"] == []


def test_low_weighted_coverage_is_discarded_even_without_numbers():
    retriever = WeightedFakeRetriever(
        [
            chunk("UEFA Europa League", "The UEFA Europa League final is played each May.", 0.70),
            chunk("Football league", "A football league has a final match.", 0.68),
        ]
    )
    nli = FakeNLI({"May": NEUTRAL, "football": CONTRADICTS})

    result = make_verifier(retriever, nli).verify("Which club won the UEFA Europa League final?", "Sevilla")

    assert result.metadata["contradicting"] == []
    assert [d["title"] for d in result.metadata["discarded_evidence"]] == ["Football league"]
    assert result.metadata["decision"] == "UNSURE"


def test_answer_numbers_are_not_required_in_evidence():
    retriever = FakeRetriever([chunk("Paris", "Paris has about two million residents in 2020.", 0.70)])
    nli = FakeNLI({"two million": CONTRADICTS})

    result = make_verifier(retriever, nli).verify("How many residents does Paris have?", "40 million")

    assert result.metadata["decision"] == "REJECT"
    assert result.metadata["discarded_evidence"] == []


# ----------------------------------------------------------------------
# Conflict-aware aggregation (issue 5)
# ----------------------------------------------------------------------

def test_strong_contradiction_alongside_entailment_is_a_conflict_not_support():
    retriever = FakeRetriever(
        [
            chunk("A", "Source A says Person A discovered X.", 0.80),
            chunk("B", "Source B says Person B discovered X.", 0.79),
        ]
    )
    nli = FakeNLI({"Source A": ENTAILS, "Source B": CONTRADICTS})

    result = make_verifier(retriever, nli).verify("Who discovered X?", "Person A")

    assert result.passed is False
    assert result.metadata["decision"] == "UNSURE"
    assert result.metadata["nli_label"] == "neutral"
    assert result.metadata["unsure_reason"] == "conflict"
    assert [s["title"] for s in result.metadata["supporting"]] == ["A"]
    assert [c["title"] for c in result.metadata["contradicting"]] == ["B"]
    assert "conflict" in result.reasoning


def test_only_contradiction_rejects_with_its_probability():
    retriever = FakeRetriever([chunk("France", "Paris is the capital of France.", 0.85)])
    result = make_verifier(retriever, FakeNLI({"Paris": CONTRADICTS})).verify("What is the capital of France?", "London")

    assert result.passed is False
    assert result.metadata["decision"] == "REJECT"
    assert result.metadata["nli_label"] == "contradiction"
    assert result.score == pytest.approx(0.93)
    assert result.metadata["evidence_title"] == "France"


def test_neutral_evidence_abstains():
    retriever = FakeRetriever([chunk("France", "The capital of France hosts many museums.", 0.70)])
    result = make_verifier(retriever, FakeNLI({"museums": NEUTRAL})).verify("What is the capital of France?", "Paris")

    assert result.passed is False
    assert result.score == 0.0
    assert result.metadata["nli_label"] == "neutral"
    assert result.metadata["unsure_reason"] == "neutral"


def test_weak_entailment_below_min_nli_score_is_not_support():
    retriever = FakeRetriever([chunk("Paris", "Paris is in France.", 0.70)])
    weak = {"entailment": 0.45, "neutral": 0.40, "contradiction": 0.15}
    result = make_verifier(retriever, FakeNLI({"Paris": weak}), min_nli_score=0.5).verify("q", "Paris")

    assert result.passed is False
    assert result.metadata["decision"] == "UNSURE"
    assert result.metadata["evaluated_evidence"][0]["nli_label"] == "entailment"


# ----------------------------------------------------------------------
# Claim-level checking (issue 7)
# ----------------------------------------------------------------------

def test_multi_sentence_answer_is_checked_per_claim():
    retriever = FakeRetriever(
        by_query={  # claim-specific needle first: every query also contains the question
            "forty million": [chunk("Paris", "Paris has about two million residents.", 0.60)],
            "capital of France": [chunk("France", "Paris is the capital of France.", 0.85)],
        }
    )
    nli = FakeNLI({"capital of France": ENTAILS, "two million": CONTRADICTS})

    result = make_verifier(retriever, nli).verify(
        "What is the capital of France?",
        "Paris is the capital of France. It has exactly forty million residents.",
    )

    assert len(result.metadata["claims"]) == 2
    assert [c["decision"] for c in result.metadata["claim_decisions"]] == ["SUPPORT", "REJECT"]
    assert result.metadata["decision"] == "REJECT"
    assert result.passed is False
    assert "forty million" in result.reasoning


def test_partially_supported_answer_is_unsure_and_lists_unchecked_claims():
    retriever = FakeRetriever(
        by_query={
            "Seine": [chunk("Germany", "Berlin is on the Spree.", 0.10)],
            "capital of France": [chunk("France", "Paris is the capital of France.", 0.85)],
        }
    )
    nli = FakeNLI({"capital of France": ENTAILS})

    result = make_verifier(retriever, nli).verify(
        "What is the capital of France?",
        "Paris is the capital of France. It lies on the Seine.",
    )

    assert result.passed is False
    assert result.metadata["decision"] == "UNSURE"
    assert result.metadata["nli_label"] == "neutral"
    assert result.metadata["unsure_reason"] == "partial_support"
    assert result.metadata["unchecked_claims"] == ["It lies on the Seine."]
    assert [c["decision"] for c in result.metadata["claim_decisions"]] == ["SUPPORT", "UNSURE"]


def test_all_claims_supported_uses_the_weakest_confidence():
    strong = {"entailment": 0.99, "neutral": 0.01, "contradiction": 0.0}
    weaker = {"entailment": 0.80, "neutral": 0.15, "contradiction": 0.05}
    retriever = FakeRetriever(
        by_query={
            "Seine": [chunk("Paris", "Paris lies on the Seine.", 0.80)],
            "capital": [chunk("France", "Paris is the capital of France.", 0.85)],
        }
    )
    nli = FakeNLI({"capital": strong, "Seine": weaker})

    result = make_verifier(retriever, nli).verify(
        "What is the capital of France?",
        "Paris is the capital of France. It lies on the Seine.",
    )

    assert result.passed is True
    assert result.metadata["decision"] == "SUPPORT"
    assert result.score == pytest.approx(0.80)


def test_metadata_contract_fields():
    retriever = FakeRetriever([chunk("France", "Paris is the capital of France.", 0.85)])
    result = make_verifier(retriever, FakeNLI({"Paris": ENTAILS})).verify("What is the capital of France?", "Paris")
    m = result.metadata
    assert m["decision"] == "SUPPORT"
    assert "not a calibrated probability" in m["score_meaning"]
    assert m["thresholds_calibrated"] is False
    assert set(m["latency_breakdown_ms"]) == {"retrieval", "nli", "total"}
    for key in ("min_retrieval_score", "retrieval_margin", "min_nli_score", "top_k", "claims", "evaluated_evidence"):
        assert key in m


# ----------------------------------------------------------------------
# Model-backed, tiny corpus only
# ----------------------------------------------------------------------

@pytest.fixture(scope="module")
def verifier() -> EvidenceVerifier:
    return EvidenceVerifier(corpus_path=TEST_CORPUS)


def test_real_label_map_is_checked(verifier: EvidenceVerifier):
    assert set(verifier.nli_label_map.values()) == {"entailment", "contradiction", "neutral"}


def test_correct_capital_answer(verifier: EvidenceVerifier):
    result = verifier.verify("What is the capital of France?", "Paris")
    assert result.passed is True
    assert result.metadata["decision"] == "SUPPORT"
    assert result.metadata["nli_label"] == "entailment"
    assert result.metadata["evaluated_evidence"]


def test_wrong_capital_answer(verifier: EvidenceVerifier):
    result = verifier.verify("What is the capital of France?", "London")
    assert result.passed is False
    assert result.metadata["decision"] == "REJECT"
    assert result.metadata["nli_label"] == "contradiction"


def test_incorrect_artificial_intelligence_answer(verifier: EvidenceVerifier):
    result = verifier.verify("What is artificial intelligence?", "Artificial intelligence is a type of automobile.")
    assert result.passed is False
    assert result.metadata["nli_label"] == "contradiction"


def test_who_question(verifier: EvidenceVerifier):
    result = verifier.verify("Who developed the theory of relativity?", "Albert Einstein")
    assert result.passed is True
    assert result.metadata["nli_label"] == "entailment"


def test_topic_outside_corpus_is_an_abstention(verifier: EvidenceVerifier):
    result = verifier.verify("What is the capital of Japan?", "Tokyo")
    assert result.passed is False
    assert result.metadata["decision"] == "UNSURE"
    assert result.metadata["nli_label"] in {None, "neutral"}


def test_unrelated_answer(verifier: EvidenceVerifier):
    result = verifier.verify("What is the capital of France?", "Bananas are yellow")
    assert result.passed is False
    assert result.metadata["decision"] in {"UNSURE", "REJECT"}


def test_multi_claim_answer_with_an_unsupported_sentence(verifier: EvidenceVerifier):
    result = verifier.verify(
        "What is the capital of France?",
        "Paris is the capital of France. It has exactly forty million residents.",
    )
    assert len(result.metadata["claims"]) == 2
    assert result.metadata["claim_decisions"][0]["decision"] == "SUPPORT"
    assert result.passed is False
    assert result.metadata["decision"] in {"UNSURE", "REJECT"}
