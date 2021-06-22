# NOTE:
# This Dockerfile is for local development only!

FROM python:3.8-buster

# wildfire one may have an old certificate, so we have to make debian more forgiving.
# RUN sed -i 's/TLSv1.2/TLSv1.0/g' /etc/ssl/openssl.cnf

# Install dependancies need by python developer packages
# NOTE: Once we no longer need pyodbc, please remove the apt-get update and install commands below.
RUN apt-get -y update
RUN apt-get -y install unixodbc-dev
# Install old (2.4.*; current debian) version of gdal and R
RUN apt-get -y install libgdal-dev
RUN apt-get update --fix-missing && apt-get -y install r-base-dev texlive-full
RUN apt-get update --fix-missing && apt-get -y install r-base-core r-base

# Update pip  
RUN python -m pip install --upgrade pip

# Install gdal
# We don't have much control over what version of gdal we're getting, it's pretty much whatever is
# available to us. As such, gdal is not installed by poetry, since the version will differ between
# platforms.
RUN python -m pip install gdal==$(gdal-config --version)

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

RUN ls

RUN R -e "install.packages('cffdrs')"

WORKDIR /app
COPY ./app /app/app

EXPOSE 8080

CMD uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
