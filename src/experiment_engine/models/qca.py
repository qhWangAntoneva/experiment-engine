"""QCA domain models — text analysis, calibration, truth tables, solutions, etc.

These models capture the full QCA analysis lifecycle: condition definitions,
fuzzy-set data, truth tables, Boolean solutions, necessity/sufficiency analysis,
robustness testing, counterfactuals, and multi-outcome comparisons.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ── Text Domain ────────────────────────────────────────────────────────


class TextDomain(str, Enum):
    """Citizen feedback text domain categories."""

    DISSATISFACTION = "dissatisfaction"
    POLICY_DEMAND = "policy_demand"
    CO_PRODUCTION = "co_production"
    TRUST = "trust"
    GOV_RESPONSIVENESS = "gov_responsiveness"


# ── QCA Variant ──────────────────────────────────────────────────────────


class QCAVariant(str, Enum):
    """QCA variant determining the type of set-membership values."""

    FSQCA = "fsqca"  # fuzzy-set QCA (continuous [0, 1])
    CSQCA = "csqca"  # crisp-set QCA (binary {0, 1})


# ── Calibration ─────────────────────────────────────────────────────────


class CalibrationMethod(str, Enum):
    """Membership calibration method types."""

    DIRECT = "direct"  # piecewise linear
    INDIRECT = "indirect"  # log-odds transformation
    FUZZY_DIRECT = "fuzzy_direct"  # Ragin's direct method
    PASSTHROUGH = "passthrough"  # use raw score as-is without transformation
    CRISP_SET = "crisp_set"  # single-threshold binarization (0 or 1)


# Backward-compatibility alias.
CalibrationType = CalibrationMethod


class ScoringSource(str, Enum):
    """How a condition's raw score is computed.

    PROTOTYPE is the only scoring source using BERT CLS embedding + cosine
    similarity. Legacy KEYWORD and HYBRID values were removed in Phase 5.
    """

    PROTOTYPE = "prototype"  # BERT CLS embedding + cosine similarity


class CalibrationParams(BaseModel):
    """Threshold parameters for fuzzy-set calibration.

    Attributes:
        threshold_full_in: Score above which membership = 1.0
        threshold_full_out: Score below which membership = 0.0
        crossover_point: Score where membership = 0.5
        direction: 'ascending' (higher score -> higher membership) or 'descending'
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
    notes: str = ""


class ConceptPrototype(BaseModel):
    """A prototype text labeled for membership in a condition.

    Attributes:
        prototype_text: Chinese text exemplifying (or not) the condition.
        is_member: 1 = positive example (full member), 0 = negative example (non-member).
        weight: Weight for aggregating multiple prototypes (0.0-1.0).
    """

    prototype_text: str = Field(..., min_length=1)
    is_member: int = Field(1, ge=0, le=1)
    weight: float = Field(1.0, ge=0.0, le=1.0)


class ConditionDefinition(BaseModel):
    """Defines a single QCA condition for text analysis.

    Attributes:
        name: Machine-readable condition identifier (e.g., 'strong_negative_affect').
        display_name: Human-readable label, typically Chinese.
        domain: The text domain this condition belongs to.
        calibration_type: Method used for fuzzy-set calibration.
        calibration_params: Thresholds for calibration (fitted or manual).
        description: Optional longer description of the condition.
        scoring_source: How raw scores are computed (PROTOTYPE is primary).
        prototypes: Prototype texts for BERT cosine-similarity scoring.
        prototype_embeddings: Pre-computed BERT CLS embeddings per prototype
            (N_prototypes, 768). Computed once and cached.
        embedding_model: Which BERT model produced prototype_embeddings.
    """

    name: str
    display_name: str
    domain: TextDomain
    calibration_type: CalibrationMethod = CalibrationMethod.DIRECT
    calibration_params: CalibrationParams | None = None
    description: str = ""
    scoring_source: ScoringSource = ScoringSource.PROTOTYPE
    keywords: list[KeywordEntry] = Field(default_factory=list)
    prototypes: list[ConceptPrototype] = Field(default_factory=list)
    prototype_embeddings: list[list[float]] | None = None
    embedding_model: str | None = None


class ConditionSet(BaseModel):
    """Complete set of QCA conditions including the outcome.

    Attributes:
        name: Human-readable label for this condition set.
        description: Optional description of the QCA model.
        conditions: List of causal condition definitions.
        outcome: The outcome condition definition.
        domain: The text domain.
        scoring_source: Default scoring source for all conditions.
        qca_variant: Whether fuzzy-set (fsqca) or crisp-set (csqca).
    """

    name: str = "qca_model"
    description: str = ""
    conditions: list[ConditionDefinition] = Field(default_factory=list)
    outcome: ConditionDefinition | None = None
    domain: TextDomain = TextDomain.DISSATISFACTION
    scoring_source: ScoringSource = ScoringSource.PROTOTYPE
    qca_variant: QCAVariant = QCAVariant.FSQCA

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


class TextCase(BaseModel):
    """A text with a binary outcome for prototype-based QCA analysis.

    Attributes:
        text_id: Unique identifier.
        text: Raw Chinese text content.
        outcome: Binary outcome (0 or 1) used directly as crisp-set membership.
        metadata: Arbitrary additional metadata.
    """

    text_id: str
    text: str
    outcome: int = Field(0, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Fuzzy-Set Data ──────────────────────────────────────────────────────


class MembershipData(BaseModel):
    """Membership matrix — the core intermediate data structure.

    Holds the membership scores for each case across all conditions plus outcome.
    The membership ndarray has shape (n_cases, n_conditions + 1), where the
    last column is the outcome.
    Supports both fuzzy-set (continuous [0,1]) and crisp-set (binary {0,1}).

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


# Deprecated backward-compatibility alias — use MembershipData instead.
FuzzySetData = MembershipData


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

    fuzzy_data: MembershipData | None = None
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
