# Regenerate SFMS Daily Actuals

Use `app.jobs.sfms_daily_backfill` to regenerate SFMS daily actuals for an inclusive date range. For a single actuals date, set `START_DATE` and `END_DATE` to the same date.

Historical forecasts cannot be regenerated from WF1 because WF1 forecast records are overwritten by actuals. If today's forecast job needs to be rerun, use the deployed CronJob directly.

## OpenShift Backfill Job

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

Set `CONTINUE_ON_ERROR=true` when generating the YAML if you want the pod to attempt later dates after a date fails. The Job will still fail at the end if any date failed.

Run and watch it:

```bash
oc -n ${PROJ_TARGET} apply -f /tmp/${JOB_NAME}.yaml
oc -n ${PROJ_TARGET} logs -f job/${JOB_NAME}
```

Backfills overwrite the same SFMS raster keys for each target date and create new `sfms_run` / `sfms_run_log` rows for auditability.

For FWI regeneration, the first date in the range needs the previous day's actual FFMC/DMC/DC rasters to exist unless the first date is one of the April/May Monday re-interpolation days. If those seed rasters are missing, the actual weather rasters are still regenerated but FWI calculation is skipped.
