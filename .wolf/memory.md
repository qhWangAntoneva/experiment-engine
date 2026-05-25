# Memory

| 2026-05-25 | Designed BERT Prototype similarity algorithm spec: mean pooling > CLS, centroid aggregation > max-similarity, softmax-with-temperature formula as primary (Eq.1), normalized-difference as fallback (Eq.3), full pipeline pseudocode, edge cases, Prototype Theory + fsQCA theoretical justification | .wolf/bert-prototype-algorithm-spec.md | Written, ~27KB, no implementation code | ~12000 |
| 2026-05-25 | Implemented CosineSimilarityEngine + 52 comprehensive unit tests: softmax(tau)/diff scoring, centroid/max aggregation, weighted prototypes, 8 edge cases, numerical stability (overflow-safe softmax, cos clipping, L2 normalization), input validation. 577 total tests pass (52 new), ruff clean | src/experiment_engine/text_calibration/cosine_similarity.py, tests/test_cosine_similarity.py, src/experiment_engine/text_calibration/__init__.py | Created: engine ~4.8k tok, tests ~12k tok; updated __init__.py exports | ~7000 |

> Chronological action log. Hooks and AI append to this file automatically.

| 2026-05-25 | P1-31: Verified build + committed raw-prototype contrast view (pre-existing implementation). TODO.md stats updated. | qca.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts, Results.tsx, Results.css, PipelineStatus.tsx, TODO.md | npm build clean, 0 errors | ~800 |
| 2026-05-24 | Reconciled TODO/FIXME/HACK after 3-agent requirement change review: fixed P1-15/16/17 done status, unchecked P2-20 (k=10 still hardcoded), reordered P2 section, corrected all stats tables | TODO.md, FIXME.md, HACK.md | 3 stats tables corrected, 4 checkbox fixes, 2 contradictions resolved, 1 section reordered | ~600 |
| 2026-05-25 | BERT 架构决策定案：Explore Agent 深度复审 bert-vs-keyword-analysis.md + 技术顾问设计浏览器端双 Worker 架构 + 评审者 16 项批判 + 定量对比（86x WASM CPU 推理差距、5.9x 冷启动差距）+ 最终决议 BERT 作为 CLI 辅助工具不做主引擎 | .wolf/bert-vs-keyword-analysis.md, TODO.md, HACK.md, cerebrum.md | 文档已更新，P1-32/33 范围缩小为纯 Python CLI，P2-25/26 添加条件门控 | ~35000 |
> Old sessions are consolidated by the daemon weekly.

| 16:39 | Batch 1: CONTRIBUTING.md + CHANGELOG.md + MkDocs文档站（含16个API页面） | D1, D2, D4 | DONE — 3 parallel workers, reviewer passed | ~5000 tok |
| 16:59 | Batch 2: pyproject发布配置 + SQLite数据库连接器 + 并行stage执行 | D5, A3, A6 | DONE — 3 parallel workers, 321 passed, 6 xfailed | ~5000 tok |
| 17:15 | Batch 3: 内置算法(线性回归+KMeans) + Streamlit Dashboard增强 + LaTeX报告导出 | A1, A2, A4 | DONE — 3 parallel workers, 352 passed, 6 xfailed | ~5000 tok |

## Session: 2026-05-24 09:38

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 10:25 | Created ../.claude/plans/synthetic-orbiting-kurzweil.md | — | ~1585 |
| 10:26 | Edited src/experiment_engine/models.py | added 1 import(s) | ~113 |
| 10:27 | Edited src/experiment_engine/models.py | modified __init__() | ~4965 |
| 10:28 | Edited pyproject.toml | 2→1 lines | ~6 |
| 10:30 | Created src/experiment_engine/text_calibration/__init__.py | — | ~256 |
| 10:30 | Created src/experiment_engine/text_calibration/domains.py | — | ~2655 |
| 10:30 | Created src/experiment_engine/text_calibration/keyword_dict.py | — | ~1774 |
| 10:31 | Created src/experiment_engine/text_calibration/condition.py | — | ~1863 |
| 10:31 | Created src/experiment_engine/text_calibration/calibrator.py | — | ~2666 |
| 10:32 | Created src/experiment_engine/text_calibration/training.py | — | ~2252 |
| 10:34 | Created src/experiment_engine/qca_engine/consistency.py | — | ~1366 |
| 10:34 | Created src/experiment_engine/qca_engine/truth_table.py | — | ~1373 |
| 10:34 | Created src/experiment_engine/qca_engine/minimization.py | — | ~2384 |
| 10:34 | Created src/experiment_engine/qca_engine/necessity.py | — | ~1107 |
| 10:34 | Created src/experiment_engine/qca_engine/sufficiency.py | — | ~1375 |
| 10:34 | Created src/experiment_engine/qca_engine/solution.py | — | ~1338 |
| 10:34 | Created src/experiment_engine/qca_engine/analyzer.py | — | ~1639 |
| 10:34 | Created src/experiment_engine/qca_engine/__init__.py | — | ~218 |
| 10:36 | Created src/experiment_engine/qca_engine/advanced/__init__.py | — | ~125 |
| 10:36 | Created src/experiment_engine/qca_engine/advanced/robustness.py | — | ~2091 |
| 10:36 | Created src/experiment_engine/qca_engine/advanced/counterfactual.py | — | ~1864 |
| 10:36 | Created src/experiment_engine/qca_engine/advanced/multi_outcome.py | — | ~799 |
| 10:36 | Created src/experiment_engine/viz/qca_plots.py | — | ~1324 |
| 10:36 | Created src/experiment_engine/report/qca_reporter.py | — | ~2098 |
| 10:37 | Edited src/experiment_engine/io/readers.py | modified name() | ~1222 |
| 10:37 | Edited src/experiment_engine/io/__init__.py | 7→8 lines | ~44 |
| 10:37 | Edited src/experiment_engine/io/__init__.py | 6→7 lines | ~46 |
| 10:39 | Created src/experiment_engine/cli.py | — | ~6588 |
| 10:39 | Created src/experiment_engine/__init__.py | — | ~368 |
| 10:40 | Edited pyproject.toml | removed 10 lines | ~14 |
| 10:40 | Edited pyproject.toml | "A modular algorithm exper" → "QCA Text Analysis Tool: c" | ~24 |
| 10:41 | Edited pyproject.toml | "0.1.0" → "0.2.0" | ~5 |
| 10:41 | Edited pyproject.toml | "experiment" → "qca" | ~28 |
| 10:41 | Edited src/experiment_engine/cli.py | 2→2 lines | ~38 |
| 10:42 | Created src/experiment_engine/algorithms/__init__.py | — | ~21 |
| 10:43 | Edited src/experiment_engine/cli.py | inline fix | ~3 |
| 10:44 | Edited src/experiment_engine/cli.py | modified _print_fit_metrics() | ~153 |
| 10:46 | Edited pyproject.toml | 15→16 lines | ~160 |
| 10:48 | Edited src/experiment_engine/cli.py | added 1 import(s) | ~43 |
| 10:48 | Edited src/experiment_engine/report/qca_reporter.py | modified _title_page() | ~179 |
| 10:49 | Edited pyproject.toml | expanded (+12 lines) | ~218 |
| 10:49 | Edited pyproject.toml | 1→4 lines | ~59 |
| 10:50 | Session end: 42 writes across 23 files (synthetic-orbiting-kurzweil.md, models.py, pyproject.toml, __init__.py, domains.py) | 40 reads | ~47545 tok |
| 10:55 | Memo: 全面更新 cerebrum.md (10节：身份/领域/架构/模块/设计决策/依赖/测试/偏好/Do-Not-Repeat/决策) + anatomy.md (补全框架+QCA模块) | cerebrum.md, anatomy.md | DONE | ~5000 |
| 10:56 | Session end: 42 writes across 23 files (synthetic-orbiting-kurzweil.md, models.py, pyproject.toml, __init__.py, domains.py) | 40 reads | ~47545 tok |
| 11:00 | Session end: 42 writes across 23 files (synthetic-orbiting-kurzweil.md, models.py, pyproject.toml, __init__.py, domains.py) | 40 reads | ~47545 tok |

## Session: 2026-05-24 11:10

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 11:25 | Edited pyproject.toml | 1→5 lines | ~106 |
| 11:25 | Edited pyproject.toml | 1→2 lines | ~46 |
| 11:25 | Edited pyproject.toml | inline fix | ~22 |
| 11:25 | Edited pyproject.toml | inline fix | ~31 |
| 11:26 | Edited pyproject.toml | inline fix | ~29 |
| 11:27 | Edited pyproject.toml | inline fix | ~20 |
| 11:27 | Edited pyproject.toml | inline fix | ~28 |
| 11:27 | Edited pyproject.toml | inline fix | ~26 |
| 11:27 | Edited tests/test_algorithms.py | "Expected np.ndarray" → "Expected np\.ndarray" | ~20 |
| 11:27 | Edited tests/test_integration.py | inline fix | ~20 |
| 11:27 | Edited tests/test_viz.py | inline fix | ~14 |
| 11:27 | Edited tests/test_viz.py | inline fix | ~7 |
| 11:28 | Edited pyproject.toml | inline fix | ~21 |
| 11:29 | Edited tests/test_integration.py | inline fix | ~9 |
| 11:29 | Edited pyproject.toml | inline fix | ~15 |
| 11:29 | Edited src/experiment_engine/io/readers.py | inline fix | ~9 |
| 11:29 | Edited src/experiment_engine/io/readers.py | inline fix | ~13 |
| 11:30 | Session end: 17 writes across 5 files (pyproject.toml, test_algorithms.py, test_integration.py, test_viz.py, readers.py) | 4 reads | ~17950 tok |
| 11:35 | Session end: 17 writes across 5 files (pyproject.toml, test_algorithms.py, test_integration.py, test_viz.py, readers.py) | 4 reads | ~17950 tok |
| 11:38 | Edited .pre-commit-config.yaml | inline fix | ~5 |
| 11:38 | Edited .pre-commit-config.yaml | 4.0 → 15.12 | ~5 |
| 11:40 | Edited pyproject.toml | inline fix | ~12 |
| 11:40 | Edited pyproject.toml | 1→2 lines | ~46 |
| 11:43 | Session end: 21 writes across 6 files (pyproject.toml, test_algorithms.py, test_integration.py, test_viz.py, readers.py) | 5 reads | ~18023 tok |
| 11:48 | Session end: 21 writes across 6 files (pyproject.toml, test_algorithms.py, test_integration.py, test_viz.py, readers.py) | 5 reads | ~18023 tok |
| 13:01 | Session end: 21 writes across 6 files (pyproject.toml, test_algorithms.py, test_integration.py, test_viz.py, readers.py) | 10 reads | ~18645 tok |
| 13:03 | Created src/types/qca.ts | — | ~2623 |
| 13:04 | Created src/services/pyodide.worker.ts | — | ~5041 |
| 13:04 | Created src/services/pyodide.ts | — | ~3177 |
| 13:05 | Created src/store/QCAPipelineContext.tsx | — | ~2204 |
| 13:05 | Session end: 25 writes across 10 files (pyproject.toml, test_algorithms.py, test_integration.py, test_viz.py, readers.py) | 36 reads | ~67185 tok |
| 13:06 | Created src/hooks/usePyodide.ts | — | ~452 |
| 13:06 | Created src/hooks/useQCAWorkflow.ts | — | ~1736 |
| 13:06 | Created src/components/TruthTableViewer.tsx | — | ~1483 |
| 13:06 | Created src/components/SolutionViewer.tsx | — | ~1202 |
| 13:06 | Created .github/workflows/deploy.yml | — | ~1906 |
| 13:06 | Created vite.config.ts | — | ~500 |
| 13:06 | Created src/main.tsx | — | ~331 |
| 13:06 | Created src/pyodide/engine.ts | — | ~3692 |
| 13:06 | Created src/pyodide/types.ts | — | ~717 |
| 13:06 | Edited package.json | 5→6 lines | ~39 |
| 13:07 | Created src/components/FuzzySetHeatmap.tsx | — | ~1294 |
| 13:07 | Created src/components/NecessityXYPlot.tsx | — | ~1034 |
| 13:07 | Created src/components/DistributionPlot.tsx | — | ~899 |
| 13:07 | Created src/components/PipelineStatus.tsx | — | ~1154 |
| 05:07 | Deployment strategy designed: Option B (gh-pages same-repo). Created .github/workflows/deploy.yml, updated vite.config.ts (base path), updated main.tsx (BrowserRouter basename), created src/pyodide/engine.ts + types.ts, added pyodide 0.26.4 dep. Pyodide CDN strategy. | deploy.yml, vite.config.ts, main.tsx, engine.ts, types.ts, package.json | complete | ~6000 |
| 13:09 | Created src/vite-env.d.ts | — | ~173 |
| 13:09 | Created src/pages/Dashboard.tsx | — | ~2824 |
| 13:09 | Created src/pages/DataInput.tsx | — | ~5169 |
| 13:10 | Created src/pages/Results.tsx | — | ~3472 |
| 13:10 | Created src/pages/Settings.tsx | — | ~3563 |
| 13:11 | Created src/App.tsx | — | ~240 |
| 13:11 | Created src/types/index.ts | — | ~400 |
| 13:11 | Created src/components/Sidebar.tsx | — | ~392 |
| 13:11 | Created vite.config.ts | — | ~334 |
| 13:11 | Created package.json | — | ~160 |
| 13:12 | Session end: 49 writes across 32 files (pyproject.toml, test_algorithms.py, test_integration.py, test_viz.py, readers.py) | 36 reads | ~100806 tok |
| 05:13 | Designed Pyodide+React web architecture: wrote qca.ts (60+ TS interfaces mirroring Python models), pyodide.worker.ts (Web Worker entry), pyodide.ts (main-thread bridge), QCAPipelineContext.tsx (Context+reducer), usePyodide.ts, useQCAWorkflow.ts, 6 viz components (Plotly heatmap, XY plot, histogram, truth table, solutions, pipeline status), rewrote 4 pages (Dashboard/DataInput/Results/Settings), updated App.tsx (provider wrap), package.json (new deps), vite.config.ts (worker) | qca.ts, pyodide.ts, pyodide.worker.ts, QCAPipelineContext.tsx, hooks, components, pages | Completed: full frontend architecture integration code | ~8000 |
| 13:15 | Edited roadmap/experiment-engine-roadmap.json | expanded (+118 lines) | ~2198 |
| 13:15 | Edited roadmap/experiment-engine-roadmap.json | 13→17 lines | ~225 |
| 13:16 | Edited roadmap/experiment-engine-roadmap.json | 3→3 lines | ~114 |
| 13:22 | Session end: 52 writes across 33 files (pyproject.toml, test_algorithms.py, test_integration.py, test_viz.py, readers.py) | 36 reads | ~103343 tok |

