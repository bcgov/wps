# ASA Go Load Tests

k6 load test harness for the ASA Go public API (`psu.api.gov.bc.ca`).

Two scenarios run sequentially in a single script:
1. **`rate_limit_check`** (0–3 min): 1 VU, single IP — verifies Kong returns 429s at 100 req/min per IP
2. **`upstream_saturation`** (4–14 min): ramping 1→50 VUs, 20 IPs — finds the upstream latency/error ceiling

## Prerequisites

- [k6](https://grafana.com/docs/k6/latest/set-up/install-k6/) installed
- Access to `psu.api.gov.bc.ca` (no auth required — public API)
- An active SFMS run for today (the setup step will fail if no data is available yet)

## IP alias setup

Kong rate-limits by `X-Forwarded-For` IP. The script sets this header per VU to simulate 20 distinct clients.
For belt-and-suspenders, IP aliases also vary the TCP source IP (Linux only for k6's `--local-ips`).

**Linux:**
```bash
./setup_ips.sh        # adds 127.0.0.2-127.0.0.21 on lo (requires sudo)
```

**macOS:**
```bash
./setup_ips_macos.sh  # adds aliases on lo0 (requires sudo)
# Note: k6's --local-ips flag is Linux-only. On macOS, X-Forwarded-For header handles IP simulation.
```

## Running the full test

**Linux** (both TCP source IP and X-Forwarded-For vary):
```bash
./setup_ips.sh
k6 run --local-ips 127.0.0.2-127.0.0.21 --out json=results.json load_test.js
./teardown_ips.sh
```

**macOS** (X-Forwarded-For only — sufficient since Kong reads that header):
```bash
./setup_ips_macos.sh
k6 run --out json=results.json load_test.js
./teardown_ips_macos.sh
```

## Running a single scenario

```bash
# Rate limit check only
k6 run --include-scenarios rate_limit_check load_test.js

# Saturation only
k6 run --local-ips 127.0.0.2-127.0.0.21 --include-scenarios upstream_saturation load_test.js
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

## Security note

Kong trusts `X-Forwarded-For` from the upstream caller. This means a caller who can set that header
freely can bypass per-IP rate limiting by spoofing different IPs. The saturation scenario demonstrates
this. Confirm with the team whether this is acceptable given the trust model of the upstream proxy.

## Adjusting the number of IPs

20 IPs gives ~2000 req/min headroom through Kong (20 × 100 req/min). If the upstream saturates
before reaching that limit, no change is needed. If you want higher throughput, increase the IP range
in `setup_ips.sh` and the `ALIAS_IPS` array in `load_test.js` to match.
