# experiment-engine

> A modular algorithm experimentation framework: **input → computation → visualization → report**.

Experiment-engine provides a clean, extensible pipeline for running algorithmic experiments. It follows a modular architecture with four core stages:

1. **Input** — Load, validate, and transform data from multiple sources (CSV, JSON, YAML, databases)
2. **Computation** — Execute user-defined algorithms or registered plugins against the prepared data
3. **Visualization** — Render results via multiple backends (Matplotlib, Plotly, or custom renderers)
4. **Report** — Aggregate outputs, logs, and metadata into a reproducible experiment record

---

## Features

- **Modular pipeline architecture** — Each stage is independently swappable and testable
- **Plugin system** — Register custom algorithms, data sources, and visualization backends via entry points or runtime discovery
- **Multi-backend visualization** — Render the same data with Matplotlib, Plotly, or both
- **Rich CLI** — Interactive progress bars, colored output, and YAML/JSON config support via `click` + `rich`
- **Pydantic-powered config** — Type-safe experiment configuration with schema validation
- **Reproducible by design** — Every run captures its config, input hash, and output artifacts

---

## Quick Start

### Installation

```bash
# From PyPI
pip install experiment-engine

# Development install
pip install -e ".[dev]"
```

### Running an Experiment

```bash
# Using python -m
python -m experiment_engine run --config configs/config.yaml --input data.csv

# Or using the shorthand CLI
experiment-engine run -c configs/config.yaml -i data.csv
```

### Validate Configuration

```bash
experiment-engine validate -c configs/config.yaml
```

### List Registered Plugins

```bash
experiment-engine list-plugins
```

---

## Pipeline Architecture

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────┐
│  Input   │ →  │ Computation  │ →  │  Visualize   │ →  │ Report  │
│ (Loader) │    │ (Algorithm)  │    │  (Renderer)  │    │ (Output)│
└──────────┘    └──────────────┘    └──────────────┘    └─────────┘
```

Each stage communicates via typed Pydantic models, enabling validation at every boundary. The pipeline follows a strict linear flow:

| Stage | Purpose | Implementation |
|-------|---------|----------------|
| **Input** | Load data from files, stdin, or generators | `io/` — readers, sources |
| **Computation** | Execute algorithms against prepared data | `pipeline.py` — `Stage` ABC |
| **Visualization** | Render results via multiple backends | `viz/` — renderers |
| **Report** | Export outputs to CSV, JSON, HTML | `io/exporters.py` |

---

## Configuration

Experiments are configured via YAML or JSON files:

```yaml
# config.yaml
name: "my-experiment"
description: "Description of the experiment"
version: "1.0"
stages:
  - name: load_data
    stage_type: csv_loader
    enabled: true
    params:
      format: csv
      path: data/input.csv
  - name: transform
    stage_type: data_transformer
    enabled: true
    params:
      normalize: true
  - name: analyze
    stage_type: analyzer
    enabled: true
    params:
      method: pca
  - name: visualize
    stage_type: visualizer
    enabled: true
    params:
      output_format: png
      dpi: 150
global_params:
  seed: 42
  device: cpu
output_dir: ./output
verbose: true
```

Load it programmatically:

```python
from experiment_engine import load_config

config = load_config("config.yaml")
print(config.name)  # "my-experiment"
```

---

## Plugin System

Register custom algorithms and visualizers using the `@register_stage` decorator:

```python
from experiment_engine.plugins import register_stage
from experiment_engine.pipeline import Stage

@register_stage("my_custom_algo")
class MyCustomAlgorithm(Stage):
    def process(self, data):
        # Custom computation logic
        return data
```

Stages can also be registered manually:

```python
from experiment_engine.plugins import PluginRegistry

registry = PluginRegistry.get_instance()
registry.register("csv_loader", CSVLoaderStage)
```

### Plugin Discovery

Plugins are discovered via three mechanisms (in order of priority):

1. **Entry points** — `experiment_engine.algorithms`, `experiment_engine.loaders`, `experiment_engine.visualizers` in `pyproject.toml`
2. **Runtime registration** — Using `@register_stage("name")` or `registry.register("name", MyClass)`
3. **Directory scanning** — Auto-discover plugins from a directory with `PluginLoader`

---

## Programmatic Usage

```python
from experiment_engine import Pipeline, Stage
from experiment_engine.config import load_config
from experiment_engine.models import InputData, ExperimentConfig

# Load configuration
config = load_config("experiments/my_exp.yaml")

# Build and run pipeline
pipeline = Pipeline(name="my-pipeline", verbose=True)
pipeline.configure_from_config(config)
result = pipeline.run(data=InputData(data=...))

print(f"Status: {result.status}")
print(f"Duration: {result.total_duration_ms:.1f} ms")
```

---

## Project Structure

```
experiment-engine/
├── src/
│   └── experiment_engine/
│       ├── __init__.py       # Package version & exports
│       ├── __main__.py       # CLI entry point (python -m)
│       ├── cli.py            # Click-based CLI commands
│       ├── config.py         # Config loader, validator, resolver
│       ├── models.py         # Pydantic data models
│       ├── pipeline.py       # Pipeline & Stage ABC
│       ├── plugins.py        # Plugin registry & discovery
│       ├── core/             # Pipeline orchestration re-exports
│       ├── io/               # Data readers, sources, exporters
│       └── viz/              # Visualization backends
├── tests/                    # Unit & integration tests
├── configs/                  # Example configurations
├── examples/                 # Runnable example scripts
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy src/

# Lint
ruff check src/

# Build documentation locally
pip install mkdocs mkdocs-material mkdocstrings[python]
mkdocs serve
```

---

## API Reference

See the [API Reference](api/experiment_engine.md) for detailed documentation of all modules and classes.

---

## License

MIT
