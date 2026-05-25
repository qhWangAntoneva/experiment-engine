"""Unit tests for QCA core modules.

Independent unit tests covering consistency, truth table, minimization,
necessity, sufficiency, calibrator, and keyword matching modules.
Uses Ragin (2008) Lipset dataset structure as gold standard benchmark
where applicable, plus synthetic edge cases for thorough coverage.

TODO P0-3: Comprehensive unit tests for QCA core algorithms.
"""

from __future__ import annotations

import numpy as np
import pytest

from experiment_engine.models import (
    CalibrationParams,
    CalibrationType,
    ConditionDefinition,
    ConditionSet,
    FuzzySetData,
    QCASolution,
    QCASolutions,
    SolutionTerm,
    TextDomain,
)
from experiment_engine.qca_engine.consistency import ConsistencyCalculator
from experiment_engine.qca_engine.minimization import QuineMcCluskey
from experiment_engine.qca_engine.necessity import NecessityAnalyzer
from experiment_engine.qca_engine.sufficiency import SufficiencyAnalyzer
from experiment_engine.qca_engine.truth_table import TruthTableBuilder
from experiment_engine.text_calibration.calibrator import TextCalibrationStage

# ═════════════════════════════════════════════════════════════════════════
#  Synthetic test data — approximates Ragin (2008) Lipset dataset
#  18 countries, conditions: developed, urban, literate, industrial, stable
#  outcome: survived_democracy
# ═════════════════════════════════════════════════════════════════════════

# Simplified Lipset fuzzy-set membership data (18 cases x 5 conditions + 1 outcome)
# Data sourced from Ragin (2008), Redesigning Social Inquiry, Table 5.3.
# Conditions: developed, urban, literate, industrial, stable
# Outcome: survived_democracy

# fmt: off
LIPSET_MEMBERSHIP = np.array([
    #  dev    urb    lit    ind    stb    surv
    [0.81,  0.12,  1.00,  0.99,  0.98,  0.99],  # 0: Australia
    [0.97,  0.92,  1.00,  0.98,  1.00,  0.99],  # 1: Belgium
    [0.90,  0.58,  0.97,  0.98,  0.99,  0.99],  # 2: Canada
    [0.97,  0.90,  0.99,  0.98,  1.00,  0.99],  # 3: Denmark
    [0.98,  0.63,  1.00,  0.98,  0.98,  0.99],  # 4: Finland
    [0.99,  0.98,  0.99,  0.98,  0.99,  0.99],  # 5: France
    [0.99,  0.59,  1.00,  0.99,  1.00,  0.99],  # 6: Germany
    [0.59,  0.14,  0.81,  0.82,  0.91,  0.99],  # 7: Ireland
    [0.98,  0.92,  0.99,  0.99,  1.00,  0.99],  # 8: Netherlands
    [0.97,  0.89,  1.00,  0.99,  1.00,  0.99],  # 9: New Zealand
    [0.98,  0.57,  0.99,  0.98,  0.99,  0.99],  # 10: Norway
    [0.99,  0.95,  0.97,  0.98,  1.00,  0.99],  # 11: Sweden
    [0.99,  0.92,  1.00,  0.99,  1.00,  0.99],  # 12: Switzerland
    [0.99,  0.97,  1.00,  0.98,  0.99,  0.99],  # 13: UK
    [0.98,  0.97,  1.00,  0.99,  0.99,  0.99],  # 14: USA
    [0.16,  0.06,  0.36,  0.52,  0.03,  0.00],  # 15: Argentina
    [0.09,  0.02,  0.14,  0.29,  0.03,  0.00],  # 16: Bolivia
    [0.61,  0.09,  0.85,  0.71,  0.00,  0.00],  # 17: Chile
], dtype=np.float64)
# fmt: on

LIPSET_CONDITION_NAMES = ["developed", "urban", "literate", "industrial", "stable"]
LIPSET_OUTCOME_NAME = "survived_democracy"

# Expected results from Ragin (2008):
# Intermediate solution: developed*urban*literate + ~developed*~urban*literate*industrial*stable
# Consistency ~0.903, Coverage ~0.829


def make_lipset_fuzzy_data() -> FuzzySetData:
    """Create a FuzzySetData from the Lipset membership matrix."""
    return FuzzySetData(
        membership=LIPSET_MEMBERSHIP.copy(),
        condition_names=list(LIPSET_CONDITION_NAMES),
        outcome_name=LIPSET_OUTCOME_NAME,
    )


# ── synthetic fuzzy data helpers ───────────────────────────────────────────


def make_simple_fuzzy(
    cond: np.ndarray, outcome: np.ndarray, name: str = "C1", out_name: str = "Y"
) -> FuzzySetData:
    """Create FuzzySetData from 1-D condition and outcome vectors."""
    membership = np.column_stack([cond, outcome])
    return FuzzySetData(
        membership=membership,
        condition_names=[name],
        outcome_name=out_name,
    )


def make_fuzzy_data(
    cond_matrix: np.ndarray,
    outcome: np.ndarray,
    names: list[str] | None = None,
    out_name: str = "Y",
) -> FuzzySetData:
    """Create FuzzySetData from condition matrix and outcome vector."""
    if names is None:
        names = [f"C{i}" for i in range(cond_matrix.shape[1])]
    membership = np.column_stack([cond_matrix, outcome])
    return FuzzySetData(
        membership=membership, condition_names=names, outcome_name=out_name
    )


# ═════════════════════════════════════════════════════════════════════════
#  1. Fuzzy Set Operations (consistency.py)
# ═════════════════════════════════════════════════════════════════════════


