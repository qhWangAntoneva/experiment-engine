# QCA Analysis Tool -- UX-Focused E2E Test Plan

**URL:** `http://127.0.0.1:3000`
**Tester role:** UX tester (this agent)
**Generated:** 2026-05-25
**Known issue:** "Load Engine" button on Dashboard clicks, state flips to `loading` briefly, then reverts to `unloaded` -- no error shown.

---

## Phase 1: Engine Loading (P0 -- HIGHEST PRIORITY, broken)

### T1.1 -- Basic load flow
**Steps:** Open Dashboard. Click "Load Engine" (Step 1 box). Wait up to 60s.
**Expected:** Button text changes to "Loading...", progress bar appears (0-100%), metric card 1 flips to "Ready" (green). After load, Step 2 button ("Start Analysis") enables.
**PASS:** Pyodide loads, metric card shows "Ready", Step 2 button is enabled, no console errors.
**FAIL:** Button text reverts from "Loading..." back to "Load Engine" within seconds (the known bug). Metric card stays "Not Loaded". Step 2 stays disabled.

### T1.2 -- Loading when CDN unreachable (simulated)
**Steps:** Block `cdn.jsdelivr.net` in DevTools Network tab or via hosts file. Click "Load Engine". Wait 60s.
**Expected:** After timeout, the state transitions to `error`. Error message appears (either on the button, in a toast, or in the metric card). Metric card 1 shows "Error" in red. User sees actionable error text (not a blank fail).
**PASS:** Error state shown with a human-readable message. Loading state does NOT revert silently.
**FAIL:** Button reverts to "Load Engine" silently. No error indicator anywhere. User has no idea what went wrong.

### T1.3 -- Worker crash recovery
**Steps:** Load engine normally. Open DevTools, find the Pyodide Web Worker (Sources > Workers), terminate it. Attempt to calibrate on DataInput page.
**Expected:** Calibration request fails with an error message like "Worker is not ready". Dashboard metric reverts to "Not Loaded". "Load Engine" button becomes clickable again for re-init.
**PASS:** Error surfaced to user. Engine can be re-loaded without page refresh.
**FAIL:** App hangs on infinite "loading" spinner. Error swallowed. Page refresh is the only recovery path.

### T1.4 -- Double-click on "Load Engine"
**Steps:** With engine unloaded, rapidly click "Load Engine" 3 times.
**Expected:** Only one init request is sent. During loading, the button is disabled. No duplicate workers are spawned. Engine loads once and shows "Ready".
**PASS:** Button is `disabled` during `loading` state. Only one network/CDN fetch cascade visible in Network tab.
**FAIL:** Multiple workers spawned (check Sources tab), multiple CDN fetches, or state oscillates between loading/unloaded.

### T1.5 -- Page navigation during loading
**Steps:** Click "Load Engine". While loading, navigate to Settings, then to DataInput, then back to Dashboard.
**Expected:** Loading progress is preserved across navigations (state lives in singleton `PyodideBridge`). Progress bar is still visible on return. When loading completes, Dashboard reflects "Ready".
**PASS:** Progress persists across page navigations. On completion, all pages show engine as ready.
**FAIL:** Returning to Dashboard shows "Load Engine" button again (state lost). Loading spinner stuck. Dashboard shows stale state.

### T1.6 -- Refresh after load
**Steps:** Load engine successfully. Refresh the browser page (F5).
**Expected:** Engine state resets (Web Worker is killed). Dashboard shows "Not Loaded". User must reload engine.
**PASS:** Clean reset. No stale "Ready" shown when worker is actually dead. Button is clickable.
**FAIL:** Dashboard shows "Ready" but any operation fails with worker-not-found errors. Inconsistent state between UI and reality.

### T1.7 -- Slow network partial load
**Steps:** Throttle network to "Slow 3G" in DevTools. Click "Load Engine".
**Expected:** Progress bar updates with increasing percentage (not stuck at 0%). After full download (may take 2-3 min), status becomes "Ready".
**PASS:** Progress updates are visible and monotonically increasing. Eventual success without timeout at the 5-min mark.
**FAIL:** Progress stuck at 0% for entire download. Premature timeout. Button reverts silently.

---

## Phase 2: i18n and Navigation

### T2.1 -- Default language detection
**Steps:** Clear browser localStorage. Open `http://127.0.0.1:3000/` in an incognito window.
**Expected:** App loads in Chinese (zh) by default. Dashboard title reads "首页". Sidebar shows "首页 / 数据输入 / 分析结果 / 设置".
**PASS:** All visible text is Chinese on first load.
**FAIL:** Mixed zh/en text. English shown by default.

