FROM artifacts.developer.gov.bc.ca/docker-remote/ubuntu:24.04

# Omit checksum if not required
ENV AWS_REQUEST_CHECKSUM_CALCULATION when_required

RUN apt-get update && \
    apt-get install -y build-essential libpq-dev postgresql-client-16 python3 ruby-full && \
    gem install pgslice

# Download the Amazon CLI installer.
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip

# Switch to root user for package installs.
USER root
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

COPY fill_partition_data.sh .
COPY partition_and_archive.sh .