"""Data models for parsed ferroelectric measurement files."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import numpy as np


class MeasurementType(Enum):
    """Supported ferroelectric measurement types."""

    PUND = "pund"
    DHM = "dhm"
    FATIGUE = "fatigue"
    UNKNOWN = "unknown"


@dataclass
class DataTable:
    """One parsed table from a ferroelectric `.dat` file.

    Attributes
    ----------
    name:
        Table title (for example `Table 1` or `Data Table [1,2]`).
    metadata:
        Metadata entries attached to this table.
    headers:
        Column names parsed from the table header row.
    data:
        Numeric data with shape `(n_rows, n_columns)`.
    """

    name: str
    metadata: dict[str, str] = field(default_factory=dict)
    headers: list[str] = field(default_factory=list)
    data: np.ndarray = field(default_factory=lambda: np.empty((0, 0), dtype=float))

    def has_column(self, name: str) -> bool:
        """Return `True` when `name` exists in table headers."""

        return name in self.headers

    def column_index(self, name: str) -> int:
        """Return the 0-based index of a column header.

        Parameters
        ----------
        name:
            Exact column header to locate.

        Returns
        -------
        int
            Index of `name` in `headers`.

        Raises
        ------
        ValueError
            If `name` is not present.
        """

        return self.headers.index(name)


@dataclass
class MeasurementFile:
    """Parsed representation of one measurement file.

    Attributes
    ----------
    path:
        Input `.dat` file path.
    measurement_type:
        Type inferred from the first non-empty line in the file.
    global_metadata:
        Metadata parsed outside of table blocks.
    tables:
        Parsed tables in the order they appear in the file.
    """

    path: Path
    measurement_type: MeasurementType
    global_metadata: dict[str, str] = field(default_factory=dict)
    tables: list[DataTable] = field(default_factory=list)

