
import json
import random
import re
from collections import defaultdict, Counter
from pathlib import Path

from datasets import load_from_disk


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation" / "datasets" / "raw"
OUTPUT = ROOT / "evaluation" / "datasets" / "unified"

SEED = 42
HISTORY_SIZE = 2000
DEV_SIZE = 500
FINAL_SIZE = 500

random.seed(SEED)


def save_json(name, records):
    path = OUTPUT / name
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(records)} records -> {path}")


def sample_records(records, count, seed=SEED):
    """Deterministic random sample."""
    if len(records) < count:
        raise ValueError(
            f"Requested {count} records, but only {len(records)} available."
        )

    rng = random.Random(seed)
    return rng.sample(records, count)


def normalize_answer(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


# ---------------------------------------------------------
# FEVER
# ---------------------------------------------------------

def group_fever_claims(dataset):
    """
    FEVER may contain multiple evidence-annotation rows
    for the same claim. Group by claim ID before sampling.
    """
    grouped = {}

    for row in dataset:
        claim_id = str(row["id"])
        label = row["label"]

        if claim_id not in grouped:
            grouped[claim_id] = {
                "id": f"fever_{claim_id}",
                "benchmark": "FEVER",
                "task_type": "fact_verification",
                "claim": row["claim"],
                "label": label,
                "evidence_urls": set(),
                "evidence_sentence_ids": set(),
                "evidence_ids": set(),
            }
        else:
            if grouped[claim_id]["label"] != label:
                raise ValueError(
                    f"Inconsistent labels for FEVER claim {claim_id}"
                )

        record = grouped[claim_id]

        if row.get("evidence_wiki_url"):
            record["evidence_urls"].add(row["evidence_wiki_url"])

        if row.get("evidence_sentence_id") is not None:
            record["evidence_sentence_ids"].add(
                str(row["evidence_sentence_id"])
            )

        if row.get("evidence_id") is not None:
            record["evidence_ids"].add(str(row["evidence_id"]))

    results = []

    for record in grouped.values():
        for key in (
            "evidence_urls",
            "evidence_sentence_ids",
            "evidence_ids",
        ):
            record[key] = sorted(record[key])

        results.append(record)

    return results


def prepare_fever():
    print("\nPreparing FEVER...")

    fever = load_from_disk(str(RAW / "fever"))

    history = group_fever_claims(fever["train"])
    development = group_fever_claims(fever["paper_dev"])
    final_test = group_fever_claims(fever["paper_test"])

    history = sample_records(history, HISTORY_SIZE, SEED)
    development = sample_records(development, DEV_SIZE, SEED + 1)
    final_test = sample_records(final_test, FINAL_SIZE, SEED + 2)

    return history, development, final_test


# ---------------------------------------------------------
# HOTPOTQA
# ---------------------------------------------------------

def normalize_hotpot(row, index):
    context = []

    titles = row["context"]["title"]
    sentences = row["context"]["sentences"]

    for title, paragraph_sentences in zip(titles, sentences):
        context.append({
            "title": title,
            "text": " ".join(paragraph_sentences),
        })

    supporting_facts = []

    for title, sentence_id in zip(
        row["supporting_facts"]["title"],
        row["supporting_facts"]["sent_id"],
    ):
        supporting_facts.append({
            "title": title,
            "sentence_id": sentence_id,
        })

    return {
        "id": f"hotpot_{row['id']}",
        "benchmark": "HotpotQA",
        "task_type": "multi_hop_question_answering",
        "question": row["question"],
        "gold_answer": str(row["answer"]),
        "question_type": row["type"],
        "difficulty": row["level"],
        "context": context,
        "supporting_facts": supporting_facts,
    }


def add_hotpot_negative_candidates(records):
    """
    Create synthetic negative answers by borrowing another
    example's gold answer. These are not official benchmark
    annotations and require validation/auditing.
    """
    answers = [record["gold_answer"] for record in records]
    results = []

    for i, record in enumerate(records):
        negative = None

        for offset in range(1, len(answers)):
            candidate = answers[(i + offset) % len(answers)]

            if normalize_answer(candidate) != normalize_answer(
                record["gold_answer"]
            ):
                negative = candidate
                break

        if negative is None:
            raise ValueError("Could not generate a distinct HotpotQA negative.")

        record["candidate_answers"] = [
            {
                "answer": record["gold_answer"],
                "expected_correct": True,
                "source": "benchmark_gold",
            },
            {
                "answer": negative,
                "expected_correct": False,
                "source": "synthetic_cross_example_answer",
            },
        ]

        results.append(record)

    return results


def prepare_hotpot():
    print("\nPreparing HotpotQA...")

    hotpot = load_from_disk(str(RAW / "hotpotqa"))

    train = [
        normalize_hotpot(row, i)
        for i, row in enumerate(hotpot["train"])
    ]

    validation = [
        normalize_hotpot(row, i)
        for i, row in enumerate(hotpot["validation"])
    ]

    # Split validation deterministically into separate dev/final pools.
    rng = random.Random(SEED + 10)
    rng.shuffle(validation)

    development = validation[:DEV_SIZE]
    final_test = validation[DEV_SIZE:DEV_SIZE + FINAL_SIZE]

    history = sample_records(train, HISTORY_SIZE, SEED + 3)

    history = add_hotpot_negative_candidates(history)
    development = add_hotpot_negative_candidates(development)
    final_test = add_hotpot_negative_candidates(final_test)

    return history, development, final_test


# ---------------------------------------------------------
# MULTINLI
# ---------------------------------------------------------

def prepare_mnli():
    print("\nPreparing MultiNLI...")

    mnli = load_from_disk(str(RAW / "multinli"))

    label_feature = mnli["train"].features["label"]
    label_names = label_feature.names

    print("MultiNLI label mapping:", label_names)

    def normalize(row, index, split_name):
        label_id = int(row["label"])

        if label_id < 0 or label_id >= len(label_names):
            raise ValueError(
                f"Invalid MultiNLI label {label_id} in {split_name}"
            )

        return {
            "id": f"mnli_{split_name}_{row['idx']}",
            "benchmark": "MultiNLI",
            "task_type": "natural_language_inference",
            "premise": row["premise"],
            "hypothesis": row["hypothesis"],
            "label_id": label_id,
            "label": label_names[label_id],
        }

    train = [
        normalize(row, i, "train")
        for i, row in enumerate(mnli["train"])
    ]

    matched = [
        normalize(row, i, "validation_matched")
        for i, row in enumerate(mnli["validation_matched"])
    ]

    mismatched = [
        normalize(row, i, "validation_mismatched")
        for i, row in enumerate(mnli["validation_mismatched"])
    ]

    history = sample_records(train, HISTORY_SIZE, SEED + 4)
    development = sample_records(matched, DEV_SIZE, SEED + 5)
    final_test = sample_records(mismatched, FINAL_SIZE, SEED + 6)

    return history, development, final_test


# ---------------------------------------------------------
# GSM8K
# ---------------------------------------------------------

def extract_gsm8k_answer(solution):
    """
    GSM8K final answers normally follow the #### marker.
    """
    match = re.search(r"####\s*(-?[\d,]+(?:\.\d+)?)", solution)

    if not match:
        raise ValueError(
            f"Could not extract GSM8K final answer: {solution[-100:]}"
        )

    return match.group(1).replace(",", "")


def normalize_gsm8k(row, index, split_name):
    gold = extract_gsm8k_answer(row["answer"])

    try:
        numeric_gold = float(gold)
    except ValueError:
        raise ValueError(f"Invalid GSM8K numeric answer: {gold}")

    # Deliberately simple synthetic negative.
    negative = str(int(numeric_gold + 1)) if numeric_gold.is_integer() else str(
        numeric_gold + 1
    )

    return {
        "id": f"gsm8k_{split_name}_{index}",
        "benchmark": "GSM8K",
        "task_type": "arithmetic_reasoning",
        "question": row["question"],
        "solution": row["answer"],
        "gold_answer": gold,
        "candidate_answers": [
            {
                "answer": gold,
                "expected_correct": True,
                "source": "benchmark_gold",
            },
            {
                "answer": negative,
                "expected_correct": False,
                "source": "synthetic_numeric_perturbation",
            },
        ],
    }


def prepare_gsm8k():
    print("\nPreparing GSM8K...")

    gsm = load_from_disk(str(RAW / "gsm8k"))

    train = [
        normalize_gsm8k(row, i, "train")
        for i, row in enumerate(gsm["train"])
    ]

    test = [
        normalize_gsm8k(row, i, "test")
        for i, row in enumerate(gsm["test"])
    ]

    # Use separate deterministic portions of the training split.
    rng = random.Random(SEED + 20)
    rng.shuffle(train)

    history = train[:HISTORY_SIZE]
    development = train[HISTORY_SIZE:HISTORY_SIZE + DEV_SIZE]
    final_test = sample_records(test, FINAL_SIZE, SEED + 7)

    return history, development, final_test


# ---------------------------------------------------------
# VALIDATION AND OUTPUT
# ---------------------------------------------------------

def check_split(name, records):
    ids = [record["id"] for record in records]

    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate IDs found in {name}")

    counts = Counter(record["benchmark"] for record in records)

    print(f"\n{name}: {len(records)} records")
    print("Benchmark counts:", dict(counts))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    fever = prepare_fever()
    hotpot = prepare_hotpot()
    mnli = prepare_mnli()
    gsm = prepare_gsm8k()

    history = fever[0] + hotpot[0] + mnli[0] + gsm[0]
    development = fever[1] + hotpot[1] + mnli[1] + gsm[1]
    final_test = fever[2] + hotpot[2] + mnli[2] + gsm[2]

    # Shuffle combined files without changing their contents.
    random.Random(SEED).shuffle(history)
    random.Random(SEED + 1).shuffle(development)
    random.Random(SEED + 2).shuffle(final_test)

    check_split("History", history)
    check_split("Development", development)
    check_split("Final test", final_test)

    history_ids = {record["id"] for record in history}
    development_ids = {record["id"] for record in development}
    final_ids = {record["id"] for record in final_test}

    assert history_ids.isdisjoint(development_ids)
    assert history_ids.isdisjoint(final_ids)
    assert development_ids.isdisjoint(final_ids)

    save_json("history.json", history)
    save_json("development.json", development)
    save_json("final_test.json", final_test)

    print("\nAll four benchmarks prepared successfully.")
    print("Output directory:", OUTPUT)


if __name__ == "__main__":
    main()
