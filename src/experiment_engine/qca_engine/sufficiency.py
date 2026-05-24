"""Sufficiency analysis for QCA solutions.

Evaluates the consistency and coverage of solution terms (conjunctions of
conditions) with respect to the outcome. Also computes the full solutions'
(combinations of terms) overall metrics.
"""

from __future__ import annotations

import numpy as np

from experiment_engine.models import (
    FuzzySetData,
    QCASolution,
    QCASolutions,
    SolutionTerm,
    SufficiencyResults,
)
from experiment_engine.qca_engine.consistency import ConsistencyCalculator


class SufficiencyAnalyzer:
    """Analyze sufficiency of QCA solution terms for the outcome.

    A solution term X is sufficient for outcome Y when X is a consistent
    fuzzy subset of Y: for all cases, membership in X <= membership in Y.
    Sufficiency consistency = Sum(min(X, Y)) / Sum(X).
    """

    def analyze(
        self,
        fuzzy_data: FuzzySetData,
        solutions: QCASolutions,
    ) -> SufficiencyResults:
        """Compute consistency and coverage for all solution terms.

        Args:
            fuzzy_data: Fuzzy-set membership data.
            solutions: Minimized QCA solutions (complex/parsimonious/intermediate).

        Returns:
            SufficiencyResults with per-term and overall metrics.
        """
        outcome = fuzzy_data.outcome_vector
        condition_matrix = fuzzy_data.condition_matrix

        result = SufficiencyResults(
            outcome_name=fuzzy_data.outcome_name,
            solutions=QCASolutions(),
        )

        for sol_type in ("complex", "parsimonious", "intermediate"):
            sol = getattr(solutions, sol_type, None)
            if sol is None or not sol.terms:
                continue

            # Compute term membership arrays
            term_memberships: list[np.ndarray] = []
            updated_terms: list[SolutionTerm] = []

            for term_obj in sol.terms:
                memb = self._compute_term_membership(
                    term_obj.term, condition_matrix, fuzzy_data.condition_names
                )
                term_memberships.append(memb)

                consistency = ConsistencyCalculator.subset_consistency(memb, outcome)
                raw_cov = ConsistencyCalculator.raw_coverage(memb, outcome)

                updated_terms.append(
                    SolutionTerm(
                        term=term_obj.term,
                        label=term_obj.label,
                        consistency=float(consistency),
                        raw_coverage=float(raw_cov),
                        unique_coverage=0.0,  # filled below
                    )
                )

            # Compute unique coverage for each term
            for idx in range(len(updated_terms)):
                other = [
                    term_memberships[j] for j in range(len(updated_terms)) if j != idx
                ]
                uc = ConsistencyCalculator.unique_coverage(
                    term_memberships[idx], other, outcome
                )
                updated_terms[idx].unique_coverage = float(uc)

            # Overall solution metrics
            sol_cons = ConsistencyCalculator.solution_consistency(
                term_memberships, outcome
            )
            sol_cov = ConsistencyCalculator.solution_coverage(term_memberships, outcome)

            formula = " + ".join(t.label for t in updated_terms)

            updated_sol = QCASolution(
                solution_type=sol_type,
                terms=updated_terms,
                formula=formula,
                solution_consistency=float(sol_cons),
                solution_coverage=float(sol_cov),
            )
            setattr(result.solutions, sol_type, updated_sol)

        return result

    @staticmethod
    def _compute_term_membership(
        term: list[str],
        condition_matrix: np.ndarray,
        condition_names: list[str],
    ) -> np.ndarray:
        """Compute fuzzy membership of each case in a solution term.

        A term is a conjunction of conditions (e.g., ['A', '~B', 'C']).
        Negated conditions (~) use 1 - membership.
        """
        n_cases = condition_matrix.shape[0]
        result = np.ones(n_cases, dtype=np.float64)

        name_to_idx = {name: i for i, name in enumerate(condition_names)}

        for cond in term:
            if cond.startswith("~"):
                name = cond[1:]
                if name in name_to_idx:
                    result = np.minimum(
                        result, 1.0 - condition_matrix[:, name_to_idx[name]]
                    )
            else:
                if cond in name_to_idx:
                    result = np.minimum(result, condition_matrix[:, name_to_idx[cond]])
                else:
                    # Condition not found, treat as 1.0 (don't-care)
                    pass

        return result
