"""Report generation for experiment-engine pipelines.

Provides:
- LaTeXReporter: complete LaTeX documents (config snapshots, stage tables, figure refs).
- QCALaTeXReporter: QCA-specific LaTeX (truth table, solutions, necessity, robustness).
- QCADocxReporter: Chinese Word .docx reports (python-docx, lazily installed via micropip).
"""

from __future__ import annotations

from experiment_engine.report.docx_reporter import QCADocxReporter
from experiment_engine.report.latex_reporter import LaTeXReporter
from experiment_engine.report.qca_reporter import QCALaTeXReporter

__all__ = ["LaTeXReporter", "QCADocxReporter", "QCALaTeXReporter"]
