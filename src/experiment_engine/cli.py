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
    from rich.console import Console

    console = Console()
    console.print("[bold cyan]experiment-engine[/] — pipeline run starting...")

    # Load configuration
    cfg = load_config(Path(config))
    if output:
        cfg.output_dir = output

    # Execute pipeline
    pipeline = Pipeline(name=cfg.name, verbose=verbose)
    data = None  # Placeholder — actual data loading will be implemented
    results = pipeline.run(data=data)

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
