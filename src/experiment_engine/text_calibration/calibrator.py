"""Text calibration stage: keyword scores → fuzzy-set membership (0-1).

The TextCalibrationStage is a Pipeline Stage that takes raw keyword scores
and produces fuzzy-set membership values using one of three calibration
methods (direct, indirect, or Ragin's fuzzy direct method).
"""

from __future__ import annotations

import numpy as np

from experiment_engine.models import (
    CalibrationParams,
    CalibrationType,
    ConditionSet,
    FuzzySetData,
    InputData,
    OutputData,
)
from experiment_engine.pipeline import Stage
from experiment_engine.text_calibration.keyword_dict import (
    ChineseKeywordDictionary,
)


class TextCalibrationStage(Stage):
    """Pipeline stage: raw keyword scores → fuzzy-set membership scores.

    This stage:
    1. Accepts raw text corpus via InputData
    2. Runs keyword matching to get raw scores per condition
    3. Applies the specified calibration function to produce 0-1 fuzzy values
    4. Returns FuzzySetData

    Attributes:
        condition_set: The QCA condition definitions.
        method: Calibration method override (defaults to per-condition setting).
    """

    def __init__(
        self,
        condition_set: ConditionSet,
        method: CalibrationType | None = None,
        name: str = "text_calibration",
    ) -> None:
        super().__init__(name=name)
        self.condition_set = condition_set
        self._method_override = method
        self._dict = ChineseKeywordDictionary()

    def setup(self) -> None:
        all_conditions = list(self.condition_set.conditions)
        if self.condition_set.outcome:
            all_conditions.append(self.condition_set.outcome)
        self._dict.load_from_conditions(all_conditions)

    def process(self, data: InputData) -> OutputData:
        texts = self._extract_texts(data)
        raw_scores = self._dict.match_corpus(texts)

        # Calibrate each condition to fuzzy values
        all_conditions = list(self.condition_set.conditions)
        if self.condition_set.outcome:
            all_conditions.append(self.condition_set.outcome)

        n_cases, n_conds = raw_scores.shape
        membership = np.zeros((n_cases, n_conds), dtype=np.float64)

        for j, cond in enumerate(all_conditions):
            cal_type = self._method_override or cond.calibration_type
            params = cond.calibration_params
            if params is None:
                # Use default params if none set
                params = CalibrationParams(
                    threshold_full_in=0.80,
                    threshold_full_out=0.20,
                    crossover_point=0.50,
                )
            membership[:, j] = self._apply_calibration(
                raw_scores[:, j], cal_type, params
            )

        condition_names = self.condition_set.condition_names
        outcome_name = (
            self.condition_set.outcome.name if self.condition_set.outcome else ""
        )

        fuzzy_data = FuzzySetData(
            membership=membership,
            case_ids=data.index if data.index else None,
            condition_names=condition_names,
            outcome_name=outcome_name,
            texts=texts,
            metadata={
                "n_original": len(texts),
                "calibration_method": (
                    self._method_override.value
                    if self._method_override
                    else "per_condition"
                ),
            },
        )

        return OutputData(
            raw=data,
            processed=fuzzy_data,
            metadata={
                "stage": self.name,
                "n_cases": n_cases,
                "n_conditions": n_conds,
            },
        )

    @staticmethod
    def _extract_texts(data: InputData) -> list[str]:
        raw = data.data
        if isinstance(raw, np.ndarray):
            # 1D array of strings
            if raw.ndim == 1:
                return [str(x) for x in raw.tolist()]
            # 2D array — use first string-like column
            if raw.ndim == 2 and raw.shape[1] >= 1:
                return [str(x) for x in raw[:, 0].tolist()]
        if isinstance(raw, list):
            return [str(x) for x in raw]
        if isinstance(raw, str):
            return [raw]
        raise TypeError(f"Cannot extract texts from {type(raw)}")

    # ── Calibration functions ───────────────────────────────────────────

    @staticmethod
    def _apply_calibration(
        raw_scores: np.ndarray,
        cal_type: CalibrationType,
        params: CalibrationParams,
    ) -> np.ndarray:
        if cal_type == CalibrationType.DIRECT:
            return TextCalibrationStage.calibrate_direct(raw_scores, params)
        if cal_type == CalibrationType.INDIRECT:
            return TextCalibrationStage.calibrate_indirect(raw_scores, params)
        if cal_type == CalibrationType.FUZZY_DIRECT:
            return TextCalibrationStage.calibrate_ragin(raw_scores, params)
        raise ValueError(f"Unknown calibration type: {cal_type}")

    @staticmethod
    def calibrate_direct(
        raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        """Piecewise linear fuzzy membership.

        Membership = 0 if score <= full_out, 1 if score >= full_in,
        linear interpolation between crossover and thresholds.
        """
        out = np.zeros_like(raw_scores, dtype=np.float64)
        lo = params.threshold_full_out
        hi = params.threshold_full_in
        cross = params.crossover_point

        # Normalize raw scores to [0, 1] using quantile-based scaling first
        score_min = float(np.min(raw_scores))
        score_max = float(np.max(raw_scores))
        if score_max > score_min:
            normalized = (raw_scores - score_min) / (score_max - score_min)
        else:
            normalized = np.full_like(raw_scores, 0.5)

        for i in range(len(normalized)):
            s = normalized[i]
            if s <= lo:
                out[i] = 0.0
            elif s >= hi:
                out[i] = 1.0
            elif s <= cross:
                # Linear: 0 → 0.5 between full_out and crossover
                out[i] = 0.5 * (s - lo) / (cross - lo)
            else:
                # Linear: 0.5 → 1.0 between crossover and full_in
                out[i] = 0.5 + 0.5 * (s - cross) / (hi - cross)

        if params.direction == "descending":
            out = 1.0 - out

        return out

    @staticmethod
    def calibrate_indirect(
        raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        """Log-odds based indirect calibration.

        Rescales raw scores to [0, 1] first, then applies a logistic
        transformation to produce fuzzy membership values.
        """
        score_min = float(np.min(raw_scores))
        score_max = float(np.max(raw_scores))
        if score_max > score_min:
            normalized = (raw_scores - score_min) / (score_max - score_min)
        else:
            normalized = np.full_like(raw_scores, 0.5)

        # Apply logistic: map [0,1] through log-odds centered at crossover
        cross = params.crossover_point
        # Scale factor controls steepness; wider → smoother transition
        k = 10.0  # steepness factor

        result = np.zeros_like(normalized, dtype=np.float64)
        for i in range(len(normalized)):
            s = normalized[i]
            if s <= 0.0:
                result[i] = 0.0
            elif s >= 1.0:
                result[i] = 1.0
            else:
                # Log-odds transform centered at crossover
                log_odds = np.log(s / (1.0 - s)) if s > 0 and s < 1 else 0.0
                cross_log_odds = (
                    np.log(cross / (1.0 - cross)) if cross > 0 and cross < 1 else 0.0
                )
                scaled = 1.0 / (1.0 + np.exp(-k * (log_odds - cross_log_odds)))
                result[i] = float(scaled)

        if params.direction == "descending":
            result = 1.0 - result

        return result

    @staticmethod
    def calibrate_ragin(
        raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        """Ragin's fuzzy direct method: log-odds of raw scores relative to anchors.

        Uses the three qualitative anchors (full non-membership threshold,
        crossover point, full membership threshold) directly as log-odds
        calibration targets.
        """
        result = np.zeros_like(raw_scores, dtype=np.float64)
        lo = params.threshold_full_out
        hi = params.threshold_full_in
        cross = params.crossover_point

        # Compute intermediate log-odds (deviation from crossover)
        # Scale so that lo→0, cross→0.5, hi→1
        for i in range(len(raw_scores)):
            s = raw_scores[i]
            if s <= lo:
                result[i] = 0.05  # near but not quite zero (fuzzy set floor)
            elif s >= hi:
                result[i] = 0.95  # near but not quite one (fuzzy set ceiling)
            else:
                # Linear interpolation between the three anchors
                if s <= cross:
                    result[i] = 0.5 * (s - lo) / (cross - lo)
                else:
                    result[i] = 0.5 + 0.5 * (s - cross) / (hi - cross)

        if params.direction == "descending":
            result = 1.0 - result

        return result
