# How to reprocess historical data

## Reprocessing snow data
- Reprocessing of snow data for specific dates can be done by manually deploying an OpenShift job using a provisioning script.
- OpenShift template: /openshift/templates/historic-snow-job.yaml
- Provisioning script: /openshift/scripts/oc_provision_historic_snow_job.sh

Example usage:
`PROJ_DEV="e1e498-dev" START_DATETIME="2024-06-28T12:00:00" END_DATETIME="2024-06-29T12:00:00" bash openshift/scripts/oc_provision_historic_snow_job.sh {SUFFIX} apply -f - `
