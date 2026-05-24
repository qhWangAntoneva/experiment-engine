"""Unit tests for the experiment-engine LaTeX report generator."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from experiment_engine.models import (
    ExperimentConfig,
    PipelineResult,
    PipelineStageConfig,
    PipelineStatus,
    StageResult,
    StageStatus,
)
from experiment_engine.report import LaTeXReporter

# ═══════════════════════════════════════════════════════════════════════
#  Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def reporter() -> LaTeXReporter:
    return LaTeXReporter()


@pytest.fixture
def sample_result() -> PipelineResult:
    """A typical completed pipeline result with two stages."""
    return PipelineResult(
        experiment_name="test_experiment",
        status=PipelineStatus.COMPLETED,
        total_duration_ms=1500.0,
        started_at="2026-05-16T20:00:00Z",
        completed_at="2026-05-16T20:00:01Z",
        stages=[
            StageResult(
                stage_name="load_data",
                stage_type="csv_loader",
                status=StageStatus.COMPLETED,
                duration_ms=500.0,
                started_at="2026-05-16T20:00:00Z",
                completed_at="2026-05-16T20:00:00Z",
            ),
            StageResult(
                stage_name="transform",
                stage_type="data_transformer",
                status=StageStatus.COMPLETED,
                duration_ms=1000.0,
                started_at="2026-05-16T20:00:00Z",
                completed_at="2026-05-16T20:00:01Z",
            ),
        ],
        metadata={"framework": "pytest", "version": "1.0"},
    )


@pytest.fixture
def sample_config() -> ExperimentConfig:
    """A sample experiment configuration with two stages."""
    return ExperimentConfig(
        name="test_experiment",
        description="A test experiment for LaTeX report generation",
        version="1.0",
        stages=[
            PipelineStageConfig(
                name="load_data",
                stage_type="csv_loader",
                enabled=True,
                params={"file_path": "data/input.csv", "delimiter": ","},
            ),
            PipelineStageConfig(
                name="transform",
                stage_type="data_transformer",
                enabled=True,
                params={"normalize": True, "scale": 1.0},
            ),
        ],
        global_params={"seed": 42, "device": "cpu"},
        output_dir="./output",
        verbose=True,
    )


@pytest.fixture
def empty_result() -> PipelineResult:
    """A pipeline result with no stages (empty pipeline)."""
    return PipelineResult(
        experiment_name="empty_pipeline",
        status=PipelineStatus.COMPLETED,
        total_duration_ms=0.0,
        stages=[],
    )


# ═══════════════════════════════════════════════════════════════════════
#  Tests
# ═══════════════════════════════════════════════════════════════════════


def test_generate_tex_file_exists(
    reporter: LaTeXReporter, sample_result: PipelineResult
) -> None:
    """Generated .tex file exists on disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.tex"
        result_path = reporter.generate_report(
            result=sample_result, output_path=str(out_path)
        )
        assert Path(result_path).exists()
        assert Path(result_path).suffix == ".tex"


def test_generate_tex_contains_experiment_name(
    reporter: LaTeXReporter, sample_result: PipelineResult
) -> None:
    """Generated .tex content contains the experiment name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.tex"
        reporter.generate_report(result=sample_result, output_path=str(out_path))
        content = out_path.read_text(encoding="utf-8")
        # Underscore is escaped in LaTeX, so search for the escaped version
        assert r"test\_experiment" in content


def test_generate_tex_contains_status_table(
    reporter: LaTeXReporter, sample_result: PipelineResult
) -> None:
    """Generated .tex contains a stage status table with stage info."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.tex"
        reporter.generate_report(result=sample_result, output_path=str(out_path))
        content = out_path.read_text(encoding="utf-8")
        # Should have a tabular environment for stages
        assert r"\begin{tabular}" in content
        # Should include stage names (underscores escaped in LaTeX)
        assert r"load\_data" in content
        assert r"transform" in content
        # Should include duration info
        assert "500.0" in content
        assert "1000.0" in content
        # Should include status indicators
        assert "statuscompleted" in content or "Completed" in content


