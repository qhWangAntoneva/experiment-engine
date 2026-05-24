"""Text calibration layer: raw text → fuzzy-set membership scores."""

from experiment_engine.text_calibration.calibrator import TextCalibrationStage
from experiment_engine.text_calibration.condition import (
    ConditionDefinitionBuilder,
    ConditionSetBuilder,
    load_condition_set,
    save_condition_set,
)
from experiment_engine.text_calibration.domains import (
    DOMAIN_PRESETS,
    build_default_conditions,
)
from experiment_engine.text_calibration.keyword_dict import (
    ChineseKeywordDictionary,
    KeywordMatcher,
)
from experiment_engine.text_calibration.prototype_similarity import (
    PrototypeSimilarityEngine,
)
from experiment_engine.text_calibration.training import TrainingEngine

__all__ = [
    "DOMAIN_PRESETS",
    "ChineseKeywordDictionary",
    "ConditionDefinitionBuilder",
    "ConditionSetBuilder",
    "KeywordMatcher",
    "PrototypeSimilarityEngine",
    "TextCalibrationStage",
    "TrainingEngine",
    "build_default_conditions",
    "load_condition_set",
    "save_condition_set",
]
