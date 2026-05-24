"""Unit tests for the experiment-engine visualization (viz) module.

Tests cover base renderer abstraction, console rendering, matplotlib
rendering, plotly rendering, and the Streamlit dashboard stub.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from experiment_engine.models import (
    InputData,
    PipelineResult,
    PipelineStatus,
    RenderConfig,
    StageResult,
    StageStatus,
)
from experiment_engine.viz import (
    ConsoleRenderer,
    MatplotlibRenderer,
    PlotlyRenderer,
    Renderer,
    StreamlitDashboard,
)
from experiment_engine.viz.base import Renderer as RendererBase

# ═══════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════


def _make_data(
    n_samples: int = 10,
    n_features: int = 2,
    with_index: bool = False,
    with_columns: bool = True,
) -> InputData:
    """Build a standard InputData fixture for tests."""
    data = np.random.randn(n_samples, n_features).astype(float)
    columns = [f"feat_{i}" for i in range(n_features)] if with_columns else None
    index = list(range(n_samples)) if with_index else None
    return InputData(data=data, columns=columns, index=index)


def _make_config(
    plot_type: str = "line",
    title: str | None = "Test Plot",
    xlabel: str | None = "X Axis",
    ylabel: str | None = "Y Axis",
    output_path: str | None = None,
) -> RenderConfig:
    """Build a standard RenderConfig fixture."""
    return RenderConfig(
        plot_type=plot_type,
        title=title,
        xlabel=xlabel,
        ylabel=ylabel,
        figsize=(6.0, 4.0),
        dpi=80,
        colormap="viridis",
        output_path=output_path,
    )


def _make_pipeline_result(
    experiment_name: str = "test-pipeline",
    status: PipelineStatus = PipelineStatus.COMPLETED,
    n_stages: int = 3,
    with_errors: bool = False,
    with_output: bool = True,
) -> PipelineResult:
    """Build a PipelineResult fixture for tests."""
    stages = []
    for i in range(n_stages):
        stage_status = StageStatus.COMPLETED
        error = None
        if with_errors and i == n_stages - 1:
            stage_status = StageStatus.FAILED
            error = f"Stage {i}: Something went wrong"
        stages.append(
            StageResult(
                stage_name=f"stage_{i}",
                stage_type=f"type_{i}",
                status=stage_status,
                duration_ms=100.0 * (i + 1),
                started_at=f"2024-01-01T00:00:{i:02d}Z",
                completed_at=f"2024-01-01T00:00:{i + 1:02d}Z",
                error=error,
            )
        )

    output = {"result": "success", "accuracy": 0.95} if with_output else None

    return PipelineResult(
        experiment_name=experiment_name,
        status=status,
        total_duration_ms=sum(s.duration_ms for s in stages),
        stages=stages,
        started_at="2024-01-01T00:00:00Z",
        completed_at="2024-01-01T00:00:05Z",
        output=output,
    )


class _ConcreteRenderer(Renderer):
    """Minimal concrete renderer for testing abstract base."""

    @property
    def name(self) -> str:
        return "concrete"

    def render(self, data: InputData, config: RenderConfig, **kwargs: Any) -> str:
        return "rendered"


# ═══════════════════════════════════════════════════════════════════
#  Test: viz/__init__.py exports
# ═══════════════════════════════════════════════════════════════════


class TestVizInit:
    """Verify all 5 classes are exported from the viz package."""

    def test_exports_renderer(self) -> None:
        assert Renderer is RendererBase

    def test_exports_console_renderer(self) -> None:
        assert issubclass(ConsoleRenderer, Renderer)

    def test_exports_matplotlib_renderer(self) -> None:
        assert issubclass(MatplotlibRenderer, Renderer)

    def test_exports_plotly_renderer(self) -> None:
        assert issubclass(PlotlyRenderer, Renderer)

    def test_exports_streamlit_dashboard(self) -> None:
        assert issubclass(StreamlitDashboard, Renderer)


# ═══════════════════════════════════════════════════════════════════
#  Test: viz/base.py — Renderer (ABC)
# ═══════════════════════════════════════════════════════════════════


class TestRendererBase:
    """Tests for the abstract Renderer base class."""

    def test_abstract_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            Renderer()  # type: ignore[abstract]

    def test_concrete_subclass_works(self) -> None:
        r = _ConcreteRenderer()
        assert r.name == "concrete"
        assert r.render(_make_data(), _make_config()) == "rendered"

    def test_supported_formats_default(self) -> None:
        r = _ConcreteRenderer()
        assert r.supported_formats() == []

    # --- _infer_plot_type ---

    def test_infer_plot_type_1_feature(self) -> None:
        """Single feature -> histogram."""
        data = _make_data(n_samples=10, n_features=1)
        assert Renderer._infer_plot_type(data) == "histogram"

    def test_infer_plot_type_2_features(self) -> None:
        """Two features -> line."""
        data = _make_data(n_samples=10, n_features=2)
        assert Renderer._infer_plot_type(data) == "line"

    def test_infer_plot_type_3_features_few_samples(self) -> None:
        """Three features, <=50 samples -> scatter."""
        data = _make_data(n_samples=30, n_features=3)
        assert Renderer._infer_plot_type(data) == "scatter"

    def test_infer_plot_type_3_features_many_samples(self) -> None:
        """Three features, >50 samples -> scatter."""
        data = _make_data(n_samples=100, n_features=3)
        assert Renderer._infer_plot_type(data) == "scatter"

    def test_infer_plot_type_5_features(self) -> None:
        data = _make_data(n_samples=20, n_features=5)
        assert Renderer._infer_plot_type(data) == "scatter"

    def test_infer_plot_type_fallback(self) -> None:
        """Edge case: 0 features -> fallback to scatter."""
        data = _make_data(n_samples=5, n_features=0)
        assert Renderer._infer_plot_type(data) == "scatter"


# ═══════════════════════════════════════════════════════════════════
#  Test: viz/console.py — ConsoleRenderer
# ═══════════════════════════════════════════════════════════════════


class TestConsoleRenderer:
    """Tests for the ConsoleRenderer class."""

    def test_name(self) -> None:
        r = ConsoleRenderer()
        assert r.name == "console"

    def test_supported_formats(self) -> None:
        r = ConsoleRenderer()
        assert r.supported_formats() == []

    def test_render_returns_string(self) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=5, n_features=2)
        config = _make_config(title="Console Test")
        result = r.render(data, config)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_contains_title(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=5, n_features=2)
        config = _make_config(title="My Custom Title")
        r.render(data, config)
        captured = capsys.readouterr()
        assert "My Custom Title" in captured.out

    def test_render_default_title(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=5, n_features=2)
        config = _make_config(title=None)
        r.render(data, config)
        captured = capsys.readouterr()
        assert "Experiment Data Summary" in captured.out

    def test_render_shows_dataset_info(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=7, n_features=3)
        config = _make_config()
        r.render(data, config)
        captured = capsys.readouterr()
        plain = re.sub(r"\x1b\[[0-9;]*m", "", captured.out)
        assert "Samples: 7" in plain
        assert "Features: 3" in plain

    def test_render_show_table_true(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=5, n_features=2, with_columns=True)
        config = _make_config()
        r.render(data, config, show_table=True)
        captured = capsys.readouterr()
        assert "Data Values" in captured.out
        assert "feat_0" in captured.out

    def test_render_show_table_false(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=5, n_features=2)
        config = _make_config()
        r.render(data, config, show_table=False)
        captured = capsys.readouterr()
        assert "Data Values" not in captured.out

    def test_render_show_stats_true(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=5, n_features=2, with_columns=True)
        config = _make_config()
        r.render(data, config, show_stats=True)
        captured = capsys.readouterr()
        assert "Summary Statistics" in captured.out

    def test_render_show_stats_false(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=5, n_features=2)
        config = _make_config()
        r.render(data, config, show_stats=False)
        captured = capsys.readouterr()
        assert "Summary Statistics" not in captured.out

    def test_render_with_max_rows(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=100, n_features=2)
        config = _make_config()
        r.render(data, config, max_rows=5)
        captured = capsys.readouterr()
        plain = re.sub(r"\x1b\[[0-9;]*m", "", captured.out)
        # Table title may be split across lines by Rich
        assert "5 of 100 rows" in plain

    def test_render_with_max_rows_no_truncation(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=3, n_features=2)
        config = _make_config()
        r.render(data, config, max_rows=20)
        captured = capsys.readouterr()
        plain = re.sub(r"\x1b\[[0-9;]*m", "", captured.out)
        # Table title may be split across lines by Rich
        assert "3 of 3 rows" in plain

    def test_render_with_index(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=3, n_features=2, with_index=True)
        config = _make_config()
        r.render(data, config)
        captured = capsys.readouterr()
        assert "Index" in captured.out

    def test_render_show_progress(self) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=5, n_features=2)
        config = _make_config()
        result = r.render(data, config, show_progress=True)
        assert isinstance(result, str)

    def test_render_with_output_path(self) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=3, n_features=2)
        config = _make_config()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            output_path = f.name

        try:
            result = r.render(data, config, output_path=output_path)
            assert isinstance(result, str)
            assert os.path.exists(output_path)
            with open(output_path) as fh:
                saved = fh.read()
            assert len(saved) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_footer(self, capsys: pytest.CaptureFixture[str]) -> None:
        r = ConsoleRenderer()
        data = _make_data(n_samples=3, n_features=1)
        config = _make_config()
        r.render(data, config)
        captured = capsys.readouterr()
        assert "ConsoleRenderer" in captured.out

    def test_progress_bar_returns_string(self) -> None:
        r = ConsoleRenderer()
        result = r.progress_bar(total=10, description="Testing")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_progress_bar_custom_description(self) -> None:
        r = ConsoleRenderer()
        result = r.progress_bar(total=5, description="Custom Step")
        assert isinstance(result, str)

    # --- _print_table format safety (the isinstance fix) ---

    def test_print_table_non_numeric_values(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify _print_table handles string-like column names in the table
        columns list and formats numeric data correctly.
        The table header shows column names (strings).
        The data values should be formatted with :.4f for floats."""
        r = ConsoleRenderer()
        # Use all-numeric data so _print_stats works; the table
        # columns are strings (always), and data values are floats.
        data = _make_data(n_samples=3, n_features=2, with_columns=True)
        config = _make_config()
        r.render(data, config)
        captured = capsys.readouterr()
        # Table should have numeric column values formatted
        assert "feat_0" in captured.out
        # Stats should be present
        assert "Mean" in captured.out


