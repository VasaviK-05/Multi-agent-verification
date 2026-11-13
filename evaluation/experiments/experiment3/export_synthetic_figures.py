"""Export figures from the existing synthetic fixture. Does not rerun or overwrite results.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "evaluation/experiments/experiment3/synthetic/results.json"
DESTINATION = ROOT / "evaluation/experiments/experiment3/synthetic/figures"


def _svg(title: str, body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="880" height="460" viewBox="0 0 880 460">'
        '<rect width="100%" height="100%" fill="white"/>'
        f'<text x="24" y="28" font-size="18">{title} (SYNTHETIC fixture)</text>'
        '<text x="24" y="50" font-size="12">Hand-built fixture cells. Not Development groups and not an empirical result.</text>'
        f'{body}<desc>SYNTHETIC</desc></svg>'
    )


def extract() -> dict:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    configurations = payload["configurations"]
    rows = []
    for name, configuration in configurations.items():
        for method, block in configuration["methods"].items():
            for attack in block["attacks"]:
                rows.append({
                    "configuration": name,
                    "aggregation_method": method,
                    "attack": attack["attack"]["kind"],
                    "members": attack["attack"]["members"],
                    "loss": attack["loss"],
                    "coverage": attack["coverage"],
                    "uncertainty": attack["uncertainty"],
                    "false_acceptance": attack["false_acceptance"],
                    "false_rejection": attack["false_rejection"],
                    "selective_risk": attack["selective_risk"],
                    "cost": attack["cost"],
                    "worst_case_expected_loss": block["worst_case_expected_loss"],
                    "aggregation_selection_frequencies": block["aggregation_selection_frequencies"],
                })
    return {
        "evidence_label": "SYNTHETIC",
        "empirical_claim": False,
        "sample": "one hand-built fixture, not the 372 Development groups",
        "source": "evaluation/experiments/experiment3/synthetic/results.json",
        "results_file_unchanged": True,
        "rows": rows,
    }


def _bars(table: dict) -> str:
    colors = {"full_minimax": "#1b4f72", "fixed_reputation_weighted": "#b9770e", "fixed_dependency_group": "#196f3d"}
    parts = []
    shared = [row for row in table["rows"] if row["configuration"] == "shared_unknown" and row["attack"] == "clean"]
    for index, row in enumerate(shared):
        height = 180 * float(row["loss"])
        parts.append(f'<rect x="{80 + index * 80}" y="{300 - height:.1f}" width="40" height="{height:.1f}" fill="{colors[row["aggregation_method"]]}"/>')
        parts.append(f'<text x="{80 + index * 80}" y="320" font-size="11">{row["aggregation_method"]}</text>')
        parts.append(f'<text x="{80 + index * 80}" y="336" font-size="11">loss={row["loss"]}</text>')
    parts.append('<text x="24" y="380" font-size="12">Clean shared_unknown cells. Coverage is plotted as text because several cells have coverage 0.</text>')
    for index, row in enumerate(shared):
        parts.append(f'<text x="{80 + index * 80}" y="400" font-size="11">coverage={row["coverage"]}</text>')
    return "".join(parts)


def main() -> int:
    table = extract()
    DESTINATION.mkdir(parents=True, exist_ok=True)
    (DESTINATION / "fixture_metrics.json").write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
    (DESTINATION / "aggregation_clean_shared_unknown.svg").write_text(_svg("Aggregation ablation", _bars(table)), encoding="utf-8")
    (DESTINATION / "hypothetical_dependency_losses.svg").write_text(
        _svg("Dependency heatmap", '<text x="24" y="140" font-size="16">Not estimable. Hypothetical dependency losses were not filled.</text>'),
        encoding="utf-8",
    )
    print(f"SYNTHETIC fixture figures written to {DESTINATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
