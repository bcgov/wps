#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#
# OpenShift Deploy Helper
#   
#   Pulls in logic for SUFFIX variable when declaring PR name
#   Intended for use with a pull request-based pipeline.
#   Suffixes incl.: pr-###.
#
# Usage:
#                         
#    [PROJ_TARGET] ${THIS_FILE} [SUFFIX] [RUN-TYPE]
#
# Examples:
#
#   Provide a PR number.
#
#   PROJ_TARGET=e1e498-prod ${THIS_FILE} pr-0 apply
#   ${THIS_FILE} pr-0 dry-run
#
RUN_TYPE=$2
# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

set -ex
echo Promote
MODULE_NAME=api bash $(dirname ${0})/oc_promote.sh ${SUFFIX} ${RUN_TYPE}
MODULE_NAME=web bash $(dirname ${0})/oc_promote.sh ${SUFFIX} ${RUN_TYPE}
MODULE_NAME=jobs bash $(dirname ${0})/oc_promote.sh ${SUFFIX} ${RUN_TYPE}
MODULE_NAME=s3-backup bash $(dirname ${0})/oc_promote.sh ${SUFFIX} ${RUN_TYPE}

# wps-weather lives on GHCR now, promoted via a registry-side copy rather than `oc tag`.
# wps-weather isn't always rebuilt if nothing in it changed, in which case there's no PR
# image to promote and oc_promote_gh.sh exits 0, leaving "prod" pointing at whatever it
# already was. An actual promotion failure (registry/auth/network error) exits non-zero 
#and fails this deploy like everything else here. The resulting path is always
# ghcr.io/bcgov/wps/wps-weather:prod, which the provisioning scripts below
# already default WEATHER_IMAGE to (since they're called with SUFFIX=prod).
PACKAGE=wps-weather bash $(dirname ${0})/oc_promote_gh.sh ${SUFFIX} ${RUN_TYPE}

# Everything below is rendered locally (`oc process --local`, no API calls) into one file
# and applied with a single `oc apply`, followed by rollout checks and post-apply steps.
# Connections to the OpenShift API server intermittently fail mid-deploy, so every call
# saved is one less chance of a failed deploy.
BATCH_FILE=$(mktemp)

FUEL_RASTER_YEAR=2026
FUEL_GRID_INSTALL_SUSPEND=true

echo Configure NATS server
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_nats_server_config.sh prod render >>"${BATCH_FILE}"
echo Provision database
PROJ_TARGET=${PROJ_TARGET} BUCKET=lwzrin CPU_REQUEST=2 MEMORY_REQUEST=2Gi MEMORY_LIMIT=16Gi DATA_SIZE=65Gi WAL_SIZE=15Gi REPLICAS=3 bash $(dirname ${0})/oc_provision_crunchy.sh prod render >>"${BATCH_FILE}"
echo Provision NATS
PROJ_TARGET=${PROJ_TARGET} ENVIRONMENT="production" bash $(dirname ${0})/oc_provision_nats.sh prod render >>"${BATCH_FILE}"
echo Deploy API
MODULE_NAME=api GUNICORN_WORKERS=8 CPU_REQUEST=100m MEMORY_REQUEST=6Gi MEMORY_LIMIT=8Gi REPLICAS=3 PROJ_TARGET=${PROJ_TARGET} VANITY_DOMAIN=psu.nrs.gov.bc.ca SECOND_LEVEL_DOMAIN=apps.silver.devops.gov.bc.ca ENVIRONMENT="production" bash $(dirname ${0})/oc_deploy.sh prod render >>"${BATCH_FILE}"
echo Deploy ASA Go API
PROJ_TARGET=${PROJ_TARGET} ENVIRONMENT="production" bash $(dirname ${0})/oc_deploy_asa_go_api.sh prod render >>"${BATCH_FILE}"
echo Allow APS to reach ASA Go API
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_asa_go_gateway_networkpolicy.sh prod render >>"${BATCH_FILE}"
echo Deploy SFMS Daily FWI API
PROJ_TARGET=${PROJ_TARGET} ENVIRONMENT="production" bash $(dirname ${0})/oc_deploy_sfms_fwi_api.sh prod render >>"${BATCH_FILE}"
echo Allow APS to reach SFMS Daily FWI API
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_sfms_fwi_gateway_networkpolicy.sh prod render >>"${BATCH_FILE}"

echo ECCC Consumer
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_eccc_grib_consumer.sh prod render >>"${BATCH_FILE}"

echo Fuel Grid Install
PROJ_TARGET=${PROJ_TARGET} FUEL_RASTER_YEAR=${FUEL_RASTER_YEAR} FUEL_GRID_INSTALL_SUSPEND=${FUEL_GRID_INSTALL_SUSPEND} bash $(dirname ${0})/oc_provision_fuel_grid_install_job.sh prod render >>"${BATCH_FILE}"

