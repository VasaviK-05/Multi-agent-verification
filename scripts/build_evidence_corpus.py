import json
import os

from datasets import load_dataset
from dotenv import load_dotenv


TARGET_COUNT = 500
DEFAULT_CORPUS_PATH = "data/evidence_corpus.json"


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

    load_dotenv()
    output = os.getenv("EVIDENCE_CORPUS_PATH", DEFAULT_CORPUS_PATH)
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    with open(
        output,
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
    print(f"Output: {output}")


if __name__ == "__main__":
    build_corpus()