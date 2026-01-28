FROM ghcr.io/osgeo/gdal:ubuntu-small-3.12.1
# in order to make the image public on GHCR, we need to add this label
LABEL org.opencontainers.image.source="https://github.com/bcgov/wps"

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1010
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive

# Install pre-requisites
# - python (we want python!)
# - gdal (for geospatial)
RUN apt-get update --fix-missing && apt-get -y install python3 python3-pip python3-dev python-is-python3 libudunits2-dev curl git build-essential libproj-dev libgeos-dev libsqlite3-dev libpq-dev libtirpc-dev

# Add the worker user with UID 1010 and assign them to the existing group with GID 1000
RUN useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN chmod a+rx /home/$USERNAME

USER $USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# Set the working directory to the user's home directory
WORKDIR /home/$USERNAME
