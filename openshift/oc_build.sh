#!/bin/bash


# Halt on errors, unsets and non-zeros exit (pipe fail); change field separator
#
set -euo pipefail
IFS=$'\n\t'


# Parameters and defaults
#
PR_NO=${1:-}
APPLY=${2:-"dry-run"}
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
	echo "OC Guide: Builder"
	echo
	echo "Provide a pull request number.  Default behaviour is a dry run."
	echo "> ./$(basename $0) <PR_NUMBER>"
	echo
	echo "Deploy with 'apply'."
	echo "> ./$(basename $0) <PR_NUMBER> apply"
	echo
	echo "Override variables at runtime.  E.g.:"
	echo "> GIT_BRANCH=master ./$(basename $0) ..."
	echo
	exit
fi


# Verify login
#
if !(oc whoami &>/dev/null)
then
	echo "Please verify oc login"
	exit
fi


# Commands for creating and consuming (applying) templates
#
OC_PROCESS="oc -n ${PROJECT} process -f ${PATH_BC} -p NAME=${NAME} -p SUFFIX=pr-${PR_NO} -p GIT_URL=${GIT_URL} -p GIT_REF=${GIT_BRANCH}"
OC_APPLY="oc -n "${PROJECT}" apply -f -"


# Process and either dry-run or apply
#
if [ "${APPLY}" == "apply" ]
then
	eval "${OC_PROCESS} | ${OC_APPLY}"
	echo
	echo "> ${OC_PROCESS} | ${OC_APPLY}"
else
	eval "${OC_PROCESS}"
	eval "${OC_PROCESS} | ${OC_APPLY} --dry-run"
	echo
	echo "> ${OC_PROCESS} | ${OC_APPLY} --dry-run"
	echo
	echo "* This is a dry run.  Use 'apply' to deploy."
fi