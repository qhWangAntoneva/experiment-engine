"""Robustness and sensitivity tests for QCA results.

Tests solution stability under varying thresholds, membership perturbations,
bootstrap resampling, and frequency sensitivity.

FIXME-6 (fixed 2026-05-24): coverage_stability now uses real solution coverage
  computed via SufficiencyAnalyzer + ConsistencyCalculator, replacing the
  broken ``hasattr(tt, "solution_coverage")`` check that always returned 0.
FIXME-7 (fixed 2026-05-24): test_calibration_sensitivity renamed to
  test_membership_perturbation; outcome column excluded from perturbation.
  Old method kept as convenience alias.
FIXME-8 (fixed 2026-05-24): added test_bootstrap() with case resampling and
  term-appearance proportion reporting.
FIXME-12 (fixed 2026-05-24): test_frequency_sensitivity default thresholds
  are now adaptive based on n_cases (proportion-based for N<20).
"""

from __future__ import annotations

import warnings

import numpy as np

from experiment_engine.models import (
    FuzzySetData,
    QCAAnalysisResult,
    RobustnessReport,
    RobustnessTestResult,
)
from experiment_engine.qca_engine.consistency import ConsistencyCalculator
from experiment_engine.qca_engine.minimization import QuineMcCluskey
from experiment_engine.qca_engine.truth_table import TruthTableBuilder