## HANDOFF: 2026-05-24 Session Wrap

### Commits pushed (3)
1. `dd6dcc2` — Phase 3: QCA text analysis refactoring (66 files, +12074/-247)
2. `f0545d0` — Upgrade pre-commit hooks: ruff v0.4.0→v0.15.12 + pre-commit-hooks v4.6.0→v5.0.0
3. `a1d6ea7` — Phase 6: Pyodide web deployment — frontend architecture + roadmap (34 files, +6236/-446)

### Current state
- **Working tree**: clean (only .wolf tracking files modified)
- **Branch**: master, synced with origin
- **Tests**: not run this session (352 baseline from prior session)
- **Active phase**: Phase 6 — Web Deployment (prototype 7/12 tasks, 5 pending)

### Key Deliverables this session
- Full QCA engine committed (qca_engine/, text_calibration/, report/)
- Pre-commit tooling upgraded and aligned (ruff v0.15.12, all hooks pass)
- Pyodide Web Worker bridge with 9 request types
- React state machine (QCAPipelineContext, 14 stages)
- 6 Plotly.js visualization components (heatmap, XY plot, histogram, truth table, solution viewer, pipeline status)
- All 4 pages rewritten for QCA workflow
- 60+ TypeScript interfaces mirroring Python Pydantic models
- GitHub Actions CI/CD for gh-pages deployment
- Vite config with GH Pages base path + worker + chunk splitting

### Critical blocker for next session
**W1 — pydantic v2 → dataclass shim layer (est. 8h)**
- pydantic-core is Rust binary, cannot run in Pyodide/Wasm
- 30+ Pydantic models in models.py need dataclass equivalents
- Plan: `models_browser.py` with dataclass + `IN_BROWSER` gate in `__init__.py`
- This is the single biggest remaining task before the web demo works end-to-end

### Do-Not-Repeat (new this session)
- ruff pre-commit version must match uv.lock version; per-file-ignore rules must exist in that version
- PD901 rule removed in ruff 0.15.x — remove from global ignore on upgrade
- Windows Python open() defaults to GBK — always use encoding='utf-8' (also affects buglog.json reads)
- pytest.raises match= patterns should use raw strings to avoid RUF043

### Files to read first next session
- `.wolf/cerebrum.md` — project overview, Do-Not-Repeat, decision log
- `roadmap/experiment-engine-roadmap.json` — Phase 6 tasks and risk register
- `src/experiment_engine/models.py` — Pydantic models to port (W1 blocker)
- `src/services/pyodide.worker.ts` — Web Worker bridge (needs Python side wired up)
| 13:37 | Session end: 52 writes across 33 files (pyproject.toml, test_algorithms.py, test_integration.py, test_viz.py, readers.py) | 36 reads | ~103343 tok |

## Session: 2026-05-24 13:38

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 13:47 | Edited src/vite-env.d.ts | 9→14 lines | ~230 |
| 13:47 | Edited src/components/PipelineStatus.tsx | 5→2 lines | ~23 |
| 13:47 | Edited src/store/QCAPipelineContext.tsx | inline fix | ~17 |
| 13:51 | Fixed CI deploy failures: package-lock sync + 3 TS errors | package-lock.json, src/vite-env.d.ts, PipelineStatus.tsx, QCAPipelineContext.tsx | CI passing, 2 commits pushed | ~800 |
| 13:51 | Session end: 3 writes across 3 files (vite-env.d.ts, PipelineStatus.tsx, QCAPipelineContext.tsx) | 5 reads | ~7095 tok |

## Session: 2026-05-24 14:36

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 15:19 | Edited src/types/qca.ts | 14→16 lines | ~89 |
| 15:19 | Edited src/store/QCAPipelineContext.tsx | 2→2 lines | ~27 |
| 15:19 | Edited src/store/QCAPipelineContext.tsx | CSS: stage, message | ~82 |
| 15:19 | Edited src/services/pyodide.worker.ts | modified mountFromInline() | ~360 |
| 15:19 | Edited src/services/pyodide.worker.ts | added error handling | ~122 |
| 15:20 | Edited src/services/pyodide.worker.ts | 49→54 lines | ~566 |
| 15:20 | Edited src/services/pyodide.worker.ts | 32→37 lines | ~360 |
| 15:20 | Edited src/services/pyodide.worker.ts | 26→31 lines | ~313 |
| 15:20 | Edited src/services/pyodide.worker.ts | 26→31 lines | ~320 |
| 15:20 | Edited src/services/pyodide.worker.ts | 10→13 lines | ~119 |
| 15:20 | Edited src/services/pyodide.worker.ts | 8→11 lines | ~120 |
| 20:00 | Fixed bug-014: code injection in pyodide.worker.ts — replaced 6 template literal JSON injections with VFS file writing | src/services/pyodide.worker.ts | build passes | ~800 |
| 20:00 | Fixed bug-015: mountFromInline() missing __init__.py — added package init files so Python imports work | src/services/pyodide.worker.ts | build passes | ~200 |
| 20:00 | Fixed bug-010: stage typo in startCounterfactuals ('running-robustness' → 'running-counterfactuals') | src/store/QCAPipelineContext.tsx | build passes | ~100 |
| 20:00 | Fixed bug-011: finishCounterfactuals missing stage transition — added SET_STAGE dispatch | src/store/QCAPipelineContext.tsx | build passes | ~80 |
| 20:00 | Fixed handleLoadCorpus from empty stub to pass-through with try/catch | src/services/pyodide.worker.ts | build passes | ~80 |
| 20:00 | Added 'running-counterfactuals' and 'counterfactuals-done' to PipelineStage type | src/types/qca.ts | build passes | ~50 |
| 15:29 | anatomy.md restored after debugger stripped it (94 files) | .wolf/anatomy.md | DONE | ~200 tok |
| 15:30 | Session end: 11 writes across 3 files (qca.ts, QCAPipelineContext.tsx, pyodide.worker.ts) | 32 reads | ~12897 tok |
| 15:43 | localhost tester full test: 5/5 PASS (routes 200, sources verified, build clean, dev server OK) | pyodide.worker.ts, QCAPipelineContext.tsx, qca.ts | PASS | ~500 tok |
| 15:43 | Session end: 11 writes across 3 files (qca.ts, QCAPipelineContext.tsx, pyodide.worker.ts) | 33 reads | ~13128 tok |

## Session: 2026-05-24 15:44

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 16:42 | Created ../.claude/plans/velvety-humming-raccoon.md | — | ~1614 |
| 16:43 | Edited src/experiment_engine/models.py | modified CalibrationType() | ~162 |
| 16:44 | Edited src/experiment_engine/models.py | modified ConceptPrototype() | ~468 |
| 16:44 | Edited src/experiment_engine/models.py | modified n_samples() | ~176 |
| 16:44 | Edited src/experiment_engine/models.py | modified ConditionSet() | ~208 |
| 16:44 | Edited src/experiment_engine/__init__.py | expanded (+7 lines) | ~135 |
| 16:44 | Edited src/experiment_engine/__init__.py | expanded (+7 lines) | ~184 |
| 16:45 | Created src/experiment_engine/text_calibration/prototype_similarity.py | — | ~1137 |
| 16:45 | Edited src/experiment_engine/text_calibration/calibrator.py | expanded (+7 lines) | ~137 |
| 16:46 | Edited src/experiment_engine/text_calibration/calibrator.py | modified setup() | ~2330 |
| 16:46 | Edited src/experiment_engine/models.py | 2→4 lines | ~72 |
| 16:46 | Edited src/experiment_engine/text_calibration/calibrator.py | modified _apply_calibration() | ~91 |
| 16:46 | Edited src/experiment_engine/text_calibration/condition.py | 7→9 lines | ~53 |
| 16:46 | Edited src/experiment_engine/text_calibration/condition.py | modified __init__() | ~186 |
| 16:47 | Edited src/experiment_engine/text_calibration/condition.py | modified add_keyword() | ~261 |
| 16:47 | Edited src/experiment_engine/text_calibration/condition.py | modified build() | ~211 |
| 16:47 | Edited src/experiment_engine/text_calibration/condition.py | modified _condition_set_to_dict() | ~105 |
| 16:47 | Edited src/experiment_engine/text_calibration/condition.py | modified _condition_to_dict() | ~347 |
| 16:47 | Edited src/experiment_engine/text_calibration/condition.py | modified _condition_set_from_dict() | ~171 |
| 16:47 | Edited src/experiment_engine/text_calibration/condition.py | modified _condition_from_dict() | ~355 |
| 16:48 | Edited src/types/qca.ts | 1→2 lines | ~43 |
| 16:48 | Edited src/types/qca.ts | 3→5 lines | ~30 |
| 16:48 | Edited src/types/qca.ts | expanded (+10 lines) | ~136 |
| 16:48 | Edited src/types/qca.ts | expanded (+7 lines) | ~82 |
| 16:48 | Edited src/types/qca.ts | 2→3 lines | ~72 |
| 16:48 | Edited src/types/qca.ts | 2→4 lines | ~67 |
| 16:49 | Edited src/services/pyodide.worker.ts | 3→6 lines | ~71 |
| 16:49 | Edited src/services/pyodide.worker.ts | added error handling | ~574 |
| 16:49 | Edited src/services/pyodide.ts | 14→15 lines | ~93 |
| 16:50 | Edited src/services/pyodide.ts | modified calibrate() | ~234 |
| 16:52 | Edited src/experiment_engine/text_calibration/__init__.py | 14→18 lines | ~141 |
| 16:53 | Edited src/store/QCAPipelineContext.tsx | CSS: startPrototypeCalibration, finishPrototypeCalibration | ~206 |
| 16:53 | Edited src/store/QCAPipelineContext.tsx | expanded (+10 lines) | ~216 |
| 16:53 | Edited src/store/QCAPipelineContext.tsx | 2→4 lines | ~30 |
| 16:53 | Edited src/hooks/useQCAWorkflow.ts | 6→7 lines | ~45 |
| 16:53 | Edited src/hooks/useQCAWorkflow.ts | expanded (+15 lines) | ~210 |
| 16:53 | Created tests/test_prototype_similarity.py | — | ~4412 |
| 16:54 | Edited src/hooks/useQCAWorkflow.ts | 3→5 lines | ~36 |
| 16:54 | Edited src/hooks/useQCAWorkflow.ts | added error handling | ~768 |
| 16:54 | Edited src/hooks/useQCAWorkflow.ts | 8→10 lines | ~48 |
| 16:54 | Edited src/pages/DataInput.tsx | expanded (+9 lines) | ~51 |
| 16:55 | Edited src/pages/DataInput.tsx | added 2 condition(s) | ~966 |
| 16:58 | Created src/pages/DataInput.tsx | — | ~11486 |
| 16:59 | Edited src/experiment_engine/text_calibration/calibrator.py | modified _compute_raw_scores() | ~163 |
| 12:30 | Added prototype calibration support: Context mutations (startPrototypeCalibration/finishPrototypeCalibration), Workflow hook methods (runPrototypeCalibration/runPrototypeFullPipeline), DataInput page mode selector + prototype editor table | src/store/QCAPipelineContext.tsx, src/hooks/useQCAWorkflow.ts, src/pages/DataInput.tsx | tsc -b + vite build pass, no errors | ~6500 |
| 17:02 | Session end: 44 writes across 13 files (velvety-humming-raccoon.md, models.py, __init__.py, prototype_similarity.py, calibrator.py) | 21 reads | ~103034 tok |
| 17:08 | Prototype calibration feature: Python models + similarity engine + TS types + worker bridge + frontend UI. 171 tests pass, tsc clean | 10 files modified, 2 new | success | ~15000 tok |
| 17:16 | Session end: 44 writes across 13 files (velvety-humming-raccoon.md, models.py, __init__.py, prototype_similarity.py, calibrator.py) | 21 reads | ~103034 tok |
| 17:32 | Edited .gitignore | 3→6 lines | ~33 |
| 17:41 | Session end: 45 writes across 14 files (velvety-humming-raccoon.md, models.py, __init__.py, prototype_similarity.py, calibrator.py) | 25 reads | ~114650 tok |
| 17:49 | Session end: 45 writes across 14 files (velvety-humming-raccoon.md, models.py, __init__.py, prototype_similarity.py, calibrator.py) | 26 reads | ~115864 tok |
| 17:53 | Commit 5753501: prototype calibration feature. 21 files, +5747/-395. Pre-commit lint issues (RUF001/SLF001/B017) logged as KI-001~003 in roadmap | pushed to master | success | ~800 tok |
| 17:53 | Session end: 45 writes across 14 files (velvety-humming-raccoon.md, models.py, __init__.py, prototype_similarity.py, calibrator.py) | 27 reads | ~120908 tok |

## Session: 2026-05-24 17:54

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 17:59 | Edited src/experiment_engine/io/readers.py | modified _get_pandas() | ~111 |
| 17:59 | Edited src/experiment_engine/io/readers.py | 7→8 lines | ~57 |
| 17:59 | Edited src/experiment_engine/io/readers.py | 1→2 lines | ~17 |
| 17:59 | Edited src/experiment_engine/io/readers.py | 2→3 lines | ~40 |
| 17:59 | Edited pyproject.toml | 1→2 lines | ~59 |
| 18:00 | Edited roadmap/experiment-engine-roadmap.json | 4→4 lines | ~41 |
| 18:01 | Edited roadmap/experiment-engine-roadmap.json | 7→7 lines | ~116 |
| 18:01 | Edited roadmap/experiment-engine-roadmap.json | 3→4 lines | ~4 |
| 18:03 | Edited pyproject.toml | 2→3 lines | ~16 |
| 18:05 | Edited tests/test_integration.py | modified _make_valid_condition_set() | ~948 |
| 18:06 | Edited tests/test_integration.py | _make_valid_yaml_config() → _make_valid_condition_set() | ~108 |
| 18:06 | Edited tests/test_integration.py | _make_valid_yaml_config() → _make_valid_condition_set() | ~133 |
| 18:06 | Edited tests/test_integration.py | modified test_list_conditions_empty() | ~217 |
| 18:06 | Edited tests/test_integration.py | modified test_run_command_succeeds() | ~135 |
| 18:07 | Edited tests/test_integration.py | modified test_run_with_verbose_flag() | ~222 |
| 18:09 | Edited src/experiment_engine/cli.py | modified _save_analysis_result() | ~51 |
| 18:10 | Edited src/experiment_engine/qca_engine/advanced/robustness.py | inline fix | ~36 |
| 18:11 | Fixed 6 stale CLI integration tests: updated helpers for text-calibration workflow config, fixed 2 pre-existing CLI bugs (numpy serialization, robustness attr) | tests/test_integration.py, src/experiment_engine/cli.py, src/experiment_engine/qca_engine/advanced/robustness.py | 6 tests + 354 others = 360 passed | ~2500 |
| 18:13 | Edited pyproject.toml | — | ~0 |
| 18:14 | Edited pyproject.toml | inline fix | ~30 |

