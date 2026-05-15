"""Data loaders, writers, and format adapters."""

from __future__ import annotations
from typing import Any


class BaseLoader:
    """Abstract base class for data loaders."""

    def load(self, path: str, **kwargs: Any) -> Any:
        """Load data from the given path."""
        raise NotImplementedError


class BaseWriter:
    """Abstract base class for data writers."""

    def write(self, data: Any, path: str, **kwargs: Any) -> None:
        """Write data to the given path."""
        raise NotImplementedError


__all__ = ["BaseLoader", "BaseWriter"]
