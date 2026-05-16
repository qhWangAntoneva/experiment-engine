"""Result exporters for experiment-engine.

Allows saving experiment results and visualizations to various file
formats including CSV, JSON, and HTML.
"""

from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from experiment_engine.models import ExportConfig, InputData


class BaseExporter(ABC):
    """Abstract base class for data exporters.

    Subclasses implement ``export()`` to write data to a file.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable exporter name."""

    @abstractmethod
    def export(
        self,
        data: InputData,
        config: ExportConfig,
        **kwargs: Any,
    ) -> str:
        """Export *data* to a file and return the output path.

        Args:
            data: The input data to export.
            config: Export configuration (format, path, options).
            **kwargs: Additional export-specific options.

        Returns:
            str: The path to the exported file.
        """


class CSVExporter(BaseExporter):
    """Exports data to CSV format.

    Examples:
        >>> exp = CSVExporter()
        >>> path = exp.export(data, ExportConfig(format="csv"))
    """

    @property
    def name(self) -> str:
        return "csv"

    def export(
        self,
        data: InputData,
        config: ExportConfig,
        **kwargs: Any,
    ) -> str:
        """Export data to a CSV file.

        Args:
            data: Input data to export.
            config: Export configuration.
            **kwargs: Additional keyword arguments for ``csv.writer``.

        Returns:
            str: Output file path.
        """
        output_path = config.output_path or "output.csv"
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, **kwargs)

            # Write header
            header = list(data.columns)
            if config.include_index and data.index is not None:
                header = ["index", *header]
            writer.writerow(header)

            # Write rows
            for i in range(data.n_samples):
                row = data.data[i].tolist()
                if config.include_index and data.index is not None:
                    row = [data.index[i], *row]
                writer.writerow(row)

        return str(path.resolve())


class JSONExporter(BaseExporter):
    """Exports data to JSON format.

    Examples:
        >>> exp = JSONExporter()
        >>> path = exp.export(data, ExportConfig(format="json"))
    """

    @property
    def name(self) -> str:
        return "json"

    def export(
        self,
        data: InputData,
        config: ExportConfig,
        **kwargs: Any,
    ) -> str:
        """Export data to a JSON file.

        Args:
            data: Input data to export.
            config: Export configuration.
            **kwargs: Additional keyword arguments for ``json.dump``.

        Returns:
            str: Output file path.
        """
        output_path = config.output_path or "output.json"
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        records: list[dict[str, Any]] = []
        for i in range(data.n_samples):
            record = dict(zip(data.columns, data.data[i].tolist(), strict=False))
            if config.include_index and data.index is not None:
                record["index"] = data.index[i]
            records.append(record)

        indent = 2 if config.pretty else None
        with path.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=indent, **kwargs)

        return str(path.resolve())


class HTMLExporter(BaseExporter):
    """Exports data to an HTML table.

    Useful for embedding results in reports or dashboards.

    Examples:
        >>> exp = HTMLExporter()
        >>> path = exp.export(data, ExportConfig(format="html"))
    """

    @property
    def name(self) -> str:
        return "html"

    def export(
        self,
        data: InputData,
        config: ExportConfig,
        **kwargs: Any,
    ) -> str:
        """Export data as an HTML table.

        Args:
            data: Input data to export.
            config: Export configuration.
            **kwargs: Additional keyword arguments (unused).

        Returns:
            str: Output file path.
        """
        output_path = config.output_path or "output.html"
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        lines: list[str] = []
        lines.append("<!DOCTYPE html>")
        lines.append("<html><head><meta charset='utf-8'>")
        lines.append("<style>")
        lines.append("table { border-collapse: collapse; font-family: sans-serif; }")
        lines.append(
            "th, td { border: 1px solid #ccc; padding: 6px 12px; text-align: right; }"
        )
        lines.append("th { background: #f5f5f5; font-weight: bold; }")
        lines.append("tr:nth-child(even) { background: #fafafa; }")
        lines.append("</style></head><body>")
        lines.append("<table>\n<thead><tr>")

        # Header row
        if config.include_index and data.index is not None:
            lines.append("<th>index</th>")
        for col in data.columns:
            lines.append(f"<th>{col}</th>")
        lines.append("</tr></thead><tbody>")

        # Data rows
        for i in range(data.n_samples):
            lines.append("<tr>")
            if config.include_index and data.index is not None:
                lines.append(f"<td>{data.index[i]}</td>")
            for val in data.data[i]:
                cell = f"{val:.4f}" if isinstance(val, (int, float)) else str(val)
                lines.append(f"<td>{cell}</td>")
            lines.append("</tr>")

        lines.append("</tbody></table>")
        lines.append("</body></html>")

        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path.resolve())
