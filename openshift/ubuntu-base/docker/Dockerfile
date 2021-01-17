FROM ubuntu:20.04

# Install GDAL
RUN apt-get -y update
RUN apt-get -y upgrade
RUN TZ="Etc/UTC" DEBIAN_FRONTEND="noninteractive" apt-get -y install libgdal-dev

# RUN apt-get -y install python
# RUN apt-get -y install python3
RUN apt-get -y install python3.8
RUN apt-get -y install python3-pip

# Update pip  
CMD python3 -m pip install --upgrade pip

# According to the stackexchange thread below, we need to install numpy before
# installing gdal or we could end up missing _gdal_array
# https://gis.stackexchange.com/questions/153199/import-error-no-module-named-gdal-array
RUN python3 -m pip install numpy

# Install gdal
# We don't have much control over what version of gdal we're getting, it's pretty much whatever is
# available to us. As such, gdal is not installed by poetry, since the version will differ between
# platforms.
RUN python3 -m pip install gdal==$(gdal-config --version)

# Install poetry https://python-poetry.org/docs/#installation
RUN cd /tmp && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py > get-poetry.py && \
    POETRY_HOME=/opt/poetry python get-poetry.py --version 1.1.4 && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false