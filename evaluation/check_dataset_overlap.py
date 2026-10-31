
from datasets import load_from_disk

# ---------------- FEVER ----------------

fever = load_from_disk("evaluation/datasets/raw/fever")

print("\n========== FEVER OVERLAP ==========")

fever_splits = {
    name: set(str(x) for x in data["id"])
    for name, data in fever.items()
    if name in ["train", "labelled_dev", "paper_dev", "paper_test"]
}

names = list(fever_splits)

for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = names[i], names[j]
        overlap = fever_splits[a] & fever_splits[b]

        print(f"{a} vs {b}: {len(overlap)} common IDs")

# ---------------- HOTPOTQA ----------------

hotpot = load_from_disk("evaluation/datasets/raw/hotpotqa")

print("\n========== HOTPOTQA ==========")

for split, data in hotpot.items():
    print(f"\n{split}")
    print("Examples:", len(data))
    print("Unique IDs:", len(set(data["id"])))
    print("Question types:", data.unique("type"))
    print("Difficulty levels:", data.unique("level"))

# Check exact question overlap
train_questions = set(
    q.strip().lower() for q in hotpot["train"]["question"]
)

validation_questions = set(
    q.strip().lower() for q in hotpot["validation"]["question"]
)

print(
    "\nHotpotQA common questions:",
    len(train_questions & validation_questions)
)

print("\nOverlap inspection completed.")
