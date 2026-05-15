# experiment-engine

> A modular algorithm experimentation framework: **input → computation → visualization**.

Experiment-engine provides a clean, extensible pipeline for running algorithmic experiments. It follows a modular architecture with four core stages:

1. **Input** — Load, validate, and transform data from multiple sources (CSV, JSON, YAML, databases)
2. **Computation** — Execute user-defined algorithms or registered plugins against the prepared data
3. **Visualization** — Render results via multiple backends (Matplotlib, Plotly, or custom renderers)
4. **Report** — Aggregate outputs, logs, and metadata into a reproducible experiment record

## Features

- **Modular pipeline architecture** — Each stage is independently swappable and testable
- **Plugin system** — Register custom algorithms, data sources, and visualization backends via entry points or runtime discovery
- **Multi-backend visualization** — Render the same data with Matplotlib, Plotly, or both
- **Rich CLI** — Interactive progress bars, colored output, and YAML/JSON config support via `click` + `rich`
- **Pydantic-powered config** — Type-safe experiment configuration with schema validation
- **Reproducible by design** — Every run captures its config, input hash, and output artifacts

## Quick Start

```bash
# Install
pip install experiment-engine

# Run an experiment
python -m experiment_engine run --config configs/config.yaml --input data.csv
```

Or use the shorthand CLI:

```bash
experiment-engine run -c configs/config.yaml -i data.csv
```

## Project Structure

```
experiment-engine/
├── src/
│   └── experiment_engine/
│       ├── __init__.py       # Package version & exports
│       ├── __main__.py       # CLI entry point (python -m)
│       ├── core/             # Pipeline orchestration & step executors
│       ├── io/               # Data loaders, writers, format adapters
│       ├── viz/              # Visualization backends & figure management
│       ├── plugins/          # Plugin registry, discovery, & base classes
│       ├── models/           # Pydantic data models (config schemas, results)
│       └── config/           # Config loader, validator, & resolver
├── tests/                    # Unit & integration tests
├── configs/                  # Example experiment configurations
├── examples/                 # Runnable example scripts
├── docs/                     # Architecture docs & API reference
└── scripts/                  # Utility scripts (git, CI helpers)
```

## Pipeline Architecture

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────┐
│  Input   │ →  │ Computation  │ →  │  Visualize   │ →  │ Report  │
│ (Loader) │    │ (Algorithm)  │    │  (Renderer)  │    │ (Output)│
└──────────┘    └──────────────┘    └──────────────┘    └─────────┘
```

Each stage communicates via typed Pydantic models, enabling validation at every boundary.

## Configuration

Experiments are configured via YAML files:

```yaml
experiment:
  name: "my-experiment"
  description: "Description of the experiment"

pipeline:
  input:
    format: csv
    path: data/input.csv
    schema:
      columns: [x, y, label]

  algorithm:
    name: linear_regression
    params:
      fit_intercept: true

  visualization:
    backends: [matplotlib, plotly]
    output_dir: results/
```

## Plugin System

Register custom algorithms and visualizers:

```python
from experiment_engine.plugins import register_algorithm

@register_algorithm("my_algo")
class MyAlgorithm:
    def run(self, data, params):
        # Custom computation logic
        return results
```

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
```

## License

MIT
