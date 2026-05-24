"""Unit tests for NLInterpreter — Chinese natural language QCA result interpretation."""

import pytest

from experiment_engine.models import (
    ConditionDefinition,
    ConditionSet,
    NecessityConditionResult,
    NecessityResults,
    QCASolution,
    QCASolutions,
    SolutionTerm,
    TextDomain,
)
from experiment_engine.qca_engine.nl_interpretation import NLInterpreter

# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def sample_condition_set() -> ConditionSet:
    """A realistic citizen-feedback QCA condition set."""
    conditions = [
        ConditionDefinition(
            name="DISSATISFACTION",
            display_name="不满程度",
            domain=TextDomain.DISSATISFACTION,
        ),
        ConditionDefinition(
            name="POLICY_DEMAND",
            display_name="政策需求",
            domain=TextDomain.POLICY_DEMAND,
        ),
        ConditionDefinition(
            name="CO_PRODUCTION",
            display_name="合产参与",
            domain=TextDomain.CO_PRODUCTION,
        ),
        ConditionDefinition(
            name="TRUST",
            display_name="信任程度",
            domain=TextDomain.TRUST,
        ),
    ]
    outcome = ConditionDefinition(
        name="GOV_RESPONSIVENESS",
        display_name="政府回应",
        domain=TextDomain.GOV_RESPONSIVENESS,
    )
    return ConditionSet(
        name="citizen_feedback_model",
        conditions=conditions,
        outcome=outcome,
    )


@pytest.fixture
def interpreter(sample_condition_set: ConditionSet) -> NLInterpreter:
    return NLInterpreter(sample_condition_set)


@pytest.fixture
def sample_solutions() -> QCASolutions:
    """Solutions with two paths: DISSATISFACTION*~POLICY_DEMAND + CO_PRODUCTION*TRUST."""
    t1 = SolutionTerm(
        term=["DISSATISFACTION", "~POLICY_DEMAND"],
        label="DISSATISFACTION*~POLICY_DEMAND",
        consistency=0.892,
        raw_coverage=0.456,
        unique_coverage=0.234,
    )
    t2 = SolutionTerm(
        term=["CO_PRODUCTION", "TRUST"],
        label="CO_PRODUCTION*TRUST",
        consistency=0.915,
        raw_coverage=0.367,
        unique_coverage=0.145,
    )
    return QCASolutions(
        complex=QCASolution(
            solution_type="complex",
            terms=[t1, t2],
            formula="DISSATISFACTION*~POLICY_DEMAND + CO_PRODUCTION*TRUST",
            solution_consistency=0.891,
            solution_coverage=0.723,
        ),
    )


@pytest.fixture
def sample_necessity() -> NecessityResults:
    """Necessity results where DISSATISFACTION is necessary."""
    return NecessityResults(
        outcome_name="GOV_RESPONSIVENESS",
        threshold=0.9,
        conditions=[
            NecessityConditionResult(
                condition_name="DISSATISFACTION",
                consistency=0.934,
                coverage=0.812,
                is_necessary=True,
            ),
            NecessityConditionResult(
                condition_name="POLICY_DEMAND",
                consistency=0.756,
                coverage=0.643,
                is_necessary=False,
            ),
            NecessityConditionResult(
                condition_name="CO_PRODUCTION",
                consistency=0.823,
                coverage=0.591,
                is_necessary=False,
            ),
            NecessityConditionResult(
                condition_name="TRUST",
                consistency=0.689,
                coverage=0.534,
                is_necessary=False,
            ),
        ],
    )


# ── interpret_solution_term ─────────────────────────────────────────────


