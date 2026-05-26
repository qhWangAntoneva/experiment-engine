#!/usr/bin/env python
"""Validate all 5 domain QCA outputs and print summary."""

import json
import os
import sys

import numpy as np

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qca_output")
DOMAINS = [
    "dissatisfaction",
    "policy_demand",
    "co_production",
    "trust",
    "gov_responsiveness",
]


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_npz(path):
    return np.load(path, allow_pickle=True)


def validate_consistency(v, name, context=""):
    ok = isinstance(v, (int, float)) and 0.0 <= v <= 1.0
    if not ok:
        print(f"  WARN: {context}{name}={v} is outside [0,1]")
    return ok


def fmt_arr(arr, key):
    """Format array stats, handling both numeric and string arrays."""
    if np.issubdtype(arr.dtype, np.number):
        return (
            f"  {key}: shape={arr.shape}, dtype={arr.dtype}, "
            f"min={arr.min():.4f}, max={arr.max():.4f}, "
            f"mean={arr.mean():.4f}, std={arr.std():.4f}"
        )
    # String arrays (condition_names, outcome_name, case_ids)
    return f"  {key}: shape={arr.shape}, dtype={arr.dtype}"


def check_near_zero_variance(arr, key):
    """Check for near-zero variance (degenerate data). Only applies to numeric arrays."""
    if not np.issubdtype(arr.dtype, np.number):
        return
    if arr.std() < 0.001:
        print(
            f"    WARN: {key} has near-zero variance (std={arr.std():.4f}) - all values ~{arr.mean():.4f}"
        )
    uniq = np.unique(arr)
    if len(uniq) < 5:
        print(f"    WARN: {key} has only {len(uniq)} unique values: {uniq}")


def check_outcome_variation(arr, key, domain):
    """Check that the outcome column has at least 2 unique values."""
    if "outcome" not in key.lower():
        return True
    if not np.issubdtype(arr.dtype, np.number):
        return True
    uniq = np.unique(arr)
    unique_count = len(uniq)
    print(f"    Outcome column: {unique_count} unique value(s): {uniq}")
    if unique_count < 2:
        print(
            f"    WARN: {domain} outcome column has only {unique_count} unique value(s): {uniq}"
        )
        return False
    return True


