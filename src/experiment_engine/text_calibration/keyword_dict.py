"""Chinese keyword matching engine using character n-gram tokenization.

No external NLP dependencies required — tokenization uses sliding-window
character n-grams (unigram, bigram, trigram) on Chinese text.
"""

from __future__ import annotations

import re

import numpy as np

from experiment_engine.models import KeywordEntry


class KeywordMatcher:
    """Low-level Chinese text tokenizer and keyword scorer.

    Since the constraint is pure Python + numpy only (no jieba), tokenization
    uses character n-gram sliding windows. For Chinese text, bigrams are the
    most effective default as most meaningful words are 2 characters.
    """

    # Punctuation and whitespace regex for pre-cleaning
    _CLEAN_PATTERN = re.compile(r"[，。！？、；：" r"''（）【】《》\s]+")

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove Chinese punctuation and normalize whitespace."""
        return KeywordMatcher._CLEAN_PATTERN.sub("", text).strip()

    @staticmethod
    def tokenize(text: str, method: str = "bigram") -> list[str]:
        """Tokenize Chinese text using character n-grams.

        Args:
            text: Raw Chinese text.
            method: One of 'unigram', 'bigram', 'trigram'.

        Returns:
            List of n-gram tokens.
        """
        cleaned = KeywordMatcher.clean_text(text)
        if not cleaned:
            return []

        n: int
        if method == "unigram":
            n = 1
        elif method == "trigram":
            n = 3
        else:
            n = 2  # bigram default

        if len(cleaned) < n:
            return [cleaned]

        return [cleaned[i : i + n] for i in range(len(cleaned) - n + 1)]

    @staticmethod
    def _count_matches(text: str, entries: list[KeywordEntry]) -> float:
        """Compute weighted match score for a list of keyword entries against text.

        For each keyword entry, its pattern is searched in the text using
        the specified scope (exact substring, regex, or n-gram token matching).
        The score is sum(weight * match_count), capped for reasonable scaling.
        """
        total = 0.0
        for entry in entries:
            count = 0
            if entry.scope == "regex":
                try:
                    count = len(re.findall(entry.pattern, text))
                except re.error:
                    count = 0
            elif entry.scope == "exact":
                count = text.count(entry.pattern)
            else:
                # n-gram based: tokenize both text and pattern
                tokens = KeywordMatcher.tokenize(text, method=entry.scope)
                pattern_tokens = KeywordMatcher.tokenize(
                    entry.pattern, method=entry.scope
                )
                if pattern_tokens:
                    # Count occurrences of the n-gram sequence in text tokens
                    p0 = pattern_tokens[0]
                    for j in range(len(tokens) - len(pattern_tokens) + 1):
                        if tokens[j] == p0:
                            match = True
                            for k in range(1, len(pattern_tokens)):
                                if tokens[j + k] != pattern_tokens[k]:
                                    match = False
                                    break
                            if match:
                                count += 1
            total += entry.weight * count
        return total

    @staticmethod
    def score_single(text: str, entries: list[KeywordEntry]) -> float:
        """Score a single text against a list of keyword entries.

        The raw score is the sum of weighted keyword match counts. This is
        a pre-calibration score; the TextCalibrationStage applies the fuzzy
        membership transformation.

        Args:
            text: The Chinese text to score.
            entries: List of keyword entries with weights.

        Returns:
            Raw score (non-negative float, typically 0 to ~20 for normal texts).
        """
        return KeywordMatcher._count_matches(text, entries)


class ChineseKeywordDictionary:
    """Manages keyword dictionaries for multiple QCA conditions.

    Provides batch matching across texts for all conditions simultaneously,
    returning a raw score matrix ready for calibration.
    """

    def __init__(self) -> None:
        self._conditions: dict[str, list[KeywordEntry]] = {}

    def add_condition(self, name: str, entries: list[KeywordEntry]) -> None:
        """Register a condition with its keyword entries."""
        self._conditions[name] = list(entries)

    def remove_condition(self, name: str) -> None:
        """Remove a condition from the dictionary."""
        self._conditions.pop(name, None)

    @property
    def condition_names(self) -> list[str]:
        return list(self._conditions.keys())

    def load_from_conditions(
        self,
        conditions: list[ConditionDefinition],  # noqa: F821
    ) -> None:
        """Load keyword entries from a list of ConditionDefinition objects."""
        for cond in conditions:
            self.add_condition(cond.name, cond.keywords)

    def match_text(self, text: str) -> dict[str, float]:
        """Match a single text against all registered conditions.

        Returns:
            Dict mapping condition_name → raw keyword score.
        """
        return {
            name: KeywordMatcher.score_single(text, entries)
            for name, entries in self._conditions.items()
        }

    def match_corpus(self, texts: list[str]) -> np.ndarray:
        """Match all texts against all conditions.

        Args:
            texts: List of Chinese text strings.

        Returns:
            numpy array of shape (n_texts, n_conditions) with raw keyword scores.
        """
        n_texts = len(texts)
        n_conds = len(self._conditions)
        matrix = np.zeros((n_texts, n_conds), dtype=np.float64)
        names = list(self._conditions.keys())

        for i, text in enumerate(texts):
            for j, name in enumerate(names):
                matrix[i, j] = KeywordMatcher.score_single(text, self._conditions[name])

        return matrix
