"""Figures for Experiment 3 ablation v1. Every plotted number is read from a result file."""

from __future__ import annotations

import json
from pathlib import Path


def _escape(value) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _load(path: Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("record_type") != "experiment3_ablation_v1":
        raise ValueError("figure source is not an ablation v1 result file")
    return payload


def _svg(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def aggregation_figure(source: Path, destination: Path) -> Path:
    payload = _load(source)
    neutral = payload["aggregation"]["neutral"]
    sensitivity = payload["aggregation"]["non_neutral_reputation"]
    methods = ("full_minimax", "fixed_reputation_weighted", "fixed_dependency_group")
    labels = {
        "full_minimax": "Joint game",
        "fixed_reputation_weighted": "Reputation only",
        "fixed_dependency_group": "Dependency only",
    }
    colors = {"full_minimax": "#1b4f72", "fixed_reputation_weighted": "#b9770e", "fixed_dependency_group": "#196f3d"}
    if not neutral["reproduction_matches_historical"]:
        raise ValueError("refusing to plot an aggregation result that does not match the preserved run")
    loss_values = [neutral["methods"][method]["mean_decision_loss"] for method in methods]
    coverage_values = [neutral["methods"][method]["coverage"] for method in methods]
    if any(value is None for value in loss_values + coverage_values):
        raise ValueError("aggregation figure is missing a measured value")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="560" viewBox="0 0 1100 560">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="28" y="28" font-size="18" font-family="Cambria, serif">Aggregation ablation on the preserved Development reports</text>',
        '<text x="28" y="50" font-size="12" font-family="Calibri, sans-serif" fill="#333">744 candidates, 372 question groups. Neutral Beta(1, 1) reputation. The non-neutral panel is not estimable.</text>',
    ]
    for origin_y, title, values, scale, note in (
        (80, "Mean decision loss", loss_values, 0.40, "Decision loss excludes the resource penalty. Lower is better."),
        (300, "Decision coverage", coverage_values, 1.0, "Coverage is the share of candidates with a passed or failed decision."),
    ):
        parts.append(f'<text x="28" y="{origin_y}" font-size="14" font-family="Calibri, sans-serif">{title}</text>')
        parts.append(f'<line x1="70" y1="{origin_y + 30}" x2="70" y2="{origin_y + 170}" stroke="#222"/>')
        parts.append(f'<line x1="70" y1="{origin_y + 170}" x2="620" y2="{origin_y + 170}" stroke="#222"/>')
        for index, method in enumerate(methods):
            value = values[index]
            height = 140 * value / scale
            x = 110 + index * 150
            y = origin_y + 170 - height
            parts.append(f'<rect x="{x}" y="{y:.1f}" width="70" height="{height:.1f}" fill="{colors[method]}"/>')
            parts.append(f'<text x="{x}" y="{origin_y + 188}" font-size="11" font-family="Calibri, sans-serif">{_escape(labels[method])}</text>')
            parts.append(f'<text x="{x}" y="{y - 6:.1f}" font-size="11" font-family="Calibri, sans-serif">{value:.6f}</text>')
        parts.append(f'<text x="640" y="{origin_y + 80}" font-size="12" font-family="Calibri, sans-serif">{note}</text>')
        if len({round(value, 12) for value in values}) == 1 and title == "Mean decision loss":
            parts.append('<text x="640" y="180" font-size="12" font-family="Calibri, sans-serif">Exactly tied. Paired loss interval [0, 0].</text>')
        elif len({round(value, 12) for value in values}) == 1:
            parts.append('<text x="640" y="400" font-size="12" font-family="Calibri, sans-serif">Exactly tied. No coverage interval was calculated.</text>')
    reason = sensitivity["reason"]
    parts.append(f'<text x="28" y="520" font-size="12" font-family="Calibri, sans-serif">Non-neutral reputation: {_escape(sensitivity["status"])}. {_escape(reason)}</text>')
    parts.append('<text x="28" y="542" font-size="12" font-family="Calibri, sans-serif">No confidence interval is drawn for a reputation snapshot that was not run.</text>')
    parts.append("</svg>")
    return _svg(destination, "".join(parts))


def _matrix_figure(payload: dict, destination: Path, *, metric: str, title: str, scale_note: str) -> Path:
    matrix = payload["dependency"]["native_matrix"]
    assumptions = ("declared_structural", "independent", "fully_correlated")
    scenarios = ("independent_failures", "correlated_failures")
    assumption_labels = {
        "declared_structural": "Declared structural",
        "independent": "Independent",
        "fully_correlated": "Fully correlated",
    }
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="460" viewBox="0 0 980 460">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="24" y="28" font-size="18" font-family="Cambria, serif">{_escape(title)}</text>',
        '<text x="24" y="50" font-size="12" font-family="Calibri, sans-serif" fill="#333">Rows are dependency assumptions. Columns are failure scenarios. Values come from the completed result file.</text>',
        '<text x="360" y="90" font-size="13" font-family="Calibri, sans-serif">Independent failures</text>',
        '<text x="620" y="90" font-size="13" font-family="Calibri, sans-serif">Correlated failures</text>',
    ]
    for row_index, assumption in enumerate(assumptions):
        y = 130 + row_index * 90
        parts.append(f'<text x="24" y="{y + 28}" font-size="13" font-family="Calibri, sans-serif">{assumption_labels[assumption]}</text>')
        for column, scenario in enumerate(scenarios):
            cell = matrix[assumption][scenario]
            value = cell.get(metric)
            x = 340 + column * 260
            if cell["status"] != "available" or value is None:
                parts.append(f'<rect x="{x}" y="{y}" width="220" height="64" fill="none" stroke="#7b241c" stroke-dasharray="4 3"/>')
                parts.append(f'<text x="{x + 12}" y="{y + 36}" font-size="14" font-family="Calibri, sans-serif">unavailable</text>')
            else:
                parts.append(f'<rect x="{x}" y="{y}" width="220" height="64" fill="#d4e6f1" stroke="#1b4f72"/>')
                parts.append(f'<text x="{x + 12}" y="{y + 28}" font-size="16" font-family="Calibri, sans-serif">{value:.6f}</text>')
                parts.append(f'<text x="{x + 12}" y="{y + 48}" font-size="11" font-family="Calibri, sans-serif">n={cell["candidates"]}</text>')
    parts.append(f'<text x="24" y="420" font-size="12" font-family="Calibri, sans-serif">{_escape(scale_note)}</text>')
    parts.append('<text x="24" y="442" font-size="12" font-family="Calibri, sans-serif">Controlled failures of the saved Development reports. This is not a measured correlation and not a Final Test result.</text>')
    parts.append("</svg>")
    return _svg(destination, "".join(parts))


