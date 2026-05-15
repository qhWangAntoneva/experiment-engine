"""Plugin registry, discovery, and base classes for extension."""

from __future__ import annotations
from typing import Any, Callable


class AlgorithmBase:
    """Base class for algorithm plugins.

    Subclasses must implement ``run(data, params)``.
    """

    def run(self, data: Any, params: dict[str, Any] | None = None) -> Any:
        """Execute the algorithm on the given data."""
        raise NotImplementedError


class PluginRegistry:
    """Central registry for discovering and resolving plugins.

    Supports three registration channels:
    - Python entry points (setuptools)
    - Runtime decorator registration
    - Directory-based auto-discovery
    """

    def __init__(self) -> None:
        self._algorithms: dict[str, type] = {}
        self._loaders: dict[str, type] = {}
        self._visualizers: dict[str, type] = {}

    def register_algorithm(self, name: str, cls: type | None = None) -> Any:
        """Register an algorithm class. Can be used as a decorator."""
        def _register(cls: type) -> type:
            self._algorithms[name] = cls
            return cls
        return _register if cls is None else _register(cls)

    def register_loader(self, name: str, cls: type | None = None) -> Any:
        """Register a data loader class."""
        def _register(cls: type) -> type:
            self._loaders[name] = cls
            return cls
        return _register if cls is None else _register(cls)

    def register_visualizer(self, name: str, cls: type | None = None) -> Any:
        """Register a visualizer class."""
        def _register(cls: type) -> type:
            self._visualizers[name] = cls
            return cls
        return _register if cls is None else _register(cls)

    def get_algorithms(self) -> dict[str, str]:
        """Return dict of {name: description} for all registered algorithms."""
        return {n: getattr(c, "__doc__", "") or "" for n, c in self._algorithms.items()}

    def get_loaders(self) -> dict[str, str]:
        """Return dict of {name: description} for all registered loaders."""
        return {n: getattr(c, "__doc__", "") or "" for n, c in self._loaders.items()}

    def get_visualizers(self) -> dict[str, str]:
        """Return dict of {name: description} for all registered visualizers."""
        return {n: getattr(c, "__doc__", "") or "" for n, c in self._visualizers.items()}


# Global singleton registry
registry = PluginRegistry()

# Convenience decorators
register_algorithm = registry.register_algorithm
register_loader = registry.register_loader
register_visualizer = registry.register_visualizer


__all__ = [
    "AlgorithmBase",
    "PluginRegistry",
    "registry",
    "register_algorithm",
    "register_loader",
    "register_visualizer",
]
