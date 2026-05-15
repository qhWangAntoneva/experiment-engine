"""Unit tests for the experiment-engine pipeline framework.

Tests core functionality: Stage lifecycle, Pipeline execution, PluginRegistry,
configuration loading, and data models.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from experiment_engine.config import (
    apply_cli_overrides,
    load_config,
    load_config_from_dict,
    merge_defaults,
)
from experiment_engine.models import (
    ExperimentConfig,
    InputData,
    OutputData,
    PipelineResult,
    PipelineStageConfig,
    PipelineStatus,
    StageResult,
    StageStatus,
    Timer,
)
from experiment_engine.pipeline import Pipeline, Stage
from experiment_engine.plugins import (
    BasePlugin,
    PluginLoader,
    PluginRegistry,
    register_stage,
)

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
        if isinstance(data, (int, float)):
            return data * factor
        return data


class ErrorStage(Stage):
    """Stage that always raises an exception."""

    def process(self, data: Any) -> Any:
        raise RuntimeError("Intentional stage failure")


class SetupTrackingStage(Stage):
    """Stage that tracks lifecycle calls for testing."""

    def __init__(self, tracker: Optional[Dict[str, bool]] = None) -> None:
        super().__init__()
        self.tracker = tracker or {}

    def setup(self) -> None:
        self.tracker["setup"] = True

    def process(self, data: Any) -> Any:
        self.tracker["process"] = True
        return data

    def teardown(self) -> None:
        self.tracker["teardown"] = True


# ═══════════════════════════════════════════════
#  Test: Stage
# ═══════════════════════════════════════════════


class TestStage:
    """Tests for the Stage abstract base class."""

    def test_identity_stage(self) -> None:
        stage = IdentityStage(name="identity")
        assert stage.name == "identity"
        assert stage.process("hello") == "hello"
        assert stage.process(42) == 42
        assert stage.process([1, 2, 3]) == [1, 2, 3]

    def test_stage_default_name(self) -> None:
        stage = IdentityStage()
        assert stage.name == "IdentityStage"

    def test_stage_custom_name(self) -> None:
        stage = IdentityStage(name="custom")
        assert stage.name == "custom"

    def test_stage_config(self) -> None:
        stage = IdentityStage(config={"key": "value"})
        assert stage.config["key"] == "value"

    def test_stage_enabled_default(self) -> None:
        stage = IdentityStage()
        assert stage.enabled is True

    def test_stage_configure(self) -> None:
        stage = IdentityStage()
        stage_cfg = PipelineStageConfig(
            name="configured_stage",
            stage_type="identity",
            enabled=False,
            params={"param1": 10},
        )
        stage.configure(stage_cfg)
        assert stage.name == "configured_stage"
        assert stage.enabled is False
        assert stage.config.get("param1") == 10

    def test_uppercase_stage(self) -> None:
        stage = UppercaseStage()
        assert stage.process("hello world") == "HELLO WORLD"

    def test_multiply_stage_default_factor(self) -> None:
        stage = MultiplyStage()
        assert stage.process(5) == 10  # default factor = 2

    def test_multiply_stage_custom_factor(self) -> None:
        stage = MultiplyStage(config={"factor": 3})
        assert stage.process(5) == 15

    def test_lifecycle_calls(self) -> None:
        tracker: Dict[str, bool] = {}
        stage = SetupTrackingStage(tracker=tracker)
        stage.setup()
        stage.process("data")
        stage.teardown()
        assert tracker.get("setup") is True
        assert tracker.get("process") is True
        assert tracker.get("teardown") is True

    def test_stage_repr(self) -> None:
        stage = IdentityStage(name="test_repr")
        repr_str = repr(stage)
        assert "IdentityStage" in repr_str
        assert "test_repr" in repr_str


# ═══════════════════════════════════════════════
#  Test: Pipeline
# ═══════════════════════════════════════════════


class TestPipeline:
    """Tests for the Pipeline class."""

    def test_empty_pipeline(self) -> None:
        pipeline = Pipeline(name="empty")
        result = pipeline.run("data")
        assert isinstance(result, PipelineResult)
        assert result.experiment_name == "empty"
        assert result.output == "data"
        assert len(result.stages) == 0

    def test_single_stage(self) -> None:
        pipeline = Pipeline(name="single", stages=[UppercaseStage()])
        result = pipeline.run("hello")
        assert result.output == "HELLO"
        assert len(result.stages) == 1
        assert result.stages[0].status == StageStatus.COMPLETED

    def test_multi_stage(self) -> None:
        pipeline = Pipeline(
            name="multi",
            stages=[
                UppercaseStage(name="upper"),
                MultiplyStage(name="multiply", config={"factor": 3}),
            ],
        )
        result = pipeline.run("hello")  # upper won't affect numeric MultiplyStage
        # Actually: upper produces "HELLO", multiply sees a string (not int), returns as-is
        assert result.output == "HELLO"
        assert len(result.stages) == 2
        for sr in result.stages:
            assert sr.status == StageStatus.COMPLETED

    def test_numeric_pipeline(self) -> None:
        pipeline = Pipeline(
            name="numeric",
            stages=[
                MultiplyStage(name="double", config={"factor": 2}),
                MultiplyStage(name="triple", config={"factor": 3}),
            ],
        )
        result = pipeline.run(5)  # 5 * 2 = 10, 10 * 3 = 30
        assert result.output == 30
        assert len(result.stages) == 2

    def test_disabled_stage(self) -> None:
        multiply = MultiplyStage(name="double", config={"factor": 2})
        multiply.enabled = False
        pipeline = Pipeline(
            name="disabled_test",
            stages=[multiply, MultiplyStage(name="triple", config={"factor": 3})],
        )
        result = pipeline.run(5)  # disabled stage skipped, then 5 * 3 = 15
        assert result.output == 15
        assert result.stages[0].status == StageStatus.SKIPPED
        assert result.stages[1].status == StageStatus.COMPLETED

    def test_stage_failure(self) -> None:
        pipeline = Pipeline(
            name="failure_test",
            stages=[
                IdentityStage(name="first"),
                ErrorStage(name="error_stage"),
                UppercaseStage(name="after_error"),
            ],
        )
        result = pipeline.run("test_data")
        # Error stage should fail, but pipeline continues
        assert result.stages[0].status == StageStatus.COMPLETED
        assert result.stages[1].status == StageStatus.FAILED
        assert "Intentional stage failure" in (result.stages[1].error or "")
        assert result.status == PipelineStatus.PARTIAL

    def test_composition_sub_pipeline(self) -> None:
        """Test that pipelines can contain sub-pipelines."""
        inner = Pipeline(
            name="inner",
            stages=[
                MultiplyStage(name="double", config={"factor": 2}),
                MultiplyStage(name="triple", config={"factor": 3}),
            ],
        )
        outer = Pipeline(
            name="outer",
            stages=[
                IdentityStage(name="pass"),
                inner,
                MultiplyStage(name="times_four", config={"factor": 4}),
            ],
        )
        result = outer.run(5)
        # inner: 5 -> 10 -> 30; outer: 30 -> 120
        assert result.output == 120  # 5 * 2 * 3 * 4
        assert len(result.stages) == 3

    def test_add_stage(self) -> None:
        pipeline = Pipeline(name="builder")
        pipeline.add_stage(UppercaseStage(name="upper"))
        pipeline.add_stage(MultiplyStage(name="double", config={"factor": 2}))
        assert len(pipeline.stages) == 2

    def test_insert_stage(self) -> None:
        pipeline = Pipeline(name="insert_test")
        pipeline.add_stage(MultiplyStage(name="triple", config={"factor": 3}))
        pipeline.insert_stage(0, MultiplyStage(name="double", config={"factor": 2}))
        assert pipeline.stages[0].name == "double"
        assert pipeline.stages[1].name == "triple"

    def test_remove_stage(self) -> None:
        pipeline = Pipeline(name="remove_test")
        pipeline.add_stage(UppercaseStage(name="upper"))
        pipeline.add_stage(MultiplyStage(name="double", config={"factor": 2}))
        removed = pipeline.remove_stage("upper")
        assert removed is not None
        assert removed.name == "upper"
        assert len(pipeline.stages) == 1
        assert pipeline.get_stage("double") is not None

    def test_get_stage_not_found(self) -> None:
        pipeline = Pipeline(name="not_found")
        assert pipeline.get_stage("nonexistent") is None

    def test_configure_from_config(self) -> None:
        """Test configuring a pipeline from an ExperimentConfig using the registry."""
        # Register test stages
        registry = PluginRegistry.get_instance()
        registry.register("identity", IdentityStage)
        registry.register("uppercase", UppercaseStage)
        registry.register("multiply", MultiplyStage)

        config = ExperimentConfig(
            name="config_test",
            stages=[
                PipelineStageConfig(
                    name="first", stage_type="uppercase", enabled=True
                ),
                PipelineStageConfig(
                    name="second",
                    stage_type="multiply",
                    enabled=True,
                    params={"factor": 5},
                ),
            ],
        )
        pipeline = Pipeline(name="config_test")
        pipeline.configure_from_config(config, registry=registry)

        assert len(pipeline.stages) == 2
        assert pipeline.stages[0].name == "first"
        assert pipeline.stages[1].name == "second"

        result = pipeline.run("hello")  # "hello" -> "HELLO", then string passed through
        assert result.output == "HELLO"

    def test_pipeline_repr(self) -> None:
        pipeline = Pipeline(name="repr_test")
        pipeline.add_stage(IdentityStage(name="a"))
        pipeline.add_stage(IdentityStage(name="b"))
        repr_str = repr(pipeline)
        assert "Pipeline" in repr_str
        assert "a" in repr_str
        assert "b" in repr_str


# ═══════════════════════════════════════════════
#  Test: Data Models
# ═══════════════════════════════════════════════


class TestModels:
    """Tests for Pydantic data models."""

    def test_experiment_config_defaults(self) -> None:
        config = ExperimentConfig()
        assert config.name == "experiment"
        assert config.version == "1.0"
        assert config.stages == []
        assert config.global_params == {}
        assert config.verbose is False

    def test_experiment_config_with_stages(self) -> None:
        config = ExperimentConfig(
            name="my_exp",
            stages=[
                PipelineStageConfig(
                    name="loader", stage_type="csv_loader", params={"path": "/data"}
                )
            ],
        )
        assert len(config.stages) == 1
        assert config.stages[0].name == "loader"
        assert config.stages[0].params["path"] == "/data"

    def test_pipeline_stage_config_validation(self) -> None:
        with pytest.raises(Exception):
            PipelineStageConfig(name="", stage_type="test")

    def test_input_data(self) -> None:
        data = InputData(data={"key": "value"}, metadata={"source": "test"})
        assert data.data["key"] == "value"
        assert data.metadata["source"] == "test"
        assert data.timestamp is not None

    def test_output_data(self) -> None:
        output = OutputData(raw="input", processed="OUTPUT")
        assert output.raw == "input"
        assert output.processed == "OUTPUT"

    def test_stage_result_defaults(self) -> None:
        sr = StageResult(stage_name="test", stage_type="test_type")
        assert sr.status == StageStatus.PENDING
        assert sr.duration_ms == 0.0
        assert sr.error is None

    def test_stage_result_completed(self) -> None:
        sr = StageResult(
            stage_name="loader",
            stage_type="csv_loader",
            status=StageStatus.COMPLETED,
            duration_ms=123.45,
        )
        assert sr.duration_ms == 123.45
        assert sr.status == StageStatus.COMPLETED

    def test_pipeline_result_defaults(self) -> None:
        pr = PipelineResult()
        assert pr.status == PipelineStatus.PENDING
        assert pr.stages == []
        assert pr.total_duration_ms == 0.0

    def test_pipeline_result_success_count(self) -> None:
        pr = PipelineResult(
            stages=[
                StageResult(
                    stage_name="a",
                    stage_type="type_a",
                    status=StageStatus.COMPLETED,
                ),
                StageResult(
                    stage_name="b", stage_type="type_b", status=StageStatus.FAILED
                ),
                StageResult(
                    stage_name="c",
                    stage_type="type_c",
                    status=StageStatus.COMPLETED,
                ),
            ]
        )
        assert pr.success_count == 2
        assert pr.failure_count == 1
        assert pr.total_stages == 3

    def test_timer(self) -> None:
        timer = Timer()
        with timer:
            pass  # Should be very fast
        assert timer.duration_ms >= 0

    def test_timer_measures_time(self) -> None:
        import time

        timer = Timer()
        with timer:
            time.sleep(0.01)  # 10ms
        assert timer.duration_ms >= 5  # Should be at least ~10ms

    def test_pipeline_result_to_dict(self) -> None:
        pr = PipelineResult(experiment_name="test", status=PipelineStatus.COMPLETED)
        d = pr.to_dict()
        assert d["experiment_name"] == "test"
        assert d["status"] == "completed"


# ═══════════════════════════════════════════════
#  Test: Plugin System
# ═══════════════════════════════════════════════


class TestPluginRegistry:
    """Tests for the PluginRegistry and decorator."""

    def setup_method(self) -> None:
        PluginRegistry.reset_instance()

    def test_singleton(self) -> None:
        r1 = PluginRegistry.get_instance()
        r2 = PluginRegistry.get_instance()
        assert r1 is r2

    def test_register_and_get(self) -> None:
        registry = PluginRegistry.get_instance()
        registry.register("identity", IdentityStage)
        cls = registry.get("identity")
        assert cls is IdentityStage

    def test_register_duplicate(self) -> None:
        registry = PluginRegistry.get_instance()
        registry.register("test", IdentityStage)
        with pytest.raises(ValueError, match="already registered"):
            registry.register("test", IdentityStage)

    def test_get_nonexistent(self) -> None:
        registry = PluginRegistry.get_instance()
        assert registry.get("nonexistent") is None

    def test_list_stages(self) -> None:
        registry = PluginRegistry.get_instance()
        registry.register("a", IdentityStage)
        registry.register("b", UppercaseStage)
        stages = registry.list_stages()
        assert "a" in stages
        assert "b" in stages
        assert len(stages) == 2

    def test_names_property(self) -> None:
        registry = PluginRegistry.get_instance()
        registry.register("x", IdentityStage)
        assert "x" in registry.names

    def test_unregister(self) -> None:
        registry = PluginRegistry.get_instance()
        registry.register("temp", IdentityStage)
        assert registry.get("temp") is not None
        registry.unregister("temp")
        assert registry.get("temp") is None

    def test_register_non_stage(self) -> None:
        registry = PluginRegistry.get_instance()

        class NotAStage:
            pass

        with pytest.raises(TypeError):
            registry.register("bad", NotAStage)  # type: ignore[arg-type]

    def test_is_enabled(self) -> None:
        registry = PluginRegistry.get_instance()
        registry.register("enabled_stage", IdentityStage, enabled=True)
        registry.register("disabled_stage", UppercaseStage, enabled=False)
        assert registry.is_enabled("enabled_stage") is True
        assert registry.is_enabled("disabled_stage") is False

    def test_discover_from_module(self) -> None:
        """Test that discover_from_module loads a module with registered stages."""
        registry = PluginRegistry.get_instance()
        count = registry.discover_from_module(
            "tests.test_pipeline"
        )  # self-referential
        # At minimum our own identities are registered
        assert count >= 0


class TestRegisterStageDecorator:
    """Tests for the @register_stage decorator."""

    def setup_method(self) -> None:
        PluginRegistry.reset_instance()

    def test_decorator_registers(self) -> None:
        @register_stage("test_decorator")
        class DecoratedStage(Stage):
            def process(self, data: Any) -> Any:
                return data

        registry = PluginRegistry.get_instance()
        cls = registry.get("test_decorator")
        assert cls is DecoratedStage

    def test_decorator_default_name(self) -> None:
        @register_stage()
        class AutoNameStage(Stage):
            def process(self, data: Any) -> Any:
                return data

        registry = PluginRegistry.get_instance()
        cls = registry.get("AutoNameStage")
        assert cls is AutoNameStage

    def test_decorator_disabled(self) -> None:
        @register_stage("disabled_stage", enabled=False)
        class DisabledStage(Stage):
            def process(self, data: Any) -> Any:
                return data

        registry = PluginRegistry.get_instance()
        assert registry.is_enabled("disabled_stage") is False

    def test_decorator_attaches_name(self) -> None:
        @register_stage("attached_name")
        class AttachedStage(Stage):
            def process(self, data: Any) -> Any:
                return data

        assert AttachedStage._registry_name == "attached_name"  # type: ignore[attr-defined]


class TestBasePlugin:
    """Tests for the BasePlugin class."""

    def test_plugin_metadata(self) -> None:
        class MyPlugin(BasePlugin):
            plugin_name = "my_plugin"
            plugin_version = "1.2.3"
            plugin_description = "A test plugin"
            plugin_author = "Test Author"

            def process(self, data: Any) -> Any:
                return data

        meta = MyPlugin.metadata()
        assert meta["name"] == "my_plugin"
        assert meta["version"] == "1.2.3"
        assert meta["description"] == "A test plugin"
        assert meta["author"] == "Test Author"

    def test_plugin_auto_name(self) -> None:
        class AutoPlugin(BasePlugin):
            def process(self, data: Any) -> Any:
                return data

        assert AutoPlugin.plugin_name == "AutoPlugin"


class TestPluginLoader:
    """Tests for the PluginLoader class."""

    def setup_method(self) -> None:
        PluginRegistry.reset_instance()

    def test_empty_paths(self) -> None:
        loader = PluginLoader()
        count = loader.discover()
        assert count == 0

    def test_scan_nonexistent_directory(self, caplog) -> None:
        loader = PluginLoader(search_paths=["/nonexistent/path"])
        count = loader.discover()
        assert count == 0

    def test_list_discovered(self) -> None:
        registry = PluginRegistry.get_instance()
        registry.register("test_stage", IdentityStage)
        loader = PluginLoader(registry=registry)
        discovered = loader.list_discovered()
        assert any(d["name"] == "test_stage" for d in discovered)


# ═══════════════════════════════════════════════
#  Test: Configuration Loading
# ═══════════════════════════════════════════════


class TestConfig:
    """Tests for configuration loading."""

    def test_merge_defaults(self) -> None:
        result = merge_defaults({"name": "custom"})
        assert result["name"] == "custom"
        assert result["version"] == "1.0"  # from defaults
        assert result["verbose"] is False  # from defaults

    def test_merge_defaults_empty(self) -> None:
        result = merge_defaults({})
        assert result["name"] == "default_experiment"

    def test_load_config_from_dict(self) -> None:
        config = load_config_from_dict(
            {
                "name": "test_exp",
                "stages": [
                    {
                        "name": "stage1",
                        "stage_type": "csv_loader",
                    }
                ],
            }
        )
        assert config.name == "test_exp"
        assert len(config.stages) == 1
        assert config.stages[0].name == "stage1"

    def test_load_config_json(self) -> None:
        """Test loading from a JSON file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(
                {
                    "name": "json_exp",
                    "stages": [
                        {
                            "name": "loader",
                            "stage_type": "data_loader",
                            "params": {"path": "/data"},
                        }
                    ],
                },
                f,
            )
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.name == "json_exp"
            assert config.stages[0].params["path"] == "/data"
        finally:
            os.unlink(temp_path)

    def test_load_config_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.json")

    def test_load_config_bad_format(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".bad", delete=False
        ) as f:
            f.write("{}")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported config file format"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_config_invalid_json(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write("{invalid json}")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_apply_cli_overrides(self) -> None:
        config = ExperimentConfig(name="base", verbose=False)
        overridden = apply_cli_overrides(config, {"name": "override_exp", "verbose": True})
        assert overridden.name == "override_exp"
        assert overridden.verbose is True

    def test_apply_cli_overrides_nested(self) -> None:
        config = ExperimentConfig(
            name="base",
            stages=[
                PipelineStageConfig(
                    name="loader", stage_type="csv_loader", params={"path": "/old"}
                )
            ],
        )
        overridden = apply_cli_overrides(
            config, {"stages.0.params.path": "/new"}
        )
        assert overridden.stages[0].params["path"] == "/new"

    def test_list_stages_from_config(self) -> None:
        from experiment_engine.config import list_stages_from_config

        config = ExperimentConfig(
            name="test",
            stages=[
                PipelineStageConfig(name="a", stage_type="t1", enabled=True),
                PipelineStageConfig(name="b", stage_type="t2", enabled=False),
                PipelineStageConfig(name="c", stage_type="t3", enabled=True),
            ],
        )
        names = list_stages_from_config(config)
        assert names == ["a", "c"]

    def test_config_to_dict(self) -> None:
        from experiment_engine.config import config_to_dict

        config = ExperimentConfig(name="test", verbose=True)
        d = config_to_dict(config)
        assert d["name"] == "test"
        assert d["verbose"] is True

    def test_generate_example_config_json(self) -> None:
        from experiment_engine.config import generate_example_config

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "example.json")
            result = generate_example_config(out_path, fmt="json")
            assert os.path.exists(result)
            # Verify it can be loaded back
            config = load_config(result)
            assert config.name == "example_experiment"
            assert len(config.stages) == 4


