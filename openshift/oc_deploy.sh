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
PATH_DC=${PATH_DC:-$(dirname $0)/templates/wps.dc.yaml}


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
	echo " 'VERBOSE=true NAME=wps ./$(basename $0) <...>'"
	echo
	exit
fi


# Function for processing the template
#
ocProcess() {
    oc -n "${PROJ_TOOLS}" process -f "${PATH_DC}" -p NAME="${NAME}" -p SUFFIX=pr-"${PR_NO}"
}


# Echo and apply the template
#
ocProcess
set -x
ocProcess | oc -n "${PROJ_DEPLOY}" apply -f -
