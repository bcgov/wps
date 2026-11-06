#!/usr/bin/env bash

## Installs backend and web dependencies on Ubuntu 26.04 LTS (WSL 2 or native Linux).
## Safe to re-run on a development machine; existing database contents are retained.

# Stop on failed commands, unset variables, or failed pipelines rather than report partial setup as success.
set -euo pipefail
trap 'echo "ERROR: Ubuntu setup failed at line $LINENO." >&2' ERR

# User-level installers and profiles must belong to the developer, not root.
if (( EUID == 0 )); then
  echo "ERROR: Run this script as your normal user, not root; it will request sudo when needed." >&2
  exit 1
fi

if [[ ! -r /etc/os-release ]]; then
  echo "ERROR: This script requires Ubuntu 26.04 LTS." >&2
  exit 1
fi

# shellcheck source=/dev/null
source /etc/os-release

# Package names and the expected PostgreSQL version below are specific to this Ubuntu release.
if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "26.04" ]]; then
  echo "ERROR: This script requires Ubuntu 26.04 LTS." >&2
  exit 1
fi

if [[ ! -d /run/systemd/system ]]; then
  echo "ERROR: systemd must be running to start PostgreSQL and Redis (including on WSL)." >&2
  exit 1
fi

# Resolve paths from the script so dependency installs work regardless of the caller's directory.
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Local development only: this creates the wps database and sets the wps superuser password to 'wps'."
sudo -v

# Preserve the terminal descriptors while installer stdout/stderr go to a private, persistent log.
exec 3>&1 4>&2
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/wps"
mkdir -p "$LOG_DIR"
LOG_FILE="$(mktemp "$LOG_DIR/ubuntu-setup-$(date +%Y%m%d-%H%M%S)-XXXXXX.log")"

CYAN="" GREEN="" YELLOW="" RED="" RESET=""
if [[ -t 3 && "${TERM:-dumb}" != dumb && -z "${NO_COLOR:-}" ]]; then
  CYAN=$'\033[1;36m' GREEN=$'\033[1;32m' YELLOW=$'\033[1;33m'
  RED=$'\033[1;31m' RESET=$'\033[0m'
fi

STAGE_NUMBER=0
STAGE_STARTED=0
PROGRESS_PID=""
PROGRESS_FILE="$LOG_FILE.progress"

stop_progress() {
  if [[ -n "$PROGRESS_PID" ]]; then
    rm -f "$PROGRESS_FILE"
    wait "$PROGRESS_PID"
    PROGRESS_PID=""
    printf '\r\033[2K' >&3
  fi
}

stage() {
  stop_progress
  if (( STAGE_NUMBER > 0 )); then
    printf '%s[DONE] Stage %s/7 (%ss)%s\n' \
      "$GREEN" "$STAGE_NUMBER" "$((SECONDS - STAGE_STARTED))" "$RESET" >&3
  fi
  STAGE_NUMBER=$((STAGE_NUMBER + 1))
  STAGE_STARTED=$SECONDS
  printf '\n%s============================================================\n  %s\n============================================================%s\n' \
    "$CYAN" "$1" "$RESET" >&3
  printf '\n=== %s ===\n' "$1"

  # Live updates require a terminal; redirected output keeps stable stage summaries.
  if [[ -t 3 && "${TERM:-dumb}" != dumb ]]; then
    : > "$PROGRESS_FILE"
    (
      trap - EXIT ERR
      frames='|/-\'
      frame=0
      build_progress=""
      while [[ -f "$PROGRESS_FILE" ]]; do
        if (( STAGE_NUMBER == 2 )); then
          reported="$(tail -n 20 "$LOG_FILE" | awk '
            /^\[[0-9]+\/[0-9]+\]/ {
              value=$1
              gsub(/[\[\]]/, "", value)
              split(value, counts, "/")
              if (counts[2] > 0) percent=int(100 * counts[1] / counts[2])
            }
            END { if (percent != "") print percent }
          ')"
          if [[ -n "$reported" ]]; then
            build_progress=" | GDAL build: $reported%"
          fi
        fi
        printf '\r\033[2K%s[%s] Working | Elapsed: %ss%s%s' \
          "$CYAN" "${frames:frame:1}" "$((SECONDS - STAGE_STARTED))" \
          "$build_progress" "$RESET" >&3
        frame=$(((frame + 1) % 4))
        sleep 1
      done
    ) &
    PROGRESS_PID=$!
  fi
}

