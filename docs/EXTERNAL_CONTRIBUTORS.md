# External contributor guide

Run the API and frontend natively with SeaweedFS and local S3 credentials.
This guide covers macOS; other platforms are unverified. The full application
Compose stack and dev container remain unsupported.

Start each command block from the repository root.

## 1. Install dependencies

Run `bash setup/mac.sh` and apply its printed shell settings. See
[manual setup](MANUAL_SETUP.md#local-machine-running-macos) for dependencies,
[Colima](COLIMA_SETUP.md) for Docker, and the [frontend guide](../web/README.md#dependencies)
for Node 24 and Yarn.

The script starts Postgres and Redis and creates the database and roles. Also apply
[role configuration](MANUAL_SETUP.md#natively) for the read-user password and grants.
Skip database and user creation if they exist. OpenShift access is not required.

## 2. Configure the local environment

Copy these templates only if the destination files do not exist:

```bash
cp external-contributor-api.env .env
cp external-contributor-web.env web/apps/wps-web/.env
```

Keep the API `.env` at the repository root; shell variables or a nearer `.env` can
override it. Run the API and tests from `backend/` to resolve the template's Java
`CLASSPATH`. Restart the API or frontend after changing its environment file.

## 3. Install Python packages and run migrations

```bash
cd backend
uv sync --all-extras --locked
cd packages/wps-api
uv run --package wps-api alembic upgrade head
```

Migrations create the schema and load seed data, without weather history or rasters.

## 4. Start storage and the application

With Docker running:

```bash
make local-object-store-up
```

SeaweedFS creates empty `wps-local` and `wps-wx-local` buckets. S3 uses
`http://127.0.0.1:9000`; the admin UI uses <http://127.0.0.1:9001>.
Both ports bind to loopback. A Docker volume preserves data across restarts.
SeaweedFS 4.47 uses the [Apache License 2.0](https://github.com/seaweedfs/seaweedfs/blob/master/LICENSE).

Start the API in a separate terminal:

```bash
cd backend
uv run --package wps-api python -m app.main
```

Check <http://localhost:8080/api/ready> for HTTP 200. `/api/health` requires deployed
infrastructure and fails locally. Alternatively, use the VS Code `api` launch with
`backend/.venv/bin/python` selected.

Start the frontend in another terminal:

```bash
cd web
corepack enable
yarn install --immutable
yarn turbo dev
```

`@psu/cffdrs_ts` comes from public GitHub; no Artifactory token is needed.

## 5. Generate and view charts

Choose a published UTC date from [MSC Datamart](https://eccc-msc.github.io/open-data/msc-datamart/readme_en/).
In VS Code, run `Weather - Local 4Panel Charts` with GDPS or RDPS and the `00` or `12`
run. It downloads public ECCC inputs and generates through forecast hour 6 without
the chart status database. Other RDPS/GDPS launches need existing GRIB inputs and Postgres.

Alternatively, run:

```bash
uv run --project backend --package wps-weather python \
  -m wps_weather.wx_4panel_charts.backfill \
  --model GDPS \
  --init-ymd "$(date -u +%Y%m%d)" \
  --model-run 00 \
  --end-hour 12
```

The command skips existing objects. GDPS hours use a 6-hour interval up to 240;
RDPS uses a 3-hour interval up to 84. Larger ranges require more downloads and processing.
The first run also downloads Cartopy map data and needs a writable cache.

Open <http://localhost:3000/weather-toolkit> with the same model, date, and run.
For download 404s, try a recent published date; today's `00` run may be unavailable
and older runs may have expired.

## Limits and cleanup

Protected pages require login and roles; WF1 needs credentials and service access.
Local buckets lack operational rasters, and the template's map URLs are placeholders.
The deprecated `/api/sfms/hourlies` endpoint still returns deployed object-store URLs.

Run tests from `backend/` with `uv run pytest`; Testcontainers tests need Docker.

`make local-object-store-down` stops SeaweedFS and preserves data.
`make local-object-store-destroy` stops it and deletes all local object-store data.
`make local-object-store-reset` destroys the data, then restarts with empty buckets.
Stop native Postgres and Redis separately when no longer needed.
