"""Base renderer abstraction for experiment-engine visualization layer.

Defines the abstract :class:`Renderer` base class that all concrete
renderers must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from experiment_engine.models import InputData, RenderConfig


class Renderer(ABC):
    """Abstract base class for all visualisation renderers.

    Subclasses implement ``render()`` to produce a visual output (static
    image, interactive HTML, console output, or dashboard launch).

    Attributes:
        name: Human-readable name for this renderer.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a human-readable name for this renderer."""

    @abstractmethod
    def render(
        self,
        data: InputData,
        config: RenderConfig,
        **kwargs: Any,
    ) -> Union[str, object]:
        """Render *data* according to *config*.

        Args:
            data: Standardized input data to visualise.
            config: Configuration controlling plot type, styling, output
                path, etc.
            **kwargs: Additional renderer-specific options.

        Returns:
            Union[str, object]: Either a file path to the rendered output,
                or a renderer-specific object (e.g. a Plotly figure, a
                Streamlit handle).
        """

    def supported_formats(self) -> List[str]:
        """Return the list of output formats this renderer supports.

        The base implementation returns an empty list, indicating the
        renderer does not produce file-based output (e.g. a streaming
        or live-display renderer).

        Returns:
            List[str]: Supported format extensions (e.g. ``["png", "svg"]``).
        """
        return []

    @staticmethod
    def _infer_plot_type(data: InputData) -> str:
        """Heuristically determine a good default plot type.

        Args:
            data: Input data to inspect.

        Returns:
            str: Recommended plot type name.
        """
        n_features = data.n_features
        n_samples = data.n_samples

        if n_features >= 3 and n_samples > 50:
            return "scatter"
        if n_features == 1:
            return "histogram"
        if n_features == 2:
            return "line"
        return "scatter"
