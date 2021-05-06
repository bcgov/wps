# As per https://fastapi.tiangolo.com/deployment/, we use the provided docker image:
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
# see: https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker for available images.

# Install old (2.4.*; current debian) version of gdal
RUN apt-get -y update
RUN apt-get -y install libgdal-dev

# wildfire one may have an old certificate, so we have to make debian more forgiving.
# RUN sed -i 's/TLSv1.2/TLSv1.0/g' /etc/ssl/openssl.cnf

# Update pip  
RUN python -m pip install --upgrade pip

# According to the stackexchange thread below, we need to install numpy before
# installing gdal or we could end up missing _gdal_array
# https://gis.stackexchange.com/questions/153199/import-error-no-module-named-gdal-array
RUN python -m pip install numpy

# Install gdal
# We don't have much control over what version of gdal we're getting, it's pretty much whatever is
# available to us. As such, gdal is not installed by poetry, since the version will differ between
# platforms.
RUN python -m pip install gdal==$(gdal-config --version)

# Install poetry https://python-poetry.org/docs/#installation
RUN cd /tmp && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py > get-poetry.py && \
    POETRY_HOME=/opt/poetry python get-poetry.py --version 1.1.5 && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false