| %H:%M | Debug session: 7 bugs fixed (KI-001/002/003 + 4 discovered). 360 tests pass, ruff clean, tsc clean. | tests/test_algorithms.py (deleted), src/experiment_engine/io/readers.py, pyproject.toml, cli.py, robustness.py, test_integration.py | 360 pass, 0 fail, 6 xfail | ~35000 tok || 18:17 | Session end: 19 writes across 6 files (readers.py, pyproject.toml, experiment-engine-roadmap.json, test_integration.py, cli.py) | 16 reads | ~51024 tok |
| 18:21 | Session end: 19 writes across 6 files (readers.py, pyproject.toml, experiment-engine-roadmap.json, test_integration.py, cli.py) | 16 reads | ~51024 tok |
| 18:25 | Edited .claude/settings.json | expanded (+10 lines) | ~138 |
| 18:28 | Session end: 20 writes across 7 files (readers.py, pyproject.toml, experiment-engine-roadmap.json, test_integration.py, cli.py) | 17 reads | ~51603 tok |

## Session: 2026-05-24 18:29

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 19:29 | Created TODO.md | — | ~1672 |
| 19:29 | Created FIXME.md | — | ~2127 |
| 19:29 | Created HACK.md | — | ~1280 |
| 19:33 | Edited TODO.md | inline fix | ~64 |
| 19:33 | Edited TODO.md | inline fix | ~52 |
| 19:33 | Edited TODO.md | inline fix | ~48 |
| 19:33 | Edited TODO.md | inline fix | ~44 |
| 19:33 | Edited TODO.md | inline fix | ~48 |
| 19:33 | Edited TODO.md | inline fix | ~42 |
| 19:34 | Edited TODO.md | inline fix | ~43 |
| 19:34 | Edited TODO.md | inline fix | ~57 |
| 19:34 | Edited TODO.md | inline fix | ~47 |
| 19:34 | Edited TODO.md | inline fix | ~31 |
| 19:34 | Edited TODO.md | inline fix | ~37 |
| 19:34 | Edited TODO.md | inline fix | ~33 |
| 19:34 | Edited TODO.md | inline fix | ~35 |
| 19:34 | Edited TODO.md | inline fix | ~34 |
| 19:34 | Edited TODO.md | inline fix | ~37 |
| 19:34 | Edited FIXME.md | 3→3 lines | ~34 |
| 19:34 | Edited FIXME.md | 2→2 lines | ~8 |
| 19:35 | Edited FIXME.md | 4→4 lines | ~69 |
| 19:35 | Edited HACK.md | 2→2 lines | ~18 |
| 19:35 | Edited HACK.md | 2→2 lines | ~19 |
| 19:35 | Edited HACK.md | 2→2 lines | ~18 |
| 19:35 | 三方审查完成：生成 TODO.md(51项)/FIXME.md(22项)/HACK.md(12项)，评审者验收通过 | TODO.md, FIXME.md, HACK.md | 交叉引用已添加，FIXME-15 升级为🔴 | ~12k tok |
| 19:35 | Session end: 24 writes across 3 files (TODO.md, FIXME.md, HACK.md) | 43 reads | ~132757 tok |
| 19:43 | 交接文档更新：cerebrum.md 添加快速上手指南+7条Do-Not-Repeat+决策日志，buglog.json 新增5个严重Bug(bug-34~38) | cerebrum.md, buglog.json, anatomy.md | 下一session按P0优先级修复 | ~2k tok |
| 19:43 | Session end: 24 writes across 3 files (TODO.md, FIXME.md, HACK.md) | 43 reads | ~132757 tok |

## Session: 2026-05-24 19:44

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 19:51 | Edited src/experiment_engine/qca_engine/advanced/counterfactual.py | modified produce_parsimonious_solution() | ~350 |
| 19:51 | Edited src/experiment_engine/qca_engine/advanced/counterfactual.py | modified produce_intermediate_solution() | ~405 |
| 19:51 | Edited src/experiment_engine/qca_engine/minimization.py | modified minimize() | ~480 |
| 19:51 | Edited src/experiment_engine/qca_engine/minimization.py | modified enumerate() | ~296 |
| 19:55 | Fix FIXME-1, FIXME-17, FIXME-18, HACK-5 — parsimonious solution algorithm + QM don't-care support | counterfactual.py, minimization.py | 360 tests pass | ~1200 tok |
| 19:56 | Session end: 4 writes across 2 files (counterfactual.py, minimization.py) | 8 reads | ~38566 tok |
| 19:56 | Created src/experiment_engine/text_calibration/calibrator.py | — | ~5564 |
| 19:57 | Edited src/experiment_engine/text_calibration/calibrator.py | inline fix | ~13 |
| 19:57 | Edited src/experiment_engine/text_calibration/calibrator.py | 4→1 lines | ~23 |
| 19:59 | Fixed FIXME-2 (col index offset via col_to_kw mapping), FIXME-3 (calibrate_ragin logistic rewrite), FIXME-4 (match_corpus caching in _precompute_kw_context), FIXME-20 (dedup via _process_core). All 360 tests pass. | calibrator.py, buglog.json, cerebrum.md, anatomy.md | All 3 bugs fixed, ruff clean, 360/360 tests pass | ~2500 |
| 20:01 | Session end: 7 writes across 3 files (counterfactual.py, minimization.py, calibrator.py) | 8 reads | ~47719 tok |
| 20:09 | Session end: 7 writes across 3 files (counterfactual.py, minimization.py, calibrator.py) | 8 reads | ~47719 tok |
| 20:11 | Edited src/experiment_engine/models.py | expanded (+8 lines) | ~131 |
| 20:11 | Edited src/experiment_engine/models.py | 5→8 lines | ~73 |
| 20:11 | Edited src/experiment_engine/qca_engine/advanced/counterfactual.py | modified zip() | ~294 |
| 20:11 | Edited src/experiment_engine/qca_engine/sufficiency.py | modified startswith() | ~269 |
| 20:11 | Edited src/experiment_engine/models.py | modified failed_stages() | ~104 |
| 20:11 | Edited src/experiment_engine/pipeline.py | modified __init__() | ~119 |
| 20:11 | Edited src/experiment_engine/pipeline.py | 10→12 lines | ~124 |
| 20:12 | Edited src/experiment_engine/qca_engine/advanced/counterfactual.py | inline fix | ~26 |
| 20:12 | Edited src/experiment_engine/qca_engine/sufficiency.py | added 1 import(s) | ~21 |
| 20:12 | Edited src/experiment_engine/qca_engine/sufficiency.py | print() → warn() | ~90 |
| 20:12 | Edited src/experiment_engine/qca_engine/sufficiency.py | print() → warn() | ~88 |
| 20:12 | Edited src/experiment_engine/pipeline.py | expanded (+11 lines) | ~924 |
| 20:12 | Edited src/experiment_engine/pipeline.py | 6→7 lines | ~91 |
| 20:12 | Edited src/experiment_engine/core/parallel.py | modified __init__() | ~105 |
| 20:12 | Edited src/experiment_engine/core/parallel.py | 4→5 lines | ~52 |
| 20:12 | Edited src/experiment_engine/core/parallel.py | 12→13 lines | ~184 |
| 20:13 | Edited src/experiment_engine/core/parallel.py | expanded (+9 lines) | ~620 |
| 20:13 | Edited src/experiment_engine/core/parallel.py | expanded (+8 lines) | ~206 |
| 20:14 | Edited src/experiment_engine/core/parallel.py | 5→8 lines | ~81 |
| 20:20 | Fixed FIXME-9: theoretical_expectation now populated from directional_expectations in counterfactual.py analyze() | counterfactual.py (+5 lines) | theo_exp no longer None, build "+name"/"-name" string | ~150 |
| 20:20 | Fixed FIXME-13: added warnings.warn() for condition name mismatches in sufficiency.py _compute_term_membership | sufficiency.py (+10 lines, import warnings) | silent pass replaced with UserWarning | ~120 |
| 20:17 | Edited FIXME.md | 7→7 lines | ~120 |
| 20:17 | Edited FIXME.md | 7→7 lines | ~99 |
| 20:17 | Edited FIXME.md | 3→3 lines | ~13 |
| 20:18 | Edited src/experiment_engine/core/parallel.py | 6→7 lines | ~91 |
| 20:18 | Session end: 30 writes across 8 files (counterfactual.py, minimization.py, calibrator.py, models.py, sufficiency.py) | 14 reads | ~62040 tok |
| 20:19 | Edited tests/test_pipeline.py | modified test_stage_failure() | ~700 |
| 20:19 | Edited tests/test_integration.py | modified test_pipeline_stage_failure_continues() | ~159 |
| 20:20 | Edited tests/test_integration.py | 13→13 lines | ~138 |
| 20:21 | FIXME-5/P0-8: added fail_fast to Pipeline/ParallelPipeline, data_quality to StageResult, failed_stages to PipelineResult | pipeline.py, models.py, core/parallel.py, tests | 361/361 tests pass, smoke tests pass | ~1200 tok |
| 20:24 | Session end: 33 writes across 10 files (counterfactual.py, minimization.py, calibrator.py, models.py, sufficiency.py) | 14 reads | ~63349 tok |
| 20:30 | Session end: 33 writes across 10 files (counterfactual.py, minimization.py, calibrator.py, models.py, sufficiency.py) | 14 reads | ~63561 tok |
| 20:34 | Created src/experiment_engine/qca_engine/advanced/robustness.py | — | ~4428 |
| 20:34 | Edited src/experiment_engine/qca_engine/minimization.py | added 1 import(s) | ~21 |
| 20:34 | Edited src/experiment_engine/qca_engine/minimization.py | expanded (+13 lines) | ~190 |
| 20:34 | Edited src/experiment_engine/qca_engine/minimization.py | modified enumerate() | ~94 |
| 20:34 | Edited src/experiment_engine/qca_engine/minimization.py | modified get() | ~242 |
| 20:34 | Edited src/experiment_engine/qca_engine/minimization.py | added 1 condition(s) | ~130 |
| 20:34 | Edited src/experiment_engine/qca_engine/minimization.py | 5→5 lines | ~71 |
| 20:34 | Edited src/experiment_engine/qca_engine/advanced/robustness.py | 2→1 lines | ~20 |
| 20:34 | Edited src/experiment_engine/qca_engine/minimization.py | 3→4 lines | ~84 |
| 20:34 | Edited src/experiment_engine/qca_engine/advanced/robustness.py | 15→14 lines | ~153 |
| 20:35 | Edited src/experiment_engine/qca_engine/minimization.py | inline fix | ~26 |
| 20:35 | Edited src/experiment_engine/qca_engine/advanced/robustness.py | modified _compute_term_membership() | ~250 |
| 20:35 | Edited src/experiment_engine/report/qca_reporter.py | modified _escape_latex() | ~348 |
| 20:35 | Edited src/experiment_engine/report/qca_reporter.py | "Outcome: {result.fuzzy_da" → "Outcome: {self._escape_la" | ~32 |
| 20:35 | Edited src/experiment_engine/report/qca_reporter.py | "Outcome: {self._escape_la" → "Outcome: {QCALaTeXReporte" | ~36 |
| 20:35 | Edited src/experiment_engine/report/qca_reporter.py | 3→3 lines | ~53 |
| 20:35 | Edited src/experiment_engine/report/qca_reporter.py | 3→5 lines | ~90 |
| 20:35 | Edited src/experiment_engine/report/qca_reporter.py | 3→3 lines | ~48 |
| 20:36 | Edited src/experiment_engine/report/qca_reporter.py | 3→3 lines | ~58 |
| 20:36 | Edited src/experiment_engine/report/qca_reporter.py | modified _robustness_section() | ~195 |
| 20:36 | Edited src/experiment_engine/report/qca_reporter.py | inline fix | ~14 |
| 20:37 | Edited src/experiment_engine/report/qca_reporter.py | 4→5 lines | ~42 |
| 12:46 | Fixed FIXME-6,7,8,12 in robustness.py: real coverage_stability via _compute_solution_coverage, renamed test_calibration_sensitivity→test_membership_perturbation (outcome excluded), added test_bootstrap with case resampling, adaptive frequency thresholds for small N | src/experiment_engine/qca_engine/advanced/robustness.py | all 361 tests pass, ruff clean, integration test verified | ~2770 |
| 20:40 | Session end: 55 writes across 12 files (counterfactual.py, minimization.py, calibrator.py, models.py, sufficiency.py) | 20 reads | ~80821 tok |
| 20:41 | Created tmp/test_escaping.py | — | ~622 |
| 20:42 | Edited tmp/test_escaping.py | 3→2 lines | ~36 |
| 20:44 | Fixed P0-1 QM k<=12 guard, FIXME-10 LaTeX escaping, FIXME-11 empty solution_stability guard, FIXME-21 hash→ID identity | minimization.py, qca_reporter.py | All 361 tests pass, ruff clean, functional tests pass | ~1800t |
| 20:47 | Session end: 57 writes across 13 files (counterfactual.py, minimization.py, calibrator.py, models.py, sufficiency.py) | 20 reads | ~81479 tok |
| 20:52 | Session end: 57 writes across 13 files (counterfactual.py, minimization.py, calibrator.py, models.py, sufficiency.py) | 20 reads | ~84053 tok |
| 20:57 | Created tests/test_qca_core.py | — | ~14948 |
| 20:58 | Created src/experiment_engine/pyodide_handlers.py | — | ~3528 |
| 20:58 | Edited src/experiment_engine/pyodide_handlers.py | 2→2 lines | ~44 |
| 20:58 | Edited tests/test_qca_core.py | assert_array_equal() → assert_array_almost_equal() | ~93 |
| 20:59 | Edited tests/test_qca_core.py | inline fix | ~19 |
| 20:59 | Edited tests/test_qca_core.py | modified test_apply_calibration_invalid_enum_raises() | ~76 |
| 20:59 | Created src/services/pyodide.worker.ts | — | ~4552 |
| 20:59 | Edited tests/test_qca_core.py | 4→4 lines | ~60 |
| 21:01 | Edited tests/test_qca_core.py | reduced (-8 lines) | ~62 |
| 21:02 | Edited tests/test_qca_core.py | 3→2 lines | ~28 |
| 21:02 | Edited tests/test_qca_core.py | 3→2 lines | ~30 |
| 21:02 | Edited pyproject.toml | 1→2 lines | ~64 |
| 21:03 | Edited src/experiment_engine/pyodide_handlers.py | inline fix | ~26 |
| 21:03 | Edited tests/test_qca_core.py | modified test_necessity_threshold() | ~372 |
| 21:03 | Edited tests/test_qca_core.py | inline fix | ~18 |
| 21:03 | Edited tests/test_qca_core.py | inline fix | ~19 |
| 21:05 | Implemented P0-3: wrote comprehensive unit tests for QCA core modules (104 tests in test_qca_core.py). Covers consistency, truth table, minimization, necessity, sufficiency, calibration, keyword matching. Uses Lipset gold-standard benchmark. Full suite: 465 passed. | tests/test_qca_core.py, pyproject.toml, .wolf/anatomy.md | Pass | ~12000 |
| 21:05 | Session end: 73 writes across 17 files (counterfactual.py, minimization.py, calibrator.py, models.py, sufficiency.py) | 28 reads | ~141273 tok |
| 21:05 | Edited FIXME.md | inline fix | ~20 |
| 21:05 | Edited FIXME.md | 7→7 lines | ~180 |
| 21:06 | Edited FIXME.md | 6 → 5 | ~4 |
| 21:06 | Edited FIXME.md | 20 → 19 | ~6 |
| 21:07 | P0-2/FIXME-15: extracted 7 handler functions from pyodide.worker.ts into pyodide_handlers.py; worker -195 lines (-24%); fixed 2 hidden bugs (bug-059, bug-060); build passes, 464 tests pass, ruff clean | src/experiment_engine/pyodide_handlers.py, src/services/pyodide.worker.ts, FIXME.md, .wolf/buglog.json | success | ~13000 |
| 21:08 | Session end: 77 writes across 17 files (counterfactual.py, minimization.py, calibrator.py, models.py, sufficiency.py) | 28 reads | ~141498 tok |
| 21:13 | Session end: 77 writes across 17 files (counterfactual.py, minimization.py, calibrator.py, models.py, sufficiency.py) | 28 reads | ~129119 tok |
| 21:18 | Created FIXME.md | — | ~1906 |
| 21:19 | Created TODO.md | — | ~1674 |
| 21:19 | Edited HACK.md | 8→7 lines | ~84 |
| 21:19 | Edited HACK.md | 8→7 lines | ~107 |
| 21:19 | Edited HACK.md | 8→7 lines | ~84 |
| 21:19 | Edited HACK.md | 6→6 lines | ~31 |
| 21:23 | Session end: 83 writes across 19 files (counterfactual.py, minimization.py, calibrator.py, models.py, sufficiency.py) | 28 reads | ~133364 tok |

