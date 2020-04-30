#!/bin/sh -l
#
# Move to repo root and pull subtree updates
#
pushd $(dirname ${0})/../..
git subtree pull --prefix openshift/scripts git@github.com:bcgov/wps.git master --squash
