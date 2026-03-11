"""CSV export helpers for parsed ferroelectric measurements."""

from __future__ import annotations

import csv
from pathlib import Path

from .helpers import safe_name
from .types import DataTable, MeasurementFile


def export_table_csv(table: DataTable, output_path: str | Path, include_metadata: bool = True) -> Path:
    """Export one parsed table to a human-readable CSV file.

    Parameters
    ----------
    table:
        Table to export.
    output_path:
        Destination CSV path.
    include_metadata:
        If `True`, writes table metadata as `# key: value` preamble rows.

    Returns
    -------
    Path
        Path to the written CSV file.
    """

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)

        if include_metadata:
            writer.writerow([f"# table: {table.name}"])
            for key, value in table.metadata.items():
                writer.writerow([f"# {key}: {value}"])

        if table.headers:
            writer.writerow(table.headers)

        if table.data.size:
            for row in table.data:
                writer.writerow(row.tolist())

    return out_path


def export_all_tables_csv(
    measurement: MeasurementFile,
    output_dir: str | Path,
    include_metadata: bool = True,
) -> list[Path]:
    """Export all tables from one measurement file into an output directory.

    Parameters
    ----------
    measurement:
        Parsed measurement object.
    output_dir:
        Destination directory for CSV files.
    include_metadata:
        If `True`, metadata preambles are included in each CSV.

    Returns
    -------
    list[Path]
        List of CSV file paths in export order.
    """

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    file_stem = safe_name(measurement.path.stem)

    for table_index, table in enumerate(measurement.tables, start=1):
        table_stem = safe_name(table.name)
        output_path = directory / f"{file_stem}_{table_index:02d}_{table_stem}.csv"
        outputs.append(export_table_csv(table, output_path, include_metadata=include_metadata))

    return outputs

