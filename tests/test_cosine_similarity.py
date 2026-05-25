"""Comprehensive unit tests for CosineSimilarityEngine.

Covers:
  - Identical / orthogonal / opposite embeddings
  - Temperature sharpening
  - Multiple conditions
  - Edge cases: no prototypes, positive-only, negative-only, zero vectors
  - Centroid vs max aggregation
  - Weighted prototypes
  - Normalized difference formula
  - Numerical stability (overflow protection)
  - Input validation (shape/dimension errors)
"""

from __future__ import annotations

import numpy as np
import pytest

from experiment_engine.text_calibration.cosine_similarity import (
    CosineSimilarityEngine,
)

# ── Helpers ──────────────────────────────────────────────────────────


def _make_proto_meta(
    proto_texts: list[str], memberships: list[int], weights: list[float] | None = None
) -> list[dict]:
    """Build a condition_prototypes list entry from parallel arrays."""
    if weights is None:
        weights = [1.0] * len(proto_texts)
    return [
        {"prototype_text": t, "is_member": m, "weight": w}
        for t, m, w in zip(proto_texts, memberships, weights, strict=False)
    ]


def _unit(vec: np.ndarray) -> np.ndarray:
    """L2-normalize a 1D vector to unit length."""
    n = np.linalg.norm(vec)
    if n < 1e-12:
        return vec.copy()
    return vec / n


# ── Test Classes ─────────────────────────────────────────────────────


class TestBasicSimilarity:
    """Tests for core similarity behavior with simple 4-dim embeddings."""

    D = 4  # small embedding dimension for clarity

    def _embed(self, *coords: float) -> np.ndarray:
        """Create a unit-length embedding from coordinates (padded to D)."""
        v = np.zeros(self.D, dtype=np.float64)
        for i, c in enumerate(coords):
            if i < self.D:
                v[i] = c
        n = np.linalg.norm(v)
        if n > 1e-12:
            return v / n
        return v

    # ── Identical embeddings (positive-only) ─────────────────────

    def test_identical_pos_only_yields_one(self):
        """Text == positive prototype => sim=1 => (1+1)/2 = 1.0."""
        engine = CosineSimilarityEngine()
        text = self._embed(1.0, 0.0, 0.0, 0.0).reshape(1, -1)

        pos_emb = text.copy()  # identical
        cond_protos = {"C": _make_proto_meta(["pos"], [1])}
        proto_embs = {"C": pos_emb}

        scores = engine.compute_scores(text, cond_protos, proto_embs)
        assert scores.shape == (1, 1)
        assert abs(scores[0, 0] - 1.0) < 1e-10

    def test_identical_with_noise_pos_only_high(self):
        """Slightly perturbed text => still very high score."""
        engine = CosineSimilarityEngine(temperature=5.0)
        pos = _unit(np.array([1.0, 0.0, 0.0, 0.0]))
        text = _unit(pos + 0.01 * np.random.RandomState(42).randn(4))
        text = text.reshape(1, -1)
        pos_emb = pos.reshape(1, -1)

        scores = engine.compute_scores(
            text,
            {"C": _make_proto_meta(["pos"], [1])},
            {"C": pos_emb},
        )
        assert scores[0, 0] > 0.95, f"Expected >0.95, got {scores[0, 0]}"

    # ── Orthogonal embeddings ────────────────────────────────────

    def test_orthogonal_pos_neg_equal_softmax_yields_half(self):
        """Equally similar to pos and neg => softmax yields 0.5."""
        engine = CosineSimilarityEngine(temperature=5.0)
        # text pointed at [1,0,0,0], pos at [0,1,0,0], neg at [0,0,1,0]
        # cos(text, pos) = 0, cos(text, neg) = 0 => softmax(0,0) = 0.5
        text = self._embed(1.0, 0.0, 0.0, 0.0).reshape(1, -1)
        pos_emb = self._embed(0.0, 1.0, 0.0, 0.0).reshape(1, -1)
        neg_emb = self._embed(0.0, 0.0, 1.0, 0.0).reshape(1, -1)

        cond = {"C": _make_proto_meta(["pos", "neg"], [1, 0])}
        emb = {"C": np.vstack([pos_emb, neg_emb])}

        scores = engine.compute_scores(text, cond, emb)
        assert abs(scores[0, 0] - 0.5) < 1e-10, f"Expected 0.5, got {scores[0, 0]}"

    def test_orthogonal_diff_formula_yields_half(self):
        """Normalized-diff formula also yields 0.5 for equal similarities."""
        engine = CosineSimilarityEngine(scoring="diff")
        text = self._embed(1.0, 0.0, 0.0, 0.0).reshape(1, -1)
        pos_emb = self._embed(0.0, 1.0, 0.0, 0.0).reshape(1, -1)
        neg_emb = self._embed(0.0, 0.0, 1.0, 0.0).reshape(1, -1)

        scores = engine.compute_scores(
            text,
            {"C": _make_proto_meta(["pos", "neg"], [1, 0])},
            {"C": np.vstack([pos_emb, neg_emb])},
        )
        assert abs(scores[0, 0] - 0.5) < 1e-10

    # ── Opposite embeddings ──────────────────────────────────────

    def test_opposite_pos_only_yields_zero(self):
        """Text = -prototype => sim=-1 => (-1+1)/2 = 0."""
        engine = CosineSimilarityEngine()
        pos_vec = _unit(np.array([1.0, 0.0, 0.0, 0.0]))
        text = (-pos_vec).reshape(1, -1)  # opposite
        pos_emb = pos_vec.reshape(1, -1)

        scores = engine.compute_scores(
            text,
            {"C": _make_proto_meta(["pos"], [1])},
            {"C": pos_emb},
        )
        assert abs(scores[0, 0] - 0.0) < 1e-10

    def test_opposite_with_both_softmax_near_zero(self):
        """Text = -pos and +neg => sim_pos=-1, sim_neg=1 => softmax near 0."""
        engine = CosineSimilarityEngine(temperature=5.0)
        pos_vec = _unit(np.array([1.0, 0.0, 0.0, 0.0]))
        neg_vec = _unit(np.array([-1.0, 0.0, 0.0, 0.0]))  # opposite to pos
        text = (-pos_vec).reshape(1, -1)  # text = [-1,0,0,0], opposite to pos

        # text cos with pos: -1 * 1 = -1; text cos with neg: (-1)*(-1) = 1
        scores = engine.compute_scores(
            text,
            {"C": _make_proto_meta(["pos", "neg"], [1, 0])},
            {"C": np.vstack([pos_vec, neg_vec])},
        )
        # sim_pos = -1, sim_neg = 1 => softmax(5*(-1), 5*1) = e^-5/(e^-5+e^5) ~ 0
        assert scores[0, 0] < 0.0001, f"Expected near 0, got {scores[0, 0]}"

    # ── Cosine similarity produces values in [-1, 1] ─────────────

    def test_cosine_clipping(self):
        """Raw dot products of unit vectors are clipped to [-1, 1]."""
        engine = CosineSimilarityEngine()
        # Slightly exceed 1.0 due to floating point
        text = _unit(np.array([1.0 + 1e-15, 0.0]))

        # Force a scenario where cosine might exceed 1.0
        pos_emb = text.copy()
        neg_emb = -text.copy()

        cond = {"C": _make_proto_meta(["pos", "neg"], [1, 0])}
        emb = {"C": np.vstack([pos_emb, neg_emb])}
        scores = engine.compute_scores(text.reshape(1, -1), cond, emb)
        # Should not be NaN
        assert not np.isnan(scores[0, 0])
        assert 0.0 <= scores[0, 0] <= 1.0


