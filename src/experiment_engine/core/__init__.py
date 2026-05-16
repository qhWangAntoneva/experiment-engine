"""Core pipeline orchestration — re-exports from the existing pipeline module.

The primary Pipeline/Stage implementations live in
``experiment_engine.pipeline`` (top-level module). This package
provides a secondary namespace for modular additions.
"""

from experiment_engine.pipeline import (
    Pipeline,
    PipelineElement,
    PipelineResult,
    Stage,
)

__all__ = ["Pipeline", "PipelineResult", "Stage"]
