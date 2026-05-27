# Cerebrum -- QCA Text Analysis Tool

> OpenWolf learning memory. Last comprehensive update: 2026-05-27
> **Context optimization (2026-05-27)**: old decision log entries archived, obsolete historical learnings trimmed, Do-Not-Repeat stale items removed.

---

## 0. Quick Start

**Before any work, read these for current status**:
- `TODO.md` — 16 remaining P2 items (P0/P1 all complete, P2-4/5/15/17/19/21/24 done)
- `FIXME.md` — 3 remaining defects (0 critical, 0 warnings, 3 suggestions)
- `HACK.md` — 8 unresolved items

**Current baseline**: HEAD `8807e15` on master, tests 532 passed, TS build clean.

---

## 1. Project Identity

| Attribute | Value |
|-----------|-------|
| **Name** | experiment-engine / QCA Text Analysis Tool |
| **Version** | 0.2.0 |
| **One-liner** | Converts citizen feedback Chinese text into fuzzy-set QCA analysis results |
| **Python** | >=3.10, package manager `uv` |
| **CLI entry** | `qca` (9 subcommands) |
| **Frontend** | React 18 + TypeScript + Vite 5 + Transformers.js (BERT) |

## 2. Domain Model

**Input**: Chinese citizen feedback text (CSV/JSON/TXT) + condition definitions (YAML).
**5 domains**: dissatisfaction, policy_demand, co_production, trust, gov_responsiveness.
**Processing**: Text → BERT CLS embedding → cosine similarity → fuzzy calibration → truth table → Boolean minimization → necessity/sufficiency analysis.
**Output**: Fuzzy membership matrix, truth table, QCA solutions (complex/parsimonious/intermediate), necessity/sufficiency, robustness, LaTeX report.

## 3. Dependency Inventory

**Runtime**: numpy>=1.24, pydantic>=2.0, click>=8.0, pyyaml>=6.0, matplotlib>=3.7, plotly>=5.14, rich>=13.0

## 4. User Preferences

- Project documentation in Chinese
- CLI defaults to Rich-formatted output
- All Python files explicitly use `encoding='utf-8'`
- Use `uv run python`, never bare `python`
- **Default UI language is English**. `detectLanguage()` always returns `'en'`. Users can switch via sidebar.
- Agent completion claims are NOT trustworthy — always verify with `git diff --stat` or file Read

## 5. Key Learnings

### Current

- **BERT + Prototype is the sole scoring method** (completed 2026-05-25). Keyword matching fully removed. Files deleted: keyword_dict.py, keyword_io.py, prototype_similarity.py. CosineSimilarityEngine (BERT CLS + cosine similarity + softmax tau=5.0) is the only scoring engine.
- **P1-B3/B6 completed**: domains.py uses prototype text templates (not keyword presets). KeywordEntry class removed from models/qca.py. ConditionDefinition.keywords field removed.
- **P2-17 completed 2026-05-27**: Created `src/experiment_engine/api.py` with 5 clean API functions (run_calibrate, run_analyze, run_robustness, run_counterfactuals, run_report). Refactored `cli.py` commands to thin wrappers delegating to api.py. `_load_fuzzy_data` shared helper moved to api.py.
- **CLI `--output` inconsistency** (cli.py:318, cli.py:414): robustness/counterfactuals now treat as directory, consistent with run command. RESOLVED 2026-05-27.
- **QCAPlotBuilder produces plain dicts, renderers expect InputData+RenderConfig** (2026-05-27): Created `viz_bridge.py` that bypasses the impedance mismatch by calling matplotlib directly from the plot dicts. The simpler approach is to create domain-specific matplotlib plots rather than constructing InputData objects from QCAPlotBuilder dicts. Also documented: qca_results.json serialized WITHOUT fuzzy_data (excluded in cli.py), so fuzzy_data.npz must be loaded separately.

### Methodology

- **Why BERT CLS + cosine similarity?** Concept prototypes represent the theoretical ideal. BERT CLS embeddings capture semantic meaning of both prototypes and texts. Cosine similarity measures theoretical fit — aligns with QCA's calibration-by-theory principle. Softmax(tau=5.0) sharpens separation.
- **Why Quine-McCluskey?** Standard in QCA literature, deterministic, generates all prime implicants. Pure Python self-implementation validated against Ragin (2008) Lipset dataset.
- **Three calibration methods**: direct (piecewise linear), indirect (log-odds), ragin (logistic formula). All receive raw scores from CosineSimilarityEngine.

