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
OC_APPLY="oc -n ${PROJ_TOOLS} apply -f -"
[ "${APPLY}" ] || OC_APPLY+=" --dry-run"

# Force to start a new build each time (apply or don't run)
#
OC_START_BUILD="oc -n ${PROJ_TOOLS} start-build ${NAME}-${SUFFIX} --follow=true"
[ "${APPLY}" ] || OC_START_BUILD=""

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"
eval "${OC_START_BUILD}"

# Follow builds if deploying and ensure they pass successfully
APP_NAME="${NAME}-${SUFFIX}"
# Get the most recent build version
BUILD_LAST=$(oc -n ${PROJ_TOOLS} get bc/${APP_NAME} -o 'jsonpath={.status.lastVersion}')
# Command to get the build result
BUILD_RESULT=$(oc -n ${PROJ_TOOLS} get build/${APP_NAME}-${BUILD_LAST} -o 'jsonpath={.status.phase}')

# Make sure that result is a successful completion
if [ "${BUILD_RESULT}" != "Complete" ]; then
	echo "Build result: ${BUILD_RESULT}"
	echo -e "\n*** Build not complete! ***\n"
	exit 1
fi

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
display_helper "${OC_START_BUILD}"