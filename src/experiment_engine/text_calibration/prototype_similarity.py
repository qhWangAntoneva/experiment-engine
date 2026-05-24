"""Prototype-based text similarity engine for QCA fuzzy-set calibration.

Uses character n-gram Jaccard similarity to measure how similar a text is
to concept prototypes. Positive prototypes (is_member=1) contribute positively
to the score; negative prototypes (is_member=0) act as a penalty baseline.
"""

from __future__ import annotations

import numpy as np

from experiment_engine.models import ConceptPrototype
from experiment_engine.text_calibration.keyword_dict import KeywordMatcher


class PrototypeSimilarityEngine:
    """Computes text-to-prototype similarity for fuzzy-set scoring.

    Algorithm:
    1. Tokenize all prototypes and target texts into character bigrams.
    2. For each (text, condition) pair:
       a. Compute Jaccard similarity between text bigram set and each prototype.
       b. Aggregate positive and negative prototype similarities separately.
       c. Final score = max(0, max_pos_sim - max_neg_sim).

    This gives a score in [0, 1] where:
    - 1.0: text is very similar to a positive prototype, unlike any negative
    - 0.0: text is similar to a negative prototype, unlike any positive
    - 0.5: equal similarity to positive and negative prototypes
    """

    def __init__(self, n_gram: str = "bigram") -> None:
        self._n_gram = n_gram

    def compute_similarities(
        self,
        texts: list[str],
        condition_prototypes: dict[str, list[ConceptPrototype]],
    ) -> np.ndarray:
        """Compute prototype similarity matrix.

        Args:
            texts: List of target Chinese texts.
            condition_prototypes: Dict mapping condition_name -> list of prototypes.

        Returns:
            ndarray of shape (n_texts, n_conditions) with scores in [0, 1].
        """
        condition_names = list(condition_prototypes.keys())
        n_texts = len(texts)
        n_conds = len(condition_names)

        if n_conds == 0:
            return np.zeros((n_texts, 0), dtype=np.float64)

        # Pre-tokenize all texts into bigram sets
        text_bigram_sets = [self._text_to_bigram_set(t) for t in texts]

        scores = np.zeros((n_texts, n_conds), dtype=np.float64)

        for j, cond_name in enumerate(condition_names):
            prototypes = condition_prototypes[cond_name]
            pos_protos = [p for p in prototypes if p.is_member == 1]
            neg_protos = [p for p in prototypes if p.is_member == 0]

            # Tokenize prototypes
            pos_bigram_sets = [
                self._text_to_bigram_set(p.prototype_text) for p in pos_protos
            ]
            neg_bigram_sets = [
                self._text_to_bigram_set(p.prototype_text) for p in neg_protos
            ]

            for i, text_bigrams in enumerate(text_bigram_sets):
                pos_sim = self._max_similarity(text_bigrams, pos_bigram_sets)
                neg_sim = self._max_similarity(text_bigrams, neg_bigram_sets)
                scores[i, j] = max(0.0, pos_sim - neg_sim)

        return scores

    def _text_to_bigram_set(self, text: str) -> set[str]:
        """Tokenize text into a set of bigrams."""
        tokens = KeywordMatcher.tokenize(text, method=self._n_gram)
        return set(tokens)

    @staticmethod
    def _max_similarity(
        text_bigrams: set[str], proto_bigram_sets: list[set[str]]
    ) -> float:
        """Return max Jaccard similarity between text and any prototype.

        Returns 0.0 if no prototypes provided.
        """
        if not proto_bigram_sets:
            return 0.0
        return max(
            PrototypeSimilarityEngine._jaccard(text_bigrams, pb)
            for pb in proto_bigram_sets
        )

    @staticmethod
    def _jaccard(set_a: set[str], set_b: set[str]) -> float:
        """Compute Jaccard similarity between two sets."""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0