warning() {
  printf 'WARNING: %s\n' "$1" >&2
  printf '%sWARNING: %s%s\n' "$YELLOW" "$1" "$RESET" >&4
}

# Authentication happens before logging starts; never allow a later hidden password prompt.
sudo() {
  if ! command sudo -n -v; then
    printf '\n%sSudo authentication is unavailable or expired. Rerun setup to authenticate at the visible initial prompt.%s\n' \
      "$RED" "$RESET" >&4
    return 1
  fi
  command sudo -n "$@"
}

finish() {
  local status=$?
  stop_progress
  if (( status != 0 )); then
    printf '\n%sSETUP FAILED (exit %s). Last log lines:%s\n' "$RED" "$status" "$RESET" >&4
    tail -n 40 "$LOG_FILE" >&4
    printf '\nFull log: %s\n' "$LOG_FILE" >&4
  fi
  if [[ -n "${WORK_DIR:-}" ]]; then
    rm -rf -- "$WORK_DIR"
  fi
  exit "$status"
}

printf '%s\n  WPS / UBUNTU DEVELOPMENT SETUP\n%s\nFull log: %s\n' \
  '============================================================' \
  '============================================================' "$LOG_FILE" >&3
exec >>"$LOG_FILE" 2>&1
trap finish EXIT

### apt prerequisites (several dependencies are in Universe)

stage "[1/7] Installing system packages"

# Refresh package indexes, including the newly enabled repository; avoid a system-wide upgrade.
sudo apt-get update
sudo apt-get install -y --no-remove software-properties-common
sudo add-apt-repository -y universe
sudo apt-get update
# libgdal-dev supplies compatible CURL headers; do not force a conflicting TLS variant.
sudo apt-get install -y --no-remove \
  build-essential ca-certificates cmake curl default-jdk gh git \
  libgdal-dev libgeos-dev libproj-dev libsqlite3-dev \
  libeccodes-dev libeccodes-tools libpq-dev libudunits2-dev \
  ninja-build postgresql postgresql-postgis python3-dev redis-server

export JAVA_HOME="/usr/lib/jvm/default-java"

# Prefer our user-installed uv and source-built GDAL over Ubuntu's older GDAL tools.
export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"

# Script exports do not reach future terminals; persist Java without duplicating the same line.
JAVA_HOME_LINE="export JAVA_HOME=\"$JAVA_HOME\""
if [[ ! -f "$HOME/.bashrc" ]] || ! grep -Fxq "$JAVA_HOME_LINE" "$HOME/.bashrc"; then
  printf '\n%s\n' "$JAVA_HOME_LINE" >> "$HOME/.bashrc"
fi

# Keep downloads/build artifacts isolated and remove them on either success or failure.
WORK_DIR="$(mktemp -d -t wps-setup.XXXXXXXXXX)"

### gdal

stage "[2/7] Preparing GDAL (first build may take a while)"

# Keep this version and checksum in step with the pyproject pins and API base image.
GDAL_VERSION="3.13.3"
GDAL_SHA256="5e0c388d83da2d686cc00a40272882432cdb54edff43d4af173e532844a0a0ea"

# Ubuntu's libgdal-dev supplies build dependencies, but its GDAL is older than our pin.
# Install into /usr/local without overwriting apt-managed files in /usr.
if ! command -v gdal-config >/dev/null 2>&1 || [[ "$(gdal-config --version)" != "$GDAL_VERSION" ]]; then
  echo "Building GDAL $GDAL_VERSION from source; this may take a while."
  curl --proto '=https' --proto-redir '=https' --tlsv1.2 -fsSL "https://github.com/OSGeo/gdal/releases/download/v$GDAL_VERSION/gdal-$GDAL_VERSION.tar.gz" \
    -o "$WORK_DIR/gdal.tar.gz"

  # Reject an unexpected archive before extracting or compiling it.
  printf '%s  %s\n' "$GDAL_SHA256" "$WORK_DIR/gdal.tar.gz" | sha256sum --check
  tar -xzf "$WORK_DIR/gdal.tar.gz" -C "$WORK_DIR"

  # uv builds Python bindings later; enable network access, geometry operations, and GeoPackage support here.
  cmake -S "$WORK_DIR/gdal-$GDAL_VERSION" -B "$WORK_DIR/build" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_INSTALL_LIBDIR=lib \
    -DBUILD_PYTHON_BINDINGS=OFF -DBUILD_JAVA_BINDINGS=OFF -DBUILD_CSHARP_BINDINGS=OFF \
    -DBUILD_TESTING=OFF -DGDAL_USE_CURL=ON -DGDAL_USE_GEOS=ON -DGDAL_USE_SQLITE3=ON

  # Limit compiler processes to avoid exhausting a typical WSL VM's memory.
  NINJA_STATUS='[%f/%t] ' cmake --build "$WORK_DIR/build" --parallel 2
  sudo cmake --install "$WORK_DIR/build"
