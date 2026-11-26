# How to reprocess historical data

## Reprocessing snow data
- Reprocessing of snow data for specific dates can be done by manually deploying an OpenShift job using a provisioning script.
- OpenShift template: /openshift/templates/historic-snow-job.yaml
- Provisioning script: /openshift/scripts/oc_provision_historic_snow_job.sh

Example usage:
`PROJ_DEV="e1e498-dev" START_DATETIME="2024-06-28T12:00:00" END_DATETIME="2024-06-29T12:00:00" bash openshift/scripts/oc_provision_historic_snow_job.sh {SUFFIX} apply -f - `

## Backfilling station observations from the BCWS data mart
- The data mart (https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART/) has every station's hourly observations back to 1987. A one-off OpenShift job copies them into the `wf1` and `by_time` station weather tables in object storage, as hourly and daily `ACTUALS`.
- OpenShift template: /openshift/templates/station_actuals_data_mart_backfill_job.yaml
- Provisioning script: /openshift/scripts/oc_provision_station_actuals_data_mart_backfill_job.sh
- Code: `wps_weather_data.data_mart_backfill` in /backend/packages/wps-weather-data

Example usage:
`FROM_YEAR=2020 TO_YEAR=2026 bash openshift/scripts/oc_provision_station_actuals_data_mart_backfill_job.sh {SUFFIX} | oc -n e1e498-dev apply -f -`

Follow it with `oc -n e1e498-dev logs -f job/station-actuals-data-mart-backfill-wps-{SUFFIX}`. The job runs the deployment's jobs image and writes under that deployment's tables. It is not retried on failure: the log names the year that failed, and running it again from that year is safe, because copying a year twice changes nothing. Delete the job before creating it again.

## Bringing existing station weather tables up to date
- The FWI System indices, dewpoint, wind gust, grass curing, danger rating and observation validity were added to the `wf1`, `by_time` and `by_station` tables after some deployments had created them. `backend/scripts/station_weather_add_columns.py` adds the missing columns in place and keeps every stored row. It also sets the checkpoint interval on every table and writes a checkpoint, so each table checkpoints itself as it is written. Tables created after these changes already have both.
- Run it once, right after deploying the change: the code before it cannot write to a table with the columns, and the code after it cannot write to one without them. Running it again changes nothing.
- Then fill the columns: run the data mart backfill above for every year (`FROM_YEAR=1987`), and then the `by_station` rebuild below from 1987. Copying a year again fills the new columns of the rows the data mart wrote. A row the WF1 jobs fetched is kept as it is, so days fetched before the change keep null indices.

Example usage, from ./backend with the deployment's object store settings:
`uv run python scripts/station_weather_add_columns.py`

## Rebuilding the by_station table of station weather
- `by_station` is a copy of the `by_time` station weather table laid out by station, for climatology. A nightly cron job rebuilds its current year only. After backfilling earlier years into `by_time`, or correcting one, a one-off OpenShift job rebuilds every year from a given year to the current one.
- OpenShift template: /openshift/templates/station_weather_by_station_backfill_job.yaml
- Provisioning script: /openshift/scripts/oc_provision_station_weather_by_station_backfill_job.sh
- Code: `wps_weather_data.by_station` in /backend/packages/wps-weather-data

Example usage:
`FROM_YEAR=1987 bash openshift/scripts/oc_provision_station_weather_by_station_backfill_job.sh {SUFFIX} | oc -n e1e498-dev apply -f -`

Follow it with `oc -n e1e498-dev logs -f job/station-weather-by-station-backfill-wps-{SUFFIX}`. A year that fails is logged and the others still run; running the job again from that year is safe. Delete the job before creating it again.
