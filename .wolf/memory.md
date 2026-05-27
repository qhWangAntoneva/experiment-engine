# Memory

> Active sessions: most recent 2. Older sessions archived to `memory-archive.md`.

| 2026-05-27 | Session start: 接手项目. READ handover.md, cerebrum.md, TODO.md, FIXME.md, HACK.md, buglog.json — HEAD fc3b64a, 532 passed, 27 P2 items (S级已全部完成, 22 remaining). | handover.md | session start | ~500 |
| 2026-05-27 | Logged bug-358 (Pyodide pydantic not loaded), updated cerebrum Do-Not-Repeat. Python/TS/tests all clean: OK, 0 errors, 532 passed. | buglog.json, cerebrum.md | done | ~10 |
| 2026-05-27 | Fix stale closure: added importedConditionSet to handleCalibrate and handleRunPipeline dependency arrays | DataInput.tsx | done | ~2 |
| 2026-05-27 | P2-28: Added 3 validation checks to validate_qca_output.py: membership shape (N_cases x N_cols), outcome column unique count (WARN if < 2), solution quality score (avg of best consistency*coverage). Updated summary table with Quality column. | validate_qca_output.py | done | ~600 |

| 2026-05-27 | Fixed Use Template bug (DataInput.tsx ignored state.conditionSet). Added useEffect hydration. TS build clean. | DataInput.tsx | fixed | ~200 |
| 2026-05-27 | Launched 3 profession-agents for optimization analysis (Backend/Algorithm, Frontend/Viz, DevOps/Report). All delivered reports. | handover.md | analysis complete | ~500 |
| 2026-05-27 | i18n for "Load 30 Sample Cases": added sampleDataBtn/sampleDataTooltip/sampleLoaded to translations.ts (zh+en) and updated DataInput.tsx. TS build clean. | DataInput.tsx, translations.ts | done | ~100 |
| 2026-05-27 | Track A Steps 2-4: TemplateLibrary uses setYamlContent directly instead of setConditionSet + hydration useEffect. Removed DataInput hydration useEffect. Fixed handleLoadSampleData. TS build clean. | TemplateLibrary.tsx, DataInput.tsx | done | ~250 |
| 2026-05-27 | P2-15/19/21: PluginRegistry DI, weighted max similarity, TextCase.outcome float. 532 tests pass. | plugins.py, cosine_similarity.py, qca.py | all done | ~500 |
| 2026-05-27 | Package optimization plan: investigated all viz/report/pipeline modules, identified impedance mismatch between QCAPlotBuilder dicts and Renderer InputData, documented current output quality issues, wrote plan in .wolf/plans/package_optimization_plan.md | viz/*.py, report/*.py, api.py, pipeline.py, run_pipeline.py, TODO.md, validate_qca_output.py, configs/config.yaml | plan written | ~500 |
| 2026-05-27 | P2-31: Changed displayModeBar: false to displayModeBar: 'hover' in 4 Plotly components, added toImageButtonOptions for PNG download | DistributionPlot.tsx, FuzzySetHeatmap.tsx, NecessityXYPlot.tsx, CalibrationPreview.tsx | done | ~100 |
| 2026-05-27 | FIX: All-0.5 membership bug. Added trigram fallback to _precompute_scores for CLI/api path without BERT embeddings. | calibrator.py | fixed | ~150 |
| 2026-05-27 | P2-4/P2-5: HelpTooltip component, ExportButton + LaTeXPreviewModal, i18n keys, tooltips on Settings/DataInput/Results, LaTeX preview + toast. Build clean. | HelpTooltip.tsx, ExportButton.tsx, LaTeXPreviewModal.tsx, translations.ts, Settings.tsx, DataInput.tsx, Results.tsx | all done | ~800 |
| 2026-05-27 | P2-17 + Bug: created api.py with 5 public functions, refactored cli.py to thin wrappers, fixed --output dir convention for robustness/counterfactuals. 532 tests pass. | api.py (new), cli.py | all done | ~300 |
| 2026-05-27 | Completed trust domain QCA pipeline: counterfactuals, robustness, and LaTeX report generation. All 5 output files in qca_output/trust/. | qca_output/trust/ | All steps succeeded | ~200 |
| 2026-05-27 | Fixed BUG-1 (run_calibrate ignores expected_outcome column) and BUG-2 (no domain filtering) in api.py; added run_viz/run_docx_report stub functions. 532 tests pass, all 5 domains verify ground-truth outcome. | api.py | 532 passed | ~200 |
| 2026-05-27 | T1: Added vacuous solution detection to LaTeX reporter (renders \top with note). T2: Verified data flow from pipeline to reporter (correct). T3: Integrated DOCX report into pipeline + api.py (supports "docx" format). T4: Rewrote validate_qca_output.py - fixed format-code 'f' for str error, added summary table, solution quality check, outcome variation check. T5: Deleted 4 stale root-level qca_output files. All 532 tests pass, DOCX 36825 bytes. | qca_reporter.py, docx_reporter.py, cli.py, api.py, validate_qca_output.py, buglog.json | all done | ~500 |
| 2026-05-26 | P1-5/8/9/10 + P2-20/22: CaseMembershipTable, CalibrationPreview, Privacy, Recent Runs, configurable steepness, --variant flag. 532 tests pass. | multiple | all done | ~5000 |
| 01:49 | Edited src/experiment_engine/cli.py | modified report() | ~179 |
| 01:49 | Edited src/pages/DataInput.tsx | 2→6 lines | ~98 |
| 01:50 | Edited src/pages/Results.tsx | added 2 import(s) | ~48 |
| 01:50 | Session end: 29 writes across 13 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 23 reads | ~12994 tok |
| 01:50 | Edited src/pages/Results.tsx | CSS: message, type | ~136 |
| 01:50 | Edited src/experiment_engine/cli.py | removed 42 lines | ~1 |
| 2026-05-27 | 3 Reviewers confirmed: all 3 algorithm bugs fixed, 30-case samples generated, pre-commit root cause found. Push notes recorded in persistent memory. Commit 737c3c4 pushed. | all files | completed | ~500 |
| 01:50 | Edited src/experiment_engine/cli.py | 7→7 lines | ~38 |
| 01:50 | Edited src/pages/Results.tsx | expanded (+89 lines) | ~1045 |
| 01:50 | Edited src/pages/Results.tsx | modified MetricChip() | ~226 |
| 01:51 | Edited src/pages/Results.tsx | modified toFixed() | ~204 |
| 01:51 | Edited src/pages/Results.tsx | 4→3 lines | ~32 |
| 01:51 | Edited src/experiment_engine/cli.py | 6→5 lines | ~36 |
| 01:52 | Edited src/i18n/translations.ts | removed 14 lines | ~25 |
| 01:52 | Edited TODO.md | inline fix | ~30 |
| 01:52 | Edited TODO.md | inline fix | ~73 |
| 01:53 | Edited TODO.md | inline fix | ~10 |
| 01:53 | Edited TODO.md | inline fix | ~11 |
| 01:53 | Edited TODO.md | inline fix | ~12 |
| 01:53 | Edited TODO.md | 2→2 lines | ~10 |
| 01:53 | Session end: 45 writes across 13 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 23 reads | ~36049 tok |
| 2026-05-27 | Deep-dive analysis of "unknown worker error": read 15 source files (pyodide.ts, pyodide.worker.ts, bert-engine.ts, DataInput.tsx, Settings.tsx, Dashboard.tsx, usePyodide.ts, useQCAWorkflow.ts, vite.config.ts, index.html, deploy.yml, package.json, dist/ bundles). Identified 6 possible root causes, primary is missing `'wasm-unsafe-eval'` in CSP `script-src` blocking WASM in Chrome 130+. Wrote analysis to .wolf/plans/worker_error_analysis.md with fixes and verification steps. | .wolf/plans/worker_error_analysis.md, index.html, pyodide.ts, pyodide.worker.ts, bert-engine.ts | analysis complete | ~24000 |
| 01:56 | Session end: 47 writes across 13 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 23 reads | ~36065 tok |
| 01:59 | Session end: 47 writes across 13 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 24 reads | ~36065 tok |
| 02:03 | Session end: 47 writes across 13 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 31 reads | ~36065 tok |
| 02:13 | Session end: 47 writes across 13 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 33 reads | ~36065 tok |
| 02:14 | Session end: 47 writes across 13 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 35 reads | ~36065 tok |
| 02:15 | Edited src/experiment_engine/text_calibration/calibrator.py | modified not() | ~142 |
| 02:15 | Edited src/experiment_engine/text_calibration/calibrator.py | modified _fallback_text_scores() | ~1137 |
| 02:16 | Session end: 49 writes across 14 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 41 reads | ~45338 tok |
| 02:17 | Session end: 49 writes across 14 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 43 reads | ~45338 tok |
| 02:17 | Session end: 49 writes across 14 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 43 reads | ~45338 tok |
| 02:18 | Session end: 49 writes across 14 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 43 reads | ~51537 tok |
| 02:23 | Created run_pipeline.py | — | ~837 |
| 02:24 | Session end: 50 writes across 15 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 44 reads | ~52374 tok |
| 02:34 | Session end: 50 writes across 15 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 53 reads | ~53211 tok |
| 02:35 | Session end: 50 writes across 15 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 53 reads | ~53211 tok |
| 02:41 | Session end: 50 writes across 15 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 53 reads | ~53211 tok |
| 02:43 | Session end: 50 writes across 15 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 65 reads | ~53203 tok |
| 2026-05-27 | Technical advisory investigation: confirmed _fallback_text_scores works for all 5 domains. Root cause of all-1/all-0 outcome is CSV expected_outcome never used (api.py:54). 30 cases not filtered by domain. Wrote plan in .wolf/plans/technical_advisory_plan.md | api.py, calibrator.py, *.yaml, sample_cases.csv, analyzer.py, truth_table.py, qca_reporter.py, solution.py, run_pipeline.py, qca_plots.py, viz/* | plan written | ~2000 |
| 02:44 | Session end: 50 writes across 15 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 69 reads | ~53203 tok |
| 02:45 | Re-ran QCA pipeline for all 5 domains with FIXED calibration, validated all outputs. All membership variance > 0 (fix confirmed). Solutions non-empty for 4/5 domains. | qca_output/*/ | all done | ~500 |
| 02:45 | Session end: 50 writes across 15 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 69 reads | ~53203 tok |
| 02:49 | Session end: 50 writes across 15 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 69 reads | ~53203 tok |
| 02:50 | Edited src/experiment_engine/report/qca_reporter.py | modified _solutions_section() | ~498 |
| 02:50 | Edited src/experiment_engine/cli.py | expanded (+15 lines) | ~328 |
| 02:50 | Edited src/experiment_engine/api.py | expanded (+16 lines) | ~307 |
| 02:50 | Edited src/experiment_engine/cli.py | inline fix | ~15 |
| 02:50 | Edited src/experiment_engine/cli.py | modified in() | ~96 |
| 02:51 | Session end: 55 writes across 16 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 70 reads | ~54640 tok |
| 02:51 | Created validate_qca_output.py | — | ~4320 |
| 02:51 | Edited src/experiment_engine/api.py | modified run_calibrate() | ~708 |
| 02:52 | Edited src/experiment_engine/report/docx_reporter.py | modified _set_run_font() | ~77 |
| 02:52 | Created src/experiment_engine/viz/viz_bridge.py | — | ~3713 |
| 02:52 | Edited src/experiment_engine/api.py | modified run_viz() | ~776 |
| 02:52 | Edited src/experiment_engine/api.py | 5→10 lines | ~102 |
| 02:53 | Edited src/experiment_engine/viz/viz_bridge.py | modified range() | ~322 |
| 02:53 | Created run_pipeline.py | — | ~1079 |
| 02:53 | Edited src/experiment_engine/viz/viz_bridge.py | subplots_adjust() → str() | ~108 |
| 02:54 | Session end: 64 writes across 19 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 71 reads | ~70892 tok |
| 2026-05-27 | Created viz_bridge.py bridging QCAPlotBuilder dicts to matplotlib PNG output. Created run_pipeline.py with --viz-only step. Bridge handles missing solutions gracefully (sufficiency/bar skipped), produces 3-5 PNGs per domain. 532 tests pass, no regressions. | viz_bridge.py, run_pipeline.py | all done | ~500 |
| 02:55 | Session end: 64 writes across 19 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 71 reads | ~70946 tok |
| 02:55 | Session end: 64 writes across 19 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 71 reads | ~70946 tok |
| 02:57 | Edited validate_qca_output.py | "C:\Users\lenovos\QCA Anal" → "qca_output" | ~24 |
| 02:59 | Edited run_pipeline.py | inline fix | ~10 |
| 02:59 | Edited src/experiment_engine/api.py | 3→2 lines | ~14 |
| 02:59 | Edited src/experiment_engine/viz/viz_bridge.py | inline fix | ~17 |
| 02:59 | Edited pyproject.toml | 2→3 lines | ~46 |
| 03:00 | Edited validate_qca_output.py | 4→3 lines | ~39 |
| 03:00 | Edited validate_qca_output.py | inline fix | ~22 |
| 03:00 | Edited validate_qca_output.py | "    First lines: {[l.stri" → "    First lines: {[line.s" | ~22 |
| 03:00 | Edited validate_qca_output.py | 3→2 lines | ~29 |
| 03:01 | Session end: 73 writes across 20 files (TODO.md, qca.py, cosine_similarity.py, HelpTooltip.tsx, plugins.py) | 72 reads | ~67933 tok |

