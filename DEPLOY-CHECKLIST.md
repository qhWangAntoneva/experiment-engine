# Deployment Verification Checklist -- QCA Analysis Tool

> **Target**: GitHub Pages at `https://qhWangAntoneva.github.io/experiment-engine/`
> **Repo**: `qhWangAntoneva/experiment-engine`
> **Deploy branch**: `gh-pages` (force-orphan, managed by `peaceiris/actions-gh-pages@v4`)
> **Build trigger**: push to `master` branch or `workflow_dispatch`

---

## Section A: Pre-build Verification

These checks run BEFORE `npm run build`. They catch problems that would produce a broken dist/ output.

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| A.1 | Branch is `master` (or `main`) | `git branch --show-current` | | | CI deploys only from `master` per `deploy.yml` |
| A.2 | Working tree clean (no unstaged breakage) | `git status --short` -- only intentional files | | | 17 files currently unstaged (handover 2026-05-26); ensure all are staged or intentionally excluded |
| A.3 | Latest commit pushed to origin | `git log origin/master..HEAD` -- should be empty | | | CI builds from pushed commits only |
| A.4 | TypeScript compilation clean (0 errors) | `npx tsc --noEmit` | | | Must be zero errors; warnings are acceptable but should be reviewed |
| A.5 | Python tests pass (522 collected, 0 failures) | `uv run pytest --tb=short -q` | | | CPU-only; CI skips this but must pass locally before tagging a deploy-worthy commit |
| A.6 | Ruff lint clean | `uv run ruff check src/ tests/` | | | Config in `pyproject.toml` line 76-118 |
| A.7 | Vite dev server starts cleanly | `npx vite --port 3000 --host 127.0.0.1` then open browser | | | **Must use `127.0.0.1`, not localhost** (Clash proxy intercepts localhost) |
| A.8 | All 5 SPA routes return HTTP 200 in dev | Navigate: `/`, `/dashboard`, `/input`, `/results`, `/settings` | | | `/` should redirect to `/dashboard` |
| A.9 | i18n works (Chinese + English) | Toggle sidebar language switch; verify all labels change | | | Check new error-state keys: `statusError`, `step1BtnError` |
| A.10 | No hardcoded non-relative URLs in source | Grep `src/` for `localhost`, `127.0.0.1`, or absolute paths that would break on GitHub Pages | | | `import.meta.env.BASE_URL` is the correct way to reference base |
| A.11 | `vite.config.ts` base is `/experiment-engine/` (production) | `grep 'base:' vite.config.ts` | | | Conditional: dev=`/`, prod=`/experiment-engine/` |
| A.12 | `main.tsx` basename matches BASE_URL | Read `src/main.tsx` line 21 -- uses `import.meta.env.BASE_URL` | | | Must strip trailing slash to avoid `//dashboard` |
| A.13 | Pyodide CDN version matches `package.json` | `package.json` has `"pyodide": "0.26.4"`; worker loads from `cdn.jsdelivr.net/pyodide/v0.26.4/full/` | | | Mismatch causes import errors or missing stdlib |
| A.14 | `dist/` is in `.gitignore` (not tracked) | `grep 'dist/' .gitignore` | | | Line 6 of `.gitignore`; verified present |

---

## Section B: Build Verification

