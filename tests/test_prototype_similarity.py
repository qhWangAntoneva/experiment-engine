"""Unit tests for prototype-based text similarity engine."""

from __future__ import annotations

import numpy as np
import pytest

from experiment_engine.models import (
    CalibrationParams,
    CalibrationType,
    ConceptPrototype,
    ConditionDefinition,
    ConditionSet,
    ScoringSource,
    TextCase,
    TextDomain,
)
from experiment_engine.text_calibration.prototype_similarity import (
    PrototypeSimilarityEngine,
)


class TestJaccardSimilarity:
    """Tests for the _jaccard helper and overall similarity computation."""

    def test_jaccard_identical_sets(self):
        """Identical bigram sets should return 1.0."""
        engine = PrototypeSimilarityEngine()
        a = {"ab", "bc", "cd"}
        b = {"ab", "bc", "cd"}
        assert engine._jaccard(a, b) == 1.0

    def test_jaccard_disjoint_sets(self):
        """Completely different bigram sets should return 0.0."""
        engine = PrototypeSimilarityEngine()
        a = {"ab", "bc"}
        b = {"xy", "yz"}
        assert engine._jaccard(a, b) == 0.0

    def test_jaccard_partial_overlap(self):
        """Partially overlapping sets should return 0 < sim < 1."""
        engine = PrototypeSimilarityEngine()
        a = {"ab", "bc", "cd"}
        b = {"ab", "bc", "de"}
        # intersection=2, union=4 → 0.5
        assert engine._jaccard(a, b) == 0.5

    def test_jaccard_empty_set(self):
        """Empty set should return 0.0."""
        engine = PrototypeSimilarityEngine()
        assert engine._jaccard(set(), {"ab"}) == 0.0
        assert engine._jaccard({"ab"}, set()) == 0.0
        assert engine._jaccard(set(), set()) == 0.0


class TestPrototypeSimilarityEngine:
    """Tests for the main PrototypeSimilarityEngine class."""

    @pytest.fixture
    def engine(self):
        return PrototypeSimilarityEngine()

    @pytest.fixture
    def sample_texts(self):
        return [
            "服务态度非常差，投诉多次都没有回应",
            "处理速度很快，工作人员态度很好",
            "政策执行高效，群众满意度高",
            "效率低下，完全没有人处理我的问题",
        ]

    @pytest.fixture
    def neg_proto(self):
        return ConceptPrototype(
            prototype_text="服务态度差投诉无门效率极低",
            is_member=1,
            weight=1.0,
        )

    @pytest.fixture
    def pos_proto(self):
        return ConceptPrototype(
            prototype_text="处理速度快态度好群众满意",
            is_member=1,
            weight=1.0,
        )

    def test_empty_texts(self, engine, neg_proto):
        """Empty text list returns zero matrix."""
        proto_map = {"bad_service": [neg_proto]}
        result = engine.compute_similarities([], proto_map)
        assert result.shape == (0, 1)

    def test_empty_conditions(self, engine):
        """Empty condition map returns zero-column matrix."""
        result = engine.compute_similarities(["some text"], {})
        assert result.shape == (1, 0)

    def test_single_positive_prototype(self, engine, sample_texts, neg_proto):
        """Texts similar to a negative-experience prototype should score high."""
        proto_map = {"bad_service": [neg_proto]}
        result = engine.compute_similarities(sample_texts, proto_map)
        assert result.shape == (4, 1)
        # Text 0 and 3 are negative → should score higher than text 1 and 2
        assert result[0, 0] > result[1, 0], (
            f"Negative text should score higher than positive text: "
            f"{result[0, 0]} vs {result[1, 0]}"
        )
        assert result[3, 0] > result[2, 0]

    def test_positive_and_negative_prototypes(self, engine, sample_texts):
        """Positive prototypes should increase score, negative should decrease."""
        pos_proto = ConceptPrototype(
            prototype_text="处理速度快态度好群众满意",
            is_member=1,
        )
        neg_proto = ConceptPrototype(
            prototype_text="服务态度差投诉无门效率极低",
            is_member=0,
        )
        proto_map = {"good_service": [pos_proto, neg_proto]}
        result = engine.compute_similarities(sample_texts, proto_map)
        assert result.shape == (4, 1)
        # Text 1 is positive → should score high because of positive prototype
        # and benefit from NOT being similar to negative prototype
        assert result[1, 0] > result[0, 0], (
            f"Positive text should score higher than negative text with good+"
            f"bad prototypes: {result[1, 0]} vs {result[0, 0]}"
        )

    def test_negative_proto_reduces_score(self, engine, sample_texts):
        """A negative prototype (is_member=0) should reduce the score."""
        pos = ConceptPrototype(
            prototype_text="处理速度快态度好",
            is_member=1,
        )
        neg = ConceptPrototype(
            prototype_text="服务态度差投诉无门效率极低",
            is_member=0,
        )
        # With only positive
        result_pos_only = engine.compute_similarities(sample_texts, {"cond": [pos]})
        # With positive + negative
        result_with_neg = engine.compute_similarities(
            sample_texts, {"cond": [pos, neg]}
        )
        # Score for negative text (index 0) should be lower with negative proto
        assert result_with_neg[0, 0] < result_pos_only[0, 0], (
            f"Negative prototype should reduce score for negative-leaning text: "
            f"{result_with_neg[0, 0]} vs {result_pos_only[0, 0]}"
        )

    def test_scores_in_range(self, engine, sample_texts):
        """All scores should be in [0, 1]."""
        pos = ConceptPrototype(
            prototype_text="处理速度快态度好群众满意",
            is_member=1,
        )
        neg = ConceptPrototype(
            prototype_text="服务态度差投诉无门",
            is_member=1,
        )
        proto_map = {"cond1": [pos], "cond2": [neg]}
        result = engine.compute_similarities(sample_texts, proto_map)
        assert np.all(result >= 0.0), "Scores should be >= 0"
        assert np.all(result <= 1.0), "Scores should be <= 1"

    def test_multiple_conditions(self, engine, sample_texts):
        """Multiple conditions should produce a (n_texts, n_conds) matrix."""
        proto1 = ConceptPrototype(
            prototype_text="服务态度差投诉无门",
            is_member=1,
        )
        proto2 = ConceptPrototype(
            prototype_text="处理速度快群众满意",
            is_member=1,
        )
        proto_map = {
            "dissatisfaction": [proto1],
            "good_service": [proto2],
        }
        result = engine.compute_similarities(sample_texts, proto_map)
        assert result.shape == (4, 2)

    def test_score_non_negative(self, engine, sample_texts):
        """Score should never go below 0 even with strong negative prototypes."""
        # All prototypes are negative → max_pos = 0, but score floor is 0
        neg = ConceptPrototype(
            prototype_text="处理速度快态度好群众满意",
            is_member=0,
        )
        result = engine.compute_similarities(sample_texts, {"cond": [neg]})
        assert np.all(result >= 0.0)


