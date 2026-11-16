# wps_weather_data module

This package reads and writes station weather data in object storage. The design is in
[docs/architecture/station-weather-storage.md](../../../docs/architecture/station-weather-storage.md).

## runs.py

The `runs` dataset: station values from every weather model run, as a Delta Lake table.
`append_run` writes one version of a run in a single commit. `read_runs` returns the newest
version of each run, and every reader should go through it so that rule lives in one place.

## by_time.py

The `by_time` dataset: the newest value per station, time and source, as a Delta Lake table.
`merge_run` merges a model run in after it is appended to `runs`. A row is only replaced by a
run at least as new as the one it came from. `read_by_time` reads a time range for one
resolution (`hourly` or `daily`) and a list of sources. Only model sources are written so far.

## maintenance.py

The daily upkeep both tables need: `optimize` merges small files, a checkpoint keeps the
transaction log quick to open, and `vacuum` deletes files that no table version from the last
30 days refers to. Run by the `station-weather-maintenance` cron job:

```bash
python -m wps_weather_data.maintenance
```

## store.py

Where the tables live in object storage and the Delta Lake storage options for reaching them.

## Status

Only the GDPS job writes to these tables so far, alongside its Postgres writes. Nothing reads
them yet. `backend/scripts/station_runs_parity_check.py` compares `runs` with Postgres.