echo S3 Data Retention
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_s3_data_retention.sh prod >>"${BATCH_FILE}"
echo Env Canada Subscriber
PROJ_TARGET=${PROJ_TARGET} MEMORY_REQUEST=1Gi MEMORY_LIMIT=2Gi bash $(dirname ${0})/oc_provision_ec_gdps_cronjob.sh prod >>"${BATCH_FILE}"
PROJ_TARGET=${PROJ_TARGET} MEMORY_REQUEST=1Gi MEMORY_LIMIT=2Gi bash $(dirname ${0})/oc_provision_ec_hrdps_cronjob.sh prod >>"${BATCH_FILE}"
PROJ_TARGET=${PROJ_TARGET} MEMORY_REQUEST=1Gi MEMORY_LIMIT=2Gi bash $(dirname ${0})/oc_provision_ec_rdps_cronjob.sh prod >>"${BATCH_FILE}"
echo NOAA Subscriber
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_noaa_gfs_cronjob.sh prod >>"${BATCH_FILE}"
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_noaa_nam_cronjob.sh prod >>"${BATCH_FILE}"
echo ECMWF Subscriber
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_ecmwf_cronjob.sh prod >>"${BATCH_FILE}"
echo VIIRS Snow
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_viirs_snow_cronjob.sh prod >>"${BATCH_FILE}"
echo Grass Curing
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_grass_curing_cronjob.sh prod >>"${BATCH_FILE}"
echo RDPS for SFMS
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_rdps_sfms_cronjob.sh prod >>"${BATCH_FILE}"
echo SFMS Raster Calculations
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_sfms_calculations_cronjob.sh prod >>"${BATCH_FILE}"
echo SFMS Daily Actuals
PROJ_TARGET=${PROJ_TARGET} MEMORY_REQUEST=1Gi MEMORY_LIMIT=2Gi bash $(dirname ${0})/oc_provision_sfms_daily_actuals_cronjob.sh prod >>"${BATCH_FILE}"
echo SFMS Forecast 15:00 UTC- 8:00 AM PDT
PROJ_TARGET=${PROJ_TARGET} MEMORY_REQUEST=1Gi MEMORY_LIMIT=2Gi JOB_SUFFIX=8am SCHEDULE="0 15 * * *" bash $(dirname ${0})/oc_provision_sfms_daily_forecasts_cronjob.sh prod >>"${BATCH_FILE}"
echo SFMS Forecast 00:45 UTC - 5:45 PM PDT
PROJ_TARGET=${PROJ_TARGET} MEMORY_REQUEST=1Gi MEMORY_LIMIT=2Gi JOB_SUFFIX=545pm SCHEDULE="45 0 * * *" bash $(dirname ${0})/oc_provision_sfms_daily_forecasts_cronjob.sh prod >>"${BATCH_FILE}"
echo Fire Watch Weather Calculations
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_fire_watch_weather_cronjob.sh prod >>"${BATCH_FILE}"
echo BC FireWeather cronjobs
echo "Run forecast at 8h30 PDT and 16h30 PDT (so before and after noon)"
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="30 * * * *" bash $(dirname ${0})/oc_provision_wfwx_noon_forecasts_cronjob.sh prod >>"${BATCH_FILE}"
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="15 * * * *" bash $(dirname ${0})/oc_provision_wfwx_hourly_actuals_cronjob.sh prod >>"${BATCH_FILE}"
echo "Configure partitioner to run every month on day 1 at 00:00"
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="0 6 1 * *" bash $(dirname ${0})/oc_provision_partitioner_cronjob.sh prod >>"${BATCH_FILE}"
echo Configure backups
PROJ_TARGET=${PROJ_TARGET} CPU_REQUEST=1000m bash $(dirname ${0})/oc_provision_backup_s3_postgres_cronjob.sh prod >>"${BATCH_FILE}"
echo Configure hourly pruner
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="0 2 * * *" bash $(dirname ${0})/oc_provision_hourly_prune_cronjob.sh prod >>"${BATCH_FILE}"
echo Configure GDPS 4panel charts
PROJ_TARGET=${PROJ_TARGET} END_HOUR=240 STEP=6 MODEL=GDPS bash $(dirname ${0})/oc_provision_wx_4panel_charts_cronjob.sh prod >>"${BATCH_FILE}"
echo Configure RDPS 4panel charts
PROJ_TARGET=${PROJ_TARGET} END_HOUR=84 STEP=3 MODEL=RDPS bash $(dirname ${0})/oc_provision_wx_4panel_charts_cronjob.sh prod >>"${BATCH_FILE}"

echo Logging alerts
oc -n ${PROJ_TARGET} process --local -f $(dirname ${0})/../logging-alerts/nats_alerts.yaml >>"${BATCH_FILE}"
oc -n ${PROJ_TARGET} process --local -f $(dirname ${0})/../logging-alerts/sfms_alerts.yaml >>"${BATCH_FILE}"
oc -n ${PROJ_TARGET} process --local -f $(dirname ${0})/../logging-alerts/oom_alerts.yaml -p NAMESPACE=e1e498-prod -p SEVERITY=critical >>"${BATCH_FILE}"

echo "Applying batched manifests in one call..."
if [ "${RUN_TYPE}" = "apply" ]; then
	oc -n ${PROJ_TARGET} apply -f "${BATCH_FILE}"
else
	oc -n ${PROJ_TARGET} apply -f "${BATCH_FILE}" --dry-run
	exit 0
fi

echo Waiting for rollouts
wait_for_rollouts "${APP_NAME}-prod" "${APP_NAME}-prod-asa-go" "${APP_NAME}-prod-sfms-fwi"

# The ECCC consumer's image tag (prod) doesn't change between releases, so re-applying its
# manifest doesn't roll it; restart it to pick up the newly promoted image.
echo Restart ECCC Consumer
oc -n ${PROJ_TARGET} rollout restart deployment/${APP_NAME}-prod-eccc-consumer

if [ "${FUEL_GRID_INSTALL_SUSPEND}" != "true" ]; then
	echo Unsuspend Fuel Grid Install
	oc -n ${PROJ_TARGET} patch "job/fuel-grid-install-${FUEL_RASTER_YEAR}-${APP_NAME}-prod" --type=merge -p '{"spec":{"suspend":false}}'
fi
