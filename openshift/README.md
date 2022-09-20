# Openshift

Infrastructure is deployed to openshift using Openshift YAML templates. Many are automatically deployed in the dev namespace when a PR is created, see: [deployment.yml](https://github.com/bcgov/wps/blob/main/.github/workflows/deployment.yml)

## NATS

https://docs.nats.io/nats-concepts/what-is-nats

We use NATS for message queueing. Below are steps you need to work with it/deploy it.

#### Get the nats-cli tool

Needed if you want to test the nats service from the cli

See: https://github.com/nats-io/natscli

#####Homebrew install:

```bash
brew tap nats-io/nats-tools
brew install nats-io/nats-tools/nats
```

#### Pushing the NATS image to `e1e498-tools` namespace

This is needed for the nats server pods to pull and run

```bash
# Grab the image
docker pull nats:2.8.4-alpine
# Tag it for upload to the registry
docker tag nats:2.8.4-alpine image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/nats:2.8.4-alpine
# Log in to openshift docker
docker login -u developer -p $(oc whoami -t) image-registry.apps.silver.devops.gov.bc.ca
# Push it to the registry
docker push image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/nats:2.8.4-alpine
```

#### Deploying NATS to the cluster

```bash
# Dry run
./oc_provision_nats.sh nats

# Wet run -- dev cluster by default
./oc_provision_nats.sh nats apply

# Specifying cluster namespace to deploy to
PROJ_TARGET=<cluster-namespace> ./oc_provision_nats.sh nats apply
```

#### Tearing down the NATS resources

```bash
oc delete all --selector app=nats
```

Then you'll need to manually delete the PVC's (`wps-nats-jetstream-nats-x1`) and ConfigMap (`nats-config`)

## Create service account in dev

## Create role binding giving service edit rights

## Create additional roles, and create a role binding for that too.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: additional_ghactions_roles
  namespace: e1e498-dev
rules:
  # for certbot to work:
  - verbs:
      - get
      - patch
    apiGroups:
      - authorization.openshift.io
    resources:
      - rolebindings
  # for patroni to work:
  - apiGroups:
      - "rbac.authorization.k8s.io"
    resources:
      - rolebindings
    verbs:
      - get
      - create
      - list
      - delete
      - patch
      - update
  - apiGroups:
      - "rbac.authorization.k8s.io"
    resources:
      - roles
    verbs:
      - get
      - create
      - list
      - delete
      - patch
```

## Used token to create appropraite token in github

- Create service account in tools

## Allow service account to pull images from tools.

```bash
oc policy add-role-to-group system:image-puller system:serviceaccounts:e1e498-dev --namespace=e1e498-tools
```

```bash
oc policy add-role-to-group system:image-puller system:serviceaccounts:e1e498-prod --namespace=e1e498-tools
```

```bash
oc policy add-role-to-group system:image-puller system:serviceaccounts:e1e498-test --namespace=e1e498-tools
```
