# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-24T12:42:08.975Z
> Files: 101 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/plans/

- `synthetic-orbiting-kurzweil.md` — QCA Text Analysis System — 顶层架构规划 (~1486 tok)
- `velvety-humming-raccoon.md` — Prototype-Based QCA Text Calibration — Implementation Plan (~1513 tok)

## ./

- `.github/workflows/deploy.yml` — CI/CD: build + Pyodide bundle + gh-pages deploy (~2000 tok)
- `.gitignore` — Git ignore rules (~134 tok)
- `.pre-commit-config.yaml` (~116 tok)
- `CLAUDE.md` — OpenWolf (~57 tok)
- `FIXME.md` — FIXME — QCA Analysis Tool (~1994 tok)
- `HACK.md` — HACK — QCA Analysis Tool (~1201 tok)
- `index.html` — QCA Simulation Tool (~130 tok)
- `package-lock.json` — npm lock file (~17146 tok)
- `package.json` — Node.js package manifest (~160 tok)
- `pyproject.toml` — QCA Text Analysis Tool: citizen feedback text to fuzzy-set QCA analysis (~1235 tok)
- `TODO.md` — 功能需求与增强计划（51 项：8 P0 + 23 P1 + 20 P2，含交叉引用） (~4300 tok)
- `tsconfig.app.json` (~160 tok)
- `tsconfig.json` — TypeScript configuration (~34 tok)
- `tsconfig.node.json` (~139 tok)
- `vite.config.ts` — Vite configuration with GH Pages base, worker build, chunk splitting (~334 tok)

## .claude/

- `settings.json` (~509 tok)

## .claude/rules/

- `openwolf.md` (~313 tok)

## .github/workflows/

- `deploy.yml` — CI/CD build + Pyodide bundle + gh-pages deploy (~1906 tok)

## roadmap/

- `experiment-engine-roadmap.json` (~6510 tok)

## src/

- `App.tsx` — App (~240 tok)
- `index.css` — Styles: 19 rules, 34 vars (~1412 tok)
- `main.tsx` — React 18 entry point with BrowserRouter (~331 tok)
- `vite-env.d.ts` — Vite + plotly type declarations (~241 tok)

## src/components/

- `DistributionPlot.tsx` — Distribution histogram for fuzzy-set membership scores. (~899 tok)
- `FuzzySetHeatmap.tsx` — Plotly-based heatmap for truth table visualization. (~1294 tok)
- `NecessityXYPlot.tsx` — Necessity/Consistency XY scatter plot. (~1034 tok)
- `PipelineStatus.tsx` — Pipeline Status Indicator — shows current stage, progress bar, elapsed time. (~1125 tok)
- `Sidebar.css` — Styles: 14 rules (~537 tok)
- `Sidebar.tsx` — navItems (~392 tok)
- `SolutionViewer.tsx` — Solution Viewer — displays QCA solution types (complex, parsimonious, intermediate). (~1202 tok)
- `TruthTableViewer.tsx` — Truth Table Viewer — sortable/filterable truth table. (~1483 tok)

## src/experiment_engine/

- `__init__.py` — QCA Text Analysis Tool — citizen feedback text → fuzzy-set QCA analysis. (~452 tok)
- `__main__.py` — CLI 入口点 (~50 tok)
- `cli.py` — QCA Text Analysis CLI — complete QCA workflow commands. (~6716 tok)
- `config.py` — YAML/JSON 配置加载 + merge_defaults + CLI 覆盖 (~800 tok)
- `models.py` — Pydantic data models for the experiment-engine pipeline framework. (~9703 tok)
- `pipeline.py` — Pipeline and Stage abstract base classes. (~5114 tok)
- `plugins.py` — BasePlugin + PluginRegistry + @register_stage (~1200 tok)

## src/experiment_engine/algorithms/

- `__init__.py` — 已替换为 qca_engine/（仅保留占位） (~21 tok)

## src/experiment_engine/core/

- `__init__.py` — 重新导出 Pipeline/Stage (~100 tok)
- `parallel.py` — Parallel stage execution support. (~5370 tok)

## src/experiment_engine/io/

- `__init__.py` — 导出所有 reader/exporter + _READER_MAP (~495 tok)
- `db.py` — SQLiteDataSource, SQLiteDataWriter + PostgreSQL stubs (~800 tok)
- `exporters.py` — CSVExporter, JSONExporter, HTMLExporter (~500 tok)
- `readers.py` — Data readers for experiment-engine. (~4891 tok)
- `sources.py` — DataSource, FileDataSource, StdinDataSource, GeneratorDataSource (~600 tok)

## src/experiment_engine/qca_engine/

- `__init__.py` — QCA engine: truth table, Boolean minimization, analysis (~218 tok)
- `analyzer.py` — Main QCA analysis pipeline stage (~1639 tok)
- `consistency.py` — Core consistency and coverage calculations (~1366 tok)
- `minimization.py` — Quine-McCluskey Boolean minimization for QCA. (~2827 tok)
- `necessity.py` — Necessary condition analysis (~1107 tok)
- `solution.py` — Solution formula formatting and term label generation (~1338 tok)
- `sufficiency.py` — Sufficiency analysis for QCA solutions. (~1526 tok)
- `truth_table.py` — Truth Table construction from fuzzy-set data (~1373 tok)

