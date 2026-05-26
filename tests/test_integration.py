"""Integration tests for experiment-engine.

Tests CLI end-to-end (via Click CliRunner), config + pipeline integration,
data flow across modules, and error paths.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from experiment_engine.cli import cli
from experiment_engine.config import load_config, load_config_from_dict
from experiment_engine.io import CSVExporter, get_reader
from experiment_engine.io.sources import FileDataSource
from experiment_engine.models import (
    ExperimentConfig,
    ExportConfig,
    PipelineStageConfig,
    PipelineStatus,
    RenderConfig,
    StageStatus,
)
from experiment_engine.pipeline import Pipeline, Stage
from experiment_engine.plugins import PluginRegistry
from experiment_engine.viz.console import ConsoleRenderer

# Disable rich logging during tests to keep output clean
logging.getLogger("experiment_engine").setLevel(logging.CRITICAL)


# ═══════════════════════════════════════════════
#  Helper stages
# ═══════════════════════════════════════════════


class IdentityStage(Stage):
    """Stage that passes data through unchanged."""

    def process(self, data: Any) -> Any:
        return data


class UppercaseStage(Stage):
    """Stage that uppercases string input."""

    def process(self, data: Any) -> Any:
        if isinstance(data, str):
            return data.upper()
        return data


class MultiplyStage(Stage):
    """Stage that multiplies numeric data by a configurable factor."""

    def process(self, data: Any) -> Any:
        factor = self.config.get("factor", 2)
        if isinstance(data, int | float):
            return data * factor
        return data


class InputDataPassthroughStage(Stage):
    """Stage that passes InputData through, preserving the object."""

    def process(self, data: Any) -> Any:
        return data


# ═══════════════════════════════════════════════
#  Fixtures
# ═══════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _reset_registry_before_each() -> None:
    """Reset the PluginRegistry singleton before every test for isolation."""
    PluginRegistry.reset_instance()


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CliRunner instance."""
    return CliRunner()


@pytest.fixture
def temp_dir() -> Path:
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def registered_stages() -> None:
    """Register standard helper stages into the plugin registry."""
    registry = PluginRegistry.get_instance()
    registry.register("identity", IdentityStage)
    registry.register("uppercase", UppercaseStage)
    registry.register("multiply", MultiplyStage)
    registry.register("passthrough", InputDataPassthroughStage)


def _make_valid_condition_set(temp_dir: Path, name: str = "integration_test") -> Path:
    """Write a valid condition set YAML file and return its path."""
    from experiment_engine.models import CalibrationType, TextDomain
    from experiment_engine.text_calibration.condition import (
        ConditionDefinitionBuilder,
        ConditionSetBuilder,
        save_condition_set,
    )

    cond1 = (
        ConditionDefinitionBuilder(
            "negative_affect", "负面情绪", TextDomain.DISSATISFACTION
        )
        .add_prototype("不满 差劲 服务差", is_member=1)
        .add_prototype("满意 很好 优秀", is_member=0)
        .scoring(source="prototype")
        .calibration(
            CalibrationType.DIRECT,
            full_in=0.80,
            full_out=0.20,
            crossover=0.50,
            direction="ascending",
        )
        .build()
    )

    cond2 = (
        ConditionDefinitionBuilder(
            "strong_demand", "强烈诉求", TextDomain.DISSATISFACTION
        )
        .add_prototype("要求 举报 投诉", is_member=1)
        .add_prototype("无关 普通 一般", is_member=0)
        .scoring(source="prototype")
        .calibration(
            CalibrationType.DIRECT,
            full_in=0.80,
            full_out=0.20,
            crossover=0.50,
            direction="ascending",
        )
        .build()
    )

    outcome = (
        ConditionDefinitionBuilder(
            "citizen_dissatisfaction", "市民不满意", TextDomain.DISSATISFACTION
        )
        .add_prototype("很差 不满意 愤怒", is_member=1)
        .add_prototype("很好 满意 开心", is_member=0)
        .scoring(source="prototype")
        .calibration(
            CalibrationType.DIRECT,
            full_in=0.80,
            full_out=0.20,
            crossover=0.50,
            direction="ascending",
        )
        .build()
    )

    cs = (
        ConditionSetBuilder(name, TextDomain.DISSATISFACTION)
        .add_condition(cond1)
        .add_condition(cond2)
        .set_outcome(outcome)
        .description("Integration test condition set")
        .build()
    )

    path = temp_dir / "condition_set.yaml"
    save_condition_set(cs, str(path))
    return path