## Session: 2026-05-24 21:25

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 22:03 | Created src/experiment_engine/models/framework.py | — | ~4128 |
| 22:04 | Created src/experiment_engine/models/qca.py | — | ~4964 |
| 22:04 | Created src/experiment_engine/models/training.py | — | ~530 |
| 22:04 | Created src/experiment_engine/models/__init__.py | — | ~657 |
| 22:06 | Edited src/experiment_engine/models/qca.py | 7→7 lines | ~52 |
| 22:06 | Edited src/experiment_engine/models/qca.py | 7→7 lines | ~48 |
| 22:04 | P1-14: Split models.py into models/framework.py + models/qca.py + models/training.py + __init__.py (re-exports for backward compat) | src/experiment_engine/models/* | 465 tests pass, ruff clean, npm build pass | ~10280 tok saved from monolithic file |
| 22:09 | Edited FIXME.md | 7→7 lines | ~126 |
| 22:09 | Edited FIXME.md | 3→3 lines | ~31 |
| 22:09 | Edited FIXME.md | 4→3 lines | ~28 |
| 22:11 | Edited TODO.md | inline fix | ~48 |
| 22:11 | Edited TODO.md | 3→3 lines | ~19 |
| 22:12 | Edited TODO.md | 3→3 lines | ~27 |
| 22:12 | Edited TODO.md | 4 → 3 | ~8 |
| 22:19 | Session end: 13 writes across 6 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 9 reads | ~33971 tok |
| 22:20 | Created src/experiment_engine/text_calibration/strategies.py | — | ~2664 |
| 22:21 | Edited src/experiment_engine/text_calibration/calibrator.py | expanded (+11 lines) | ~345 |
| 22:21 | Edited src/experiment_engine/text_calibration/calibrator.py | modified _apply_calibration() | ~508 |
| 22:21 | Edited src/experiment_engine/text_calibration/__init__.py | expanded (+14 lines) | ~405 |
| 22:22 | Edited src/experiment_engine/text_calibration/calibrator.py | 7→6 lines | ~47 |
| 22:22 | Edited src/experiment_engine/text_calibration/strategies.py | added 1 import(s) | ~55 |
| 22:22 | Edited src/experiment_engine/text_calibration/strategies.py | inline fix | ~24 |
| 22:24 | P1-15: 校准器策略模式重构 — 创建 strategies.py (ABC + 4种策略 + Registry), 重构 _apply_calibration 用注册表, calibrate_* 静态方法代理到策略类, HACK-6 已解决 | strategies.py, calibrator.py, __init__.py | DONE — 465 passed, 6 xfailed, ruff clean | ~2700 tok |
| 22:24 | Edited HACK.md | 8→7 lines | ~104 |
| 22:24 | Edited HACK.md | 4→4 lines | ~24 |
| 22:25 | Edited HACK.md | 4→4 lines | ~24 |
| 22:31 | Session end: 23 writes across 9 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 15 reads | ~65018 tok |
| 22:37 | Edited src/experiment_engine/text_calibration/strategies.py | modified calibrate() | ~761 |
| 22:37 | Edited src/experiment_engine/text_calibration/strategies.py | modified calibrate() | ~618 |
| 22:37 | Edited src/experiment_engine/text_calibration/strategies.py | modified errstate() | ~100 |
| 22:38 | Edited src/experiment_engine/pyodide_handlers.py | modified handle_load_corpus() | ~443 |
| 22:39 | Edited src/services/pyodide.worker.ts | modified handleLoadCorpus() | ~203 |
| 22:39 | Edited src/services/pyodide.worker.ts | 3→7 lines | ~51 |
| 22:39 | Edited src/types/qca.ts | inline fix | ~31 |
| 22:39 | Edited src/services/pyodide.ts | isArray() → read() | ~161 |
| 22:39 | Edited src/hooks/useQCAWorkflow.ts | expanded (+7 lines) | ~76 |
| 22:39 | Edited src/hooks/useQCAWorkflow.ts | modified useCallback() | ~199 |
| 22:40 | Edited src/pages/DataInput.tsx | added 2 condition(s) | ~275 |
| 22:40 | Edited src/pages/DataInput.tsx | 6→7 lines | ~44 |
| 22:41 | Edited src/pages/DataInput.tsx | added 1 condition(s) | ~274 |
| 22:41 | Edited src/pages/DataInput.tsx | modified catch() | ~183 |
| 22:41 | Edited src/pages/DataInput.tsx | added 1 condition(s) | ~236 |
| %H:%M | P1-17: vectorized DirectCalibration + IndirectCalibration in strategies.py (for-loop → np.select) | strategies.py | 12/12 calibration tests pass, no warnings | ~1800 |
| %H:%M | P1-16: moved text parsing from frontend to Python TextCorpusReader via worker | pyodide_handlers.py, pyodide.worker.ts, pyodide.ts, qca.ts, useQCAWorkflow.ts, DataInput.tsx | removed parseTextContent(), added detectCorpusFormat() + checkFileSize() frontend helpers | ~2500 |
| 22:48 | Verified P1-16+P1-17: 465 tests, ruff clean, npm build ok, strategies.py no for-loop, DataInput.tsx no parseTextContent, worker chain complete. Committed b9b1687. | src/, tests/ | pass | ~3500 |
| 22:49 | Session end: 38 writes across 15 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 23 reads | ~104634 tok |
| 22:51 | Edited src/experiment_engine/models/qca.py | 3→4 lines | ~48 |
| 22:51 | Edited src/experiment_engine/text_calibration/condition.py | 4→3 lines | ~24 |
| 22:51 | Edited src/experiment_engine/text_calibration/condition.py | modified _kw_to_dict() | ~62 |
| 22:52 | Created src/experiment_engine/text_calibration/keyword_io.py | — | ~4112 |
| 22:52 | Edited src/experiment_engine/pyodide_handlers.py | modified handle_import_keywords() | ~930 |
| 22:52 | Edited src/types/qca.ts | 12→14 lines | ~346 |
| 22:53 | Edited src/types/qca.ts | 2→6 lines | ~101 |
| 22:53 | Edited src/services/pyodide.worker.ts | expanded (+11 lines) | ~138 |
| 22:53 | Edited src/services/pyodide.worker.ts | modified handleValidate() | ~676 |
| 22:53 | Edited src/services/pyodide.ts | modified importKeywords() | ~416 |
| 22:53 | Edited src/hooks/useQCAWorkflow.ts | expanded (+14 lines) | ~181 |
| 22:53 | Edited src/hooks/useQCAWorkflow.ts | modified useCallback() | ~282 |
| 22:54 | Edited src/hooks/useQCAWorkflow.ts | added 1 import(s) | ~38 |
| 22:54 | Edited src/pages/DataInput.tsx | added 1 import(s) | ~49 |
| 22:54 | Edited src/pages/DataInput.tsx | 2→5 lines | ~83 |
| 22:55 | Edited src/pages/DataInput.tsx | added error handling | ~506 |
| 22:55 | Edited src/pages/DataInput.tsx | added optional chaining | ~659 |
| 22:55 | Edited src/pages/DataInput.tsx | 6→6 lines | ~76 |
| 22:55 | Edited src/pages/DataInput.tsx | 6→6 lines | ~57 |
| 22:55 | Edited src/pages/Settings.tsx | added 2 import(s) | ~98 |
| 22:56 | Edited src/pages/Settings.tsx | CSS: state | ~76 |
| 22:56 | Edited src/pages/Settings.tsx | added error handling | ~395 |
| 22:57 | Edited src/pages/Settings.tsx | expanded (+41 lines) | ~535 |
| 22:58 | Created tests/test_keyword_io.py | — | ~4530 |
| 22:58 | Edited tests/test_keyword_io.py | inline fix | ~8 |
| 22:58 | Edited tests/test_keyword_io.py | inline fix | ~9 |
| 22:58 | Edited tests/test_keyword_io.py | inline fix | ~8 |
| 22:58 | Edited tests/test_keyword_io.py | inline fix | ~9 |
| 23:00 | Edited src/experiment_engine/text_calibration/keyword_io.py | 12→14 lines | ~144 |
| 23:00 | Edited src/experiment_engine/text_calibration/keyword_io.py | 12→14 lines | ~153 |
| 23:01 | Edited src/experiment_engine/models/qca.py | 4→4 lines | ~42 |
| 23:02 | Edited src/experiment_engine/text_calibration/keyword_io.py | 6→6 lines | ~36 |
| 23:03 | Edited src/experiment_engine/text_calibration/keyword_io.py | "r" → "utf-8" | ~13 |
| 23:03 | Session end: 71 writes across 19 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 27 reads | ~131007 tok |
| 23:03 | Session end: 71 writes across 19 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 27 reads | ~131007 tok |
| 23:15 | Session end: 71 writes across 19 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 27 reads | ~131007 tok |
| 23:18 | Edited TODO.md | expanded (+9 lines) | ~576 |
| 23:18 | Edited TODO.md | expanded (+11 lines) | ~448 |
| 23:19 | Edited TODO.md | 2→6 lines | ~267 |
| 23:19 | Edited TODO.md | 15→15 lines | ~116 |
| 23:19 | Created .claude/worktrees/agent-a182dd20ad100bc90/TODO.md | — | ~2288 |
| 23:20 | Edited FIXME.md | expanded (+8 lines) | ~682 |
| 23:20 | Edited FIXME.md | expanded (+24 lines) | ~461 |
| 23:20 | Edited TODO.md | expanded (+36 lines) | ~398 |
| 23:20 | Created .claude/worktrees/agent-a182dd20ad100bc90/FIXME.md | — | ~2779 |
| 23:21 | Edited TODO.md | expanded (+8 lines) | ~232 |
| 23:21 | Edited TODO.md | expanded (+6 lines) | ~134 |
| 23:21 | Edited FIXME.md | _compute_solution_coverage() → match_corpus() | ~613 |
| 23:21 | Edited TODO.md | 16→17 lines | ~149 |
| 23:21 | Edited FIXME.md | expanded (+8 lines) | ~250 |
| 23:21 | Edited FIXME.md | 11→12 lines | ~115 |
| 23:22 | Edited HACK.md | expanded (+9 lines) | ~284 |
| 23:22 | Created .claude/worktrees/agent-a182dd20ad100bc90/HACK.md | — | ~2066 |
| 23:22 | Edited HACK.md | expanded (+18 lines) | ~484 |
| 23:22 | Edited HACK.md | 6→6 lines | ~31 |
| 23:23 | Edited FIXME.md | expanded (+45 lines) | ~870 |
| 23:23 | Edited .claude/worktrees/agent-a182dd20ad100bc90/FIXME.md | 10→10 lines | ~105 |
| 23:23 | 需求变更审查: 分析 prototype 管道错误 + csQCA 缺失 + FuzzySetData 命名，更新 TODO.md/FIXME.md/HACK.md (新增 FIXME-23~28, HACK-13~15, TODO P0-9~12 + P1-24~31 + P2-21~24) | TODO.md, FIXME.md, HACK.md | 文档更新完成，待实施 | ~5000 |
| 23:23 | Edited FIXME.md | 12→15 lines | ~174 |
| 23:23 | Edited TODO.md | inline fix | ~64 |
| 23:23 | Edited .claude/worktrees/agent-a182dd20ad100bc90/.wolf/cerebrum.md | expanded (+8 lines) | ~518 |
| 23:23 | Edited .claude/worktrees/agent-a182dd20ad100bc90/.wolf/cerebrum.md | 3→3 lines | ~70 |
| 23:23 | Edited HACK.md | expanded (+18 lines) | ~430 |
| 23:23 | Edited .claude/worktrees/agent-a182dd20ad100bc90/.wolf/cerebrum.md | 4→7 lines | ~64 |
| 23:23 | Edited HACK.md | 6→6 lines | ~34 |
| 23:24 | Edited .claude/worktrees/agent-a182dd20ad100bc90/.wolf/cerebrum.md | 4→4 lines | ~59 |
| 23:24 | Edited .claude/worktrees/agent-a182dd20ad100bc90/.wolf/memory.md | 4→6 lines | ~118 |
| 23:24 | Session end: 101 writes across 21 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 40 reads | ~171246 tok |
| 23:24 | Session end: 101 writes across 21 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 40 reads | ~171246 tok |
| 23:24 | Edited .claude/worktrees/agent-a182dd20ad100bc90/.wolf/anatomy.md | 2→2 lines | ~44 |
| 23:24 | Edited .claude/worktrees/agent-a182dd20ad100bc90/.wolf/anatomy.md | inline fix | ~25 |
| 23:25 | Session end: 103 writes across 22 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 41 reads | ~171320 tok |
| 23:28 | Edited TODO.md | inline fix | ~41 |
| 23:28 | Edited TODO.md | inline fix | ~50 |
| 23:28 | Edited TODO.md | inline fix | ~48 |
| 23:28 | Edited TODO.md | inline fix | ~54 |
| 23:29 | Edited TODO.md | 20→20 lines | ~545 |
| 23:29 | Edited TODO.md | 15→14 lines | ~134 |
| 23:30 | Edited FIXME.md | 6→6 lines | ~103 |
| 23:30 | Edited HACK.md | inline fix | ~4 |
| 23:30 | Edited HACK.md | 6→6 lines | ~36 |
| 23:34 | Session end: 112 writes across 22 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 41 reads | ~172445 tok |
| 23:42 | Session end: 112 writes across 22 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 41 reads | ~172445 tok |
| 23:47 | Edited FIXME.md | expanded (+27 lines) | ~673 |
| 23:47 | Edited FIXME.md | 17→18 lines | ~216 |
| 23:48 | Edited HACK.md | expanded (+13 lines) | ~487 |
| 23:48 | Edited HACK.md | 8→8 lines | ~39 |
| 23:48 | Edited FIXME.md | inline fix | ~14 |
| 23:49 | BERT-vs-关键词架构分析完成：深度分析结论（BERT 不能完全替代关键词）+ 新增 FIXME-34/35/36、更新 HACK-17、新增 HACK-18、产出分析报告 | .wolf/bert-vs-keyword-analysis.md, FIXME.md, HACK.md, .wolf/anatomy.md | FIXME: 20/36 resolved, HACK: 4/18 resolved, 新增 6000 字分析报告 | ~4000 |
| 23:51 | Session end: 117 writes across 22 files (framework.py, qca.py, training.py, __init__.py, FIXME.md) | 43 reads | ~153916 tok |

## Session: 2026-05-24 23:55

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 00:46 | Edited TODO.md | expanded (+8 lines) | ~149 |
| 00:46 | Edited TODO.md | inline fix | ~103 |
| 00:46 | Edited TODO.md | 1→3 lines | ~120 |
| 00:47 | Edited TODO.md | 5→5 lines | ~131 |
| 00:47 | Edited TODO.md | 5→9 lines | ~108 |
| 00:47 | Edited HACK.md | inline fix | ~52 |
| 00:47 | Edited HACK.md | 2→2 lines | ~60 |
| 2026-05-25 | BERT 决策定案 session: Explore Agent + 技术顾问 + 算法顾问 + 评审者 三轮讨论，定量对比（86x WASM CPU，5.9x 冷启动），最终决议 BERT 辅助工具不做主引擎 | bert-vs-keyword-analysis.md, TODO.md, HACK.md, cerebrum.md, memory.md | 文档全部更新，下一 session 按 P0-9 开始 | ~35000 |

## HANDOFF: 2026-05-25 Session Wrap

### 核心产出
BERT 架构决策已定案：**BERT 作为辅助工具不做主引擎。** 关键词匹配是 QCA 方法论核心不可替代。详见 `.wolf/bert-vs-keyword-analysis.md` 第 10 节。

### 当前基线
- 8/8 P0 已修复，P0-9~P0-12（需求变更阻塞项）待开始
- 19/22 FIXME 已修复，14 FIXME 待处理（2 🔴 + 9 🟡 + 5 🟢）
- 465 测试通过，ruff 干净，npm build 通过

### 下一会话推进顺序
1. P0-9: 消除 prototype 独立管道（FIXME-23）
2. P0-10: csQCA 全链路实现（FIXME-24）
3. P0-11/12: 模型重命名 + QCAVariant 拆分（FIXME-25/26）
4. P1-24~31: 需求变更相关
5. P1-34: 预置词典在线编辑器
6. P1-32/33: BERT CLI 辅助工具（范围已缩小）
| 00:48 | Session end: 7 writes across 2 files (TODO.md, HACK.md) | 16 reads | ~7130 tok |

## Session: 2026-05-24 00:49

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 00:55 | Edited src/experiment_engine/models/qca.py | modified QCAVariant() | ~235 |
| 00:56 | Edited src/experiment_engine/models/qca.py | inline fix | ~19 |
| 00:56 | Edited src/experiment_engine/models/qca.py | modified ConditionSet() | ~242 |
| 00:56 | Edited src/experiment_engine/models/qca.py | modified MembershipData() | ~105 |
| 00:56 | Edited src/experiment_engine/models/qca.py | modified outcome_vector() | ~93 |
| 00:56 | Edited src/experiment_engine/models/qca.py | inline fix | ~13 |
| 00:56 | Edited src/types/qca.ts | expanded (+15 lines) | ~143 |
| 00:56 | Edited src/experiment_engine/models/__init__.py | 26→29 lines | ~197 |
| 00:56 | Edited src/types/qca.ts | inline fix | ~11 |
| 00:56 | Edited src/types/qca.ts | 8→9 lines | ~66 |
| 00:57 | Edited src/types/qca.ts | 10→13 lines | ~125 |
| 00:57 | Edited src/experiment_engine/models/__init__.py | 42→45 lines | ~270 |
| 00:57 | Edited src/experiment_engine/__init__.py | 25→27 lines | ~147 |
| 00:57 | Edited src/types/qca.ts | inline fix | ~12 |
| 00:57 | Edited src/types/qca.ts | inline fix | ~12 |
| 00:57 | Edited src/types/qca.ts | 3→3 lines | ~94 |
| 00:57 | Edited src/types/qca.ts | 3→3 lines | ~52 |
| 00:57 | Edited src/experiment_engine/__init__.py | 33→35 lines | ~197 |
| 00:57 | Edited src/experiment_engine/text_calibration/strategies.py | 11→12 lines | ~151 |
| 00:57 | Edited src/types/index.ts | 35→40 lines | ~216 |
| 00:57 | Edited src/pages/DataInput.tsx | 3→3 lines | ~15 |
| 00:57 | Edited src/pages/DataInput.tsx | inline fix | ~14 |
| 00:57 | Edited src/services/pyodide.ts | 1→2 lines | ~12 |
| 00:57 | Edited src/experiment_engine/text_calibration/strategies.py | inline fix | ~21 |
| 00:57 | Edited src/experiment_engine/text_calibration/strategies.py | inline fix | ~5 |
| 00:57 | Edited src/services/pyodide.ts | 2→2 lines | ~22 |
| 00:57 | Edited src/services/pyodide.ts | 3→3 lines | ~32 |
| 00:57 | Edited src/services/pyodide.ts | 3→3 lines | ~33 |
| 00:57 | Edited src/experiment_engine/text_calibration/strategies.py | modified calibrate() | ~182 |
| 00:58 | Edited src/services/pyodide.ts | inline fix | ~10 |
| 00:58 | Edited src/experiment_engine/text_calibration/strategies.py | 6→7 lines | ~110 |
| 00:58 | Edited src/store/QCAPipelineContext.tsx | inline fix | ~6 |
| 00:58 | Edited src/components/DistributionPlot.tsx | inline fix | ~6 |
| 00:58 | Edited src/pyodide/engine.ts | inline fix | ~22 |
| 00:58 | Edited src/experiment_engine/text_calibration/calibrator.py | 11→11 lines | ~63 |
| 00:58 | Edited src/experiment_engine/text_calibration/calibrator.py | inline fix | ~5 |
| 00:58 | Edited src/services/pyodide.ts | 2→1 lines | ~6 |
| 00:58 | Session end: 37 writes across 11 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 30 reads | ~10118 tok |
| 00:59 | Edited src/pages/DataInput.tsx | added 1 import(s) | ~60 |
| 00:59 | Edited src/pages/DataInput.tsx | inline fix | ~16 |
| 00:59 | Edited src/types/index.ts | 4→2 lines | ~10 |
| 01:00 | TypeScript-side type refactoring for P0-12 + P0-11: renamed CalibrationType->CalibrationMethod (enum), added QCAVariant enum, added CRISP_SET, renamed FuzzySetDataJSON->MembershipDataJSON, added qca_variant to ConditionSet, updated all 6 files | src/types/qca.ts src/types/index.ts src/pages/DataInput.tsx src/services/pyodide.ts src/store/QCAPipelineContext.tsx src/components/DistributionPlot.tsx src/pyodide/engine.ts | tsc clean, vite build passes | ~1500 |
| 01:01 | Edited src/experiment_engine/text_calibration/calibrator.py | inline fix | ~4 |
| 01:01 | Edited tests/test_qca_core.py | inline fix | ~10 |
| 01:05 | Session end: 42 writes across 12 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 30 reads | ~14648 tok |
| 01:09 | Edited src/types/qca.ts | "ragin" → "fuzzy_direct" | ~10 |
| 01:10 | Edited src/pages/Settings.tsx | inline fix | ~19 |
| 01:10 | Edited src/experiment_engine/text_calibration/calibrator.py | inline fix | ~7 |
| 01:10 | Edited tests/test_qca_core.py | inline fix | ~7 |
| 01:13 | Session end: 46 writes across 13 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 30 reads | ~10261 tok |
| 01:14 | Edited src/experiment_engine/text_calibration/strategies.py | modified calibrate() | ~196 |
| 01:14 | Edited src/experiment_engine/text_calibration/__init__.py | 8→9 lines | ~69 |
| 01:14 | Edited src/experiment_engine/text_calibration/__init__.py | 3→4 lines | ~34 |
| 01:14 | Edited src/experiment_engine/text_calibration/calibrator.py | 11→12 lines | ~68 |
| 01:14 | Edited src/experiment_engine/text_calibration/calibrator.py | 9→14 lines | ~181 |
| 01:14 | Edited src/experiment_engine/text_calibration/calibrator.py | 9→14 lines | ~180 |
| 01:15 | Edited src/experiment_engine/qca_engine/truth_table.py | modified _compute_config_membership() | ~176 |
| 01:15 | Edited src/pages/Settings.tsx | 5→5 lines | ~86 |
| 01:15 | Edited src/experiment_engine/cli.py | inline fix | ~23 |
| 01:15 | Edited src/pages/Settings.tsx | expanded (+9 lines) | ~170 |
| 01:15 | Edited src/pages/Settings.tsx | CSS: method | ~195 |
| 01:15 | Edited src/experiment_engine/cli.py | modified calibrate() | ~450 |
| 01:15 | Edited src/pages/Settings.tsx | CSS: options, options | ~116 |
| 01:15 | Edited src/experiment_engine/cli.py | modified analyze() | ~428 |
| 01:15 | Edited src/pages/DataInput.tsx | inline fix | ~18 |
| 01:15 | Edited src/pages/DataInput.tsx | added error handling | ~148 |
| 01:15 | Edited src/experiment_engine/cli.py | modified run() | ~368 |
| 01:16 | Edited src/pages/DataInput.tsx | modified generatePrototypeConditionSet() | ~501 |
| 01:16 | Edited src/pages/DataInput.tsx | 3→7 lines | ~72 |
| 01:16 | Edited src/pages/DataInput.tsx | 2→6 lines | ~58 |
| 01:17 | Edited tests/test_qca_core.py | modified test_apply_calibration_invalid_enum_raises() | ~2909 |
| 01:17 | Edited src/pages/DataInput.tsx | added nullish coalescing | ~86 |
| 01:17 | Edited tests/test_qca_core.py | 11→12 lines | ~67 |
| 01:17 | Edited src/pages/DataInput.tsx | added nullish coalescing | ~105 |
| 01:17 | Edited src/hooks/useQCAWorkflow.ts | added error handling | ~216 |
| 01:17 | Edited tests/test_qca_core.py | 3→3 lines | ~32 |
| 01:18 | Edited src/hooks/useQCAWorkflow.ts | modified if() | ~253 |
| 01:18 | Edited src/hooks/useQCAWorkflow.ts | modified if() | ~228 |
| 01:18 | Edited src/hooks/useQCAWorkflow.ts | modified if() | ~232 |
| 01:18 | Edited src/hooks/useQCAWorkflow.ts | modified if() | ~202 |
| 01:18 | Edited tests/test_qca_core.py | inline fix | ~20 |
| 17:19 | Added csQCA variant support to frontend: qca_variant toggle in Settings with dynamic calibration method filtering, qca_variant propagation in DataInput ConditionSet creation, and ensureQCAVariant fallback in useQCAWorkflow hook | src/pages/Settings.tsx, src/pages/DataInput.tsx, src/hooks/useQCAWorkflow.ts | tsc -b and vite build both pass with zero errors | ~250 |
| 01:20 | Session end: 77 writes across 16 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 32 reads | ~35717 tok |
| 01:20 | Implemented csQCA (crisp-set QCA) end-to-end on Python backend | strategies.py, calibrator.py, truth_table.py, cli.py, __init__.py, test_qca_core.py | 490 tests pass, ruff clean | ~600 |
| 01:22 | Session end: 77 writes across 16 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 32 reads | ~35717 tok |
| 01:32 | Session end: 77 writes across 16 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 32 reads | ~35717 tok |
| 01:37 | Session end: 77 writes across 16 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 33 reads | ~40680 tok |
| 01:38 | Edited src/types/qca.ts | 18→16 lines | ~89 |
| 01:38 | Edited src/types/qca.ts | 16→18 lines | ~211 |
| 01:38 | Edited src/types/qca.ts | 14→15 lines | ~95 |
| 01:39 | Edited src/types/qca.ts | 14→13 lines | ~328 |
| 01:39 | Edited src/types/qca.ts | 10→8 lines | ~128 |
| 01:39 | Edited src/store/QCAPipelineContext.tsx | 12→12 lines | ~200 |
| 01:39 | Edited src/store/QCAPipelineContext.tsx | added nullish coalescing | ~54 |
| 01:39 | Edited src/store/QCAPipelineContext.tsx | 21→19 lines | ~216 |
| 01:39 | Edited src/store/QCAPipelineContext.tsx | reduced (-7 lines) | ~89 |
| 01:39 | Edited src/store/QCAPipelineContext.tsx | 19→17 lines | ~94 |
| 01:40 | Edited src/experiment_engine/models/qca.py | 3→8 lines | ~143 |
| 01:41 | Edited src/experiment_engine/pyodide_handlers.py | modified _serialize_fuzzy() | ~1860 |
| 01:41 | Edited src/experiment_engine/text_calibration/calibrator.py | expanded (+6 lines) | ~212 |
| 01:43 | Edited src/experiment_engine/pyodide_handlers.py | added 1 import(s) | ~19 |
| 01:43 | Edited src/experiment_engine/pyodide_handlers.py | modified in() | ~36 |
| 01:45 | P0-9: unified calibrate pipeline Python side — deprecated PROTOTYPE in ScoringSource, merged handle_calibrate + handle_calibrate_prototype into unified handler with optional prototypeTexts, added deprecation comments in calibrator.py | src/experiment_engine/models/qca.py, src/experiment_engine/pyodide_handlers.py, src/experiment_engine/text_calibration/calibrator.py | 490 passed, ruff clean | ~350 |
| 01:46 | Session end: 92 writes across 17 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 34 reads | ~62904 tok |
| 01:52 | Edited src/pages/DataInput.tsx | removed 28 lines | ~15 |
| 01:52 | Edited src/pages/DataInput.tsx | 5→3 lines | ~20 |
| 01:52 | Edited src/pages/DataInput.tsx | inline fix | ~3 |
| 01:52 | Edited src/pages/DataInput.tsx | inline fix | ~3 |
| 01:52 | Edited src/pages/DataInput.tsx | 6→3 lines | ~40 |
| 01:52 | Edited src/pages/DataInput.tsx | 6→3 lines | ~35 |
| 01:53 | Edited src/hooks/useQCAWorkflow.ts | 7→8 lines | ~72 |
| 01:53 | Session end: 99 writes across 17 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 34 reads | ~61853 tok |
| 01:57 | Edited src/pages/DataInput.tsx | 4→3 lines | ~28 |
| 02:01 | Removed extra `)} ` on line 921 of DataInput.tsx — leftover from P0-9 calibrationMode wrapper removal | src/pages/DataInput.tsx | npx tsc -b clean, 490 pytest pass | ~50 |
| 02:14 | Session end: 100 writes across 17 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 35 reads | ~73884 tok |
| 02:18 | Session end: 100 writes across 17 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 36 reads | ~83938 tok |
| 02:21 | Edited TODO.md | 4→4 lines | ~152 |
| 02:21 | Edited TODO.md | 7→7 lines | ~271 |
| 02:21 | Edited TODO.md | 18→16 lines | ~172 |
| 02:21 | Session end: 103 writes across 18 files (qca.py, qca.ts, __init__.py, strategies.py, index.ts) | 36 reads | ~84575 tok |

## Session: 2026-05-24 02:27

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 02:36 | Edited src/types/qca.ts | 16→18 lines | ~104 |
| 02:36 | Edited src/types/qca.ts | 21→24 lines | ~209 |
| 02:36 | Edited src/store/QCAPipelineContext.tsx | 2→3 lines | ~60 |
| 02:36 | Edited src/store/QCAPipelineContext.tsx | CSS: prototypeAnalysisResult | ~67 |
| 02:36 | Edited src/store/QCAPipelineContext.tsx | CSS: startPrototypeAnalysis, finishPrototypeAnalysis | ~64 |
| 02:36 | Edited src/store/QCAPipelineContext.tsx | expanded (+13 lines) | ~147 |
| 02:36 | Edited src/store/QCAPipelineContext.tsx | 3→5 lines | ~34 |
| 02:37 | Edited src/hooks/useQCAWorkflow.ts | expanded (+6 lines) | ~112 |
| 02:37 | Edited src/hooks/useQCAWorkflow.ts | 3→5 lines | ~34 |
| 02:37 | Edited src/hooks/useQCAWorkflow.ts | added 1 condition(s) | ~332 |
| 02:37 | Edited src/hooks/useQCAWorkflow.ts | expanded (+7 lines) | ~71 |
| 02:38 | Edited src/hooks/useQCAWorkflow.ts | added 1 condition(s) | ~178 |
| 02:38 | Edited src/hooks/useQCAWorkflow.ts | 2→3 lines | ~38 |
| 02:39 | Edited src/hooks/useQCAWorkflow.ts | 2→3 lines | ~19 |
| 02:39 | Edited src/components/PipelineStatus.tsx | 3→5 lines | ~76 |
| 02:41 | Created src/pages/Results.tsx | — | ~7952 |
| 02:41 | Edited src/pages/Results.css | modified not() | ~436 |
| 02:47 | Session end: 17 writes across 6 files (qca.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts, PipelineStatus.tsx, Results.tsx) | 8 reads | ~21171 tok |
| 02:52 | Edited TODO.md | inline fix | ~41 |
| 02:52 | Edited TODO.md | inline fix | ~11 |
| 02:52 | Edited TODO.md | inline fix | ~13 |
| 02:53 | Edited TODO.md | inline fix | ~8 |
| 02:57 | Edited src/hooks/useQCAWorkflow.ts | 2→2 lines | ~44 |
| 02:57 | Edited src/pages/Results.tsx | modified CompareView() | ~34 |
| 02:57 | Edited src/pages/Results.tsx | 7→4 lines | ~31 |
| 02:58 | Edited tests/test_keyword_io.py | modified zip() | ~68 |
| 03:03 | Edited src/experiment_engine/text_calibration/__init__.py | expanded (+10 lines) | ~245 |
| 03:03 | Edited src/experiment_engine/io/readers.py | added 3 import(s) | ~151 |
| 03:04 | Edited src/experiment_engine/io/readers.py | modified can_read() | ~64 |
| 03:04 | Edited src/experiment_engine/cli.py | modified import_keywords() | ~1284 |
| 03:04 | Edited src/pages/DataInput.tsx | 6→7 lines | ~38 |
| 03:04 | Edited src/pages/DataInput.tsx | 4→7 lines | ~106 |
| 03:04 | Edited src/experiment_engine/io/readers.py | modified name() | ~1655 |
| 03:04 | Edited src/pages/DataInput.tsx | added error handling | ~342 |
| 03:04 | Edited src/experiment_engine/io/readers.py | 2→5 lines | ~55 |
| 03:04 | Edited src/pages/DataInput.tsx | CSS: gap | ~462 |
| 03:04 | Edited src/experiment_engine/pyodide_handlers.py | expanded (+7 lines) | ~113 |
| 03:04 | Edited src/types/qca.ts | inline fix | ~34 |
| 03:05 | Edited src/services/pyodide.worker.ts | modified handleLoadCorpus() | ~62 |
| 03:05 | Edited src/services/pyodide.ts | modified loadCorpus() | ~41 |
| 03:05 | Edited src/hooks/useQCAWorkflow.ts | 6→6 lines | ~61 |
| 03:05 | Edited src/hooks/useQCAWorkflow.ts | modified useCallback() | ~52 |
| 03:06 | Edited src/pages/DataInput.tsx | CSS: buffer | ~262 |
| 03:06 | Edited src/pages/DataInput.tsx | CSS: content | ~369 |
| 03:06 | Edited src/pages/DataInput.tsx | CSS: content | ~307 |
| 03:06 | Edited src/pages/DataInput.tsx | 7→7 lines | ~98 |
| 03:07 | Edited src/pages/DataInput.tsx | inline fix | ~17 |
| 03:07 | P1-1: keyword dict import/export. Added exports to __init__.py, CLI commands import-keywords/export-keywords, export button in DataInput.tsx | __init__.py, cli.py, DataInput.tsx | 17 tests pass, ruff clean, build OK | ~500 |
| 03:31 | Created src/experiment_engine/qca_engine/nl_interpretation.py | — | ~4254 |
| 03:31 | Edited src/experiment_engine/qca_engine/nl_interpretation.py | modified _interpret_coverage_text() | ~177 |
| 03:32 | Created tests/test_nl_interpretation.py | — | ~4603 |
| 03:33 | Edited pyproject.toml | 1→3 lines | ~74 |
| 03:33 | Edited src/experiment_engine/qca_engine/nl_interpretation.py | added 1 import(s) | ~30 |
| 03:33 | Edited src/experiment_engine/qca_engine/nl_interpretation.py | expanded (+16 lines) | ~223 |
| 03:33 | Edited src/experiment_engine/qca_engine/nl_interpretation.py | 11→11 lines | ~86 |
| 03:33 | Edited src/experiment_engine/qca_engine/nl_interpretation.py | modified _num_to_cn() | ~94 |
| 03:35 | Created src/experiment_engine/qca_engine/nl_interpretation.py | — | ~4473 |
| 03:36 | Edited src/experiment_engine/qca_engine/nl_interpretation.py | 3→3 lines | ~11 |
| 03:37 | Edited src/pages/Results.tsx | expanded (+7 lines) | ~44 |
| 03:37 | Edited src/pages/Results.tsx | 5→8 lines | ~103 |
| 03:38 | Edited src/pages/Results.tsx | added optional chaining | ~2437 |
| 03:42 | P1-3: QCA natural language interpretation — Python backend + 35 tests + TS frontend auto-interpretation card | nl_interpretation.py, test_nl_interpretation.py, Results.tsx, Results.css, pyproject.toml | 525 tests pass, ruff clean, npm build passes | ~1500 |
| 03:47 | Created src/i18n/translations.ts | — | ~8874 |
| 03:48 | Created src/i18n/I18nContext.tsx | — | ~1424 |
| 03:48 | Edited src/App.tsx | modified App() | ~271 |
| 03:48 | Edited src/components/Sidebar.tsx | modified Sidebar() | ~456 |
| 03:48 | Edited src/components/PipelineStatus.tsx | CSS: t, path | ~600 |
| 03:49 | Edited src/pages/Dashboard.tsx | added 1 import(s) | ~444 |
| 03:49 | Edited src/pages/Dashboard.tsx | 4→4 lines | ~51 |
| 03:49 | Edited src/pages/Dashboard.tsx | modified t() | ~1533 |
| 03:49 | Edited src/pages/Dashboard.tsx | 9→9 lines | ~119 |
| 03:50 | Edited src/pages/DataInput.tsx | added 1 import(s) | ~128 |
| 03:50 | Edited src/pages/DataInput.tsx | modified DataInput() | ~53 |
| 03:50 | Edited src/pages/DataInput.tsx | CSS: _DOMAIN_LABELS_LEGACY | ~89 |
| 03:50 | Edited src/pages/DataInput.tsx | 2→2 lines | ~37 |
| 03:50 | Edited src/pages/DataInput.tsx | "Load Engine" → "dataInput.engineNotReady" | ~12 |
| 03:50 | Edited src/pages/DataInput.tsx | modified t() | ~288 |
| 03:50 | Edited src/pages/DataInput.tsx | 13→13 lines | ~225 |
| 03:50 | Edited src/pages/DataInput.tsx | 25→25 lines | ~321 |
| 03:51 | Edited src/pages/DataInput.tsx | 14→14 lines | ~208 |
| 03:51 | Edited src/pages/DataInput.tsx | modified t() | ~88 |
| 03:51 | Edited src/pages/DataInput.tsx | 6→6 lines | ~93 |
| 03:51 | Edited src/pages/DataInput.tsx | 3→3 lines | ~46 |
| 03:51 | Edited src/pages/DataInput.tsx | 2→2 lines | ~32 |
| 03:51 | Edited src/pages/DataInput.tsx | inline fix | ~22 |
| 03:52 | Edited src/pages/DataInput.tsx | 31→30 lines | ~381 |
| 03:52 | Edited src/pages/DataInput.tsx | "编号,文本内容,结果&#10;case_1,服务态" → "dataInput.prototypePlaceh" | ~18 |
| 03:52 | Edited src/pages/DataInput.tsx | 6→6 lines | ~94 |
| 03:52 | Edited src/pages/DataInput.tsx | 6→6 lines | ~130 |
| 03:52 | Edited src/pages/DataInput.tsx | inline fix | ~18 |
| 03:53 | Edited src/pages/DataInput.tsx | inline fix | ~30 |
| 03:53 | Edited src/pages/DataInput.tsx | 3→3 lines | ~42 |
| 03:53 | Edited src/pages/DataInput.tsx | inline fix | ~23 |
| 03:54 | Edited src/pages/DataInput.tsx | 5→5 lines | ~70 |
| 03:54 | Edited src/pages/DataInput.tsx | 4→3 lines | ~47 |
| 03:54 | Edited src/pages/DataInput.tsx | 12→12 lines | ~154 |
| 03:54 | Edited src/pages/DataInput.tsx | 37→37 lines | ~509 |
| 03:55 | Edited src/pages/DataInput.tsx | 6→7 lines | ~141 |
| 03:55 | Edited src/pages/DataInput.tsx | modified t() | ~158 |
| 03:55 | Edited src/pages/DataInput.tsx | "Error: ${sizeError}" → "Error: ${t(" | ~32 |
| 03:57 | Edited src/pages/DataInput.tsx | modified if() | ~268 |
| 03:57 | Edited src/pages/DataInput.tsx | modified catch() | ~73 |
| 03:57 | Edited src/pages/DataInput.tsx | 3→3 lines | ~38 |
| 03:57 | Edited src/pages/DataInput.tsx | modified catch() | ~78 |
| 03:58 | Edited src/pages/DataInput.tsx | added 1 condition(s) | ~578 |
| 03:58 | Edited src/pages/DataInput.tsx | modified catch() | ~84 |
| 03:58 | Edited src/pages/DataInput.tsx | modified catch() | ~65 |
| 03:59 | Edited src/pages/DataInput.tsx | modified if() | ~184 |
| 04:05 | Edited src/pages/DataInput.tsx | "No keyword dictionary loa" → "dataInput.noDictLoaded" | ~16 |
| 04:07 | Edited src/pages/DataInput.tsx | modified catch() | ~93 |
| 04:07 | Edited src/pages/DataInput.tsx | 7→7 lines | ~47 |
| 04:08 | Edited src/pages/Results.tsx | added 1 import(s) | ~202 |
| 04:08 | Edited src/pages/Results.tsx | modified Results() | ~39 |
| 04:09 | Edited src/pages/Results.tsx | 6→6 lines | ~135 |
| 04:10 | Edited src/pages/Results.tsx | modified if() | ~170 |
| 04:10 | Edited src/pages/Results.tsx | 2→2 lines | ~36 |
| 04:10 | Edited src/pages/Results.tsx | 18→18 lines | ~186 |
| 04:19 | Edited src/pages/DataInput.tsx | inline fix | ~22 |
| 04:19 | Edited src/pages/Results.tsx | 3→4 lines | ~74 |
| 04:20 | Edited src/pages/Results.tsx | modified catch() | ~207 |
| 04:20 | Edited src/pages/Results.tsx | expanded (+11 lines) | ~383 |
| 04:20 | Edited src/pages/DataInput.tsx | modified if() | ~264 |
| 04:20 | Edited src/pages/Results.tsx | modified toFixed() | ~278 |
| 04:20 | Edited src/pages/DataInput.tsx | modified if() | ~242 |
| 04:20 | Edited src/i18n/translations.ts | 2→3 lines | ~33 |
| 04:20 | Edited src/i18n/translations.ts | 2→3 lines | ~40 |
| 04:20 | Edited src/pages/Results.tsx | 45→45 lines | ~653 |
| 04:20 | Edited src/pages/DataInput.tsx | modified catch() | ~295 |
| 04:20 | Edited src/i18n/translations.ts | 2→3 lines | ~48 |
| 04:20 | Edited src/pages/Results.tsx | modified t() | ~774 |
| 04:20 | Edited src/pages/Settings.tsx | added 1 import(s) | ~68 |
| 04:20 | Edited src/pages/DataInput.tsx | 12→15 lines | ~240 |
| 04:21 | Edited src/pages/Settings.tsx | 3→4 lines | ~45 |
| 04:21 | Edited src/pages/Settings.tsx | modified if() | ~28 |
| 04:21 | Edited src/pages/Settings.tsx | modified catch() | ~56 |
| 04:21 | Edited src/pages/Results.tsx | CSS: t, path | ~1021 |
| 04:21 | Edited src/i18n/translations.ts | 20→21 lines | ~112 |
| 04:21 | Edited src/pages/Settings.tsx | 2→2 lines | ~37 |
| 04:21 | Edited src/pages/Results.tsx | 3→3 lines | ~52 |
| 04:21 | Edited src/pages/Settings.tsx | inline fix | ~23 |
| 04:21 | Edited src/i18n/translations.ts | 2→3 lines | ~16 |
| 04:21 | Edited src/pages/Results.tsx | 6→7 lines | ~62 |
| 04:21 | Edited src/pages/Settings.tsx | inline fix | ~23 |
| 04:21 | Edited src/pages/Settings.tsx | inline fix | ~23 |
| 04:21 | Edited src/i18n/translations.ts | 2→3 lines | ~19 |
| 04:21 | Edited src/pages/Settings.tsx | 4→4 lines | ~66 |
| 04:22 | Edited src/pages/Settings.tsx | inline fix | ~23 |
| 04:22 | Edited src/pages/Settings.tsx | inline fix | ~22 |
| 04:22 | Edited src/pages/Results.tsx | CSS: t, path, headingStyle | ~1425 |
| 04:22 | Edited src/pages/Settings.tsx | modified t() | ~58 |
| 04:22 | Edited src/pages/Settings.tsx | 2→2 lines | ~37 |
| 04:22 | Edited src/pages/Settings.tsx | 8→8 lines | ~125 |
| 04:22 | Edited src/pages/Results.tsx | CSS: t, path | ~608 |
| 04:22 | Edited src/pages/Settings.tsx | "Exporting..." → "settings.exportDictExport" | ~27 |
| 04:22 | Edited src/pages/DataInput.tsx | inline fix | ~23 |
| 04:22 | Edited src/pages/Settings.tsx | inline fix | ~38 |
| 04:22 | Edited src/pages/Results.tsx | CSS: t, path | ~453 |
| 04:22 | Edited src/i18n/translations.ts | 2→3 lines | ~21 |
| 04:22 | Edited src/pages/Settings.tsx | 27→27 lines | ~407 |
| 04:23 | Edited src/pages/Settings.tsx | 5→5 lines | ~57 |
| 04:23 | Edited src/pages/Results.tsx | modified t() | ~339 |
| 04:23 | Edited src/i18n/translations.ts | 2→3 lines | ~20 |
| 04:23 | Edited src/i18n/translations.ts | 2→3 lines | ~25 |
| 04:23 | Edited src/pages/Results.tsx | modified AutoInterpretation() | ~530 |
| 04:23 | Edited src/pages/Settings.tsx | modified SettingRow() | ~704 |
| 04:26 | Edited src/pages/Results.tsx | " AND " → " 且 " | ~21 |
| 04:26 | Edited src/pages/Results.tsx | " AND " → " 且 " | ~6 |
| 04:26 | Completed P1-4 Chinese translation: fixed hardcoded English in DataInput.tsx (more cases, Error: prefix, Plain Text, validation styling) + added common.error and formatPlainText keys | src/pages/DataInput.tsx, src/i18n/translations.ts | build passes, committed | ~200 |
| 04:28 | Translated Settings.tsx to Chinese via i18n (useT hook). Added exportDictError key. Build passes. | src/pages/Settings.tsx, src/i18n/translations.ts | commit ad48b15 | ~400 |
| 04:32 | P1-4 verification: all 5 files already translated in prior commits (81cc862, 8e386c6, ad48b15). Verified Sidebar/App/Dashboard/PipelineStatus 100% translated. Results.tsx already fully using t(). npm build passes. No diff from HEAD. | src/pages/Results.tsx, src/i18n/translations.ts | verified complete | ~500 |
| 04:34 | Session end: 165 writes across 24 files (qca.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts, PipelineStatus.tsx, Results.tsx) | 31 reads | ~144475 tok |
| 04:41 | Edited TODO.md | inline fix | ~33 |
| 04:41 | Edited TODO.md | inline fix | ~31 |
| 04:41 | Edited TODO.md | inline fix | ~29 |
| 04:41 | Edited TODO.md | inline fix | ~30 |
| 04:41 | Edited TODO.md | inline fix | ~45 |
| 04:41 | Edited TODO.md | 3→3 lines | ~34 |
| 04:41 | Edited TODO.md | 3→5 lines | ~33 |
| 04:43 | Session end: 172 writes across 24 files (qca.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts, PipelineStatus.tsx, Results.tsx) | 31 reads | ~147914 tok |

## Session: 2026-05-25 09:02

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 09:08 | Edited TODO.md | 7→4 lines | ~26 |
| 09:08 | Edited TODO.md | removed 3 lines | ~11 |
| 09:08 | Edited TODO.md | 6→6 lines | ~70 |
| 09:09 | Edited TODO.md | removed 8 lines | ~2 |
| 09:09 | Edited TODO.md | removed 9 lines | ~7 |
| 09:09 | Edited TODO.md | removed 18 lines | ~1 |
| 09:09 | Edited TODO.md | 4→3 lines | ~26 |
| 09:10 | Edited TODO.md | 6→6 lines | ~70 |
| 09:10 | Edited TODO.md | inline fix | ~11 |
| 09:10 | Edited TODO.md | inline fix | ~14 |
| 09:11 | Edited roadmap/experiment-engine-roadmap.json | inline fix | ~10 |
| 09:11 | Removed all BERT content from TODO.md, handover.md, roadmap: P1-32/33 + P2-25/26 + P2-14 removed. Stats recalculated (P1: 23→10 remaining, P2: 28→23 remaining). | TODO.md, handover.md, experiment-engine-roadmap.json | 33 tasks remaining | ~3000 |
| 09:14 | Session end: 11 writes across 2 files (TODO.md, experiment-engine-roadmap.json) | 3 reads | ~2910 tok |

## Session: 2026-05-25 12:46

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 13:35 | Edited TODO.md | expanded (+40 lines) | ~643 |
| 13:35 | Edited TODO.md | inline fix | ~17 |
| 13:36 | Edited TODO.md | 15→17 lines | ~128 |
| 13:36 | Edited roadmap/experiment-engine-roadmap.json | 18→19 lines | ~175 |
| 13:36 | Edited roadmap/experiment-engine-roadmap.json | expanded (+160 lines) | ~1935 |
| 13:37 | Edited roadmap/experiment-engine-roadmap.json | expanded (+14 lines) | ~113 |
| 13:37 | Edited roadmap/experiment-engine-roadmap.json | 15→16 lines | ~122 |
| 13:42 | BERT+Prototype architecture refactoring plan finalized: TODO.md + roadmap.json + cerebrum.md | 3 files | 5-phase implementation sequence designed | ~12000 tok |
| 13:43 | Session end: 7 writes across 2 files (TODO.md, experiment-engine-roadmap.json) | 42 reads | ~25591 tok |
| 13:44 | Edited package.json | 1→2 lines | ~18 |
| 13:44 | Created src/types/bert.ts | — | ~675 |
| 13:46 | Session end: 9 writes across 4 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts) | 43 reads | ~26959 tok |
| 13:47 | Created src/services/bert-cache.ts | — | ~3612 |
| 13:48 | Created src/experiment_engine/text_calibration/cosine_similarity.py | — | ~4701 |
| 13:49 | Session end: 11 writes across 6 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 46 reads | ~35444 tok |
| 13:49 | Created src/services/bert-engine.ts | — | ~2378 |
| 13:50 | created bert-cache.ts — IndexedDB cache for BERT prototype + text embeddings | src/services/bert-cache.ts | build passes | ~288 tok |
| 13:50 | Edited src/services/bert-engine.ts | modified for() | ~173 |
| 13:51 | Session end: 13 writes across 7 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 47 reads | ~38283 tok |
| 13:51 | Created BertEngine service at src/services/bert-engine.ts | bert-engine.ts | TS type-check passes; lazy-load pipeline, attention-masked mean pooling, L2 norm, embedding cache, batch processing | ~3200 |
| 13:52 | Created tests/test_cosine_similarity.py | — | ~12116 |
| 13:53 | Edited tests/test_cosine_similarity.py | modified test_opposite_with_both_softmax_near_zero() | ~241 |
| 13:53 | Edited tests/test_cosine_similarity.py | modified test_diff_formula_symmetric() | ~312 |
| 13:53 | Edited src/types/bert.ts | 7→5 lines | ~42 |
| 13:53 | Edited src/services/bert-engine.ts | 2→1 lines | ~18 |
| 13:53 | Edited src/experiment_engine/text_calibration/cosine_similarity.py | 8→7 lines | ~120 |
| 13:54 | Edited src/experiment_engine/text_calibration/cosine_similarity.py | modified _normalize_rows() | ~125 |
| 13:54 | Edited src/services/bert-engine.ts | 3→2 lines | ~22 |
| 13:54 | Edited src/services/bert-engine.ts | modified if() | ~27 |
| 13:54 | Edited src/services/bert-engine.ts | inline fix | ~16 |
| 13:54 | Edited src/services/bert-engine.ts | 2→5 lines | ~81 |
| 13:54 | Edited src/services/bert-engine.ts | modified _truncateText() | ~38 |
| 13:54 | Edited src/types/bert.ts | 5→4 lines | ~33 |
| 13:54 | Session end: 26 writes across 8 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 48 reads | ~54674 tok |
| 13:55 | Edited src/experiment_engine/text_calibration/cosine_similarity.py | inline fix | ~13 |
| 13:55 | Edited src/experiment_engine/text_calibration/cosine_similarity.py | 4→3 lines | ~43 |
| 13:55 | Edited tests/test_cosine_similarity.py | inline fix | ~22 |
| 13:56 | Edited src/experiment_engine/text_calibration/cosine_similarity.py | 7→7 lines | ~88 |
| 13:59 | Edited src/experiment_engine/text_calibration/__init__.py | 7→10 lines | ~92 |
| 13:59 | Edited src/experiment_engine/text_calibration/__init__.py | 7→8 lines | ~63 |
| 14:04 | Session end: 32 writes across 9 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 50 reads | ~71865 tok |
| 14:21 | Edited src/experiment_engine/models/qca.py | modified ScoringSource() | ~159 |
| 14:21 | Edited src/experiment_engine/models/qca.py | modified ConditionDefinition() | ~379 |
| 14:21 | Edited src/experiment_engine/models/qca.py | 2→2 lines | ~31 |
| 14:22 | Edited src/types/qca.ts | "keyword" → "prototype" | ~12 |
| 14:22 | Edited src/types/qca.ts | 13→12 lines | ~102 |
| 14:22 | Edited src/i18n/translations.ts | expanded (+8 lines) | ~78 |
| 14:22 | Edited src/i18n/translations.ts | expanded (+8 lines) | ~88 |
| 14:22 | Edited src/i18n/translations.ts | expanded (+8 lines) | ~121 |
| 14:23 | Session end: 40 writes across 12 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 50 reads | ~72835 tok |
| 14:24 | Session end: 40 writes across 12 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 50 reads | ~78275 tok |
| 14:27 | Edited src/types/qca.ts | 4→3 lines | ~69 |
| 14:27 | Edited src/types/qca.ts | 7→4 lines | ~81 |
| 14:27 | Session end: 42 writes across 12 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 54 reads | ~90822 tok |
| 14:27 | Edited src/pages/DataInput.tsx | CSS: prototype_embeddings, embedding_model | ~177 |
| 14:27 | Edited src/pages/DataInput.tsx | CSS: prototype_embeddings, embedding_model | ~128 |
| 14:27 | Edited src/pages/DataInput.tsx | added optional chaining | ~134 |
| 14:27 | Edited src/pages/DataInput.tsx | added optional chaining | ~69 |
| 14:28 | Edited src/pages/DataInput.tsx | added optional chaining | ~273 |
| 14:28 | Edited src/pages/DataInput.tsx | CSS: FIXME-BERT | ~42 |
| 14:28 | Edited src/pages/DataInput.tsx | CSS: FIXME-BERT | ~55 |
| 14:28 | Edited src/pages/DataInput.tsx | CSS: FIXME-BERT | ~52 |
| 14:28 | Created src/i18n/translations.ts | — | ~8236 |
| 14:28 | Edited src/hooks/useQCAWorkflow.ts | 2→3 lines | ~42 |
| 14:28 | Edited src/hooks/useQCAWorkflow.ts | 2→3 lines | ~49 |
| 14:29 | Session end: 53 writes across 14 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 54 reads | ~100079 tok |
| 2026-05-25 | Removed 21 keyword-dict-specific strings from TranslationDict interface/zh/en (dataInput: importExportTitle, importCsvJson, exportCsv, exporting, importHelp, imported, kw, calibrationMode, importedDict, importedDictNoOutcome, dictImportError, exportDictError, noDictLoaded, exportedDict; settings: exportDictSection, exportDictHelp, exportDictNoConditionSet, exportDictBtn, exportDictExporting, exportDictError, exportedDict). Updated calibration_direction descriptions (zh: remove '关键词', en: 'keyword scores' -> 'raw scores'). Added bert_model setting field to zh/en translations. All tsc checks pass. | src/i18n/translations.ts, .wolf/anatomy.md | Clean removal, no TS errors | ~1000 |
| 14:30 | Session end: 53 writes across 14 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 54 reads | ~100079 tok |
| 15:29 | Session end: 53 writes across 14 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 54 reads | ~100079 tok |
| 15:49 | Session end: 53 writes across 14 files (TODO.md, experiment-engine-roadmap.json, package.json, bert.ts, bert-cache.ts) | 54 reads | ~100079 tok |

## Session: 2026-05-25 15:57

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 16:02 | Edited tests/test_keyword_io.py | modified test_basic_csv_import() | ~55 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_weight_validation() | ~35 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_duplicate_keyword_rejected() | ~37 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_missing_columns() | ~34 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_empty_values_rejected() | ~36 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_default_weight_when_missing() | ~38 |
| 16:02 | Edited tests/test_keyword_io.py | modified test_invalid_weight_string() | ~36 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_basic_json_import() | ~56 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_json_with_outcome() | ~35 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_duplicate_condition_name_rejected() | ~39 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_duplicate_keyword_in_condition_rejected() | ~41 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_weight_out_of_range_rejected() | ~38 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_missing_condition_name_rejected() | ~39 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_export_csv_roundtrip() | ~56 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_export_csv_includes_notes() | ~37 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_export_json_roundtrip() | ~57 |
| 16:03 | Edited tests/test_keyword_io.py | modified test_export_json_without_outcome() | ~38 |
| 16:04 | Edited src/experiment_engine/pyodide_handlers.py | modified handle_embed_calibrate() | ~1518 |
| 16:04 | Edited tests/test_integration.py | modified _make_valid_condition_set() | ~514 |
| 16:04 | Edited tests/test_qca_core.py | modified test_csqca_calibrator_forces_crisp_set() | ~787 |
| 16:04 | Edited tests/test_qca_core.py | modified test_load_from_conditions() | ~192 |
| 16:04 | Edited tests/test_prototype_similarity.py | modified test_keyword_mode_unchanged() | ~599 |
| 16:04 | Edited src/experiment_engine/pyodide_handlers.py | 6→8 lines | ~102 |
| 16:04 | Created src/experiment_engine/text_calibration/calibrator.py | — | ~4838 |
| 16:05 | Edited src/experiment_engine/pyodide_handlers.py | modified enumerate() | ~248 |
| 16:05 | Edited src/experiment_engine/pyodide_handlers.py | inline fix | ~20 |
| 16:05 | Edited src/experiment_engine/pyodide_handlers.py | inline fix | ~8 |
| 2026-05-25 | Added handle_embed_calibrate to pyodide_handlers.py — integrates CosineSimilarityEngine into Pyodide handler pipeline. Loads texts with pre-computed BERT embeddings + condition set JSON, builds condition_prototypes/prototype_embeddings dicts, computes raw cosine-similarity scores via engine, applies calibration via CalibrationStrategyRegistry, outputs MembershipData JSON. Handles edge cases: empty texts, missing prototype_embeddings, missing calibration_params. Ruff clean. | src/experiment_engine/pyodide_handlers.py | 131 lines added. Note: _condition_from_dict does not deserialize prototype_embeddings — handler extracts from raw JSON dict as workaround. | ~3000 |
| 16:06 | Session end: 27 writes across 6 files (test_keyword_io.py, pyodide_handlers.py, test_integration.py, test_qca_core.py, test_prototype_similarity.py) | 12 reads | ~43596 tok |
| 16:07 | Edited src/experiment_engine/text_calibration/condition.py | 19→19 lines | ~214 |
| 16:07 | Edited src/experiment_engine/text_calibration/condition.py | 13→10 lines | ~136 |
| 16:08 | Edited tests/test_prototype_similarity.py | modified test_prototype_calibration_produces_fuzzy_data() | ~1426 |
| 16:08 | Edited src/experiment_engine/text_calibration/condition.py | 13→10 lines | ~123 |
| 16:08 | Edited tests/test_prototype_similarity.py | modified test_prototype_calibration_with_outcome() | ~758 |
| 16:09 | Edited tests/test_prototype_similarity.py | modified test_prototype_calibration_without_embeddings_zeroes_scores() | ~522 |
| 16:09 | Edited tests/test_prototype_similarity.py | modified test_prototype_calibration_without_embeddings_zeroes_scores() | ~96 |
| 16:10 | Edited src/experiment_engine/text_calibration/condition.py | modified build() | ~23 |
| 16:11 | Edited src/experiment_engine/text_calibration/condition.py | modified _condition_from_dict() | ~30 |
| 16:11 | Phase 2: refactored calibrator.py — removed ChineseKeywordDictionary and PrototypeSimilarityEngine, integrated CosineSimilarityEngine, added text_embeddings/prototype_embeddings params to process/process_with_outcome/calibrate_one, rewrote _precompute_kw_context as _precompute_scores | src/experiment_engine/text_calibration/calibrator.py, tests/test_prototype_similarity.py | 513 passed, 21 skipped, 6 xfailed | ~3600 |
| 16:12 | Session end: 36 writes across 7 files (test_keyword_io.py, pyodide_handlers.py, test_integration.py, test_qca_core.py, test_prototype_similarity.py) | 12 reads | ~50310 tok |
| 16:13 | Session end: 36 writes across 7 files (test_keyword_io.py, pyodide_handlers.py, test_integration.py, test_qca_core.py, test_prototype_similarity.py) | 12 reads | ~50310 tok |
| 16:16 | Session end: 36 writes across 7 files (test_keyword_io.py, pyodide_handlers.py, test_integration.py, test_qca_core.py, test_prototype_similarity.py) | 13 reads | ~80937 tok |
| 16:24 | Session end: 36 writes across 7 files (test_keyword_io.py, pyodide_handlers.py, test_integration.py, test_qca_core.py, test_prototype_similarity.py) | 13 reads | ~80937 tok |

## Session: 2026-05-25 16:30

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 16:48 | Edited src/types/qca.ts | expanded (+21 lines) | ~991 |
| 16:48 | Edited src/services/pyodide.worker.ts | added 1 import(s) | ~46 |
| 16:48 | Edited src/services/pyodide.worker.ts | 4→5 lines | ~58 |
| 16:48 | Edited src/services/pyodide.worker.ts | expanded (+15 lines) | ~204 |
| 16:49 | Edited src/services/pyodide.worker.ts | added error handling | ~1054 |
| 16:49 | Edited src/services/pyodide.ts | 15→16 lines | ~102 |
| 16:49 | Edited src/services/pyodide.ts | modified initBert() | ~795 |
| 16:50 | Edited src/types/qca.ts | 6→8 lines | ~182 |
| 16:50 | Edited src/types/qca.ts | 1→5 lines | ~89 |
| 16:55 | Phase 3 — Worker protocol extension for BERT+Prototype | src/types/qca.ts (+BERT msg types), src/services/pyodide.worker.ts (+5 BERT handlers), src/services/pyodide.ts (+5 bridge methods) | npm run build passes, 662 lines delta | ~1800 |
| 16:55 | Session end: 9 writes across 3 files (qca.ts, pyodide.worker.ts, pyodide.ts) | 11 reads | ~3521 tok |
| 16:55 | Edited src/types/qca.ts | 18→22 lines | ~127 |
| 16:56 | Edited src/types/qca.ts | expanded (+6 lines) | ~399 |
| 16:56 | Edited src/store/QCAPipelineContext.tsx | CSS: status, embeddings | ~268 |
| 16:56 | Edited src/store/QCAPipelineContext.tsx | added nullish coalescing | ~149 |
| 16:57 | Edited src/types/qca.ts | 4→5 lines | ~38 |
| 16:57 | Edited src/types/qca.ts | 3→4 lines | ~22 |
| 16:57 | Edited src/store/QCAPipelineContext.tsx | CSS: bertEmbeddingsReady | ~25 |
| 16:57 | Edited src/store/QCAPipelineContext.tsx | 4→9 lines | ~105 |
| 16:57 | Edited src/store/QCAPipelineContext.tsx | expanded (+26 lines) | ~362 |
| 16:57 | Edited src/store/QCAPipelineContext.tsx | CSS: setBertStatus | ~56 |
| 16:57 | Edited src/hooks/useQCAWorkflow.ts | 7→8 lines | ~56 |
| 16:57 | Edited src/hooks/useQCAWorkflow.ts | expanded (+9 lines) | ~104 |
| 16:58 | Edited src/hooks/useQCAWorkflow.ts | 16→21 lines | ~125 |
| 16:58 | Edited src/hooks/useQCAWorkflow.ts | added error handling | ~968 |
| 16:58 | Edited src/pages/DataInput.tsx | 8→10 lines | ~72 |
| 16:58 | Edited src/pages/DataInput.tsx | 2→6 lines | ~99 |
| 16:58 | Edited src/pages/DataInput.tsx | added 1 condition(s) | ~650 |
| 16:59 | Edited src/pages/DataInput.tsx | inline fix | ~27 |
| 16:59 | Edited src/experiment_engine/models/qca.py | modified ScoringSource() | ~88 |
| 16:59 | Edited src/pages/DataInput.tsx | modified t() | ~965 |
| 16:59 | Edited src/types/index.ts | 2→1 lines | ~7 |
| 16:59 | Edited src/experiment_engine/text_calibration/__init__.py | removed 14 lines | ~17 |
| 16:59 | Edited src/experiment_engine/models/__init__.py | 3→2 lines | ~21 |
| 16:59 | Edited src/pages/Settings.tsx | modified t() | ~796 |
| 16:59 | Edited src/types/qca.ts | removed 7 lines | ~10 |
| 17:00 | Edited src/experiment_engine/text_calibration/__init__.py | reduced (-7 lines) | ~130 |
| 17:00 | Edited src/experiment_engine/models/__init__.py | 2→1 lines | ~6 |
| 17:00 | Edited src/experiment_engine/pyodide_handlers.py | removed 87 lines | ~6 |
| 17:00 | Edited src/services/pyodide.worker.ts | reduced (-11 lines) | ~38 |
| 17:00 | Edited src/services/pyodide.worker.ts | removed 47 lines | ~23 |
| 17:00 | Edited src/services/pyodide.ts | removed 51 lines | ~22 |
| 17:00 | Edited src/pyodide/engine.ts | 2→1 lines | ~23 |
| 17:00 | Edited src/experiment_engine/text_calibration/training.py | expanded (+11 lines) | ~378 |
| 17:01 | Edited src/experiment_engine/text_calibration/training.py | 6→5 lines | ~63 |
| 17:01 | Edited src/experiment_engine/text_calibration/training.py | modified _compute_raw_scores() | ~208 |
| 17:01 | Edited src/types/qca.ts | removed 3 lines | ~7 |
| 17:01 | Edited src/types/qca.ts | removed 5 lines | ~10 |
| 17:01 | Edited src/i18n/translations.ts | expanded (+15 lines) | ~145 |
| 17:02 | Edited src/i18n/translations.ts | expanded (+15 lines) | ~171 |
| 17:02 | Edited src/i18n/translations.ts | expanded (+15 lines) | ~241 |
| 17:03 | Edited src/pages/Settings.tsx | 4→4 lines | ~63 |
| 17:03 | Edited src/experiment_engine/models/__init__.py | 2→3 lines | ~39 |
| 17:03 | Edited src/experiment_engine/models/__init__.py | 4→5 lines | ~40 |
| 17:03 | Edited src/pages/Settings.tsx | 2→2 lines | ~47 |
| 17:04 | Edited src/i18n/translations.ts | 4→7 lines | ~36 |
| 17:04 | Edited src/hooks/useQCAWorkflow.ts | removed 26 lines | ~10 |
| 17:04 | Edited src/hooks/useQCAWorkflow.ts | 5→3 lines | ~19 |
| 17:04 | Edited src/i18n/translations.ts | 2→5 lines | ~37 |
| 17:04 | Edited src/i18n/translations.ts | 2→5 lines | ~50 |
| 17:04 | Edited src/hooks/useQCAWorkflow.ts | removed 20 lines | ~34 |
| 17:05 | Edited src/hooks/useQCAWorkflow.ts | expanded (+16 lines) | ~184 |
| 17:07 | Edited src/hooks/useQCAWorkflow.ts | modified useCallback() | ~229 |
| 17:08 | Edited src/hooks/useQCAWorkflow.ts | added 1 import(s) | ~41 |
| 17:10 | Edited src/pages/DataInput.tsx | 8→5 lines | ~27 |
| 17:12 | Session end: 63 writes across 14 files (qca.ts, pyodide.worker.ts, pyodide.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts) | 24 reads | ~50801 tok |
| 17:14 | Edited src/hooks/useQCAWorkflow.ts | removed 28 lines | ~6 |
| 17:14 | Edited src/hooks/useQCAWorkflow.ts | 4→2 lines | ~12 |
| 17:14 | Edited src/pages/DataInput.tsx | — | ~0 |
| 17:14 | Edited src/pages/Settings.tsx | — | ~0 |
| 17:15 | Edited src/pages/Settings.tsx | 3→2 lines | ~32 |
| 17:17 | Fix Phase 4/5 merge conflict: removed dangling importKeywords/exportKeywords from useQCAWorkflow.ts (callbacks + return obj), removed FIXME-BERT keyword import/export section from DataInput.tsx, removed Export Keyword Dictionary UI + unused useQCAWorkflow import from Settings.tsx | useQCAWorkflow.ts, DataInput.tsx, Settings.tsx | npm build passes | ~2000 |
| 17:20 | Edited src/experiment_engine/text_calibration/condition.py | inline fix | ~16 |
| 17:39 | Edited src/services/pyodide.ts | expanded (+6 lines) | ~143 |
| 17:41 | Edited src/hooks/useQCAWorkflow.ts | reduced (-11 lines) | ~20 |
| 17:41 | Edited src/hooks/useQCAWorkflow.ts | removed 17 lines | ~11 |
| 17:41 | Edited src/hooks/useQCAWorkflow.ts | removed 26 lines | ~10 |
| 17:42 | Session end: 73 writes across 15 files (qca.ts, pyodide.worker.ts, pyodide.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts) | 33 reads | ~69138 tok |
| 17:42 | Edited src/hooks/useQCAWorkflow.ts | 4→2 lines | ~12 |
| 17:43 | Edited src/pages/DataInput.tsx | CSS: sum, c | ~45 |
| 17:44 | Fixed remaining TS build errors: added explicit types to reduce() callback params in DataInput.tsx line 426 | src/pages/DataInput.tsx | build passes (31s, 0 errors) | ~50 |
| 17:45 | Phase 5: Cleanup old keyword code — deleted keyword_dict.py, keyword_io.py, prototype_similarity.py + tests. Removed KEYWORD/HYBRID from ScoringSource. Updated calibrator/similarity to PROTOTYPE-only. Cleaned pyodide handlers, worker, bridge, hook, and UI of keyword methods. Build passes, 515 tests pass. | src/experiment_engine/text_calibration/*, src/experiment_engine/models/qca.py, src/types/qca.ts, src/services/*.ts, src/hooks/useQCAWorkflow.ts, src/pages/{DataInput,Settings}.tsx, tests/* | 26 files, +2425/-675 | ~1200 tok |
| 17:46 | Session end: 75 writes across 15 files (qca.ts, pyodide.worker.ts, pyodide.ts, QCAPipelineContext.tsx, useQCAWorkflow.ts) | 33 reads | ~70957 tok |
