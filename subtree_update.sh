#!/bin/bash
#
# Move to repo root and pull subtree updates
#
set -x
pushd $(dirname ${0})/../..
pwd
git subtree pull --prefix openshift/scripts git@github.com:bcgov/wps.git master --squash
