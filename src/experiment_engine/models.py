"""Pydantic data models for the experiment-engine pipeline framework.

All models use Pydantic v2 patterns with built-in validation and serialization.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ──────────────────────────────────────────────
#  Generic type variables
# ──────────────────────────────────────────────

T = TypeVar("T")
U = TypeVar("U")


# ──────────────────────────────────────────────
#  Enums
# ──────────────────────────────────────────────


class StageStatus(str, Enum):
    """Execution status of a pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineStatus(str, Enum):
    """Overall execution status of a pipeline."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # some stages succeeded, some failed


# ──────────────────────────────────────────────
#  Configuration models
# ──────────────────────────────────────────────


class PipelineStageConfig(BaseModel):
    """Configuration for a single pipeline stage.

    Attributes:
        name: Unique stage name used for lookup and logging.
        stage_type: Identifier string matching a registered plugin or class.
        enabled: Whether the stage is active. Disabled stages are skipped.
        params: Arbitrary key-value parameters passed to the stage on setup.
    """

    name: str = Field(..., description="Unique stage name")
    stage_type: str = Field(..., description="Registered stage type identifier")
    enabled: bool = Field(True, description="Whether this stage is active")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Stage-specific parameters"
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Stage name must not be empty")
        return v.strip()

    @field_validator("stage_type")
    @classmethod
    def stage_type_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Stage type must not be empty")
        return v.strip()


class InputConfig(BaseModel):
    """Configuration for data input in an experiment.

    Specifies how to load data: the source format, file path (if any),
    and additional options passed to the reader.

    Attributes:
        format: Data source format (csv, json, array, synthetic).
        path: Optional file path. If None, synthetic/generated data is used.
        options: Additional kwargs forwarded to the reader's ``read()`` method.
    """

    format: str = Field("csv", description="Data source format (csv, json, array, synthetic)")
    path: Optional[str] = Field(None, description="File path for data input")
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Reader kwargs"
    )


class ExportConfig(BaseModel):
    """Configuration for exporting pipeline results.

    Attributes:
        format: Export format (csv, json, html).
        output_path: Destination file path. If None, auto-generated.
        include_index: Whether to include row indices in tabular output.
        pretty: Whether to pretty-print structured formats (JSON, HTML).
    """

    format: str = Field("csv", description="Export format (csv, json, html)")
    output_path: Optional[str] = Field(None, description="Output file path")
    include_index: bool = Field(False, description="Include row indices")
    pretty: bool = Field(False, description="Pretty-print output")


class ExperimentConfig(BaseModel):
    """Top-level global pipeline configuration.

    Attributes:
        name: Human-readable experiment name.
        description: Optional description of the experiment.
        version: Config schema version.
        stages: Ordered list of stage configurations defining the pipeline.
        global_params: Parameters shared across all stages.
        output_dir: Directory for writing output artifacts.
        verbose: Enable verbose / debug logging.
    """

    name: str = Field("experiment", description="Experiment name")
    description: Optional[str] = Field(None, description="Experiment description")
    version: str = Field("1.0", description="Config schema version")
    stages: List[PipelineStageConfig] = Field(
        default_factory=list, description="Ordered pipeline stage definitions"
    )
    global_params: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters shared across all stages"
    )
    output_dir: Optional[str] = Field(
        None, description="Directory for output artifacts"
    )
    verbose: bool = Field(False, description="Enable verbose logging")

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Experiment name must not be empty")
        return v.strip()


class RenderConfig(BaseModel):
    """Configuration for rendering visualizations.

    Specifies the plot type, layout options, and output path used by
    visualization renderers (Matplotlib, Plotly, Console, etc.).

    Attributes:
        plot_type: Type of plot (line, scatter, bar, histogram, surface).
        title: Optional plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        figsize: Figure dimensions as (width, height) in inches.
        dpi: Image resolution in dots per inch.
        colormap: Matplotlib-compatible colormap name.
        output_path: Optional output file path override.
    """

    plot_type: str = Field("line", description="Plot type (line/scatter/bar/histogram/surface)")
    title: Optional[str] = Field(None, description="Plot title")
    xlabel: Optional[str] = Field(None, description="X-axis label")
    ylabel: Optional[str] = Field(None, description="Y-axis label")
    figsize: Tuple[float, float] = Field((8.0, 5.0), description="Figure size (width, height)")
    dpi: int = Field(150, description="Image resolution")
    colormap: str = Field("viridis", description="Color scheme")
    output_path: Optional[str] = Field(None, description="Output file path override")


# ──────────────────────────────────────────────
#  Data models
# ──────────────────────────────────────────────


class InputData(BaseModel, Generic[T]):
    """Generic input data schema for pipeline stages.

    Attributes:
        data: The raw input payload (type varies by stage).
        metadata: Arbitrary metadata attached to the input.
        timestamp: When this input was created.
        columns: Optional column / feature names.
        index: Optional row index labels.
    """

    data: T = Field(..., description="Raw input payload")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Input metadata"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    columns: Optional[List[str]] = Field(None, description="Column / feature names")
    index: Optional[List[Any]] = Field(None, description="Row index labels")

    @property
    def n_samples(self) -> int:
        """Number of samples (rows) in the data."""
        if hasattr(self.data, "shape"):
            return self.data.shape[0]
        if isinstance(self.data, list):
            return len(self.data)
        return 0

    @property
    def n_features(self) -> int:
        """Number of features (columns) in the data."""
        if hasattr(self.data, "shape") and len(self.data.shape) >= 2:
            return self.data.shape[1]
        return 1

    @property
    def shape(self) -> Tuple[int, ...]:
        """Shape of the underlying data array."""
        if hasattr(self.data, "shape"):
            return self.data.shape
        if isinstance(self.data, list):
            return (len(self.data),)
        return (0,)


class OutputData(BaseModel, Generic[T]):
    """Generic output data schema produced by pipeline stages.

    Stores both the raw (pre-stage) and processed (post-stage) data,
    enabling downstream introspection and debugging.

    Attributes:
        raw: Original input data before stage processing.
        processed: Data after stage processing.
        metadata: Processing metadata including timing and stage info.
    """

    raw: T = Field(..., description="Original input data")
    processed: Optional[T] = Field(None, description="Processed output data")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Processing metadata"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Output creation timestamp",
    )


# ──────────────────────────────────────────────
#  Result models
# ──────────────────────────────────────────────


class StageResult(BaseModel):
    """Result from a single pipeline stage execution.

    Carries detailed metadata including timing, status, and optional errors.

    Attributes:
        stage_name: Name of the stage that produced this result.
        stage_type: Type identifier of the stage.
        status: Execution status.
        duration_ms: Execution time in milliseconds.
        started_at: ISO-formatted start timestamp.
        completed_at: ISO-formatted completion timestamp.
        error: Error message if the stage failed.
        metadata: Arbitrary result metadata produced by the stage.
    """

    stage_name: str = Field(..., description="Stage name")
    stage_type: str = Field(..., description="Stage type identifier")
    status: StageStatus = Field(StageStatus.PENDING, description="Execution status")
    duration_ms: float = Field(0.0, description="Duration in milliseconds")
    started_at: Optional[str] = Field(None, description="Start timestamp (ISO)")
    completed_at: Optional[str] = Field(None, description="Completion timestamp (ISO)")
    error: Optional[str] = Field(None, description="Error message on failure")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Stage-specific result metadata"
    )


class PipelineResult(BaseModel):
    """Complete result from a full pipeline execution.

    Aggregates per-stage results and provides top-level summary metrics.

    Attributes:
        experiment_name: Name of the experiment / pipeline.
        status: Overall pipeline status.
        total_duration_ms: Total end-to-end execution time.
        stages: Ordered list of per-stage results.
        started_at: ISO-formatted pipeline start timestamp.
        completed_at: ISO-formatted pipeline completion timestamp.
        output: Final output data produced by the last stage (if any).
        metadata: Pipeline-level metadata.
    """

    experiment_name: str = Field("experiment", description="Experiment name")
    status: PipelineStatus = Field(
        PipelineStatus.PENDING, description="Overall pipeline status"
    )
    total_duration_ms: float = Field(0.0, description="Total duration in milliseconds")
    stages: List[StageResult] = Field(
        default_factory=list, description="Per-stage results in execution order"
    )
    started_at: Optional[str] = Field(None, description="Start timestamp (ISO)")
    completed_at: Optional[str] = Field(None, description="Completion timestamp (ISO)")
    output: Optional[Any] = Field(None, description="Final pipeline output")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Pipeline-level metadata"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_name": "my-experiment",
                "status": "completed",
                "total_duration_ms": 1234.56,
                "stages": [
                    {
                        "stage_name": "loader",
                        "stage_type": "data_loader",
                        "status": "completed",
                        "duration_ms": 100.5,
                    }
                ],
            }
        }
    )

    @property
    def success_count(self) -> int:
        """Number of stages that completed successfully."""
        return sum(
            1
            for s in self.stages
            if s.status == StageStatus.COMPLETED or s.status == StageStatus.SKIPPED
        )

    @property
    def failure_count(self) -> int:
        """Number of stages that failed."""
        return sum(1 for s in self.stages if s.status == StageStatus.FAILED)

    @property
    def total_stages(self) -> int:
        """Total number of stages in the pipeline (excluding sub-pipelines)."""
        return len(self.stages)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to a plain dictionary (JSON-compatible)."""
        return self.model_dump(mode="json")


# ──────────────────────────────────────────────
#  Timing utility
# ──────────────────────────────────────────────


class Timer:
    """Simple context-manager timer for measuring execution duration.

    Usage:
        with Timer() as timer:
            do_something()
        print(f"Took {timer.duration_ms:.2f} ms")
    """

    def __init__(self) -> None:
        self._start: float = 0.0
        self._end: float = 0.0
        self.duration_ms: float = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self._end = time.perf_counter()
        self.duration_ms = (self._end - self._start) * 1000.0
