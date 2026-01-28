FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2
# in order to make the image public on GHCR, we need to add this label
LABEL org.opencontainers.image.source="https://github.com/bcgov/wps"

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1010

# Tell r-base not to wait for interactive input.
ENV DEBIAN_FRONTEND=noninteractive

# Install pre-requisites
RUN apt-get update --fix-missing && apt-get -y install build-essential curl git python3 python3-dev python-is-python3 python3-pip \
    libgeos-dev libpq-dev libproj-dev libsqlite3-dev libtirpc-dev libudunits2-dev \
    && apt-get clean

# When our app is running, we want to allow poetry full access to the workers home directory.
# Add the worker user with UID 1000
# +x : to execute the poetry binary
# +r : to read poetry cache
RUN useradd --uid "$USER_UID" -m "$USERNAME" && chmod a+rx /home/"$USERNAME"

USER $USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# # Set the working directory to the user's home directory
WORKDIR /home/$USERNAME