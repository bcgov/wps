ARG DOCKER_IMAGE=image-registry.openshift-image-registry.svc:5000/e1e498-tools/wps-api-base:ubuntu.22.04-latest

# Using local docker image to speed up build. See openshift/wps-api-base for details.
# To build locally, pointing to local base image: docker build --build-arg DOCKER_IMAGE=wps-api-base:my-tag .

FROM ${DOCKER_IMAGE}

ARG USERNAME=worker
ARG USER_UID=1000
ARG USER_GID=$USER_UID

USER 0

RUN mkdir /app
RUN chown $USERNAME /app
WORKDIR /app

USER $USERNAME

# Copy poetry files.
COPY --chown=$USERNAME:$USERNAME ./api/pyproject.toml ./api/poetry.lock /app/
RUN poetry install

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

CMD ["./start.sh"]