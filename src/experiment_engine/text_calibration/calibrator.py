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
    ConditionDefinition,
    ConditionSet,
    FuzzySetData,
    InputData,
    OutputData,
    ScoringSource,
    TrainingSample,
)
from experiment_engine.pipeline import Stage
from experiment_engine.text_calibration.keyword_dict import (
    ChineseKeywordDictionary,
)
from experiment_engine.text_calibration.prototype_similarity import (
    PrototypeSimilarityEngine,
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
        # Build keyword dictionary for keyword/hybrid conditions only
        kw_conditions = [
            c
            for c in self._all_conditions()
            if c.scoring_source in (ScoringSource.KEYWORD, ScoringSource.HYBRID)
        ]
        if kw_conditions:
            self._dict.load_from_conditions(kw_conditions)
        self._prototype_engine = PrototypeSimilarityEngine()

    def _all_conditions(self) -> list[ConditionDefinition]:
        conds = list(self.condition_set.conditions)
        if self.condition_set.outcome:
            conds.append(self.condition_set.outcome)
        return conds

    def process(self, data: InputData) -> OutputData:
        texts = self._extract_texts(data)
        all_conditions = self._all_conditions()

        n_cases = len(texts)
        n_conds = len(all_conditions)
        membership = np.zeros((n_cases, n_conds), dtype=np.float64)

        for j, cond in enumerate(all_conditions):
            raw_scores = self._compute_raw_scores(texts, cond, j, all_conditions)

            cal_type = self._method_override or cond.calibration_type
            params = cond.calibration_params or CalibrationParams(
                threshold_full_in=0.80,
                threshold_full_out=0.20,
                crossover_point=0.50,
            )
            membership[:, j] = self._apply_calibration(raw_scores, cal_type, params)

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

    def _compute_raw_scores(
        self,
        texts: list[str],
        cond: ConditionDefinition,
        col_idx: int,
        all_conditions: list[ConditionDefinition],
    ) -> np.ndarray:
        """Compute raw scores for a condition based on its scoring source."""
        if cond.scoring_source == ScoringSource.PROTOTYPE:
            if not cond.prototypes:
                # No prototypes defined — return zeros (outcome handled separately)
                return np.zeros(len(texts), dtype=np.float64)
            proto_map = {cond.name: cond.prototypes}
            matrix = self._prototype_engine.compute_similarities(texts, proto_map)
            return matrix[:, 0]
        if cond.scoring_source == ScoringSource.HYBRID:
            kw_scores = self._dict.match_corpus(texts)
            # Find this condition's column in the keyword dict output
            kw_conds = [
                c
                for c in all_conditions
                if c.scoring_source in (ScoringSource.KEYWORD, ScoringSource.HYBRID)
            ]
            kw_idx = kw_conds.index(cond) if cond in kw_conds else col_idx
            kw_col = (
                kw_scores[:, kw_idx] if kw_scores.shape[1] > kw_idx else kw_scores[:, 0]
            )

            proto_map = {cond.name: cond.prototypes} if cond.prototypes else {}
            if proto_map:
                proto_matrix = self._prototype_engine.compute_similarities(
                    texts, proto_map
                )
                proto_col = proto_matrix[:, 0]
            else:
                proto_col = np.zeros(len(texts), dtype=np.float64)

            return (
                cond.hybrid_keyword_weight * kw_col
                + cond.hybrid_prototype_weight * proto_col
            )
        # KEYWORD — use existing keyword dictionary
        raw_scores = self._dict.match_corpus(texts)
        return raw_scores[:, col_idx]

    def process_with_outcome(
        self, data: InputData, outcome_vector: np.ndarray
    ) -> OutputData:
        """Process conditions normally but use pre-supplied outcome values.

        The outcome column is set from outcome_vector (crisp 0/1) instead
        of being computed from keywords or prototypes.

        Args:
            data: InputData with texts.
            outcome_vector: 1D array of binary outcomes (0 or 1).

        Returns:
            OutputData with FuzzySetData where the last column is the outcome.
        """
        texts = self._extract_texts(data)
        all_conditions = self._all_conditions()
        n_cases = len(texts)
        n_conds = len(all_conditions)
        membership = np.zeros((n_cases, n_conds), dtype=np.float64)

        for j, cond in enumerate(all_conditions):
            # Check if this is the outcome column
            is_outcome = (
                self.condition_set.outcome is not None
                and cond.name == self.condition_set.outcome.name
            )
            if is_outcome:
                membership[:, j] = outcome_vector.astype(np.float64)
            else:
                raw_scores = self._compute_raw_scores(texts, cond, j, all_conditions)
                cal_type = self._method_override or cond.calibration_type
                params = cond.calibration_params or CalibrationParams(
                    threshold_full_in=0.80,
                    threshold_full_out=0.20,
                    crossover_point=0.50,
                )
                membership[:, j] = self._apply_calibration(raw_scores, cal_type, params)

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
            metadata={"n_original": len(texts)},
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

    def calibrate_one(self, sample: TrainingSample) -> FuzzySetData:
        """Calibrate a single training sample.

        Used by the Pyodide worker to process samples one at a time.

        Args:
            sample: A TrainingSample with text and optional labeled_scores.

        Returns:
            FuzzySetData with membership shape (1, n_conditions + 1).
        """
        texts = [sample.text]
        all_conditions = self._all_conditions()
        n_conds = len(all_conditions)
        membership = np.zeros((1, n_conds), dtype=np.float64)

        for j, cond in enumerate(all_conditions):
            raw_scores = self._compute_raw_scores(texts, cond, j, all_conditions)
            cal_type = self._method_override or cond.calibration_type
            params = cond.calibration_params or CalibrationParams(
                threshold_full_in=0.80,
                threshold_full_out=0.20,
                crossover_point=0.50,
            )
            membership[0, j] = self._apply_calibration(raw_scores, cal_type, params)[0]

        condition_names = self.condition_set.condition_names
        outcome_name = (
            self.condition_set.outcome.name if self.condition_set.outcome else ""
        )

        return FuzzySetData(
            membership=membership,
            case_ids=[sample.text_id],
            condition_names=condition_names,
            outcome_name=outcome_name,
            texts=texts,
            metadata={},
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
        if cal_type == CalibrationType.PASSTHROUGH:
            return raw_scores.astype(np.float64)
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