### T2.2 -- Language switcher on Dashboard
**Steps:** Find language toggle (dropdown or button) on Dashboard. Switch to English.
**Expected:** Dashboard title changes to "Dashboard". Metric card labels change to English. Step titles (1-4) change to English. "Load Engine" button text changes to English.
**PASS:** All visible Dashboard text flips to English in under 1 second (no page reload).
**FAIL:** Partial translation -- some labels remain Chinese. UI flickers/blinks. Requires page reload to take effect.

### T2.3 -- Language persists across pages
**Steps:** Switch to English on Dashboard. Navigate to DataInput, then Settings, then Results.
**Expected:** All pages render in English. Labels, buttons, placeholders all in English.
**PASS:** Consistent English across all 4 pages. No page flashes in zh before showing en.
**FAIL:** Any page reverts to Chinese after navigation. Mixed language on a single page.

### T2.4 -- Language persists across refresh
**Steps:** Switch to English. Refresh the page (F5).
**Expected:** App loads in English. Language choice was persisted (localStorage).
**PASS:** English on post-refresh load.
**FAIL:** App reverts to Chinese after refresh.

### T2.5 -- BERT labels in both languages
**Steps:** Switch to Chinese. Go to DataInput. Look for BERT-related controls. Switch to English. Check same controls.
**Expected:** In zh: BERT labels read "BERT 模型", "加载 BERT 模型", "BERT 嵌入校准". In en: "BERT Model", "Load BERT Model", "BERT Embedding Calibration".
**PASS:** All BERT labels translate correctly in both languages. No hardcoded Chinese text when English is selected and vice versa.
**FAIL:** BERT labels show keys instead of text (e.g. `dataInput.bertLoadBtn`). Missing translations. Mixed language for BERT section.

### T2.6 -- Sidebar navigation structure
**Steps:** Verify sidebar shows 4 items: Dashboard, Data Input, Results, Settings. Click each in sequence.
**Expected:** Each click navigates to the correct route: `/`, `/input`, `/results`, `/settings`. Active item is highlighted. URL updates correctly.
**PASS:** All 4 routes load their respective pages. Active state visible on current nav item.
**FAIL:** 404 on any route. Sidebar highlight desynced from current page. Clicking current page reloads unnecessarily.

### T2.7 -- Direct URL entry
**Steps:** Type `http://127.0.0.1:3000/input` directly in address bar. Then `/results`, then `/settings`.
**Expected:** Each URL loads the correct page directly. No redirect to `/`.
**PASS:** All 4 routes accessible via direct URL. No infinite redirect loops.
**FAIL:** Any route redirects to `/`. 404 blank page.

---

## Phase 3: Settings Persistence

### T3.1 -- Save calibration params
**Steps:** Go to Settings. Change Threshold Full-In from 0.85 to 0.90. Change Crossover Point from 0.50 to 0.55. Click Save. Refresh the page (F5).
**Expected:** After refresh, both values are restored to 0.90 and 0.55 respectively.
**PASS:** Values persist across refresh. Confirmation toast/message shown after save.
**FAIL:** Values reset to defaults after refresh. No save feedback shown. Save button does nothing.

### T3.2 -- BERT model selector persistence
**Steps:** Go to Settings. Select a BERT model from the dropdown (e.g., `bert-base-chinese`). Click Save. Refresh the page.
**Expected:** The selected model is still shown in the dropdown after refresh.
**PASS:** BERT model selection persists.
**FAIL:** Model selection resets to default/empty after refresh.

### T3.3 -- Save without changes
**Steps:** Go to Settings. Without modifying any field, click Save.
**Expected:** No error. Save completes silently or shows "No changes" / "Settings unchanged" message.
**PASS:** Graceful no-op. No console errors.
**FAIL:** Error thrown. Form validation prevents save. Settings corrupted.

### T3.4 -- Invalid numeric input
**Steps:** Enter "2.0" for Threshold Full-In (valid range: 0.5-1.0). Click Save.
**Expected:** Validation error shown. Value rejected or clamped. Field highlighted in red.
**PASS:** User sees clear validation message. Invalid value is not saved.
**FAIL:** Invalid value saved silently. NaN or overflow accepted. App crashes on save.

### T3.5 -- QCA variant switch
**Steps:** On Settings page, switch QCA variant from fsQCA to csQCA. Observe the calibration method dropdown and related fields.
**Expected:** Calibration method options change (crisp_set becomes available/selected). Related fields that only apply to fsQCA are disabled or removed.
**PASS:** UI updates reflect the variant change. Options incompatible with current variant are hidden/disabled.
**FAIL:** All options remain shown regardless of variant. Switching variant has no visible effect.

