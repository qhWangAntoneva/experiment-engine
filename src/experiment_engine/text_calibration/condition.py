"""Condition set I/O helpers — YAML serialization for QCA condition definitions.

The Pydantic models (ConditionDefinition, ConditionSet) are defined in
experiment_engine.models. This module provides convenience builders and
YAML file serialization.
"""

from __future__ import annotations

import yaml

from experiment_engine.models import (
    CalibrationParams,
    CalibrationType,
    ConceptPrototype,
    ConditionDefinition,
    ConditionSet,
    ScoringSource,
    TextDomain,
)


class ConditionDefinitionBuilder:
    """Fluent builder for :class:`ConditionDefinition`."""

    def __init__(
        self,
        name: str,
        display_name: str = "",
        domain: TextDomain = TextDomain.DISSATISFACTION,
    ) -> None:
        self._name = name
        self._display_name = display_name or name
        self._domain = domain
        self._keywords: list[dict[str, object]] = []
        self._prototypes: list[dict[str, object]] = []
        self._calibration_type = CalibrationType.DIRECT
        self._calibration_params: CalibrationParams | None = None
        self._description = ""
        self._scoring_source = ScoringSource.PROTOTYPE
        self._hybrid_kw_weight = 0.5
        self._hybrid_proto_weight = 0.5

    def add_keyword(
        self, pattern: str, weight: float = 1.0, scope: str = "bigram"
    ) -> ConditionDefinitionBuilder:
        self._keywords.append({"pattern": pattern, "weight": weight, "scope": scope})
        return self

    def add_prototype(
        self, text: str, is_member: int = 1, weight: float = 1.0
    ) -> ConditionDefinitionBuilder:
        self._prototypes.append(
            {
                "prototype_text": text,
                "is_member": is_member,
                "weight": weight,
            }
        )
        return self

    def scoring(
        self,
        source: str = "prototype",
        hybrid_kw_weight: float = 0.5,
        hybrid_proto_weight: float = 0.5,
    ) -> ConditionDefinitionBuilder:
        self._scoring_source = ScoringSource(source)
        self._hybrid_kw_weight = hybrid_kw_weight
        self._hybrid_proto_weight = hybrid_proto_weight
        return self

    def calibration(
        self,
        cal_type: CalibrationType,
        full_in: float = 0.80,
        full_out: float = 0.20,
        crossover: float = 0.50,
        direction: str = "ascending",
    ) -> ConditionDefinitionBuilder:
        self._calibration_type = cal_type
        self._calibration_params = CalibrationParams(
            threshold_full_in=full_in,
            threshold_full_out=full_out,
            crossover_point=crossover,
            direction=direction,
        )
        return self

    def description(self, text: str) -> ConditionDefinitionBuilder:
        self._description = text
        return self

    def build(self) -> ConditionDefinition:
        return ConditionDefinition(
            name=self._name,
            display_name=self._display_name,
            domain=self._domain,
            calibration_type=self._calibration_type,
            calibration_params=self._calibration_params,
            description=self._description,
            scoring_source=self._scoring_source,
            prototypes=[ConceptPrototype(**p) for p in self._prototypes],
        )


class ConditionSetBuilder:
    """Fluent builder for :class:`ConditionSet`."""

    def __init__(
        self, name: str = "qca_model", domain: TextDomain = TextDomain.DISSATISFACTION
    ) -> None:
        self._name = name
        self._description = ""
        self._domain = domain
        self._conditions: list[ConditionDefinition] = []
        self._outcome: ConditionDefinition | None = None

    def add_condition(self, cond: ConditionDefinition) -> ConditionSetBuilder:
        self._conditions.append(cond)
        return self

    def set_outcome(self, outcome: ConditionDefinition) -> ConditionSetBuilder:
        self._outcome = outcome
        return self

    def description(self, text: str) -> ConditionSetBuilder:
        self._description = text
        return self

    def build(self) -> ConditionSet:
        return ConditionSet(
            name=self._name,
            description=self._description,
            conditions=self._conditions,
            outcome=self._outcome,
            domain=self._domain,
        )


# ── YAML serialization ──────────────────────────────────────────────────


def save_condition_set(condition_set: ConditionSet, path: str) -> None:
    """Save a ConditionSet to a YAML file."""
    data = _condition_set_to_dict(condition_set)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(
            data, fh, allow_unicode=True, sort_keys=False, default_flow_style=False
        )


def load_condition_set(path: str) -> ConditionSet:
    """Load a ConditionSet from a YAML file."""
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return _condition_set_from_dict(data)


def _condition_set_to_dict(cs: ConditionSet) -> dict:
    return {
        "name": cs.name,
        "description": cs.description,
        "domain": cs.domain.value,
        "scoring_source": cs.scoring_source.value,
        "conditions": [_condition_to_dict(c) for c in cs.conditions],
        "outcome": _condition_to_dict(cs.outcome) if cs.outcome else None,
    }


def _kw_to_dict(k) -> dict:
    d = {"pattern": k.pattern, "weight": k.weight, "scope": k.scope}
    if k.notes:
        d["notes"] = k.notes
    return d


def _condition_to_dict(cond: ConditionDefinition) -> dict:
    d: dict = {
        "name": cond.name,
        "display_name": cond.display_name,
        "domain": cond.domain.value,
        "calibration_type": cond.calibration_type.value,
        "description": cond.description,
        "scoring_source": cond.scoring_source.value,
        "hybrid_keyword_weight": getattr(cond, "hybrid_keyword_weight", 0.5),
        "hybrid_prototype_weight": getattr(cond, "hybrid_prototype_weight", 0.5),
        "keywords": [_kw_to_dict(k) for k in getattr(cond, "keywords", [])],
        "prototypes": [
            {
                "prototype_text": p.prototype_text,
                "is_member": p.is_member,
                "weight": p.weight,
            }
            for p in cond.prototypes
        ],
    }
    if cond.calibration_params:
        d["calibration_params"] = {
            "threshold_full_in": cond.calibration_params.threshold_full_in,
            "threshold_full_out": cond.calibration_params.threshold_full_out,
            "crossover_point": cond.calibration_params.crossover_point,
            "direction": cond.calibration_params.direction,
        }
    return d


def _condition_set_from_dict(data: dict) -> ConditionSet:
    domain = TextDomain(data.get("domain", "dissatisfaction"))
    conditions = [_condition_from_dict(c, domain) for c in data.get("conditions", [])]
    outcome = (
        _condition_from_dict(data["outcome"], domain) if data.get("outcome") else None
    )
    return ConditionSet(
        name=data.get("name", "qca_model"),
        description=data.get("description", ""),
        domain=domain,
        conditions=conditions,
        outcome=outcome,
        scoring_source=ScoringSource(data.get("scoring_source", "prototype")),
    )


def _condition_from_dict(data: dict, domain: TextDomain) -> ConditionDefinition:
    cal_params = None
    if data.get("calibration_params"):
        cp = data["calibration_params"]
        cal_params = CalibrationParams(
            threshold_full_in=cp["threshold_full_in"],
            threshold_full_out=cp["threshold_full_out"],
            crossover_point=cp["crossover_point"],
            direction=cp.get("direction", "ascending"),
        )

    return ConditionDefinition(
        name=data["name"],
        display_name=data.get("display_name", data["name"]),
        domain=domain,
        calibration_type=CalibrationType(data.get("calibration_type", "direct")),
        calibration_params=cal_params,
        description=data.get("description", ""),
        scoring_source=ScoringSource(data.get("scoring_source", "prototype")),
        prototypes=[ConceptPrototype(**p) for p in data.get("prototypes", [])],
    )