These checks run AFTER `npm run build` but BEFORE deploying. Simulate as closely as possible to CI environment.

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| B.1 | `npm run build` exits 0 | `npm run build` (runs `tsc -b && vite build`) | | | `tsc -b` must pass first; Vite build follows |
| B.2 | `dist/` directory exists and is non-empty | `ls dist/` | | | Expected: `index.html`, `assets/`, `py/` |
| B.3 | `dist/index.html` exists and loads correct base | Check `<head>` for `<base>` or asset paths prefixed with `/experiment-engine/` | | | Vite injects `__vite_base__` as `/experiment-engine/` |
| B.4 | All asset paths in `dist/index.html` are prefixed | `grep -o 'src="[^"]*"' dist/index.html` -- all should start with `/experiment-engine/assets/` | | | Wrong prefix = 404 on all JS/CSS |
| B.5 | `dist/assets/` contains vendor chunks | Check for `vendor-react-*.js` and `vendor-plotly-*.js` | | | Manual chunks configured in `vite.config.ts` line 33-36 |
| B.6 | No sourcemaps in dist (production build) | `ls dist/assets/*.map 2>/dev/null` -- should be empty | | | `sourcemap: false` in `vite.config.ts` line 29 |
| B.7 | `dist/py/experiment_engine.tar.gz` exists | `ls -lh dist/py/experiment_engine.tar.gz` | | | Bundled by CI step; verify locally with `tar tzf dist/py/experiment_engine.tar.gz` |
| B.8 | `dist/py/pyodide-manifest.json` exists and valid | Read `dist/py/pyodide-manifest.json` -- has `pyodide_version`, `packages`, `python_module` | | | Used at runtime to verify the Python module is compatible |
| B.9 | tar.gz contains expected modules (not excluded) | `tar tzf dist/py/experiment_engine.tar.gz | sort` | | | Must NOT contain: `viz/`, `report/`, `cli.py`, `__main__.py`, `io/db.py`, `core/parallel.py` |
| B.10 | tar.gz is NOT a directory-only tarball | `tar tzf dist/py/experiment_engine.tar.gz | wc -l` -- should be >20 files | | | Warning sign: only top-level `__init__.py` files = packaging config broken |
| B.11 | No node_modules or .git in dist | `ls dist/node_modules dist/.git 2>/dev/null` -- should error | | | Accidental inclusion bloats the gh-pages branch |
| B.12 | `dist/404.html` exists (SPA routing) | `ls dist/404.html` | | | **CRITICAL**: Without this, refreshing `/experiment-engine/dashboard` shows GitHub 404 page |
| B.13 | `dist/404.html` sessionStorage redirect works | Read `dist/404.html` -- should store `location.href` in `sessionStorage.redirect` then meta-refresh to `/experiment-engine/` | | | Standard GitHub Pages SPA workaround |
| B.14 | `dist/CNAME` does NOT exist (no custom domain) | `ls dist/CNAME 2>/dev/null` -- should error | | | CNAME only needed if using custom domain |
| B.15 | Total dist size is reasonable (< 50 MB) | `du -sh dist/` | | | Excludes 50MB Pyodide CDN assets; threshold is ~5 MB for SPA + tar.gz |
| B.16 | Build output matches dev-server behavior | Run `npx vite preview --port 4173` and navigate routes | | | Preview serves from `/experiment-engine/` (uses production base) |

---

## Section C: SPA 404.html Setup (Pre-deploy Fix)

This is a standalone task that must be completed before or during the first deploy. Without it, direct URL access to any sub-route will fail.

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| C.1 | SPA `404.html` exists in repo root | `ls public/404.html` or Vite-copied to `dist/404.html` | | | Place in `public/404.html` so Vite copies it to `dist/` verbatim |
| C.2 | `404.html` captures URL via sessionStorage | Script stores `location.href` in `sessionStorage.redirect` | | | Source: `sessionStorage.setItem("redirect", location.href)` |
| C.3 | `404.html` redirects to SPA root with base | Meta refresh to `/experiment-engine/` | | | Must use the full base path, not `/` |
| C.4 | `index.html` (or `main.tsx`) restores the redirect | On mount, check `sessionStorage.redirect`, extract path, call `history.replaceState(null, "", path)` then clear sessionStorage | | | This completes the SPA-on-GitHub-Pages redirect dance |
| C.5 | `404.html` works when deployed (server-side 404) | GitHub Pages serves `404.html` automatically when a path doesn't exist on the server | | | This is GitHub Pages built-in behavior; it works if `404.html` is at repo root |
| C.6 | No conflicting `404.html` from `site/` directory | Confirm `site/404.html` (MkDocs artifact) is NOT copied to `dist/404.html` | | | The MkDocs 404 is for documentation, not the SPA |

---

## Section D: GitHub Pages Configuration

These checks are done in the GitHub repo's Settings tab.

