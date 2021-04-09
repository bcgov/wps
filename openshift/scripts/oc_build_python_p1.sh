#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

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
# %   ${THIS_FILE} pr-0
# %
# %   Apply when satisfied.
# %   ${THIS_FILE} pr-0 apply
# %


## Step 1:
# Check if phase 1 build with matching hash exists.
PHASE_ONE_HASH=$(sha1sum api/poetry.lock | awk '{print $1}')
CHECK_COMMAND="oc -n ${PROJ_TOOLS} get is -l hash=${NAME_APP}-${SUFFIX}-phase-1-${PHASE_ONE_HASH} --ignore-not-found=true"
CHECK_RESULT=$(eval "${CHECK_COMMAND}")

## Step 2:
# If the phase 1 build doesn't exist - then build it!
if ! [ "${CHECK_RESULT}" ]; then
	display_helper "did not find phase 1 build"

	# Process a template (mostly variable substition)
	#​​
	OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_BC} \
	-p NAME=${NAME_APP} \
	-p SUFFIX=${SUFFIX} \
	-p GIT_BRANCH=${GIT_BRANCH} \
	-p PHASE_ONE_HASH=${PHASE_ONE_HASH} \
	${DOCKER_IMAGE:+ "-p DOCKER_IMAGE=${DOCKER_IMAGE}"} \
	${DOCKER_FILE:+ "-p DOCKER_FILE=${DOCKER_FILE}"}"

	# Apply a template (apply or use --dry-run)

	OC_APPLY="oc -n ${PROJ_TOOLS} apply -f -"
	[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run=client"

	# Cancel non complete builds and start a new build (apply or don't run)
	#
	OC_CANCEL_BUILD="oc -n ${PROJ_TOOLS} cancel-build bc/${NAME_OBJ}"
	[ "${APPLY}" ] || OC_CANCEL_BUILD=""
	OC_START_BUILD="oc -n ${PROJ_TOOLS} start-build ${NAME_OBJ} --follow=true"
	[ "${APPLY}" ] || OC_START_BUILD=""

	# Execute commands
	#
	eval "${OC_PROCESS}"
	eval "${OC_PROCESS} | ${OC_APPLY}"
	eval "${OC_CANCEL_BUILD}"
	eval "${OC_START_BUILD}"

	if [ "${APPLY}" ]; then
		# Get the most recent build version
		BUILD_LAST=$(oc -n ${PROJ_TOOLS} get bc/${NAME_OBJ} -o 'jsonpath={.status.lastVersion}')
		# Command to get the build result
		BUILD_RESULT=$(oc -n ${PROJ_TOOLS} get build/${NAME_OBJ}-${BUILD_LAST} -o 'jsonpath={.status.phase}')

		# Make sure that result is a successful completion
		if [ "${BUILD_RESULT}" != "Complete" ]; then
			echo "Build result: ${BUILD_RESULT}"
			echo -e "\n*** Build not complete! ***\n"
			exit 1
		fi
	fi
fi

# Provide oc command instruction
#
display_helper "${CHECK_COMMAND}" "${OC_PROCESS} | ${OC_APPLY}" "${OC_CANCEL_BUILD}" "${OC_START_BUILD}"
