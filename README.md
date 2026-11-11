# Beam calculation and Pareto visualization

Tools for Team A, Assignment 1: calculate the mass, maximum deflection, and bending stress of a rectangular cantilever beam, and visualize HEEDS optimization results as interactive Pareto charts.

## Installation

Install Python 3.12 and run these commands from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pandas plotly
```

Use `.venv\Scripts\python.exe` instead of `python` in the commands below to use the virtual environment. The beam calculation itself needs no additional packages.

## Beam calculation

```powershell
python beam_calculation.py input.txt output.txt
```

Input uses one `name value` pair per line. Required parameters are `b`, `h`, `L` (mm), `F` (N), `E`, `sigma_allow` (MPa), and `rho` (kg/m³). Optional `g` defaults to 9.81 m/s². See [input.txt](input.txt) for an example. Results are written to `output.txt` for use in HEEDS.

## Pareto charts

Install `pandas` and `plotly` as above. Input CSV files must contain feasible designs only, with `mass_kg` and `deflection_mm` columns.

Generate a chart with a logarithmic Y axis:

```powershell
python pareto.py "csv/AufgabeA Opt_L400 Design Table.csv" --log-y --output pareto.html
```

Compare several CSV files in one chart:

```powershell
python pareto.py "csv/AufgabeA Opt_L400 Design Table.csv" "csv/AufgabeA Opt_L500 Design Table.csv" --log-y --output comparison.html
```

Add `--hide-all` to display only Pareto points. Each run also writes a `<source-name>_pareto.csv` next to each input file.

Double-click the generated HTML to open it in a browser. Charts are interactive and work offline because Plotly is embedded in each file.

## GitHub Actions

- **Generate Pareto HTML pages:** runs on every push to any branch, or manually. Reads all CSV files directly inside the root `csv/` folder and generates one HTML per file, always with `--log-y`. In the workflow run, download the **pareto-html** artifact, extract the ZIP, and open the HTML files in a browser. The artifact is retained for 30 days.
- **Build Windows executable:** runs on pushes to `main`, or manually. Packages `beam_calculation.py` as a Windows executable. Download and extract **beam-calculation-windows-x64**, then run `beam_calculation.exe input.txt output.txt`; Python is not required.

Commit `pareto.py`, the input `csv/` folder, and the workflow files so they are available to GitHub Actions.