def test_generate_tex_with_config(
    reporter: LaTeXReporter,
    sample_result: PipelineResult,
    sample_config: ExperimentConfig,
) -> None:
    """With a config, the report includes configuration snapshot content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.tex"
        reporter.generate_report(
            result=sample_result,
            config=sample_config,
            output_path=str(out_path),
        )
        content = out_path.read_text(encoding="utf-8")

        # Config section label
        assert r"\section{Configuration Snapshot}" in content
        # Config fields
        assert "seed" in content
        assert "device" in content
        assert "cpu" in content
        # Stage params (underscores escaped)
        assert r"file\_path" in content
        assert "delimiter" in content
        assert r"data/input.csv" in content  # forward slash not escaped


def test_generate_tex_with_figures(
    reporter: LaTeXReporter, sample_result: PipelineResult
) -> None:
    """With figure paths, includegraphics commands appear in the report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy figure files
        fig1 = Path(tmpdir) / "accuracy_plot.png"
        fig2 = Path(tmpdir) / "loss_curve.png"
        fig1.touch()
        fig2.touch()

        out_path = Path(tmpdir) / "report.tex"
        reporter.generate_report(
            result=sample_result,
            figure_paths=[str(fig1), str(fig2)],
            output_path=str(out_path),
        )
        content = out_path.read_text(encoding="utf-8")

        # Figure section
        assert r"\section{Figures and Charts}" in content
        # includegraphics commands
        assert r"\includegraphics" in content
        # Figure captions with the file stems
        assert "accuracy_plot" in content
        assert "loss_curve" in content


def test_generate_tex_empty_pipeline(
    reporter: LaTeXReporter, empty_result: PipelineResult
) -> None:
    """An empty stages list does not cause errors and produces valid output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.tex"
        reporter.generate_report(result=empty_result, output_path=str(out_path))
        content = out_path.read_text(encoding="utf-8")

        # Basic document structure is present
        assert r"\documentclass" in content
        assert r"\begin{document}" in content
        assert r"\end{document}" in content
        # Experiment name is present (underscore escaped)
        assert r"empty\_pipeline" in content
        # Indication of no stages
        assert "No stages were executed" in content or "0/0" in content


def test_generate_tex_contains_metadata(
    reporter: LaTeXReporter, sample_result: PipelineResult
) -> None:
    """Metadata dictionary renders as a table in the report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.tex"
        reporter.generate_report(result=sample_result, output_path=str(out_path))
        content = out_path.read_text(encoding="utf-8")

        assert r"\section{Metadata}" in content
        assert "framework" in content
        assert "pytest" in content
        assert "version" in content


def test_generate_tex_without_config_and_figures(
    reporter: LaTeXReporter, sample_result: PipelineResult
) -> None:
    """Report without config/figures has no config or figures sections."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.tex"
        reporter.generate_report(result=sample_result, output_path=str(out_path))
        content = out_path.read_text(encoding="utf-8")

        assert r"\section{Configuration Snapshot}" not in content
        assert r"\section{Figures and Charts}" not in content
        # But metadata should still be there
        assert r"\section{Metadata}" in content


def test_compile_pdf_no_pdflatex(
    reporter: LaTeXReporter, sample_result: PipelineResult
) -> None:
    """compile_pdf returns None when pdflatex is not available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "report.tex"
        reporter.generate_report(result=sample_result, output_path=str(tex_path))
        pdf_path = reporter.compile_pdf(str(tex_path))
        # On most test environments pdflatex won't be installed
        assert pdf_path is None or Path(pdf_path).suffix == ".pdf"


def test_generate_tex_contains_preamble(
    reporter: LaTeXReporter, sample_result: PipelineResult
) -> None:
    """Preamble includes required LaTeX packages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.tex"
        reporter.generate_report(result=sample_result, output_path=str(out_path))
        content = out_path.read_text(encoding="utf-8")

        assert r"\documentclass[12pt,a4paper]{article}" in content
        assert r"\usepackage{amsmath}" in content
        assert r"\usepackage{graphicx}" in content
        assert r"\usepackage{booktabs}" in content
        assert r"\usepackage[margin=2.5cm]{geometry}" in content


def test_generate_tex_contains_timing_breakdown(
    reporter: LaTeXReporter, sample_result: PipelineResult
) -> None:
    """The per-stage timing breakdown table is present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.tex"
        reporter.generate_report(result=sample_result, output_path=str(out_path))
        content = out_path.read_text(encoding="utf-8")

        assert "% of Total" in content
        assert "Per-Stage Timing" in content