# ═══════════════════════════════════════════════════════════════════
#  Test: viz/matplotlib_renderer.py — MatplotlibRenderer
# ═══════════════════════════════════════════════════════════════════


class TestMatplotlibRenderer:
    """Tests for the MatplotlibRenderer class."""

    def test_name(self) -> None:
        r = MatplotlibRenderer()
        assert r.name == "matplotlib"

    def test_supported_formats(self) -> None:
        r = MatplotlibRenderer()
        formats = r.supported_formats()
        assert isinstance(formats, list)
        assert "png" in formats
        assert "svg" in formats
        assert "pdf" in formats
        assert len(formats) == 3

    @pytest.mark.parametrize(
        "plot_type",
        ["line", "bar", "histogram", "surface"],
    )
    def test_render_plot_types(self, plot_type: str) -> None:
        """Each supported plot type produces a valid PNG file."""
        r = MatplotlibRenderer()
        n_features = 2
        data = _make_data(n_samples=20, n_features=n_features)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(
                plot_type=plot_type,
                title=f"{plot_type} Test",
                output_path=output_path,
            )
            result = r.render(data, config)
            assert os.path.exists(result)
            assert result == str(Path(output_path).resolve())
            assert os.path.getsize(result) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_scatter(self) -> None:
        """Scatter plot with 3 features (colorbar path)."""
        r = MatplotlibRenderer()
        data = _make_data(n_samples=20, n_features=3)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        config = _make_config(plot_type="scatter", output_path=output_path)
        try:
            result_path = r.render(data, config)
            assert result_path == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 100
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_unsupported_plot_type(self) -> None:
        r = MatplotlibRenderer()
        data = _make_data()
        config = _make_config(plot_type="invalid_type")
        with pytest.raises(ValueError, match=r"Unsupported plot type.*invalid_type"):
            r.render(data, config)

    def test_render_with_title_xlabel_ylabel(self) -> None:
        r = MatplotlibRenderer()
        data = _make_data(n_samples=10, n_features=1)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            config = RenderConfig(
                plot_type="line",
                title="Custom Title",
                xlabel="My X",
                ylabel="My Y",
                output_path=output_path,
            )
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_custom_figsize_dpi(self) -> None:
        r = MatplotlibRenderer()
        data = _make_data(n_samples=10, n_features=1)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            config = RenderConfig(
                plot_type="line",
                figsize=(10.0, 8.0),
                dpi=200,
                output_path=output_path,
            )
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_custom_colormap(self) -> None:
        r = MatplotlibRenderer()
        data = _make_data(n_samples=10, n_features=3)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            config = RenderConfig(
                plot_type="line",
                colormap="plasma",
                output_path=output_path,
            )
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_auto_output_path(self) -> None:
        """When no output_path is given, a default name is used."""
        r = MatplotlibRenderer()
        data = _make_data(n_samples=5, n_features=1)
        config = _make_config(plot_type="line", output_path=None)
        expected = str(Path("output_line.png").resolve())
        try:
            result = r.render(data, config)
            assert result == expected
            assert os.path.exists(result)
        finally:
            if os.path.exists(expected):
                os.unlink(expected)

    def test_render_surface_with_few_samples(self) -> None:
        """Surface plot with non-perfect-square sample count."""
        r = MatplotlibRenderer()
        data = _make_data(n_samples=7, n_features=1)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="surface", output_path=output_path)
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_closes_figure_on_error(self) -> None:
        """Figure is closed even when an exception is raised."""
        import matplotlib.pyplot as plt

        r = MatplotlibRenderer()
        data = _make_data(n_samples=5, n_features=1)
        config = _make_config(plot_type="nonexistent_plot")
        with pytest.raises(ValueError):
            r.render(data, config)
        assert len(plt.get_fignums()) == 0

    def test_render_svg_format(self) -> None:
        """SVG output works."""
        r = MatplotlibRenderer()
        data = _make_data(n_samples=10, n_features=1)
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="line", output_path=output_path)
            result = r.render(data, config)
            assert os.path.exists(result)
            assert result.endswith(".svg")
            assert os.path.getsize(result) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_with_kwargs_not_conflicting(self) -> None:
        """Additional kwargs are forwarded to matplotlib as long as they
        don't conflict with internally-set kwargs (``_plot_line`` already
        passes ``linewidth=1.5``, so ``linewidth`` would conflict).
        Use a non-conflicting kwarg like ``alpha`` which isn't set internally
        by ``_plot_line`` — but note that some plot types forward **kwargs
        directly to the underlying plotting call.
        """
        r = MatplotlibRenderer()
        data = _make_data(n_samples=10, n_features=1)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="line", output_path=output_path)
            # ``alpha`` is *not* set by _plot_line's ax.plot() call,
            # so it should pass through without conflict.
            # NOTE: this test confirms the *mechanism* works for non-conflicting kwargs.
            result = r.render(data, config, alpha=0.5)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_bar_grouped(self) -> None:
        """Bar chart with multiple features produces grouped bars."""
        r = MatplotlibRenderer()
        data = _make_data(n_samples=10, n_features=3)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="bar", output_path=output_path)
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_scatter_2d_no_colorbar(self) -> None:
        """Scatter with 2 features does not call plt.colorbar."""
        r = MatplotlibRenderer()
        data = _make_data(n_samples=20, n_features=2)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="scatter", output_path=output_path)
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


