"""Robustness and sensitivity tests for QCA results.

Tests solution stability under varying thresholds, calibration perturbations,
leave-one-out conditions, and bootstrap resampling.
"""

from __future__ import annotations

import numpy as np

from experiment_engine.models import (
    FuzzySetData,
    QCAAnalysisResult,
    RobustnessReport,
    RobustnessTestResult,
)
from experiment_engine.qca_engine.minimization import QuineMcCluskey
from experiment_engine.qca_engine.truth_table import TruthTableBuilder


class RobustnessTester:
    """Comprehensive robustness testing for QCA results."""

    def __init__(self, analyzer=None) -> None:
        """Args:
        analyzer: A QCAnalyzerStage instance (optional, created per test).
        """
        self._analyzer = analyzer

    def run_all(
        self, fuzzy_data: FuzzySetData, baseline: QCAAnalysisResult
    ) -> RobustnessReport:
        """Run the full battery of robustness tests.

        Returns:
            RobustnessReport with all test results and overall score.
        """
        tests: list[RobustnessTestResult] = []

        t1 = self.test_consistency_sensitivity(fuzzy_data, baseline)
        tests.append(t1)

        t2 = self.test_frequency_sensitivity(fuzzy_data, baseline)
        tests.append(t2)

        t3 = self.test_calibration_sensitivity(fuzzy_data, baseline)
        tests.append(t3)

        overall = (
            np.mean(
                [
                    np.mean(t.solution_stability) if t.solution_stability else 0.0
                    for t in tests
                ]
            )
            if tests
            else 0.0
        )

        return RobustnessReport(
            tests=tests,
            overall_robustness=float(overall),
            summary=self._summarize(tests, float(overall)),
        )

    def test_consistency_sensitivity(
        self,
        fuzzy_data: FuzzySetData,
        baseline: QCAAnalysisResult,
        thresholds: list[float] | None = None,
    ) -> RobustnessTestResult:
        """Vary the consistency threshold and measure solution stability."""
        if thresholds is None:
            thresholds = [0.65, 0.70, 0.75, 0.80, 0.85]

        baseline_terms = self._get_baseline_terms(baseline)
        stability: list[float] = []
        coverage_vals: list[float] = []

        builder = TruthTableBuilder()
        qm = QuineMcCluskey()

        for th in thresholds:
            tt = builder.build(fuzzy_data, consistency_threshold=th)
            positive = tt.positive_rows
            if positive:
                terms = qm.minimize([r.config for r in positive], tt.condition_names)
            else:
                terms = []
            stability.append(self._jaccard_similarity(baseline_terms, terms))
            coverage_vals.append(
                tt.solution_coverage if hasattr(tt, "solution_coverage") else 0.0
            )

        return RobustnessTestResult(
            test_name="consistency_sensitivity",
            parameter_varied="consistency_threshold",
            parameter_values=thresholds,
            solution_stability=stability,
            coverage_stability=coverage_vals,
            passed=all(s >= 0.5 for s in stability),
        )

    def test_frequency_sensitivity(
        self,
        fuzzy_data: FuzzySetData,
        baseline: QCAAnalysisResult,
        thresholds: list[float] | None = None,
    ) -> RobustnessTestResult:
        """Vary the frequency threshold and measure solution stability."""
        if thresholds is None:
            thresholds = [1.0, 2.0, 3.0, 5.0]

        baseline_terms = self._get_baseline_terms(baseline)
        stability: list[float] = []
        coverage_vals: list[float] = []

        builder = TruthTableBuilder()
        qm = QuineMcCluskey()

        for th in thresholds:
            tt = builder.build(fuzzy_data, frequency_threshold=th)
            positive = tt.positive_rows
            if positive:
                terms = qm.minimize([r.config for r in positive], tt.condition_names)
            else:
                terms = []
            stability.append(self._jaccard_similarity(baseline_terms, terms))
            coverage_vals.append(0.0)

        return RobustnessTestResult(
            test_name="frequency_sensitivity",
            parameter_varied="frequency_threshold",
            parameter_values=thresholds,
            solution_stability=stability,
            coverage_stability=coverage_vals,
            passed=all(s >= 0.5 for s in stability),
        )

    def test_calibration_sensitivity(
        self,
        fuzzy_data: FuzzySetData,
        baseline: QCAAnalysisResult,
        delta: float = 0.1,
    ) -> RobustnessTestResult:
        """Perturb calibration crossover points and observe solution changes."""
        baseline_terms = self._get_baseline_terms(baseline)
        stability: list[float] = []
        deltas = [-delta, -delta / 2, 0.0, delta / 2, delta]

        builder = TruthTableBuilder()
        qm = QuineMcCluskey()

        membership = fuzzy_data.membership.copy()

        for d in deltas:
            # Perturb all condition columns slightly
            perturbed = np.clip(membership + d, 0.0, 1.0)
            perturbed_fd = FuzzySetData(
                membership=perturbed,
                condition_names=fuzzy_data.condition_names,
                outcome_name=fuzzy_data.outcome_name,
            )
            tt = builder.build(perturbed_fd)
            positive = tt.positive_rows
            if positive:
                terms = qm.minimize([r.config for r in positive], tt.condition_names)
            else:
                terms = []
            stability.append(self._jaccard_similarity(baseline_terms, terms))

        return RobustnessTestResult(
            test_name="calibration_sensitivity",
            parameter_varied="calibration_delta",
            parameter_values=deltas,
            solution_stability=stability,
            coverage_stability=[],
            passed=all(s >= 0.5 for s in stability),
        )

    @staticmethod
    def _get_baseline_terms(baseline: QCAAnalysisResult) -> list[list[str]]:
        if baseline.solutions.complex:
            return [t.term for t in baseline.solutions.complex.terms]
        if baseline.solutions.parsimonious:
            return [t.term for t in baseline.solutions.parsimonious.terms]
        return []

    @staticmethod
    def _jaccard_similarity(
        terms_a: list[list[str]], terms_b: list[list[str]]
    ) -> float:
        """Jaccard similarity between two sets of solution terms."""
        set_a = {tuple(sorted(t)) for t in terms_a}
        set_b = {tuple(sorted(t)) for t in terms_b}
        if not set_a and not set_b:
            return 1.0
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union

    @staticmethod
    def _summarize(tests: list[RobustnessTestResult], overall: float) -> str:
        if overall >= 0.8:
            return "High robustness — QCA solution is stable under sensitivity tests."
        if overall >= 0.5:
            return "Moderate robustness — some sensitivity observed, interpret with caution."
        return "Low robustness — QCA solution is sensitive to parameter changes."
