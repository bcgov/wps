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

RUN apt-get -y install python3

COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /bin/

# Install locked dependencies into a venv and put it first on PATH, so the
# scripts' plain `python3` calls pick it up.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
# Use the base image's python3; fail the build rather than download another.
ENV UV_PYTHON_DOWNLOADS=never
ENV PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml uv.lock /tmp/
RUN cd /tmp && uv sync --locked --no-dev --no-build

# Copy scripts.
COPY backup_to_s3.sh .
COPY cleanup_bucket.sh .
COPY prune.py .
COPY prune_test.py .

# Configure the default command to run.
CMD sh backup_to_s3.sh