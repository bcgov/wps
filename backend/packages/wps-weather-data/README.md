# wps_weather_data module

This package reads and writes station weather data in object storage. The design is in
[docs/architecture/station-weather-storage.md](../../../docs/architecture/station-weather-storage.md).

## table.py

`DeltaWeatherTable` is what the Delta Lake tables share: where the table lives, the storage
options for reaching it, and `maintain()`, the upkeep every table needs (`optimize` merges
small files, a checkpoint keeps the transaction log quick to open, and `vacuum` deletes files
that no table version from the last 30 days refers to). Create a table object once and reuse
it; creating one does not contact the object store.

## runs.py

`RunsTable` is the `runs` dataset: station values from every weather model run.
`append_run` writes one version of a run in a single commit. `read` returns the newest version
of each run, and every reader should go through it so that rule lives in one place.

## staging.py

`StagingTable` is a model's `staging` dataset: the station values of runs that are still
downloading, one table per model. A job stages the files it processes with `append_files`, and
each file leaves a marker row in the same commit, so `processed_sources` tells what is done.
Once every file of a run is staged, the job reads it back with `station_values`, publishes the
run to `runs` and `by_time`, then calls `delete_run`.

## by_time.py

`ByTimeTable` is the `by_time` dataset: the newest value per station, time and source.
`merge_run` merges a model run in after it is appended to `runs`. A row is only replaced by a
run at least as new as the one it came from. `read` returns a time range for one resolution
(`hourly` or `daily`) and a list of sources. Only model sources are written so far.

## maintenance.py

Runs `maintain()` on every table. Run by the `station-weather-maintenance` cron job:

```bash
python -m wps_weather_data.maintenance
```

## addresser.py

`StationWeatherAddresser` builds the object store keys, in the style of `BaseRasterAddresser`.
Production tables live under `weather/stations/`. Dev deployments share one bucket, so each
writes under `dev/{suffix}/weather/stations/`, using the `SUFFIX` setting (for example
`pr-123`). With no `SUFFIX`, as when running locally, the production root is used.

## Status

The model jobs (GDPS, RDPS, HRDPS, GFS, NAM and ECMWF) keep no station data in Postgres: they
stage runs in `staging`, publish them to `runs` and `by_time`, and train the bias adjustments on
`runs`. The API reads MoreCast's model values from `by_time` (`morecast.py`) and fire watch's
from `runs` (`fire_watch.py`). Postgres still holds the station observations that training and
24 hour precip use.

`backend/scripts/station_weather_backfill.py` copies runs from the legacy Postgres tables into
`runs` and `by_time`, to fill a deployment's tables.
