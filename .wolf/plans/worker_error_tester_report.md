# DevTools Inspection Report: live.experiment-engine

**Test Date:** 2026-05-27
**URL:** https://qhwangantoneva.github.io/experiment-engine/
**Browser:** Chromium headless (Playwright)

---

## 1. Console Log Summary

### 0 Console Errors
### 0 Page Errors (JS crashes)
### 0 Network Failures (failed requests)

### Successful Console Messages (Pyodide engine load):
```
[log] Loading numpy
[log] Loaded numpy
[log] Loading annotated-types, pydantic, pydantic_core, typing-extensions
[log] Loaded annotated-types, pydantic, pydantic_core, typing-extensions
[log] Loading pyyaml
[log] Loaded pyyaml
[log] Loading micropip, packaging
[log] Loaded micropip, packaging
```

**Conclusion:** No JS errors, no worker crashes, no unhandled rejections at any point. The Pyodide Python-in-browser engine loads all dependencies successfully (numpy, pydantic, pyyaml, micropip, packaging).

### Warning:
- `[warning] Unable to determine content-length from response headers. Will expand buffer when needed.` — emitted when loading BERT model from HuggingFace.

---

## 2. Network Request Analysis

### All successful — no failures

| Asset | Status | Size |
|---|---|---|
| index-CcdgCoKU.js | OK | 221 KB |
| vendor-react-YERAfeWB.js | OK | 54 KB |
| index-BIFYZCpM.css | OK | 4.3 KB |
| pyodide.worker-CbkWeLSt.js | OK | 204 KB |

### HuggingFace BERT model HTTP redirects (not failures):
These are 307/302 redirects from HuggingFace CDN, which the browser follows automatically. They are NOT errors:
- `307 https://huggingface.co/Xenova/bert-base-chinese/resolve/main/config.json`
- `307 https://huggingface.co/Xenova/bert-base-chinese/resolve/main/tokenizer.json`
- `307 https://huggingface.co/Xenova/bert-base-chinese/resolve/main/tokenizer_config.json`
- `302 https://huggingface.co/Xenova/bert-base-chinese/resolve/main/onnx/model_quantized.onnx`

**Result:** BERT model loaded successfully (UI showed "BERT model loaded successfully").

---

## 3. Button State Analysis

### Dashboard Page (initial):
| Button | State |
|---|---|
| "中" (language toggle) | Enabled |
| "Load Engine" | Enabled |
| "Go to Data Input" | Disabled |
| "Save Project" | Disabled |
| "Load Project" | Enabled |
| "Use Template" x5 | Enabled |
| "Clear All Local Data" | Enabled |

### Data Input Page (after Load Engine + Load 30 Sample Cases + Parse Text):
| Button | State |
|---|---|
| "中" | Enabled |
| "Share Link" | Disabled |
| "dataInput.importCsvJson" | Enabled |
| "dataInput.exportCsv" | Disabled |
| "Load BERT Model" | Enabled |
| "Calibrate with BERT Embeddings" | **Disabled** |
| "Paste Text" | Enabled |
| "Upload File" | Enabled |
| "Load 30 Sample Cases" | Enabled |
| "Parse Text" | Enabled |
| "Parse CSV" | Enabled |
| "+ Add Condition" | Enabled |
| **"Calibrate (Text to Fuzzy-Set)"** | **Disabled** |
| **"Run Full Pipeline"** | **Disabled** |
| "Reset" | Enabled |

### Results Page:
| Button | State |
|---|---|
| "中" | Enabled |

---

## 4. Critical Findings

### Finding A: Pipeline buttons remain disabled after loading samples
After clicking "Load 30 Sample Cases" then "Parse Text", the following buttons remain disabled:
- "Calibrate (Text to Fuzzy-Set)" — disabled
- "Calibrate with BERT Embeddings" — disabled
- "Run Full Pipeline" — disabled

Dashboard still shows:
- **Cases Analyzed: 0**
- **Conditions Defined: 0**

This means either:
1. The "Parse Text" action after "Load 30 Sample Cases" did not produce valid parsed data, OR
2. The calibration/pipeline buttons check for additional prerequisites (e.g., defined conditions) before enabling

### Finding B: i18n translation keys exposed in UI
Button text shows raw i18n keys instead of translated labels:
- `dataInput.importCsvJson`
- `dataInput.exportCsv`

This suggests the i18n system may not be properly initialized in the test environment, or fallback translations are missing.

### Finding C: Pyodide worker initializes cleanly
The worker loads all Python dependencies successfully with no errors. The engine status changes from "Not Loaded" to "Ready" after clicking "Load Engine", confirming the worker initialization path works.

### Finding D: BERT model loads successfully on first click
"Load BERT Model" triggers HuggingFace downloads that succeed after redirects. The UI updates to show "BERT model loaded successfully".

---

## 5. Screenshots

Two full-page screenshots were captured:
- `C:/tmp/playwright-test/screenshot_initial.png` — initial Dashboard page
- `C:/tmp/playwright-test/screenshot_final.png` — Data Input page after loading samples

---

## 6. Conclusion

**No worker initialization failure detected.** The app loads, the Pyodide engine initializes, and all Python dependencies are installed correctly. The BERT model loads successfully from HuggingFace.

**The primary UX issue** is that after loading 30 sample cases and clicking Parse Text, the calibrate/analyze/pipeline buttons remain disabled, and the Dashboard continues to show zero cases analyzed and zero conditions defined. This could be:
- A frontend state management issue (parsed data not updating the store correctly)
- A processing requirement not met (e.g., conditions must be defined via the YAML editor before calibration is allowed)
- A silent failure in the text parsing pipeline

The user workflow likely requires: (1) Load Engine, (2) Load 30 Sample Cases, (3) Define conditions in YAML, (4) Parse CSV (not Parse Text, since sample data might be CSV), (5) Then calibrate and run pipeline.
