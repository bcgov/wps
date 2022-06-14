ARG DOCKER_IMAGE=image-registry.openshift-image-registry.svc:5000/e1e498-tools/wps-api-base:python3.9-latest
# SUPER IMPORTANT: NODE_OPTIONS="--v8-pool-size=1"
# A pod running in our openshift cluster, will report a ridiculous amount of cpu's available, as
# it's reporting on the underlying hardware. Node, in it's wisdom, will try to scale to using a
# huge amount of cpu's, which in turn results in massive memory usage. It's very important to
# limit the cpu pool size to something realistic.
ARG NODE_OPTIONS="--v8-pool-size=1"
# Source maps are not required for production builds, only for development builds to assist
# in debugging. We set this to false, to reduce memory usage.
ARG GENERATE_SOURCEMAP=false

# PHASE 1 - build static html.
# Pull from local registry - we can't pull from docker due to limits.
# see https://catalog.redhat.com/software/containers/ubi8/nodejs-14/5ed7887dd70cc50e69c2fabb for details
FROM registry.access.redhat.com/ubi8/nodejs-16 as static

# Switch to root user for package installs
USER 0

ADD web .
# NOTE: Can't use "--production=true", because we need react-scripts for yarn run build.
RUN npm install -g npm@latest && npm install -g yarn@latest && yarn install --frozen-lockfile
RUN yarn run build

# Switch back to default user
USER 1001

# PHASE 2 - prepare python.
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
# Copy the static content:
COPY --from=static /opt/app-root/src/build /app/static
# Copy almebic:
COPY ./api/alembic /app/alembic
COPY ./api/alembic.ini /app
# Copy pre-start.sh (it will be run on startup):
COPY ./api/prestart.sh /app

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080

# Set the classpath to include copied libs
ENV CLASSPATH=/app/libs/REDapp_Lib.jar:/app/libs/WTime.jar:/app/libs/hss-java.jar:${CLASSPATH}