class TestSoftmaxTemperature:
    """Tests for temperature parameter effects."""

    D = 4

    def _setup(self, sim_pos_val: float, sim_neg_val: float):
        """Create embeddings with known cosine similarities."""
        # Build unit vectors such that dot products equal the target values
        text_unit = _unit(np.array([1.0, 0.0, 0.0, 0.0]))

        # pos_vec: a * text_unit + b * orthogonal
        # cos = a -> we want a = sim_pos_val
        a_pos = np.clip(sim_pos_val, -0.999, 0.999)  # avoid exact 1.0
        b_pos = np.sqrt(max(0.0, 1.0 - a_pos**2))
        pos_vec = _unit(np.array([a_pos, b_pos, 0.0, 0.0]))

        a_neg = np.clip(sim_neg_val, -0.999, 0.999)
        b_neg = np.sqrt(max(0.0, 1.0 - a_neg**2))
        neg_vec = _unit(np.array([a_neg, b_neg, 0.0, 0.0]))

        return text_unit, pos_vec, neg_vec

    def test_higher_temperature_sharpens(self):
        """tau=10 should produce more extreme scores than tau=1 for same sim."""
        text, pos_vec, neg_vec = self._setup(0.5, 0.3)

        engine_low = CosineSimilarityEngine(temperature=1.0)
        engine_high = CosineSimilarityEngine(temperature=10.0)

        cond = {"C": _make_proto_meta(["pos", "neg"], [1, 0])}
        emb = {"C": np.vstack([pos_vec.reshape(1, -1), neg_vec.reshape(1, -1)])}

        s_low = engine_low.compute_scores(text.reshape(1, -1), cond, emb)
        s_high = engine_high.compute_scores(text.reshape(1, -1), cond, emb)

        # Higher temperature -> more extreme (further from 0.5)
        assert abs(s_high[0, 0] - 0.5) > abs(s_low[0, 0] - 0.5), (
            f"low tau score={s_low[0, 0]}, high tau score={s_high[0, 0]}"
        )

    def test_low_temperature_near_half(self):
        """tau=0.5 gives scores very close to 0.5 even with clear diff."""
        engine = CosineSimilarityEngine(temperature=0.5)
        text, pos_vec, neg_vec = self._setup(0.8, 0.2)
        cond = {"C": _make_proto_meta(["pos", "neg"], [1, 0])}
        emb = {"C": np.vstack([pos_vec.reshape(1, -1), neg_vec.reshape(1, -1)])}

        scores = engine.compute_scores(text.reshape(1, -1), cond, emb)
        # With tau=0.5, even sim_pos=0.8, sim_neg=0.2 produces a moderate score
        assert 0.4 < scores[0, 0] < 0.75, f"Expected moderate score, got {scores[0, 0]}"

    def test_very_high_temperature_approaches_step(self):
        """tau=100 effectively produces 0 or 1 based on which sim is larger."""
        engine = CosineSimilarityEngine(temperature=100.0)
        text, pos_vec, neg_vec = self._setup(0.6, 0.4)
        cond = {"C": _make_proto_meta(["pos", "neg"], [1, 0])}
        emb = {"C": np.vstack([pos_vec.reshape(1, -1), neg_vec.reshape(1, -1)])}

        scores = engine.compute_scores(text.reshape(1, -1), cond, emb)
        # pos > neg => score near 1
        assert scores[0, 0] > 0.999

    def test_temperature_equals_softmax_sigmoid_equivalent(self):
        """softmax(tau*s_pos, tau*s_neg) = sigmoid(tau*(s_pos - s_neg))."""
        engine = CosineSimilarityEngine(temperature=3.0)
        text, pos_vec, neg_vec = self._setup(0.7, 0.15)

        cond = {"C": _make_proto_meta(["pos", "neg"], [1, 0])}
        emb = {"C": np.vstack([pos_vec.reshape(1, -1), neg_vec.reshape(1, -1)])}

        scores = engine.compute_scores(text.reshape(1, -1), cond, emb)

        # Manual computation via sigmoid
        s_pos = float(np.clip(np.dot(text, pos_vec), -1.0, 1.0))
        s_neg = float(np.clip(np.dot(text, neg_vec), -1.0, 1.0))
        expected = 1.0 / (1.0 + np.exp(-3.0 * (s_pos - s_neg)))

        assert abs(scores[0, 0] - expected) < 1e-12


