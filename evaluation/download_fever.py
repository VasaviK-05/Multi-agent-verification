from datasets import load_dataset

print("Downloading FEVER dataset...")

fever = load_dataset(
    "fever/fever",
    "v1.0",
    trust_remote_code=True
)

print("\nDataset downloaded successfully!")
print(fever)

for split in fever:
    print(f"{split}: {len(fever[split])} examples")

fever.save_to_disk("evaluation/datasets/raw/fever")

print("\nFEVER saved successfully!")