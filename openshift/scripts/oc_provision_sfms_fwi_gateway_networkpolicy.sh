#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift SFMS API gateway network policy helper
#%
#%   Apply the NetworkPolicy that allows APS to reach the dedicated
#%   SFMS API pods. Required for the SFMS APS
#%   gateway route.
#%
#% Usage:
#%
#%   ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   ${THIS_FILE} pr-0
#%   ${THIS_FILE} pr-0 apply
#

PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

OC_PROCESS="oc -n ${PROJ_TARGET} process --local -f ${TEMPLATE_PATH}/allow_gateway_to_wps_sfms_fwi_api.yaml \
 -p APP_NAME=${APP_NAME} \
 -p SUFFIX=${SUFFIX}"

OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

render_and_exit_if_requested "${OC_PROCESS}"
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

display_helper "${OC_PROCESS} | ${OC_APPLY}"