def _compute_term_membership(
    term: list[str],
    condition_matrix: np.ndarray,
    name_to_idx: dict[str, int],
) -> np.ndarray:
    """Compute fuzzy membership of each case in a solution term.

    A term is a conjunction of conditions (e.g., ['A', '~B', 'C']).
    Negated conditions (~) use 1 - membership.
    Unknown condition names emit a warning (matching sufficiency.py FIXME-13 fix).
    """
    n_cases = condition_matrix.shape[0]
    result = np.ones(n_cases, dtype=np.float64)

    for cond in term:
        if cond.startswith("~"):
            name = cond[1:]
            if name in name_to_idx:
                result = np.minimum(
                    result, 1.0 - condition_matrix[:, name_to_idx[name]]
                )
            else:
                warnings.warn(
                    f"Negated condition '{name}' not found in condition matrix "
                    f"(available: {list(name_to_idx.keys())}). Treating as 1.0.",
                    stacklevel=2,
                )
        else:
            if cond in name_to_idx:
                result = np.minimum(result, condition_matrix[:, name_to_idx[cond]])
            else:
                warnings.warn(
                    f"Condition '{cond}' not found in condition matrix "
                    f"(available: {list(name_to_idx.keys())}). Treating as 1.0.",
                    stacklevel=2,
                )

    return result


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

        t3 = self.test_membership_perturbation(fuzzy_data, baseline)
        tests.append(t3)

        t4 = self.test_bootstrap(fuzzy_data, baseline)
        tests.append(t4)

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

    # ── Consistency Sensitivity ────────────────────────────────────────────

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
            coverage_vals.append(self._compute_solution_coverage(terms, fuzzy_data))

        return RobustnessTestResult(
            test_name="consistency_sensitivity",
            parameter_varied="consistency_threshold",
            parameter_values=thresholds,
            solution_stability=stability,
            coverage_stability=coverage_vals,
            passed=all(s >= 0.5 for s in stability),
        )

    # ── Frequency Sensitivity (FIXME-12) ───────────────────────────────────

    def test_frequency_sensitivity(
        self,
        fuzzy_data: FuzzySetData,
        baseline: QCAAnalysisResult,
        thresholds: list[float] | None = None,
    ) -> RobustnessTestResult:
        """Vary the frequency threshold and measure solution stability.

        Default thresholds are adaptive based on the number of cases:
        - N < 20: proportion-based thresholds [0.05*N, 0.10*N, 0.15*N, 0.25*N]
          This prevents excluding all rows for small-N fuzzy-set QCA.
        - N >= 20: absolute thresholds [1.0, 2.0, 3.0, 5.0]
        """
        if thresholds is None:
            n_cases = fuzzy_data.n_cases
            if n_cases < 20:
                proportions = [0.05, 0.10, 0.15, 0.25]
                thresholds = [round(p * n_cases, 2) for p in proportions]
            else:
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
            coverage_vals.append(self._compute_solution_coverage(terms, fuzzy_data))

        return RobustnessTestResult(
            test_name="frequency_sensitivity",
            parameter_varied="frequency_threshold",
            parameter_values=thresholds,
            solution_stability=stability,
            coverage_stability=coverage_vals,
            passed=all(s >= 0.5 for s in stability),
        )

    # ── Membership Perturbation (FIXME-7) ──────────────────────────────────

    def test_membership_perturbation(
        self,
        fuzzy_data: FuzzySetData,
        baseline: QCAAnalysisResult,
        delta: float = 0.1,
    ) -> RobustnessTestResult:
        """Perturb condition membership scores and measure solution stability.

        Adds additive perturbation to condition columns only (the outcome
        column is excluded to avoid conflating with outcome sensitivity).
        This is a membership-level sensitivity test, distinct from true
        calibration sensitivity which would require perturbing calibration
        threshold parameters and re-running the calibration step.

        For true calibration sensitivity in a full pipeline context, perturb
        the CalibrationParams thresholds and re-run TextCalibrationStage.

        Args:
            fuzzy_data: Baseline fuzzy-set membership data.
            baseline: Baseline QCAAnalysisResult for Jaccard comparison.
            delta: Magnitude of additive perturbation (default 0.1).
        """
        baseline_terms = self._get_baseline_terms(baseline)
        stability: list[float] = []
        deltas = [-delta, -delta / 2, 0.0, delta / 2, delta]

        builder = TruthTableBuilder()
        qm = QuineMcCluskey()

        membership = fuzzy_data.membership.copy()

        for d in deltas:
            # Perturb condition columns only (NOT the outcome column)
            perturbed = membership.copy()
            perturbed[:, :-1] = np.clip(perturbed[:, :-1] + d, 0.0, 1.0)
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
            test_name="membership_perturbation",
            parameter_varied="membership_delta",
            parameter_values=deltas,
            solution_stability=stability,
            coverage_stability=[],
            passed=all(s >= 0.5 for s in stability),
        )

    def test_calibration_sensitivity(
        self,
        fuzzy_data: FuzzySetData,
        baseline: QCAAnalysisResult,
        delta: float = 0.1,
    ) -> RobustnessTestResult:
        """Membership perturbation test (backward-compatible alias).

        NOTE: This is currently a membership-level perturbation, not true
        calibration parameter sensitivity. The outcome column is excluded
        from perturbation. For full calibration sensitivity, perturb
        CalibrationParams thresholds and re-run calibration externally.

        Delegates to test_membership_perturbation().
        """
        result = self.test_membership_perturbation(fuzzy_data, baseline, delta)
        return RobustnessTestResult(
            test_name="calibration_sensitivity",
            parameter_varied="calibration_delta",
            parameter_values=result.parameter_values,
            solution_stability=result.solution_stability,
            coverage_stability=result.coverage_stability,
            passed=result.passed,
        )

    # ── Bootstrap Resampling (FIXME-8) ─────────────────────────────────────

    def test_bootstrap(
        self,
        fuzzy_data: FuzzySetData,
        baseline: QCAAnalysisResult,
        n_iterations: int = 100,
        sample_fraction: float = 1.0,
    ) -> RobustnessTestResult:
        """Bootstrap resampling: case resampling with replacement.

        For each bootstrap sample:
        1. Draw N * sample_fraction cases with replacement from the data
        2. Reconstruct truth table and run Boolean minimization
        3. Compute Jaccard similarity of resulting terms vs. baseline
        4. Track how often each baseline solution term appears

        The coverage_stability field contains the mean proportion of
        bootstrap samples in which each baseline solution term appears.
        solution_stability contains per-iteration Jaccard similarities.

        Args:
            fuzzy_data: Baseline fuzzy-set membership data.
            baseline: Baseline QCAAnalysisResult for comparison.
            n_iterations: Number of bootstrap resamples (default 100).
            sample_fraction: Fraction of cases to draw per sample
                (1.0 = same N as original data).
        """
        baseline_terms = self._get_baseline_terms(baseline)
        n_cases = fuzzy_data.n_cases
        sample_size = max(1, int(n_cases * sample_fraction))

        stability: list[float] = []
        term_appearance_counts: dict[tuple[str, ...], int] = {
            tuple(sorted(t)): 0 for t in baseline_terms
        }

        builder = TruthTableBuilder()
        qm = QuineMcCluskey()

        for _ in range(n_iterations):
            # Case resampling with replacement
            indices = np.random.choice(n_cases, size=sample_size, replace=True)
            bootstrap_membership = fuzzy_data.membership[indices, :].copy()
            bootstrap_fd = FuzzySetData(
                membership=bootstrap_membership,
                condition_names=fuzzy_data.condition_names,
                outcome_name=fuzzy_data.outcome_name,
            )

            tt = builder.build(bootstrap_fd)
            positive = tt.positive_rows
            if positive:
                terms = qm.minimize([r.config for r in positive], tt.condition_names)
            else:
                terms = []

            stability.append(self._jaccard_similarity(baseline_terms, terms))

            # Track which baseline terms appear in this bootstrap result
            bootstrap_set = {tuple(sorted(t)) for t in terms}
            for baseline_tuple in term_appearance_counts:
                if baseline_tuple in bootstrap_set:
                    term_appearance_counts[baseline_tuple] += 1

        # Compute mean term appearance proportion across all baseline terms
        if baseline_terms:
            term_proportions = [
                float(term_appearance_counts[tuple(sorted(t))]) / n_iterations
                for t in baseline_terms
            ]
            mean_proportion = float(np.mean(term_proportions))
        else:
            mean_proportion = 0.0

        return RobustnessTestResult(
            test_name="bootstrap_resampling",
            parameter_varied="bootstrap_iteration",
            parameter_values=list(range(n_iterations)),
            solution_stability=stability,
            coverage_stability=[mean_proportion],
            passed=bool(np.mean(stability) >= 0.5) if stability else True,
        )

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_solution_coverage(
        terms: list[list[str]], fuzzy_data: FuzzySetData
    ) -> float:
        """Compute overall solution coverage for a set of minimized terms.

        Uses the fuzzy-set sufficiency formula: for each term, compute case
        membership via fuzzy AND of condition memberships; then union all
        terms and compute raw coverage w.r.t. the outcome.

        Args:
            terms: List of solution terms from QM minimization.
            fuzzy_data: The fuzzy-set data used for this iteration.

        Returns:
            Solution coverage in [0, 1].
        """
        if not terms:
            return 0.0

        outcome = fuzzy_data.outcome_vector
        condition_matrix = fuzzy_data.condition_matrix
        condition_names = fuzzy_data.condition_names
        name_to_idx = {name: i for i, name in enumerate(condition_names)}

        term_memberships = []
        for term in terms:
            memb = _compute_term_membership(term, condition_matrix, name_to_idx)
            term_memberships.append(memb)

        return ConsistencyCalculator.solution_coverage(term_memberships, outcome)

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
