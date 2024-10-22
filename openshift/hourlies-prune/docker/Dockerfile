ARG DOCKER_IMAGE=artifacts.developer.gov.bc.ca/docker-remote/ubuntu:24.04
# For the final stage, we use ubuntu:22.04
# Rationale for using ubuntu:22.04:
# - It's the latest ubuntu LTS release.
# - It generally has a more recent version of gdal than debian.
# - It generally has a fairly recent version of python.
# - It has a more recent version of wkhtmltopdf and supporting libraries than debian.
#
# When building local, you can pull direct from docker, instead of artifacts.developer.gov.bc.ca:
# docker build --build-arg DOCKER_IMAGE=ubuntu:24.04 . --tag=wps-api-base:ubuntu:24.04-latest
FROM ${DOCKER_IMAGE}

RUN apt-get update && apt-get -y install unzip

# Download the Amazon CLI installer.
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip

# Switch to root user for package installs.
USER root
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

# Copy script.
COPY prune_hourlies.sh .

# Configure the default command to run.
CMD sh prune_hourlies.sh