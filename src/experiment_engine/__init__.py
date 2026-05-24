"""QCA Text Analysis Tool — citizen feedback text → fuzzy-set QCA analysis.

Pipeline: Text Input → Calibration → QCA Analysis → Report
"""

__version__ = "0.2.0"
__author__ = "experiment-engine contributors"
__license__ = "MIT"

from experiment_engine.config import load_config, merge_defaults
from experiment_engine.models import (
    CalibrationType,
    ConceptPrototype,
    ConditionDefinition,
    ConditionSet,
    ExperimentConfig,
    ExportConfig,
    FuzzySetData,
    InputConfig,
    InputData,
    OutputData,
    PipelineResult,
    PipelineStageConfig,
    PipelineStatus,
    QCAAnalysisResult,
    QCASolutions,
    RenderConfig,
    ScoringSource,
    StageResult,
    StageStatus,
    TextCase,
    Timer,
    TrainingSample,
    TruthTable,
)
from experiment_engine.pipeline import Pipeline, Stage
from experiment_engine.plugins import (
    BasePlugin,
    PluginLoader,
    PluginRegistry,
    register_stage,
)

__all__ = [
    "BasePlugin",
    "CalibrationType",
    "ConceptPrototype",
    "ConditionDefinition",
    "ConditionSet",
    "ExperimentConfig",
    "ExportConfig",
    "FuzzySetData",
    "InputConfig",
    "InputData",
    "OutputData",
    "Pipeline",
    "PipelineResult",
    "PipelineStageConfig",
    "PipelineStatus",
    "PluginLoader",
    "PluginRegistry",
    "QCAAnalysisResult",
    "QCASolutions",
    "RenderConfig",
    "ScoringSource",
    "Stage",
    "StageResult",
    "StageStatus",
    "TextCase",
    "Timer",
    "TrainingSample",
    "TruthTable",
    "load_config",
    "merge_defaults",
    "register_stage",
]
