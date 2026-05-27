# Worker Error Analysis: "Unknown Worker Error"

> Analysis date: 2026-05-27
> Target: `https://qhwangantoneva.github.io/experiment-engine/`
> Files examined: `pyodide.ts`, `pyodide.worker.ts`, `bert-engine.ts`, `DataInput.tsx`, `Settings.tsx`, `Dashboard.tsx`, `usePyodide.ts`, `useQCAWorkflow.ts`, `vite.config.ts`, `index.html`, `deploy.yml`, `package.json`, bundled `dist/` output

---

## 1. Error Mechanism

The "unknown worker error" message originates from exactly one location:

**`src/services/pyodide.ts:440-446`** -- the `worker.onerror` fallback handler:

```typescript
this.worker.onerror = (err) => {
  console.error('Pyodide worker error:', err);
  this.setState({
    status: 'error',
    error: err.message || 'Unknown worker error',  // <-- THE SOURCE
  });
};
```

This handler fires ONLY when an **uncaught error** propagates to the Web Worker's global scope, bypassing all try/catch blocks in:
- `self.onmessage` (worker.ts:138-225) -- outer dispatch try/catch
- `handleInit()` (worker.ts:229-311) -- inner init try/catch
- `handleInitBert()` (worker.ts:590-606) -- inner BERT try/catch

For an error to reach `worker.onerror`, it must be **completely unhandled** within the worker -- typically a top-level exception during module evaluation, an unhandled promise rejection, or a CSP/WASM instantiation failure that the browser throws directly.

---

## 2. Possible Root Causes (Ordered by Likelihood)

### Root Cause #1 (PRIMARY): Missing `'wasm-unsafe-eval'` in CSP blocks WASM instantiation in the Worker

**Affected code path:**
- `pyodide.worker.ts:239` -- `await import('https://cdn.jsdelivr.net/.../pyodide.mjs')` loads Pyodide
- Pyodide internally calls `WebAssembly.instantiate()` or `WebAssembly.instantiateStreaming()` to load the CPython WASM module
- If the CSP blocks WASM compilation, the WASM instantiation throws an uncatchable error

**Why it triggers "unknown worker error":**
Chrome (v127+, which includes May 2026 Chrome >= 130) enforces `'wasm-unsafe-eval'` in `script-src` when a CSP is present. Without it, `WebAssembly.instantiate()` throws a `WebAssembly.CompileError` or `TypeError`. In a module worker context, this error may bypass JavaScript try/catch blocks when the WASM compilation happens as a side effect of `loadPyodide()`'s internal initialization (not directly in a JavaScript `await` chain the worker can catch).

**How to verify:**
1. Open the deployed site in Chrome DevTools
2. Go to Console, look for:
   - `WebAssembly.CompileError: Wasm code generation disallowed by embedder`
   - `TypeError: WebAssembly is not allowed in this context`
   - Or a CSP violation in the Issues panel: `"'wasm-unsafe-eval'" is not in script-src`
3. Check `chrome://net-internals/#csp` (Chrome CSP debugging)

**Current CSP (index.html:30-38):**
```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' https://cdn.jsdelivr.net;
  connect-src 'self' https://cdn.jsdelivr.net https://huggingface.co https://cdn-lfs.huggingface.co;
  worker-src 'self' blob:;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data:;
  font-src 'self';
" />
```

Note: `'wasm-unsafe-eval'` is **absent** from `script-src`. This affects both Pyodide (CPython WASM) and Transformers.js (ONNX Runtime WASM backend).

---

### Root Cause #2 (HIGH): `worker-src` does not cover dynamic `import()` of cross-origin modules inside the Worker

**Affected code path:**
- `pyodide.worker.ts:239` -- `await import('https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.mjs')`
- CSP `worker-src 'self' blob:` allows creating the worker from same-origin
- CSP `script-src 'self' https://cdn.jsdelivr.net` should allow the import
- BUT: Some browsers check BOTH `worker-src` AND `script-src` for module imports in workers

