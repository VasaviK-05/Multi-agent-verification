"""Draw EMPIRICAL figures from the diagnosis file. Synthetic plots are not inputs.

The existing ``attack_validation_loss.svg`` is left unchanged.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIAGNOSIS = ROOT / "evaluation/experiments/experiment3/empirical/diagnosis/policy_diagnosis.json"
FIGURES = ROOT / "evaluation/experiments/experiment3/empirical/figures"
PRESERVED = FIGURES / "attack_validation_loss.svg"

METHOD_COLORS = {
    "full_minimax": "#1b4f72",
    "fixed_reputation_weighted": "#b9770e",
    "fixed_dependency_group": "#196f3d",
}
ATTACK_ORDER = (
    "clean",
    "forced_support [confidence,evidence,semantic]",
    "forced_support [rule]",
    "forced_rejection [confidence,evidence,semantic]",
    "forced_rejection [rule]",
    "confidence_inflation [confidence,evidence,semantic]",
    "confidence_inflation [rule]",
)
SHORT_ATTACK = {
    "clean": "clean",
    "forced_support [confidence,evidence,semantic]": "support models",
    "forced_support [rule]": "support rule",
    "forced_rejection [confidence,evidence,semantic]": "reject models",
    "forced_rejection [rule]": "reject rule",
    "confidence_inflation [confidence,evidence,semantic]": "inflation models",
    "confidence_inflation [rule]": "inflation rule",
}


def _escape(value) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _write(destination: Path, body: str) -> Path:
    text = destination.as_posix().lower()
    if "synthetic" in text:
        raise ValueError("empirical figure cannot be written under a synthetic path")
    if destination.resolve() == PRESERVED.resolve():
        raise ValueError("refusing to overwrite the preserved attack_validation_loss.svg")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if "<desc>EMPIRICAL</desc>" not in body:
        body = body.replace("</svg>", "<desc>EMPIRICAL</desc></svg>")
    destination.write_text(body, encoding="utf-8")
    return destination


def _frame(width: int, height: int, title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="28" y="28" font-size="18" font-family="Cambria, serif">{_escape(title)}</text>',
        f'<text x="28" y="50" font-size="12" font-family="Calibri, sans-serif" fill="#333">{_escape(subtitle)}</text>',
    ]


def _bars(parts: list[str], *, origin_x: int, origin_y: int, width: int, height: int, scale: float, series: list[dict]) -> None:
    parts.append(f'<line x1="{origin_x}" y1="{origin_y - height}" x2="{origin_x}" y2="{origin_y}" stroke="#222"/>')
    parts.append(f'<line x1="{origin_x}" y1="{origin_y}" x2="{origin_x + width}" y2="{origin_y}" stroke="#222"/>')
    for tick in range(5):
        value = scale * tick / 4
        y = origin_y - height * tick / 4
        parts.append(f'<line x1="{origin_x - 4}" y1="{y:.1f}" x2="{origin_x}" y2="{y:.1f}" stroke="#222"/>')
        parts.append(f'<text x="{origin_x - 8}" y="{y + 4:.1f}" font-size="11" text-anchor="end" font-family="Calibri, sans-serif">{value:.2f}</text>')
    group_width = width / max(1, len(series[0]["values"]))
    bar_width = min(18, (group_width - 8) / len(series))
    for group, label in enumerate(series[0]["labels"]):
        for index, item in enumerate(series):
            value = item["values"][group]
            bar = 0 if scale == 0 else height * value / scale
            x = origin_x + 12 + group * group_width + index * (bar_width + 2)
            y = origin_y - bar
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar:.1f}" fill="{item["color"]}"/>')
        parts.append(
            f'<text x="{origin_x + 12 + group * group_width:.1f}" y="{origin_y + 16}" font-size="10" font-family="Calibri, sans-serif">{_escape(label)}</text>'
        )


def _legend(parts: list[str], series: list[dict], x: int, y: int) -> None:
    for index, item in enumerate(series):
        parts.append(f'<rect x="{x}" y="{y + index * 18}" width="12" height="12" fill="{item["color"]}"/>')
        parts.append(f'<text x="{x + 18}" y="{y + 11 + index * 18}" font-size="12" font-family="Calibri, sans-serif">{_escape(item["name"])}</text>')


def attack_loss_figure(payload: dict, destination: Path) -> Path:
    rows = {row["attack"]: row for row in payload["slices"]["by_attack"]}
    labels = [SHORT_ATTACK[name] for name in ATTACK_ORDER]
    values = [rows[name]["mean_decision_loss"] for name in ATTACK_ORDER]
    series = [
        {"name": "full_minimax", "color": METHOD_COLORS["full_minimax"], "labels": labels, "values": values},
        {"name": "fixed_reputation_weighted", "color": METHOD_COLORS["fixed_reputation_weighted"], "labels": labels, "values": values},
        {"name": "fixed_dependency_group", "color": METHOD_COLORS["fixed_dependency_group"], "labels": labels, "values": values},
    ]
    parts = _frame(1100, 460, "EMPIRICAL attack-wise decision loss", "Each bar is the mean decision loss over 744 candidates. The three methods match on every cell, so the three bars in a group have the same height.")
    _bars(parts, origin_x=70, origin_y=360, width=760, height=260, scale=0.40, series=series)
    _legend(parts, series, 860, 90)
    parts.append('<text x="28" y="420" font-size="12" font-family="Calibri, sans-serif">Decision loss excludes the resource penalty. Denominator: 744 candidates per attack. Execution failures: 0.</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts))


def _benchmark_rows(payload: dict, attack: str) -> dict[str, dict]:
    return {
        row["benchmark"]: row
        for row in payload["slices"]["by_benchmark_and_attack"]
        if row["attack"] == attack
    }


def coverage_figure(payload: dict, destination: Path) -> Path:
    clean = _benchmark_rows(payload, "clean")
    attacked = _benchmark_rows(payload, "forced_support [confidence,evidence,semantic]")
    labels = ["GSM8K clean", "GSM8K support", "HotpotQA clean", "HotpotQA support"]
    coverage = [clean["GSM8K"]["coverage"], attacked["GSM8K"]["coverage"], clean["HotpotQA"]["coverage"], attacked["HotpotQA"]["coverage"]]
    uncertainty = [1 - value for value in coverage]
    series = [
        {"name": "Coverage", "color": "#1b4f72", "labels": labels, "values": coverage},
        {"name": "Uncertainty", "color": "#7f8c8d", "labels": labels, "values": uncertainty},
    ]
    parts = _frame(1100, 460, "EMPIRICAL coverage and uncertainty by benchmark", "Clean versus forced support of the confidence/evidence/semantic component. GSM8K denominator 374. HotpotQA denominator 370.")
    _bars(parts, origin_x=70, origin_y=360, width=760, height=260, scale=1.0, series=series)
    _legend(parts, series, 860, 90)
    parts.append('<text x="28" y="420" font-size="12" font-family="Calibri, sans-serif">Coverage counts passed and failed decisions. Uncertainty is the complement. These bars are one attack, not the seven-attack pool.</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts))


def selective_risk_figure(payload: dict, destination: Path) -> Path:
    rows = _benchmark_rows(payload, "clean")
    attacked = _benchmark_rows(payload, "forced_support [confidence,evidence,semantic]")
    labels = [
        f"GSM8K clean n={rows['GSM8K']['classified']}",
        f"GSM8K support n={attacked['GSM8K']['classified']}",
        f"HotpotQA clean n={rows['HotpotQA']['classified']}",
        f"HotpotQA support n={attacked['HotpotQA']['classified']}",
    ]
    values = [rows["GSM8K"]["selective_risk"], attacked["GSM8K"]["selective_risk"], rows["HotpotQA"]["selective_risk"], attacked["HotpotQA"]["selective_risk"]]
    series = [{"name": "Selective risk", "color": "#6c3483", "labels": labels, "values": values}]
    parts = _frame(1100, 460, "EMPIRICAL selective risk by benchmark", "Selective risk is errors divided by classified decisions. The n in each label is that denominator, not the candidate count.")
    _bars(parts, origin_x=70, origin_y=360, width=860, height=260, scale=1.0, series=series)
    parts.append('<text x="28" y="430" font-size="12" font-family="Calibri, sans-serif">GSM8K classifies 11 clean candidates and 19 under model-component forced support. Those rates are unstable.</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts))


def false_rate_figure(payload: dict, destination: Path) -> Path:
    rows = {row["attack"]: row for row in payload["slices"]["by_attack"]}
    labels = [SHORT_ATTACK[name] for name in ATTACK_ORDER]
    false_accept = [rows[name]["false_acceptance_rate"] or 0.0 for name in ATTACK_ORDER]
    false_reject = [rows[name]["false_rejection_rate"] or 0.0 for name in ATTACK_ORDER]
    series = [
        {"name": "False acceptance rate", "color": "#922b21", "labels": labels, "values": false_accept},
        {"name": "False rejection rate", "color": "#1a5276", "labels": labels, "values": false_reject},
    ]
    parts = _frame(1100, 480, "EMPIRICAL false acceptance and false rejection by attack", "Rates use classified negatives or positives. A missing class would be omitted; every plotted cell has a positive denominator.")
    _bars(parts, origin_x=70, origin_y=360, width=760, height=250, scale=1.0, series=series)
    _legend(parts, series, 860, 90)
    notes = []
    for name in ATTACK_ORDER:
        row = rows[name]
        notes.append(f"{SHORT_ATTACK[name]} FA {row['false_acceptance']}/{row['false_acceptance_denominator']} FR {row['false_rejection']}/{row['false_rejection_denominator']}")
    parts.append(f'<text x="28" y="430" font-size="11" font-family="Calibri, sans-serif">{_escape("; ".join(notes[:4]))}</text>')
    parts.append(f'<text x="28" y="448" font-size="11" font-family="Calibri, sans-serif">{_escape("; ".join(notes[4:]))}</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts))


def verifier_figure(payload: dict, destination: Path) -> Path:
    summary = payload["verifier_summary"]["by_verifier"]
    parts = _frame(1100, 520, "EMPIRICAL verifier decisions by benchmark", "Counts are clean recorded reports, before attack transforms. Denominators: GSM8K 374 and HotpotQA 370.")
    colors = {"UNSURE": "#7f8c8d", "SUPPORT": "#1e8449", "REJECT": "#922b21"}
    names = ("semantic", "evidence", "rule", "confidence")
    benchmarks = ("GSM8K", "HotpotQA")
    totals = {"GSM8K": 374, "HotpotQA": 370}
    origin_x, origin_y, height = 160, 400, 280
    parts.append(f'<line x1="{origin_x}" y1="80" x2="{origin_x}" y2="{origin_y}" stroke="#222"/>')
    parts.append(f'<line x1="{origin_x}" y1="{origin_y}" x2="1040" y2="{origin_y}" stroke="#222"/>')
    for index, name in enumerate(names):
        for bench_index, benchmark in enumerate(benchmarks):
            x = origin_x + 40 + index * 220 + bench_index * 70
            y = origin_y
            counts = summary[name]["decisions"].get(benchmark, {})
            for decision in ("REJECT", "SUPPORT", "UNSURE"):
                count = counts.get(decision, 0)
                bar = height * count / totals[benchmark]
                y -= bar
                parts.append(f'<rect x="{x}" y="{y:.1f}" width="48" height="{bar:.1f}" fill="{colors[decision]}"/>')
            parts.append(f'<text x="{x}" y="{origin_y + 18}" font-size="11" font-family="Calibri, sans-serif">{benchmark}</text>')
        parts.append(f'<text x="{origin_x + 40 + index * 220}" y="70" font-size="14" font-family="Calibri, sans-serif">{name}</text>')
    for index, (decision, color) in enumerate(colors.items()):
        parts.append(f'<rect x="860" y="{100 + index * 22}" width="12" height="12" fill="{color}"/>')
        parts.append(f'<text x="878" y="{111 + index * 22}" font-size="12" font-family="Calibri, sans-serif">{decision}</text>')
    parts.append('<text x="28" y="460" font-size="12" font-family="Calibri, sans-serif">GSM8K semantic is UNSURE on all 374 candidates, reason no_context. Rule is UNSURE on 742 of 744 candidates.</text>')
    parts.append('<text x="28" y="480" font-size="12" font-family="Calibri, sans-serif">Recorded wall time is not the frozen calibration cost used for feasibility.</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts))


def team_figure(payload: dict, destination: Path) -> Path:
    chosen = [row for row in payload["policy"]["strategies"] if row["aggregation"] == "reputation_weighted"]
    chosen = sorted(chosen, key=lambda row: row["worst_augmented_loss"])
    parts = _frame(1100, 520, "EMPIRICAL feasible-team worst-case loss", "Worst attack-column mean of decision loss plus the selected resource penalty. Both aggregations match. Highlighted team is the unique optimum inside each aggregation.")
    origin_x, origin_y = 280, 450
    scale = 0.60
    width = 700
    for index, row in enumerate(chosen):
        y = 90 + index * 48
        bar = width * row["worst_augmented_loss"] / scale
        color = "#1b4f72" if row["verifiers"] == ["evidence", "rule"] else "#85929e"
        parts.append(f'<rect x="{origin_x}" y="{y}" width="{bar:.1f}" height="28" fill="{color}"/>')
        parts.append(f'<text x="{origin_x - 12}" y="{y + 19}" font-size="13" text-anchor="end" font-family="Calibri, sans-serif">{_escape(" + ".join(row["verifiers"]))}</text>')
        parts.append(f'<text x="{origin_x + bar + 8:.1f}" y="{y + 19}" font-size="12" font-family="Calibri, sans-serif">{row["worst_augmented_loss"]:.3f}</text>')
    parts.append(f'<line x1="{origin_x}" y1="80" x2="{origin_x}" y2="{origin_y}" stroke="#222"/>')
    parts.append('<text x="28" y="490" font-size="12" font-family="Calibri, sans-serif">EMPIRICAL scores of every feasible team on the stored reports. Confidence-bearing teams include a penalty near 0.20.</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts))


def _log_x(cost: float) -> float:
    start, end = math.log10(50), math.log10(20000)
    return 120 + 820 * (math.log10(cost) - start) / (end - start)


def tradeoff_figure(payload: dict, destination: Path) -> Path:
    chosen = [row for row in payload["policy"]["strategies"] if row["aggregation"] == "reputation_weighted"]
    parts = _frame(1100, 520, "EMPIRICAL team cost and clean coverage", "Each point is one feasible team scored on the stored clean reports. X is the frozen-mean team cost, on a log scale. Coverage denominator: 744.")
    origin_y = 420
    parts.append(f'<line x1="120" y1="80" x2="120" y2="{origin_y}" stroke="#222"/>')
    parts.append(f'<line x1="120" y1="{origin_y}" x2="960" y2="{origin_y}" stroke="#222"/>')
    for tick in (0, 0.25, 0.5, 0.75, 1):
        y = origin_y - 300 * tick
        parts.append(f'<text x="112" y="{y + 4:.1f}" font-size="11" text-anchor="end" font-family="Calibri, sans-serif">{tick:.2f}</text>')
    for cost in (100, 1000, 10000):
        x = _log_x(cost)
        parts.append(f'<text x="{x:.1f}" y="{origin_y + 18}" font-size="11" text-anchor="middle" font-family="Calibri, sans-serif">{cost:g} ms</text>')
    for row in chosen:
        x = _log_x(row["estimated_cost_ms"])
        y = origin_y - 300 * row["clean_coverage"]
        color = "#1b4f72" if row["verifiers"] == ["evidence", "rule"] else "#922b21"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}"/>')
        parts.append(f'<text x="{x + 8:.1f}" y="{y - 8:.1f}" font-size="11" font-family="Calibri, sans-serif">{_escape(" + ".join(row["verifiers"]))}</text>')
    parts.append('<text x="28" y="470" font-size="12" font-family="Calibri, sans-serif">Blue is the solved team. Red points are other feasible teams, not alternative empirical runs. Dependency-group coverage matches these points.</text>')
    parts.append('<text x="28" y="490" font-size="12" font-family="Calibri, sans-serif">EMPIRICAL. Cost is the frozen calibration sum, not this run\'s recorded wall time.</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts))


def write_all(payload: dict, destination: Path | None = None) -> list[Path]:
    if payload.get("evidence_label") != "EMPIRICAL":
        raise ValueError("figure payload must be empirical")
    folder = destination or FIGURES
    writers = (
        ("attack_decision_loss_by_method.svg", attack_loss_figure),
        ("benchmark_coverage_uncertainty.svg", coverage_figure),
        ("benchmark_selective_risk.svg", selective_risk_figure),
        ("attack_false_rates.svg", false_rate_figure),
        ("verifier_uncertainty.svg", verifier_figure),
        ("team_selection.svg", team_figure),
        ("resource_cost_coverage.svg", tradeoff_figure),
    )
    return [function(payload, folder / name) for name, function in writers]


def main() -> None:
    payload = json.loads(DIAGNOSIS.read_text(encoding="utf-8"))
    for path in write_all(payload):
        print(path)


if __name__ == "__main__":
    main()