else
  echo "GDAL $GDAL_VERSION already installed; skipping the build."
fi

# Make the new shared library discoverable at runtime, not just by the compiler.
sudo ldconfig

if [[ "$(gdal-config --version)" != "$GDAL_VERSION" ]]; then
  echo "ERROR: gdal-config does not resolve to GDAL $GDAL_VERSION; check your PATH." >&2
  exit 1
fi
gdalinfo --version

### wkhtmltopdf (optional; for HFI Calculator PDFs)

stage "[3/7] Installing optional PDF renderer"

# shortcut: upstream only provides older Jammy packages, replace when a maintained renderer is adopted.
# A renderer failure must not block developers who do not need PDF generation.
if command -v wkhtmltopdf >/dev/null 2>&1; then
  echo "wkhtmltopdf already installed; skipping."
else
  ARCH="$(dpkg --print-architecture)"
  case "$ARCH" in
    amd64|arm64)
      WKHTMLTOPDF_PKG_URL="https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_$ARCH.deb"
      if curl --proto '=https' --proto-redir '=https' --tlsv1.2 -fsSL "$WKHTMLTOPDF_PKG_URL" -o "$WORK_DIR/wkhtmltox.deb" \
        && sudo apt-get install -y --no-remove "$WORK_DIR/wkhtmltox.deb" \
        && wkhtmltopdf --version; then
        echo "wkhtmltopdf installed."
      else
        warning "wkhtmltopdf install failed; HFI PDF generation is unavailable. Continuing."
      fi
      ;;
    *)
      warning "No wkhtmltopdf package configured for $ARCH; HFI PDF generation is unavailable."
      ;;
  esac
fi

### uv (Python comes from backend/.python-version on the first uv sync)

stage "[4/7] Installing uv and configuring its shell profile"

# Re-run the installer to configure PATH even after an earlier profile-free install.
curl --proto '=https' --proto-redir '=https' --tlsv1.2 -fsSL https://astral.sh/uv/install.sh -o "$WORK_DIR/uv-install.sh"

# The installer skips profiles when its install directory is already on PATH.
env -u UV_NO_MODIFY_PATH -u INSTALLER_NO_MODIFY_PATH -u UV_UNMANAGED_INSTALL \
  PATH="/usr/bin:/bin" UV_INSTALL_DIR="$HOME/.local/bin" sh "$WORK_DIR/uv-install.sh"
uv --version

### postgres + postgis + redis

stage "[5/7] Starting PostgreSQL and Redis; provisioning local database"

# Enable services for future boots and start them now; cluster startup can lag behind systemctl.
sudo systemctl enable --now postgresql redis-server

for _ in {1..15}; do
  if pg_isready -q -h /var/run/postgresql -p 5432 -U postgres; then break; fi
  sleep 1
done

if ! pg_isready -q -h /var/run/postgresql -p 5432 -U postgres; then
  echo "ERROR: PostgreSQL did not become ready on local port 5432; check pg_lsclusters." >&2
  exit 1
fi

# Use Ubuntu's postgres OS account and a fixed local socket, not inherited PGHOST/PGPORT.
# Ignore personal psql startup files and abort on SQL errors so provisioning failures are visible.
PSQL=(sudo -u postgres psql -X -v ON_ERROR_STOP=1 -h /var/run/postgresql -p 5432 -U postgres)
PG_VERSION="$("${PSQL[@]}" -d postgres -Atc "SHOW server_version_num")"
if [[ "$PG_VERSION" != 18* ]]; then
  echo "ERROR: Expected PostgreSQL 18 on local port 5432; check pg_lsclusters before re-running." >&2
  exit 1
fi

# \gexec runs CREATE only when the existence query returns a row, preserving existing data on re-runs.
"${PSQL[@]}" -d postgres <<'SQL'
SELECT 'CREATE DATABASE wps'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'wps') \gexec
SQL

