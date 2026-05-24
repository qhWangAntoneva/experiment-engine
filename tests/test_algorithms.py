"""Tests for the built-in algorithm stages (linear regression, K-Means).

Verifies correctness using synthetic data with known ground-truth.
"""

import numpy as np
import pytest
from experiment_engine.algorithms.kmeans import KMeansStage
from experiment_engine.algorithms.linear_regression import LinearRegressionStage
from experiment_engine.models import InputData

# ═══════════════════════════════════════════════════════════════════════
#  Linear Regression
# ═══════════════════════════════════════════════════════════════════════


class TestLinearRegression:
    """Test suite for LinearRegressionStage (normal equation)."""

    def test_linear_regression_ols(self) -> None:
        """Verify that y = 2x + 1 is recovered exactly."""
        rng = np.random.default_rng(42)
        x = rng.uniform(-10, 10, size=(100, 1))
        y = 2.0 * x.ravel() + 1.0  # y = 2x + 1
        data_array = np.column_stack([x, y])

        inp = InputData(data=data_array, columns=["x", "y"])
        stage = LinearRegressionStage()
        result = stage.process(inp)

        beta = result.processed  # [intercept, slope]
        assert beta.shape == (2,), f"Expected 2 coefficients, got {beta.shape}"
        np.testing.assert_allclose(
            beta[0], 1.0, atol=1e-8, err_msg="Intercept mismatch"
        )
        np.testing.assert_allclose(beta[1], 2.0, atol=1e-8, err_msg="Slope mismatch")

    def test_linear_regression_r_squared_perfect(self) -> None:
        """R² should be exactly 1.0 for a perfectly linear relationship."""
        rng = np.random.default_rng(99)
        x = rng.uniform(-5, 5, size=(50, 3))
        true_coeffs = np.array([3.0, -1.5, 0.7])
        y = x @ true_coeffs + 5.0  # intercept = 5
        data_array = np.column_stack([x, y])

        inp = InputData(data=data_array)
        stage = LinearRegressionStage()
        result = stage.process(inp)

        assert result.metadata["r_squared"] == pytest.approx(1.0, abs=1e-10)
        assert result.metadata["mse"] == pytest.approx(0.0, abs=1e-10)
        np.testing.assert_allclose(result.metadata["intercept"], 5.0, atol=1e-8)
        np.testing.assert_allclose(
            result.metadata["coeffs"], true_coeffs.tolist(), atol=1e-8
        )

    def test_linear_regression_multi_collinear(self) -> None:
        """Should still produce a usable result with near-collinear features."""
        rng = np.random.default_rng(7)
        x1 = rng.normal(0, 1, size=(30,))
        x2 = x1 * 0.999 + rng.normal(0, 1e-6, size=(30,))  # near-collinear
        y = 4.0 * x1 - 2.0 * x2 + 0.5
        data_array = np.column_stack([x1, x2, y])

        inp = InputData(data=data_array)
        stage = LinearRegressionStage()
        result = stage.process(inp)

        # Should not crash — lstsq fallback handles singular matrices
        assert result.processed is not None
        assert result.metadata["r_squared"] > 0.99

    def test_linear_regression_wrong_dims(self) -> None:
        """1D input should raise."""
        inp = InputData(data=np.array([1.0, 2.0, 3.0]))
        stage = LinearRegressionStage()
        with pytest.raises(ValueError, match="Expected 2D"):
            stage.process(inp)

    def test_linear_regression_single_column(self) -> None:
        """Only one column means no features — should raise."""
        inp = InputData(data=np.array([[1.0], [2.0], [3.0]]))
        stage = LinearRegressionStage()
        with pytest.raises(ValueError, match="at least 2 columns"):
            stage.process(inp)


# ═══════════════════════════════════════════════════════════════════════
#  K-Means
# ═══════════════════════════════════════════════════════════════════════


