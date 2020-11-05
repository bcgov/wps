# PHASE 1 - build static html.
FROM node:10 as static

# Set the working directory
WORKDIR /app
COPY web /app/
RUN npx browserslist@latest --update-db
RUN npm run build

# PHASE 2 - prepare python.
# As per https://fastapi.tiangolo.com/deployment/, we use the provided docker image:
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
# see: https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker for available images.

# Install old (2.4.*; current debian) version of gdal
RUN apt-get -y update
RUN apt-get -y install libgdal-dev

# spotwx has an old certificate, so we have to make debian more forgiving.
RUN sed -i 's/TLSv1.2/TLSv1.0/g' /etc/ssl/openssl.cnf

# Update pip  
RUN python -m pip install --upgrade pip

# Install gdal
# We don't have much control over what version of gdal we're getting, it's pretty much whatever is
# available to us. As such, gdal is not installed by poetry, since the version will differ between
# platforms.
RUN python -m pip install gdal==$(gdal-config --version)

# Install poetry https://python-poetry.org/docs/#installation
RUN cd /tmp && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py > get-poetry.py && \
    POETRY_HOME=/opt/poetry python get-poetry.py --version 1.0.8 && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry files.
COPY ./api/pyproject.toml ./api/poetry.lock /tmp/

# Install dependancies.
RUN cd /tmp && \
    poetry install --no-root --no-dev

# Copy the app:
COPY ./api/app /app/app
# Copy the static content:
COPY --from=static /app/build /app/static
# COPY ./static /app/static
# Copy almebic:
COPY ./api/alembic /app/alembic
COPY ./api/alembic.ini /app
# Copy pre-start.sh (it will be run on startup):
COPY ./api/prestart.sh /app

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080
