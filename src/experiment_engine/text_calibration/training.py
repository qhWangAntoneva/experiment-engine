"""Training engine for fitting calibration parameters from labeled samples.

Given concept prototypes (text + human-labeled fuzzy-set membership scores),
the TrainingEngine learns optimal calibration thresholds for each condition.

.. note::
    Keyword-based scoring was removed in Phase 5. Prototype-based training
    (via BERT embeddings + CosineSimilarityEngine) is not yet implemented.
    The engine is retained as a structural placeholder.
"""

from __future__ import annotations

import warnings

import numpy as np

from experiment_engine.models import (
    CalibrationParams,
    ConditionDefinition,
    ConditionSet,
    TrainingDataset,
)


class TrainingEngine:
    """Fit calibration parameters from labeled training samples.

    For each condition, the engine:
    1. Computes raw scores for all training texts
    2. Compares raw score distribution with labeled fuzzy-set scores
    3. Estimates optimal thresholds (full_out, crossover, full_in) via
       quantile matching

    .. note::
        Prototype-based training (BERT embedding + CosineSimilarityEngine)
        is not yet implemented. This engine currently returns raw scores of
        0.0 for all text-condition pairs.

    Usage:
        engine = TrainingEngine()
        updated_conditions = engine.fit(dataset, condition_set)
    """

    def __init__(self) -> None:
        self._last_fit_metrics: dict[str, dict[str, float]] = {}

    @property
    def fit_metrics(self) -> dict[str, dict[str, float]]:
        """Per-condition fit quality metrics from the last :meth:`fit` call."""
        return dict(self._last_fit_metrics)

    def fit(
        self, dataset: TrainingDataset, condition_set: ConditionSet
    ) -> ConditionSet:
        """Fit calibration parameters for all conditions.

        Args:
            dataset: Labeled training samples with text and fuzzy-set scores.
            condition_set: Initial condition definitions to fit against.

        Returns:
            A new ConditionSet with updated calibration_params on each condition.
        """
        if not dataset.samples:
            raise ValueError("Training dataset has no samples")

        all_conditions = list(condition_set.conditions)
        if condition_set.outcome:
            all_conditions.append(condition_set.outcome)

        # Compute raw scores for all samples
        texts = [s.text for s in dataset.samples]
        raw_scores_matrix = self._compute_raw_scores(texts, all_conditions)

        updated_conditions: list[ConditionDefinition] = []
        self._last_fit_metrics = {}

        for j, cond in enumerate(all_conditions):
            cond_name = cond.name
            # Collect labeled scores for this condition
            labeled = np.array(
                [s.labeled_scores.get(cond_name, 0.5) for s in dataset.samples],
                dtype=np.float64,
            )
            raw = raw_scores_matrix[:, j]

            # Estimate thresholds via quantile matching
            full_out, cross, full_in = self.estimate_thresholds_quantile(raw, labeled)

            # Compute fit quality (correlation between calibrated and labeled)
            calibrated = self._apply_thresholds(raw, full_out, cross, full_in)
            corr = (
                float(np.corrcoef(calibrated, labeled)[0, 1])
                if len(labeled) > 1
                else 0.0
            )

            self._last_fit_metrics[cond_name] = {
                "pearson_r": corr,
                "mae": float(np.mean(np.abs(calibrated - labeled))),
                "threshold_full_out": full_out,
                "crossover_point": cross,
                "threshold_full_in": full_in,
            }

            updated_cond = ConditionDefinition(
                name=cond.name,
                display_name=cond.display_name,
                domain=cond.domain,
                calibration_type=cond.calibration_type,
                calibration_params=CalibrationParams(
                    threshold_full_in=full_in,
                    threshold_full_out=full_out,
                    crossover_point=cross,
                    direction=cond.calibration_params.direction
                    if cond.calibration_params
                    else "ascending",
                ),
                description=cond.description,
            )
            updated_conditions.append(updated_cond)

        new_outcome = None
        if condition_set.outcome and updated_conditions:
            new_outcome = updated_conditions[-1]
            updated_conditions = updated_conditions[:-1]

        return ConditionSet(
            name=condition_set.name,
            description=condition_set.description,
            domain=condition_set.domain,
            conditions=updated_conditions,
            outcome=new_outcome,
        )

    @staticmethod
    def _compute_raw_scores(
        texts: list[str], conditions: list[ConditionDefinition]
    ) -> np.ndarray:
        """Compute raw scores matrix — prototype-based training TBD.

        Keyword scoring was removed in Phase 5.  Prototype-based training
        (via BERT embeddings + CosineSimilarityEngine) is not yet
        implemented.  Returns a zero matrix for now.
        """
        n = len(texts)
        m = len(conditions)
        warnings.warn(
            "TrainingEngine._compute_raw_scores: prototype-based training "
            "not yet implemented — returning zero scores",
            FutureWarning,
            stacklevel=2,
        )
        return np.zeros((n, m), dtype=np.float64)

    @staticmethod
    def estimate_thresholds_quantile(
        raw_scores: np.ndarray, labeled_scores: np.ndarray
    ) -> tuple[float, float, float]:
        """Estimate calibration thresholds via quantile matching.

        Maps the distribution of raw scores to the distribution of labeled scores
        by finding raw-score values that correspond to the 5th, 50th, and 95th
        percentiles of labeled scores.

        Args:
            raw_scores: 1D array of raw keyword match scores.
            labeled_scores: 1D array of human-labeled fuzzy membership (0-1).

        Returns:
            Tuple of (threshold_full_out, crossover_point, threshold_full_in).
            All values are in the normalized [0,1] range.
        """
        if len(raw_scores) == 0:
            return (0.20, 0.50, 0.80)

        # Normalize raw scores to [0, 1]
        raw_min = float(np.min(raw_scores))
        raw_max = float(np.max(raw_scores))
        if raw_max > raw_min:
            raw_norm = (raw_scores - raw_min) / (raw_max - raw_min)
        else:
            raw_norm = np.full_like(raw_scores, 0.5)

        # Find raw_norm values at labeled score percentiles
        # Low labeled scores → full_out, median → crossover, high → full_in
        sorted_idx = np.argsort(labeled_scores)
        n = len(labeled_scores)

        lo_idx = max(0, int(n * 0.10))  # 10th percentile → full_out
        mid_idx = n // 2  # median → crossover
        hi_idx = min(n - 1, int(n * 0.90))  # 90th percentile → full_in

        full_out = float(np.clip(raw_norm[sorted_idx[lo_idx]], 0.05, 0.40))
        crossover = float(np.clip(raw_norm[sorted_idx[mid_idx]], 0.25, 0.75))
        full_in = float(np.clip(raw_norm[sorted_idx[hi_idx]], 0.60, 0.95))

        # Ensure ordering: full_out < crossover < full_in
        full_out = min(full_out, crossover - 0.05)
        full_in = max(full_in, crossover + 0.05)

        return (full_out, crossover, full_in)

    @staticmethod
    def _apply_thresholds(
        raw_scores: np.ndarray,
        full_out: float,
        crossover: float,
        full_in: float,
    ) -> np.ndarray:
        """Apply direct calibration with given thresholds."""
        raw_min = float(np.min(raw_scores))
        raw_max = float(np.max(raw_scores))
        if raw_max > raw_min:
            norm = (raw_scores - raw_min) / (raw_max - raw_min)
        else:
            norm = np.full_like(raw_scores, 0.5)

        result = np.zeros_like(norm, dtype=np.float64)
        for i in range(len(norm)):
            s = norm[i]
            if s <= full_out:
                result[i] = 0.0
            elif s >= full_in:
                result[i] = 1.0
            elif s <= crossover:
                result[i] = 0.5 * (s - full_out) / (crossover - full_out)
            else:
                result[i] = 0.5 + 0.5 * (s - crossover) / (full_in - crossover)
        return result
