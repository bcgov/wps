#!/bin/bash
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Deploy Helper
#%
#%   Intended for use with a pull request-based pipeline.
#%
#% Usage:
#%
#%   ${THIS_FILE} [PR_NUMBER] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Defaults to a dry-run.
#%   ${THIS_FILE} 0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} 0 apply
#%

# Create OpenShift commands to consume
#
# Process a template (mostly variable substition)
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_DC} -p NAME=${NAME} -p SUFFIX=pr-${PR_NO}"
# Apply a template (can use --dry-run)
OC_APPLY="oc -n ${PROJ_DEV} apply -f -"
# Pipe the first command into the second
OC_COMMAND="${OC_PROCESS} | ${OC_APPLY}"
#
# If not using apply, then use a dry run
if [ ! "${APPLY}" ]; then
	OC_COMMAND+=" --dry-run"
fi
# Execute commands
eval "${OC_PROCESS}"
eval "${OC_COMMAND}"

# Provide oc command instruction
#
display_helper "${OC_COMMAND}"
