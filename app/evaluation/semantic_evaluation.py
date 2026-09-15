from datasets import load_dataset
from sentence_transformers import SentenceTransformer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

MODEL_NAME = "all-MiniLM-L6-v2"
THRESHOLD = 0.50
START_INDEX = 8000
EVAL_SIZE = 2000


def main():
    dataset = load_dataset(
        "pminervini/HaluEval",
        "qa",
        split=f"data[{START_INDEX}:{START_INDEX + EVAL_SIZE}]",
    )

    model = SentenceTransformer(MODEL_NAME)

    y_true = []
    y_pred = []

    for item in dataset:
        question = item["question"]
        knowledge = item["knowledge"]

        correct = item["right_answer"]
        hallucinated = item["hallucinated_answer"]

        for answer, label in [
            (correct, 1),
            (hallucinated, 0),
        ]:
            comparison_text = f"{question} {answer}"

            answer_embedding = model.encode(comparison_text)
            knowledge_embedding = model.encode(knowledge)

            from sklearn.metrics.pairwise import cosine_similarity

            score = cosine_similarity(
                [answer_embedding],
                [knowledge_embedding],
            )[0][0]

            y_true.append(label)
            y_pred.append(1 if score >= THRESHOLD else 0)

    print(f"Total examples: {len(y_true)}")
    print()
    print(f"Threshold: {THRESHOLD}")
    print(f"Accuracy:  {accuracy_score(y_true, y_pred):.4f}")
    print(f"Precision: {precision_score(y_true, y_pred, zero_division=0):.4f}")
    print(f"Recall:    {recall_score(y_true, y_pred, zero_division=0):.4f}")
    print(f"F1:        {f1_score(y_true, y_pred, zero_division=0):.4f}")


if __name__ == "__main__":
    main()