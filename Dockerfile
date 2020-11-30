# PHASE 1 - build static html.
# FROM node:10 as static <-- pulls from docker, can't use
FROM registry.access.redhat.com/rhscl/nodejs-10-rhel7 as static
# FROM registry.access.redhat.com/ubi7/nodejs-10 as static
# FROM ubi7/nodejs-10 as static <-- error: 
# FROM nodejs:10 as static <-- error: build error: failed to pull image: repository docker.io/nodejs not found: does not exist or no pull access

# Set the working directory
# RUN pwd
# RUN mkdir /tmp/app
# WORKDIR /tmp/app
# COPY web /tmp/app/
USER 0
RUN pwd
ADD web .
RUN npm ci --production
RUN npm run build
USER 1001

# PHASE 2 - prepare python.
# Using local docker image to speed up build. See openshift/unicorn-base for details.
FROM docker-registry.default.svc:5000/auzhsi-tools/uvicorn-gunicorn-fastapi:python3.8-latest

# Copy poetry files.
COPY ./api/pyproject.toml ./api/poetry.lock /tmp/

# Install dependancies.
RUN cd /tmp && \
    poetry install --no-root --no-dev

# Copy the app:
COPY ./api/app /app/app
# Copy the static content:
COPY --from=static /app/build /app/static
# Copy almebic:
COPY ./api/alembic /app/alembic
COPY ./api/alembic.ini /app
# Copy pre-start.sh (it will be run on startup):
COPY ./api/prestart.sh /app

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080
