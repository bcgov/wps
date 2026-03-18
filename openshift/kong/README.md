# Kong API Gateway — Public FBA Routes

Routes `/api/fba/*` publicly via the BC Government [API Platform Services (APS)](https://api.gov.bc.ca) Kong gateway, with IP-based rate limiting.

Public endpoint: `https://api.psu.nrs.gov.bc.ca/api/fba/*`
Upstream: `https://psu.nrs.gov.bc.ca/api/fba/*`

## Onboarding (one-time)

1. Log in to https://api.gov.bc.ca with your IDIR
2. Create an APS namespace (this is separate from your OpenShift project namespace) and note the name
3. Generate a service account — save the client ID and secret
4. Replace `YOUR_NAMESPACE` in `kong.yaml` with your APS namespace
5. Request a DNS CNAME for `api.psu.nrs.gov.bc.ca` pointing at the APS Kong gateway (contact the APS team for the target)

## Prerequisites

```bash
npm install -g @bcgov/gwa-cli
```

## Publishing the config

The config is published automatically on production deploy via `production.yml`. It requires three secrets set in GitHub:

| Secret | Description |
|---|---|
| `GWA_NAMESPACE` | APS namespace name |
| `GWA_CLIENT_ID` | APS service account client ID |
| `GWA_CLIENT_SECRET` | APS service account client secret |

To publish manually:

```bash
export GWA_NAMESPACE=<namespace>
export GWA_CLIENT_ID=<id>
export GWA_CLIENT_SECRET=<secret>

gwa login --client-id $GWA_CLIENT_ID --client-secret $GWA_CLIENT_SECRET
envsubst < openshift/kong/kong.yaml | gwa pg
```

PR dev environments do not use Kong — they are accessible directly via the OpenShift dev route at `https://${SUFFIX}-dev-psu.apps.silver.devops.gov.bc.ca/api/fba/*`.

## Configuration

See `kong.yaml`. Key settings:

| Setting | Value | Notes |
|---|---|---|
| `limit_by` | `ip` | Rate limit per client IP |
| `minute` | `60` | Requests per minute per IP |
| `hour` | `1000` | Requests per hour per IP |
| `policy` | `local` | In-memory, ~1ms overhead |

Adjust the rate limits to suit expected public traffic before publishing.
