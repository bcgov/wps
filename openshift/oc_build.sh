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
PROJECT=${PROJECT:-auzhsi-tools}
PATH_BC=${PATH_BC:-$(dirname $0)/templates/wps.bc.yaml}
GIT_URL=${GIT_URL:-$(git remote get-url origin)}
GIT_BRANCH=${GIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}


# Show message if no params
#
if [ "${#}" -lt 1 ]
then
	echo
	echo "OC Builder"
	echo
	echo "Provide a pull request number."
	echo " './$(basename $0) <PR_NUMBER>'"
	echo
	echo "Override variables at runtime.  E.g.:"
	echo " 'VERBOSE=true GIT_BRANCH=master ./$(basename $0) <...>'"
	echo
	exit
fi


# Function for processing the template
#
ocProcess() {
    oc -n "${PROJECT}" process -f "${PATH_BC}" -p NAME="${NAME}" -p SUFFIX=pr-"${PR_NO}" \
        -p GIT_URL="${GIT_URL}" -p GIT_REF="${GIT_BRANCH}"
}


# Echo and apply the template
#
ocProcess
set -x 
ocProcess | oc -n "${PROJECT}" apply -f -