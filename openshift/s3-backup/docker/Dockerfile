FROM centos/postgresql-12-centos7

# Set the locale (important for poetry)
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Download the Amazon CLI installer.
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip

# Switch to root user for package installs.
USER root
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

RUN yum install -y python3 python3-setuptools

# Install poetry.
# This is not the recommended way to install poetry, but it works.
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install --upgrade poetry

# Getting poetry to play nice with centos in openshift is a nightmare, so we just
# take the easy route and create a requirements.txt file.
COPY pyproject.toml poetry.lock /tmp/
RUN cd /tmp && \
    python3 -m poetry export -f requirements.txt --output requirements.txt && \
    pip3 install -r requirements.txt

# Switch back to default user - 26 is the postgres user.
USER 26

# Copy scripts.
COPY backup_to_s3.sh .
COPY cleanup_bucket.sh .
COPY prune.py .
COPY prune_test.py .

# Configure the default command to run.
CMD sh backup_to_s3.sh