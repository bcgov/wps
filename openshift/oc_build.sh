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
#%   GIT_BRANCH=branch PROJECT=project PATH_BC=./bc.yaml ${THIS_FILE} 0 apply
#%

# Halt on errors, unsets and non-zeros exit (pipe fail); change field separator
#
set -euo pipefail
IFS=$'\n\t'

# Parameters and defaults
#
THIS_FILE="./$(basename ${0})"
PR_NO=${1:-}
APPLY=${2:-}
#
NAME=${APPLICATION_NAME:-wps}
PROJECT=${PROJECT:-auzhsi-tools}
PATH_BC=${PATH_BC:-$(dirname $0)/templates/build.bc.yaml}
GIT_URL=${GIT_URL:-$(git remote get-url origin)}
GIT_BRANCH=${GIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}

# Show help if no params
#
[ "${#}" -gt 0 ] || {
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
OC_PROCESS="oc -n ${PROJECT} process -f ${PATH_BC} -p NAME=${NAME} -p SUFFIX=pr-${PR_NO} -p GIT_URL=${GIT_URL} -p GIT_REF=${GIT_BRANCH}"
OC_APPLY="oc -n "${PROJECT}" apply -f -"
OC_COMMAND="${OC_PROCESS} | ${OC_APPLY}"
#
[ "${APPLY}" == "apply" ] || {
	OC_COMMAND+=" --dry-run"
	eval "${OC_PROCESS}"
	echo -e "\n*** This is a dry run.  Use 'apply' to deploy. ***\n"
}
eval "${OC_COMMAND}"
echo -e "\n${OC_COMMAND}\n"
