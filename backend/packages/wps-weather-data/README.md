# wps_weather_data module

This package reads and writes station weather data in object storage. The design is in
[docs/architecture/station-weather-storage.md](../../../docs/architecture/station-weather-storage.md).

## runs.py

The `runs` dataset: station values from every weather model run, as a Delta Lake table.
`append_run` writes one version of a run in a single commit. `read_runs` returns the newest
version of each run, and every reader should go through it so that rule lives in one place.

Only the GDPS job writes to `runs` so far, alongside its Postgres writes. Nothing reads it yet.
`backend/scripts/station_runs_parity_check.py` compares it with Postgres.
