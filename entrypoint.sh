#!/bin/sh -l

# Login to cluster
oc login https://console.pathfinder.gov.bc.ca:8443 --token="$INPUT_AUTH_TOKEN"

# Run whatever commands were passed in
exec "${@}"