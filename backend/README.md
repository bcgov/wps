# WPS Backend

Python workspace containing all backend packages managed by uv.

## Structure

```
backend/
├── packages/
│   ├── wps-api/      # Main API application
│   ├── wps-jobs/     # Background jobs
│   ├── wps-sfms/     # SFMS processing
│   ├── wps-shared/   # Shared utilities
│   ├── wps-tools/    # Tooling / scripts
│   ├── wps-weather/  # Weather model processing
│   └── wps-wf1/      # WF1 (WFWX) integration
├── .venv/            # Single virtual environment
├── pyproject.toml    # Workspace configuration
└── uv.lock           # Dependency lock file
```

## Getting Started

You will need an environment file at the **repo root**: copy `.env.example` (in the repo root) to `.env`. python-decouple discovers it by walking up from the package directory, so it must live at the repo root, not in `backend/`. Contact current maintainers for current variable settings.

### Installing

- Automated (mac only):
  - Run `setup/mac.sh` in parent folder
  - Follow [manual setup](../docs/MANUAL_SETUP.md) for database setup notes as of Nov 2024.
  - Follow [vsc setup steps](../setup/VSC.md)
- Manual (linux): See [manual setup](../docs/MANUAL_SETUP.md).
  Note: you may want to alias `python3` as `python` in your profile

### Setup

- Installation section above is completed
- `.env` is correctly configured in the repo root

### Install Dependencies

```bash
cd wps/backend
uv sync --all-extras
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run tests for a specific package (see pytest.ini for the full list of test paths)
uv run pytest packages/wps-api/src
uv run pytest packages/wps-jobs/src
uv run pytest packages/wps-sfms/src
uv run pytest packages/wps-shared/src
uv run pytest packages/wps-weather/src
uv run pytest packages/wps-wf1/src
uv run pytest packages/wps-tools/tests

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

Each package can be built independently. Run these from the **repo root** (the
Dockerfiles and their build context live there, not in `backend/`):

```bash
# API image
docker build -f Dockerfile -t wps-api .

# Jobs image
docker build -f Dockerfile.jobs -t wps-jobs .
```

The `--package` flag in Dockerfiles ensures only needed dependencies are installed.
