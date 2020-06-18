# Source & Credit
Contributed to and copied from https://github.com/zalando/patroni

# Additional Information
This documentation contains primarily examples on how to get patroni running on our Openshift cluster. For full documentation on Patroni, please see https://patroni.readthedocs.io/en/latest/

# Patroni OpenShift Configuration
Patroni can be run in OpenShift. Based on the kubernetes configuration, the Dockerfile and Entrypoint has been modified to support the dynamic UID/GID configuration that is applied in OpenShift. This can be run under the standard `restricted` SCC. 

# Examples

## Create test project

```
oc new-project patroni-test
```

## Build the image

Note: Update the references when merged upstream. 
Note: If deploying as a template for multiple users, the following commands should be performed in a shared namespace like `openshift`. 

```
oc process -f openshift/build.yaml -p "GIT_URI=$(git config --get remote.origin.url)" -p "GIT_REF=$(git rev-parse --abbrev-ref HEAD)" -p SUFFIX=-001 -p VERSION=v10-latest | oc apply -f -

# Trigger a build
oc start-build patroni-001

#HINT: avoid unecessary commits and build from current git clone/checkout directory.
#oc start-build patroni-001 "--from-dir=$(git rev-parse --show-toplevel)" --wait

#oc tag patroni-001:v10-latest patroni-001:v10-stable

oc process -f openshift/deployment-prereq.yaml -p SUFFIX=-001 -p NAME=patroni | oc apply -f -

oc process -f openshift/deployment.yaml -p "IMAGE_STREAM_NAMESPACE=$(oc project -q)" -p "IMAGE_STREAM_TAG=patroni:v10-latest" -p SUFFIX=-001  -p NAME=patroni | oc apply -f -

oc delete configmap,statefulset,service,endpoints -l cluster-name=patroni-001

oc scale StatefulSet/patroni-001 --replicas=1 --timeout=1m
oc scale StatefulSet/patroni-001 --replicas=0 --timeout=1m && oc delete configmap/patroni-001-config

# Clean everthing
oc delete all -l cluster-name=patroni-001
oc delete pvc,secret,configmap,rolebinding,role -l cluster-name=patroni-001

```

## Deploy the Image 
Two configuration templates exist in [templates](templates) directory: 
- Patroni Ephemeral
- Patroni Persistent

The only difference is whether or not the statefulset requests persistent storage. 

## Create the Template
Install the template into the `openshift` namespace if this should be shared across projects: 

```
oc create -f templates/template_patroni_ephemeral.yml -n openshift
oc create -f templates/template_patroni_persistent.yml -n openshift

```

Then, from your own project: 

```
oc new-app patroni-pgsql-ephemeral
```

Once the pods are running, two configmaps should be available: 

```
$ oc get configmap
NAME                DATA      AGE
patroniocp-config   0         1m
patroniocp-leader   0         1m
```

## Development
Install minishift and use the scripts in `test/*` to build/deploy/test

- `test/e2e.sh`: runs all tests
- `test/build.sh`: Test Build
- `test/deploy.sh`: Test Deployment
   - `test/patroni.sh`: Test Patroni
   - `test/psql.sh`: Test PostgreSQL
## TODO
- Need to add anti-affinity rules
- Investigate using redhat postgres image as base image

## References
- https://github.com/sclorg/postgresql-container/blob/generated/10/root/usr/bin/run-postgresql
- https://github.com/sclorg/postgresql-container/blob/generated/10/root/usr/share/container-scripts/postgresql/common.sh
