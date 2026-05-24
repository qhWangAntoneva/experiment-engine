"""LaTeX report generation for experiment-engine pipelines.

Provides a LaTeXReporter class that produces complete LaTeX documents
with config snapshots, stage execution status tables, and figure references —
without relying on external LaTeX Python libraries (pure string generation).
"""

from __future__ import annotations

from experiment_engine.report.latex_reporter import LaTeXReporter

__all__ = ["LaTeXReporter"]