class TestPrototypeCalibrationIntegration:
    """Integration tests for prototype-based calibration via TextCalibrationStage."""

    def test_prototype_calibration_produces_fuzzy_data(self):
        """Calibrating with prototype condition set produces valid FuzzySetData."""
        from experiment_engine.models import InputData
        from experiment_engine.text_calibration.calibrator import (
            TextCalibrationStage,
        )

        condition_set = ConditionSet(
            name="test_prototype",
            scoring_source=ScoringSource.PROTOTYPE,
            conditions=[
                ConditionDefinition(
                    name="negative_experience",
                    display_name="负面体验",
                    domain=TextDomain.DISSATISFACTION,
                    scoring_source=ScoringSource.PROTOTYPE,
                    calibration_type=CalibrationType.DIRECT,
                    calibration_params=CalibrationParams(
                        threshold_full_in=0.80,
                        threshold_full_out=0.20,
                        crossover_point=0.50,
                    ),
                    prototypes=[
                        ConceptPrototype(
                            prototype_text="服务态度差投诉无门效率极低",
                            is_member=1,
                        ),
                        ConceptPrototype(
                            prototype_text="处理速度快态度好群众满意",
                            is_member=0,
                        ),
                    ],
                ),
            ],
            outcome=ConditionDefinition(
                name="outcome",
                display_name="结果",
                domain=TextDomain.DISSATISFACTION,
                scoring_source=ScoringSource.PROTOTYPE,
                calibration_type=CalibrationType.PASSTHROUGH,
            ),
        )

        texts = [
            "这个部门服务态度非常差，投诉多次没有回应",  # negative
            "处理速度快，工作人员态度很好，问题解决了",  # positive
        ]

        stage = TextCalibrationStage(condition_set=condition_set)
        stage.setup()

        data = InputData(data=np.array(texts, dtype=object))
        result = stage.process(data)

        fuzzy = result.processed
        assert fuzzy is not None
        assert fuzzy.n_cases == 2
        assert fuzzy.n_conditions == 1  # 1 causal condition + 1 outcome
        # Negative text should have higher membership in negative_experience
        membership = fuzzy.condition_matrix
        assert membership[0, 0] > membership[1, 0], (
            f"Text 0 (negative) should score higher than text 1 (positive) "
            f"on 'negative_experience': {membership[0, 0]} vs {membership[1, 0]}"
        )

    def test_prototype_calibration_with_outcome(self):
        """process_with_outcome uses provided binary outcome directly."""
        from experiment_engine.models import InputData
        from experiment_engine.text_calibration.calibrator import (
            TextCalibrationStage,
        )

        condition_set = ConditionSet(
            name="test_with_outcome",
            scoring_source=ScoringSource.PROTOTYPE,
            conditions=[
                ConditionDefinition(
                    name="cond_a",
                    display_name="条件A",
                    domain=TextDomain.DISSATISFACTION,
                    scoring_source=ScoringSource.PROTOTYPE,
                    calibration_type=CalibrationType.PASSTHROUGH,
                    prototypes=[
                        ConceptPrototype(
                            prototype_text="服务态度差投诉无门",
                            is_member=1,
                        ),
                    ],
                ),
            ],
            outcome=ConditionDefinition(
                name="response_effective",
                display_name="回应有效",
                domain=TextDomain.GOV_RESPONSIVENESS,
                scoring_source=ScoringSource.PROTOTYPE,
                calibration_type=CalibrationType.PASSTHROUGH,
            ),
        )

        texts = ["投诉多次没有回应", "处理速度快很满意"]
        outcomes = np.array([0.0, 1.0], dtype=np.float64)

        stage = TextCalibrationStage(condition_set=condition_set)
        stage.setup()

        data = InputData(data=np.array(texts, dtype=object))
        result = stage.process_with_outcome(data, outcomes)

        fuzzy = result.processed
        assert fuzzy is not None
        # Outcome column should match the provided binary outcomes
        outcome_col = fuzzy.membership[:, 1]  # last column is outcome
        assert outcome_col[0] == 0.0, f"Expected 0.0, got {outcome_col[0]}"
        assert outcome_col[1] == 1.0, f"Expected 1.0, got {outcome_col[1]}"

    def test_passthrough_calibration_type(self):
        """PASSTHROUGH calibration preserves raw scores unchanged."""
        from experiment_engine.text_calibration.calibrator import (
            TextCalibrationStage,
        )

        raw = np.array([0.3, 0.7, 0.0, 1.0], dtype=np.float64)
        params = CalibrationParams(
            threshold_full_in=0.80,
            threshold_full_out=0.20,
            crossover_point=0.50,
        )
        result = TextCalibrationStage._apply_calibration(
            raw, CalibrationType.PASSTHROUGH, params
        )
        np.testing.assert_array_equal(raw, result)

    def test_keyword_mode_unchanged(self):
        """Keyword-based calibration should still work identically."""
        from experiment_engine.models import InputData, KeywordEntry
        from experiment_engine.text_calibration.calibrator import (
            TextCalibrationStage,
        )

        condition_set = ConditionSet(
            name="keyword_test",
            scoring_source=ScoringSource.KEYWORD,
            conditions=[
                ConditionDefinition(
                    name="negative_affect",
                    display_name="负面情感",
                    domain=TextDomain.DISSATISFACTION,
                    scoring_source=ScoringSource.KEYWORD,
                    calibration_type=CalibrationType.DIRECT,
                    calibration_params=CalibrationParams(
                        threshold_full_in=0.80,
                        threshold_full_out=0.20,
                        crossover_point=0.50,
                    ),
                    keywords=[
                        KeywordEntry(pattern="投诉", weight=1.0, scope="bigram"),
                        KeywordEntry(pattern="不满", weight=1.0, scope="bigram"),
                    ],
                ),
            ],
            outcome=ConditionDefinition(
                name="outcome",
                display_name="结果",
                domain=TextDomain.DISSATISFACTION,
                calibration_type=CalibrationType.PASSTHROUGH,
            ),
        )

        texts = ["投诉多次不满", "处理快满意"]
        stage = TextCalibrationStage(condition_set=condition_set)
        stage.setup()

        data = InputData(data=np.array(texts, dtype=object))
        result = stage.process(data)

        fuzzy = result.processed
        assert fuzzy is not None
        assert fuzzy.n_cases == 2
        # Keyword "投诉" and "不满" should match text 0
        membership = fuzzy.condition_matrix
        assert membership[0, 0] > membership[1, 0]


