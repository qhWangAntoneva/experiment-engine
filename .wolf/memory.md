# Memory

> Active sessions: most recent 2. Older sessions (before 2026-05-26 19:10) archived to `memory-archive.md`.

| 2026-05-26 | P1-5 + P1-10: CaseMembershipTable (sort/search/filter/expand, color-coded) + CalibrationPreview (Plotly dual histogram, JS calibration, i18n). P2-20: configurable steepness. P2-22: --variant for train/robustness CLI. P1-8 + P1-9: Privacy section + Clear Data + Recent Runs from localStorage. P1-B7/B8 plan designed. Handover updated. | CalibrationPreview.tsx, CaseMembershipTable.tsx, Results.tsx/Results.css, Settings.tsx/Settings.css, Dashboard.tsx/Dashboard.css, QCAPipelineContext.tsx, cli.py, strategies.py, qca.py, qca.ts, translations.ts | 532 tests pass, build clean | ~25000 |
| 2026-05-26 | Cleaned up .wolf/HANDOVER.md: removed outdated session-specific content, handover framing, commit history, subagent workflow docs. Updated HEAD ref to 60fa11e, refreshed untracked files list. Retained architecture summary, active issues, verification commands, TODO status. | .wolf/HANDOVER.md | n/a | ~200 |
| 2026-05-26 | Design QC: screenshots for all routes captured. Default language finalized as English (detectLanguage always 'en', index.html lang="en"). FIXME.md + HACK.md cleaned (removed resolved/moot entries). Memory contextual optimization: old sessions archived to memory-archive.md. | translations.ts, index.html, FIXME.md, HACK.md, memory.md, memory-archive.md, cerebrum.md | context budget reduced | ~5000 |

> Chronological action log.

## Session: 2026-05-26 19:10

- P1-10: CalibrationPreview component with Plotly dual histogram + JS calibration + i18n keys (zh+en). Integrated into Settings page.
- P1-5: CaseMembershipTable with sort/search/filter/expand + color-coded membership scores. Integrated Cases tab into Results page.
- P2-20: Added steepness field to CalibrationParams, updated IndirectCalibration, TS interface, test (532 pass)
- P2-22: Added --variant flag to train and robustness CLI commands
- P1-8 + P1-9: Privacy section + Clear Data button, Recent Runs from localStorage, run persistence in QCAPipelineContext
- Reviewer found 2 bugs in CaseMembershipTable (hardcoded string "no text", missing i18n key) -- fixed
- TODO.md stats updated (P1-5/8/9/10, P2-20/22 marked done)
- P1-B7/B8 plan designed by Plan agent for next session
- Handover updated
| ~15000 tok |

## Session: 2026-05-26 20:11

- Design QC: captured screenshots of all routes (/, /Dashboard, /DataInput, /Results, /Settings) -- 2 runs
- i18n language switcher confirmed working; language toggle tested (zh<->en)
- Default language finalized as English: detectLanguage() always returns 'en', index.html lang="en"
- FIXME.md cleaned: removed 20 resolved + 5 MOOT entries, kept FIXME-28 and FIXME-32
- HACK.md cleaned: removed 10 resolved entries, kept 8 active, trimmed descriptions
- Memory contextual optimization: archived old session logs to memory-archive.md
| ~5000 tok |
| 20:29 | Session end: 6 writes across 4 files (translations.ts, index.html, FIXME.md, HACK.md) | 10 reads | ~15898 tok |
| 20:30 | Created TODO.md | — | ~1757 |
| 20:31 | Cleaned TODO.md: collapsed P0-BERT to summary, removed commit hashes from all done items, removed fsQCA/csQCA requirement table, removed deprecated P1-34, updated 推进顺序 to reflect current state. File went from ~3300→~2200 tokens (-33%). Stats verified: P0=0, P1=7, P2=21. | TODO.md | done | ~2200 |
| 20:31 | Session end: 7 writes across 5 files (translations.ts, index.html, FIXME.md, HACK.md, TODO.md) | 10 reads | ~17780 tok |
| 20:32 | 5 agent 并行清理过时文档: memory.md (-95%), FIXME.md (-83%), HACK.md (-66%), HANDOVER.md (-38%), TODO.md (-31%) | HANDOVER.md, TODO.md, memory.md, FIXME.md, HACK.md, memory-archive.md | 全部完成 | ~3000 |
| 20:32 | Session end: 7 writes across 5 files (translations.ts, index.html, FIXME.md, HACK.md, TODO.md) | 10 reads | ~17780 tok |
| 20:36 | Session end: 7 writes across 5 files (translations.ts, index.html, FIXME.md, HACK.md, TODO.md) | 10 reads | ~17780 tok |
| 20:37 | Session end: 7 writes across 5 files (translations.ts, index.html, FIXME.md, HACK.md, TODO.md) | 10 reads | ~17780 tok |

