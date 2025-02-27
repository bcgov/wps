FROM --platform=linux/amd64 postgres:16

# Set the locale (important for poetry)
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

RUN apt-get update && apt-get -y install unzip

# Download the Amazon CLI installer.
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-2.23.0.zip" /tmp/awscliv2.zip


# Switch to root user for package installs.
USER root
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

RUN aws --version

RUN apt-get -y install python3 python3-setuptools python3-pip

# We don't care that we break system packages, this is only used for backup related tasks
RUN pip3 install poetry==1.8.5 --break-system-packages

# Getting poetry to play nice in openshift is a nightmare, so we just
# take the easy route and create a requirements.txt file.
COPY pyproject.toml poetry.lock /tmp/
RUN cd /tmp && \
    python3 -m poetry export -f requirements.txt --output requirements.txt && \
    pip3 install -r requirements.txt --break-system-packages

# Copy scripts.
COPY backup_to_s3.sh .
COPY cleanup_bucket.sh .
COPY prune.py .
COPY prune_test.py .

# Configure the default command to run.
CMD sh backup_to_s3.sh