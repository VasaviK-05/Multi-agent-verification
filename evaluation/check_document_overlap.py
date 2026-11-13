
from datasets import load_from_disk
from collections import defaultdict

# FEVER: check shared Wikipedia pages
fever = load_from_disk("evaluation/datasets/raw/fever")

print("\n========== FEVER DOCUMENT OVERLAP ==========")

fever_docs = {}

for split in ["train", "paper_dev", "paper_test"]:
    docs = set()

    for url in fever[split]["evidence_wiki_url"]:
        if isinstance(url, str) and url.strip():
            docs.add(url.strip().lower())

    fever_docs[split] = docs
    print(f"{split}: {len(docs)} unique evidence URLs")

for a, b in [
    ("train", "paper_dev"),
    ("train", "paper_test"),
    ("paper_dev", "paper_test")
]:
    common = fever_docs[a] & fever_docs[b]
    print(f"{a} vs {b}: {len(common)} shared URLs")


# HotpotQA: check shared Wikipedia titles
hotpot = load_from_disk("evaluation/datasets/raw/hotpotqa")

print("\n========== HOTPOTQA DOCUMENT OVERLAP ==========")

hotpot_docs = {}

for split in ["train", "validation"]:
    docs = set()

    for context in hotpot[split]["context"]:
        if isinstance(context, dict):
            docs.update(
                str(title).strip().lower()
                for title in context.get("title", [])
            )

    hotpot_docs[split] = docs
    print(f"{split}: {len(docs)} unique document titles")

common = hotpot_docs["train"] & hotpot_docs["validation"]

print("Shared HotpotQA document titles:", len(common))

print("\nDocument overlap check completed.")
