# Ubuntu development setup

This guide sets up the WPS backend and web frontend on **Ubuntu 26.04 LTS**,
either natively or in **WSL 2**. Use Bash and a normal Linux user with sudo access.
The [setup script](./ubuntu.sh) installs dependencies, but does not configure
application secrets, populate application data, run migrations, or start the API
and frontend.

**Local development only:** setup creates a PostgreSQL superuser named `wps`
with password `wps`. Do not run it on production or shared database servers.
Existing database contents are retained, but the `wps` role/password is reset.

## 1. Prepare Ubuntu and get the repository

Systemd must be running. On WSL, if it is disabled, follow
[Microsoft's systemd instructions](https://learn.microsoft.com/en-us/windows/wsl/systemd)
before continuing.

WSL distributions can contend for the same localhost ports. Keep Redis and
PostgreSQL in other distributions stopped during installation and development:
setup expects **5432** for PostgreSQL and **6379** for Redis. The API and frontend
also use **8080** and **3000**.

To stop another distribution, first save its work, then use Windows PowerShell:

```powershell
wsl --list --running
wsl --terminate <original-distro-name>
```

This stops all processes in that distribution, including any VS Code remote
workspace. Do not terminate the Ubuntu distribution you are setting up.

In Ubuntu, refresh the package indexes and bring installed packages up to date
before setup:

```bash
sudo apt-get update
sudo apt-get upgrade
```

Review the proposed upgrades before confirming. This updates the whole
distribution, not just WPS dependencies, and may restart services or require a
reboot. Save running work first and complete any requested reboot before continuing.
The setup script deliberately does not perform a system-wide upgrade itself.

Install Git if needed (safe to rerun when it is already installed),
then clone WPS:

```bash
sudo apt-get install -y git
git clone https://github.com/bcgov/wps.git ~/wps
cd ~/wps
```

## 2. Run automated setup

From the repository root:

```bash
bash setup/ubuntu.sh
```

Setup displays colored section banners instead of installer output. Full output
is saved to a private timestamped log (the exact path is printed at startup and completion).
Failures show the last 40 log lines. The first GDAL compilation can take a while.

Setup performs:

- Apt package-index updates and Universe enablement, then installation of build
  tools, Python development headers, Java, GitHub CLI, ecCodes, PostgreSQL 18,
  PostGIS, and Redis. GDAL's development package supplies compatible CURL headers
  without forcing a switch between GnuTLS and OpenSSL development packages.
- GDAL installation from a checksum-verified source archive into `/usr/local`.
  Ubuntu's GDAL 3.12.2 is older than the project's pinned 3.13.3. Existing matching
  GDAL installations skip compilation. Two compiler jobs limit memory use.
- Best-effort installation of wkhtmltopdf from the upstream Jammy package on
  amd64/arm64. Only HFI Calculator PDF generation needs it. A warning means that
  feature is unavailable, not that the rest of setup failed.
- uv installation and shell-profile configuration, plus automatic
  `uv sync --all-extras` in the backend. The GDAL binding is rebuilt without cache
  and with `/usr/local/lib` first in linker search order. Setup checks its Python
  import and version.
- PostgreSQL/Redis startup and creation of the `wps` database, PostGIS extension,
  and `wps`/`wpsread` roles.
- nvm installation, Node selection from the repository's `.nvmrc`, and setting
  that version as nvm's default. Corepack/Yarn versions come from
  [web/package.json](../web/package.json). Setup runs `yarn install` in `web/`.
- Persistence of `JAVA_HOME` in `~/.bashrc`.

Failures other than the optional PDF installation stop setup. Correct the reported
error and rerun the script. No manual `uv sync` or `yarn install` is needed.
Re-running may update uv and rebuild its Python GDAL binding.

### Refresh the current command-line session

After setup finishes:

```bash
exec bash -l
```

This replaces the current shell with a Bash login shell, loading uv, nvm/Node,
Yarn, and `JAVA_HOME`. Save or finish running work first: shell-local settings are
lost and background jobs may be disrupted. It does not open a new window, and
must be run in your terminal after the script exits.

**Stopping point:** if you only wanted a local checkout and installed tools to
contribute to GitHub, setup is complete. Everything below is for running the
application locally in developer testing mode. Testing changes that depend on
application services may still require these additional steps.

## Developer testing mode

Application environment settings, secrets, and development data are not supplied
by setup. Arrange these with an internal developer before continuing.
Without them, startup or individual features may fail.

## 3. Run database migrations

After configuring the backend environment:

```bash
cd ~/wps/backend/packages/wps-api
uv run --package wps-api alembic upgrade head
```

Migrations change database schema and are deliberately not run by setup.

## 4. Start the backend and frontend

In one Ubuntu terminal:

```bash
cd ~/wps/backend/packages/wps-api
uv run --package wps-api python -m app.main
```

In a second Bash terminal in the **same Ubuntu distribution**:

```bash
cd ~/wps/web
yarn turbo dev
```

Open [http://localhost:3000](http://localhost:3000).
Keep both commands running. Use Ctrl+C to stop each. Login and data-dependent
screens may still require the settings and data described above.
See the [backend](../backend/README.md) and [web](../web/README.md) docs for test,
build, and development commands.

## Troubleshooting and verification

- **Setup fails:** review the error and log path printed by the script. Share the
  relevant log lines with a developer after checking them for sensitive information.
  Correct the reported issue and rerun setup.
- **uv/Node/Yarn not found after setup:** run `exec bash -l` in the same distro.
  If still missing, report the setup output and shell-profile configuration.
  Do not replace PATH with a string that omits Ubuntu's system directories.
