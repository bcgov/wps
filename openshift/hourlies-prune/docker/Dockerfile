ARG DOCKER_IMAGE=artifacts.developer.gov.bc.ca/docker-remote/ubuntu:24.04
# For the final stage, we use ubuntu:22.04
# Rationale for using ubuntu:22.04:
# - It's the latest ubuntu LTS release.
# - It generally has a more recent version of gdal than debian.
# - It generally has a fairly recent version of python.
# - It has a more recent version of wkhtmltopdf and supporting libraries than debian.
#
# When building local, you can pull direct from docker, instead of artifacts.developer.gov.bc.ca:
# docker build --build-arg DOCKER_IMAGE=ubuntu:24.04 . --tag=wps-api-base:ubuntu:24.04-latest
FROM ${DOCKER_IMAGE}

RUN apt-get update && apt-get -y install ca-certificates unzip

# Download and install the Amazon CLI for the target architecture.
# BuildKit and buildah set TARGETARCH. Builders that don't set it fall back to
# dpkg's architecture.
ARG TARGETARCH
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    TARGET_ARCH="${TARGETARCH:-$(dpkg --print-architecture)}" && \
    case "${TARGET_ARCH}" in \
      amd64) AWSCLI_ARCH=x86_64 ;; \
      arm64) AWSCLI_ARCH=aarch64 ;; \
      *) echo "Unsupported architecture: ${TARGET_ARCH}" >&2; exit 1 ;; \
    esac && \
    curl --proto '=https' --tlsv1.2 -fsSL -o /tmp/awscliv2.zip \
      "https://awscli.amazonaws.com/awscli-exe-linux-${AWSCLI_ARCH}.zip" && \
    unzip /tmp/awscliv2.zip -d /tmp/ && \
    /tmp/aws/install

# Copy script.
COPY prune_hourlies.sh .

# Configure the default command to run.
CMD sh prune_hourlies.sh