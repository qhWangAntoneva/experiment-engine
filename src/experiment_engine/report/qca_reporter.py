"""QCA-specific LaTeX report generation.

Extends the base LaTeX reporter with QCA-specific sections:
truth table, solution formulas, necessity/sufficiency metrics, and robustness.
"""

from __future__ import annotations

from experiment_engine.models import (
    QCAAnalysisResult,
    RobustnessReport,
)


class QCALaTeXReporter:
    """Generate LaTeX reports from QCA analysis results.

    Usage:
        reporter = QCALaTeXReporter()
        reporter.generate(result, output_path="report.tex")

    The generated LaTeX document includes:
    - Title page with analysis metadata
    - Truth table (tabular)
    - Solution formulas (all three types)
    - Necessity analysis table
    - Sufficiency metrics table
    - Robustness test results
    - Counterfactual analysis
    """

    # ── LaTeX escaping helpers ───────────────────────────────────────────────

    @staticmethod
    def _escape_latex(text: str) -> str:
        """Escape special LaTeX characters in user-provided text.

        Characters %, $, #, &, {, }, _ are backslash-escaped.
        ~ is replaced with \\textasciitilde{} (literal tilde in text mode).
        * is left as-is (safe in LaTeX text mode).
        """
        escape_map = {
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "&": r"\&",
            "{": r"\{",
            "}": r"\}",
            "_": r"\_",
            "~": r"\textasciitilde{}",
        }
        result = text
        for char, replacement in escape_map.items():
            result = result.replace(char, replacement)
        return result

    @staticmethod
    def _escape_latex_formula(formula: str) -> str:
        """Convert QCA formula notation to LaTeX math operators.

        ~ → \\neg (negation), * → \\land (conjunction), + → \\lor (disjunction).
        """
        return (
            formula.replace("~", r"\neg ")
            .replace("*", r" \land ")
            .replace("+", r" \lor ")
        )

    def generate(
        self,
        result: QCAAnalysisResult,
        output_path: str = "qca_report.tex",
        robustness: RobustnessReport | None = None,
        counterfactual_report=None,
        title: str = "QCA Analysis Report",
    ) -> str:
        """Generate a complete QCA LaTeX report.

        Args:
            result: The QCA analysis result.
            output_path: Path for the generated .tex file.
            robustness: Optional robustness test report.
            counterfactual_report: Optional counterfactual analysis report.
            title: Document title.

        Returns:
            Path to the generated .tex file.
        """
        sections: list[str] = [
            self._preamble(title),
            r"\begin{document}",
            self._title_page(title, result),
            r"\tableofcontents",
            r"\newpage",
        ]

        if result.truth_table:
            sections.append(self._truth_table_section(result))

        if result.solutions:
            sections.append(self._solutions_section(result))

        if result.necessity:
            sections.append(self._necessity_section(result))

        if result.sufficiency:
            sections.append(self._sufficiency_section(result))

        if robustness:
            sections.append(self._robustness_section(robustness))

        if counterfactual_report:
            sections.append(self._counterfactual_section(counterfactual_report))

        sections.append(r"\end{document}")

        content = "\n\n".join(sections)
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return output_path

    @staticmethod
    def _preamble(title: str) -> str:
        return (
            r"""\documentclass[12pt,a4paper]{article}
\usepackage[UTF8]{ctex}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{hyperref}
\geometry{margin=2.5cm}
\title{"""
            + title
            + "}"
        )

    @staticmethod
    def _title_page(_title: str, result: QCAAnalysisResult) -> str:
        n = result.fuzzy_data.n_cases if result.fuzzy_data else 0
        k = result.fuzzy_data.n_conditions if result.fuzzy_data else 0
        return (
            r"\maketitle"
            + "\n"
            + r"\begin{center}"
            + "\n"
            + r"\large"
            + "\n"
            + "Analysis Summary \\\\\n"
            + f"Cases: {n} \\\\\n"
            + f"Conditions: {k} \\\\\n"
            + f"Outcome: {QCALaTeXReporter._escape_latex(result.fuzzy_data.outcome_name) if result.fuzzy_data else 'N/A'}\n"
            + r"\end{center}"
            + "\n"
            + r"\newpage"
        )

    @staticmethod
    def _truth_table_section(result: QCAAnalysisResult) -> str:
        tt = result.truth_table
        if not tt:
            return r"\section{Truth Table}\nNo truth table available."

        rows_latex: list[str] = []
        for r in tt.included_rows:
            outcome_str = "1" if r.outcome_value else "0"
            rows_latex.append(
                f"    {QCALaTeXReporter._escape_latex(r.config_label)} & {r.frequency:.1f} & {r.raw_consistency:.3f} & {outcome_str} \\\\"
            )

        return rf"""
\section{{Truth Table}}
\begin{{longtable}}{{lrrr}}
\toprule
Configuration & Frequency & Consistency & Outcome \\
\midrule
{chr(10).join(rows_latex)}
\bottomrule
\end{{longtable}}

Thresholds: consistency $\geq$ {tt.consistency_threshold}, frequency $\geq$ {tt.frequency_threshold}.
"""

    @staticmethod
    def _solutions_section(result: QCAAnalysisResult) -> str:
        parts: list[str] = [r"\section{QCA Solutions}"]
        for sol_type in ("complex", "parsimonious", "intermediate"):
            sol = getattr(result.solutions, sol_type, None)
            if sol is None:
                continue

            # Detect vacuous solution: empty formula with no meaningful terms.
            # This happens when ALL truth table rows share the same outcome
            # (all 1 or all 0), so the minimizer produces an empty formula.
            is_vacuous = (
                not sol.formula
                or not sol.formula.strip()
                or (
                    len(sol.terms) <= 1
                    and sol.solution_consistency == 0.0
                    and sol.solution_coverage == 0.0
                )
            )

            parts.append(rf"\subsection{{{sol_type.title()} Solution}}")

            if is_vacuous:
                parts.append(r"Formula: $\displaystyle \top$")
                parts.append(
                    r"\emph{Note: This is a vacuous solution -- all truth table "
                    r"rows have the same outcome value, so the Boolean "
                    r"minimizer produced an empty formula ($\top$ = always-true).}"
                )
            else:
                parts.append(
                    rf"Formula: $\displaystyle {QCALaTeXReporter._escape_latex_formula(sol.formula)}$"
                )
                parts.append(rf"Solution Consistency: {sol.solution_consistency:.3f}")
                parts.append(rf"Solution Coverage: {sol.solution_coverage:.3f}")
            parts.append("")
        return "\n\n".join(parts)

    @staticmethod
    def _necessity_section(result: QCAAnalysisResult) -> str:
        if not result.necessity:
            return ""

        rows: list[str] = []
        for c in result.necessity.conditions:
            nec = r"\checkmark" if c.is_necessary else ""
            rows.append(
                f"    {QCALaTeXReporter._escape_latex(c.condition_name)} & {c.consistency:.3f} & {c.coverage:.3f} & {nec} \\\\"
            )

        return rf"""
\section{{Necessity Analysis}}
\begin{{tabular}}{{lrrl}}
\toprule
Condition & Consistency & Coverage & Necessary? \\
\midrule
{chr(10).join(rows)}
\bottomrule
\end{{tabular}}

Threshold: Consistency $\geq$ {result.necessity.threshold}
"""

    @staticmethod
    def _sufficiency_section(result: QCAAnalysisResult) -> str:
        if not result.sufficiency:
            return ""

        parts: list[str] = [r"\section{Sufficiency Analysis}"]
        for sol_type in ("complex", "parsimonious", "intermediate"):
            sol = getattr(result.sufficiency.solutions, sol_type, None)
            if sol and sol.terms:
                rows: list[str] = []
                for t in sol.terms:
                    rows.append(
                        f"    {QCALaTeXReporter._escape_latex(t.label)} & {t.consistency:.3f} & {t.raw_coverage:.3f} & {t.unique_coverage:.3f} \\\\"
                    )
                parts.append(rf"\subsection{{{sol_type.title()} Solution}}")
                parts.append(r"""\begin{tabular}{lrrr}
\toprule
Term & Consistency & Raw Coverage & Unique Coverage \\
\midrule""")
                parts.append("\n".join(rows))
                parts.append(r"""\bottomrule
\end{tabular}""")
        return "\n\n".join(parts)

    @staticmethod
    def _robustness_section(report: RobustnessReport) -> str:
        rows: list[str] = []
        for t in report.tests:
            status = "Pass" if t.passed else "Fail"
            if t.solution_stability:
                first = t.solution_stability[0]
                last = t.solution_stability[-1]
                stability_range = f"{first:.3f}-{last:.3f}"
            else:
                stability_range = "N/A"
            rows.append(
                f"    {QCALaTeXReporter._escape_latex(t.test_name)} & "
                f"{QCALaTeXReporter._escape_latex(t.parameter_varied)} & "
                f"{stability_range} & {status} \\\\"
            )

        return rf"""
\section{{Robustness Tests}}
\begin{{tabular}}{{llrl}}
\toprule
Test & Parameter & Stability Range & Result \\
\midrule
{chr(10).join(rows)}
\bottomrule
\end{{tabular}}

Overall Robustness: {report.overall_robustness:.2f}

{QCALaTeXReporter._escape_latex(report.summary)}
"""

    @staticmethod
    def _counterfactual_section(report) -> str:
        return rf"""
\section{{Counterfactual Analysis}}
Easy counterfactuals: {report.n_easy_counterfactuals}

Hard counterfactuals: {report.n_hard_counterfactuals}

Logical remainders: {report.n_logical_remainders}
"""
