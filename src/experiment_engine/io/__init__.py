"""Input/output layer for experiment-engine.

Provides data readers, data sources, and exporters for standardized
experiment data handling.
"""

try:
    from experiment_engine.io.db import (
        PostgreSQLDataSource,
        PostgreSQLDataWriter,
        SQLiteDataSource,
        SQLiteDataWriter,
    )
except ImportError:
    # db.py is excluded from Pyodide deployments (SQLite/PostgreSQL require
    # native filesystem access, unavailable in the browser's Pyodide runtime).
    # These names are set to None so that `from experiment_engine.io import
    # PostgreSQLDataSource` still works but returns None instead of raising.
    PostgreSQLDataSource = None  # type: ignore
    PostgreSQLDataWriter = None  # type: ignore
    SQLiteDataSource = None  # type: ignore
    SQLiteDataWriter = None  # type: ignore
from experiment_engine.io.exporters import CSVExporter, HTMLExporter, JSONExporter
from experiment_engine.io.readers import (
    ArrayReader,
    CSVReader,
    DataReader,
    JSONReader,
    SyntheticReader,
    TextCorpusReader,
)
from experiment_engine.io.sources import (
    DataSource,
    FileDataSource,
    GeneratorDataSource,
    StdinDataSource,
)

_READER_MAP = {
    "csv": CSVReader,
    "json": JSONReader,
    "array": ArrayReader,
    "synthetic": SyntheticReader,
    "text_corpus": TextCorpusReader,
}


def get_reader(format: str) -> DataReader:
    """Create a DataReader instance for the given format string.

    Args:
        format: One of ``"csv"``, ``"json"``, ``"array"``, ``"synthetic"``.

    Returns:
        A :class:`DataReader` instance ready to read data.

    Raises:
        ValueError: If the format is not recognised.
    """
    cls = _READER_MAP.get(format.lower())
    if cls is None:
        raise ValueError(
            f"Unknown input format: {format!r}. Supported: {', '.join(_READER_MAP)}"
        )
    return cls()


__all__ = [
    "ArrayReader",
    "CSVExporter",
    "CSVReader",
    "DataReader",
    "DataSource",
    "FileDataSource",
    "GeneratorDataSource",
    "HTMLExporter",
    "JSONExporter",
    "JSONReader",
    "PostgreSQLDataSource",
    "PostgreSQLDataWriter",
    "SQLiteDataSource",
    "SQLiteDataWriter",
    "StdinDataSource",
    "SyntheticReader",
    "get_reader",
]
