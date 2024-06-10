ARG DOCKER_IMAGE=image-registry.openshift-image-registry.svc:5000/e1e498-tools/wps-api-base:ubuntu.22.04-latest

# To build locally, point to a local base image you've already built (see openshift/wps-api-base)
# e.g. : docker build --build-arg DOCKER_IMAGE=wps-api-base:my-tag .

# Stage 1: Install Python packages, including internally published cffdrs. Installation from artifactory
# requires a username/password which we don't want in our final image, so we use a multi-stage build. 
FROM ${DOCKER_IMAGE} AS builder

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Switch to root
USER 0

# Create a directory for the app to run in, and grant worker access
RUN mkdir /app
RUN chown "$USERNAME" /app
WORKDIR /app

# Switch back to our non-root user
USER $USERNAME

WORKDIR /app

# Make sure we have the latest pip.
RUN python -m pip install --upgrade pip
# Copy poetry files.
COPY --chown=$USERNAME:$USERNAME ./api/pyproject.toml ./api/poetry.lock /app/

ARG ARTIFACTORY_PYPI_USERNAME
ARG ARTIFACTORY_PYPI_PASSWORD

RUN poetry config http-basic.psu "$ARTIFACTORY_PYPI_USERNAME" "$ARTIFACTORY_PYPI_PASSWORD"

# Install dependencies.
RUN poetry install --without dev
# Get a python binding for gdal that matches the version of gdal we have installed.
RUN poetry run python -m pip install gdal==$(gdal-config --version)

# Stage 2: Preapre the final image, inclusing copying Python packages from Stage 1.
FROM ${DOCKER_IMAGE}

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Switch to root
USER 0

# Create a directory for the app to run in, and grant worker access
RUN mkdir /app
RUN chown "$USERNAME" /app
WORKDIR /app

# Copy poetry files.
COPY --from=builder --chown=$USERNAME:$USERNAME /app/pyproject.toml /app/poetry.lock /app/

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
COPY ./api/start_sfms.sh /app

# Copy installed Python packages
COPY --from=builder /home/worker/.cache/pypoetry/virtualenvs /home/worker/.cache/pypoetry/virtualenvs

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080

# Set the classpath to include copied libs
ENV CLASSPATH=/app/libs/REDapp_Lib.jar:/app/libs/WTime.jar:/app/libs/hss-java.jar:${CLASSPATH}
# Tell poetry where to find the cache
ENV POETRY_CACHE_DIR="/home/${USERNAME}/.cache/pypoetry"
# Put poetry on the path
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# root user please
USER 0
# We don't know what user poetry is going to run as, so we give everyone write access directories
# in the app folder. We need write access for .pyc files to be created. .pyc files are good,
# they speed up python.
RUN chmod a+w $(find /app/app -type d)

# Openshift runs with a random non-root user, so switching our user to 1001 allows us
# to test locally with similar conditions to what we may find in openshift.
USER 1001

CMD ["./start.sh"]