"""Data readers for experiment-engine.

Provides an abstract DataReader base class and concrete implementations
for reading experiment data from various sources. All readers return
standardized InputData objects.
"""

from __future__ import annotations

import csv
import itertools
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

from experiment_engine.models import InputData


class DataReader(ABC):
    """Abstract base class for all data readers.

    Subclasses must implement the ``read()`` method which returns an
    :class:`InputData` instance.

    Attributes:
        name: Human-readable name for this reader.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a human-readable name for this reader."""

    @abstractmethod
    def read(self, source: Any, **kwargs: Any) -> InputData:
        """Read data from *source* and return a standardized InputData.

        Args:
            source: The data source (path, URL, object, etc.).
            **kwargs: Implementation-specific keyword arguments.

        Returns:
            InputData: Standardized container with data array and metadata.
        """

    def can_read(self, source: Any) -> bool:
        """Return True if this reader can handle the given *source*.

        The base implementation returns True if the source is a string
        ending with the reader's typical file extension. Subclasses
        should override for more sophisticated detection.

        Args:
            source: The data source to check.

        Returns:
            bool: Whether this reader can handle the source.
        """
        ext = self._guess_extension()
        if ext and isinstance(source, (str, Path)):
            return str(source).lower().endswith(ext)
        return False

    def _guess_extension(self) -> Optional[str]:
        """Return the default file extension for this reader, if any."""
        return None


class CSVReader(DataReader):
    """Reads tabular data from CSV files using pandas.

    Supports standard CSV, TSV, and other delimiter-separated formats.

    Examples:
        >>> reader = CSVReader()
        >>> data = reader.read("data.csv")
        >>> data.n_samples, data.n_features
        (100, 5)
    """

    @property
    def name(self) -> str:
        return "csv"

    def _guess_extension(self) -> Optional[str]:
        return ".csv"

    def read(
        self,
        source: Union[str, Path, Iterator[str]],
        delimiter: str = ",",
        header: Optional[int] = 0,
        index_col: Optional[int] = None,
        **kwargs: Any,
    ) -> InputData:
        """Read data from a CSV file or line iterator.

        Args:
            source: File path or iterator yielding CSV lines.
            delimiter: Field delimiter character (default: ``,``).
            header: Row to use as column names (None = no header).
            index_col: Column to use as row index (None = no index).
            **kwargs: Additional arguments passed to ``pandas.read_csv``.

        Returns:
            InputData: Parsed data with columns and optional index.
        """
        df = pd.read_csv(
            source,
            delimiter=delimiter,
            header=header,
            index_col=index_col,
            **kwargs,
        )
        columns = [str(c) for c in df.columns.tolist()]
        index: Optional[List[Any]] = None
        if df.index.name is not None:
            index = df.index.tolist()

        metadata = {
            "source": str(source) if isinstance(source, (str, Path)) else "<iterator>",
            "n_rows": len(df),
            "n_cols": len(df.columns),
            "dtypes": {c: str(dt) for c, dt in df.dtypes.items()},
        }

        return InputData(
            data=df.to_numpy(),
            columns=columns,
            index=index,
            metadata=metadata,
        )


class JSONReader(DataReader):
    """Reads structured data from JSON files or strings.

    Expects a list of records (dicts) or a dict with a ``"data"`` key
    containing a list of records.

    Examples:
        >>> reader = JSONReader()
        >>> data = reader.read("experiment.json")
        >>> data.columns
        ['x', 'y', 'z']
    """

    @property
    def name(self) -> str:
        return "json"

    def _guess_extension(self) -> Optional[str]:
        return ".json"

    def read(
        self,
        source: Union[str, Path, str],
        data_key: Optional[str] = None,
        orient: str = "records",
        **kwargs: Any,
    ) -> InputData:
        """Read data from a JSON file or string.

        Args:
            source: File path or JSON string.
            data_key: If the top-level JSON is a dict, the key whose value
                contains the data records. If None, tries common keys
                (``"data"``, ``"values"``, ``"results"``) automatically.
            orient: Pandas orientation for JSON parsing (default: ``records``).
            **kwargs: Additional arguments passed to ``pandas.read_json``.

        Returns:
            InputData: Parsed data.
        """
        raw: Any
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.exists():
                raw = json.loads(path.read_text(encoding="utf-8"))
            else:
                # Treat as a JSON string
                raw = json.loads(source)
        else:
            raw = json.loads(source)

        # If it's a dict, try to extract the data array
        if isinstance(raw, dict):
            if data_key is not None:
                raw = raw[data_key]
            else:
                for key in ("data", "values", "results", "records"):
                    if key in raw:
                        raw = raw[key]
                        break

        df = pd.DataFrame(raw)
        columns = [str(c) for c in df.columns.tolist()]
        index: Optional[List[Any]] = None
        if df.index.name is not None:
            index = df.index.tolist()

        metadata = {
            "source": str(source) if isinstance(source, (str, Path)) else "<string>",
            "n_rows": len(df),
            "n_cols": len(df.columns),
        }

        return InputData(
            data=df.to_numpy(),
            columns=columns,
            index=index,
            metadata=metadata,
        )


