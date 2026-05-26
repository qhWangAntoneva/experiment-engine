# Cerebrum -- QCA Text Analysis Tool

> OpenWolf learning memory. Last comprehensive update: 2026-05-26
> Purpose: project overview for new agent sessions.
> **Context optimization (2026-05-26)**: memory.md archived 916 lines to memory-archive.md; Do-Not-Repeat merged 6 agent-fabrication entries into 1.

---

## 0. Quick Start (read first every new session)

**Before any work, read these three files for current status**:
- `TODO.md` -- 34 items (0 P0 + 11 P1 + 23 P2), P0 all complete, P1-B3/P1-B6 done
- `FIXME.md` -- 3 remaining defects (0 critical, 0 warnings, 3 suggestions), 19/22 fixed
- `HACK.md` -- 18 items (8 unresolved, 10 resolved)

**Current baseline**:
- Tests: 531 passed, 1 skipped, 6 xfailed
- TypeScript: build passes
- Python: ruff all clean
- Git: master branch, HEAD 7ac38d8 (2 new commits this session)
- KeywordEntry: zero references in entire codebase

**Recommended work order** (next session):
1. **P1-5 ~ P1-13** -- Feature requirements by customer priority (P1-5 case-level calibration display, P1-9 Recent Runs real data are quick wins)
2. **P1-B7 + P1-B8** -- Model switching support + performance monitoring
3. **P2 items** -- As bandwidth permits

**Planning docs re-synced on 2026-05-26.** TODO.md, FIXME.md, HACK.md now reflect actual codebase state. P0-BERT fully complete (12/12). P1-B3/P1-B6 completed this session — domains.py now has prototype text templates, KeywordEntry fully removed from codebase.

---

## 1. Project Identity

| Attribute | Value |
|-----------|-------|
| **Name** | experiment-engine (package name) / QCA Text Analysis Tool (product name) |
| **Version** | 0.2.0 |
| **One-liner** | Converts citizen feedback Chinese text into fuzzy-set QCA analysis results automatically |
| **Python** | >=3.10 |
| **Package manager** | uv |
| **CLI entry** | `qca` (9 subcommands) |
| **Test framework** | pytest (465 passed historical baseline) |

---

## 2. Domain Model: What is QCA Text Analysis?

**Input**: Citizen feedback Chinese text (CSV/JSON/TXT) + condition definitions (YAML, with concept prototypes and calibration parameters)
**Processing**: Text -> BERT CLS embedding -> cosine similarity -> fuzzy calibration -> truth table -> Boolean minimization -> necessity/sufficiency analysis
**Output**: Fuzzy membership matrix, truth table, QCA solutions (complex/parsimonious/intermediate), necessity/sufficiency metrics, robustness report, LaTeX report

**5 text domains** (predefined domain presets in domains.py -- NOTE: currently keyword-based, pending P1-B3 migration to prototype-text templates):
- `dissatisfaction` -- Dissatisfaction (complaints, reporting, negative sentiment)
- `policy_demand` -- Policy demand (suggestions, resource requests, legislative appeals)
- `co_production` -- Co-production requests (willingness to participate, contribution offers, knowledge sharing)
- `trust` -- Trust (institutional trust, competence perception, benevolence perception)
- `gov_responsiveness` -- Government responsiveness (timeliness, resolution effectiveness, transparency)

**Core constraint**: Pure Python implementation (numpy allowed), no extra dependency install, no R or other packages.

---

## 3. Architecture: Four-Layer Data Flow

```
+-------------------------------------------------------------+
|  Layer 1: text_calibration/  Text -> Fuzzy Sets              |
|  +--------------+  +--------------------+  +---------------+ |
|  | domains.py   |  |cosine_similarity.py |  | calibrator.py | |
|  | 5 domain     |->| BERT CLS embedding  |->| 3 calibration  | |
|  | presets      |  | + centroid prototype|  | methods        | |
|  | (keyword-    |  | + softmax scoring   |  | (direct/       | |
|  |  based,       |  |   (tau=5.0)         |  |  indirect/     | |
|  |  P1-B3 pend.)|  |                     |  |  ragin)        | |
|  +--------------+  +--------------------+  +---------------+ |
|  condition.py: YAML <-> ConditionSet serialization             |
|  training.py: Estimate calibration thresholds from labeled     |
|               samples via quantile matching                   |
+-------------------------------------------------------------+
|  Layer 2: qca_engine/  Fuzzy Sets -> QCA Analysis            |
|  +--------------+  +--------------+  +------------------+    |
|  | consistency  |  | truth_table  |  | minimization.py  |    |
|  | consistency  |->| 2^k config   |->| Quine-McCluskey  |    |
|  | /coverage    |  | enumeration  |  | prime implicants |    |
|  | pure numpy   |  | frequency +  |  | + min cover      |    |
|  | formulas     |  | consistency  |  |                  |    |
|  +--------------+  +--------------+  +------------------+    |
|  +--------------+  +--------------+  +------------------+    |
|  | necessity.py |  | sufficiency  |  | solution.py      |    |
|  | X_i >= Y?    |  | solution     |  | formula           |    |
|  |              |  | term <= Y?   |  | formatting        |    |
|  +--------------+  +--------------+  +------------------+    |
|  analyzer.py: QCAnalyzerStage orchestrates all above          |
|               (@register_stage)                               |
+-------------------------------------------------------------+
|  Layer 3: qca_engine/advanced/  Advanced Analysis             |
|  robustness.py:  Consistency/frequency/calibration sensitivity|
|                  + bootstrap                                  |
|  counterfactual.py: Easy/difficult counterfactual             |
|                     classification -> complex/parsimonious/   |
|                     intermediate solutions                    |
|  multi_outcome.py: Cross-outcome comparison (shared           |
|                    conditions, Jaccard similarity)            |
+-------------------------------------------------------------+
|  Layer 4: Output                                              |
|  viz/qca_plots.py:     Truth table heatmap, N/S XY plot,      |
|                        distribution histogram                 |
|  report/qca_reporter.py: Full LaTeX report (extends legacy    |
|                           latex_reporter)                     |
|  io/readers.py:        TextCorpusReader (CSV/JSON/TXT)       |
|  cli.py:               9-command full CLI                     |
+-------------------------------------------------------------+
```

