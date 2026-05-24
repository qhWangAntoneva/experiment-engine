"""Keyword dictionary import/export — CSV and JSON formats.

Provides functions to import ConditionSet keyword definitions from CSV/JSON
files and export existing ConditionSet definitions to CSV/JSON.

CSV Import Format::

    condition,keyword,weight,notes
    dissatisfaction,somekeyword,1.0,optional note

JSON Import Format::

    {
      "domain": "custom",
      "conditions": [
        {
          "name": "dissatisfaction",
          "keywords": [
            {"keyword": "someword", "weight": 1.0, "notes": "note"}
          ]
        }
      ]
    }

All file I/O uses UTF-8 encoding.
"""

from __future__ import annotations

import csv
import json
from collections import OrderedDict

from experiment_engine.models import (
    CalibrationParams,
    CalibrationType,
    ConditionDefinition,
    ConditionSet,
    KeywordEntry,
    ScoringSource,
    TextDomain,
)

__all__ = [
    "export_keywords_csv",
    "export_keywords_json",
    "import_keywords_csv",
    "import_keywords_json",
]


# ── Import ───────────────────────────────────────────────────────────────────


def import_keywords_csv(
    filepath: str,
    domain: TextDomain | str = TextDomain.DISSATISFACTION,
    name: str = "imported_keywords",
) -> ConditionSet:
    """Import keyword dictionary from a CSV file.

    Expected CSV columns: condition, keyword, weight, notes (optional).

    Rows with the same ``condition`` value are grouped into a single
    ConditionDefinition.  The ``weight`` column must be in [0, 1].
    Duplicate keyword patterns within a condition raise ValueError.

    Args:
        filepath: Path to a UTF-8 CSV file.
        domain: TextDomain or domain string for the resulting ConditionSet.
        name: Name for the resulting ConditionSet.

    Returns:
        A ConditionSet with all imported conditions (no outcome).
    """
    if isinstance(domain, str):
        domain = TextDomain(domain)

    with open(filepath, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)

        # Validate required columns
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")
        for required in ("condition", "keyword", "weight"):
            if required not in reader.fieldnames:
                raise ValueError(
                    f"CSV missing required column: '{required}'. "
                    f"Found: {reader.fieldnames}"
                )

        # Group rows by condition name, preserving insertion order
        cond_keywords: OrderedDict[str, list[dict]] = OrderedDict()
        for row in reader:
            cond_name = row["condition"].strip()
            kw_pattern = row["keyword"].strip()
            kw_weight_raw = row.get("weight", "1.0").strip()
            kw_notes = row.get("notes", "").strip()

            if not cond_name or not kw_pattern:
                raise ValueError(f"Row has empty condition or keyword: {row}")

            # Parse weight — default to 1.0 if empty
            if not kw_weight_raw:
                kw_weight_raw = "1.0"
            try:
                kw_weight = float(kw_weight_raw)
            except ValueError:
                raise ValueError(
                    f"Invalid weight '{kw_weight_raw}' for keyword "
                    f"'{kw_pattern}' in condition '{cond_name}'"
                ) from None

            if not (0.0 <= kw_weight <= 1.0):
                raise ValueError(
                    f"Weight {kw_weight} for keyword '{kw_pattern}' is not in [0, 1]"
                )

            cond_keywords.setdefault(cond_name, []).append(
                {"pattern": kw_pattern, "weight": kw_weight, "notes": kw_notes}
            )

    # Check for duplicate keywords within conditions
    for cond_name, kw_list in cond_keywords.items():
        seen = set()
        for kw in kw_list:
            if kw["pattern"] in seen:
                raise ValueError(
                    f"Duplicate keyword '{kw['pattern']}' in condition '{cond_name}'"
                )
            seen.add(kw["pattern"])

    # Build ConditionDefinitions
    conditions: list[ConditionDefinition] = []
    for cond_name, kw_list in cond_keywords.items():
        conditions.append(
            ConditionDefinition(
                name=cond_name,
                display_name=cond_name,
                domain=domain,
                keywords=[KeywordEntry(**kw) for kw in kw_list],
                calibration_type=CalibrationType.DIRECT,
                calibration_params=CalibrationParams(
                    threshold_full_in=0.80,
                    threshold_full_out=0.20,
                    crossover_point=0.50,
                    direction="ascending",
                ),
                scoring_source=ScoringSource.KEYWORD,
            )
        )

    return ConditionSet(
        name=name,
        description=f"Imported keywords from {filepath}",
        conditions=conditions,
        outcome=None,
        domain=domain,
        scoring_source=ScoringSource.KEYWORD,
    )


