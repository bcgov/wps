FROM ghcr.io/osgeo/gdal:ubuntu-full-3.13.3
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
# - xfonts-75dpi, xfonts-base (for wkhtmltopdf)
# - tippecanoe for generating pmtiles
RUN apt-get update --fix-missing && apt-get -y install \
    ca-certificates python3 python3-pip python3-dev python-is-python3 \
    libudunits2-dev xfonts-base xfonts-75dpi curl git build-essential \
    libproj-dev libgeos-dev libsqlite3-dev libpq-dev libtirpc-dev libssl-dev \
    libcurl4-openssl-dev libxml2-dev cmake libabsl-dev

# Install tippecanoe for pmtiles
RUN git clone https://github.com/felt/tippecanoe.git --branch 2.62.5 && cd tippecanoe && make -j && make install && cd ..

# Add the worker user with UID 1010 and assign them to the existing group with GID 1000
RUN useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# When our app is running, we want to allow poetry full access to the workers home directory.
# +x : to execute the poetry binary
# +r : to read poetry cache
RUN chmod a+rx /home/$USERNAME

# - wkhtmltopdf (for making pdf's), picking the .deb for the target architecture.
# BuildKit and buildah set TARGETARCH. Builders that don't set it fall back to
# dpkg's architecture.
ARG TARGETARCH
RUN WKHTMLTOX_ARCH="${TARGETARCH:-$(dpkg --print-architecture)}" && \
    WKHTMLTOX_URL=https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2 && \
    case "${WKHTMLTOX_ARCH}" in \
      amd64|arm64) ;; \
      *) echo "Unsupported architecture: ${WKHTMLTOX_ARCH}" >&2; exit 1 ;; \
    esac && \
    curl --proto '=https' --tlsv1.2 -fsSL -o /tmp/wkhtmltox.deb \
      "${WKHTMLTOX_URL}/wkhtmltox_0.12.6.1-2.jammy_${WKHTMLTOX_ARCH}.deb" && \
    dpkg -i /tmp/wkhtmltox.deb

USER $USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# Set the working directory to the user's home directory
WORKDIR /home/$USERNAME