def summarize_results(domain, results_summary):
    """Summarize results for a single domain and populate results_summary dict."""
    print(f"\n{'=' * 80}")
    print(f"DOMAIN: {domain}")
    print(f"{'=' * 80}")

    d = os.path.join(BASE_DIR, domain)
    results_summary[domain] = {"errors": [], "warnings": [], "pass": True}

    # Check files
    files = os.listdir(d)
    print(f"  Files: {', '.join(files)}")

    # 1. fuzzy_data.npz
    npz_path = os.path.join(d, "fuzzy_data.npz")
    if os.path.exists(npz_path):
        try:
            data = load_npz(npz_path)
            print("\n  --- fuzzy_data.npz ---")
            for key in data.files:
                arr = data[key]
                print(f"    {fmt_arr(arr, key)}")
                # Check for flat 0.5 (degenerate)
                check_near_zero_variance(arr, key)
                # Check outcome variation
                if key == "outcome_name" or (
                    key == "membership" and "outcome" in str(key)
                ):
                    pass
                # Membership shape check
                if key == "membership":
                    if arr.ndim != 2:
                        print(
                            f"    WARN: membership matrix is not 2D (ndim={arr.ndim})"
                        )
                        results_summary[domain]["warnings"].append(
                            f"membership not 2D: ndim={arr.ndim}"
                        )
                    else:
                        n_cases, n_cols = arr.shape
                        print(
                            f"    Membership matrix: {n_cases} cases x {n_cols} columns"
                        )
                        if n_cases < 2:
                            print(f"    WARN: only {n_cases} case(s) — degenerate")
                            results_summary[domain]["warnings"].append(
                                f"membership has < 2 cases: {n_cases}"
                            )
                        if n_cols < 2:
                            print(f"    WARN: only {n_cols} column(s) — need >= 2")
                            results_summary[domain]["warnings"].append(
                                f"membership has < 2 columns: {n_cols}"
                            )
                        # Outcome column check: last column of membership
                        if n_cols >= 1:
                            outcome_col = arr[:, -1]
                            if not check_outcome_variation(
                                outcome_col, f"{key}[outcome_col]", domain
                            ):
                                results_summary[domain]["warnings"].append(
                                    "outcome column has < 2 unique values"
                                )
            data.close()
        except Exception as e:
            print(f"  ERROR loading npz: {e}")
            results_summary[domain]["errors"].append(f"npz load error: {e}")
            results_summary[domain]["pass"] = False
    else:
        print("  MISSING: fuzzy_data.npz")
        results_summary[domain]["errors"].append("missing fuzzy_data.npz")
        results_summary[domain]["pass"] = False

    # 2. qca_results.json
    results_path = os.path.join(d, "qca_results.json")
    if not os.path.exists(results_path):
        print("  MISSING: qca_results.json")
        results_summary[domain]["errors"].append("missing qca_results.json")
        results_summary[domain]["pass"] = False
        return

    r = load_json(results_path)
    tt = r.get("truth_table", {})
    sol = r.get("solutions", {})
    nec = r.get("necessity", {})
    suf = r.get("sufficiency", {})
    meta = r.get("metadata", {})
    cs = r.get("condition_set", {})

    print("\n  --- Truth Table ---")
    print(f"    Outcome: {tt.get('outcome_name', '?')}")
    print(f"    Conditions: {tt.get('condition_names', [])}")
    print(f"    n_cases: {tt.get('n_cases', '?')}")
    print(f"    Consistency threshold: {tt.get('consistency_threshold', '?')}")
    print(f"    Frequency threshold: {tt.get('frequency_threshold', '?')}")

    rows = tt.get("rows", [])
    print(f"    Total rows: {len(rows)}")

    if rows:
        freqs = [r["frequency"] for r in rows]
        consistencies = [r["raw_consistency"] for r in rows]
        outcome_values = [r["outcome_value"] for r in rows]
        included = [r["included"] for r in rows]

        print(
            f"    Frequency: min={min(freqs):.1f}, max={max(freqs):.1f}, mean={np.mean(freqs):.1f}"
        )
        print(
            f"    Raw consistency: min={min(consistencies):.4f}, max={max(consistencies):.4f}"
        )
        print(f"    Outcome values: {set(outcome_values)}")
        print(f"    Included: {sum(included)}/{len(included)} rows")

        # Check for variance issues
        if len(set(freqs)) == 1:
            print(
                f"    WARN: All {len(freqs)} rows have identical frequency {freqs[0]}"
            )
            results_summary[domain]["warnings"].append(
                "all rows have identical frequency"
            )
        if len(set(consistencies)) == 1:
            print(
                f"    WARN: All {len(consistencies)} rows have identical consistency {consistencies[0]}"
            )
            results_summary[domain]["warnings"].append(
                "all rows have identical consistency"
            )
        if len(set(outcome_values)) < 2:
            print(
                f"    WARN: Outcome has only {len(set(outcome_values))} unique value(s): {set(outcome_values)}"
            )
            results_summary[domain]["warnings"].append(
                f"outcome has < 2 unique values: {set(outcome_values)}"
            )
    else:
        results_summary[domain]["errors"].append("truth table has 0 rows")
        results_summary[domain]["pass"] = False

    print("\n  --- Solutions ---")
    for sol_type in ["complex", "parsimonious", "intermediate"]:
        s = sol.get(sol_type)
        if s is None:
            print(f"    {sol_type}: None")
            results_summary[domain]["warnings"].append(f"{sol_type} solution: None")
            continue
        formula = s.get("formula", "")
        sol_cons = s.get("solution_consistency", 0)
        sol_cov = s.get("solution_coverage", 0)
        n_terms = len(s.get("terms", []))
        print(
            f"    {sol_type}: formula='{formula}', terms={n_terms}, consistency={sol_cons:.4f}, coverage={sol_cov:.4f}"
        )
        validate_consistency(sol_cons, f"{sol_type}.solution_consistency")
        validate_consistency(sol_cov, f"{sol_type}.solution_coverage")

        # Solution quality check: non-empty with non-zero consistency
        if n_terms > 0 or (formula and formula.strip()):
            if sol_cons == 0.0 and sol_cov == 0.0:
                print(f"    WARN: {sol_type} has terms but zero consistency/coverage")
                results_summary[domain]["warnings"].append(
                    f"{sol_type} has terms but zero consistency/coverage"
                )
        else:
            # Empty solution -- could be vacuous or degenerate
            print(f"    WARN: {sol_type} solution is empty/missing")
            results_summary[domain]["warnings"].append(f"{sol_type} solution is empty")

    # Solution quality score
    print("\n  --- Solution Quality Score ---")
    quality_scores = {}
    for sol_type in ["complex", "parsimonious", "intermediate"]:
        s = sol.get(sol_type)
        if s is not None:
            sc = s.get("solution_consistency", 0)
            sv = s.get("solution_coverage", 0)
            if sc is not None and sv is not None and sc > 0 and sv > 0:
                q = sc * sv
                quality_scores[sol_type] = q
                print(
                    f"    {sol_type}: consistency={sc:.4f} x coverage={sv:.4f} = {q:.4f}"
                )
    if quality_scores:
        best_type = max(quality_scores, key=quality_scores.get)
        avg_score = sum(quality_scores.values()) / len(quality_scores)
        print(f"    Best: {best_type} ({quality_scores[best_type]:.4f})")
        print(f"    Average quality: {avg_score:.4f}")
        results_summary[domain]["quality_score"] = avg_score
    else:
        print("    No valid solutions to score")
        results_summary[domain]["quality_score"] = 0.0

    # Outcome variation check from truth table
    if rows:
        unique_outcomes = set(outcome_values)
        if len(unique_outcomes) < 2:
            print(
                f"\n    FAIL: Outcome has no variation (only {unique_outcomes}) - solutions will be vacuous"
            )
            results_summary[domain]["errors"].append(
                f"outcome has no variation: {unique_outcomes}"
            )
            results_summary[domain]["pass"] = False

    print(f"\n  --- Necessity (threshold={nec.get('threshold', '?')}) ---")
    conds = nec.get("conditions", [])
    print(f"    Outcome: {nec.get('outcome_name', '?')}")
    print(f"    Conditions analyzed: {len(conds)}")
    necessary = [c for c in conds if c.get("is_necessary")]
    print(f"    Necessary conditions: {len(necessary)}/{len(conds)}")
    for c in necessary:
        print(
            f"      {c['condition_name']}: consistency={c['consistency']:.4f}, coverage={c['coverage']:.4f}"
        )
        validate_consistency(c["consistency"], f"nec.{c['condition_name']}.consistency")
        validate_consistency(c["coverage"], f"nec.{c['condition_name']}.coverage")

    # Sanity check: both X and ~X can't be necessary in real data
    cond_names = list({c["condition_name"].replace("~", "") for c in conds})
    for cn in cond_names:
        has_pos = any(c["condition_name"] == cn and c["is_necessary"] for c in conds)
        has_neg = any(
            c["condition_name"] == f"~{cn}" and c["is_necessary"] for c in conds
        )
        if has_pos and has_neg:
            print(
                f"    WARN: Both {cn} AND ~{cn} are necessary (possible only if all fuzzy values = 0.5)"
            )
            results_summary[domain]["warnings"].append(
                f"both {cn} AND ~{cn} are necessary"
            )

    print("\n  --- Sufficiency ---")
    suf_sols = suf.get("solutions", {})
    for sol_type in ["complex", "parsimonious", "intermediate"]:
        s = suf_sols.get(sol_type)
        if s is None:
            print(f"    {sol_type}: None")
        else:
            sol_cons = s.get("solution_consistency", 0)
            sol_cov = s.get("solution_coverage", 0)
            print(f"    {sol_type}: consistency={sol_cons:.4f}, coverage={sol_cov:.4f}")
            validate_consistency(sol_cons, f"suf.{sol_type}.solution_consistency")

    print("\n  --- Condition Set ---")
    print(f"    Name: {cs.get('name', '?')}")
    print(f"    Domain: {cs.get('domain', '?')}")
    print(f"    Outcome: {cs.get('outcome', {}).get('name', '?')}")
    conds_list = cs.get("conditions", [])
    print(f"    Conditions ({len(conds_list)}):")
    for c in conds_list:
        cal = c.get("calibration_type", "?")
        params = c.get("calibration_params", {})
        print(
            f"      {c['name']}: cal={cal}, full_in={params.get('threshold_full_in')}, crossover={params.get('crossover_point')}, full_out={params.get('threshold_full_out')}"
        )

    print("\n  --- Metadata ---")
    print(f"    consistency_threshold: {meta.get('consistency_threshold', '?')}")
    print(f"    frequency_threshold: {meta.get('frequency_threshold', '?')}")

    # 3. counterfactual_report.json
    cf_path = os.path.join(d, "counterfactual_report.json")
    if os.path.exists(cf_path):
        cf = load_json(cf_path)
        print("\n  --- Counterfactual Report ---")
        for key in cf:
            val = cf[key]
            if isinstance(val, list):
                print(f"    {key}: {len(val)} items")
                if val and isinstance(val[0], dict):
                    for item in val[:3]:
                        print(f"      {dict(list(item.items())[:5])}")
            elif isinstance(val, dict):
                print(f"    {key}: {dict(list(val.items())[:5])}")
            else:
                print(f"    {key}: {val}")
    else:
        print("\n  MISSING: counterfactual_report.json")

    # 4. robustness_report.json
    rb_path = os.path.join(d, "robustness_report.json")
    if os.path.exists(rb_path):
        rb = load_json(rb_path)
        print("\n  --- Robustness Report ---")
        for key in rb:
            val = rb[key]
            if isinstance(val, float):
                print(f"    {key}: {val:.4f}")
            elif isinstance(val, list):
                print(f"    {key}: {len(val)} items")
                if val:
                    print(f"      First: {val[0]}")
            else:
                print(f"    {key}: {val}")
    else:
        print("\n  MISSING: robustness_report.json")

    # 5. qca_report.tex
    tex_path = os.path.join(d, "qca_report.tex")
    if os.path.exists(tex_path):
        size = os.path.getsize(tex_path)
        print("\n  --- LaTeX Report ---")
        print(f"    Size: {size} bytes")
        with open(tex_path, encoding="utf-8") as f:
            first_lines = f.readlines()[:10]
        print(f"    First lines: {[line.strip() for line in first_lines]}")
    else:
        print("\n  MISSING: qca_report.tex")

    # 6. PNG files
    pngs = [f for f in files if f.endswith(".png")]
    if pngs:
        print("\n  --- Visualizations ---")
        for p in pngs:
            print(f"    {p} ({os.path.getsize(os.path.join(d, p))} bytes)")
    else:
        print("\n  NO visualization files (*.png)")