| # | Check | Where / How | PASS | FAIL | Notes |
|---|-------|-------------|------|------|-------|
| D.1 | GitHub Pages source: "Deploy from a branch" | Settings > Pages > Source | | | Select branch: `gh-pages`, folder: `/ (root)` |
| D.2 | `gh-pages` branch exists and is populated | `https://github.com/qhWangAntoneva/experiment-engine/tree/gh-pages` | | | Created by CI on first successful run |
| D.3 | No custom domain configured (unless intentional) | Settings > Pages > Custom domain -- should be empty | | | Current design uses `username.github.io/repo` subdirectory |
| D.4 | HTTPS enforced | Settings > Pages > Enforce HTTPS -- must be checked | | | GitHub Pages enables this by default for public repos |
| D.5 | CI workflow has `contents: write` permission | `.github/workflows/deploy.yml` line 42-43 | | | Required for peaceiris/actions-gh-pages to push |
| D.6 | CI workflow concurrency group prevents race | `.github/workflows/deploy.yml` line 47-48 | | | Group `"pages"` with `cancel-in-progress: true` |
| D.7 | CI deploys from `master` branch trigger | `.github/workflows/deploy.yml` line 30: `branches: [main, master]` | | | Push to master auto-deploys |
| D.8 | CI `workflow_dispatch` manual trigger available | GitHub Actions tab > "Deploy to GitHub Pages" > Run workflow | | | Manual deploy override with optional Pyodide version |
| D.9 | CI uses `force_orphan: true` on gh-pages | `.github/workflows/deploy.yml` line 134 | | | Keeps gh-pages at 1 commit (no CI history bloat) |
| D.10 | CI node version matches local (`node: '20'`) | `.github/workflows/deploy.yml` line 65-66 | | | Ubuntu `ubuntu-latest` runner |

---

## Section E: Post-deploy Verification (Browser)

Run these against the live URL `https://qhWangAntoneva.github.io/experiment-engine/`.

### E.1: Core Availability

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| E.1.1 | URL returns HTTP 200 | Open `https://qhWangAntoneva.github.io/experiment-engine/` | | | First deploy may take 1-2 minutes after CI completes |
| E.1.2 | Dashboard loads (redirect from `/`) | Navigate to root URL, verify redirect to `/experiment-engine/dashboard` | | | Client-side redirect via `<Navigate to="/dashboard" replace />` |
| E.1.3 | Dashboard metric cards visible | Engine Status = "Not loaded" (or zh "未加载"), Pipeline Status = "Idle" (or zh "空闲") | | | Verify no blank cards or console errors |
| E.1.4 | Sidebar navigation works | Click each sidebar link: Dashboard, Data Input, Results, Settings | | | URL bar should show correct path after each click |
| E.1.5 | Settings page loads and saves | Modify a setting > Save > Refresh page > Verify setting persisted | | | Settings use localStorage |

### E.2: SPA Routing (No 404 on Refresh)

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| E.2.1 | `/experiment-engine/` loads (root) | Enter URL directly in address bar and press Enter | | | Not a client-side navigate -- full page load |
| E.2.2 | `/experiment-engine/dashboard` loads | Direct URL entry, full page reload | | | Critical: tests SPA 404.html redirect |
| E.2.3 | `/experiment-engine/input` loads | Direct URL entry, full page reload | | | Same as above for DataInput page |
| E.2.4 | `/experiment-engine/results` loads | Direct URL entry, full page reload | | | Same as above for Results page |
| E.2.5 | `/experiment-engine/settings` loads | Direct URL entry, full page reload | | | Same as above for Settings page |
| E.2.6 | Refresh (F5) on any page works | From `/dashboard`, press F5 -- should reload same page, not redirect to `/` | | | No `sessionStorage.redirect` loop |
| E.2.7 | Invalid route shows app (not GitHub 404) | Navigate to `/experiment-engine/nonexistent` | | | Should show the app shell (React Router handles 404 internally or shows blank layout) |

