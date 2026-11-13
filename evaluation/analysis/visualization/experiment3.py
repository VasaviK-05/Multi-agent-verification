"""SVG figures for Experiment 3. Values come from the analysis rows, not from constants."""

from __future__ import annotations

from pathlib import Path

from evaluation.analysis.experiment3 import (
    METHODS, SCENARIOS, aggregation_comparison, coverage_risk_points, method_metrics,
    paired_loss_differences, validate_rows,
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
    synthetic = rows[0]["evidence_label"] == "SYNTHETIC" or rows[0].get("result_class") in {"SYNTHETIC", "HYPOTHETICAL"}
    if synthetic and ("/results" in text or "empirical" in text):
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


def coverage_risk_plot(rows: list[dict], destination: Path) -> Path:
    assert_figure_destination(rows, destination)
    points = coverage_risk_points(rows)
    label = rows[0]["evidence_label"]
    width, height = 760, 480
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="24" y="28" font-size="18">Coverage-risk tradeoff ({_escape(label)})</text>',
             '<text x="24" y="50" font-size="12">Coverage is the recorded decision coverage. Selective risk is errors among decisive classified decisions.</text>',
             '<line x1="80" y1="360" x2="680" y2="360" stroke="#666"/>',
             '<line x1="80" y1="80" x2="80" y2="360" stroke="#666"/>',
             '<text x="300" y="390" font-size="12">Coverage (fraction)</text>',
             '<text x="16" y="230" font-size="12" transform="rotate(-90 16 230)">Selective risk</text>']
    plotted = [point for point in points if point["coverage"] is not None and point["selective_risk"] is not None]
    if not plotted:
        parts.append('<text x="100" y="200" font-size="16">No decisive classified decisions. Selective risk is unavailable.</text>')
    for point in plotted:
        x = 80 + 560 * max(0.0, min(1.0, float(point["coverage"])))
        y = 360 - 250 * max(0.0, min(1.0, float(point["selective_risk"])))
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{COLORS[point["aggregation_method"]]}"/>')
        parts.append(f'<text x="{x + 8:.1f}" y="{y:.1f}" font-size="10">{_escape(point["attack_condition"])} n={point["sample_size"]}</text>')
    for index, method in enumerate(METHODS):
        parts.append(f'<rect x="{80 + index * 210}" y="420" width="14" height="14" fill="{COLORS[method]}"/>')
        parts.append(f'<text x="{100 + index * 210}" y="432" font-size="12">{_escape(METHOD_LABELS[method])}</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts), evidence_label=label)


def _png(destination: Path, width: int, height: int, pixels: bytes, *, method: str) -> Path:
    import struct
    import zlib
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    note = f"SYNTHETIC {method}".encode("latin-1")
    image = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    image += chunk(b"tEXt", b"Description\x00" + note)
    image += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    destination.write_bytes(image)
    return destination


def _heat(value: float, low: float, high: float) -> tuple[int, int, int]:
    span = high - low or 1.0
    mix = max(0.0, min(1.0, (value - low) / span))
    return int(255 - 180 * mix), int(245 - 160 * mix), int(230 - 40 * mix)


def assumption_heatmap(payload: dict, destination: Path, *, method: str) -> Path:
    """One aggregation method. Rows are dependency assumptions and columns are attacks."""
    if payload.get("evidence_label") != "SYNTHETIC":
        raise ValueError("dependency assumption heatmap is synthetic only")
    text = destination.as_posix().lower()
    if "empirical" in text or "/results" in text:
        raise ValueError("synthetic figure cannot be written to an empirical result directory")
    rows = [row["assumption"] for row in payload["scenarios"]]
    columns = list(payload["attacks"])
    cells = [cell for cell in payload["cells"] if cell["aggregation_method"] == method]
    if not cells:
        raise ValueError("heatmap data is empty")
    values = [cell["validation_loss"] for cell in cells]
    low, high = min(values), max(values)
    labels = {"independent": "Independent verifiers", "correlated_semantic_evidence": "Semantic + evidence correlated",
              "fully_correlated": "Fully correlated", "clean": "Clean", "forced_support": "Forced support",
              "forced_rejection": "Forced rejection", "confidence_inflation": "Confidence inflation",
              "full_minimax": "Full joint minimax", "fixed_reputation_weighted": "Fixed reputation-weighted",
              "fixed_dependency_group": "Fixed dependency-group"}
    if destination.suffix.lower() == ".png":
        width, height = 980, 420
        canvas = bytearray(b"\xff" * (width * height * 3))
        header = {"full_minimax": (27, 79, 114), "fixed_reputation_weighted": (185, 119, 14), "fixed_dependency_group": (25, 111, 61)}
        def paint(x0, y0, x1, y1, color):
            for y in range(max(0, y0), min(height, y1)):
                for x in range(max(0, x0), min(width, x1)):
                    offset = (y * width + x) * 3
                    canvas[offset:offset + 3] = bytes(color)
        paint(0, 0, width, 36, header.get(method, (27, 79, 114)))
        for row_index, assumption in enumerate(rows):
            for column, attack in enumerate(columns):
                cell = next(item for item in cells if item["dependency_assumption"] == assumption and item["attack_condition"] == attack)
                paint(250 + column * 170, 80 + row_index * 90, 400 + column * 170, 150 + row_index * 90, _heat(cell["validation_loss"], low, high))
        return _png(destination, width, height, bytes(canvas), method=method)
    width, height = 980, 460
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="24" y="28" font-size="18">Synthetic dependency robustness ({_escape(labels.get(method, method))})</text>',
             '<text x="24" y="50" font-size="12">Rows are dependency assumptions. Columns are attack conditions. Cells are validation loss. SYNTHETIC fixture, not measured dependence.</text>',
             '<text x="430" y="78" font-size="13">Attack condition</text>',
             '<text x="18" y="230" font-size="13" transform="rotate(-90 18 230)">Dependency assumption</text>']
    for column, attack in enumerate(columns):
        parts.append(f'<text x="{250 + column * 170}" y="100" font-size="12">{_escape(labels.get(attack, attack))}</text>')
    for row_index, assumption in enumerate(rows):
        parts.append(f'<text x="36" y="{150 + row_index * 90}" font-size="12">{_escape(labels.get(assumption, assumption))}</text>')
        for column, attack in enumerate(columns):
            cell = next(item for item in cells if item["dependency_assumption"] == assumption and item["attack_condition"] == attack)
            red, green, blue = _heat(cell["validation_loss"], low, high)
            x, y = 250 + column * 170, 112 + row_index * 90
            parts.append(f'<rect x="{x}" y="{y}" width="150" height="64" fill="rgb({red},{green},{blue})" stroke="#1b4f72"/>')
            parts.append(f'<text x="{x + 10}" y="{y + 28}" font-size="16">{cell["validation_loss"]:.3f}</text>')
            parts.append(f'<text x="{x + 10}" y="{y + 48}" font-size="11">worst of {len(cell["group_losses"])} group(s)</text>')
    parts.append('<text x="24" y="420" font-size="12">Validation loss is the game mean loss: decision loss plus 0.1 times estimated attempt cost. A cell with several groups uses the worst group.</text>')
    parts.append('<text x="24" y="442" font-size="12">SYNTHETIC. One hand-built example. This does not estimate Development robustness.</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts), evidence_label="SYNTHETIC")


def attack_stratified_plot(rows: list[dict], destination: Path) -> Path:
    assert_figure_destination(rows, destination)
    summaries = [row for row in method_metrics(rows) if row["status"] == "available"]
    label = rows[0]["evidence_label"]
    conditions = sorted({row["attack_condition"] for row in summaries})
    width, height = 880, 420
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="24" y="28" font-size="18">Attack-stratified validation loss ({_escape(label)})</text>',
             '<text x="24" y="50" font-size="12">Each bar is mean validation loss. Suppression is shown only when a row records that attack.</text>']
    values = [row["validation_loss"] for row in summaries if row["validation_loss"] is not None]
    scale = max(values) if values else 1
    for index, condition in enumerate(conditions):
        for method_index, method in enumerate(METHODS):
            row = next((item for item in summaries if item["attack_condition"] == condition and item["aggregation_method"] == method), None)
            value = 0 if row is None or row["validation_loss"] is None else row["validation_loss"]
            bar_height = 0 if not scale else 180 * value / scale
            x = 70 + index * 150 + method_index * 28
            y = 280 - bar_height
            parts.append(f'<rect x="{x}" y="{y:.1f}" width="24" height="{bar_height:.1f}" fill="{COLORS[method]}"/>')
        parts.append(f'<text x="{70 + index * 150}" y="310" font-size="11">{_escape(condition)}</text>')
    for index, method in enumerate(METHODS):
        parts.append(f'<rect x="24" y="{340 + index * 20}" width="14" height="14" fill="{COLORS[method]}"/>')
        parts.append(f'<text x="44" y="{352 + index * 20}" font-size="12">{_escape(METHOD_LABELS[method])}</text>')
    parts.append("</svg>")
    return _write(destination, "".join(parts), evidence_label=label)
