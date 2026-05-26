"""Necessary condition analysis for QCA.

For each condition, tests whether it is necessary for the outcome:
X is necessary for Y if Y is a fuzzy subset of X (Y <= X).
"""

from __future__ import annotations

import numpy as np

from experiment_engine.models import (
    MembershipData,
    NecessityConditionResult,
    NecessityResults,
)


class NecessityAnalyzer:
    """Analyze whether individual conditions are necessary for the outcome.

    A condition X is necessary for outcome Y when Y is a consistent fuzzy
    subset of X: for all cases, membership in Y <= membership in X.
    Necessity consistency = Sum(min(X, Y)) / Sum(Y).

    The conventional threshold for necessity is 0.9 (Ragin 2008).
    """

    def __init__(self, threshold: float = 0.9) -> None:
        """Args:
        threshold: Consistency threshold for declaring a condition necessary.
        """
        self.threshold = threshold

    def analyze(self, fuzzy_data: MembershipData) -> NecessityResults:
        """Analyze necessity for all conditions against the outcome.

        Args:
            fuzzy_data: Fuzzy-set membership data with conditions and outcome.

        Returns:
            NecessityResults with per-condition analysis.
        """
        cond_matrix = fuzzy_data.condition_matrix
        outcome = fuzzy_data.outcome_vector
        condition_names = fuzzy_data.condition_names

        results: list[NecessityConditionResult] = []
        for j, name in enumerate(condition_names):
            cond_col = cond_matrix[:, j]
            consistency = self._necessity_consistency(cond_col, outcome)
            coverage = self._necessity_coverage(cond_col, outcome)
            results.append(
                NecessityConditionResult(
                    condition_name=name,
                    consistency=consistency,
                    coverage=coverage,
                    is_necessary=consistency >= self.threshold,
                )
            )

        # Also test negations of each condition
        for j, name in enumerate(condition_names):
            neg_cond = 1.0 - cond_matrix[:, j]
            consistency = self._necessity_consistency(neg_cond, outcome)
            coverage = self._necessity_coverage(neg_cond, outcome)
            results.append(
                NecessityConditionResult(
                    condition_name=f"~{name}",
                    consistency=consistency,
                    coverage=coverage,
                    is_necessary=consistency >= self.threshold,
                )
            )

        return NecessityResults(
            outcome_name=fuzzy_data.outcome_name,
            threshold=self.threshold,
            conditions=results,
        )

    @staticmethod
    def _necessity_consistency(condition: np.ndarray, outcome: np.ndarray) -> float:
        """Sum(min(X, Y)) / Sum(Y)."""
        denom = float(np.sum(outcome))
        if denom == 0.0:
            return 0.0
        return float(np.sum(np.minimum(condition, outcome)) / denom)

    @staticmethod
    def _necessity_coverage(condition: np.ndarray, outcome: np.ndarray) -> float:
        """Sum(min(X, Y)) / Sum(X)."""
        denom = float(np.sum(condition))
        if denom == 0.0:
            return 0.0
        return float(np.sum(np.minimum(condition, outcome)) / denom)

    def summarize(self, results: NecessityResults) -> str:
        """Produce a text summary of necessity findings."""
        lines = [
            f"Necessity Analysis (threshold = {results.threshold})",
            f"Outcome: {results.outcome_name}",
            "-" * 60,
        ]
        for r in results.conditions:
            star = " *NECESSARY*" if r.is_necessary else ""
            lines.append(
                f"  {r.condition_name:30s}  Cons={r.consistency:.3f}  Cov={r.coverage:.3f}{star}"
            )
        return "\n".join(lines)