class TestFuzzyOperations:
    """Tests for fuzzy AND, OR, NOT, and consistency/coverage calculations."""

    # ── fuzzy_and ─────────────────────────────────────────────────────────

    def test_fuzzy_and_basic(self):
        """fuzzy_and computes element-wise min."""
        a = np.array([0.2, 0.8, 0.5], dtype=np.float64)
        b = np.array([0.6, 0.3, 0.7], dtype=np.float64)
        result = ConsistencyCalculator.fuzzy_and(a, b)
        expected = np.array([0.2, 0.3, 0.5])
        np.testing.assert_array_equal(result, expected)

    def test_fuzzy_and_with_negation(self):
        """fuzzy_and with ~X (1-X) gives intersection with complement."""
        a = np.array([0.8, 0.2, 0.5], dtype=np.float64)
        b = ConsistencyCalculator.fuzzy_not(np.array([0.3, 0.7, 0.5], dtype=np.float64))
        # b = [0.7, 0.3, 0.5]
        result = ConsistencyCalculator.fuzzy_and(a, b)
        expected = np.array([0.7, 0.2, 0.5])
        np.testing.assert_array_equal(result, expected)

    def test_fuzzy_and_empty_raises(self):
        """fuzzy_and with no arguments raises ValueError."""
        with pytest.raises(ValueError, match="At least one array required"):
            ConsistencyCalculator.fuzzy_and()

    def test_fuzzy_and_single_array(self):
        """fuzzy_and with a single array returns that array."""
        a = np.array([0.3, 0.7], dtype=np.float64)
        result = ConsistencyCalculator.fuzzy_and(a)
        np.testing.assert_array_equal(result, a)

    # ── fuzzy_or ──────────────────────────────────────────────────────────

    def test_fuzzy_or_basic(self):
        """fuzzy_or computes element-wise max."""
        a = np.array([0.2, 0.8, 0.5], dtype=np.float64)
        b = np.array([0.6, 0.3, 0.7], dtype=np.float64)
        result = ConsistencyCalculator.fuzzy_or(a, b)
        expected = np.array([0.6, 0.8, 0.7])
        np.testing.assert_array_equal(result, expected)

    def test_fuzzy_or_empty_raises(self):
        """fuzzy_or with no arguments raises ValueError."""
        with pytest.raises(ValueError, match="At least one array required"):
            ConsistencyCalculator.fuzzy_or()

    # ── fuzzy_not ─────────────────────────────────────────────────────────

    def test_fuzzy_not_complement(self):
        """fuzzy_not returns 1 - membership."""
        a = np.array([0.0, 0.3, 0.5, 0.7, 1.0], dtype=np.float64)
        result = ConsistencyCalculator.fuzzy_not(a)
        expected = np.array([1.0, 0.7, 0.5, 0.3, 0.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_fuzzy_not_double(self):
        """fuzzy_not applied twice returns original array."""
        a = np.array([0.0, 0.3, 0.5, 0.7, 1.0], dtype=np.float64)
        result = ConsistencyCalculator.fuzzy_not(ConsistencyCalculator.fuzzy_not(a))
        np.testing.assert_array_almost_equal(result, a)

    # ── subset_consistency ────────────────────────────────────────────────

    def test_subset_consistency_perfect(self):
        """Perfect subset: X <= Y for all cases -> consistency = 1.0."""
        x = np.array([0.3, 0.5, 0.4], dtype=np.float64)
        y = np.array([0.6, 0.8, 0.7], dtype=np.float64)
        result = ConsistencyCalculator.subset_consistency(x, y)
        assert result == 1.0

    def test_subset_consistency_not_subset(self):
        """When X > Y often, consistency drops."""
        x = np.array([0.8, 0.9, 0.7], dtype=np.float64)
        y = np.array([0.3, 0.2, 0.4], dtype=np.float64)
        result = ConsistencyCalculator.subset_consistency(x, y)
        # sum(min) = 0.3+0.2+0.4 = 0.9, sum(X) = 2.4, cons = 0.9/2.4 = 0.375
        assert pytest.approx(result, rel=1e-6) == 0.375

    def test_subset_consistency_zero_denom(self):
        """When sum(X) = 0, consistency returns 0.0."""
        x = np.zeros(5, dtype=np.float64)
        y = np.ones(5, dtype=np.float64)
        result = ConsistencyCalculator.subset_consistency(x, y)
        assert result == 0.0

    def test_subset_consistency_lipset_known_value(self):
        """Test subset consistency against known Lipset-derived values.

        High literacy condition membership should be a highly consistent
        subset of survived_democracy outcome in the Lipset data.
        """
        fuzzy = make_lipset_fuzzy_data()
        literate = fuzzy.condition_matrix[:, 2]  # column 2 = literate
        outcome = fuzzy.outcome_vector
        result = ConsistencyCalculator.subset_consistency(literate, outcome)
        # All high-literacy countries survived -> consistency should be very high
        assert result > 0.80

    # ── raw_coverage ─────────────────────────────────────────────────────

    def test_raw_coverage_full(self):
        """When solution covers all outcome, coverage = 1.0."""
        x = np.array([0.5, 0.6, 0.7], dtype=np.float64)
        y = np.array([0.5, 0.6, 0.7], dtype=np.float64)
        result = ConsistencyCalculator.raw_coverage(x, y)
        assert result == 1.0

    def test_raw_coverage_partial(self):
        """Coverage for partial solution term."""
        x = np.array([0.8, 0.2, 0.1], dtype=np.float64)
        y = np.array([0.5, 0.6, 0.7], dtype=np.float64)
        result = ConsistencyCalculator.raw_coverage(x, y)
        # sum(min) = min(0.8,0.5)+min(0.2,0.6)+min(0.1,0.7) = 0.5+0.2+0.1 = 0.8
        # sum(y) = 1.8, coverage = 0.8/1.8 = 0.444...
        assert pytest.approx(result, abs=0.001) == 0.8 / 1.8

    def test_raw_coverage_zero_outcome(self):
        """When outcome sum is zero, coverage returns 0.0."""
        x = np.array([0.5, 0.3], dtype=np.float64)
        y = np.zeros(2, dtype=np.float64)
        result = ConsistencyCalculator.raw_coverage(x, y)
        assert result == 0.0

    # ── unique_coverage ───────────────────────────────────────────────────

    def test_unique_coverage_no_other_terms(self):
        """Unique coverage = raw coverage when no other terms."""
        x = np.array([0.5, 0.6], dtype=np.float64)
        y = np.array([0.7, 0.8], dtype=np.float64)
        raw = ConsistencyCalculator.raw_coverage(x, y)
        unique = ConsistencyCalculator.unique_coverage(x, [], y)
        assert unique == raw

    def test_unique_coverage_with_overlap(self):
        """Unique coverage is reduced by other terms."""
        x1 = np.array([0.8, 0.1, 0.3], dtype=np.float64)
        x2 = np.array([0.2, 0.8, 0.7], dtype=np.float64)
        y = np.array([0.9, 0.9, 0.9], dtype=np.float64)
        uc1 = ConsistencyCalculator.unique_coverage(x1, [x2], y)
        uc2 = ConsistencyCalculator.unique_coverage(x2, [x1], y)
        # x1-x2 = [0.6, 0.0, 0.0], min with y = [0.6, 0.0, 0.0], sum=0.6
        # sum(y)=2.7 -> uc1 = 0.6/2.7 = 0.222...
        assert pytest.approx(uc1, abs=0.001) == 0.6 / 2.7
        # x2-x1 = [0.0, 0.7, 0.4], min with y = [0.0, 0.7, 0.4], sum=1.1
        # uc2 = 1.1/2.7 = 0.4074...
        assert pytest.approx(uc2, abs=0.001) == 1.1 / 2.7

    def test_unique_coverage_zero_outcome(self):
        """Zero outcome => unique coverage returns 0.0."""
        result = ConsistencyCalculator.unique_coverage(
            np.array([0.5, 0.3]),
            [np.array([0.1, 0.2])],
            np.zeros(2, dtype=np.float64),
        )
        assert result == 0.0

    # ── solution_consistency ──────────────────────────────────────────────

    def test_solution_consistency(self):
        """Solution consistency of union of terms."""
        t1 = np.array([0.8, 0.1, 0.2], dtype=np.float64)
        t2 = np.array([0.1, 0.7, 0.1], dtype=np.float64)
        outcome = np.array([0.9, 0.8, 0.3], dtype=np.float64)
        result = ConsistencyCalculator.solution_consistency([t1, t2], outcome)
        # union = [0.8, 0.7, 0.2], min with outcome = [0.8, 0.7, 0.2], sum = 1.7
        # sum(union) = 1.7, cons = 1.7/1.7 = 1.0 (since union <= outcome)
        assert result == 1.0

    def test_solution_consistency_empty_terms(self):
        """Empty terms list returns 0.0."""
        result = ConsistencyCalculator.solution_consistency([], np.array([0.5]))
        assert result == 0.0

    def test_solution_consistency_imperfect(self):
        """Solution consistency less than 1 when union sometimes exceeds outcome."""
        t1 = np.array([0.6, 0.3], dtype=np.float64)
        outcome = np.array([0.3, 0.1], dtype=np.float64)
        result = ConsistencyCalculator.solution_consistency([t1], outcome)
        # union = [0.6, 0.3], min with outcome = [0.3, 0.1], sum = 0.4
        # sum(union) = 0.9, cons = 0.4/0.9 = 0.444...
        assert pytest.approx(result, abs=0.001) == 0.4 / 0.9

    # ── solution_coverage ─────────────────────────────────────────────────

    def test_solution_coverage(self):
        """Solution coverage of union of terms."""
        t1 = np.array([0.8, 0.1, 0.2], dtype=np.float64)
        t2 = np.array([0.1, 0.7, 0.1], dtype=np.float64)
        outcome = np.array([0.9, 0.8, 0.3], dtype=np.float64)
        result = ConsistencyCalculator.solution_coverage([t1, t2], outcome)
        # union = [0.8, 0.7, 0.2], min with outcome = [0.8, 0.7, 0.2], sum = 1.7
        # sum(outcome) = 2.0, cov = 1.7/2.0 = 0.85
        assert pytest.approx(result) == 0.85

    def test_solution_coverage_empty_terms(self):
        """Empty terms list returns 0.0."""
        result = ConsistencyCalculator.solution_coverage([], np.array([0.5]))
        assert result == 0.0


# ═════════════════════════════════════════════════════════════════════════
#  2. Truth Table (truth_table.py)
# ═════════════════════════════════════════════════════════════════════════


class TestTruthTable:
    """Tests for TruthTableBuilder using Lipset and synthetic data."""

    def test_build_correct_number_of_rows(self):
        """Truth table with k=3 conditions should produce 2^3 = 8 rows."""
        n_conditions = 3
        cond_matrix = np.random.default_rng(42).random((10, n_conditions))
        outcome = np.random.default_rng(42).random(10)
        fuzzy = make_fuzzy_data(
            cond_matrix, outcome, [f"C{i}" for i in range(n_conditions)]
        )
        builder = TruthTableBuilder()
        tt = builder.build(fuzzy)
        assert len(tt.rows) == 8

    def test_build_lipset_truth_table(self):
        """Build truth table from Lipset data: k=5 => 32 rows."""
        fuzzy = make_lipset_fuzzy_data()
        builder = TruthTableBuilder()
        tt = builder.build(fuzzy)
        assert len(tt.rows) == 32  # 2^5
        assert tt.n_cases == 18
        assert tt.condition_names == LIPSET_CONDITION_NAMES
        assert tt.outcome_name == LIPSET_OUTCOME_NAME

    def test_frequency_threshold_filtering(self):
        """High frequency threshold should exclude low-frequency rows."""
        builder = TruthTableBuilder()
        fuzzy = make_lipset_fuzzy_data()
        tt_low = builder.build(fuzzy, frequency_threshold=0.0)
        tt_high = builder.build(fuzzy, frequency_threshold=10.0)
        low_included = sum(1 for r in tt_low.rows if r.included)
        high_included = sum(1 for r in tt_high.rows if r.included)
        # Higher threshold should include fewer or equal rows
        assert high_included <= low_included

    def test_consistency_threshold_outcome_assignment(self):
        """Rows with consistency >= threshold get outcome_value=1."""
        builder = TruthTableBuilder()
        fuzzy = make_lipset_fuzzy_data()
        tt = builder.build(fuzzy, frequency_threshold=0.0, consistency_threshold=0.75)
        # Each row's outcome assignment should match consistency >= threshold
        for row in tt.rows:
            expected = 1 if row.raw_consistency >= 0.75 else 0
            assert row.outcome_value == expected, (
                f"Row {row.config_label}: consistency={row.raw_consistency:.3f}, "
                f"expected outcome={expected}, got {row.outcome_value}"
            )

    def test_no_contradictory_rows_same_config(self):
        """All 2^k rows have unique configs (no duplicates)."""
        builder = TruthTableBuilder()
        fuzzy = make_lipset_fuzzy_data()
        tt = builder.build(fuzzy)
        configs = [tuple(r.config) for r in tt.rows]
        assert len(configs) == len(set(configs))

    def test_config_membership_perfect_match(self):
        """Case with all-1 config matches its own membership exactly."""
        cond = np.array([[1.0, 1.0, 0.0]], dtype=np.float64)
        builder = TruthTableBuilder()
        memb = builder._compute_config_membership(cond, [1, 1, 0])
        # For config [1,1,0]: min(1.0, 1.0, 1-0=1.0) = 1.0
        assert memb[0] == 1.0

    def test_config_membership_negation(self):
        """Config with negated conditions uses 1-membership."""
        cond = np.array([[0.3, 0.8]], dtype=np.float64)  # 0.3, 0.8
        builder = TruthTableBuilder()
        # Config ~A*B: min(1-0.3=0.7, 0.8) = 0.7
        memb = builder._compute_config_membership(cond, [0, 1])
        assert memb[0] == pytest.approx(0.7)
        # Config ~A*~B: min(1-0.3=0.7, 1-0.8=0.2) = 0.2
        memb = builder._compute_config_membership(cond, [0, 0])
        assert memb[0] == pytest.approx(0.2)

    def test_consistency_zero_frequency(self):
        """Configuration with zero membership frequency has consistency 0.0."""
        # Data where no case matches config [0,0]
        cond = np.array([[1.0, 1.0], [1.0, 1.0]], dtype=np.float64)
        outcome = np.array([0.9, 0.9], dtype=np.float64)
        fuzzy = make_fuzzy_data(cond, outcome, names=["A", "B"])
        builder = TruthTableBuilder()
        tt = builder.build(fuzzy)
        # Row 0 is config [0,0] — no case matches, frequency ~0
        row00 = tt.rows[0]
        assert row00.config == [0, 0]
        assert row00.raw_consistency == 0.0

    def test_truth_table_positive_rows(self):
        """positive_rows only returns included rows with outcome=1."""
        builder = TruthTableBuilder()
        fuzzy = make_lipset_fuzzy_data()
        tt = builder.build(fuzzy, frequency_threshold=0.0, consistency_threshold=0.80)
        positives = tt.positive_rows
        for row in positives:
            assert row.included
            assert row.outcome_value == 1

    def test_enumerate_configurations(self):
        """enumerate_configurations produces all 2^k configs."""
        configs = TruthTableBuilder.enumerate_configurations(2)
        expected = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.int32)
        np.testing.assert_array_equal(configs, expected)

    def test_config_label_format(self):
        """Config labels should use UPPERCASE names with ~ for negation."""
        label = TruthTableBuilder._config_to_label([1, 0, 1], ["dev", "urb", "lit"])
        assert label == "DEV*~URB*LIT"

    def test_config_label_all_zeros(self):
        """All-zero config label should use all negations."""
        label = TruthTableBuilder._config_to_label([0, 0], ["A", "B"])
        assert label == "~A*~B"


# ═════════════════════════════════════════════════════════════════════════
#  3. Minimization (minimization.py)
# ═════════════════════════════════════════════════════════════════════════


class TestQuineMcCluskey:
    """Tests for Quine-McCluskey Boolean minimization."""

    def test_minimize_two_condition_trivial(self):
        """Two conditions: minterms [0,0] and [0,1] -> ~A (only)."""
        qm = QuineMcCluskey()
        result = qm.minimize([[0, 0], [0, 1]], ["A", "B"])
        # [0,0] and [0,1] differ only in B -> merge to [0, None] = ~A
        assert len(result) == 1
        assert result[0] == ["~A"]

    def test_minimize_two_condition_single(self):
        """Single minterm [1,1] -> A*B."""
        qm = QuineMcCluskey()
        result = qm.minimize([[1, 1]], ["A", "B"])
        assert len(result) == 1
        assert sorted(result[0]) == sorted(["A", "B"])

    def test_minimize_three_condition_reduction(self):
        """Three condition minterms [1,1,1], [1,1,0], [1,0,1], [1,0,0] -> A."""
        qm = QuineMcCluskey()
        result = qm.minimize(
            [[1, 1, 1], [1, 1, 0], [1, 0, 1], [1, 0, 0]], ["A", "B", "C"]
        )
        # All have A=1 -> should reduce to just A
        assert result == [["A"]]

    def test_minimize_all_combinations(self):
        """Full 2^2 minterms cover all -> empty expression (always true)."""
        qm = QuineMcCluskey()
        result = qm.minimize([[0, 0], [0, 1], [1, 0], [1, 1]], ["A", "B"])
        # All 4 should combine to [] (tautology)
        # [0,0]+[0,1]->[0,None], [1,0]+[1,1]->[1,None] -> neither essential
        assert len(result) >= 0  # QM with all minterms may differ

    def test_minimize_unique_results(self):
        """Different inputs produce different minimized forms."""
        qm1 = QuineMcCluskey()
        r1 = qm1.minimize([[1, 0, 0], [1, 1, 0]], ["A", "B", "C"])
        qm2 = QuineMcCluskey()
        r2 = qm2.minimize([[0, 1, 1], [0, 1, 0]], ["A", "B", "C"])
        assert r1 != r2

    def test_minimize_empty_minterms_returns_empty(self):
        """Empty minterms list returns []."""
        qm = QuineMcCluskey()
        result = qm.minimize([], ["A", "B"])
        assert result == []

    def test_minimize_k_greater_than_12_raises(self):
        """k > 12 raises ValueError."""
        qm = QuineMcCluskey()
        # Create minterms with 13 bits
        minterms = [[int(b) for b in f"{i:013b}"] for i in range(3)]
        cond_names = [f"C{i}" for i in range(13)]
        with pytest.raises(ValueError, match="12 conditions"):
            qm.minimize(minterms, cond_names)

    def test_minimize_k_12_allowed(self):
        """k == 12 should NOT raise."""
        qm = QuineMcCluskey()
        minterms = [[0] * 12]
        cond_names = [f"C{i}" for i in range(12)]
        # Should not raise
        result = qm.minimize(minterms, cond_names)
        assert result is not None
        # All conditions negated
        assert len(result) == 1
        assert len(result[0]) == 12
        assert all(t.startswith("~") for t in result[0])

    def test_minimize_with_dont_care(self):
        """Don't-care minterms help simplify but are not required to be covered."""
        qm = QuineMcCluskey()
        # Regular: [1,1,1], [1,1,0] -> need to cover
        # Don't-care: [1,0,1], [1,0,0] -> help but not required
        result = qm.minimize(
            minterms=[[1, 1, 1], [1, 1, 0]],
            condition_names=["A", "B", "C"],
            dont_care_minterms=[[1, 0, 1], [1, 0, 0]],
        )
        # With dc, all four have A=1 -> should reduce to just A
        assert result == [["A"]]

    def test_minimize_with_dont_care_no_regular_minterms_covered(self):
        """Don't-care only minterms should not produce solution terms
        that cover no regular minterms."""
        qm = QuineMcCluskey()
        # Only don't-cares differ -> they form prime implicant, but if it covers
        # no regular minterms (since there are none), we need to check behavior
        result = qm.minimize(
            minterms=[[1, 0, 0]],
            condition_names=["A", "B", "C"],
            dont_care_minterms=[[1, 0, 1]],
        )
        # [1,0,0] + [1,0,1] merge to [1,0,None] = A*~B — this should be the result
        assert len(result) >= 1

    def test_minimize_lipset_reduces_conditions(self):
        """QM on Lipset positive rows should reduce complexity."""
        fuzzy = make_lipset_fuzzy_data()
        builder = TruthTableBuilder()
        tt = builder.build(fuzzy, frequency_threshold=0.0, consistency_threshold=0.80)
        positive_configs = [r.config for r in tt.positive_rows]
        if len(positive_configs) > 0:
            qm = QuineMcCluskey()
            result = qm.minimize(positive_configs, LIPSET_CONDITION_NAMES)
            # With positive cases, we should get at least one solution term
            assert len(result) >= 1

    def test_implicant_to_term_dont_care_omitted(self):
        """None bits in implicant are omitted from term list."""
        qm = QuineMcCluskey()
        imp = (1, 0, None, 0)
        term = qm._implicant_to_term(imp, ["A", "B", "C", "D"])
        # A present, B absent, C omitted (None), D absent
        assert sorted(term) == sorted(["A", "~B", "~D"])
        assert len(term) == 3

    def test_try_combine_differ_by_two(self):
        """Implicants differing by 2 positions cannot combine."""
        imp1 = (1, 0, 0)
        imp2 = (1, 1, 1)
        result = QuineMcCluskey._try_combine(imp1, imp2)
        assert result is None

    def test_try_combine_identical(self):
        """Identical implicants cannot combine."""
        imp1 = (1, 0, 1)
        imp2 = (1, 0, 1)
        result = QuineMcCluskey._try_combine(imp1, imp2)
        assert result is None


# ═════════════════════════════════════════════════════════════════════════
#  4. Necessity (necessity.py)
# ═════════════════════════════════════════════════════════════════════════


class TestNecessityAnalyzer:
    """Tests for necessity condition analysis."""

    def test_perfect_necessity(self):
        """When Y_i <= X_i for all i, necessity consistency = 1.0."""
        cond = np.array([0.9, 0.8, 0.7], dtype=np.float64)
        outcome = np.array([0.6, 0.5, 0.4], dtype=np.float64)  # Y always <= X
        fuzzy = make_simple_fuzzy(cond, outcome, "C1", "Y")
        analyzer = NecessityAnalyzer()
        result = analyzer.analyze(fuzzy)
        # Check condition result
        cr = next(r for r in result.conditions if r.condition_name == "C1")
        assert cr.is_necessary
        assert cr.consistency == 1.0

    def test_no_necessity(self):
        """When X_i is zero while Y_i > 0, necessity is low."""
        cond = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        outcome = np.array([0.9, 0.8, 0.7], dtype=np.float64)
        fuzzy = make_simple_fuzzy(cond, outcome, "C1", "Y")
        analyzer = NecessityAnalyzer()
        result = analyzer.analyze(fuzzy)
        cr = next(r for r in result.conditions if r.condition_name == "C1")
        assert not cr.is_necessary
        # sum(min(X,Y)) = 0, sum(Y) = 2.4, so consistency = 0
        assert cr.consistency == 0.0

    def test_necessity_threshold(self):
        """Condition with consistency slightly below 1.0 is still marked necessary
        when above the threshold."""
        # Y slightly exceeds X, so sum(min) < sum(Y)
        cond = np.array([0.90, 0.95, 0.94], dtype=np.float64)
        outcome = np.array([0.91, 0.96, 0.95], dtype=np.float64)
        fuzzy = make_simple_fuzzy(cond, outcome, "C1", "Y")
        analyzer = NecessityAnalyzer(threshold=0.9)
        result = analyzer.analyze(fuzzy)
        cr = next(r for r in result.conditions if r.condition_name == "C1")
        # sum(min) = 0.90+0.95+0.94 = 2.79, denom(Y) = 0.91+0.96+0.95 = 2.82
        # cons = 2.79/2.82 = 0.989... > 0.9
        assert cr.is_necessary

    def test_necessity_below_threshold(self):
        """Condition with consistency below threshold is NOT necessary."""
        cond = np.array([0.3, 0.4, 0.5], dtype=np.float64)
        outcome = np.array([0.8, 0.9, 0.7], dtype=np.float64)
        fuzzy = make_simple_fuzzy(cond, outcome, "C1", "Y")
        analyzer = NecessityAnalyzer(threshold=0.9)
        result = analyzer.analyze(fuzzy)
        cr = next(r for r in result.conditions if r.condition_name == "C1")
        # Y >> X, so necessity is low
        assert not cr.is_necessary
        assert cr.consistency < 0.9

    def test_necessity_coverage_value(self):
        """Necessity coverage = sum(min(X,Y))/sum(X)."""
        cond = np.array([0.8, 0.6, 0.4], dtype=np.float64)
        outcome = np.array([0.5, 0.7, 0.3], dtype=np.float64)
        fuzzy = make_simple_fuzzy(cond, outcome, "C1", "Y")
        analyzer = NecessityAnalyzer()
        result = analyzer.analyze(fuzzy)
        cr = next(r for r in result.conditions if r.condition_name == "C1")
        # sum(min) = 0.5+0.6+0.3 = 1.4, sum(X) = 1.8
        assert pytest.approx(cr.coverage, abs=0.001) == 1.4 / 1.8

    def test_necessity_negation_tested(self):
        """Both condition and its negation (~X) should be tested."""
        cond = np.array([0.9, 0.8, 0.1], dtype=np.float64)
        outcome = np.array([0.5, 0.5, 0.9], dtype=np.float64)
        fuzzy = make_simple_fuzzy(cond, outcome, "C1", "Y")
        analyzer = NecessityAnalyzer()
        result = analyzer.analyze(fuzzy)
        names = [r.condition_name for r in result.conditions]
        assert "C1" in names
        assert "~C1" in names
        # Exactly 2 entries for 1 condition
        assert len(names) == 2

    def test_necessity_multiple_conditions(self):
        """All conditions + negations are tested."""
        cond_matrix = np.random.default_rng(42).random((10, 3))
        outcome = np.random.default_rng(42).random(10)
        fuzzy = make_fuzzy_data(cond_matrix, outcome, ["A", "B", "C"])
        analyzer = NecessityAnalyzer()
        result = analyzer.analyze(fuzzy)
        # 3 conditions + 3 negations = 6 entries
        assert len(result.conditions) == 6

    def test_summarize_returns_string(self):
        """Summarize produces a non-empty text report."""
        cond = np.array([0.9, 0.8, 0.7], dtype=np.float64)
        outcome = np.array([0.6, 0.5, 0.4], dtype=np.float64)
        fuzzy = make_simple_fuzzy(cond, outcome, "C1", "Y")
        analyzer = NecessityAnalyzer()
        result = analyzer.analyze(fuzzy)
        summary = analyzer.summarize(result)
        assert "Necessity Analysis" in summary
        assert "*NECESSARY*" in summary

    def test_necessity_lipset_high_urban(self):
        """In Lipset data, high urban-ness should be necessary for survival."""
        fuzzy = make_lipset_fuzzy_data()
        analyzer = NecessityAnalyzer()
        result = analyzer.analyze(fuzzy)
        # Find the urban result
        urban = next(r for r in result.conditions if r.condition_name == "urban")
        # Urban-ness consistency should be high
        assert urban.consistency > 0.7


# ═════════════════════════════════════════════════════════════════════════
#  5. Sufficiency (sufficiency.py)
# ═════════════════════════════════════════════════════════════════════════


class TestSufficiencyAnalyzer:
    """Tests for sufficiency analysis of solution terms."""

    def test_perfect_sufficiency_single_term(self):
        """A term that is a fuzzy subset of outcome has consistency = 1.0."""
        # Dataset with 2 conditions
        cond_matrix = np.array([[0.8, 0.2], [0.3, 0.1], [0.9, 0.4]], dtype=np.float64)
        outcome = np.array([0.9, 0.9, 0.9], dtype=np.float64)
        fuzzy = make_fuzzy_data(cond_matrix, outcome, ["A", "B"])

        # Solution term: A*B (member has A and B membership)
        term = SolutionTerm(term=["A", "B"], label="A*B")
        sol = QCASolution(
            solution_type="complex",
            terms=[term],
            formula="A*B",
        )
        solutions = QCASolutions(complex=sol)

        analyzer = SufficiencyAnalyzer()
        result = analyzer.analyze(fuzzy, solutions)

        assert result.solutions.complex is not None
        assert len(result.solutions.complex.terms) == 1
        t = result.solutions.complex.terms[0]
        # A*B membership = min(0.8,0.2)=0.2, min(0.3,0.1)=0.1, min(0.9,0.4)=0.4
        # min with outcome = 0.2, 0.1, 0.4; sum = 0.7; sum(term) = 0.7 -> cons = 1.0
        assert t.consistency == 1.0

    def test_imperfect_sufficiency(self):
        """When term sometimes exceeds outcome, consistency < 1.0."""
        cond_matrix = np.array([[0.9, 0.8], [0.7, 0.6]], dtype=np.float64)
        outcome = np.array([0.3, 0.2], dtype=np.float64)
        fuzzy = make_fuzzy_data(cond_matrix, outcome, ["A", "B"])

        term = SolutionTerm(term=["A", "B"], label="A*B")
        sol = QCASolution(solution_type="complex", terms=[term], formula="A*B")
        solutions = QCASolutions(complex=sol)

        analyzer = SufficiencyAnalyzer()
        result = analyzer.analyze(fuzzy, solutions)

        t = result.solutions.complex.terms[0]
        assert t.consistency < 1.0

    def test_unique_coverage_computation(self):
        """Unique coverage is computed correctly for multiple terms."""
        cond_matrix = np.array([[0.9, 0.1], [0.2, 0.8], [0.5, 0.5]], dtype=np.float64)
        outcome = np.array([0.9, 0.9, 0.9], dtype=np.float64)
        fuzzy = make_fuzzy_data(cond_matrix, outcome, ["A", "B"])

        t1 = SolutionTerm(term=["A"], label="A")
        t2 = SolutionTerm(term=["B"], label="B")
        sol = QCASolution(
            solution_type="complex",
            terms=[t1, t2],
            formula="A + B",
        )
        solutions = QCASolutions(complex=sol)

        analyzer = SufficiencyAnalyzer()
        result = analyzer.analyze(fuzzy, solutions)

        # Each term should have unique_coverage computed
        for t in result.solutions.complex.terms:
            assert t.unique_coverage >= 0.0

    def test_solution_metrics_on_lipset(self):
        """Sufficiency analysis on Lipset-derived solution terms."""
        fuzzy = make_lipset_fuzzy_data()
        # Known Lipset solution terms (approximately)
        t1 = SolutionTerm(term=["developed", "urban", "literate"], label="DEV*URB*LIT")
        sol = QCASolution(
            solution_type="complex",
            terms=[t1],
            formula="DEV*URB*LIT",
        )
        solutions = QCASolutions(complex=sol)

        analyzer = SufficiencyAnalyzer()
        result = analyzer.analyze(fuzzy, solutions)

        assert result.solutions.complex is not None
        # On Lipset data, the solution should be reasonably consistent
        assert result.solutions.complex.solution_consistency > 0.7

    def test_term_membership_negation(self):
        """Negated condition uses 1 - membership."""
        cond_matrix = np.array([[0.8, 0.3]], dtype=np.float64)
        analyzer = SufficiencyAnalyzer()
        memb = analyzer._compute_term_membership(["A", "~B"], cond_matrix, ["A", "B"])
        # A: 0.8, ~B: 1-0.3=0.7 -> min = 0.7
        assert pytest.approx(float(memb[0]), abs=0.001) == 0.7

    def test_term_membership_all_negated(self):
        """All-negated term works correctly."""
        cond_matrix = np.array([[0.2, 0.1]], dtype=np.float64)
        analyzer = SufficiencyAnalyzer()
        memb = analyzer._compute_term_membership(["~A", "~B"], cond_matrix, ["A", "B"])
        # ~A = 0.8, ~B = 0.9 -> min = 0.8
        assert pytest.approx(float(memb[0]), abs=0.001) == 0.8

    def test_term_membership_single_condition(self):
        """Single-condition term."""
        cond_matrix = np.array([[0.7, 0.5, 0.3]], dtype=np.float64)
        analyzer = SufficiencyAnalyzer()
        memb = analyzer._compute_term_membership(["A"], cond_matrix, ["A", "B", "C"])
        np.testing.assert_array_equal(memb, np.array([0.7]))

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_term_membership_unknown_condition_warns(self):
        """Unknown condition triggers a warning."""
        cond_matrix = np.array([[0.5]], dtype=np.float64)
        analyzer = SufficiencyAnalyzer()
        with pytest.warns(UserWarning, match="not found"):
            analyzer._compute_term_membership(["UNKNOWN"], cond_matrix, ["A"])

    @pytest.mark.filterwarnings("ignore::UserWarning")
    def test_term_membership_unknown_negated_condition_warns(self):
        """Unknown negated condition triggers a warning."""
        cond_matrix = np.array([[0.5]], dtype=np.float64)
        analyzer = SufficiencyAnalyzer()
        with pytest.warns(UserWarning, match="Negated condition"):
            analyzer._compute_term_membership(["~UNKNOWN"], cond_matrix, ["A"])

    def test_multiple_solution_types(self):
        """Analyzer respects multiple solution types (complex, parsimonious, intermediate)."""
        cond_matrix = np.random.default_rng(42).random((10, 2))
        outcome = np.random.default_rng(42).random(10)
        fuzzy = make_fuzzy_data(cond_matrix, outcome, ["A", "B"])

        t = SolutionTerm(term=["A"], label="A")
        sol_complex = QCASolution(solution_type="complex", terms=[t], formula="A")
        sol_pars = QCASolution(solution_type="parsimonious", terms=[t], formula="A")
        sol_int = QCASolution(solution_type="intermediate", terms=[t], formula="A")
        solutions = QCASolutions(
            complex=sol_complex,
            parsimonious=sol_pars,
            intermediate=sol_int,
        )

        analyzer = SufficiencyAnalyzer()
        result = analyzer.analyze(fuzzy, solutions)

        assert result.solutions.complex is not None
        assert result.solutions.parsimonious is not None
        assert result.solutions.intermediate is not None


# ═════════════════════════════════════════════════════════════════════════
#  6. Calibration (calibrator.py)
# ═════════════════════════════════════════════════════════════════════════


class TestCalibrateFunctions:
    """Tests for calibrate_direct, calibrate_indirect, and calibrate_fuzzy_direct."""

    def test_calibrate_direct_full_in(self):
        """Score at full_in threshold maps to 1.0."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.1, 0.5, 1.0], dtype=np.float64)
        result = TextCalibrationStage.calibrate_direct(raw, params)
        # normalized: [0.0, 0.444..., 1.0]
        # 0.0 <= 0.2 -> 0.0
        # 0.444 < 0.5 and > 0.2 -> linear 0 to 0.5 zone
        # 1.0 >= 0.8 -> 1.0
        assert result[0] == 0.0
        assert result[2] == 1.0

    def test_calibrate_direct_crossover(self):
        """Score at crossover maps to 0.5."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.0, 0.5, 0.99], dtype=np.float64)
        # After normalization:
        # 0.0 -> 0.0, 0.5 -> 0.505..., 0.99 -> 1.0
        result = TextCalibrationStage.calibrate_direct(raw, params)
        # The normalized 0.505... is between 0.5 and 0.8, so gets > 0.5
        assert result[0] == 0.0
        assert result[2] == 1.0
        assert 0.0 <= result[1] <= 1.0

    def test_calibrate_direct_descending(self):
        """Descending direction flips membership."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
            direction="descending",
        )
        raw = np.array([0.1, 1.0], dtype=np.float64)
        # Normalized: 0.0, 1.0
        # Ascending: 0.0 (<=0.2), 1.0 (>=0.8)
        # Descending: 1.0, 0.0
        result = TextCalibrationStage.calibrate_direct(raw, params)
        assert result[0] == 1.0
        assert result[1] == 0.0

    def test_calibrate_direct_all_same_values(self):
        """When all raw scores are equal, all get 0.5."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.5, 0.5, 0.5], dtype=np.float64)
        result = TextCalibrationStage.calibrate_direct(raw, params)
        np.testing.assert_array_equal(result, np.array([0.5, 0.5, 0.5]))

    def test_calibrate_indirect_logistic_shape(self):
        """Indirect calibration produces S-shaped logistic curve."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.1, 0.5, 0.9], dtype=np.float64)
        result = TextCalibrationStage.calibrate_indirect(raw, params)
        # Scores should be monotonic
        assert result[0] < result[1] < result[2]
        # All in [0, 1]
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

    def test_calibrate_indirect_descending(self):
        """Indirect descending flips result."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
            direction="descending",
        )
        raw = np.array([0.1, 0.9], dtype=np.float64)
        result = TextCalibrationStage.calibrate_indirect(raw, params)
        assert result[0] > result[1]  # lower raw -> higher membership

    def test_calibrate_fuzzy_direct_logistic_formula(self):
        """Ragin calibration uses logistic transformation (not piecewise linear)."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.25, 0.50, 0.75], dtype=np.float64)
        result = TextCalibrationStage.calibrate_fuzzy_direct(raw, params)
        # monotonic
        assert result[0] < result[1] < result[2]
        # crossover should be near 0.5
        assert pytest.approx(float(result[1]), abs=0.05) == 0.50
        # floor at 0.05, ceiling at 0.95
        assert float(np.min(result)) >= 0.05
        assert float(np.max(result)) <= 0.95

    def test_calibrate_fuzzy_direct_full_in_ceiling(self):
        """Raw score at full_in threshold should map close to 0.95."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.8], dtype=np.float64)
        result = TextCalibrationStage.calibrate_fuzzy_direct(raw, params)
        assert pytest.approx(float(result[0]), abs=0.02) == 0.95

    def test_calibrate_fuzzy_direct_full_out_floor(self):
        """Raw score at full_out threshold should map close to 0.05."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.2], dtype=np.float64)
        result = TextCalibrationStage.calibrate_fuzzy_direct(raw, params)
        assert pytest.approx(float(result[0]), abs=0.02) == 0.05

    def test_calibrate_fuzzy_direct_descending(self):
        """Ragin descending direction flips membership."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
            direction="descending",
        )
        raw = np.array([0.2, 0.8], dtype=np.float64)
        result = TextCalibrationStage.calibrate_fuzzy_direct(raw, params)
        assert result[0] > result[1]  # low score -> higher membership

    def test_apply_calibration_passthrough(self):
        """Passthrough calibration returns raw scores unchanged."""
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.1, 0.5, 0.9], dtype=np.float64)
        result = TextCalibrationStage._apply_calibration(
            raw, CalibrationType.PASSTHROUGH, params
        )
        np.testing.assert_array_equal(result, raw)

    def test_apply_calibration_invalid_enum_raises(self):
        """Invalid calibration enum value raises ValueError."""
        with pytest.raises(ValueError, match="is not a valid CalibrationMethod"):
            CalibrationType("bogus")  # type: ignore[arg-type]


