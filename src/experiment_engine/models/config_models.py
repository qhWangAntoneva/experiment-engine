"""Schema-oriented config models for the experiment pipeline.

These models define the YAML/JSON config schema for the
input → computation → visualization → report pipeline.
They are separate from the core Pipeline/Stage domain models
in ``experiment_engine.models``.
"""

from __future__ import annotations
from typing import Any

from pydantic import BaseModel, Field


class InputConfig(BaseModel):
    """Configuration for the input data loading stage."""
    format: str = Field(default="csv", description="Data format (csv, json, yaml, ...)")
    path: str = Field(default="", description="Path to input data file")
    field_schema: dict[str, Any] = Field(default_factory=dict, description="Expected column/field schema")


class AlgorithmConfig(BaseModel):
    """Configuration for the computation stage."""
    name: str = Field(default="", description="Registered algorithm name")
    params: dict[str, Any] = Field(default_factory=dict, description="Algorithm parameters")


class VisualizationConfig(BaseModel):
    """Configuration for the visualization stage."""
    backends: list[str] = Field(default_factory=lambda: ["matplotlib"], description="Visualization backends to use")
    output_dir: str = Field(default="results/", description="Output directory for figures")


class OutputConfig(BaseModel):
    """Configuration for output / report generation."""
    path: str = Field(default="results/", description="Root output directory")


class PipelineConfig(BaseModel):
    """Complete pipeline configuration assembled from sub-configs.

    This is the top-level schema for experiment YAML/JSON configs.
    """
    input: InputConfig = Field(default_factory=InputConfig)
    algorithm: AlgorithmConfig = Field(default_factory=AlgorithmConfig)
    visualization: VisualizationConfig = Field(default_factory=VisualizationConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


class ExperimentResult(BaseModel):
    """Container for experiment run results and metadata."""
    pipeline_config: PipelineConfig = Field(default_factory=PipelineConfig)
    metrics: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
