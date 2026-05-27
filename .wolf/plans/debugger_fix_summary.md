# Debugger Fix Summary

## Root Cause #1 (CRITICAL): Missing `'wasm-unsafe-eval'` in CSP
- **File**: `index.html`
- **Fix**: Added `'wasm-unsafe-eval'` to `script-src` directive in CSP meta tag.
- **Why**: Chrome 130+ blocks WASM compilation in module workers without this directive. Both Pyodide (CPython WASM) and Transformers.js (ONNX WASM) require it.

## Root Cause #2: `worker-src` missing CDN origin
- **File**: `index.html`
- **Fix**: Added `https://cdn.jsdelivr.net` to `worker-src` directive.
- **Why**: Some browsers check `worker-src` (not `script-src`) for dynamic `import()` inside workers.

## Root Cause #3: No `unhandledrejection` handler in worker
- **File**: `src/services/pyodide.worker.ts`
- **Fix**: Added `self.onunhandledrejection` handler that logs the rejection reason and calls `event.preventDefault()` to prevent propagation to `self.onerror` with sanitized messages.

## Root Cause #4: Poor error message extraction in `pyodide.ts`
- **File**: `src/services/pyodide.ts`
- **Fix**: Changed `worker.onerror` handler to use `err.error?.stack || err.error?.message || err.message` instead of just `err.message`.
- **Why**: `err.message` is sanitized ("Script error.") for cross-origin errors. `err.error` contains the actual Error object with stack trace.

## Root Cause #5: Pipeline buttons stay disabled / Dashboard shows 0
- **Result**: NOT a bug in the current codebase. After loading sample data, `texts.length` is properly set to 30 and the buttons' disabled condition (`isRunning || isBertLoading || isEmbedding || texts.length === 0`) correctly evaluates to `false`. Dashboard showing "Cases Analyzed: 0" and "Conditions Defined: 0" is EXPECTED behavior before calibration runs. The stale closure bug affecting `handleCalibrate`/`handleRunPipeline` with `importedConditionSet` was already fixed in a previous session (see cerebrum Do-Not-Repeat entry [2026-05-27]).

## Root Cause #6: Raw i18n keys exposed
- **File**: `src/i18n/translations.ts`
- **Fix**: Added `importCsvJson`, `exportCsv`, and `exporting` keys to the `TranslationDict` interface `dataInput` section, and added both Chinese and English translations.
- **Details**: The buttons showed raw keys `dataInput.importCsvJson`, `dataInput.exportCsv`, and `dataInput.exporting` instead of translated text. Added `importCsvJson: '导入 CSV/JSON'` / `'Import CSV/JSON'`, `exportCsv: '导出 CSV'` / `'Export CSV'`, `exporting: '导出中...'` / `'Exporting...'`.

## Verification Results
- `npm run build` (tsc -b + vite build): PASSED
- `dist/index.html` CSP verified: Contains both `'wasm-unsafe-eval'` in `script-src` and `https://cdn.jsdelivr.net` in `worker-src`
- Only build warning: chunk size warnings (expected for plotly and onnxruntime-web), no errors
