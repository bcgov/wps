FROM artifacts.developer.gov.bc.ca/docker-remote/ubuntu:24.04

RUN apt-get update && \
    apt-get install -y build-essential libpq-dev postgresql16-client ruby-full && \
    gem install pgslice

# Download the Amazon CLI installer.
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip

# Switch to root user for package installs.
USER root
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

COPY fill_partition_data.sh .
COPY partition_and_archive.sh .