ARG DOCKER_IMAGE=ghcr.io/osgeo/gdal:ubuntu-small-3.9.2

# Builder stage
# ────────────────────────────────────────────────────────────────
FROM ${DOCKER_IMAGE} AS builder

ARG USERNAME=worker
ARG USER_UID=1010

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Minimal deps
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*


# uv binary for builder
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /uvx /bin/

RUN useradd --uid "${USER_UID}" --create-home "${USERNAME}" \
    && chmod a+rx /home/"${USERNAME}"

RUN mkdir -p /app/packages/wps-shared \
    /app/packages/wps-wf1 \
    /app/packages/wps-weather \
    && chown -R ${USERNAME}:${USERNAME} /app

WORKDIR /app
USER ${USERNAME}


# Copy workspace files (cache layer)
COPY ./backend/pyproject.toml ./backend/uv.lock ./
COPY ./backend/packages/wps-shared/pyproject.toml ./packages/wps-shared/
COPY ./backend/packages/wps-shared/src /app/packages/wps-shared/src
COPY ./backend/packages/wps-wf1/pyproject.toml   ./packages/wps-wf1/
COPY ./backend/packages/wps-wf1/src /app/packages/wps-wf1/src
COPY ./backend/packages/wps-weather/pyproject.toml ./packages/wps-weather/
COPY ./backend/packages/wps-weather/src /app/packages/wps-weather/src

# Switch to root to set file permissions
USER 0

# Set configuration files to read-only for security
RUN chmod 444 ./pyproject.toml ./uv.lock \
    ./packages/wps-shared/pyproject.toml \
    ./packages/wps-wf1/pyproject.toml \
    ./packages/wps-weather/pyproject.toml && \
    chmod -R a-w ./packages/wps-shared/src ./packages/wps-weather/src ./packages/wps-wf1/src

# Switch back to non-root user
USER $USERNAME

# Install locked deps + workspace packages
RUN uv sync --frozen --no-dev --package wps-weather


# Runtime stage
# ────────────────────────────────────────────────────────────────
FROM ${DOCKER_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Use root during image build
USER 0

# Copy uv binary into runtime (enables uv at runtime)
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /uvx /bin/

# Create application directory and make it OpenShift-compatible
RUN mkdir /app && chown "$USERNAME" /app

WORKDIR /app

# Copy prepared virtual environment
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/packages/wps-shared/pyproject.toml ./packages/wps-shared/
COPY --from=builder /app/packages/wps-wf1/pyproject.toml ./packages/wps-wf1/
COPY --from=builder /app/packages/wps-weather/pyproject.toml ./packages/wps-weather/

# Copy source code
COPY ./backend/packages/wps-shared/src ./packages/wps-shared/src
COPY ./backend/packages/wps-wf1/src    ./packages/wps-wf1/src
COPY ./backend/packages/wps-weather/src ./packages/wps-weather/src

# Optional metadata
COPY ./backend/pyproject.toml ./backend/uv.lock ./

# Hardening: make configs and source read-only
RUN chmod -R a-w pyproject.toml uv.lock packages 2>/dev/null || true \
    && find packages -type d -exec chmod a+rX {} + 2>/dev/null || true

# OpenShift simulation: random non-root UID
USER 1001
