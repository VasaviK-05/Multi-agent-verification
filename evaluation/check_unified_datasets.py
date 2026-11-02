
import json
from pathlib import Path
from collections import Counter

ROOT = Path("evaluation/datasets/unified")

for split in ["history", "development", "final_test"]:
    path = ROOT / f"{split}.json"

    with path.open("r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"\n{split}: {len(records)} records")
    print("Keys:", list(records[0].keys()))

    counts = Counter(row.get("dataset") for row in records)
    print("Benchmarks:", dict(counts))

    for dataset in sorted(counts):
        example = next(row for row in records if row.get("dataset") == dataset)
        print(f"\n{dataset} example:")
        print(json.dumps(example, indent=2, ensure_ascii=False)[:1800])