**Why it triggers "unknown worker error":**
Firefox and some Chromium versions check `worker-src` (not `script-src`) for `import()` of ES modules inside a dedicated worker. If `worker-src` doesn't include the CDN origin, the import is blocked with a CSP violation. The violation event is dispatched asynchronously and may fire after the try/catch has exited, landing on `worker.onerror`.

**How to verify:**
1. Open deployed site in Firefox DevTools
2. Look for CSP violation in Console: `"Content Security Policy: The page's settings blocked the loading of a resource at https://cdn.jsdelivr.net/..."` with directive `worker-src`
3. In Chrome, check `chrome://net-export/` for CSP violation events

---

### Root Cause #3 (HIGH): Unhandled promise rejection in the Worker during Pyodide initialization

**Affected code path:**
- `pyodide.worker.ts:244-246` -- `pyodide = await loadPyodide({ indexURL: '...' })`
- `loadPyodide()` internally creates multiple Promise chains for:
  - WASM module loading
  - Filesystem initialization (`.data` file mounting)
  - Package fetching
  - Internal worker thread pools

**Why it triggers "unknown worker error":**
Pyodide's initialization is complex and involves many asynchronous operations. If one internal Promise rejects without being caught (e.g., a network failure for a sub-resource that doesn't bubble up to the main `loadPyodide()` promise), the rejection becomes an unhandled promise rejection. In Web Workers, unhandled rejections fire the `self.onerror` handler, which propagates to the main thread's `worker.onerror`.

**How to verify:**
1. Open deployed site, watch for `"Unhandled Promise Rejection"` in Console
2. Check the Network tab for failed requests to `cdn.jsdelivr.net` (e.g., 404 for `.data` or `.wasm` files)
3. In the Worker's context, check `self.onunhandledrejection` (not currently handled in the worker code)

---

### Root Cause #4 (MEDIUM): experiment_engine.tar.gz fetch failure cascades to uncaught Python ImportError

**Affected code path:**
- `pyodide.worker.ts:322-330` -- `fetch(tarUrl)` for `experiment_engine.tar.gz`
- On fetch failure, `mountFromInline()` creates EMPTY package directories
- When `handleCalibrate` calls `runHandler` with `from experiment_engine.pyodide_handlers import handle_calibrate`, the import fails
- The try/catch in `handleCalibrate` (worker.ts:407-433) catches this and returns `calibrate-error`

**Why it DOESN'T directly cause "unknown worker error":**
The Python ImportError IS caught by `handleCalibrate`'s try/catch. BUT: if `pyodide.runPythonAsync()` throws in a way that Pyodide doesn't correctly return (e.g., the Python WASM runtime crashes rather than throwing a Python exception), the error may bypass the try/catch.

**How to verify:**
1. Check Network tab: does `GET /experiment-engine/py/experiment_engine.tar.gz` return 200?
2. Verify the file exists in the Pages deployment artifact
3. Check if the tar.gz extracts correctly (try locally)

---

### Root Cause #5 (MEDIUM): `@xenova/transformers` SharedArrayBuffer crash during BERT initialization

**Affected code path:**
- `pyodide.worker.ts:592` -- `const bertEngine = new BertEngine()`
- `bert-engine.ts:150` -- `env.allowLocalModels = false`
- ONNX Runtime Web internally creates `SharedArrayBuffer` for WASM memory

**Why it triggers "unknown worker error":**
ONNX Runtime Web (used by `@xenova/transformers` v2.17.2) tries to allocate a `SharedArrayBuffer` for WASM thread support during `pipeline('feature-extraction', name, ...)`. On GitHub Pages (no `Cross-Origin-Opener-Policy: same-origin` header), `new SharedArrayBuffer()` throws a `TypeError: SharedArrayBuffer requires cross-origin isolation`. If this throw happens during the `pipeline()` constructor (before the try/catch in `loadModel()`), it becomes an uncaught error.

