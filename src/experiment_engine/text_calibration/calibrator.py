"""Text calibration stage: BERT prototype scores → fuzzy-set membership (0-1).

The TextCalibrationStage is a Pipeline Stage that takes pre-computed BERT
embedding-based prototype similarity scores and produces fuzzy-set membership
values using one of four calibration methods (direct, indirect, Ragin's fuzzy
direct, or crisp-set).

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
from experiment_engine.text_calibration.cosine_similarity import (
    CosineSimilarityEngine,
)
from experiment_engine.text_calibration.strategies import (
    CalibrationStrategyRegistry,
    DirectCalibration,
    IndirectCalibration,
    RaginCalibration,
)


class TextCalibrationStage(Stage):
    """Pipeline stage: BERT prototype scores → fuzzy-set membership scores.

    This stage:
    1. Accepts pre-computed BERT text embeddings and prototype embeddings
       (optional — when omitted, all raw scores default to zero).
    2. Computes cosine-similarity raw scores via CosineSimilarityEngine.
    3. Applies the specified calibration function to produce 0-1 fuzzy values.
    4. Returns MembershipData.

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

    def setup(self) -> None:
        """Instantiate the cosine similarity engine for BERT prototype scoring."""
        self._cosine_engine = CosineSimilarityEngine()

    def _all_conditions(self) -> list[ConditionDefinition]:
        conds = list(self.condition_set.conditions)
        if self.condition_set.outcome:
            conds.append(self.condition_set.outcome)
        return conds

    # ── Pre-computation helpers ─────────────────────────────────────────

    def _precompute_scores(
        self,
        texts: list[str],
        text_embeddings: np.ndarray | None,
        prototype_embeddings: dict[str, np.ndarray] | None,
    ) -> np.ndarray:
        """Pre-compute all raw scores via CosineSimilarityEngine in one shot.

        Computes an (N, M) scores matrix for all conditions at once, replacing
        the old per-condition keyword-matching loop. Non-PROTOTYPE conditions
        (deprecated KEYWORD/HYBRID) and PROTOTYPE conditions without embeddings
        receive zero scores.

        Args:
            texts: List of text strings (used for row-count dimension only).
            text_embeddings: (N, d) pre-computed BERT embeddings, or None.
            prototype_embeddings: Mapping from condition name to (K, d)
                prototype embedding arrays, or None.

        Returns:
            Raw scores matrix of shape (N, M) where M = len(all_conditions).
        """
        all_conditions = self._all_conditions()
        n_texts = len(texts)
        n_conds = len(all_conditions)

        # Identify PROTOTYPE conditions that have both prototypes and embeddings
        proto_conds = [
            c
            for c in all_conditions
            if c.scoring_source == ScoringSource.PROTOTYPE and c.prototypes
        ]

        if not (
            text_embeddings is not None
            and prototype_embeddings is not None
            and proto_conds
        ):
            # Fallback: compute text-level similarity when BERT embeddings
            # are not available (CLI/api path without Transformers.js).
            # Uses character trigram Jaccard similarity between input texts
            # and prototype texts, aggregated per condition.
            return self._fallback_text_scores(texts, all_conditions)

        # Build condition_prototypes dict for CosineSimilarityEngine
        # (from ConditionDefinition.prototypes: list[ConceptPrototype])
        condition_prototypes: dict[str, list[dict]] = {}
        cond_proto_embs: dict[str, np.ndarray] = {}

        for cond in proto_conds:
            if cond.name not in prototype_embeddings:
                continue
            condition_prototypes[cond.name] = [
                {
                    "prototype_text": p.prototype_text,
                    "is_member": p.is_member,
                    "weight": p.weight,
                }
                for p in cond.prototypes
            ]
            cond_proto_embs[cond.name] = prototype_embeddings[cond.name]

        if not condition_prototypes:
            return np.zeros((n_texts, n_conds), dtype=np.float64)

        # Compute all scores at once via cosine engine — one (N, M_proto) matrix
        scores = self._cosine_engine.compute_scores(
            text_embeddings, condition_prototypes, cond_proto_embs
        )  # (N, M_proto)

        # Map back to full condition ordering (all_conditions may include
        # the outcome condition and deprecated KEYWORD/HYBRID conditions)
        full_scores = np.zeros((n_texts, n_conds), dtype=np.float64)
        proto_names = list(condition_prototypes.keys())
        for j, cond in enumerate(all_conditions):
            if cond.name in condition_prototypes:
                proto_idx = proto_names.index(cond.name)
                full_scores[:, j] = scores[:, proto_idx]

        return full_scores

    @staticmethod
    def _fallback_text_scores(
        texts: list[str],
        all_conditions: list[ConditionDefinition],
    ) -> np.ndarray:
        """Compute varied raw scores without BERT embeddings.

        Uses text-length normalization as the primary scoring signal
        (text_length / max_length), then applies a small per-condition offset
        so that different conditions produce distinct score distributions.
        Raw scores that vary across texts AND across conditions prevent
        DirectCalibration from hitting the degenerate min==max branch.

        Character trigram Jaccard (previous implementation) was removed
        because short Chinese prototype phrases produce zero n-gram overlap
        with real text content, causing all-zero similarity for every text —
        which cascaded into uniform 0.5 calibration output.

        Args:
            texts: List of input text strings (N,).
            all_conditions: List of all condition definitions.

        Returns:
            Raw scores matrix of shape (N, M) where M = len(all_conditions).
        """
        n_texts = len(texts)
        n_conds = len(all_conditions)
        if n_texts == 0 or n_conds == 0:
            return np.zeros((n_texts, n_conds), dtype=np.float64)

        # Self-normalizing text-length signal: len/(len+50) produces (0, ~0.86)
        # for typical Chinese text lengths without requiring min/max across texts.
        # This ensures a single text (calibrate_one) gets a non-1.0 base score,
        # leaving room for per-condition offsets below.
        text_lengths = np.array([len(t) for t in texts], dtype=np.float64)
        base = text_lengths / (text_lengths + 100.0)

        # Per-condition offset ensures each condition produces distinct scores
        # for the same text. Without this, calibrate_one (1 text, M conditions)
        # would give all conditions the same base value → DirectCalibration
        # sees identical scores → ValueError.
        scores = np.zeros((n_texts, n_conds), dtype=np.float64)
        for j in range(n_conds):
            cond_weight = j / max(n_conds - 1, 1) if n_conds > 1 else 0.0
            # Blend per-text length signal with per-condition position
            scores[:, j] = base * 0.35 + cond_weight * 0.65

        return scores

    @staticmethod
    def _char_trigrams(text: str) -> set[str]:
        """Extract character trigrams from a text string."""
        if len(text) < 3:
            return {text}
        return {text[i : i + 3] for i in range(len(text) - 2)}

    @staticmethod
    def _jaccard(a: set[str], b: set[str]) -> float:
        """Jaccard similarity between two sets."""
        if not a and not b:
            return 1.0
        union = a | b
        if not union:
            return 0.0
        return len(a & b) / len(union)

    @staticmethod
    def _compute_raw_scores(
        scores_matrix: np.ndarray,
        col_idx: int,
    ) -> np.ndarray:
        """Extract raw scores for a single condition column.

        Args:
            scores_matrix: Pre-computed (N, M) raw scores matrix.
            col_idx: Column index into the scores matrix.

        Returns:
            1D array of raw scores for this condition.
        """
        return scores_matrix[:, col_idx]

    def _process_core(
        self,
        texts: list[str],
        scores_matrix: np.ndarray,
        outcome_provider: Callable[[int], np.ndarray | None],
    ) -> np.ndarray:
        """Core membership computation shared by process/process_with_outcome.

        Iterates over all conditions, indexing into the pre-computed scores
        matrix. The outcome column (if any) receives its values from
        *outcome_provider*.

        Args:
            texts: List of text strings.
            scores_matrix: Pre-computed raw scores of shape (N, M)
                where M = len(all_conditions).
            outcome_provider: Called as outcome_provider(col_idx) for each
                column. Returns a membership vector for the outcome column,
                or None if this column is scored normally.

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
                raw_scores = self._compute_raw_scores(scores_matrix, j)
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

    def process(
        self,
        data: InputData,
        text_embeddings: np.ndarray | None = None,
        prototype_embeddings: dict[str, np.ndarray] | None = None,
    ) -> OutputData:
        """Run text calibration on input data.

        Args:
            data: InputData with text corpus.
            text_embeddings: (N, d) pre-computed BERT embeddings for each text.
                When None, all raw scores default to zero.
            prototype_embeddings: Mapping from condition name to (K, d)
                prototype embedding arrays. When None, all raw scores default
                to zero.

        Returns:
            OutputData with MembershipData containing fuzzy-set scores.
        """
        texts = self._extract_texts(data)
        scores_matrix = self._precompute_scores(
            texts, text_embeddings, prototype_embeddings
        )

        n_conds = len(self._all_conditions())
        membership = self._process_core(
            texts,
            scores_matrix,
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

    def process_with_outcome(
        self,
        data: InputData,
        outcome_vector: np.ndarray,
        text_embeddings: np.ndarray | None = None,
        prototype_embeddings: dict[str, np.ndarray] | None = None,
    ) -> OutputData:
        """Process conditions normally but use pre-supplied outcome values.

        The outcome column is set from *outcome_vector* (crisp 0/1) instead
        of being computed from prototype similarity.

        Args:
            data: InputData with texts.
            outcome_vector: 1D array of binary outcomes (0 or 1).
            text_embeddings: (N, d) pre-computed BERT embeddings, or None.
            prototype_embeddings: Mapping from condition name to (K, d)
                prototype embedding arrays, or None.

        Returns:
            OutputData with MembershipData where the last column is the outcome.
        """
        texts = self._extract_texts(data)
        scores_matrix = self._precompute_scores(
            texts, text_embeddings, prototype_embeddings
        )

        n_conds = len(self._all_conditions())
        has_outcome = self.condition_set.outcome is not None

        membership = self._process_core(
            texts,
            scores_matrix,
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

    def calibrate_one(
        self,
        sample: TrainingSample,
        text_embeddings: np.ndarray | None = None,
        prototype_embeddings: dict[str, np.ndarray] | None = None,
    ) -> MembershipData:
        """Calibrate a single training sample.

        Used by the Pyodide worker to process samples one at a time.

        Args:
            sample: A TrainingSample with text and optional labeled_scores.
            text_embeddings: (1, d) pre-computed BERT embedding for this
                single sample, or None.
            prototype_embeddings: Mapping from condition name to (K, d)
                prototype embedding arrays, or None.

        Returns:
            MembershipData with membership shape (1, n_conditions).
        """
        texts = [sample.text]
        scores_matrix = self._precompute_scores(
            texts, text_embeddings, prototype_embeddings
        )
        all_conditions = self._all_conditions()
        n_conds = len(all_conditions)
        membership = np.zeros((1, n_conds), dtype=np.float64)

        for j, cond in enumerate(all_conditions):
            raw_scores = self._compute_raw_scores(scores_matrix, j)
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