---

## 4. Complete Module Path Listing

### 4.1 Framework Core (retained from 0.1.0, unmodified)

| File | Responsibility | Key Classes/Functions |
|------|---------------|----------------------|
| `pipeline.py` | Stage/Pipeline abstraction | `Stage` (ABC: setup/process/teardown), `Pipeline` (composite) |
| `plugins.py` | Plugin registration system | `BasePlugin(Stage)`, `PluginRegistry` (singleton), `@register_stage`, `PluginLoader` |
| `config.py` | YAML/JSON config loading | `load_config()`, `merge_defaults()`, `apply_cli_overrides()` |
| `core/parallel.py` | Parallel execution | `ParallelStageGroup`, `ParallelPipeline` (ThreadPoolExecutor) |

### 4.2 Data Models

| File | Responsibility | Key Models (30+ Pydantic v2 models) |
|------|---------------|--------------------------------------|
| `models/framework.py` | Framework-layer models | **Generic**: `InputData[T]`, `OutputData[T]`, `PipelineResult`, `ExperimentConfig` |
| | | **Enums**: `StageStatus`, `PipelineStatus` |
| | | **Config**: `PipelineStageConfig`, `InputConfig`, `ExportConfig`, `RenderConfig` |
| | | **Results**: `StageResult`, `PipelineResult`, `Timer` |
| `models/qca.py` | QCA domain models | **Calibration**: `TextDomain`, `CalibrationType`, `ScoringSource` (PROTOTYPE only), `CalibrationParams`, `KeywordEntry` (legacy, P1-B6 cleanup pending), `ConceptPrototype` |
| | | **Conditions**: `ConditionDefinition`, `ConditionSet`, `TextCase` |
| | | **Core data**: `FuzzySetData` (ndarray + metadata) |
| | | **Analysis**: `TruthTable`, `TruthTableRow`, `QCASolutions`, `SolutionTerm`, `QCAAnalysisResult` |
| | | **Necessity**: `NecessityResults`, `NecessityConditionResult`; **Sufficiency**: `SufficiencyResults` |
| | | **Robustness**: `RobustnessReport`, `RobustnessTestResult` |
| | | **Counterfactual**: `CounterfactualReport`, `CounterfactualClassification`; **Multi-outcome**: `MultiOutcomeReport` |
| `models/training.py` | Training models | `TrainingSample`, `TrainingDataset` |
| `models/__init__.py` | Re-exports all 34 public symbols | Maintains `from experiment_engine.models import X` backward compatibility |

### 4.3 Layer 1: text_calibration/

| File | Responsibility | Key Classes/Functions |
|------|---------------|----------------------|
| `domains.py` | 5 domains x keyword presets (legacy keyword-based, P1-B3 pending migration to prototype-text templates) | `DOMAIN_PRESETS: dict[TextDomain, dict]`, `build_default_conditions(domain)` |
| `cosine_similarity.py` | **BERT CLS embedding + cosine similarity engine (PRIMARY scoring method)** | `CosineSimilarityEngine` -- embed_texts(), compute_raw_scores(): BERT CLS embedding -> mean-pooled centroid -> cosine similarity -> softmax(tau=5.0) |
| `condition.py` | Condition set I/O (YAML serialization + Fluent Builder) | `ConditionDefinitionBuilder`, `ConditionSetBuilder`, `save_condition_set()`, `load_condition_set()` |
| `calibrator.py` | Text calibration Stage (cosine similarity raw scores -> fuzzy membership 0-1) | `TextCalibrationStage(Stage)` -- process() via `CosineSimilarityEngine`, then calibrate_direct/indirect/ragin |
| `training.py` | Learn calibration thresholds from labeled samples | `TrainingEngine` -- fit() uses quantile matching to estimate threshold_full_in/out/crossover |

### 4.4 Layer 2: qca_engine/