### E.3: Pyodide Engine

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| E.3.1 | CDN `cdn.jsdelivr.net` reachable from browser | Network tab: `pyodide.mjs` and `.asm.wasm` load without CORS/network errors | | | If blocked (GFW/region), Pyodide won't load |
| E.3.2 | Click "Load Engine" starts loading | Button text changes to "Loading..." or zh "加载中..." with progress bar | | | Fix from bug-001; should NOT flash back immediately |
| E.3.3 | Engine loads to "Ready" state (30-90s) | Wait; button becomes "Engine Ready" or zh "引擎就绪"; metric card shows "Ready"/"就绪" | | | First load: slow (~60-90s) due to CDN download; subsequent: browser-cached (~5-10s) |
| E.3.4 | Python tar.gz fetched from self-hosted path | Network tab: `GET /experiment-engine/py/experiment_engine.tar.gz` returns 200 | | | Path must be `/experiment-engine/py/experiment_engine.tar.gz` (NOT `/experiment-engine/dist/py/...`) |
| E.3.5 | Python modules importable post-load | Console: `pyodide.pyimport("experiment_engine")` succeeds | | | Verify `pyodide_handlers.py` is inside the tar.gz |
| E.3.6 | Block CDN -> Engine shows error UI | DevTools Network > Block `cdn.jsdelivr.net` > Click "Load Engine" | | | Should show red error banner + "Retry (Error)" button with error message |
| E.3.7 | Unblock CDN -> Retry succeeds | Remove block > Click "Retry (Error)" | | | Bridge cleanup (worker terminate + recreate) must work correctly |

### E.4: Calibration Pipeline

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| E.4.1 | Text corpus CSV parses correctly | DataInput: paste test CSV (see `handover.md` section 4.4) > "Parse" | | | 5 rows, columns: `id`, `text` |
| E.4.2 | Prototype CSV parses correctly | DataInput: paste prototype CSV (see `handover.md` section 4.4) > "Parse" | | | 4 rows, columns: `编号`, `文本内容`, `结果` |
| E.4.3 | "Calibrate" button works | Click "Calibrate" > Verify calibration completes | | | Knowledge-driven keyword calibration |
| E.4.4 | DistributionPlot displays post-calibration | Verify plot renders (no blank canvas, no console errors) | | | Uses Plotly.js-dist-min |
| E.4.5 | "Run Full Pipeline" completes | Click "Run Full Pipeline" > Auto-redirect to Results page | | | Runs QCA truth table, minimization, NL interpretation |
| E.4.6 | Results page shows all tabs | Verify tabs: Truth Table, Solutions, Robustness, NL Interpretation | | | Check each tab has content (no empty panels) |
| E.4.7 | Robustness report is non-empty | Robustness tab shows parameter sensitivity data | | | Can be slow; threshold tolerance varies |

### E.5: BERT Embeddings (Optional, Slow)

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| E.5.1 | BERT model loads from HuggingFace Hub | Settings > Select BERT model > "Load" > Wait | | | `@xenova/transformers` fetches from `huggingface.co`; ~50-200 MB download |
| E.5.2 | BERT model selection persists across refresh | Select model > Refresh page > Verify selection kept | | | localStorage persistence |
| E.5.3 | "BERT Embedding Calibrate" works | DataInput > Load model > Paste text > Click "BERT Embedding 校准" | | | Runs feature extraction via Transformers.js |
| E.5.4 | BERT embedding cache works (IndexedDB) | Re-run same text corpus > Should complete much faster (cached) | | | `bert-cache.ts` stores embeddings in IndexedDB |

### E.6: Asset Integrity

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| E.6.1 | All assets loaded over HTTPS (no mixed content) | DevTools Console: filter "Mixed Content" -- should be zero | | | GitHub Pages enforces HTTPS; CDN (jsdelivr) uses HTTPS |
| E.6.2 | No 404 on any JS/CSS asset | DevTools Network tab: filter status 404 -- should be zero | | | Check vendor-react, vendor-plotly, main entry chunks |
| E.6.3 | Favicon not missing (no console warning) | DevTools Console: check for favicon 404 | | | Add `public/favicon.ico` if not present |
| E.6.4 | All `workers/*.js` load correctly | Network tab: find `worker` in filenames -- status 200 | | | Vite's ES worker format produces entry files in assets |

### E.7: Mobile / Responsive

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| E.7.1 | Dashboard responsive at 375px (iPhone SE) | Chrome DevTools > Device toolbar > 375x812 | | | Sidebar should collapse/hamburger; metric cards stack |
| E.7.2 | DataInput responsive at 375px | Same device profile | | | Text areas usable; buttons accessible |
| E.7.3 | Settings responsive at 375px | Same device profile | | | Dropdowns/selects not cut off |
| E.7.4 | Plotly charts responsive | Results page on mobile viewport | | | Plots should shrink, not overflow horizontally |
| E.7.5 | No horizontal scroll on any page at 375px | Verify each page fits viewport width | | | Horizontal scroll = broken responsive design |