## src/experiment_engine/qca_engine/advanced/

- `__init__.py` — Advanced QCA: robustness, counterfactuals, multi-outcome (~125 tok)
- `counterfactual.py` — Counterfactual analysis for QCA. (~2064 tok)
- `multi_outcome.py` — Multi-outcome comparison (~799 tok)
- `robustness.py` — Robustness and sensitivity tests for QCA results. FIXME-6,7,8,12 fixed: real coverage, membership perturb (outcome excluded), bootstrap resampling, adaptive freq thresholds. (~4635 tok)

## src/experiment_engine/report/

- `__init__.py` — 导出 LaTeXReporter (~50 tok)
- `latex_reporter.py` — 基础 LaTeX 报告 (~1200 tok)
- `qca_reporter.py` — QCA-specific LaTeX report generation. (~2653 tok)

## src/experiment_engine/text_calibration/

- `__init__.py` — Text calibration layer: raw text → fuzzy-set membership scores. (~295 tok)
- `calibrator.py` — Text calibration stage: keyword scores → fuzzy-set membership (0-1). FIXME-2,3,4,20 fixed: logistic calibrate_ragin, col_idx mapping, cached match_corpus, dedup via _process_core. (~7749 tok)
- `condition.py` — Condition set I/O helpers — YAML serialization for QCA condition definitions. (~2463 tok)
- `domains.py` — Pre-built keyword dictionaries for 5 text domains (~2655 tok)
- `keyword_dict.py` — Chinese keyword matching engine using character n-gram (~1774 tok)
- `prototype_similarity.py` — Prototype-based text similarity engine for QCA fuzzy-set calibration. (~1137 tok)
- `training.py` — Training engine for fitting calibration parameters (~2252 tok)

## src/experiment_engine/viz/

- `__init__.py` — 导出所有渲染器 (~300 tok)
- `base.py` — Renderer ABC (~150 tok)
- `console.py` — ConsoleRenderer (Rich 终端表格/统计) (~1000 tok)
- `matplotlib_renderer.py` — MatplotlibRenderer (PNG/SVG/PDF) (~800 tok)
- `plotly_renderer.py` — PlotlyRenderer (交互 HTML) (~700 tok)
- `qca_plots.py` — QCA 专用图（热力图/XY图/分布直方图/柱状图） (~1324 tok)
- `streamlit_dashboard.py` — Streamlit Web 仪表板 (~1200 tok)

## src/hooks/

- `usePyodide.ts` — React hook wrapping the Pyodide bridge singleton. (~452 tok)
- `useQCAWorkflow.ts` — Hook that ties the Pyodide bridge to the pipeline state context. Has keyword + prototype calibration workflow methods. (~2900 tok)

## src/layouts/

- `MainLayout.css` — Styles: 2 rules (~54 tok)
- `MainLayout.tsx` — MainLayout (~85 tok)

## src/pages/

- `Dashboard.css` — Styles: 22 rules (~534 tok)
- `Dashboard.tsx` — Dashboard — QCA pipeline overview with pipeline status widget (~2824 tok)
- `DataInput.css` — Styles: 11 rules (~398 tok)
- `DataInput.tsx` — Data Input — text corpus upload + condition set YAML editor + prototype calibration mode. (~13000 tok)
- `Results.css` — Styles: 17 rules (~484 tok)
- `Results.tsx` — Results — displays all QCA analysis output (~3472 tok)
- `Settings.css` — Styles: 16 rules (~443 tok)
- `Settings.tsx` — Settings — QCA analysis parameters, calibration defaults (~3563 tok)

## src/pyodide/

- `engine.ts` — PyodideEngine singleton: CDN Pyodide load, micropip deps, tar extract (~3692 tok)
- `types.ts` — JS<->Python bridge types (~717 tok)

## src/services/

- `pyodide.ts` — Main-thread Pyodide bridge — methods called from React components. (~3295 tok)
- `pyodide.worker.ts` — Pyodide Web Worker — runs Python/NumPy in a background thread so the (~6121 tok)

## src/store/

- `QCAPipelineContext.tsx` — React Context for tracking the QCA pipeline lifecycle. Supports keyword + prototype calibration. (~2600 tok)

## src/types/

- `index.ts` — Legacy types — kept for backward compatibility (~400 tok)
- `qca.ts` — QCA-specific TypeScript interfaces mirroring experiment_engine/models.py. (~2843 tok)

## tests/

- `test_integration.py` — Integration tests for experiment-engine. (~11590 tok)
- `test_pipeline.py` — Unit tests for the experiment-engine pipeline framework. (~9264 tok)
- `test_prototype_similarity.py` — Unit tests for prototype-based text similarity engine. (~4412 tok)
- `test_viz.py` — Unit tests for visualization module (~11630 tok)

## tmp/

- `test_escaping.py` — Functional test for LaTeX escaping in qca_reporter.py. (~599 tok)
