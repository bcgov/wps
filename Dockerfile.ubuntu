# Using local docker image to speed up build. See openshift/unicorn-base for details.
FROM image-registry.openshift-image-registry.svc:5000/e1e498-tools/ubuntu-base:20.04

# Copy poetry files.
COPY ./api/pyproject.toml ./api/poetry.lock /tmp/

# Install dependancies.
RUN cd /tmp && \
    poetry install --no-root --no-dev

# Copy the app:
COPY ./api/app /app/app

WORKDIR /app
