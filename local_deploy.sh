#!/bin/bash
 
# Usually "pr-<PR number>" - e.g., "pr-1600" 
SUFFIX="pr-1666"
 
echo Promote
bash openshift/scripts/oc_promote.sh ${SUFFIX} apply
bash openshift/scripts/oc_promote_ubuntu.sh ${SUFFIX} apply
echo Provision database
CPU_REQUEST=75m CPU_LIMIT=2000m MEMORY_REQUEST=2Gi MEMORY_LIMIT=16Gi PVC_SIZE=45Gi PROJ_TARGET=e1e498-prod bash openshift/scripts/oc_provision_db.sh prod apply
echo Deploy API
CPU_REQUEST=50m CPU_LIMIT=500m MEMORY_REQUEST=2Gi MEMORY_LIMIT=3Gi REPLICAS=3 PROJ_TARGET=e1e498-prod VANITY_DOMAIN=psu.nrs.gov.bc.ca SECOND_LEVEL_DOMAIN=apps.silver.devops.gov.bc.ca bash ./openshift/scripts/oc_deploy.sh prod apply
echo Env Canada Subscriber
PROJ_TARGET=e1e498-prod bash openshift/scripts/oc_provision_ec_gdps_cronjob.sh prod apply
PROJ_TARGET=e1e498-prod bash openshift/scripts/oc_provision_ec_hrdps_cronjob.sh prod apply
PROJ_TARGET=e1e498-prod bash openshift/scripts/oc_provision_ec_rdps_cronjob.sh prod apply
echo C-Haines
PROJ_TARGET=e1e498-prod bash openshift/scripts/oc_provision_c_haines_cronjob.sh prod apply
echo BC FireWeather cronjobs
echo "Run forecast at 8h30 PDT and 16h30 PDT (so before and after noon)"
PROJ_TARGET=e1e498-prod SCHEDULE="30 * * * *" bash openshift/scripts/oc_provision_wfwx_noon_forecasts_cronjob.sh prod apply
PROJ_TARGET=e1e498-prod SCHEDULE="15 * * * *" bash openshift/scripts/oc_provision_wfwx_hourly_actuals_cronjob.sh prod apply
echo Configure backups
PROJ_TARGET=e1e498-prod CPU_REQUEST=1000m CPU_LIMIT=2000m bash openshift/scripts/oc_provision_backup_s3_postgres_cronjob.sh prod apply
PROJ_TARGET=e1e498-prod CPU_REQUEST=50m CPU_LIMIT=500m BACKUP_VOLUME_SIZE=3Gi bash openshift/scripts/oc_provision_backup_mariadb.sh prod apply
PROJ_TARGET=e1e498-prod CPU_REQUEST=50m CPU_LIMIT=500m bash openshift/scripts/oc_provision_backup_mariadb_cronjob.sh prod apply
echo Configure
PROJ_TARGET=e1e498-prod CERTBOT_STAGING=false DRYRUN=false bash openshift/scripts/oc_provision_certbot_cronjob.sh prod apply