class TestKMeans:
    """Test suite for KMeansStage (Lloyd's algorithm)."""

    def test_kmeans_simple(self) -> None:
        """Two well-separated clusters should be recovered perfectly."""
        rng = np.random.default_rng(42)
        n_per_cluster = 50
        cluster_a = rng.normal(loc=[0.0, 0.0], scale=0.3, size=(n_per_cluster, 2))
        cluster_b = rng.normal(loc=[5.0, 5.0], scale=0.3, size=(n_per_cluster, 2))
        X = np.vstack([cluster_a, cluster_b])

        inp = InputData(data=X)
        stage = KMeansStage(n_clusters=2, max_iter=50, tol=1e-6)
        result = stage.process(inp)

        labels = np.array(result.metadata["labels"])
        assert labels.shape == (100,), f"Expected 100 labels, got {labels.shape}"

        # The two clusters should each have exactly 50 points
        unique, counts = np.unique(labels, return_counts=True)
        assert len(unique) == 2, f"Expected 2 clusters, got {len(unique)}"
        assert all(counts == n_per_cluster), f"Cluster sizes not equal: {counts}"

        # Inertia should be small (tight clusters)
        assert result.metadata["inertia"] < 50.0

    def test_kmeans_convergence(self) -> None:
        """Check that the algorithm terminates within max_iter and reports
        the correct convergence status."""
        rng = np.random.default_rng(123)
        X = rng.uniform(-1, 1, size=(200, 5))

        inp = InputData(data=X)
        stage = KMeansStage(n_clusters=4, max_iter=200, tol=1e-6)
        result = stage.process(inp)

        assert result.metadata["n_iter"] <= 200
        assert result.metadata["n_clusters"] == 4
        assert result.metadata["n_features"] == 5
        assert result.metadata["n_samples"] == 200
        assert len(result.metadata["labels"]) == 200

        # Centroids should have the right shape
        centroids = result.processed
        assert centroids.shape == (4, 5)

    def test_kmeans_three_clusters(self) -> None:
        """Three well-separated clusters on a line.

        Uses a generous gap (centres 0, 10, 20) with tight variance.
        Because random initialisation can sometimes produce sub-optimal
        clusterings, we check that:
          - exactly 3 clusters are discovered,
          - no cluster is empty,
          - the recovered centroids are close to the true centres
            (within ~1.0 after sorting).
        """
        rng = np.random.default_rng(42)  # deterministic seed
        c1 = rng.normal(loc=0.0, scale=0.3, size=(30, 1))
        c2 = rng.normal(loc=10.0, scale=0.3, size=(30, 1))
        c3 = rng.normal(loc=20.0, scale=0.3, size=(30, 1))
        X = np.vstack([c1, c2, c3])

        inp = InputData(data=X)
        stage = KMeansStage(n_clusters=3, max_iter=200, tol=1e-6)
        result = stage.process(inp)

        labels = np.array(result.metadata["labels"])
        unique, counts = np.unique(labels, return_counts=True)
        assert len(unique) == 3, f"Expected 3 clusters, got {len(unique)}"
        assert all(c > 0 for c in counts), f"Empty cluster: {counts}"

        # Check recovered centroids are close to true centres
        true_centres = sorted([0.0, 10.0, 20.0])
        recovered = sorted(c.item() for c in result.processed.flatten())
        for true_c, rec_c in zip(true_centres, recovered, strict=False):
            assert (
                abs(true_c - rec_c) < 1.0
            ), f"Centroid mismatch: true {true_c:.2f} vs recovered {rec_c:.2f}"

    def test_kmeans_single_sample_per_cluster(self) -> None:
        """k == n_samples is a degenerate case — each point is its own centroid."""
        X = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
        inp = InputData(data=X)
        stage = KMeansStage(n_clusters=3, max_iter=10, tol=1e-6)
        result = stage.process(inp)

        assert result.metadata["inertia"] == pytest.approx(0.0, abs=1e-10)

    def test_kmeans_empty_cluster_handling(self) -> None:
        """If a cluster becomes empty the algorithm should not crash."""
        rng = np.random.default_rng(1)
        X = rng.uniform(0, 1, size=(100, 3))
        inp = InputData(data=X)
        # Use a large k that might produce empty clusters
        stage = KMeansStage(n_clusters=20, max_iter=10, tol=1e-8)
        # Should not raise
        result = stage.process(inp)
        assert len(np.unique(result.metadata["labels"])) <= 20

    def test_kmeans_1d_data(self) -> None:
        """Single-feature data should work correctly."""
        rng = np.random.default_rng(5)
        X = rng.uniform(0, 10, size=(50, 1))
        inp = InputData(data=X)
        stage = KMeansStage(n_clusters=3, max_iter=50, tol=1e-6)
        result = stage.process(inp)
        assert result.processed.shape == (3, 1)

    def test_kmeans_invalid_input(self) -> None:
        """Non-array input should raise TypeError."""
        inp = InputData(data=[[1, 2], [3, 4]])  # plain list, not ndarray
        stage = KMeansStage()
        with pytest.raises(TypeError, match=r"Expected np\.ndarray"):
            stage.process(inp)
