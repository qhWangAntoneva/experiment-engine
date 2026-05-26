"""QCA Analysis Python API — clean functions for programmatic use.

Each function returns data objects. CLI-specific concerns (console output,
interactive prompts) belong in :mod:`cli.py`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiment_engine.models import (
    MembershipData,
    QCAAnalysisResult,
    QCAVariant,
    RobustnessReport,
)

# ═══════════════════════════════════════════════════════════════════════════
#  Public API functions
# ═══════════════════════════════════════════════════════════════════════════


def run_calibrate(
    condition_set_path: str,
    data_path: str,
    variant: str = "fsqca",
    text_column: str = "text",
) -> MembershipData:
    """Calibrate raw texts to fuzzy-set membership scores.

    Uses ground-truth outcomes from the CSV ``expected_outcome`` column
    instead of computing outcome values from prototype similarity.
    Filters cases by domain matching the condition set's domain.

    Args:
        condition_set_path: Path to condition set YAML file.
        data_path: Path to input corpus file (CSV).
        variant: QCA variant (``'fsqca'`` or ``'csqca'``).
        text_column: Column name containing text content.

    Returns:
        MembershipData with calibrated membership scores.

    Raises:
        ValueError: If the CSV does not contain an ``expected_outcome`` column.
    """
    import numpy as np
    import pandas as pd

    from experiment_engine.models import InputData
    from experiment_engine.text_calibration import (
        TextCalibrationStage,
        load_condition_set,
    )

    cs = load_condition_set(condition_set_path)
    if variant == "csqca":
        cs.qca_variant = QCAVariant.CSQCA

    # --- Read CSV with pandas to access expected_outcome + domain columns ---
    df = pd.read_csv(data_path, encoding="utf-8")

    # Determine the domain from the condition set
    domain_name = cs.domain.value  # e.g. "trust", "dissatisfaction"

    # BUG-2 fix: filter rows by domain
    df_filtered = df[df["domain"] == domain_name].copy()
    if df_filtered.empty:
        raise ValueError(f"No cases found for domain '{domain_name}' in {data_path}")

    # BUG-1 fix: extract ground-truth outcomes from expected_outcome column
    if "expected_outcome" not in df_filtered.columns:
        raise ValueError(
            f"CSV {data_path} has no 'expected_outcome' column. "
            "Ground-truth outcomes are required for calibration."
        )

    texts = df_filtered[text_column].tolist()
    outcome_vector = df_filtered["expected_outcome"].to_numpy(dtype=np.float64)

    # Create InputData from filtered texts (use text_id if available, else row index)
    if "text_id" in df_filtered.columns:
        case_ids = [str(x) for x in df_filtered["text_id"]]
    else:
        case_ids = [str(i) for i in df_filtered.index]

    input_data = InputData(
        data=np.array(texts, dtype=object),
        index=case_ids,
    )

    stage = TextCalibrationStage(cs)
    stage.setup()
    result = stage.process_with_outcome(
        input_data,
        outcome_vector=outcome_vector,
    )

    fuzzy: MembershipData = result.processed  # type: ignore[assignment]
    return fuzzy


def run_analyze(
    condition_set_path: str,
    fuzzy_data_path: str,
    variant: str = "fsqca",
    consistency_threshold: float = 0.75,
    frequency_threshold: float = 1.0,
) -> QCAAnalysisResult:
    """Run full QCA analysis: truth table -> minimization -> necessity -> sufficiency.

    Args:
        condition_set_path: Path to condition set YAML file.
        fuzzy_data_path: Path to fuzzy-set data file (.npz/.csv).
        variant: QCA variant (``'fsqca'`` or ``'csqca'``).
        consistency_threshold: Consistency threshold for truth table outcome
            assignment.
        frequency_threshold: Frequency threshold for truth table inclusion.

    Returns:
        QCAAnalysisResult with truth table, solutions, necessity, sufficiency.
    """
    from experiment_engine.qca_engine import QCAnalyzerStage
    from experiment_engine.text_calibration import load_condition_set

    cs = load_condition_set(condition_set_path)
    if variant == "csqca":
        cs.qca_variant = QCAVariant.CSQCA

    fuzzy = _load_fuzzy_data(fuzzy_data_path, cs)

    stage = QCAnalyzerStage(
        condition_set=cs,
        consistency_threshold=consistency_threshold,
        frequency_threshold=frequency_threshold,
    )
    stage.setup()
    return stage.analyze(fuzzy)


def run_robustness(
    condition_set_path: str,
    fuzzy_data_path: str,
    variant: str = "fsqca",
) -> tuple[QCAAnalysisResult, RobustnessReport]:
    """Run robustness and sensitivity tests on QCA results.

    Args:
        condition_set_path: Path to condition set YAML file.
        fuzzy_data_path: Path to fuzzy-set data file (.npz/.csv).
        variant: QCA variant (``'fsqca'`` or ``'csqca'``).

    Returns:
        Tuple of ``(baseline QCAAnalysisResult, RobustnessReport)``.
    """
    from experiment_engine.qca_engine import QCAnalyzerStage
    from experiment_engine.qca_engine.advanced import RobustnessTester
    from experiment_engine.text_calibration import load_condition_set

    cs = load_condition_set(condition_set_path)
    if variant == "csqca":
        cs.qca_variant = QCAVariant.CSQCA

    fuzzy = _load_fuzzy_data(fuzzy_data_path, cs)

    stage = QCAnalyzerStage(condition_set=cs)
    stage.setup()
    baseline = stage.analyze(fuzzy)

    tester = RobustnessTester()
    report = tester.run_all(fuzzy, baseline)
    return baseline, report


def run_counterfactuals(
    condition_set_path: str,
    fuzzy_data_path: str,
    variant: str = "fsqca",
    expectations_path: str | None = None,
) -> dict[str, Any]:
    """Run counterfactual analysis (complex/parsimonious/intermediate solutions).

    Args:
        condition_set_path: Path to condition set YAML file.
        fuzzy_data_path: Path to fuzzy-set data file (.npz/.csv).
        variant: QCA variant (``'fsqca'`` or ``'csqca'``).
        expectations_path: Optional path to directional expectations YAML file.

    Returns:
        Dict with keys ``counterfactual_report``, ``complex_terms``,
        ``parsimonious_terms``, ``intermediate_terms``.

    Raises:
        ValueError: If the analysis result contains no truth table.
    """
    from experiment_engine.qca_engine import QCAnalyzerStage
    from experiment_engine.qca_engine.advanced import CounterfactualAnalyzer
    from experiment_engine.text_calibration import load_condition_set

    cs = load_condition_set(condition_set_path)
    fuzzy = _load_fuzzy_data(fuzzy_data_path, cs)

    stage = QCAnalyzerStage(condition_set=cs)
    stage.setup()
    result = stage.analyze(fuzzy)

    if result.truth_table is None:
        raise ValueError("No truth table in analysis result")

    # Load directional expectations
    dir_exp = None
    if expectations_path:
        import yaml as _yaml

        with open(expectations_path, encoding="utf-8") as fh:
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

    return {
        "counterfactual_report": cf_report.model_dump(),
        "complex_terms": complex_terms,
        "parsimonious_terms": parsimonious_terms,
        "intermediate_terms": intermediate_terms,
    }


def run_report(
    results_path: str,
    output_dir: str = ".",
    fmt: str = "latex",
    robustness_path: str | None = None,
) -> str:
    """Generate an analysis report (LaTeX or console).

    Args:
        results_path: Path to QCA results JSON file (from analyze).
        output_dir: Directory to write the report into. Created if it does not
            exist.
        fmt: Report format (``'latex'`` or ``'console'``).
        robustness_path: Optional path to robustness report JSON to include
            in the LaTeX output.

    Returns:
        Path to the generated report file (LaTeX), or empty string (console).
    """
    from experiment_engine.models import QCAAnalysisResult

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(results_path, encoding="utf-8") as fh:
        data = json.load(fh)

    result = QCAAnalysisResult(**data)

    if fmt == "latex":
        from experiment_engine.report.qca_reporter import QCALaTeXReporter

        rob_report = None
        if robustness_path:
            with open(robustness_path, encoding="utf-8") as fh:
                rob_data = json.load(fh)
            rob_report = RobustnessReport(**rob_data)

        out_path = str(out_dir / "qca_report.tex")
        reporter = QCALaTeXReporter()
        reporter.generate(result, output_path=out_path, robustness=rob_report)
        return out_path

    if fmt == "docx":
        from experiment_engine.report.docx_reporter import QCADocxReporter

        rob_report = None
        if robustness_path:
            with open(robustness_path, encoding="utf-8") as fh:
                rob_data = json.load(fh)
            rob_report = RobustnessReport(**rob_data)

        reporter = QCADocxReporter()
        docx_bytes = reporter.generate(result, robustness=rob_report)
        out_path = str(out_dir / "qca_report.docx")
        with open(out_path, "wb") as fh:
            fh.write(docx_bytes)
        return out_path

    # Console format does not produce an output file
    return ""


def run_viz(
    results_path: str,
    fuzzy_data_path: str,
    output_dir: str = ".",
) -> dict[str, str]:
    """Generate visualization charts from QCA results (stub).

    Loads QCA results from JSON and fuzzy data from NPZ, then calls
    :class:`QCAPlotBuilder` methods to produce PNG charts.

    Args:
        results_path: Path to QCA results JSON file.
        fuzzy_data_path: Path to fuzzy-set data file (.npz).
        output_dir: Directory to write chart PNGs into.

    Returns:
        Dict mapping chart name to output file path.

    .. note::

       This is a stub that validates the viz module imports and logs what
       would be generated. The actual viz bridge will be completed by
       another agent.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Validate imports — raise ImportError if viz module not available
    from experiment_engine.viz import QCAPlotBuilder  # noqa: F401

    charts = {
        "truth_table_heatmap": str(out_dir / "truth_table_heatmap.png"),
        "necessity_xy_plot": str(out_dir / "necessity_xy_plot.png"),
        "fuzzy_distribution_plot": str(out_dir / "fuzzy_distribution_plot.png"),
    }

    # Stub: log what would be generated
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        "run_viz stub: would generate %d charts from %s / %s -> %s",
        len(charts),
        results_path,
        fuzzy_data_path,
        output_dir,
    )

    return charts


