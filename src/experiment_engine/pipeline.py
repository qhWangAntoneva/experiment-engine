"""Pipeline and Stage abstract base classes.

Defines the core abstractions for composable, configurable processing pipelines.
Stages are pluggable units with setup/process/teardown lifecycle. Pipelines
manage ordered stage execution and support nesting (sub-pipelines).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from experiment_engine.plugins import PluginRegistry

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from experiment_engine.models import (
    ExperimentConfig,
    PipelineResult,
    PipelineStageConfig,
    PipelineStatus,
    StageResult,
    StageStatus,
    Timer,
)

# ──────────────────────────────────────────────
#  Logging setup
# ──────────────────────────────────────────────

_console = Console(stderr=True)

_rich_handler = RichHandler(
    console=_console,
    show_time=True,
    show_path=False,
    enable_link_path=False,
    rich_tracebacks=True,
    tracebacks_show_locals=True,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[_rich_handler],
)

logger = logging.getLogger("experiment_engine.pipeline")


# ──────────────────────────────────────────────
#  Stage — abstract base
# ──────────────────────────────────────────────


class Stage(ABC):
    """Abstract base class for all pipeline stages.

    Each stage follows a three-phase lifecycle:
        1. **setup(config)** — called once before processing begins.
        2. **process(data)** — called for every data item; returns transformed data.
        3. **teardown()** — called once after processing completes (even on error).

    Subclasses must implement :meth:`process`. Override :meth:`setup` and
    :meth:`teardown` when stage-specific initialization or cleanup is needed.

    Attributes:
        name: Human-readable stage name (defaults to the class name).
        config: Stage-specific configuration dictionary.
        enabled: If False, the stage is skipped during pipeline execution.
        logger: Per-stage logger instance.
    """

    def __init__(
        self,
        name: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.name: str = name or self.__class__.__name__
        self.config: dict[str, Any] = config or {}
        self.enabled: bool = True
        self.logger = logging.getLogger(f"experiment_engine.stage.{self.name}")

    # ── Lifecycle ──────────────────────────────

    def setup(self) -> None:
        """Initialize stage resources.

        Called once before any calls to :meth:`process`. Override in subclasses
        to open files, connect to services, load models, etc.

        Raises:
            RuntimeError: If setup fails irrecoverably.
        """
        pass

    @abstractmethod
    def process(self, data: Any) -> Any:
        """Transform input data and return output.

        This is the only required override. Subclasses should perform their
        core transformation logic here.

        Args:
            data: Input data from the previous stage (or pipeline input).

        Returns:
            Transformed data to pass to the next stage.

        Raises:
            Exception: Any exception during processing is caught by the
                pipeline and recorded in the stage result.
        """
        ...

    def teardown(self) -> None:
        """Release stage resources.

        Called once after all processing is done, even if a prior stage failed.
        Override in subclasses to close files, disconnect services, etc.
        """
        pass

    # ── Configuration ──────────────────────────

    def configure(self, stage_config: PipelineStageConfig) -> None:
        """Apply a :class:`PipelineStageConfig` to this stage.

        Sets the stage name, enabled flag, and merges params into
        the stage's config dictionary.

        Args:
            stage_config: Configuration object for this stage.
        """
        self.name = stage_config.name
        self.enabled = stage_config.enabled
        self.config.update(stage_config.params)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, enabled={self.enabled})"


# ──────────────────────────────────────────────
#  Pipeline — ordered stage executor
# ──────────────────────────────────────────────


PipelineElement = Union[Stage, "Pipeline"]


class Pipeline(Stage):
    """Ordered collection of stages executed sequentially.

    Pipelines are themselves :class:`Stage` instances, enabling recursive
    composition: a pipeline can contain other pipelines as sub-pipelines.

    Attributes:
        stages: Ordered list of stages and sub-pipelines to execute.
        verbose: Enable per-stage rich logging output.
    """

    def __init__(
        self,
        name: str | None = None,
        stages: list[PipelineElement] | None = None,
        config: dict[str, Any] | None = None,
        verbose: bool = False,
    ) -> None:
        super().__init__(name=name, config=config)
        self.stages: list[PipelineElement] = stages or []
        self.verbose = verbose

    # ── Stage management ───────────────────────

    def add_stage(self, stage: PipelineElement) -> Pipeline:
        """Append a stage or sub-pipeline to the end of the pipeline.

        Args:
            stage: A :class:`Stage` or :class:`Pipeline` instance.

        Returns:
            Self for chaining.
        """
        self.stages.append(stage)
        return self

    def insert_stage(self, index: int, stage: PipelineElement) -> Pipeline:
        """Insert a stage at a specific position.

        Args:
            index: Position to insert at (0 = beginning).
            stage: A :class:`Stage` or :class:`Pipeline` instance.

        Returns:
            Self for chaining.
        """
        self.stages.insert(index, stage)
        return self

    def remove_stage(self, name: str) -> PipelineElement | None:
        """Remove and return a stage by name.

        Args:
            name: Name of the stage to remove.

        Returns:
            The removed stage, or None if not found.
        """
        for i, stage in enumerate(self.stages):
            if stage.name == name:
                return self.stages.pop(i)
        return None

    def get_stage(self, name: str) -> PipelineElement | None:
        """Look up a stage (or sub-pipeline) by name.

        Does NOT recursively search sub-pipelines.

        Args:
            name: Name of the stage to find.

        Returns:
            The stage if found, else None.
        """
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    # ── Lifecycle (delegates to children) ──────

    def setup(self) -> None:
        """Set up all stages in order.

        Calls :meth:`Stage.setup` on every enabled stage. If a stage fails
        during setup, subsequent stages are still attempted.
        """
        for stage in self.stages:
            if not stage.enabled:
                self.logger.info("  [dim]Skipping [bold]%s[/] (disabled)", stage.name)
                continue
            try:
                stage.setup()
                self.logger.info("  [green]✓[/] Setup [bold]%s[/]", stage.name)
            except Exception as exc:
                self.logger.error(
                    "  [red]✗[/] Setup [bold]%s[/] failed: %s", stage.name, exc
                )

    def process(self, data: Any) -> Any:
        """Run all stages sequentially on the input data.

        Each stage's output becomes the next stage's input. If a stage fails,
        the pipeline continues with the remaining stages. Sub-pipelines are
        executed recursively.

        Args:
            data: Initial input data for the pipeline.

        Returns:
            The output of the last successfully executed stage, or the
            original data if no stages ran.
        """
        current = data
        for stage in self.stages:
            if not stage.enabled:
                self.logger.info("  [dim]Skipping [bold]%s[/] (disabled)", stage.name)
                continue

            # ── Run stage ──
            try:
                result = stage.process(current)
                current = result
            except Exception as exc:
                self.logger.error(
                    "  [red]✗[/] Stage [bold]%s[/] failed: %s", stage.name, exc
                )
                # Continue with the last good data
        return current

    def teardown(self) -> None:
        """Tear down all stages in reverse order.

        Even if some stages failed, teardown is called for all stages that
        were set up, ensuring proper resource cleanup.
        """
        for stage in reversed(self.stages):
            if not stage.enabled:
                continue
            try:
                stage.teardown()
                self.logger.info("  [yellow]✕[/] Teardown [bold]%s[/]", stage.name)
            except Exception as exc:
                self.logger.warning(
                    "  [yellow]⚠[/] Teardown [bold]%s[/] warning: %s",
                    stage.name,
                    exc,
                )

    # ── Execution with result tracking ─────────

    def run(
        self,
        data: Any,
        experiment_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """Execute the full pipeline with rich result tracking.

        This is the primary entry point. It handles setup → process → teardown,
        collects per-stage timing and status, and returns a complete
        :class:`PipelineResult`.

        Args:
            data: Input data to process.
            experiment_name: Optional override for the experiment name.
            metadata: Optional pipeline-level metadata.

        Returns:
            A :class:`PipelineResult` with per-stage results and overall status.
        """
        start_time = datetime.now(timezone.utc)
        result = PipelineResult(
            experiment_name=experiment_name or self.name,
            started_at=start_time.isoformat(),
            metadata=metadata or {},
        )

        self.logger.info("[bold cyan]═══ Pipeline: %s ═══[/]", result.experiment_name)

        # ── Setup phase ──
        self.logger.info("[bold]Phase 1: Setup[/]")
        self.setup()

        # ── Process phase ──
        self.logger.info("[bold]Phase 2: Process[/]")
        current = data
        overall_status = PipelineStatus.COMPLETED

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=_console,
            transient=False,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Running {len(self.stages)} stage(s)...",
                total=len(self.stages),
            )

            for stage in self.stages:
                if not stage.enabled:
                    sr = StageResult(
                        stage_name=stage.name,
                        stage_type=stage.__class__.__name__,
                        status=StageStatus.SKIPPED,
                        started_at=datetime.now(timezone.utc).isoformat(),
                        completed_at=datetime.now(timezone.utc).isoformat(),
                    )
                    result.stages.append(sr)
                    progress.advance(task)
                    continue

                # ── Execute stage ──
                sr = StageResult(
                    stage_name=stage.name,
                    stage_type=stage.__class__.__name__,
                    status=StageStatus.RUNNING,
                    started_at=datetime.now(timezone.utc).isoformat(),
                )

                with Timer() as timer:
                    try:
                        stage_result = stage.process(current)
                        current = stage_result
                        sr.status = StageStatus.COMPLETED
                    except Exception as exc:
                        sr.status = StageStatus.FAILED
                        sr.error = f"{type(exc).__name__}: {exc}"
                        overall_status = PipelineStatus.PARTIAL
                        self.logger.error(
                            "  [red]✗[/] Stage [bold]%s[/] failed: %s",
                            stage.name,
                            exc,
                        )

                sr.duration_ms = timer.duration_ms
                sr.completed_at = datetime.now(timezone.utc).isoformat()
                result.stages.append(sr)

                status_icon = (
                    "[green]✓[/]" if sr.status == StageStatus.COMPLETED else "[red]✗[/]"
                )
                self.logger.info(
                    "  %s [bold]%s[/] — %.1f ms",
                    status_icon,
                    stage.name,
                    sr.duration_ms,
                )
                progress.advance(task)

        # ── Teardown phase ──
        self.logger.info("[bold]Phase 3: Teardown[/]")
        self.teardown()

        # ── Assemble result ──
        end_time = datetime.now(timezone.utc)
        result.completed_at = end_time.isoformat()
        result.total_duration_ms = sum(s.duration_ms for s in result.stages)
        result.status = overall_status
        result.output = current

        self._log_summary(result)
        return result

    # ── Rich output helpers ────────────────────

    def _log_summary(self, result: PipelineResult) -> None:
        """Log a rich summary table of the pipeline execution."""
        table = Table(
            title=f"Pipeline Summary: {result.experiment_name}",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Stage", style="bold")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Duration", justify="right")

        for sr in result.stages:
            status_str = {
                StageStatus.COMPLETED: "[green]✓ completed[/]",
                StageStatus.FAILED: "[red]✗ failed[/]",
                StageStatus.SKIPPED: "[dim]— skipped[/]",
                StageStatus.RUNNING: "[yellow]… running[/]",
                StageStatus.PENDING: "[dim]· pending[/]",
            }.get(sr.status, str(sr.status))

            table.add_row(
                sr.stage_name,
                sr.stage_type,
                status_str,
                f"{sr.duration_ms:.1f} ms",
            )

        table.add_row(
            "",
            "",
            f"[bold]{result.status.value}[/]",
            f"[bold]{result.total_duration_ms:.1f} ms[/]",
            end_section=True,
        )

        _console.print(table)

    def configure_from_config(
        self, config: ExperimentConfig, registry: PluginRegistry | None = None
    ) -> None:
        """Configure the pipeline from an :class:`ExperimentConfig`.

        For each stage config entry, this method looks up the stage type
        in the provided plugin registry (or falls back to the class name)
        and instantiates the stage, then configures it.

        Args:
            config: The experiment configuration object.
            registry: Optional registry for resolving stage type names.
                  If None, stages must be registered or added manually.
        """
        # Lazy import to avoid circular dependency at module level
        from experiment_engine.plugins import PluginRegistry

        reg = registry or PluginRegistry.get_instance()
        self.name = config.name
        self.verbose = config.verbose

        for stage_cfg in config.stages:
            if not stage_cfg.enabled:
                continue

            stage_cls = reg.get(stage_cfg.stage_type)
            if stage_cls is None:
                self.logger.warning(
                    "Stage type %r not found in registry; skipping.",
                    stage_cfg.stage_type,
                )
                continue

            stage_instance = stage_cls()
            stage_instance.configure(stage_cfg)
            self.add_stage(stage_instance)

    def __repr__(self) -> str:
        stages_repr = ", ".join(s.name for s in self.stages)
        return f"Pipeline(name={self.name!r}, stages=[{stages_repr}])"
