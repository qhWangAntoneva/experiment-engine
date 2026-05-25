"""Text calibration layer: raw text → fuzzy-set membership scores."""

from experiment_engine.text_calibration.calibrator import TextCalibrationStage
from experiment_engine.text_calibration.condition import (
    ConditionDefinitionBuilder,
    ConditionSetBuilder,
    load_condition_set,
    save_condition_set,
)
from experiment_engine.text_calibration.cosine_similarity import (
    CosineSimilarityEngine,
)
from experiment_engine.text_calibration.domains import (
    DOMAIN_PRESETS,
    build_default_conditions,
)
from experiment_engine.text_calibration.keyword_dict import (
    ChineseKeywordDictionary,
    KeywordMatcher,
)
from experiment_engine.text_calibration.keyword_io import (
    export_keywords_csv,
    export_keywords_json,
    import_keywords_csv,
    import_keywords_json,
)
from experiment_engine.text_calibration.prototype_similarity import (
    PrototypeSimilarityEngine,
)
from experiment_engine.text_calibration.strategies import (
    CalibrationStrategy,
    CalibrationStrategyRegistry,
    CrispCalibration,
    DirectCalibration,
    IndirectCalibration,
    PassthroughCalibration,
    RaginCalibration,
)
from experiment_engine.text_calibration.training import TrainingEngine

__all__ = [
    "DOMAIN_PRESETS",
    "CalibrationStrategy",
    "CalibrationStrategyRegistry",
    "ChineseKeywordDictionary",
    "ConditionDefinitionBuilder",
    "ConditionSetBuilder",
    "CosineSimilarityEngine",
    "CrispCalibration",
    "DirectCalibration",
    "IndirectCalibration",
    "KeywordMatcher",
    "PassthroughCalibration",
    "PrototypeSimilarityEngine",
    "RaginCalibration",
    "TextCalibrationStage",
    "TrainingEngine",
    "build_default_conditions",
    "export_keywords_csv",
    "export_keywords_json",
    "import_keywords_csv",
    "import_keywords_json",
    "load_condition_set",
    "save_condition_set",
]
