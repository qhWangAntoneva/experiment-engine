"""experiment-engine — A modular algorithm experimentation framework.

Pipeline: Input → Computation → Visualization → Report
"""

__version__ = "0.1.0"
__author__ = "experiment-engine contributors"
__license__ = "MIT"

from experiment_engine.pipeline import Pipeline, Stage
from experiment_engine.models import (
    ExperimentConfig,
    InputData,
    OutputData,
    PipelineStageConfig,
    PipelineResult,
    StageResult,
    StageStatus,
    PipelineStatus,
    Timer,
)
from experiment_engine.plugins import (
    BasePlugin,
    PluginRegistry,
    PluginLoader,
    register_stage,
)
from experiment_engine.config import load_config, merge_defaults

__all__ = [
    "Pipeline",
    "Stage",
    "ExperimentConfig",
    "InputData",
    "OutputData",
    "PipelineStageConfig",
    "PipelineResult",
    "StageResult",
    "StageStatus",
    "PipelineStatus",
    "Timer",
    "BasePlugin",
    "PluginRegistry",
    "PluginLoader",
    "register_stage",
    "load_config",
    "merge_defaults",
]
