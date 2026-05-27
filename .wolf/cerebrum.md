# Cerebrum -- QCA Text Analysis Tool

> OpenWolf learning memory. Last comprehensive update: 2026-05-28
> **Context optimization (2026-05-27)**: old decision log entries archived, obsolete historical learnings trimmed, Do-Not-Repeat stale items removed.

---

## 0. Quick Start

**Before any work, read these for current status**:
- `TODO.md` — 16 remaining P2 items (P0/P1 all complete, P2-4/5/15/17/19/21/24 done)
- `FIXME.md` — 3 remaining defects (0 critical, 0 warnings, 3 suggestions)
- `HACK.md` — 8 unresolved items

**Current baseline**: HEAD `b914889` on master, tests 532 passed, TS build clean.

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

- **2026-05-28: Transformers.js ONNX Runtime 云端推理崩溃防护**：`bert-engine.ts` 中 `this._model(batchTexts, ...)` 调用在云端生产环境可能抛出 Transformers.js 内部错误（访问 undefined tensor `.data`），本地 dev 正常。添加 try-catch 包裹 + 零向量回退，确保单个 batch 推理失败不会崩溃整个 pipeline。同时将 tensor 无 data 时的 `throw new Error` 改为零向量回退 + console.warn。

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

- [2026-05-27 → 2026-05-27 **FIXED**] **TemplateLibrary's setConditionSet stale closure**: handleCalibrate/handleRunPipeline useCallback deps lacked `importedConditionSet` → captured old `null`, fell back to yamlContent. Fix: add `importedConditionSet` to both dependency arrays. useEffect hydration + dispatch null pattern is correct.

- [2026-05-27 **ACTIVE**] **process_with_outcome() 审查漏检**: 引入后导致 outcome 列退化为 0/1。根源: (a) reviewer 未验证运行时语义仅验结构 (b) CLI/web 路径语义差异未区分 (c) CEREBRUM 指令未在所有路径验证。修复在 TODO.md E节。(Critical — review process gap)
- [2026-05-26] **memory.md growth**: archive sessions >2 days to memory-archive.md periodically
- [2026-05-25/26] **Agent completion claims not trustworthy** — after any agent claims completion, MUST verify with Read/Grep/`git diff --stat`. Fabricated modifications common.
- [2026-05-27] **PNG 截图读取 token 开销大 (~2500/张)**：单次 Design QC 最多读 3 张（顶/中/底/关键变化），不全部读取。仅用于确认 UI 正确性时先问用户是否需要看图，避免不必要的 compact。
- [2026-05-27] **conditionSetToYaml ↔ yamlToConditionSet 缩进一致性问题**：`conditionSetToYaml()` 生成 YAML 列表项 (`- name:`, `- prototype_text:`) 在缩进 0，但 `yamlToConditionSet()` Phase 1 以**任何缩进 0 行**终止 section。修复：`- name:` 改为缩进 2，`- prototype_text:` 改为 `prototypes:` 缩进 +2。同时 `calibration_params:` (空值=子块) 被 `value === ''` 当 null 跳过 —— 去掉该条件。
- [2026-05-25] **Large task single agent = timeout + failure**: L-level tasks MUST be split into 2-3 file-level subtasks, executed by multiple agents in parallel.
- [2026-05-25] **Parallel agents sharing files causes change loss**: Agents with shared file dependencies MUST run serially; each commits before next starts.
- [2026-05-24] **Planning doc statistics deviate after multi-agent editing**: Always recalculate counts from scratch, not trusting incremental updates.
- [2026-05-27] **CLI/api path has no BERT embeddings**: TextCalibrationStage must ALWAYS include text-level fallback (_fallback_text_scores, trigram Jaccard) when introducing new scoring paths. Without it, all-0 fallback → DirectCalibration degeneracy → all 0.5 membership.
- [2026-05-27] **CSV expected_outcome column NEVER used in api.py**: run_calibrate() calls TextCorpusReader.read(text_column="text") dropping expected_outcome. MUST use pandas.read_csv() to extract both, filter by domain, then call process_with_outcome(). Without this, truth tables are meaningless (all outcome=1 or 0).
- [2026-05-27] **Same bug in pyodide_handlers**: handle_load_corpus/handle_load_corpus_direct dropped expected_outcome via TextCorpusReader.read(). Fix: re-read CSV with pandas, inject expected_outcome into each entry's metadata.
- [2026-05-27 **REVERTED**] **handle_calibrate web path: REVERTED process_with_outcome()**: process_with_outcome() causes outcome column (high_dissatisfaction) to show crisp 0/1. Web users expect fuzzy values for all columns. Web path: always uses process(). CLI api.py: still uses process_with_outcome() for ground-truth.
- [2026-05-27] **handle_robustness missing input validation**: Validate membership shape (ndim==2, shape[0]>0) before MembershipData. Wrap run_all in try/except.
- [2026-05-27] **handle_analyze must pass condition_set to QCAnalyzerStage**: Needed for domain info + condition metadata in solution labels. Update full calling chain (worker, bridge, hook, types).
- [2026-05-27] **Reviewer confirmed**: All 3 algorithm bugs fixed. 2 domains empty solutions = test fixture data quality, not code bug.
- [2026-05-28] **runFullPipeline 调用缺 runRobustness: true**: DataInput.tsx 调用 runFullPipeline 没传 runRobustness: true，robustness 步骤被静默跳过，导致结果显示 N/A。修复：在 runFullPipeline 选项中加入 runRobustness: true。
- [2026-05-28 **FIXED**] **solution_consistency/solution_coverage default 0.0 in QCAAnalysisResult**: SufficiencyAnalyzer.analyze() creates a NEW QCASolutions() with computed consistency/coverage but stores it in SufficiencyResults.solutions — the original solutions object from SolutionFormatter has default 0.0. Fix: copied sufficiency-computed QCASolution objects back to the main solutions in analyzer.py after sufficiency analysis.

- [2026-05-28 **FIXED**] **PyodideBridge.resolveOne() 返回 worker 消息信封**: resolveOne() 调用 `pending.resolve(msg)` 返回完整 worker 消息 `{ type, result }`，但 analyze() 期望直接拿到 QCAAnalysisResultJSON。修复：在 analyze() 的 .then() 中提取 `resp?.result ?? resp`，同样 runRobustness() 提取 `resp?.report ?? resp`，runCounterfactuals() 提取 `resp?.report ?? resp`。

# Important: When editing .then() chains inside class methods in pyodide.ts, NEVER remove the class method's closing `}` brace. The `.then().catch()` statement ends with `});` but the enclosing method needs a separate `}` on the next line.

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
- [2026-05-27] **embed_calibrate paths must also compute prototype_embeddings for outcome condition**: `runEmbedCalibrate` and `runFullPipeline` both built `prototypeTextsByCondition` from only `conditionSet.conditions`, ignoring `conditionSet.outcome`. The Python handler (`handle_embed_calibrate`) validates ALL conditions (including outcome) with prototypes must have `prototype_embeddings`. Fix: add outcome's prototypes to the map AND attach `prototype_embeddings` to `enrichedConditionSet.outcome`. Always check both conditions and outcome when computing prototype embeddings.

---

*Old decision log entries (2026-05-24/25) and historical bug fix list (FIXME-1 through FIXME-21) archived to wolf archives. See git log for complete history.*
