# HACK -- QCA Analysis Tool

> Last updated 2026-05-26
> HACK records **intentional design trade-offs / temporary solutions** (not bugs) that need future reconsideration.
> 10 resolved entries removed 2026-05-26. Only active trade-offs remain.

---

## Architecture

### HACK-2: Pyodide CDN strategy -- 50MB core loaded from jsDelivr

**Location**: `src/pyodide/engine.ts`, `.github/workflows/deploy.yml`
**Risk**: CDN outage makes the tool completely unusable. jsDelivr may be slow for users in mainland China.
**When to revisit**: Moving off GitHub Pages hosting or packaging as Electron desktop app.
**Source**: cerebrum.md decision log, customer#S4

### HACK-3: pydantic v2 / dataclass dual-backend not implemented

**Location**: `src/experiment_engine/models.py`
**Risk**: pydantic-core Rust binary compatibility in Pyodide is not well-tested; future version upgrades may break.
**When to revisit**: If pydantic-core causes issues in Pyodide, or WASM bundle size needs reduction.
**Source**: cerebrum.md decision log, technical advisor

### HACK-4: All QCA analysis runs in a single Web Worker thread

**Location**: `src/services/pyodide.worker.ts`
**Risk**: Large datasets (10000+ texts) may take minutes to process since no multi-core parallelism is used.
**When to revisit**: When browsers support SharedArrayBuffer + Pyodide multithreading, or migration to server-side.
**Source**: architecture analysis

---

## Code

### HACK-7: DataInput.tsx hardcodes the default condition set YAML template

**Location**: `src/pages/DataInput.tsx:34-100`
**Risk**: Frontend YAML template and Python `domains.py` presets must be manually kept in sync -- mismatch causes incorrect keywords in analysis.
**When to revisit**: Implement TODO P1-16 (unify frontend parsing in Pyodide Worker).
**Source**: technical advisor#7

### HACK-9: PluginRegistry global singleton

**Location**: `src/experiment_engine/plugins.py:77-238`
**Risk**: pytest-xdist parallel tests may interfere with each other; cannot run two independent QCA pipelines in one process.
**When to revisit**: Before introducing parallel testing or multi-tenant scenarios. @see TODO P2-15.
**Source**: technical advisor#9

### HACK-10: Frontend parseTextContent() duplicates backend TextCorpusReader

**Location**: `src/pages/DataInput.tsx:120-168`, `src/experiment_engine/io/readers.py`
**Risk**: CSV escaping and encoding handling may produce divergent results between frontend pre-check and backend parsing.
**When to revisit**: Implement TODO P1-16.
**Source**: technical advisor#7

### HACK-13: Domain presets hardcoded in domains.py

**Location**: `src/experiment_engine/text_calibration/domains.py`
**Risk**: Researcher domain knowledge cannot easily be added; custom preset override behavior is opaque.
**When to revisit**: Implement TODO P1-34 + P1-1 (frontend condition editor + localStorage persistence + "restore defaults").
**Source**: customer representative analysis, reviewer#2026-05-24

---

## Tests

### HACK-12: Zero frontend automated tests

**Location**: `src/pages/`, `src/components/`, `src/hooks/`, `src/store/`
**Risk**: State management bugs (e.g. bug-010, bug-011) are hard to catch in code review and only surface during manual testing.
**When to revisit**: Implement TODO P2-18.
**Source**: technical advisor#12

---

## Stats

| Category | Count |
|----------|-------|
| Architecture | 3 |
| Code | 4 |
| Tests | 1 |
| **Total** | **8** (all unresolved) |