def dependency_loss_heatmap(source: Path, destination: Path) -> Path:
    return _matrix_figure(
        _load(source), destination, metric="worst_column_decision_loss",
        title="Dependency robustness: worst-column decision loss",
        scale_note="Each number is the selected dependency-group team's worst failure-column mean decision loss.",
    )


def dependency_coverage_heatmap(source: Path, destination: Path) -> Path:
    return _matrix_figure(
        _load(source), destination, metric="coverage",
        title="Dependency robustness: decision coverage on the worst-loss column",
        scale_note="Coverage uses the same selected team and the same failure column as the loss heatmap.",
    )


def difference_figure(source: Path, destination: Path) -> Path:
    payload = _load(source)
    contrasts = payload["differences"]
    if any(row.get("mean") is None or row.get("lower") is None or row.get("upper") is None for row in contrasts):
        raise ValueError("difference figure is missing a calculated interval")
    width, height = 1100, 520
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="28" font-size="18" font-family="Cambria, serif">Paired loss differences</text>',
        '<text x="24" y="50" font-size="12" font-family="Calibri, sans-serif" fill="#333">Positive means the named method has higher decision loss than the reference. The horizontal line is zero.</text>',
        '<line x1="80" y1="250" x2="1040" y2="250" stroke="#222"/>',
        '<text x="1048" y="254" font-size="12" font-family="Calibri, sans-serif">0</text>',
    ]
    span = 0.05
    for row in contrasts:
        span = max(span, abs(row["mean"]), abs(row["lower"]), abs(row["upper"]))
    for index, row in enumerate(contrasts):
        x = 120 + index * 160
        y = 250 - (160 * row["mean"] / span)
        y1 = 250 - (160 * row["upper"] / span)
        y2 = 250 - (160 * row["lower"] / span)
        parts.append(f'<line x1="{x}" y1="{y1:.1f}" x2="{x}" y2="{y2:.1f}" stroke="#1b4f72" stroke-width="2"/>')
        parts.append(f'<circle cx="{x}" cy="{y:.1f}" r="5" fill="#1b4f72"/>')
        parts.append(f'<text x="{x - 55}" y="290" font-size="10" font-family="Calibri, sans-serif">{_escape(row["label"])}</text>')
        parts.append(f'<text x="{x - 55}" y="306" font-size="10" font-family="Calibri, sans-serif">mean={row["mean"]:.4f}</text>')
        parts.append(f'<text x="{x - 55}" y="322" font-size="10" font-family="Calibri, sans-serif">[{row["lower"]:.4f}, {row["upper"]:.4f}]</text>')
        parts.append(f'<text x="{x - 55}" y="338" font-size="10" font-family="Calibri, sans-serif">zero groups={row["exact_ties"]}</text>')
    parts.append('<text x="24" y="430" font-size="12" font-family="Calibri, sans-serif">Intervals are 95 percent group bootstraps, 2000 resamples, seed 20261113. Question groups are the resampled units.</text>')
    parts.append('<text x="24" y="452" font-size="12" font-family="Calibri, sans-serif">A zero interval on the neutral aggregation contrasts means every paired difference was zero. It is not a general equivalence result.</text>')
    parts.append('<text x="24" y="474" font-size="12" font-family="Calibri, sans-serif">Dependency contrasts use the matched failure columns. Native correlated columns are not plotted here because their targets differ by assumption.</text>')
    parts.append("</svg>")
    return _svg(destination, "".join(parts))
