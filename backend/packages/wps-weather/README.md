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
