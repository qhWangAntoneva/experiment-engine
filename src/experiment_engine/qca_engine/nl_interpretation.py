"""Natural language interpretation of QCA analysis results in Chinese.

Generates human-readable Chinese explanations for Boolean solution terms,
solution formulas, consistency/coverage metrics, and necessity analysis results.
"""

from __future__ import annotations

from typing import ClassVar

from experiment_engine.models import (
    ConditionDefinition,
    ConditionSet,
    NecessityResults,
    QCASolution,
    QCASolutions,
    SolutionTerm,
)

# Unicode constants for CJK quotation marks to avoid parser confusion
_LQ = "“"  # Chinese left double quote "
_RQ = "”"  # Chinese right double quote "


class NLInterpreter:
    """Generate Chinese natural-language interpretations of QCA results.

    Converts boolean formulas like ``DISSATISFACTION*~POLICY_DEMAND`` into
    readable Chinese like ``高不满程度 AND 低政策需求``, and explains
    consistency/coverage/necessity metrics in plain language.

    Args:
        condition_set: The condition definitions used in this QCA analysis,
            providing name-to-display_name mapping and outcome label.
    """

    # -- Domain -> Default Chinese labels ---------------------------------

    DOMAIN_LABELS: ClassVar[dict[str, str]] = {
        "dissatisfaction": "不满程度",
        "policy_demand": "政策需求",
        "co_production": "合产参与",
        "trust": "信任程度",
        "gov_responsiveness": "政府响应",
    }

    OUTCOME_LABELS: ClassVar[dict[str, str]] = {
        "dissatisfaction": "公民投诉",
        "policy_demand": "政策诉求",
        "co_production": "合产行为",
        "trust": "制度信任",
        "gov_responsiveness": "政府回应",
    }

    # -- Chinese numerals for path counting --------------------------------

    _CN_NUMERALS: ClassVar[list[str]] = [
        "零",
        "一",
        "两",
        "三",
        "四",
        "五",
        "六",
        "七",
        "八",
        "九",
        "十",
    ]

    def __init__(self, condition_set: ConditionSet | None = None) -> None:
        self._condition_set = condition_set
        # Build lookups from condition_set
        self._name_to_display: dict[str, str] = {}
        self._outcome_display: str = ""
        if condition_set is not None:
            for cond in condition_set.conditions:
                self._name_to_display[cond.name] = (
                    cond.display_name or self._guess_label(cond)
                )
            if condition_set.outcome is not None:
                self._outcome_display = (
                    condition_set.outcome.display_name
                    or self._guess_label(condition_set.outcome)
                )

    # -- Public API --------------------------------------------------------

    def interpret_solution_term(
        self, term: SolutionTerm, condition_set: ConditionSet | None = None
    ) -> str:
        """Convert a single solution term into Chinese.

        ``['DISSATISFACTION', '~POLICY_DEMAND']``
        becomes ``"高不满程度 AND 低政策需求"``.

        Args:
            term: A QCA solution term with ``term`` (list of condition names)
                and/or ``label`` (formula string like ``A*~B``).
            condition_set: Optional override condition set for display names.
        """
        # Use term.term list (condition names with optional ~ prefix)
        if term.term:
            parts = [self._interpret_condition(c, condition_set) for c in term.term]
            return " AND ".join(parts)

        # Fallback: parse the label string
        if term.label:
            cond_names = [c.strip() for c in term.label.split("*")]
            parts = [self._interpret_condition(c, condition_set) for c in cond_names]
            return " AND ".join(parts)

        return "未知条件组合"

    def interpret_solutions(
        self,
        solutions: QCASolutions,
        condition_set: ConditionSet | None = None,
    ) -> str:
        """Generate a Chinese paragraph explaining QCA solutions.

        Includes:
        - How many paths lead to the outcome
        - Each path explained in Chinese
        - Overall consistency and coverage with plain-language interpretation

        Args:
            solutions: The three QCA solution types.
            condition_set: Optional override for display names.
        """
        cs = condition_set or self._condition_set

        # Prefer solutions in order: intermediate > complex > parsimonious
        primary = solutions.intermediate or solutions.complex or solutions.parsimonious
        if primary is None or not primary.terms:
            return "未找到有效的解。"

        outcome = self._outcome_display or "结果"
        if cs is not None and cs.outcome is not None:
            outcome = cs.outcome.display_name or self._guess_label(cs.outcome)

        lines: list[str] = []
        n_terms = len(primary.terms)

        # -- Intro: how many paths --
        if n_terms == 1:
            lines.append(f"导致{_LQ}{outcome}{_RQ}有一条主要路径：")
        else:
            num_cn = self._num_to_cn(n_terms)
            lines.append(f"导致{_LQ}{outcome}{_RQ}有{num_cn}条路径：")

        # -- Each path --
        path_labels = [
            "一",
            "二",
            "三",
            "四",
            "五",
            "六",
        ]
        for i, term in enumerate(primary.terms):
            idx = path_labels[i] if i < len(path_labels) else str(i + 1)
            cn = self.interpret_solution_term(term, cs)
            term_detail = self._interpret_term_metrics(term)
            lines.append(f"路径{idx}：{cn}{term_detail}")

        # -- Solution type note --
        solution_types_cn = {
            "complex": "复杂解",
            "parsimonious": "精简解",
            "intermediate": "中间解",
        }
        sol_type_cn = solution_types_cn.get(
            primary.solution_type, primary.solution_type
        )
        lines.append(f"\n（以上为{sol_type_cn}）")

        # -- Consistency & Coverage explanations --
        lines.append("")
        lines.append(self._interpret_consistency_text(primary))
        lines.append(self._interpret_coverage_text(primary))

        # -- Alternative solution types summary --
        lines.append("")
        lines.append(
            self._interpret_all_solutions_summary(solutions, primary.solution_type)
        )

        return "\n".join(lines)

    def interpret_consistency(self, solution: QCASolution) -> str:
        """Explain solution consistency in plain Chinese.

        Returns a string like:
        ``"解的一致性为0.892（较高），表明这些条件组合是结果的充分条件。"``
        """
        return self._interpret_consistency_text(solution)

    def interpret_coverage(self, solution: QCASolution) -> str:
        """Explain solution coverage in plain Chinese.

        Returns a string like:
        ``"解的覆盖度为0.723（中等），表明这些路径解释了约72%的结果案例。"``
        """
        return self._interpret_coverage_text(solution)

    def interpret_necessity(
        self,
        necessity: NecessityResults,
        condition_set: ConditionSet | None = None,
    ) -> str:
        """Generate Chinese explanation of necessity findings.

        Args:
            necessity: Necessity analysis results.
            condition_set: Optional override for display names.
        """
        cs = condition_set or self._condition_set

        outcome = necessity.outcome_name or self._outcome_display or "结果"

        if not necessity.conditions:
            return f"对于{_LQ}{outcome}{_RQ}，未找到必要条件分析结果。"

        threshold = necessity.threshold
        necessary_conds = [c for c in necessity.conditions if c.is_necessary]
        not_necessary = [c for c in necessity.conditions if not c.is_necessary]

        lines: list[str] = []
        lines.append(f"必要条件分析（阈值 = {threshold}）：")

        if necessary_conds:
            n = self._num_to_cn(len(necessary_conds))
            lines.append(f"其有{n}个条件是{_LQ}{outcome}{_RQ}的必要条件：")
            for c in necessary_conds:
                disp = self._resolve_display(c.condition_name, cs)
                lines.append(
                    f"  • {disp}：一致性{c.consistency:.3f}，覆盖度{c.coverage:.3f}"
                )
            lines.append(
                f"这意味着当{_LQ}{outcome}{_RQ}"
                f"出现时，这些条件几乎总是存在"
                f"（一致性≥{threshold}）。"
            )
        else:
            lines.append(f"没有条件达到必要性阈值（一致性 ≥ {threshold}）。")
            lines.append(f"这表明没有单一条件是{_LQ}{outcome}{_RQ}的必要前提。")

        if not_necessary:
            n = self._num_to_cn(len(not_necessary))
            lines.append(f"\n其他{n}个条件未达到必要性阈值：")
            for c in not_necessary:
                disp = self._resolve_display(c.condition_name, cs)
                lines.append(f"  • {disp}：一致性{c.consistency:.3f}")

        return "\n".join(lines)

    def interpret_full_result(
        self,
        solutions: QCASolutions,
        necessity: NecessityResults | None = None,
        condition_set: ConditionSet | None = None,
    ) -> str:
        """Generate a complete Chinese interpretation of a QCA result.

        Combines solution and necessity interpretations into a single
        readable Chinese document.

        Args:
            solutions: QCA solution types.
            necessity: Optional necessity analysis results.
            condition_set: Optional override condition set.
        """
        sections = [
            "━━━ QCA 分析结果自然语言解读 ━━━",
            "",
            self.interpret_solutions(solutions, condition_set),
        ]

        if necessity is not None:
            sections.append("")
            sections.append("━━━ 必要条件分析 ━━━")
            sections.append("")
            sections.append(self.interpret_necessity(necessity, condition_set))

        return "\n".join(sections)

    # -- Private helpers ---------------------------------------------------

    @classmethod
    def _num_to_cn(cls, n: int) -> str:
        """Convert a small integer to Chinese numerals."""
        if 0 <= n < len(cls._CN_NUMERALS):
            return cls._CN_NUMERALS[n]
        return str(n)

    def _interpret_condition(
        self,
        cond_name: str,
        condition_set: ConditionSet | None = None,
    ) -> str:
        """Convert a single condition name (with optional ``~`` prefix) to Chinese.

        ``'DISSATISFACTION'`` -> ``'高不满程度'``
        ``'~POLICY_DEMAND'`` -> ``'低政策需求'``
        """
        is_negated = cond_name.startswith("~")
        clean = cond_name[1:] if is_negated else cond_name
        display = self._resolve_display(clean, condition_set)
        if is_negated:
            return f"低{display}"
        return f"高{display}"

    def _resolve_display(
        self,
        name: str,
        condition_set: ConditionSet | None = None,
    ) -> str:
        """Resolve a condition name to its Chinese display name."""
        # 1. From condition_set if available
        cs = condition_set or self._condition_set
        if cs is not None:
            for cond in cs.conditions:
                if cond.name == name:
                    return cond.display_name or self._guess_label(cond)
            if cs.outcome is not None and cs.outcome.name == name:
                return cs.outcome.display_name or self._guess_label(cs.outcome)

        # 2. From internal lookup
        if name in self._name_to_display:
            return self._name_to_display[name]

        # 3. Natural language fallback: replace underscores
        return name.replace("_", " ")

    @staticmethod
    def _guess_label(cond: ConditionDefinition) -> str:
        """Guess a Chinese label from a condition's domain and name."""
        domain = (
            cond.domain.value if hasattr(cond.domain, "value") else str(cond.domain)
        )
        if domain in NLInterpreter.DOMAIN_LABELS:
            return NLInterpreter.DOMAIN_LABELS[domain]
        return cond.name.replace("_", " ")

    def _interpret_term_metrics(self, term: SolutionTerm) -> str:
        """Generate a metrics suffix for a term.

        E.g., ' (一致性: 0.892, 覆盖度: 0.345)'.
        """
        if term.consistency > 0 or term.raw_coverage > 0:
            parts = []
            if term.consistency > 0:
                parts.append(f"一致性: {term.consistency:.3f}")
            if term.raw_coverage > 0:
                parts.append(f"覆盖度: {term.raw_coverage:.3f}")
            if parts:
                return " (" + ", ".join(parts) + ")"
        return ""

    @staticmethod
    def _interpret_consistency_text(solution: QCASolution) -> str:
        """Produce Chinese consistency explanation."""
        cons = solution.solution_consistency
        if cons >= 0.95:
            quality = "非常高"
        elif cons >= 0.90:
            quality = "很高"
        elif cons >= 0.80:
            quality = "较高"
        elif cons >= 0.75:
            quality = "可接受"
        else:
            quality = "偏低"

        return (
            f"解的一致性为{cons:.3f}（{quality}），"
            f"表明这些条件组合是结果的充分条件——"
            f"即当这些条件组合出现时，结果几乎总是出现。"
        )

    @staticmethod
    def _interpret_coverage_text(solution: QCASolution) -> str:
        """Produce Chinese coverage explanation."""
        cov = solution.solution_coverage
        pct = cov * 100
        if cov >= 0.80:
            quality = "很高"
            detail = f"绝大部分（约{pct:.0f}%）"
        elif cov >= 0.60:
            quality = "较高"
            detail = f"超过一半（约{pct:.0f}%）"
        elif cov >= 0.40:
            quality = "中等"
            detail = f"约{pct:.0f}%"
        else:
            quality = "较低"
            detail = f"仅约{pct:.0f}%"

        return (
            f"解的覆盖度为{cov:.3f}（{quality}），"
            f"表明这些路径解释了{detail}的结果案例。"
        )

    def _interpret_all_solutions_summary(
        self,
        solutions: QCASolutions,
        primary_type: str | None = None,
    ) -> str:
        """Summarize availability of all three solution types."""
        lines: list[str] = []
        solution_types_cn = {
            "complex": "复杂解",
            "parsimonious": "精简解",
            "intermediate": "中间解",
        }
        solution_types_desc = {
            "complex": "仅基于实际观察到的配置推导",
            "parsimonious": ("包含全部逻辑余项作为" + _LQ + "不确定" + _RQ + "行"),
            "intermediate": "仅包含理论上可能的反事实",
        }

        for sol_type in ("complex", "parsimonious", "intermediate"):
            sol = getattr(solutions, sol_type, None)
            cn_name = solution_types_cn.get(sol_type, sol_type)
            desc = solution_types_desc.get(sol_type, "")

            if sol and sol.terms:
                if sol_type == primary_type:
                    lines.append(f"• {cn_name}（已展示于上方）：{desc}")
                else:
                    n = sol.terms
                    n_str = self._num_to_cn(len(n))
                    lines.append(f"• {cn_name}：{n_str}条路径，{desc}")
                    lines.append(f"  公式：{sol.formula}")
            else:
                lines.append(f"• {cn_name}：未生成（不足够的一致配置）")
                lines.append(f"  {desc}")

        return "\n".join(lines)
