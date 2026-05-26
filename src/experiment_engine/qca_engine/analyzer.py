"""Main QCA analysis pipeline stage — orchestrates the full analysis."""

from __future__ import annotations

from experiment_engine.models import (
    ConditionSet,
    InputData,
    MembershipData,
    OutputData,
    QCAAnalysisResult,
)
from experiment_engine.plugins import BasePlugin, register_stage
from experiment_engine.qca_engine.minimization import QuineMcCluskey
from experiment_engine.qca_engine.necessity import NecessityAnalyzer
from experiment_engine.qca_engine.solution import SolutionFormatter
from experiment_engine.qca_engine.sufficiency import SufficiencyAnalyzer
from experiment_engine.qca_engine.truth_table import TruthTableBuilder


@register_stage("qca_analysis")
class QCAnalyzerStage(BasePlugin):
    """Full QCA analysis pipeline stage.

    Orchestrates the complete QCA workflow:
    1. Truth table construction
    2. Boolean minimization (complex solution)
    3. Necessity analysis
    4. Sufficiency analysis (consistency + coverage)

    Attributes:
        condition_set: The QCA condition definitions.
        consistency_threshold: Threshold for outcome assignment in truth table.
        frequency_threshold: Minimum frequency to include a truth table row.
    """

    plugin_name = "qca_analyzer"
    plugin_description = (
        "Full QCA analysis: truth table → minimization → necessity → sufficiency"
    )
    plugin_author = "experiment-engine"
    plugin_version = "0.1.0"
    plugin_tags = ["qca", "analysis", "core"]

    def __init__(
        self,
        condition_set: ConditionSet | None = None,
        consistency_threshold: float = 0.75,
        frequency_threshold: float = 1.0,
        name: str = "qca_analysis",
    ) -> None:
        super().__init__(name=name)
        self.condition_set = condition_set
        self.consistency_threshold = consistency_threshold
        self.frequency_threshold = frequency_threshold

        # Sub-components (initialized in setup)
        self.truth_table_builder: TruthTableBuilder = None  # type: ignore[assignment]
        self.minimizer: QuineMcCluskey = None  # type: ignore[assignment]
        self.necessity_analyzer: NecessityAnalyzer = None  # type: ignore[assignment]
        self.sufficiency_analyzer: SufficiencyAnalyzer = None  # type: ignore[assignment]
        self.formatter: SolutionFormatter = None  # type: ignore[assignment]

    def setup(self) -> None:
        self.truth_table_builder = TruthTableBuilder()
        self.minimizer = QuineMcCluskey()
        self.necessity_analyzer = NecessityAnalyzer()
        self.sufficiency_analyzer = SufficiencyAnalyzer()
        self.formatter = SolutionFormatter()

    def process(self, data: InputData) -> OutputData:
        fuzzy_data = self._extract_fuzzy_data(data)

        result = self.analyze(fuzzy_data)

        return OutputData(
            raw=data,
            processed=result,
            metadata={
                "stage": self.name,
                "n_cases": fuzzy_data.n_cases,
                "n_conditions": fuzzy_data.n_conditions,
                "outcome": fuzzy_data.outcome_name,
            },
        )

    def analyze(self, fuzzy_data: MembershipData) -> QCAAnalysisResult:
        """Run the full QCA analysis on fuzzy-set data.

        Args:
            fuzzy_data: Calibrated fuzzy-set membership matrix.

        Returns:
            Complete QCAAnalysisResult with truth table, solutions, and metrics.
        """
        # 1. Build truth table
        truth_table = self.truth_table_builder.build(
            fuzzy_data,
            frequency_threshold=self.frequency_threshold,
            consistency_threshold=self.consistency_threshold,
        )

        # 2. Boolean minimization — complex solution
        positive_rows = truth_table.positive_rows
        if positive_rows:
            minterms = [r.config for r in positive_rows]
            complex_terms = self.minimizer.minimize(
                minterms, truth_table.condition_names
            )
        else:
            complex_terms = []

        # 3. Format solutions
        solutions = self.formatter.format_all_solutions(
            complex_terms=complex_terms if complex_terms else None,
            parsimonious_terms=None,  # filled by CounterfactualAnalyzer
            intermediate_terms=None,  # filled by CounterfactualAnalyzer
            condition_names=truth_table.condition_names,
        )

        # 4. Necessity analysis
        necessity = self.necessity_analyzer.analyze(fuzzy_data)

        # 5. Sufficiency analysis
        sufficiency = self.sufficiency_analyzer.analyze(fuzzy_data, solutions)

        return QCAAnalysisResult(
            fuzzy_data=fuzzy_data,
            truth_table=truth_table,
            solutions=solutions,
            necessity=necessity,
            sufficiency=sufficiency,
            condition_set=self.condition_set,
            metadata={
                "consistency_threshold": self.consistency_threshold,
                "frequency_threshold": self.frequency_threshold,
            },
        )

    @staticmethod
    def _extract_fuzzy_data(data: InputData) -> MembershipData:
        raw = data.data
        if isinstance(raw, MembershipData):
            return raw
        if isinstance(raw, OutputData):
            inner = raw.processed
            if isinstance(inner, MembershipData):
                return inner
            # Try data attribute
            if hasattr(inner, "membership"):
                return MembershipData(**inner.model_dump())
        raise TypeError(
            f"Expected MembershipData, got {type(raw).__name__}. "
            "Run TextCalibrationStage first."
        )
