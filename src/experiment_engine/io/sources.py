"""Data source abstractions for experiment-engine.

A DataSource encapsulates the origin of data — whether from a file,
standard input, or a generator — and provides a unified interface
for reading.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from experiment_engine.io.readers import (
    CSVReader,
    DataReader,
    JSONReader,
    SyntheticReader,
)
from experiment_engine.models import InputData


class DataSource(ABC):
    """Abstract data source that reads from a specific origin.

    A DataSource wraps a :class:`DataReader` and a location, providing
    a consistent ``load()`` interface.

    Attributes:
        reader: The reader used to parse the data.
        location: Description of where the data comes from.
    """

    def __init__(self, reader: DataReader, location: str = "") -> None:
        self.reader = reader
        self.location = location

    @abstractmethod
    def load(self, **kwargs: Any) -> InputData:
        """Load data from this source.

        Returns:
            InputData: The parsed data.
        """

    @classmethod
    def auto_detect(cls, source: Any, **kwargs: Any) -> DataSource:
        """Auto-detect the appropriate DataSource for a given *source*.

        Tries registered readers in order and returns the first match.

        Args:
            source: The data source (path, URL, array, etc.).
            **kwargs: Additional arguments forwarded to the reader.

        Returns:
            DataSource: An appropriate DataSource instance.

        Raises:
            ValueError: If no suitable DataSource is found.
        """
        readers: list[DataReader] = [
            CSVReader(),
            JSONReader(),
            SyntheticReader(),
        ]

        for reader in readers:
            if reader.can_read(source):
                return cls(reader=reader, location=str(source))

        # Fallback: try CSVReader for any string path
        if isinstance(source, (str, Path)):
            return cls(reader=CSVReader(), location=str(source))

        raise ValueError(f"Cannot auto-detect a DataSource for {type(source).__name__}")


class FileDataSource(DataSource):
    """DataSource that reads from a file on disk.

    Examples:
        >>> ds = FileDataSource(CSVReader(), "data.csv")
        >>> data = ds.load(delimiter=",")
    """

    def __init__(self, reader: DataReader, path: str | Path) -> None:
        super().__init__(reader, location=str(path))
        self.path = Path(path)

    def load(self, **kwargs: Any) -> InputData:
        """Load data from the file path.

        Args:
            **kwargs: Forwarded to the reader's ``read()`` method.

        Returns:
            InputData: Parsed data.
        """
        if not self.path.exists():
            raise FileNotFoundError(f"Data file not found: {self.path}")
        return self.reader.read(self.path, **kwargs)


class StdinDataSource(DataSource):
    """DataSource that reads from standard input.

    Useful for piping data into the experiment engine.

    Examples:
        >>> ds = StdinDataSource(CSVReader())
        >>> data = ds.load()  # reads from sys.stdin
    """

    def __init__(self, reader: DataReader) -> None:
        super().__init__(reader, location="<stdin>")

    def load(self, **kwargs: Any) -> InputData:
        """Read data from stdin.

        Args:
            **kwargs: Forwarded to the reader's ``read()`` method.

        Returns:
            InputData: Parsed data.
        """
        return self.reader.read(sys.stdin, **kwargs)


class GeneratorDataSource(DataSource):
    """DataSource that uses a generator function to produce data.

    Useful for synthetic or streaming data sources.

    Examples:
        >>> ds = GeneratorDataSource(SyntheticReader())
        >>> data = ds.load(n_samples=500, pattern="spiral")
    """

    def __init__(self, reader: DataReader) -> None:
        super().__init__(reader, location="<generated>")

    def load(self, **kwargs: Any) -> InputData:
        """Generate data using the underlying reader.

        Args:
            **kwargs: Forwarded to the reader's ``read()`` method.

        Returns:
            InputData: Generated data.
        """
        return self.reader.read(source=None, **kwargs)
