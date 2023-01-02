# Sysdig

Metrics and dashboard configuration for WPS

## Assumptions

- Templates are applied manually to cluster, it should be a one-time setup, no need to automate
- Template must be applied to `tools` namespace
- Further instructions here: https://beta-docs.developer.gov.bc.ca/sysdig-monitor-setup-team/#create-sysdig-team-access

## Applying template to cluster

```
# switch to the tools namespace
oc project e1e498-tools
# edit the sample sysdig-team resource and apply the manifest
oc apply -f sysdig.yaml
```
