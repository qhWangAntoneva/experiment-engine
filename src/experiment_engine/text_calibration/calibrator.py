"""Text calibration stage: keyword scores → fuzzy-set membership (0-1).

The TextCalibrationStage is a Pipeline Stage that takes raw keyword scores
and produces fuzzy-set membership values using one of three calibration
methods (direct, indirect, or Ragin's fuzzy direct method).

Calibration method dispatch uses the strategy pattern (HACK-6 resolved).
New methods can be added by registering a CalibrationStrategy without
modifying TextCalibrationStage.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from experiment_engine.models import (
    CalibrationMethod,
    CalibrationParams,
    ConditionDefinition,
    ConditionSet,
    InputData,
    MembershipData,
    OutputData,
    QCAVariant,
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
from experiment_engine.text_calibration.strategies import (
    CalibrationStrategyRegistry,
    DirectCalibration,
    IndirectCalibration,
    RaginCalibration,
)


class TextCalibrationStage(Stage):
    """Pipeline stage: raw keyword scores → fuzzy-set membership scores.

    This stage:
    1. Accepts raw text corpus via InputData
    2. Runs keyword matching to get raw scores per condition
    3. Applies the specified calibration function to produce 0-1 fuzzy values
    4. Returns MembershipData

    Attributes:
        condition_set: The QCA condition definitions.
        method: Calibration method override (defaults to per-condition setting).
    """

    def __init__(
        self,
        condition_set: ConditionSet,
        method: CalibrationMethod | None = None,
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

    # ── Pre-computation helpers (FIXME-2, FIXME-4) ────────────────────────

    def _precompute_kw_context(
        self, texts: list[str]
    ) -> tuple[np.ndarray | None, dict[int, int]]:
        """Pre-compute keyword matrix and col_idx -> kw_col_idx mapping.

        FIXME-2: Builds the mapping from global condition index to keyword
        matrix column, so that PROTOTYPE conditions interleaved with
        KEYWORD/HYBRID conditions do not cause column index offset.

        FIXME-4: Calls match_corpus() once and caches the result matrix,
        avoiding O(n_conditions) redundant recomputation.
        """
        all_conditions = self._all_conditions()

        kw_conditions = [
            c
            for c in all_conditions
            if c.scoring_source in (ScoringSource.KEYWORD, ScoringSource.HYBRID)
        ]
        kw_matrix = self._dict.match_corpus(texts) if kw_conditions else None

        col_to_kw: dict[int, int] = {}
        kw_idx = 0
        for j, cond in enumerate(all_conditions):
            if cond.scoring_source in (ScoringSource.KEYWORD, ScoringSource.HYBRID):
                col_to_kw[j] = kw_idx
                kw_idx += 1

        return kw_matrix, col_to_kw

    def _process_core(
        self,
        texts: list[str],
        kw_matrix: np.ndarray | None,
        col_to_kw: dict[int, int],
        outcome_provider: Callable[[int], np.ndarray | None],
    ) -> np.ndarray:
        """Core membership computation shared by process/process_with_outcome.

        FIXME-20: Extracted common logic from process() and
        process_with_outcome() to eliminate ~60 lines of duplicated code.

        Args:
            texts: List of text strings.
            kw_matrix: Pre-computed keyword match matrix (or None).
            col_to_kw: Mapping from global col_idx to keyword matrix column.
            outcome_provider: Called as outcome_provider(col_idx) for each
                column. Returns a membership vector for the outcome column,
                or None if this column is a regular condition.

        Returns:
            membership matrix of shape (n_texts, n_conditions).
        """
        all_conditions = self._all_conditions()
        n_cases = len(texts)
        n_conds = len(all_conditions)
        membership = np.zeros((n_cases, n_conds), dtype=np.float64)

        for j, cond in enumerate(all_conditions):
            outcome_vals = outcome_provider(j)
            if outcome_vals is not None:
                membership[:, j] = outcome_vals.astype(np.float64)
            else:
                raw_scores = self._compute_raw_scores(
                    texts, cond, j, kw_matrix, col_to_kw
                )
                cal_type = self._method_override or cond.calibration_type

                # csQCA: force crisp-set calibration regardless of per-condition settings
                if self.condition_set.qca_variant == QCAVariant.CSQCA:
                    cal_type = CalibrationMethod.CRISP_SET

                params = cond.calibration_params or CalibrationParams(
                    threshold_full_in=0.80,
                    threshold_full_out=0.20,
                    crossover_point=0.50,
                )
                membership[:, j] = self._apply_calibration(raw_scores, cal_type, params)

        return membership

    # ── Main processing methods ───────────────────────────────────────────

    def process(self, data: InputData) -> OutputData:
        texts = self._extract_texts(data)
        kw_matrix, col_to_kw = self._precompute_kw_context(texts)

        n_conds = len(self._all_conditions())
        membership = self._process_core(
            texts,
            kw_matrix,
            col_to_kw,
            outcome_provider=lambda _j: None,
        )

        n_cases = len(texts)
        condition_names = self.condition_set.condition_names
        outcome_name = (
            self.condition_set.outcome.name if self.condition_set.outcome else ""
        )

        fuzzy_data = MembershipData(
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
        kw_matrix: np.ndarray | None = None,
        col_to_kw: dict[int, int] | None = None,
    ) -> np.ndarray:
        """Compute raw scores for a condition based on its scoring source.

        Args:
            texts: List of text strings.
            cond: The condition definition.
            col_idx: Global column index in all_conditions.
            kw_matrix: Pre-computed keyword match matrix (FIXME-4).
            col_to_kw: Mapping from global col_idx to keyword matrix column
                (FIXME-2). When provided, fixes column index offset when
                PROTOTYPE conditions are interleaved with KEYWORD/HYBRID.
        """
        # DEPRECATED: PROTOTYPE scoring source is deprecated.
        # Prototype similarity computation is now handled at a higher level
        # (see pyodide_handlers.py unified calibrate handler — prototype texts
        # are calibrated through the same keyword pipeline as raw texts).
        # This branch is retained for backward compatibility and will be
        # removed when PROTOTYPE support is dropped.
        if cond.scoring_source == ScoringSource.PROTOTYPE:
            if not cond.prototypes:
                return np.zeros(len(texts), dtype=np.float64)
            proto_map = {cond.name: cond.prototypes}
            matrix = self._prototype_engine.compute_similarities(texts, proto_map)
            return matrix[:, 0]

        # KEYWORD and HYBRID: determine the keyword matrix column.
        # Use the corrected mapping when available (FIXME-2), otherwise fall
        # back to col_idx (legacy behaviour, only correct when all conditions
        # are KEYWORD/HYBRID).
        kw_col = col_to_kw.get(col_idx, 0) if col_to_kw is not None else col_idx

        if kw_matrix is not None:
            if kw_matrix.shape[1] > kw_col:
                kw_scores = kw_matrix[:, kw_col]
            else:
                kw_scores = kw_matrix[:, 0]
        else:
            # Fallback: compute on the fly (backward compat for callers that
            # do not pre-compute).
            kw_scores_full = self._dict.match_corpus(texts)
            if kw_scores_full.shape[1] > kw_col:
                kw_scores = kw_scores_full[:, kw_col]
            else:
                kw_scores = kw_scores_full[:, 0]

        if cond.scoring_source == ScoringSource.KEYWORD:
            return kw_scores.astype(np.float64)

        # HYBRID — blend keyword score with prototype similarity
        proto_map = {cond.name: cond.prototypes} if cond.prototypes else {}
        if proto_map:
            proto_matrix = self._prototype_engine.compute_similarities(texts, proto_map)
            proto_col = proto_matrix[:, 0]
        else:
            proto_col = np.zeros(len(texts), dtype=np.float64)

        return (
            cond.hybrid_keyword_weight * kw_scores
            + cond.hybrid_prototype_weight * proto_col
        )

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
            OutputData with MembershipData where the last column is the outcome.
        """
        texts = self._extract_texts(data)
        kw_matrix, col_to_kw = self._precompute_kw_context(texts)

        n_conds = len(self._all_conditions())
        has_outcome = self.condition_set.outcome is not None

        membership = self._process_core(
            texts,
            kw_matrix,
            col_to_kw,
            outcome_provider=(
                lambda j: outcome_vector if (has_outcome and j == n_conds - 1) else None
            ),
        )

        n_cases = len(texts)
        condition_names = self.condition_set.condition_names
        outcome_name = (
            self.condition_set.outcome.name if self.condition_set.outcome else ""
        )

        fuzzy_data = MembershipData(
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

    def calibrate_one(self, sample: TrainingSample) -> MembershipData:
        """Calibrate a single training sample.

        Used by the Pyodide worker to process samples one at a time.

        Args:
            sample: A TrainingSample with text and optional labeled_scores.

        Returns:
            MembershipData with membership shape (1, n_conditions + 1).
        """
        texts = [sample.text]
        kw_matrix, col_to_kw = self._precompute_kw_context(texts)
        all_conditions = self._all_conditions()
        n_conds = len(all_conditions)
        membership = np.zeros((1, n_conds), dtype=np.float64)

        for j, cond in enumerate(all_conditions):
            raw_scores = self._compute_raw_scores(texts, cond, j, kw_matrix, col_to_kw)
            cal_type = self._method_override or cond.calibration_type

            # csQCA: force crisp-set calibration regardless of per-condition settings
            if self.condition_set.qca_variant == QCAVariant.CSQCA:
                cal_type = CalibrationMethod.CRISP_SET

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

        return MembershipData(
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

    # Class-level strategy registry. Pre-populated with the four default
    # strategies. External code can register custom strategies via
    # TextCalibrationStage._registry.register(CalibrationMethod.DIRECT, my_impl).
    _registry = CalibrationStrategyRegistry()

    @staticmethod
    def _apply_calibration(
        raw_scores: np.ndarray,
        cal_type: CalibrationMethod,
        params: CalibrationParams,
    ) -> np.ndarray:
        """Dispatch to the appropriate calibration strategy via registry.

        Uses the strategy pattern (HACK-6 resolved) instead of hardcoded
        if/elif branches. New calibration methods can be added by registering
        a CalibrationStrategy instance without modifying this class.
        """
        strategy = TextCalibrationStage._registry.get(cal_type)
        return strategy.calibrate(raw_scores, params)

    @staticmethod
    def calibrate_direct(
        raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        """Piecewise linear fuzzy membership (delegates to DirectCalibration strategy)."""
        return DirectCalibration().calibrate(raw_scores, params)

    @staticmethod
    def calibrate_indirect(
        raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        """Log-odds based indirect calibration (delegates to IndirectCalibration strategy)."""
        return IndirectCalibration().calibrate(raw_scores, params)

    @staticmethod
    def calibrate_fuzzy_direct(
        raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        """Ragin's fuzzy direct method (delegates to RaginCalibration strategy)."""
        return RaginCalibration().calibrate(raw_scores, params)
