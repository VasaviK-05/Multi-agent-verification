"""Write the empirical validation-loss figure from stored metrics.

The figure is labeled EMPIRICAL. It reads metrics.json and does not call verifiers.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
METRICS = ROOT / "evaluation/experiments/experiment3/empirical/metrics.json"
DESTINATION = ROOT / "evaluation/experiments/experiment3/empirical/figures/attack_validation_loss.svg"


def _bars() -> list[dict]:
    payload = json.loads(METRICS.read_text(encoding="utf-8"))
    rows = [
        row for row in payload["analysis"]["metrics"]
        if row["aggregation_method"] == "full_minimax" and row["status"] == "available"
    ]
    order = {"clean": 0, "forced_support": 1, "forced_rejection": 2, "confidence_inflation": 3}
    rows.sort(key=lambda row: (row["benchmark"], order[row["attack_condition"].split()[0]], row["attack_condition"]))
    return rows


def render(rows: list[dict]) -> str:
    width, height = 1180, 520
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="28" font-size="18">EMPIRICAL Development validation loss</text>',
        '<text x="24" y="50" font-size="12">Decision loss only. full_minimax, fixed_reputation_weighted, and fixed_dependency_group matched on every cell.</text>',
        '<text x="24" y="68" font-size="12">Bar labels are the stored mean validation loss. This figure is not a synthetic sensitivity result.</text>',
    ]
    scale = 0.40
    plot_bottom = 390
    plot_height = 250
    for index, row in enumerate(rows):
        panel = 0 if row["benchmark"] == "GSM8K" else 1
        local = index if panel == 0 else index - 7
        x = 70 + panel * 560 + local * 72
        value = float(row["validation_loss"])
        bar = plot_height * value / scale
        y = plot_bottom - bar
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="36" height="{bar:.1f}" fill="#1b4f72"/>')
        parts.append(f'<text x="{x}" y="{y - 6:.1f}" font-size="10">{value:.3f}</text>')
        label = row["attack_condition"].replace(" [", "\n[")
        parts.append(f'<text x="{x}" y="408" font-size="9">{label.split()[0]}</text>')
        target = row["attack_condition"].split("[", 1)[-1].rstrip("]") if "[" in row["attack_condition"] else "none"
        short = "rule" if target == "rule" else ("models" if "confidence" in target else "clean")
        parts.append(f'<text x="{x}" y="422" font-size="9">{short}</text>')
    parts.append('<text x="70" y="96" font-size="13">GSM8K, 374 candidates per bar</text>')
    parts.append('<text x="630" y="96" font-size="13">HotpotQA, 370 candidates per bar</text>')
    parts.append('<text x="24" y="460" font-size="12">EMPIRICAL. Development only. 744 candidates, 372 groups, 15,624 completed cells. Rates and denominators are in the results document.</text>')
    parts.append("<desc>EMPIRICAL</desc></svg>")
    return "".join(parts)


def main() -> None:
    rows = _bars()
    if len(rows) != 14:
        raise SystemExit(f"expected 14 full_minimax cells, found {len(rows)}")
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(render(rows), encoding="utf-8")
    print(DESTINATION)


if __name__ == "__main__":
    main()
