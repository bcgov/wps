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
echo Configure
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_nats_server_config.sh prod ${RUN_TYPE}
echo Promote
MODULE_NAME=api bash $(dirname ${0})/oc_promote.sh ${SUFFIX} ${RUN_TYPE}
MODULE_NAME=web bash $(dirname ${0})/oc_promote.sh ${SUFFIX} ${RUN_TYPE}
MODULE_NAME=jobs bash $(dirname ${0})/oc_promote.sh ${SUFFIX} ${RUN_TYPE}

# wps-weather lives on GHCR now, promoted via a registry-side copy rather than `oc tag`.
# Tolerant of a missing PR image, same as the other modules -- wps-weather isn't always
# rebuilt if nothing in it changed, in which case "prod" just keeps pointing at whatever
# it already was. The resulting path is always ghcr.io/bcgov/wps/wps-weather:prod, which
# the provisioning scripts below already default WEATHER_IMAGE to (since they're called
# with SUFFIX=prod) -- nothing needs to be captured or passed through here.
PACKAGE=wps-weather bash $(dirname ${0})/oc_promote_gh.sh ${SUFFIX} ${RUN_TYPE} || true

echo Provision database
PROJ_TARGET=${PROJ_TARGET} BUCKET=lwzrin CPU_REQUEST=2 MEMORY_REQUEST=2Gi MEMORY_LIMIT=16Gi DATA_SIZE=65Gi WAL_SIZE=15Gi REPLICAS=3 bash $(dirname ${0})/oc_provision_crunchy.sh prod ${RUN_TYPE}

echo Provision NATS
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_nats.sh prod ${RUN_TYPE}
echo Deploy API
MODULE_NAME=api GUNICORN_WORKERS=8 CPU_REQUEST=100m MEMORY_REQUEST=6Gi MEMORY_LIMIT=8Gi REPLICAS=3 PROJ_TARGET=${PROJ_TARGET} VANITY_DOMAIN=psu.nrs.gov.bc.ca SECOND_LEVEL_DOMAIN=apps.silver.devops.gov.bc.ca ENVIRONMENT="production" bash $(dirname ${0})/oc_deploy.sh prod ${RUN_TYPE}
echo Deploy ASA Go API
PROJ_TARGET=${PROJ_TARGET} ENVIRONMENT="production" bash $(dirname ${0})/oc_deploy_asa_go_api.sh prod ${RUN_TYPE}
echo Allow APS to reach ASA Go API
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_asa_go_gateway_networkpolicy.sh prod ${RUN_TYPE}
echo Deploy SFMS Daily FWI API
PROJ_TARGET=${PROJ_TARGET} ENVIRONMENT="production" bash $(dirname ${0})/oc_deploy_sfms_fwi_api.sh prod ${RUN_TYPE}
echo Allow APS to reach SFMS Daily FWI API
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_sfms_fwi_gateway_networkpolicy.sh prod ${RUN_TYPE}

echo ECCC Consumer
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_eccc_grib_consumer.sh prod ${RUN_TYPE}
echo S3 Data Retention
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_s3_data_retention.sh prod ${RUN_TYPE}

echo Fuel Grid Install
PROJ_TARGET=${PROJ_TARGET} FUEL_RASTER_YEAR=2026 FUEL_GRID_INSTALL_SUSPEND=true bash $(dirname ${0})/oc_provision_fuel_grid_install_job.sh prod ${RUN_TYPE}
echo Env Canada Subscriber
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_ec_gdps_cronjob.sh prod ${RUN_TYPE}
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_ec_hrdps_cronjob.sh prod ${RUN_TYPE} 
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_ec_rdps_cronjob.sh prod ${RUN_TYPE}
echo NOAA Subscriber
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_noaa_gfs_cronjob.sh prod ${RUN_TYPE}
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_noaa_nam_cronjob.sh prod ${RUN_TYPE}
echo ECMWF Subscriber
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_ecmwf_cronjob.sh prod ${RUN_TYPE}
echo VIIRS Snow
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_viirs_snow_cronjob.sh prod ${RUN_TYPE}
echo Grass Curing
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_grass_curing_cronjob.sh prod ${RUN_TYPE}
echo RDPS for SFMS
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_rdps_sfms_cronjob.sh prod ${RUN_TYPE}
echo SFMS Raster Calculations
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_sfms_calculations_cronjob.sh prod ${RUN_TYPE}
echo SFMS Daily Actuals
PROJ_TARGET=${PROJ_TARGET} MEMORY_REQUEST=1Gi MEMORY_LIMIT=2Gi bash $(dirname ${0})/oc_provision_sfms_daily_actuals_cronjob.sh prod ${RUN_TYPE}
echo SFMS Forecast 15:00 UTC- 8:00 AM PDT
PROJ_TARGET=${PROJ_TARGET} MEMORY_REQUEST=1Gi MEMORY_LIMIT=2Gi JOB_SUFFIX=8am SCHEDULE="0 15 * * *" bash $(dirname ${0})/oc_provision_sfms_daily_forecasts_cronjob.sh prod ${RUN_TYPE}
echo SFMS Forecast 00:45 UTC - 5:45 PM PDT
PROJ_TARGET=${PROJ_TARGET} MEMORY_REQUEST=1Gi MEMORY_LIMIT=2Gi JOB_SUFFIX=545pm SCHEDULE="45 0 * * *" bash $(dirname ${0})/oc_provision_sfms_daily_forecasts_cronjob.sh prod ${RUN_TYPE}
echo Fire Watch Weather Calculations
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_fire_watch_weather_cronjob.sh prod ${RUN_TYPE}
echo BC FireWeather cronjobs
echo "Run forecast at 8h30 PDT and 16h30 PDT (so before and after noon)"
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="30 * * * *" bash $(dirname ${0})/oc_provision_wfwx_noon_forecasts_cronjob.sh prod ${RUN_TYPE}
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="15 * * * *" bash $(dirname ${0})/oc_provision_wfwx_hourly_actuals_cronjob.sh prod ${RUN_TYPE}
echo "Configure partitioner to run every month on day 1 at 00:00"
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="0 6 1 * *" bash $(dirname ${0})/oc_provision_partitioner_cronjob.sh prod ${RUN_TYPE}
echo Configure backups
PROJ_TARGET=${PROJ_TARGET} CPU_REQUEST=1000m bash $(dirname ${0})/oc_provision_backup_s3_postgres_cronjob.sh prod ${RUN_TYPE}
echo Configure hourly pruner
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="0 2 * * *" bash $(dirname ${0})/oc_provision_hourly_prune_cronjob.sh prod ${RUN_TYPE}
echo Configure GDPS 4panel charts
PROJ_TARGET=${PROJ_TARGET} END_HOUR=240 STEP=6 MODEL=GDPS bash $(dirname ${0})/oc_provision_wx_4panel_charts_cronjob.sh prod ${RUN_TYPE}
echo Configure RDPS 4panel charts
PROJ_TARGET=${PROJ_TARGET} END_HOUR=84 STEP=3 MODEL=RDPS bash $(dirname ${0})/oc_provision_wx_4panel_charts_cronjob.sh prod ${RUN_TYPE}
echo Logging alerts
oc apply -f $(dirname ${0})/../logging-alerts/nats_alerts.yaml
oc apply -f $(dirname ${0})/../logging-alerts/sfms_alerts.yaml
oc process -f $(dirname ${0})/../logging-alerts/oom_alerts.yaml -p NAMESPACE=e1e498-prod -p SEVERITY=critical | oc apply -f -
