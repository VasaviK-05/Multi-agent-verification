"""SVG figures for Experiment 3. Values come from the analysis rows, not from constants."""

from __future__ import annotations

from pathlib import Path

from evaluation.analysis.experiment3 import (
    METHODS, SCENARIOS, aggregation_comparison, paired_loss_differences, validate_rows,
)

METHOD_LABELS = {
    "full_minimax": "Full joint minimax",
    "fixed_reputation_weighted": "Fixed reputation-weighted",
    "fixed_dependency_group": "Fixed dependency-group",
}
COLORS = {"full_minimax": "#1b4f72", "fixed_reputation_weighted": "#b9770e", "fixed_dependency_group": "#196f3d"}


def _escape(value) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def assert_figure_destination(rows: list[dict], destination: Path) -> None:
    validate_rows(rows)
    text = destination.as_posix().lower()
    if rows[0]["evidence_label"] == "SYNTHETIC" and ("/results" in text or "empirical" in text):
        raise ValueError("synthetic figure cannot be written to an empirical result directory")


def _write(destination: Path, body: str, *, evidence_label: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    marker = "SYNTHETIC" if evidence_label == "SYNTHETIC" else "EMPIRICAL"
    destination.write_text(body.replace("</svg>", f"<desc>{marker}</desc></svg>"), encoding="utf-8")
    return destination


def aggregation_grouped_bars(rows: list[dict], destination: Path, *, intervals: dict | None = None) -> Path:
    assert_figure_destination(rows, destination)
    summaries = [row for row in aggregation_comparison(rows) if row["status"] == "available"]
    label = rows[0]["evidence_label"]
    conditions = sorted({row["attack_condition"] for row in summaries})
    benchmarks = sorted({row["benchmark"] for row in summaries})
    width, height = 880, 560
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="24" y="28" font-size="18">Aggregation ablation grouped bars ({_escape(label)})</text>']
    parts.append('<text x="24" y="50" font-size="12">Matched question groups. Loss and coverage use the same recordings, attacks, costs, and rules.</text>')
    for panel, metric, title, origin_y in (("validation_loss", "validation_loss", "Validation loss", 80), ("coverage", "coverage", "Decision coverage", 300)):
        values = [row[metric] for row in summaries if row[metric] is not None]
        scale = max(values) if values else 1
        parts.append(f'<text x="24" y="{origin_y}" font-size="14">{title}</text>')
        for index, condition in enumerate(conditions):
            for method_index, method in enumerate(METHODS):
                row = next((item for item in summaries if item["attack_condition"] == condition and item["aggregation_method"] == method), None)
                value = 0 if row is None or row[metric] is None else row[metric]
                bar_height = 0 if scale == 0 else 120 * value / scale
                x = 80 + index * 220 + method_index * 36
                y = origin_y + 150 - bar_height
                parts.append(f'<rect x="{x}" y="{y:.1f}" width="30" height="{bar_height:.1f}" fill="{COLORS[method]}"/>')
                if intervals and (method, condition, metric) in intervals:
                    lower, upper = intervals[(method, condition, metric)]
                    if lower is not None and upper is not None:
                        y1 = origin_y + 150 - (120 * upper / scale)
                        y2 = origin_y + 150 - (120 * lower / scale)
                        parts.append(f'<line x1="{x + 15}" y1="{y1:.1f}" x2="{x + 15}" y2="{y2:.1f}" stroke="black"/>')
                sample = 0 if row is None else row["sample_size"]
                parts.append(f'<text x="{x}" y="{origin_y + 168}" font-size="9">n={sample}</text>')
            parts.append(f'<text x="{80 + index * 220}" y="{origin_y + 186}" font-size="11">{_escape(condition)}</text>')
    legend_x = 620
    for index, method in enumerate(METHODS):
        parts.append(f'<rect x="{legend_x}" y="{80 + index * 22}" width="14" height="14" fill="{COLORS[method]}"/>')
        parts.append(f'<text x="{legend_x + 20}" y="{92 + index * 22}" font-size="12">{_escape(METHOD_LABELS[method])}</text>')
    parts.append(f'<text x="24" y="530" font-size="12">Benchmarks: {_escape(", ".join(benchmarks))}. Sample sizes are printed under the bars. Strategy probabilities are not plotted.</text>')
    parts.append(f'<text x="24" y="548" font-size="12">Caption: {_escape(label)} aggregation comparison of validation loss and decision coverage. Identical outcomes are reported by the analysis, not inferred from bar height.</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts), evidence_label=label)


def dependency_heatmap(matrix: dict, destination: Path) -> Path:
    label = matrix["evidence_label"]
    if label == "SYNTHETIC" and ("/results" in destination.as_posix().lower() or "empirical" in destination.as_posix().lower()):
        raise ValueError("synthetic figure cannot be written to an empirical result directory")
    width, height = 760, 420
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="24" y="28" font-size="18">Dependency robustness heatmap ({_escape(label)})</text>',
             '<text x="24" y="50" font-size="12">Aggregation policy is held fixed. Columns are failure scenarios. Cells are validation loss.</text>']
    if not matrix["estimable"]:
        parts.append(f'<text x="24" y="120" font-size="16">Not estimable. {_escape(matrix["reason"])}</text>')
        parts.append('<text x="24" y="150" font-size="13">Unavailable cells are not filled with values.</text>')
    else:
        for column, scenario in enumerate(SCENARIOS):
            parts.append(f'<text x="{260 + column * 160}" y="90" font-size="12">{_escape(scenario)}</text>')
        for row_index, model in enumerate(matrix["rows"]):
            parts.append(f'<text x="24" y="{130 + row_index * 70}" font-size="12">{_escape(model)}</text>')
            for column, scenario in enumerate(SCENARIOS):
                cell = next(item for item in matrix["cells"] if item["dependency_model"] == model and item["dependency_scenario"] == scenario)
                x, y = 250 + column * 160, 100 + row_index * 70
                if cell["status"] != "available":
                    parts.append(f'<rect x="{x}" y="{y}" width="140" height="48" fill="none" stroke="#7b241c" stroke-dasharray="4 3"/>')
                    parts.append(f'<text x="{x + 8}" y="{y + 28}" font-size="12">unavailable</text>')
                else:
                    parts.append(f'<rect x="{x}" y="{y}" width="140" height="48" fill="#d4e6f1" stroke="#1b4f72"/>')
                    parts.append(f'<text x="{x + 8}" y="{y + 22}" font-size="14">{cell["validation_loss"]:.3f}</text>')
                    parts.append(f'<text x="{x + 8}" y="{y + 40}" font-size="11">n={cell["sample_size"]}</text>')
    discrimination = matrix.get("dependency_discrimination") or {}
    if discrimination.get("limited_dependency_discrimination"):
        parts.append(f'<text x="24" y="360" font-size="12">Limited dependency discrimination. {_escape(discrimination["reason"])}</text>')
    parts.append(f'<text x="24" y="390" font-size="12">Caption: {_escape(label)} dependency stress comparison for {_escape(matrix["aggregation_method"])}. Measured evidence and hypothetical assumptions stay separated by evidence_label.</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts), evidence_label=label)


def paired_difference_plot(rows: list[dict], destination: Path, *, resamples=None, confidence_level=None, seed=None) -> Path:
    assert_figure_destination(rows, destination)
    contrasts = paired_loss_differences(rows, resamples=resamples, confidence_level=confidence_level, seed=seed)
    label = rows[0]["evidence_label"]
    width, height = 760, 420
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="24" y="28" font-size="18">Paired ablation-effect differences ({_escape(label)})</text>',
             '<text x="24" y="50" font-size="12">Each point is the mean of ablation loss minus full-game loss, paired on related_group_id and attack.</text>',
             '<line x1="80" y1="210" x2="680" y2="210" stroke="black" data-zero="0"/>',
             '<text x="690" y="214" font-size="12">zero</text>']
    span = 1.0
    for index, contrast in enumerate(contrasts):
        mean = contrast["mean_loss_difference"]
        if mean is not None:
            span = max(span, abs(mean))
        interval = contrast["confidence_interval"]
        if interval["lower"] is not None:
            span = max(span, abs(interval["lower"]), abs(interval["upper"]))
    for index, contrast in enumerate(contrasts):
        x = 180 + index * 220
        mean = 0 if contrast["mean_loss_difference"] is None else contrast["mean_loss_difference"]
        y = 210 - (120 * mean / span)
        parts.append(f'<circle cx="{x}" cy="{y:.1f}" r="6" fill="{COLORS[contrast["aggregation_method"]]}"/>')
        interval = contrast["confidence_interval"]
        if interval["lower"] is not None:
            y1 = 210 - (120 * interval["upper"] / span)
            y2 = 210 - (120 * interval["lower"] / span)
            parts.append(f'<line x1="{x}" y1="{y1:.1f}" x2="{x}" y2="{y2:.1f}" stroke="black"/>')
        parts.append(f'<text x="{x - 70}" y="250" font-size="12">{_escape(METHOD_LABELS[contrast["aggregation_method"]])}</text>')
        parts.append(f'<text x="{x - 70}" y="268" font-size="11">n={contrast["sample_size"]}; missing pairs={contrast["missing_pairs"]}</text>')
        parts.append(f'<text x="{x - 70}" y="286" font-size="11">mean={mean:.3f}; zeros={contrast["zero_difference_count"]}</text>')
    parts.append('<text x="24" y="340" font-size="12">Positive values are worse loss than the full game. Negative values are an improvement. Zero is identical loss.</text>')
    parts.append('<text x="24" y="360" font-size="12">The interval is a paired bootstrap when its settings are supplied. The mean is the practical effect and is reported separately from that interval.</text>')
    parts.append(f'<text x="24" y="390" font-size="12">Caption: {_escape(label)} paired contrasts against full joint minimax. Independent means are not compared.</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts), evidence_label=label)
