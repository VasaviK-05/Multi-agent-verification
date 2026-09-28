from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


MODEL_NAME = "all-MiniLM-L6-v2"
SAMPLE_SIZE = 100


def similarity(text1, text2, model):
    emb1 = model.encode(text1)
    emb2 = model.encode(text2)

    return float(
        cosine_similarity([emb1], [emb2])[0][0]
    )


def main():
    dataset = load_dataset(
        "pminervini/HaluEval",
        "qa",
        split=f"data[:{SAMPLE_SIZE}]",
    )

    model = SentenceTransformer(MODEL_NAME)

    answer_knowledge_correct = []
    answer_knowledge_hallucinated = []

    question_answer_correct = []
    question_answer_hallucinated = []

    for item in dataset:
        question = item["question"]
        knowledge = item["knowledge"]

        correct = item["right_answer"]
        hallucinated = item["hallucinated_answer"]

        # Approach 1: answer ↔ knowledge
        answer_knowledge_correct.append(
            similarity(correct, knowledge, model)
        )

        answer_knowledge_hallucinated.append(
            similarity(hallucinated, knowledge, model)
        )

        # Approach 2: question + answer ↔ knowledge
        question_answer_correct.append(
            similarity(
                question + " " + correct,
                knowledge,
                model,
            )
        )

        question_answer_hallucinated.append(
            similarity(
                question + " " + hallucinated,
                knowledge,
                model,
            )
        )

    print("\nAverage Similarity Scores")
    print("-" * 60)

    print(
        f"Answer ↔ Knowledge | Correct: "
        f"{sum(answer_knowledge_correct) / len(answer_knowledge_correct):.4f}"
    )

    print(
        f"Answer ↔ Knowledge | Hallucinated: "
        f"{sum(answer_knowledge_hallucinated) / len(answer_knowledge_hallucinated):.4f}"
    )

    print()

    print(
        f"Question+Answer ↔ Knowledge | Correct: "
        f"{sum(question_answer_correct) / len(question_answer_correct):.4f}"
    )

    print(
        f"Question+Answer ↔ Knowledge | Hallucinated: "
        f"{sum(question_answer_hallucinated) / len(question_answer_hallucinated):.4f}"
    )


if __name__ == "__main__":
    main()