### T3.6 -- Export keyword dictionary
**Steps:** Go to Settings. Find export/keyword dictionary export button. Click it.
**Expected:** A file downloads (CSV or JSON) containing the keyword dictionary. File is well-formed and can be opened.
**PASS:** File downloads. Content is valid CSV/JSON. Keywords match the current condition set.
**FAIL:** Download fails. File is empty. File format is corrupted. Button does nothing.

---

## Phase 4: Data Input and Calibration

### T4.1 -- Paste CSV text corpus
**Steps:** On DataInput page, paste the test CSV:
```
id,text
case_01,"The government response was very fast and effective"
case_02,"I am extremely dissatisfied with the poor service"
case_03,"建议政府提高办事效率"
case_04,"严重怀疑政策能否执行到位"
case_05,"满意，已解决问题"
```
Click "Parse" or equivalent action.
**Expected:** Preview table appears showing all 5 rows with `id` and `text` columns. Row count shown as "5 cases loaded".
**PASS:** All 5 rows parsed. Table displays id and text columns correctly. Chinese text is not garbled.
**FAIL:** Parse error. Empty table. Chinese text shows as mojibake. Only partial rows parsed.

### T4.2 -- Paste prototype CSV
**Steps:** In prototype mode (if toggleable), paste:
```
编号, 文本内容, 结果
1, 政府第一时间回应了群众诉求, 1
2, 问题处理非常迅速有效, 1
3, 多次投诉仍没有答复, 0
4, 办事人员态度差效率低, 0
```
Click Parse.
**Expected:** Prototype editor table shows 4 rows. Prototype text and result (0/1) are visible.
**PASS:** 4 prototype entries parsed correctly. Result column shows 1/0 values.
**FAIL:** Parse error. Results treated as text instead of numbers. Table empty.

### T4.3 -- Calibrate (keyword mode)
**Steps:** Load engine (Phase 1). Paste test CSV (T4.1). Keep the default YAML condition set. Verify the YAML is valid (no red error markers). Click "Calibrate".
**Expected:** Calibration runs (may take 5-15s). Progress indicator shown. DistributionPlot appears showing fuzzy membership distributions for each condition. PipelineStatus transitions to "calibrated".
**PASS:** Membership scores generated. Distribution plots visible. No errors. PipelineStatus = calibrated.
**FAIL:** Calibration hangs. Error toast/alert. PipelineStatus shows error. No plots rendered.

### T4.4 -- Calibrate (prototype mode)
**Steps:** Load engine. Paste prototype CSV (T4.2). Ensure prototype mode is selected. Click "Calibrate" or "Prototype Calibrate".
**Expected:** Prototype calibration runs. Prototype fuzzy data is generated. PipelineStatus shows "calibrated-prototype".
**PASS:** Prototype membership scores generated. Distinct from keyword calibration results. PipelineStatus transitions correctly.
**FAIL:** Error during prototype calibration. Prototype and keyword calibration results are conflated.

### T4.5 -- Calibrate with invalid YAML
**Steps:** Load engine. Paste test CSV. Delete a colon or bracket in the YAML editor to make it syntactically invalid. Click "Calibrate".
**Expected:** YAML validation error shown BEFORE sending to worker. Calibrate button is disabled or clicking it shows inline error. No worker request is made.
**PASS:** Validation catches the YAML error. Error message points to the problematic line. Calibrate button blocked.
**FAIL:** Invalid YAML sent to Python worker. Cryptic Python traceback shown in page. App crashes.

### T4.6 -- Calibrate without engine loaded
**Steps:** Ensure engine is NOT loaded (Dashboard shows "Not Loaded"). Go to DataInput. Paste valid CSV and YAML. Click "Calibrate".
**Expected:** Warning or error: "Engine not ready. Please load Pyodide first." Calibrate button may be disabled, or clicking it shows a clear message. User is directed to Dashboard.
**PASS:** Clear error message. No cryptic worker error. Path to recovery shown.
**FAIL:** Calibrate button appears to work but hangs. Generic "Worker not found" error. App crashes.

### T4.7 -- Empty input calibration attempt
**Steps:** Load engine. Leave text area empty. Click "Calibrate".
**Expected:** Validation error: "No text data provided" or similar. Calibration does not proceed.
**PASS:** Clear error message. No worker request sent.
**FAIL:** Empty data sent to worker. Worker error with unhelpful Python traceback shown.

