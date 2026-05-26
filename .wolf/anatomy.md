# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-26T16:18:42.770Z
> Files: 30 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/


## ../.claude/plans/


## ../National-Policy-Database/


## ./

- `TODO.md` — TODO — QCA Analysis Tool (~1764 tok)
- `validate_qca_output.py` — Validate all 5 domain QCA outputs and print summary. (~2738 tok)

## .claude/


## .claude/rules/


## .claude/worktrees/agent-a182dd20ad100bc90/


## .claude/worktrees/agent-a182dd20ad100bc90/.wolf/


## .github/workflows/


## .wolf/


## public/


## roadmap/


## src/

- `App.tsx` — App (~300 tok)

## src/components/

- `CompareView.tsx` — CompareView — shared comparison components for side-by-side QCA result comparison. (~3924 tok)
- `ParamDiffTable.tsx` — ParamDiffTable (P1-7) (~2341 tok)
- `ShareImportModal.tsx` — ShareImportModal — mounted on the Dashboard. On mount, checks for (~2046 tok)
- `ShareLinkButton.tsx` — ShareLinkButton — generates a shareable URL for the current ConditionSet (~803 tok)
- `Sidebar.tsx` — Sidebar (~475 tok)
- `TemplateLibrary.css` — Styles: 21 rules (~704 tok)
- `TemplateLibrary.tsx` — TemplateLibrary — displays built-in and imported QCA condition set (~1490 tok)

## src/experiment_engine/

- `pyodide_handlers.py` — handle_calibrate, handle_calibrate_prototype, handle_analyze, handle_robustness (~6894 tok)

## src/experiment_engine/algorithms/


## src/experiment_engine/core/


## src/experiment_engine/io/


## src/experiment_engine/models/


## src/experiment_engine/qca_engine/


## src/experiment_engine/qca_engine/advanced/


## src/experiment_engine/report/

- `__init__.py` — Report generation for experiment-engine pipelines. (~184 tok)
- `docx_reporter.py` — Chinese Word (.docx) report generation for QCA analysis results. (~3718 tok)

## src/experiment_engine/text_calibration/


## src/experiment_engine/viz/


## src/hooks/

- `useProjectAutoSave.ts` — useProjectAutoSave — automatically saves project state to localStorage (~783 tok)
- `useQCAWorkflow.ts` — Hook that ties the Pyodide bridge to the pipeline state context. (~5328 tok)

## src/i18n/

- `translations.ts` — i18n translations: Chinese (zh) and English (en). (~13589 tok)

## src/layouts/


## src/pages/

- `Compare.css` — Styles: 10 rules (~355 tok)
- `Compare.tsx` — Compare (P1-7) (~2730 tok)
- `Dashboard.tsx` — Dashboard — QCA pipeline overview with pipeline status widget, (~6932 tok)
- `DataInput.tsx` — Data Input — text corpus upload + condition set YAML editor. (~14020 tok)
- `Results.tsx` — Results — displays all QCA analysis output in organized sections: (~8083 tok)

## src/pyodide/


## src/services/

- `project-serialization.ts` — Project Serialization (P1-6) (~3008 tok)
- `pyodide.ts` — Main-thread Pyodide bridge — methods called from React components. (~4732 tok)
- `pyodide.worker.ts` — Pyodide Web Worker — runs Python/NumPy in a background thread so the (~7466 tok)
- `templateService.ts` — Condition Set Sharing & Team Templates (P1-13) (~5590 tok)

## src/store/

- `QCAPipelineContext.tsx` — React Context for tracking the QCA pipeline lifecycle. (~6186 tok)

## src/types/

- `index.ts` — Legacy types — kept for backward compatibility with existing UI components. (~450 tok)
- `qca.ts` — QCA-specific TypeScript interfaces mirroring experiment_engine/models.py. (~4711 tok)

## src/utils/

- `snapshotStorage.ts` — Snapshot Storage (P1-7) (~706 tok)

## tests/


## tests/fixtures/

- `sample_cases.csv` (~423 tok)

## tmp/
