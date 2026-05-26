# Technical Advisory Plan — QCA Analysis Tool

## Date: 2026-05-27
## Author: Technical Advisor agent

---

## Executive Summary

The FIXER agent's `_fallback_text_scores()` method (trigram Jaccard similarity) **successfully solved the all-0.5 membership problem** for all 5 domains. The remaining issues are **not in calibration** but in **data filtering and outcome assignment**. The core root cause is a single design gap: `run_calibrate()` never reads the CSV `expected_outcome` column.

---

## Diagnostic Results

All diagnostics were run against commit `8807e15` on current master.

### Calibration is working (confirmed)

| Domain | Membership shape | Outcome std | Condition std |
|--------|-----------------|-------------|---------------|
| dissatisfaction | (30, 6) | 0.1689 | 0.2217 |
| trust | (30, 6) | 0.1795 | 0.4110 |
| policy_demand | (30, 6) | 0.1461 | 0.4054 |
| co_production | (30, 5) | 0.1996 | 0.2591 |
| gov_responsiveness | (30, 6) | 0.2604 | 0.3771 |

All domains show non-zero variance in membership. The old all-0.5 bug is fixed.

### All output files exist (contradicts previous report)

All 5 domains have complete output: `fuzzy_data.npz`, `qca_results.json`, `robustness_report.json`, `counterfactual_report.json`, `qca_report.tex`. Missing robustness reports were not confirmed in this session.

---

## Root Cause Analysis

### BUG-1 (CRITICAL): Expected outcome from CSV is never used

**File**: `src/experiment_engine/api.py`, line 54 — `run_calibrate()`

```python
reader = TextCorpusReader()
input_data = reader.read(data_path, text_column=text_column)
```

`TextCorpusReader.read()` with `text_column="text"` reads ONLY the `text` column from the CSV. The `expected_outcome` column is **silently dropped**.

**Consequence**: The outcome column in the membership matrix is computed from trigram Jaccard similarity to the outcome prototype (e.g., for trust: "I trust the government" prototype), NOT from the ground-truth labels in `expected_outcome`. This produces outcome values that:

- Cluster around 0.488 for dissatisfaction (most trigram comparisons land near the crossover point)
- Are near 0.033 for trust (trust outcome prototype mismatches many texts)
- Are near 0.949 for co_production (co_production outcome prototype matches too many texts)

**Proof** — dissatisfaction truth table:
- All 32 truth table rows have outcome=1 (consistency always >= 0.882), even though outcome vector ranges from 0.0 to 1.0
- Consistency threshold=0.75 is always exceeded because the trigram-based outcome fails to discriminate

**Proof** — trust truth table:
- Only 3 of 32 rows pass frequency threshold, all with consistency 0.000-0.040
- No solutions generated because no positive rows exist

### BUG-2 (CRITICAL): No domain filtering

**File**: `src/experiment_engine/api.py`, line 54 — `run_calibrate()`

The same CSV (all 30 cases across 5 domains) is loaded for every domain. There is no filtering like:
```python
df[df['domain'] == current_domain]
```

**Consequence**: The membership matrix always has shape (30, N+1), not (6, N+1). All 30 cases participate in every domain's truth table construction.

### BUG-3: LaTeX solution for dissatisfaction is empty

**File**: `src/experiment_engine/report/qca_reporter.py`, line 189-199

When ALL truth table rows have outcome=1 (dissatisfaction), the minimizer produces a "vacuous" solution (always-true), which formats as an empty formula `"Formula: $\displaystyle $"`. The LaTeX reporter doesn't distinguish between "no solution" and "vacuous solution".

**File**: `src/experiment_engine/qca_engine/solution.py`, line 102-109

`format_formula()` concatenates term labels with "+". If the sole term has an empty label (the always-true term from QM minimization), the result is an empty string, which is passed to LaTeX as `""`.

### BUG-4: Visualization module never called

**Files**: `src/experiment_engine/viz/qca_plots.py`, `run_pipeline.py`

`QCAPlotBuilder` has 5 plot types (truth_table_heatmap, necessity_xy_plot, sufficiency_xy_plot, fuzzy_distribution_plot, solution_bar_chart). `MatplotlibRenderer` can render them. But `run_pipeline.py` never imports or calls visualization.

---

## Fix Plan

### Fix 1: Modify `run_calibrate()` to use CSV expected_outcome + domain filter

**File**: `src/experiment_engine/api.py`

Change `run_calibrate()` from:

```python
reader = TextCorpusReader()
input_data = reader.read(data_path, text_column=text_column)
stage = TextCalibrationStage(cs)
stage.setup()
result = stage.process(input_data)
```

To something like:

