"""QCA Truth Table construction from fuzzy-set membership data."""

from __future__ import annotations

import numpy as np

from experiment_engine.models import FuzzySetData, TruthTable, TruthTableRow


class TruthTableBuilder:
    """Build a QCA truth table from fuzzy-set membership data.

    Follows Ragin's method:
    1. Enumerate all 2^k Boolean configurations of conditions
    2. For each configuration, compute case memberships using fuzzy intersection
    3. Compute frequency and consistency per configuration
    4. Filter by thresholds and assign outcome values
    """

    def build(
        self,
        fuzzy_data: FuzzySetData,
        frequency_threshold: float = 1.0,
        consistency_threshold: float = 0.75,
    ) -> TruthTable:
        """Construct the truth table.

        Args:
            fuzzy_data: Fuzzy-set membership matrix (conditions + outcome).
            frequency_threshold: Minimum frequency to include a row.
            consistency_threshold: Consistency above which outcome = 1.

        Returns:
            A populated TruthTable.
        """
        cond_matrix = fuzzy_data.condition_matrix
        outcome = fuzzy_data.outcome_vector
        n_cases, n_conditions = cond_matrix.shape
        n_configs = 2**n_conditions

        rows: list[TruthTableRow] = []
        for config_idx in range(n_configs):
            config = self._idx_to_config(config_idx, n_conditions)

            # Compute each case's membership in this ideal-type configuration
            config_membership = self._compute_config_membership(cond_matrix, config)

            # Frequency = sum of memberships (or count with membership > 0.5)
            frequency = float(np.sum(config_membership))

            # Consistency = subset_consistency(config_membership ⊆ outcome)
            consistency = self._compute_consistency(config_membership, outcome)

            # Determine if this row passes thresholds
            included = frequency >= frequency_threshold

            # Assign outcome value based on consistency threshold
            outcome_value = 1 if (consistency >= consistency_threshold) else 0

            config_label = self._config_to_label(config, fuzzy_data.condition_names)

            rows.append(
                TruthTableRow(
                    config=config,
                    config_label=config_label,
                    frequency=frequency,
                    raw_consistency=consistency,
                    outcome_value=outcome_value,
                    included=included,
                )
            )

        return TruthTable(
            rows=rows,
            condition_names=list(fuzzy_data.condition_names),
            outcome_name=fuzzy_data.outcome_name,
            consistency_threshold=consistency_threshold,
            frequency_threshold=frequency_threshold,
            n_cases=n_cases,
        )

    @staticmethod
    def enumerate_configurations(n_conditions: int) -> np.ndarray:
        """Generate all 2^k Boolean configurations as a (2^k, k) matrix."""
        return np.array(
            [[int(b) for b in f"{i:0{n_conditions}b}"] for i in range(2**n_conditions)],
            dtype=np.int32,
        )

    @staticmethod
    def _idx_to_config(idx: int, n_conditions: int) -> list[int]:
        bits = f"{idx:0{n_conditions}b}"
        return [int(b) for b in bits]

    @staticmethod
    def _compute_config_membership(
        cond_matrix: np.ndarray, config: list[int]
    ) -> np.ndarray:
        """Compute each case's fuzzy membership in a given configuration.

        For each condition present (1), use the membership directly.
        For each condition absent (0), use 1 - membership.
        Final membership = min across all conditions (fuzzy AND).

        Works for both fuzzy-set (continuous [0,1]) and crisp-set (binary {0,1}):
        with crisp-set data, min(0,1)=0 and min(1,1)=1 correctly compute the
        Boolean AND of the configuration match.
        """
        n_cases = cond_matrix.shape[0]
        members = np.ones(n_cases, dtype=np.float64)
        for j, val in enumerate(config):
            if val == 1:
                members = np.minimum(members, cond_matrix[:, j])
            else:
                members = np.minimum(members, 1.0 - cond_matrix[:, j])
        return members

    @staticmethod
    def _compute_consistency(
        config_membership: np.ndarray, outcome: np.ndarray
    ) -> float:
        denom = float(np.sum(config_membership))
        if denom == 0.0:
            return 0.0
        return float(np.sum(np.minimum(config_membership, outcome)) / denom)

    @staticmethod
    def _config_to_label(config: list[int], condition_names: list[str]) -> str:
        parts: list[str] = []
        for val, name in zip(config, condition_names, strict=False):
            if val == 1:
                parts.append(name.upper())
            else:
                parts.append(f"~{name.upper()}")
        return "*".join(parts) if parts else "empty"
