"""CLI interface for experiment-engine. Defines the `run` command using click."""

import sys
import click
from pathlib import Path


@click.group()
@click.version_option(version="0.1.0", prog_name="experiment-engine")
def cli():
    """experiment-engine: modular algorithm experimentation framework.

    Pipeline: Input → Computation → Visualization → Report
    """
    pass


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), required=True,
              help="Path to experiment configuration file (YAML/JSON)")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Output directory for results")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Enable verbose logging")
def run(config, output, verbose):
    """Run an experiment with the given configuration.

    Loads the experiment config, executes the pipeline (input → computation
    → visualization → report), and writes outputs to the specified directory.
    """
    from experiment_engine.config import load_config
    from experiment_engine.pipeline import Pipeline
    from experiment_engine.io import get_reader
    from experiment_engine.io.sources import FileDataSource, GeneratorDataSource
    from experiment_engine.io.exporters import CSVExporter, JSONExporter
    from experiment_engine.models import ExportConfig
    from experiment_engine.viz.console import ConsoleRenderer
    from rich.console import Console
    from rich.table import Table
    from pathlib import Path

    console = Console()
    console.print("[bold cyan]experiment-engine[/] — pipeline run starting...")

    # Load configuration
    cfg = load_config(Path(config))
    if output:
        cfg.output_dir = output

    # Build and configure pipeline from config stages
    pipeline = Pipeline(name=cfg.name, verbose=verbose)
    pipeline.configure_from_config(cfg)

    # ── Data loading ──────────────────────────────────────────
    # Find the first enabled stage whose params contain a "format" key
    input_data = None
    load_stage = None
    for sc in cfg.stages:
        if sc.enabled and "format" in sc.params:
            load_stage = sc
            break

    if load_stage is not None:
        fmt = load_stage.params.get("format", "csv")
        path = load_stage.params.get("path")
        reader = get_reader(fmt)

        # Forward params to the reader, stripping format/path
        reader_kwargs = {
            k: v for k, v in load_stage.params.items()
            if k not in ("format", "path")
        }

        if fmt == "synthetic":
            source = GeneratorDataSource(reader)
            input_data = source.load(**reader_kwargs)
        elif path:
            source = FileDataSource(reader, path)
            input_data = source.load(**reader_kwargs)
        else:
            input_data = reader.read(path, **reader_kwargs)

        input_desc = input_data.shape
        if hasattr(input_data, "n_samples"):
            input_desc = f"{input_data.n_samples} × {input_data.n_features}"
        console.print(f"[green]✓[/] Data loaded: {input_desc}")

        # Print data summary via ConsoleRenderer
        try:
            renderer = ConsoleRenderer()
            renderer.render(input_data)
        except Exception as exc:
            console.print(f"[dim]ConsoleRenderer skipped: {exc}[/]")
    else:
        console.print("[yellow]⚠[/] No data-loading stage found in configuration.")

    # ── Pipeline execution ────────────────────────────────────
    results = pipeline.run(data=input_data, experiment_name=cfg.name)

    # ── Export results ────────────────────────────────────────
    if cfg.output_dir and results.output is not None:
        out_dir = Path(cfg.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        export_formats = [
            ("csv", CSVExporter),
            ("json", JSONExporter),
        ]
        for ext, exp_cls in export_formats:
            exporter = exp_cls()
            export_cfg = ExportConfig(
                format=ext,
                output_path=str(out_dir / f"results.{ext}"),
                include_index=True,
                pretty=True,
            )
            try:
                out_path = exporter.export(results.output, export_cfg)
                console.print(f"[green]✓[/] Results exported: {out_path}")
            except Exception as exc:
                console.print(f"[yellow]⚠[/] Export .{ext} failed: {exc}")

    # Show stage timing table (already printed by _log_summary inside pipeline.run)
    console.print(f"[green]✓[/] Experiment completed. Status: {results.status.value}")


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), required=True,
              help="Path to experiment configuration file")
def validate(config):
    """Validate an experiment configuration file without running it."""
    from experiment_engine.config import load_config
    from rich.console import Console
    from rich.markup import escape

    console = Console()
    try:
        cfg = load_config(Path(config))
        console.print(f"[green]✓[/] Configuration is valid")
        enabled_stages = [s.name for s in cfg.stages if s.enabled]
        console.print(f"     Name: {cfg.name}")
        console.print(f"     Stages: {len(cfg.stages)} total")
        if enabled_stages:
            console.print(f"     Enabled: {', '.join(enabled_stages)}")
        console.print(f"     Output dir: {cfg.output_dir or '(default)'}")
        console.print(f"     Verbose: {cfg.verbose}")
    except Exception as exc:
        console.print(f"[red]✗[/] Invalid configuration: {escape(str(exc))}")
        sys.exit(1)


@cli.command()
def list_plugins():
    """List all registered pipeline stage plugins."""
    from experiment_engine.plugins import PluginRegistry
    from rich.console import Console
    from rich.table import Table

    console = Console()
    registry = PluginRegistry.get_instance()
    stages = registry.list_stages()

    if not stages:
        console.print("[yellow]No plugins registered yet.[/]")
        return

    table = Table(title="Registered Pipeline Stages", header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Class")
    table.add_column("Module")
    table.add_column("Enabled")

    for name in sorted(stages.keys()):
        cls = stages[name]
        enabled = "[green]✓[/]" if registry.is_enabled(name) else "[dim]—[/]"
        table.add_row(name, cls.__name__, cls.__module__, enabled)

    console.print(table)


main = cli

if __name__ == "__main__":
    cli()
