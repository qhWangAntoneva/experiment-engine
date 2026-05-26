"""BERT CLS embedding cosine similarity engine for prototype-based QCA scoring.

Replaces the character-bigram Jaccard similarity approach with BERT semantic
similarity for fuzzy-set calibration. Uses prototype theory to compute graded
category membership from embedding-space distances.

Algorithm:
  1. L2-normalize all embeddings (texts and prototypes).
  2. Aggregate prototype embeddings per condition into positive/negative centroids.
  3. Compute cosine similarity (dot product of unit vectors) between each text
     and each condition's positive/negative centroids.
  4. Convert cosine similarities to raw scores in [0,1] via softmax or
     normalized-difference formula.
"""

from __future__ import annotations

import numpy as np


class CosineSimilarityEngine:
    """Computes prototype-based similarity scores from pre-computed embeddings.

    This engine is the *similarity* stage of the BERT prototype pipeline.
    It takes already-computed BERT embeddings (from any embedding source:
    ONNX, Transformers.js, sentence-transformers, etc.) and produces raw
    scores suitable for downstream calibration (Direct/Indirect/Ragin).

    The embedding extraction and pooling strategy (CLS, mean-pooling, etc.)
    are external concerns. This engine operates purely on vectors.

    Algorithm specification:
        Primary formula (softmax with temperature):
            raw = exp(tau * sim_pos) / (exp(tau * sim_pos) + exp(tau * sim_neg))
        Fallback formula (normalized difference):
            raw = clip((sim_pos - sim_neg + 1) / 2, 0, 1)
        Aggregation methods:
            centroid: mean of prototype embeddings (Rosch prototype theory)
            max: maximum individual prototype similarity (exemplar theory)

    Edge cases handled:
        No prototypes -> raw = 0.0
        Positive-only -> raw = (sim_pos + 1) / 2
        Negative-only -> raw = (1 - sim_neg) / 2
        Zero-vector / empty text -> raw = 0.5 (maximum ambiguity)
    """

    #: Valid aggregation strategies.
    AGGREGATIONS: tuple[str, ...] = ("centroid", "max")

    #: Valid scoring formulas.
    SCORINGS: tuple[str, ...] = ("softmax", "diff")

    def __init__(
        self,
        temperature: float = 5.0,
        aggregation: str = "centroid",
        scoring: str = "softmax",
    ) -> None:
        """Initialise the cosine similarity engine.

        Args:
            temperature: Softmax temperature parameter tau.
                Higher values sharpen discrimination (default 5.0).
                Typical range: 1.0 (soft) to 10.0 (very sharp).
            aggregation: Prototype aggregation strategy.
                ``"centroid"`` — mean of embeddings (prototype theory).
                ``"max"`` — maximum individual similarity (exemplar theory).
            scoring: Cosine-to-raw-score formula.
                ``"softmax"`` — softmax with temperature (primary).
                ``"diff"`` — normalized difference (fallback).

        Raises:
            ValueError: If *aggregation* or *scoring* is not a recognised value.
        """
        if temperature <= 0:
            raise ValueError(f"temperature must be > 0, got {temperature}")
        self.temperature = float(temperature)

        if aggregation not in self.AGGREGATIONS:
            raise ValueError(
                f"aggregation must be one of {self.AGGREGATIONS}, got {aggregation!r}"
            )
        self.aggregation = aggregation

        if scoring not in self.SCORINGS:
            raise ValueError(f"scoring must be one of {self.SCORINGS}, got {scoring!r}")
        self.scoring = scoring

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_scores(
        self,
        text_embeddings: np.ndarray,
        condition_prototypes: dict[str, list[dict]],
        prototype_embeddings: dict[str, np.ndarray],
    ) -> np.ndarray:
        """Compute raw prototype-similarity scores for every text-condition pair.

        Args:
            text_embeddings: Pre-computed BERT embeddings of shape ``(N, d)``
                where *N* is the number of texts and *d* is the embedding
                dimension (e.g. 768 for bert-base-chinese).
            condition_prototypes: Mapping from condition name to a list of
                prototype dictionaries. Each dictionary must have keys
                ``prototype_text`` (str), ``is_member`` (int: 0 or 1), and
                ``weight`` (float in [0, 1]).
                The order of prototypes must match the order of rows in
                the corresponding entry of *prototype_embeddings*.
            prototype_embeddings: Mapping from condition name to a ``(K, d)``
                ndarray of pre-computed prototype embeddings, where *K* is
                the number of prototypes for that condition.

        Returns:
            ndarray of shape ``(N, M)`` with raw scores in ``[0, 1]``,
            where *M* is the number of conditions.

        Raises:
            ValueError: If shapes or dimensions are inconsistent.

        Notes:
            Texts whose embedding is the zero vector (within numerical epsilon)
            produce a score of 0.5 — maximum ambiguity — regardless of the
            scoring formula, because cosine similarity to any unit vector is 0.
        """
        # ── Input validation ───────────────────────────────────────
        self._validate_inputs(
            text_embeddings, condition_prototypes, prototype_embeddings
        )

        n_texts, _d = text_embeddings.shape
        condition_names = list(condition_prototypes.keys())
        m_conds = len(condition_names)

        if m_conds == 0:
            return np.zeros((n_texts, 0), dtype=np.float64)

        # ── L2-normalize text embeddings ───────────────────────────
        text_norms = np.linalg.norm(text_embeddings, axis=1, keepdims=True)
        zero_mask = (text_norms < 1e-12).ravel()
        # Avoid 0/0 warning: use safe division
        safe_norms = np.where(text_norms > 1e-12, text_norms, 1.0)
        text_unit = text_embeddings / safe_norms
        text_unit[zero_mask] = 0.0  # zero vectors stay zero

        # ── Compute scores per condition ───────────────────────────
        scores = np.zeros((n_texts, m_conds), dtype=np.float64)

        for j, cond_name in enumerate(condition_names):
            proto_emb = prototype_embeddings[cond_name]  # (K_j, d)
            proto_meta = condition_prototypes[cond_name]  # list of K_j dicts

            pos_indices = [i for i, p in enumerate(proto_meta) if p["is_member"] == 1]
            neg_indices = [i for i, p in enumerate(proto_meta) if p["is_member"] == 0]

            has_pos = len(pos_indices) > 0
            has_neg = len(neg_indices) > 0

            # Edge case 6.1: no prototypes at all
            if not has_pos and not has_neg:
                scores[:, j] = 0.0
                continue

            # L2-normalize prototype embeddings
            proto_unit = self._normalize_rows(proto_emb)

            if self.aggregation == "centroid":
                sim_pos = (
                    self._compute_centroid_similarity(
                        text_unit, proto_unit, pos_indices, proto_meta
                    )
                    if has_pos
                    else None
                )
                sim_neg = (
                    self._compute_centroid_similarity(
                        text_unit, proto_unit, neg_indices, proto_meta
                    )
                    if has_neg
                    else None
                )
            else:  # max
                sim_pos = (
                    self._compute_max_similarity(
                        text_unit, proto_unit, pos_indices, proto_meta
                    )
                    if has_pos
                    else None
                )
                sim_neg = (
                    self._compute_max_similarity(
                        text_unit, proto_unit, neg_indices, proto_meta
                    )
                    if has_neg
                    else None
                )

            # Edge case 6.2: positive-only
            if has_pos and not has_neg:
                scores[:, j] = (sim_pos + 1.0) / 2.0  # type: ignore[operator]
            # Edge case 6.3: negative-only
            elif not has_pos and has_neg:
                scores[:, j] = (1.0 - sim_neg) / 2.0  # type: ignore[operator]
            # Full case: both positive and negative
            else:
                scores[:, j] = self._apply_scoring(sim_pos, sim_neg)  # type: ignore[arg-type]

        # Edge case 6.5: zero-vector texts -> 0.5 (maximum ambiguity)
        for j in range(m_conds):
            scores[zero_mask, j] = 0.5

        return scores

    # ------------------------------------------------------------------
    # Scoring formulas
    # ------------------------------------------------------------------

    def _apply_scoring(
        self,
        sim_pos: np.ndarray,
        sim_neg: np.ndarray,
    ) -> np.ndarray:
        """Convert cosine similarities to raw scores via the configured formula."""
        if self.scoring == "softmax":
            return self._softmax_scoring(sim_pos, sim_neg)
        return self._diff_scoring(sim_pos, sim_neg)

    def _softmax_scoring(
        self,
        sim_pos: np.ndarray,
        sim_neg: np.ndarray,
    ) -> np.ndarray:
        """Softmax with temperature: exp(tau*pos) / (exp(tau*pos) + exp(tau*neg)).

        Numerically stable via the log-sum-exp trick.
        """
        # Clip cosines to [-1, 1] to guard against rounding errors
        sim_pos = np.clip(sim_pos, -1.0, 1.0)
        sim_neg = np.clip(sim_neg, -1.0, 1.0)

        a = self.temperature * sim_pos
        b = self.temperature * sim_neg
        # Numerically stable: subtract max to avoid exp overflow
        m = np.maximum(a, b)
        exp_a = np.exp(a - m)
        exp_b = np.exp(b - m)
        denom = exp_a + exp_b

        # Guard division by zero (can happen if both exps underflow)
        safe_denom = np.where(denom > 0, denom, 1.0)
        result = exp_a / safe_denom

        # Where both exps underflowed, fall back to 0.5
        result = np.where(denom > 0, result, 0.5)
        return result.astype(np.float64)

    def _diff_scoring(
        self,
        sim_pos: np.ndarray,
        sim_neg: np.ndarray,
    ) -> np.ndarray:
        """Normalized difference: clip((sim_pos - sim_neg + 1) / 2, 0, 1)."""
        sim_pos = np.clip(sim_pos, -1.0, 1.0)
        sim_neg = np.clip(sim_neg, -1.0, 1.0)
        return np.clip((sim_pos - sim_neg + 1.0) / 2.0, 0.0, 1.0)

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
        """L2-normalize each row of *matrix* to unit length.

        Rows with near-zero norm are returned as zero vectors.
        """
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        safe_norms = np.where(norms > 1e-12, norms, 1.0)
        result = matrix / safe_norms
        result[norms.ravel() <= 1e-12] = 0.0
        return result

    @staticmethod
    def _compute_centroid_similarity(
        text_unit: np.ndarray,
        proto_unit: np.ndarray,
        indices: list[int],
        proto_meta: list[dict],
    ) -> np.ndarray:
        """Compute cosine similarity between text embeddings and a weighted centroid.

        Args:
            text_unit: Row-normalized text embeddings, shape ``(N, d)``.
            proto_unit: Row-normalized prototype embeddings, shape ``(K, d)``.
            indices: Indices of prototypes to include in the centroid.
            proto_meta: Metadata for each prototype (has ``weight`` field).

        Returns:
            Cosine similarities, shape ``(N,)``, clipped to ``[-1, 1]``.
        """
        n_idx = len(indices)
        if n_idx == 0:
            return np.zeros(text_unit.shape[0], dtype=np.float64)

        weights = np.array(
            [proto_meta[i]["weight"] for i in indices],
            dtype=np.float64,
        )
        # Compute weighted centroid
        weighted_sum = np.sum(proto_unit[indices] * weights[:, np.newaxis], axis=0)
        total_weight = np.sum(weights)
        if total_weight > 0:
            centroid = weighted_sum / total_weight
        else:
            centroid = np.mean(proto_unit[indices], axis=0)

        # Re-normalize centroid to unit length
        centroid_norm = np.linalg.norm(centroid)
        if centroid_norm > 1e-12:
            centroid = centroid / centroid_norm

        # Dot product of unit vectors = cosine similarity
        cos_sim = text_unit @ centroid  # (N,)
        return np.clip(cos_sim, -1.0, 1.0)

    @staticmethod
    def _compute_max_similarity(
        text_unit: np.ndarray,
        proto_unit: np.ndarray,
        indices: list[int],
        proto_meta: list[dict],
    ) -> np.ndarray:
        """Compute maximum weighted cosine similarity between each text and prototypes.

        Each prototype's cosine similarity is multiplied by its weight before
        taking the max. A prototype with weight 0.0 is effectively ignored;
        a prototype with weight 1.0 contributes its full similarity.

        Args:
            text_unit: Row-normalized text embeddings, shape ``(N, d)``.
            proto_unit: Row-normalized prototype embeddings, shape ``(K, d)``.
            indices: Indices of prototypes to consider.
            proto_meta: Metadata for each prototype (has ``weight`` field).

        Returns:
            Maximum weighted cosine similarity per text, shape ``(N,)``,
            clipped to ``[-1, 1]``.
        """
        if len(indices) == 0:
            return np.zeros(text_unit.shape[0], dtype=np.float64)

        # (N, d) @ (d, K_sub) -> (N, K_sub)
        cos_all = text_unit @ proto_unit[indices].T
        cos_all = np.clip(cos_all, -1.0, 1.0)

        # Weight each prototype's similarity by its weight before taking max
        weights = np.array(
            [proto_meta[i]["weight"] for i in indices],
            dtype=np.float64,
        )
        weighted = cos_all * weights[np.newaxis, :]

        # If all weights are zero, return zeros to avoid misleading max
        if np.all(weights == 0.0):
            return np.zeros(text_unit.shape[0], dtype=np.float64)

        return np.max(weighted, axis=1)

    # ------------------------------------------------------------------
    # Input validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_inputs(
        text_embeddings: np.ndarray,
        condition_prototypes: dict[str, list[dict]],
        prototype_embeddings: dict[str, np.ndarray],
    ) -> None:
        """Validate shapes, dimensions, and value ranges of inputs.

        Raises:
            ValueError: On shape mismatches or invalid values.
        """
        if text_embeddings.ndim != 2:
            raise ValueError(
                f"text_embeddings must be 2D (N, d), got shape {text_embeddings.shape}"
            )
        _n_texts, d = text_embeddings.shape
        if d < 1:
            raise ValueError(f"embedding dimension must be >= 1, got {d}")

        # Prototype metadata keys must match embedding keys
        meta_keys = set(condition_prototypes.keys())
        emb_keys = set(prototype_embeddings.keys())
        if meta_keys != emb_keys:
            missing_meta = emb_keys - meta_keys
            missing_emb = meta_keys - emb_keys
            msg_parts = []
            if missing_meta:
                msg_parts.append(
                    f"prototype_embeddings keys {sorted(missing_meta)} "
                    f"missing from condition_prototypes"
                )
            if missing_emb:
                msg_parts.append(
                    f"condition_prototypes keys {sorted(missing_emb)} "
                    f"missing from prototype_embeddings"
                )
            raise ValueError("; ".join(msg_parts))

        for cond_name in condition_prototypes:
            proto_list = condition_prototypes[cond_name]
            emb = prototype_embeddings[cond_name]

            if emb.ndim != 2:
                raise ValueError(
                    f"prototype_embeddings['{cond_name}'] must be 2D "
                    f"(K, d), got shape {emb.shape}"
                )
            k_emb, d_emb = emb.shape
            k_meta = len(proto_list)

            if k_emb != k_meta:
                raise ValueError(
                    f"Condition '{cond_name}': prototype count mismatch "
                    f"— {k_meta} in condition_prototypes but {k_emb} in "
                    f"prototype_embeddings"
                )

            if d_emb != d:
                raise ValueError(
                    f"Condition '{cond_name}': embedding dimension {d_emb} "
                    f"does not match text embedding dimension {d}"
                )

            for idx, proto in enumerate(proto_list):
                if proto.get("is_member") not in (0, 1):
                    raise ValueError(
                        f"Condition '{cond_name}', prototype {idx}: "
                        f"is_member must be 0 or 1, got {proto.get('is_member')!r}"
                    )
                w = proto.get("weight", 1.0)
                if not (0.0 <= w <= 1.0):
                    raise ValueError(
                        f"Condition '{cond_name}', prototype {idx}: "
                        f"weight must be in [0, 1], got {w}"
                    )