class TestMultipleConditions:
    """Tests for multi-condition scoring."""

    def test_three_conditions_simultaneously(self):
        """Three conditions produce (N, 3) output."""
        engine = CosineSimilarityEngine(temperature=5.0)

        # 2 texts, 3 conditions, 4-dim embeddings
        np.random.seed(123)
        text_emb = np.random.randn(2, 4).astype(np.float64)
        text_emb = text_emb / np.linalg.norm(text_emb, axis=1, keepdims=True)

        cond_protos = {
            "cond_a": _make_proto_meta(["a_pos", "a_neg"], [1, 0]),
            "cond_b": _make_proto_meta(["b_pos"], [1]),
            "cond_c": _make_proto_meta(["c_neg"], [0]),
        }
        proto_embs = {
            "cond_a": np.vstack(
                [
                    _unit(np.array([1.0, 0.0, 0.0, 0.0])),
                    _unit(np.array([-1.0, 0.0, 0.0, 0.0])),
                ]
            ),
            "cond_b": _unit(np.array([0.0, 1.0, 0.0, 0.0])).reshape(1, -1),
            "cond_c": _unit(np.array([0.0, 0.0, 1.0, 0.0])).reshape(1, -1),
        }

        scores = engine.compute_scores(text_emb, cond_protos, proto_embs)
        assert scores.shape == (2, 3)
        assert np.all(scores >= 0.0)
        assert np.all(scores <= 1.0)

    def test_condition_order_preserved(self):
        """Output column order matches condition_prototypes key order."""
        engine = CosineSimilarityEngine()
        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)

        # Two conditions with different prototypes
        cond_protos = {
            "first": _make_proto_meta(["fp"], [1]),
            "second": _make_proto_meta(["sn"], [0]),
        }
        proto_embs = {
            "first": _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1),
            "second": _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1),
        }

        scores = engine.compute_scores(text, cond_protos, proto_embs)
        # first (positive-only, same direction) -> near 1.0
        # second (negative-only, same direction) -> near 0.0
        assert scores[0, 0] > 0.99, f"first col: {scores[0, 0]}"
        assert scores[0, 1] < 0.01, f"second col: {scores[0, 1]}"


