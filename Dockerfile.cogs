ARG DOCKER_IMAGE=image-registry.openshift-image-registry.svc:5000/e1e498-tools/wps-api-base:python3.9-latest

# Using local docker image to speed up build. See openshift/wps-api-base for details.
FROM ${DOCKER_IMAGE}

# Copy poetry files.
COPY ./cogtiler/pyproject.toml ./cogtiler/poetry.lock /tmp/

# Install dependancies.
RUN cd /tmp && \
    poetry install --no-root --no-dev

# Copy the app:
COPY ./cogtiler/cogtiler /cogtiler/cogtiler

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8090
