# Memory

> Active sessions: most recent 2. Older sessions archived to `memory-archive.md`.

| 2026-05-27 | P2-37: Unified report CLI path via api.run_report(). Removed redundant file load, console-only fallback. 532 tests pass. | cli.py | done | ~50 |
| 2026-05-27 | P2-28: Added 3 validation checks to validate_qca_output.py: membership shape (N_cases x N_cols), outcome column unique count (WARN if < 2), solution quality score (avg of best consistency*coverage). Updated summary table with Quality column. | validate_qca_output.py | done | ~600 |

| 2026-05-27 | Fixed Use Template bug (DataInput.tsx ignored state.conditionSet). Added useEffect hydration. TS build clean. | DataInput.tsx | fixed | ~200 |
| 2026-05-27 | Launched 3 profession-agents for optimization analysis (Backend/Algorithm, Frontend/Viz, DevOps/Report). All delivered reports. | handover.md | analysis complete | ~500 |
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
| 01:55 | Edited TODO.md | inline fix | ~7 |
| 01:55 | Edited TODO.md | inline fix | ~7 |
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
