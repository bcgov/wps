#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#
# OpenShift Deploy Helper
#   
#   Pulls in logic for SUFFIX variable when declaring PR name
#   Intended for use with a pull request-based pipeline.
#   Suffixes incl.: pr-###.
#
# Usage:
#                         
#    [PROJ_TARGET] ${THIS_FILE} [SUFFIX] [RUN-TYPE]
#
# Examples:
#
#   Provide a PR number.
#
#   PROJ_TARGET=e1e498-prod ${THIS_FILE} pr-0 apply
#   ${THIS_FILE} pr-0 dry-run
#
RUN_TYPE=$2
# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

set -ex
echo Configure
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_nats_server_config.sh prod ${RUN_TYPE}
echo Promote
MODULE_NAME=api bash $(dirname ${0})/oc_promote.sh ${SUFFIX} ${RUN_TYPE}
MODULE_NAME=web bash $(dirname ${0})/oc_promote.sh ${SUFFIX} ${RUN_TYPE}
MODULE_NAME=jobs bash $(dirname ${0})/oc_promote.sh ${SUFFIX} ${RUN_TYPE}

# wps-weather lives on GHCR now, promoted via a registry-side copy rather than `oc tag`.
# wps-weather isn't always rebuilt if nothing in it changed, in which case there's no PR
# image to promote and oc_promote_gh.sh exits 0, leaving "prod" pointing at whatever it
# already was. An actual promotion failure (registry/auth/network error) exits non-zero 
#and fails this deploy like everything else here. The resulting path is always
# ghcr.io/bcgov/wps/wps-weather:prod, which the provisioning scripts below
# already default WEATHER_IMAGE to (since they're called with SUFFIX=prod).
PACKAGE=wps-weather bash $(dirname ${0})/oc_promote_gh.sh ${SUFFIX} ${RUN_TYPE}

echo Provision database
PROJ_TARGET=${PROJ_TARGET} BUCKET=lwzrin CPU_REQUEST=2 MEMORY_REQUEST=2Gi MEMORY_LIMIT=16Gi DATA_SIZE=65Gi WAL_SIZE=15Gi REPLICAS=3 bash $(dirname ${0})/oc_provision_crunchy.sh prod ${RUN_TYPE}

echo Provision NATS
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_nats.sh prod ${RUN_TYPE}

# DEPLOY_VERSION changes once per deploy so the API/ASA Go/SFMS FWI pod templates each roll
# exactly once, same convention as every individual oc_deploy*.sh script used (now folded
# into the Kustomize batch below instead of three separate oc process | oc apply calls).
DEPLOY_VERSION="${DEPLOY_VERSION:-$(date +%s)}"

echo ECCC Consumer
PROJ_TARGET=${PROJ_TARGET} bash $(dirname ${0})/oc_provision_eccc_grib_consumer.sh prod ${RUN_TYPE}

# 20 independent CronJobs + the two APS gateway NetworkPolicies + the fuel-grid-install Job
# + the API/ASA Go/SFMS FWI Deployments, migrated to Kustomize (openshift/kustomize/ -- see
# its README) -- this replaces the hand-rolled batch-file mechanism entirely, and the
# separate script calls that used to run here (oc_provision_asa_go_gateway_networkpolicy.sh,
# oc_provision_sfms_fwi_gateway_networkpolicy.sh, oc_provision_fuel_grid_install_job.sh,
# oc_deploy.sh, oc_deploy_asa_go_api.sh, oc_deploy_sfms_fwi_api.sh). fuel-grid-install always
# renders with spec.suspend: true; prod was already called with FUEL_GRID_INSTALL_SUSPEND=true
# (skip the unsuspend patch), so no follow-up step is needed here to match prod's existing
# behavior -- see deployment.yml for dev, which still needs one.
# `oc kustomize` is a fully local render (unlike `oc process`, confirmed this week to hit the
# API server by default). __SUFFIX__ is substituted with the literal "prod" (not ${SUFFIX},
# which here is the source PR's suffix used only for image promotion above) -- prod
# resources are always named "prod", never per-PR, same as every oc_provision_*.sh call in
# this file. Using ${SUFFIX} here previously caused duplicate/orphaned per-PR-tagged
# CronJobs in live prod; don't reintroduce that.
echo "Applying batched resources via Kustomize..."
if [ "${RUN_TYPE}" = "apply" ]; then
	oc kustomize $(dirname ${0})/../kustomize/overlays/prod \
		| sed "s/__SUFFIX__/prod/g; s/__NAMESPACE__/${PROJ_TARGET}/g; s/__DEPLOY_VERSION__/${DEPLOY_VERSION}/g" \
		| oc -n ${PROJ_TARGET} apply -f -
else
	oc kustomize $(dirname ${0})/../kustomize/overlays/prod \
		| sed "s/__SUFFIX__/prod/g; s/__NAMESPACE__/${PROJ_TARGET}/g; s/__DEPLOY_VERSION__/${DEPLOY_VERSION}/g" \
		| oc -n ${PROJ_TARGET} apply -f - --dry-run
fi

# Rollout wait stays external -- Kustomize only renders, applying/waiting is still the
# caller's job, same as oc_deploy.sh/oc_deploy_asa_go_api.sh/oc_deploy_sfms_fwi_api.sh always did.
oc -n ${PROJ_TARGET} rollout status deployment/wps-prod
oc -n ${PROJ_TARGET} rollout status deployment/wps-prod-asa-go
oc -n ${PROJ_TARGET} rollout status deployment/wps-prod-sfms-fwi

# Not yet migrated (see openshift/kustomize/README.md): backup_s3_postgres_cronjob's
# param wiring doesn't follow the pattern every other cronjob script does, and needs
# individual investigation before converting.
echo Configure backups
PROJ_TARGET=${PROJ_TARGET} CPU_REQUEST=1000m bash $(dirname ${0})/oc_provision_backup_s3_postgres_cronjob.sh prod | oc -n ${PROJ_TARGET} apply -f -

echo Logging alerts
cat $(dirname ${0})/../logging-alerts/nats_alerts.yaml | oc -n ${PROJ_TARGET} apply -f -
cat $(dirname ${0})/../logging-alerts/sfms_alerts.yaml | oc -n ${PROJ_TARGET} apply -f -
oc -n ${PROJ_TARGET} process -f $(dirname ${0})/../logging-alerts/oom_alerts.yaml -o yaml -p NAMESPACE=e1e498-prod -p SEVERITY=critical | oc -n ${PROJ_TARGET} apply -f -
