# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-24T17:18:46.414Z
> Files: 9 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/plans/


## ./


## .claude/


## .claude/rules/


## .claude/worktrees/agent-a182dd20ad100bc90/


## .claude/worktrees/agent-a182dd20ad100bc90/.wolf/


## .github/workflows/


## .wolf/


## roadmap/


## src/


## src/components/


## src/experiment_engine/

- `cli.py` — QCA Text Analysis CLI — complete QCA workflow commands. --variant option for fsqca/csqca. (~7294 tok)

## src/experiment_engine/algorithms/


## src/experiment_engine/core/


## src/experiment_engine/io/


## src/experiment_engine/models/


## src/experiment_engine/qca_engine/

- `truth_table.py` — QCA Truth Table construction from fuzzy-set data. Crisp-set compatible. (~1473 tok)

## src/experiment_engine/qca_engine/advanced/


## src/experiment_engine/report/


## src/experiment_engine/text_calibration/

- `__init__.py` — Text calibration layer: raw text → fuzzy-set membership scores. Exports CrispCalibration. (~447 tok)
- `calibrator.py` — Text calibration stage: keyword scores → fuzzy-set membership (0-1). csQCA-aware forces CRISP_SET. (~4721 tok)
- `strategies.py` — Calibration strategy pattern. CrispCalibration handles descending direction. (~3552 tok)

## src/experiment_engine/viz/


## src/hooks/

- `useQCAWorkflow.ts` — Hook that ties the Pyodide bridge to the pipeline state context. (~3456 tok)

## src/layouts/


## src/pages/

- `DataInput.tsx` — Data Input — text corpus upload + condition set YAML editor. (~13245 tok)
- `Settings.tsx` — Settings — QCA analysis parameters, calibration defaults, and engine config. (~4949 tok)

## src/pyodide/


## src/services/


## src/store/


## src/types/


## tests/

- `test_qca_core.py` — Unit tests for QCA core modules + CrispCalibration + csQCA integration. (~19224 tok)

## tmp/
