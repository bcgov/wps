FROM artifacts.developer.gov.bc.ca/docker-remote/ubuntu:24.04

RUN apt-get update && \
    apt-get install -y build-base libpq-dev postgresql16-client python3 aws-cli && \
    gem install pgslice

COPY fill_partition_data.sh .
COPY partition_and_archive.sh .