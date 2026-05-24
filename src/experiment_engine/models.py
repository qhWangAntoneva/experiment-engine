"""Pydantic data models for the experiment-engine pipeline framework.

All models use Pydantic v2 patterns with built-in validation and serialization.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ──────────────────────────────────────────────
#  Generic type variables
# ──────────────────────────────────────────────

T = TypeVar("T")
U = TypeVar("U")


# ──────────────────────────────────────────────
#  Enums
# ──────────────────────────────────────────────


class StageStatus(str, Enum):
    """Execution status of a pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineStatus(str, Enum):
    """Overall execution status of a pipeline."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # some stages succeeded, some failed


# ──────────────────────────────────────────────
#  Configuration models
# ──────────────────────────────────────────────


class PipelineStageConfig(BaseModel):
    """Configuration for a single pipeline stage.

    Attributes:
        name: Unique stage name used for lookup and logging.
        stage_type: Identifier string matching a registered plugin or class.
        enabled: Whether the stage is active. Disabled stages are skipped.
        params: Arbitrary key-value parameters passed to the stage on setup.
    """

    name: str = Field(..., description="Unique stage name")
    stage_type: str = Field(..., description="Registered stage type identifier")
    enabled: bool = Field(True, description="Whether this stage is active")
    params: dict[str, Any] = Field(
        default_factory=dict, description="Stage-specific parameters"
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Stage name must not be empty")
        return v.strip()

    @field_validator("stage_type")
    @classmethod
    def stage_type_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Stage type must not be empty")
        return v.strip()


class InputConfig(BaseModel):
    """Configuration for data input in an experiment.

    Specifies how to load data: the source format, file path (if any),
    and additional options passed to the reader.

    Attributes:
        format: Data source format (csv, json, array, synthetic).
        path: Optional file path. If None, synthetic/generated data is used.
        options: Additional kwargs forwarded to the reader's ``read()`` method.
    """

    format: str = Field(
        "csv", description="Data source format (csv, json, array, synthetic)"
    )
    path: str | None = Field(None, description="File path for data input")
    options: dict[str, Any] = Field(default_factory=dict, description="Reader kwargs")


class ExportConfig(BaseModel):
    """Configuration for exporting pipeline results.

    Attributes:
        format: Export format (csv, json, html).
        output_path: Destination file path. If None, auto-generated.
        include_index: Whether to include row indices in tabular output.
        pretty: Whether to pretty-print structured formats (JSON, HTML).
    """

    format: str = Field("csv", description="Export format (csv, json, html)")
    output_path: str | None = Field(None, description="Output file path")
    include_index: bool = Field(False, description="Include row indices")
    pretty: bool = Field(False, description="Pretty-print output")


class ExperimentConfig(BaseModel):
    """Top-level global pipeline configuration.

    Attributes:
        name: Human-readable experiment name.
        description: Optional description of the experiment.
        version: Config schema version.
        stages: Ordered list of stage configurations defining the pipeline.
        global_params: Parameters shared across all stages.
        output_dir: Directory for writing output artifacts.
        verbose: Enable verbose / debug logging.
    """

    name: str = Field("experiment", description="Experiment name")
    description: str | None = Field(None, description="Experiment description")
    version: str = Field("1.0", description="Config schema version")
    stages: list[PipelineStageConfig] = Field(
        default_factory=list, description="Ordered pipeline stage definitions"
    )
    global_params: dict[str, Any] = Field(
        default_factory=dict, description="Parameters shared across all stages"
    )
    output_dir: str | None = Field(None, description="Directory for output artifacts")
    verbose: bool = Field(False, description="Enable verbose logging")

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Experiment name must not be empty")
        return v.strip()


class RenderConfig(BaseModel):
    """Configuration for rendering visualizations.

    Specifies the plot type, layout options, and output path used by
    visualization renderers (Matplotlib, Plotly, Console, etc.).

    Attributes:
        plot_type: Type of plot (line, scatter, bar, histogram, surface).
        title: Optional plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        figsize: Figure dimensions as (width, height) in inches.
        dpi: Image resolution in dots per inch.
        colormap: Matplotlib-compatible colormap name.
        output_path: Optional output file path override.
    """

    plot_type: str = Field(
        "line", description="Plot type (line/scatter/bar/histogram/surface)"
    )
    title: str | None = Field(None, description="Plot title")
    xlabel: str | None = Field(None, description="X-axis label")
    ylabel: str | None = Field(None, description="Y-axis label")
    figsize: tuple[float, float] = Field(
        (8.0, 5.0), description="Figure size (width, height)"
    )
    dpi: int = Field(150, description="Image resolution")
    colormap: str = Field("viridis", description="Color scheme")
    output_path: str | None = Field(None, description="Output file path override")


# ──────────────────────────────────────────────
#  Data models
# ──────────────────────────────────────────────


class InputData(BaseModel, Generic[T]):
    """Generic input data schema for pipeline stages.

    Attributes:
        data: The raw input payload (type varies by stage).
        metadata: Arbitrary metadata attached to the input.
        timestamp: When this input was created.
        columns: Optional column / feature names.
        index: Optional row index labels.
    """

    data: T = Field(..., description="Raw input payload")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Input metadata")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    columns: list[str] | None = Field(None, description="Column / feature names")
    index: list[Any] | None = Field(None, description="Row index labels")

    @property
    def n_samples(self) -> int:
        """Number of samples (rows) in the data."""
        if hasattr(self.data, "shape"):
            return self.data.shape[0]
        if isinstance(self.data, list):
            return len(self.data)
        return 0

    @property
    def n_features(self) -> int:
        """Number of features (columns) in the data."""
        if hasattr(self.data, "shape") and len(self.data.shape) >= 2:
            return self.data.shape[1]
        return 1

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the underlying data array."""
        if hasattr(self.data, "shape"):
            return self.data.shape
        if isinstance(self.data, list):
            return (len(self.data),)
        return (0,)


