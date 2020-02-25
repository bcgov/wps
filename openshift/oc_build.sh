#!/bin/bash
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
#%   Provide a PR number. Defaults to is a dry-run.
#%   ${THIS_FILE} 0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} 0 apply
#%
#%   Override variables at runtime.
#%   GIT_BRANCH=branch PROJ_TOOLS=project PATH_BC=./bc.yaml ${THIS_FILE} 0 apply
#%

# Halt conditions (errors, unsets, non-zero pipes), field separator and verbosity
#
set -euo pipefail
IFS=$'\n\t'
[ ! "${VERBOSE:-}" == "true" ] || set -x

# Parameters and environment vars
#
PR_NO=${1:-}
APPLY=${2:-}
source "$(dirname ${0})/envars"

# Show help if no params
#
[ "${#}" -gt 0 ] || {
	THIS_FILE="$(dirname ${0})/$(basename ${0})"
	cat ${THIS_FILE} | grep "^#%" | sed -e "s|^#%||g" -e "s|\${THIS_FILE}|${THIS_FILE}|g"
	exit
}

# Verify login
#
$(oc whoami &>/dev/null) || {
	echo "Please verify oc login"
	exit
}

# Process commands
#
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_BC} -p NAME=${NAME} -p SUFFIX=pr-${PR_NO} -p GIT_URL=${GIT_URL} -p GIT_BRANCH=${GIT_BRANCH}"
OC_APPLY="oc -n "${PROJ_TOOLS}" apply -f -"
OC_COMMAND="${OC_PROCESS} | ${OC_APPLY}"
#
[ "${APPLY}" == "apply" ] || {
	OC_COMMAND+=" --dry-run"
	eval "${OC_PROCESS}"
	echo -e "\n*** This is a dry run.  Use 'apply' to deploy. ***\n"
}
eval "${OC_COMMAND}"

# Follow source to image build (build source, provide artifact to docker)
#
[ "${APPLY}" != "apply" ] || {
	POD_SOURCE=$(oc get bc -n ${PROJ_TOOLS} -o name -l app=${NAME}-pr-${PR_NO} | grep "source")
	POD_DOCKER=$(oc get bc -n ${PROJ_TOOLS} -o name -l app=${NAME}-pr-${PR_NO} | grep "docker")
	oc logs -n ${PROJ_TOOLS} --follow ${POD_SOURCE}
	oc logs -n ${PROJ_TOOLS} --follow ${POD_DOCKER}
}

# Echo command
#
echo -e "\n${OC_COMMAND}\n"
