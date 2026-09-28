"""Build a small targeted Wikipedia evidence corpus."""

import json
import os

from datasets import load_dataset


TARGET_TITLES = {
    "France",
    "Paris",
    "Germany",
    "India",
    "Python (programming language)",
    "Artificial intelligence",
    "Machine learning",
    "Albert Einstein",
    "World War II",
    "United States",
}


def build_corpus() -> None:
    dataset = load_dataset(
        "wikimedia/wikipedia",
        "20231101.en",
        split="train",
        streaming=True,
    )

    articles = []

    for article in dataset:
        if article["title"] in TARGET_TITLES:
            articles.append(article)
            print(f"Found: {article['title']}")

        if len(articles) == len(TARGET_TITLES):
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

    print(f"\nSaved articles: {len(articles)}")
    print("Output: data/evidence_corpus.json")


if __name__ == "__main__":
    build_corpus()
    