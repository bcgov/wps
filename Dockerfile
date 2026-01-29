ARG DOCKER_IMAGE=ghcr.io/bcgov/wps/wps-api-base:29-01-2026
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
RUN mkdir /app && chown "$USERNAME" /app
WORKDIR /app

# Switch back to our non-root user
USER $USERNAME

WORKDIR /app

# Copy workspace configuration and package manifests
COPY ./backend/pyproject.toml /app/
COPY ./backend/uv.lock /app/
COPY ./backend/packages/wps-api/pyproject.toml /app/packages/wps-api/
COPY ./backend/packages/wps-shared/pyproject.toml /app/packages/wps-shared/
COPY ./backend/packages/wps-shared/src /app/packages/wps-shared/src
COPY ./backend/packages/wps-sfms/pyproject.toml /app/packages/wps-sfms/
COPY ./backend/packages/wps-sfms/src /app/packages/wps-sfms/src
COPY ./backend/packages/wps-wf1/pyproject.toml /app/packages/wps-wf1/
COPY ./backend/packages/wps-wf1/src /app/packages/wps-wf1/src

# Switch to root to set file permissions
USER 0

# Set configuration files to read-only for security
RUN chmod 444 /app/pyproject.toml /app/uv.lock \
    /app/packages/wps-api/pyproject.toml \
    /app/packages/wps-shared/pyproject.toml \
    /app/packages/wps-wf1/pyproject.toml \
    /app/packages/wps-sfms/pyproject.toml && \
    chmod -R a-w /app/packages/wps-shared/src /app/packages/wps-sfms/src /app/packages/wps-wf1/src

# Switch back to non-root user
USER $USERNAME

# Install dependencies using uv, including setuptools for GDAL build and GDAL itself
RUN uv sync --frozen --no-dev --package wps-api && \
    uv pip install setuptools && \
    uv pip install --no-build-isolation --no-cache-dir --force-reinstall gdal==$(gdal-config --version)

# Stage 2: Prepare the final image, including copying Python packages from Stage 1.
FROM ${DOCKER_IMAGE}

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1010
ARG USER_GID=1000

RUN apt-get install libgdal-hdf5

# Switch to root
USER 0

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.11 /uv /uvx /bin/

# Create a directory for the app to run in, and grant worker access
RUN mkdir /app && chown "$USERNAME" /app
WORKDIR /app

# Copy workspace and package configuration
COPY --from=builder /app/pyproject.toml /app/
COPY --from=builder /app/packages/wps-api/pyproject.toml /app/packages/wps-api/
COPY --from=builder /app/packages/wps-shared/pyproject.toml /app/packages/wps-shared/
COPY --from=builder /app/packages/wps-sfms/pyproject.toml /app/packages/wps-sfms/
COPY --from=builder /app/packages/wps-wf1/pyproject.toml /app/packages/wps-wf1/

# Switch back to our non-root user
USER $USERNAME

# Copy the app from new src layout:
COPY ./backend/packages/wps-api/src/app /app/app
# TODO: we need to do this better.
# Create directories for advisory and java libs
RUN mkdir /app/advisory /app/libs
COPY ./backend/packages/wps-api/advisory /app/advisory
COPY ./backend/packages/wps-api/libs /app/libs
# Copy alembic:
COPY ./backend/packages/wps-api/alembic /app/alembic
COPY ./backend/packages/wps-api/alembic.ini /app
# Copy pre-start.sh (it will be run on startup):
COPY ./backend/packages/wps-api/prestart.sh /app
COPY ./backend/packages/wps-api/start.sh /app

# Make uv happy by copying wps_shared and wps_sfms
COPY ./backend/packages/wps-shared/src /app/packages/wps-shared/src
COPY ./backend/packages/wps-sfms/src /app/packages/wps-sfms/src
COPY ./backend/packages/wps-wf1/src /app/packages/wps-wf1/src

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
# Remove write permissions from copied configuration and source files for security,
# but allow write access to app directories for .pyc file creation
RUN chmod -R a-w \
    /app/pyproject.toml \
    /app/packages/wps-api/pyproject.toml \
    /app/packages/wps-shared/src \
    /app/packages/wps-sfms/src \
    /app/packages/wps-wf1/src \
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
