# APS Gateway Configuration

This directory contains APS gateway configuration for services exposed through the BC Government API Services Portal.

## Services

| Service        | Gateway config            | Dataset / Product                                |
| -------------- | ------------------------- | ------------------------------------------------ |
| ASA Go API     | `asa-go-gw-config.yaml`   | —                                                |
| SFMS Daily FWI | `sfms-fwi-gw-config.yaml` | `sfms-fwi-dataset.yaml`, `sfms-fwi-product.yaml` |

## Gateway IDs

Two different gateways are in play, on two different tenants, using different credentials
(see `.github/workflows/deployment.yml`/`cleanup.yml` `env:` blocks):

| Gateway ID | Tenant                | Used for                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ---------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `gw-313f6` | Production APS portal | Real production releases only (`production.yml`) — both Kong gateway-config publishing (`gwa publish-gateway`) and, for SFMS FWI, Dataset/Product API Directory publishing (`gwa apply`). Credentials: `secrets.GWA_ACCT_ID` / `secrets.GWA_ACCT_SECRET`.                                                                                                                                                                       |
| `gw-11008` | Test APS portal       | All PR/dev builds (`deployment.yml`, `cleanup.yml`) — both gateway-config publishing and Dataset/Product publishing. Requires the `host: api-gov-bc-ca.test.api.gov.bc.ca` override; the test portal is a fully separate tenant, not reachable with the production credentials above. Credentials: `secrets.GWA_TEST_ACCT_ID` / `secrets.GWA_TEST_ACCT_SECRET`. Service account needs the same permissions as `gw-313f6` above. |

---

## ASA Go API

Exposes the ASA Go API at `<public-host>/api/asa-go` via rate-limiting (no key-auth).

### Publishing

Uses `gwa publish-gateway` (raw Kong format). PR builds publish to the **test** gateway
(`gw-11008`); production publishes to the **production** gateway (`gw-313f6`) — see
"Gateway IDs" above. The `--qualifier` (`pr-<number>` for PRs, `prod` for production) further
scopes configs within whichever gateway is targeted, so multiple PRs can coexist on the test
gateway without pruning each other.

See `openshift/scripts/render_asa_go_gateway_config.sh` for render usage.

### Manual production publish

```bash
APS_NAMESPACE="<gateway-id>" \
PROJECT_NAMESPACE="<oc-namespace>" \
GW_HOST="<public-host>" \
openshift/scripts/render_asa_go_gateway_config.sh prod ./asa-go-gw-config-prod.yaml

gwa config set host api.gov.bc.ca
gwa login
gwa config set --gateway <gateway-id>
gwa publish-gateway ./asa-go-gw-config-prod.yaml --qualifier prod
```

### Cleanup (PR)

Publish the empty config under the same qualifier to prune that scope. Targets the **test**
gateway (`gw-11008`), same as the PR publish above:

```bash
gwa publish-gateway openshift/aps/empty-gw-config.yaml --qualifier <suffix>
```

---

## SFMS Daily FWI

Exposes `/api/sfms/daily-fwi` from the dedicated `wps-sfms-fwi-api` service via key-auth and rate-limiting. The service has no public route — it is reachable only from the APS gateway (see `openshift/templates/allow_gateway_to_wps_sfms_fwi_api.yaml`).

### Two publishing flows, both split by PR vs. production tenant

Both flows below publish to `gw-11008` on the **test** APS portal for PR builds
(`deployment.yml`, `cleanup.yml`), and to `gw-313f6` on the **production** APS portal for real
production releases (`production.yml`) — see "Gateway IDs" above. Each tenant has its own
service account; production credentials aren't valid against the test portal, and vice versa.

**Gateway config** (`gwa publish-gateway`) — deploys the Kong service/route/plugin config. The
`--qualifier` (`fwi-<suffix>` for PRs, `fwi-prod` for production) further namespaces configs
within whichever gateway is targeted, and `GW_HOST`/`PROJECT_NAMESPACE` control which actual
OpenShift backend a route forwards to.

**Dataset + Product** (`gwa apply`) — publishes the API Directory (devportal) listing. Has no
qualifier-equivalent scoping of its own, so it relies entirely on being pointed at the correct
gateway/tenant for the build.

### Manual production publish

**Gateway config:**

```bash
APS_NAMESPACE="<gateway-id>" \
PROJECT_NAMESPACE="<oc-namespace>" \
GW_HOST="<public-host>" \
openshift/scripts/render_sfms_fwi_gateway_config.sh prod ./sfms-fwi-gw-config-prod.yaml

gwa config set host api.gov.bc.ca
gwa login
gwa config set --gateway <gateway-id>
gwa publish-gateway ./sfms-fwi-gw-config-prod.yaml --qualifier fwi-prod
```

```bash
openshift/scripts/render_sfms_fwi_aps_resources.sh prod /tmp/sfms-fwi-prod

gwa config set host api.gov.bc.ca
gwa login
gwa config set --gateway <gateway-id>
gwa apply -i /tmp/sfms-fwi-prod/sfms-fwi-dataset-prod.yaml
gwa apply -i /tmp/sfms-fwi-prod/sfms-fwi-product-prod.yaml
```

### Cleanup (PR)

Gateway config — publish empty config under the FWI qualifier. Targets the **test** gateway
(`gw-11008`), same as the PR publish above:

```bash
gwa publish-gateway openshift/aps/empty-gw-config.yaml --qualifier fwi-<suffix>
```

Dataset and Product — delete from the API Directory. Also targets the **test** gateway
(`gw-11008`), since PR datasets/products are only ever published there, never to production:

```bash
gwa config set host api-gov-bc-ca.test.api.gov.bc.ca
gwa login
gwa config set --gateway <test-gateway-id>
TOKEN=$(grep 'api_key:' ~/.gwa-config.yaml | awk '{print $2}')
BASE="https://api-gov-bc-ca.test.api.gov.bc.ca/ds/api/v3/gateways/<test-gateway-id>"

# Dataset: delete by name
curl -X DELETE "${BASE}/datasets/psu-sfms-daily-fwi-<suffix>" -H "Authorization: Bearer ${TOKEN}"

# Product: the DELETE endpoint uses appId, not the product name
PRODUCT_NAME="SFMS Daily Fire Weather Index (<suffix>)"
PRODUCT_APP_ID=$(curl -s "${BASE}/products" -H "Authorization: Bearer ${TOKEN}" | \
  jq -r --arg name "${PRODUCT_NAME}" '.[] | select(.name==$name) | .appId // empty')
curl -X DELETE "${BASE}/products/${PRODUCT_APP_ID}" -H "Authorization: Bearer ${TOKEN}"
```
