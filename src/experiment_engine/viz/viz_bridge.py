"""Bridge between QCAPlotBuilder (plot data) and file-based visualization output.

This module bridges the impedance mismatch between QCAPlotBuilder (which produces
plain dicts of numpy arrays) and the existing MatplotlibRenderer/PlotlyRenderer
(which expect InputData + RenderConfig objects). Rather than constructing
InputData from the plot dicts, this module calls matplotlib directly using the
data produced by QCAPlotBuilder -- the simplest working approach.

Usage:
    >>> from experiment_engine.viz.viz_bridge import generate_all_viz
    >>> result = generate_all_viz(
    ...     "qca_output/trust/qca_results.json",
    ...     "qca_output/trust/fuzzy_data.npz",
    ...     "qca_output/trust/",
    ... )
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from experiment_engine.models import (
    MembershipData,
    QCAAnalysisResult,
    QCASolution,
    QCASolutions,
)
from experiment_engine.viz.qca_plots import QCAPlotBuilder

logger = logging.getLogger("experiment_engine.viz.viz_bridge")

# ─────────────────────────────────────────────────────────────────────────────
#  Matplotlib direct-render helpers for each plot type produced by QCAPlotBuilder
# ─────────────────────────────────────────────────────────────────────────────


def _render_heatmap(plot_dict: dict, output_path: str) -> str:
    """Render a heatmap from the truth_table_heatmap plot dict."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize

    data = plot_dict["data"]  # shape (n_rows, n_cols)
    row_labels = plot_dict["row_labels"]
    col_labels = plot_dict["col_labels"]
    title = plot_dict.get("title", "")
    xlabel = plot_dict.get("xlabel", "")
    ylabel = plot_dict.get("ylabel", "")

    n_rows = data.shape[0]
    # Estimate label width: count chars in longest label, roughly 0.1 inch per char
    max_label_chars = max((len(str(r)) for r in row_labels), default=10)
    label_width_inches = max(1.2, max_label_chars * 0.08)
    fig_width = max(6, len(col_labels) * 2 + label_width_inches)

    fig, ax = plt.subplots(figsize=(fig_width, max(4, n_rows * 0.35)))

    norm = Normalize(vmin=data.min(), vmax=data.max())
    cmap = plt.get_cmap("viridis")
    im = ax.imshow(data, aspect="auto", cmap=cmap, norm=norm)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Value")

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, fontsize=9)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=7)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")

    # Annotate cells (skip annotation for very large tables to keep clean)
    if n_rows <= 40:
        for i in range(n_rows):
            for j in range(data.shape[1]):
                ax.text(
                    j,
                    i,
                    f"{data[i, j]:.3f}",
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if data[i, j] > data.mean() else "black",
                )

    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _render_scatter(plot_dict: dict, output_path: str) -> str:
    """Render an XY scatter plot from necessity_xy_plot or sufficiency_xy_plot dicts."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = plot_dict["x"]
    y = plot_dict["y"]
    labels = plot_dict.get("labels", [])
    title = plot_dict.get("title", "")
    xlabel = plot_dict.get("xlabel", "X")
    ylabel = plot_dict.get("ylabel", "Y")

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.scatter(x, y, c="steelblue", s=60, alpha=0.8, edgecolors="white", linewidth=0.5)

    if labels:
        for i, label in enumerate(labels):
            ax.annotate(
                label,
                (x[i], y[i]),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
                alpha=0.85,
            )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _render_histograms(plot_dict: dict, output_path: str) -> str:
    """Render faceted histogram subplots from fuzzy_distribution_plot dict."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    histograms = plot_dict["histograms"]
    bins = plot_dict["bins"]
    title = plot_dict.get("title", "")
    xlabel = plot_dict.get("xlabel", "Score")
    ylabel = plot_dict.get("ylabel", "Count")

    n_vars = len(histograms)
    n_cols = min(3, n_vars)
    n_rows = int(np.ceil(n_vars / n_cols))

    fig, axes = plt.subplots(
        n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows), squeeze=False
    )
    axes_flat = axes.flatten()

    bin_centers = (bins[:-1] + bins[1:]) / 2

    for idx, (name, counts) in enumerate(histograms.items()):
        ax = axes_flat[idx]
        ax.bar(
            bin_centers,
            counts,
            width=(bins[1] - bins[0]) * 0.8,
            alpha=0.7,
            color="steelblue",
            edgecolor="white",
        )
        ax.set_title(name, fontsize=10)
        ax.set_xlabel(xlabel, fontsize=8)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(labelsize=7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # Hide unused subplots
    for idx in range(len(histograms), len(axes_flat)):
        axes_flat[idx].set_visible(False)

    fig.suptitle(title, fontweight="bold", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _render_grouped_bar(plot_dict: dict, output_path: str) -> str:
    """Render a grouped bar chart from solution_bar_chart plot dict."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = plot_dict["labels"]
    consistency = plot_dict["consistency"]
    raw_coverage = plot_dict["raw_coverage"]
    unique_coverage = plot_dict["unique_coverage"]
    title = plot_dict.get("title", "")

    n_terms = len(labels)
    x = np.arange(n_terms)
    width = 0.25

    fig, ax = plt.subplots(figsize=(max(6, n_terms * 1.2), 5))

    ax.bar(
        x - width,
        consistency,
        width,
        label="Consistency",
        alpha=0.85,
        color="steelblue",
    )
    ax.bar(x, raw_coverage, width, label="Raw Coverage", alpha=0.85, color="coral")
    ax.bar(
        x + width,
        unique_coverage,
        width,
        label="Unique Coverage",
        alpha=0.85,
        color="seagreen",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, rotation=30, ha="right")
    ax.set_ylabel("Score")
    ax.set_title(title, fontweight="bold")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

_VIZ_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "truth_table_heatmap",
        "filename": "qca_truth_table_heatmap.png",
        "builder_method": "truth_table_heatmap",
        "builder_arg": "truth_table",
        "render_fn": _render_heatmap,
    },
    {
        "name": "necessity_xy_plot",
        "filename": "qca_necessity_xy_plot.png",
        "builder_method": "necessity_xy_plot",
        "builder_arg": "result",
        "render_fn": _render_scatter,
    },
    {
        "name": "sufficiency_xy_plot",
        "filename": "qca_sufficiency_xy_plot.png",
        "builder_method": "sufficiency_xy_plot",
        "builder_arg": "sufficiency_solution",
        "render_fn": _render_scatter,
    },
    {
        "name": "fuzzy_distribution_plot",
        "filename": "qca_fuzzy_distribution.png",
        "builder_method": "fuzzy_distribution_plot",
        "builder_arg": "fuzzy_data",
        "render_fn": _render_histograms,
    },
    {
        "name": "solution_bar_chart",
        "filename": "qca_solution_bar_chart.png",
        "builder_method": "solution_bar_chart",
        "builder_arg": "solution_complex",
        "render_fn": _render_grouped_bar,
    },
]


def _load_qca_result(qca_results_path: str) -> QCAAnalysisResult:
    """Load QCA analysis result from JSON file.

    Handles the case where 'fuzzy_data' is absent from the JSON (it is excluded
    during serialization in cli.py) by loading it separately from the .npz.

    Args:
        qca_results_path: Path to qca_results.json.

    Returns:
        QCAAnalysisResult parsed from the JSON file.
    """
    with open(qca_results_path, encoding="utf-8") as fh:
        data = json.load(fh)
    return QCAAnalysisResult(**data)


def _load_fuzzy_data(fuzzy_data_path: str) -> MembershipData | None:
    """Load fuzzy-set data from .npz file.

    Args:
        fuzzy_data_path: Path to fuzzy_data.npz.

    Returns:
        MembershipData or None if the file cannot be loaded.
    """
    try:
        npz = np.load(fuzzy_data_path, allow_pickle=True)
        return MembershipData(
            membership=npz["membership"],
            condition_names=list(npz.get("condition_names", [])),
            outcome_name=str(npz.get("outcome_name", "")),
            case_ids=list(npz.get("case_ids", [])),
        )
    except Exception as exc:
        logger.warning("Failed to load fuzzy data from %s: %s", fuzzy_data_path, exc)
        return None


def _pick_solution(solutions: QCASolutions) -> tuple[str, QCASolution | None]:
    """Pick the first available solution for sufficiency/scatter and bar chart.

    Prefers complex > parsimonious > intermediate.

    Args:
        solutions: The QCASolutions object.

    Returns:
        Tuple of (solution_type_name, QCASolution or None).
    """
    for sol_type in ("complex", "parsimonious", "intermediate"):
        sol = getattr(solutions, sol_type, None)
        if sol is not None and sol.terms:
            return sol_type, sol
    return "", None


def generate_all_viz(
    qca_results_path: str,
    fuzzy_data_path: str,
    output_dir: str,
) -> dict[str, str]:
    """Generate all available QCA visualizations as PNG files.

    This is the main entry point. It loads the QCA results and fuzzy-set data,
    calls each QCAPlotBuilder method, renders the plot data as a PNG using
    matplotlib directly, and saves the file to *output_dir*.

    Args:
        qca_results_path: Path to qca_results.json.
        fuzzy_data_path: Path to fuzzy_data.npz.
        output_dir: Directory to write .png files into (created if missing).

    Returns:
        Dict mapping visualization name -> absolute path to output PNG file.
        Only successfully generated visualizations are included.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Load data
    result = _load_qca_result(qca_results_path)
    fuzzy_data = _load_fuzzy_data(fuzzy_data_path)

    # Prepare arguments for QCAPlotBuilder methods
    builder_args: dict[str, Any] = {
        "truth_table": result.truth_table,
        "result": result,
        "fuzzy_data": fuzzy_data,
    }

    # Pick first available solution for sufficiency/bar-chart plots
    _sol_type_name, sol = _pick_solution(result.solutions)
    builder_args["sufficiency_solution"] = sol
    builder_args["solution_complex"] = sol

    generated: dict[str, str] = {}

    for viz_def in _VIZ_DEFINITIONS:
        name = viz_def["name"]
        builder_method = viz_def["builder_method"]
        arg_key = viz_def["builder_arg"]
        filename = viz_def["filename"]
        render_fn = viz_def["render_fn"]

        # Determine the argument to pass to the builder
        arg = builder_args.get(arg_key)

        # Skip if the required argument is None/empty
        if arg is None:
            logger.info("  Skipping %s: required arg %s is None", name, arg_key)
            continue
        if isinstance(arg, (list, dict, np.ndarray)) and len(arg) == 0:
            logger.info("  Skipping %s: required arg %s is empty", name, arg_key)
            continue

        # Call the builder method
        try:
            builder_fn = getattr(QCAPlotBuilder, builder_method)
            plot_dict: dict = builder_fn(arg)
        except Exception as exc:
            logger.warning("  Skipping %s: builder error: %s", name, exc)
            continue

        # Skip if the builder returned an empty dict
        if not plot_dict:
            logger.info("  Skipping %s: builder returned empty plot data", name)
            continue

        # Render to PNG
        output_path = str(out / filename)
        try:
            render_fn(plot_dict, output_path)
            generated[name] = output_path
            file_size = Path(output_path).stat().st_size
            logger.info("  Generated %s -> %s (%d bytes)", name, output_path, file_size)
        except Exception as exc:
            logger.warning("  Failed to render %s: %s", name, exc)

    return generated
