"""Core consistency and coverage calculations for QCA.

All formulae use numpy vectorised operations on fuzzy-set membership arrays.
These are the mathematical building blocks for truth table construction,
necessity analysis, and sufficiency analysis.
"""

from __future__ import annotations

import numpy as np


class ConsistencyCalculator:
    """Static methods for QCA consistency and coverage metrics.

    All methods accept 1-D numpy arrays of fuzzy-set membership scores (0-1).
    """

    @staticmethod
    def subset_consistency(subset: np.ndarray, superset: np.ndarray) -> float:
        """Consistency of the subset relation: degree to which X is a fuzzy subset of Y.

        .. math:: \\text{Consistency}(X \\subseteq Y) = \\frac{\\sum \\min(X_i, Y_i)}{\\sum X_i}

        Args:
            subset: Fuzzy membership in the alleged subset (X).
            superset: Fuzzy membership in the alleged superset (Y).

        Returns:
            Consistency value in [0, 1]. Values >= 0.75 conventionally indicate
            a consistent subset relationship.
        """
        denom = float(np.sum(subset))
        if denom == 0.0:
            return 0.0
        return float(np.sum(np.minimum(subset, superset)) / denom)

    @staticmethod
    def raw_coverage(solution_term: np.ndarray, outcome: np.ndarray) -> float:
        """Raw coverage: proportion of outcome membership covered by the solution term.

        .. math:: \\text{Coverage}(X) = \\frac{\\sum \\min(X_i, Y_i)}{\\sum Y_i}

        Args:
            solution_term: Fuzzy membership in the solution term.
            outcome: Fuzzy membership in the outcome.

        Returns:
            Coverage value in [0, 1].
        """
        denom = float(np.sum(outcome))
        if denom == 0.0:
            return 0.0
        return float(np.sum(np.minimum(solution_term, outcome)) / denom)

    @staticmethod
    def unique_coverage(
        solution_term: np.ndarray,
        other_terms: list[np.ndarray],
        outcome: np.ndarray,
    ) -> float:
        """Coverage uniquely attributable to this solution term.

        Computes the part of the outcome covered by this term but not by
        any other solution term (i.e., membership in this term and outcome
        minus membership in the union of other terms).

        Args:
            solution_term: Fuzzy membership in the target term.
            other_terms: List of fuzzy membership arrays for other terms.
            outcome: Fuzzy membership in the outcome.

        Returns:
            Unique coverage in [0, 1].
        """
        denom = float(np.sum(outcome))
        if denom == 0.0:
            return 0.0
        if other_terms:
            other_union = np.maximum.reduce(other_terms)
        else:
            other_union = np.zeros_like(solution_term)
        unique_part = np.maximum(0.0, solution_term - other_union)
        return float(np.sum(np.minimum(unique_part, outcome)) / denom)

    @staticmethod
    def solution_consistency(
        solution_terms: list[np.ndarray], outcome: np.ndarray
    ) -> float:
        """Overall consistency of the solution (union of all terms).

        Args:
            solution_terms: List of fuzzy membership arrays for each solution term.
            outcome: Fuzzy membership in the outcome.

        Returns:
            Solution consistency in [0, 1].
        """
        if not solution_terms:
            return 0.0
        union = np.maximum.reduce(solution_terms)
        return ConsistencyCalculator.subset_consistency(union, outcome)

    @staticmethod
    def solution_coverage(
        solution_terms: list[np.ndarray], outcome: np.ndarray
    ) -> float:
        """Overall coverage of the solution (union of all terms).

        Args:
            solution_terms: List of fuzzy membership arrays for each solution term.
            outcome: Fuzzy membership in the outcome.

        Returns:
            Solution coverage in [0, 1].
        """
        if not solution_terms:
            return 0.0
        union = np.maximum.reduce(solution_terms)
        return ConsistencyCalculator.raw_coverage(union, outcome)

    @staticmethod
    def fuzzy_and(*arrays: np.ndarray) -> np.ndarray:
        """Fuzzy logical AND: element-wise minimum."""
        if not arrays:
            raise ValueError("At least one array required")
        return np.minimum.reduce(arrays)

    @staticmethod
    def fuzzy_or(*arrays: np.ndarray) -> np.ndarray:
        """Fuzzy logical OR: element-wise maximum."""
        if not arrays:
            raise ValueError("At least one array required")
        return np.maximum.reduce(arrays)

    @staticmethod
    def fuzzy_not(array: np.ndarray) -> np.ndarray:
        """Fuzzy logical NOT: 1 - membership."""
        return 1.0 - array
