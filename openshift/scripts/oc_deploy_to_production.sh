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
echo Provision database
CPU_REQUEST=75m CPU_LIMIT=2000m MEMORY_REQUEST=2Gi MEMORY_LIMIT=16Gi PVC_SIZE=45Gi PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_db.sh prod ${RUN_TYPE}
echo Provision tileserv
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_tileserv.sh ${SUFFIX} apply
echo Provision NATS
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_nats.sh prod ${RUN_TYPE}
echo Deploy API
MODULE_NAME=api GUNICORN_WORKERS=8 CPU_REQUEST=100m CPU_LIMIT=500m MEMORY_REQUEST=3Gi MEMORY_LIMIT=6Gi REPLICAS=3 PROJ_TARGET=${PROJ_TARGET} VANITY_DOMAIN=psu.nrs.gov.bc.ca SECOND_LEVEL_DOMAIN=apps.silver.devops.gov.bc.ca bash $(dirname ${0})/oc_deploy.sh prod ${RUN_TYPE}
echo Env Canada Subscriber
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_ec_gdps_cronjob.sh prod ${RUN_TYPE}
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_ec_hrdps_cronjob.sh prod ${RUN_TYPE} 
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_ec_rdps_cronjob.sh prod ${RUN_TYPE}
echo C-Haines
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_c_haines_cronjob.sh prod ${RUN_TYPE}
echo BC FireWeather cronjobs
echo "Run forecast at 8h30 PDT and 16h30 PDT (so before and after noon)"
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="30 * * * *" bash $(dirname ${0})/oc_provision_wfwx_noon_forecasts_cronjob.sh prod ${RUN_TYPE}
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="15 * * * *" bash $(dirname ${0})/oc_provision_wfwx_hourly_actuals_cronjob.sh prod ${RUN_TYPE}
echo Configure backups
PROJ_TARGET=${PROJ_TARGET} CPU_REQUEST=1000m CPU_LIMIT=2000m bash $(dirname ${0})/oc_provision_backup_s3_postgres_cronjob.sh prod ${RUN_TYPE}
echo Configure
PROJ_TARGET=${PROJ_TARGET} CERTBOT_STAGING=false DRYRUN=false DEBUG=true bash $(dirname ${0})/oc_provision_certbot_cronjob.sh prod ${RUN_TYPE}
