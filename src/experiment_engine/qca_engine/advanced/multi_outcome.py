"""Multi-outcome comparison for QCA.

Compares QCA results across multiple outcomes to identify shared conditions
and divergent pathways.
"""

from __future__ import annotations

from experiment_engine.models import MultiOutcomeReport, QCAAnalysisResult


class MultiOutcomeComparison:
    """Compare QCA analyses across multiple outcomes."""

    def compare(self, analyses: dict[str, QCAAnalysisResult]) -> MultiOutcomeReport:
        """Compare QCA results across outcomes.

        Args:
            analyses: Dict mapping outcome_name → QCAAnalysisResult.

        Returns:
            MultiOutcomeReport with cross-outcome comparison.
        """
        outcomes = list(analyses.keys())
        if len(outcomes) < 2:
            return MultiOutcomeReport(outcomes=outcomes)

        # Shared conditions: conditions appearing in all solutions
        all_conditions: list[set[str]] = []
        for name, result in analyses.items():
            conds = self._extract_conditions_from_result(result)
            all_conditions.append(conds)

        shared = all_conditions[0].intersection(*all_conditions[1:])

        # Unique conditions per outcome
        unique: dict[str, list[str]] = {}
        for i, name in enumerate(outcomes):
            others = set()
            for j, other_conds in enumerate(all_conditions):
                if i != j:
                    others |= other_conds
            unique[name] = sorted(all_conditions[i] - others)

        # Pairwise solution similarity
        n = len(outcomes)
        similarity = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                sim = self._jaccard(all_conditions[i], all_conditions[j])
                similarity[i][j] = sim
                similarity[j][i] = sim

        return MultiOutcomeReport(
            outcomes=outcomes,
            shared_conditions=sorted(shared),
            unique_conditions=unique,
            pairwise_similarity=similarity,
        )

    @staticmethod
    def _extract_conditions_from_result(result: QCAAnalysisResult) -> set[str]:
        """Extract all condition names appearing in any solution."""
        conds: set[str] = set()
        for sol_type in ("complex", "parsimonious", "intermediate"):
            sol = getattr(result.solutions, sol_type, None)
            if sol:
                for term in sol.terms:
                    for c in term.term:
                        name = c.lstrip("~")
                        conds.add(name)
        return conds

    @staticmethod
    def _jaccard(set_a: set[str], set_b: set[str]) -> float:
        if not set_a and not set_b:
            return 1.0
        return len(set_a & set_b) / len(set_a | set_b)
