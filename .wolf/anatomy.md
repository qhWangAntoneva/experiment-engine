# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-27T10:45:44.322Z
> Files: 11 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/plans/


## ./


## .github/workflows/


## scripts/

- `prototype_usage_samples.py` — Declares Usage (~9941 tok)

## src/components/


## src/experiment_engine/

- `pyodide_handlers.py` — handle_calibrate, handle_calibrate_prototype, handle_analyze, handle_robustness (~9342 tok)

## src/experiment_engine/text_calibration/

- `calibrator.py` — Text calibration stage: BERT prototype scores → fuzzy-set membership (0-1). (~5872 tok)

## src/hooks/

- `useQCAWorkflow.ts` — Hook that ties the Pyodide bridge to the pipeline state context. (~5344 tok)

## src/i18n/

- `translations.ts` — i18n translations: Chinese (zh) and English (en). (~14169 tok)

## src/pages/

- `DataInput.tsx` — Data Input — text corpus upload + condition set YAML editor. (~16042 tok)

## src/services/

- `pyodide.ts` — Main-thread Pyodide bridge — methods called from React components. (~4762 tok)
- `pyodide.worker.ts` — Pyodide Web Worker — runs Python/NumPy in a background thread so the (~9630 tok)

## src/types/

- `qca.ts` — QCA-specific TypeScript interfaces mirroring experiment_engine/models.py. (~5176 tok)

## src/utils/


## tests/

- `test_qca_core.py` — Unit tests for QCA core modules. (~16198 tok)

## tmp/

- `prototype_usage_samples.py` — 3 prototype usage samples (CSV + ConditionSet dict + validation) for testing prototype-based calibration paths (~9663 tok)
