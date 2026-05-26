"""Core pipeline orchestration — re-exports from the existing pipeline module.

The primary Pipeline/Stage implementations live in
``experiment_engine.pipeline`` (top-level module). This package
provides a secondary namespace for modular additions.
"""

import contextlib

with contextlib.suppress(ImportError):
    from experiment_engine.core.parallel import (
        ParallelPipeline,
        ParallelStageGroup,
    )
# parallel.py is excluded from Pyodide deployments (multiprocessing
# requires native OS fork, unavailable in the browser's Pyodide runtime).
# Do NOT bind ParallelPipeline/ParallelStageGroup to None — __getattr__
# below intercepts access and raises a descriptive ImportError.
from experiment_engine.pipeline import (
    Pipeline,
    PipelineElement,
    PipelineResult,
    Stage,
)

__all__ = [
    "ParallelPipeline",
    "ParallelStageGroup",
    "Pipeline",
    "PipelineResult",
    "Stage",
]


def __getattr__(name: str):
    if name in ("ParallelPipeline", "ParallelStageGroup"):
        raise ImportError(
            f"{name} requires experiment_engine.core.parallel "
            "(multiprocessing), which is not available in "
            "Pyodide/browser environments."
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