| File | Responsibility | Key Classes/Methods |
|------|---------------|---------------------|
| `consistency.py` | Core QCA math (pure numpy) | `ConsistencyCalculator` -- subset_consistency, raw_coverage, unique_coverage, solution_consistency/coverage, fuzzy_and/or/not |
| `truth_table.py` | Truth table construction | `TruthTableBuilder` -- build() enumerates 2^k configs, computes per-case config membership (min intersection), filters |
| `minimization.py` | Quine-McCluskey Boolean minimization | `QuineMcCluskey` -- minimize() grouping->merging->prime implicants->minimal cover (greedy algorithm) |
| `necessity.py` | Necessary condition analysis | `NecessityAnalyzer` -- analyze() computes necessity for each condition + its negation (default threshold 0.9) |
| `sufficiency.py` | Sufficient condition analysis | `SufficiencyAnalyzer` -- analyze() computes consistency + raw/unique/solution coverage for solution terms |
| `solution.py` | Solution formula formatting | `SolutionFormatter` -- supports boolean(*)/logical(^~)/latex three styles |
| `analyzer.py` | Orchestration Stage | `QCAnalyzerStage(BasePlugin)` -- @register_stage("qca_analysis"), orchestrates full QCA pipeline |

### 4.5 Layer 3: qca_engine/advanced/

| File | Responsibility | Key Classes/Methods |
|------|---------------|---------------------|
| `robustness.py` | Robustness testing | `RobustnessTester` -- test_consistency_sensitivity, test_frequency_sensitivity, test_calibration_sensitivity, run_all() |
| `counterfactual.py` | Counterfactual analysis | `CounterfactualAnalyzer` -- analyze() classifies easy/difficult counterfactuals, produce_complex/parsimonious/intermediate_solution() |
| `multi_outcome.py` | Multi-outcome comparison | `MultiOutcomeComparison` -- compare() cross-outcome Jaccard similarity + shared/unique conditions |

### 4.6 I/O Layer

| File | Responsibility | Key Classes |
|------|---------------|-------------|
| `io/readers.py` | Data readers | `DataReader` (ABC), `CSVReader`, `JSONReader`, `ArrayReader`, `SyntheticReader`, **`TextCorpusReader`** (new -- reads Chinese corpus CSV/JSON/TXT) |
| `io/exporters.py` | Data export | `CSVExporter`, `JSONExporter`, `HTMLExporter` |
| `io/sources.py` | Data source abstraction | `DataSource`, `FileDataSource`, `StdinDataSource`, `GeneratorDataSource` |
| `io/db.py` | Database connections | `SQLiteDataSource`, `SQLiteDataWriter`, PostgreSQL stubs |

### 4.7 Visualization Layer

| File | Responsibility | Key Classes |
|------|---------------|-------------|
| `viz/base.py` | Renderer ABC | `Renderer` |
| `viz/console.py` | Rich terminal rendering | `ConsoleRenderer` |
| `viz/matplotlib_renderer.py` | Matplotlib static plots | `MatplotlibRenderer` |
| `viz/plotly_renderer.py` | Plotly interactive plots | `PlotlyRenderer` |
| `viz/streamlit_dashboard.py` | Streamlit web dashboard | Streamlit app |
| `viz/qca_plots.py` | **QCA-specific plots** | `QCAPlotBuilder` -- truth_table_heatmap, necessity_xy_plot, sufficiency_xy_plot, fuzzy_distribution_plot, solution_bar_chart |

### 4.8 Reporting Layer

| File | Responsibility | Key Classes |
|------|---------------|-------------|
| `report/latex_reporter.py` | Basic LaTeX generation | `LaTeXReporter` -- generates reports from PipelineResult (retained from 0.1.0) |
| `report/qca_reporter.py` | **QCA-specific LaTeX** | `QCALaTeXReporter` -- generate() produces complete LaTeX doc with truth table, solution formulas, necessity/sufficiency/robustness tables |

### 4.9 CLI (cli.py, fully rewritten)

9 subcommands, all via Click:

| Command | Function | Key Parameters |
|---------|----------|---------------|
| `qca calibrate` | Text -> fuzzy sets | --condition-set, --input, --text-column, --output |
| `qca train` | Train calibration params from labeled samples | --condition-set, --samples, --output |
| `qca analyze` | Full QCA analysis | --condition-set, --fuzzy-data, --consistency, --frequency |
| `qca robustness` | Robustness testing | --condition-set, --fuzzy-data, --output |
| `qca counterfactuals` | Counterfactual analysis | --condition-set, --fuzzy-data, --expectations |
| `qca report` | Generate reports (latex/console) | --results, --format, --output |
| `qca run` | One-click full pipeline | --config (complete YAML workflow config) |
| `qca validate` | Validate condition set YAML | --condition-set |
| `qca list-conditions` | List domain presets | --domain (optional filter) |

### 4.10 Frontend (React + TypeScript + Vite)

