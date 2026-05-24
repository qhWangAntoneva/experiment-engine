# Changelog

All notable changes to the **experiment-engine** project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-16

### Added

#### Core Foundation
- **Project scaffolding** — `pyproject.toml`, `src/` package layout, `README.md` architecture overview
- **Pydantic data models** — `ExperimentConfig`, `PipelineStageConfig`, `InputData`, `OutputData`, `StageResult`, `PipelineResult`, `StageStatus`, `PipelineStatus`, `Timer`
- **Pipeline + Stage ABC** — `setup` / `process` / `teardown` lifecycle hooks, nested sub-pipeline support, `run()` method with Rich progress bars and summary tables
- **Plugin system** — `PluginRegistry` singleton, `@register_stage` decorator, `PluginLoader` directory scanner, `BasePlugin` metadata class
- **Configuration loading** — `load_config()` (YAML/JSON), `merge_defaults()`, `apply_cli_overrides()` with dot-path notation, `generate_example_config()`
- **Click CLI** — `run`, `validate`, `list-plugins` commands
- **OpenWolf context management** integration (`.wolf/` directory, `CLAUDE.md`)
- **git-auto-push.sh** script and `.gitignore` configuration

#### I/O Module
- **Data sources** — `StdinDataSource`, `FileDataSource`, `SyntheticReader`, `CsvSource` covering all input strategies
- **API alignment** — `InputData` model integration, proper index parameter on `SyntheticReader`, consistent export of all data source types
- **115 unit tests** in `tests/test_io.py`

#### Visualization Module
- **Rendering backends** — `ConsoleRenderer`, `MatplotlibRenderer`, `PlotlyRenderer` with unified interface
- **Matplotlib & Plotly integrations** — fixed missing `plt` / `go` imports and `ConsoleRenderer` signature
- **81 unit tests** in `tests/test_viz.py`

#### Quality Infrastructure
- **Ruff + mypy configuration** in `pyproject.toml` — automated fix of 252 lint errors, discovery and fix of 3 runtime bugs
- **Pre-commit hooks** (`.pre-commit-config.yaml`) — Ruff linting, trailing whitespace, YAML/JSON validation
- **Integration tests** — 34 tests in `tests/test_integration.py`

#### Examples
- **Sample data** — `examples/data.csv`
- **Run script** — `examples/run_experiment.py`

#### Packaging
- **PyPI entry points** configuration in `pyproject.toml`

### Changed
- `configs/config.yaml` — migrated from legacy format to `stages` list format
- CLI `run` command — integrated `io/` module for data loading and `viz/` module for result rendering
- Project URLs — updated from example placeholders to the real repository addresses

### Fixed
- Config format incompatibility between old pipeline format and new `stages` list schema
- CLI `run` command missing I/O and visualization integration
- 3 runtime bugs discovered during Ruff + mypy linting pass
- `ConsoleRenderer` API signature mismatch
- Missing `matplotlib.pyplot` import in `MatplotlibRenderer`
- Missing `plotly.graph_objects` import in `PlotlyRenderer`
- `StdinDataSource` not exported in `io/` module `__init__.py`
- `SyntheticReader` missing `index` parameter

---

**Test status:** 295 passed, 6 xfailed
**Git commits:** 3 local commits (Phase 2, Q1+Q4, Q2) — pending push to remote