class TestEdgeCases:
    """Tests for all edge cases specified in the algorithm document."""

    D = 4

    def test_no_prototypes_produces_zero(self):
        """Section 6.1: no prototypes => all zeros."""
        engine = CosineSimilarityEngine()
        text = np.random.randn(3, self.D).astype(np.float64)

        scores = engine.compute_scores(
            text,
            {"C": []},  # empty prototype list
            {"C": np.zeros((0, self.D), dtype=np.float64)},
        )
        assert np.all(scores == 0.0)

    def test_positive_only_monotonic(self):
        """Section 6.2: score = (sim_pos + 1) / 2, monotonic in sim_pos."""
        engine = CosineSimilarityEngine()

        # text=[1,0,0,0], proto_a=[0.707,0.707,0,0]=high sim, proto_b=[0,1,0,0]=0
        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)
        proto_a = _unit(np.array([0.707, 0.707, 0.0, 0.0]))  # cos ≈ 0.707
        proto_b = _unit(np.array([0.0, 1.0, 0.0, 0.0]))  # cos = 0

        scores_a = engine.compute_scores(
            text,
            {"C": _make_proto_meta(["a"], [1])},
            {"C": proto_a.reshape(1, -1)},
        )
        scores_b = engine.compute_scores(
            text,
            {"C": _make_proto_meta(["b"], [1])},
            {"C": proto_b.reshape(1, -1)},
        )
        # Higher cosine -> higher score
        assert scores_a[0, 0] > scores_b[0, 0], f"{scores_a[0, 0]} vs {scores_b[0, 0]}"

    def test_positive_only_range(self):
        """Positive-only scores span (0, 1) for cosine in (-1, 1)."""
        engine = CosineSimilarityEngine()
        # cos = 1 -> (1+1)/2 = 1; cos = 0 -> 0.5; cos = -1 -> 0
        text_pos = _unit(np.array([1.0, 0.0])).reshape(1, -1)
        proto_same = _unit(np.array([1.0, 0.0])).reshape(1, -1)
        proto_orth = _unit(np.array([0.0, 1.0])).reshape(1, -1)
        proto_opp = _unit(np.array([-1.0, 0.0])).reshape(1, -1)

        s_same = engine.compute_scores(
            text_pos, {"C": _make_proto_meta(["s"], [1])}, {"C": proto_same}
        )
        s_orth = engine.compute_scores(
            text_pos, {"C": _make_proto_meta(["o"], [1])}, {"C": proto_orth}
        )
        s_opp = engine.compute_scores(
            text_pos, {"C": _make_proto_meta(["p"], [1])}, {"C": proto_opp}
        )

        assert abs(s_same[0, 0] - 1.0) < 1e-10
        assert abs(s_orth[0, 0] - 0.5) < 1e-10
        assert abs(s_opp[0, 0] - 0.0) < 1e-10

    def test_negative_only_anti_monotonic(self):
        """Section 6.3: score = (1 - sim_neg) / 2, anti-monotonic."""
        engine = CosineSimilarityEngine()

        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)
        neg_similar = _unit(np.array([1.0, 0.0, 0.0, 0.0]))  # cos=1 -> 0
        neg_different = _unit(np.array([-1.0, 0.0, 0.0, 0.0]))  # cos=-1 -> 1

        s_similar = engine.compute_scores(
            text,
            {"C": _make_proto_meta(["n"], [0])},
            {"C": neg_similar.reshape(1, -1)},
        )
        s_different = engine.compute_scores(
            text,
            {"C": _make_proto_meta(["n"], [0])},
            {"C": neg_different.reshape(1, -1)},
        )
        # More similarity to negative = lower score
        assert s_similar[0, 0] < s_different[0, 0], (
            f"{s_similar[0, 0]} vs {s_different[0, 0]}"
        )

    def test_negative_only_range(self):
        """Negative-only scores span (0, 1)."""
        engine = CosineSimilarityEngine()
        text = _unit(np.array([1.0, 0.0])).reshape(1, -1)
        neg_same = _unit(np.array([1.0, 0.0])).reshape(1, -1)  # cos=1 -> (1-1)/2=0
        neg_orth = _unit(np.array([0.0, 1.0])).reshape(1, -1)  # cos=0 -> 0.5
        neg_opp = _unit(np.array([-1.0, 0.0])).reshape(1, -1)  # cos=-1 -> 1

        s_same = engine.compute_scores(
            text, {"C": _make_proto_meta(["n"], [0])}, {"C": neg_same}
        )
        s_orth = engine.compute_scores(
            text, {"C": _make_proto_meta(["n"], [0])}, {"C": neg_orth}
        )
        s_opp = engine.compute_scores(
            text, {"C": _make_proto_meta(["n"], [0])}, {"C": neg_opp}
        )

        assert abs(s_same[0, 0] - 0.0) < 1e-10
        assert abs(s_orth[0, 0] - 0.5) < 1e-10
        assert abs(s_opp[0, 0] - 1.0) < 1e-10

    def test_zero_vector_text_yields_half(self):
        """Section 6.5: empty text / zero vector => 0.5 (maximum ambiguity)."""
        engine = CosineSimilarityEngine(temperature=5.0)
        text = np.zeros((1, 4), dtype=np.float64)
        pos_emb = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)
        neg_emb = _unit(np.array([-1.0, 0.0, 0.0, 0.0])).reshape(1, -1)

        cond = {"C": _make_proto_meta(["p", "n"], [1, 0])}
        emb = {"C": np.vstack([pos_emb, neg_emb])}

        scores = engine.compute_scores(text, cond, emb)
        assert abs(scores[0, 0] - 0.5) < 1e-10, (
            f"Zero vector should yield 0.5, got {scores[0, 0]}"
        )

    def test_zero_vector_all_conditions_half(self):
        """Zero vectors produce 0.5 for every condition."""
        engine = CosineSimilarityEngine()
        text = np.zeros((2, 8), dtype=np.float64)

        rng = np.random.RandomState(99)
        p1 = rng.randn(2, 8).astype(np.float64)
        p2 = rng.randn(1, 8).astype(np.float64)

        cond_protos = {
            "a": _make_proto_meta(["a1", "a2"], [1, 0]),
            "b": _make_proto_meta(["b1"], [1]),
        }
        proto_embs = {"a": p1, "b": p2}

        scores = engine.compute_scores(text, cond_protos, proto_embs)
        assert np.allclose(scores, 0.5, atol=1e-10)

    def test_zero_conditions_returns_empty(self):
        """Zero conditions => (N, 0) output."""
        engine = CosineSimilarityEngine()
        text = np.random.randn(5, 64).astype(np.float64)
        scores = engine.compute_scores(text, {}, {})
        assert scores.shape == (5, 0)

    def test_single_prototype_centroid(self):
        """Single prototype: centroid = that prototype (no averaging needed)."""
        engine = CosineSimilarityEngine(aggregation="centroid")
        text = _unit(np.array([0.8, 0.6, 0.0, 0.0])).reshape(1, -1)
        proto = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)

        scores = engine.compute_scores(
            text,
            {"C": _make_proto_meta(["p"], [1])},
            {"C": proto},
        )
        # cos = 0.8, positive-only => (0.8+1)/2 = 0.9
        assert abs(scores[0, 0] - 0.9) < 1e-10

    def test_all_zero_weight_prototypes(self):
        """All-zero weights mean equal weighting (fallback to mean)."""
        engine = CosineSimilarityEngine(aggregation="centroid")
        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)

        pos1 = _unit(np.array([1.0, 0.0, 0.0, 0.0]))
        pos2 = _unit(np.array([0.0, 1.0, 0.0, 0.0]))

        cond = {"C": _make_proto_meta(["p1", "p2"], [1, 1], weights=[0.0, 0.0])}
        emb = {"C": np.vstack([pos1, pos2])}

        scores = engine.compute_scores(text, cond, emb)
        # Should not produce NaN; falls back to equal-weight mean
        assert not np.isnan(scores[0, 0])
        assert 0.0 <= scores[0, 0] <= 1.0


