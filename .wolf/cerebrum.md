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
- **`process_with_outcome()` DANGER**: This method overrides the outcome column with external crisp 0/1 values. In fsQCA, ALL columns (including outcome) should be continuous fuzzy values in (0,1). Calling `process_with_outcome()` in a user-facing web context causes the outcome column to display only 0/1, which is semantically wrong. **The two-method API (process vs process_with_outcome) is a known design flaw** — the name `process_with_outcome` misleadingly suggests "processing that includes an outcome" (which `process()` already does), when it actually means "overwrite outcome with external values." Prefer a single `process()` with an explicit `OutcomeHandling` enum parameter. See P2-40.

## 6. Do-Not-Repeat

### Critical (still active)

- [2026-05-27 → 2026-05-27 **FIXED**] **TemplateLibrary's `setConditionSet` fails because `handleCalibrate`/`handleRunPipeline` have stale closures**: The hydration `useEffect` (DataInput.tsx:359-365) correctly sets `importedConditionSet`, but `handleCalibrate` and `handleRunPipeline` useCallback dependency arrays **lacked `importedConditionSet`**, so the memoized callbacks captured the old `null` value and fell back to `yamlContent`. Root cause confirmed by 3-agent analysis (functional analyst, code technical advisor, investigator), reviewed and ACCEPTED. Fix: add `importedConditionSet` to both dependency arrays. Also added `qca_variant` to TemplateLibrary's constructed ConditionSet object. **The useEffect hydration + dispatch null pattern is correct** — React 18 StrictMode does NOT cause this bug because useState values persist across StrictMode double-mounts.

- [2026-05-27 **ACTIVE**] **`process_with_outcome()` 算法BUG + reviewer 漏检**: 修复 agent 为了 "CSV expected_outcome 必须使用" 引入 `process_with_outcome()`，导致 outcome 列退化为 0/1。reviewer 只验证了代码结构（API签名、变量提取、分支正确）但没有验证运行时语义。**根源**：(a) reviewer prompt 缺少对"输出值语义"的检查要求；(b) 没有区分 CLI（研究者期望 ground-truth）和 web（交互式用户期望模糊值）两条路径的语义差异；(c) reviewer 没有质疑 CEREBRUM 指令是否适用于所有路径。**修复**：已列入 TODO.md E 节 9 项改进（流程/测试/架构三层防御）。(Critical — review process gap)
- [2026-05-26] **memory.md growth**: archive sessions >2 days to memory-archive.md periodically
- [2026-05-25/26] **Agent completion claims not trustworthy** — after any agent claims completion, MUST verify with Read/Grep/`git diff --stat`. Fabricated modifications common.
- [2026-05-25] **Large task single agent = timeout + failure**: L-level tasks MUST be split into 2-3 file-level subtasks, executed by multiple agents in parallel.
- [2026-05-25] **Parallel agents sharing files causes change loss**: Agents with shared file dependencies MUST run serially; each commits before next starts.
- [2026-05-24] **Planning doc statistics deviate after multi-agent editing**: Always recalculate counts from scratch, not trusting incremental updates.
- [2026-05-27] **CLI/api path has no BERT embeddings**: TextCalibrationStage must ALWAYS include a text-level fallback for _precompute_scores. The old all-zeros fallback cascades through DirectCalibration degeneracy (identical scores -> all 0.5). Always add _fallback_text_scores() (trigram Jaccard) when introducing new scoring paths.
- [2026-05-27] **CSV expected_outcome column is NEVER used**: `api.py` `run_calibrate()` calls `TextCorpusReader.read()` with `text_column="text"` only, silently dropping the `expected_outcome` column. This causes all outcome values to be computed from trigram similarity to outcome prototypes rather than ground-truth labels. The outcome column MUST come from CSV labels. Use `pandas.read_csv()` to get both `text` and `expected_outcome`, filter by domain, then call `TextCalibrationStage.process_with_outcome()`. Without this fix, truth tables are meaningless (all outcome=1 or all outcome=0).
- [2026-05-27] **Same bug exists in pyodide_handlers.py handle_load_corpus / handle_load_corpus_direct**: Both functions called TextCorpusReader.read() and set metadata: {} — the expected_outcome column from CSV was never passed through to calibration. Fix: After reading with TextCorpusReader, re-read CSV with pandas and inject expected_outcome into each entry's metadata.
- [2026-05-27 → 2026-05-27 **REVERTED**] **handle_calibrate in pyodide_handlers (web path) also had same bug**: used process() instead of process_with_outcome(), ignoring ground-truth outcomes. Fix: extract expected_outcome from sample metadata, build np.float64 vector, use process_with_outcome(). Fall back to process() when no samples have expected_outcome. **REVERTED 2026-05-27**: process_with_outcome() causes outcome column (e.g. high_dissatisfaction) to show only crisp 0/1, but users expect fuzzy values for all columns in the web Results table. Web path now always uses process() so outcome is calibrated normally. CLI api.py still uses process_with_outcome() for ground-truth outcomes.
- [2026-05-27] **handle_robustness in pyodide_handlers missing input validation**: Empty fuzzy data (0 cases) crashes RobustnessTester.run_all with a cryptic error. Always validate `_fd_dict.get("membership", [])` shape (ndim==2, shape[0]>0) before constructing MembershipData, and wrap run_all in try/except with a diagnostic RuntimeError.
- [2026-05-27] **handle_analyze in pyodide_handlers did not pass condition_set to QCAnalyzerStage**: The condition_set stores domain info and condition metadata used in solution labels. Fix: add optional condition_set_path parameter, load condition set when provided, pass to QCAnalyzerStage constructor. This required updating the full calling chain (worker, bridge, hook, types).
- [2026-05-27] **Reviewer confirmed**: All 3 algorithm bugs fixed (domain filter, outcome injection, calibration variance). 2 domains (dissatisfaction, trust) have empty solutions — this is a test fixture data quality issue, NOT a code bug. Pre-commit hook root cause: ruff version mismatch (v0.4.0 vs v0.15.12) and running separate commands instead of `pre-commit run --all-files`.

