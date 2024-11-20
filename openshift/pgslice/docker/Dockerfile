FROM ankane/pgslice:v0.6.1

RUN apk update && apk add unzip bash jq postgresql python3

# Download the Amazon CLI installer.
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip

# Switch to root user for package installs.
USER root
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install


COPY fill_partition_data.sh .
COPY partition_and_archive.sh .