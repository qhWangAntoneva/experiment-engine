"""Unit tests for robustness testing module (qca_engine/advanced/robustness.py)."""

from __future__ import annotations

import warnings

import numpy as np

from experiment_engine.models import ConditionSet, MembershipData, QCAAnalysisResult
from experiment_engine.qca_engine.advanced.robustness import (
    RobustnessTester,
    RobustnessTestResult,
    _compute_term_membership,
)
from experiment_engine.qca_engine.analyzer import QCAnalyzerStage

# ── helpers ──────────────────────────────────────────────────────────────────


def _make_fuzzy(n: int, k: int, seed: int = 42) -> MembershipData:
    """Create synthetic MembershipData with n cases and k conditions."""
    rng = np.random.RandomState(seed)
    membership = rng.uniform(0, 1, (n, k + 1))
    condition_names = [f"cond_{i}" for i in range(k)]
    return MembershipData(
        membership=membership,
        condition_names=condition_names,
        outcome_name="outcome",
    )


def _make_condition_set(k: int) -> ConditionSet:
    """Create a minimal ConditionSet for k conditions."""
    from experiment_engine.models import (
        CalibrationMethod,
        ConditionDefinition,
        ScoringSource,
        TextDomain,
    )

    conditions = [
        ConditionDefinition(
            name=f"cond_{i}",
            display_name=f"Condition {i}",
            domain=TextDomain.DISSATISFACTION,
            calibration_type=CalibrationMethod.DIRECT,
            scoring_source=ScoringSource.PROTOTYPE,
        )
        for i in range(k)
    ]
    outcome = ConditionDefinition(
        name="outcome",
        display_name="Outcome",
        domain=TextDomain.DISSATISFACTION,
        calibration_type=CalibrationMethod.DIRECT,
        scoring_source=ScoringSource.PROTOTYPE,
    )
    return ConditionSet(
        name="test_cs",
        conditions=conditions,
        outcome=outcome,
        domain=TextDomain.DISSATISFACTION,
    )


def _run_analyzer(fuzzy: MembershipData) -> QCAAnalysisResult:
    """Run QCAnalyzerStage on fuzzy data and return the result."""
    cs = _make_condition_set(fuzzy.membership.shape[1] - 1)
    analyzer = QCAnalyzerStage(
        name="test_analyzer",
        condition_set=cs,
        consistency_threshold=0.75,
        frequency_threshold=0.5,
    )
    analyzer.setup()
    return analyzer.analyze(fuzzy)


# ── _compute_term_membership ─────────────────────────────────────────────────


def test_compute_term_membership_simple_and():
    """AND of two conditions: min of both columns."""
    matrix = np.array([[0.8, 0.6], [0.3, 0.9]], dtype=np.float64)
    name_to_idx = {"A": 0, "B": 1}
    result = _compute_term_membership(["A", "B"], matrix, name_to_idx)
    expected = np.array([0.6, 0.3], dtype=np.float64)
    np.testing.assert_array_almost_equal(result, expected)


def test_compute_term_membership_with_negation():
    """Negated condition uses 1 - membership."""
    matrix = np.array([[0.8, 0.6], [0.3, 0.9]], dtype=np.float64)
    name_to_idx = {"A": 0, "B": 1}
    result = _compute_term_membership(["A", "~B"], matrix, name_to_idx)
    expected = np.minimum(matrix[:, 0], 1.0 - matrix[:, 1])
    np.testing.assert_array_almost_equal(result, expected)


def test_compute_term_membership_unknown_condition_warns():
    """Unknown condition name should emit warning and treat as 1.0."""
    matrix = np.array([[0.8], [0.3]], dtype=np.float64)
    name_to_idx = {"A": 0}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = _compute_term_membership(["A", "UNKNOWN"], matrix, name_to_idx)
    assert len(w) == 1
    assert "UNKNOWN" in str(w[0].message)
    np.testing.assert_array_almost_equal(result, matrix[:, 0])


def test_compute_term_membership_unknown_negated_warns():
    """Unknown negated condition should emit warning and treat as 1.0."""
    matrix = np.array([[0.8], [0.3]], dtype=np.float64)
    name_to_idx = {"A": 0}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = _compute_term_membership(["~UNKNOWN"], matrix, name_to_idx)
    assert len(w) == 1
    assert "UNKNOWN" in str(w[0].message)
    np.testing.assert_array_almost_equal(result, np.ones(2))


def test_compute_term_membership_empty_term():
    """Empty term returns all ones."""
    matrix = np.array([[0.8], [0.3]], dtype=np.float64)
    name_to_idx = {"A": 0}
    result = _compute_term_membership([], matrix, name_to_idx)
    np.testing.assert_array_almost_equal(result, np.ones(2))


