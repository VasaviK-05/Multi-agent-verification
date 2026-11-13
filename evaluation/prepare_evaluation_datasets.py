
import json
import random
from pathlib import Path
from collections import Counter, defaultdict

from datasets import load_from_disk

SEED = 42
random.seed(SEED)

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "datasets" / "raw"
OUTPUT = ROOT / "datasets" / "processed"
MANIFESTS = ROOT / "datasets" / "manifests"

OUTPUT.mkdir(parents=True, exist_ok=True)
MANIFESTS.mkdir(parents=True, exist_ok=True)


def stratified_sample(rows, size, key_fn):
    """Deterministic proportional sampling across categories."""
    groups = defaultdict(list)

    for row in rows:
        groups[key_fn(row)].append(row)

    total = len(rows)
    allocations = {
        key: int(size * len(group) / total)
        for key, group in groups.items()
    }

    remaining = size - sum(allocations.values())

    for key in sorted(
        groups,
        key=lambda k: size * len(groups[k]) / total
        - allocations[k],
        reverse=True
    ):
        if remaining == 0:
            break
        if allocations[key] < len(groups[key]):
            allocations[key] += 1
            remaining -= 1

    result = []

    for key, group in groups.items():
        result.extend(
            random.sample(group, allocations[key])
        )

    random.shuffle(result)
    return result


