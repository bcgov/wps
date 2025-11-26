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

## Getting Started

You will need an environment file. See: `.env.example`. Contact current maintainers for current variable settings.

### Installing

- Automated (mac only):
  - Run `setup/mac.sh` in parent folder
  - Follow [manual setup](../docs/MANUAL_SETUP.md) for database setup notes as of Nov 2024.
  - Follow [vsc setup steps](../setup/VSC.md)
- Manual (linux): See [manual setup](../docs/MANUAL_SETUP.md).
  Note: you may want to alias `python3` as `python` in your profile

### Setup

- Installation section above is completed
- `.env` is correctly configured in the project root
- this dynamic library is set in the env: `DYLD_LIBRARY_PATH=/Library/Frameworks/R.framework/Resources/lib`

### Install Dependencies

```bash
cd wps/backend
uv sync --all-extras
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
