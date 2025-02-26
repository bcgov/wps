FROM postgres:16

# Set the locale (important for poetry)
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

RUN apt-get update && apt-get -y install unzip

# Download the Amazon CLI installer.
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip

# Switch to root user for package installs.
USER root
RUN unzip /tmp/awscliv2.zip -d /tmp/ &&\
    /tmp/aws/install

RUN apt-get -y install curl python3 python3-setuptools python3-pip

# Download poetry
RUN curl -sSL https://install.python-poetry.org > /tmp/install.python-poetry.org

ARG USERNAME=worker
ARG USER_UID=1010
ARG USER_GID=1000

# Add the worker user with UID 1010
RUN useradd --uid $USER_UID -m $USERNAME

# When our app is running, we want to allow poetry full access to the workers home directory.
# +x : to execute the poetry binary
# +r : to read poetry cache
RUN chmod a+rx /home/$USERNAME

ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

RUN mkdir /app
RUN chown "$USERNAME" /app
RUN chmod a+w /app

USER $USERNAME

COPY --chown=$USERNAME pyproject.toml poetry.lock prune.py prune_test.py backup_to_s3.sh cleanup_bucket.sh /app/

# Install poetry
RUN cat /tmp/install.python-poetry.org | python3 -

# Add poetry location to PATH
# ENV PATH="/root/.local/bin:${PATH}"

# We don't care that we break system packages, this is only used for backup related tasks
# RUN pip3 install poetry==1.8.5 --break-system-packages

# Getting poetry to play nice in openshift is a nightmare, so we just
# take the easy route and create a requirements.txt file.
# COPY pyproject.toml poetry.lock /tmp/

RUN cd /app && \
    poetry install --no-root

# RUN cd /tmp && \
#     /usr/local/bin/poetry install --no-root
#python3 -m poetry install --no-root
# export -f requirements.txt --output requirements.txt && \
# pip3 install -r requirements.txt --break-system-packages

USER root

ENV POSTGRES_HOST_AUTH_METHOD trust

# Copy scripts.
# COPY prune.py /app
# COPY prune_test.py /tmp
# COPY backup_to_s3.sh /tmp
# COPY cleanup_bucket.sh /tmp

# Configure the default command to run.
# CMD sh /tmp/backup_to_s3.sh

