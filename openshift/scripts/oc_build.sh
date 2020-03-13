#!/bin/bash
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Build Helper
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
#%   Provide a PR number. Defaults to a dry-run.
#%   ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} pr-0 apply
#%

# Process a template (mostly variable substition)
#
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_BC} -p NAME=${NAME} -p SUFFIX=${SUFFIX} -p GIT_BRANCH=${GIT_BRANCH}"

# Apply a template (apply or use --dry-run)
#
OC_APPLY="oc -n "${PROJ_TOOLS}" apply -f -"
[ "${APPLY}" ] || OC_APPLY+=" --dry-run"

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

# Follow builds if deploying (wait condition) and ensure sure they pass successfully
#
if [ "${APPLY}" ]; then
	APP_NAME=${NAME}-${SUFFIX}
	# Identify buildconfig objects
	BUILD_PODS=$(oc get bc -n ${PROJ_TOOLS} -o name -l app=${APP_NAME})
	# Follow building of these objects (creates wait condition, lots of output!)
	for p in "${BUILD_PODS}"; do
		oc logs -n ${PROJ_TOOLS} --follow $p
	done
	# Get the most recent build version
	BUILD_LAST=$(oc -n ${PROJ_TOOLS} get bc/${APP_NAME} -o 'jsonpath={.status.lastVersion}')
	# Command to get the build result
	BUILD_RESULT=$(oc -n ${PROJ_TOOLS} get build/${APP_NAME}-${BUILD_LAST} -o 'jsonpath={.status.phase}')
	# Make sure that result is a successful completion
	if [ "${BUILD_RESULT}" != "Complete" ]; then
		echo -e "\n*** Build not complete! ***\n"
		exit 1
	fi
fi

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
