"""Plotly-based renderer for experiment-engine.

Produces interactive HTML visualisations with support for line plots,
scatter plots, bar charts, histograms, and 3D surface plots. Outputs
are self-contained HTML files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from experiment_engine.models import InputData, RenderConfig
from experiment_engine.viz.base import Renderer


class PlotlyRenderer(Renderer):
    """Renders experiment data using Plotly.

    Produces interactive HTML files with hover tooltips, zoom, pan,
    and other interactive features.

    Examples:
        >>> renderer = PlotlyRenderer()
        >>> path = renderer.render(data, VisualizationConfig(plot_type="scatter"))
    """

    @property
    def name(self) -> str:
        return "plotly"

    def supported_formats(self) -> List[str]:
        return ["html"]

    def render(
        self,
        data: InputData,
        config: RenderConfig,
        **kwargs: Any,
    ) -> str:
        """Render data to an interactive HTML file.

        Args:
            data: Input data to visualise.
            config: Visualisation configuration.
            **kwargs: Additional keyword arguments forwarded to Plotly's
                figure update methods.

        Returns:
            str: Path to the saved HTML file.
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        plot_type = config.plot_type
        x = np.arange(data.n_samples) if data.index is None else np.array(data.index, dtype=float)
        colors = self._generate_colors(data.n_features)

        fig: Optional[go.Figure] = None

        if plot_type == "line":
            fig = self._build_line(data, x, colors, config)
        elif plot_type == "scatter":
            fig = self._build_scatter(data, colors, config)
        elif plot_type == "bar":
            fig = self._build_bar(data, x, colors, config)
        elif plot_type == "histogram":
            fig = self._build_histogram(data, colors, config)
        elif plot_type == "surface":
            fig = self._build_surface(data, config)
        else:
            raise ValueError(
                f"Unsupported plot type '{plot_type}'. "
                f"Supported: line, scatter, bar, histogram, surface"
            )

        if fig is None:
            raise RuntimeError("Figure creation failed")

        # Apply layout
        fig.update_layout(
            title=config.title or None,
            xaxis_title=config.xlabel or None,
            yaxis_title=config.ylabel or None,
            template="plotly_white",
            width=config.figsize[0] * 80,
            height=config.figsize[1] * 80,
            hovermode="closest",
            **kwargs,
        )

        output_path = config.output_path or f"output_{plot_type}.html"
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fig.write_html(
            str(path),
            include_plotlyjs="cdn",
            full_html=True,
        )

        return str(path.resolve())

    # ------------------------------------------------------------------
    # Plot type implementations
    # ------------------------------------------------------------------

    def _build_line(
        self,
        data: InputData,
        x: np.ndarray,
        colors: List[str],
        config: VisualizationConfig,
    ) -> "go.Figure":
        """Build an interactive line plot."""
        import plotly.graph_objects as go

        fig = go.Figure()
        for i in range(data.n_features):
            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=data.data[:, i],
                    mode="lines",
                    name=data.columns[i] if data.columns else f"feature_{i}",
                    line=dict(color=colors[i % len(colors)], width=2),
                )
            )
        return fig

    def _build_scatter(
        self,
        data: InputData,
        colors: List[str],
        config: VisualizationConfig,
    ) -> "go.Figure":
        """Build an interactive scatter plot."""
        import plotly.graph_objects as go

        fig = go.Figure()

        if data.n_features >= 2:
            fig.add_trace(
                go.Scatter(
                    x=data.data[:, 0],
                    y=data.data[:, 1],
                    mode="markers",
                    marker=dict(
                        size=6,
                        color=data.data[:, 2] if data.n_features >= 3 else colors[0],
                        colorscale=config.colormap,
                        showscale=data.n_features >= 3,
                        colorbar=dict(
                            title=data.columns[2] if len(data.columns) > 2 else ""
                        ) if data.n_features >= 3 else None,
                    ),
                    text=[f"Point {i}" for i in range(data.n_samples)],
                    name=data.columns[0] if data.columns else "data",
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=np.arange(data.n_samples),
                    y=data.data[:, 0],
                    mode="markers",
                    marker=dict(size=6, color=colors[0]),
                    name=data.columns[0] if data.columns else "data",
                )
            )
        return fig

    def _build_bar(
        self,
        data: InputData,
        x: np.ndarray,
        colors: List[str],
        config: VisualizationConfig,
    ) -> "go.Figure":
        """Build an interactive bar chart."""
        import plotly.graph_objects as go

        fig = go.Figure()
        for i in range(data.n_features):
            fig.add_trace(
                go.Bar(
                    x=x,
                    y=data.data[:, i],
                    name=data.columns[i] if data.columns else f"feature_{i}",
                    marker_color=colors[i % len(colors)],
                    opacity=0.85,
                )
            )
        fig.update_layout(barmode="group")
        return fig

    def _build_histogram(
        self,
        data: InputData,
        colors: List[str],
        config: VisualizationConfig,
    ) -> "go.Figure":
        """Build an interactive histogram."""
        import plotly.graph_objects as go

        fig = go.Figure()
        for i in range(data.n_features):
            fig.add_trace(
                go.Histogram(
                    x=data.data[:, i],
                    name=data.columns[i] if data.columns else f"feature_{i}",
                    marker_color=colors[i % len(colors)],
                    opacity=0.6,
                    nbinsx=30,
                )
            )
        fig.update_layout(barmode="overlay")
        return fig

    def _build_surface(
        self,
        data: InputData,
        config: VisualizationConfig,
    ) -> "go.Figure":
        """Build a 3D surface plot."""
        import plotly.graph_objects as go

        n = data.n_samples
        side = int(np.ceil(np.sqrt(n)))

        x_1d = np.linspace(-3, 3, side)
        y_1d = np.linspace(-3, 3, side)
        x_grid, y_grid = np.meshgrid(x_1d, y_1d)

        z_grid = np.zeros((side, side))
        for idx in range(min(n, side * side)):
            i = idx // side
            j = idx % side
            z_grid[i, j] = data.data[idx, 0] if data.n_features >= 1 else 0

        fig = go.Figure(
            data=[
                go.Surface(
                    z=z_grid,
                    x=x_grid,
                    y=y_grid,
                    colorscale=config.colormap,
                    opacity=0.9,
                    showscale=True,
                )
            ]
        )
        fig.update_layout(
            scene=dict(
                xaxis_title=config.xlabel or "X",
                yaxis_title=config.ylabel or "Y",
                zaxis_title=data.columns[0] if data.columns else "Z",
            )
        )
        return fig

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_colors(n: int) -> List[str]:
        """Generate a list of distinct hex colors."""
        import plotly.express as px

        if n <= 10:
            return px.colors.qualitative.Plotly[:n]
        import plotly.colors

        return plotly.colors.sample_colorscale(
            "viridis", [i / (n - 1) for i in range(n)]
        )
