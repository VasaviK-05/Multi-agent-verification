import json

import pytest

from app.verifiers.evidence_retriever import EvidenceRetriever, content_terms

FULL_CORPUS = "data/evidence_corpus.json"
TEST_CORPUS = "data/test_evidence_corpus.json"


# ----------------------------------------------------------------------
# Index is keyed to the corpus it was built from
# ----------------------------------------------------------------------

def test_default_index_dir_is_keyed_to_the_corpus_stem(tmp_path):
    corpus = tmp_path / "mini_corpus.json"
    corpus.write_text(json.dumps([{"id": "1", "title": "A", "url": "", "text": "Alpha is first."}]), encoding="utf-8")

    retriever = EvidenceRetriever(corpus_path=str(corpus))

    assert retriever.index_dir == tmp_path / "evidence_index" / "mini_corpus"
    assert retriever.index_path.exists()
    assert retriever.chunks_path.exists()
    assert retriever.manifest_path.exists()
    assert retriever.index.ntotal == 1


def test_index_is_rebuilt_when_the_corpus_changes(tmp_path):
    corpus = tmp_path / "c.json"
    corpus.write_text(json.dumps([{"id": "1", "title": "A", "url": "", "text": "Alpha is first."}]), encoding="utf-8")
    first = EvidenceRetriever(corpus_path=str(corpus))
    assert first.index.ntotal == 1

    corpus.write_text(
        json.dumps(
            [
                {"id": "1", "title": "A", "url": "", "text": "Alpha is first."},
                {"id": "2", "title": "B", "url": "", "text": "Beta is second."},
            ]
        ),
        encoding="utf-8",
    )
    second = EvidenceRetriever(corpus_path=str(corpus), model=first.model)
    assert second.index.ntotal == 2
    assert {chunk["title"] for chunk in second.chunks} == {"A", "B"}


def test_index_is_reused_when_the_manifest_matches(tmp_path, monkeypatch):
    corpus = tmp_path / "c.json"
    corpus.write_text(json.dumps([{"id": "1", "title": "A", "url": "", "text": "Alpha is first."}]), encoding="utf-8")
    first = EvidenceRetriever(corpus_path=str(corpus))

    monkeypatch.setattr(EvidenceRetriever, "build_index", lambda self: pytest.fail("index should be loaded, not rebuilt"))
    second = EvidenceRetriever(corpus_path=str(corpus), model=first.model)
    assert second.index.ntotal == 1


def test_tiny_corpus_never_answers_from_the_full_index():
    retriever = EvidenceRetriever(corpus_path=TEST_CORPUS)
    titles = {chunk["title"] for chunk in retriever.chunks}
    assert retriever.index.ntotal == len(retriever.chunks) == 10
    assert "Alaska" not in titles
    results = retriever.retrieve("What is Alaska?", k=3)
    assert all(result["title"] in titles for result in results)


def test_k_is_clamped_to_the_index_size(tmp_path):
    corpus = tmp_path / "c.json"
    corpus.write_text(json.dumps([{"id": "1", "title": "A", "url": "", "text": "Alpha is first."}]), encoding="utf-8")
    retriever = EvidenceRetriever(corpus_path=str(corpus))
    assert len(retriever.retrieve("alpha", k=5)) == 1
    assert retriever.retrieve("alpha", k=0) == []


def test_scores_are_cosine_similarities():
    retriever = EvidenceRetriever(corpus_path=TEST_CORPUS)
    results = retriever.retrieve("Paris is the capital and largest city of France.", k=3)
    assert results[0]["title"] in {"France", "Paris"}
    assert all(-1.0 <= result["score"] <= 1.0 + 1e-6 for result in results)
    assert results[0]["score"] >= results[-1]["score"]


# ----------------------------------------------------------------------
# Term statistics for the topic gate
# ----------------------------------------------------------------------

def test_content_terms_drops_stopwords_and_keeps_numbers():
    assert content_terms("Who won the 2010 UEFA Europa League Final?") == {
        "won", "2010", "uefa", "europa", "league", "final",
    }


def test_term_weights_rank_rare_terms_above_common_ones():
    retriever = EvidenceRetriever(corpus_path=TEST_CORPUS)
    weights = retriever.term_weights({"capital", "france", "seine", "notinthecorpus"})

    assert "notinthecorpus" not in weights  # cannot discriminate between chunks
    assert weights["seine"] > weights["france"] > weights["capital"]
    assert all(weight >= 0 for weight in weights.values())


# ----------------------------------------------------------------------
# Full corpus retrieval quality (one-time index build on first run)
# ----------------------------------------------------------------------

def test_alaska_retrieval():
    retriever = EvidenceRetriever(corpus_path=FULL_CORPUS)
    titles = [result["title"] for result in retriever.retrieve("What is Alaska?", k=3)]
    assert "Alaska" in titles


def test_einstein_retrieval():
    retriever = EvidenceRetriever(corpus_path=FULL_CORPUS)
    titles = [result["title"] for result in retriever.retrieve("Who developed the theory of relativity?", k=3)]
    assert "Albert Einstein" in titles


def test_retrieval_recall():
    test_cases = [
        ("What is the capital of France?", "France"),
        ("Who developed the theory of relativity?", "Albert Einstein"),
        ("Who was Aristotle?", "Aristotle"),
        ("What is ASCII?", "ASCII"),
        ("What is Alaska?", "Alaska"),
        ("What is agriculture?", "Agriculture"),
        ("What is an amphibian?", "Amphibian"),
        ("What is altruism?", "Altruism"),
        ("Who was Abraham Lincoln?", "Abraham Lincoln"),
        ("What is anarchism?", "Anarchism"),
    ]

    retriever = EvidenceRetriever(corpus_path=FULL_CORPUS)

    hits_at_1 = hits_at_3 = hits_at_5 = 0
    for question, expected_title in test_cases:
        titles = [result["title"] for result in retriever.retrieve(question, k=5)]
        print(f"\nQuestion: {question}\nExpected: {expected_title}\nRetrieved: {titles}")
        hits_at_1 += expected_title in titles[:1]
        hits_at_3 += expected_title in titles[:3]
        hits_at_5 += expected_title in titles[:5]

    total = len(test_cases)
    print("\n==============================")
    print("Retrieval Recall")
    print("==============================")
    print(f"Total questions: {total}")
    print(f"Recall@1: {hits_at_1 / total:.2%}")
    print(f"Recall@3: {hits_at_3 / total:.2%}")
    print(f"Recall@5: {hits_at_5 / total:.2%}")

    assert total > 0