class TestInterpretSolutionTerm:
    def test_single_positive_condition(self, interpreter: NLInterpreter):
        term = SolutionTerm(term=["DISSATISFACTION"], label="DISSATISFACTION")
        result = interpreter.interpret_solution_term(term)
        assert "高" in result
        assert "不满程度" in result

    def test_single_negated_condition(self, interpreter: NLInterpreter):
        term = SolutionTerm(term=["~POLICY_DEMAND"], label="~POLICY_DEMAND")
        result = interpreter.interpret_solution_term(term)
        assert "低" in result
        assert "政策需求" in result
        assert "~" not in result

    def test_compound_term(self, interpreter: NLInterpreter):
        term = SolutionTerm(
            term=["DISSATISFACTION", "~POLICY_DEMAND"],
            label="DISSATISFACTION*~POLICY_DEMAND",
        )
        result = interpreter.interpret_solution_term(term)
        assert "高不满程度" in result
        assert "低政策需求" in result
        assert "AND" in result
        assert "~" not in result

    def test_compound_term_three_conditions(self, interpreter: NLInterpreter):
        term = SolutionTerm(
            term=["CO_PRODUCTION", "TRUST", "~POLICY_DEMAND"],
            label="CO_PRODUCTION*TRUST*~POLICY_DEMAND",
        )
        result = interpreter.interpret_solution_term(term)
        assert "高合产参与" in result
        assert "高信任程度" in result
        assert "低政策需求" in result
        assert result.count("AND") == 2

    def test_fallback_to_label_when_term_empty(self, interpreter: NLInterpreter):
        term = SolutionTerm(term=[], label="A*~B")
        result = interpreter.interpret_solution_term(term)
        assert "AND" in result

    def test_empty_term_and_label(self, interpreter: NLInterpreter):
        term = SolutionTerm(term=[], label="")
        result = interpreter.interpret_solution_term(term)
        assert len(result) > 0  # Should return fallback string

    def test_uses_override_condition_set(self, sample_condition_set: ConditionSet):
        interp = NLInterpreter()  # no condition_set
        term = SolutionTerm(term=["DISSATISFACTION"], label="DISSATISFACTION")
        result = interp.interpret_solution_term(term, sample_condition_set)
        assert "不满程度" in result


# ── interpret_solutions ─────────────────────────────────────────────────


class TestInterpretSolutions:
    def test_two_path_solution(
        self, interpreter: NLInterpreter, sample_solutions: QCASolutions
    ):
        result = interpreter.interpret_solutions(sample_solutions)
        assert "两条路径" in result  # "两条路径"
        assert "路径一" in result  # "路径一"
        assert "路径二" in result  # "路径二"
        assert "政府回应" in result

    def test_includes_consistency_explanation(
        self, interpreter: NLInterpreter, sample_solutions: QCASolutions
    ):
        result = interpreter.interpret_solutions(sample_solutions)
        assert "一致性" in result  # "一致性"
        assert "0.891" in result  # consistency value

    def test_includes_coverage_explanation(
        self, interpreter: NLInterpreter, sample_solutions: QCASolutions
    ):
        result = interpreter.interpret_solutions(sample_solutions)
        assert "覆盖度" in result  # "覆盖度"
        assert "0.723" in result  # coverage value

    def test_includes_solution_type_note(
        self, interpreter: NLInterpreter, sample_solutions: QCASolutions
    ):
        result = interpreter.interpret_solutions(sample_solutions)
        assert "复杂解" in result  # "复杂解"

    def test_empty_solutions(self, interpreter: NLInterpreter):
        empty = QCASolutions()
        result = interpreter.interpret_solutions(empty)
        assert "未找到" in result  # "未找到"

    def test_single_path_solution(self, interpreter: NLInterpreter):
        t1 = SolutionTerm(
            term=["DISSATISFACTION"],
            label="DISSATISFACTION",
            consistency=0.92,
            raw_coverage=0.65,
        )
        sol = QCASolutions(
            complex=QCASolution(
                solution_type="complex",
                terms=[t1],
                formula="DISSATISFACTION",
                solution_consistency=0.92,
                solution_coverage=0.65,
            ),
        )
        result = interpreter.interpret_solutions(sol)
        assert "一条主要路径" in result  # "一条主要路径"
        assert "路径一" in result  # "路径一"

    def test_all_three_solution_types_summarized(
        self, interpreter: NLInterpreter, sample_solutions: QCASolutions
    ):
        result = interpreter.interpret_solutions(sample_solutions)
        # Should mention all three types
        assert "复杂解" in result
        assert "精简解" in result

    def test_term_metrics_included_when_present(self, interpreter: NLInterpreter):
        term = SolutionTerm(
            term=["DISSATISFACTION"],
            label="DISSATISFACTION",
            consistency=0.892,
            raw_coverage=0.456,
        )
        sol = QCASolutions(
            complex=QCASolution(
                solution_type="complex",
                terms=[term],
                formula="DISSATISFACTION",
                solution_consistency=0.892,
                solution_coverage=0.456,
            ),
        )
        result = interpreter.interpret_solutions(sol)
        assert "0.892" in result

    def test_term_metrics_omitted_when_zero(self, interpreter: NLInterpreter):
        term = SolutionTerm(
            term=["DISSATISFACTION"],
            label="DISSATISFACTION",
            consistency=0.0,
            raw_coverage=0.0,
        )
        sol = QCASolutions(
            complex=QCASolution(
                solution_type="complex",
                terms=[term],
                formula="DISSATISFACTION",
                solution_consistency=0.80,
                solution_coverage=0.50,
            ),
        )
        result = interpreter.interpret_solutions(sol)
        # Term-level metrics should be omitted
        assert "一致性: 0.000" not in result


