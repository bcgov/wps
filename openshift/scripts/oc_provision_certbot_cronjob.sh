#!/bin/sh -l

## Run as PROJ_TARGET=target CERTBOT_STAGING=[true|false] DRYRUN=[true|false\ ./oc_provision_certbot_cronjob.sh

# Target project override for Dev or Prod deployments
PROJ_TARGET="${PROJ_TARGET:-${PROJ_DEV}}"
# Default to staging
CERTBOT_STAGING="${CERTBOT_STAGING:-true}"
# Default to dry run
DRYRUN="${DRYRUN:-true}"

export CERTBOT_EMAIL=BCWS.PredictiveServices@gov.bc.ca
export CERTBOT_SERVER=$(oc -n $PROJ_TARGET get secret wps-global -o jsonpath='{.data.certbot-server}' | base64 --decode)

oc process -n $PROJ_TARGET -f "https://raw.githubusercontent.com/BCDevOps/certbot/v1.0.2/openshift/certbot.dc.yaml" -p CRON_SCHEDULE="0 */12 * * *" -p CERTBOT_EMAIL=$CERTBOT_EMAIL -p CERTBOT_SERVER=$CERTBOT_SERVER -p CERTBOT_SUBSET=true -p CERTBOT_DEBUG=true | oc apply -n $PROJ_TARGET -f -