class TestAggregationMethods:
    """Centroid vs max-similarity aggregation."""

    D = 4

    def test_centroid_vs_max_different_output(self):
        """Multi-prototype condition: centroid and max produce different scores."""
        text = _unit(np.array([0.5, 0.5, 0.0, 0.0])).reshape(1, -1)

        # Two very different positive prototypes
        pos1 = _unit(np.array([1.0, 0.0, 0.0, 0.0]))
        pos2 = _unit(np.array([0.0, 1.0, 0.0, 0.0]))
        neg1 = _unit(np.array([-1.0, 0.0, 0.0, 0.0]))

        cond = {"C": _make_proto_meta(["p1", "p2", "n1"], [1, 1, 0])}
        emb = {"C": np.vstack([pos1, pos2, neg1])}

        engine_centroid = CosineSimilarityEngine(aggregation="centroid")
        engine_max = CosineSimilarityEngine(aggregation="max")

        s_c = engine_centroid.compute_scores(text, cond, emb)
        s_m = engine_max.compute_scores(text, cond, emb)

        # Should differ (max picks the closest prototype; centroid averages)
        assert abs(s_c[0, 0] - s_m[0, 0]) > 1e-6, (
            f"Centroid={s_c[0, 0]}, Max={s_m[0, 0]}"
        )

    def test_max_with_single_proto_equals_centroid(self):
        """With one positive, one negative: max == centroid (only one element)."""
        text = _unit(np.array([0.6, 0.8, 0.0, 0.0])).reshape(1, -1)
        pos = _unit(np.array([1.0, 0.0, 0.0, 0.0]))
        neg = _unit(np.array([0.0, 1.0, 0.0, 0.0]))

        cond = {"C": _make_proto_meta(["p", "n"], [1, 0])}
        emb = {"C": np.vstack([pos, neg])}

        engine_c = CosineSimilarityEngine(aggregation="centroid")
        engine_m = CosineSimilarityEngine(aggregation="max")

        s_c = engine_c.compute_scores(text, cond, emb)
        s_m = engine_m.compute_scores(text, cond, emb)

        assert abs(s_c[0, 0] - s_m[0, 0]) < 1e-10

    def test_max_favors_best_match(self):
        """Max-similarity: score driven by the closest prototype, not the average."""
        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)

        # One near-exact match and one opposite
        pos_near = _unit(np.array([1.0, 0.0, 0.0, 0.0]))  # cos = 1
        pos_far = _unit(np.array([-1.0, 0.0, 0.0, 0.0]))  # cos = -1
        neg = _unit(np.array([0.0, 1.0, 0.0, 0.0]))  # cos = 0

        cond = {"C": _make_proto_meta(["pn", "pf", "n"], [1, 1, 0])}
        emb = {"C": np.vstack([pos_near, pos_far, neg])}

        engine = CosineSimilarityEngine(aggregation="max")
        scores = engine.compute_scores(text, cond, emb)

        # Max picks pos_near (cos=1), neg (cos=0)
        # sim_pos_max = 1, sim_neg_max = 0
        # softmax(5*1, 5*0) = e^5/(e^5+e^0) ≈ 0.9933
        assert scores[0, 0] > 0.99

        # Centroid would average pos_near and pos_far -> centroid ~ [0,0,0,0] after
        # weighted sum, giving lower score
        engine_c = CosineSimilarityEngine(aggregation="centroid")
        scores_c = engine_c.compute_scores(text, cond, emb)
        assert scores_c[0, 0] < scores[0, 0], (
            f"Max should exceed centroid: {scores[0, 0]} vs {scores_c[0, 0]}"
        )


class TestWeightedPrototypes:
    """Weighted prototype aggregation."""

    D = 4

    def test_weight_zero_excludes_prototype(self):
        """Prototype with weight=0 should not influence centroid."""
        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)

        pos_main = _unit(np.array([1.0, 0.0, 0.0, 0.0]))  # cos=1
        pos_irrelevant = _unit(np.array([-1.0, 0.0, 0.0, 0.0]))  # cos=-1

        # Without weight: centroid = [0,0,0,0] (cancels out)
        # With weight: pos_main=1.0, pos_irrelevant=0.0 => centroid = pos_main
        cond_w = {"C": _make_proto_meta(["pm", "pi"], [1, 1], weights=[1.0, 0.0])}
        cond_now = {"C": _make_proto_meta(["pm", "pi"], [1, 1], weights=[1.0, 1.0])}

        emb = {"C": np.vstack([pos_main, pos_irrelevant])}

        engine = CosineSimilarityEngine(aggregation="centroid", temperature=1.0)
        s_w = engine.compute_scores(text, cond_w, emb)
        s_now = engine.compute_scores(text, cond_now, emb)

        # Weighted: centroid ≈ pos_main => sim_pos ≈ 1 => high score
        assert s_w[0, 0] > s_now[0, 0], (
            f"Weight 0 exclusion should give higher score: {s_w[0, 0]} vs {s_now[0, 0]}"
        )

    def test_weight_half_dilutes_centroid(self):
        """Weight=0.5 dilutes the influence compared to weight=1.0."""
        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)

        pos_good = _unit(np.array([1.0, 0.0, 0.0, 0.0]))  # cos=1
        pos_noise = _unit(np.array([-0.5, 0.866, 0.0, 0.0]))  # cos=-0.5

        cond_w1 = {"C": _make_proto_meta(["g", "n"], [1, 1], weights=[1.0, 1.0])}
        cond_w05 = {"C": _make_proto_meta(["g", "n"], [1, 1], weights=[1.0, 0.5])}

        emb = {"C": np.vstack([pos_good, pos_noise])}

        engine = CosineSimilarityEngine(aggregation="centroid", scoring="diff")
        s_w1 = engine.compute_scores(text, cond_w1, emb)
        s_w05 = engine.compute_scores(text, cond_w05, emb)

        # weight=0.5 on negative prototype => centroid weighted more toward good
        # This is positive-only, so higher centroid similarity -> higher score
        assert s_w05[0, 0] > s_w1[0, 0], (
            f"Higher weight on good prototype should yield higher score: "
            f"{s_w05[0, 0]} vs {s_w1[0, 0]}"
        )

    def test_weighted_negative_prototypes(self):
        """Weights on negative prototypes affect centroid and thus score."""
        engine = CosineSimilarityEngine(aggregation="centroid", scoring="softmax")
        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)

        pos = _unit(np.array([1.0, 0.0, 0.0, 0.0]))  # cos=1
        neg_strong = _unit(np.array([1.0, 0.0, 0.0, 0.0]))  # cos=1 (same as text!)
        neg_weak = _unit(np.array([-1.0, 0.0, 0.0, 0.0]))  # cos=-1

        # strong negative weight -> lower score (neg centroid closer to text)
        cond_strong = {
            "C": _make_proto_meta(["p", "ns", "nw"], [1, 0, 0], weights=[1.0, 1.0, 0.0])
        }
        cond_weak = {
            "C": _make_proto_meta(["p", "ns", "nw"], [1, 0, 0], weights=[1.0, 0.0, 1.0])
        }

        emb = {"C": np.vstack([pos, neg_strong, neg_weak])}

        s_strong = engine.compute_scores(text, cond_strong, emb)
        s_weak = engine.compute_scores(text, cond_weak, emb)

        # Strong negative (similar to text) -> pushes centroid toward text
        # -> sim_neg higher -> softmax score lower
        assert s_strong[0, 0] < s_weak[0, 0], (
            f"Weighted neg should reduce score more: {s_strong[0, 0]} vs {s_weak[0, 0]}"
        )


