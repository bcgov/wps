ARG DOCKER_IMAGE=image-registry.openshift-image-registry.svc:5000/e1e498-tools/uvicorn-gunicorn-fastapi:python3.8-latest

# PHASE 1 - build static html.
# Pull from local registry - we can't pull from docker due to limits.
# see https://catalog.redhat.com/software/containers/ubi8/nodejs-14/5ed7887dd70cc50e69c2fabb for details
FROM registry.access.redhat.com/ubi8/nodejs-14 as static

# Switch to root user for package installs
USER 0

ADD web .
RUN npm i yarn && yarn install --production
RUN yarn run build

# Switch back to default user
USER 1001

# PHASE 2 - prepare python.
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
COPY --from=static /opt/app-root/src/build /app/static
# Copy almebic:
COPY ./api/alembic /app/alembic
COPY ./api/alembic.ini /app
# Copy pre-start.sh (it will be run on startup):
COPY ./api/prestart.sh /app

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080
