"""Parallel stage execution support.

Provides :class:`ParallelStageGroup` for running multiple sub-stages
concurrently within a single pipeline node, and :class:`ParallelPipeline`
which extends the standard pipeline with per-sub-stage result tracking.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from experiment_engine.models import (
    PipelineResult,
    PipelineStatus,
    StageResult,
    StageStatus,
    Timer,
)
from experiment_engine.pipeline import Pipeline, PipelineElement, Stage

if TYPE_CHECKING:
    pass

logger = logging.getLogger("experiment_engine.parallel")

# ──────────────────────────────────────────────
#  ParallelStageGroup
# ──────────────────────────────────────────────


class ParallelStageGroup(Stage):
    """A stage that runs multiple sub-stages concurrently.

    Broadcasts the same input data to all sub-stages and collects their
    outputs into a dictionary keyed by stage name.

    If a sub-stage fails, it does **not** affect other sub-stages. The failed
    stage's entry in the output dict will contain the raised exception.

    .. code-block:: python

        group = ParallelStageGroup(name=\"analysis\", max_workers=4)
        group.add_stage(KMeansStage())
        group.add_stage(PCAStage())

        outputs = group.process(data)
        # => {\"KMeansStage\": <kmeans_result>, \"PCAStage\": <pca_result>}

    Args:
        name: Human-readable name for this group.
        max_workers: Maximum number of parallel workers. ``None`` lets
            :class:`~concurrent.futures.ThreadPoolExecutor` choose.
        config: Optional stage configuration dictionary.
    """

    def __init__(
        self,
        name: str | None = None,
        max_workers: int | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name=name, config=config)
        self._sub_stages: list[Stage] = []
        self.max_workers = max_workers

    # ── Stage management ───────────────────────

    @property
    def stages(self) -> list[Stage]:
        """The list of sub-stages in this group."""
        return self._sub_stages

    def add_stage(self, stage: Stage) -> ParallelStageGroup:
        """Append a sub-stage to this group.

        Args:
            stage: A :class:`~experiment_engine.pipeline.Stage` instance.

        Returns:
            Self for chaining.
        """
        self._sub_stages.append(stage)
        return self

    def insert_stage(self, index: int, stage: Stage) -> ParallelStageGroup:
        """Insert a sub-stage at a specific position.

        Args:
            index: Position to insert at (0 = beginning).
            stage: A :class:`~experiment_engine.pipeline.Stage` instance.

        Returns:
            Self for chaining.
        """
        self._sub_stages.insert(index, stage)
        return self

    def remove_stage(self, name: str) -> Stage | None:
        """Remove and return a sub-stage by name.

        Args:
            name: Name of the stage to remove.

        Returns:
            The removed stage, or ``None`` if not found.
        """
        for i, stage in enumerate(self._sub_stages):
            if stage.name == name:
                return self._sub_stages.pop(i)
        return None

    def get_stage(self, name: str) -> Stage | None:
        """Look up a sub-stage by name (non-recursive).

        Args:
            name: Name of the stage to find.

        Returns:
            The stage if found, else ``None``.
        """
        for stage in self._sub_stages:
            if stage.name == name:
                return stage
        return None

    # ── Lifecycle ──────────────────────────────

    def setup(self) -> None:
        """Set up all sub-stages in order."""
        for stage in self._sub_stages:
            if not stage.enabled:
                continue
            try:
                stage.setup()
                logger.info(
                    "  [green]✓[/] Setup [bold]%s[/] in group [bold]%s[/]",
                    stage.name,
                    self.name,
                )
            except Exception as exc:
                logger.error(
                    "  [red]✗[/] Setup [bold]%s[/] in group [bold]%s[/] failed: %s",
                    stage.name,
                    self.name,
                    exc,
                )

    def process(self, data: Any) -> dict[str, Any]:
        """Run all *enabled* sub-stages concurrently.

        Broadcasts the same ``data`` to every sub-stage. Returns a dictionary
        mapping each sub-stage's name to its output. If a sub-stage raised an
        exception, the exception object is stored as the value instead.

        The returned dict preserves insertion order of the sub-stages.

        Args:
            data: Input data to broadcast to all sub-stages.

        Returns:
            dict[str, Any] — stage name → output (or exception on failure).
        """
        enabled_stages = [s for s in self._sub_stages if s.enabled]
        if not enabled_stages:
            return {}

        raw: dict[str, Any] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map: dict[Any, Stage] = {
                executor.submit(stage.process, data): stage for stage in enabled_stages
            }

            for future in as_completed(future_map):
                stage = future_map[future]
                try:
                    raw[stage.name] = future.result()
                except Exception as exc:
                    raw[stage.name] = exc
                    logger.error(
                        "  [red]✗[/] Sub-stage [bold]%s[/] in group "
                        "[bold]%s[/] failed: %s",
                        stage.name,
                        self.name,
                        exc,
                    )

        # Preserve insertion order in the returned dict
        ordered: dict[str, Any] = {}
        for stage in enabled_stages:
            if stage.name in raw:
                ordered[stage.name] = raw[stage.name]
        return ordered

    def teardown(self) -> None:
        """Tear down all sub-stages in reverse order."""
        for stage in reversed(self._sub_stages):
            if not stage.enabled:
                continue
            try:
                stage.teardown()
                logger.info(
                    "  [yellow]✕[/] Teardown [bold]%s[/] in group [bold]%s[/]",
                    stage.name,
                    self.name,
                )
            except Exception as exc:
                logger.warning(
                    "  [yellow]⚠[/] Teardown [bold]%s[/] in group "
                    "[bold]%s[/] warning: %s",
                    stage.name,
                    self.name,
                    exc,
                )

    # ── Internal helpers ───────────────────────

    def _execute_all_with_results(
        self, data: Any
    ) -> tuple[dict[str, Any], list[StageResult]]:
        """Run all enabled sub-stages in parallel and collect per-stage results.

        This is used internally by :class:`ParallelPipeline` to produce
        individual :class:`StageResult` entries for each sub-stage.

        Args:
            data: Input data to broadcast.

        Returns:
            Tuple of ``(outputs_dict, list[StageResult])``.
        """
        enabled_stages = [s for s in self._sub_stages if s.enabled]
        if not enabled_stages:
            return {}, []

        outputs: dict[str, Any] = {}
        stage_results: dict[str, StageResult] = {}

        for stage in enabled_stages:
            stage_results[stage.name] = StageResult(
                stage_name=stage.name,
                stage_type=stage.__class__.__name__,
                status=StageStatus.RUNNING,
                started_at=datetime.now(timezone.utc).isoformat(),
            )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {
                executor.submit(stage.process, data): stage for stage in enabled_stages
            }

            for future in as_completed(future_map):
                stage = future_map[future]
                sr = stage_results[stage.name]
                with Timer() as timer:
                    try:
                        outputs[stage.name] = future.result()
                        sr.status = StageStatus.COMPLETED
                    except Exception as exc:
                        outputs[stage.name] = exc
                        sr.status = StageStatus.FAILED
                        sr.error = f"{type(exc).__name__}: {exc}"
                sr.duration_ms = timer.duration_ms
                sr.completed_at = datetime.now(timezone.utc).isoformat()

        # Preserve insertion order in both outputs and results list
        ordered_outputs: dict[str, Any] = {}
        ordered_results: list[StageResult] = []
        for stage in enabled_stages:
            if stage.name in outputs:
                ordered_outputs[stage.name] = outputs[stage.name]
            if stage.name in stage_results:
                ordered_results.append(stage_results[stage.name])

        return ordered_outputs, ordered_results


# ──────────────────────────────────────────────
#  ParallelPipeline
# ──────────────────────────────────────────────


class ParallelPipeline(Pipeline):
    """A pipeline that recognizes :class:`ParallelStageGroup` and creates
    individual :class:`StageResult` entries for each sub-stage within a group.

    Behaves identically to :class:`Pipeline` for all other stage types,
    including serial execution and progress reporting.

    .. code-block:: python

        pipe = ParallelPipeline(name=\"parallel-demo\")
        pipe.add_stage(InputStage())
        group = ParallelStageGroup(name=\"analysis\", max_workers=4)
        group.add_stage(KMeansStage())
        group.add_stage(PCAStage())
        pipe.add_stage(group)
        pipe.add_stage(OutputStage())
        result = pipe.run(data)
        # result.stages includes individual entries for KMeansStage
        # and PCAStage alongside InputStage and OutputStage.
    """

    def __init__(
        self,
        name: str | None = None,
        stages: list[PipelineElement] | None = None,
        config: dict[str, Any] | None = None,
        verbose: bool = False,
        fail_fast: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            stages=stages,
            config=config,
            verbose=verbose,
            fail_fast=fail_fast,
        )

    def run(
        self,
        data: Any,
        experiment_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """Execute the pipeline with per-sub-stage tracking for
        :class:`ParallelStageGroup` instances.

        The overall flow (setup → process → teardown) mirrors
        :meth:`Pipeline.run`.  When a :class:`ParallelStageGroup` is
        encountered during processing, each of its sub-stages receives its
        own :class:`StageResult` in the returned result.

        Args:
            data: Input data to process.
            experiment_name: Optional override for the experiment name.
            metadata: Optional pipeline-level metadata.

        Returns:
            A :class:`PipelineResult` with per-stage (and per-sub-stage)
            results.
        """
        from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

        # Lazy-import the console used by Pipeline
        from experiment_engine.pipeline import _console as pipe_console

        start_time = datetime.now(timezone.utc)
        result = PipelineResult(
            experiment_name=experiment_name or self.name,
            started_at=start_time.isoformat(),
            metadata=metadata or {},
        )

        logger.info(
            "[bold cyan]═══ ParallelPipeline: %s ═══[/]", result.experiment_name
        )

        # ── Setup phase ──
        logger.info("[bold]Phase 1: Setup[/]")
        self.setup()

        # ── Process phase ──
        logger.info("[bold]Phase 2: Process[/]")
        current = data
        overall_status = PipelineStatus.COMPLETED
        data_degraded = False

        # Count total items for progress bar (expand ParallelStageGroups)
        total_items = 0
        for stage in self.stages:
            if isinstance(stage, ParallelStageGroup):
                total_items += sum(1 for s in stage.stages if s.enabled)
            else:
                total_items += 1

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=pipe_console,
            transient=False,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Running {total_items} stage(s)...",
                total=total_items,
            )

            for stage in self.stages:
                if not stage.enabled:
                    sr = StageResult(
                        stage_name=stage.name,
                        stage_type=stage.__class__.__name__,
                        status=StageStatus.SKIPPED,
                        data_quality="valid" if not data_degraded else "stale",
                        started_at=datetime.now(timezone.utc).isoformat(),
                        completed_at=datetime.now(timezone.utc).isoformat(),
                    )
                    result.stages.append(sr)
                    progress.advance(task)
                    continue

                # ── ParallelStageGroup: expand into sub-stage results ──
                if isinstance(stage, ParallelStageGroup):
                    outputs, sub_results = stage._execute_all_with_results(current)

                    # Collect latest non-exception output for data flow
                    # (last sub-stage wins if multiple succeed)
                    group_any_failed = False
                    for sub_sr in sub_results:
                        sub_sr.data_quality = "stale" if data_degraded else "valid"
                        result.stages.append(sub_sr)
                        if sub_sr.status == StageStatus.FAILED:
                            group_any_failed = True
                            sub_sr.data_quality = None
                            if self.fail_fast:
                                overall_status = PipelineStatus.FAILED
                            else:
                                data_degraded = True
                                overall_status = PipelineStatus.PARTIAL
                            logger.error(
                                "  [red]✗[/] Sub-stage [bold]%s[/] in group "
                                "[bold]%s[/] failed: %s",
                                sub_sr.stage_name,
                                stage.name,
                                sub_sr.error,
                            )
                        else:
                            logger.info(
                                "  [green]✓[/] [bold]%s[/] (group [bold]%s[/])"
                                " — %.1f ms",
                                sub_sr.stage_name,
                                stage.name,
                                sub_sr.duration_ms,
                            )
                        progress.advance(task)

                    # Build data flow: use the last successful output if any
                    # Otherwise keep current data unchanged
                    group_outputs_ok = {
                        k: v
                        for k, v in outputs.items()
                        if not isinstance(v, BaseException)
                    }
                    if group_outputs_ok:
                        current = outputs  # dict with all outputs
                    # If all failed, keep current unchanged

                    if group_any_failed and self.fail_fast:
                        break

                else:
                    # ── Regular stage ──
                    sr = StageResult(
                        stage_name=stage.name,
                        stage_type=stage.__class__.__name__,
                        status=StageStatus.RUNNING,
                        data_quality="stale" if data_degraded else "valid",
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
                            sr.data_quality = None
                            if self.fail_fast:
                                overall_status = PipelineStatus.FAILED
                            else:
                                data_degraded = True
                                overall_status = PipelineStatus.PARTIAL
                            logger.error(
                                "  [red]✗[/] Stage [bold]%s[/] failed: %s",
                                stage.name,
                                exc,
                            )

                    sr.duration_ms = timer.duration_ms
                    sr.completed_at = datetime.now(timezone.utc).isoformat()
                    result.stages.append(sr)

                    status_icon = (
                        "[green]✓[/]"
                        if sr.status == StageStatus.COMPLETED
                        else "[red]✗[/]"
                    )
                    logger.info(
                        "  %s [bold]%s[/] — %.1f ms",
                        status_icon,
                        stage.name,
                        sr.duration_ms,
                    )
                    progress.advance(task)

                    if sr.status == StageStatus.FAILED and self.fail_fast:
                        break

        # ── Teardown phase ──
        logger.info("[bold]Phase 3: Teardown[/]")
        self.teardown()

        # ── Assemble result ──
        end_time = datetime.now(timezone.utc)
        result.completed_at = end_time.isoformat()
        result.total_duration_ms = sum(s.duration_ms for s in result.stages)
        result.status = overall_status
        result.output = current
        result.fail_fast = self.fail_fast

        self._log_summary(result)
        return result