### T4.8 -- YAML keyword modification
**Steps:** Load engine. Paste test CSV. In the YAML editor, add a new keyword to one condition (e.g., add `- pattern: "及时" weight: 0.6 scope: unigram`). Click "Calibrate".
**Expected:** Calibration runs with the modified keyword set. New keyword affects membership scores (visible in distribution plot).
**PASS:** Calibration succeeds. Distribution shows different scores compared to default YAML.
**FAIL:** New keyword ignored. Calibration fails. YAML editor resets to default.

---

## Phase 5: Full Pipeline

### T5.1 -- Run full pipeline (keyword mode)
**Steps:** Load engine. Paste test CSV. Keep default YAML. Click "Calibrate". After calibration completes, click "Run Analysis" or "Run Pipeline".
**Expected:** Pipeline executes (calibration + analysis + robustness). Auto-navigates to Results page. Solutions tab is active by default. Solution formulas are displayed (complex, parsimonious, intermediate).
**PASS:** Auto-navigation to `/results`. At least one solution shown. Solution formulas render correctly (AND = *, OR = +, negation = ~). No errors.
**FAIL:** Pipeline hangs at any stage. No navigation to Results. Results page shows empty state ("No results yet"). Partial results (truth table but no solutions).

### T5.2 -- Truth Table tab
**Steps:** After running pipeline, click "Truth Table" tab on Results page.
**Expected:** Truth table renders with columns for condition configurations, outcome, frequency, and consistency. Table is sortable. Heatmap visualization is visible below or alongside the table.
**PASS:** Truth table populated. Sortable columns. Heatmap renders without errors.
**FAIL:** Empty truth table. Heatmap shows blank canvas. Sorting crashes the page.

### T5.3 -- Solutions tab
**Steps:** Click "Solutions" tab. Verify all three solution types are shown (complex, parsimonious, intermediate).
**Expected:** Each solution has a formatted formula, consistency score, and coverage score. Formulas use boolean notation. If Chinese NL interpretation is enabled, each solution has a text explanation.
**PASS:** Three solution types displayed. Formulas are syntactically valid. Consistency/coverage values in [0,1].
**FAIL:** Only one or two solution types shown. Formula shows raw JSON. Values outside valid range. Solution tab crashes.

### T5.4 -- Necessity/Sufficiency plots
**Steps:** Click "Necessity" tab. Verify XY plots or bar charts render for each condition.
**Expected:** At least one plot rendered showing necessity scores. Conditions above the necessity threshold (default 0.9) are highlighted. Plot is interactive (Plotly zoom/hover).
**PASS:** Plots render. Plotly interactions work (hover shows values, zoom available). Threshold line visible.
**FAIL:** Blank tab. Plotly error in console. Plots are static images with no interaction.

### T5.5 -- Robustness tab
**Steps:** Click "Robustness" tab (only visible after complete pipeline with robustness test).
**Expected:** Robustness report shown. Includes consistency sensitivity, frequency sensitivity, calibration/membership perturbation, and bootstrap results. Each test shows stability/coverage metrics.
**PASS:** All robustness tests have results. Stability values in [0,1]. No "undefined" or "NaN" values.
**FAIL:** Tab is empty. Error message. Values outside expected range.

### T5.6 -- Export results
**Steps:** On Results page, click "Export CSV". Then "Export JSON". Then "Export LaTeX".
**Expected:** Each export triggers a file download. CSV is readable in Excel/Google Sheets. JSON is well-formed and can be parsed. LaTeX file is syntactically valid with no unescaped special characters.
**PASS:** All three formats download successfully. Files are non-empty. LaTeX compiles without errors.
**FAIL:** Any export produces an empty file. Download fails with error. LaTeX contains unescaped Chinese characters or special symbols.

### T5.7 -- View mode toggle (raw/prototype/compare)
**Steps:** If both keyword AND prototype calibrations were run, test the view mode toggle on Results page: switch to "raw", then "prototype", then "compare".
**Expected:** Raw shows keyword-calibrated results. Prototype shows prototype-calibrated results. Compare shows side-by-side with differences highlighted.
**PASS:** All three modes render distinct content. Compare mode highlights meaningful differences.
**FAIL:** Modes show identical content. Compare mode crashes. Mode switch has no effect.

---

## Phase 6: Error Handling and Edge Cases

### T6.1 -- Empty CSV (header only)
**Steps:** On DataInput, paste: `id,text`. Click Parse.
**Expected:** Warning: "No data rows found" or "Header only -- please add data rows". No empty rows displayed. Calibration is blocked.
**PASS:** Clear warning message. No phantom rows in preview. Calibrate blocked or shows pre-validation error.
**FAIL:** Empty row rendered. Parser crashes. Calibration attempted with empty data.