def run_docx_report(
    results_path: str,
    output_dir: str = ".",
) -> str:
    """Generate a Word (.docx) report from QCA results.

    Loads QCA results from JSON and generates a DOCX report via
    :class:`QCADocxReporter`.

    Args:
        results_path: Path to QCA results JSON file.
        output_dir: Directory to write the report into.

    Returns:
        Path to the generated ``.docx`` file.
    """
    from experiment_engine.models import QCAAnalysisResult
    from experiment_engine.report.docx_reporter import QCADocxReporter

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(results_path, encoding="utf-8") as fh:
        data = json.load(fh)

    result = QCAAnalysisResult(**data)

    reporter = QCADocxReporter()
    docx_bytes = reporter.generate(result)
    out_path = str(out_dir / "qca_report.docx")
    with open(out_path, "wb") as fh:
        fh.write(docx_bytes)

    return out_path


# ═══════════════════════════════════════════════════════════════════════════
#  Internal helpers
# ═══════════════════════════════════════════════════════════════════════════


def _load_fuzzy_data(path: str, cs: Any) -> MembershipData:
    """Load fuzzy-set data from ``.npz``, ``.json``, or ``.csv`` file.

    Shared between :mod:`api` and :mod:`cli`.
    """
    import numpy as np

    if path.endswith(".npz"):
        data = np.load(path, allow_pickle=True)
        return MembershipData(
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
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        return MembershipData(
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
    return MembershipData(
        membership=membership,
        condition_names=[c for c in available if c != outcome_name],
        outcome_name=outcome_name,
    )
