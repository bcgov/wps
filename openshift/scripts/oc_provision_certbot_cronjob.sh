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
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"
# Default to staging
CERTBOT_STAGING="${CERTBOT_STAGING:-true}"
# Default to dry run
DRYRUN="${DRYRUN:-true}"


OC_PROCESS="oc process -n ${PROJ_TARGET} -f ${TEMPLATE_PATH}/../certbot/openshift/certbot.dc.yaml \
    -p EMAIL=${EMAIL:-BCWS.PredictiveServices@gov.bc.ca} \
    -p NAMESPACE=${PROJ_TOOLS} \
    -p CERTBOT_STAGING=${CERTBOT_STAGING} \
    -p DRYRUN=${DRYRUN} \
    ${DEBUG:+ " -p DEBUG=${DEBUG}"}"

# Apply template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
