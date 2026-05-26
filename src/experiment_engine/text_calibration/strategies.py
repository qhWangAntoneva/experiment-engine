"""Calibration strategy pattern — pluggable membership calibration algorithms.

Each strategy implements a specific calibration method (direct piecewise-linear,
indirect log-odds, Ragin logistic, crisp-set threshold, passthrough). The
CalibrationStrategyRegistry maps CalibrationMethod enum values to strategy
instances, enabling new calibration methods to be added without modifying the
TextCalibrationStage.

References:
    - HACK-6: Resolved — replaces hardcoded if/elif dispatch with strategy pattern.
    - TODO P1-15
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

import numpy as np

from experiment_engine.models import CalibrationMethod, CalibrationParams


class CalibrationStrategy(ABC):
    """Abstract base class for fuzzy-set calibration strategies.

    Each concrete strategy maps raw keyword/prototype scores (float ndarray)
    to fuzzy-set membership values in [0, 1] using a specific mathematical
    transformation controlled by CalibrationParams.
    """

    @abstractmethod
    def calibrate(
        self, raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        """Transform raw scores into fuzzy-set membership values.

        Args:
            raw_scores: 1D numpy array of raw scores (keyword match counts,
                prototype similarities, etc.).
            params: Threshold and direction parameters controlling the
                calibration mapping.

        Returns:
            1D numpy array of fuzzy membership values in [0, 1].
        """
        ...


class DirectCalibration(CalibrationStrategy):
    """Piecewise linear fuzzy membership calibration.

    Membership = 0 if normalized_score <= full_out,
                1 if normalized_score >= full_in,
                linear interpolation between crossover and thresholds otherwise.

    Raw scores are first min-max normalized to [0, 1].

    .. note::
        Min-max normalization makes calibration thresholds relative to the
        empirical distribution of raw scores, not absolute values.  When raw
        scores are already naturally bounded to [0, 1] (e.g. BERT cosine
        similarities), the normalization is a no-op.  When raw scores come
        from keyword matching (which can produce values > 1), the
        normalization maps the observed range onto [0, 1], so the user's
        ``full_in`` / ``full_out`` / ``crossover`` thresholds refer to
        percentiles of the sample, not absolute keyword scores.  This
        follows the *degree of membership* principle of Ragin (2008) where
        membership is defined relative to the empirical evidence, but users
        should be aware that absolute thresholds have no fixed meaning
        across datasets of different score ranges.

    Uses numpy vectorized np.select for WASM performance.
    """

    def calibrate(
        self, raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        lo = params.threshold_full_out
        hi = params.threshold_full_in
        cross = params.crossover_point

        # Normalize raw scores to [0, 1] via min-max scaling
        score_min = float(np.min(raw_scores))
        score_max = float(np.max(raw_scores))
        if score_max > score_min:
            normalized = (raw_scores - score_min) / (score_max - score_min)
        else:
            normalized = np.full_like(raw_scores, 0.5)

        # Guard against degenerate anchors: if thresholds collapse,
        # all points lie in the same region and the for-loop fallback
        # would assign everything to either 0.0 or 1.0 depending on
        # which threshold is degenerate.
        denom_low = cross - lo
        denom_hi = hi - cross

        # Vectorized piecewise linear transformation using np.select.
        # Conditions match the original if/elif/else order exactly:
        #   1. s <= lo          -> 0.0
        #   2. s >= hi          -> 1.0
        #   3. s <= cross       -> 0.5 * (s - lo) / (cross - lo)
        #   4. otherwise        -> 0.5 + 0.5 * (s - cross) / (hi - cross)
        #
        # NaN propagates correctly: all NaN comparisons are False,
        # so NaN falls through to the default (choice 4), which
        # produces NaN — matching the original for-loop behaviour.
        condlist: list[np.ndarray] = [
            normalized <= lo,
            normalized >= hi,
            normalized <= cross,
        ]
        choicelist: list[np.ndarray | float] = [
            0.0,
            1.0,
            (
                0.5 * (normalized - lo) / denom_low
                if denom_low > 0
                else np.full_like(normalized, 0.0)
            ),
        ]
        default_val: np.ndarray | float = (
            0.5 + 0.5 * (normalized - cross) / denom_hi
            if denom_hi > 0
            else np.full_like(normalized, 0.5)
        )

        with np.errstate(divide="ignore", invalid="ignore"):
            out = np.select(condlist, choicelist, default=default_val)

        if params.direction == "descending":
            out = 1.0 - out

        return out.astype(np.float64)


class IndirectCalibration(CalibrationStrategy):
    """Log-odds based indirect calibration.

    Rescales raw scores to [0, 1] via min-max normalization, then applies
    a logistic transformation centered at the crossover point to produce
    fuzzy membership values in [0, 1].

    Uses numpy vectorized operations for WASM performance.
    """

    def calibrate(
        self, raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        score_min = float(np.min(raw_scores))
        score_max = float(np.max(raw_scores))
        if score_max > score_min:
            normalized = (raw_scores - score_min) / (score_max - score_min)
        else:
            normalized = np.full_like(raw_scores, 0.5)

        # Logistic: map [0,1] through log-odds centered at crossover
        cross = params.crossover_point
        k = params.steepness if params.steepness is not None else 10.0

        # Pre-compute crossover log-odds (constant across all elements)
        cross_log_odds = float(np.log(cross / (1.0 - cross))) if 0 < cross < 1 else 0.0

        # Vectorized: replace the original if/elif/else for-loop with
        # np.select. Conditions match the original logic:
        #   1. s <= 0.0  -> 0.0
        #   2. s >= 1.0  -> 1.0
        #   3. otherwise -> logistic(log_odds(s))
        #
        # NaN: all three comparison conditions are False, so NaN falls
        # through to the default where log_odds=0.0 (matching the
        # original for-loop's "else: if s>0 and s<1 else 0.0" behaviour).
        mask_mid = (normalized > 0.0) & (normalized < 1.0)
        with np.errstate(divide="ignore", invalid="ignore"):
            log_odds = np.where(
                mask_mid,
                np.log(normalized / (1.0 - normalized)),
                0.0,
            )
        logistic_val = 1.0 / (1.0 + np.exp(-k * (log_odds - cross_log_odds)))

        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.select(
                [normalized <= 0.0, normalized >= 1.0],
                [0.0, 1.0],
                default=logistic_val,
            )

        if params.direction == "descending":
            result = 1.0 - result

        return result.astype(np.float64)


class RaginCalibration(CalibrationStrategy):
    """Ragin's fuzzy direct method: log-odds of raw scores relative to anchors.

    Uses logistic transformation based on three qualitative anchors:
    - threshold_full_out -> fuzzy membership 0.05 (floor)
    - crossover_point    -> fuzzy membership 0.50
    - threshold_full_in  -> fuzzy membership 0.95 (ceiling)

    The membership is computed by scaling the deviation from crossover
    into log-odds space and applying the logistic function::

        log_odds_95 = ln(0.95 / 0.05)
        deviation   = (raw - crossover) * scale_factor
        membership  = exp(deviation) / (1 + exp(deviation))

    The scale factor differs above and below the crossover to ensure
    that raw==full_in maps to membership==0.95 and raw==full_out maps
    to membership==0.05.
    """

    def calibrate(
        self, raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        lo = params.threshold_full_out
        hi = params.threshold_full_in
        cross = params.crossover_point

        # Log-odds of the ceiling membership
        log_odds_95 = np.log(0.95 / 0.05)

        # Scale factors for the two sides of the crossover.
        # Guard against degenerate anchors (hi==cross or cross==lo).
        scale_up = log_odds_95 / (hi - cross) if hi > cross else 0.0
        scale_down = log_odds_95 / (cross - lo) if cross > lo else 0.0

        # Deviation from crossover in log-odds space
        deviation = np.where(
            raw_scores >= cross,
            (raw_scores - cross) * scale_up,
            (raw_scores - cross) * scale_down,
        )

        # Clip deviation to prevent exp() overflow with extreme raw scores
        deviation = np.clip(deviation, -700.0, 700.0)

        # Logistic transformation
        result = np.exp(deviation) / (1.0 + np.exp(deviation))

        # Apply fuzzy-set floor and ceiling
        result = np.clip(result, 0.05, 0.95)

        if params.direction == "descending":
            result = 1.0 - result

        return result


class PassthroughCalibration(CalibrationStrategy):
    """Return raw scores as-is without any transformation."""

    def calibrate(
        self, raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        return raw_scores.astype(np.float64)


class CrispCalibration(CalibrationStrategy):
    """Crisp-set calibration: single threshold binarizes raw scores to 0 or 1.

    Raw scores >= crossover_point -> 1.0 (full membership)
    Raw scores <  crossover_point -> 0.0 (full non-membership)

    If direction is "descending", the result is flipped (1 - result) so that
    lower raw scores map to membership 1.0.
    """

    def calibrate(
        self, raw_scores: np.ndarray, params: CalibrationParams
    ) -> np.ndarray:
        threshold = params.crossover_point
        result = np.where(raw_scores >= threshold, 1.0, 0.0)
        if params.direction == "descending":
            result = 1.0 - result
        return result


class CalibrationStrategyRegistry:
    """Registry mapping CalibrationMethod enum values to strategy instances.

    New calibration methods can be added without modifying the registry's
    source code via ``register()``.

    Usage::

        # Look up a pre-registered strategy
        strategy = CalibrationStrategyRegistry.get(CalibrationMethod.DIRECT)
        result = strategy.calibrate(raw_scores, params)

        # Register a custom strategy
        registry = CalibrationStrategyRegistry()
        registry.register(CalibrationMethod.DIRECT, MyCustomDirect())
    """

    _default_strategies: ClassVar[dict[CalibrationMethod, CalibrationStrategy]] = {
        CalibrationMethod.DIRECT: DirectCalibration(),
        CalibrationMethod.INDIRECT: IndirectCalibration(),
        CalibrationMethod.FUZZY_DIRECT: RaginCalibration(),
        CalibrationMethod.PASSTHROUGH: PassthroughCalibration(),
        CalibrationMethod.CRISP_SET: CrispCalibration(),
    }

    def __init__(self) -> None:
        self._strategies: dict[CalibrationMethod, CalibrationStrategy] = dict(
            self._default_strategies
        )

    def register(self, name: CalibrationMethod, strategy: CalibrationStrategy) -> None:
        """Register a strategy for a calibration type.

        Args:
            name: The CalibrationMethod enum value to associate.
            strategy: The strategy instance to use for this type.
        """
        if not isinstance(strategy, CalibrationStrategy):
            raise TypeError(
                f"strategy must be a CalibrationStrategy, got {type(strategy)}"
            )
        self._strategies[name] = strategy

    def get(self, name: CalibrationMethod) -> CalibrationStrategy:
        """Retrieve the strategy for a given calibration type.

        Args:
            name: The CalibrationMethod enum value.

        Returns:
            The registered CalibrationStrategy instance.

        Raises:
            KeyError: If no strategy is registered for this type.
        """
        if name not in self._strategies:
            raise KeyError(
                f"No calibration strategy registered for {name}. "
                f"Available: {list(self._strategies.keys())}"
            )
        return self._strategies[name]

    @property
    def registered_types(self) -> list[CalibrationMethod]:
        """Return all currently registered calibration types."""
        return list(self._strategies.keys())
