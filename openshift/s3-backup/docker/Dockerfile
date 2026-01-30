FROM postgres:16

# Set the locale
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Omit checksum if not required
ENV AWS_REQUEST_CHECKSUM_CALCULATION when_required

# Install system dependencies and clean up cache
RUN apt-get update && apt-get -y install unzip python3 python3-setuptools python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Download and install AWS CLI, then clean up
ADD "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" /tmp/awscliv2.zip
RUN unzip /tmp/awscliv2.zip -d /tmp/ \
    && /tmp/aws/install \
    && rm -rf /tmp/aws /tmp/awscliv2.zip

# Install uv and clean cache
RUN pip3 install uv==0.9.26 --break-system-packages --no-cache-dir

# Install Python dependencies
COPY pyproject.toml uv.lock /tmp/
RUN cd /tmp \
    && uv sync --no-cache

# Copy scripts
COPY backup_to_s3.sh cleanup_bucket.sh prune.py prune_test.py ./

# Configure the default command to run
CMD ["sh", "backup_to_s3.sh"]