| File | Responsibility | Key Notes |
|------|---------------|-----------|
| `src/services/bert-engine.ts` | Transformers.js BERT model loading + CLS embedding extraction, Web Worker | bert-base-chinese model, ONNX Runtime Web backend |
| `src/services/bert-cache.ts` | IndexedDB persistent embedding cache | Caches model weights + pre-computed prototype embeddings |
| `src/services/pyodide.worker.ts` | Pyodide WASM worker | Runs Python engine in browser, communicates via message protocol |
| `src/experiment_engine/pyodide_handlers.py` | Python handlers invoked from worker | `handle_calibrate` (unified: raw+prototype), `handle_calibrate_prototype` (deprecated wrapper), `handle_embed_calibrate` (new: embedding-based calibrate) |

### 4.11 Deleted files (keyword matching, removed 2026-05-25)

| File | Status | Notes |
|------|--------|-------|
| `keyword_dict.py` | **DELETED** | Chinese keyword matching engine (character n-gram tokenizer) |
| `keyword_io.py` | **DELETED** | Keyword import/export functionality |
| `prototype_similarity.py` | **DELETED** | Bigram Jaccard prototype similarity engine (replaced by CosineSimilarityEngine) |

---

## 5. Key Design Decisions

### 5.1 Why BERT CLS embedding + cosine similarity instead of keyword matching?

**Keyword matching has been completely removed** (2026-05-25, 5-phase refactoring). BERT CLS embedding + cosine similarity is now the sole scoring method. Rationale:

- **Methodological**: In QCA, concept prototypes represent the theoretical ideal for each condition. BERT CLS embeddings capture the semantic meaning of both prototypes and citizen feedback texts. Cosine similarity between a text's embedding and a prototype centroid directly measures theoretical fit -- this aligns with QCA's calibration-by-theory principle.
- **Technical**: bert-base-chinese provides rich Chinese semantic representations that keyword n-gram matching cannot match. Mean pooling over all token embeddings produces a single dense vector per text. The prototype centroid (average of positive-example embeddings) defines the "ideal" for each condition.
- **Softmax calibration (tau=5.0)**: Raw cosine similarity [0.3, 0.9] is transformed via softmax(cos_sim * tau) to produce a sharper separation between matching and non-matching texts. This provides better discrimination than raw cosine scores while still feeding into the standard calibrate_direct/indirect/ragin pipeline.
- **Trade-off**: BERT inference is ~86x slower than keyword matching in WASM (CPU-only). This is mitigated by IndexedDB embedding caching (bert-cache.ts) and lazy loading.

### 5.2 Why Quine-McCluskey?

Standard algorithm in QCA literature (Ragin, Rihoux, Schneider & Wagemann). Deterministic, generates all prime implicants, acceptable complexity for typical QCA with 5-12 conditions. Pure Python self-implementation. Unit tests validated against Ragin (2008) Lipset dataset as gold standard.

### 5.3 Why keep Pipeline/Stage/Plugin abstractions?

QCA workflow is naturally pipeline-based: load -> calibrate -> analyze -> test -> visualize -> report. The existing framework's composite pattern, lifecycle management (setup/process/teardown), Rich progress bars, error handling, and parallel execution all map directly to QCA needs.

### 5.4 Fuzzy-set calibration three methods (fed by CosineSimilarityEngine raw scores)

- **direct** (direct method): Piecewise linear, given full_in/full_out/crossover three thresholds
- **indirect** (indirect method): Normalize to [0,1] first, then Log-Odds transform
- **ragin** (Ragin direct method): Logistic formula `exp(dev)/(1+exp(dev))` with qualitative anchors

All three methods now receive raw scores from `CosineSimilarityEngine.compute_raw_scores()` instead of the former `ChineseKeywordDictionary.match_corpus()`. The calibration methods themselves are unchanged -- only the upstream scoring engine changed.

### 5.5 Three QCA solutions

- **Complex solution**: Minimizes only empirically observed configuration rows
- **Parsimonious solution**: Includes "easy counterfactuals" (logical remainders consistent with theoretical expectations) as don't-care rows
- **Intermediate solution**: Only includes counterfactuals with clear directional expectations

---

## 6. Dependency Inventory

**Runtime** (pyproject.toml [project].dependencies):
numpy>=1.24, pydantic>=2.0, click>=8.0, pyyaml>=6.0, matplotlib>=3.7, plotly>=5.14, rich>=13.0

**Dev** ([project.optional-dependencies].dev):
pytest>=7.0, pytest-cov>=4.0, black>=23.0, ruff>=0.1, mypy>=1.0, pre-commit>=3.0

**Docs** ([project.optional-dependencies].docs):
mkdocs>=1.5, mkdocstrings[python]>=0.24

**Frontend** (package.json, independent): React 18 + TypeScript + Vite 5 + react-router-dom + Transformers.js (BERT)

---

## 7. Tests

| File | Coverage |
|------|----------|
| `tests/test_pipeline.py` | Stage/Pipeline lifecycle |
| `tests/test_io.py` | Readers/exporters/data sources |
| `tests/test_integration.py` | End-to-end pipeline |
| `tests/test_qca_core.py` | **QCA core module unit tests** (104 tests, 7 modules), Lipset dataset gold standard |
| `tests/test_viz.py` | Visualization renderers |
| `tests/test_algorithms.py` | Legacy algorithm tests (pending update to QCA tests) |
| `tests/test_report.py` | Report generation |
| **Run**: `uv run pytest` |
| **QCA standard validation**: Uses Ragin (2008) textbook Lipset dataset as gold standard benchmark |

