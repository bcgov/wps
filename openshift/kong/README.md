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

```bash
gwa login --client-id <id> --client-secret <secret>
gwa pg openshift/kong/kong.yaml
```

## Configuration

See `kong.yaml`. Key settings:

| Setting | Value | Notes |
|---|---|---|
| `limit_by` | `ip` | Rate limit per client IP |
| `minute` | `60` | Requests per minute per IP |
| `hour` | `1000` | Requests per hour per IP |
| `policy` | `local` | In-memory, ~1ms overhead |

Adjust the rate limits to suit expected public traffic before publishing.
