# Local Reproduction Report: 30-Sample Loading Crash

**Date:** 2026-05-27
**Test Environment:** Local Vite dev server (port 3100) with Playwright headless Chromium
**Branch:** master (worktree)

---

## Test Results Summary

| Step | Result | Time |
|------|--------|------|
| Page load | PASS | 2s |
| Engine init (Load Engine click) | PASS | 6s |
| 30 Sample Cases loading | **FAIL** | Silent failure, error in validation card |
| Calibrate button | Disabled (no data loaded) | N/A |

---

## Error Detail

The exact error rendered in the React validation card after clicking "Load 30 Sample Cases":

```
Error: Corpus loading failed: Traceback (most recent call last):
  File "/lib/python312.zip/_pyodide/_base.py", line 597, in eval_code_async
    await CodeRunner(
  File "/lib/python312.zip/_pyodide/_base.py", line 411, in run_async
    coroutine = eval(self.code, globals, locals)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<exec>", line 1, in <module>
ModuleNotFoundError: No module named 'experiment_engine.pyodide_handlers'
```

**Root cause:** `ModuleNotFoundError: No module named 'experiment_engine.pyodide_handlers'`

---

## Root Cause Analysis

The crash follows this chain:

1. **Engine init succeeds.** Clicking "Load Engine" successfully:
   - Downloads Pyodide runtime from jsDelivr CDN
   - Installs all required packages: numpy, pydantic, pyyaml, micropip, rich
   - All packages confirmed loaded in console logs
   - Button changes to "Engine Ready" at ~6s

2. **Mount project modules fails silently.** The `mountProjectModules()` function in `pyodide.worker.ts`:
   - Fetches `/py/experiment_engine.tar.gz` from the base URL
   - In the deployed site, this should be `experiment-engine/py/experiment_engine.tar.gz`
   - In dev mode, it fetches `/py/experiment_engine.tar.gz` which returns **HTTP 200 with HTML content** (Vite's SPA fallback serves index.html for unknown routes)
   - `resp.ok` is `true` (status 200), so the code proceeds to extract HTML as tar.gz
   - Python's `tarfile.extractall()` fails on HTML content
   - The catch block falls back to `mountFromInline()`

3. **`mountFromInline()` creates empty directories only.** The fallback function only creates Python package directories with empty `__init__.py` files. It does NOT copy the actual Python source files into Pyodide's VFS.

4. **Loading 30 samples triggers a Python import that fails.** When the user clicks "Load 30 Sample Cases":
   - `DataInput.tsx` calls `loadCorpus()` which sends `load_corpus` message to the worker
   - The worker calls `runHandler()` which runs:
     ```
     from experiment_engine.pyodide_handlers import handle_load_corpus; ...
     ```
   - Python raises `ModuleNotFoundError: No module named 'experiment_engine.pyodide_handlers'`
   - The error is caught and sent as `corpus-error` via `postMessage`
   - The bridge rejects the promise, the React error handler sets a validation message
   - The user sees "Error: Corpus loading failed: ..." in a red card

5. **Calibrate button remains disabled** because the `texts` array is empty (no data loaded).

---

## Console Log Analysis

### Package Loading (all successful)
```
[log] Loading numpy
[log] Loaded numpy
[log] Loading annotated-types, pydantic, pydantic_core, typing-extensions
[log] Loaded annotated-types, pydantic, pydantic_core, typing-extensions
[log] Loading pyyaml
[log] Loaded pyyaml
[log] Loading micropip, packaging
[log] Loaded micropip, packaging
[log] Loading rich
[log] Loaded rich
```

### Error Counts
- **Page-level errors:** 0
- **Console errors:** 0
- **Console warnings:** 2 (React Router Future Flag warnings — harmless)
- **Network failures:** 0
- **HTTP failures:** 49 (all 304 NOT MODIFIED from Vite HMR — harmless)
- **ModuleNotFoundError (in console):** 0 (errors go through postMessage, not console)
- **CSP violations:** 0
- **Worker init errors:** 0
- **CDN failures:** 0

---

## Key Observations

### 1. Error visibility problem
The most critical issue is that **worker errors are silently swallowed**. The error chain is:
- Worker: Python `ModuleNotFoundError` → caught by `handleLoadCorpus`'s try/catch
- Worker: sends `corpus-error` via `respond()` → `self.postMessage()`
- Bridge: receives `corpus-error` → rejects the `send()` promise
- React: `handleLoadSampleData`'s catch sets `setValidationMessage()`
- User: sees a red validation card, but the error message is a Python traceback that is hard to understand

No `console.error()` is called anywhere in this chain. The error never appears in the browser's developer console.

### 2. The `py/experiment_engine.tar.gz` bundle does not exist in the repo
The `py/` directory is not tracked by git and does not exist on disk. The production deploy likely generates this via CI. In dev mode, there is no fallback that provides the actual Python module files.

### 3. `mountFromInline()` is insufficient
The `mountFromInline()` function only creates empty directory structure:
```python
_packages = [
    '/src/experiment_engine',
    '/src/experiment_engine/qca_engine',
    '/src/experiment_engine/qca_engine/advanced',
    '/src/experiment_engine/text_calibration',
    '/src/experiment_engine/report',
    '/src/experiment_engine/viz',
    '/src/experiment_engine/io',
    '/src/experiment_engine/core',
]

for _pkg in _packages:
    os.makedirs(_pkg, exist_ok=True)
    _init = os.path.join(_pkg, '__init__.py')
    if not os.path.exists(_init):
        with open(_init, 'w') as f:
            f.write('# auto-generated package init\n')
```

It creates empty `__init__.py` files but does NOT write the actual module source files (e.g., `pyodide_handlers.py`, `calibrator.py`, etc.). Any Python import of these modules will fail with `ModuleNotFoundError`.

---

## Previously Deployed Fixes — Verification

| Fix | Status | Notes |
|-----|--------|-------|
| pydantic package install | WORKING | `Loaded pydantic` confirmed in logs |
| CSP `wasm-unsafe-eval` | WORKING | No CSP violations detected |
| Worker error handling | PARTIAL | Worker errors are caught but only shown as validation message, not logged |
| rich package install | WORKING | `Loaded rich` confirmed in logs |

The previously deployed fixes addressed package installation and CSP but did NOT address the fundamental issue that `mountFromInline()` does not provide the actual Python module files.

---

## Recommended Fix

The `mountFromInline()` function needs to be extended to write the actual Python source files into Pyodide's VFS. The approach would be:

1. **For dev mode:** Read `src/experiment_engine/` files from the filesystem (or have a build step that creates a JSON manifest of file contents), then write them into Pyodide's VFS during `mountFromInline()`.

2. **Alternative for dev mode:** Have the worker fetch each Python file from the Vite dev server individually instead of relying on the tar.gz bundle.

3. **Better error logging:** Add `console.error()` calls in the bridge's error handling paths so that worker errors are visible in the browser's developer console.

4. **Short-term fix:** Modify `mountFromInline()` to accept file content data (via the init request payload) and write all Python module files to Pyodide's VFS before setting `isReady = true`.
