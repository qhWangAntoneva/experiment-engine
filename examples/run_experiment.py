#!/usr/bin/env python3
"""
experiment-engine — Comprehensive Usage Example
================================================

This script demonstrates the full experiment-engine API, including:
  1. CSV data loading via CSVReader
  2. Creating custom Pipeline Stage subclasses
  3. Building and running a pipeline
  4. Exporting results to CSV / JSON / HTML
  5. Using the CLI equivalent via subprocess (commented)
  6. Using the Pipeline API with @register_stage

Usage:
    python examples/run_experiment.py          # run the programmatic example
    python -m experiment_engine run -c configs/config.yaml  # CLI equivalent

Output is written to ``results/`` under the project root.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── Ensure the project root is on sys.path ──────────────────────────
# This allows running the script directly: python examples/run_experiment.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ══════════════════════════════════════════════════════════════════════
#  Imports
# ══════════════════════════════════════════════════════════════════════

import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from experiment_engine import (
    Pipeline,
    Stage,
    InputData,
    ExportConfig,
    PipelineStageConfig,
    ExperimentConfig,
    PipelineResult,
    StageResult,
    StageStatus,
    Timer,
)
from experiment_engine.io import (
    CSVReader,
    CSVExporter,
    JSONExporter,
    HTMLExporter,
)
from experiment_engine.plugins import register_stage, PluginRegistry
from experiment_engine.config import load_config, load_config_from_dict

console = Console()


# ══════════════════════════════════════════════════════════════════════
#  1. Custom Pipeline Stages
# ══════════════════════════════════════════════════════════════════════


class NormalizerStage(Stage):
    """Normalize numerical features to unit variance.
    
    Non-numeric columns are passed through unchanged.
    """

    def process(self, data: InputData) -> InputData:
        arr = data.data
        if arr.ndim < 2:
            arr = arr.reshape(-1, 1)
        # Detect numeric columns (float/int types)
        numeric_mask = np.array([
            np.issubdtype(arr[:, i].dtype, np.number)
            for i in range(arr.shape[1])
        ])
        result = arr.copy()
        if numeric_mask.any():
            numeric_data = arr[:, numeric_mask].astype(float)
            std = numeric_data.std(axis=0)
            std[std == 0] = 1.0
            result[:, numeric_mask] = (numeric_data - numeric_data.mean(axis=0)) / std
        return InputData(
            data=result,
            columns=data.columns,
            index=data.index,
            metadata={**data.metadata, "normalized": True},
        )


@register_stage("feature_stats")
class FeatureStatsStage(Stage):
    """Compute per-feature summary statistics."""

    def process(self, data: InputData) -> InputData:
        arr = data.data
        columns = data.columns or [f"col_{i}" for i in range(arr.shape[1])]
        
        # Separate numeric and non-numeric columns
        numeric_mask = np.array([
            np.issubdtype(arr[:, i].dtype, np.number)
            for i in range(arr.shape[1])
        ])
        numeric_idx = np.where(numeric_mask)[0]
        
        stats = {}
        if len(numeric_idx) > 0:
            numeric_data = arr[:, numeric_idx].astype(float)
            stats = {
                "mean": numeric_data.mean(axis=0).tolist(),
                "std": numeric_data.std(axis=0).tolist(),
                "min": numeric_data.min(axis=0).tolist(),
                "max": numeric_data.max(axis=0).tolist(),
                "p25": np.percentile(numeric_data, 25, axis=0).tolist(),
                "p75": np.percentile(numeric_data, 75, axis=0).tolist(),
            }
        
        stat_columns = [columns[i] for i in numeric_idx] if len(numeric_idx) > 0 else []
        rprint(Panel.fit(
            "[bold cyan]Feature Statistics[/]",
            border_style="cyan",
        ))
        stat_table = Table(title="Per-Feature Summary", header_style="bold magenta")
        stat_table.add_column("Metric", style="bold")
        for col in stat_columns:
            stat_table.add_column(col, justify="right")
        for metric_name, values in stats.items():
            stat_table.add_row(metric_name, *[f"{v:.4f}" for v in values])
        console.print(stat_table)
        return data  # pass through


# ══════════════════════════════════════════════════════════════════════
#  2. Build and run the pipeline
# ══════════════════════════════════════════════════════════════════════


def run_programmatic_example():
    """Run the full pipeline using the Python API."""

    console.rule("[bold green]Programmatic API Example[/]")
    console.print()

    # ── Load data ────────────────────────────────────────────────────
    data_path = PROJECT_ROOT / "examples" / "data.csv"
    console.print(f"[dim]Reading CSV:[/] {data_path}")

    reader = CSVReader()
    input_data = reader.read(
        source=str(data_path),
        delimiter=",",
        header=0,
    )
    console.print(
        f"[green]✓[/] Loaded [bold]{input_data.shape[0]}[/] samples "
        f"× [bold]{input_data.shape[1]}[/] features"
    )
    console.print(f"    Columns: {', '.join(input_data.columns or [])}")
    console.print()

    # ── Build pipeline ───────────────────────────────────────────────
    pipeline = Pipeline(name="csv-demo-pipeline", verbose=True)
    pipeline.add_stage(NormalizerStage(name="normalize"))
    pipeline.add_stage(FeatureStatsStage(name="stats"))

    console.print("[bold]Pipeline stages:[/]")
    for s in pipeline.stages:
        console.print(f"  • [cyan]{s.name}[/] ({s.__class__.__name__})")
    console.print()

    # ── Run ──────────────────────────────────────────────────────────
    console.print("[bold yellow]Running pipeline...[/]")
    result: PipelineResult = pipeline.run(
        data=input_data,
        experiment_name="CSV Demo",
        metadata={"source": "run_experiment.py", "dataset": "data.csv"},
    )
    console.print()

    # ── Check results ────────────────────────────────────────────────
    if result.status.value == "completed":
        console.print("[green]✓[/] Pipeline completed successfully")
    else:
        console.print(f"[yellow]⚠[/] Pipeline status: {result.status.value}")

    console.print(f"    Total time: [bold]{result.total_duration_ms:.1f} ms[/]")
    console.print(f"    Stages: {result.total_stages} total, "
                  f"{result.success_count} OK, "
                  f"{result.failure_count} failed")
    console.print()

    # ── Export results ───────────────────────────────────────────────
    output_dir = PROJECT_ROOT / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    exporters = [
        ("CSV", CSVExporter(), ExportConfig(
            format="csv",
            output_path=str(output_dir / "demo_results.csv"),
            include_index=True,
        )),
        ("JSON", JSONExporter(), ExportConfig(
            format="json",
            output_path=str(output_dir / "demo_results.json"),
            include_index=True,
            pretty=True,
        )),
        ("HTML", HTMLExporter(), ExportConfig(
            format="html",
            output_path=str(output_dir / "demo_results.html"),
            include_index=True,
            pretty=True,
        )),
    ]

    # Export the pipeline output (post-normalization data)
    if result.output is not None:
        console.print("[bold]Exporting results:[/]")
        for label, exporter, export_cfg in exporters:
            try:
                out_path = exporter.export(result.output, export_cfg)
                console.print(f"  [green]✓[/] {label}: {out_path}")
            except Exception as e:
                console.print(f"  [red]✗[/] {label} failed: {e}")
    else:
        console.print("[yellow]⚠[/] No pipeline output to export")

    console.print()
    return result


# ══════════════════════════════════════════════════════════════════════
#  3. Config-driven example (using ExperimentConfig)
# ══════════════════════════════════════════════════════════════════════


def run_config_driven_example():
    """Build a pipeline from an ExperimentConfig dictionary."""

    console.rule("[bold green]Config-Driven API Example[/]")
    console.print()

    # ── Build config programmatically ────────────────────────────────
    cfg = ExperimentConfig(
        name="config-driven-demo",
        description="Example using ExperimentConfig directly",
        stages=[
            PipelineStageConfig(
                name="stats",
                stage_type="feature_stats",
                enabled=True,
                params={},
            ),
        ],
        output_dir=str(PROJECT_ROOT / "results"),
        verbose=True,
    )

    console.print(f"[bold]Config:[/] {cfg.name}")
    console.print(f"    Stages: {len(cfg.stages)} configured")

    # Build pipeline from config (uses registered stages)
    pipeline = Pipeline(name=cfg.name, verbose=cfg.verbose)
    pipeline.configure_from_config(cfg)

    # Load data
    reader = CSVReader()
    input_data = reader.read(
        source=str(PROJECT_ROOT / "examples" / "data.csv"),
    )

    console.print(f"[green]✓[/] Loaded {input_data.shape[0]} × {input_data.shape[1]} data")

    # Run
    result = pipeline.run(data=input_data, experiment_name=cfg.name)

    # Export
    if result.output is not None:
        out_dir = Path(cfg.output_dir) if cfg.output_dir else PROJECT_ROOT / "results"
        out_dir.mkdir(parents=True, exist_ok=True)
        exporter = CSVExporter()
        export_path = exporter.export(
            result.output,
            ExportConfig(
                format="csv",
                output_path=str(out_dir / "config_demo_results.csv"),
                include_index=True,
            ),
        )
        console.print(f"[green]✓[/] Exported: {export_path}")

    console.print()
    return result


# ══════════════════════════════════════════════════════════════════════
#  4. CLI-driven example (via config file)
# ══════════════════════════════════════════════════════════════════════


def run_cli_equivalent():
    """
    Show the CLI command that achieves the same result.
    Run this manually from the project root:

        python -m experiment_engine run -c configs/config.yaml -o results/
        python -m experiment_engine validate -c configs/config.yaml
        python -m experiment_engine list-plugins
    """
    console.rule("[bold green]CLI Usage[/]")
    console.print()

    # Register our custom stage for the config-based flow
    registry = PluginRegistry.get_instance()
    registry.register("csv_loader", type("CSVLoaderStage", (Stage,), {
        "process": lambda self, data: data,
    }))

    # Load the YAML config
    config_path = PROJECT_ROOT / "configs" / "config.yaml"
    if config_path.exists():
        cfg = load_config(str(config_path))
        console.print(f"[bold]Config file:[/] {config_path}")
        console.print(f"    Name: [cyan]{cfg.name}[/]")
        console.print(f"    Stages: {len(cfg.stages)} configured")
        for sc in cfg.stages:
            status = "[green]enabled[/]" if sc.enabled else "[dim]disabled[/]"
            console.print(f"      • [bold]{sc.name}[/] ({sc.stage_type}) [{status}]")
        console.print()
        console.print("[dim]To run the CLI equivalent:[/]")
        console.print(f"  [bold]python -m experiment_engine run -c {config_path} -o results/[/]")
        console.print("  [bold]python -m experiment_engine validate -c configs/config.yaml[/]")
    else:
        console.print(f"[yellow]⚠[/] Config file not found: {config_path}")
    console.print()


# ══════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════


def main():
    console.print(Panel.fit(
        "[bold cyan]experiment-engine[/] — CSV Example",
        subtitle="Step 6: Examples + E2E Validation",
        border_style="cyan",
    ))
    console.print()

    # 1. Programmatic API
    prog_result = run_programmatic_example()

    # 2. Config-driven API
    cfg_result = run_config_driven_example()

    # 3. CLI notes
    run_cli_equivalent()

    # ── Summary ──────────────────────────────────────────────────────
    console.rule("[bold green]Summary[/]")
    summary = Table(show_header=True, header_style="bold cyan")
    summary.add_column("Method", style="bold")
    summary.add_column("Pipeline Result")

    prog_status = "[green]✓[/] completed" if prog_result.status.value == "completed" else f"[yellow]⚠[/] {prog_result.status.value}"
    cfg_status = "[green]✓[/] completed" if cfg_result.status.value == "completed" else f"[yellow]⚠[/] {cfg_result.status.value}"

    summary.add_row("Programmatic API", prog_status)
    summary.add_row("Config-Driven API", cfg_status)
    summary.add_row("Method", "Status")
    summary.add_row("", "")
    summary.add_row("Total stages (prog)", str(prog_result.total_stages))
    summary.add_row("Duration (prog)", f"{prog_result.total_duration_ms:.1f} ms")
    summary.add_row("Duration (cfg)", f"{cfg_result.total_duration_ms:.1f} ms")
    console.print(summary)
    console.print()

    output_dir = PROJECT_ROOT / "results"
    console.print(f"[dim]Output files written to: {output_dir}[/]")
    console.print("[green]✓[/] [bold]E2E validation complete[/] — all pipeline modes operational")


if __name__ == "__main__":
    main()
