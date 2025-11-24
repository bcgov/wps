ARG DOCKER_IMAGE=ghcr.io/bcgov/wps/wps-api-base:06-30-2025
# To build locally, point to a local base image you've already built (see openshift/wps-api-base)
# e.g. : docker build --build-arg DOCKER_IMAGE=wps-api-base:my-tag .

# Stage 1: Install Python packages
FROM ${DOCKER_IMAGE} AS builder

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1010
ARG USER_GID=1000

# Switch to root
USER 0

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.11 /uv /uvx /bin/

# Create a directory for the app to run in, and grant worker access
RUN mkdir /app
RUN chown "$USERNAME" /app
WORKDIR /app

# Switch back to our non-root user
USER $USERNAME

WORKDIR /app

# Copy workspace configuration and package manifests
COPY ./backend/pyproject.toml /app/
COPY ./backend/uv.lock /app/
COPY ./backend/packages/wps-api/pyproject.toml /app/packages/wps-api/
COPY ./backend/packages/wps-api/README.md /app/packages/wps-api/
COPY ./backend/packages/wps-shared/pyproject.toml /app/packages/wps-shared/
COPY ./backend/packages/wps-shared/README.md /app/packages/wps-shared/
COPY ./backend/packages/wps-shared/src /app/packages/wps-shared/src

# Switch to root to set file permissions
USER 0

# Set configuration files to read-only for security
RUN chmod 444 /app/pyproject.toml /app/uv.lock \
    /app/packages/wps-api/pyproject.toml /app/packages/wps-api/README.md \
    /app/packages/wps-shared/pyproject.toml /app/packages/wps-shared/README.md
RUN chmod -R a-w /app/packages/wps-shared/src

# Switch back to non-root user
USER $USERNAME

# Install dependencies using uv
RUN uv sync --frozen --no-dev --package wps-api

# Install setuptools required for GDAL build
RUN uv pip install setuptools

# Get a python binding for gdal that matches the version of gdal we have installed.
RUN uv pip install --no-build-isolation --no-cache-dir --force-reinstall gdal==$(gdal-config --version)

# Stage 2: Prepare the final image, including copying Python packages from Stage 1.
FROM ${DOCKER_IMAGE}

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1010
ARG USER_GID=1000

# Switch to root
USER 0

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.11 /uv /uvx /bin/

# Create a directory for the app to run in, and grant worker access
RUN mkdir /app
RUN chown "$USERNAME" /app
WORKDIR /app

# Copy workspace and package configuration
COPY --from=builder /app/pyproject.toml /app/
COPY --from=builder /app/packages/wps-api/pyproject.toml /app/packages/wps-api/
COPY --from=builder /app/packages/wps-api/README.md /app/packages/wps-api/
COPY --from=builder /app/packages/wps-shared/pyproject.toml /app/packages/wps-shared/
COPY --from=builder /app/packages/wps-shared/README.md /app/packages/wps-shared/

# Switch back to our non-root user
USER $USERNAME

# Copy the app from new src layout:
COPY ./backend/packages/wps-api/src/app /app/app
# TODO: we need to do this better.
RUN mkdir /app/advisory
COPY ./backend/packages/wps-api/advisory /app/advisory
# Copy java libs:
RUN mkdir /app/libs
COPY ./backend/packages/wps-api/libs /app/libs
# Copy alembic:
COPY ./backend/packages/wps-api/alembic /app/alembic
COPY ./backend/packages/wps-api/alembic.ini /app
# Copy pre-start.sh (it will be run on startup):
COPY ./backend/packages/wps-api/prestart.sh /app
COPY ./backend/packages/wps-api/start.sh /app

# Make uv happy by copying wps_shared
COPY ./backend/packages/wps-shared/src /app/packages/wps-shared/src

# Copy installed Python packages
COPY --from=builder /app/.venv /app/.venv

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080

# Set the classpath to include copied libs
ENV CLASSPATH=/app/libs/REDapp_Lib.jar:/app/libs/WTime.jar:/app/libs/hss-java.jar:${CLASSPATH}
# Add .venv to PATH
ENV PATH="/app/.venv/bin:${PATH}"
# Set virtual env location
ENV VIRTUAL_ENV="/app/.venv"

# root user please
USER 0
# Remove write permissions from copied configuration and source files for security
RUN chmod -R a-w /app/pyproject.toml /app/packages/wps-api/pyproject.toml /app/advisory /app/libs /app/alembic /app/alembic.ini /app/prestart.sh /app/start.sh /app/packages/wps-shared/src
# We don't know what user uv is going to run as, so we give everyone write access directories
# in the app folder. We need write access for .pyc files to be created. .pyc files are good,
# they speed up python.
RUN chmod a+w $(find /app/app -type d)

# Openshift runs with a random non-root user, so switching our user to 1001 allows us
# to test locally with similar conditions to what we may find in openshift.
USER 1001

CMD ["./start.sh"]
