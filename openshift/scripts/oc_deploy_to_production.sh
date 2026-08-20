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
# wps-weather isn't always rebuilt if nothing in it changed, in which case there's no PR
# image to promote and oc_promote_gh.sh exits 0, leaving "prod" pointing at whatever it
# already was. An actual promotion failure (registry/auth/network error) exits non-zero 
#and fails this deploy like everything else here. The resulting path is always
# ghcr.io/bcgov/wps/wps-weather:prod, which the provisioning scripts below
# already default WEATHER_IMAGE to (since they're called with SUFFIX=prod).
PACKAGE=wps-weather bash $(dirname ${0})/oc_promote_gh.sh ${SUFFIX} ${RUN_TYPE}

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

echo Fuel Grid Install
PROJ_TARGET=${PROJ_TARGET} FUEL_RASTER_YEAR=2026 FUEL_GRID_INSTALL_SUSPEND=true bash $(dirname ${0})/oc_provision_fuel_grid_install_job.sh prod ${RUN_TYPE}

# 20 independent CronJobs, migrated to Kustomize (openshift/kustomize/ -- see its
# README) -- this replaces the hand-rolled batch-file mechanism entirely. `oc kustomize`
# is a fully local render (unlike `oc process`, confirmed this week to hit the API
# server by default); SUFFIX is substituted with a plain sed pass since it's genuinely
# dynamic per run, not something Kustomize's static overlays can express.
echo "Applying batched CronJobs via Kustomize..."
if [ "${RUN_TYPE}" = "apply" ]; then
	oc kustomize $(dirname ${0})/../kustomize/overlays/prod \
		| sed "s/__SUFFIX__/${SUFFIX}/g; s/__NAMESPACE__/${PROJ_TARGET}/g" \
		| oc -n ${PROJ_TARGET} apply -f -
else
	oc kustomize $(dirname ${0})/../kustomize/overlays/prod \
		| sed "s/__SUFFIX__/${SUFFIX}/g; s/__NAMESPACE__/${PROJ_TARGET}/g" \
		| oc -n ${PROJ_TARGET} apply -f - --dry-run
fi

# Not yet migrated (see openshift/kustomize/README.md): backup_s3_postgres_cronjob's
# param wiring doesn't follow the pattern every other cronjob script does, and needs
# individual investigation before converting.
echo Configure backups
PROJ_TARGET=${PROJ_TARGET} CPU_REQUEST=1000m bash $(dirname ${0})/oc_provision_backup_s3_postgres_cronjob.sh prod | oc -n ${PROJ_TARGET} apply -f -

echo Logging alerts
cat $(dirname ${0})/../logging-alerts/nats_alerts.yaml | oc -n ${PROJ_TARGET} apply -f -
cat $(dirname ${0})/../logging-alerts/sfms_alerts.yaml | oc -n ${PROJ_TARGET} apply -f -
oc -n ${PROJ_TARGET} process -f $(dirname ${0})/../logging-alerts/oom_alerts.yaml -o yaml -p NAMESPACE=e1e498-prod -p SEVERITY=critical | oc -n ${PROJ_TARGET} apply -f -
