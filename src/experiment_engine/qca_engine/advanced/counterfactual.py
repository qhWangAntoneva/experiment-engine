"""Counterfactual analysis for QCA.

Classifies truth table rows into easy/hard counterfactuals (logical remainders)
and produces the three classical QCA solution types:
- Complex solution: only empirically observed configurations
- Parsimonious solution: includes easy counterfactuals
- Intermediate solution: includes theoretically plausible counterfactuals
"""

from __future__ import annotations

from experiment_engine.models import (
    CounterfactualClassification,
    CounterfactualReport,
    TruthTable,
)
from experiment_engine.qca_engine.minimization import QuineMcCluskey


class CounterfactualAnalyzer:
    """Analyze counterfactual configurations and produce all three solution types.

    Follows Ragin (2008): Logical remainders are truth table rows without
    empirical cases. Easy counterfactuals are those consistent with theoretical
    expectations; hard counterfactuals contradict theory.
    """

    def __init__(self) -> None:
        self._qm = QuineMcCluskey()

    def analyze(
        self,
        truth_table: TruthTable,
        directional_expectations: dict[str, str] | None = None,
    ) -> CounterfactualReport:
        """Classify all truth table configurations.

        Args:
            truth_table: The constructed truth table.
            directional_expectations: Dict mapping condition_name →
                expected direction ('present', 'absent', or None for no expectation).

        Returns:
            CounterfactualReport with per-row classification.
        """
        classifications: list[CounterfactualClassification] = []
        n_easy = 0
        n_hard = 0
        n_remainder = 0

        expectations = directional_expectations or {}

        for row in truth_table.rows:
            freq = row.frequency
            is_observed = freq >= 1.0
            cf_type: str | None = None

            # Build theoretical expectation string from directional expectations
            theo_parts: list[str] = []
            for name, _val in zip(
                truth_table.condition_names, row.config, strict=False
            ):
                exp = expectations.get(name)
                if exp:
                    marker = "+" if exp == "present" else "-"
                    theo_parts.append(f"{marker}{name}")
            theo_exp: str | None = ", ".join(theo_parts) if theo_parts else None

            if not is_observed:
                n_remainder += 1
                # Assess counterfactual type based on directional expectations
                cf_type = self._classify_counterfactual(
                    row.config, truth_table.condition_names, expectations
                )
                if cf_type == "easy":
                    n_easy += 1
                else:
                    n_hard += 1

            classifications.append(
                CounterfactualClassification(
                    config=row.config,
                    is_observed=is_observed,
                    counterfactual_type=cf_type,
                    theoretical_expectation=theo_exp,
                )
            )

        return CounterfactualReport(
            classifications=classifications,
            n_easy_counterfactuals=n_easy,
            n_hard_counterfactuals=n_hard,
            n_logical_remainders=n_remainder,
        )

    def produce_complex_solution(self, truth_table: TruthTable) -> list[list[str]]:
        """Complex solution: minimize only empirically observed positive rows."""
        observed_positive = [
            r
            for r in truth_table.rows
            if r.included and r.outcome_value == 1 and r.frequency >= 1.0
        ]
        if not observed_positive:
            return []
        minterms = [r.config for r in observed_positive]
        return self._qm.minimize(minterms, truth_table.condition_names)

    def produce_parsimonious_solution(
        self,
        truth_table: TruthTable,
        directional_expectations: dict[str, str] | None = None,
    ) -> list[list[str]]:
        """Parsimonious solution: include ALL logical remainders as don't-care.

        In standard QCA (Ragin 2008), the parsimonious solution treats ALL
        logical remainders as don't-care minterms, without distinguishing
        between easy and hard counterfactuals. This differs from the
        intermediate solution which only includes easy counterfactuals.
        """
        # Regular minterms: observed positive rows that must be covered
        minterms: list[list[int]] = [
            r.config
            for r in truth_table.rows
            if r.included and r.outcome_value == 1 and r.frequency >= 1.0
        ]

        # ALL logical remainders as don't-care (no easy/hard filtering)
        dont_care: list[list[int]] = [
            r.config for r in truth_table.rows if r.frequency < 1.0
        ]

        if not minterms:
            return []
        return self._qm.minimize(
            minterms,
            truth_table.condition_names,
            dont_care_minterms=dont_care,
        )

    def produce_intermediate_solution(
        self,
        truth_table: TruthTable,
        directional_expectations: dict[str, str],
    ) -> list[list[str]]:
        """Intermediate solution: include only easy counterfactuals as don't-care.

        Easy counterfactuals (logical remainders consistent with theoretical
        directional expectations) are passed as don't-care minterms. Hard
        counterfactuals are excluded. This is the most commonly reported
        solution type in QCA research.
        """
        # Regular minterms: observed positive rows that must be covered
        minterms: list[list[int]] = [
            r.config
            for r in truth_table.rows
            if r.included and r.outcome_value == 1 and r.frequency >= 1.0
        ]

        # Easy counterfactuals as don't-care (filtered by directional expectations)
        dont_care: list[list[int]] = []
        for row in truth_table.rows:
            if row.frequency < 1.0:
                cf_type = self._classify_counterfactual(
                    row.config, truth_table.condition_names, directional_expectations
                )
                if cf_type == "easy":
                    dont_care.append(row.config)

        if not minterms:
            return []
        return self._qm.minimize(
            minterms,
            truth_table.condition_names,
            dont_care_minterms=dont_care,
        )

    @staticmethod
    def _classify_counterfactual(
        config: list[int],
        condition_names: list[str],
        expectations: dict[str, str],
    ) -> str:
        """Classify a logical remainder as easy or hard.

        An 'easy' counterfactual is consistent with theoretical expectations
        (condition present when expected, absent when expected absent).
        A 'hard' counterfactual contradicts expectations.
        """
        for _j, (name, val) in enumerate(zip(condition_names, config, strict=False)):
            if name in expectations:
                expected = expectations[name]
                if expected == "present" and val == 0:
                    return "hard"
                if expected == "absent" and val == 1:
                    return "hard"
        return "easy"
