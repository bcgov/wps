FROM postgres:16

# Set the locale
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Omit checksum if not required
ENV AWS_REQUEST_CHECKSUM_CALCULATION when_required


RUN apt-get update && apt-get -y install curl unzip

# Download and install the Amazon CLI for the target architecture.
# TARGETARCH is set by BuildKit and buildah; fall back to dpkg's architecture for builders that don't set it.
ARG TARGETARCH
USER root
RUN case "${TARGETARCH:-$(dpkg --print-architecture)}" in \
      amd64) AWSCLI_ARCH=x86_64 ;; \
      arm64) AWSCLI_ARCH=aarch64 ;; \
      *) echo "Unsupported architecture: ${TARGETARCH:-$(dpkg --print-architecture)}" >&2; exit 1 ;; \
    esac && \
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${AWSCLI_ARCH}.zip" -o /tmp/awscliv2.zip && \
    unzip /tmp/awscliv2.zip -d /tmp/ && \
    /tmp/aws/install

RUN apt-get -y install python3

COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /bin/

# Install locked dependencies into a venv and put it first on PATH, so the
# scripts' plain `python3` calls pick it up.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
# Use the base image's python3; fail the build rather than download another.
ENV UV_PYTHON_DOWNLOADS=never
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-build

# Copy scripts.
COPY backup_to_s3.sh cleanup_bucket.sh prune.py prune_test.py ./

# Configure the default command to run.
CMD ["bash", "backup_to_s3.sh"]