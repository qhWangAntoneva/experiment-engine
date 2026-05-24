"""Pure-LaTeX report generator for experiment-engine pipelines.

Generates complete LaTeX documents with config snapshots, stage execution
status tables, and figure references — using only string concatenation
(no pylatex or other LaTeX Python bindings).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from experiment_engine.models import ExperimentConfig, PipelineResult, StageStatus

# ═══════════════════════════════════════════════════════════════════════
#  LaTeX escaping helper
# ═══════════════════════════════════════════════════════════════════════


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters for safe inclusion in document text."""
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    # Replace backslash first to avoid double-escaping
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a LaTeX label or safe filename reference."""
    return "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)


# ═══════════════════════════════════════════════════════════════════════
#  Section builders
# ═══════════════════════════════════════════════════════════════════════


def _build_preamble() -> str:
    """Return the LaTeX preamble with standard packages and page geometry."""
    return r"""\documentclass[12pt,a4paper]{article}

% ── Packages ──────────────────────────────────────────────
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage[margin=2.5cm]{geometry}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{longtable}
\usepackage{array}

% ── Colours for status indicators ─────────────────────────
\definecolor{statuscompleted}{HTML}{28a745}
\definecolor{statusfailed}{HTML}{dc3545}
\definecolor{statusrunning}{HTML}{007bff}
\definecolor{statuspending}{HTML}{6c757d}
\definecolor{statusskipped}{HTML}{ffc107}
\definecolor{statuspartial}{HTML}{fd7e14}

