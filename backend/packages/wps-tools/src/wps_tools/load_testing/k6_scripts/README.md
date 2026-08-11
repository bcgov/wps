# k6 scripts

k6 test scripts (`.js`) for use with `run_k6_test.py`. Each script targets a
specific endpoint or flow, so there's no default -- pass one explicitly:

```bash
uv run --project packages/wps-tools python -m wps_tools.load_testing.run_k6_test \
  k6_scripts/<name>.js --stack-name distributed-load-testing --region ca-central-1
```

Scripts here can also be run locally with the [k6 CLI](https://k6.io/docs/get-started/installation/)
for quick iteration before uploading:

```bash
k6 run k6_scripts/<name>.js
```

Every script needs at least one HTTP call (`http.get`/`http.post`/etc). Taurus/BZT
(which wraps k6 on the Fargate task) only captures request-level metrics in its
CSV output; a script that never issues a request produces an empty results file,
and BZT reports the whole run as failed even if k6 itself ran and exited cleanly.
