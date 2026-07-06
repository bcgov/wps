# APS Gateway Configuration

This directory contains APS gateway configuration for services exposed through the BC Government API Services Portal.

## Services

| Service | Gateway config | Dataset / Product |
|---|---|---|
| ASA Go API | `asa-go-gw-config.yaml` | — |
| SFMS Daily FWI | `sfms-fwi-gw-config.yaml` | `sfms-fwi-dataset.yaml`, `sfms-fwi-product.yaml` |

---

## ASA Go API

Exposes the ASA Go API at `<public-host>/api/asa-go` via rate-limiting (no key-auth).

### Publishing

Uses `gwa publish-gateway` (raw Kong format) with a qualifier to allow coexistence of PR and prod configs on the same gateway.

**Qualifier pattern:** `pr-<number>` for PRs, `prod` for production.

See `openshift/scripts/render_asa_go_gateway_config.sh` for render usage.

### Manual production publish

```bash
APS_NAMESPACE="<gateway-id>" \
PROJECT_NAMESPACE="<oc-namespace>" \
GW_HOST="<public-host>" \
openshift/scripts/render_asa_go_gateway_config.sh prod ./asa-go-gw-config-prod.yaml

gwa login
gwa config set --gateway <gateway-id>
gwa publish-gateway ./asa-go-gw-config-prod.yaml --qualifier prod
```

### Cleanup (PR)

Publish the empty config under the same qualifier to prune that scope:

```bash
gwa publish-gateway openshift/aps/empty-gw-config.yaml --qualifier <suffix>
```

---

## SFMS Daily FWI

Exposes `/api/sfms/daily-fwi` from the dedicated `wps-sfms-fwi-api` service via key-auth and rate-limiting. The service has no public route — it is reachable only from the APS gateway (see `openshift/templates/allow_gateway_to_wps_sfms_fwi_api.yaml`).

### Two separate publishing flows

**Gateway config** (`gwa publish-gateway`) — deploys the Kong service/route/plugin config. Per-PR with qualifier `fwi-<suffix>`.

**Dataset + Product** (`gwa apply`) — publishes the API Directory listing. Per-PR on the APS test portal; production on the production portal.

### Manual production publish

**Gateway config:**

```bash
APS_NAMESPACE="<gateway-id>" \
PROJECT_NAMESPACE="<oc-namespace>" \
GW_HOST="<public-host>" \
openshift/scripts/render_sfms_fwi_gateway_config.sh prod ./sfms-fwi-gw-config-prod.yaml

gwa login
gwa config set --gateway <gateway-id>
gwa publish-gateway ./sfms-fwi-gw-config-prod.yaml --qualifier fwi-prod
```

```bash
openshift/scripts/render_sfms_fwi_aps_resources.sh prod /tmp/sfms-fwi-prod

gwa login
gwa config set --gateway <gateway-id>
gwa apply -i /tmp/sfms-fwi-prod/sfms-fwi-dataset-prod.yaml
gwa apply -i /tmp/sfms-fwi-prod/sfms-fwi-product-prod.yaml
```

### Cleanup (PR)

Gateway config — publish empty config under the FWI qualifier:

```bash
gwa publish-gateway openshift/aps/empty-gw-config.yaml --qualifier fwi-<suffix>
```

Dataset and Product — delete from the API Directory (test portal, since PR datasets/products are never published to production):

```bash
gwa config set host api-gov-bc-ca.test.api.gov.bc.ca
gwa login
gwa config set --gateway <gateway-id>
TOKEN=$(grep 'api_key:' ~/.gwa-config.yaml | awk '{print $2}')
BASE="https://api-gov-bc-ca.test.api.gov.bc.ca/ds/api/v3/gateways/<gateway-id>"

# Dataset: delete by name
curl -X DELETE "${BASE}/datasets/psu-sfms-daily-fwi-<suffix>" -H "Authorization: Bearer ${TOKEN}"

# Product: the DELETE endpoint uses appId, not the product name
PRODUCT_NAME="SFMS Daily Fire Weather Index (<suffix>)"
PRODUCT_APP_ID=$(curl -s "${BASE}/products" -H "Authorization: Bearer ${TOKEN}" | \
  jq -r --arg name "${PRODUCT_NAME}" '.[] | select(.name==$name) | .appId // empty')
curl -X DELETE "${BASE}/products/${PRODUCT_APP_ID}" -H "Authorization: Bearer ${TOKEN}"
```
