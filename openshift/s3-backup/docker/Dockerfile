FROM centos/postgresql-12-centos7

ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Download the installer
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip

# Switch to root user for package installs
USER root
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

RUN yum install -y python3
RUN yum install -y python3-setuptools

# Switch back to default user - 26 is the postgres user

USER 26

# Install poetry
RUN pip3 install --user --upgrade pip setuptools wheel
RUN pip3 install --user --upgrade poetry

# Install python dependencies.
COPY pyproject.toml .
COPY poetry.lock .
RUN python3 -m poetry install

# Copy scripts
COPY backup_to_s3.sh .
COPY cleanup_bucket.sh .
COPY prune.py .

CMD sh backup_to_s3.sh