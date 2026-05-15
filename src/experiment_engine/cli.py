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
@click.option("--input", "-i", type=click.Path(exists=True), default=None,
              help="Path to input data file")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Output directory for results")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Enable verbose logging")
def run(config, input, output, verbose):
    """Run an experiment with the given configuration.

    Loads the experiment config, executes the pipeline (input → computation
    → visualization → report), and writes outputs to the specified directory.
    """
    from experiment_engine.config import load_config
    from experiment_engine.core import Pipeline
    from rich.console import Console

    console = Console()
    console.print("[bold cyan]experiment-engine[/] — pipeline run starting...")

    # Load configuration
    cfg = load_config(Path(config))
    if input:
        cfg.input.path = input
    if output:
        cfg.output.path = output

    # Execute pipeline
    pipeline = Pipeline(name=cfg.experiment.name, verbose=verbose)
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
        console.print(f"     Input: {cfg.input.format} → {cfg.input.path}")
        console.print(f"     Algorithm: {cfg.algorithm.name}")
        console.print(f"     Visualization backends: {cfg.visualization.backends}")
    except Exception as exc:
        console.print(f"[red]✗[/] Invalid configuration: {escape(str(exc))}")
        sys.exit(1)


@cli.command()
def list_plugins():
    """List all registered plugins (algorithms, loaders, visualizers)."""
    from experiment_engine.plugins import registry
    from rich.console import Console
    from rich.table import Table

    console = Console()

    for kind, plugins in [("Algorithms", registry.get_algorithms()),
                           ("Loaders", registry.get_loaders()),
                           ("Visualizers", registry.get_visualizers())]:
        if not plugins:
            continue
        table = Table(title=kind)
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        for name, desc in sorted(plugins.items()):
            table.add_row(name, desc)
        console.print(table)
        console.print()


main = cli
