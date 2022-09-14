# As per https://fastapi.tiangolo.com/deployment/, we use the provided docker image from docker
# tianglo/uvicorn-gunicorn-fastapi:python3.9
# see: https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker for available images.
#
# When building in openshift, you'll need the latest image in openshift:
# 1) get the latest:
# docker pull tiangolo/uvicorn-gunicorn-fastapi:python3.9
# 2) tag it for upload:
# docker tag tiangolo/uvicorn-gunicorn-fastapi:python3.9 image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/uvicorn-gunicorn-fastapi:python3.9
# 3) log into openshift:
# docker login -u developer -p $(oc whoami -t) image-registry.apps.silver.devops.gov.bc.ca
# 4) push to openshift:
# docker push image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/uvicorn-gunicorn-fastapi:python3.9


# When building in openshift, you can reference the image in openshift:
# FROM image-registry.openshift-image-registry.svc:5000/e1e498-tools/uvicorn-gunicorn-fastapi:python3.9
#
# When building local, you can reference the docker image:
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

# Install pre-requisites
# - old (2.4.*; current debian) version of gdal
# - R (for cffdrs)
# - JDK (for red-app)
# - xfonts-75dpi xfonts-base (for wkhtmltopdf)
RUN apt-get update --fix-missing && apt-get -y install libgdal-dev r-base openjdk-11-jdk xfonts-75dpi xfonts-base

# Install cffdrs
RUN R -e "install.packages('cffdrs')"

# Install pdf-kit for PDF generation on HFI (with qt support!)
# We can't just run apt-get -y install wkhtmltopdf, because we don't get qt support.
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb -P /tmp && \
    dpkg -i /tmp/wkhtmltox_0.12.6-1.buster_amd64.deb

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
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py > install-poetry.py && \
    POETRY_HOME=/opt/poetry python install-poetry.py --version 1.1.11 && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false && \
    poetry config experimental.new-installer false
