ARG DOCKER_IMAGE=image-registry.openshift-image-registry.svc:5000/e1e498-tools/wps-api-base:python3.9-latest

# Using local docker image to speed up build. See openshift/wps-api-base for details.
FROM ${DOCKER_IMAGE}

# Copy poetry files.
COPY ./api/pyproject.toml ./api/poetry.lock /tmp/

# Install dependancies.
RUN cd /tmp && \
    poetry install --no-root --no-dev

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

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080

# Set the classpath to include copied libs
ENV CLASSPATH=/app/libs/REDapp_Lib.jar:/app/libs/WTime.jar:/app/libs/hss-java.jar:${CLASSPATH}