```python
# Read CSV with pandas to get texts + outcomes + domain
pd = _get_pandas()
df = pd.read_csv(data_path)
# Filter by domain if specified
domain = cs.domain.value
domain_df = df[df['domain'] == domain]
texts = domain_df[text_column].tolist()
outcomes = domain_df['expected_outcome'].to_numpy(dtype=np.float64)

# Create InputData from filtered texts
from experiment_engine.models import InputData
input_data = InputData(
    data=np.array(texts, dtype=object),
    columns=[text_column],
    index=domain_df.get('text_id', [None]).tolist() if 'text_id' in domain_df.columns else None,
)

# Use process_with_outcome to inject CSV outcome labels
stage = TextCalibrationStage(cs)
stage.setup()
result = stage.process_with_outcome(input_data, outcome_vector=outcomes)
```

**Why**: `TextCalibrationStage.process_with_outcome()` already exists (calibrator.py line 398-459). It accepts a pre-supplied outcome vector and injects it as the last column while computing conditions normally. This is the correct, non-breaking fix.

**Why domain filtering**: Each domain should only analyze its own cases. Without filtering, co_production texts pollute the trust truth table.

### Fix 2: Handle vacuous solution in LaTeX reporter

**File**: `src/experiment_engine/report/qca_reporter.py`, line 187-199

Add a check: if the formula is empty or the solution type has no meaningful terms, either skip it or label it as "Vacuous solution (always true)".

```python
for sol_type in ("complex", "parsimonious", "intermediate"):
    sol = getattr(result.solutions, sol_type, None)
    if sol and sol.terms and sol.formula and sol.formula != "No solution":
        # render formula
    elif sol and sol.terms:
        # vacuous solution (all-1 outcome) — show explanation
```

### Fix 3: Add visualization generation to `run_pipeline.py`

**File**: `run_pipeline.py`

After `run_analyze()`, add:

```python
from experiment_engine.viz.qca_plots import QCAPlotBuilder
from experiment_engine.viz.matplotlib_renderer import MatplotlibRenderer
from experiment_engine.models import InputData

vis_dir = os.path.join(out_dir, 'visualizations')
os.makedirs(vis_dir, exist_ok=True)

viz = QCAPlotBuilder()
renderer = MatplotlibRenderer()

# 1. Truth table heatmap
tt_data = viz.truth_table_heatmap(result.truth_table)
if tt_data:
    # Convert QCAPlotBuilder dict to InputData for renderer
    # ... render truth_table_heatmap ...

# 2. Fuzzy distribution plot
dist_data = viz.fuzzy_distribution_plot(result.fuzzy_data)

# 3. Solution bar charts (if solutions exist)
```

### Fix 4: Process with `run_pipeline.py`

Regenerate all output by running `uv run python run_pipeline.py`.

---

## Dependency Graph

```
Fix 1 (api.py run_calibrate) ──► Fix 4 (re-run pipeline)
                                         │
                                          ├─► Fix 2 (LaTeX reporter) becomes meaningful
                                          │    (real outcome variance → real truth tables → real solutions)
                                          │
                                          ├─► Fix 3 (visualization) uses real data
                                          │
                                          └─► All 5 domains produce correct QCA results
```

Fixes 1 and 2 can be done in parallel. Fix 3 depends on Fix 1 for meaningful visualization. Fix 4 is last.

---

## Files to Modify

| File | Change | Priority |
|------|--------|----------|
| `src/experiment_engine/api.py` (line 30-61) | Add pandas-based domain filtering + `process_with_outcome` | P0 |
| `src/experiment_engine/report/qca_reporter.py` (line 187-199) | Handle vacuous/empty solution formulas | P1 |
| `run_pipeline.py` (after step 4) | Add visualization generation block | P1 |

## Files to Read Before Fixing

- `src/experiment_engine/text_calibration/calibrator.py` (lines 398-459) — `process_with_outcome()` signature to verify correct usage
- `src/experiment_engine/models/qca.py` (lines 205-259) — `MembershipData` constructor to verify membership shape requirements
- `src/experiment_engine/viz/qca_plots.py` — `QCAPlotBuilder` return types to understand how to feed results to `MatplotlibRenderer`
- `src/experiment_engine/viz/matplotlib_renderer.py` — `MatplotlibRenderer.render()` signature to understand required `InputData` + `RenderConfig` format

---

## Verification After Fix

After implementing all fixes and running `uv run python run_pipeline.py`:

1. Membership matrix should be shape (6, N+1) for each domain (6 cases, not 30)
2. Outcome column should match CSV `expected_outcome` values (0.0 or 1.0)
3. Truth table should have varied outcome values (both 0 and 1)
4. Complex solutions should exist for all domains with meaningful formulas
5. LaTeX reports should show non-empty solution sections
6. Visualization directory should contain generated PNG/SVG files
7. Necessity analysis should not show both X and ~X as necessary
