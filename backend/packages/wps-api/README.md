Assumes installation and setup is done in [backend/README.md](../../../backend/README.md)

Run API with:

```bash
uv run --package wps-api python -m app.main
```

### Testing

Code must pass all unit tests.

```bash
uv run pytest
```

### Troubleshooting

**`uv sync` fails building psycopg2: `pg_config executable not found`**

`pg_config` must be on `PATH`. `postgresql@17` is keg-only, so add it:

```bash
export PATH="$(brew --prefix postgresql@17)/bin:$PATH"
```

**Tests using jnius/REDapp segfault or can't find Java**

Point `JAVA_HOME` at the brew openjdk (mac.sh installs it):

```bash
export JAVA_HOME="$(brew --prefix openjdk)/libexec/openjdk.jdk/Contents/Home"
```

**`GET /api/health` returns 500 locally**

Expected — `/api/health` checks the CrunchyDB/patroni cluster via the OpenShift
API, which isn't available locally. Use `GET /api/ready` to confirm the API is up.
