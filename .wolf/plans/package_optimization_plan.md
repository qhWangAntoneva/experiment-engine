# Package Optimization Plan — QCA Analysis Tool

**Author:** 包体优化师 (Package Optimizer)
**Date:** 2026-05-27
**Status:** PLAN (not yet implemented)

---

## 1. Investigation Summary

### 1.1 What Exists in Viz Module (src/experiment_engine/viz/)

| File | Description | Integration Status |
|------|-------------|-------------------|
| `__init__.py` | Exports MatplotlibRenderer, PlotlyRenderer, ConsoleRenderer, StreamlitDashboard | OK |
| `base.py` | Abstract `Renderer` base class | OK |
| `qca_plots.py` | `QCAPlotBuilder` — 5 static methods: `truth_table_heatmap()`, `necessity_xy_plot()`, `sufficiency_xy_plot()`, `fuzzy_distribution_plot()`, `solution_bar_chart()` | **NOT called anywhere** |
| `matplotlib_renderer.py` | `MatplotlibRenderer` — renders to PNG/SVG/PDF from `InputData` + `RenderConfig` | **Impedance mismatch** |
| `plotly_renderer.py` | `PlotlyRenderer` — renders to interactive HTML from `InputData` + `RenderConfig` | **Impedance mismatch** |
| `console.py` | `ConsoleRenderer` — Rich terminal output | Not needed for file output |
| `streamlit_dashboard.py` | `StreamlitDashboard` — interactive web dashboard | Not needed for file output |

**Critical finding**: QCAPlotBuilder produces plain dicts (numpy arrays). MatplotlibRenderer/PlotlyRenderer expect `InputData` objects. These two layers cannot currently talk to each other without a bridge.

### 1.2 What Exists in Report Module (src/experiment_engine/report/)

| File | Description | Integration Status |
|------|-------------|-------------------|
| `qca_reporter.py` | `QCALaTeXReporter` — generates `qca_report.tex` | Called in `run_pipeline.py` step 5 |
| `docx_reporter.py` | `QCADocxReporter` — generates .docx bytes | **NOT called anywhere** |
| `latex_reporter.py` | `LaTeXReporter` — general pipeline LaTeX report | Not QCA-specific |

### 1.3 What the Pipeline Currently Generates (run_pipeline.py)

| Step | Output File | Status |
|------|-------------|--------|
| 1. Calibrate | `fuzzy_data.npz` | Working (variance present) |
| 2. Analyze | `qca_results.json` | Working (solutions are empty/broken) |
| 3. Robustness | `robustness_report.json` | Working |
| 4. Counterfactuals | `counterfactual_report.json` | Working |
| 5. LaTeX Report | `qca_report.tex` | Working (sections are empty due to empty solutions) |
| **MISSING** | `*.png` visualizations | **Not generated** |
| **MISSING** | `*.html` interactive charts | **Not generated** |
| **MISSING** | `*.docx` Chinese report | **Not generated** |

### 1.4 API Exposure (api.py)

- `run_report()` only supports `fmt='latex'` or `fmt='console'` — no DOCX, no viz
- No function exists to generate visualizations programmatically
- No function exists to generate DOCX reports

### 1.5 Root-Level Stale Files

The files at `qca_output/fuzzy_data.npz`, `qca_output/qca_results.json`, `qca_output/robustness_report.json`, and `qca_output/qca_report.tex` are from an older pipeline run that did not use domain subdirectories. They should be cleaned up.

### 1.6 Current Output Quality Issues

| Issue | Severity | Root Cause |
|-------|----------|------------|
| All truth table rows have outcome=1 | **CRITICAL** | Calibration bug — outcome membership too high for all cases |
| Solutions are empty/broken | **CRITICAL** | Consequence of all-1 outcome — minimizer has no contrast |
| No visualizations | HIGH | Viz module never integrated into pipeline |
| No DOCX reports | HIGH | DOCX reporter never integrated |
| Root-level stale files | LOW | Leftover from earlier run |
| validate_qca_output.py no summary | LOW | Script only prints, doesn't generate summary file |

### 1.7 Dependencies

The solution-emptiness problem is the **primary blocker** for nearly all output quality improvements:
- Empty solutions -> `solution_bar_chart()` has no data
- Empty solutions -> `sufficiency_xy_plot()` has no data
- Empty solutions -> LaTeX solution sections are blank
- Empty solutions -> DOCX reports say "未找到有效的解"

