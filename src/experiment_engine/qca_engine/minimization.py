"""Quine-McCluskey Boolean minimization for QCA.

Pure Python implementation of the QM algorithm:
1. Group minterms by number of 1-bits
2. Iteratively combine adjacent groups (differ by one bit)
3. Identify prime implicants (uncombinable)
4. Build prime implicant chart
5. Find minimal cover (Petrick's method or greedy heuristic)
"""

from __future__ import annotations

import numpy as np


class QuineMcCluskey:
    """Boolean minimization using the Quine-McCluskey algorithm.

    Takes truth table rows with outcome=1 as minterms and produces a set of
    prime implicants that minimally cover all minterms.
    """

    def __init__(self) -> None:
        self._prime_implicants: list[tuple[tuple[int | None, ...], list[int]]] = []
        """List of (implicant_pattern, covered_minterms) tuples."""

    def minimize(
        self,
        minterms: list[list[int]],
        condition_names: list[str],
        dont_care_minterms: list[list[int]] | None = None,
    ) -> list[list[str]]:
        """Find minimal Boolean expression covering all minterms.

        Args:
            minterms: List of binary configurations that must be covered
                (e.g., [[1,0,1], [1,1,0]]).
            condition_names: Names of conditions for each bit position.
            dont_care_minterms: Optional don't-care minterms. These
                participate in prime implicant generation (helping merge
                and simplify) but are NOT required to be covered.

        Returns:
            List of solution terms, each a list of condition names
            (with '~' prefix for negated conditions).
        """
        if not minterms:
            return []

        # Combine regular and don't-care minterms for prime implicant generation.
        # Regular minterms have indices 0..n_reg-1 (must be covered).
        # Don't-care minterms have indices n_reg..n_total-1 (optional).
        dc_list = dont_care_minterms or []
        all_minterms: list[list[int]] = list(minterms) + list(dc_list)
        n_reg = len(minterms)

        # Step 1-2: Find all prime implicants
        implicant_map: dict[int, list[tuple[tuple[int | None, ...], list[int]]]] = {}
        # Group by number of 1-bits (all minterms participate in combining)
        for idx, mt in enumerate(all_minterms):
            ones = sum(mt)
            key = ones
            if key not in implicant_map:
                implicant_map[key] = []
            implicant_map[key].append((tuple(mt), [idx]))

        prime_implicants: list[tuple[tuple[int | None, ...], list[int]]] = []
        used_in_combination: set[int] = set()

        while True:
            next_map: dict[int, list[tuple[tuple[int | None, ...], list[int]]]] = {}
            combined_this_round: set[int] = set()

            # Sort keys
            sorted_keys = sorted(implicant_map.keys())
            for i in range(len(sorted_keys) - 1):
                k1 = sorted_keys[i]
                k2 = sorted_keys[i + 1]
                if k2 - k1 != 1:
                    continue  # only combine groups with 1-bit difference in count

                for imp1, cov1 in implicant_map.get(k1, []):
                    for imp2, cov2 in implicant_map.get(k2, []):
                        result = self._try_combine(imp1, imp2)
                        if result is not None:
                            new_key = sum(1 for b in result if b == 1)
                            if new_key not in next_map:
                                next_map[new_key] = []
                            merged_cov = list(set(cov1 + cov2))
                            next_map[new_key].append((result, merged_cov))
                            # Mark originals as used
                            h1 = hash((imp1, tuple(cov1)))
                            h2 = hash((imp2, tuple(cov2)))
                            combined_this_round.add(h1)
                            combined_this_round.add(h2)

            # Uncombined implicants become prime implicants
            for k in sorted_keys:
                for imp, cov in implicant_map.get(k, []):
                    h = hash((imp, tuple(cov)))
                    if h not in combined_this_round and h not in used_in_combination:
                        if (imp, cov) not in prime_implicants:
                            prime_implicants.append((imp, cov))

            for h in combined_this_round:
                used_in_combination.add(h)

            if not next_map:
                break
            implicant_map = next_map

        # Also add any remaining from last round
        for k in implicant_map:
            for imp, cov in implicant_map[k]:
                if (imp, cov) not in prime_implicants:
                    prime_implicants.append((imp, cov))

        self._prime_implicants = prime_implicants

        if not prime_implicants:
            return []

        # Step 3: Build prime implicant chart (regular minterms only).
        # Don't-care minterms (indices >= n_reg) are excluded from the chart
        # because they do not need to be covered.
        n_pi = len(prime_implicants)
        chart = np.zeros((n_pi, n_reg), dtype=np.int32)
        for i, (_, covered) in enumerate(prime_implicants):
            for idx in covered:
                if idx < n_reg:  # Only regular minterms require coverage
                    chart[i, idx] = 1

        # Step 4: Find essential prime implicants
        essential_indices = self._find_essential(chart)

        # Step 5: Find minimal cover for remaining uncovered regular minterms
        covered = np.zeros(n_reg, dtype=np.int32)
        for ei in essential_indices:
            covered += chart[ei, :]

        remaining = np.where(covered == 0)[0]
        if len(remaining) > 0:
            # Greedy cover for remaining
            remaining_chart = chart[:, remaining]
            additional = self._greedy_cover(remaining_chart)
        else:
            additional = []

        selected_indices = sorted(set(essential_indices + additional))

        # Convert selected prime implicants to solution terms
        solution_terms: list[list[str]] = []
        for idx in selected_indices:
            imp, _ = prime_implicants[idx]
            term = self._implicant_to_term(imp, condition_names)
            solution_terms.append(term)

        return solution_terms

    @staticmethod
    def _try_combine(
        imp1: tuple[int | None, ...], imp2: tuple[int | None, ...]
    ) -> tuple[int | None, ...] | None:
        """Try to combine two implicants. Returns combined or None."""
        if len(imp1) != len(imp2):
            return None
        diff_count = 0
        diff_idx = -1
        result = list(imp1)
        for i in range(len(imp1)):
            if imp1[i] != imp2[i]:
                diff_count += 1
                diff_idx = i
                if diff_count > 1:
                    return None
        if diff_count == 0:
            return None  # identical
        result[diff_idx] = None  # mark as don't-care
        return tuple(result)

    @staticmethod
    def _find_essential(chart: np.ndarray) -> list[int]:
        """Find essential prime implicants (those uniquely covering a minterm)."""
        essential: list[int] = []
        _n_pi, n_mt = chart.shape
        for j in range(n_mt):
            covering = np.where(chart[:, j] == 1)[0]
            if len(covering) == 1:
                pi_idx = int(covering[0])
                if pi_idx not in essential:
                    essential.append(pi_idx)
        return essential

    @staticmethod
    def _greedy_cover(chart: np.ndarray) -> list[int]:
        """Greedy minimal cover heuristic.

        Repeatedly pick the prime implicant covering the most uncovered minterms.
        """
        if chart.size == 0:
            return []
        n_pi, n_mt = chart.shape
        uncovered = set(range(n_mt))
        selected: list[int] = []
        while uncovered:
            best_pi = -1
            best_count = 0
            for i in range(n_pi):
                if i in selected:
                    continue
                count = sum(1 for j in uncovered if chart[i, j] == 1)
                if count > best_count:
                    best_count = count
                    best_pi = i
            if best_pi < 0 or best_count == 0:
                break
            selected.append(best_pi)
            # Remove covered minterms
            covered_now = {j for j in uncovered if chart[best_pi, j] == 1}
            uncovered -= covered_now
        return selected

    @staticmethod
    def _implicant_to_term(
        implicant: tuple[int | None, ...], condition_names: list[str]
    ) -> list[str]:
        """Convert an implicant pattern to a list of condition names.

        Present conditions (1) → condition name.
        Absent conditions (0) → '~condition_name'.
        Don't-care (None) → omitted.
        """
        term: list[str] = []
        for val, name in zip(implicant, condition_names, strict=False):
            if val == 1:
                term.append(name)
            elif val == 0:
                term.append(f"~{name}")
            # None → don't-care, omit
        return term
