"""Visualization backends and figure management.

Supports multiple backends:
- matplotlib: static publication-quality figures
- plotly: interactive web-ready figures
- custom: user-registered renderers via plugin system
"""

from __future__ import annotations
from typing import Any


class BaseVisualizer:
    """Abstract base class for visualization backends."""

    def render(self, data: Any, params: dict[str, Any] | None = None) -> Any:
        """Render data into a visual representation."""
        raise NotImplementedError

    def save(self, figure: Any, path: str) -> None:
        """Save the rendered figure to disk."""
        raise NotImplementedError


__all__ = ["BaseVisualizer"]