Fixes that do NOT depend on solutions:
- `truth_table_heatmap()` — depends on truth table only (data is valid)
- `necessity_xy_plot()` — depends on necessity results (data is valid)
- `fuzzy_distribution_plot()` — depends on fuzzy data only (data is valid)
- DOCX report title page, truth table, necessity table — can be generated now
- Pipeline integration of viz module — can be set up now

---

## 2. Proposed Output Structure

### 2.1 Standard Per-Domain Output (after full successful run)

Each domain directory under `qca_output/{domain}/` should contain:

```
qca_output/{domain}/
  fuzzy_data.npz              [REQUIRED] — fuzzy membership matrix
  qca_results.json            [REQUIRED] — truth table, solutions, necessity, sufficiency
  robustness_report.json      [REQUIRED] — robustness test results
  counterfactual_report.json  [REQUIRED] — counterfactual analysis results
  qca_report.tex              [REQUIRED] — LaTeX report
  qca_report.docx             [OPTIONAL] — Chinese Word report
  truth_table_heatmap.png     [OPTIONAL] — truth table visualization
  necessity_xy_plot.png       [OPTIONAL] — necessity consistency vs coverage scatter
  sufficiency_xy_plot.png     [OPTIONAL] — sufficiency consistency vs coverage scatter
  membership_distribution.png [OPTIONAL] — histogram of fuzzy-set scores
  solution_bar_chart.png      [OPTIONAL] — solution term metrics bar chart
  qca_output_summary.json     [OPTIONAL] — machine-readable summary of quality
```

### 2.2 Summary Index File

A file at `qca_output/pipeline_summary.json` containing:

```json
{
  "pipeline_version": "0.2.0",
  "generated_at": "2026-05-27T...",
  "n_domains": 5,
  "domains": {
    "dissatisfaction": {
      "n_cases": 6,
      "n_conditions": 5,
      "outcome": "satisfaction_improvement",
      "solutions_found": true,
      "files_present": ["fuzzy_data.npz", "qca_results.json", ...],
      "warnings": []
    },
    ...
  },
  "overall_quality": "good" | "degraded" | "failed"
}
```

---

## 3. Plan: Integration Steps

### Step 1: Bridge QCAPlotBuilder dicts -> InputData/RenderConfig (Priority: HIGH)

**Problem**: QCAPlotBuilder returns raw dicts. MatplotlibRenderer/PlotlyRenderer expect `InputData` + `RenderConfig`.

**Solution**: Create a bridge function in `viz/__init__.py` or a new `viz/bridge.py`:

```python
def plot_builder_to_inputdata(plot_data: dict) -> tuple[InputData, RenderConfig]:
    """Convert QCAPlotBuilder output dict to (InputData, RenderConfig) pair."""
```

Each of the 5 plot types needs its own converter. The converters should:
- Extract data arrays from the dict
- Build `InputData(data=..., columns=..., index=...)`
- Build `RenderConfig(plot_type=..., title=..., xlabel=..., ylabel=..., output_path=..., figsize=..., dpi=...)`

### Step 2: Add viz functions to api.py (Priority: HIGH)

Add to `api.py`:

```python
def run_viz(
    results_path: str,
    fuzzy_data_path: str,
    output_dir: str = ".",
    formats: list[str] = ["png"],
    include_plots: list[str] = ["truth_table_heatmap", "necessity_xy_plot",
                                 "fuzzy_distribution_plot"],
) -> list[str]:
    """Generate visualization files from QCA results."""
```

Non-solution-dependent plots (`truth_table_heatmap`, `necessity_xy_plot`, `fuzzy_distribution_plot`) should be generated unconditionally. Solution-dependent plots (`sufficiency_xy_plot`, `solution_bar_chart`) should be generated only if solutions exist.

### Step 3: Add DOCX to api.py (Priority: HIGH)

Add to `api.py`:

```python
def run_docx_report(
    results_path: str,
    output_dir: str = ".",
    robustness_path: str | None = None,
    chart_paths: dict[str, str] | None = None,
) -> str:
    """Generate a Chinese Word (.docx) report from QCA results."""
```

This should call `QCADocxReporter.generate()` with chart PNG bytes embedded.

### Step 4: Integrate into run_pipeline.py (Priority: HIGH)

Add steps 6 and 7 to `run_pipeline.py`:

