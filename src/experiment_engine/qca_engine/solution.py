"""Solution formula formatting and term label generation."""

from __future__ import annotations

from experiment_engine.models import QCASolution, QCASolutions, SolutionTerm


class SolutionFormatter:
    """Convert minimized solution terms to human-readable formula strings."""

    def __init__(self, style: str = "boolean") -> None:
        """Args:
        style: Output style — 'boolean' (*), 'logical' (∧¬), 'latex' ($...$).
        """
        self.style = style

    def format_solution_terms(
        self,
        solution_terms: list[list[str]],
        condition_names: list[str],
        solution_type: str = "complex",
    ) -> QCASolution:
        """Format a list of solution terms into a QCASolution.

        Args:
            solution_terms: Each term is a list of condition names.
            condition_names: All condition names.
            solution_type: 'complex', 'parsimonious', or 'intermediate'.

        Returns:
            A QCASolution with formatted labels and formula.
        """
        terms: list[SolutionTerm] = []
        for term in solution_terms:
            label = self.format_term(term)
            terms.append(
                SolutionTerm(
                    term=term,
                    label=label,
                    consistency=0.0,  # filled by SufficiencyAnalyzer
                    raw_coverage=0.0,
                    unique_coverage=0.0,
                )
            )

        formula = self.format_formula(terms)

        return QCASolution(
            solution_type=solution_type,
            terms=terms,
            formula=formula,
        )

    def format_all_solutions(
        self,
        complex_terms: list[list[str]] | None,
        parsimonious_terms: list[list[str]] | None,
        intermediate_terms: list[list[str]] | None,
        condition_names: list[str],
    ) -> QCASolutions:
        """Build a QCASolutions object from all three solution types.

        Args:
            complex_terms: Solution terms from empirically observed rows only.
            parsimonious_terms: Solution terms including easy counterfactuals.
            intermediate_terms: Solution terms including theoretically expected counterfactuals.
            condition_names: Names of all causal conditions.
        """
        solutions = QCASolutions()

        if complex_terms is not None:
            solutions.complex = self.format_solution_terms(
                complex_terms, condition_names, "complex"
            )
        if parsimonious_terms is not None:
            solutions.parsimonious = self.format_solution_terms(
                parsimonious_terms, condition_names, "parsimonious"
            )
        if intermediate_terms is not None:
            solutions.intermediate = self.format_solution_terms(
                intermediate_terms, condition_names, "intermediate"
            )

        return solutions

    def format_term(self, term: list[str]) -> str:
        """Format a single term (list of condition names) into a string.

        Examples:
            ['A', '~B', 'C'] → 'A*~B*C' (boolean style)
            ['A', '~B', 'C'] → 'A∧¬B∧C' (logical style)
        """
        if self.style == "logical":
            parts = [f"¬{c[1:]}" if c.startswith("~") else c for c in term]
            return "∧".join(parts)
        if self.style == "latex":
            parts = [f"\\neg {c[1:]}" if c.startswith("~") else c for c in term]
            return " \\land ".join(parts)
        # Boolean / default style
        return "*".join(term)

    def format_formula(self, terms: list[SolutionTerm]) -> str:
        """Format a full solution formula from multiple terms.

        Uses the terms' labels joined by '+'.
        """
        if not terms:
            return "No solution"
        return " + ".join(t.label for t in terms)

    def to_latex(self, solutions: QCASolutions) -> dict[str, str]:
        """Return LaTeX-formatted solution formulas.

        Returns:
            Dict mapping solution_type → LaTeX formula string.
        """
        result: dict[str, str] = {}
        for sol_type in ("complex", "parsimonious", "intermediate"):
            sol = getattr(solutions, sol_type, None)
            if sol:
                parts = []
                for term in sol.terms:
                    latex_parts = [
                        f"\\neg {c[1:]}" if c.startswith("~") else c for c in term.term
                    ]
                    parts.append(" \\land ".join(latex_parts))
                result[sol_type] = " \\lor ".join(parts)
        return result
