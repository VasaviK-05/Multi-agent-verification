from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity


MODEL_NAME = "all-MiniLM-L6-v2"
SAMPLE_SIZE = 8000


def main():
    print("Loading HaluEval...")

    dataset = load_dataset(
        "pminervini/HaluEval",
        "qa",
        split=f"data[:{SAMPLE_SIZE}]",
    )

    model = SentenceTransformer(MODEL_NAME)

    scores = []
    labels = []

    for item in dataset:
        knowledge = item["knowledge"]

        knowledge_embedding = model.encode(knowledge)

        right_embedding = model.encode(item["right_answer"])
        hallucinated_embedding = model.encode(item["hallucinated_answer"])

        right_score = cosine_similarity(
            [right_embedding],
            [knowledge_embedding],
        )[0][0]

        hallucinated_score = cosine_similarity(
            [hallucinated_embedding],
            [knowledge_embedding],
        )[0][0]

        scores.extend([
            float(right_score),
            float(hallucinated_score),
        ])

        labels.extend([1, 0])

    print(f"\nTotal examples: {len(scores)}")

    thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]

    print("\nThreshold Evaluation")
    print("-" * 70)
    print("Threshold | Accuracy | Precision | Recall | F1")
    print("-" * 70)

    for threshold in thresholds:
        predictions = [
            1 if score >= threshold else 0
            for score in scores
        ]

        accuracy = accuracy_score(labels, predictions)
        precision = precision_score(labels, predictions, zero_division=0)
        recall = recall_score(labels, predictions, zero_division=0)
        f1 = f1_score(labels, predictions, zero_division=0)

        print(
            f"{threshold:9.2f} | "
            f"{accuracy:8.4f} | "
            f"{precision:9.4f} | "
            f"{recall:6.4f} | "
            f"{f1:6.4f}"
        )


if __name__ == "__main__":
    main()