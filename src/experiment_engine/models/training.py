"""Training-related models — labeled samples and training datasets.

These models bridge raw text data and the calibration pipeline: labeled
training samples encode human-annotated fuzzy-set scores, and
TrainingDataset collects them for supervised threshold estimation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from experiment_engine.models.qca import TextDomain


class TrainingSample(BaseModel):
    """A single labeled training sample mapping text to fuzzy-set scores.

    Attributes:
        text_id: Unique identifier for the text.
        text: The raw Chinese text content.
        labeled_scores: Dict mapping condition_name -> fuzzy membership (0-1).
        domain: Optional text domain override.
        metadata: Arbitrary additional metadata.
    """

    text_id: str
    text: str
    labeled_scores: dict[str, float] = Field(default_factory=dict)
    domain: TextDomain | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("labeled_scores")
    @classmethod
    def scores_in_range(cls, v: dict[str, float]) -> dict[str, float]:
        for key, val in v.items():
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"Score for '{key}' is {val}, must be in [0, 1]")
        return v


class TrainingDataset(BaseModel):
    """Collection of labeled training samples.

    Attributes:
        samples: List of training samples.
        condition_names: Names of conditions in the labeled_scores dict.
        outcome_name: Name of the outcome condition.
    """

    samples: list[TrainingSample] = Field(default_factory=list)
    condition_names: list[str] = Field(default_factory=list)
    outcome_name: str = ""

    @property
    def n_samples(self) -> int:
        return len(self.samples)
