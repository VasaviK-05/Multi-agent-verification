from datasets import load_dataset

print("Downloading HotpotQA...")

hotpot = load_dataset(
    "hotpotqa/hotpot_qa",
    "distractor"
)

hotpot.save_to_disk(
    "evaluation/datasets/raw/hotpotqa"
)

for split, dataset in hotpot.items():
    print(f"\n{split}: {len(dataset)} examples")
    print("Columns:", dataset.column_names)

print("\nDownload complete!")