Note: This ONLY affects BERT init, not Pyodide init. So it is a SECONDARY cause, explaining the "calibrating BERT model" failure but not the initial "loading analysis engine" failure.

**How to verify:**
1. Check browser console for `"SharedArrayBuffer requires cross-origin isolation"`
2. Check `self.crossOriginIsolated` in the Worker -- will be `false` on GitHub Pages

---

### Root Cause #6 (LOW): TypeScript build error -- `import.meta.env.BASE_URL` type in Worker

**Affected code path:**
- `pyodide.worker.ts:319-320` -- `import.meta.env?.BASE_URL`
- `vite.config.ts:22` -- `worker: { format: 'es' }`

**Why it might contribute:**
The `import.meta.env.BASE_URL` reference in the worker uses optional chaining (`?.`) which implies BASE_URL might be undefined. Vite replaces this at build time with the literal string `/experiment-engine/`. The bundled output confirms this works (verified by checking the minified worker code). Not a direct cause.

---

## 3. Recommended Fix

### Fix #1: Add `'wasm-unsafe-eval'` to CSP `script-src` (CRITICAL)

**File:** `index.html:32`

Change:
```html
script-src 'self' https://cdn.jsdelivr.net;
```
To:
```html
script-src 'self' https://cdn.jsdelivr.net 'wasm-unsafe-eval';
```

This allows WASM compilation in worker contexts, which is required for:
- Pyodide's CPython WASM runtime
- Transformers.js ONNX Runtime WASM backend

### Fix #2: Add `https://cdn.jsdelivr.net` to `worker-src` (RECOMMENDED)

**File:** `index.html:34`

Change:
```html
worker-src 'self' blob:;
```
To:
```html
worker-src 'self' blob: https://cdn.jsdelivr.net;
```

This ensures cross-browser compatibility for dynamic `import()` of CDN modules inside the Worker. While `script-src` should cover this per spec, some browsers check `worker-src` for module imports.

### Fix #3: Add `Cross-Origin-Isolation` headers (OPTIONAL, for BERT performance)

If COOP/COEP headers are set (GitHub Pages does not support custom headers via the meta-tag approach), SharedArrayBuffer becomes available and ONNX Runtime can use multi-threaded WASM. However, this is not feasible on GitHub Pages without custom server configuration.

Alternative: Ensure Transformers.js uses the single-threaded WASM backend by default. This is already the behavior when cross-origin isolation is missing, but an explicit env flag improves reliability:

**File:** `bert-engine.ts:150`, add before `pipeline()`:
```typescript
env.backends.onnx.wasm.wasmPaths = undefined; // USE single-threaded WASM
env.backends.onnx.numThreads = 1; // Explicitly single-threaded
```

### Fix #4: Add `unhandledrejection` handler in the Worker (DEFENSE-IN-DEPTH)

**File:** `pyodide.worker.ts`, after the existing `self.onmessage` (around line 216):

```typescript
self.onunhandledrejection = (event: PromiseRejectionEvent) => {
  const msg = event.reason?.message || String(event.reason) || 'Unhandled promise rejection';
  respond({ type: 'init-error', error: `Worker unhandled rejection: ${msg}` });
  log('error', `Unhandled rejection: ${msg}`);
};
```

This catches unhandled promise rejections that would otherwise fire `worker.onerror` with a sanitized message.

### Fix #5: Improve `worker.onerror` error message extraction (DEFENSE-IN-DEPTH)

**File:** `src/services/pyodide.ts:440-446`

Change:
```typescript
this.worker.onerror = (err) => {
  console.error('Pyodide worker error:', err);
  this.setState({
    status: 'error',
    error: err.message || 'Unknown worker error',
  });
};
```
To:
```typescript
this.worker.onerror = (err: ErrorEvent) => {
  console.error('Pyodide worker error:', err);
  const detail = err.error?.stack || err.error?.message || err.message || '';
  const location = err.filename ? `${err.filename}:${err.lineno}:${err.colno}` : '';
  this.setState({
    status: 'error',
    error: `Worker error: ${detail || location || 'Unknown worker error'}`,
  });
};
```