## Session: 2026-05-26 03:04

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 03:15 | Created ../.claude/projects/C--Users-lenovos-QCA-Analysis-Tool/memory/push_notes.md | — | ~264 |
| 03:17 | Session end: 1 writes across 1 files (push_notes.md) | 8 reads | ~4401 tok |

## Session: 2026-05-26 03:17

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 03:24 | Edited src/pages/DataInput.tsx | inline fix | ~21 |
| 03:24 | Edited src/pages/DataInput.tsx | 7→8 lines | ~60 |
| 03:24 | Edited src/pages/DataInput.tsx | CSS: type, conditionSet | ~132 |
| 03:25 | Session end: 3 writes across 1 files (DataInput.tsx) | 34 reads | ~213 tok |
| 03:27 | Created TODO.md | — | ~1144 |
| 03:28 | Edited src/experiment_engine/report/qca_reporter.py | 3→4 lines | ~37 |
| 03:31 | Edited src/experiment_engine/cli.py | modified report() | ~152 |
| 03:35 | Edited src/experiment_engine/api.py | inline fix | ~4 |
| 03:35 | Edited src/experiment_engine/cli.py | inline fix | ~4 |
| 03:35 | Edited src/experiment_engine/pyodide_handlers.py | inline fix | ~4 |
| 03:35 | Edited src/experiment_engine/qca_engine/advanced/robustness.py | inline fix | ~4 |
| 03:35 | Edited src/experiment_engine/qca_engine/analyzer.py | inline fix | ~4 |
| 03:35 | Edited src/experiment_engine/qca_engine/necessity.py | inline fix | ~4 |
| 03:35 | Edited src/experiment_engine/qca_engine/sufficiency.py | inline fix | ~4 |
| 03:35 | Edited src/experiment_engine/qca_engine/truth_table.py | inline fix | ~4 |
| 03:35 | Edited src/experiment_engine/viz/qca_plots.py | inline fix | ~4 |
| 03:35 | Edited src/experiment_engine/viz/viz_bridge.py | inline fix | ~4 |
| 03:35 | Edited tests/test_qca_core.py | inline fix | ~4 |
| 03:35 | Edited tests/test_robustness.py | inline fix | ~4 |
| 03:35 | Edited src/experiment_engine/models/qca.py | removed 5 lines | ~1 |
| 03:35 | Edited src/experiment_engine/models/__init__.py | 2→1 lines | ~20 |
| 03:35 | Edited src/experiment_engine/models/__init__.py | 2→1 lines | ~6 |
| 03:35 | Edited src/experiment_engine/models/__init__.py | 2→1 lines | ~6 |
| 03:35 | Edited src/experiment_engine/__init__.py | 27→26 lines | ~142 |
| 03:35 | Edited src/experiment_engine/__init__.py | 3→2 lines | ~11 |
| 03:35 | Edited src/types/qca.ts | removed 5 lines | ~1 |
| 03:35 | Edited src/types/index.ts | inline fix | ~6 |
| 03:40 | Edited src/components/DistributionPlot.tsx | expanded (+9 lines) | ~69 |
| 03:40 | Edited src/components/FuzzySetHeatmap.tsx | expanded (+6 lines) | ~68 |
| 03:40 | Edited src/components/NecessityXYPlot.tsx | expanded (+9 lines) | ~69 |
| 03:40 | Edited src/components/CalibrationPreview.tsx | expanded (+9 lines) | ~70 |
| 03:41 | Session end: 30 writes across 23 files (DataInput.tsx, TODO.md, qca_reporter.py, cli.py, api.py) | 48 reads | ~5171 tok |
| 03:45 | Edited validate_qca_output.py | modified check_outcome_variation() | ~158 |
| 03:45 | Edited validate_qca_output.py | modified check_outcome_variation() | ~538 |
| 03:45 | Edited validate_qca_output.py | expanded (+26 lines) | ~348 |
| 03:45 | Edited validate_qca_output.py | modified items() | ~295 |
| 03:49 | Session end: 34 writes across 24 files (DataInput.tsx, TODO.md, qca_reporter.py, cli.py, api.py) | 48 reads | ~11908 tok |