---

## 8. User Preferences

- Project documentation in Chinese
- Docs prefer local MkDocs build validation, no need to push to GitHub Pages
- CLI defaults to Rich-formatted output
- All Python files explicitly use `encoding='utf-8'`
- Use `uv run python`, never bare `python`

---

## 9. Key Learnings

### Current (post-BERT-refactoring, 2026-05-26)

- **BERT + Prototype refactoring completed 2026-05-25 across 5 phases (~20 commits).** Keyword matching fully removed. BERT CLS embedding + cosine similarity is now the only scoring method. Files deleted: keyword_dict.py, keyword_io.py, prototype_similarity.py. New files: cosine_similarity.py, bert-engine.ts, bert-cache.ts. calibrator.py refactored to use CosineSimilarityEngine. ScoringSource enum reduced to PROTOTYPE only. Domains.py keyword presets are legacy (P1-B3 cleanup pending). KeywordEntry class in models/qca.py is legacy (P1-B6 cleanup pending).
- **The BERT-vs-keyword debate is resolved -- BERT won, keywords removed.** The earlier analysis (2026-05-24/25) documented the tension between theoretical operationalization (keywords) and semantic matching (BERT). User made the final decision: concept prototypes are the sole theoretical basis, BERT CLS + cosine similarity is the implementation.
- **Planning docs were out of sync with codebase (fixed 2026-05-26).** Prior to re-sync, P0-BERT was 70-80% functionally complete but listed as 0% in TODO.md. All 4 planning docs (TODO/FIXME/HACK/cerebrum) have been updated to reflect actual state. Cross-reference with file system when in doubt.

### Historical (pre-BERT-refactoring context, retained for reference)

- **BERT cannot fully replace keyword matching -- this is a methodological requirement, not a technical limitation** (historical, from 2026-05-24 pre-decision analysis): QCA calibration must be theory-based, not purely statistical. Keyword dictionaries are themselves the vehicle of "theoretical operationalization" -- each keyword and weight is an intentional theoretical choice. BERT cosine similarity is a statistical artifact of pre-training corpus distribution, not the researcher's theory. Removing keywords means removing the theoretical foundation of the analysis. **[Note: This analysis was superseded by the user's decision on 2026-05-25 to adopt BERT + Prototype as the sole approach.]**
- **BERT inference must execute on JS side, not in Pyodide** (historical, from 2026-05-24): transformers/torch/sentence-transformers cannot run in Pyodide WASM (require C++ extensions). BERT needs independent JS Web Worker with Transformers.js. **[Note: This was correct and is now implemented reality -- bert-engine.ts runs in a Web Worker.]**
- **bigram tokenization has a negation blind spot** (historical, from 2026-05-24, applies to deleted keyword_dict.py): "不满意" tokenized to ["不满", "满意"] allows "满意" to independently match the trust domain, causing semantic contamination between mutually exclusive condition pairs (dissatisfaction vs trust). This was a fundamental limitation of bigram tokenization. **[Note: This problem no longer exists because keyword matching has been fully removed. BERT embeddings are negation-aware.]**

---

## 10. Do-Not-Repeat

### Critical (still active)

- [2026-05-26] **memory.md will keep growing**: OpenWolf protocol appends one line per action; 1408 lines 126KB consumes ~39K tokens of context. Periodically archive old sessions (>2 weeks) to `memory-archive.md`. Current memory.md keeps only the most recent 1-2 days.
- [2026-05-26] **`administration: write` is not a valid GitHub Actions permission**: Writing `administration: write` in deploy.yml permissions block causes workflow YAML parse failure (HTTP 422: Unexpected value 'administration'), push-triggered run yields 0 jobs immediately. Legitimate permissions: `actions`, `checks`, `contents`, `deployments`, `environments`, `id-token`, `issues`, `discussions`, `packages`, `pages`, `pull-requests`, `repository-projects`, `security-events`, `statuses`. `administration` does not exist in any GitHub Actions documentation -- it is not a valid permission scope.
- [2026-05-25/26] **Agent completion claims are not trustworthy -- 6 independent confirmations**: FIXER/Phase agents claimed code modifications were done multiple times, but actual verification found zero file changes (`git diff --stat` empty, source files unmodified, `git log` no new commits). Manifestations: (1) completely fabricated modifications; (2) only modifying TODO.md to mark done without writing source code; (3) claiming commits in worktree but actually none. **Mandatory rule**: after an agent claims completion, MUST verify changes with Read/Grep/`git diff --stat`. FIXER->REVIEWER has a race condition, wait for FIXER to fully complete +5-10s before starting REVIEWER. Clean fabricated-completion worktree residue with `git worktree unlock` + `remove --force` + `git branch -D`.
- [2026-05-26] **GitHub Pages requires one-time manual enable in repository Settings**: workflow can push build artifacts to gh-pages branch, but repository Settings > Pages must be manually set to source = gh-pages branch (`/ (root)`). This operation cannot be automated via `gh api` or CI; it is a pure manual step.
- [2026-05-25] **Large task single agent = timeout + failure**: P1-4 (L level, 12+ files) single agent timed out incomplete. L-level tasks MUST be split into 2-3 file-level subtasks, executed by multiple agents in parallel, each handling disjoint file sets.
- [2026-05-25] **Reviewer agent has low ROI for frontend tasks**: Frontend P1 task quality gating is sufficient with `npm run build` (tsc + vite). Reviewer agent (5 min+) is only worthwhile for critical algorithm tasks.
- [2026-05-25] **Parallel agents modifying shared files causes change loss**: Phase 4 agent (UI integration) and Phase 5 agent (cleanup) ran in parallel, each modifying useQCAWorkflow.ts/DataInput.tsx/Settings.tsx. Phase 5's delete operations overwrote Phase 4's add operations, causing complete loss of BERT UI code. Agents with shared file dependencies MUST run serially; each phase agent completes + commits before starting next phase.
- [2026-05-24] **Planning doc statistics deviate immediately after multi-agent editing**: Statistics tables in TODO/FIXME/HACK files MUST be independently recomputed after each agent edit, not relying on incremental updates. A recent reconciliation found FIXME severity deviation of 3 items, HACK code item deviation of 1 item, TODO P1/P2 count deviation. When reconciling planning docs, always recalculate each priority/severity/category count from scratch rather than trusting existing statistics.

