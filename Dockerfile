ARG DOCKER_IMAGE=image-registry.openshift-image-registry.svc:5000/e1e498-tools/uvicorn-gunicorn-fastapi:python3.8-latest

# Using local docker image to speed up build. See openshift/unicorn-base for details.
FROM ${DOCKER_IMAGE}

# Copy poetry files.
COPY ./api/pyproject.toml ./api/poetry.lock /tmp/

# Install dependancies.
RUN cd /tmp && \
    poetry install --no-root --no-dev

# Copy the app:
COPY ./api/app /app/app
# Copy the static content:
# COPY --from=static /opt/app-root/src/build /app/static
# Copy almebic:
COPY ./api/alembic /app/alembic
COPY ./api/alembic.ini /app
# Copy pre-start.sh (it will be run on startup):
COPY ./api/prestart.sh /app

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080
