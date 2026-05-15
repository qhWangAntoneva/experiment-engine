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
)
from experiment_engine.plugins import (
    PluginRegistry,
    registry,
    register_algorithm,
    register_loader,
    register_visualizer,
    AlgorithmBase,
)
from experiment_engine.config import load_config

__all__ = [
    "Pipeline",
    "Stage",
    "ExperimentConfig",
    "InputData",
    "OutputData",
    "PipelineStageConfig",
    "PipelineResult",
    "StageResult",
    "PluginRegistry",
    "registry",
    "register_algorithm",
    "register_loader",
    "register_visualizer",
    "AlgorithmBase",
    "load_config",
]