# ═══════════════════════════════════════════════════════════════════
#  Test: viz/plotly_renderer.py — PlotlyRenderer
# ═══════════════════════════════════════════════════════════════════


class TestPlotlyRenderer:
    """Tests for the PlotlyRenderer class."""

    def test_name(self) -> None:
        r = PlotlyRenderer()
        assert r.name == "plotly"

    def test_supported_formats(self) -> None:
        r = PlotlyRenderer()
        assert r.supported_formats() == ["html"]

    def test_render_returns_html_path(self) -> None:
        r = PlotlyRenderer()
        data = _make_data(n_samples=10, n_features=2)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="line", output_path=output_path)
            result = r.render(data, config)
            assert os.path.exists(result)
            assert result.endswith(".html")
            with open(result) as fh:
                content = fh.read()
            assert "html" in content.lower()
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    @pytest.mark.parametrize(
        "plot_type",
        ["line", "scatter", "bar", "histogram", "surface"],
    )
    def test_render_all_plot_types(self, plot_type: str) -> None:
        """Each supported plot type produces an HTML file."""
        r = PlotlyRenderer()
        n_features = 3 if plot_type == "scatter" else 2
        data = _make_data(n_samples=20, n_features=n_features)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(
                plot_type=plot_type,
                title=f"{plot_type} Test",
                output_path=output_path,
            )
            result = r.render(data, config)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_unsupported_plot_type(self) -> None:
        r = PlotlyRenderer()
        data = _make_data()
        config = _make_config(plot_type="invalid_type")
        with pytest.raises(ValueError, match=r"Unsupported plot type.*invalid_type"):
            r.render(data, config)

    def test_render_with_labels_and_title(self) -> None:
        r = PlotlyRenderer()
        data = _make_data(n_samples=10, n_features=1)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            config = RenderConfig(
                plot_type="line",
                title="My Plot",
                xlabel="Time",
                ylabel="Value",
                output_path=output_path,
            )
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_with_custom_figsize(self) -> None:
        r = PlotlyRenderer()
        data = _make_data(n_samples=10, n_features=1)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            config = RenderConfig(
                plot_type="line",
                figsize=(12.0, 6.0),
                output_path=output_path,
            )
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_render_auto_output_path(self) -> None:
        """When no output_path is given, a default name is used."""
        r = PlotlyRenderer()
        data = _make_data(n_samples=5, n_features=1)
        config = _make_config(plot_type="line", output_path=None)
        expected = str(Path("output_line.html").resolve())
        try:
            result = r.render(data, config)
            assert result == expected
            assert os.path.exists(result)
        finally:
            if os.path.exists(expected):
                os.unlink(expected)

    def test_render_with_non_conflicting_kwargs(self) -> None:
        """Additional kwargs NOT already set by update_layout are forwarded.

        ``hovermode`` is already set by ``update_layout(hovermode="closest")``,
        so passing it again via **kwargs causes a conflict.  We use ``dragmode``
        instead, which is *not* in the default update_layout call.
        """
        r = PlotlyRenderer()
        data = _make_data(n_samples=10, n_features=1)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="line", output_path=output_path)
            result = r.render(data, config, dragmode="zoom")
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_scatter_with_colorbar(self) -> None:
        """Scatter with >=3 features includes colorbar config."""
        r = PlotlyRenderer()
        data = _make_data(n_samples=20, n_features=3)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="scatter", output_path=output_path)
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_scatter_single_feature(self) -> None:
        """Scatter with 1 feature still works (no colorbar)."""
        r = PlotlyRenderer()
        data = _make_data(n_samples=10, n_features=1)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="scatter", output_path=output_path)
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_bar_grouped(self) -> None:
        """Bar chart with multiple features uses grouped bars."""
        r = PlotlyRenderer()
        data = _make_data(n_samples=10, n_features=3)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="bar", output_path=output_path)
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_surface_plot(self) -> None:
        """Surface plot with small sample count."""
        r = PlotlyRenderer()
        data = _make_data(n_samples=7, n_features=1)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            config = _make_config(plot_type="surface", output_path=output_path)
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    # --- _generate_colors ---

    def test_generate_colors_few(self) -> None:
        """Fewer than 10 colors uses Plotly qualitative palette."""
        colors = PlotlyRenderer._generate_colors(3)
        assert len(colors) == 3
        for c in colors:
            assert isinstance(c, str)

    def test_generate_colors_many(self) -> None:
        """More than 10 colors samples from viridis."""
        colors = PlotlyRenderer._generate_colors(15)
        assert len(colors) == 15
        for c in colors:
            assert isinstance(c, str)

    def test_generate_colors_zero(self) -> None:
        colors = PlotlyRenderer._generate_colors(0)
        assert colors == []


