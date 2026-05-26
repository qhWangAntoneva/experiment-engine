#!/usr/bin/env python3
"""End-to-end QCA Analysis Pipeline with Visualization.

Runs the full pipeline: calibrate -> analyze -> robustness -> counterfactuals ->
report -> visualizations. Or, given a directory with already-generated results
(qca_results.json + fuzzy_data.npz), runs only the visualization step.

Usage:
    # Full pipeline
    uv run python run_pipeline.py --config config.yaml --output-dir qca_output/my_domain

    # Visualization only (post-processing)
    uv run python run_pipeline.py --viz-only --output-dir qca_output/trust
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from rich.console import Console

console = Console()


def run_viz_step(out_dir: str) -> dict[str, str]:
    """Step 6: Generate visualizations from already-computed results.

    Args:
        out_dir: Directory containing qca_results.json and fuzzy_data.npz.

    Returns:
        Dict mapping viz name -> absolute PNG file path.
    """
    console.print("[bold cyan]Step 6/6:[/] Generating visualizations...")

    results_json = os.path.join(out_dir, "qca_results.json")
    fuzzy_npz = os.path.join(out_dir, "fuzzy_data.npz")

    if not os.path.exists(results_json):
        console.print(f"  [yellow]⚠[/] qca_results.json not found in {out_dir}")
        return {}
    if not os.path.exists(fuzzy_npz):
        console.print(f"  [yellow]⚠[/] fuzzy_data.npz not found in {out_dir}")
        return {}

    from experiment_engine.viz.viz_bridge import generate_all_viz

    viz_files = generate_all_viz(results_json, fuzzy_npz, str(out_dir))

    if viz_files:
        console.print(f"  [green]✓[/] Generated {len(viz_files)} visualizations")
        for name, path in viz_files.items():
            size = Path(path).stat().st_size
            console.print(f"    - {name}: {path} ({size} bytes)")
    else:
        console.print("  [yellow]⚠[/] No visualizations were generated")

    return viz_files


def main() -> None:
    """Entry point: parse args and run the pipeline."""
    import argparse

    parser = argparse.ArgumentParser(
        description="QCA Analysis Pipeline with Visualization"
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Path to pipeline config YAML file",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="qca_output",
        help="Output directory for results (default: qca_output)",
    )
    parser.add_argument(
        "--variant",
        type=str,
        default="fsqca",
        choices=["fsqca", "csqca"],
        help="QCA variant (default: fsqca)",
    )
    parser.add_argument(
        "--viz-only",
        action="store_true",
        help="Only run visualization step on existing results",
    )

    args = parser.parse_args()

    if args.viz_only:
        run_viz_step(args.output_dir)
        return

    if not args.config:
        console.print("[red]Error:[/] --config is required unless --viz-only is used")
        sys.exit(1)

    # Delegate to the CLI pipeline (Steps 1-5)
    from experiment_engine.cli import run as cli_run

    # Build Click-compatible args
    click_args = [
        "--config",
        args.config,
        "--output-dir",
        args.output_dir,
        "--variant",
        args.variant,
    ]

    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli_run, click_args)

    if result.exit_code != 0:
        console.print(f"[red]Pipeline failed:[/] {result.output}")
        console.print(f"[red]Exception:[/] {result.exception}")
        sys.exit(result.exit_code)

    console.print(result.output)

    # Step 6: Visualizations
    run_viz_step(args.output_dir)


if __name__ == "__main__":
    main()
