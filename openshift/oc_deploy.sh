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
#%   Provide a PR number. Defaults to a dry-run.
#%   ${THIS_FILE} 0
#%
#%   Apply when satisfied.
#%   ${THIS_FILE} 0 apply
#%
#%   Override variables at runtime.
#%   NAME=name PROJECT=project PATH_DC=./dc.yaml ${THIS_FILE} 0 apply
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

# Process commands
#
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_DC} -p NAME=${NAME} -p SUFFIX=pr-${PR_NO}"
OC_APPLY="oc -n ${PROJ_DEV} apply -f -"
OC_COMMAND="${OC_PROCESS} | ${OC_APPLY}"
#
[ "${APPLY}" == "apply" ] || {
	OC_COMMAND+=" --dry-run"
	eval "${OC_PROCESS}"
	echo -e "\n*** This is a dry run.  Use 'apply' to deploy. ***\n"
}
eval "${OC_COMMAND}"

# Provide oc command instruction
#
echo -e "\n${OC_COMMAND}\n"