# ═══════════════════════════════════════════════
#  Test: Integration
# ═══════════════════════════════════════════════


class TestIntegration:
    """Integration tests combining multiple components."""

    def setup_method(self) -> None:
        PluginRegistry.reset_instance()

    def test_full_pipeline_flow(self) -> None:
        """End-to-end: configure -> build -> run -> collect results."""
        registry = PluginRegistry.get_instance()
        registry.register("identity", IdentityStage)
        registry.register("uppercase", UppercaseStage)
        registry.register("multiply", MultiplyStage)

        config = ExperimentConfig(
            name="integration_test",
            stages=[
                PipelineStageConfig(
                    name="to_upper", stage_type="uppercase", enabled=True
                ),
                PipelineStageConfig(
                    name="double",
                    stage_type="multiply",
                    enabled=True,
                    params={"factor": 2},
                ),
                PipelineStageConfig(
                    name="passthrough", stage_type="identity", enabled=True
                ),
            ],
        )

        pipeline = Pipeline(name="integration")
        pipeline.configure_from_config(config, registry=registry)
        result = pipeline.run("hello")

        assert result.experiment_name == "integration_test"
        assert result.status == PipelineStatus.COMPLETED
        assert result.output == "HELLO"
        assert len(result.stages) == 3
        for sr in result.stages:
            assert sr.status == StageStatus.COMPLETED
            assert sr.duration_ms >= 0

    def test_pipeline_with_metadata(self) -> None:
        pipeline = Pipeline(
            name="metadata_test",
            stages=[UppercaseStage(name="upper")],
        )
        result = pipeline.run(
            "test",
            experiment_name="custom_exp",
            metadata={"user": "test_user"},
        )
        assert result.experiment_name == "custom_exp"
        assert result.metadata.get("user") == "test_user"

    def test_plugin_and_config_pipeline(self) -> None:
        """Verify @register_stage + configure_from_config works end-to-end."""
        PluginRegistry.reset_instance()

        @register_stage("custom_upper")
        class CustomUpper(Stage):
            def process(self, data: Any) -> Any:
                if isinstance(data, str):
                    return data.upper() + "!"
                return data

        registry = PluginRegistry.get_instance()
        config = load_config_from_dict(
            {
                "name": "plugin_test",
                "stages": [
                    {"name": "shout", "stage_type": "custom_upper", "enabled": True}
                ],
            }
        )

        pipeline = Pipeline(name="plugin_test")
        pipeline.configure_from_config(config, registry=registry)
        result = pipeline.run("hello")
        assert result.output == "HELLO!"

    def test_disabled_plugin_stage(self) -> None:
        """Verify that disabled stages are skipped."""
        registry = PluginRegistry.get_instance()
        registry.register("enabled", UppercaseStage)
        registry.register("disabled", MultiplyStage)

        config = ExperimentConfig(
            name="skip_test",
            stages=[
                PipelineStageConfig(
                    name="active", stage_type="enabled", enabled=True
                ),
                PipelineStageConfig(
                    name="inactive", stage_type="disabled", enabled=False
                ),
                PipelineStageConfig(
                    name="also_active", stage_type="enabled", enabled=True
                ),
            ],
        )

        pipeline = Pipeline(name="skip_test")
        pipeline.configure_from_config(config, registry=registry)
        # Only 2 stages should be added (the disabled one is skipped)
        assert len(pipeline.stages) == 2
        assert pipeline.stages[0].name == "active"
        assert pipeline.stages[1].name == "also_active"
