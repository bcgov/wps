# As per https://fastapi.tiangolo.com/deployment/, we use the provided docker image from docker
# tianglo/uvicorn-gunicorn-fastapi:python3.8 - except, we use a copy of it that's been placed
# on openshift:
# If you need to update the openshift image, do the following - all from your local machine
# 1) get the latest:
# docker pull tiangolo/uvicorn-gunicorn-fastapi:python3.8
# 2) tag it for upload:
# docker tag tiangolo/uvicorn-gunicorn-fastapi:python3.8 image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/uvicorn-gunicorn-fastapi:python3.8
# 3) log into openshift:
# docker login -u developer -p $(oc whoami -t) image-registry.apps.silver.devops.gov.bc.ca
# 4) push to openshift:
# docker push image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/uvicorn-gunicorn-fastapi:python3.8
#
FROM image-registry.openshift-image-registry.svc:5000/e1e498-tools/uvicorn-gunicorn-fastapi:python3.8
# see: https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker for available images.

# Install old (2.4.*; current debian) version of gdal and R
RUN apt-get -y update
RUN apt-get -y install libgdal-dev r-base

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
    POETRY_HOME=/opt/poetry python get-poetry.py --version 1.1.6 && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Install cffdrs
RUN R -e "install.packages('cffdrs')"
