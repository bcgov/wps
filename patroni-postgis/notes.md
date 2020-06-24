# Notes

Need to add roles:
Error from server (Forbidden): roles.rbac.authorization.k8s.io "patroniocp-wps-api-pr-86" is forbidden: User "system:serviceaccount:auzhsi-dev:ghactions-edit" cannot get roles.rbac.authorization.k8s.io in the namespace "auzhsi-dev": no RBAC policy matched
Error from server (Forbidden): rolebindings.rbac.authorization.k8s.io "patroniocp-wps-api-pr-86" is forbidden: User "system:serviceaccount:auzhsi-dev:ghactions-edit" cannot get rolebindings.rbac.authorization.k8s.io in the namespace "auzhsi-dev": no RBAC policy matched

## 1. build the image

What I did:

- Copied code from [BCDevOps/platform-services](https://github.com/BCDevOps/platform-services)
- Modified openshift/build.yaml to point to our repo
- Applied openshift/build.yaml

oc -n auzhsi-dev process -f openshift/build.yaml -p SUFFIX=-001
oc -n auzhsi-dev process -f openshift/build.yaml -p SUFFIX=-001 | oc -n auzhsi-dev apply -f -

tag the imagestream for use

oc -n auzhsi-dev tag patroni:v10-latest patroni:10

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

Why would I use new-app?

```bash
oc -n auzhsi-dev new-app patroni-pgsql-ephemeral -p PATRONI_CLUSTER_NAME=patroni-ephemeral-210 -p APPLICATION_NAME=wps-api-210 -p PATRONI_MASTER_SERVICE_NAME=patroni-ephemeral-master-210 -p PATRONI_REPLICA_SERVICE_NAME=patroni-ephemeral-replica-210 -p SERVICE_ACCOUNT=patroniocp-210
```

Applying the template allows me to run and re-run without issues.

```bash
oc -n auzhsi-dev process patroni-pgsql-ephemeral -p PATRONI_CLUSTER_NAME=patroni-ephemeral-dev-210 -p APPLICATION_NAME=patroni-ephemeral-dev-210 -p PATRONI_MASTER_SERVICE_NAME=patroni-ephemeral-master-dev-210 -p PATRONI_REPLICA_SERVICE_NAME=patroni-ephemeral-replica-dev-210 -p SERVICE_ACCOUNT=patroniocp-dev-210 APPLICATION_SECRET=wps-api-pr-86 NAMESPACE=auzhsi-dev | oc -n auzhsi-dev apply -f -
```

#### Clean

```bash
oc get all,cm,secret,endpoints,serviceaccounts,rolebinding.rbac.authorization.k8s.io,roles.rbac.authorization.k8s.io -o name -l application=patroni-ephemeral-dev-210
oc delete all,cm,secret,endpoints,serviceaccounts,rolebinding.rbac.authorization.k8s.io,roles.rbac.authorization.k8s.io -o name -l application=patroni-ephemeral-dev-210
```

### Validate

```bash
# Get something to connect to
oc get endpoints
oc get pods
# rsh in
oc rsh <some pod with psql>
# connect psql
psql -h patroni-ephemeral-master-dev-210 -U wps-api-pr-86 wps-api-pr-86
```

## Scratchpad

See if it builds...
docker build -f Dockerfile -t db-dev .

Connect to it:

## Estimating

Logical steps:

- Manually deploy patroni instance in openshift
- Modify to use PostGIS
- Make it automatically deploy for dev instances
- Deploy an instance in prod

## PSQL stuffs

- Create user and database

```bash
psql -h localhost -d postgres -U postgres -c "CREATE ROLE pruser WITH password 'pruser';"
psql -h localhost -d postgres -U postgres -c "CREATE DATABASE prdb OWNER pruser;"
```

- Cleanup

```bash
psql -h localhost -d postgres -U pipeline -c "DROP USER pruser; DROP DATABASE prdb;"
```

### Using oc

```bash
oc exec patroni-ephemeral-0 psql -h patroni-ephemeral-master -d postgres -U postgres -c "CREATE ROLE pruser WITH password 'pruser';"


```

```
psql -h patroni-ephemeral-master -d postgres -U postgres -c "drop ROLE pruser;"
```
