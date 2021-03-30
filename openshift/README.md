Github actions

# Create service account in dev

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
