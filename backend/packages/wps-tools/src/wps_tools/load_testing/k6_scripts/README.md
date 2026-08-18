# k6 scripts

k6 test scripts (`.js`) for use with [`deploy_k6_lambda.py`](../deploy_k6_lambda.py).
Each script targets a specific endpoint or flow, so there's no default -- pass one explicitly:

```bash
uv run --project packages/wps-tools python -m wps_tools.load_testing.deploy_k6_lambda \
  deploy k6_scripts/<name>.js --regions ca-central-1,ca-west-1,us-west-1,us-west-2
```

Scripts here can also be run locally with the [k6 CLI](https://k6.io/docs/get-started/installation/)
for quick iteration before deploying:

```bash
k6 run k6_scripts/<name>.js
```
