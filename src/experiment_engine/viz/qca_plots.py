"""QCA-specific visualizations using existing renderer backends.

Provides truth table heatmaps, necessity/sufficiency XY plots, fuzzy-set
distribution plots, and solution term bar charts.
"""

from __future__ import annotations

import numpy as np

from experiment_engine.models import (
    MembershipData,
    QCAAnalysisResult,
    QCASolution,
    TruthTable,
)


class QCAPlotBuilder:
    """Build QCA-specific plot data and configurations.

    This is a data-preparation layer. It produces RenderConfig + data tuples
    suitable for the existing MatplotlibRenderer / PlotlyRenderer backends.
    """

    @staticmethod
    def truth_table_heatmap(truth_table: TruthTable) -> dict:
        """Build a heatmap dataset from a truth table.

        Returns a dict with 'data', 'row_labels', 'col_labels', 'title'
        suitable for rendering as a heatmap.
        """
        included = [r for r in truth_table.rows if r.included]
        if not included:
            return {}

        data = np.array([[r.frequency, r.raw_consistency] for r in included])
        row_labels = [r.config_label for r in included]

        return {
            "data": data,
            "row_labels": row_labels,
            "col_labels": ["Frequency", "Consistency"],
            "title": f"Truth Table (outcome: {truth_table.outcome_name})",
            "xlabel": "Metric",
            "ylabel": "Configuration",
        }

    @staticmethod
    def necessity_xy_plot(result: QCAAnalysisResult) -> dict:
        """Build XY scatter data for necessity analysis.

        X = consistency, Y = coverage, per condition.
        """
        if not result.necessity:
            return {}

        # Only conditions (not negations) from necessity results
        positive = [
            c
            for c in result.necessity.conditions
            if not c.condition_name.startswith("~")
        ]

        x = [c.consistency for c in positive]
        y = [c.coverage for c in positive]
        labels = [c.condition_name for c in positive]

        return {
            "x": np.array(x),
            "y": np.array(y),
            "labels": labels,
            "title": "Necessity: Consistency vs Coverage",
            "xlabel": "Consistency",
            "ylabel": "Coverage",
        }

    @staticmethod
    def sufficiency_xy_plot(solution: QCASolution) -> dict:
        """Build XY scatter data for sufficiency analysis of one solution type.

        X = consistency, Y = raw_coverage, per solution term.
        """
        if not solution or not solution.terms:
            return {}

        x = [t.consistency for t in solution.terms]
        y = [t.raw_coverage for t in solution.terms]
        labels = [t.label for t in solution.terms]

        return {
            "x": np.array(x),
            "y": np.array(y),
            "labels": labels,
            "title": f"Sufficiency ({solution.solution_type}): Consistency vs Coverage",
            "xlabel": "Consistency",
            "ylabel": "Raw Coverage",
        }

    @staticmethod
    def fuzzy_distribution_plot(fuzzy_data: MembershipData) -> dict:
        """Build histogram data for fuzzy-set score distributions.

        Returns binned counts per condition.
        """
        membership = fuzzy_data.membership
        n_bins = 10
        bins = np.linspace(0, 1, n_bins + 1)

        histograms: dict[str, np.ndarray] = {}
        all_names = list(fuzzy_data.condition_names) + [fuzzy_data.outcome_name]
        for j, name in enumerate(all_names):
            if j < membership.shape[1]:
                hist, _ = np.histogram(membership[:, j], bins=bins)
                histograms[name] = hist.astype(np.float64)

        return {
            "histograms": histograms,
            "bins": bins,
            "title": "Fuzzy-Set Membership Distributions",
            "xlabel": "Membership Score",
            "ylabel": "Case Count",
        }

    @staticmethod
    def solution_bar_chart(solution: QCASolution) -> dict:
        """Build grouped bar chart data for solution term metrics."""
        if not solution or not solution.terms:
            return {}

        labels = [t.label for t in solution.terms]
        consistency = [t.consistency for t in solution.terms]
        raw_cov = [t.raw_coverage for t in solution.terms]
        unique_cov = [t.unique_coverage for t in solution.terms]

        return {
            "labels": labels,
            "consistency": np.array(consistency),
            "raw_coverage": np.array(raw_cov),
            "unique_coverage": np.array(unique_cov),
            "title": f"Solution Term Metrics ({solution.solution_type})",
        }
