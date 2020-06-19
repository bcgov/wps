# Notes

## 1. build the image

What I did:

- Copied code from https://github.com/BCDevOps/platform-services
- Modified openshift/build.yaml to point to our repo
- Applied openshift/build.yaml

oc -n auzhsi-dev process -f openshift/build.yaml -p SUFFIX=-001
oc -n auzhsi-dev process -f openshift/build.yaml -p SUFFIX=-001 | oc -n auzhsi-dev apply -f -

## 2. deploy the image

### Upload the template

```bash
# how does one update?
oc delete template/patroni-pgsql-ephemeral -n auzhsi-dev
# create:
oc create -f openshift-example/templates/template_patroni_ephemeral.yml -n auzhsi-dev
```

### Deploy

oc -n auzhsi-dev new-app patroni-pgsql-ephemeral

### Use the template for each PR

oc -n auzhsi-dev new-app patroni-pgsql-ephemeral -p PATRONI_CLUSTER_NAME=patroni-ephemeral-210 -p APPLICATION_NAME=wps-api-210 -p PATRONI_MASTER_SERVICE_NAME=patroni-ephemeral-master-210 -p PATRONI_REPLICA_SERVICE_NAME=patroni-ephemeral-replica-210 -p SERVICE_ACCOUNT=patroniocp-210

#### Clean

```bash
oc get all,cm,secret,endpoints,serviceaccounts,rolebinding.rbac.authorization.k8s.io,roles.rbac.authorization.k8s.io -o name -l application=wps-api-210
oc delete all,cm,secret,endpoints,serviceaccounts,rolebinding.rbac.authorization.k8s.io,roles.rbac.authorization.k8s.io -o name -l application=wps-api-210
```

## Scratchpad

See if it builds...
docker build -f Dockerfile -t db-dev .

## Estimating

Logical steps:

- Manually deploy patroni instance in openshift
- Modify to use PostGIS
- Make it automatically deploy for dev instances
- Deploy an instance in prod
