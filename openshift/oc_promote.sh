#!/bin/bash
#%
#% OpenShift Deployment Promotion Helper
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
#
# If no parameters, then show this help header (cat file, grep #% lines and clean up with sed)
#
[ "${#}" -gt 0 ] || {
	THIS_FILE="$(dirname ${0})/$(basename ${0})"
	cat ${THIS_FILE} |
		grep "^#%" |
		sed -e "s|^#%||g" |
		sed -e "s|\${THIS_FILE}|${THIS_FILE}|g"
	exit
}

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

# Verify login
#
$(oc whoami &>/dev/null) || {
	echo "Please verify oc login"
	exit
}

# Command to copy imagestreamtag from dev PR to prod (ENV is the after-dash portion of PROJ_PROD)
#
ENV=$(echo $PROJ_PROD | cut -d'-' -f2)
SOURCE_IMG="docker-registry.default.svc:5000/${PROJ_TOOLS}/${NAME}:pr-${PR_NO}"
OC_PROMOTE="oc -n ${PROJ_TOOLS} import-image ${NAME}:${ENV} --from=${SOURCE_IMG}"

# Command to process and apply deployment template
#
OC_PROCESS="oc -n ${PROJ_TOOLS} process -f ${PATH_DC} -p NAME=${NAME} -p SUFFIX=${ENV}"
OC_APPLY="oc -n ${PROJ_PROD} apply -f -"
OC_COMMAND="${OC_PROCESS} | ${OC_APPLY}"
#
[ "${APPLY}" == "apply" ] || {
	OC_COMMAND+=" --dry-run"
	eval "${OC_PROCESS}"
	echo -e "\n*** This is a dry run.  Use 'apply' to deploy. ***\n"
}

# Execute and output commands
#
eval "${OC_PROMOTE}"
eval "${OC_COMMAND}"
#
echo -e "\n${OC_PROMOTE}"
echo -e "\n${OC_COMMAND}\n"