class OutputData(BaseModel, Generic[T]):
    """Generic output data schema produced by pipeline stages.

    Stores both the raw (pre-stage) and processed (post-stage) data,
    enabling downstream introspection and debugging.

    Attributes:
        raw: Original input data before stage processing.
        processed: Data after stage processing.
        metadata: Processing metadata including timing and stage info.
    """

    raw: T = Field(..., description="Original input data")
    processed: T | None = Field(None, description="Processed output data")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Processing metadata"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Output creation timestamp",
    )


# ──────────────────────────────────────────────
#  Result models
# ──────────────────────────────────────────────


class StageResult(BaseModel):
    """Result from a single pipeline stage execution.

    Carries detailed metadata including timing, status, and optional errors.

    Attributes:
        stage_name: Name of the stage that produced this result.
        stage_type: Type identifier of the stage.
        status: Execution status.
        duration_ms: Execution time in milliseconds.
        started_at: ISO-formatted start timestamp.
        completed_at: ISO-formatted completion timestamp.
        error: Error message if the stage failed.
        metadata: Arbitrary result metadata produced by the stage.
    """

    stage_name: str = Field(..., description="Stage name")
    stage_type: str = Field(..., description="Stage type identifier")
    status: StageStatus = Field(StageStatus.PENDING, description="Execution status")
    duration_ms: float = Field(0.0, description="Duration in milliseconds")
    started_at: str | None = Field(None, description="Start timestamp (ISO)")
    completed_at: str | None = Field(None, description="Completion timestamp (ISO)")
    error: str | None = Field(None, description="Error message on failure")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Stage-specific result metadata"
    )


