ARG DOCKER_IMAGE=ghcr.io/bcgov/wps/wps-api-base:10-20-2026
# To build locally, point to a local base image you've already built (see openshift/wps-api-base)
# e.g. : docker build --build-arg DOCKER_IMAGE=wps-api-base:my-tag .

# Each instruction costs a layer commit (1-3s on OpenShift, which has no layer cache between
# builds), so related COPYs are grouped and permissions are set once in the final stage.

# Stage 1: Install Python packages
FROM ${DOCKER_IMAGE} AS builder

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1010
ARG USER_GID=1000

# Switch to root
USER 0

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /uvx /bin/

# Create a directory for the app to run in, and grant worker access
RUN mkdir /app && chown "$USERNAME" /app
WORKDIR /app

# Switch back to our non-root user
USER $USERNAME

# Copy workspace configuration and the workspace packages wps-api depends on
COPY ./backend/pyproject.toml ./backend/uv.lock ./backend/.python-version /app/
COPY ./backend/packages/wps-api/pyproject.toml /app/packages/wps-api/
COPY ./backend/packages/cffdrs-vec /app/packages/cffdrs-vec
COPY ./backend/packages/wps-shared /app/packages/wps-shared
COPY ./backend/packages/wps-sfms /app/packages/wps-sfms
COPY ./backend/packages/wps-wf1 /app/packages/wps-wf1

# Fail the build if the base image's python3 doesn't match .python-version, instead of downloading one
ENV UV_PYTHON_DOWNLOADS=never

# The base image already ships GDAL Python bindings (osgeo) built for its python3 and libgdal,
# so the venv sees system site-packages and skips the gdal sdist instead of compiling it.
# Venv packages (e.g. numpy from uv.lock) still take precedence over the system copies.
RUN uv venv --system-site-packages && \
    uv sync --frozen --no-dev --package wps-api --no-install-package gdal

# Stage 2: Prepare the final image, including copying Python packages from Stage 1.
FROM ${DOCKER_IMAGE}

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1010
ARG USER_GID=1000

# Switch to root
USER 0

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /uvx /bin/

# Create a directory for the app to run in, and grant worker access
RUN mkdir /app && chown "$USERNAME" /app
WORKDIR /app

# Copy the venv along with the workspace configuration and package source it is installed from
# (workspace packages are editable installs pointing at /app/packages/*/src)
COPY --from=builder /app /app

# Copy the app, advisory templates, java libs, alembic and startup scripts
COPY ./backend/packages/wps-api/src/app /app/app
COPY ./backend/packages/wps-api/advisory /app/advisory
COPY ./backend/packages/wps-api/libs /app/libs
COPY ./backend/packages/wps-api/alembic /app/alembic
COPY ./backend/packages/wps-api/alembic.ini ./backend/packages/wps-api/prestart.sh ./backend/packages/wps-api/start.sh /app/

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080

# Set the classpath to include copied libs
ENV CLASSPATH=/app/libs/REDapp_Lib.jar:/app/libs/WTime.jar:/app/libs/hss-java.jar:${CLASSPATH}
# Add .venv to PATH
ENV PATH="/app/.venv/bin:${PATH}"
# Set virtual env location
ENV VIRTUAL_ENV="/app/.venv"

# Remove write permissions from copied configuration and source files for security,
# but allow write access to app directories for .pyc file creation
RUN chmod -R a-w \
    /app/pyproject.toml \
    /app/uv.lock \
    /app/.python-version \
    /app/packages \
    /app/advisory \
    /app/libs \
    /app/alembic \
    /app/alembic.ini \
    /app/prestart.sh \
    /app/start.sh && \
    chmod a+w $(find /app/app -type d)

# Openshift runs with a random non-root user, so switching our user to 1001 allows us
# to test locally with similar conditions to what we may find in openshift.
USER 1001

CMD ["./start.sh"]
