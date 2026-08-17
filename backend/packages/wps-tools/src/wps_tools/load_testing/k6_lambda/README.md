# k6-on-Lambda

Runs k6 itself *inside* an AWS Lambda function (via a layer), instead of on the DLT stack's
ECS Fargate tasks (`../manage_dlt.py`). Same k6 script, same checks, same rate-shaping but
different execution substrate.

A Lambda function *without* VPC configuration bypasses this VPC's networking entirely and
uses AWS's own shared, region-wide Lambda IP pool instead. Invocation **concurrency** becomes
the analog of `--task-count`: each concurrent invocation is more likely to land on a distinct
execution environment (and thus a distinct egress path) than serialized calls.

## Verifying real IP diversity, before trusting it for the actual test

Everything above is the theory: Lambda without VPC config *should* get its outbound IP from
AWS's shared pool instead of this VPC's gateway-bound egress. It is something that can be validated,
to some degree, via `verify_ip_diversity.py`, it deploys a
tiny throwaway function (`ip_probe_handler.py`, no k6 layer, no bundled script) that just
calls a public IP-echo service (`https://checkip.amazonaws.com`) and returns what it saw,
fans out `--concurrency` invocations at once, and reports how many *distinct* IPs came back:

```bash
uv run --project packages/wps-tools python -m wps_tools.load_testing.k6_lambda.verify_ip_diversity \
  --region ca-central-1 --concurrency 50
```

Running this shows that most lambdas (~80%) depending on concurrency, get assigned a unique IP.
This is our best known option for load testing our public API without hitting our rate-limit-by-ip policy. 


## Usage

```bash
# Build the k6 layer, create the execution role, deploy the function to every listed region
uv run --project packages/wps-tools python -m wps_tools.load_testing.k6_lambda.deploy_k6_lambda \
  deploy ../k6_scripts/asa_go_peak_burst.js --regions ca-central-1,ca-west-1,us-west-1,us-west-2

# Fan out N concurrent invocations in EACH region (the --task-count analog)
uv run --project packages/wps-tools python -m wps_tools.load_testing.k6_lambda.deploy_k6_lambda \
  run --function-name k6-lambda-load-gen --regions ca-central-1,ca-west-1,us-west-1,us-west-2 \
  --concurrency 10
```

Each AWS region has its own separate, non-overlapping shared IP pool -- confirmed directly
against AWS's published `ip-ranges.json` (there's no dedicated `LAMBDA` service tag in it;
non-VPC Lambda draws from the same region-scoped dynamic `AMAZON`/`EC2` pool as everything
else). That's why `--regions` fans out across several rather than relying on `--concurrency`
alone in one region:

| region | dynamic pool size (unique IPv4 addresses) |
|---|---|
| ca-central-1 | ~1.49M |
| ca-west-1 | ~0.80M |
| us-west-1 | ~1.99M |
| us-west-2 | ~11.06M |

`deploy --regions ...` builds the k6 layer and reads the target script once, then deploys to
every listed region in parallel (the IAM execution role is also created once and reused --
IAM has no per-region endpoint, unlike the layer and function, which are regional).
`run --regions ...` fires `--concurrency` invocations in **each** region in parallel, so total invocations scale with region count, and prints one aggregate summary plus a `by_region`
breakdown. If any single region fails to deploy or run, the others still complete and the failure is reported rather than aborting the whole batch.

A single `--region <region>` still works if you want to target just one -- `--region` and `--regions` are mutually exclusive, and one of them must always be given.

Verify each new region's actual IP diversity with `verify_ip_diversity.py --region <region>`
before trusting it for a real run -- same reasoning as the single-region case above.

## Gotchas

- **Lambda's filesystem is read-only except `/tmp`.** `handler.py` sets `HOME=/tmp` on the k6
  subprocess explicitly -- without it, k6 tries to write its own config/cache to an
  unwritable default `$HOME` and fails outright.
- **k6 pings home on startup by default.** `handler.py` sets `K6_DISABLE_USAGE_REPORT=true` to
  skip k6's own update-check/telemetry call -- one less unrelated outbound request per cold
  start, and avoids conflating that traffic with the actual test.
- **Function timeout must exceed the k6 script's own total duration**, or invocations get
  killed mid-run before k6 can write its summary. `--timeout-seconds` defaults to 150s against
  `asa_go_peak_burst.js`'s ~105s (30s ramp + 60s hold + 15s ramp-down) -- adjust if you point
  this at a different script.
- **The bundled script's filename isn't rediscoverable from the function itself by default.**
  `deploy` sets it as the `SCRIPT_NAME` environment variable; `handler.py` reads that as a
  fallback when an invocation's event payload doesn't override it, and `run` reads it back via
  `get_function` to fail fast with a clear error if you try to `run` before ever `deploy`ing.
- **k6 omits a Counter metric entirely from `--summary-export` when it was never
  incremented**, rather than including it with `count: 0` -- confirmed via the podman test
  above (an invocation with zero 429s has no `rate_limited_responses` key in `metrics` at
  all). `aggregate_summaries` relies on this and defaults every lookup accordingly; don't
  "simplify" those `.get(..., {})` calls into direct indexing.
- **`aggregate_summaries` is intentionally specific to `asa_go_peak_burst.js`'s own check
  names and counter** (`status is 200`, `status is 429 (rate limited)`,
  `rate_limited_responses`), not a generic k6-summary parser -- reasonable since this module
  always runs one known script, but it'll silently report zeros if pointed at a script with
  different check/counter names rather than erroring.
