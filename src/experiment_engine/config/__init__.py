"""Configuration loader, validator, and resolver.

Supports YAML and JSON config files with schema validation via Pydantic models.
"""

from __future__ import annotations
from pathlib import Path

import yaml

from experiment_engine.models.config_models import PipelineConfig


def load_config(path: Path) -> PipelineConfig:
    """Load and validate an experiment configuration from a YAML/JSON file.

    Args:
        path: Path to the configuration file (.yaml, .yml, or .json).

    Returns:
        A validated PipelineConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML is malformed.
        pydantic.ValidationError: If the config schema is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    raw: dict = {}
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        with open(path, "r") as f:
            raw = yaml.safe_load(f) or {}
    elif suffix == ".json":
        import json
        with open(path, "r") as f:
            raw = json.load(f) or {}
    else:
        raise ValueError(f"Unsupported config format: {suffix} (use .yaml, .yml, or .json)")

    return PipelineConfig(**raw)
