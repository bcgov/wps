# wps-weather

Weather maps and meteorological data processing for Wildfire Predictive Services Unit.

Contains utilities for fetching, processing, and visualizing weather data including maps, forecasts, and meteorological datasets.

## Standalone installation with uv

### Installing uv

First, install uv if you don't have it:

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Homebrew:**
```bash
HOMEBREW_NO_AUTO_UPDATE=1 brew install uv
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Winget:**
```powershell
winget install --id=astral-sh.uv -e
```

**Alternative (using pip):**
```bash
pip install uv
```

### Installing the package

To install in a separate virtual environment:

```bash
# Navigate to the package directory
cd packages/wps-weather

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On macOS/Linux
# or: .venv\Scripts\activate  # On Windows

# Install the package
uv pip install .
```

### Using standard pip

```bash
cd packages/wps-weather
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Dependencies

This package includes:
- **Data processing**: numpy, xarray, scipy, pandas
- **Geospatial**: geopandas, shapely, pyproj, fiona, cartopy
- **Visualization**: matplotlib
- **Interactive development**: jupyter, notebook, jupyterlab

## Development

### Adding new Python files

Add new Python modules to `src/wps_weather/`. They will be automatically available for import as `from wps_weather.your_module import ...`

Optionally export them from `src/wps_weather/__init__.py` for easier access.

## Local Weather Toolkit charts

The repository's local object-store sidecar can hold both downloaded ECCC GRIB inputs
and generated four-panel charts without requiring deployed S3 credentials. Copy
`external-contributor-api.env` to the repository root as `.env`, then start the sidecar
with `make local-object-store-up`. In VS Code, run `Weather - Local 4Panel Charts` and
enter a published model date, model, and run hour. This launch downloads the required
inputs and generates charts without the chart status database. The existing RDPS and
GDPS chart launches need GRIB inputs and Postgres.

The same bounded backfill can be run from the repository root without VS Code:

```bash
uv run --project backend --package wps-weather python \
  -m wps_weather.wx_4panel_charts.backfill \
  --model RDPS \
  --init-ymd "$(date -u +%Y%m%d)" \
  --model-run 00 \
  --end-hour 12
```

Required arguments deliberately identify the model, UTC model-run date, run hour, and
ending forecast hour so a local setup does not unexpectedly download a complete model
run. `--start-hour` defaults to `0`, and `--max-concurrent-downloads` defaults to `4`.
Use a recent archived date if today's `00` run is not available yet. The command accepts
only a loopback object-store endpoint and uses public ECCC data to produce charts with
the same processor used by deployed jobs.