```python
# Step 6: Visualization
print('  Step 6: Visualization...')
viz_files = run_viz(results_path=..., fuzzy_data_path=..., output_dir=out_dir)

# Step 7: DOCX Report
print('  Step 7: DOCX Report...')
docx_path = run_docx_report(results_path=..., output_dir=out_dir, chart_paths={...})
```

### Step 5: Integrate into CLI (Priority: MEDIUM)

Add a new CLI command or extend the existing `report` command:

```bash
qca report --results qca_results.json --format docx
qca report --results qca_results.json --format viz --output-dir figures/
```

Also add viz generation to the `qca run` command.

### Step 6: Update validate_qca_output.py (Priority: MEDIUM)

Add checks for:
- PNG files presence and non-zero size
- Solution quality (formula non-empty, consistency > 0)
- DOCX file presence
- Generate `qca_output_summary.json` as output of validation

### Step 7: Clean up stale root files (Priority: LOW)

Before the next full pipeline run, delete:
- `qca_output/fuzzy_data.npz`
- `qca_output/qca_results.json`
- `qca_output/robustness_report.json`
- `qca_output/qca_report.tex`

These are superseded by domain-subdirectory files.

---

## 4. Implementation Order

### 4.1 What CAN be done now (does not depend on calibration fix)

| Item | Effort | Reason |
|------|--------|--------|
| Bridge function (QCAPlotBuilder -> InputData) | 2-3 hours | Pure adapter code, all existing classes stable |
| `run_viz()` in api.py | 1 hour | Wrapper around bridge + renderers |
| `truth_table_heatmap` + `necessity_xy_plot` generation | 1 hour | Only need truth table + necessity data (both work now) |
| `fuzzy_distribution_plot` generation | 1 hour | Only needs fuzzy_data.npz (works now) |
| `run_docx_report()` in api.py | 1-2 hours | Wrapper around `QCADocxReporter.generate()` |
| DOCX integration for non-solution sections | 1-2 hours | Title page, truth table, necessity all work now |
| Integrate steps 6-7 into `run_pipeline.py` | 2 hours | Straightforward wiring |
| Clean up stale root files | 5 minutes | `rm` command |
| `pipeline_summary.json` generation | 1-2 hours | New function |

**Total independent work**: ~10-12 hours

### 4.2 What must wait for calibration fix

| Item | Effort | Dependency |
|------|--------|------------|
| `sufficiency_xy_plot` | 1 hour | Requires non-empty solution terms |
| `solution_bar_chart` | 1 hour | Requires non-empty solution terms |
| Full LaTeX solution sections | — | Requires non-empty solution terms |
| DOCX executive summary | — | Requires non-empty solution terms |
| Full `validate_qca_output.py` solution checks | — | Requires non-empty solutions |

### 4.3 Runtime vs implementation

The viz step should NOT increase pipeline runtime significantly:
- Membership plots: ~500ms per domain (matplotlib + np.histogram)
- Truth table heatmap: ~200ms per domain
- Necessity XY plot: ~200ms per domain
- Solution plots: ~200ms per domain (when solutions exist)
- DOCX generation: ~500ms per domain

Total added: ~2-3 seconds per domain, ~10-15 seconds total for 5 domains.

---

## 5. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Solution emptiness persists after calibration fix | Medium | High | Implement fallback: if no solutions, skip solution-dependent viz/DOCX sections with a clear warning |
| Matplotlib not available in all environments | Low | Medium | Fall back to Plotly HTML output; check availability at runtime |
| DOCX library (python-docx) not installed | Low | Medium | Check at import time; skip DOCX step with warning |
| Impedance mismatch more complex than expected | Medium | Medium | Build minimal direct matplotlib/plotly plotting functions that bypass Renderer/InputData entirely |
| Running viz on stale (all-0.5) data produces useless charts | Medium | Low | Add variance check before plotting; skip with warning if std < 0.001 |
| Chinese fonts not available for matplotlib | Low | Medium | Fall back to English labels, document font requirement |

---

## 6. Metrics for Success

After implementation, the following should be true:

1. `ls qca_output/{domain}/ | grep -c ".png"` >= 3 for each domain
2. `ls qca_output/{domain}/qca_report.docx` exists for each domain
3. `qca_output/pipeline_summary.json` exists and is valid JSON
4. `validate_qca_output.py` does not produce MISSING warnings for viz or DOCX
5. No stale root-level files remain
6. LaTeX reports show charts as `\includegraphics{}` references
7. DOCX reports have populated sections for truth table, necessity, and (when available) solutions
