# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-27T07:34:06.667Z
> Files: 26 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/plans/

- `synthetic-coalescing-sunbeam.md` — 30样本加载崩溃 - 并行调查计划 (~459 tok)

## ./

- `index.html` — QCA Simulation Tool (~574 tok)
- `vite.config.ts` — ============================================================================= (~373 tok)

## .github/workflows/

- `deploy.yml` — ============================================================================== (~1814 tok)

## scripts/

- `vite-plugin-pyodide-modules.ts` — Vite plugin that serves Python module sources as JSON for Pyodide in dev mode. (~785 tok)

## src/experiment_engine/

- `config.py` — Configuration loading for experiment-engine pipelines. (~3117 tok)
- `pipeline.py` — Pipeline and Stage abstract base classes. (~5480 tok)
- `plugins.py` — Plugin system for experiment-engine pipeline stages. (~4227 tok)
- `pyodide_handlers.py` — handle_calibrate, handle_calibrate_prototype, handle_analyze, handle_robustness (~7360 tok)

## src/i18n/

- `translations.ts` — i18n translations: Chinese (zh) and English (en). (~14422 tok)

## src/services/

- `pyodide.ts` — Main-thread Pyodide bridge — methods called from React components. (~4707 tok)
- `pyodide.worker.ts` — Pyodide Web Worker — runs Python/NumPy in a background thread so the (~8579 tok)

## tmp/

- `capture_error.mjs` — Quick test to capture the exact error message when clicking (~1014 tok)
- `capture_full_error.mjs` — Capture the FULL error message from the validation card after (~661 tok)
- `clear_cache.mjs` — Declares browser (~479 tok)
- `e2e_rich_fix.mjs` — E2E Rich Module Fix Verification Test. (~3453 tok)
- `minimal_test.mjs` — Minimal test to verify Playwright works (~311 tok)
- `reproduction_diag_v2.mjs` — Comprehensive crash reproduction diagnostic test — v2. (~5389 tok)
- `reproduction_diag_v3.mjs` — Comprehensive crash reproduction diagnostic test — v3. (~4009 tok)
- `reproduction_diag.mjs` — Comprehensive crash reproduction diagnostic test. (~5257 tok)
- `reviewer_test.mjs` — Declares browser (~849 tok)
- `serve-prod.mjs` — Simple HTTP server for production build testing. (~731 tok)
- `verify_fix.mjs` — Verification test: starts at local dev server, clicks "Load Engine" button, (~1486 tok)
- `verify_page.mjs` — Declares browser (~147 tok)
- `verify_rich_diag.mjs` — Diagnostic DevTools test: dump ALL log lines containing "rich" or "module" (~526 tok)
- `verify_rich_fix.mjs` — DevTools verification: Test that the "No module named 'rich'" error is fixed. (~968 tok)
