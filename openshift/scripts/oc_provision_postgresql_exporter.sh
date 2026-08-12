#!/usr/bin/env bash
#
source "$(dirname "${0}")/common/common"

#%
#% postgresql exporter deploy helper
#%
#%   Deploys the Sysdig PostgreSQL exporter for production or a pull request database.
#%   Defaults to a dry run.
#%
#% Usage:
#%
#%   ${THIS_FILE} [prod|pr-####] [apply]
#%
#% Examples:
#%
#%   ${THIS_FILE} pr-5691
#%   ${THIS_FILE} pr-5691 apply
#%   ${THIS_FILE} prod
#%   ${THIS_FILE} prod apply
#%

if [ "${SUFFIX}" = "prod" ]; then
    PROJ_TARGET="${PROJ_PROD}"
elif [[ "${SUFFIX}" =~ ^pr-[0-9]+$ ]]; then
    PROJ_TARGET="${PROJ_DEV}"
else
    echo "Suffix must be 'prod' or match 'pr-####'."
    exit 1
fi

OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/postgresql_exporter.yaml \
-p SUFFIX=${SUFFIX} \
-p CRUNCHY_NAME=${CRUNCHY_NAME} \
-p PROJECT_NAMESPACE=${PROJ_TARGET} \
-p POSTGRES_DATABASE=${POSTGRES_DATABASE:-${APP_NAME}} \
${EXPORTER_IMAGE:+\"-p EXPORTER_IMAGE=${EXPORTER_IMAGE}\"}"

OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

display_helper "${OC_PROCESS} | ${OC_APPLY}"
