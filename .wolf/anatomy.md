# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-24T03:40:20.701Z
> Files: 76 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/plans/

- `synthetic-orbiting-kurzweil.md` — QCA Text Analysis System — 顶层架构规划 (~1486 tok)

## ./

- `.gitignore` — Git ignore rules (~7 tok)
- `.pre-commit-config.yaml` (~116 tok)
- `CLAUDE.md` — OpenWolf (~57 tok)
- `index.html` — QCA Simulation Tool (~130 tok)
- `package-lock.json` — npm lock file (~17146 tok)
- `package.json` — Node.js package manifest (~142 tok)
- `pyproject.toml` — QCA Text Analysis Tool: citizen feedback text to fuzzy-set QCA analysis (~1214 tok)
- `tsconfig.app.json` (~160 tok)
- `tsconfig.json` — TypeScript configuration (~34 tok)
- `tsconfig.node.json` (~139 tok)
- `vite.config.ts` — Vite build configuration (~52 tok)

## .claude/

- `settings.json` (~441 tok)

## .claude/rules/

- `openwolf.md` (~313 tok)

## src/

- `App.tsx` — App (~201 tok)
- `index.css` — Styles: 19 rules, 34 vars (~1412 tok)
- `main.tsx` (~93 tok)

## src/components/

- `Sidebar.css` — Styles: 14 rules (~537 tok)
- `Sidebar.tsx` — navItems (~393 tok)

## src/experiment_engine/

- `__init__.py` — v0.2.0 exports: 泛型模型 + QCA 模型 (FuzzySetData, TruthTable, QCASolutions, QCAAnalysisResult) (~368 tok)
- `__main__.py` — CLI 入口点 (~50 tok)
- `cli.py` — 9 命令 CLI (calibrate/train/analyze/robustness/counterfactuals/report/run/validate/list-conditions) (~6655 tok)
- `config.py` — YAML/JSON 配置加载 + merge_defaults + CLI 覆盖 (~800 tok)
- `models.py` — 30+ Pydantic v2 模型：泛型 (InputData/OutputData/PipelineResult) + QCA (FuzzySetData/TruthTable/QCASolutions...) (~8981 tok)
- `pipeline.py` — Stage (ABC: setup/process/teardown) + Pipeline (composite Stage) (~1800 tok)
- `plugins.py` — BasePlugin(Stage) + PluginRegistry (singleton) + @register_stage + PluginLoader (~1200 tok)

## src/experiment_engine/algorithms/

- `__init__.py` — 已替换为 qca_engine/（仅保留占位） (~21 tok)

## src/experiment_engine/core/

- `__init__.py` — 重新导出 Pipeline/Stage (~100 tok)
- `parallel.py` — ParallelStageGroup + ParallelPipeline (ThreadPoolExecutor) (~1000 tok)

## src/experiment_engine/io/

- `__init__.py` — 导出所有 reader/exporter + _READER_MAP (含 text_corpus) (~495 tok)
- `db.py` — SQLiteDataSource, SQLiteDataWriter + PostgreSQL stubs (~800 tok)
- `exporters.py` — CSVExporter, JSONExporter, HTMLExporter (~500 tok)
- `readers.py` — Data readers for experiment-engine. (~4776 tok)
- `sources.py` — DataSource, FileDataSource, StdinDataSource, GeneratorDataSource (~600 tok)

## src/experiment_engine/qca_engine/

- `__init__.py` — QCA engine: truth table construction, Boolean minimization, and analysis. (~218 tok)
- `analyzer.py` — Main QCA analysis pipeline stage — orchestrates the full analysis. (~1639 tok)
- `consistency.py` — Core consistency and coverage calculations for QCA. (~1366 tok)
- `minimization.py` — Quine-McCluskey Boolean minimization for QCA. (~2384 tok)
- `necessity.py` — Necessary condition analysis for QCA. (~1107 tok)
- `solution.py` — Solution formula formatting and term label generation. (~1338 tok)
- `sufficiency.py` — Sufficiency analysis for QCA solutions. (~1375 tok)
- `truth_table.py` — QCA Truth Table construction from fuzzy-set membership data. (~1373 tok)

## src/experiment_engine/qca_engine/advanced/

- `__init__.py` — Advanced QCA analysis: robustness, counterfactuals, multi-outcome comparison. (~125 tok)
- `counterfactual.py` — Counterfactual analysis for QCA. (~1864 tok)
- `multi_outcome.py` — Multi-outcome comparison for QCA. (~799 tok)
- `robustness.py` — Robustness and sensitivity tests for QCA results. (~2091 tok)

## src/experiment_engine/report/

- `__init__.py` — 导出 LaTeXReporter (~50 tok)
- `latex_reporter.py` — 基础 LaTeX 报告（从 PipelineResult 生成） (~1200 tok)
- `qca_reporter.py` — QCA 专用 LaTeX 报告（真值表+解+必要性+稳健性） (~2142 tok)

## src/experiment_engine/text_calibration/

- `__init__.py` — Text calibration layer: raw text → fuzzy-set membership scores. (~256 tok)
- `calibrator.py` — Text calibration stage: keyword scores → fuzzy-set membership (0-1). (~2666 tok)
- `condition.py` — Condition set I/O helpers — YAML serialization for QCA condition definitions. (~1863 tok)
- `domains.py` — Pre-built keyword dictionaries and default conditions for 5 text domains. (~2655 tok)
- `keyword_dict.py` — Chinese keyword matching engine using character n-gram tokenization. (~1774 tok)
- `training.py` — Training engine for fitting calibration parameters from labeled samples. (~2252 tok)

## src/experiment_engine/viz/

- `__init__.py` — 导出所有渲染器 (~300 tok)
- `base.py` — Renderer ABC (~150 tok)
- `console.py` — ConsoleRenderer (Rich 终端表格/统计) (~1000 tok)
- `matplotlib_renderer.py` — MatplotlibRenderer (PNG/SVG/PDF) (~800 tok)
- `plotly_renderer.py` — PlotlyRenderer (交互 HTML) (~700 tok)
- `qca_plots.py` — QCA 专用图（热力图/XY图/分布直方图/柱状图） (~1324 tok)
- `streamlit_dashboard.py` — Streamlit Web 仪表板 (~1200 tok)

## src/layouts/

- `MainLayout.css` — Styles: 2 rules (~54 tok)
- `MainLayout.tsx` — MainLayout (~85 tok)

## src/pages/

- `Dashboard.css` — Styles: 22 rules (~534 tok)
- `Dashboard.tsx` — metrics — renders table (~973 tok)
- `DataInput.css` — Styles: 11 rules (~398 tok)
- `DataInput.tsx` — fieldGroups — renders form — uses useState (~2015 tok)
- `Results.css` — Styles: 17 rules (~484 tok)
- `Results.tsx` — results — renders table (~1182 tok)
- `Settings.css` — Styles: 16 rules (~443 tok)
- `Settings.tsx` — settings — renders form (~1484 tok)

## src/types/

- `index.ts` — Exports SimulationParams, SimulationResult, MetricCardData, NavItem (~173 tok)

## tests/

- `test_algorithms.py` — Tests for the built-in algorithm stages (linear regression, K-Means). (~2489 tok)
- `test_integration.py` — Integration tests for experiment-engine. (~10623 tok)
- `test_viz.py` — Unit tests for the experiment-engine visualization (viz) module. (~11630 tok)