% ── Commands ──────────────────────────────────────────────
\newcommand{\statusbox}[2]{\textcolor{#1}{\textbf{#2}}}

\hypersetup{%
    colorlinks=true,
    linkcolor=blue!60!black,
    urlcolor=blue!60!black,
}

"""


def _build_title_page(
    experiment_name: str,
    description: str | None,
    started_at: str | None,
    completed_at: str | None,
    total_duration_ms: float,
) -> str:
    """Generate the title page section."""
    name_esc = _escape_latex(experiment_name)
    desc_esc = _escape_latex(description or "No description provided.")
    today = date.today().strftime("%B %d, %Y")

    lines = [
        r"\begin{titlepage}",
        r"  \centering",
        r"  \vspace*{3cm}",
        rf"  {{\Huge \textbf{{{name_esc}}}}} \\[0.8cm]",
        rf"  {{\Large {desc_esc}}} \\[2cm]",
        r"  {\large Experiment Report} \\[1cm]",
        rf"  Generated: {today} \\",
    ]

    if started_at:
        lines.append(rf"  Started:   {_escape_latex(started_at)} \\")
    if completed_at:
        lines.append(rf"  Completed: {_escape_latex(completed_at)} \\")

    lines.append(rf"  Total duration: {total_duration_ms:.1f} ms \\")
    lines.append(
        r"  \vfill",
    )
    lines.append(r"\end{titlepage}")
    lines.append("")
    return "\n".join(lines)


def _build_config_snapshot(config: ExperimentConfig) -> str:
    """Generate a section with the experiment configuration snapshot."""
    name_esc = _escape_latex(config.name)
    desc_esc = _escape_latex(config.description or "N/A")
    version_esc = _escape_latex(config.version)
    output_dir_esc = _escape_latex(str(config.output_dir or "(default)"))
    verbose_str = "Yes" if config.verbose else "No"

    lines = [
        r"\section{Configuration Snapshot}",
        r"\label{sec:config}",
        "",
        r"\begin{tabular}{ll}",
        r"\toprule",
        r"\textbf{Parameter} & \textbf{Value} \\",
        r"\midrule",
        rf"Name        & {name_esc} \\",
        rf"Description & {desc_esc} \\",
        rf"Version     & {version_esc} \\",
        rf"Output Dir  & {output_dir_esc} \\",
        rf"Verbose     & {verbose_str} \\",
    ]

    if config.global_params:
        params_str = ", ".join(
            f"{_escape_latex(k)}={_escape_latex(str(v))}"
            for k, v in config.global_params.items()
        )
        lines.append(rf"Global Params & \small{{{params_str}}} \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append("")

    # ── Pipeline stages table ──
    if config.stages:
        lines.append(r"\subsection*{Configured Stages}")
        lines.append("")
        lines.extend(
            [
                r"\begin{tabular}{lll}",
                r"\toprule",
                r"\textbf{Stage} & \textbf{Type} & \textbf{Enabled} \\",
                r"\midrule",
            ]
        )
        for stage in config.stages:
            sname = _escape_latex(stage.name)
            stype = _escape_latex(stage.stage_type)
            enabled = "Yes" if stage.enabled else "No"
            lines.append(rf"{sname} & {stype} & {enabled} \\")
        lines.append(r"\bottomrule")
        lines.append(r"\end{tabular}")
        lines.append("")

    # ── Stage parameters ──
    for stage in config.stages:
        if stage.params:
            sname_esc = _escape_latex(stage.name)
            lines.append(rf"\subsubsection*{{{sname_esc} Parameters}}")
            lines.append("")
            lines.extend(
                [
                    r"\begin{tabular}{ll}",
                    r"\toprule",
                    r"\textbf{Parameter} & \textbf{Value} \\",
                    r"\midrule",
                ]
            )
            for k, v in stage.params.items():
                k_esc = _escape_latex(k)
                v_esc = _escape_latex(str(v))
                lines.append(rf"{k_esc} & {v_esc} \\")
            lines.append(r"\bottomrule")
            lines.append(r"\end{tabular}")
            lines.append("")

    return "\n".join(lines)


def _status_latex(status: StageStatus) -> str:
    """Return a LaTeX coloured status command for a given status enum value."""
    mapping: dict[StageStatus, tuple[str, str]] = {
        StageStatus.COMPLETED: ("statuscompleted", "Completed"),
        StageStatus.FAILED: ("statusfailed", "Failed"),
        StageStatus.RUNNING: ("statusrunning", "Running"),
        StageStatus.PENDING: ("statuspending", "Pending"),
        StageStatus.SKIPPED: ("statusskipped", "Skipped"),
    }
    colour, label = mapping.get(status, ("statuspending", str(status.value)))
    return rf"\statusbox{{{colour}}}{{{label}}}"


def _build_execution_results(result: PipelineResult) -> str:
    """Generate the section with stage execution results and status table."""
    lines = [
        r"\section{Execution Results}",
        r"\label{sec:results}",
        "",
        rf"Overall pipeline status: {_status_latex_from_pipeline(result.status)}",
        "",
        rf"Total duration: \textbf{{{result.total_duration_ms:.1f} ms}}",
        rf" ({result.success_count}/{result.total_stages} stages succeeded"
        rf", {result.failure_count} failed)",
        "",
    ]

    if not result.stages:
        lines.append(r"\emph{No stages were executed.}")
        lines.append("")
        return "\n".join(lines)

    # ── Stage status table ──
    lines.extend(
        [
            r"\subsection*{Stage Execution Summary}",
            "",
            r"\begin{tabular}{lcccc}",
            r"\toprule",
            r"\textbf{Stage} & \textbf{Type} & \textbf{Status} & \textbf{Duration} "
            r"& \textbf{Error} \\",
            r"\midrule",
        ]
    )

    for stage in result.stages:
        sname = _escape_latex(stage.stage_name)
        stype = _escape_latex(stage.stage_type)
        status_str = _status_latex(stage.status)
        duration_str = f"{stage.duration_ms:.1f} ms"
        error_str = _escape_latex(stage.error or r"---")
        lines.append(
            rf"{sname} & {stype} & {status_str} & {duration_str} & {error_str} \\"
        )

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append("")

    # ── Detailed per-stage timing ──
    lines.append(r"\subsection*{Per-Stage Timing}")
    lines.append("")
    lines.extend(
        [
            r"\begin{tabular}{lrr}",
            r"\toprule",
            r"\textbf{Stage} & \textbf{Duration (ms)} & \textbf{\% of Total} \\",
            r"\midrule",
        ]
    )
    total = result.total_duration_ms if result.total_duration_ms > 0 else 1
    for stage in result.stages:
        sname = _escape_latex(stage.stage_name)
        pct = (stage.duration_ms / total) * 100.0 if total > 0 else 0.0
        lines.append(
            rf"{sname} & {stage.duration_ms:.1f} & {pct:.1f}\% \\",
        )
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append("")

    return "\n".join(lines)


def _status_latex_from_pipeline(status: Any) -> str:
    """Convert a PipelineStatus to a LaTeX colour-coded box."""
    from experiment_engine.models import PipelineStatus

    mapping: dict[PipelineStatus, tuple[str, str]] = {
        PipelineStatus.COMPLETED: ("statuscompleted", "Completed"),
        PipelineStatus.FAILED: ("statusfailed", "Failed"),
        PipelineStatus.RUNNING: ("statusrunning", "Running"),
        PipelineStatus.PENDING: ("statuspending", "Pending"),
        PipelineStatus.PARTIAL: ("statuspartial", "Partial"),
    }
    colour, label = mapping.get(status, ("statuspending", str(status.value)))
    return rf"\statusbox{{{colour}}}{{{label}}}"


def _build_figures(figure_paths: list[str]) -> str:
    """Generate a figures section with \\includegraphics for each path."""
    if not figure_paths:
        return ""

    lines = [
        r"\section{Figures and Charts}",
        r"\label{sec:figures}",
        "",
    ]

    for i, fpath in enumerate(figure_paths, start=1):
        # Resolve to absolute path for LaTeX
        p = Path(fpath).expanduser().resolve()
        # Use forward slashes for LaTeX cross-platform compatibility
        tex_path = str(p.as_posix())
        label = f"fig:{_sanitize_filename(p.stem)}"

        lines.extend(
            [
                r"\begin{figure}[htbp]",
                r"  \centering",
                rf"  \includegraphics[width=\textwidth]{{{tex_path}}}",
                rf"  \caption{{{_escape_latex(p.stem)}}}",
                rf"  \label{{{label}}}",
                r"\end{figure}",
                "",
            ]
        )

    return "\n".join(lines)


def _build_metadata(metadata: dict[str, Any]) -> str:
    """Generate a metadata section from a dictionary."""
    if not metadata:
        return ""

    lines = [
        r"\section{Metadata}",
        r"\label{sec:metadata}",
        "",
        r"\begin{tabular}{ll}",
        r"\toprule",
        r"\textbf{Key} & \textbf{Value} \\",
        r"\midrule",
    ]

    for k, v in metadata.items():
        k_esc = _escape_latex(k)
        v_esc = _escape_latex(str(v))
        lines.append(rf"{k_esc} & {v_esc} \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
#  Main reporter class
# ═══════════════════════════════════════════════════════════════════════


class LaTeXReporter:
    """Generate LaTeX experiment reports from pipeline results.

    Produces complete, self-contained LaTeX documents using pure string
    generation. No external LaTeX Python libraries are required.

    The report includes:
    - Title page with experiment name, description, and timing
    - Configuration snapshot (when an ExperimentConfig is provided)
    - Stage execution status table with colour-coded results
    - Per-stage timing breakdown
    - Included figures (when figure paths are provided)
    - Pipeline metadata dictionary
    """

    def generate_report(
        self,
        result: PipelineResult,
        config: ExperimentConfig | None = None,
        figure_paths: list[str] | None = None,
        output_path: str = "report.tex",
    ) -> str:
        """Generate a complete LaTeX report document.

        Args:
            result: The pipeline execution result to document.
            config: Optional experiment configuration for the config snapshot
                section.
            figure_paths: Optional list of file paths to images/plots to include
                in the figures section.
            output_path: Destination path for the generated ``.tex`` file.

        Returns:
            The absolute path to the generated ``.tex`` file.

        Raises:
            OSError: If the output directory cannot be created or the file
                cannot be written.
        """
        out = Path(output_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        document = self._build_document(result, config, figure_paths or [])

        out.write_text(document, encoding="utf-8")
        return str(out)

    def _build_document(
        self,
        result: PipelineResult,
        config: ExperimentConfig | None,
        figure_paths: list[str],
    ) -> str:
        """Assemble the full LaTeX document string."""
        parts: list[str] = []

        # Preamble
        parts.append(_build_preamble())

        # Document begin
        parts.append(r"\begin{document}")
        parts.append("")

        # Title page
        parts.append(
            _build_title_page(
                experiment_name=result.experiment_name,
                description=config.description if config else None,
                started_at=result.started_at,
                completed_at=result.completed_at,
                total_duration_ms=result.total_duration_ms,
            )
        )

        # Table of contents
        parts.append(r"\tableofcontents")
        parts.append(r"\newpage")
        parts.append("")

        # Section 1: Config snapshot
        if config is not None:
            parts.append(_build_config_snapshot(config))
            parts.append("")

        # Section 2: Execution results
        parts.append(_build_execution_results(result))
        parts.append("")

        # Section 3: Figures
        if figure_paths:
            parts.append(_build_figures(figure_paths))
            parts.append("")

        # Section 4: Metadata
        metadata = result.metadata or {}
        if metadata:
            parts.append(_build_metadata(metadata))
            parts.append("")

        # Document end
        parts.append(r"\end{document}")
        parts.append("")

        return "\n".join(parts)

    def compile_pdf(
        self,
        tex_path: str,
        output_dir: str | None = None,
        runs: int = 2,
    ) -> str | None:
        """Compile a ``.tex`` file into PDF using ``pdflatex``.

        This method is optional — it only works if ``pdflatex`` is available
        on the system PATH. The ``.tex`` file output from
        :meth:`generate_report` is always the primary deliverable.

        Args:
            tex_path: Path to the ``.tex`` file to compile.
            output_dir: Directory for PDF output (default: same as the tex
                file).
            runs: Number of ``pdflatex`` passes (default: 2, for cross-refs).

        Returns:
            Path to the generated ``.pdf`` file, or ``None`` if ``pdflatex``
            is not available or compilation failed.
        """
        # Check if pdflatex is available
        if not shutil.which("pdflatex"):
            return None

        tex = Path(tex_path).expanduser().resolve()
        out_dir = Path(output_dir).expanduser().resolve() if output_dir else tex.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        # We compile in a temporary working directory to avoid clobbering
        # the user's workspace with auxiliary LaTeX files.
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_tex = Path(tmpdir) / tex.name
            tmp_tex.write_text(tex.read_text(encoding="utf-8"), encoding="utf-8")

            for _ in range(runs):
                proc = subprocess.run(
                    [
                        "pdflatex",
                        "-interaction=nonstopmode",
                        f"-output-directory={tmpdir}",
                        str(tmp_tex),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if proc.returncode != 0:
                    # Check if a PDF was produced despite the error
                    pdf_candidate = Path(tmpdir) / tex.with_suffix(".pdf").name
                    if not pdf_candidate.exists():
                        return None

            # Copy the PDF to the target output directory
            pdf_name = tex.with_suffix(".pdf").name
            src_pdf = Path(tmpdir) / pdf_name
            if src_pdf.exists():
                dst_pdf = out_dir / pdf_name
                dst_pdf.write_bytes(src_pdf.read_bytes())
                return str(dst_pdf)

        return None
