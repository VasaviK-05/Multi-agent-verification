from app.verifiers.evidence_retriever import EvidenceRetriever


TEST_CORPUS = "data/test_evidence_corpus.json"


def test_france_retrieval():
    retriever = EvidenceRetriever(corpus_path=TEST_CORPUS)

    results = retriever.retrieve(
        "What is the capital of France?",
        k=3,
    )

    titles = [result["title"] for result in results]

    assert "France" in titles or "Paris" in titles


def test_python_retrieval():
    retriever = EvidenceRetriever(corpus_path=TEST_CORPUS)

    results = retriever.retrieve(
        "What is Python?",
        k=3,
    )

    titles = [result["title"] for result in results]

    assert "Python" in titles


def test_einstein_retrieval():
    retriever = EvidenceRetriever(corpus_path=TEST_CORPUS)

    results = retriever.retrieve(
        "Who developed the theory of relativity?",
        k=3,
    )

    titles = [result["title"] for result in results]

    assert "Albert Einstein" in titles