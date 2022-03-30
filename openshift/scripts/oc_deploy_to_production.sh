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
bash oc_promote.sh ${SUFFIX} ${RUN_TYPE}
bash oc_promote_ubuntu.sh ${SUFFIX} ${RUN_TYPE}
echo Provision database
CPU_REQUEST=75m CPU_LIMIT=2000m MEMORY_REQUEST=2Gi MEMORY_LIMIT=16Gi PVC_SIZE=45Gi PROJ_TARGET=${PROJ_TARGET} bash oc_provision_db.sh ${PROJ_TARGET} ${RUN_TYPE}
echo Deploy API
CPU_REQUEST=100m CPU_LIMIT=500m MEMORY_REQUEST=3Gi MEMORY_LIMIT=4Gi REPLICAS=3 PROJ_TARGET=${PROJ_TARGET} VANITY_DOMAIN=psu.nrs.gov.bc.ca SECOND_LEVEL_DOMAIN=apps.silver.devops.gov.bc.ca bash ./oc_deploy.sh ${PROJ_TARGET} ${RUN_TYPE}
echo Env Canada Subscriber
PROJ_TARGET=${PROJ_TARGET} bash oc_provision_ec_gdps_cronjob.sh ${PROJ_TARGET} ${RUN_TYPE}
PROJ_TARGET=${PROJ_TARGET} bash oc_provision_ec_hrdps_cronjob.sh ${PROJ_TARGET} ${RUN_TYPE}
PROJ_TARGET=${PROJ_TARGET} bash oc_provision_ec_rdps_cronjob.sh ${PROJ_TARGET} ${RUN_TYPE}
echo C-Haines
PROJ_TARGET=${PROJ_TARGET} bash oc_provision_c_haines_cronjob.sh ${PROJ_TARGET} ${RUN_TYPE}
echo BC FireWeather cronjobs
echo "Run forecast at 8h30 PDT and 16h30 PDT (so before and after noon)"
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="30 * * * *" bash oc_provision_wfwx_noon_forecasts_cronjob.sh ${PROJ_TARGET} ${RUN_TYPE}
PROJ_TARGET=${PROJ_TARGET} SCHEDULE="15 * * * *" bash oc_provision_wfwx_hourly_actuals_cronjob.sh ${PROJ_TARGET} ${RUN_TYPE}
echo Configure backups
PROJ_TARGET=${PROJ_TARGET} CPU_REQUEST=1000m CPU_LIMIT=2000m bash oc_provision_backup_s3_postgres_cronjob.sh ${PROJ_TARGET} ${RUN_TYPE}
PROJ_TARGET=${PROJ_TARGET} CPU_REQUEST=50m CPU_LIMIT=500m BACKUP_VOLUME_SIZE=3Gi bash oc_provision_backup_mariadb.sh ${PROJ_TARGET} ${RUN_TYPE}
PROJ_TARGET=${PROJ_TARGET} CPU_REQUEST=50m CPU_LIMIT=500m bash oc_provision_backup_mariadb_cronjob.sh ${PROJ_TARGET} ${RUN_TYPE}
echo Configure
PROJ_TARGET=${PROJ_TARGET} CERTBOT_STAGING=false DRYRUN=false bash oc_provision_certbot_cronjob.sh ${PROJ_TARGET} ${RUN_TYPE}