# ── interpret_consistency ───────────────────────────────────────────────


class TestInterpretConsistency:
    def test_very_high_consistency(self, interpreter: NLInterpreter):
        sol = QCASolution(
            solution_type="complex",
            terms=[],
            formula="",
            solution_consistency=0.97,
        )
        result = interpreter.interpret_consistency(sol)
        assert "非常高" in result  # "非常高"
        assert "充分条件" in result  # "充分条件"

    def test_high_consistency(self, interpreter: NLInterpreter):
        sol = QCASolution(solution_type="complex", solution_consistency=0.92)
        result = interpreter.interpret_consistency(sol)
        assert "很高" in result  # "很高"

    def test_moderate_consistency(self, interpreter: NLInterpreter):
        sol = QCASolution(solution_type="complex", solution_consistency=0.85)
        result = interpreter.interpret_consistency(sol)
        assert "较高" in result  # "较高"

    def test_acceptable_consistency(self, interpreter: NLInterpreter):
        sol = QCASolution(solution_type="complex", solution_consistency=0.78)
        result = interpreter.interpret_consistency(sol)
        assert "可接受" in result  # "可接受"

    def test_low_consistency(self, interpreter: NLInterpreter):
        sol = QCASolution(solution_type="complex", solution_consistency=0.65)
        result = interpreter.interpret_consistency(sol)
        assert "偏低" in result  # "偏低"


# ── interpret_coverage ──────────────────────────────────────────────────


class TestInterpretCoverage:
    def test_high_coverage(self, interpreter: NLInterpreter):
        sol = QCASolution(solution_type="complex", solution_coverage=0.85)
        result = interpreter.interpret_coverage(sol)
        assert "很高" in result  # "很高"
        assert "绝大部分" in result  # "绝大部分"

    def test_moderate_high_coverage(self, interpreter: NLInterpreter):
        sol = QCASolution(solution_type="complex", solution_coverage=0.70)
        result = interpreter.interpret_coverage(sol)
        assert "较高" in result  # "较高"
        assert "超过一半" in result  # "超过一半"

    def test_medium_coverage(self, interpreter: NLInterpreter):
        sol = QCASolution(solution_type="complex", solution_coverage=0.50)
        result = interpreter.interpret_coverage(sol)
        assert "中等" in result  # "中等"

    def test_low_coverage(self, interpreter: NLInterpreter):
        sol = QCASolution(solution_type="complex", solution_coverage=0.30)
        result = interpreter.interpret_coverage(sol)
        assert "较低" in result  # "较低"
        assert "仅约" in result  # "仅约"


