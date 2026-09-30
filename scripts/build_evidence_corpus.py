import json
import os

from datasets import load_dataset


TARGET_COUNT = 500


def build_corpus() -> None:
    dataset = load_dataset(
        "wikimedia/wikipedia",
        "20231101.en",
        split="train",
        streaming=True,
    )

    articles = []

    for article in dataset:
        articles.append(article)

        if len(articles) >= TARGET_COUNT:
            break

    os.makedirs("data", exist_ok=True)

    with open(
        "data/evidence_corpus.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            articles,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Saved articles: {len(articles)}")
    print("Output: data/evidence_corpus.json")


if __name__ == "__main__":
    build_corpus()