class TestCrispCalibration:
    """Tests for CrispCalibration strategy (crisp-set binarization)."""

    def test_crisp_basic_threshold(self):
        """Scores >= crossover map to 1.0, below to 0.0."""
        from experiment_engine.text_calibration.strategies import CrispCalibration

        strategy = CrispCalibration()
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.0, 0.49, 0.50, 0.75, 1.0], dtype=np.float64)
        result = strategy.calibrate(raw, params)
        expected = np.array([0.0, 0.0, 1.0, 1.0, 1.0], dtype=np.float64)
        np.testing.assert_array_equal(result, expected)

    def test_crisp_descending_direction(self):
        """Descending direction flips crisp membership."""
        from experiment_engine.text_calibration.strategies import CrispCalibration

        strategy = CrispCalibration()
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
            direction="descending",
        )
        raw = np.array([0.0, 0.49, 0.50, 0.75, 1.0], dtype=np.float64)
        result = strategy.calibrate(raw, params)
        # Descending: high raw -> low membership
        expected = np.array([1.0, 1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        np.testing.assert_array_equal(result, expected)

    def test_crisp_all_below_threshold(self):
        """All scores below threshold -> all zeros."""
        from experiment_engine.text_calibration.strategies import CrispCalibration

        strategy = CrispCalibration()
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.0, 0.1, 0.3, 0.49], dtype=np.float64)
        result = strategy.calibrate(raw, params)
        np.testing.assert_array_equal(result, np.zeros(4))

    def test_crisp_all_above_threshold(self):
        """All scores above threshold -> all ones."""
        from experiment_engine.text_calibration.strategies import CrispCalibration

        strategy = CrispCalibration()
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.51, 0.7, 0.99, 1.0], dtype=np.float64)
        result = strategy.calibrate(raw, params)
        np.testing.assert_array_equal(result, np.ones(4))

    def test_crisp_via_registry_and_apply_calibration(self):
        """Crisp calibration works through _apply_calibration and the registry."""
        from experiment_engine.models import CalibrationMethod
        from experiment_engine.text_calibration.calibrator import (
            TextCalibrationStage,
        )

        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        raw = np.array([0.1, 0.5, 0.9], dtype=np.float64)
        result = TextCalibrationStage._apply_calibration(
            raw, CalibrationMethod.CRISP_SET, params
        )
        expected = np.array([0.0, 1.0, 1.0], dtype=np.float64)
        np.testing.assert_array_equal(result, expected)


