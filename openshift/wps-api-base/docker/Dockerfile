ARG DOCKER_IMAGE=artifacts.developer.gov.bc.ca/docker-remote/ubuntu:22.04
# STAGE 0 : "poetry"
FROM registry.access.redhat.com/rhel7/rhel-tools AS poetry
# We grab the image for step 0 from registry.access.redhat.com because both openshift and your
# local machine can access it - so it's easy to test in both environments.
# We can use any image we want here - we just need something to grab the latest poetry installer
# for us. We don't want to have any dependencies on the final image, that we don't need there
# and curl is one of those.

RUN curl -sSL https://install.python-poetry.org > /tmp/install.python-poetry.org

# For the final stage, we use ubuntu:22.04
# Rationale for using ubuntu:22.04:
# - It's the latest ubuntu LTS release.
# - It generally has a more recent version of gdal than debian.
# - It generally has a fairly recent version of python.
# - It has a more recent version of wkhtmltopdf and supporting libraries than debian.
# When building in openshift, you can reference the image in openshift:
# FROM image-registry.openshift-image-registry.svc:5000/e1e498-tools/ubuntu:22.04
#
# When building local, you can do
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
# - JDK (for red-app)
# - wkhtmltopdf (for making pdf's)
RUN apt-get update --fix-missing && apt-get -y install python3 python3-pip python3-dev python-is-python3 libgdal-dev r-base openjdk-17-jdk wkhtmltopdf

# Install cffdrs
RUN R -e "install.packages('cffdrs')"

# Create our worker user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

USER $USERNAME
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# Set the working directory to the user's home directory
WORKDIR /home/$USERNAME

# Update pip
RUN python3 -m pip install --upgrade pip

# Install poetry (using installation file from previous stage)
COPY --from=poetry /tmp/install.python-poetry.org ./tmp/install.python-poetry.org
RUN cat ./tmp/install.python-poetry.org | python3 -
