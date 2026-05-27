"""Configuration loading for experiment-engine pipelines.

Supports loading experiment configurations from YAML/JSON files, merging
with sensible defaults, and overriding values via CLI arguments.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from experiment_engine.models import ExperimentConfig, PipelineStageConfig

logger = logging.getLogger("experiment_engine.config")

# Default configuration used when no config file is provided.
_DEFAULT_CONFIG: dict[str, Any] = {
    "name": "default_experiment",
    "description": "Default experiment configuration",
    "version": "1.0",
    "stages": [],
    "global_params": {},
    "output_dir": None,
    "verbose": False,
}


def _read_file(path: str) -> str:
    """Read a file and return its contents as a string.

    Args:
        path: Absolute or relative file path.

    Returns:
        File contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    path_obj = Path(path).expanduser().resolve()
    if not path_obj.exists():
        raise FileNotFoundError(f"Config file not found: {path_obj}")
    return path_obj.read_text(encoding="utf-8")


def _parse_json(content: str, source: str) -> dict[str, Any]:
    """Parse JSON string into a dictionary.

    Args:
        content: JSON string content.
        source: Label for error messages (e.g., file path).

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If the content is not valid JSON.
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {source}: {exc}") from exc


def _parse_yaml(content: str, source: str) -> dict[str, Any]:
    """Parse YAML string into a dictionary.

    Uses the ``yaml`` (PyYAML) library if available. Falls back to JSON parsing
    if YAML is not installed.

    Args:
        content: YAML string content.
        source: Label for error messages (e.g., file path).

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If the content is not valid YAML.
        RuntimeError: If PyYAML is not installed.
    """
    try:
        import yaml
    except ImportError:
        raise RuntimeError(
            "PyYAML is required to load YAML config files. "
            "Install it with: pip install pyyaml"
        ) from None

    try:
        parsed = yaml.safe_load(content)
        if not isinstance(parsed, dict):
            raise ValueError(
                f"YAML root must be a mapping (dict), got {type(parsed).__name__}"
            )
        return parsed
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {source}: {exc}") from exc


def _detect_format(path: str) -> str:
    """Detect config file format from its extension.

    Args:
        path: File path.

    Returns:
        ``"json"`` or ``"yaml"``.

    Raises:
        ValueError: If the extension is not recognised.
    """
    ext = Path(path).suffix.lower()
    if ext in (".json",):
        return "json"
    if ext in (".yaml", ".yml"):
        return "yaml"
    raise ValueError(
        f"Unsupported config file format: {ext!r}. Supported: .json, .yaml, .yml"
    )


# ──────────────────────────────────────────────
#  Core loading functions
# ──────────────────────────────────────────────


def load_config(path: str) -> ExperimentConfig:
    """Load an experiment configuration from a file.

    Supports JSON (``.json``) and YAML (``.yaml`` / ``.yml``) formats.
    The file is read, parsed, validated against :class:`ExperimentConfig`,
    and merged with default values.

    Args:
        path: Path to the configuration file.

    Returns:
        A validated :class:`ExperimentConfig` instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format or content is invalid.
        ValidationError: If the config data fails Pydantic validation.

    Example:
        >>> config = load_config("experiments/my_exp.yaml")
        >>> config.name
        'my_experiment'
    """
    content = _read_file(path)
    fmt = _detect_format(path)

    data = _parse_json(content, path) if fmt == "json" else _parse_yaml(content, path)

    # Merge with defaults
    merged = merge_defaults(data)

    from pydantic import ValidationError

    try:
        return ExperimentConfig(**merged)
    except ValidationError:
        logger.error("Config validation failed for %s", path)
        raise


def load_config_from_dict(data: dict[str, Any]) -> ExperimentConfig:
    """Load an experiment configuration from an in-memory dictionary.

    Useful for programmatic configuration without a file on disk.

    Args:
        data: Dictionary containing configuration fields.

    Returns:
        A validated :class:`ExperimentConfig` instance.

    Raises:
        ValidationError: If the data fails Pydantic validation.
    """
    merged = merge_defaults(data)
    return ExperimentConfig(**merged)


def merge_defaults(config: dict[str, Any]) -> dict[str, Any]:
    """Merge a configuration dictionary with system defaults.

    Missing top-level keys are filled from the default configuration.
    Nested keys inside ``global_params`` and individual ``stages`` entries
    are NOT deep-merged (only top-level keys are filled).

    Args:
        config: Input configuration dictionary (may be partial).

    Returns:
        A new dictionary with all required keys present.
    """
    merged = dict(_DEFAULT_CONFIG)
    merged.update(config)
    return merged


# ──────────────────────────────────────────────
#  CLI argument overrides
# ──────────────────────────────────────────────


def apply_cli_overrides(
    config: ExperimentConfig,
    overrides: dict[str, Any],
) -> ExperimentConfig:
    """Override experiment config fields with CLI argument values.

    Supports simple key-value overrides and dotted-path overrides for
    nested fields (e.g., ``global_params.learning_rate=0.01``).

    Args:
        config: Base configuration to override.
        overrides: Dictionary of override key-value pairs.

    Returns:
        A new :class:`ExperimentConfig` with overrides applied.

    Example:
        >>> config = load_config("config.yaml")
        >>> config = apply_cli_overrides(config, {
        ...     "name": "run-2",
        ...     "stages.0.params.threshold": 0.5,
        ... })
    """
    # Convert to dict for mutation
    data = config.model_dump()

    for key, value in overrides.items():
        _set_nested(data, key, value)

    return ExperimentConfig(**data)


def _set_nested(d: dict[str, Any], dotted_path: str, value: Any) -> None:
    """Set a value in a nested dictionary using a dotted path.

    Args:
        d: The dictionary to mutate.
        dotted_path: Dot-separated key path (e.g. ``"stages.0.params.x"``).
        value: Value to set at the target location.
    """
    keys = dotted_path.split(".")
    target = d

    for i, key in enumerate(keys):
        if i == len(keys) - 1:
            target[key] = value
        else:
            # Parse integer index for list access
            try:
                idx = int(key)
                if not isinstance(target, list):
                    raise ValueError(f"Expected list at path prefix {key!r}")
                # Ensure list is long enough
                while len(target) <= idx:
                    target.append({})
                target = target[idx]
            except (ValueError, TypeError):
                target = target.setdefault(key, {})


# ──────────────────────────────────────────────
#  Convenience helpers
# ──────────────────────────────────────────────


def list_stages_from_config(config: ExperimentConfig) -> list[str]:
    """Return the names of all enabled stages in a configuration.

    Args:
        config: Experiment configuration.

    Returns:
        List of enabled stage names.
    """
    return [s.name for s in config.stages if s.enabled]


def config_to_dict(config: ExperimentConfig) -> dict[str, Any]:
    """Serialize an :class:`ExperimentConfig` to a plain dictionary.

    Args:
        config: The configuration to serialize.

    Returns:
        JSON-compatible dictionary representation.
    """
    return config.model_dump(mode="json")


def generate_example_config(path: str, fmt: str = "yaml") -> str:
    """Generate an example configuration file and write it to disk.

    Args:
        path: Output file path.
        fmt: Format (``"yaml"`` or ``"json"``).

    Returns:
        The path to the written file.

    Raises:
        ValueError: If the format is unsupported.
    """
    example_stages = [
        PipelineStageConfig(
            name="load_data",
            stage_type="csv_loader",
            enabled=True,
            params={"file_path": "data/input.csv", "delimiter": ","},
        ),
        PipelineStageConfig(
            name="transform",
            stage_type="data_transformer",
            enabled=True,
            params={"normalize": True, "scale": 1.0},
        ),
        PipelineStageConfig(
            name="analyze",
            stage_type="analyzer",
            enabled=True,
            params={"method": "pca", "components": 3},
        ),
        PipelineStageConfig(
            name="visualize",
            stage_type="visualizer",
            enabled=True,
            params={"output_format": "png", "dpi": 150},
        ),
    ]

    config = ExperimentConfig(
        name="example_experiment",
        description="Example experiment configuration",
        stages=example_stages,
        global_params={"seed": 42, "device": "cpu"},
        output_dir="./output",
        verbose=True,
    )

    data = config.model_dump(mode="python")

    path_obj = Path(path).expanduser().resolve()
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "json":
        content = json.dumps(data, indent=2, default=str)
    elif fmt == "yaml":
        try:
            import yaml
        except ImportError:
            raise RuntimeError(
                "PyYAML is required to generate YAML config files"
            ) from None

        content = yaml.dump(data, default_flow_style=False, sort_keys=False)
    else:
        raise ValueError(f"Unsupported format: {fmt!r}")

    path_obj.write_text(content, encoding="utf-8")
    logger.info("Example config written to %s", path_obj)
    return str(path_obj)
