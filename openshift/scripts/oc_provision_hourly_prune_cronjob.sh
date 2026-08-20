#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Render Helper
#%
#%   Renders this resource's manifest to stdout -- does not apply it. Intended for
#%   use with a pull request-based pipeline. Suffixes incl.: pr-###.
#%
#%   Applying is the caller's job: pipe into `oc apply -f -` yourself, or see
#%   oc_deploy_to_production.sh / deployment.yml for how this is combined with
#%   other resources and applied together in one call.
#%
#% Usage:
#%
#%    ${THIS_FILE} [SUFFIX]
#%
#% Examples:
#%
#%   Just render it:
#%   ${THIS_FILE} pr-0
#%
#%   Render and apply this one resource on its own:
#%   ${THIS_FILE} pr-0 | oc apply -f -
#%

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Use a random time if schedule not specified.
SCHEDULE="${SCHEDULE:-0 2 * * *}"

# Process template
OC_PROCESS="oc -n ${PROJ_TARGET} process -f ${TEMPLATE_PATH}/prune_hourlies_cronjob.yaml \
-p SUFFIX=${SUFFIX} \
-p APP_LABEL=${APP_NAME}-${SUFFIX} \
-p SCHEDULE=\"${SCHEDULE}\" \
${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"}"

# Render the manifest to stdout.
#
eval "${OC_PROCESS}"