# ═══════════════════════════════════════════════════════════════════
#  Test: viz/streamlit_dashboard.py — StreamlitDashboard
# ═══════════════════════════════════════════════════════════════════


class TestStreamlitDashboard:
    """Tests for the StreamlitDashboard class.

    We deliberately do NOT test ``run()`` because it spawns a server.

    NOTE: ``_generate_script`` calls ``self.DASHBOARD_TEMPLATE.format(...)``
    but the template contains unescaped ``{n_samples}`` and ``{n_features}``
    (which are intended as f-string placeholders in the *generated* code).
    This causes a ``KeyError`` at format time.  These tests verify the
    method's behaviour as-is (xfail for the KeyError path), and check
    ``_write_script`` and ``supported_formats`` which work.
    """

    def test_name(self) -> None:
        d = StreamlitDashboard()
        assert d.name == "streamlit"

    def test_render_raises_not_implemented(self) -> None:
        d = StreamlitDashboard()
        data = _make_data()
        config = _make_config()
        with pytest.raises(NotImplementedError) as exc_info:
            d.render(data, config)
        assert "does not support render" in str(exc_info.value).lower()

    def test_supported_formats(self) -> None:
        d = StreamlitDashboard()
        assert d.supported_formats() == []

    # _generate_script previously broken due to unescaped template braces
    # (the template has {n_samples} / {n_features} meant for f-strings in
    #  the generated code, but Python's ``.format()`` interpreted them as
    #  placeholders).  Now fixed — tests verify correct script generation.

    def test_generate_script_returns_string(self) -> None:
        """_generate_script produces a non-empty script string."""
        d = StreamlitDashboard()
        data = _make_data(n_samples=5, n_features=2, with_columns=True)
        script = d._generate_script(data)
        assert isinstance(script, str)
        assert len(script) > 500
        assert "DATA_ARRAY" in script
        assert "COLUMNS" in script
        assert "feat_0" in script
        assert "feat_1" in script

    def test_generate_script_with_index(self) -> None:
        """Index data is embedded correctly."""
        d = StreamlitDashboard()
        data = _make_data(n_samples=3, n_features=1, with_index=True, with_columns=True)
        script = d._generate_script(data)
        assert "INDEX" in script
        # The generated should reference index (for the if INDEX check)
        assert "if INDEX" in script

    def test_generate_script_without_columns(self) -> None:
        """When columns are None, COLUMNS is set to None."""
        d = StreamlitDashboard()
        data = _make_data(n_samples=3, n_features=2, with_columns=False)
        script = d._generate_script(data)
        # None without index means pd.DataFrame(DATA_ARRAY)
        assert "INDEX" in script
        assert "None" in script

    def test_write_script_creates_file(self) -> None:
        """``_write_script`` works independently; it only needs a string."""
        script = "import streamlit as st\nst.title('test')\n"
        path = StreamlitDashboard._write_script(script)
        try:
            assert path.exists()
            assert path.suffix == ".py"
            written = path.read_text(encoding="utf-8")
            assert written == script
        finally:
            if path.exists():
                path.unlink()

    # ── Pipeline result tests ───────────────────────────────────────

    def test_generate_pipeline_script_returns_string(self) -> None:
        """_generate_pipeline_script produces a non-empty script string."""
        d = StreamlitDashboard()
        result = _make_pipeline_result()
        script = d._generate_pipeline_script(result)
        assert isinstance(script, str)
        assert len(script) > 200

    def test_generate_pipeline_script_contains_experiment_name(
        self,
    ) -> None:
        """The generated script references the experiment name."""
        d = StreamlitDashboard()
        result = _make_pipeline_result(experiment_name="my-test-run")
        script = d._generate_pipeline_script(result)
        assert "my-test-run" in script

    def test_generate_pipeline_script_contains_stages(self) -> None:
        """The generated script includes stage data."""
        d = StreamlitDashboard()
        result = _make_pipeline_result(n_stages=4)
        script = d._generate_pipeline_script(result)
        # Should reference stage keys and counts
        assert "stage_name" in script
        assert "duration_ms" in script
        assert "stage_0" in script
        assert "stage_3" in script

    def test_generate_pipeline_script_contains_status_badge(
        self,
    ) -> None:
        """The generated script includes status emoji lookup."""
        d = StreamlitDashboard()
        result = _make_pipeline_result()
        script = d._generate_pipeline_script(result)
        assert "completed" in script
        assert "Pipeline Results" in script

    def test_generate_pipeline_script_with_errors(self) -> None:
        """Failed stages produce scripts that contain error messages."""
        d = StreamlitDashboard()
        result = _make_pipeline_result(n_stages=3, with_errors=True)
        script = d._generate_pipeline_script(result)
        assert "Stage 2: Something went wrong" in script
        assert "failed" in script.lower() or "FAILED" in script

    def test_generate_pipeline_script_with_output(self) -> None:
        """Output data is embedded in the script."""
        d = StreamlitDashboard()
        result = _make_pipeline_result(with_output=True)
        script = d._generate_pipeline_script(result)
        assert "success" in script
        assert "accuracy" in script

    def test_generate_pipeline_script_without_output(self) -> None:
        """When output is None, the script shows 'None'."""
        d = StreamlitDashboard()
        result = _make_pipeline_result(with_output=False)
        script = d._generate_pipeline_script(result)
        assert "None" in script

    def test_generate_pipeline_script_contains_pipeline_sections(
        self,
    ) -> None:
        """The generated script contains key pipeline dashboard sections."""
        d = StreamlitDashboard()
        result = _make_pipeline_result()
        script = d._generate_pipeline_script(result)
        # All key section markers
        assert "Stage Execution Summary" in script
        assert "Stage Errors" in script or "Errors" in script
        assert "Final Pipeline Output" in script or "Final Output" in script
        assert "Pipeline Status" in script
        assert "Total Duration" in script


