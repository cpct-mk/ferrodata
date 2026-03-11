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
m = read_dat("examples/[example data]PUND.dat")

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


## License

MIT
