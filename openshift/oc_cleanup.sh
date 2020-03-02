#!/bin/bash
#%
#% OpenShift Cleanup Helper
#%
#%   Intended for use with a pull request-based pipeline.
#%
#% Usage:
#%
#%   ${THIS_FILE} [PR_NUMBER] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Default only returns object names.
#%   ${THIS_FILE} 0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} 0 apply
#%
#%   Override variables at runtime.
#%   PROJ_TOOLS=tools PROJ_DEV=dev ${THIS_FILE} 0 apply
#%

# Specify halt conditions (errors, unsets, non-zero pipes), field separator and verbosity
#
set -euo pipefail
IFS=$'\n\t'
[ ! "${VERBOSE:-}" == "true" ] || set -x

# Receive parameters and source/load environment variables from a file
#
PR_NO=${1:-}
APPLY=${2:-}
source "$(dirname ${0})/envars"

# If no parameters have been passed show the help header from this script
#
[ "${#}" -gt 0 ] || {
	THIS_FILE="$(dirname ${0})/$(basename ${0})"

	# Cat this file, grep #% lines and clean up with sed
	cat ${THIS_FILE} |
		grep "^#%" |
		sed -e "s|^#%||g" |
		sed -e "s|\${THIS_FILE}|${THIS_FILE}|g"
	exit
}

# Verify login
#
$(oc whoami &>/dev/null) || {
	echo "Please verify oc login"
	exit
}

# Set and process commands
#
APP_LABEL="${NAME}-pr-${PR_NO}"
if [ "${APPLY}" == "apply" ]; then
	OC_CLEAN_DEPLOY="oc -n ${PROJ_DEV} delete all -o name -l app=${APP_LABEL}"
	OC_CLEAN_TOOLS="oc -n ${PROJ_TOOLS} delete all -o name -l app=${APP_LABEL}"
else
	OC_CLEAN_DEPLOY="oc -n ${PROJ_DEV} get all -o name -l app=${APP_LABEL}"
	OC_CLEAN_TOOLS="oc -n ${PROJ_TOOLS} get all -o name -l app=${APP_LABEL}"
	echo -e "\n*** This only a listing.  Use 'apply' to delete. ***"
fi
echo -e "\n${PROJ_DEV}:"
eval "${OC_CLEAN_DEPLOY}"
echo -e "\n${PROJ_TOOLS}:"
eval "${OC_CLEAN_TOOLS}"

# Provide oc command instruction
#
echo -e "\n${OC_CLEAN_DEPLOY}"
echo -e "\n${OC_CLEAN_TOOLS}\n"
