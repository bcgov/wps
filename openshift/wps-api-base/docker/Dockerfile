ARG DOCKER_IMAGE=artifacts.developer.gov.bc.ca/docker-remote/ubuntu:22.04
# For the final stage, we use ubuntu:22.04
# Rationale for using ubuntu:22.04:
# - It's the latest ubuntu LTS release.
# - It generally has a more recent version of gdal than debian.
# - It generally has a fairly recent version of python.
# - It has a more recent version of wkhtmltopdf and supporting libraries than debian.
#
# When building local, you can pull direct from docker, instead of artifacts.developer.gov.bc.ca:
# docker build --build-arg DOCKER_IMAGE=ubuntu:22.04 . --tag=wps-api-base:ubuntu.22.04-latest
FROM ${DOCKER_IMAGE}

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Tell r-base not to wait for interactive input.
ENV DEBIAN_FRONTEND=noninteractive

# Install pre-requisites
# - python (we want python!)
# - gdal (for geospatial)
# - R (for cffdrs)
# - xfonts-75dpi, xfonts-base (for wkhtmltopdf)
RUN apt-get update --fix-missing && apt-get -y install python3 python3-pip python3-dev python-is-python3 libgdal-dev r-base xfonts-base xfonts-75dpi curl

RUN curl -sSL https://install.python-poetry.org > /tmp/install.python-poetry.org
RUN curl -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb > /tmp/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
# Enable for mac M1
# RUN curl -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_arm64.deb > /tmp/wkhtmltox_0.12.6.1-2.jammy_amd64.deb


# - wkhtmltopdf (for making pdf's)

# Enable for mac M1
# RUN dpkg -i /tmp/wkhtmltox_0.12.6.1-2.jammy_arm64.deb
RUN dpkg -i /tmp/wkhtmltox_0.12.6.1-2.jammy_amd64.deb

# Install cffdrs
RUN R -e "install.packages('cffdrs')"

# Create our worker user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# When our app is running, we want to allow poetry full access to the workers home directory.
# +x : to execute the poetry binary
# +r : to read poetry cache
RUN chmod a+rx /home/$USERNAME

USER $USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# Set the working directory to the user's home directory
WORKDIR /home/$USERNAME

# Update pip
RUN python3 -m pip install --upgrade pip

# Install poetry
RUN cat /tmp/install.python-poetry.org | python3 -
