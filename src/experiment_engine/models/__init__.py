"""
experiment-engine models package.

Re-exports from the legacy ``experiment_engine.models`` module (``models.py``)
and provides additional schema-oriented config helpers from ``.config_models``.
"""

# ── Import the legacy ``models.py`` module via its file path ──
# Python resolves package directories over .py modules of the same name,
# so we use importlib to load the pre-existing ``models.py`` file directly.
import importlib.util
import sys
from pathlib import Path

_legacy_path = Path(__file__).resolve().parent.with_name("models.py")
if _legacy_path.exists():
    _spec = importlib.util.spec_from_file_location(
        "experiment_engine._models_legacy", _legacy_path
    )
    if _spec and _spec.loader:
        _legacy = importlib.util.module_from_spec(_spec)
        sys.modules["experiment_engine._models_legacy"] = _legacy
        _spec.loader.exec_module(_legacy)

        # Re-export all public names from the legacy module
        from experiment_engine._models_legacy import *  # noqa: F403
else:
    # Fallback: define the minimal set needed by pipeline.py
    from enum import Enum
    from typing import Any, Dict, List, Optional
    from pydantic import BaseModel, Field

    class StageStatus(str, Enum):
        PENDING = "pending"; RUNNING = "running"
        COMPLETED = "completed"; FAILED = "failed"; SKIPPED = "skipped"

    class PipelineStatus(str, Enum):
        PENDING = "pending"; RUNNING = "running"
        COMPLETED = "completed"; FAILED = "failed"; PARTIAL = "partial"

    class PipelineStageConfig(BaseModel):
        name: str = Field(...)
        stage_type: str = Field(...)
        enabled: bool = True
        params: Dict[str, Any] = Field(default_factory=dict)

    class StageResult(BaseModel): pass
    class PipelineResult(BaseModel): pass
    class Timer: pass

# ── Schema-oriented config models ──
from experiment_engine.models.config_models import (  # noqa: E402, F401
    InputConfig,
    AlgorithmConfig,
    VisualizationConfig,
    OutputConfig,
    PipelineConfig as SchemaPipelineConfig,
    ExperimentResult,
)

__all__ = [
    # Legacy models
    "StageStatus", "PipelineStatus", "PipelineStageConfig",
    "InputData", "OutputData", "StageResult", "PipelineResult", "Timer",
    # Config schemas
    "InputConfig", "AlgorithmConfig", "VisualizationConfig",
    "OutputConfig", "SchemaPipelineConfig", "ExperimentResult",
]
