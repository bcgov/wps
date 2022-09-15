ARG DOCKER_IMAGE=image-registry.openshift-image-registry.svc:5000/e1e498-tools/wps-api-base:ubuntu.22.04-latest

# To build locally, point to a local base image you've already built (see openshift/wps-api-base)
# e.g. : docker build --build-arg DOCKER_IMAGE=wps-api-base:my-tag .

FROM ${DOCKER_IMAGE}

# We don't want to run our app as root, we we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Switch to root
USER 0

# Create a directory for the app to run in, and grant worker access
RUN mkdir /app
RUN chown $USERNAME /app
WORKDIR /app

# Switch back to our non-root user
USER $USERNAME

# Make sure we have the latest pip.
RUN python -m pip install --upgrade pip
# Copy poetry files.
COPY --chown=$USERNAME:$USERNAME ./api/pyproject.toml ./api/poetry.lock /app/
# Install dependencies.
RUN poetry install --without dev
# Get a python binding for gdal that matches the version of gdal we have installed.
RUN poetry run python -m pip install gdal==$(gdal-config --version)

# Copy the app:
COPY ./api/app /app/app
# Copy java libs:
RUN mkdir /app/libs
COPY ./api/libs /app/libs
# Copy almebic:
COPY ./api/alembic /app/alembic
COPY ./api/alembic.ini /app
# Copy pre-start.sh (it will be run on startup):
COPY ./api/prestart.sh /app
COPY ./api/start.sh /app

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080

# Set the classpath to include copied libs
ENV CLASSPATH=/app/libs/REDapp_Lib.jar:/app/libs/WTime.jar:/app/libs/hss-java.jar:${CLASSPATH}
# Tell poetry where to find the cache
# TODO: change "worker" to somehow use $USERNAME
ENV POETRY_CACHE_DIR="/home/worker/.cache/pypoetry"
# Put poetry on the path
ENV PATH="/home/worker/.local/bin:${PATH}"

CMD ["./start.sh"]