### E.8: Cross-Browser

| # | Check | How to Verify | PASS | FAIL | Notes |
|---|-------|---------------|------|------|-------|
| E.8.1 | Works in Chrome (latest) | Primary test target | | | Main development browser |
| E.8.2 | Works in Edge (latest) | Secondary test (Chromium-based, should match Chrome) | | | Good fallback for Chinese Windows users |
| E.8.3 | Works in Firefox (latest) | Test Pyodide loading especially | | | Firefox's Web Worker spec compliance can differ from Chrome |
| E.8.4 | Works in Safari (macOS/iOS) | Test if available | | | WebKit has different Web Worker behavior; important for Pyodide init |

---

## Section F: Edge Cases & Stress Tests

| # | Scenario | Expected Behavior | PASS | FAIL | Notes |
|---|----------|-------------------|------|------|-------|
| F.1 | Click "Load Engine" twice rapidly | Second click is no-op or shows "already loading"; no double-worker created | | | `pyodide.ts` "already loading" guard at line 84 |
| F.2 | Reload page while engine is loading | Engine state resets; can retry | | | Worker is terminated on page unload |
| F.3 | Switch language while engine is loading | UI text switches but loading continues uninterrupted | | | i18n is independent of Pyodide state |
| F.4 | Navigate away and back while engine is loading | Engine state preserved (via hook/context); loading continues in background | | | Worker is singleton; survives route changes |
| F.5 | GH Pages deploy while users are on the page | Old assets may 404; hard-refresh should fix | | | Service Worker (if added later) can handle this gracefully |
| F.6 | Browser offline: Pyodide CDN unreachable | Error state shown ("Retry (Error)") not infinite spinner | | | Network error from `fetch()` should propagate to error state |
| F.7 | Very large text corpus (>100 rows) | Parse succeeds; calibration may be slow but doesn't crash | | | Python-side; check for memory pressure in Pyodide's WASM heap |
| F.8 | Special characters in CSV (CJK + emoji + quotes) | CSV parses correctly; BERT handles CJK | | | Test data includes Chinese text |
| F.9 | BERT loading while Pyodide is loading | Both operations should not conflict; separate workers/threads | | | BERT uses Transformers.js (separate from Pyodide worker) |
| F.10 | Tab inactive during engine load | Engine continues loading (not throttled by Chrome) | | | Chrome may throttle inactive tab timers |
| F.11 | `experiment_engine.tar.gz` returns 404 | Engine shows error: "Failed to fetch Python module" with retry | | | Simulate by temporarily renaming the tar.gz on the server |
| F.12 | Performance: Dashboard first contentful paint < 3s | Lighthouse or Chrome Performance tab | | | Cached; first load with Pyodide can be >60s (acceptable) |
| F.13 | No console errors on any page | Open each page; check DevTools Console (all levels) | | | Zero errors is the target; warnings are acceptable |
| F.14 | Export keyword dictionary works | Settings > "Export Keyword Dictionary" > downloads JSON | | | `Settings.tsx` exportKeywords feature from Phase 4 |

---

## Quick-Run Script

For rapid pre-build checks (local, pre-commit):

```bash
#!/bin/bash
# quick-deploy-check.sh — fast pre-deploy verification (local only)

echo "=== A.4: TypeScript ==="
npx tsc --noEmit && echo "PASS" || echo "FAIL"

echo "=== A.5: Python tests ==="
uv run pytest --tb=short -q 2>&1 | tail -1

echo "=== A.6: Ruff lint ==="
uv run ruff check src/ tests/ 2>&1 | tail -5

echo "=== B.1-B.3: Build ==="
npm run build && echo "PASS" || echo "FAIL"
ls dist/index.html dist/assets/ dist/py/experiment_engine.tar.gz

echo "=== B.8: tar.gz contents ==="
tar tzf dist/py/experiment_engine.tar.gz | head -20

echo "=== B.15: dist size ==="
du -sh dist/

echo "=== C.1: 404.html ==="
ls -l dist/404.html && echo "PASS" || echo "WARNING: SPA 404.html missing — direct URL access will fail"

echo "=== A.10: No localhost hardcoding ==="
grep -r "localhost\|127\.0\.0\.1" src/ --include="*.ts" --include="*.tsx" -l 2>/dev/null
```