## Session: 2026-05-26 20:37

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 12:50 | Fixed pre-commit end-of-file-fixer stash-conflict loop: .wolf/hooks/pre-commit.js now runs `pre-commit run --all-files` (all 8 hooks) instead of just ruff | .wolf/hooks/pre-commit.js, .wolf/cerebrum.md, .wolf/buglog.json | Bug-270 logged, cerebrum.md Do-Not-Repeat entry updated | ~250 |
| 21:37 | Edited src/services/bert-engine.ts | expanded (+7 lines) | ~222 |
| 21:37 | Edited src/services/bert-engine.ts | expanded (+11 lines) | ~108 |
| 21:37 | Edited src/services/bert-engine.ts | expanded (+9 lines) | ~128 |
| 21:37 | Edited src/services/bert-engine.ts | modified getModelName() | ~186 |
| 21:37 | Edited src/services/bert-engine.ts | 3→4 lines | ~47 |
| 21:38 | Edited src/services/bert-engine.ts | modified if() | ~694 |
| 21:39 | P1-B7 + P1-B8 Phase 1: added AVAILABLE_MODELS list and PerformanceMetrics instrumentation to BertEngine | src/services/bert-engine.ts | TS compiles clean, no errors | ~200 |
| 21:40 | Session end: 6 writes across 1 files (bert-engine.ts) | 15 reads | ~23582 tok |
| 21:40 | Edited src/hooks/useQCAWorkflow.ts | added error handling | ~152 |
| 21:40 | Edited src/hooks/useQCAWorkflow.ts | inline fix | ~18 |
| 21:40 | Edited src/hooks/useQCAWorkflow.ts | inline fix | ~18 |
| 21:41 | Edited src/pages/Settings.tsx | added 1 import(s) | ~49 |
| 21:41 | Edited src/pages/Settings.tsx | CSS: marginTop, color | ~196 |
| 21:41 | P1-B7 Steps 2/3/4: removed hardcoded BERT model name from useQCAWorkflow.ts, replaced with getBertModelFromSettings() dynamic lookup from localStorage | src/hooks/useQCAWorkflow.ts | tsc passes, 0 errors | ~15 |
| 21:41 | Edited src/types/qca.ts | 2→3 lines | ~43 |
| 21:41 | Edited src/store/QCAPipelineContext.tsx | added 1 import(s) | ~91 |
| 21:41 | Edited src/store/QCAPipelineContext.tsx | CSS: metrics | ~35 |
| 21:41 | Edited src/store/QCAPipelineContext.tsx | CSS: performanceMetrics | ~74 |
| 21:41 | Edited src/store/QCAPipelineContext.tsx | CSS: setPerformanceMetrics, metrics | ~28 |
| 21:41 | Edited src/store/QCAPipelineContext.tsx | CSS: setPerformanceMetrics, metrics, type | ~41 |
| 21:41 | Edited src/types/qca.ts | 2→3 lines | ~65 |
| 21:42 | Edited src/services/pyodide.ts | modified getBertStatus() | ~186 |
| 21:42 | Edited src/types/qca.ts | 5→8 lines | ~69 |
| 21:42 | Edited src/types/qca.ts | 2→3 lines | ~18 |
| 21:42 | Edited src/services/pyodide.worker.ts | added 1 condition(s) | ~162 |
| 21:42 | P1-B7 Step 5/6: Added 3rd BERT model option (distilbert) from AVAILABLE_MODELS, added localStorage save in onChange, added model-switch warning paragraph | src/pages/Settings.tsx | tsc clean | ~250 |
| 13:43 | P1-B8 Step 3: wired BERT performance metrics from Web Worker to PyodideBridge. Added get_bert_metrics request/response types, bridge method, and worker switch case. | src/types/qca.ts, src/services/pyodide.ts, src/services/pyodide.worker.ts | tsc --noEmit passes clean | ~800 |
| 21:44 | Session end: 22 writes across 7 files (bert-engine.ts, useQCAWorkflow.ts, Settings.tsx, qca.ts, QCAPipelineContext.tsx) | 15 reads | ~43947 tok |
| 21:44 | Edited src/i18n/translations.ts | 2→4 lines | ~33 |
| 21:45 | Edited src/i18n/translations.ts | expanded (+12 lines) | ~100 |
| 21:48 | Created src/components/PerformancePanel.tsx | — | ~1016 |
| 21:48 | Edited src/pages/Dashboard.tsx | added 1 import(s) | ~35 |
| 21:48 | Edited src/pages/Dashboard.tsx | 3→6 lines | ~58 |
| 21:49 | P1-B8 Steps 4/5: created PerformancePanel component with collapsible BERT metrics, integrated into Dashboard, added i18n keys | src/components/PerformancePanel.tsx, src/pages/Dashboard.tsx, src/i18n/translations.ts | tsc --noEmit passed with zero errors | ~200 |
| 21:50 | Added P1-B7/B8 i18n translations: bertModelSwitchWarning + bertModel in settings, new performance section (7 keys), verified tsc clean | src/i18n/translations.ts | tsc --noEmit passed, zero errors | ~80 |
| 21:55 | Session end: 27 writes across 10 files (bert-engine.ts, useQCAWorkflow.ts, Settings.tsx, qca.ts, QCAPipelineContext.tsx) | 18 reads | ~48318 tok |
| 21:58 | Edited src/services/bert-engine.ts | 2→2 lines | ~33 |
| 21:59 | Edited src/hooks/useQCAWorkflow.ts | added 1 import(s) | ~34 |
| 21:59 | Edited src/hooks/useQCAWorkflow.ts | modified getBertModelFromSettings() | ~48 |
| 22:00 | Session end: 30 writes across 10 files (bert-engine.ts, useQCAWorkflow.ts, Settings.tsx, qca.ts, QCAPipelineContext.tsx) | 18 reads | ~52260 tok |
| 22:04 | Edited src/pages/Settings.tsx | inline fix | ~22 |
| 22:04 | Edited src/pages/Settings.tsx | 2→2 lines | ~31 |

