from app.verifiers.evidence_retriever import EvidenceRetriever


TEST_CORPUS = "data/evidence_corpus.json"




def test_alaska_retrieval():
    retriever = EvidenceRetriever(corpus_path=TEST_CORPUS)

    results = retriever.retrieve(
        "What is Alaska?",
        k=3,
    )

    titles = [result["title"] for result in results]

    assert "Alaska" in titles


def test_einstein_retrieval():
    retriever = EvidenceRetriever(corpus_path=TEST_CORPUS)

    results = retriever.retrieve(
        "Who developed the theory of relativity?",
        k=3,
    )

    titles = [result["title"] for result in results]

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

    retriever = EvidenceRetriever(corpus_path=TEST_CORPUS)

    hits_at_1 = 0
    hits_at_3 = 0
    hits_at_5 = 0

    for question, expected_title in test_cases:
        results = retriever.retrieve(question, k=5)

        titles = [result["title"] for result in results]

        print(f"\nQuestion: {question}")
        print(f"Expected: {expected_title}")
        print(f"Retrieved: {titles}")

        if expected_title in titles[:1]:
            hits_at_1 += 1

        if expected_title in titles[:3]:
            hits_at_3 += 1

        if expected_title in titles[:5]:
            hits_at_5 += 1

    total = len(test_cases)

    recall_at_1 = hits_at_1 / total
    recall_at_3 = hits_at_3 / total
    recall_at_5 = hits_at_5 / total

    print("\n==============================")
    print("Retrieval Recall")
    print("==============================")
    print(f"Total questions: {total}")
    print(f"Recall@1: {recall_at_1:.2%}")
    print(f"Recall@3: {recall_at_3:.2%}")
    print(f"Recall@5: {recall_at_5:.2%}")

    assert total > 0