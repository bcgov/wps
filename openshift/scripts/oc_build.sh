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

PHASE_ONE_HASH=$(sha1sum api/poetry.lock | awk '{print $1}')
PHASE_ONE_NODE_HASH=$(sha1sum web/yarn.lock | awk '{print $1}')
DOCKER_IMAGE_TAG="${DOCKER_IMAGE_TAG:-${SUFFIX}-${PHASE_ONE_HASH}}"
NODE_DOCKER_IMAGE="image-registry.openshift-image-registry.svc:5000/e1e498-tools/wps-pr-${SUFFIX}-node-phase-1"
NODE_DOCKER_IMAGE_TAG="${SUFFIX}-${PHASE_ONE_NODE_HASH}"

# Process a template (mostly variable substition)
#​​
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_BC} \
 -p NAME=${NAME_APP} \
 -p SUFFIX=${SUFFIX} \
 -p GIT_BRANCH=${GIT_BRANCH} \
 -p DOCKER_IMAGE_TAG=${DOCKER_IMAGE_TAG} \
 ${NODE_DOCKER_IMAGE:+ "-p NODE_DOCKER_IMAGE=${NODE_DOCKER_IMAGE}"} \
 ${NODE_DOCKER_IMAGE_TAG:+ "-p NODE_DOCKER_IMAGE_TAG=${NODE_DOCKER_IMAGE_TAG}"} \
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

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}" "${OC_CANCEL_BUILD}" "${OC_START_BUILD}"
