"""Input/output layer for experiment-engine.

Provides data readers, data sources, and exporters for standardized
experiment data handling.
"""

from experiment_engine.io.exporters import CSVExporter, HTMLExporter, JSONExporter
from experiment_engine.io.readers import (
    ArrayReader,
    CSVReader,
    DataReader,
    JSONReader,
    SyntheticReader,
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
    "StdinDataSource",
    "SyntheticReader",
    "get_reader",
]
