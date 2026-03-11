"""Visualization functions for ferroelectric `PUND`, `DHM`, and `Fatigue` data."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .helpers import find_suffix_column, parse_metadata_float
from .types import DataTable


def _field_axis_scale(field_unit: str) -> tuple[float, str]:
    """Return field-axis conversion settings from base SI units (V/m).

    Parameters
    ----------
    field_unit:
        Target field unit. Supported values: `kV/cm`, `MV/cm`, `MV/m`.

    Returns
    -------
    tuple[float, str]
        `(divider, label)` where `field = value_in_V_per_m / divider`.
    """

    normalized = field_unit.strip()
    if normalized == "kV/cm":
        return 1e5, "Electric field (kV/cm)"
    if normalized == "MV/cm":
        return 1e8, "Electric field (MV/cm)"
    if normalized == "MV/m":
        return 1e6, "Electric field (MV/m)"
    return 1.0, "Electric field (V/m)"


def _remove_baseline(signal: np.ndarray, n_points: int = 10) -> np.ndarray:
    """Remove baseline offset by subtracting mean of leading/trailing windows."""

    if signal.size == 0:
        return signal
    n_eff = min(n_points, signal.size // 5 if signal.size >= 20 else max(1, signal.size // 10))
    if n_eff <= 0:
        return signal
    edge_mean = (np.mean(signal[:n_eff]) + np.mean(signal[-n_eff:])) / 2.0
    return signal - edge_mean


def _extract_pund_columns(table: DataTable) -> dict[str, np.ndarray]:
    """Extract P/U/N/D waveform columns from one PUND table.

    The expected column layout is:
    - P: columns `0..3` as `Time, V, I, P`
    - U: columns `4..7`
    - N: columns `8..11`
    - D: columns `12..15`
    """

    if table.data.ndim != 2 or table.data.shape[1] < 16:
        raise ValueError(f"{table.name}: expected at least 16 columns for a PUND waveform table.")

    data = table.data
    return {
        "time_p": data[:, 0],
        "voltage_p": data[:, 1],
        "current_p": data[:, 2],
        "polarization_p": data[:, 3],
        "time_u": data[:, 4],
        "voltage_u": data[:, 5],
        "current_u": data[:, 6],
        "polarization_u": data[:, 7],
        "time_n": data[:, 8],
        "voltage_n": data[:, 9],
        "current_n": data[:, 10],
        "polarization_n": data[:, 11],
        "time_d": data[:, 12],
        "voltage_d": data[:, 13],
        "current_d": data[:, 14],
        "polarization_d": data[:, 15],
    }


def plot_pund(
    table: DataTable,
    field_unit: str = "MV/cm",
    baseline_points: int = 10,
    figsize: tuple[float, float] = (9.0, 2.4),
):
    """Plot one PUND waveform table.

    Subplots include:
    1. Raw current traces (`P`, `U`, `N`, `D`) vs voltage.
    2. Switched current density (`P-U`, `N-D`) vs electric field.
    3. Baseline-corrected polarization (`PU`, `ND`) vs electric field.

    Parameters
    ----------
    table:
        PUND waveform table.
    field_unit:
        Target field unit (`kV/cm`, `MV/cm`, `MV/m`, or `V/m` fallback).
    baseline_points:
        Number of edge points used for baseline subtraction.
    figsize:
        Matplotlib figure size.

    Returns
    -------
    tuple
        `(figure, (ax_raw, ax_current_density, ax_polarization))`.
    """

    columns = _extract_pund_columns(table)

    area_mm2 = parse_metadata_float(table.metadata, "Area [mm2]")
    thickness_nm = parse_metadata_float(table.metadata, "Thickness [nm]")
    area_m2 = area_mm2 * 1e-6 if np.isfinite(area_mm2) else np.nan
    thickness_m = thickness_nm * 1e-9 if np.isfinite(thickness_nm) else np.nan

    field_divider, field_label = _field_axis_scale(field_unit)

    def as_field(voltage: np.ndarray) -> np.ndarray:
        """Convert voltage to electric field in selected units."""

        if np.isfinite(thickness_m) and thickness_m > 0:
            return voltage / thickness_m / field_divider
        return voltage.copy()

    switched_p = columns["current_p"] - columns["current_u"]
    switched_n = columns["current_n"] - columns["current_d"]
    if np.isfinite(area_m2) and area_m2 > 0:
        switched_p = switched_p / area_m2 / 1e4  # A/cm^2
        switched_n = switched_n / area_m2 / 1e4  # A/cm^2

    polarization_pu = _remove_baseline(
        columns["polarization_p"] - columns["polarization_u"],
        baseline_points,
    )
    polarization_nd = _remove_baseline(
        columns["polarization_n"] - columns["polarization_d"],
        baseline_points,
    )

    figure, (ax_raw, ax_current_density, ax_polarization) = plt.subplots(1, 3, figsize=figsize)

    ax_raw.plot(columns["voltage_p"], columns["current_p"], label="P")
    ax_raw.plot(columns["voltage_u"], columns["current_u"], label="U")
    ax_raw.plot(columns["voltage_n"], columns["current_n"], label="N")
    ax_raw.plot(columns["voltage_d"], columns["current_d"], label="D")
    ax_raw.set_xlabel("Voltage (V)")
    ax_raw.set_ylabel("Raw current (A)")

    ax_current_density.plot(as_field(columns["voltage_p"]), switched_p, label="P-U")
    ax_current_density.plot(as_field(columns["voltage_n"]), switched_n, label="N-D")
    ax_current_density.set_xlabel(field_label)
    ax_current_density.set_ylabel("Current density (A/cm$^2$)")

    ax_polarization.plot(as_field(columns["voltage_p"]), polarization_pu, label="PU")
    ax_polarization.plot(as_field(columns["voltage_n"]), polarization_nd, label="ND")
    ax_polarization.set_xlabel(field_label)
    ax_polarization.set_ylabel(r"Polarization ($\mu$C/cm$^2$)")

    sample_name = table.metadata.get("SampleName", "")
    frequency_hz = parse_metadata_float(table.metadata, "Pund Frequency [Hz]")
    frequency_suffix = f", {frequency_hz:.0f} Hz" if np.isfinite(frequency_hz) else ""
    figure.suptitle(f"{table.name} {sample_name}{frequency_suffix}".strip(), y=1.08)
    figure.subplots_adjust(wspace=0.45)

    return figure, (ax_raw, ax_current_density, ax_polarization)


def plot_dhm(
    table: DataTable,
    field_unit: str = "MV/cm",
    figsize: tuple[float, float] = (9.0, 2.6),
):
    """Plot one DHM waveform table.

    Subplots include:
    1. Voltage waveform vs time.
    2. Current trace(s) vs electric field.
    3. Polarization trace(s) vs electric field.

    Parameters
    ----------
    table:
        DHM waveform table.
    field_unit:
        Target field unit (`kV/cm`, `MV/cm`, `MV/m`, or `V/m` fallback).
    figsize:
        Matplotlib figure size.

    Returns
    -------
    tuple
        `(figure, (ax_voltage, ax_current, ax_polarization))`.
    """

    if table.data.ndim != 2 or table.data.shape[1] < 5:
        raise ValueError(f"{table.name}: expected at least 5 columns for a DHM waveform table.")

    header_to_index = {header: idx for idx, header in enumerate(table.headers)}
    data = table.data

    time = data[:, header_to_index["Time [s]"]] if "Time [s]" in header_to_index else data[:, 0]
    voltage_pos = data[:, header_to_index["V+ [V]"]] if "V+ [V]" in header_to_index else data[:, 1]
    voltage_neg = data[:, header_to_index["V- [V]"]] if "V- [V]" in header_to_index else voltage_pos

    current_1 = data[:, header_to_index["I1 [A]"]] if "I1 [A]" in header_to_index else data[:, 3]
    polarization_1 = data[:, header_to_index["P1 [uC/cm2]"]] if "P1 [uC/cm2]" in header_to_index else data[:, 4]
    current_2 = data[:, header_to_index["I2 [A]"]] if "I2 [A]" in header_to_index else None
    polarization_2 = data[:, header_to_index["P2 [uC/cm2]"]] if "P2 [uC/cm2]" in header_to_index else None
    current_3 = data[:, header_to_index["I3 [A]"]] if "I3 [A]" in header_to_index else None
    polarization_3 = data[:, header_to_index["P3 [uC/cm2]"]] if "P3 [uC/cm2]" in header_to_index else None

    thickness_nm = parse_metadata_float(table.metadata, "Thickness [nm]")
    thickness_m = thickness_nm * 1e-9 if np.isfinite(thickness_nm) else np.nan
    field_divider, field_label = _field_axis_scale(field_unit)

    def as_field(voltage: np.ndarray) -> np.ndarray:
        """Convert voltage to electric field in selected units."""

        if np.isfinite(thickness_m) and thickness_m > 0:
            return voltage / thickness_m / field_divider
        return voltage.copy()

    field_pos = as_field(voltage_pos)
    field_neg = as_field(voltage_neg)

    figure, (ax_voltage, ax_current, ax_polarization) = plt.subplots(1, 3, figsize=figsize)

    ax_voltage.plot(time, voltage_pos, label="V+")
    if "V- [V]" in header_to_index:
        ax_voltage.plot(time, voltage_neg, label="V-")
    ax_voltage.set_xlabel("Time (s)")
    ax_voltage.set_ylabel("Voltage (V)")

    ax_current.plot(field_pos, current_1, label="I1")
    if current_2 is not None:
        ax_current.plot(field_neg, current_2, label="I2")
    if current_3 is not None:
        ax_current.plot(field_pos, current_3, label="I3")
    ax_current.set_xlabel(field_label)
    ax_current.set_ylabel("Current (A)")

    ax_polarization.plot(field_pos, polarization_1, label="P1")
    if polarization_2 is not None:
        ax_polarization.plot(field_neg, polarization_2, label="P2")
    if polarization_3 is not None:
        ax_polarization.plot(field_pos, polarization_3, label="P3")
    ax_polarization.set_xlabel(field_label)
    ax_polarization.set_ylabel(r"Polarization ($\mu$C/cm$^2$)")

    sample_name = table.metadata.get("SampleName", "")
    frequency_hz = parse_metadata_float(table.metadata, "Hysteresis Frequency [Hz]")
    frequency_suffix = f", {frequency_hz:.0f} Hz" if np.isfinite(frequency_hz) else ""
    figure.suptitle(f"{table.name} {sample_name}{frequency_suffix}".strip(), y=1.08)
    figure.subplots_adjust(wspace=0.45)

    return figure, (ax_voltage, ax_current, ax_polarization)


def plot_fatigue(result_table: DataTable, figsize: tuple[float, float] = (8.0, 3.1)):
    """Plot fatigue summary metrics versus cycle count.

    Parameters
    ----------
    result_table:
        Fatigue summary table with `Cycles [n]` and polarization metrics.
    figsize:
        Matplotlib figure size.

    Returns
    -------
    tuple
        `(figure, (ax_remanent, ax_switching))`.
    """

    if result_table.data.ndim != 2 or result_table.data.shape[0] == 0:
        raise ValueError("Fatigue result table has no numeric rows to plot.")

    headers = result_table.headers
    data = result_table.data

    idx_cycles = find_suffix_column(headers, "Cycles [n]")
    idx_pr_plus = find_suffix_column(headers, "Pr+ [uC/cm2]")
    idx_pr_minus = find_suffix_column(headers, "Pr- [uC/cm2]")
    idx_psw = find_suffix_column(headers, "Psw [uC/cm2]")
    idx_pnsw = find_suffix_column(headers, "Pnsw [uC/cm2]")
    idx_dpsw = find_suffix_column(headers, "dPsw [uC/cm2]")

    if idx_cycles is None:
        raise ValueError("Cycles column not found in fatigue result table.")

    cycles = data[:, idx_cycles]
    valid = np.isfinite(cycles) & (cycles > 0)
    cycles = cycles[valid]

    figure, (ax_remanent, ax_switching) = plt.subplots(1, 2, figsize=figsize)

    if idx_pr_plus is not None:
        ax_remanent.semilogx(cycles, data[:, idx_pr_plus][valid], marker="o", label="Pr+")
    if idx_pr_minus is not None:
        ax_remanent.semilogx(cycles, data[:, idx_pr_minus][valid], marker="o", label="Pr-")
    ax_remanent.set_xlabel("Cycles")
    ax_remanent.set_ylabel(r"Remanent polarization ($\mu$C/cm$^2$)")
    ax_remanent.grid(True, which="both", alpha=0.3)
    if ax_remanent.get_legend_handles_labels()[0]:
        ax_remanent.legend(frameon=False)

    if idx_psw is not None:
        ax_switching.semilogx(cycles, data[:, idx_psw][valid], marker="o", label="Psw")
    if idx_pnsw is not None:
        ax_switching.semilogx(cycles, data[:, idx_pnsw][valid], marker="o", label="Pnsw")
    if idx_dpsw is not None:
        ax_switching.semilogx(cycles, data[:, idx_dpsw][valid], marker="o", label="dPsw")
    ax_switching.set_xlabel("Cycles")
    ax_switching.set_ylabel(r"Switching polarization ($\mu$C/cm$^2$)")
    ax_switching.grid(True, which="both", alpha=0.3)
    if ax_switching.get_legend_handles_labels()[0]:
        ax_switching.legend(frameon=False)

    sample_name = result_table.metadata.get("SampleName", "")
    figure.suptitle(f"{result_table.name} {sample_name}".strip(), y=1.05)
    figure.subplots_adjust(wspace=0.35)

    return figure, (ax_remanent, ax_switching)

