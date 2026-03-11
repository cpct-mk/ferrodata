"""Parsing utilities for AixACCT ferroelectric `.dat` files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional

import numpy as np

from .helpers import split_tsv, to_float_token
from .types import DataTable, MeasurementFile, MeasurementType


_TABLE_START_RE = re.compile(r"^(Table \d+|Result Table \d+|Data Table \[[^\]]+\])\s*$")
_META_RE = re.compile(r"^([^:\t]+):\s*(.*)$")


def _detect_measurement_type(lines: Iterable[str]) -> MeasurementType:
    """Infer measurement type from the first non-empty line."""

    first_non_empty = ""
    for line in lines:
        stripped = line.strip()
        if stripped:
            first_non_empty = stripped
            break

    if first_non_empty.startswith("PulseResult"):
        return MeasurementType.PUND
    if first_non_empty.startswith("DynamicHysteresisResult"):
        return MeasurementType.DHM
    if first_non_empty.startswith("Fatigue"):
        return MeasurementType.FATIGUE
    return MeasurementType.UNKNOWN


def _parse_numeric_row(raw_line: str, width: int) -> list[float]:
    """Parse one numeric TSV line into fixed-width float values."""

    fields = split_tsv(raw_line)
    if len(fields) < width:
        fields += [""] * (width - len(fields))
    elif len(fields) > width:
        fields = fields[:width]
    return [to_float_token(token) for token in fields]


def read_dat(filepath: str | Path) -> MeasurementFile:
    """Read one AixACCT ferroelectric `.dat` file.

    Parameters
    ----------
    filepath:
        Path to an input `.dat` file.

    Returns
    -------
    MeasurementFile
        Parsed file object containing metadata and tables.

    Notes
    -----
    Parsing strategy is generic and format-driven:
    - Table starts are matched using `Table ...`, `Result Table ...`, and `Data Table [...]`.
    - Per-table metadata is parsed from `key: value` lines.
    - Data header is identified as the first tab-separated line in a table section.
    - Data rows are parsed as floats with robust fallback to `NaN`.
    """

    path = Path(filepath)
    lines = path.read_text(encoding="cp1252").splitlines()
    measurement_type = _detect_measurement_type(lines)
    parsed = MeasurementFile(path=path, measurement_type=measurement_type)

    current_name: Optional[str] = None
    current_metadata: dict[str, str] = {}
    current_headers: list[str] = []
    current_rows: list[list[float]] = []
    in_table = False

    def finish_table() -> None:
        """Append the current table to `parsed` and reset temporary state."""

        nonlocal current_name, current_metadata, current_headers, current_rows, in_table
        if current_name is None:
            in_table = False
            return

        if current_headers and current_rows:
            data = np.asarray(current_rows, dtype=float)
        elif current_headers:
            data = np.empty((0, len(current_headers)), dtype=float)
        else:
            data = np.empty((0, 0), dtype=float)

        parsed.tables.append(
            DataTable(
                name=current_name,
                metadata=dict(current_metadata),
                headers=list(current_headers),
                data=data,
            )
        )

        current_name = None
        current_metadata = {}
        current_headers = []
        current_rows = []
        in_table = False

    index = 0
    while index < len(lines):
        raw_line = lines[index].rstrip("\n")
        stripped = raw_line.strip()

        if _TABLE_START_RE.match(stripped):
            finish_table()
            current_name = stripped
            current_metadata = {}
            current_headers = []
            current_rows = []
            in_table = True
            index += 1
            continue

        if not in_table:
            match = _META_RE.match(stripped)
            if match:
                parsed.global_metadata[match.group(1).strip()] = match.group(2).strip()
            index += 1
            continue

        if not stripped:
            if current_headers and current_rows:
                finish_table()
            index += 1
            continue

        if not current_headers:
            if "\t" in raw_line and ":" not in raw_line.split("\t", 1)[0]:
                current_headers = split_tsv(raw_line)
            else:
                match = _META_RE.match(stripped)
                if match:
                    current_metadata[match.group(1).strip()] = match.group(2).strip()
            index += 1
            continue

        if "\t" in raw_line:
            current_rows.append(_parse_numeric_row(raw_line, len(current_headers)))
            index += 1
            continue

        finish_table()
        continue

    finish_table()
    return parsed


def get_waveform_tables(measurement: MeasurementFile) -> list[DataTable]:
    """Return tables whose first header starts with `Time [s]`."""

    return [
        table
        for table in measurement.tables
        if table.headers and table.headers[0].startswith("Time [s]")
    ]


def get_fatigue_result_table(measurement: MeasurementFile) -> DataTable:
    """Return the fatigue summary table with first column `Cycles [n]`.

    Raises
    ------
    ValueError
        If no fatigue result table exists in `measurement`.
    """

    for table in measurement.tables:
        if table.headers and table.headers[0].startswith("Cycles [n]"):
            return table
    raise ValueError("No fatigue result table found (expected first column: 'Cycles [n]').")

