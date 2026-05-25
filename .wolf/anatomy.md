# anatomy.md

> Auto-maintained by OpenWolf. Last scanned: 2026-05-25T06:28:37.576Z
> Files: 15 tracked | Anatomy hits: 0 | Misses: 0

## ../.claude/plans/


## ./

- `package.json` — Node.js package manifest (~172 tok)
- `TODO.md` — TODO — QCA Analysis Tool (~3163 tok)

## .claude/


## .claude/rules/


## .claude/worktrees/agent-a182dd20ad100bc90/


## .claude/worktrees/agent-a182dd20ad100bc90/.wolf/


## .github/workflows/


## .wolf/


## roadmap/

- `experiment-engine-roadmap.json` (~8572 tok)

## src/


## src/components/


## src/experiment_engine/


## src/experiment_engine/algorithms/


## src/experiment_engine/core/


## src/experiment_engine/io/


## src/experiment_engine/models/

- `qca.py` — QCA domain models — text analysis, calibration, truth tables, solutions, etc. (~5440 tok)

## src/experiment_engine/qca_engine/


## src/experiment_engine/qca_engine/advanced/


## src/experiment_engine/report/


## src/experiment_engine/text_calibration/

- `__init__.py` — Text calibration layer: raw text → fuzzy-set membership scores. (~533 tok)
- `cosine_similarity.py` — BERT CLS embedding cosine similarity engine for prototype-based QCA scoring. (~4804 tok)

## src/experiment_engine/viz/


## src/hooks/

- `useQCAWorkflow.ts` — Hook that ties the Pyodide bridge to the pipeline state context. (~3010 tok)

## src/i18n/

- `translations.ts` — i18n translations: Chinese (zh) and English (en). Keyword dict import/export strings removed; BERT model setting added. (~8000 tok)

## src/layouts/


## src/pages/

- `DataInput.tsx` — Data Input — text corpus upload + condition set YAML editor. (~13186 tok)
- `Results.tsx` — Results — displays all QCA analysis output in organized sections: (~10757 tok)

## src/pyodide/


## src/services/

- `bert-cache.ts` — BERT embedding cache service — IndexedDB persistence for prototype embeddings + text embeddings, keyed by model name (~288 tok)
- `bert-engine.ts` — Default BERT model for Chinese text feature extraction. (~2432 tok)

## src/store/


## src/types/

- `bert.ts` — BERT engine status. (~642 tok)
- `qca.ts` — QCA-specific TypeScript interfaces mirroring experiment_engine/models.py. (~3169 tok)

## tests/

- `test_cosine_similarity.py` — Comprehensive unit tests for CosineSimilarityEngine. (~12066 tok)

## tmp/
