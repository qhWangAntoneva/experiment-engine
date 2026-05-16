"""experiment-engine — A modular algorithm experimentation framework.

Pipeline: Input → Computation → Visualization → Report
"""

__version__ = "0.1.0"
__author__ = "experiment-engine contributors"
__license__ = "MIT"

from experiment_engine.config import load_config, merge_defaults
from experiment_engine.models import (
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
    Timer,
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
    "ExperimentConfig",
    "ExportConfig",
    "InputConfig",
    "InputData",
    "OutputData",
    "Pipeline",
    "PipelineResult",
    "PipelineStageConfig",
    "PipelineStatus",
    "PluginLoader",
    "PluginRegistry",
    "RenderConfig",
    "Stage",
    "StageResult",
    "StageStatus",
    "Timer",
    "load_config",
    "merge_defaults",
    "register_stage",
]
