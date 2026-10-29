# Manual Setup

The backend is a `uv`-managed Python workspace (see [backend/README.md](../backend/README.md)).
On macOS most of this is automated by [`setup/mac.sh`](../setup/mac.sh); this document
covers the manual steps and platform-specific notes.
For local credentials and charts, see the [external contributor guide](EXTERNAL_CONTRIBUTORS.md).

#### Local machine, in docker

> **Note:** The full-application Docker Compose setup and VS Code dev container are
> **currently unsupported** and may be out of date — native setup (below) is the
> recommended and supported path. The standalone local object-store sidecar documented
> below is intentionally supported for native development.

For local development with docker compose, copy the repo-root `.env.example` to the
two files compose reads (see `docker-compose.yml`'s `env_file` entries):

- API: `backend/packages/wps-api/src/app/.env.docker`
- Web: `web/.env` (sample at `web/apps/wps-web/.env.example`)

```bash
docker compose build
```

#### Local machine, running MacOS

For native development, copy `.env.example` to `.env` at the repository root,
where python-decouple finds it in a parent directory. Use `external-contributor-api.env`
instead for local S3 credentials. Set database hosts to `localhost`:

```
POSTGRES_WRITE_HOST=localhost
POSTGRES_READ_HOST=localhost
```

NOTE: matching the exact version of postgresql/postgis with production on your local
machine is not necessary — production runs in containers (CrunchyDB) and CI matches it
there. Locally we use Homebrew's `postgresql@17` + `postgis`.

#### Local object storage

For local S3 storage with SeaweedFS, follow the [external guide](EXTERNAL_CONTRIBUTORS.md#4-start-storage-and-the-application).

##### Frontend packages

The frontend uses a pinned public GitHub commit for `@psu/cffdrs_ts`; no Artifactory
or private registry settings are needed. See the [frontend guide](../web/README.md).

##### Java

Some of the unit tests use jnius to compare output against RedAPP. `setup/mac.sh`
installs `openjdk` via brew; point `JAVA_HOME` at it (the default macOS Java is likely
to cause segmentation errors when running the unit tests):

```bash
export JAVA_HOME="$(brew --prefix openjdk)/libexec/openjdk.jdk/Contents/Home"
```

Ensure the `CLASSPATH` environment variable in your `.env` points to the jar files in
`backend/packages/wps-api/libs/` (`REDapp_Lib.jar`, `WTime.jar`, `hss-java.jar`), or the
RedAPP unit tests will fail.

##### Gdal

The python `gdal` binding is pinned in `backend/packages/*/pyproject.toml` and is built
from source by `uv sync` against the system libgdal, which must be **at least** the
pinned version. Install GDAL from Homebrew:

```bash
brew install gdal
```

We deliberately don't `brew pin gdal`: pinning the formula doesn't pin its dependencies
(poppler, proj, geos, …), so a later `brew upgrade` can still move a dependency soname and
break gdal. Letting homebrew keep gdal consistent with its deps avoids that; if gdal drifts
ahead of the pinned version, `uv sync` fails loudly — that's the signal to bump.

Keep the `ghcr.io/osgeo/gdal` base-image tag (`openshift/wps-api-base/docker/Dockerfile`)
and all `gdal==` pyproject pins in step. To bump: update the base-image tag and
all pins, `uv lock`, then `uv sync` (run `brew upgrade gdal` first if your local gdal is
behind).

##### wkhtmltopdf

wkhtmltopdf (used by `pdfkit` to generate HFI calculator PDFs) is discontinued and the
Homebrew cask has been removed. `setup/mac.sh` installs it from the wkhtmltopdf packaging
releases. Note that the production image uses the Linux `0.12.6.1-2` `.deb`, but that
release has **no macOS build** — the newest macOS package is the older `0.12.6-2`
x86_64 ("cocoa") `.pkg`, so on Apple Silicon it needs Rosetta 2:

```bash
softwareupdate --install-rosetta --agree-to-license
curl -L -o /tmp/wkhtmltox.pkg \
  https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-2/wkhtmltox-0.12.6-2.macos-cocoa.pkg
sudo installer -pkg /tmp/wkhtmltox.pkg -target /
```

PDF generation is not required for most backend work; the package is unsigned and the
project is archived, so this is best-effort.

##### eccodes

The weather-model tests need the ecCodes library:

```bash
brew install eccodes
```

##### Python (pyenv) and uv

Match the latest version of python in our production environment (as of writing, 3.12.3):

```bash
brew install pyenv
pyenv install 3.12.3
pyenv global 3.12.3
brew install uv
```

##### Install project python requirements

Dependencies are installed for the whole workspace with `uv sync` — there is no
per-package install step, and gdal/wps_shared are handled by the lockfile (no manual
`pip install` needed).

`psycopg2` builds from source, so `pg_config` must be on `PATH`. `postgresql@17` is
keg-only, so expose its bin dir first:

```bash
export PATH="$(brew --prefix postgresql@17)/bin:$PATH"
cd backend
uv sync --all-extras
```

##### Troubleshooting

###### psycopg2

If you get errors about `pg_config` not being found when building `psycopg2`, it means
`pg_config` isn't on `PATH` — see the export above (`$(brew --prefix postgresql@17)/bin`).

###### GDAL

If the python gdal build complains about header files (likely if you've installed gdal
manually rather than via brew), help it find them before running `uv sync`:

```bash
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
```

If gdal isn't building on a mac with errors like "no member named 'signbit' in the global
namespace", then:

- ensure you've applied the most recent OS updates
- ensure XCode is updated
- wipe your existing virtual environment (`backend/.venv`) and re-run `uv sync`

#### Local machine, running Linux

These notes are incomplete and unverified. This branch pins GDAL bindings to 3.13.3;
check system GDAL before installing Python packages. Distribution packages may be too old.

##### Ubuntu

The production base image (`openshift/wps-api-base/docker/Dockerfile`) is the
authoritative list of system dependencies. Historical Ubuntu package notes:

```bash
sudo apt install python3 python3-pip python3-dev python-is-python3
# geospatial / build dependencies
sudo apt install libgdal-dev libproj-dev libgeos-dev libsqlite3-dev libxml2-dev cmake build-essential
# required by cffdrs
sudo apt install libudunits2-dev
# postgres client headers (for psycopg2)
sudo apt install libpq-dev
# the jdk (for running tests against RedAPP)
sudo apt install default-jdk
```

Install `uv` (<https://docs.astral.sh/uv/>) and run `uv sync --all-extras` from
`backend/`. The python `gdal` package must match the system libgdal version.

##### Fedora

Historical package note, not a complete setup:

```bash
sudo dnf install unixODBC-devel
```

### Executing program

See the [Makefile](../Makefile) for docker examples and [backend/README.md](../backend/README.md)
for running the API natively.

Install dependencies (required before running the program for the first time):

```bash
cd backend && uv sync --all-extras
```

The full application Docker stack remains unsupported:

```bash
make docker-run        # docker compose up
```

Run the API natively from `backend/` so the contributor template's relative Java
classpath resolves correctly:

```bash
uv run --package wps-api python -m app.main
```

To shell into the running docker containers: `make docker-shell-api` / `make docker-shell-web`.

### Running the database locally

#### In Docker

```bash
make docker-db         # docker compose up db
```

Runs a local Postgres/PostGIS container and creates the `wps` database.

#### Natively

We use Homebrew `postgresql@17` + `postgis` locally. (This became viable once the
project's GDAL pin moved to current homebrew-core — brew `postgis` links the same
libgdal the venv uses, so there is no longer a conflict. The older Postgres.app
workaround is no longer required.)

```bash
brew install postgresql@17 postgis
brew services start postgresql@17
```

Create the database, extension and users unless `setup/mac.sh` already did so.
These values match the `.env` defaults:

```bash
psql -d postgres -c "create database wps;"
psql -d wps -c "create extension postgis;"
psql -d wps -c "
CREATE USER wps;
CREATE USER wpsread;
"
```

Apply these role settings even after `setup/mac.sh`. Grants cover existing tables
and future tables created by the migration role, `wps`:

```bash
psql -d wps -c "
ALTER USER wps WITH LOGIN;
ALTER USER wpsread WITH LOGIN;
ALTER USER wps WITH SUPERUSER;
ALTER USER wps WITH PASSWORD 'wps';
ALTER USER wpsread WITH PASSWORD 'wps';
GRANT CONNECT ON DATABASE wps TO wpsread;
GRANT USAGE ON SCHEMA public TO wpsread;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO wpsread;
ALTER DEFAULT PRIVILEGES FOR ROLE wps IN SCHEMA public
  GRANT SELECT ON TABLES TO wpsread;
"
```

`\dx` in `psql -d wps` should list `postgis`. Then run the migrations:

```bash
cd backend/packages/wps-api && uv run --package wps-api alembic upgrade head
```

The CI pipeline enforces migrations and tests with `uv run pytest` (see
`.github/workflows/integration.yml`); run `cd backend && uv run pytest` locally to match.

##### Postgres.app (alternative)

If you'd rather not use Homebrew postgres, [Postgres.app](https://postgresapp.com/)
bundles Postgres + PostGIS. Create the database/users with the same SQL as above. Note
that Postgres.app bundles its own older `gdal-config`; if you add its `bin` to `PATH`,
**append** it rather than prepend, so it doesn't shadow Homebrew's gdal during `uv sync`.

## New Workstation Setup

### Required Software

The following is a list of required software applications and packages. Some of these can be installed automatically using the `setup/mac.sh` script.

- VS Code (technically there are other options, but this is arguably the best)
  - using the "Python: Select Interpreter" command within VS Code, select `backend/.venv/bin/python`
- Git CLI
- GitHub CLI
- OpenShift CLI for deployment work only
- Docker with Compose for local object storage and container tests
- Brew (for Mac)

### Optional but Recommended Software

- [Oh My Zsh](https://ohmyz.sh/)
- [Zenhub extension for GitHub](https://www.zenhub.com/extension)

### Recommended VS Code Extensions

The extensions listed here are shown exactly as they appear in the VS Code Extensions marketplace.

- Copy without formatting
- Dev Containers
- Docker
- ESLint
- GitLens - Git supercharged
- Jupyter
- Jupyter Cell Tags
- Jupyter Keymap
- Jupyter Notebook Renderers
- Jupyter Slide Show
- Makefile Tools
- Markdown All in One
- markdownlint
- Markdown Preview Enhanced
- Markdown+Math
- Math to Image
- Prettier - Code formatter
- Pylance
- Python
- Rainbow Brackets
- Remote - SSH
- Ruff
- SonarLint
- VS Code Counter
