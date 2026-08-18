# k6-on-Lambda

Runs k6 itself *inside* an AWS Lambda function (via a layer), instead of on the now-removed
DLT (Distributed Load Testing on AWS) stack's ECS Fargate tasks. Same k6 script, same checks,
same rate-shaping but different execution substrate.

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
uv run --project packages/wps-tools python -m wps_tools.load_testing.verify_ip_diversity \
  --region ca-central-1 --concurrency 50
```

Running this shows that most lambdas (~80%) depending on concurrency, get assigned a unique IP.
This is our best known option for load testing our public API without hitting our rate-limit-by-ip policy. 


## Usage

```bash
# Build the k6 layer, create the execution role, deploy the function to every listed region
uv run --project packages/wps-tools python -m wps_tools.load_testing.deploy_k6_lambda \
  deploy ../k6_scripts/asa_go_peak_burst.js --regions ca-central-1,ca-west-1,us-west-1,us-west-2

# Fan out N concurrent invocations in EACH region (the --task-count analog)
uv run --project packages/wps-tools python -m wps_tools.load_testing.deploy_k6_lambda \
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

- **Lambda's filesystem is read-only except `/tmp`, which is shared and world-writable.**
  `handler.py` sets `HOME` to a privately-owned (0700) `tempfile.mkdtemp()`
  subdirectory rather than `/tmp` itself -- without a writable `$HOME`, k6 tries to write its
  own config/cache to an unwritable default and fails outright.
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
  all). `aggregate_summaries` relies on this: a Counter no invocation ever touched is simply
  absent from the combined `metrics` output too, not defaulted to `count: 0`.
- **`aggregate_summaries` combines every metric k6 reports, not just `http_reqs` and
  `rate_limited_responses`** -- it detects each metric's shape (Counter/Gauge/Trend) from its
  fields rather than hardcoding metric names, so built-ins like `http_req_duration`, `vus`,
  `data_sent`, etc. and any custom metric a different script defines all show up under the
  combined `metrics` output, and check names are aggregated by name too -- this now works for
  any script, not just `asa_go_peak_burst.js`. Counters sum exactly; Gauges (e.g. `vus`,
  `vus_max`) report the peak (max) value seen; Trends report min-of-mins/max-of-maxes/an
  unweighted mean of `avg` (an approximation, not a recomputed percentile, since
  `--summary-export` only gives each invocation's own already-aggregated stats -- percentile
  fields like `p(90)` aren't recombinable and are dropped rather than silently averaged into
  something meaningless). Confirmed live against a real k6 v2.2.0 `--summary-export` (10
  Lambda invocations against production, 2026-08-17) -- notably `http_req_failed` and the
  built-in aggregate `checks` pass rate are actually Gauge-shaped (`{"value": ...}`), not
  Rate-shaped as their names might suggest; every metric this run observed had one of
  `count`/`value`/`avg`, none needed the bare-`rate` fallback branch. Those two are still
  semantically rates despite the Gauge shape, so they're averaged across invocations instead
  of maxed like a real gauge -- max() would report the worst single invocation's rate as if it
  were the whole run's.
- **k6's `ramping-arrival-rate` executor requires an integer `stages[].target`.**
  `asa_go_peak_burst.js`'s `TARGET_RPS` is requests/second (matching `--target-rps`'s
  documented units); dividing it by `REQUESTS_PER_ITERATION` to get an iterations/second rate
  produces a fractional value, not an integer -- confirmed live: k6 refused to even parse the
  script (`cannot unmarshal number 1.6666666666666667 ... of type int64`) until the scenario's
  `timeUnit` was changed to `60s` and the stage target computed as
  `Math.round(TARGET_ITERATIONS_PER_SECOND * 60)`, so it lands on a whole number of
  iterations per minute instead of rounding a fractional per-second target.
- **A Lambda layer's zip is extracted directly into `/opt/`, not merged under it.** An entry
  named `opt/k6` inside the zip therefore lands at `/opt/opt/k6`, not `/opt/k6` --
  confirmed live: `handler.py`'s `K6_BINARY = "/opt/k6"` got a `FileNotFoundError` until
  `build_layer_zip`'s zip entry was renamed from `"opt/k6"` to the top-level `"k6"`.
- **The k6 binary zips to ~65MB, over Lambda's direct-upload limit for
  `PublishLayerVersion`.** Confirmed live: passing it via `Content={"ZipFile": ...}` failed
  with `RequestEntityTooLargeException` ("Request must be smaller than 70167211 bytes").
  `publish_k6_layer` instead stages the zip in a dedicated per-region S3 bucket
  (`ensure_layer_bucket`, named `k6-lambda-layer-<account-id>-<region>`, created on first use)
  and references it via `Content={"S3Bucket": ..., "S3Key": ...}`, which supports layers up
  to Lambda's real 250MB-unzipped limit.

## Tearing everything down

`teardown_k6_lambda.py` deletes every resource `deploy`/`run`/`verify_ip_diversity.py` can
create in a region: both Lambda functions (the k6 load generator and the IP-diversity probe)
and their CloudWatch Logs log groups (Lambda auto-creates these on first invocation; deleting
the function alone leaves them behind), every version of the k6 layer, the per-region S3
staging bucket (emptied first), and -- once, after every region -- the shared IAM execution
role.

```bash
uv run --project packages/wps-tools python -m wps_tools.load_testing.teardown_k6_lambda \
  --regions ca-central-1,ca-west-1,us-west-1,us-west-2
```

Prompts for confirmation unless `--yes` is passed. One region failing doesn't stop the others
(same collect-and-continue handling as `deploy`/`run`), and the IAM role is still deleted
even if a region-level resource failed to clean up.
