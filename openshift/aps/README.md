# ASA Go APS Gateway Config

This directory contains the APS gateway config for the split ASA Go service.

## How it works

- The public host is the APS gateway route host.
- The upstream is the internal OpenShift service `wps-asa-go-api-<suffix>.<project-namespace>.svc`.
- `strip_path: false` keeps `/api/asa-go/...` intact when Kong proxies to the upstream.
- The template uses raw Kong `services:` format, so it must be published with `gwa publish-gateway`.
- Do not use `gwa apply` with this template.

## Important inputs

- `APS_NAMESPACE`
  This is the APS gateway id.
- `PROJECT_NAMESPACE`
  The OpenShift namespace that contains the upstream ASA Go service.
- `ASA_GO_HOST`
  The public hostname consumers call through APS.
- `SUFFIX`
  The config scope. Uses `prod` for production and `pr-<number>` for pull requests.

## Qualifiers

Use the same qualifier as the suffix when publishing:

- PR example: `pr-5296`
- prod example: `prod`

Qualifiers let one gateway hold multiple independent config sets without one publish pruning the others.

This template tags objects like:

- `ns.<gateway-id>.<suffix>`

Example:

- `ns.gw-abcxyz.pr-5296`
- `ns.gw-abcxyz.prod`

## Manually render a production config locally

From the repo root:

```bash

APS_NAMESPACE="gw-313f6" \
PROJECT_NAMESPACE="e1e498-prod" \
ASA_GO_HOST="psu.api.gov.bc.ca" \
openshift/scripts/render_asa_go_gateway_config.sh \
  prod \
  ./asa-go-gw-config-prod.yaml
```

## Publish the production config with gwa

If you have not already configured the gateway and logged in:

```bash
gwa login
gwa config set --gateway gw-313f6
gwa publish-gateway ./asa-go-gw-config-prod.yaml --qualifier prod
```

## Cleanup

To remove one qualifier-scoped config set, publish the empty config with the same qualifier:

```bash
gwa publish-gateway openshift/aps/empty-gw-config.yaml --qualifier pr-5296
```

That prunes only the services/routes/plugins in that qualifier scope.