## Session: 2026-05-26 03:50

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 04:03 | Edited src/pages/DataInput.tsx | added 1 import(s) | ~36 |
| 04:03 | Edited src/pages/DataInput.tsx | added 1 import(s) | ~32 |
| 04:03 | Edited src/components/TemplateLibrary.tsx | inline fix | ~20 |
| 04:03 | Edited src/components/TemplateLibrary.tsx | CSS: CSQCA, qca_variant | ~192 |
| 04:04 | Session end: 4 writes across 2 files (DataInput.tsx, TemplateLibrary.tsx) | 11 reads | ~16471 tok |
| 04:07 | Session end: 4 writes across 2 files (DataInput.tsx, TemplateLibrary.tsx) | 12 reads | ~16471 tok |
| 2026-05-27 | Created src/utils/conditionSetToYaml.ts — builds YAML from ConditionSet with 2-space indent, controlled quoting, null safety. Verified round-trip with js-yaml. | conditionSetToYaml.ts | done | ~300 |
| 05:10 | Edited src/pages/DataInput.tsx | expanded (+35 lines) | ~497 |
| 05:10 | Edited src/pages/DataInput.tsx | added 1 import(s) | ~38 |
| 05:10 | Edited src/pages/DataInput.tsx | 8→9 lines | ~66 |
| 05:10 | Edited src/pages/DataInput.tsx | added error handling | ~316 |
| 05:10 | Edited src/pages/DataInput.tsx | CSS: marginTop | ~330 |
| 05:11 | Session end: 16 writes across 4 files (translations.ts, DataInput.tsx, conditionSetToYaml.ts, __test_condset_yaml.ts) | 54 reads | ~20485 tok |
| 05:17 | Edited src/components/TemplateLibrary.tsx | added 1 import(s) | ~48 |
| 05:17 | Edited src/components/TemplateLibrary.tsx | inline fix | ~14 |
| 05:17 | Edited src/components/TemplateLibrary.tsx | 4→4 lines | ~32 |
| 05:17 | Edited src/types/qca.ts | expanded (+68 lines) | ~474 |
| 05:17 | Edited src/types/qca.ts | inline fix | ~12 |
| 05:17 | Edited src/pages/DataInput.tsx | inline fix | ~26 |
| 05:17 | Edited src/pages/DataInput.tsx | — | ~0 |
| 27/05 14:10 | Track A Step 1: moved DEFAULT_CONDITION_SET_YAML from DataInput.tsx to types/qca.ts | src/pages/DataInput.tsx src/types/qca.ts | done | ~50 tokens |
| 05:18 | Edited src/pages/DataInput.tsx | inline fix | ~18 |
| 05:18 | Edited src/pages/DataInput.tsx | added 1 import(s) | ~42 |
| 05:18 | Edited src/pages/DataInput.tsx | reduced (-8 lines) | ~44 |
| 05:18 | Edited src/pages/DataInput.tsx | modified catch() | ~106 |
| 05:18 | Edited src/pages/DataInput.tsx | 9→7 lines | ~56 |
| 05:19 | Session end: 28 writes across 6 files (translations.ts, DataInput.tsx, conditionSetToYaml.ts, __test_condset_yaml.ts, TemplateLibrary.tsx) | 60 reads | ~26385 tok |
| 2026-05-27 | removed public/samples/ dead code | public/samples/ | done | ~5 |
| 2026-05-27 | Updated deploy.yml actions: checkout@v4→v6, setup-node@v4→v6, configure-pages@v4→v6, upload-pages-artifact@v3→v5, deploy-pages@v4→v5 — all now use Node 24 runtime, resolves Node 20 deprecation (2026-06-02) | deploy.yml | done | ~50 |
| 05:22 | Edited src/i18n/translations.ts | 2→6 lines | ~49 |
| 05:22 | Edited src/i18n/translations.ts | 2→6 lines | ~66 |
| 05:22 | Edited src/i18n/translations.ts | 2→6 lines | ~90 |
| 05:22 | Edited src/pages/DataInput.tsx | 8→9 lines | ~98 |
| 05:22 | Edited src/pages/DataInput.tsx | "Loaded ${entries.length} " → "dataInput.sampleLoaded" | ~26 |
| 05:24 | Session end: 33 writes across 6 files (translations.ts, DataInput.tsx, conditionSetToYaml.ts, __test_condset_yaml.ts, TemplateLibrary.tsx) | 60 reads | ~26713 tok |
| 05:38 | Edited src/types/index.ts | 2→1 lines | ~6 |
| 05:39 | designqc: captured 6 screenshots (186KB, ~15000 tok) | /, /Compare, /Dashboard, /DataInput, /Results, /Settings | ready for eval | ~0 |

