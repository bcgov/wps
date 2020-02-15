#!/bin/bash


# Halt on errors/unsets, change fail returns, change field separator
#
set -euo pipefail
IFS=$'\n\t'


# Parameters and defaults
#
PR_NO=${1:-}
#
NAME=${APPLICATION_NAME:-wps}
PROJ_TOOLS=${PROJ_TOOLS:-auzhsi-tools}
PROJ_DEPLOY=${PROJ_DEPLOY:-auzhsi-dev}
PATH_DC=${PATH_DC:-templates/wps.dc.yaml}
GIT_URL=${GIT_URL:-$(git remote get-url origin)}
GIT_BRANCH=${GIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}


# Show message if no params
#
if [ "${#}" -lt 1 ]
then
	echo
	echo "OC Deployer"
	echo
	echo "Provide a pull request number."
	echo " './$(basename $0) <PR_NUMBER>'"
	echo
	echo "Override variables at runtime.  E.g.:"
	echo " 'VERBOSE=true GIT_BRANCH=master ./$(basename $0) <...>'"
	echo
	exit
fi


# Function for oc command
ocProcess() {
    oc -n "${PROJ_TOOLS}" process -f $(dirname $0)/"${PATH_DC}" -p NAME="${NAME}" -p SUFFIX=pr-"${PR_NO}"
}
TEMPLATE=$(ocProcess)
echo "${TEMPLATE}" | oc -n "${PROJ_DEPLOY}" apply -f - --dry-run
set -x
echo "${TEMPLATE}" | oc -n "${PROJ_DEPLOY}" apply -f -
