# ASA Go Load Tests

k6 load test harness for the ASA Go public API (`psu.api.gov.bc.ca`).

Two scenarios run sequentially in a single script:
1. **`rate_limit_check`** (0–3 min): 1 VU, single IP — verifies Kong returns 429s at 100 req/min per IP
2. **`upstream_saturation`** (4–14 min): ramping 1→50 VUs, 20 IPs — finds the upstream latency/error ceiling

## Prerequisites

- [k6](https://grafana.com/docs/k6/latest/set-up/install-k6/) installed
- A [Grafana Cloud](https://grafana.com/auth/sign-up/create-user) account (free tier — 500 VU-hours/month, 50 VU max)
- `K6_CLOUD_TOKEN` set to your Grafana Cloud k6 API token
- Access to `psu.api.gov.bc.ca` (no auth required — public API)
- An active SFMS run for today (the setup step will fail if no data is available yet)

## Running the full test

```bash
K6_CLOUD_TOKEN=<your-token> k6 cloud run load_test.js
```

Results are stored in Grafana Cloud with a dashboard link printed at the end of the run.

## Running a single scenario

```bash
# Rate limit check only
K6_CLOUD_TOKEN=<your-token> k6 cloud run --include-scenarios rate_limit_check load_test.js

# Saturation only
K6_CLOUD_TOKEN=<your-token> k6 cloud run --include-scenarios upstream_saturation load_test.js
```

## Interpreting results

### Rate limit check
- **Pass:** `rate_limited` counter > 0, `http_req_failed` rate > 10%
- Look for `X-RateLimit-Limit-Minute: 100` and `X-RateLimit-Remaining-Minute: N` headers in the check summary
- 429s should appear ~100 requests into the first minute window

### Upstream saturation
- **Saturation point:** the RPS level at which p95 latency starts climbing sharply in the summary
- **Hard ceiling:** the RPS level at which `upstream_errors` (5xx) begins increasing
- Record both values as the findings for [issue #5364](https://github.com/bcgov/wps/issues/5364)

### Threshold summary (exit code)
k6 exits non-zero if thresholds fail:
- `rate_limit_check` fails if no 429s were observed (Kong rate limiting not working)
- `upstream_saturation` fails only if p95 latency exceeds 10s (safety net — expect passes unless the service is severely degraded)