## Session: 2026-05-26 05:40

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 05:44 | Edited .github/workflows/deploy.yml | inline fix | ~10 |
| 05:44 | Edited .github/workflows/deploy.yml | inline fix | ~10 |
| 05:44 | Edited .github/workflows/deploy.yml | inline fix | ~12 |
| 05:45 | Edited .github/workflows/deploy.yml | inline fix | ~14 |
| 05:45 | Edited .github/workflows/deploy.yml | inline fix | ~11 |
| 05:47 | Session end: 5 writes across 1 files (deploy.yml) | 2 reads | ~2329 tok |

## Session: 2026-05-27 11:21

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 11:35 | Edited src/services/pyodide.worker.ts | 5→6 lines | ~24 |
| 11:35 | Edited src/experiment_engine/config.py | 3→1 lines | ~9 |
| 11:35 | Edited src/experiment_engine/config.py | added 1 import(s) | ~52 |
| 11:35 | Session end: 3 writes across 2 files (pyodide.worker.ts, config.py) | 12 reads | ~10672 tok |
| 11:35 | Session end: 3 writes across 2 files (pyodide.worker.ts, config.py) | 12 reads | ~10672 tok |
| 11:35 | Session end: 3 writes across 2 files (pyodide.worker.ts, config.py) | 12 reads | ~10672 tok |
| 11:37 | Session end: 3 writes across 2 files (pyodide.worker.ts, config.py) | 12 reads | ~10672 tok |
| 11:39 | Created tmp/clear_cache.mjs | — | ~479 |
| 11:40 | Created tmp/verify_page.mjs | — | ~166 |
| 11:40 | Created tmp/verify_page.mjs | — | ~147 |
| 11:40 | Session end: 6 writes across 4 files (pyodide.worker.ts, config.py, clear_cache.mjs, verify_page.mjs) | 12 reads | ~11520 tok |
| 11:41 | Session end: 6 writes across 4 files (pyodide.worker.ts, config.py, clear_cache.mjs, verify_page.mjs) | 12 reads | ~11520 tok |
| 11:42 | Session end: 6 writes across 4 files (pyodide.worker.ts, config.py, clear_cache.mjs, verify_page.mjs) | 12 reads | ~11520 tok |

