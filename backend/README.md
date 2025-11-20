# WPS Backend

Python workspace containing all backend packages managed by uv.

## Structure

```
backend/
├── packages/
│   ├── wps-api/      # Main API application
│   ├── wps-jobs/     # Background jobs
│   └── wps-shared/   # Shared utilities
├── .venv/            # Single virtual environment
├── pyproject.toml    # Workspace configuration
└── uv.lock           # Dependency lock file
```

## Setup

### Install Dependencies

```bash
cd backend
uv sync
```

### Install GDAL (Development)

GDAL is platform-specific and installed separately:

```bash
# Check your system GDAL version
gdal-config --version

# Install matching Python bindings (replace X.X.X with your version)
uv pip install --no-build-isolation gdal==$(gdal-config --version)
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run tests for a specific package
uv run pytest packages/wps-api/src
uv run pytest packages/wps-jobs/src
uv run pytest packages/wps-shared/src

# Run a specific test file
uv run pytest packages/wps-shared/src/wps_shared/tests/test_fuel_raster.py
```

## VSCode Integration

The workspace is configured for VSCode with:
- Python interpreter: `backend/.venv/bin/python`
- Test discovery working directory: `backend/`
- Pytest configuration in `backend/pytest.ini`

After setup, tests should appear in the VSCode Test Explorer automatically.

## Package Management

### Add a dependency to a package

```bash
# Edit the package's pyproject.toml, then:
uv lock
uv sync
```

### Add a new package to the workspace

1. Create directory in `packages/`
2. Add `pyproject.toml`
3. It will be auto-discovered (using `members = ["packages/*"]`)

## Docker Images

Each package can be built independently:

```bash
# API image
docker build -f Dockerfile -t wps-api .

# Jobs image  
docker build -f Dockerfile.jobs -t wps-jobs .
```

The `--package` flag in Dockerfiles ensures only needed dependencies are installed.
