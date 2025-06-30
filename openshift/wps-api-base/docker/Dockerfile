FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2
# in order to make the image public on GHCR, we need to add this label
LABEL org.opencontainers.image.source="https://github.com/bcgov/wps"

# We don't want to run our app as root, so we define a worker user.
ARG USERNAME=worker
ARG USER_UID=1010
ARG USER_GID=1000

# Tell r-base not to wait for interactive input.
ENV DEBIAN_FRONTEND=noninteractive

# Install pre-requisites
# - python (we want python!)
# - gdal (for geospatial)
# - R (for cffdrs)
# - xfonts-75dpi, xfonts-base (for wkhtmltopdf)
# - tippecanoe for generating pmtiles
# - Additional libraries for R spatial packages (s2, sf)
# - cmake and libabsl-dev for s2 package compilation
RUN apt-get update --fix-missing && apt-get -y install python3 python3-pip python3-dev python-is-python3 libudunits2-dev r-base-dev xfonts-base xfonts-75dpi curl git build-essential libproj-dev libgeos-dev libsqlite3-dev libpq-dev libtirpc-dev libssl-dev libcurl4-openssl-dev libxml2-dev cmake libabsl-dev

RUN curl -sSL https://install.python-poetry.org > /tmp/install.python-poetry.org
RUN curl -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb > /tmp/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
# Enable for mac M1
# RUN curl -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_arm64.deb > /tmp/wkhtmltox_0.12.6.1-2.jammy_amd64.deb


# - wkhtmltopdf (for making pdf's)

# Enable for mac M1
# RUN dpkg -i /tmp/wkhtmltox_0.12.6.1-2.jammy_arm64.deb
RUN dpkg -i /tmp/wkhtmltox_0.12.6.1-2.jammy_amd64.deb

# Install tippecanoe for pmtiles
RUN git clone https://github.com/felt/tippecanoe.git --branch 2.62.5 && cd tippecanoe && make -j && make install && cd ..

# Install cffdrs
RUN R -e "install.packages('cffdrs')"

# Add the worker user with UID 1010 and assign them to the existing group with GID 1000
RUN useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# When our app is running, we want to allow poetry full access to the workers home directory.
# +x : to execute the poetry binary
# +r : to read poetry cache
RUN chmod a+rx /home/$USERNAME

USER $USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# Set the working directory to the user's home directory
WORKDIR /home/$USERNAME

# Install poetry
RUN cat /tmp/install.python-poetry.org | python3 -