## Session: 2026-05-27 11:43

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 11:50 | Created ../../../tmp/playwright-test/devtools_test.mjs | — | ~951 |
| 11:52 | Created ../../../tmp/playwright-test/devtools_test2.mjs | — | ~1528 |
| 11:52 | Created ../../../tmp/playwright-test/devtools_test3.mjs | — | ~1406 |
| 11:53 | Edited ../../../tmp/playwright-test/devtools_test3.mjs | added 6 condition(s) | ~527 |
| 11:54 | Created ../../../tmp/playwright-test/devtools_test4.mjs | — | ~885 |

## Session: 2026-05-27 11:56

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 11:58 | Edited index.html | 3→3 lines | ~62 |
| 11:58 | Edited src/services/pyodide.ts | added optional chaining | ~124 |
| 11:58 | Edited src/services/pyodide.worker.ts | added optional chaining | ~221 |
| 11:58 | Edited src/i18n/translations.ts | 5→9 lines | ~69 |
| 11:58 | Edited src/i18n/translations.ts | 1→4 lines | ~47 |
| 11:59 | Edited src/i18n/translations.ts | 1→4 lines | ~58 |

| 04:00 | Fixed CSP (wasm-unsafe-eval, worker-src cdn), worker error handlers, missing i18n keys | index.html, src/services/pyodide.ts, src/services/pyodide.worker.ts, src/i18n/translations.ts | TS build clean, dist CSP verified | ~1200 |
| 04:30 | Reviewed all 4 fixes: CSP `wasm-unsafe-eval` + worker-src cdn, worker onerror detail extraction, onunhandledrejection handler, i18n keys. Build 0 errors. DevTools verification: no CSP/worker/WASM errors, app loads correctly with CSP active. | .wolf/plans/reviewer_report.md | review PASS | ~800 |
| 12:02 | Created tmp/reviewer_test.mjs | — | ~849 |
