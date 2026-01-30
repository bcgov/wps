FROM postgres:16

# Set the locale
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Omit checksum if not required
ENV AWS_REQUEST_CHECKSUM_CALCULATION when_required

RUN apt-get update && apt-get -y install unzip

# Download the Amazon CLI installer.
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip

# Switch to root user for package installs.
USER root
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

RUN apt-get -y install python3 python3-setuptools python3-pip

# We don't care that we break system packages, this is only used for backup related tasks
RUN pip3 install uv --break-system-packages

# Install dependencies using uv from pyproject.toml
COPY pyproject.toml uv.lock /tmp/
RUN cd /tmp && uv sync

# Copy scripts.
COPY backup_to_s3.sh .
COPY cleanup_bucket.sh .
COPY prune.py .
COPY prune_test.py .

# Configure the default command to run.
CMD sh backup_to_s3.sh