class TestNormalizedDifferenceFormula:
    """Tests for the normalized-difference scoring (Eq. 3)."""

    D = 4

    def test_diff_formula_range(self):
        """Diff formula maps [-1,1] cos difference into [0,1]."""
        engine = CosineSimilarityEngine(scoring="diff")
        text = _unit(np.array([1.0, 0.0])).reshape(1, -1)

        # pos=text => cos=1, neg=-text => cos=-1 => diff=2 => score=(2+1)/2=1.5->1
        pos = _unit(np.array([1.0, 0.0]))
        neg = _unit(np.array([-1.0, 0.0]))

        cond = {"C": _make_proto_meta(["p", "n"], [1, 0])}
        emb = {"C": np.vstack([pos, neg])}

        scores = engine.compute_scores(text, cond, emb)
        assert abs(scores[0, 0] - 1.0) < 1e-10

    def test_diff_formula_symmetric(self):
        """Diff formula: swapping positive/negative inverts the score."""
        engine = CosineSimilarityEngine(scoring="diff")
        text = _unit(np.array([0.6, 0.8])).reshape(1, -1)

        pos_vec = _unit(np.array([1.0, 0.0]))  # cos with text = 0.6
        neg_vec = _unit(np.array([0.0, 1.0]))  # cos with text = 0.8

        emb = np.vstack([pos_vec, neg_vec])

        # Normal: first is positive, second is negative
        cond_normal = {"C": _make_proto_meta(["p", "n"], [1, 0])}
        cond_swapped = {"C": _make_proto_meta(["p", "n"], [0, 1])}

        s_normal = engine.compute_scores(text, cond_normal, {"C": emb})
        scores_swapped = engine.compute_scores(text, cond_swapped, {"C": emb})
        # Normal: diff = 0.6 - 0.8 = -0.2 => score = 0.4
        # Swapped: what was positive is now negative so
        # diff = 0.8 - 0.6 = 0.2 => score = 0.6
        assert abs(s_normal[0, 0] + scores_swapped[0, 0] - 1.0) < 1e-10, (
            f"{s_normal[0, 0]} + {scores_swapped[0, 0]} should = 1.0"
        )

    def test_diff_clips_to_unit_interval(self):
        """Diff formula clips output to [0, 1] for extreme cosine differences."""
        engine = CosineSimilarityEngine(scoring="diff")

        # text distinguishes perfectly: cos_pos=1, cos_neg=-1
        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)
        pos = _unit(np.array([1.0, 0.0, 0.0, 0.0]))
        neg = _unit(np.array([-1.0, 0.0, 0.0, 0.0]))

        cond = {"C": _make_proto_meta(["p", "n"], [1, 0])}
        emb = {"C": np.vstack([pos, neg])}

        scores = engine.compute_scores(text, cond, emb)
        # sim_pos=1, sim_neg=-1 => diff=2 => (2+1)/2=1.5 clipped to 1.0
        assert abs(scores[0, 0] - 1.0) < 1e-10

        # Opposite: text=neg, sim_pos=-1, sim_neg=1
        text_opp = (-_unit(np.array([1.0, 0.0, 0.0, 0.0]))).reshape(1, -1)
        scores_opp = engine.compute_scores(text_opp, cond, emb)
        # sim_pos=-1, sim_neg=1 => diff=-2 => (-2+1)/2=-0.5 clipped to 0.0
        assert abs(scores_opp[0, 0] - 0.0) < 1e-10


