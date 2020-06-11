FROM python:3.8-buster

# spotwx has an old certificate, so we have to make debian more forgiving.
RUN sed -i 's/TLSv1.2/TLSv1.0/g' /etc/ssl/openssl.cnf

WORKDIR /app
COPY ./app /app

# Install dependancies need by python developer packages
# NOTE: Once we no longer need pyodbc, please remove the apt-get update and install commands below.
RUN apt-get -y update
RUN apt-get -y install unixodbc-dev

# Install poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry files.
COPY pyproject.toml poetry.lock /tmp/

# Install dependancies.
RUN cd /tmp && \
    poetry install --no-root

EXPOSE 8080

CMD python -m db.create_db; uvicorn main:app --reload --host 0.0.0.0 --port 8080