class PipelineResult(BaseModel):
    """Complete result from a full pipeline execution.

    Aggregates per-stage results and provides top-level summary metrics.

    Attributes:
        experiment_name: Name of the experiment / pipeline.
        status: Overall pipeline status.
        total_duration_ms: Total end-to-end execution time.
        stages: Ordered list of per-stage results.
        started_at: ISO-formatted pipeline start timestamp.
        completed_at: ISO-formatted pipeline completion timestamp.
        output: Final output data produced by the last stage (if any).
        metadata: Pipeline-level metadata.
    """

    experiment_name: str = Field("experiment", description="Experiment name")
    status: PipelineStatus = Field(
        PipelineStatus.PENDING, description="Overall pipeline status"
    )
    total_duration_ms: float = Field(0.0, description="Total duration in milliseconds")
    stages: list[StageResult] = Field(
        default_factory=list, description="Per-stage results in execution order"
    )
    started_at: str | None = Field(None, description="Start timestamp (ISO)")
    completed_at: str | None = Field(None, description="Completion timestamp (ISO)")
    output: Any | None = Field(None, description="Final pipeline output")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Pipeline-level metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_name": "my-experiment",
                "status": "completed",
                "total_duration_ms": 1234.56,
                "stages": [
                    {
                        "stage_name": "loader",
                        "stage_type": "data_loader",
                        "status": "completed",
                        "duration_ms": 100.5,
                    }
                ],
            }
        }
    )

    @property
    def success_count(self) -> int:
        """Number of stages that completed successfully."""
        return sum(
            1
            for s in self.stages
            if s.status == StageStatus.COMPLETED or s.status == StageStatus.SKIPPED
        )

    @property
    def failure_count(self) -> int:
        """Number of stages that failed."""
        return sum(1 for s in self.stages if s.status == StageStatus.FAILED)

    @property
    def total_stages(self) -> int:
        """Total number of stages in the pipeline (excluding sub-pipelines)."""
        return len(self.stages)

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to a plain dictionary (JSON-compatible)."""
        return self.model_dump(mode="json")


# ──────────────────────────────────────────────
#  Timing utility
# ──────────────────────────────────────────────


class Timer:
    """Simple context-manager timer for measuring execution duration.

    Usage:
        with Timer() as timer:
            do_something()
        print(f"Took {timer.duration_ms:.2f} ms")
    """

    def __init__(self) -> None:
        self._start: float = 0.0
        self._end: float = 0.0
        self.duration_ms: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self._end = time.perf_counter()
        self.duration_ms = (self._end - self._start) * 1000.0


# ═══════════════════════════════════════════════════════════════════════════
#  QCA Text Analysis Models
# ═══════════════════════════════════════════════════════════════════════════


# ── Text Domain ────────────────────────────────────────────────────────


class TextDomain(str, Enum):
    """Citizen feedback text domain categories."""

    DISSATISFACTION = "dissatisfaction"
    POLICY_DEMAND = "policy_demand"
    CO_PRODUCTION = "co_production"
    TRUST = "trust"
    GOV_RESPONSIVENESS = "gov_responsiveness"


# ── Calibration ─────────────────────────────────────────────────────────


class CalibrationType(str, Enum):
    """Fuzzy-set calibration method types."""

    DIRECT = "direct"  # piecewise linear
    INDIRECT = "indirect"  # log-odds transformation
    FUZZY_DIRECT = "fuzzy_direct"  # Ragin's direct method


class CalibrationParams(BaseModel):
    """Threshold parameters for fuzzy-set calibration.

    Attributes:
        threshold_full_in: Score above which membership = 1.0
        threshold_full_out: Score below which membership = 0.0
        crossover_point: Score where membership = 0.5
        direction: 'ascending' (higher score → higher membership) or 'descending'
    """

    threshold_full_in: float = Field(..., ge=0.0, le=1.0)
    threshold_full_out: float = Field(..., ge=0.0, le=1.0)
    crossover_point: float = Field(..., ge=0.0, le=1.0)
    direction: str = Field("ascending", pattern=r"^(ascending|descending)$")

    @field_validator("threshold_full_in")
    @classmethod
    def full_in_gt_crossover(cls, v: float, info: Any) -> float:
        crossover = info.data.get("crossover_point", 0.5)
        if v < crossover:
            raise ValueError("threshold_full_in must be >= crossover_point")
        return v

    @field_validator("threshold_full_out")
    @classmethod
    def full_out_lt_crossover(cls, v: float, info: Any) -> float:
        crossover = info.data.get("crossover_point", 0.5)
        if v > crossover:
            raise ValueError("threshold_full_out must be <= crossover_point")
        return v


class KeywordEntry(BaseModel):
    """A keyword pattern with associated weight for text-to-score matching.

    Attributes:
        pattern: The keyword string or regex pattern.
        weight: Contribution weight (0.0-1.0 range typical).
        scope: Matching granularity: unigram, bigram, trigram, regex, or exact.
    """

    pattern: str
    weight: float = 1.0
    scope: str = Field("bigram", pattern=r"^(unigram|bigram|trigram|regex|exact)$")


class ConditionDefinition(BaseModel):
    """Defines a single QCA condition for text analysis.

    Attributes:
        name: Machine-readable condition identifier (e.g., 'strong_negative_affect').
        display_name: Human-readable label, typically Chinese.
        domain: The text domain this condition belongs to.
        keywords: List of keyword entries for text matching.
        calibration_type: Method used for fuzzy-set calibration.
        calibration_params: Thresholds for calibration (fitted or manual).
        description: Optional longer description of the condition.
    """

    name: str
    display_name: str
    domain: TextDomain
    keywords: list[KeywordEntry] = Field(default_factory=list)
    calibration_type: CalibrationType = CalibrationType.DIRECT
    calibration_params: CalibrationParams | None = None
    description: str = ""


class ConditionSet(BaseModel):
    """Complete set of QCA conditions including the outcome.

    Attributes:
        name: Human-readable label for this condition set.
        description: Optional description of the QCA model.
        conditions: List of causal condition definitions.
        outcome: The outcome condition definition.
        domain: The text domain.
    """

    name: str = "qca_model"
    description: str = ""
    conditions: list[ConditionDefinition] = Field(default_factory=list)
    outcome: ConditionDefinition | None = None
    domain: TextDomain = TextDomain.DISSATISFACTION

    @property
    def condition_names(self) -> list[str]:
        return [c.name for c in self.conditions]

    @property
    def all_names(self) -> list[str]:
        names = self.condition_names
        if self.outcome:
            names.append(self.outcome.name)
        return names

    @property
    def n_conditions(self) -> int:
        return len(self.conditions)


# ── Training / Labeled Samples ──────────────────────────────────────────


class TrainingSample(BaseModel):
    """A single labeled training sample mapping text to fuzzy-set scores.

    Attributes:
        text_id: Unique identifier for the text.
        text: The raw Chinese text content.
        labeled_scores: Dict mapping condition_name → fuzzy membership (0-1).
        domain: Optional text domain override.
        metadata: Arbitrary additional metadata.
    """

    text_id: str
    text: str
    labeled_scores: dict[str, float] = Field(default_factory=dict)
    domain: TextDomain | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("labeled_scores")
    @classmethod
    def scores_in_range(cls, v: dict[str, float]) -> dict[str, float]:
        for key, val in v.items():
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"Score for '{key}' is {val}, must be in [0, 1]")
        return v


class TrainingDataset(BaseModel):
    """Collection of labeled training samples.

    Attributes:
        samples: List of training samples.
        condition_names: Names of conditions in the labeled_scores dict.
        outcome_name: Name of the outcome condition.
    """

    samples: list[TrainingSample] = Field(default_factory=list)
    condition_names: list[str] = Field(default_factory=list)
    outcome_name: str = ""

    @property
    def n_samples(self) -> int:
        return len(self.samples)


# ── Fuzzy-Set Data ──────────────────────────────────────────────────────


class FuzzySetData(BaseModel):
    """Fuzzy-set membership matrix — the core intermediate data structure.

    Holds the membership scores for each case across all conditions plus outcome.
    The membership ndarray has shape (n_cases, n_conditions + 1), where the
    last column is the outcome.

    Attributes:
        membership: 2D numpy array of fuzzy membership scores.
        case_ids: Optional identifiers for each case.
        condition_names: Names of causal conditions (excluding outcome).
        outcome_name: Name of the outcome condition.
        texts: Optional original text content for traceability.
        metadata: Arbitrary additional metadata.
    """

    membership: np.ndarray
    case_ids: list[str] | None = None
    condition_names: list[str] = Field(default_factory=list)
    outcome_name: str = ""
    texts: list[str] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("membership")
    @classmethod
    def membership_2d(cls, v: np.ndarray) -> np.ndarray:
        if v.ndim != 2:
            raise ValueError(f"membership must be 2D, got {v.ndim}D")
        if v.shape[1] < 1:
            raise ValueError("membership must have at least 1 column")
        if np.any(v < 0) or np.any(v > 1):
            raise ValueError("membership values must be in [0, 1]")
        return v

    @property
    def n_cases(self) -> int:
        return int(self.membership.shape[0])

    @property
    def n_conditions(self) -> int:
        return int(self.membership.shape[1]) - 1

    @property
    def condition_matrix(self) -> np.ndarray:
        """All columns except the outcome (last column)."""
        return self.membership[:, : self.n_conditions]

    @property
    def outcome_vector(self) -> np.ndarray:
        """The outcome column (last column)."""
        return self.membership[:, self.n_conditions]


# ── Truth Table ─────────────────────────────────────────────────────────


class TruthTableRow(BaseModel):
    """A single row in a QCA truth table.

    Attributes:
        config: Binary configuration vector (e.g., [1, 0, 1, 0]).
        config_label: Human-readable label (e.g., 'A*~B*C*~D').
        frequency: Number of cases in this configuration.
        raw_consistency: Subset consistency with the outcome.
        outcome_value: Assigned outcome (1 = consistent, 0 = not).
        included: Whether this row passes frequency/consistency thresholds.
    """

    config: list[int]
    config_label: str
    frequency: float
    raw_consistency: float
    outcome_value: int = 0
    included: bool = True

    @field_validator("outcome_value")
    @classmethod
    def outcome_binary(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError(f"outcome_value must be 0 or 1, got {v}")
        return v


class TruthTable(BaseModel):
    """Complete QCA truth table.

    Attributes:
        rows: All truth table rows (2^k configurations).
        condition_names: Names of causal conditions.
        outcome_name: Name of the outcome.
        consistency_threshold: Threshold used for outcome assignment.
        frequency_threshold: Minimum frequency to include a row.
        n_cases: Total number of cases.
    """

    rows: list[TruthTableRow] = Field(default_factory=list)
    condition_names: list[str] = Field(default_factory=list)
    outcome_name: str = ""
    consistency_threshold: float = 0.75
    frequency_threshold: float = 1.0
    n_cases: int = 0

    @property
    def n_configurations(self) -> int:
        return 2 ** len(self.condition_names)

    @property
    def included_rows(self) -> list[TruthTableRow]:
        return [r for r in self.rows if r.included]

    @property
    def positive_rows(self) -> list[TruthTableRow]:
        return [r for r in self.rows if r.included and r.outcome_value == 1]


# ── QCA Solutions ───────────────────────────────────────────────────────


class SolutionTerm(BaseModel):
    """A single solution term (conjunction of conditions).

    Attributes:
        term: List of condition names with optional '~' prefix for negation.
        label: Formatted label (e.g., 'A*~B*C').
        consistency: Sufficiency consistency of this term.
        raw_coverage: Raw coverage of this term.
        unique_coverage: Unique coverage of this term.
    """

    term: list[str] = Field(default_factory=list)
    label: str = ""
    consistency: float = 0.0
    raw_coverage: float = 0.0
    unique_coverage: float = 0.0


class QCASolution(BaseModel):
    """A QCA solution of a single type (complex/parsimonious/intermediate).

    Attributes:
        solution_type: One of 'complex', 'parsimonious', 'intermediate'.
        terms: List of solution terms.
        formula: Boolean formula string (e.g., 'A*~B*C + ~A*D*E').
        solution_consistency: Overall solution consistency.
        solution_coverage: Overall solution coverage.
    """

    solution_type: str = "complex"
    terms: list[SolutionTerm] = Field(default_factory=list)
    formula: str = ""
    solution_consistency: float = 0.0
    solution_coverage: float = 0.0


class QCASolutions(BaseModel):
    """The three types of QCA solutions.

    Attributes:
        complex: Solution from only empirically observed configurations.
        parsimonious: Solution including easy counterfactuals.
        intermediate: Solution including theoretically plausible counterfactuals.
    """

    complex: QCASolution | None = None
    parsimonious: QCASolution | None = None
    intermediate: QCASolution | None = None


# ── Necessity / Sufficiency Results ─────────────────────────────────────


class NecessityConditionResult(BaseModel):
    """Necessity analysis result for a single condition.

    Attributes:
        condition_name: Name of the condition.
        consistency: Necessity consistency (X_i >= Y).
        coverage: Necessity coverage.
        is_necessary: Whether consistency >= threshold (default 0.9).
    """

    condition_name: str
    consistency: float
    coverage: float
    is_necessary: bool


class NecessityResults(BaseModel):
    """Full necessity analysis results.

    Attributes:
        outcome_name: The outcome analyzed.
        threshold: Necessity consistency threshold used.
        conditions: Per-condition necessity results.
    """

    outcome_name: str = ""
    threshold: float = 0.9
    conditions: list[NecessityConditionResult] = Field(default_factory=list)


class SufficiencyResults(BaseModel):
    """Full sufficiency analysis results.

    Attributes:
        outcome_name: The outcome analyzed.
        solutions: The QCA solutions with consistency/coverage metrics.
    """

    outcome_name: str = ""
    solutions: QCASolutions = Field(default_factory=QCASolutions)


# ── Comprehensive QCA Result ────────────────────────────────────────────


class QCAAnalysisResult(BaseModel):
    """Complete output of a QCA analysis run.

    Attributes:
        fuzzy_data: The input fuzzy-set membership matrix.
        truth_table: The constructed truth table.
        solutions: All three solution types.
        necessity: Necessity analysis results.
        sufficiency: Sufficiency analysis results.
        condition_set: The condition definitions used.
        metadata: Arbitrary additional metadata.
    """

    fuzzy_data: FuzzySetData | None = None
    truth_table: TruthTable | None = None
    solutions: QCASolutions = Field(default_factory=QCASolutions)
    necessity: NecessityResults | None = None
    sufficiency: SufficiencyResults | None = None
    condition_set: ConditionSet | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Robustness ──────────────────────────────────────────────────────────


class RobustnessTestResult(BaseModel):
    """Result of a single robustness/sensitivity test.

    Attributes:
        test_name: Name of the robustness test.
        parameter_varied: Which parameter was varied.
        parameter_values: Values the parameter took.
        solution_stability: Jaccard similarity to baseline per value.
        coverage_stability: Coverage change per value.
        passed: Whether the test passed (results stable).
    """

    test_name: str
    parameter_varied: str
    parameter_values: list[float] = Field(default_factory=list)
    solution_stability: list[float] = Field(default_factory=list)
    coverage_stability: list[float] = Field(default_factory=list)
    passed: bool = True


class RobustnessReport(BaseModel):
    """Complete robustness analysis report.

    Attributes:
        tests: Individual test results.
        overall_robustness: Aggregate stability score (0-1).
        summary: Human-readable summary.
    """

    tests: list[RobustnessTestResult] = Field(default_factory=list)
    overall_robustness: float = 0.0
    summary: str = ""


# ── Counterfactuals ─────────────────────────────────────────────────────


class CounterfactualClassification(BaseModel):
    """Classification of a truth table row for counterfactual analysis.

    Attributes:
        config: The truth table configuration row.
        is_observed: Whether this configuration has empirical cases.
        counterfactual_type: 'easy', 'hard', or None if observed.
        theoretical_expectation: Expected outcome direction from theory.
    """

    config: list[int] = Field(default_factory=list)
    is_observed: bool = False
    counterfactual_type: str | None = None
    theoretical_expectation: str | None = None


class CounterfactualReport(BaseModel):
    """Complete counterfactual analysis report.

    Attributes:
        classifications: Per-row counterfactual classifications.
        n_easy_counterfactuals: Count of easy counterfactuals.
        n_hard_counterfactuals: Count of hard counterfactuals.
        n_logical_remainders: Count of logical remainders.
    """

    classifications: list[CounterfactualClassification] = Field(default_factory=list)
    n_easy_counterfactuals: int = 0
    n_hard_counterfactuals: int = 0
    n_logical_remainders: int = 0


# ── Multi-Outcome ───────────────────────────────────────────────────────


class MultiOutcomeReport(BaseModel):
    """Cross-outcome comparison report.

    Attributes:
        outcomes: List of outcome names compared.
        shared_conditions: Conditions common to all outcomes.
        unique_conditions: Conditions unique to specific outcomes.
        pairwise_similarity: Matrix of solution similarities between outcomes.
    """

    outcomes: list[str] = Field(default_factory=list)
    shared_conditions: list[str] = Field(default_factory=list)
    unique_conditions: dict[str, list[str]] = Field(default_factory=dict)
    pairwise_similarity: list[list[float]] = Field(default_factory=list)
