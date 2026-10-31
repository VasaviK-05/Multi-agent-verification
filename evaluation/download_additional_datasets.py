
from pathlib import Path
from datasets import load_dataset

# Project paths
ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "datasets" / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_mnli():
    print("\n" + "=" * 60)
    print("Downloading MultiNLI...")
    print("=" * 60)

    dataset = load_dataset(
        "nyu-mll/glue",
        "mnli"
    )

    output = RAW_DIR / "multinli"

    dataset.save_to_disk(str(output))

    print("\nMultiNLI downloaded successfully!")

    for split, data in dataset.items():
        print(f"{split}: {len(data)} examples")
        print("Columns:", data.column_names)

        if len(data):
            print("Sample:", {
                key: data[0][key]
                for key in ["premise", "hypothesis", "label"]
            })


def download_gsm8k():
    print("\n" + "=" * 60)
    print("Downloading GSM8K...")
    print("=" * 60)

    dataset = load_dataset(
        "openai/gsm8k",
        "main"
    )

    output = RAW_DIR / "gsm8k"

    dataset.save_to_disk(str(output))

    print("\nGSM8K downloaded successfully!")

    for split, data in dataset.items():
        print(f"{split}: {len(data)} examples")
        print("Columns:", data.column_names)

        if len(data):
            print("Sample:", {
                key: data[0][key]
                for key in ["question", "answer"]
            })


if __name__ == "__main__":

    try:
        download_mnli()
    except Exception as e:
        print(f"\nMultiNLI download failed: {e}")

    try:
        download_gsm8k()
    except Exception as e:
        print(f"\nGSM8K download failed: {e}")

    print("\nDownload process completed.")