### Python/CLI

- [2026-05-24] pyproject.toml `long_description_content_type` field not supported by setuptools, already removed
- [2026-05-24] CLI `click.Choice([d.value for d in [...strings...]])` throws AttributeError (strings have no .value), use plain string lists directly
- [2026-05-24] `_print_fit_metrics` function must be defined at module level (cannot be nested inside train function)
- [2026-05-24] rf-string `\begin{center}` parsed as Python expression `{center}`, causing F821 error; use string concatenation instead
- [2026-05-24] Ruff RUF001 on Chinese punctuation (，。！？etc.) reporting ambiguous is expected behavior; was suppressed via per-file-ignore in keyword_dict.py **[Note: keyword_dict.py deleted, per-file-ignore may be removable]**
- [2026-05-24] **pre-commit version mismatch trap**: local `uv run ruff` and pre-commit hook ruff versions must match. When per-file-ignore references new rules (e.g. RUF043) but hook uses old version, it reports "Unknown rule selector". Fix: upgrade `.pre-commit-config.yaml` ruff `rev` to match `uv.lock` version.
- [2026-05-24] **PD901 rule removed in ruff 0.15.x**: if pyproject.toml globally ignores PD901, upgrading ruff reports "rules have been removed" warning. Remove deprecated rules from ignore list promptly.
- [2026-05-24] **Windows Python GBK trap also affects buglog.json**: `python -c "import json; ..."` defaults to GBK for file reading, causing UnicodeDecodeError. Always use `open(path, encoding='utf-8')`.
- [2026-05-24] **@staticmethod calling another @staticmethod needs ClassName.method()**: Cannot use self.method() in static method (no self parameter). Must use ClassName.method(). Misusing self. causes NameError.

### Frontend/Pyodide

- [2026-05-24] **npm ci failure masks subsequent TypeScript errors**: CI exits at npm ci failure step, tsc -b never executes. Fix lock file first to see actual TS compile errors. Should run `npm run build` locally before pushing.
- [2026-05-24] **package-lock.json out of sync with package.json trap**: Manual package.json edits without running `npm install`, directly committing old lock file. npm ci refuses to install when lock file versions exceed semver range. Must run npm install after dependency changes to refresh lock file.
- [2026-05-24] **Pyodide: never inject data into Python code via JS template literals**: `pyodide.runPython(\`x = ''''${json}\n''')` pattern is a code injection vulnerability. Attacker input `'''` escapes the Python string and executes arbitrary code. Safe approach: write data to VFS first with `pyodide.FS.writeFile('/tmp/xxx.json', jsonStr)`, then read in Python with `json.load(open('/tmp/xxx.json'))`.
- [2026-05-24] **Pyodide mountFromInline must write __init__.py**: Only creating directories (os.makedirs) does not make Python recognize them as packages. Must write `__init__.py` in each package directory. Omission causes `ModuleNotFoundError`.
- [2026-05-24] **PipelineStage type cross-validation**: Every time a new PipelineStage value is added, must simultaneously confirm all dispatch calls use that value (not hardcoded strings), otherwise TypeScript compiles but runtime semantics are wrong (e.g. 'running-robustness' used for counterfactuals).
- [2026-05-24] **pre-commit stash-conflict infinite loop**: During git commit, if unstaged changes exist, pre-commit hooks (ruff-format, end-of-file-fixer) auto-format, then unstash conflicts and reverts fixes, causing repeated commit failure. Solution: (1) PreToolUse hook (`.wolf/hooks/pre-commit.js`) added to auto `ruff format . && ruff check --fix . && git add -u` before each git commit; (2) if committing manually, ensure `git add -u` before commit.
- [2026-05-24] **Pyodide worker handler pattern**: All Python logic should go in `src/experiment_engine/pyodide_handlers.py` as independent functions, communicating with worker via `FS.writeFile -> runPythonAsync('import & call') -> FS.readFile` pattern. Never embed Python code strings in worker. Worker's `runHandler()` template function encapsulates this pattern.
- [2026-05-24] **pyodide.worker.ts original handleCalibrate had _fuzzy_data accumulation bug**: Variable initialized to None and never updated, causing only last sample to be processed, and json.dumps would fail. Correct approach: extract membership/case_ids/texts and rebuild FuzzySetData step by step.
- [2026-05-24] **qca_reporter.py class is QCALaTeXReporter not QCAReporter**: Hardcoded import name mismatch in worker causes ImportError.

