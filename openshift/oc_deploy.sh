#!/bin/bash
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
#%   Provide a PR number. Defaults to is a dry-run.
#%   ${THIS_FILE} 0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} 0 apply
#%
#%   Override variables at runtime.
#%   NAME=name PROJECT=project PATH_DC=./dc.yaml ${THIS_FILE} 0 apply
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
PROJ_TOOLS=${PROJ_TOOLS:-auzhsi-tools}
PROJ_DEPLOY=${PROJ_DEPLOY:-auzhsi-dev}
PATH_DC=${PATH_DC:-$(dirname $0)/templates/deploy.dc.yaml}

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
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_DC} -p NAME=${NAME} -p SUFFIX=pr-${PR_NO}"
OC_APPLY="oc -n ${PROJ_DEPLOY} apply -f -"
OC_COMMAND="${OC_PROCESS} | ${OC_APPLY}"
#
[ "${APPLY}" == "apply" ] || {
	OC_COMMAND+=" --dry-run"
	eval "${OC_PROCESS}"
	echo -e "\n*** This is a dry run.  Use 'apply' to deploy. ***\n"
}
eval "${OC_COMMAND}"
echo -e "\n${OC_COMMAND}\n"
