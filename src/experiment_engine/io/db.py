"""SQLite database data source and writer for experiment-engine.

Provides :class:`SQLiteDataSource` for loading data from SQLite databases
as :class:`InputData`, and :class:`SQLiteDataWriter` for exporting
:class:`InputData` into SQLite tables.

Uses only the Python standard library ``sqlite3`` module – no extra
dependencies required.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import numpy as np

from experiment_engine.io.exporters import BaseExporter
from experiment_engine.io.sources import DataSource
from experiment_engine.models import ExportConfig, InputData

# ──────────────────────────────────────────────
#  SQLite DataSource
# ──────────────────────────────────────────────


class SQLiteDataSource(DataSource):
    """DataSource that loads data from a SQLite database via a SQL query.

    Executes a parameterised SQL query against a SQLite database file and
    converts the result set into an :class:`InputData` object.  Column names
    are taken from the query result's ``description`` attribute.

    Parameters
    ----------
    db_path : str or Path
        Path to the SQLite database file.
    query : str
        SQL ``SELECT`` query to execute.
    params : tuple, optional
        Parameters to bind to the query (for parameterised queries).

    Examples
    --------
    >>> ds = SQLiteDataSource("experiments.db", "SELECT * FROM results")
    >>> data = ds.load()
    >>> data.n_samples, data.columns
    (100, ['run_id', 'score', 'duration'])
    """

    def __init__(
        self,
        db_path: str | Path,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> None:
        # DataSource base expects a reader & location – we pass None
        # because SQLiteDataSource is self-contained.
        super().__init__(reader=None, location=str(db_path))  # type: ignore[arg-type]
        self.db_path = Path(db_path)
        self.query = query
        self.params = params

    def load(self, **kwargs: Any) -> InputData:
        """Execute the SQL query and return results as InputData.

        Parameters
        ----------
        **kwargs :
            Ignored (included for API compatibility with the DataSource ABC).

        Returns
        -------
        InputData
            Data with a 2-D float64 numpy array, column names from the
            query result, and metadata about the query.

        Raises
        ------
        sqlite3.OperationalError
            If the database file cannot be opened or the query is invalid.
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {self.db_path}")

        conn = sqlite3.connect(str(self.db_path))
        try:
            cur = conn.execute(self.query, self.params)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
        finally:
            conn.close()

        # Convert to numpy array (float64)
        arr = np.array(rows, dtype=float) if rows else np.empty((0, len(columns)))

        metadata: dict[str, Any] = {
            "source": str(self.db_path),
            "query": self.query,
            "params": self.params,
            "n_rows": len(rows),
            "n_cols": len(columns),
        }

        return InputData(
            data=arr,
            columns=columns,
            index=None,
            metadata=metadata,
        )


# ──────────────────────────────────────────────
#  SQLite DataWriter
# ──────────────────────────────────────────────