### Historical bug fixes (apply to current or now-deleted code, kept for context)

- [2026-05-24] **counterfactual.py produce_parsimonious_solution algorithm error** (see FIXME-1): Parsimonious solution should include all logical remainders as don't-care rows. **[FIXED: 2026-05-24]**
- [2026-05-24] **calibrate_ragin implemented as piecewise linear instead of log-odds** (see FIXME-3): Docstring claims Ragin log-odds direct method but actually piecewise linear interpolation. **[FIXED: 2026-05-24]**
- [2026-05-24] **calibrator.py mixed scoring_source column index offset** (see FIXME-2): KEYWORD/HYBRID/PROTOTYPE mixing caused column misalignment. **[FIXED: 2026-05-24 -- NOTE: keyword/hybrid paths now deleted, this fix is moot]**
- [2026-05-24] **match_corpus() called redundantly per condition** (see FIXME-4): O(n_conditions x n_texts x n_keywords) redundancy. **[FIXED: 2026-05-24 -- NOTE: match_corpus() deleted with keyword_dict.py]**
- [2026-05-24] **pipeline Stage silently passes corrupted data after failure** (see FIXME-5): After Stage failure, Pipeline passes last good data to downstream. **[FIXED: 2026-05-24]**
- [2026-05-24] **robustness coverage_stability always 0** (see FIXME-6): `hasattr(tt, "solution_coverage")` always False. **[FIXED: 2026-05-24]**
- [2026-05-24] **robustness test_calibration_sensitivity actually membership perturbation** (see FIXME-7): Method perturbs all membership columns (including outcome). **[FIXED: 2026-05-24]**
- [2026-05-24] **robustness missing bootstrap resampling** (see FIXME-8): Docstring mentions but not implemented. **[FIXED: 2026-05-24]**
- [2026-05-24] **robustness default frequency threshold unreasonable for small N** (see FIXME-12): Default [1.0, 2.0, 3.0, 5.0] may exclude all rows for N<10. **[FIXED: 2026-05-24]**
- [2026-05-24] **qca_reporter.py LaTeX special characters unescaped** (see FIXME-10): `*` `~` `_` etc. directly inserted into LaTeX causing compile failure. **[FIXED: 2026-05-24]**
- [2026-05-24] **qca_reporter.py _robustness_section empty list IndexError** (see FIXME-11): `t.solution_stability[0]` crashes when list empty. **[FIXED: 2026-05-24]**
- [2026-05-24] **minimization.py hash-based identity unreliable** (see FIXME-21): `hash((imp1, tuple(cov1)))` has theoretical collision risk and PYTHONHASHSEED cross-process instability. **[FIXED: 2026-05-24]**
- [2026-05-24] **QM no k<=12 upper bound guard causing browser WASM hang** (see P0-1): minimize() no condition count check, k>12 2^k explosion blocks single-threaded WASM. **[FIXED: 2026-05-24]**
- [2026-05-24] **counterfactual.py theoretical_expectation always None** (see FIXME-9): `theo_exp` initialized to None and never assigned. **[FIXED: 2026-05-24]**
- [2026-05-24] **sufficiency.py silently skips on condition name mismatch** (see FIXME-13): `_compute_term_membership` silent pass on mismatch hides bugs. **[FIXED: 2026-05-24]**

---

## 11. Decision Log

### 2026-05-26

- **Planning docs (TODO/FIXME/HACK) re-synced with actual codebase state.** Significant disconnect found: P0-BERT was 70-80% functionally complete but all 12 P0-B tasks listed as 0% unchecked in TODO.md. Stats corrected from 52→36→34 remaining. 6 MOOT FIXME items removed (deleted files). 6 HACK items resolved. 8 subagents dispatched (1 plan + 4 fixer + 1 reviewer across 2 phases).
- **P1-B3 + P1-B6 completed**: domains.py refactored from keyword presets to prototype text templates (5 domains, each condition 2 prototypes: 1 positive + 1 negative). KeywordEntry class removed from models/qca.py. ConditionDefinition.keywords field removed. condition.py keyword dead code cleaned (add_keyword, _kw_to_dict, hybrid weights). Zero KeywordEntry references remain in codebase. 531 tests pass.

