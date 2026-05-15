# experiment-engine Phase 1 Fix — 共享接口契约

## 项目状态
- 骨架已搭好（pipeline/plugins/models/config/cli/io/viz），18源文件
- **关键断裂点**：config.yaml格式不匹配、CLI run命令是placeholder、缺entry points
- GitHub: https://github.com/qhWangAntoneva/experiment-engine.git (branch: master)
- 项目根: ~/experiment-engine/

## 核心数据模型（定义在 models.py）

- ExperimentConfig: {name, description, version, stages: List[PipelineStageConfig], global_params, output_dir, verbose}
- PipelineStageConfig: {name, stage_type, enabled, params}
- InputData: {data: T, metadata, timestamp}
- OutputData: {raw: T, processed: Optional[T], metadata, timestamp}
- StageResult: {stage_name, stage_type, status, duration_ms, started_at, completed_at, error, metadata}
- PipelineResult: {experiment_name, status, total_duration_ms, stages: List[StageResult], started_at, completed_at, output, metadata}
- StageStatus: PENDING / RUNNING / COMPLETED / FAILED / SKIPPED
- PipelineStatus: PENDING / RUNNING / COMPLETED / FAILED / PARTIAL

## 配置文件格式约定

使用 YAML/JSON，顶层字段对应 ExperimentConfig 字段名：
```yaml
name: "my-experiment"
description: "..."
stages:
  - name: "load-data"
    stage_type: "csv_loader"
    enabled: true
    params:
      file_path: "data.csv"
      delimiter: ","
```

## 模块路径约定

- experiment_engine.pipeline → Pipeline, Stage
- experiment_engine.models → 所有Pydantic模型
- experiment_engine.plugins → PluginRegistry, BasePlugin, register_stage, PluginLoader
- experiment_engine.config → load_config, merge_defaults, apply_cli_overrides
- experiment_engine.cli → Click CLI (run/validate/list-plugins)
- experiment_engine.io → readers, sources, exporters
- experiment_engine.viz → base, matplotlib_renderer, plotly_renderer, console, streamlit_dashboard

## CLI命令签名

- run: --config/-c (required), --output/-o (optional), --verbose/-v
- validate: --config/-c (required)
- list-plugins: 无参数
