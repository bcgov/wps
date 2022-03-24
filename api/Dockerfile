# NOTE:
# This Dockerfile is for local development only!

FROM python:3.8.12-buster

# wildfire one may have an old certificate, so we have to make debian more forgiving.
# RUN sed -i 's/TLSv1.2/TLSv1.0/g' /etc/ssl/openssl.cnf

# Install dependancies need by python developer packages
# NOTE: Once we no longer need pyodbc, please remove the apt-get update and install commands below.
RUN apt-get -y update
RUN apt-get -y install unixodbc-dev
# Install old (2.4.*; current debian) version of gdal
RUN apt-get -y install libgdal-dev

# Install R
RUN apt-get update --fix-missing && apt-get -y install r-base

# Install cffdrs
RUN R -e "install.packages('cffdrs')"

# Install JDK
RUN apt-get -y install openjdk-11-jdk

# Install pdf-kit for PDF generation on HFI (with qt support!)
# As of writing, 0.12.6 (the most recent) is the version currently being installed by 3.8.12-buster,
# but without qt. We do a manual instllation of 0.12.6 in order to get qt support.
RUN apt-get update --fix-missing && apt-get -y install xfonts-75dpi xfonts-base
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb -P /tmp && \
    dpkg -i /tmp/wkhtmltox_0.12.6-1.buster_amd64.deb

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

WORKDIR /app
COPY ./app /app/app
RUN mkdir /app/libs
COPY ./libs /app/libs

EXPOSE 8080

ENV CLASSPATH=/app/libs/REDapp_Lib.jar:/app/libs/WTime.jar:/app/libs/hss-java.jar:${CLASSPATH}
CMD uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