# PostGIS supplies spatial types; these roles mirror local macOS setup, not production access controls.
# Re-runs reset the development superuser password; wpsread receives access to tables that already exist.
"${PSQL[@]}" -d wps <<'SQL'
CREATE EXTENSION IF NOT EXISTS postgis;
SELECT 'CREATE USER wps'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'wps') \gexec
SELECT 'CREATE USER wpsread'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'wpsread') \gexec
ALTER USER wps WITH LOGIN SUPERUSER PASSWORD 'wps';
ALTER USER wpsread WITH LOGIN;
GRANT CONNECT ON DATABASE wps TO wpsread;
GRANT USAGE ON SCHEMA public TO wpsread;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO wpsread;
SQL

# Check the endpoint the application uses rather than relying only on the service's enabled state.
if [[ "$(redis-cli -h 127.0.0.1 -p 6379 ping)" != "PONG" ]]; then
  echo "ERROR: Redis did not respond with PONG on localhost:6379." >&2
  exit 1
fi

stage "[6/7] Installing backend dependencies and verifying Python GDAL"
(
  cd "$REPO_ROOT/backend"

  # Prefer the new native GDAL and rebuild cached bindings that may link to Ubuntu's older library.
  LDFLAGS="-L/usr/local/lib ${LDFLAGS:-}" uv sync --all-extras --no-cache --reinstall-package gdal

  # A successful wheel build alone does not prove the runtime loader finds the correct GDAL.
  uv run python -c 'from osgeo import gdal; from importlib.metadata import version; assert gdal.__version__ == version("gdal"); print("Python GDAL", gdal.__version__)'
)

### node + yarn + web dependencies

stage "[7/7] Installing Node, Yarn, and web dependencies"
export NVM_DIR="$HOME/.nvm"
if [[ ! -s "$NVM_DIR/nvm.sh" ]]; then
  curl --proto '=https' --proto-redir '=https' --tlsv1.2 -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.41.0/install.sh \
    -o "$WORK_DIR/nvm-install.sh"
  bash "$WORK_DIR/nvm-install.sh"
fi

# shellcheck source=/dev/null
# Defer automatic version selection until nvm install can supply the repository's requested Node.
source "$NVM_DIR/nvm.sh" --no-use
(
  cd "$REPO_ROOT"
  nvm install
  nvm use

  # New shells must select the project's Node even if nvm already had another default.
  nvm alias default "$(cat .nvmrc)"

  cd web

  # Match CI's pinned Corepack; it selects Yarn from web/package.json instead of a global Yarn version.
  npm install --global --ignore-scripts \
    "corepack@$(node -p 'require("./package.json").devDependencies.corepack')"
  corepack enable

  echo "Installing web dependencies; see setup/ubuntu.md if registry authentication fails."
  # Setup already requests pinned Yarn; prevent a hidden download prompt or other interactive waits.
  COREPACK_ENABLE_DOWNLOAD_PROMPT=0 yarn install </dev/null
)

stop_progress
printf '%s[DONE] Stage 7/7 (%ss)%s\n' \
  "$GREEN" "$((SECONDS - STAGE_STARTED))" "$RESET" >&3
printf '\n%s[OK] Local machine, backend, and web dependencies installed.%s\nFull log: %s\n' \
  "$GREEN" "$RESET" "$LOG_FILE" >&3

# Leave shell replacement and migrations to the caller: profiles and database settings need their context.
printf '\n%s============================================================\n  ACTION REQUIRED / TWO COMMANDS TO FINISH SETUP\n============================================================%s\n' \
  "$YELLOW" "$RESET" >&3

printf '%s[1/2] RELOAD YOUR UBUNTU SHELL%s\n\n  %sexec bash -l%s\n' \
  "$CYAN" "$RESET" "$GREEN" "$RESET" >&3
cat >&3 <<EOF

Run this after the script exits. It loads the shell-profile
changes so uv, Node, and Yarn
are available in your terminal. The script cannot update
the shell that launched it.
WARNING: This replaces your current shell with a Bash login
shell, clears session-only shell settings, and may disrupt
background jobs. Finish or save any running work first.

Arrange application environment settings with an internal
developer before running migrations or starting the apps.

EOF
printf '%s[2/2] RUN MIGRATIONS AFTER CONFIGURING YOUR ENVIRONMENT%s\n\n' \
  "$CYAN" "$RESET" >&3
printf '  %s(cd "%s/backend/packages/wps-api" && uv run --package wps-api alembic upgrade head)%s\n' \
  "$GREEN" "$REPO_ROOT" "$RESET" >&3
cat >&3 <<EOF

The wps/wps database superuser credentials are for local development only.
============================================================
EOF
