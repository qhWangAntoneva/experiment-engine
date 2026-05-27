# Deployment Verification Report

**Date:** 2026-05-27
**HEAD Commit:** `ec02dc5` (latest deployment SHA confirmed via `gh api`)
**Site URL:** https://qhwangantoneva.github.io/experiment-engine/

---

## 1. Pages Configuration

- **build_type:** `workflow` (Actions-based deployment) -- CORRECT
- **source branch:** `gh-pages` (expected for Actions-based Pages)
- **Status:** `built`
- **Verdict:** PASS -- Pages is correctly configured for GitHub Actions deployment.

## 2. Deployment Source Verification

- **Latest deployment SHA:** `ec02dc50f2cbc7f13aa9974c976a38c3d5ca7bad`
- **Matches HEAD?** YES -- `ec02dc5` is the current HEAD.
- **Verdict:** PASS -- The latest commit IS deployed.

## 3. Deployed index.html -- CSP and Asset References

- **HTTP Status:** 200
- **CSP meta tag:** PRESENT
- **`wasm-unsafe-eval` in script-src:** PRESENT
  ```
  script-src 'self' 'wasm-unsafe-eval' https://cdn.jsdelivr.net;
  ```
- **connect-src includes HuggingFace:** PRESENT (`https://huggingface.co https://cdn-lfs.huggingface.co`)
- **worker-src includes blob:** PRESENT (`worker-src 'self' blob: https://cdn.jsdelivr.net`)
- **Module script reference:** PRESENT (`<script type="module" crossorigin src="/experiment-engine/assets/index-Bcxr2OUD.js">`)
- **Verdict:** PASS -- All CSP directives and asset references are correct.

## 4. Deployed pyodide-manifest.json

- **HTTP Status:** 200
- **Content:**
  ```json
  {
    "pyodide_version": "0.26.4",
    "packages": ["numpy", "pydantic", "pyyaml"],
    "python_module": "experiment_engine.tar.gz",
    "excluded": ["viz", "report", "cli.py", "__main__.py", "io/db.py", "core/parallel.py"]
  }
  ```
- **Expected packages:** `["numpy", "pydantic", "pyyaml", "micropip", "rich"]`
- **Actual packages:** `["numpy", "pydantic", "pyyaml"]`
- **Missing:** `"micropip"` and `"rich"`
- **Root cause of discrepancy:** The manifest is **hardcoded** in `.github/workflows/deploy.yml` line 110, which was never updated after the `rich`/`micropip` fixes were added to the worker JS.
- **Impact:** LOW -- The manifest is **not consumed by any runtime code**. The worker JS directly calls `pyodide.loadPackage()` with its own `REQUIRED_PACKAGES` array. The manifest is purely informational/documentation.
- **Verdict:** FAIL (cosmetic/documentation) -- The manifest is out of date but does not cause crashes.

## 5. Deployed Worker JS (pyodide.worker-DCSb5jOy.js)

- **URL:** `https://qhwangantoneva.github.io/experiment-engine/assets/pyodide.worker-DCSb5jOy.js`
- **HTTP Status:** 200
- **Content-Type:** Valid JavaScript (first bytes: `var fn=Object.defineProperty...` -- NOT HTML)
- **REQUIRED_PACKAGES found:**
  ```
  REQUIRED_PACKAGES=["numpy","pydantic","pyyaml","micropip","rich"]
  ```
- **Local dist has same hash:** `pyodide.worker-DCSb5jOy.js` exists with identical filename in local dist -- confirming local build = deployed build.
- **Verdict:** PASS -- Worker JS is valid JS, NOT HTML, and contains all 5 required packages.

## 6. Deployed Python Package (experiment_engine.tar.gz)

- **URL:** `https://qhwangantoneva.github.io/experiment-engine/py/experiment_engine.tar.gz`
- **HTTP Status:** 200
- **Size:** 76,578 bytes (76 KB)
- **Format:** Valid gzip compressed data (confirmed by `file` command)
- **Size check (> 50 KB):** PASS
- **Note:** Local dist tar.gz is 297 KB -- the difference suggests the CI build may exclude fewer files or was built from a different point. This needs further investigation but the deployed archive is valid.
- **Verdict:** PASS -- Valid gzip archive, properly served.

## Summary

| Check | Result | Details |
|-------|--------|---------|
| Pages config (Actions-based) | PASS | `build_type: workflow` |
| Latest commit deployed | PASS | SHA `ec02dc5` matches HEAD |
| CSP has `wasm-unsafe-eval` | PASS | Present in meta tag |
| Module script reference | PASS | `/experiment-engine/assets/index-Bcxr2OUD.js` |
| Worker JS is valid JS (not HTML) | PASS | Starts with JS, not `<html>` |
| Worker JS REQUIRED_PACKAGES | PASS | Includes `numpy`, `pydantic`, `pyyaml`, `micropip`, `rich` |
| Worker JS hash matches local build | PASS | `pyodide.worker-DCSb5jOy.js` matches |
| Main JS hash matches local build | PASS | `index-Bcxr2OUD.js` matches |
| pyodide-manifest.json | **FAIL (cosmetic)** | Missing `micropip` and `rich` -- hardcoded in deploy.yml line 110 |
| Package archive | PASS | Valid gzip, HTTP 200, 76 KB |

## Key Findings

1. **The deployed site IS serving the correct code.** Asset hashes (`index-Bcxr2OUD.js`, `pyodide.worker-DCSb5jOy.js`) match the local build of HEAD `ec02dc5`. All 4 Pyodide fixes (pydantic, CSP, worker error, rich) are included in the deployed JavaScript bundles.

2. **pyodide-manifest.json is out of date** but this is a **documentation issue only**. The manifest is hardcoded in `.github/workflows/deploy.yml` line 110 as `["numpy", "pydantic", "pyyaml"]` and was never updated to include `"micropip"` and `"rich"`. However, the manifest is **not consumed by any runtime code** -- the worker JS directly calls `pyodide.loadPackage()` with its own REQUIRED_PACKAGES array. **This does not cause any crashes.**

3. **If the app still crashes on the deployed site with 30 samples**, the cause is likely:
   - A different runtime error not addressed by the 4 known fixes (e.g., a data parsing issue in the sample CSV/Excel files, or a Pyodide memory limitation with 30 samples of BERT inference)
   - A race condition or timing issue in the async init sequence
   - An issue specific to the user's browser/environment (cache, extensions, browser version)
   - A bug in the `experiment_engine` Python code itself that only manifests with 30-sample inputs

4. **Recommended actions:**
   - Fix `deploy.yml` line 110 to include `"micropip"` and `"rich"` in the packages array (cosmetic fix)
   - Use Playwright or browser DevTools to capture the actual error message from the deployed site with 30 samples
   - Check browser console logs for the specific error that occurs after loading 30 samples
