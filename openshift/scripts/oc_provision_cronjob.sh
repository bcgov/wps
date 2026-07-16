#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

#%
#% OpenShift Deploy Helper
#%
#%   Generic cronjob provisioner, used by every weather model job. Set CRONJOB_SOURCE to
#%   either a plain template YAML file, or a kustomize overlay directory (detected by the
#%   presence of a kustomization.yaml) - the latter is built with `oc kustomize` first and
#%   piped into `oc process`. Set JOB_PREFIX to the job name prefix, and DEFAULT_SCHEDULE
#%   to the cron schedule used unless SCHEDULE is already set.
#%
#%   Intended for use with a pull request-based pipeline.
#%   Suffixes incl.: pr-###.
#%
#% Usage:
#%
#%    CRONJOB_SOURCE=[source] JOB_PREFIX=[prefix] DEFAULT_SCHEDULE=[cron] ${THIS_FILE} [SUFFIX] [apply]
#%
#% Examples:
#%
#%   Provide a PR number. Defaults to a dry-run.
#%   CRONJOB_SOURCE=openshift/kustomize/weather-model-jobs/overlays/env-canada-rdps \
#%     JOB_PREFIX=env-canada-rdps DEFAULT_SCHEDULE="24 */2 * * *" ${THIS_FILE} pr-0
#%
#%   Apply when satisfied.
#%   CRONJOB_SOURCE=openshift/templates/ecmwf.cronjob.yaml \
#%     JOB_PREFIX=ecmwf DEFAULT_SCHEDULE="13 * * * *" ${THIS_FILE} pr-0 apply
#%

# Target project override for Dev or Prod deployments
#
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"

# Use the caller-provided default unless SCHEDULE is already set.
SCHEDULE="${SCHEDULE:-${DEFAULT_SCHEDULE}}"

# A kustomize overlay directory is built with `oc kustomize` first; a plain template file
# is read as-is. Either way, `oc process` reads the result from stdin.
if [ -f "${CRONJOB_SOURCE}/kustomization.yaml" ]; then
	RENDER="oc kustomize ${CRONJOB_SOURCE}"
else
	RENDER="cat ${CRONJOB_SOURCE}"
fi

# Process template
OC_PROCESS="${RENDER} | oc -n ${PROJ_TARGET} process -f - \
-p JOB_NAME=${JOB_PREFIX}-${APP_NAME}-${SUFFIX} \
-p APP_LABEL=${APP_NAME}-${SUFFIX} \
-p NAME=${APP_NAME} \
-p SUFFIX=${SUFFIX} \
-p SCHEDULE=\"${SCHEDULE}\" \
-p POSTGRES_DATABASE=${POSTGRES_DATABASE:-${APP_NAME}} \
-p CRUNCHYDB_USER=${CRUNCHY_NAME}-${SUFFIX}-pguser-${CRUNCHY_NAME}-${SUFFIX} \
${PROJ_TOOLS:+ "-p PROJ_TOOLS=${PROJ_TOOLS}"} \
${IMAGE_REGISTRY:+ "-p IMAGE_REGISTRY=${IMAGE_REGISTRY}"} \
-p PROJECT_NAMESPACE=${PROJ_TARGET}"

# Apply template (apply or use --dry-run)
#
OC_APPLY="oc -n ${PROJ_TARGET} apply -f -"
[ "${APPLY}" ] || OC_APPLY="${OC_APPLY} --dry-run"

# Execute commands
#
eval "${OC_PROCESS}"
eval "${OC_PROCESS} | ${OC_APPLY}"

# Provide oc command instruction
#
display_helper "${OC_PROCESS} | ${OC_APPLY}"
