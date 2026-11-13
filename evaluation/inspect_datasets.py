
from datasets import load_from_disk
from collections import Counter

DATASETS = {
    "FEVER": "evaluation/datasets/raw/fever",
    "HotpotQA": "evaluation/datasets/raw/hotpotqa"
}

for name, path in DATASETS.items():

    print(f"\n{'=' * 50}\n{name}\n{'=' * 50}")

    dataset = load_from_disk(path)

    for split_name, data in dataset.items():

        print(f"\nSplit: {split_name}")
        print("Total rows:", len(data))
        print("Columns:", data.column_names)

        if len(data) == 0:
            continue

        sample = data[0]

        # Print only important fields
        for field in ["id", "question", "claim", "answer", "label"]:
            if field in sample:
                print(f"{field}: {str(sample[field])[:150]}")

        # Label distribution
        label_field = next(
            (f for f in ["label", "answer"] if f in data.column_names),
            None
        )

        if label_field:
            counts = Counter(
                str(x) for x in data[label_field]
            )
            print("Label distribution:", dict(counts))

print("\nInspection completed.")