### 2026-05-25

- **BERT+Prototype refactoring completed across 5 phases (~20 commits).** Keyword matching fully removed. BERT CLS embedding + cosine similarity is now the sole scoring method. ScoringSource reduced to PROTOTYPE only. Files deleted: keyword_dict.py, keyword_io.py, prototype_similarity.py. New files: cosine_similarity.py (BERT CLS cosine similarity engine), bert-engine.ts (Transformers.js BERT model), bert-cache.ts (IndexedDB embedding cache). calibrator.py refactored to use CosineSimilarityEngine instead of ChineseKeywordDictionary. pyodide_handlers.py: handle_embed_calibrate added, handle_calibrate unified (raw+prototype), handle_calibrate_prototype is backward-compat deprecated wrapper. Remaining cleanup: KeywordEntry in models/qca.py (P1-B6), domains.py keyword presets (P1-B3).
- **BERT decision finalized -- BERT CLS + cosine similarity replaces keyword matching entirely.** User explicitly directed abandoning keyword recognition approach. Concept prototypes are the sole theoretical foundation of QCA. BERT CLS embedding + cosine similarity (Softmax tau=5.0) completely replaces keyword matching. Architecture: Hybrid Transformers.js + Pyodide. Model: bert-base-chinese. Detailed spec in `.wolf/bert-prototype-algorithm-spec.md`.

### 2026-05-24

- **Three-role review completed**: Dispatched 3 subagents as technical advisor (architecture optimization), customer representative (requirements), reviewer (code evaluation). Produced TODO.md (51 items), FIXME.md (22 items), HACK.md (12 items). Found 5 critical algorithm bugs. Accepted by reviewer subagent.
- **Three-review reconciliation**: Three agents independently edited TODO/FIXME/HACK. Reconciliation found: (1) all statistics inaccurate due to independent edits; (2) P2-20 incorrectly marked completed but FIXME-22 still open; (3) P1-15/16/17 already implemented but planning docs not updated. Fix: recalculated all statistics, corrected checkboxes. Commit bfbd3e2.
- **Added prototype matching calibration mode**: Users can provide concept prototypes via "condition, prototype text, membership(0/1)" format. **[Note: The bigram Jaccard implementation (prototype_similarity.py) has been replaced by BERT CLS + cosine similarity (cosine_similarity.py). The concept of prototype-based scoring remains, but the implementation changed.]**
- Refactored experiment-engine from generic "algorithm experiment framework" to domain-specific QCA text analysis system.
- Deleted `algorithms/linear_regression.py` and `algorithms/kmeans.py` -- unrelated to QCA.
- CLI entry point renamed from `experiment-engine` to `qca`.
- **Adopted Pyodide browser-side execution**: Compile QCA Python engine to WebAssembly via Pyodide for browser execution, zero backend server.
- **Pyodide CDN strategy**: Pyodide core 50MB from jsDelivr CDN, only ~80KB Python source self-hosted.
- **Single-repo gh-pages deployment**: Chose Option B (same repo gh-pages branch). URL: `qhWangAntoneva.github.io/experiment-engine/`
- **pydantic v2 -> dataclass dual-backend**: pydantic-core is Rust binary, cannot run in Pyodide. `IN_BROWSER` gated model backend selection: CLI retains Pydantic v2, browser uses dataclass shim.
- **Plotly.js replaces matplotlib**: Browser-side uses Plotly only.
- **Fixed FIXME-1/HACK-5/FIXME-17/FIXME-18**: Rewrote produce_parsimonious_solution to include all logical remainders as don't-care. Extended QuineMcCluskey.minimize() with dont_care_minterms.
- **Fixed FIXME-2/3/4/20 (calibrator.py four bugs)**: calibrate_ragin rewritten as logistic, column index offset fixed, match_corpus cached once, ~60 lines deduplicated via _process_core(). All 360 tests pass.
- **Fixed FIXME-9 (counterfactual.py theoretical_expectation always None)** and **FIXME-13 (sufficiency.py silent skip on condition name mismatch)**.
- **Fixed FIXME-6/7/8/12 (robustness.py four bugs)**: coverage_stability, membership perturbation, bootstrap, frequency thresholds. All 361 tests pass.
- **Fixed P0-1/FIXME-10/FIXME-11/FIXME-21 (cross-file four bug batch fix)**: QM k<=12 guard, LaTeX escaping, empty solution_stability guard, hash->ID identity. All 361 tests pass.
- **P1-14/FIXME-16 models.py split into package**: Split 9500-token monolithic models.py into framework/qca/training/__init__.py. 100% backward compatible. 465 tests pass.
- **P1-15 calibrator strategy pattern refactoring (HACK-6)**: Created strategies.py with 5 strategy classes. calibrator.py _apply_calibration() uses strategy lookup. 465 tests pass. HACK-6 resolved.
- **BERT-vs-keyword architecture decision analysis complete**: Conclusion at the time -- BERT is complement not replacement. **[Note: This conclusion was reversed on 2026-05-25.]**