# ── interpret_necessity ─────────────────────────────────────────────────


class TestInterpretNecessity:
    def test_necessary_conditions_listed(
        self, interpreter: NLInterpreter, sample_necessity: NecessityResults
    ):
        result = interpreter.interpret_necessity(sample_necessity)
        assert "必要条件" in result  # "必要条件"
        assert "DISSATISFACTION" in result or "不满程度" in result
        assert "0.934" in result

    def test_non_necessary_conditions_listed(
        self, interpreter: NLInterpreter, sample_necessity: NecessityResults
    ):
        result = interpreter.interpret_necessity(sample_necessity)
        assert "未达到" in result  # "未达到"

    def test_threshold_mentioned(
        self, interpreter: NLInterpreter, sample_necessity: NecessityResults
    ):
        result = interpreter.interpret_necessity(sample_necessity)
        assert "0.9" in result  # threshold value

    def test_no_necessary_conditions(self, interpreter: NLInterpreter):
        necc = NecessityResults(
            outcome_name="GOV_RESPONSIVENESS",
            threshold=0.9,
            conditions=[
                NecessityConditionResult(
                    condition_name="DISSATISFACTION",
                    consistency=0.75,
                    coverage=0.60,
                    is_necessary=False,
                ),
            ],
        )
        result = interpreter.interpret_necessity(necc)
        assert "没有" in result and "条件" in result  # "没有条件"

    def test_empty_conditions(self, interpreter: NLInterpreter):
        necc = NecessityResults(
            outcome_name="OUTCOME",
            threshold=0.9,
            conditions=[],
        )
        result = interpreter.interpret_necessity(necc)
        assert len(result) > 0  # Should produce output, not crash

    def test_displays_resolved_names(
        self, interpreter: NLInterpreter, sample_necessity: NecessityResults
    ):
        result = interpreter.interpret_necessity(sample_necessity)
        assert "不满程度" in result


# ── interpret_full_result ───────────────────────────────────────────────


class TestInterpretFullResult:
    def test_combines_solutions_and_necessity(
        self,
        interpreter: NLInterpreter,
        sample_solutions: QCASolutions,
        sample_necessity: NecessityResults,
    ):
        result = interpreter.interpret_full_result(sample_solutions, sample_necessity)
        assert "QCA 分析结果自然语言解读" in result  # title
        assert "必要条件分析" in result  # necessity section
        assert "政府回应" in result

    def test_solutions_only(
        self, interpreter: NLInterpreter, sample_solutions: QCASolutions
    ):
        result = interpreter.interpret_full_result(sample_solutions)
        assert "QCA 分析结果自然语言解读" in result
        assert "必要条件分析" not in result  # No necessity section


# ── Display name resolution ─────────────────────────────────────────────


class TestDisplayNameResolution:
    def test_falls_back_to_name_when_no_condition_set(self):
        interp = NLInterpreter()  # No condition set
        term = SolutionTerm(term=["UNKNOWN_CONDITION"], label="UNKNOWN_CONDITION")
        result = interp.interpret_solution_term(term)
        assert "高" in result
        assert "UNKNOWN" in result

    def test_falls_back_to_domain_label_for_known_domains(self):
        """When condition_set is absent, domain-based labels are used if available."""
        cond = ConditionDefinition(
            name="SATISFACTION",
            display_name="",
            domain=TextDomain.DISSATISFACTION,
        )
        cs = ConditionSet(
            name="test",
            conditions=[cond],
        )
        interp = NLInterpreter(cs)
        term = SolutionTerm(term=["SATISFACTION"], label="SATISFACTION")
        result = interp.interpret_solution_term(term)
        # Should use domain-based label since display_name is empty
        assert "不满程度" in result
