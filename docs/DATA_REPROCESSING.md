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
