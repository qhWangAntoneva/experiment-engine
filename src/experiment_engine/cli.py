"""QCA Text Analysis CLI — complete QCA workflow commands."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import numpy as np
from rich.console import Console
from rich.table import Table

from experiment_engine.models import FuzzySetData, QCAVariant, TrainingDataset

console = Console()


@click.group()
@click.version_option(version="0.2.0", prog_name="qca")
def cli() -> None:
    """QCA Text Analysis Tool — citizen feedback text → fuzzy-set QCA analysis.

    Workflow: calibrate → analyze → robustness → report
    """


# ═══════════════════════════════════════════════════════════════════════════
#  calibrate
# ═══════════════════════════════════════════════════════════════════════════


@cli.command()
@click.option(
    "--condition-set",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to condition set YAML file",
)
@click.option(
    "--input",
    "-i",
    type=click.Path(exists=True),
    required=True,
    help="Path to input corpus file (CSV/JSON/TXT)",
)
@click.option(
    "--text-column",
    "-t",
    default="text",
    help="Column name containing text content",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="fuzzy_data.npz",
    help="Output path for fuzzy-set data (.npz, .csv, or .json)",
)
@click.option(
    "--variant",
    type=click.Choice(["fsqca", "csqca"]),
    default="fsqca",
    help="QCA variant: fsqca (fuzzy-set) or csqca (crisp-set)",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def calibrate(
    condition_set: str,
    input: str,
    text_column: str,
    output: str,
    variant: str,
    verbose: bool,
) -> None:
    """Calibrate raw texts to fuzzy-set membership scores."""
    from experiment_engine.io.readers import TextCorpusReader
    from experiment_engine.text_calibration import (
        TextCalibrationStage,
        load_condition_set,
    )

    cs = load_condition_set(condition_set)
    if variant == "csqca":
        cs.qca_variant = QCAVariant.CSQCA
    reader = TextCorpusReader()
    input_data = reader.read(input, text_column=text_column)
    console.print(f"[green]✓[/] Loaded {input_data.n_samples} texts")

    stage = TextCalibrationStage(cs)
    stage.setup()
    result = stage.process(input_data)

    fuzzy: FuzzySetData = result.processed  # type: ignore[assignment]
    console.print(
        f"[green]✓[/] Calibrated: {fuzzy.n_cases} cases x{fuzzy.n_conditions + 1} sets"
    )

    # Save
    _save_fuzzy_data(fuzzy, output)
    console.print(f"[green]✓[/] Saved to {output}")


# ═══════════════════════════════════════════════════════════════════════════
#  train
# ═══════════════════════════════════════════════════════════════════════════


@cli.command()
@click.option(
    "--condition-set",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to condition set YAML file",
)
@click.option(
    "--samples",
    "-s",
    type=click.Path(exists=True),
    required=True,
    help="Path to labeled training samples (CSV/JSON)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="conditions_fitted.yaml",
    help="Output path for fitted condition set YAML",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def train(condition_set: str, samples: str, output: str, verbose: bool) -> None:
    """Train calibration parameters from labeled concept prototypes."""
    from experiment_engine.text_calibration import (
        TrainingEngine,
        load_condition_set,
        save_condition_set,
    )

    cs = load_condition_set(condition_set)
    console.print(f"[green]✓[/] Loaded condition set: {cs.name}")

    # Load training samples
    dataset = _load_training_samples(samples, cs)
    console.print(f"[green]✓[/] Loaded {dataset.n_samples} training samples")

    engine = TrainingEngine()
    fitted = engine.fit(dataset, cs)

    save_condition_set(fitted, output)
    console.print(f"[green]✓[/] Fitted condition set saved to {output}")

    if verbose:
        _print_fit_metrics(engine.fit_metrics)


def _print_fit_metrics(metrics: dict) -> None:
    """Print per-condition fit quality metrics."""
    if not metrics:
        return
    console.print("\n[bold]Fit Quality:[/]")
    for name, m in metrics.items():
        console.print(
            f"  {name}: r={m['pearson_r']:.3f}  MAE={m['mae']:.3f}  "
            f"out={m['threshold_full_out']:.2f}  "
            f"crossover={m['crossover_point']:.2f}  "
            f"in={m['threshold_full_in']:.2f}"
        )


# ═══════════════════════════════════════════════════════════════════════════
#  analyze
# ═══════════════════════════════════════════════════════════════════════════


@cli.command()
@click.option(
    "--condition-set",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to condition set YAML file",
)
@click.option(
    "--fuzzy-data",
    "-f",
    type=click.Path(exists=True),
    required=True,
    help="Path to fuzzy-set data file (.npz/.csv)",
)
@click.option(
    "--consistency",
    default=0.75,
    type=float,
    help="Consistency threshold for truth table outcome assignment",
)
@click.option(
    "--frequency",
    default=1.0,
    type=float,
    help="Frequency threshold for truth table inclusion",
)
@click.option(
    "--variant",
    type=click.Choice(["fsqca", "csqca"]),
    default="fsqca",
    help="QCA variant: fsqca (fuzzy-set) or csqca (crisp-set)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="qca_results.json",
    help="Output path for QCA results",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def analyze(
    condition_set: str,
    fuzzy_data: str,
    consistency: float,
    frequency: float,
    variant: str,
    output: str,
    verbose: bool,
) -> None:
    """Run full QCA analysis: truth table → minimization → necessity → sufficiency."""
    from experiment_engine.qca_engine import QCAnalyzerStage
    from experiment_engine.text_calibration import load_condition_set

    cs = load_condition_set(condition_set)
    if variant == "csqca":
        cs.qca_variant = QCAVariant.CSQCA
    fuzzy = _load_fuzzy_data(fuzzy_data, cs)

    stage = QCAnalyzerStage(
        condition_set=cs,
        consistency_threshold=consistency,
        frequency_threshold=frequency,
    )
    stage.setup()
    result = stage.analyze(fuzzy)

    # Print summary
    _print_analysis_summary(result, verbose)

    # Save
    _save_analysis_result(result, output)
    console.print(f"[green]✓[/] Results saved to {output}")


# ═══════════════════════════════════════════════════════════════════════════
#  robustness
# ═══════════════════════════════════════════════════════════════════════════


@cli.command()
@click.option(
    "--condition-set",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to condition set YAML file",
)
@click.option(
    "--fuzzy-data",
    "-f",
    type=click.Path(exists=True),
    required=True,
    help="Path to fuzzy-set data file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="robustness_report.json",
    help="Output path for robustness report",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def robustness(condition_set: str, fuzzy_data: str, output: str, verbose: bool) -> None:
    """Run robustness and sensitivity tests on QCA results."""
    from experiment_engine.qca_engine import QCAnalyzerStage
    from experiment_engine.qca_engine.advanced import RobustnessTester
    from experiment_engine.text_calibration import load_condition_set

    cs = load_condition_set(condition_set)
    fuzzy = _load_fuzzy_data(fuzzy_data, cs)

    stage = QCAnalyzerStage(condition_set=cs)
    stage.setup()
    baseline = stage.analyze(fuzzy)

    tester = RobustnessTester()
    report = tester.run_all(fuzzy, baseline)

    console.print(f"Overall robustness: {report.overall_robustness:.2f}")
    console.print(report.summary)

    with open(output, "w", encoding="utf-8") as fh:
        fh.write(report.model_dump_json(indent=2))
    console.print(f"[green]✓[/] Report saved to {output}")


# ═══════════════════════════════════════════════════════════════════════════
#  counterfactuals
# ═══════════════════════════════════════════════════════════════════════════


@cli.command()
@click.option(
    "--condition-set",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to condition set YAML file",
)
@click.option(
    "--fuzzy-data",
    "-f",
    type=click.Path(exists=True),
    required=True,
    help="Path to fuzzy-set data file",
)
@click.option(
    "--expectations",
    "-e",
    type=click.Path(exists=True),
    default=None,
    help="Path to directional expectations YAML file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="counterfactual_report.json",
    help="Output path for counterfactual report",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def counterfactuals(
    condition_set: str,
    fuzzy_data: str,
    expectations: str | None,
    output: str,
    verbose: bool,
) -> None:
    """Run counterfactual analysis (complex/parsimonious/intermediate solutions)."""
    from experiment_engine.qca_engine import QCAnalyzerStage
    from experiment_engine.qca_engine.advanced import CounterfactualAnalyzer
    from experiment_engine.text_calibration import load_condition_set

    cs = load_condition_set(condition_set)
    fuzzy = _load_fuzzy_data(fuzzy_data, cs)

    stage = QCAnalyzerStage(condition_set=cs)
    stage.setup()
    result = stage.analyze(fuzzy)

    if result.truth_table is None:
        console.print("[red]No truth table in analysis result[/]")
        sys.exit(1)

    # Load directional expectations
    dir_exp = None
    if expectations:
        import yaml as _yaml

        with open(expectations, encoding="utf-8") as fh:
            dir_exp = _yaml.safe_load(fh)

    analyzer = CounterfactualAnalyzer()
    cf_report = analyzer.analyze(result.truth_table, dir_exp)

    # Produce all three solution types
    complex_terms = analyzer.produce_complex_solution(result.truth_table)
    parsimonious_terms = analyzer.produce_parsimonious_solution(
        result.truth_table, dir_exp
    )
    intermediate_terms = analyzer.produce_intermediate_solution(
        result.truth_table, dir_exp or {}
    )

    console.print(f"Easy counterfactuals: {cf_report.n_easy_counterfactuals}")
    console.print(f"Hard counterfactuals: {cf_report.n_hard_counterfactuals}")
    console.print(f"Logical remainders: {cf_report.n_logical_remainders}")
    console.print(f"Complex solution: {len(complex_terms)} terms")
    console.print(f"Parsimonious solution: {len(parsimonious_terms)} terms")
    console.print(f"Intermediate solution: {len(intermediate_terms)} terms")

    data_out = {
        "counterfactual_report": cf_report.model_dump(),
        "complex_terms": complex_terms,
        "parsimonious_terms": parsimonious_terms,
        "intermediate_terms": intermediate_terms,
    }
    with open(output, "w", encoding="utf-8") as fh:
        json.dump(data_out, fh, indent=2, ensure_ascii=False)
    console.print(f"[green]✓[/] Report saved to {output}")


# ═══════════════════════════════════════════════════════════════════════════
#  report
# ═══════════════════════════════════════════════════════════════════════════


@cli.command()
@click.option(
    "--results",
    "-r",
    type=click.Path(exists=True),
    required=True,
    help="Path to QCA results JSON file (from analyze)",
)
@click.option(
    "--format",
    "-f",
    "fmt",
    type=click.Choice(["latex", "console"]),
    default="console",
    help="Report format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default=None,
    help="Output path for report",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def report(results: str, fmt: str, output: str | None, verbose: bool) -> None:
    """Generate an analysis report (LaTeX or console)."""
    with open(results, encoding="utf-8") as fh:
        data = json.load(fh)

    if fmt == "latex":
        from experiment_engine.models import QCAAnalysisResult
        from experiment_engine.report.qca_reporter import QCALaTeXReporter

        result = QCAAnalysisResult(**data)
        out_path = output or "qca_report.tex"
        reporter = QCALaTeXReporter()
        reporter.generate(result, output_path=out_path)
        console.print(f"[green]✓[/] LaTeX report saved to {out_path}")
    else:
        _print_console_report(data)


# ═══════════════════════════════════════════════════════════════════════════
#  run (full workflow)
# ═══════════════════════════════════════════════════════════════════════════


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to workflow configuration YAML file",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="qca_output",
    help="Directory for all output artifacts",
)
@click.option(
    "--variant",
    type=click.Choice(["fsqca", "csqca"]),
    default="fsqca",
    help="QCA variant: fsqca (fuzzy-set) or csqca (crisp-set)",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(config: str, output_dir: str, variant: str, verbose: bool) -> None:
    """Run the complete QCA workflow (calibrate → analyze → robustness → report)."""
    import yaml as _yaml

    with open(config, encoding="utf-8") as fh:
        cfg = _yaml.safe_load(fh)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Calibrate
    console.print("[bold cyan]Step 1/4:[/] Text calibration...")
    from experiment_engine.io.readers import TextCorpusReader
    from experiment_engine.text_calibration import (
        TextCalibrationStage,
        load_condition_set,
    )

    cs = load_condition_set(cfg["conditions"]["definition_file"])
    if variant == "csqca":
        cs.qca_variant = QCAVariant.CSQCA
    reader = TextCorpusReader()
    input_cfg = cfg["input"]
    input_data = reader.read(
        input_cfg["path"],
        text_column=input_cfg.get("text_column", "text"),
    )

    stage = TextCalibrationStage(cs)
    stage.setup()
    cal_result = stage.process(input_data)

    fuzzy: FuzzySetData = cal_result.processed  # type: ignore[assignment]
    fuzzy_path = out_dir / "fuzzy_data.npz"
    _save_fuzzy_data(fuzzy, str(fuzzy_path))
    console.print(f"  [green]✓[/] {fuzzy.n_cases} cases x{fuzzy.n_conditions + 1} sets")

    # 2. Analyze
    console.print("[bold cyan]Step 2/4:[/] QCA analysis...")
    from experiment_engine.qca_engine import QCAnalyzerStage

    qca_cfg = cfg.get("qca", {})
    qca_stage = QCAnalyzerStage(
        condition_set=cs,
        consistency_threshold=qca_cfg.get("consistency_threshold", 0.75),
        frequency_threshold=qca_cfg.get("frequency_threshold", 1.0),
    )
    qca_stage.setup()
    qca_result = qca_stage.analyze(fuzzy)
    _print_analysis_summary(qca_result, verbose)

    results_path = out_dir / "qca_results.json"
    _save_analysis_result(qca_result, str(results_path))

    # 3. Robustness
    console.print("[bold cyan]Step 3/4:[/] Robustness tests...")
    from experiment_engine.qca_engine.advanced import RobustnessTester

    tester = RobustnessTester()
    rob_report = tester.run_all(fuzzy, qca_result)
    console.print(f"  Overall robustness: {rob_report.overall_robustness:.2f}")
    rob_path = out_dir / "robustness_report.json"
    with open(str(rob_path), "w", encoding="utf-8") as fh:
        fh.write(rob_report.model_dump_json(indent=2))

    # 4. Report
    console.print("[bold cyan]Step 4/4:[/] Generating report...")
    from experiment_engine.report.qca_reporter import QCALaTeXReporter

    reporter = QCALaTeXReporter()
    report_path = out_dir / "qca_report.tex"
    reporter.generate(
        qca_result,
        output_path=str(report_path),
        robustness=rob_report,
    )
    console.print(f"  [green]✓[/] Report saved to {report_path}")

    console.print(f"\n[bold green]Done![/] All outputs in {out_dir}")


# ═══════════════════════════════════════════════════════════════════════════
#  validate
# ═══════════════════════════════════════════════════════════════════════════


@cli.command()
@click.option(
    "--condition-set",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to condition set YAML file",
)
def validate(condition_set: str) -> None:
    """Validate a condition set configuration file."""
    from experiment_engine.text_calibration import load_condition_set

    try:
        cs = load_condition_set(condition_set)
        console.print(f"[green]✓[/] Valid condition set: {cs.name}")
        console.print(f"  Domain: {cs.domain.value}")
        console.print(f"  Conditions: {cs.n_conditions}")
        console.print(f"  Condition names: {', '.join(cs.condition_names)}")
        if cs.outcome:
            console.print(f"  Outcome: {cs.outcome.name}")
    except Exception as exc:
        console.print(f"[red]✗[/] Invalid: {exc}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
#  list-conditions
# ═══════════════════════════════════════════════════════════════════════════


@cli.command()
@click.option(
    "--domain",
    "-d",
    type=click.Choice(
        [
            "dissatisfaction",
            "policy_demand",
            "co_production",
            "trust",
            "gov_responsiveness",
        ]
    ),
    default=None,
    help="Filter by domain",
)
def list_conditions(domain: str | None) -> None:
    """List available domain presets and their conditions."""
    from experiment_engine.models import TextDomain
    from experiment_engine.text_calibration import DOMAIN_PRESETS

    domains = [TextDomain(domain)] if domain else list(DOMAIN_PRESETS.keys())

    for d in domains:
        preset = DOMAIN_PRESETS.get(d, {})
        console.print(f"\n[bold cyan]{d.value.upper()}[/]")
        for cond_name, keywords in preset.items():
            is_outcome = cond_name == list(preset.keys())[-1]
            tag = "[bold yellow](outcome)[/]" if is_outcome else ""
            console.print(f"  {cond_name} {tag}: {len(keywords)} keywords")


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════


def _save_fuzzy_data(fuzzy: FuzzySetData, path: str) -> None:
    if path.endswith(".npz"):
        np.savez_compressed(
            path,
            membership=fuzzy.membership,
            condition_names=np.array(fuzzy.condition_names, dtype=object),
            outcome_name=fuzzy.outcome_name,
            case_ids=np.array(fuzzy.case_ids or [], dtype=object),
        )

    elif path.endswith(".json"):
        import json as _json

        out = {
            "condition_names": fuzzy.condition_names,
            "outcome_name": fuzzy.outcome_name,
            "case_ids": fuzzy.case_ids,
            "membership": fuzzy.membership.tolist(),
            "metadata": fuzzy.metadata,
        }
        with open(path, "w", encoding="utf-8") as fh:
            _json.dump(out, fh, indent=2, ensure_ascii=False)
    else:
        import csv

        all_names = [*fuzzy.condition_names, fuzzy.outcome_name]
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(all_names)
            for i in range(fuzzy.n_cases):
                writer.writerow(fuzzy.membership[i].tolist())


def _load_fuzzy_data(path: str, cs) -> FuzzySetData:
    from experiment_engine.models import FuzzySetData as FSD

    if path.endswith(".npz"):
        data = np.load(path, allow_pickle=True)
        return FSD(
            membership=data["membership"],
            condition_names=data.get("condition_names", cs.condition_names).tolist(),
            outcome_name=str(
                data.get("outcome_name", cs.outcome.name if cs.outcome else "")
            ),
            case_ids=data.get("case_ids", []).tolist()
            if data.get("case_ids") is not None
            else None,
        )
    if path.endswith(".json"):
        import json as _json

        with open(path, encoding="utf-8") as fh:
            raw = _json.load(fh)
        return FSD(
            membership=np.array(raw["membership"]),
            condition_names=raw.get("condition_names", []),
            outcome_name=raw.get("outcome_name", ""),
            case_ids=raw.get("case_ids"),
        )
    import pandas as pd

    df = pd.read_csv(path)
    condition_names = cs.condition_names
    outcome_name = cs.outcome.name if cs.outcome else ""
    all_names = [*condition_names, outcome_name]
    available = [c for c in all_names if c in df.columns]
    membership = df[available].to_numpy(dtype=np.float64)
    return FSD(
        membership=membership,
        condition_names=[c for c in available if c != outcome_name],
        outcome_name=outcome_name,
    )


def _load_training_samples(path, cs) -> TrainingDataset:
    from experiment_engine.models import TrainingDataset, TrainingSample

    samples: list[TrainingSample] = []
    condition_names = cs.condition_names
    outcome_name = cs.outcome.name if cs.outcome else ""

    import pandas as pd

    path_str = str(path)
    if path_str.endswith(".json"):
        import json as _json

        with open(path_str, encoding="utf-8") as fh:
            raw = _json.load(fh)
        records = (
            raw if isinstance(raw, list) else raw.get("samples", raw.get("data", []))
        )
    else:
        df = pd.read_csv(path_str)
        records = df.to_dict(orient="records")

    for rec in records:
        scores = {}
        for name in [*condition_names, outcome_name]:
            if name in rec and name:
                scores[name] = float(rec[name])
        samples.append(
            TrainingSample(
                text_id=str(rec.get("id", rec.get("text_id", ""))),
                text=str(rec.get("text", "")),
                labeled_scores=scores,
            )
        )

    return TrainingDataset(
        samples=samples,
        condition_names=condition_names,
        outcome_name=outcome_name,
    )


def _save_analysis_result(result, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(result.model_dump_json(indent=2, exclude={"fuzzy_data"}))


def _print_analysis_summary(result, verbose: bool) -> None:
    if result.truth_table:
        tt = result.truth_table
        console.print(
            f"  Truth table: {len(tt.included_rows)}/{len(tt.rows)} rows included"
        )
        console.print(f"  Positive configurations: {len(tt.positive_rows)}")

    if result.solutions.complex:
        console.print(f"  Complex solution: {result.solutions.complex.formula}")
        console.print(
            f"    Consistency={result.solutions.complex.solution_consistency:.3f}  "
            f"Coverage={result.solutions.complex.solution_coverage:.3f}"
        )

    if result.necessity:
        necessary = [
            c.condition_name for c in result.necessity.conditions if c.is_necessary
        ]
        if necessary:
            console.print(f"  Necessary conditions: {', '.join(necessary)}")


def _print_console_report(data: dict) -> None:
    if data.get("truth_table"):
        tt = data["truth_table"]
        console.print("\n[bold]Truth Table[/]")
        table = Table(title=f"Truth Table (n={len(tt.get('rows', []))} rows)")
        table.add_column("Config")
        table.add_column("Freq", justify="right")
        table.add_column("Cons", justify="right")
        table.add_column("Outcome", justify="center")
        for r in tt.get("rows", []):
            table.add_row(
                r.get("config_label", ""),
                f"{r.get('frequency', 0):.1f}",
                f"{r.get('raw_consistency', 0):.3f}",
                str(r.get("outcome_value", 0)),
            )
        console.print(table)


main = cli

if __name__ == "__main__":
    cli()
