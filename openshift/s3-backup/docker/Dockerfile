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
# This is not the reccomended way to install poetry, but it works.
RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install --upgrade poetry

# Switch back to default user - 26 is the postgres user.
USER 26

RUN python3 -m poetry config virtualenvs.create false

# Install python dependencies, using poetry.
COPY pyproject.toml .
COPY poetry.lock .
RUN python3 -m poetry install --no-root --no-dev --verbose

# Copy scripts.
COPY backup_to_s3.sh .
COPY cleanup_bucket.sh .
COPY prune.py .
COPY prune_test.py .

# Configure the default command to run.
CMD sh backup_to_s3.sh