### T6.2 -- CSV with missing text column
**Steps:** Paste: `id,wrong_column\ncase_01,some_value`. Click Parse.
**Expected:** Warning: "Column 'text' not found" or similar. User is prompted to map columns or fix the CSV.
**PASS:** Clear error about missing column. Does not silently accept the data.
**FAIL:** Data parsed with empty text fields. Calibration produces all-zero membership. Error swallowed.

### T6.3 -- CSV with mixed encodings
**Steps:** Create a CSV file with some rows in UTF-8 Chinese and some with Latin-1 characters. Upload/paste it. Click Parse.
**Expected:** Parser handles encoding. Either auto-detects UTF-8 or shows encoding error. Does not crash.
**PASS:** Either parses correctly or shows clear encoding error. No garbled text in preview.
**FAIL:** App crashes. Partial parse with garbled rows. Infinite loop.

### T6.4 -- Very large CSV (10MB limit)
**Steps:** Generate a CSV file larger than 10MB. Attempt to upload.
**Expected:** File rejected with message: "File too large. Maximum size: 10MB". Upload button disabled or error shown.
**PASS:** Clear file size error. File is not sent to worker.
**FAIL:** File upload hangs. Browser tab crashes from memory. File silently truncated.

### T6.5 -- BERT calibration without BERT loaded
**Steps:** Load Pyodide engine. Do NOT load BERT model. On DataInput, click "Calibrate with BERT Embedding".
**Expected:** Warning or error: "BERT model not loaded. Please load BERT model first." Button is disabled or shows inline message. Does not attempt calibration.
**PASS:** Clear error message. BERT calibration blocked. Regular (keyword) calibration still works.
**FAIL:** Attempts BERT calibration and hangs. Vague error from Transformers.js. Crashes.

### T6.6 -- Rapid pipeline re-run
**Steps:** Run full pipeline successfully. Immediately (without waiting) click "Run Pipeline" again.
**Expected:** Either the button is disabled during an active run, or the new run cancels/queues after the current one. No duplicate parallel executions.
**PASS:** Only one pipeline instance runs at a time. Results are not corrupted by parallel execution.
**FAIL:** Two pipeline instances run simultaneously. Results overlap/corrupt. App crashes.

### T6.7 -- Results page without data
**Steps:** Navigate directly to `http://127.0.0.1:3000/results` without running any analysis.
**Expected:** Empty state shown: "No analysis results yet" or similar. Export buttons are disabled. Tabs show no content. User is directed to run a pipeline first.
**PASS:** Clean empty state. No blank page. No console errors. Clear path back to DataInput/Dashboard.
**FAIL:** Blank white screen. React crashes (white screen of death). Export buttons clickable but do nothing or error.

### T6.8 -- Reset pipeline state
**Steps:** Run full pipeline. On Dashboard or via PipelineStatus widget, click "Reset".
**Expected:** All pipeline state clears. PipelineStatus shows "idle". Results page shows empty state. DataInput clears or shows previously entered data.
**PASS:** State reset to idle. No stale results visible. Can run a fresh pipeline.
**FAIL:** Reset does nothing. Residual state causes errors in next run. Reset clears engine state too (engine should remain loaded).

---

## Quick-Reference: Test Data

**CSV text corpus (use for T4.1, T4.3, T5.1):**
```csv
id,text
case_01,"The government response was very fast and effective"
case_02,"I am extremely dissatisfied with the poor service"
case_03,"建议政府提高办事效率"
case_04,"严重怀疑政策能否执行到位"
case_05,"满意，已解决问题"
```

**Prototype CSV (use for T4.2, T4.4):**
```csv
编号, 文本内容, 结果
1, 政府第一时间回应了群众诉求, 1
2, 问题处理非常迅速有效, 1
3, 多次投诉仍没有答复, 0
4, 办事人员态度差效率低, 0
```

---

## Execution Order (Explorer Agent)

1. **Smoke test** (T1.1, T2.1, T2.6) -- 3 min. If any fail, STOP. Fix P0s first.
2. **Engine loading deep dive** (T1.2-T1.7) -- 10 min. The known bug is here.
3. **i18n** (T2.2-T2.5, T2.7) -- 5 min.
4. **Settings persistence** (T3.1-T3.6) -- 5 min.
5. **Data input + calibration** (T4.1-T4.8) -- 15 min.
6. **Full pipeline** (T5.1-T5.7) -- 10 min.
7. **Error handling** (T6.1-T6.8) -- 10 min.

**Total: ~58 min** (excluding BERT model downloads)
