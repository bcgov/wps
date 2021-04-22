#!/usr/bin/env bash

#   Commands including these common checks expect the following variables, and oc installed:

#   PROJECT=OPENSHIFT_PROJECT_NAME POD=OPENSHIFT_POD DATABASE=POSTGRESQL_DATABASE
#
#   e.g. PROJECT=e1e498-prod POD=patroni-wps-prod-2 DATABASE=wps


RSH="oc -n ${PROJECT} rsh ${POD}"

if [ -z ${PROJECT+0} ]
then
    echo "---------------------"
    echo "PROJECT not specified"
    printf "\nSpecify a project:\n\n"
    RSH="oc get projects"
    eval "${RSH}"
    exit 1
fi

if [ -z ${POD+0} ]
then
    echo "-----------------"
    echo "POD not specified"
    printf "\nSpecify a pod:\n\n"
    RSH="oc -n ${PROJECT} get pods"
    eval $RSH
    exit 1
fi

if [ -z ${DATABASE+0} ]
then
    echo "----------------------"
    echo "DATABASE not specified"
    echo "Specify a database:"
    echo ""
    eval "${RSH} psql -c '\l'"
    exit 1
fi

# Check that the pod specified is a replica, not a leader. We don't want to bog
# down the leader, since it's getting a lot of stuff written to it.
if eval "${RSH} patronictl list" | grep ${POD} | grep -q 'Leader'; then
    echo "-------------------------"
    echo "Please specify a Replica!"
    printf "\n\n"
    eval "${RSH} patronictl list"
    exit 1
fi
