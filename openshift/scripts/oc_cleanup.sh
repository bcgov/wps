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
OC_CLEAN_DEPLOY="oc -n ${PROJ_TARGET} ${DELETE_OR_GET} all,cm,pvc -o name -l app=${NAME_OBJ}"
# OC_DELETE_EC_PODS="oc -n ${PROJ_TARGET} get pods -o name | { grep -E 'env-canada-(gdps|rdps|hrdps)-${NAME_APP}-${SUFFIX}' || test \$? = 1; } | { xargs -r oc ${DELETE_OR_GET} || test \$? = 1; } | cat"
OC_CLEAN_MARIDB_BACKUP="oc -n ${PROJ_TARGET} ${DELETE_OR_GET} all,cm -o name -l app=backup-mariadb-${NAME_OBJ}"
OC_CLEAN_BACKUP_POSTGRES="oc -n ${PROJ_TARGET} ${DELETE_OR_GET} all,cm -o name -l app=backup-postgres-${NAME_OBJ}"

# Execute commands
#
echo -e "\n${PROJ_TARGET}:"
# eval "${OC_DELETE_EC_PODS}"
eval "${OC_CLEAN_DEPLOY}"
eval "${OC_CLEAN_MARIDB_BACKUP}"
eval "${OC_CLEAN_BACKUP_POSTGRES}"

# Provide oc command instruction
#
display_helper "${OC_CLEAN_DEPLOY}" \
	"${OC_CLEAN_MARIDB_BACKUP}" "${OC_CLEAN_BACKUP_POSTGRES}"