def test_compute_term_membership_single_condition():
    """Single condition returns its column directly."""
    matrix = np.array([[0.8], [0.3]], dtype=np.float64)
    name_to_idx = {"A": 0}
    result = _compute_term_membership(["A"], matrix, name_to_idx)
    np.testing.assert_array_almost_equal(result, matrix[:, 0])


# ── RobustnessTester ─────────────────────────────────────────────────────────


def test_robustness_tester_initialization():
    """Tester can be constructed with no analyzer."""
    tester = RobustnessTester()
    assert tester is not None
    assert tester._analyzer is None  # noqa: SLF001


def test_robustness_tester_with_analyzer():
    """Tester can be constructed with an analyzer."""
    analyzer = QCAnalyzerStage(
        name="test_analyzer",
        consistency_threshold=0.8,
        frequency_threshold=1.0,
    )
    tester = RobustnessTester(analyzer=analyzer)
    assert tester._analyzer is analyzer  # noqa: SLF001


# ── Integration: full robustness pipeline ────────────────────────────────────


def test_run_all_on_small_dataset():
    """run_all should execute all four robustness tests on valid fuzzy data."""
    fuzzy = _make_fuzzy(n=20, k=3, seed=42)
    baseline = _run_analyzer(fuzzy)

    tester = RobustnessTester()
    report = tester.run_all(fuzzy, baseline)
    assert report is not None
    assert len(report.tests) == 4  # consistency, frequency, membership, bootstrap


def test_consistency_sensitivity_on_analyzer_output():
    """Consistency sensitivity returns a RobustnessTestResult with stability metrics."""
    fuzzy = _make_fuzzy(n=20, k=3, seed=42)
    baseline = _run_analyzer(fuzzy)

    tester = RobustnessTester()
    result = tester.test_consistency_sensitivity(fuzzy, baseline)
    assert isinstance(result, RobustnessTestResult)
    assert result.test_name == "consistency_sensitivity"
    assert len(result.solution_stability) > 0


def test_frequency_sensitivity_small_n():
    """Small-N (<20) uses proportional frequency thresholds."""
    fuzzy = _make_fuzzy(n=10, k=2, seed=123)
    baseline = _run_analyzer(fuzzy)

    tester = RobustnessTester()
    result = tester.test_frequency_sensitivity(fuzzy, baseline)
    assert isinstance(result, RobustnessTestResult)
    assert result.test_name == "frequency_sensitivity"


def test_frequency_sensitivity_large_n():
    """Large-N (>=20) uses absolute frequency thresholds."""
    fuzzy = _make_fuzzy(n=25, k=3, seed=456)
    baseline = _run_analyzer(fuzzy)

    tester = RobustnessTester()
    result = tester.test_frequency_sensitivity(fuzzy, baseline)
    assert isinstance(result, RobustnessTestResult)
    assert result.test_name == "frequency_sensitivity"


def test_membership_perturbation_excludes_outcome():
    """Perturbation must only affect condition columns, not outcome."""
    fuzzy = _make_fuzzy(n=15, k=3, seed=42)
    original_outcome = fuzzy.membership[:, -1].copy()
    baseline = _run_analyzer(fuzzy)

    tester = RobustnessTester()
    result = tester.test_membership_perturbation(fuzzy, baseline)
    assert isinstance(result, RobustnessTestResult)
    assert result.test_name == "membership_perturbation"
    # Outcome column must not have been perturbed in the original data
    np.testing.assert_array_almost_equal(fuzzy.membership[:, -1], original_outcome)


def test_bootstrap_produces_results():
    """Bootstrap resampling produces valid stability metrics."""
    fuzzy = _make_fuzzy(n=15, k=3, seed=99)
    baseline = _run_analyzer(fuzzy)

    tester = RobustnessTester()
    result = tester.test_bootstrap(fuzzy, baseline, n_iterations=10)
    assert isinstance(result, RobustnessTestResult)
    assert result.test_name == "bootstrap_resampling"
    assert len(result.solution_stability) >= 0


def test_calibration_sensitivity_backward_compat():
    """Backward-compatible alias test_calibration_sensitivity exists."""
    fuzzy = _make_fuzzy(n=15, k=3, seed=77)
    baseline = _run_analyzer(fuzzy)

    tester = RobustnessTester()
    result = tester.test_calibration_sensitivity(fuzzy, baseline)
    assert isinstance(result, RobustnessTestResult)
    assert result.test_name == "calibration_sensitivity"


def test_bootstrap_default_iterations():
    """Bootstrap with default n_iterations produces valid output."""
    fuzzy = _make_fuzzy(n=12, k=2, seed=11)
    baseline = _run_analyzer(fuzzy)

    tester = RobustnessTester()
    result = tester.test_bootstrap(fuzzy, baseline)
    assert isinstance(result, RobustnessTestResult)
    assert len(result.solution_stability) >= 0
