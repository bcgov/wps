FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2
# in order to make the image public on GHCR, we need to add this label
LABEL org.opencontainers.image.source="https://github.com/bcgov/wps"

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1010
ENV POETRY_VERSION 1.8.5

# Tell r-base not to wait for interactive input.
ENV DEBIAN_FRONTEND=noninteractive

# Install pre-requisites
# - python (we want python!)
RUN apt-get update --fix-missing && apt-get -y install python3 python3-pip python3-dev python-is-python3 libudunits2-dev curl git build-essential libproj-dev libgeos-dev libsqlite3-dev libpq-dev libtirpc-dev

RUN curl -sSL https://install.python-poetry.org > /tmp/install.python-poetry.org

# Add the worker user with UID 1000
RUN useradd --uid $USER_UID -m $USERNAME

# When our app is running, we want to allow poetry full access to the workers home directory.
# +x : to execute the poetry binary
# +r : to read poetry cache
RUN chmod a+rx /home/$USERNAME

USER $USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# # Set the working directory to the user's home directory
WORKDIR /home/$USERNAME

# # Install poetry
RUN cat /tmp/install.python-poetry.org | python3 -