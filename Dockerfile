# PHASE 1 - build static html.
FROM registry.access.redhat.com/rhscl/nodejs-10-rhel7 as static

# Set the working directory
WORKDIR /app
COPY web /app/
RUN npm ci --production
RUN npm run build

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