def _make_valid_corpus(temp_dir: Path) -> Path:
    """Write a minimal text corpus CSV file and return its path."""
    import csv

    path = temp_dir / "corpus.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text"])
        writer.writerow(["这个服务太差了，很不满意"])
        writer.writerow(["态度很恶劣，非常差劲"])
        writer.writerow(["总体感觉还可以接受吧"])
        writer.writerow(["强烈要求改善服务质量"])
        writer.writerow(["已经举报相关部门不作为"])
    return path


def _make_valid_yaml_config(
    temp_dir: Path,
    name: str | None = None,
    stages: list[dict[str, Any]] | None = None,
) -> Path:
    """Write a valid QCA workflow YAML config file and return its path."""
    # Create supporting files that the workflow config references
    cond_set_path = _make_valid_condition_set(temp_dir, name=name or "integration_test")
    corpus_path = _make_valid_corpus(temp_dir)

    config_data = {
        "conditions": {
            "definition_file": str(cond_set_path),
        },
        "input": {
            "path": str(corpus_path),
            "text_column": "text",
        },
    }
    path = temp_dir / "workflow.yaml"
    with open(path, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    return path


def _write_csv_data(path: Path, rows: list[list[str]]) -> None:
    """Write a simple CSV file."""
    import csv

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


# ═══════════════════════════════════════════════
#  1. CLI end-to-end tests (CliRunner)
# ═══════════════════════════════════════════════


class TestCliValidate:
    """Tests for the ``validate`` CLI command."""

    def test_validate_ok(self, runner: CliRunner, temp_dir: Path) -> None:
        """Call ``validate -c <valid_condition_set>`` and verify success output."""
        config_path = _make_valid_condition_set(temp_dir)
        result = runner.invoke(cli, ["validate", "-c", str(config_path)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_validate_prints_config_details(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """Valid output includes the condition set name and condition names."""
        config_path = _make_valid_condition_set(temp_dir, name="my_demo")
        result = runner.invoke(cli, ["validate", "-c", str(config_path)])
        assert result.exit_code == 0
        assert "my_demo" in result.output
        assert "Condition names:" in result.output

    def test_validate_invalid_config(self, runner: CliRunner) -> None:
        """Call ``validate -c <nonexistent>`` and verify failure exit code."""
        result = runner.invoke(cli, ["validate", "-c", "/nonexistent/config.yaml"])
        assert result.exit_code != 0

    def test_validate_bad_yaml(self, runner: CliRunner, temp_dir: Path) -> None:
        """Call ``validate -c <bad_yaml>`` and verify error is reported."""
        bad_path = temp_dir / "bad.yaml"
        bad_path.write_text("{invalid: yaml: [unbalanced")
        result = runner.invoke(cli, ["validate", "-c", str(bad_path)])
        assert result.exit_code != 0
        assert "Invalid" in result.output or "invalid" in result.output.lower()


class TestCliListConditions:
    """Tests for the ``list-conditions`` CLI command."""

    def test_list_conditions_empty(self, runner: CliRunner) -> None:
        """With no domain filter, the command lists all domain presets."""
        result = runner.invoke(cli, ["list-conditions"])
        assert result.exit_code == 0

    def test_list_conditions_with_domain_filter(
        self, runner: CliRunner, registered_stages: None
    ) -> None:
        """Domain filter shows the correct preset and its prototypes."""
        result = runner.invoke(cli, ["list-conditions", "-d", "dissatisfaction"])
        assert result.exit_code == 0
        assert "DISSATISFACTION" in result.output
        assert "prototypes" in result.output.lower()


class TestCliRun:
    """Tests for the ``run`` CLI command."""

    def test_run_command_succeeds(
        self, runner: CliRunner, temp_dir: Path, registered_stages: None
    ) -> None:
        """Call ``run -c <valid_workflow_config> -o <out_dir>`` and verify completion."""
        config_path = _make_valid_yaml_config(temp_dir)
        out_dir = temp_dir / "output"
        result = runner.invoke(cli, ["run", "-c", str(config_path), "-o", str(out_dir)])
        assert result.exit_code == 0
        assert "Done" in result.output

    def test_run_with_verbose_flag(
        self, runner: CliRunner, temp_dir: Path, registered_stages: None
    ) -> None:
        """The ``-v`` verbose flag does not cause errors."""
        config_path = _make_valid_yaml_config(temp_dir)
        result = runner.invoke(
            cli, ["run", "-c", str(config_path), "-o", str(temp_dir / "out"), "-v"]
        )
        assert result.exit_code == 0

    def test_run_without_output_dir(
        self, runner: CliRunner, temp_dir: Path, registered_stages: None
    ) -> None:
        """Running without ``-o`` still succeeds (default qca_output dir used)."""
        config_path = _make_valid_yaml_config(temp_dir)
        result = runner.invoke(cli, ["run", "-c", str(config_path)])
        assert result.exit_code == 0

    def test_run_missing_config(self, runner: CliRunner, temp_dir: Path) -> None:
        """Running with a non-existent config file exits with non-zero."""
        result = runner.invoke(cli, ["run", "-c", str(temp_dir / "nonexistent.yaml")])
        assert result.exit_code != 0


# ═══════════════════════════════════════════════
#  2. Pipeline integration tests
# ═══════════════════════════════════════════════


class TestPipelineIntegration:
    """Pipeline-level integration with config loading."""

    def test_pipeline_from_config(self, registered_stages: None) -> None:
        """Build pipeline from ExperimentConfig and verify execution."""
        registry = PluginRegistry.get_instance()
        config = ExperimentConfig(
            name="from_config_test",
            stages=[
                PipelineStageConfig(name="upper", stage_type="uppercase", enabled=True),
                PipelineStageConfig(
                    name="double",
                    stage_type="multiply",
                    enabled=True,
                    params={"factor": 2},
                ),
            ],
        )
        pipeline = Pipeline(name="from_config_test")
        pipeline.configure_from_config(config, registry=registry)

        assert len(pipeline.stages) == 2
        result = pipeline.run("hello")
        assert result.status == PipelineStatus.COMPLETED
        # "hello" -> "HELLO", multiply sees a string (not numeric) -> "HELLO"
        assert result.output == "HELLO"
        assert len(result.stages) == 2
        for sr in result.stages:
            assert sr.status == StageStatus.COMPLETED

    def test_pipeline_from_config_numeric(self, registered_stages: None) -> None:
        """Numeric data flows correctly through multiply stages."""
        registry = PluginRegistry.get_instance()
        config = ExperimentConfig(
            name="numeric_pipe",
            stages=[
                PipelineStageConfig(
                    name="double",
                    stage_type="multiply",
                    enabled=True,
                    params={"factor": 2},
                ),
                PipelineStageConfig(
                    name="triple",
                    stage_type="multiply",
                    enabled=True,
                    params={"factor": 3},
                ),
            ],
        )
        pipeline = Pipeline(name="numeric_pipe")
        pipeline.configure_from_config(config, registry=registry)

        result = pipeline.run(5)
        # 5 * 2 = 10, 10 * 3 = 30
        assert result.output == 30
        assert result.status == PipelineStatus.COMPLETED

    def test_pipeline_empty_stages(self) -> None:
        """A pipeline with no stages still completes successfully."""
        config = ExperimentConfig(name="empty", stages=[])
        pipeline = Pipeline(name="empty")
        pipeline.configure_from_config(config)

        assert len(pipeline.stages) == 0
        result = pipeline.run("no_stages")
        assert result.status == PipelineStatus.COMPLETED
        assert result.output == "no_stages"
        assert len(result.stages) == 0

    def test_pipeline_disabled_stages(self, registered_stages: None) -> None:
        """Disabled stages from config are not added to the pipeline."""
        registry = PluginRegistry.get_instance()
        config = ExperimentConfig(
            name="disabled_test",
            stages=[
                PipelineStageConfig(name="active", stage_type="identity", enabled=True),
                PipelineStageConfig(
                    name="inactive",
                    stage_type="uppercase",
                    enabled=False,
                ),
                PipelineStageConfig(
                    name="also_active", stage_type="identity", enabled=True
                ),
            ],
        )
        pipeline = Pipeline(name="disabled_test")
        pipeline.configure_from_config(config, registry=registry)

        # Only enabled stages are added
        assert len(pipeline.stages) == 2
        assert pipeline.stages[0].name == "active"
        assert pipeline.stages[1].name == "also_active"

    def test_pipeline_disabled_stages_execution(self, registered_stages: None) -> None:
        """Disabled stages are skipped during pipeline execution."""
        registry = PluginRegistry.get_instance()
        config = ExperimentConfig(
            name="skip_in_run",
            stages=[
                PipelineStageConfig(name="upper", stage_type="uppercase", enabled=True),
                PipelineStageConfig(
                    name="skip_me",
                    stage_type="multiply",
                    enabled=False,
                    params={"factor": 100},
                ),
                PipelineStageConfig(
                    name="identity", stage_type="identity", enabled=True
                ),
            ],
        )
        pipeline = Pipeline(name="skip_in_run")
        pipeline.configure_from_config(config, registry=registry)

        result = pipeline.run("test")
        assert result.output == "TEST"  # only uppercase applied
        # configure_from_config only adds enabled stages (disabled is skipped at add time)
        assert len(result.stages) == 2
        assert result.stages[0].status == StageStatus.COMPLETED
        assert result.stages[1].status == StageStatus.COMPLETED

    def test_pipeline_configure_twice(self, registered_stages: None) -> None:
        """Calling configure_from_config multiple times adds stages cumulatively."""
        registry = PluginRegistry.get_instance()

        cfg1 = ExperimentConfig(
            name="first",
            stages=[
                PipelineStageConfig(name="upper", stage_type="uppercase", enabled=True),
            ],
        )
        cfg2 = ExperimentConfig(
            name="second",
            stages=[
                PipelineStageConfig(
                    name="double",
                    stage_type="multiply",
                    enabled=True,
                    params={"factor": 2},
                ),
            ],
        )

        pipeline = Pipeline(name="multi_config")
        pipeline.configure_from_config(cfg1, registry=registry)
        assert len(pipeline.stages) == 1
        assert pipeline.stages[0].name == "upper"
        assert pipeline.name == "first"

        # Configure again — stages are appended
        pipeline.configure_from_config(cfg2, registry=registry)
        assert len(pipeline.stages) == 2
        assert pipeline.stages[0].name == "upper"
        assert pipeline.stages[1].name == "double"
        # Name overwritten by second config
        assert pipeline.name == "second"

    def test_pipeline_configure_twice_no_error(self, registered_stages: None) -> None:
        """Configure twice with same config does not raise."""
        registry = PluginRegistry.get_instance()
        config = ExperimentConfig(
            name="twice",
            stages=[
                PipelineStageConfig(name="id", stage_type="identity", enabled=True),
            ],
        )
        pipeline = Pipeline(name="twice")
        pipeline.configure_from_config(config, registry=registry)
        pipeline.configure_from_config(config, registry=registry)
        assert len(pipeline.stages) == 2

    def test_pipeline_from_load_config_from_dict(self, registered_stages: None) -> None:
        """Use load_config_from_dict to build and run a pipeline."""
        registry = PluginRegistry.get_instance()
        cfg = load_config_from_dict(
            {
                "name": "dict_test",
                "stages": [
                    {
                        "name": "upper",
                        "stage_type": "uppercase",
                        "enabled": True,
                    },
                    {
                        "name": "identity",
                        "stage_type": "identity",
                        "enabled": True,
                    },
                ],
            }
        )
        pipeline = Pipeline(name="dict_test")
        pipeline.configure_from_config(cfg, registry=registry)
        result = pipeline.run("hello")
        assert result.output == "HELLO"
        assert result.status == PipelineStatus.COMPLETED

    def test_pipeline_unknown_stage_type(self, registered_stages: None) -> None:
        """Unknown stage types are gracefully skipped (no crash)."""
        registry = PluginRegistry.get_instance()
        config = ExperimentConfig(
            name="unknown_stage",
            stages=[
                PipelineStageConfig(
                    name="known",
                    stage_type="identity",
                    enabled=True,
                ),
                PipelineStageConfig(
                    name="bogus",
                    stage_type="completely_fake_stage_type",
                    enabled=True,
                ),
                PipelineStageConfig(
                    name="also_known",
                    stage_type="uppercase",
                    enabled=True,
                ),
            ],
        )
        pipeline = Pipeline(name="unknown_stage")
        pipeline.configure_from_config(config, registry=registry)
        # Only the known stages should be added
        assert len(pipeline.stages) == 2
        assert pipeline.stages[0].name == "known"
        assert pipeline.stages[1].name == "also_known"


# ═══════════════════════════════════════════════
#  3. End-to-end data flow tests
# ═══════════════════════════════════════════════


class TestDataFlow:
    """Data-flow integration across io, pipeline, and viz modules."""

    def test_data_flow_csv_to_export(self, temp_dir: Path) -> None:
        """CSVLoader -> Pipeline -> CSVExporter: read, process, export."""
        # ── 1. Write a CSV file ──
        csv_path = temp_dir / "input.csv"
        _write_csv_data(
            csv_path,
            [["x", "y", "z"], ["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]],
        )

        # ── 2. Read via CSVReader ──
        reader = get_reader("csv")
        input_data = reader.read(str(csv_path))
        assert input_data.n_samples == 3
        assert input_data.n_features == 3
        assert input_data.columns == ["x", "y", "z"]

        # ── 3. Run through a pipeline (identity pass-through) ──
        pipeline = Pipeline(
            name="csv_flow",
            stages=[IdentityStage(name="passthrough")],
        )
        result = pipeline.run(input_data)
        assert result.status == PipelineStatus.COMPLETED
        assert result.output is not None
        assert result.output.n_samples == 3

        # ── 4. Export to CSV ──
        export_path = temp_dir / "exported.csv"
        exporter = CSVExporter()
        out_path = exporter.export(
            result.output,
            ExportConfig(
                format="csv",
                output_path=str(export_path),
                include_index=False,
            ),
        )
        assert Path(out_path).exists()
        exported_text = Path(out_path).read_text()
        assert exported_text.strip().startswith("x,y,z")
        assert "1,2,3" in exported_text
        assert "7,8,9" in exported_text

    def test_data_flow_csv_with_file_datasource(self, temp_dir: Path) -> None:
        """Use FileDataSource with CSVReader to load data."""
        csv_path = temp_dir / "source.csv"
        _write_csv_data(
            csv_path,
            [["a", "b"], ["10", "20"], ["30", "40"]],
        )

        reader = get_reader("csv")
        source = FileDataSource(reader, str(csv_path))
        input_data = source.load()

        assert input_data.n_samples == 2
        assert input_data.n_features == 2

        # Pass through pipeline
        pipeline = Pipeline(name="source_flow", stages=[IdentityStage()])
        result = pipeline.run(input_data)
        assert result.status == PipelineStatus.COMPLETED
        assert result.output is not None
        assert result.output.n_samples == 2

    def test_data_flow_synthetic_to_console(self) -> None:
        """SyntheticReader -> Pipeline -> ConsoleRenderer produces output."""
        reader = get_reader("synthetic")
        input_data = reader.read(n_samples=10, n_features=2, pattern="sine", seed=42)
        assert input_data.n_samples == 10
        assert input_data.n_features == 2

        pipeline = Pipeline(
            name="synthetic_flow",
            stages=[IdentityStage(name="pass")],
        )
        result = pipeline.run(input_data)
        assert result.status == PipelineStatus.COMPLETED

        # Render to console
        renderer = ConsoleRenderer()
        output = renderer.render(
            result.output,
            RenderConfig(title="Synthetic Test"),
            show_progress=False,
            show_stats=True,
            show_table=True,
            max_rows=5,
        )
        assert isinstance(output, str)
        # Rich Panel objects render as repr in captured output;
        # plain text content like shape info is preserved as-is
        assert "Samples:" in output
        assert "Features:" in output
        assert "Shape:" in output

    def test_data_flow_synthetic_to_export(self, temp_dir: Path) -> None:
        """SyntheticReader -> Pipeline -> CSVExporter."""
        reader = get_reader("synthetic")
        input_data = reader.read(n_samples=5, n_features=2, pattern="random", seed=1)

        pipeline = Pipeline(
            name="synth_export",
            stages=[IdentityStage(name="pass")],
        )
        result = pipeline.run(input_data)

        export_path = temp_dir / "synth_out.csv"
        exporter = CSVExporter()
        out_path = exporter.export(
            result.output,
            ExportConfig(
                format="csv",
                output_path=str(export_path),
                include_index=False,
            ),
        )
        assert Path(out_path).exists()
        lines = Path(out_path).read_text().strip().splitlines()
        assert len(lines) == 6  # header + 5 rows

    def test_data_flow_multi_stage_pipeline(self, temp_dir: Path) -> None:
        """Multi-stage pipeline with registered stages processes data."""
        registry = PluginRegistry.get_instance()
        registry.register("identity", IdentityStage)

        # Load synthetic data
        reader = get_reader("synthetic")
        input_data = reader.read(n_samples=5, n_features=2, seed=0)

        # Build pipeline from config with multiple identity stages
        config = ExperimentConfig(
            name="multi_stage_flow",
            stages=[
                PipelineStageConfig(
                    name="stage_1", stage_type="identity", enabled=True
                ),
                PipelineStageConfig(
                    name="stage_2", stage_type="identity", enabled=True
                ),
                PipelineStageConfig(
                    name="stage_3", stage_type="identity", enabled=True
                ),
            ],
        )
        pipeline = Pipeline(name="multi_stage_flow")
        pipeline.configure_from_config(config, registry=registry)
        assert len(pipeline.stages) == 3

        result = pipeline.run(input_data)
        assert result.status == PipelineStatus.COMPLETED
        assert len(result.stages) == 3
        for sr in result.stages:
            assert sr.status == StageStatus.COMPLETED
            assert sr.duration_ms >= 0
        assert result.output is not None
        assert result.output.n_samples == 5


# ═══════════════════════════════════════════════
#  4. Error path tests
# ═══════════════════════════════════════════════


class TestErrorPaths:
    """Error-handling tests for config loading and pipeline edge cases."""

    def test_missing_config_file(self) -> None:
        """load_config raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/to/config.yaml")

    def test_missing_config_file_json(self) -> None:
        """load_config raises FileNotFoundError for missing JSON file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.json")

    def test_invalid_yaml(self, temp_dir: Path) -> None:
        """load_config raises ValueError for invalid YAML content."""
        bad_path = temp_dir / "bad.yaml"
        bad_path.write_text("{invalid: yaml: [unbalanced]")
        with pytest.raises(ValueError, match=r"Invalid YAML|invalid"):
            load_config(str(bad_path))

    def test_invalid_json(self, temp_dir: Path) -> None:
        """load_config raises ValueError for invalid JSON content."""
        bad_path = temp_dir / "bad.json"
        bad_path.write_text("{invalid json}")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_config(str(bad_path))

    def test_unsupported_format(self, temp_dir: Path) -> None:
        """load_config raises ValueError for unsupported file extension."""
        bad_path = temp_dir / "config.xyz"
        bad_path.write_text("some content")
        with pytest.raises(ValueError, match="Unsupported config file format"):
            load_config(str(bad_path))

    def test_load_config_empty_file(self, temp_dir: Path) -> None:
        """load_config on an empty YAML file raises ValueError."""
        empty_path = temp_dir / "empty.yaml"
        empty_path.write_text("")
        with pytest.raises(ValueError):
            load_config(str(empty_path))

    def test_load_config_yaml_not_dict(self, temp_dir: Path) -> None:
        """load_config raises ValueError when YAML root is not a dict."""
        path = temp_dir / "list.yaml"
        path.write_text("- one\n- two\n- three\n")
        with pytest.raises(ValueError, match="must be a mapping"):
            load_config(str(path))

    def test_pipeline_stage_failure_continues(self) -> None:
        """A failing stage does not crash the pipeline; later stages still run (fail_fast=False)."""

        class FailStage(Stage):
            def process(self, data: Any) -> Any:
                raise RuntimeError("boom")

        pipeline = Pipeline(
            name="fail_test",
            stages=[
                IdentityStage(name="first"),
                FailStage(name="exploder"),
                UppercaseStage(name="after"),
            ],
            fail_fast=False,
        )
        result = pipeline.run("hello")
        assert result.stages[0].status == StageStatus.COMPLETED
        assert result.stages[1].status == StageStatus.FAILED
        assert "boom" in (result.stages[1].error or "")
        # Pipeline continues after failure
        assert result.stages[2].status == StageStatus.COMPLETED
        assert result.status == PipelineStatus.PARTIAL
        # Pipeline continues after failure; later stage (UppercaseStage)
        # still runs and transforms the data
        assert result.output == "HELLO"

    def test_validate_invalid_yaml_via_cli(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """CLI validate command errors on invalid YAML."""
        bad_path = temp_dir / "invalid.yaml"
        bad_path.write_text("[[broken")
        result = runner.invoke(cli, ["validate", "-c", str(bad_path)])
        assert result.exit_code != 0
        assert "Invalid" in result.output or "invalid" in result.output.lower()

    def test_config_with_validation_error(self, temp_dir: Path) -> None:
        """Pydantic validation errors propagate from load_config."""
        # Empty name should fail Pydantic validation
        config_data = {
            "name": "  ",
            "stages": [],
        }
        path = temp_dir / "bad_name.yaml"
        with open(path, "w") as f:
            yaml.dump(config_data, f)

        with pytest.raises(Exception):
            load_config(str(path))


# ═══════════════════════════════════════════════
#  5. Parallel execution tests
# ═══════════════════════════════════════════════


class TestParallelExecution:
    """Tests for :class:`ParallelStageGroup` and :class:`ParallelPipeline`."""

    # ── Helpers ─────────────────────────────

    class _DoubleStage(Stage):
        def process(self, data: Any) -> Any:
            return data * 2

    class _TripleStage(Stage):
        def process(self, data: Any) -> Any:
            return data * 3

    class _FailStage(Stage):
        def process(self, data: Any) -> Any:
            raise RuntimeError("stage exploded")

    class _TransformStage(Stage):
        def __init__(
            self,
            name: str | None = None,
            transform: str = "upper",
        ) -> None:
            super().__init__(name=name)
            self.transform = transform

        def process(self, data: Any) -> Any:
            if isinstance(data, str):
                if self.transform == "upper":
                    return data.upper()
                if self.transform == "lower":
                    return data.lower()
            return data

    # ── Tests ───────────────────────────────

    def test_parallel_group_processes_all_stages(self) -> None:
        """All sub-stages in a ParallelStageGroup execute and produce output."""
        from experiment_engine.core.parallel import ParallelStageGroup

        group = ParallelStageGroup(name="math", max_workers=2)
        group.add_stage(self._DoubleStage(name="double"))
        group.add_stage(self._TripleStage(name="triple"))

        result = group.process(5)

        assert isinstance(result, dict)
        assert len(result) == 2
        assert result["double"] == 10
        assert result["triple"] == 15

    def test_parallel_group_processes_all_stages_with_string(self) -> None:
        """ParallelStageGroup works with non-numeric data."""
        from experiment_engine.core.parallel import ParallelStageGroup

        group = ParallelStageGroup(name="string_group", max_workers=2)
        group.add_stage(self._TransformStage(name="up", transform="upper"))
        group.add_stage(self._TransformStage(name="low", transform="lower"))

        result = group.process("Hello World")

        assert result["up"] == "HELLO WORLD"
        assert result["low"] == "hello world"

    def test_parallel_group_processes_all_stages_single_sub_stage(
        self,
    ) -> None:
        """A group with a single sub-stage still works correctly."""
        from experiment_engine.core.parallel import ParallelStageGroup

        group = ParallelStageGroup(name="single", max_workers=1)
        group.add_stage(self._DoubleStage(name="double"))

        result = group.process(7)

        assert result == {"double": 14}

    def test_parallel_group_handles_failure_gracefully(self) -> None:
        """A failing sub-stage does not affect other sub-stages."""
        from experiment_engine.core.parallel import ParallelStageGroup

        group = ParallelStageGroup(name="mixed", max_workers=2)
        group.add_stage(self._DoubleStage(name="good"))
        group.add_stage(self._FailStage(name="bad"))

        result = group.process(10)

        # The successful stage still produced output
        assert result["good"] == 20
        # The failed stage stored the exception
        assert isinstance(result["bad"], Exception)
        assert "stage exploded" in str(result["bad"])

    def test_parallel_group_handles_failure_gracefully_all_fail(
        self,
    ) -> None:
        """When all sub-stages fail, all values are exceptions."""
        from experiment_engine.core.parallel import ParallelStageGroup

        group = ParallelStageGroup(name="all_fail", max_workers=2)
        group.add_stage(self._FailStage(name="a"))
        group.add_stage(self._FailStage(name="b"))

        result = group.process(42)

        assert len(result) == 2
        assert all(isinstance(v, Exception) for v in result.values())

    def test_parallel_group_handles_failure_gracefully_mixed(
        self,
    ) -> None:
        """Mix of success and failure — successful outputs are correct."""
        from experiment_engine.core.parallel import ParallelStageGroup

        group = ParallelStageGroup(name="mixed2", max_workers=3)
        group.add_stage(self._DoubleStage(name="d1"))
        group.add_stage(self._FailStage(name="f1"))
        group.add_stage(self._TripleStage(name="t1"))
        group.add_stage(self._FailStage(name="f2"))

        result = group.process(5)

        assert result["d1"] == 10
        assert isinstance(result["f1"], Exception)
        assert result["t1"] == 15
        assert isinstance(result["f2"], Exception)

    def test_parallel_pipeline_integration(self) -> None:
        """ParallelPipeline runs mixed serial and parallel stages."""
        from experiment_engine.core.parallel import (
            ParallelPipeline,
            ParallelStageGroup,
        )

        pipe = ParallelPipeline(name="integrated")
        pipe.add_stage(self._TransformStage(name="prepare", transform="upper"))

        group = ParallelStageGroup(name="analysis", max_workers=2)
        group.add_stage(self._DoubleStage(name="double"))
        group.add_stage(self._TripleStage(name="triple"))
        pipe.add_stage(group)

        pipe.add_stage(self._TransformStage(name="finish", transform="upper"))

        result = pipe.run("test")

        assert result.status == PipelineStatus.COMPLETED
        assert result.output is not None
        # Stages: prepare, double, triple, finish = 4 entries
        assert len(result.stages) == 4
        for sr in result.stages:
            assert sr.status == StageStatus.COMPLETED
        # All stages have sensible durations
        for sr in result.stages:
            assert sr.duration_ms >= 0

    def test_parallel_pipeline_integration_with_failure_in_group(
        self,
    ) -> None:
        """ParallelPipeline handles sub-stage failure within a group."""
        from experiment_engine.core.parallel import (
            ParallelPipeline,
            ParallelStageGroup,
        )

        pipe = ParallelPipeline(name="partial_fail", fail_fast=False)

        group = ParallelStageGroup(name="analysis", max_workers=2)
        group.add_stage(self._DoubleStage(name="good"))
        group.add_stage(self._FailStage(name="bad"))
        pipe.add_stage(group)

        pipe.add_stage(self._TransformStage(name="after"))

        result = pipe.run(5)

        # Overall status is PARTIAL because fail_fast=False
        assert result.status == PipelineStatus.PARTIAL
        # 3 stage results: good, bad, after
        assert len(result.stages) == 3
        assert result.stages[0].status == StageStatus.COMPLETED
        assert result.stages[1].status == StageStatus.FAILED
        assert "stage exploded" in (result.stages[1].error or "")
        # Pipeline continues even after group failure
        assert result.stages[2].status == StageStatus.COMPLETED

    def test_parallel_pipeline_with_multiple_groups(self) -> None:
        """ParallelPipeline handles multiple ParallelStageGroups."""
        from experiment_engine.core.parallel import (
            ParallelPipeline,
            ParallelStageGroup,
        )

        pipe = ParallelPipeline(name="multi_group")

        # DictTransformer extracts a specific key from the dict output
        # of a previous group and passes it through as the new value.
        class DictTransformer(Stage):
            def __init__(self, name: str | None = None, key: str = "d1") -> None:
                super().__init__(name=name)
                self.key = key

            def process(self, data: Any) -> Any:
                if isinstance(data, dict) and self.key in data:
                    return data[self.key]
                return data

        g1 = ParallelStageGroup(name="g1", max_workers=2)
        g1.add_stage(self._DoubleStage(name="d1"))
        g1.add_stage(self._TripleStage(name="t1"))
        pipe.add_stage(g1)

        pipe.add_stage(DictTransformer(name="extract", key="d1"))

        g2 = ParallelStageGroup(name="g2", max_workers=2)
        g2.add_stage(self._DoubleStage(name="d2"))
        g2.add_stage(self._TripleStage(name="t2"))
        pipe.add_stage(g2)

        result = pipe.run(2)

        assert result.status == PipelineStatus.COMPLETED
        assert len(result.stages) == 5  # g1(2) + extract(1) + g2(2)
        for sr in result.stages:
            assert sr.status == StageStatus.COMPLETED
        # 2 * 2 = 4, 4 * 2 = 8 (d2)
        # 4 * 3 = 12 (t2)
        assert result.output is not None
        assert isinstance(result.output, dict)
        assert result.output["d2"] == 8
        assert result.output["t2"] == 12

    def test_parallel_pipeline_with_empty_group(self) -> None:
        """A ParallelPipeline with an empty ParallelStageGroup works."""
        from experiment_engine.core.parallel import (
            ParallelPipeline,
            ParallelStageGroup,
        )

        pipe = ParallelPipeline(name="empty_group")
        empty = ParallelStageGroup(name="empty")
        pipe.add_stage(empty)
        pipe.add_stage(self._TransformStage(name="after"))

        result = pipe.run("hello")
        assert result.status == PipelineStatus.COMPLETED
        assert result.output is not None
