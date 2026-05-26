"""Plugin system for experiment-engine pipeline stages.

Provides a registry pattern with decorator-based registration, automatic
plugin discovery via directory scanning, and a clean metadata API.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from experiment_engine.pipeline import Stage

logger = logging.getLogger("experiment_engine.plugins")

_console = Console(stderr=True)


# ──────────────────────────────────────────────
#  BasePlugin
# ──────────────────────────────────────────────


class BasePlugin(Stage):
    """Base class for all experiment-engine plugins.

    Extends :class:`Stage` with metadata attributes that describe the
    plugin's purpose, version, and author.

    Attributes:
        plugin_name: Display name of the plugin (defaults to class name).
        plugin_version: Semantic version string (default ``"0.1.0"``).
        plugin_description: Short description of what the plugin does.
        plugin_author: Author or organization name.
        plugin_tags: List of tag strings for categorization.
    """

    plugin_name: str = ""
    plugin_version: str = "0.1.0"
    plugin_description: str = ""
    plugin_author: str = ""
    plugin_tags: list[str] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Auto-set plugin_name from class name if not overridden."""
        super().__init_subclass__(**kwargs)
        if not cls.plugin_name:
            cls.plugin_name = cls.__name__

    @classmethod
    def metadata(cls) -> dict[str, Any]:
        """Return plugin metadata as a dictionary."""
        return {
            "name": cls.plugin_name,
            "class": cls.__name__,
            "module": cls.__module__,
            "version": cls.plugin_version,
            "description": cls.plugin_description,
            "author": cls.plugin_author,
            "tags": cls.plugin_tags,
        }


# ──────────────────────────────────────────────
#  PluginRegistry
# ──────────────────────────────────────────────


