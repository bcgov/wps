#!/bin/sh -l
#

# %
# % OpenShift Build Helper
# %
# %   Intended for use with a pull request-based pipeline.
# %   Suffixes incl.: pr-###, test and prod.
# %
# % Usage:
# %
# %   ${THIS_FILE} [SUFFIX] [apply]
# %
# % Examples:
# %
# %   Provide a PR number. Defaults to a dry-run.
# %   VERSION=jan-10-2023 ${THIS_FILE}
# %
# %   Apply when satisfied.
# %   VERSION=jan-10-2023 ${THIS_FILE} apply
# %

# Process a template (mostly variable substition)
#​​
PROJ_TOOLS="e1e498-tools"

OC_PROCESS="oc -n ${PROJ_TOOLS} process -f build.yaml \
 -p VERSION=${VERSION}"

# Apply a template (apply or use --dry-run)

OC_APPLY="oc -n ${PROJ_TOOLS} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

# Cancel non complete builds and start a new build (apply or don't run)
#
OC_START_BUILD="oc -n ${PROJ_TOOLS} start-build --follow=true --wait=true"
[ "${APPLY}" ] || OC_START_BUILD=""

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"
eval "${OC_START_BUILD}"

if [ "${APPLY}" ]; then
	# Get the most recent build version
	BUILD_LAST=$(oc -n ${PROJ_TOOLS} get bc/${OBJ_NAME} -o 'jsonpath={.status.lastVersion}')
	# Command to get the build result
	BUILD_RESULT=$(oc -n ${PROJ_TOOLS} get build/${OBJ_NAME}-${BUILD_LAST} -o 'jsonpath={.status.phase}')

	# Make sure that result is a successful completion
	if [ "${BUILD_RESULT}" != "Complete" ]; then
		echo "Build result: ${BUILD_RESULT}"
		echo -e "\n*** Build not complete! ***\n"
		exit 1
	fi
fi

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}" "${OC_START_BUILD}"