class SQLiteDataWriter(BaseExporter):
    """Writes :class:`InputData` into a SQLite database table.

    Parameters
    ----------
    table_name : str
        Name of the target table.
    if_exists : str, optional
        Behaviour when the table already exists:

        - ``"replace"`` – drop the table and recreate it (default).
        - ``"append"``  – insert rows into the existing table.
        - ``"fail"``    – raise :class:`ValueError`.

    Examples
    --------
    >>> writer = SQLiteDataWriter("results")
    >>> path = writer.export(data, ExportConfig(output_path="out.db"))
    """

    def __init__(
        self,
        table_name: str,
        if_exists: str = "replace",
    ) -> None:
        if if_exists not in ("replace", "append", "fail"):
            raise ValueError(
                f"if_exists must be 'replace', 'append', or 'fail'; got {if_exists!r}"
            )
        self.table_name = table_name
        self.if_exists = if_exists

    @property
    def name(self) -> str:
        return "sqlite"

    def export(
        self,
        data: InputData,
        config: ExportConfig,
        **kwargs: Any,
    ) -> str:
        """Export *data* into a SQLite table.

        The output path is taken from ``config.output_path``; if not
        provided it defaults to ``"output.db"``.

        Parameters
        ----------
        data : InputData
            The data to write.  Uses ``data.data`` (2-D array) and
            ``data.columns`` (column names).
        config : ExportConfig
            Must contain ``output_path`` pointing to the ``.db`` file.
        **kwargs :
            Ignored (included for API compatibility with BaseExporter).

        Returns
        -------
        str
            Absolute path to the created database file.
        """
        output_path = config.output_path or "output.db"
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        columns = data.columns or [f"col_{i}" for i in range(data.n_features)]
        conn = sqlite3.connect(str(path))
        try:
            self._write_table(conn, data, columns)
            conn.commit()
        finally:
            conn.close()

        return str(path.resolve())

    def _write_table(
        self,
        conn: sqlite3.Connection,
        data: InputData,
        columns: list[str],
    ) -> None:
        """Create or prepare the table and insert data rows."""
        table = self.table_name

        # ── handle if_exists ──────────────────────────────────────
        if self.if_exists == "replace":
            conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        elif self.if_exists == "fail":
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
            if cur.fetchone() is not None:
                raise ValueError(f"Table {table!r} already exists and if_exists='fail'")

        # ── create table ──────────────────────────────────────────
        col_defs = ", ".join(f'"{c}" REAL' for c in columns)
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs})')

        # ── insert rows ───────────────────────────────────────────
        placeholders = ", ".join("?" for _ in columns)
        insert_sql = f'INSERT INTO "{table}" VALUES ({placeholders})'
        rows = [tuple(row.tolist()) for row in data.data]
        conn.executemany(insert_sql, rows)


# ──────────────────────────────────────────────
#  PostgreSQL stubs  (optional / future work)
# ──────────────────────────────────────────────


class PostgreSQLDataSource:
    """DataSource that loads data from a PostgreSQL database.

    **Requires** ``psycopg2-binary`` to be installed:

    .. code-block:: bash

        pip install psycopg2-binary

    Parameters
    ----------
    dsn : str
        PostgreSQL connection string (e.g.
        ``"host=localhost dbname=mydb user=me password=secret"``).
    query : str
        SQL query to execute.
    params : tuple, optional
        Query parameters.

    Usage
    -----
    .. code-block:: python

        ds = PostgreSQLDataSource("host=... dbname=test", "SELECT * FROM data")
        data = ds.load()

    .. note::

        This is a stub implementation.  Install ``psycopg2-binary`` and
        replace the body of :meth:`load` with real ``psycopg2`` logic.
    """

    def __init__(
        self,
        dsn: str,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> None:
        self.dsn = dsn
        self.query = query
        self.params = params

    def load(self, **kwargs: Any) -> InputData:
        raise NotImplementedError(
            "PostgreSQLDataSource requires psycopg2-binary. "
            "Install it with: pip install psycopg2-binary"
        )


class PostgreSQLDataWriter:
    """Writes :class:`InputData` into a PostgreSQL table.

    **Requires** ``psycopg2-binary`` to be installed.

    Parameters
    ----------
    dsn : str
        PostgreSQL connection string.
    table_name : str
        Target table name.
    if_exists : str, optional
        ``"replace"``, ``"append"``, or ``"fail"`` (default ``"replace"``).

    .. note::

        This is a stub implementation.  Install ``psycopg2-binary`` and
        adapt the :meth:`export` body from :class:`SQLiteDataWriter`.
    """

    def __init__(
        self,
        dsn: str,
        table_name: str,
        if_exists: str = "replace",
    ) -> None:
        self.dsn = dsn
        self.table_name = table_name
        self.if_exists = if_exists

    def export(
        self,
        data: InputData,
        config: ExportConfig,
        **kwargs: Any,
    ) -> str:
        raise NotImplementedError(
            "PostgreSQLDataWriter requires psycopg2-binary. "
            "Install it with: pip install psycopg2-binary"
        )