class PluginRegistry:
    """Registry that maps stage type names to Stage subclasses.

    Supports both dependency injection (pass a ``registry`` dict and ``enabled``
    set on construction) and classic singleton access via :meth:`get_instance`.

    In DI mode, construct with explicit arguments for test isolation:
        >>> reg = PluginRegistry(registry={"my_stage": MyStage}, enabled={"my_stage"})

    In singleton mode (backward-compatible default), use :meth:`get_instance`:
        >>> registry = PluginRegistry.get_instance()
        >>> registry.register("my_stage", MyStage)
        >>> cls = registry.get("my_stage")

    Stages are registered via the :func:`register_stage` decorator or the
    :meth:`register` method.
    """

    _instance: PluginRegistry | None = None

    def __init__(
        self,
        registry: dict[str, type[Stage]] | None = None,
        enabled: set[str] | None = None,
    ) -> None:
        """Initialise the registry.

        Args:
            registry: Pre-populated registry mapping stage names to classes.
                Defaults to an empty dict.
            enabled: Set of stage names enabled by default. Defaults to an
                empty set.
        """
        self._registry: dict[str, type[Stage]] = registry or {}
        self._enabled: set[str] = enabled or set()

    # ── Singleton ──────────────────────────────

    @classmethod
    def get_instance(cls) -> PluginRegistry:
        """Return the singleton registry instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None

    # ── Registration ───────────────────────────

    def register(
        self,
        name: str,
        stage_cls: type[Stage],
        enabled: bool = True,
    ) -> None:
        """Register a stage class under a given name.

        Args:
            name: Unique identifier for the stage type.
            stage_cls: Subclass of :class:`Stage` to register.
            enabled: Whether the stage is enabled by default.

        Raises:
            ValueError: If a stage with the same name is already registered.
            TypeError: If stage_cls is not a Stage subclass.
        """
        if not issubclass(stage_cls, Stage):
            raise TypeError(f"{stage_cls.__name__} must be a subclass of Stage")

        if name in self._registry:
            raise ValueError(
                f"Stage type {name!r} is already registered "
                f"(existing: {self._registry[name].__name__})"
            )

        self._registry[name] = stage_cls
        if enabled:
            self._enabled.add(name)

        logger.debug("Registered stage type %r → %s", name, stage_cls.__name__)

    def unregister(self, name: str) -> None:
        """Remove a stage type from the registry.

        Args:
            name: Name of the stage type to remove.
        """
        self._registry.pop(name, None)
        self._enabled.discard(name)

    # ── Lookup ─────────────────────────────────

    def get(self, name: str) -> type[Stage] | None:
        """Look up a stage class by registered name.

        Args:
            name: Registered stage type name.

        Returns:
            The stage class, or None if not found.
        """
        return self._registry.get(name)

    def is_enabled(self, name: str) -> bool:
        """Check if a stage type is enabled by default.

        Args:
            name: Registered stage type name.

        Returns:
            True if enabled, False otherwise.
        """
        return name in self._enabled

    def list_stages(self) -> dict[str, type[Stage]]:
        """Return a copy of all registered stages.

        Returns:
            Dictionary mapping type names to stage classes.
        """
        return dict(self._registry)

    @property
    def names(self) -> list[str]:
        """List of all registered stage type names."""
        return list(self._registry.keys())

    # ── Discovery ──────────────────────────────

    def discover_from_module(self, module_name: str) -> int:
        """Scan a Python module for registered stage classes.

        Loads the module; any :func:`register_stage` decorators will have
        already populated the registry.

        Args:
            module_name: Fully-qualified module name (e.g. ``"my_package.stages"``).

        Returns:
            Number of newly registered stages found.
        """
        count_before = len(self._registry)
        try:
            importlib.import_module(module_name)
        except ImportError as exc:
            logger.warning("Could not load module %r: %s", module_name, exc)
            return 0

        count_after = len(self._registry)
        return count_after - count_before

    # ── Display ────────────────────────────────

    def show_registry(self) -> None:
        """Print a rich-formatted table of all registered stages."""
        if not self._registry:
            _console.print("[yellow]No stages registered.[/]")
            return

        table = Table(
            title="Registered Pipeline Stages",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Name", style="bold")
        table.add_column("Class")
        table.add_column("Module")
        table.add_column("Enabled")

        for name in sorted(self._registry.keys()):
            cls = self._registry[name]
            enabled_str = "[green]✓[/]" if name in self._enabled else "[dim]—[/]"
            table.add_row(name, cls.__name__, cls.__module__, enabled_str)

        _console.print(table)


# ──────────────────────────────────────────────
#  Decorator
# ──────────────────────────────────────────────


def register_stage(
    name: str | None = None,
    *,
    enabled: bool = True,
    registry: PluginRegistry | None = None,
) -> Callable[[type[Stage]], type[Stage]]:
    """Decorator that registers a :class:`Stage` subclass with the plugin registry.

    The stage's class name is used as the registration name unless an explicit
    name is provided.

    Args:
        name: Explicit registration name. If None, the class name is used.
        enabled: Whether the stage is enabled by default.
        registry: Registry to use. Defaults to the singleton registry.

    Returns:
        The original class (unchanged).

    Usage:
        >>> @register_stage("csv_loader")
        >>> class CSVLoaderStage(Stage):
        ...     def process(self, data):
        ...         return data
    """
    reg = registry or PluginRegistry.get_instance()

    def decorator(cls: type[Stage]) -> type[Stage]:
        stage_name = name or cls.__name__
        reg.register(stage_name, cls, enabled=enabled)

        # Attach registration info to the class for introspection
        cls._registry_name = stage_name  # type: ignore[attr-defined]
        return cls

    return decorator


# ──────────────────────────────────────────────
#  PluginLoader — directory scanning
# ──────────────────────────────────────────────


class PluginLoader:
    """Scans directories for plugin modules and registers discovered stages.

    Discovers Python files (``.py``) in the given directories, imports each
    module, and relies on :func:`register_stage` decorators inside those
    modules to populate the registry.

    Supports both explicit file paths and package-style directories.

    Attributes:
        registry: The registry to populate during discovery.
        search_paths: List of directory paths to scan.
    """

    def __init__(
        self,
        registry: PluginRegistry | None = None,
        search_paths: list[str] | None = None,
    ) -> None:
        self.registry = registry or PluginRegistry.get_instance()
        self.search_paths: list[str] = search_paths or []

    def add_search_path(self, path: str) -> None:
        """Add a directory to the plugin search path.

        Args:
            path: Absolute or relative directory path.
        """
        if path not in self.search_paths:
            self.search_paths.append(path)

    def discover(self, paths: list[str] | None = None) -> int:
        """Discover plugins by scanning directories.

        Each Python file in the scan path is imported as a module. Any
        ``@register_stage`` decorators inside will auto-register stages.

        Args:
            paths: Override paths to scan. If None, uses ``self.search_paths``.

        Returns:
            Total number of newly registered stages.
        """
        scan_paths = paths if paths is not None else self.search_paths
        total_found = 0

        for scan_path in scan_paths:
            path_obj = Path(scan_path)
            if not path_obj.is_dir():
                logger.warning("Plugin search path not found: %s", scan_path)
                continue

            found = self._scan_directory(path_obj)
            total_found += found

        return total_found

    def _scan_directory(self, directory: Path) -> int:
        """Scan a single directory for plugin modules.

        Args:
            directory: Path to the directory to scan.

        Returns:
            Count of newly registered stages.
        """
        count_before = len(self.registry._registry)
        py_files = sorted(directory.glob("*.py"))

        for py_file in py_files:
            # Skip __init__.py
            if py_file.name == "__init__.py":
                continue

            module_name = py_file.stem
            self._load_module_from_path(module_name, py_file)

        return len(self.registry._registry) - count_before

    def _load_module_from_path(self, module_name: str, file_path: Path) -> bool:
        """Load a Python module from a file path using importlib.

        Args:
            module_name: Name to assign to the loaded module.
            file_path: Path to the .py file.

        Returns:
            True if the module was loaded successfully.
        """
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.warning("Could not create module spec for %s", file_path)
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            logger.debug("Loaded plugin module: %s → %s", module_name, file_path)
            return True
        except Exception as exc:
            logger.warning(
                "Failed to load plugin %s from %s: %s",
                module_name,
                file_path,
                exc,
            )
            return False

    def discover_package(self, package_name: str) -> int:
        """Discover plugins from an installed Python package.

        Args:
            package_name: Fully-qualified package name.

        Returns:
            Number of newly registered stages.
        """
        return self.registry.discover_from_module(package_name)

    def list_discovered(self) -> list[dict[str, Any]]:
        """Return metadata for all currently registered stages.

        Returns:
            List of metadata dictionaries, one per registered stage.
        """
        result = []
        for name, cls in self.registry.list_stages().items():
            meta = {"name": name, "class": cls.__name__, "module": cls.__module__}
            if hasattr(cls, "plugin_name"):
                meta["plugin_name"] = getattr(cls, "plugin_name", "")
                meta["version"] = getattr(cls, "plugin_version", "")
                meta["description"] = getattr(cls, "plugin_description", "")
            result.append(meta)
        return result
