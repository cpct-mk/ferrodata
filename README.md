# ferrodata

A minimal Python package to read, export, and visualize ferroelectric AixACCT `.dat` files.

Supported measurement types:
- PUND (`PulseResult`)
- DHM (`DynamicHysteresisResult`)
- Fatigue (`Fatigue`)

## Features
- Parse `.dat` files into structured Python objects
- Export parsed tables to human-readable CSV
- Plot:
  - PUND waveform/current-density/polarization views
  - DHM voltage/current/polarization views
  - Fatigue summary vs cycle count

## Project Layout

- `src/ferrodata/`: package source code
- `notebooks/ferrodata_walkthrough.ipynb`: guided end-to-end tutorial
- `examples/`: sample raw `.dat` files for testing

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from ferrodata import (
    read_dat,
    get_waveform_tables,
    get_fatigue_result_table,
    export_all_tables_csv,
    plot_pund,
    plot_dhm,
    plot_fatigue,
)

# Parse
m = read_dat("examples/[example data]WMO 1-2-2 10IDE D1 PUND.dat")

# Export CSV
export_all_tables_csv(m, "out_csv")

# Plot
wf = get_waveform_tables(m)[0]
fig, _ = plot_pund(wf)
```

## Notebook

Open the tutorial notebook:

```bash
jupyter notebook notebooks/ferrodata_walkthrough.ipynb
```

## Publish To GitHub

This project includes a helper script:

```bash
./publish_to_github.sh <github-username> <repo-name>
```

Before publishing, ensure:
1. `git` works in your terminal.
2. Your local git identity is configured:
   `git config --global user.name "Your Name"`
   `git config --global user.email "you@example.com"`
3. The target GitHub repo exists (or create it at `https://github.com/new`).

## License

MIT
