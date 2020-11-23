#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Cleanup Helper
#%
#%   Intended for use with a pull request-based pipeline.
#%   Suffixes incl.: pr-###
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

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

OC_CLEAN_MATOMO_BACKUP="oc -n ${PROJ_DEV} ${DELETE_OR_GET} all,cm -o name -l app=${NAME_OBJ}"
OC_CLEAN_MATOMO_BACKUP_PVC="oc -n ${PROJ_DEV} ${DELETE_OR_GET} pvc -o name -l app=${NAME_OBJ}-persistent"
OC_CLEAN_MATOMO_CRONJOB="oc -n ${PROJ_DEV} ${DELETE_OR_GET} cronjob/matomo-backup-${NAME_OBJ}"

# Execute commands
#
echo -e "\n${PROJ_TARGET}:" 
eval "${OC_CLEAN_MATOMO_CRONJOB}"
eval "${OC_CLEAN_MATOMO_BACKUP}"
eval "${OC_CLEAN_MATOMO_BACKUP_PVC}"


# Provide oc command instruction
#
display_helper "${OC_CLEAN_MATOMO_BACKUP}" "${OC_CLEAN_MATOMO_BACKUP_PVC}" "${OC_CLEAN_MATOMO_CRONJOB}"