## 6. Do-Not-Repeat

### Critical (still active)

- [2026-05-27 → 2026-05-27 **FIXED**] **TemplateLibrary's `setConditionSet` fails because `handleCalibrate`/`handleRunPipeline` have stale closures**: The hydration `useEffect` (DataInput.tsx:359-365) correctly sets `importedConditionSet`, but `handleCalibrate` and `handleRunPipeline` useCallback dependency arrays **lacked `importedConditionSet`**, so the memoized callbacks captured the old `null` value and fell back to `yamlContent`. Root cause confirmed by 3-agent analysis (functional analyst, code technical advisor, investigator), reviewed and ACCEPTED. Fix: add `importedConditionSet` to both dependency arrays. Also added `qca_variant` to TemplateLibrary's constructed ConditionSet object. **The useEffect hydration + dispatch null pattern is correct** — React 18 StrictMode does NOT cause this bug because useState values persist across StrictMode double-mounts.

- [2026-05-26] **memory.md growth**: archive sessions >2 days to memory-archive.md periodically
- [2026-05-25/26] **Agent completion claims not trustworthy** — after any agent claims completion, MUST verify with Read/Grep/`git diff --stat`. Fabricated modifications common.
- [2026-05-25] **Large task single agent = timeout + failure**: L-level tasks MUST be split into 2-3 file-level subtasks, executed by multiple agents in parallel.
- [2026-05-25] **Parallel agents sharing files causes change loss**: Agents with shared file dependencies MUST run serially; each commits before next starts.
- [2026-05-24] **Planning doc statistics deviate after multi-agent editing**: Always recalculate counts from scratch, not trusting incremental updates.
- [2026-05-27] **CLI/api path has no BERT embeddings**: TextCalibrationStage must ALWAYS include a text-level fallback for _precompute_scores. The old all-zeros fallback cascades through DirectCalibration degeneracy (identical scores -> all 0.5). Always add _fallback_text_scores() (trigram Jaccard) when introducing new scoring paths.
- [2026-05-27] **CSV expected_outcome column is NEVER used**: `api.py` `run_calibrate()` calls `TextCorpusReader.read()` with `text_column="text"` only, silently dropping the `expected_outcome` column. This causes all outcome values to be computed from trigram similarity to outcome prototypes rather than ground-truth labels. The outcome column MUST come from CSV labels. Use `pandas.read_csv()` to get both `text` and `expected_outcome`, filter by domain, then call `TextCalibrationStage.process_with_outcome()`. Without this fix, truth tables are meaningless (all outcome=1 or all outcome=0).
- [2026-05-27] **Reviewer confirmed**: All 3 algorithm bugs fixed (domain filter, outcome injection, calibration variance). 2 domains (dissatisfaction, trust) have empty solutions — this is a test fixture data quality issue, NOT a code bug. Pre-commit hook root cause: ruff version mismatch (v0.4.0 vs v0.15.12) and running separate commands instead of `pre-commit run --all-files`.

### Python/CLI

- [2026-05-24] `click.Choice([d.value for d in [...strings...]])` throws AttributeError; use plain string lists
- [2026-05-24] **Windows Python GBK trap**: always `open(path, encoding='utf-8')`
- [2026-05-24] **pre-commit version mismatch**: local `uv run ruff` and pre-commit hook ruff versions must match
- [2026-05-24] `@staticmethod` calling another @staticmethod needs `ClassName.method()`, not `self.method()`

### Frontend/Pyodide

- [2026-05-24] **Never inject data into Python via JS template literals** — code injection risk. Use `FS.writeFile` then `json.load()` in Python.
- [2026-05-24] **Pyodide mountFromInline must write `__init__.py`** in each package directory.
- [2026-05-24] **pre-commit stash-conflict infinite loop** — fix: `.wolf/hooks/pre-commit.js` runs `pre-commit run --all-files` before `git add -u`.
- [2026-05-24] `npm ci` failure masks subsequent TypeScript errors — run `npm run build` locally before pushing.
- [2026-05-27] **Pyodide init must include pydantic**: `pyodide.worker.ts` `REQUIRED_PACKAGES` must include `'pydantic'` for ALL experiment_engine operations to work. The error message suggests micropip but `pyodide.loadPackage()` works since pydantic is in the Pyodide distribution. Never assume pydantic is available in Pyodide — it must be explicitly loaded.

---

*Old decision log entries (2026-05-24/25) and historical bug fix list (FIXME-1 through FIXME-21) archived to wolf archives. See git log for complete history.*
