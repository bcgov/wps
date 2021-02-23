#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Cleanup Helper
#%
#%   Intended for use with a pull request-based pipeline.
#%   Suffixes incl.: pr-###, test and prod.
#%
#% Usage:
#%
#%   ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Default only returns object names.
#%   ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} pr-0 apply
#%

# Delete (apply) or get (not apply) items matching the a label
#
if [ "${APPLY}" ]; then
	DELETE_OR_GET="delete"
else
	DELETE_OR_GET="get"
fi
OC_CLEAN_DEPLOY="oc -n ${PROJ_DEV} ${DELETE_OR_GET} all,cm -o name -l app=${NAME_OBJ}"
OC_CLEAN_HOURLY_CRONJOB="oc -n ${PROJ_DEV} ${DELETE_OR_GET} --ignore-not-found=true cronjob/bcfw-p1-hourly-actuals-${NAME_APP}-${SUFFIX}"
OC_CLEAN_FORECAST_CRONJOB="oc -n ${PROJ_DEV} ${DELETE_OR_GET} --ignore-not-found=true cronjob/bcfw-p1-forecasts-${NAME_APP}-${SUFFIX}"
OC_CLEAN_EC_GDPS_CRONJOB="oc -n ${PROJ_DEV} ${DELETE_OR_GET} --ignore-not-found=true cronjob/env-canada-gdps-${NAME_APP}-${SUFFIX}"
OC_CLEAN_EC_HRDPS_CRONJOB="oc -n ${PROJ_DEV} ${DELETE_OR_GET} --ignore-not-found=true cronjob/env-canada-hrdps-${NAME_APP}-${SUFFIX}"
OC_CLEAN_EC_RDPS_CRONJOB="oc -n ${PROJ_DEV} ${DELETE_OR_GET} --ignore-not-found=true cronjob/env-canada-rdps-${NAME_APP}-${SUFFIX}"
OC_DELETE_EC_PODS="oc -n ${PROJ_DEV} get pods -o name | { grep -E 'env-canada-(gdps|rdps|hrdps)-${NAME_APP}-${SUFFIX}' || test \$? = 1; } | { xargs -r oc ${DELETE_OR_GET} || test \$? = 1; } | cat"
OC_CLEAN_MATOMO_BACKUP="oc -n ${PROJ_DEV} ${DELETE_OR_GET} all,cm -o name -l app=${NAME_OBJ}"
OC_CLEAN_MATOMO_BACKUP_PVC="oc -n ${PROJ_DEV} ${DELETE_OR_GET} pvc -o name -l app=${NAME_OBJ}-persistent"
OC_CLEAN_MATOMO_CRONJOB="oc -n ${PROJ_DEV} ${DELETE_OR_GET} --ignore-not-found=true cronjob/matomo-backup-${NAME_OBJ}"
OC_CLEAN_BACKUP_POSTGRES="oc -n ${PROJ_DEV} ${DELETE_OR_GET} all,cm -o name -l app=backup-postgres-${NAME_OBJ}"
OC_CLEAN_BACKUP_POSTGRES_CRONJOB="oc -n ${PROJ_DEV} ${DELETE_OR_GET} cronjob/backup-postgres-${NAME_OBJ}"

# Execute commands
#
echo -e "\n${PROJ_DEV}:"
eval "${OC_CLEAN_EC_GDPS_CRONJOB}"
eval "${OC_CLEAN_EC_HRDPS_CRONJOB}"
eval "${OC_CLEAN_EC_RDPS_CRONJOB}"
eval "${OC_DELETE_EC_PODS}"
eval "${OC_CLEAN_DEPLOY}"
eval "${OC_CLEAN_HOURLY_CRONJOB}"
eval "${OC_CLEAN_FORECAST_CRONJOB}"
eval "${OC_CLEAN_MATOMO_CRONJOB}"
eval "${OC_CLEAN_MATOMO_BACKUP}"
eval "${OC_CLEAN_MATOMO_BACKUP_PVC}"
eval "${OC_CLEAN_BACKUP_POSTGRES}"
eval "${OC_CLEAN_BACKUP_POSTGRES_CRONJOB}"

# Provide oc command instruction
#
display_helper "${OC_CLEAN_DEPLOY}" "${OC_CLEAN_HOURLY_CRONJOB}" \
	"${OC_CLEAN_FORECAST_CRONJOB}" "${OC_CLEAN_EC_GDPS_CRONJOB}" "${OC_CLEAN_EC_HRDPS_CRONJOB}" \
	"${OC_CLEAN_EC_RDPS_CRONJOB}" "${OC_DELETE_EC_PODS}" \
	"${OC_CLEAN_MATOMO_CRONJOB}" "${OC_CLEAN_MATOMO_BACKUP}" "${OC_CLEAN_MATOMO_BACKUP_PVC}" \
	"${OC_CLEAN_BACKUP_POSTGRES}" "${OC_CLEAN_BACKUP_POSTGRES_CRONJOB}"
