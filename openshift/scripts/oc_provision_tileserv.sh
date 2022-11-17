#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Deploy Helper
#%
#%   Intended for use with a pull request-based pipeline.
#%   Suffixes incl.: pr-###.
#%
#% Usage:
#%
#%    ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Defaults to a dry-run.
#%   ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} pr-0 apply
#%


# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/tileserv/tileserv.yaml \
-p SUFFIX=${SUFFIX}"

# Nginx build
OC_NGINX_BUILD="oc -n ${PROJ_TARGET} new-build nginx~https://github.com/bcgov/wps-vector-tileserver.git --context-dir=openshift --name=nginx-tilecache-${SUFFIX}"
[ "${APPLY}" ] || OC_NGINX_BUILD="${OC_NGINX_BUILD} --dry-run=true"


OC_NGINX_START_BUILD="oc -n ${PROJ_TARGET} start-build nginx-tilecache-${SUFFIX} --follow"
[ "${APPLY}" ] || OC_NGINX_START_BUILD="${OC_NGINX_START_BUILD} --dry-run=true"

# Apply template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

# Execute commands
#
eval "${OC_NGINX_BUILD}"
eval "${OC_NGINX_START_BUILD}"
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
