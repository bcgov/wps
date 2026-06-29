# Run SFMS Daily Jobs in Production for a Specific Date

Use a one-off Job created from the production CronJob. Do not edit the CronJob.

Set these values first:

```bash
NAMESPACE=e1e498-prod
DATE=2026-06-16
DATE_ID=20260616
```

## Actuals

```bash
CRONJOB=$(oc -n ${NAMESPACE} get cronjob -o name | grep sfms-daily-actuals | head -1)
oc -n ${NAMESPACE} create job sfms-daily-actuals-${DATE_ID} \
  --from=${CRONJOB} \
  --dry-run=client -o yaml > /tmp/sfms-daily-actuals-${DATE_ID}.yaml
```

Edit `/tmp/sfms-daily-actuals-${DATE_ID}.yaml` and append the date to the container `command`:

```yaml
- "app.jobs.sfms_daily_actuals"
- "2026-06-16"
```

Run and watch it:

```bash
oc -n ${NAMESPACE} apply -f /tmp/sfms-daily-actuals-${DATE_ID}.yaml
oc -n ${NAMESPACE} logs -f job/sfms-daily-actuals-${DATE_ID}
```

## Forecasts

Choose the forecast CronJob to copy from:

```bash
oc -n ${NAMESPACE} get cronjob | grep sfms-forecast
```

Then create the one-off Job:

```bash
CRONJOB=cronjob/<cronjob-name>
oc -n ${NAMESPACE} create job sfms-forecast-${DATE_ID} \
  --from=${CRONJOB} \
  --dry-run=client -o yaml > /tmp/sfms-forecast-${DATE_ID}.yaml
```

Edit `/tmp/sfms-forecast-${DATE_ID}.yaml` and append the date to the container `command`:

```yaml
- "app.jobs.sfms_daily_forecasts"
- "2026-06-16"
```

Run and watch it:

```bash
oc -n ${NAMESPACE} apply -f /tmp/sfms-forecast-${DATE_ID}.yaml
oc -n ${NAMESPACE} logs -f job/sfms-forecast-${DATE_ID}
```

Actuals process `DATE` at `20:00 UTC`. Forecasts process the next three forecast dates after `DATE`, each at `20:00 UTC`.

## Date Range Backfill

Use the `app.jobs.sfms_daily_backfill` wrapper when you need to regenerate actuals for more than one day. It runs dates sequentially in one OpenShift Job.

The range is inclusive. Historical forecasts cannot be regenerated from WF1 because WF1 forecast records are overwritten by actuals.

Generate a one-off Job from the actuals CronJob so it inherits the same image, database, WF1, Redis, object-store, and ChatOps configuration:

```bash
PROJ_TARGET=e1e498-prod
START_DATE=2026-06-25
END_DATE=2026-06-27
JOB_NAME=sfms-daily-backfill-${START_DATE//-/}-to-${END_DATE//-/}

PROJ_TARGET=${PROJ_TARGET} \
START_DATE=${START_DATE} \
END_DATE=${END_DATE} \
JOB_NAME=${JOB_NAME} \
bash openshift/scripts/oc_generate_sfms_daily_backfill_job.sh prod \
  > /tmp/${JOB_NAME}.yaml
```

The generated YAML replaces the copied CronJob command with:

```yaml
command:
  - "uv"
  - "run"
  - "--package"
  - "wps-api"
  - "--no-sync"
  - "python"
  - "-m"
  - "app.jobs.sfms_daily_backfill"
  - "--start-date"
  - "2026-06-25"
  - "--end-date"
  - "2026-06-27"
```

Set `CONTINUE_ON_ERROR=true` when generating the YAML if you want the pod to attempt later dates after a date fails. The Job will still fail at the end if any date failed.

Run and watch it:

```bash
oc -n ${PROJ_TARGET} apply -f /tmp/${JOB_NAME}.yaml
oc -n ${PROJ_TARGET} logs -f job/${JOB_NAME}
```

Backfills overwrite the same SFMS raster keys for each target date and create new `sfms_run` / `sfms_run_log` rows for auditability.

For actual FWI regeneration, the first date in the range needs the previous day's actual FFMC/DMC/DC rasters to exist unless the first date is one of the April/May Monday re-interpolation days. If those seed rasters are missing, the actual weather rasters are still regenerated but FWI calculation is skipped.