This extracts the actual error stack trace (from `err.error`) rather than just `err.message`, which is sanitized for cross-origin errors.

---

## 4. Verification Steps

### Step 1: CSP validation
- Deploy the fix with updated `script-src` including `'wasm-unsafe-eval'`
- Open `https://qhwangantoneva.github.io/experiment-engine/` in a fresh Chrome incognito window
- Open DevTools > Console
- Click "Load Engine" on the Dashboard
- Expected: Pyodide initializes successfully (progress messages appear, status becomes "ready")

### Step 2: BERT initialization
- After Step 1 succeeds, navigate to DataInput page
- Click "Load BERT Model"
- Expected: BERT model downloads and initializes successfully
- Check Network tab for `huggingface.co` and `cdn-lfs.huggingface.co` requests

### Step 3: Cross-browser testing
- Test in Chrome (primary target, May 2026 Chrome >= 130)
- Test in Firefox (different CSP enforcement)
- Test in Edge (Chromium-based, same CSP as Chrome)

### Step 4: SharedArrayBuffer verification
- In the Worker's DevTools console, run `self.crossOriginIsolated`
- Expected: `false` (this is fine as long as WASM works without it)
- Check that `new SharedArrayBuffer(1024)` throws (this is expected without COOP/COEP)

### Step 5: experiment_engine.tar.gz verification
- Fetch `https://qhwangantoneva.github.io/experiment-engine/py/experiment_engine.tar.gz` in browser
- Expected: 200 response, valid gzip archive
- Size should be > 0 bytes (verify in deploy logs)

### Step 6: Full pipeline test
- Load sample data on DataInput page
- Click "Calibrate"
- Expected: Calibration completes, fuzzy membership matrix appears
- Click "Run Full Pipeline"
- Expected: Analysis completes, navigate to Results page

---

## Appendix A: Key Files

| File | Role | Path |
|------|------|------|
| CSP definition | Meta tag CSP | `index.html:30-38` |
| Bridge class | Worker lifecycle, error handling | `src/services/pyodide.ts` |
| Worker logic | Pyodide init, message dispatch | `src/services/pyodide.worker.ts` |
| BERT engine | Transformers.js wrapper | `src/services/bert-engine.ts` |
| Init trigger | Dashboard "Load Engine" button | `src/pages/Dashboard.tsx:128-134` |
| Calibration trigger | DataInput "Calibrate" button | `src/pages/DataInput.tsx:665-696` |
| BERT init trigger | Settings page BERT load | `src/pages/Settings.tsx:216-225` |
| Orchestration | useQCAWorkflow hook | `src/hooks/useQCAWorkflow.ts` |
| Bridge hook | usePyodide hook | `src/hooks/usePyodide.ts` |
| Build config | Vite worker format, base URL | `vite.config.ts` |
| Deploy pipeline | GitHub Actions | `.github/workflows/deploy.yml` |

## Appendix B: Deployed Bundle Confirmation

Confirmed from local `dist/`:
- Worker bundle: `dist/assets/pyodide.worker-DdnAbkTI.js` (831 KB) -- exists, bundled correctly
- BASE_URL in worker: replaced with `"/experiment-engine/"` -- confirmed in minified code
- CDN URL: `import("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.mjs")` -- present in minified code
- indexURL: `"https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"` -- present in minified code
- tar.gz URL: `"/experiment-engine/py/experiment_engine.tar.gz"` -- present in minified code
- No `dist/py/` locally (created only during CI)
- CSP meta tag present in `dist/index.html` with same content as source
- Script tags include `crossorigin` attribute (standard for Vite module scripts)
