#!/bin/bash
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Build Helper
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
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_BC} -p NAME=${NAME} -p SUFFIX=pr-${PR_NO} -p GIT_BRANCH=${GIT_BRANCH}"
# Apply a template (can use --dry-run)
OC_APPLY="oc -n "${PROJ_TOOLS}" apply -f -"
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

# Follow builds if deploying (wait condition)
#
if [ "${APPLY}" ]; then
	# Identify buildconfig objects
	BUILD_PODS=$(oc get bc -n ${PROJ_TOOLS} -o name -l app=${NAME}-pr-${PR_NO})
	# Follow building of these objects (creates wait condition, lots of output!)
	for p in "${BUILD_PODS}"; do
		oc logs -n ${PROJ_TOOLS} --follow $p
	done
fi

# Provide oc command instruction
#
display_helper "${OC_COMMAND}"