## Session: 2026-05-26 22:09

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 22:10 | Edited TODO.md | 2→2 lines | ~35 |
| 22:10 | Edited TODO.md | 7 → 5 | ~12 |
| 22:10 | Edited TODO.md | 8→7 lines | ~41 |
| 22:20 | P1-B7/B8 收尾: Settings.tsx 残留硬编码替换为 DEFAULT_MODEL, tsc --noEmit 通过, OpenWolf 文档更新 (TODO.md P1-B7/B8→done, stats 28→26, cerebrum.md 推荐顺序更新) | Settings.tsx, TODO.md, cerebrum.md, memory.md | tsc clean, all hardcoded strings eliminated | ~300 |
| 22:11 | Session end: 3 writes across 1 files (TODO.md) | 2 reads | ~8499 tok |

## Session: 2026-05-26 22:13

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 22:27 | Edited index.html | 1→5 lines | ~42 |
| 22:27 | Edited src/i18n/I18nContext.tsx | inline fix | ~14 |
| 22:27 | Edited src/i18n/translations.ts | — | ~0 |
| 22:27 | Edited src/i18n/I18nContext.tsx | CSS: DEFAULT_LANGUAGE | ~125 |
| 22:27 | Added inline script to index.html before </head> to force html lang=en before React loads | index.html | done | ~20 |
| 14:29 | Removed dead detectLanguage() from translations.ts; inlined DEFAULT_LANGUAGE = 'en' constant in I18nContext.tsx. npx tsc --noEmit passed clean. | src/i18n/I18nContext.tsx, src/i18n/translations.ts | Dead-code removal + inlined constant. | ~200 |
| 22:33 | Edited index.html | removed 5 lines | ~3 |
| 22:33 | Session end: 5 writes across 3 files (index.html, I18nContext.tsx, translations.ts) | 15 reads | ~29395 tok |
| 22:35 | Session end: 5 writes across 3 files (index.html, I18nContext.tsx, translations.ts) | 15 reads | ~29395 tok |
| 22:36 | Session end: 5 writes across 3 files (index.html, I18nContext.tsx, translations.ts) | 15 reads | ~29395 tok |
| 22:44 | Session end: 5 writes across 3 files (index.html, I18nContext.tsx, translations.ts) | 15 reads | ~29395 tok |
| 22:54 | Session end: 5 writes across 3 files (index.html, I18nContext.tsx, translations.ts) | 43 reads | ~1313 tok |
| 22:55 | Edited src/types/qca.ts | expanded (+39 lines) | ~345 |
| 22:55 | Edited src/types/index.ts | 2→6 lines | ~42 |
| 22:55 | Edited src/experiment_engine/pyodide_handlers.py | modified handle_multi_outcome() | ~338 |
| 22:56 | Edited src/types/qca.ts | expanded (+9 lines) | ~151 |
| 22:56 | Edited src/types/qca.ts | 3→5 lines | ~37 |
| 22:56 | Created src/experiment_engine/report/docx_reporter.py | — | ~3762 |
| 22:56 | Edited src/types/qca.ts | 5→9 lines | ~164 |
| 22:56 | Created src/services/project-serialization.ts | — | ~2934 |
| 22:56 | Edited src/experiment_engine/report/__init__.py | added 2 import(s) | ~184 |
| 22:56 | Edited src/types/qca.ts | 5→7 lines | ~54 |
| 22:56 | Edited src/types/qca.ts | 2→3 lines | ~54 |
| 22:56 | Edited src/store/QCAPipelineContext.tsx | 12→15 lines | ~109 |
| 22:56 | Edited src/types/qca.ts | 3→5 lines | ~82 |
| 22:56 | Edited src/types/qca.ts | 4→6 lines | ~86 |
| 22:56 | Edited src/store/QCAPipelineContext.tsx | expanded (+14 lines) | ~228 |
| 22:56 | Edited src/store/QCAPipelineContext.tsx | expanded (+27 lines) | ~280 |
| 22:56 | Edited src/experiment_engine/pyodide_handlers.py | expanded (+14 lines) | ~308 |
| 22:56 | Edited src/services/pyodide.worker.ts | 9→12 lines | ~98 |
| 22:57 | Edited src/store/QCAPipelineContext.tsx | expanded (+16 lines) | ~569 |
| 22:57 | Edited src/services/pyodide.worker.ts | added error handling | ~232 |
| 22:57 | Edited src/services/pyodide.ts | 16→17 lines | ~108 |
| 22:57 | Edited src/store/QCAPipelineContext.tsx | added error handling | ~902 |
| 22:57 | Edited src/services/pyodide.ts | modified runMultiOutcome() | ~236 |
| 22:57 | Edited src/types/qca.ts | expanded (+6 lines) | ~122 |
| 22:57 | Edited src/types/qca.ts | 5→9 lines | ~54 |
| 22:57 | Created src/hooks/useProjectAutoSave.ts | — | ~747 |
| 22:57 | Edited src/store/QCAPipelineContext.tsx | 13→14 lines | ~82 |
| 22:57 | Edited src/types/qca.ts | inline fix | ~34 |
| 22:58 | Edited src/store/QCAPipelineContext.tsx | CSS: result | ~76 |
| 22:58 | Edited src/i18n/translations.ts | expanded (+20 lines) | ~239 |
| 22:58 | Edited src/store/QCAPipelineContext.tsx | CSS: analysisResultB, multiOutcomeReport | ~94 |
| 22:58 | Edited src/types/qca.ts | inline fix | ~21 |
| 22:58 | Edited src/store/QCAPipelineContext.tsx | 3→7 lines | ~107 |
| 22:58 | Edited src/i18n/translations.ts | expanded (+19 lines) | ~260 |
| 22:58 | Edited src/store/QCAPipelineContext.tsx | CSS: result | ~368 |
| 22:58 | Edited src/i18n/translations.ts | expanded (+19 lines) | ~376 |
| 22:58 | Edited src/services/pyodide.worker.ts | added 3 condition(s) | ~453 |
| 22:58 | Edited src/store/QCAPipelineContext.tsx | 3→7 lines | ~58 |
| 22:58 | Edited src/store/QCAPipelineContext.tsx | CSS: analysisResultB, multiOutcomeReport | ~156 |
| 22:58 | Edited src/services/pyodide.ts | modified exportResult() | ~199 |
| 22:58 | Edited src/hooks/useQCAWorkflow.ts | modified useCallback() | ~31 |
| 22:58 | Edited src/hooks/useQCAWorkflow.ts | 2→2 lines | ~31 |
| 22:58 | Edited src/store/QCAPipelineContext.tsx | CSS: analysisResultB, multiOutcomeReport | ~173 |
| 22:59 | Edited src/pages/Results.tsx | modified catch() | ~248 |
| 22:59 | Edited src/store/QCAPipelineContext.tsx | CSS: analysisResultB, multiOutcomeReport | ~223 |
| 22:59 | Edited src/pages/Results.tsx | expanded (+8 lines) | ~157 |
| 22:59 | Edited src/store/QCAPipelineContext.tsx | CSS: analysisResultB, multiOutcomeReport | ~161 |
| 22:59 | Edited src/i18n/translations.ts | 3→4 lines | ~34 |
| 22:59 | Edited src/i18n/translations.ts | 1→2 lines | ~18 |
| 22:59 | Edited src/hooks/useQCAWorkflow.ts | expanded (+10 lines) | ~182 |
| 22:59 | Created src/pages/Dashboard.tsx | — | ~6746 |
| 22:59 | Edited src/i18n/translations.ts | 1→2 lines | ~16 |
| 23:00 | Edited src/hooks/useQCAWorkflow.ts | 4→8 lines | ~61 |
| 23:00 | Edited src/hooks/useQCAWorkflow.ts | added error handling | ~1254 |
| 23:00 | Edited src/pages/DataInput.tsx | 9→10 lines | ~54 |
| 23:00 | Edited src/hooks/useQCAWorkflow.ts | 8→10 lines | ~75 |
| 23:00 | Edited src/pages/DataInput.tsx | modified newProtoRow() | ~44 |
| 23:00 | Edited src/pages/DataInput.tsx | inline fix | ~8 |
| 23:00 | Edited src/pages/DataInput.tsx | CSS: setTextCases, setYamlContent, setProtoConditions | ~104 |
| 23:00 | Edited src/hooks/useQCAWorkflow.ts | 4→5 lines | ~31 |
| 23:01 | Edited src/pages/DataInput.tsx | 17→16 lines | ~203 |
| 23:01 | Edited src/pages/DataInput.tsx | inline fix | ~4 |
| 23:01 | Edited src/pages/DataInput.tsx | inline fix | ~7 |
| 23:01 | Edited src/i18n/translations.ts | expanded (+11 lines) | ~114 |
| 23:01 | Edited src/pages/DataInput.tsx | inline fix | ~6 |
| 23:01 | Edited src/pages/DataInput.tsx | inline fix | ~8 |
| 23:02 | Edited src/experiment_engine/report/docx_reporter.py | modified _set_run_font() | ~222 |
| 23:02 | Session end: 72 writes across 17 files (index.html, I18nContext.tsx, translations.ts, qca.ts, index.ts) | 44 reads | ~73875 tok |
| 15:02 | P1-6: Project Save & Restore implemented (8 steps: types, serialization, context hydration, auto-save hook, Dashboard UI, i18n, text corpus wire-up, clear data) | src/types/qca.ts, src/services/project-serialization.ts, src/store/QCAPipelineContext.tsx, src/hooks/useProjectAutoSave.ts, src/pages/Dashboard.tsx, src/pages/DataInput.tsx, src/i18n/translations.ts, src/types/index.ts | tsc --noEmit clean, all 8 steps complete | ~3000 |
| 23:03 | Edited src/experiment_engine/report/docx_reporter.py | 8→4 lines | ~10 |
| 23:04 | Session end: 73 writes across 17 files (index.html, I18nContext.tsx, translations.ts, qca.ts, index.ts) | 44 reads | ~73871 tok |
| 23:04 | P1-11: implemented Chinese Word .docx report export (QCADocxReporter + full TS integration) | docx_reporter.py, __init__.py, pyodide_handlers.py, pyodide.worker.ts, pyodide.ts, useQCAWorkflow.ts, Results.tsx, translations.ts, qca.ts | ruff clean, tsc --noEmit clean | ~350 |
| 23:05 | Edited src/types/qca.ts | expanded (+31 lines) | ~322 |
| 23:05 | Session end: 74 writes across 17 files (index.html, I18nContext.tsx, translations.ts, qca.ts, index.ts) | 45 reads | ~110127 tok |
| 23:06 | Created src/utils/snapshotStorage.ts | — | ~706 |
| 23:06 | Edited src/store/QCAPipelineContext.tsx | inline fix | ~25 |
| 23:06 | Edited src/store/QCAPipelineContext.tsx | added 1 import(s) | ~143 |
| 23:06 | Edited src/store/QCAPipelineContext.tsx | added error handling | ~424 |
| 23:07 | Edited src/hooks/useQCAWorkflow.ts | 9→10 lines | ~93 |
| 23:07 | Edited src/hooks/useQCAWorkflow.ts | 5→6 lines | ~68 |
| 23:07 | Edited src/hooks/useQCAWorkflow.ts | modified if() | ~346 |
| 23:07 | Edited src/hooks/useQCAWorkflow.ts | 9→10 lines | ~90 |
| 23:07 | Edited src/types/qca.ts | expanded (+14 lines) | ~134 |
| 23:07 | Edited src/types/index.ts | 2→3 lines | ~18 |
| 23:07 | Created src/services/templateService.ts | — | ~5590 |
| 23:07 | Edited src/hooks/useQCAWorkflow.ts | 5→5 lines | ~60 |
| 23:08 | Edited src/i18n/translations.ts | expanded (+28 lines) | ~228 |
| 23:08 | Created src/components/TemplateLibrary.tsx | — | ~1490 |
| 23:08 | Created src/components/TemplateLibrary.css | — | ~704 |
| 23:08 | Created src/components/CompareView.tsx | — | ~3924 |
| 23:08 | Edited src/pages/Results.tsx | expanded (+9 lines) | ~298 |
| 23:09 | Created src/components/ShareLinkButton.tsx | — | ~803 |
| 23:09 | Created src/components/ShareImportModal.tsx | — | ~2046 |
| 23:09 | Edited src/pages/Results.tsx | added error handling | ~347 |
| 23:09 | Edited src/pages/Results.tsx | expanded (+30 lines) | ~370 |
| 23:09 | Edited src/i18n/translations.ts | expanded (+27 lines) | ~233 |
| 23:09 | Edited src/i18n/translations.ts | expanded (+27 lines) | ~333 |
| 23:10 | Edited src/pages/Dashboard.tsx | added 2 import(s) | ~123 |
| 23:10 | Edited src/pages/Dashboard.tsx | 4→7 lines | ~46 |
| 23:10 | Edited src/pages/Dashboard.tsx | 10→13 lines | ~132 |
| 23:10 | Edited src/pages/Results.tsx | removed 349 lines | ~23 |
| 23:10 | Edited src/pages/DataInput.tsx | added 1 import(s) | ~52 |
| 23:10 | Edited src/pages/DataInput.tsx | 8→9 lines | ~109 |
| 23:11 | Created src/components/ParamDiffTable.tsx | — | ~2341 |
| 23:11 | P1-13 implemented: templateService.ts, TemplateLibrary, ShareLinkButton, ShareImportModal, wired into Dashboard + DataInput, i18n keys added | src/services/templateService.ts src/types/qca.ts src/types/index.ts src/components/TemplateLibrary.tsx src/components/TemplateLibrary.css src/components/ShareLinkButton.tsx src/components/ShareImportModal.tsx src/i18n/translations.ts src/pages/Dashboard.tsx src/pages/DataInput.tsx | tsc --noEmit clean | ~1200 |
| 23:11 | Created src/pages/Compare.tsx | — | ~2986 |
| 23:12 | Session end: 105 writes across 26 files (index.html, I18nContext.tsx, translations.ts, qca.ts, index.ts) | 46 reads | ~140028 tok |
| 23:12 | Created src/pages/Compare.tsx | — | ~2730 |
| 23:12 | Created src/pages/Compare.css | — | ~355 |
| 23:12 | Edited src/App.tsx | added 1 import(s) | ~57 |
| 23:12 | Edited src/App.tsx | 2→3 lines | ~52 |
| 23:13 | Edited src/components/Sidebar.tsx | 6→7 lines | ~103 |
| 23:13 | Edited src/i18n/translations.ts | 11→12 lines | ~69 |
| 23:13 | Edited src/i18n/translations.ts | 3→5 lines | ~41 |
| 23:13 | Edited src/i18n/translations.ts | expanded (+33 lines) | ~229 |
| 23:14 | Edited src/i18n/translations.ts | 10→11 lines | ~68 |
| 23:14 | Edited src/i18n/translations.ts | 3→5 lines | ~48 |
| 23:14 | Edited src/i18n/translations.ts | expanded (+32 lines) | ~263 |
| 23:14 | Edited src/i18n/translations.ts | 10→11 lines | ~76 |
| 23:15 | Edited src/i18n/translations.ts | 6→8 lines | ~67 |
| 23:16 | Edited src/i18n/translations.ts | expanded (+32 lines) | ~398 |
| 23:17 | P1-7 implemented: Parameter Comparison (A/B Analysis). Created Compare.tsx, CompareView.tsx, ParamDiffTable.tsx, snapshotStorage.ts, Compare.css. Modified qca.ts (3 new interfaces), QCAPipelineContext.tsx (captureAsLabel), useQCAWorkflow.ts (captureAsLabel passthrough), Results.tsx (snapshot buttons + extracted compare components), App.tsx (route), Sidebar.tsx (nav), translations.ts (34 new i18n keys). tsc --noEmit passes. | 13 files | P1-7 complete | ~18000 |
| 23:21 | Edited src/i18n/translations.ts | expanded (+11 lines) | ~146 |
| 23:21 | Edited src/i18n/translations.ts | expanded (+11 lines) | ~213 |
| 23:21 | Edited src/pages/Dashboard.tsx | added nullish coalescing | ~204 |
| 23:21 | Edited src/pages/Dashboard.tsx | added nullish coalescing | ~188 |
| 23:22 | Edited src/pages/DataInput.tsx | 21→17 lines | ~200 |
| 23:22 | Edited src/pages/Results.tsx | modified if() | ~444 |
| 23:22 | Edited src/services/project-serialization.ts | added nullish coalescing | ~190 |
| 23:22 | Edited src/services/pyodide.ts | inline fix | ~21 |
| 23:23 | Edited src/services/project-serialization.ts | 2→3 lines | ~19 |
| 23:24 | Edited src/services/project-serialization.ts | 1→3 lines | ~45 |
| 23:24 | Edited src/hooks/useProjectAutoSave.ts | 10→12 lines | ~183 |
| 23:25 | Edited src/pages/Dashboard.tsx | CSS: analysisResultB, multiOutcomeReport | ~166 |
| 23:26 | Fixed all 20+ TypeScript compilation errors from P1 feature merge: added missing multiOutcome keys to translations.ts (zh/en), added analysisResultB/multiOutcomeReport to Dashboard.tsx object literals (3 locations), project-serialization.ts SerializeOpts interface and pipeline object, useProjectAutoSave.ts; replaced callback patterns with direct array ops in DataInput.tsx; reordered activeResult before use in Results.tsx; added BlobPart type assertion in pyodide.ts | translations.ts, Dashboard.tsx, DataInput.tsx, Results.tsx, project-serialization.ts, pyodide.ts, useProjectAutoSave.ts | tsc -b and npm run build pass with zero errors | ~1500 |
| 23:27 | Session end: 131 writes across 29 files (index.html, I18nContext.tsx, translations.ts, qca.ts, index.ts) | 50 reads | ~145427 tok |
| 23:32 | Session end: 131 writes across 29 files (index.html, I18nContext.tsx, translations.ts, qca.ts, index.ts) | 51 reads | ~146433 tok |
| 23:33 | Edited TODO.md | inline fix | ~10 |
| 23:33 | Edited TODO.md | 7→7 lines | ~120 |
| 23:33 | Edited TODO.md | 10→10 lines | ~160 |
| 23:33 | Updated TODO.md: marked remaining 5 P1 items done, updated stats to P0=0 P1=0 P2=21, reordered recommendation
| 23:34 | Updated HANDOVER.md: all P1 items (12/12) marked complete, HEAD updated to 7474dee, new files + modified files documented | .wolf/HANDOVER.md | written | ~150 |
