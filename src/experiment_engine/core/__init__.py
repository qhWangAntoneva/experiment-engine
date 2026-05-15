"""Core pipeline orchestration — re-exports from the existing pipeline module.

The primary Pipeline/Stage implementations live in
``experiment_engine.pipeline`` (top-level module). This package
provides a secondary namespace for modular additions.
"""

from experiment_engine.pipeline import Pipeline, Stage, PipelineResult
from experiment_engine.pipeline import PipelineElement  # noqa: F401

__all__ = ["Pipeline", "Stage", "PipelineResult"]
