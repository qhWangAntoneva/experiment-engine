"""Matplotlib-based renderer for experiment-engine.

Produces static publication-quality figures in PNG, SVG, and PDF formats.
Supports line plots, scatter plots, bar charts, histograms, and 3D
surface plots.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np

from experiment_engine.models import InputData, RenderConfig
from experiment_engine.viz.base import Renderer


class MatplotlibRenderer(Renderer):
    """Renders experiment data using Matplotlib.

    Produces static images (PNG, SVG, PDF) with auto-sizing and
    consistent styling.

    Examples:
        >>> renderer = MatplotlibRenderer()
        >>> path = renderer.render(data, VisualizationConfig(plot_type="line"))
    """

    @property
    def name(self) -> str:
        return "matplotlib"

    def supported_formats(self) -> List[str]:
        return ["png", "svg", "pdf"]

    def render(
        self,
        data: InputData,
        config: RenderConfig,
        **kwargs: Any,
    ) -> str:
        """Render data to a static image file.

        Args:
            data: Input data to visualise.
            config: Visualisation configuration.
            **kwargs: Additional keyword arguments forwarded to the
                underlying matplotlib plotting function.

        Returns:
            str: Path to the saved image file.
        """
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend

        import matplotlib.pyplot as plt
        from matplotlib import rcParams

        # Apply styling
        rcParams.update(
            {
                "figure.figsize": config.figsize,
                "figure.dpi": config.dpi,
                "axes.grid": True,
                "grid.alpha": 0.3,
                "axes.spines.top": False,
                "axes.spines.right": False,
            }
        )

        fig, ax = plt.subplots(figsize=config.figsize)

        plot_type = config.plot_type
        x = np.arange(data.n_samples) if data.index is None else np.array(data.index, dtype=float)
        cmap = plt.get_cmap(config.colormap)

        try:
            if plot_type == "line":
                self._plot_line(ax, data, x, cmap, **kwargs)
            elif plot_type == "scatter":
                self._plot_scatter(ax, data, x, cmap, **kwargs)
            elif plot_type == "bar":
                self._plot_bar(ax, data, x, cmap, **kwargs)
            elif plot_type == "histogram":
                self._plot_histogram(ax, data, cmap, **kwargs)
            elif plot_type == "surface":
                fig, ax = self._plot_surface(fig, ax, data, cmap, **kwargs)
            else:
                raise ValueError(
                    f"Unsupported plot type '{plot_type}'. "
                    f"Supported: line, scatter, bar, histogram, surface"
                )
        except Exception:
            plt.close(fig)
            raise

        self._apply_labels(ax, config)
        fig.suptitle(config.title, fontweight="bold")

        output_path = self._resolve_output_path(config, plot_type)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fig.savefig(
            path,
            dpi=config.dpi,
            bbox_inches="tight",
            format=path.suffix.lstrip("."),
        )
        plt.close(fig)

        return str(path.resolve())

    # ------------------------------------------------------------------
    # Plot type implementations
    # ------------------------------------------------------------------

    def _plot_line(
        self,
        ax: Any,
        data: InputData,
        x: np.ndarray,
        cmap: Any,
        **kwargs: Any,
    ) -> None:
        """Draw a line plot, one line per feature."""
        for i in range(data.n_features):
            color = cmap(i / max(data.n_features - 1, 1))
            ax.plot(
                x,
                data.data[:, i],
                color=color,
                label=data.columns[i] if data.columns else None,
                linewidth=1.5,
                **kwargs,
            )
        if data.columns:
            ax.legend(frameon=False)

    def _plot_scatter(
        self,
        ax: Any,
        data: InputData,
        x: np.ndarray,
        cmap: Any,
        **kwargs: Any,
    ) -> None:
        """Draw a scatter plot."""
        if data.n_features >= 2:
            scatter = ax.scatter(
                data.data[:, 0],
                data.data[:, 1],
                c=data.data[:, 2] if data.n_features >= 3 else "steelblue",
                cmap=cmap,
                alpha=0.7,
                edgecolors="none",
                **kwargs,
            )
            if data.n_features >= 3:
                plt.colorbar(scatter, ax=ax, label=data.columns[2] if len(data.columns) > 2 else "")
        else:
            ax.scatter(x, data.data[:, 0], alpha=0.7, **kwargs)

    def _plot_bar(
        self,
        ax: Any,
        data: InputData,
        x: np.ndarray,
        cmap: Any,
        **kwargs: Any,
    ) -> None:
        """Draw a grouped bar chart."""
        n_groups = data.n_samples
        n_features = data.n_features
        width = 0.8 / max(n_features, 1)

        for i in range(n_features):
            offset = (i - n_features / 2 + 0.5) * width
            color = cmap(i / max(n_features - 1, 1))
            ax.bar(
                x + offset,
                data.data[:, i],
                width=width,
                label=data.columns[i] if data.columns else None,
                color=color,
                alpha=0.85,
                **kwargs,
            )
        if data.columns:
            ax.legend(frameon=False)

    def _plot_histogram(
        self,
        ax: Any,
        data: InputData,
        cmap: Any,
        **kwargs: Any,
    ) -> None:
        """Draw histograms, one per feature."""
        bins = kwargs.pop("bins", 30)
        for i in range(data.n_features):
            color = cmap(i / max(data.n_features - 1, 1))
            ax.hist(
                data.data[:, i],
                bins=bins,
                alpha=0.6,
                label=data.columns[i] if data.columns else None,
                color=color,
                **kwargs,
            )
        if data.columns:
            ax.legend(frameon=False)

    def _plot_surface(
        self,
        fig: Any,
        ax: Any,
        data: InputData,
        cmap: Any,
        **kwargs: Any,
    ) -> tuple:
        """Draw a 3D surface plot (requires at least 2 features)."""
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401, ensures 3D projection

        n = data.n_samples
        side = int(np.sqrt(n))

        if side * side < n:
            side = int(np.ceil(np.sqrt(n)))
            x_1d = np.linspace(-3, 3, side)
            y_1d = np.linspace(-3, 3, side)
            x_grid, y_grid = np.meshgrid(x_1d, y_1d)
            z_grid = np.zeros((side, side))
            for idx in range(min(n, side * side)):
                i = idx // side
                j = idx % side
                z_grid[i, j] = data.data[idx, 0] if data.n_features >= 1 else 0
        else:
            x_1d = np.linspace(0, 4 * np.pi, side)
            y_1d = np.linspace(0, 4 * np.pi, side)
            x_grid, y_grid = np.meshgrid(x_1d, y_1d)
            z_grid = data.data[:side, :side].reshape(side, side) if data.n_samples >= side * side else np.random.randn(side, side)

        # Create a new 3D axis
        fig.clear()
        ax = fig.add_subplot(111, projection="3d")
        surf = ax.plot_surface(
            x_grid, y_grid, z_grid,
            cmap=cmap,
            alpha=0.9,
            linewidth=0,
            antialiased=True,
            **kwargs,
        )
        fig.colorbar(surf, ax=ax, shrink=0.5, aspect=20)
        return fig, ax

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_labels(self, ax: Any, config: RenderConfig) -> None:
        """Set axis labels from config."""
        if config.xlabel:
            ax.set_xlabel(config.xlabel)
        if config.ylabel:
            ax.set_ylabel(config.ylabel)

    def _resolve_output_path(
        self,
        config: RenderConfig,
        plot_type: str,
    ) -> str:
        """Determine the output file path.

        If *config.output_path* is provided, uses it. Otherwise
        auto-generates a path.
        """
        if config.output_path:
            return config.output_path
        return f"output_{plot_type}.png"