class TestNumericalStability:
    """Tests for numerical stability edge cases."""

    def test_large_embeddings_no_overflow(self):
        """Large but normalized embeddings should not overflow exp()."""
        engine = CosineSimilarityEngine(temperature=10.0)

        # Very large values (but L2-normalized to unit vectors)
        text = np.full((1, 768), 1.0 / np.sqrt(768), dtype=np.float64)
        pos = np.full((1, 768), 1.0 / np.sqrt(768), dtype=np.float64)
        neg = np.full((1, 768), -1.0 / np.sqrt(768), dtype=np.float64)

        cond = {"C": _make_proto_meta(["p", "n"], [1, 0])}
        emb = {"C": np.vstack([pos, neg])}

        scores = engine.compute_scores(text, cond, emb)
        # sim_pos = 1, sim_neg = -1
        # softmax(10, -10) -> near 1, should not overflow
        assert not np.isnan(scores[0, 0])
        assert not np.isinf(scores[0, 0])
        assert scores[0, 0] > 0.999

    def test_extreme_temperature_no_overflow(self):
        """tau=100 with extreme cosine values should not overflow."""
        engine = CosineSimilarityEngine(temperature=100.0)

        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)
        pos = _unit(np.array([1.0, 0.0, 0.0, 0.0]))
        neg = _unit(np.array([-1.0, 0.0, 0.0, 0.0]))

        cond = {"C": _make_proto_meta(["p", "n"], [1, 0])}
        emb = {"C": np.vstack([pos, neg])}

        scores = engine.compute_scores(text, cond, emb)
        # sim_pos=1, sim_neg=-1, tau=100
        # exp(100) and exp(-100) — stable softmax handles this
        assert not np.isnan(scores[0, 0])
        assert not np.isinf(scores[0, 0])

    def test_near_boundary_embeddings(self):
        """Embeddings near numerical precision boundaries are handled."""
        engine = CosineSimilarityEngine(temperature=5.0)

        # Near-zero (but not exactly zero) text vector
        text = np.full((1, 4), 1e-200, dtype=np.float64)
        pos = _unit(np.array([1.0, 0.0, 0.0, 0.0]))
        neg = _unit(np.array([0.0, 1.0, 0.0, 0.0]))

        cond = {"C": _make_proto_meta(["p", "n"], [1, 0])}
        emb = {"C": np.vstack([pos, neg])}

        scores = engine.compute_scores(text, cond, emb)
        # After normalization, these tiny values may or may not be treated as
        # zero vectors depending on eps threshold. Either way, no crash.
        assert not np.isnan(scores[0, 0])

    def test_random_768d_stable(self):
        """Random 768-dim embeddings never produce NaN or inf."""
        rng = np.random.RandomState(789)
        engine = CosineSimilarityEngine(temperature=5.0)

        text = rng.randn(10, 768).astype(np.float64)
        text = text / np.linalg.norm(text, axis=1, keepdims=True)

        proto_emb = rng.randn(6, 768).astype(np.float64)
        proto_emb = proto_emb / np.linalg.norm(proto_emb, axis=1, keepdims=True)

        cond = {"C": _make_proto_meta([f"p{i}" for i in range(6)], [1, 1, 1, 0, 0, 0])}
        emb = {"C": proto_emb}

        scores = engine.compute_scores(text, cond, emb)
        assert not np.any(np.isnan(scores))
        assert not np.any(np.isinf(scores))
        assert np.all(scores >= 0.0)
        assert np.all(scores <= 1.0)

    def test_softmax_underflow_stable(self):
        """When both exps underflow, fall back to 0.5."""
        engine = CosineSimilarityEngine(temperature=5.0)
        # Both cosine similarities very large negative => both exps -> 0
        text = _unit(np.array([1.0, 0.0])).reshape(1, -1)

        # Create embeddings with very negative cosines
        # text=[1,0], pos=[x, sqrt(1-x^2)] for some x close to -1
        # But cosine can only be -1 min. With tau=5, exp(-5) = 0.0067
        # To underflow, we'd need tau*cos << -745
        # That requires tau=5, cos << -149... not possible with [-1,1] range
        # But the guard is there for safety, test it doesn't crash
        pos = _unit(np.array([-1.0, 0.0]))
        neg = _unit(np.array([-1.0, 0.0]))

        cond = {"C": _make_proto_meta(["p", "n"], [1, 0])}
        emb = {"C": np.vstack([pos, neg])}

        scores = engine.compute_scores(text, cond, emb)
        # Both equal (both cos=-1) => score = 0.5
        assert abs(scores[0, 0] - 0.5) < 1e-10


class TestInputValidation:
    """Input validation and error handling."""

    def test_bad_text_embeddings_shape(self):
        """1D text_embeddings should raise."""
        engine = CosineSimilarityEngine()
        with pytest.raises(ValueError, match="must be 2D"):
            engine.compute_scores(
                np.array([1.0, 0.0]),
                {"C": _make_proto_meta(["p"], [1])},
                {"C": np.array([[1.0, 0.0]])},
            )

    def test_zero_embedding_dimension(self):
        """d=0 embedding dimension raises."""
        engine = CosineSimilarityEngine()
        with pytest.raises(ValueError, match="embedding dimension"):
            engine.compute_scores(
                np.zeros((1, 0), dtype=np.float64),
                {"C": _make_proto_meta(["p"], [1])},
                {"C": np.zeros((1, 0), dtype=np.float64)},
            )

    def test_dimension_mismatch_text_vs_proto(self):
        """Text dimension != prototype dimension raises."""
        engine = CosineSimilarityEngine()
        text = np.random.randn(2, 64).astype(np.float64)
        proto = np.random.randn(1, 128).astype(np.float64)

        with pytest.raises(ValueError, match="embedding dimension"):
            engine.compute_scores(
                text,
                {"C": _make_proto_meta(["p"], [1])},
                {"C": proto},
            )

    def test_prototype_count_mismatch(self):
        """Meta list length != embedding row count raises."""
        engine = CosineSimilarityEngine()
        text = np.random.randn(1, 4).astype(np.float64)
        # 2 rows but metadata only 1 entry
        proto = np.random.randn(2, 4).astype(np.float64)

        with pytest.raises(ValueError, match="prototype count mismatch"):
            engine.compute_scores(
                text,
                {"C": _make_proto_meta(["p"], [1])},
                {"C": proto},
            )

    def test_key_mismatch_between_dicts(self):
        """Different keys in prototype dicts raises."""
        engine = CosineSimilarityEngine()
        text = np.random.randn(1, 4).astype(np.float64)
        proto = np.random.randn(1, 4).astype(np.float64)

        with pytest.raises(ValueError, match="missing"):
            engine.compute_scores(
                text,
                {"C": _make_proto_meta(["p"], [1])},
                {"D": proto},  # different key
            )

    def test_invalid_is_member_value(self):
        """is_member outside {0, 1} raises."""
        engine = CosineSimilarityEngine()
        text = np.random.randn(1, 4).astype(np.float64)
        proto = np.random.randn(1, 4).astype(np.float64)

        with pytest.raises(ValueError, match="is_member"):
            engine.compute_scores(
                text,
                {"C": [{"prototype_text": "x", "is_member": 2, "weight": 1.0}]},
                {"C": proto},
            )

    def test_invalid_weight_value(self):
        """Weight outside [0, 1] raises."""
        engine = CosineSimilarityEngine()
        text = np.random.randn(1, 4).astype(np.float64)
        proto = np.random.randn(1, 4).astype(np.float64)

        with pytest.raises(ValueError, match="weight"):
            engine.compute_scores(
                text,
                {"C": [{"prototype_text": "x", "is_member": 0, "weight": 1.5}]},
                {"C": proto},
            )

    def test_invalid_aggregation(self):
        """Invalid aggregation string raises on init."""
        with pytest.raises(ValueError, match="aggregation"):
            CosineSimilarityEngine(aggregation="median")

    def test_invalid_scoring(self):
        """Invalid scoring string raises on init."""
        with pytest.raises(ValueError, match="scoring"):
            CosineSimilarityEngine(scoring="ratio")

    def test_negative_temperature(self):
        """Negative or zero temperature raises."""
        with pytest.raises(ValueError, match="temperature"):
            CosineSimilarityEngine(temperature=0.0)
        with pytest.raises(ValueError, match="temperature"):
            CosineSimilarityEngine(temperature=-1.0)


