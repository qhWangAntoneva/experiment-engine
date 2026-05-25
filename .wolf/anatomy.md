# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-25T10:46:57.920Z
> Files: 19 tracked | Anatomy hits: 0 | Misses: 0

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

- `pyodide_handlers.py` — handle_calibrate, handle_calibrate_prototype, handle_analyze, handle_robustness (~6266 tok)

## src/experiment_engine/algorithms/


## src/experiment_engine/core/


## src/experiment_engine/io/


## src/experiment_engine/models/

- `__init__.py` — QCA Text Analysis Tool — data models. (~738 tok)
- `qca.py` — QCA domain models — text analysis, calibration, truth tables, solutions, etc. (~5368 tok)

## src/experiment_engine/qca_engine/


## src/experiment_engine/qca_engine/advanced/


## src/experiment_engine/report/


## src/experiment_engine/text_calibration/

- `__init__.py` — Text calibration layer: raw text → fuzzy-set membership scores. (~368 tok)
- `condition.py` — Condition set I/O helpers — YAML serialization for QCA condition definitions. (~2415 tok)
- `training.py` — Training engine for fitting calibration parameters from labeled samples. (~2411 tok)

## src/experiment_engine/viz/


## src/hooks/

- `useQCAWorkflow.ts` — Hook that ties the Pyodide bridge to the pipeline state context. (~3749 tok)

## src/i18n/

- `translations.ts` — i18n translations: Chinese (zh) and English (en). (~8807 tok)

## src/layouts/


## src/pages/

- `DataInput.tsx` — Data Input — text corpus upload + condition set YAML editor. (~13680 tok)
- `Settings.tsx` — Settings — QCA analysis parameters, calibration defaults, and engine config. (~5929 tok)

## src/pyodide/

- `engine.ts` — jsdelivr CDN URL for Pyodide full build (stdlib + numpy + common pkgs). (~3669 tok)

## src/services/

- `bert-cache.ts` — BERT embedding cache service — IndexedDB persistence. (~288 tok)
- `bert-engine.ts` — BertEngine class — Transformers.js feature extraction. (~2432 tok)
- `pyodide.ts` — Main-thread Pyodide bridge — methods called from React components. (~4307 tok)
- `pyodide.worker.ts` — Pyodide Web Worker — runs Python/NumPy in a background thread so the (~5883 tok)

## src/store/

- `QCAPipelineContext.tsx` — React Context for tracking the QCA pipeline lifecycle. (~3090 tok)

## src/types/

- `bert.ts` — BERT engine types: status, embeddings, prototype maps, worker request/response interfaces. (~642 tok)
- `index.ts` — Legacy types — kept for backward compatibility with existing UI components. (~412 tok)
- `qca.ts` — QCA-specific TypeScript interfaces mirroring experiment_engine/models.py. (~3516 tok)

## tests/


## tmp/