def save_split(name, records):
    path = OUTPUT / f"{name}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    manifest = {
        "split": name,
        "total_examples": len(records),
        "seed": SEED,
        "datasets": dict(Counter(
            r["dataset"] for r in records
        )),
        "labels": dict(Counter(
            r["ground_truth_label"] for r in records
        ))
    }

    with open(
        MANIFESTS / f"{name}_manifest.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(manifest, f, indent=2)

    print(f"{name}: {len(records)} examples")
    print("  Datasets:", manifest["datasets"])
    print("  Labels:", manifest["labels"])


# -------------------------------------------------
# 1. LOAD DATASETS
# -------------------------------------------------

print("Loading FEVER and HotpotQA...")

fever = load_from_disk(str(RAW / "fever"))
hotpot = load_from_disk(str(RAW / "hotpotqa"))


# -------------------------------------------------
# 2. NORMALIZE FEVER
# -------------------------------------------------


# -------------------------------------------------
# 2. NORMALIZE FEVER
# -------------------------------------------------

def normalize_fever_split(dataset, split):
    """
    Combine multiple evidence annotation rows
    belonging to the same FEVER claim.
    """

    grouped = defaultdict(list)

    for row in dataset:
        grouped[str(row["id"])].append(row)

    records = []

    for claim_id, rows in grouped.items():

        first = rows[0]

        # Verify all annotations have consistent labels.
        labels = {r["label"] for r in rows}

        if len(labels) != 1:
            raise ValueError(
                f"Inconsistent labels for FEVER ID {claim_id}: {labels}"
            )

        def unique_values(field):
            values = []

            for row in rows:
                value = row[field]

                if value is None or value == "":
                    continue

                if value not in values:
                    values.append(value)

            return values

        label = first["label"]

        records.append({
            "id": f"FEVER_{claim_id}",
            "group_id": f"FEVER_CLAIM_{claim_id}",
            "dataset": "fever",
            "source_split": split,
            "task_type": "claim_verification",
            "question": "Verify the following claim: " + first["claim"],
            "claim": first["claim"],
            "candidate_answer": first["claim"],
            "ground_truth_label": label,
            "ground_truth": (
                True if label == "SUPPORTS"
                else False if label == "REFUTES"
                else None
            ),
            "evidence_annotation_ids": unique_values(
                "evidence_annotation_id"
            ),
            "evidence_ids": unique_values("evidence_id"),
            "evidence_urls": unique_values("evidence_wiki_url"),
            "evidence_sentence_ids": unique_values(
                "evidence_sentence_id"
            )
        })

    return records


fever_history = normalize_fever_split(
    fever["train"], "train"
)

fever_dev = normalize_fever_split(
    fever["paper_dev"], "paper_dev"
)

fever_test = normalize_fever_split(
    fever["paper_test"], "paper_test"
)

print("\nFEVER unique claim counts:")
print("History:", len(fever_history))
print("Development:", len(fever_dev))
print("Final Test:", len(fever_test))

# Sample AFTER combining duplicate annotations.
fever_history = stratified_sample(
    fever_history, 2000,
    lambda r: r["ground_truth_label"]
)

fever_dev = stratified_sample(
    fever_dev, 500,
    lambda r: r["ground_truth_label"]
)

fever_test = stratified_sample(
    fever_test, 500,
    lambda r: r["ground_truth_label"]
)


# -------------------------------------------------
# 3. NORMALIZE HOTPOTQA
# -------------------------------------------------

def normalize_hotpot(row, split):
    context = row["context"]

    # Convert Wikipedia paragraphs into readable text.
    paragraphs = []

    for title, sentences in zip(
        context["title"],
        context["sentences"]
    ):
        paragraphs.append({
            "title": title,
            "text": " ".join(sentences)
        })

    return {
        "id": f"HOTPOT_{row['id']}",
        "group_id": f"HOTPOT_{row['id']}",
        "dataset": "hotpotqa",
        "source_split": split,
        "task_type": "question_answering",
        "question": row["question"],
        "candidate_answer": row["answer"],
        "ground_truth_label": "CORRECT",
        "ground_truth": True,
        "answer_type": row["type"],
        "difficulty": row["level"],
        "context": paragraphs,
        "supporting_facts": row["supporting_facts"]
    }


hotpot_history_all = [
    normalize_hotpot(r, "train")
    for r in hotpot["train"]
]

hotpot_validation_all = [
    normalize_hotpot(r, "validation")
    for r in hotpot["validation"]
]

hotpot_history = stratified_sample(
    hotpot_history_all, 2000,
    lambda r: (r["answer_type"], r["difficulty"])
)

# Divide validation into separate development and
# final-test pools using a fixed seed.
random.seed(SEED)
random.shuffle(hotpot_validation_all)

hotpot_dev_pool = hotpot_validation_all[:2000]
hotpot_test_pool = hotpot_validation_all[2000:]

hotpot_dev = stratified_sample(
    hotpot_dev_pool, 500,
    lambda r: (r["answer_type"], r["difficulty"])
)

hotpot_test = stratified_sample(
    hotpot_test_pool, 500,
    lambda r: (r["answer_type"], r["difficulty"])
)


# -------------------------------------------------
# 4. COMBINE DATASETS
# -------------------------------------------------

history = fever_history + hotpot_history
development = fever_dev + hotpot_dev
final_test = fever_test + hotpot_test


# -------------------------------------------------
# 5. VALIDATE IDS AND SAVE
# -------------------------------------------------
from collections import Counter

def inspect_duplicates(records, name):
    counts = Counter(r["id"] for r in records)

    duplicates = {
        key: count
        for key, count in counts.items()
        if count > 1
    }

    print(f"\n{name}:")
    print("Total records:", len(records))
    print("Unique IDs:", len(counts))
    print("Duplicate IDs:", len(duplicates))
    print("Examples:", list(duplicates.items())[:10])
def check_duplicates(records, name):
    ids = [r["id"] for r in records]

    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate IDs found in {name}")


for name, records in [
    ("history", history),
    ("development", development),
    ("final_test", final_test)
]:
    inspect_duplicates(records, name)

history_ids = {r["id"] for r in history}
dev_ids = {r["id"] for r in development}
test_ids = {r["id"] for r in final_test}

assert not (history_ids & dev_ids)
assert not (history_ids & test_ids)
assert not (dev_ids & test_ids)

save_split("history", history)
save_split("development", development)
save_split("final_test", final_test)

print("\nAll datasets prepared successfully!")
print("Total examples:", len(history) + len(development) + len(final_test))
