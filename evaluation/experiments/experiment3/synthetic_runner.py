"""Write the synthetic Experiment 3 report. This does not run Development or a Final Test."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.game.research.experiment3 import write_synthetic_outputs


def main():
    destination = ROOT / "evaluation" / "experiments" / "experiment3" / "synthetic"
    write_synthetic_outputs(destination)
    print(f"SYNTHETIC Experiment 3 outputs written to {destination}")


if __name__ == "__main__":
    main()