class TestTextCaseModel:
    """Tests for the TextCase model."""

    def test_text_case_creation(self):
        tc = TextCase(text_id="001", text="服务态度差", outcome=0)
        assert tc.text_id == "001"
        assert tc.text == "服务态度差"
        assert tc.outcome == 0

    def test_text_case_outcome_range(self):
        """Outcome must be 0 or 1."""
        TextCase(text_id="1", text="test", outcome=0)
        TextCase(text_id="1", text="test", outcome=1)
        with pytest.raises(Exception):
            TextCase(text_id="1", text="test", outcome=2)
        with pytest.raises(Exception):
            TextCase(text_id="1", text="test", outcome=-1)


class TestConceptPrototypeModel:
    """Tests for the ConceptPrototype model."""

    def test_concept_prototype_creation(self):
        cp = ConceptPrototype(
            prototype_text="服务态度差投诉无门",
            is_member=1,
            weight=1.0,
        )
        assert cp.prototype_text == "服务态度差投诉无门"
        assert cp.is_member == 1
        assert cp.weight == 1.0

    def test_concept_prototype_is_member_range(self):
        ConceptPrototype(prototype_text="test", is_member=0)
        ConceptPrototype(prototype_text="test", is_member=1)
        with pytest.raises(Exception):
            ConceptPrototype(prototype_text="test", is_member=2)