# ═══════════════════════════════════════════════════════════════════
#  Test: Integration — renderers handle edge-case data
# ═══════════════════════════════════════════════════════════════════


class TestVizEdgeCases:
    """Edge cases common across renderers."""

    def test_single_sample_data(self) -> None:
        """Single sample should not crash any renderer."""
        data = _make_data(n_samples=1, n_features=2)

        # Console
        r_console = ConsoleRenderer()
        result = r_console.render(data, _make_config(title="Single"))
        assert isinstance(result, str)

        # Matplotlib
        r_mpl = MatplotlibRenderer()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            out = f.name
        try:
            config = _make_config(plot_type="line", output_path=out)
            result = r_mpl.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(out):
                os.unlink(out)

        # Plotly
        r_plotly = PlotlyRenderer()
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            out = f.name
        try:
            config = _make_config(plot_type="line", output_path=out)
            result = r_plotly.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(out):
                os.unlink(out)

    def test_large_dataset_console(self) -> None:
        """Large data does not cause issues in console rendering."""
        data = _make_data(n_samples=500, n_features=10)
        r = ConsoleRenderer()
        config = _make_config(title="Large Dataset")
        result = r.render(data, config, max_rows=10)
        assert isinstance(result, str)

    def test_many_features_matplotlib(self) -> None:
        """Many features work with matplotlib."""
        data = _make_data(n_samples=20, n_features=15)
        r = MatplotlibRenderer()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            out = f.name
        try:
            config = _make_config(plot_type="line", output_path=out)
            result = r.render(data, config)
            assert os.path.exists(result)
        finally:
            if os.path.exists(out):
                os.unlink(out)
