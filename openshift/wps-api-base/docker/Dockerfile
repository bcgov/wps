# When building in openshift, you'll need the latest image in openshift:
# 1) get the latest:
# docker pull ubuntu:22.04
# 2) tag it for upload:
# docker tag ubuntu:22.04 image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/ubuntu:22.04
# 3) log into openshift:
# docker login -u developer -p $(oc whoami -t) image-registry.apps.silver.devops.gov.bc.ca
# 4) push to openshift:
# docker push image-registry.apps.silver.devops.gov.bc.ca/e1e498-tools/ubuntu:22.04


# Rationale for using ubuntu:22.04:
# - It's the latest ubuntu LTS release.
# - It generally has a more recent version of gdal than debian.
# - It generally has a fairly recent version of python.
# - It has a more recent version of wkhtmltopdf and supporting libraries than debian.
# When building in openshift, you can reference the image in openshift:
# FROM image-registry.openshift-image-registry.svc:5000/e1e498-tools/ubuntu:22.04
#
# When building local, you can reference the docker image:
FROM ubuntu:22.04

ARG USERNAME=worker
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Tell r-base not to wait for interactive input.
ENV DEBIAN_FRONTEND=noninteractive

# Install pre-requisites
# - python (we want python!)
# - gdal (for geospatial)
# - R (for cffdrs)
# - JDK (for red-app)
# - wkhtmltopdf (for making pdf's)
RUN apt-get update --fix-missing && apt-get -y install python3 python3-pip python3-dev python-is-python3 libgdal-dev r-base openjdk-17-jdk wkhtmltopdf

# Install cffdrs
RUN R -e "install.packages('cffdrs')"

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

USER $USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

WORKDIR /home/$USERNAME

# Update pip  
RUN python3 -m pip install --upgrade pip

RUN curl -sSL https://install.python-poetry.org | python3 -

# According to the stackexchange thread below, we need to install numpy before
# installing gdal or we could end up missing _gdal_array
# https://gis.stackexchange.com/questions/153199/import-error-no-module-named-gdal-array
# RUN python -m pip install numpy

# Install gdal
# We don't have much control over what version of gdal we're getting, it's pretty much whatever is
# available to us. As such, gdal is not installed by poetry, since the version will differ between
# platforms.
# RUN python -m pip install gdal==$(gdal-config --version)

# Install poetry https://python-poetry.org/docs/#installation
# RUN cd /tmp && \
#     curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py > install-poetry.py && \
#     POETRY_HOME=/opt/poetry python install-poetry.py --version 1.1.11 && \
#     cd /usr/local/bin && \
#     ln -s /opt/poetry/bin/poetry && \
#     poetry config virtualenvs.create false && \
#     poetry config experimental.new-installer false
