"""Shared helper utilities used across `ferrodata` modules."""

from __future__ import annotations

import re
from typing import Optional

import numpy as np


def to_float_token(token: str) -> float:
    """Convert one text token to float, handling AixACCT non-standard values.

    Parameters
    ----------
    token:
        Raw token string from a data table cell.

    Returns
    -------
    float
        Parsed numeric value. Unparseable or empty tokens become `NaN`.

    Notes
    -----
    Handles values like `1.#INF00e+000`, `-1.#INF00e+000`, and `#NAN`.
    """

    value = token.strip()
    if not value:
        return np.nan

    upper = value.upper()
    if "#INF" in upper:
        return -np.inf if value.startswith("-") else np.inf
    if "#NAN" in upper or "#IND" in upper:
        return np.nan

    try:
        return float(value.replace("D", "E"))
    except ValueError:
        return np.nan


def split_tsv(raw_line: str) -> list[str]:
    """Split one tab-separated line and trim trailing empty fields."""

    parts = raw_line.rstrip("\n").split("\t")
    while parts and parts[-1] == "":
        parts.pop()
    return [part.strip() for part in parts]


def parse_metadata_float(metadata: dict[str, str], key: str, default: float = np.nan) -> float:
    """Read one metadata entry as float.

    Parameters
    ----------
    metadata:
        Metadata dictionary.
    key:
        Metadata key.
    default:
        Value returned when the key is absent.

    Returns
    -------
    float
        Parsed float value or `default` when key is absent.
    """

    if key not in metadata:
        return default
    return to_float_token(metadata[key])


def safe_name(text: str) -> str:
    """Create a filesystem-safe, compact string from free text."""

    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", text.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "table"


def find_suffix_column(headers: list[str], suffix: str) -> Optional[int]:
    """Return the first header index that ends with `suffix`.

    Parameters
    ----------
    headers:
        List of header names.
    suffix:
        Suffix to match.

    Returns
    -------
    Optional[int]
        Matching index or `None` when no header matches.
    """

    for index, header in enumerate(headers):
        if header.endswith(suffix):
            return index
    return None