### Python/CLI

- [2026-05-24] `click.Choice([d.value for d in [...strings...]])` throws AttributeError; use plain string lists
- [2026-05-24] **Windows Python GBK trap**: always `open(path, encoding='utf-8')`
- [2026-05-24] **pre-commit version mismatch**: local `uv run ruff` and pre-commit hook ruff versions must match
- [2026-05-24] `@staticmethod` calling another @staticmethod needs `ClassName.method()`, not `self.method()`

### Frontend/Pyodide

- [2026-05-27] **mountFromInline() VFS path prefix must match sys.path**: When writing Python files to Pyodide VFS, the path prefix must match `sys.path`. If `sys.path` has `/src`, files must be at `/src/experiment_engine/...`, NOT `/experiment_engine/...`. Otherwise Python raises `ModuleNotFoundError`. Always add both `/src` and `/` to `sys.path` as backup.
- [2026-05-27] **mountFromInline() must write actual Python source files, not just empty dirs**: The old fallback created empty package directories causing `ModuleNotFoundError` at import time. Fix: create Vite plugin serving `/py/modules.json` with all `.py` file contents as JSON. Worker fetches this and writes files via `FS.mkdirTree`/`FS.writeFile`.
- [2026-05-27] **Retry loop post-check bug**: `writeAttempts >= MAX_WRITE_ATTEMPTS` after a `while` loop fires incorrectly when the 3rd attempt succeeds (3 >= 3). ALWAYS put the exhaustion check INSIDE the loop after the stat check, not as a post-loop check.
- [2026-05-27] **FS.unlink catch must check errno**: Never `catch (_) { /* ignore */ }` — EACCES/EBUSY/EISDIR should propagate. Only swallow ENOENT (errno 44 in Emscripten). Always use `catch (e: any) { if (e && e.errno !== 44) throw e; }`.
- [2026-05-27] **Pyodide Python diagnostics**: Use `print(..., file=__import__('sys').stderr, flush=True)` instead of `os.write(1, ...)`. The latter bypasses Python's buffering and may not appear in browser console reliably.
- [2026-05-27] **Multi-agent workflow with review**: 3 fix agents in parallel, each reviewed by a dedicated reviewer agent, then main session applies review fixups. This catches cross-agent issues (e.g., retry loop logic bug caught by Reviewer B reviewing Agent C's code).
- [2026-05-27] **Never pass yamlContent (YAML string) directly as ConditionSet**: JS spread operator `{...str}` on a string yields character-indexed object `{'0':'n','1':'a',...}` — all `conditions`/`outcome`/`domain` fields are lost. This causes `ValidationError: membership must have at least 1 column` on the Python side. Always parse YAML to ConditionSet object before passing to `ensureQCAVariant()` or any pipeline function. Use `yamlToConditionSet()` from `conditionSetToYaml.ts`.
- [2026-05-27] **Worker errors are invisible in DevTools without console.error()**: Pyodide worker errors go through `postMessage()` → React state, never call `console.error()`. Always add `console.error()` in the bridge's error handling paths in `pyodide.ts`.
- [2026-05-27] **UX: bridge "Load 30 Samples" and "Parse Text" with pasteContent auto-fill**: After `handleLoadSampleData` calls `loadCorpus()`, call `setPasteContent(SAMPLE_CSV_CONTENT)` so the textarea shows the loaded data AND "解析文本" works. This solves the "请先粘贴文本内容再解析" error when samples were loaded via button. Also add a StepIndicator (Load Data / Calibrate / Analyze / Results) and a guidance bar below the textarea when `pasteContent === SAMPLE_CSV_CONTENT`. The StepIndicator uses inline styles with CSS variables and shows current step with filled circle + label.
- [2026-05-27] **pandas REQUIRED for CSV corpus loading in Pyodide**: The `_get_pandas()` helper in `readers.py` raises `ImportError` if pandas is absent. Since 30 sample data is CSV, pandas must be in `REQUIRED_PACKAGES` AND in `deploy.yml` manifest. pandas IS available in the Pyodide distribution (can be loaded via `pyodide.loadPackage('pandas')`), but it's large (~10MB), so install times may increase.
- [2026-05-27] **Vite SPA fallback returns HTML (HTTP 200) for missing assets**: In dev mode, Vite serves `index.html` with status 200 for ANY unhandled route. This means `resp.ok` is `true` even when the resource doesn't exist (e.g., `/py/experiment_engine.tar.gz`). Always check response `Content-Type` or size as a secondary validation, not just HTTP status code.
- [2026-05-27] **REQUIRED_PACKAGES in pyodide.worker.ts is the SOURCE OF TRUTH**: The deploy.yml manifest is purely informational and NOT consumed at runtime. When adding a package to Pyodide, ALWAYS update `REQUIRED_PACKAGES` in `pyodide.worker.ts` first, then update `deploy.yml` manifest as documentation.
- [2026-05-27] **pyodide-manifest.json is hardcoded in deploy.yml**: The manifest at `.github/workflows/deploy.yml` line 110 is created by `cat > dist/py/pyodide-manifest.json << 'MANIFEST'`. It must be manually kept in sync with `REQUIRED_PACKAGES`.
- [2026-05-27] **Pyodide FS.writeFile with string + Chinese UTF-8 produces 0-byte file**: In Pyodide v0.26.4 (Emscripten 3.1.64), `pyodide.FS.writeFile(path, content, { encoding: 'utf8' })` where `content` is a JS string containing multi-byte Chinese characters can produce a 0-byte file. The `encoding` option is intended for `FS.readFile` (decoding), not `FS.writeFile` (encoding), but passing it can trigger a different code path in Emscripten's `intArrayFromString`. **Fix**: Always use `new TextEncoder().encode(content)` to produce a `Uint8Array`, then pass that to `FS.writeFile(path, uint8array)`. Do NOT pass a raw JS string with Chinese characters + opts to `FS.writeFile`. Also, bypassing the JSON.stringify intermediate alone is insufficient — the root issue is FS.writeFile string handling, not the JSON chain. **ALL FS.writeFile calls must use this pattern** — `runHandler()` (line 95) and `mountFromInline()` (line 413) were also vulnerable. FS.readFile with {encoding:'utf8'} is safe (different code path). See bug-376, bug-380.
- [2026-05-24] **Never inject data into Python via JS template literals** — code injection risk. Use `FS.writeFile` then `json.load()` in Python.
- [2026-05-24] **Pyodide mountFromInline must write `__init__.py`** in each package directory.
- [2026-05-24] **pre-commit stash-conflict infinite loop** — fix: `.wolf/hooks/pre-commit.js` runs `pre-commit run --all-files` before `git add -u`.
- [2026-05-24] `npm ci` failure masks subsequent TypeScript errors — run `npm run build` locally before pushing.
- [2026-05-27] **Pyodide init must include pydantic**: `pyodide.worker.ts` `REQUIRED_PACKAGES` must include `'pydantic'` for ALL experiment_engine operations to work. The error message suggests micropip but `pyodide.loadPackage()` works since pydantic is in the Pyodide distribution. Never assume pydantic is available in Pyodide — it must be explicitly loaded.
- [2026-05-27] **Python handle_calibrate must validate condition_set conditions BEFORE calling calibrate_one**: If conditions are empty, MembershipData validation will fail with `membership must have at least 1 column`. Add guard with diagnostic info (JSON keys, types) to help debug frontend data issues. See `pyodide_handlers.py:80-92`.

---

*Old decision log entries (2026-05-24/25) and historical bug fix list (FIXME-1 through FIXME-21) archived to wolf archives. See git log for complete history.*