class ArrayReader(DataReader):
    """Reads data directly from numpy arrays.

    Useful for in-memory data that is already available as arrays.

    Examples:
        >>> import numpy as np
        >>> reader = ArrayReader()
        >>> arr = np.random.randn(50, 3)
        >>> data = reader.read(arr, columns=["a", "b", "c"])
        >>> data.shape
        (50, 3)
    """

    @property
    def name(self) -> str:
        return "array"

    def read(
        self,
        source: Union[np.ndarray, Sequence[Sequence[float]]],
        columns: Optional[List[str]] = None,
        index: Optional[List[Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> InputData:
        """Read data from a numpy array.

        Args:
            source: A 1D or 2D numpy array (or convertible sequence).
            columns: Optional list of column names. Auto-generated if not
                provided.
            index: Optional list of row labels.
            metadata: Optional metadata dict.
            **kwargs: Ignored.

        Returns:
            InputData: Wrapped data.
        """
        arr = np.asarray(source, dtype=float)
        return InputData(
            data=arr,
            columns=columns or [],
            index=index,
            metadata=metadata or {"source": "array"},
        )

    def can_read(self, source: Any) -> bool:
        """Return True if *source* is a numpy array or array-like."""
        return isinstance(source, (np.ndarray, list, tuple))


class SyntheticReader(DataReader):
    """Generates synthetic test data for experimentation.

    Supports sine waves, random noise, step functions, and combinations.

    Examples:
        >>> reader = SyntheticReader()
        >>> data = reader.read(n_samples=200, n_features=3, pattern="sine")
        >>> data.n_samples
        200
    """

    PATTERNS = ("sine", "cosine", "random", "step", "mixed", "spiral")

    @property
    def name(self) -> str:
        return "synthetic"

    def read(
        self,
        source: Optional[Any] = None,
        n_samples: int = 100,
        n_features: int = 2,
        pattern: str = "sine",
        noise: float = 0.0,
        seed: Optional[int] = None,
        columns: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> InputData:
        """Generate synthetic data.

        Args:
            source: Ignored (included for API compatibility).
            n_samples: Number of data points (default: 100).
            n_features: Number of feature dimensions (default: 2).
            pattern: One of ``sine``, ``cosine``, ``random``, ``step``,
                ``mixed``, ``spiral`` (default: ``sine``).
            noise: Standard deviation of Gaussian noise added (default: 0).
            seed: Random seed for reproducibility.
            columns: Optional column names.
            **kwargs: Ignored.

        Returns:
            InputData: Generated data.
        """
        rng = np.random.default_rng(seed)
        t = np.linspace(0, 4 * np.pi, n_samples)

        generators = {
            "sine": lambda: np.column_stack(
                [np.sin(t + (2 * np.pi * i / n_features)) for i in range(n_features)]
            ),
            "cosine": lambda: np.column_stack(
                [np.cos(t + (2 * np.pi * i / n_features)) for i in range(n_features)]
            ),
            "random": lambda: rng.standard_normal((n_samples, n_features)),
            "step": lambda: np.column_stack(
                [
                    np.repeat(
                        rng.standard_normal(n_samples // 20),
                        20,
                    )[:n_samples]
                    for _ in range(n_features)
                ]
            ),
            "mixed": lambda: np.column_stack(
                [
                    np.sin(t) if i == 0
                    else rng.standard_normal(n_samples) if i == 1
                    else np.sin(t) + 0.5 * rng.standard_normal(n_samples)
                    for i in range(n_features)
                ]
            ),
            "spiral": lambda: np.column_stack(
                [
                    t * np.cos(t + (2 * np.pi * i / max(1, n_features - 1))),
                    t * np.sin(t + (2 * np.pi * i / max(1, n_features - 1))),
                ]
                + [
                    rng.standard_normal(n_samples)
                    for _ in range(n_features - 2)
                ]
            ),
        }

        if pattern not in generators:
            raise ValueError(
                f"Unknown pattern '{pattern}'. "
                f"Choose from {', '.join(self.PATTERNS)}"
            )

        data = generators[pattern]()
        if data.shape[1] < n_features:
            # Pad with noise if needed (e.g. spiral for n_features > 2)
            padding = np.column_stack(
                [rng.standard_normal(n_samples) for _ in range(n_features - data.shape[1])]
            )
            data = np.column_stack([data, padding])
        elif data.shape[1] > n_features:
            data = data[:, :n_features]

        if noise > 0:
            data += noise * rng.standard_normal(data.shape)

        if columns is None:
            columns = [f"{pattern}_{i}" for i in range(n_features)]

        metadata = {
            "source": "synthetic",
            "pattern": pattern,
            "noise": noise,
            "seed": seed,
            "n_samples": n_samples,
            "n_features": n_features,
        }

        return InputData(data=data, columns=columns, metadata=metadata)
