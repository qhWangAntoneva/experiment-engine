"""QCA Text Analysis Tool — data models.

This package provides all Pydantic v2 data models used across the pipeline:
  - framework.py  — pipeline-generic models (Stage, Pipeline, Configs, I/O)
  - qca.py        — QCA domain models (conditions, truth tables, solutions, etc.)
  - training.py   — training-related models (labeled samples, datasets)

All symbols are re-exported from this __init__ so that existing imports
like ``from experiment_engine.models import FuzzySetData`` continue to work.
"""

from experiment_engine.models.framework import (
    ExperimentConfig,
    ExportConfig,
    InputConfig,
    InputData,
    OutputData,
    PipelineResult,
    PipelineStageConfig,
    PipelineStatus,
    RenderConfig,
    StageResult,
    StageStatus,
    T,
    Timer,
    U,
)
from experiment_engine.models.qca import (
    CalibrationParams,
    CalibrationType,
    ConceptPrototype,
    ConditionDefinition,
    ConditionSet,
    CounterfactualClassification,
    CounterfactualReport,
    FuzzySetData,
    KeywordEntry,
    MultiOutcomeReport,
    NecessityConditionResult,
    NecessityResults,
    QCAAnalysisResult,
    QCASolution,
    QCASolutions,
    RobustnessReport,
    RobustnessTestResult,
    ScoringSource,
    SolutionTerm,
    SufficiencyResults,
    TextCase,
    TextDomain,
    TruthTable,
    TruthTableRow,
)
from experiment_engine.models.training import TrainingDataset, TrainingSample

__all__ = [
    "CalibrationParams",
    "CalibrationType",
    "ConceptPrototype",
    "ConditionDefinition",
    "ConditionSet",
    "CounterfactualClassification",
    "CounterfactualReport",
    "ExperimentConfig",
    "ExportConfig",
    "FuzzySetData",
    "InputConfig",
    "InputData",
    "KeywordEntry",
    "MultiOutcomeReport",
    "NecessityConditionResult",
    "NecessityResults",
    "OutputData",
    "PipelineResult",
    "PipelineStageConfig",
    "PipelineStatus",
    "QCAAnalysisResult",
    "QCASolution",
    "QCASolutions",
    "RenderConfig",
    "RobustnessReport",
    "RobustnessTestResult",
    "ScoringSource",
    "SolutionTerm",
    "StageResult",
    "StageStatus",
    "SufficiencyResults",
    "T",
    "TextCase",
    "TextDomain",
    "Timer",
    "TrainingDataset",
    "TrainingSample",
    "TruthTable",
    "TruthTableRow",
    "U",
]
