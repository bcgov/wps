# As per https://fastapi.tiangolo.com/deployment/, we use the provided docker image:
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

# spotwx has an old certificate, so we have to make debian more forgiving.
RUN sed -i 's/TLSv1.2/TLSv1.0/g' /etc/ssl/openssl.cnf

# Install poetry
RUN cd /tmp && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py > get-poetry.py && \
    POETRY_HOME=/opt/poetry python get-poetry.py --version 1.0.8 && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry files.
COPY pyproject.toml poetry.lock /tmp/

# Install dependancies.
RUN cd /tmp && \
    poetry install --no-root --no-dev

COPY ./app /app
COPY ./alembic /bootstrap/alembic
COPY alembic.ini /bootstrap

# The fastapi docker image defaults to port 80, but openshift doesn't allow non-root users port 80.
EXPOSE 8080