def import_keywords_json(
    filepath: str,
    name: str = "imported_keywords",
) -> ConditionSet:
    """Import keyword dictionary from a JSON file.

    Expected JSON structure::

        {
          "domain": "dissatisfaction",
          "conditions": [
            {
              "name": "condition_name",
              "display_name": "Human Label",
              "keywords": [
                {"keyword": "word", "weight": 1.0, "notes": "note", "scope": "bigram"}
              ]
            }
          ],
          "outcome": { ... }  // optional
        }

    Args:
        filepath: Path to a UTF-8 JSON file.
        name: Name for the resulting ConditionSet (overridden if JSON has "name").

    Returns:
        A ConditionSet with all imported conditions.
    """
    with open(filepath, encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be a dict, got {type(data).__name__}")

    domain_str = data.get("domain", "dissatisfaction")
    domain = TextDomain(domain_str)

    cs_name = data.get("name", name)
    cs_description = data.get("description", "")

    raw_conditions = data.get("conditions", [])
    if not isinstance(raw_conditions, list):
        raise ValueError(
            f"'conditions' must be a list, got {type(raw_conditions).__name__}"
        )

    # Validate each condition entry
    conditions: list[ConditionDefinition] = []
    seen_patterns: dict[str, set] = {}  # cond_name -> set of patterns

    for i, cond_data in enumerate(raw_conditions):
        if not isinstance(cond_data, dict):
            raise ValueError(f"Condition[{i}] must be a dict")

        cond_name = cond_data.get("name", "").strip()
        if not cond_name:
            raise ValueError(f"Condition[{i}] missing 'name'")

        # Validate unique condition names
        existing_names = {c.name for c in conditions}
        if cond_name in existing_names:
            raise ValueError(f"Duplicate condition name: '{cond_name}'")

        # Track keyword patterns for uniqueness per condition
        if cond_name not in seen_patterns:
            seen_patterns[cond_name] = set()

        raw_kw_list = cond_data.get("keywords", [])
        if not isinstance(raw_kw_list, list):
            raise ValueError(f"Condition '{cond_name}' keywords must be a list")

        pattern_set: set[str] = set()
        keyword_entries: list[dict] = []
        for kw in raw_kw_list:
            if not isinstance(kw, dict):
                raise ValueError(f"Keyword in condition '{cond_name}' must be a dict")

            # JSON uses "keyword" key, map to "pattern"
            kw_pattern = kw.get("keyword", "")
            if not kw_pattern:
                raise ValueError(
                    f"Keyword in condition '{cond_name}' missing 'keyword'"
                )

            if kw_pattern in pattern_set:
                raise ValueError(
                    f"Duplicate keyword '{kw_pattern}' in condition '{cond_name}'"
                )

            kw_weight = float(kw.get("weight", 1.0))
            if not (0.0 <= kw_weight <= 1.0):
                raise ValueError(
                    f"Weight {kw_weight} for keyword '{kw_pattern}' is not in [0, 1]"
                )

            kw_scope = kw.get("scope", "bigram")
            kw_notes = kw.get("notes", "")

            pattern_set.add(kw_pattern)
            keyword_entries.append(
                {
                    "pattern": kw_pattern,
                    "weight": kw_weight,
                    "scope": kw_scope,
                    "notes": kw_notes,
                }
            )

        seen_patterns[cond_name] = pattern_set

        conditions.append(
            ConditionDefinition(
                name=cond_name,
                display_name=cond_data.get("display_name", cond_name),
                domain=domain,
                keywords=[KeywordEntry(**kw) for kw in keyword_entries],
                calibration_type=CalibrationType(
                    cond_data.get("calibration_type", "direct")
                ),
                calibration_params=_parse_calibration_params(cond_data),
                description=cond_data.get("description", ""),
                scoring_source=ScoringSource(
                    cond_data.get("scoring_source", "keyword")
                ),
            )
        )

    # Optional outcome
    outcome = None
    outcome_data = data.get("outcome")
    if outcome_data and isinstance(outcome_data, dict):
        outcome_kw_list = outcome_data.get("keywords", [])
        outcome_entries = []
        for kw in outcome_kw_list:
            if isinstance(kw, dict):
                outcome_entries.append(
                    {
                        "pattern": kw.get("keyword", ""),
                        "weight": float(kw.get("weight", 1.0)),
                        "scope": kw.get("scope", "bigram"),
                        "notes": kw.get("notes", ""),
                    }
                )

        outcome = ConditionDefinition(
            name=outcome_data.get("name", "outcome"),
            display_name=outcome_data.get("display_name", "Outcome"),
            domain=domain,
            keywords=[KeywordEntry(**kw) for kw in outcome_entries],
            calibration_type=CalibrationType(
                outcome_data.get("calibration_type", "direct")
            ),
            calibration_params=_parse_calibration_params(outcome_data),
            description=outcome_data.get("description", ""),
            scoring_source=ScoringSource(outcome_data.get("scoring_source", "keyword")),
        )

    return ConditionSet(
        name=cs_name,
        description=cs_description,
        conditions=conditions,
        outcome=outcome,
        domain=domain,
        scoring_source=ScoringSource.KEYWORD,
    )


def _parse_calibration_params(
    data: dict,
) -> CalibrationParams | None:
    """Parse calibration params dict or return None."""
    cp = data.get("calibration_params")
    if cp and isinstance(cp, dict):
        return CalibrationParams(
            threshold_full_in=cp.get("threshold_full_in", 0.80),
            threshold_full_out=cp.get("threshold_full_out", 0.20),
            crossover_point=cp.get("crossover_point", 0.50),
            direction=cp.get("direction", "ascending"),
        )
    return None


# ── Export ───────────────────────────────────────────────────────────────────


def export_keywords_csv(condition_set: ConditionSet, filepath: str) -> int:
    """Export keyword dictionary from a ConditionSet to a CSV file.

    Args:
        condition_set: The ConditionSet to export.
        filepath: Destination UTF-8 CSV file path.

    Returns:
        Number of keyword rows written.
    """
    with open(filepath, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["condition", "keyword", "weight", "notes"])

        count = 0
        all_conditions = list(condition_set.conditions)
        if condition_set.outcome:
            all_conditions.append(condition_set.outcome)

        for cond in all_conditions:
            for kw in cond.keywords:
                writer.writerow(
                    [
                        cond.name,
                        kw.pattern,
                        kw.weight,
                        kw.notes,
                    ]
                )
                count += 1

    return count


def export_keywords_json(condition_set: ConditionSet, filepath: str) -> None:
    """Export keyword dictionary from a ConditionSet to a JSON file.

    The JSON structure mirrors the import format exactly.

    Args:
        condition_set: The ConditionSet to export.
        filepath: Destination UTF-8 JSON file path.
    """
    conditions_data = []
    for cond in condition_set.conditions:
        cd = _condition_to_json_dict(cond)
        conditions_data.append(cd)

    result: dict = {
        "name": condition_set.name,
        "description": condition_set.description,
        "domain": condition_set.domain.value,
        "conditions": conditions_data,
    }

    if condition_set.outcome:
        result["outcome"] = _condition_to_json_dict(condition_set.outcome)

    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)


def _condition_to_json_dict(cond: ConditionDefinition) -> dict:
    """Convert a ConditionDefinition to a dict suitable for JSON export."""
    keywords_data = []
    for kw in cond.keywords:
        kwd: dict = {"keyword": kw.pattern, "weight": kw.weight, "scope": kw.scope}
        if kw.notes:
            kwd["notes"] = kw.notes
        keywords_data.append(kwd)

    cd: dict = {
        "name": cond.name,
        "display_name": cond.display_name,
        "keywords": keywords_data,
        "calibration_type": cond.calibration_type.value,
        "scoring_source": cond.scoring_source.value,
        "description": cond.description,
    }

    if cond.calibration_params:
        cd["calibration_params"] = {
            "threshold_full_in": cond.calibration_params.threshold_full_in,
            "threshold_full_out": cond.calibration_params.threshold_full_out,
            "crossover_point": cond.calibration_params.crossover_point,
            "direction": cond.calibration_params.direction,
        }

    return cd
