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
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create a directory for the app to run in, and grant worker access
RUN mkdir /app
RUN chown "$USERNAME" /app
WORKDIR /app

# Switch back to our non-root user
USER $USERNAME

WORKDIR /app

# Copy workspace configuration and package manifests
COPY --chown=$USERNAME:$USER_GID ./pyproject.toml /app/
COPY --chown=$USERNAME:$USER_GID ./api/pyproject.toml /app/api/
COPY --chown=$USERNAME:$USER_GID ./wps_shared/pyproject.toml /app/wps_shared/
COPY --chown=$USERNAME:$USER_GID ./wps_shared/wps_shared /app/wps_shared/wps_shared

# Install dependencies using uv
RUN uv sync --frozen --no-dev --package wps-api

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
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create a directory for the app to run in, and grant worker access
RUN mkdir /app
RUN chown "$USERNAME" /app
WORKDIR /app

# Copy workspace and package configuration
COPY --from=builder --chown=$USERNAME:$USER_GID /app/pyproject.toml /app/
COPY --from=builder --chown=$USERNAME:$USER_GID /app/api/pyproject.toml /app/api/

# Switch back to our non-root user
USER $USERNAME

# Copy the app:
COPY ./api/app /app/app
# TODO: we need to do this better.
RUN mkdir /app/advisory
COPY ./api/advisory /app/advisory
# Copy java libs:
RUN mkdir /app/libs
COPY ./api/libs /app/libs
# Copy alembic:
COPY ./api/alembic /app/alembic
COPY ./api/alembic.ini /app
# Copy pre-start.sh (it will be run on startup):
COPY ./api/prestart.sh /app
COPY ./api/start.sh /app

# Make uv happy by copying wps_shared
COPY ./wps_shared /app/wps_shared

# Copy installed Python packages (the chown lets us install the dev packages later without root if we want)
COPY --from=builder --chown=$USERNAME:$USER_GID /app/.venv /app/.venv

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
# We don't know what user uv is going to run as, so we give everyone write access directories
# in the app folder. We need write access for .pyc files to be created. .pyc files are good,
# they speed up python.
RUN chmod a+w $(find /app/app -type d)

# Openshift runs with a random non-root user, so switching our user to 1001 allows us
# to test locally with similar conditions to what we may find in openshift.
USER 1001

CMD ["./start.sh"]
