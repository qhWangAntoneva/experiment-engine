# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-26T19:35:59.858Z
> Files: 17 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/


## ../.claude/plans/


## ../.claude/projects/C--Users-lenovos-QCA-Analysis-Tool/memory/


## ../National-Policy-Database/


## ./


## .claude/


## .claude/rules/


## .claude/worktrees/agent-a182dd20ad100bc90/


## .claude/worktrees/agent-a182dd20ad100bc90/.wolf/


## .github/workflows/


## .wolf/


## .wolf/plans/


## public/


## roadmap/


## src/


## src/components/


## src/experiment_engine/

- `__init__.py` — QCA Text Analysis Tool — citizen feedback text → fuzzy-set QCA analysis. (~467 tok)
- `api.py` — QCA Analysis Python API — clean functions for programmatic use. (~4123 tok)
- `cli.py` — QCA Text Analysis CLI — complete QCA workflow commands. (~6552 tok)
- `pyodide_handlers.py` — handle_calibrate, handle_calibrate_prototype, handle_analyze, handle_robustness (~6892 tok)

## src/experiment_engine/algorithms/


## src/experiment_engine/core/


## src/experiment_engine/io/


## src/experiment_engine/models/

- `__init__.py` — QCA Text Analysis Tool — data models. (~659 tok)
- `qca.py` — QCA domain models — text analysis, calibration, truth tables, solutions, etc. (~5271 tok)

## src/experiment_engine/qca_engine/

- `analyzer.py` — Main QCA analysis pipeline stage — orchestrates the full analysis. (~1613 tok)
- `necessity.py` — Necessary condition analysis for QCA. (~1104 tok)
- `sufficiency.py` — Sufficiency analysis for QCA solutions. (~1528 tok)
- `truth_table.py` — QCA Truth Table construction from fuzzy-set membership data. (~1429 tok)

## src/experiment_engine/qca_engine/advanced/

- `robustness.py` — Robustness and sensitivity tests for QCA results. (~4829 tok)

## src/experiment_engine/report/


## src/experiment_engine/text_calibration/


## src/experiment_engine/viz/

- `qca_plots.py` — QCA-specific visualizations using existing renderer backends. (~1328 tok)
- `viz_bridge.py` — Bridge between QCAPlotBuilder (plot data) and file-based visualization output. (~4034 tok)

## src/hooks/


## src/i18n/


## src/layouts/


## src/pages/


## src/pyodide/


## src/services/


## src/store/


## src/types/

- `index.ts` — Legacy types — kept for backward compatibility with existing UI components. (~451 tok)
- `qca.ts` — QCA-specific TypeScript interfaces mirroring experiment_engine/models.py. (~4685 tok)

## src/utils/


## tests/

- `test_qca_core.py` — Unit tests for QCA core modules. (~16209 tok)
- `test_robustness.py` — Unit tests for robustness testing module (qca_engine/advanced/robustness.py). (~2664 tok)

## tests/fixtures/


## tmp/
