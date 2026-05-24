# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-24T17:01:59.142Z
> Files: 16 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/plans/


## ./

- `FIXME.md` — FIXME — QCA Analysis Tool (~4063 tok)
- `HACK.md` — HACK — QCA Analysis Tool (~2331 tok)
- `TODO.md` — TODO — QCA Analysis Tool (~3310 tok)

## .claude/


## .claude/rules/


## .claude/worktrees/agent-a182dd20ad100bc90/


## .claude/worktrees/agent-a182dd20ad100bc90/.wolf/


## .github/workflows/


## .wolf/


## roadmap/


## src/


## src/components/

- `DistributionPlot.tsx` — Distribution histogram for fuzzy-set membership scores. (~900 tok)

## src/experiment_engine/

- `__init__.py` — QCA Text Analysis Tool — citizen feedback text → fuzzy-set QCA analysis. (~478 tok)

## src/experiment_engine/algorithms/


## src/experiment_engine/core/


## src/experiment_engine/io/


## src/experiment_engine/models/

- `__init__.py` — QCA Text Analysis Tool — data models. (~713 tok)
- `qca.py` — QCA domain models — text analysis, calibration, truth tables, solutions, etc. (~5332 tok)

## src/experiment_engine/qca_engine/


## src/experiment_engine/qca_engine/advanced/


## src/experiment_engine/report/


## src/experiment_engine/text_calibration/

- `calibrator.py` — Text calibration stage: keyword scores → fuzzy-set membership (0-1). (~4434 tok)
- `strategies.py` — Calibration strategy pattern — pluggable membership calibration algorithms. (~3298 tok)

## src/experiment_engine/viz/


## src/hooks/


## src/layouts/


## src/pages/

- `DataInput.tsx` — Data Input — text corpus upload + condition set YAML editor. (~12882 tok)

## src/pyodide/

- `engine.ts` — jsdelivr CDN URL for Pyodide full build (stdlib + numpy + common pkgs). (~3693 tok)

## src/services/

- `pyodide.ts` — Main-thread Pyodide bridge — methods called from React components. (~3838 tok)

## src/store/

- `QCAPipelineContext.tsx` — React Context for tracking the QCA pipeline lifecycle. (~2440 tok)

## src/types/

- `index.ts` — Legacy types — kept for backward compatibility with existing UI components. (~416 tok)
- `qca.ts` — QCA-specific TypeScript interfaces mirroring experiment_engine/models.py. (~3190 tok)

## tests/

- `test_qca_core.py` — Unit tests for QCA core modules. (~14767 tok)

## tmp/
