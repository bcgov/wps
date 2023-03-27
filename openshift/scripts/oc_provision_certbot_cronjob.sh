#!/bin/sh -l
#
source "$(dirname ${0})/common/common"

# Target project override for Dev or Prod deployments
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"
# Default to staging
CERTBOT_STAGING="${CERTBOT_STAGING:-true}"
# Default to dry run
DRYRUN="${DRYRUN:-true}"

export CERTBOT_EMAIL=BCWS.PredictiveServices@gov.bc.ca
export CERTBOT_SERVER=$(oc get secret wps-global -o jsonpath='{.data.certbot-server}' | base64 --decode)

oc process -n $PROJ_TARGET -f "https://raw.githubusercontent.com/BCDevOps/certbot/v1.0.2/openshift/certbot.dc.yaml" -p CERTBOT_EMAIL=$CERTBOT_EMAIL -p CERTBOT_SERVER=$CERTBOT_SERVER -p CERTBOT_SUBSET=true -p CERTBOT_DEBUG=true | oc apply -n $PROJ_TARGET -f -
