# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-26T08:16:43.267Z
> Files: 50 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/

- `CLAUDE.md` — Claude Code — 通用规则 (~198 tok)

## ../.claude/plans/


## ../National-Policy-Database/

- `CLAUDE.md` — National-Policy-Database — 项目规则 (~2972 tok)

## ./

- `.gitignore` — Git ignore rules (~177 tok)
- `DEPLOY-CHECKLIST.md` — Deployment Verification Checklist -- QCA Analysis Tool (~5095 tok)
- `FIXME.md` — FIXME — QCA Analysis Tool (~2800 tok, re-synced 2026-05-26)
- `HACK.md` — HACK — QCA Analysis Tool (re-synced 2026-05-26, ~1600 tok)
- `index.html` — QCA Simulation Tool (~563 tok)
- `package.json` — Node.js package manifest (~194 tok)
- `TODO.md` — TODO — QCA Analysis Tool (~3300 tok, updated 2026-05-26)
- `vite.config.ts` — ============================================================================= (~344 tok)

## .claude/


## .claude/rules/


## .claude/worktrees/agent-a182dd20ad100bc90/


## .claude/worktrees/agent-a182dd20ad100bc90/.wolf/


## .github/workflows/

- `deploy.yml` — ============================================================================== (~1806 tok)

## .wolf/

- `e2e-test-plan.md` — UX-focused E2E test plan: 45 tests across 6 phases, with PASS/FAIL criteria and execution order (~1200 tok)
- `memory-archive.md` — Archived session logs (pre-2026-05-25) — moved here to reduce context consumption (~27000 tok)

## public/

- `.nojekyll` (~0 tok)
- `404.html` — QCA Analysis Tool (~278 tok)

## roadmap/


## src/

- `main.tsx` — ============================================================================= (~725 tok)
- `vite-env.d.ts` — / <reference types="vite/client" /> (~296 tok)

## src/components/


## src/experiment_engine/

- `pyodide_handlers.py` — handle_calibrate, handle_calibrate_prototype, handle_analyze, handle_robustness (~6402 tok)

## src/experiment_engine/algorithms/


## src/experiment_engine/core/

- `__init__.py` — Core pipeline orchestration — re-exports from the existing pipeline module. (~375 tok)

## src/experiment_engine/io/

- `__init__.py` — Input/output layer for experiment-engine. (~658 tok)

## src/experiment_engine/models/

- `__init__.py` — QCA Text Analysis Tool — data models. (~738 tok)
- `qca.py` — QCA domain models — text analysis, calibration, truth tables, solutions, etc. (~5386 tok)

## src/experiment_engine/qca_engine/


## src/experiment_engine/qca_engine/advanced/

- `robustness.py` — Robustness and sensitivity tests for QCA results. (~4823 tok)

## src/experiment_engine/report/


## src/experiment_engine/text_calibration/

- `__init__.py` — Text calibration layer: raw text → fuzzy-set membership scores. (~368 tok)
- `condition.py` — Condition set I/O helpers — YAML serialization for QCA condition definitions. (~2415 tok)
- `strategies.py` — Calibration strategy pattern — pluggable membership calibration algorithms. (~3647 tok)
- `training.py` — Training engine for fitting calibration parameters from labeled samples. (~2411 tok)

## src/experiment_engine/viz/


## src/hooks/

- `usePyodide.ts` — React hook wrapping the Pyodide bridge singleton. (~452 tok)
- `useQCAWorkflow.ts` — Hook that ties the Pyodide bridge to the pipeline state context. (~3749 tok)

## src/i18n/

- `translations.ts` — i18n translations: Chinese (zh) and English (en). (~9360 tok)

## src/layouts/


## src/pages/

- `Dashboard.css` — Styles: 24 rules (~592 tok)
- `Dashboard.tsx` — Dashboard — QCA pipeline overview with pipeline status widget, (~3040 tok)
- `DataInput.tsx` — Data Input — text corpus upload + condition set YAML editor. (~13966 tok)
- `Settings.tsx` — Settings — QCA analysis parameters, calibration defaults, and engine config. (~6443 tok)

## src/pyodide/

- `types.ts` — Raw Chinese text strings to calibrate. Dead code — no external consumers; kept as documentation. (~750 tok)

## src/services/

- `bert-cache.ts` — BERT embedding cache service — IndexedDB persistence. (~288 tok)
- `bert-engine.ts` — Default BERT model for Chinese text feature extraction. (~2722 tok)
- `pyodide.ts` — Main-thread Pyodide bridge — methods called from React components. (~4448 tok)
- `pyodide.worker.ts` — Pyodide Web Worker — runs Python/NumPy in a background thread so the (~6864 tok)

## src/store/

- `QCAPipelineContext.tsx` — React Context for tracking the QCA pipeline lifecycle. (~3090 tok)

## src/types/

- `bert.ts` — BERT engine types: status, embeddings, prototype maps, worker request/response interfaces. (~642 tok)
- `index.ts` — Legacy types — kept for backward compatibility with existing UI components. (~412 tok)
- `qca.ts` — QCA-specific TypeScript interfaces mirroring experiment_engine/models.py. (~3516 tok)

## tests/

- `test_robustness.py` — Unit tests for robustness testing module (qca_engine/advanced/robustness.py). (~2661 tok)

## tmp/

- `generate_test_data.py` — Generate QCA test datasets and verify them. (~4823 tok)
- `test_condition_set.yaml` — Custom QCA condition set YAML with modified keywords/calibration for testing custom conditions (~500 tok)
- `test_dataset_1_standard.csv` — 15 realistic citizen feedback texts across all 5 QCA domains (~400 tok)
- `test_dataset_2_edge_cases.csv` — 10 edge-case texts testing algorithmic boundaries (~300 tok)
- `test_dataset_3_small_n.csv` — 5 precision validation texts with predictable keyword coverage (~200 tok)
- `verify_pipeline.py` — record (~8086 tok)
- `verify-load-engine.mjs` — BASE: snap, check (~2089 tok)
