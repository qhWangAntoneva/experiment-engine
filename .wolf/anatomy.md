# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-24T18:53:00.644Z
> Files: 17 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/plans/


## ./

- `TODO.md` — TODO — QCA Analysis Tool (~3153 tok)

## .claude/


## .claude/rules/


## .claude/worktrees/agent-a182dd20ad100bc90/


## .claude/worktrees/agent-a182dd20ad100bc90/.wolf/


## .github/workflows/


## .wolf/


## roadmap/


## src/


## src/components/

- `PipelineStatus.tsx` — Pipeline Status Indicator — shows current stage, progress bar, elapsed time, (~1316 tok)

## src/experiment_engine/

- `cli.py` — QCA Text Analysis CLI — complete QCA workflow commands. --variant option for fsqca/csqca. (~7294 tok)
- `pyodide_handlers.py` — handle_calibrate, handle_calibrate_prototype, handle_analyze, handle_robustness (~5593 tok)

## src/experiment_engine/algorithms/


## src/experiment_engine/core/


## src/experiment_engine/io/


## src/experiment_engine/models/

- `qca.py` — QCA domain models — text analysis, calibration, truth tables, solutions, etc. (~5429 tok)

## src/experiment_engine/qca_engine/

- `truth_table.py` — QCA Truth Table construction from fuzzy-set data. Crisp-set compatible. (~1473 tok)

## src/experiment_engine/qca_engine/advanced/


## src/experiment_engine/report/


## src/experiment_engine/text_calibration/

- `__init__.py` — Text calibration layer: raw text → fuzzy-set membership scores. Exports CrispCalibration. (~447 tok)
- `calibrator.py` — Text calibration stage: keyword scores → fuzzy-set membership (0-1). (~4683 tok)
- `strategies.py` — Calibration strategy pattern. CrispCalibration handles descending direction. (~3552 tok)

## src/experiment_engine/viz/


## src/hooks/

- `useQCAWorkflow.ts` — Hook: Pyodide bridge to pipeline context. Includes prototype analysis workflow. (~3702 tok)

## src/layouts/


## src/pages/

- `DataInput.tsx` — Data Input — text corpus upload + condition set YAML editor. (~12003 tok)
- `Results.css` — Styles for Results page + prototype contrast comparison view (~1362 tok)
- `Results.tsx` — Results — QCA analysis output + raw/prototype contrast view with side-by-side comparison (~11309 tok)
- `Settings.tsx` — Settings — QCA analysis parameters, calibration defaults, and engine config. (~4949 tok)

## src/pyodide/


## src/services/


## src/store/

- `QCAPipelineContext.tsx` — React Context for tracking the QCA pipeline lifecycle. Supports prototype analysis stages. (~3023 tok)

## src/types/

- `qca.ts` — QCA-specific TypeScript interfaces. Includes prototype analysis stage + result fields. (~3525 tok)

## tests/

- `test_qca_core.py` — Unit tests for QCA core modules + CrispCalibration + csQCA integration. (~19224 tok)

## tmp/