class Test768DimRealistic:
    """Integration-style tests with realistic 768-dim BERT-like embeddings."""

    def test_full_workflow_768d(self):
        """Complete end-to-end with 768-dim random embeddings."""
        rng = np.random.RandomState(42)

        # Generate 5 text embeddings
        n_texts = 5
        d = 768
        text_emb = rng.randn(n_texts, d).astype(np.float64)
        text_emb = text_emb / np.linalg.norm(text_emb, axis=1, keepdims=True)

        # 3 conditions with varying prototype counts
        cond_protos = {}
        proto_embs = {}

        # Condition A: 3 positive, 2 negative
        k_a = 5
        proto_a = rng.randn(k_a, d).astype(np.float64)
        proto_a = proto_a / np.linalg.norm(proto_a, axis=1, keepdims=True)
        cond_protos["A"] = _make_proto_meta(
            [f"a{i}" for i in range(k_a)], [1, 1, 1, 0, 0]
        )
        proto_embs["A"] = proto_a

        # Condition B: 1 positive only
        proto_b = rng.randn(1, d).astype(np.float64)
        proto_b = proto_b / np.linalg.norm(proto_b, axis=1, keepdims=True)
        cond_protos["B"] = _make_proto_meta(["b0"], [1])
        proto_embs["B"] = proto_b

        # Condition C: 2 negative only
        proto_c = rng.randn(2, d).astype(np.float64)
        proto_c = proto_c / np.linalg.norm(proto_c, axis=1, keepdims=True)
        cond_protos["C"] = _make_proto_meta(["c0", "c1"], [0, 0])
        proto_embs["C"] = proto_c

        # Test all four engines
        for scoring in ("softmax", "diff"):
            for aggregation in ("centroid", "max"):
                engine = CosineSimilarityEngine(
                    temperature=5.0, aggregation=aggregation, scoring=scoring
                )
                scores = engine.compute_scores(text_emb, cond_protos, proto_embs)
                assert scores.shape == (n_texts, 3)
                assert not np.any(np.isnan(scores))
                assert not np.any(np.isinf(scores))
                assert np.all(scores >= 0.0)
                assert np.all(scores <= 1.0)

    def test_deterministic_output(self):
        """Same inputs should always produce same outputs."""
        rng = np.random.RandomState(0)
        text = rng.randn(4, 768).astype(np.float64)
        text = text / np.linalg.norm(text, axis=1, keepdims=True)
        proto = rng.randn(3, 768).astype(np.float64)
        proto = proto / np.linalg.norm(proto, axis=1, keepdims=True)

        cond = {"X": _make_proto_meta(["a", "b", "c"], [1, 1, 0])}
        emb = {"X": proto}

        engine = CosineSimilarityEngine(temperature=5.0)
        scores1 = engine.compute_scores(text, cond, emb)
        scores2 = engine.compute_scores(text, cond, emb)

        np.testing.assert_array_equal(scores1, scores2)

    def test_scores_monotonic_in_cosine(self):
        """If text A is more similar to pos prototype than text B, score_A > score_B."""
        engine = CosineSimilarityEngine(temperature=5.0, aggregation="max")

        # Exact match vs random
        pos = _unit(np.array([1.0] + [0.0] * 767)).reshape(1, -1)
        neg = _unit(np.array([-1.0] + [0.0] * 767)).reshape(1, -1)

        text_near = pos.copy()  # exact match to pos
        rng = np.random.RandomState(1)
        text_far = rng.randn(1, 768).astype(np.float64)
        text_far = text_far / np.linalg.norm(text_far, axis=1, keepdims=True)

        text_both = np.vstack([text_near, text_far])

        cond = {"C": _make_proto_meta(["p", "n"], [1, 0])}
        emb = {"C": np.vstack([pos, neg])}

        scores = engine.compute_scores(text_both, cond, emb)
        assert scores[0, 0] > scores[1, 0], (
            f"Near-match (row 0) should outscore random (row 1): "
            f"{scores[0, 0]} vs {scores[1, 0]}"
        )


class TestNegativeTemperatureEdgeCase:
    """Edge cases around temperature and cosine behavior."""

    def test_negative_cosine_with_positive_only(self):
        """Positive-only with negative cos => score in [0, 0.5)."""
        engine = CosineSimilarityEngine()

        # text opposite to the only positive prototype
        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)
        pos = _unit(np.array([-1.0, 0.0, 0.0, 0.0]))  # cos = -1

        cond = {"C": _make_proto_meta(["p"], [1])}
        emb = {"C": np.vstack([pos])}

        scores = engine.compute_scores(text, cond, emb)
        # (cos + 1)/2 = (-1 + 1)/2 = 0
        assert abs(scores[0, 0] - 0.0) < 1e-10

    def test_negative_cosine_with_negative_only(self):
        """Negative-only with negative cos => score in (0.5, 1]."""
        engine = CosineSimilarityEngine()

        # text opposite to the only negative prototype
        text = _unit(np.array([1.0, 0.0, 0.0, 0.0])).reshape(1, -1)
        neg = _unit(np.array([-1.0, 0.0, 0.0, 0.0]))  # cos = -1

        cond = {"C": _make_proto_meta(["n"], [0])}
        emb = {"C": np.vstack([neg])}

        scores = engine.compute_scores(text, cond, emb)
        # (1 - cos)/2 = (1 - (-1))/2 = 1
        assert abs(scores[0, 0] - 1.0) < 1e-10