def print_summary_table(results_summary):
    """Print a pass/fail summary table per domain."""
    print(f"\n{'#' * 80}")
    print("# VALIDATION SUMMARY")
    print(f"{'#' * 80}")
    print()
    header = (
        f"{'Domain':<25} {'Status':<10} {'Errors':<8} {'Warnings':<10} {'Quality':<10}"
    )
    print(header)
    print("-" * len(header))
    all_pass = True
    total_errors = 0
    total_warnings = 0
    total_quality = 0.0
    n_with_quality = 0
    for domain, info in results_summary.items():
        status = "PASS" if info["pass"] else "FAIL"
        n_err = len(info["errors"])
        n_warn = len(info["warnings"])
        q = info.get("quality_score", 0.0)
        q_str = f"{q:.4f}" if q > 0 else "N/A"
        print(f"{domain:<25} {status:<10} {n_err:<8} {n_warn:<10} {q_str:<10}")
        if not info["pass"]:
            all_pass = False
        total_errors += n_err
        total_warnings += n_warn
        if q > 0:
            total_quality += q
            n_with_quality += 1
    avg_q = total_quality / n_with_quality if n_with_quality > 0 else 0.0
    print("-" * len(header))
    print(
        f"{'TOTAL':<25} {'PASS' if all_pass else 'FAIL':<10} {total_errors:<8} {total_warnings:<10} {avg_q:.4f}"
    )
    print()
    if not all_pass:
        print("FAILED DOMAINS:")
        for domain, info in results_summary.items():
            if not info["pass"]:
                print(f"  - {domain}: {', '.join(info['errors'])}")
    print()


def main():
    print(f"{'#' * 80}")
    print("# QCA PIPELINE OUTPUT VALIDATION")
    print(f"{'#' * 80}")
    print(f"Base directory: {BASE_DIR}")
    print(f"Domains: {DOMAINS}")

    results_summary = {}

    for domain in DOMAINS:
        d = os.path.join(BASE_DIR, domain)
        if not os.path.isdir(d):
            print(f"\n{'=' * 80}")
            print(f"DOMAIN: {domain} - DIRECTORY NOT FOUND")
            results_summary[domain] = {
                "errors": ["directory not found"],
                "warnings": [],
                "pass": False,
            }
            continue
        summarize_results(domain, results_summary)

    print_summary_table(results_summary)

    print(f"{'#' * 80}")
    print("# VALIDATION COMPLETE")
    print(f"{'#' * 80}")

    # Exit with non-zero code if any domain failed
    if any(not info["pass"] for info in results_summary.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