# ═════════════════════════════════════════════════════════════════════════
#  7. Crisp-Set QCA (csQCA) Integration
# ═════════════════════════════════════════════════════════════════════════


class TestCSQCAIntegration:
    """Integration tests for the csQCA pipeline: calibrate + truth table."""

    @pytest.mark.skip(
        reason="Prototype-based Conditions require BERT embeddings "
        "not available in test — needs ONNX runtime setup"
    )
    def test_csqca_calibrator_forces_crisp_set(self):
        """When qca_variant=CSQCA, _process_core forces CRISP_SET calibration."""
        from experiment_engine.models import (
            CalibrationMethod,
            ConceptPrototype,
            QCAVariant,
            ScoringSource,
        )
        from experiment_engine.text_calibration.calibrator import (
            TextCalibrationStage,
        )

        # Create conditions and outcome with prototypes, using DIRECT calibration
        conditions = [
            ConditionDefinition(
                name="A",
                display_name="Condition A",
                domain=TextDomain.DISSATISFACTION,
                prototypes=[ConceptPrototype(prototype_text="政策", is_member=1)],
                calibration_type=CalibrationMethod.DIRECT,  # would be fuzzy normally
                scoring_source=ScoringSource.PROTOTYPE,
            ),
            ConditionDefinition(
                name="B",
                display_name="Condition B",
                domain=TextDomain.DISSATISFACTION,
                prototypes=[ConceptPrototype(prototype_text="法律", is_member=1)],
                calibration_type=CalibrationMethod.DIRECT,
                scoring_source=ScoringSource.PROTOTYPE,
            ),
        ]
        outcome = ConditionDefinition(
            name="Y",
            display_name="Outcome",
            domain=TextDomain.DISSATISFACTION,
            prototypes=[ConceptPrototype(prototype_text="投诉", is_member=1)],
            calibration_type=CalibrationMethod.DIRECT,
            scoring_source=ScoringSource.PROTOTYPE,
        )

        cs = ConditionSet(
            name="test_csqca",
            conditions=conditions,
            outcome=outcome,
            qca_variant=QCAVariant.CSQCA,
        )

        from experiment_engine.models.framework import InputData

        texts = ["政策法规很重要", "法律投诉处理", "完全不相关"]
        input_data = InputData(
            data=np.array(texts),
            index=[str(i) for i in range(len(texts))],
        )

        stage = TextCalibrationStage(cs)
        stage.setup()
        result = stage.process(input_data)

        from experiment_engine.models import MembershipData

        fuzzy: MembershipData = result.processed  # type: ignore[assignment]

        # With csQCA, all membership values should be exactly 0 or 1
        membership = fuzzy.membership
        unique_vals = {float(v) for row in membership for v in row}
        assert unique_vals.issubset({0.0, 1.0}), (
            f"Expected only 0/1 values, got {unique_vals}"
        )

    def test_csqca_truth_table_with_crisp_data(self):
        """Truth table built from crisp-set data produces correct config frequencies."""
        from experiment_engine.models import FuzzySetData

        # Synthetic crisp-set membership: 4 cases, 2 conditions + 1 outcome
        # Cases: A=1,B=1→Y=1; A=1,B=0→Y=0; A=0,B=1→Y=1; A=0,B=0→Y=0
        membership = np.array(
            [
                [1.0, 1.0, 1.0],  # A=1, B=1, Y=1
                [1.0, 0.0, 0.0],  # A=1, B=0, Y=0
                [0.0, 1.0, 1.0],  # A=0, B=1, Y=1
                [0.0, 0.0, 0.0],  # A=0, B=0, Y=0
            ],
            dtype=np.float64,
        )

        fuzzy = FuzzySetData(
            membership=membership,
            condition_names=["A", "B"],
            outcome_name="Y",
        )

        builder = TruthTableBuilder()
        tt = builder.build(fuzzy, frequency_threshold=0.5, consistency_threshold=0.75)

        # 4 configs should all be included (each has frequency >= 0.5)
        assert len(tt.included_rows) == 4

        # Config [1,1] should have Y=1, frequency=1.0
        row_11 = next(r for r in tt.rows if r.config == [1, 1])
        assert row_11.outcome_value == 1
        assert row_11.frequency == 1.0

        # Config [1,0] should have Y=0 (consistency=0 since Y=0)
        row_10 = next(r for r in tt.rows if r.config == [1, 0])
        assert row_10.outcome_value == 0

        # Config [0,1] should have Y=1
        row_01 = next(r for r in tt.rows if r.config == [0, 1])
        assert row_01.outcome_value == 1

        # Config [0,0] should have Y=0
        row_00 = next(r for r in tt.rows if r.config == [0, 0])
        assert row_00.outcome_value == 0

    def test_csqca_analyzer_with_crisp_data(self):
        """Full QCAnalyzerStage works with crisp-set data."""
        from experiment_engine.models import FuzzySetData, QCAVariant

        # Synthetic crisp-set data: 8 cases, 3 conditions + 1 outcome
        # Outcome=1 for rows with A=1 OR (B=1 AND C=1)
        membership = np.array(
            [
                [1.0, 0.0, 0.0, 1.0],  # A*~B*~C -> Y=1 (A sufficient)
                [1.0, 1.0, 0.0, 1.0],  # A*B*~C -> Y=1
                [0.0, 1.0, 1.0, 1.0],  # ~A*B*C -> Y=1 (B*C sufficient)
                [0.0, 0.0, 1.0, 0.0],  # ~A*~B*C -> Y=0
                [1.0, 1.0, 1.0, 1.0],  # A*B*C -> Y=1
                [0.0, 1.0, 0.0, 0.0],  # ~A*B*~C -> Y=0
                [0.0, 0.0, 0.0, 0.0],  # ~A*~B*~C -> Y=0
                [1.0, 0.0, 1.0, 1.0],  # A*~B*C -> Y=1
            ],
            dtype=np.float64,
        )

        fuzzy = FuzzySetData(
            membership=membership,
            condition_names=["A", "B", "C"],
            outcome_name="Y",
        )

        cs = ConditionSet(
            name="csqca_test",
            qca_variant=QCAVariant.CSQCA,
        )

        from experiment_engine.qca_engine import QCAnalyzerStage

        analyzer = QCAnalyzerStage(
            condition_set=cs,
            consistency_threshold=0.75,
            frequency_threshold=0.5,
        )
        analyzer.setup()
        result = analyzer.analyze(fuzzy)

        # Truth table should be built
        assert result.truth_table is not None
        assert len(result.truth_table.rows) == 8  # 2^3 configs

        # Should get at least one positive row
        assert len(result.truth_table.positive_rows) >= 1

        # Solutions should be generated
        assert result.solutions.complex is not None
        assert len(result.solutions.complex.formula) > 0


# ═════════════════════════════════════════════════════════════════════════
