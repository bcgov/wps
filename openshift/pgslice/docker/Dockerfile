# Defaults to Docker Hub so the image builds off-cluster without an Artifactory login.
# The OpenShift BuildConfig (openshift/build.yaml) passes the Artifactory mirror instead:
# DOCKER_IMAGE=artifacts.developer.gov.bc.ca/docker-remote/ubuntu:24.04
ARG DOCKER_IMAGE=ubuntu:24.04
FROM ${DOCKER_IMAGE}

# Omit checksum if not required
ENV AWS_REQUEST_CHECKSUM_CALCULATION when_required

RUN apt-get update && \
    apt-get install -y build-essential ca-certificates curl libpq-dev postgresql-client-16 python3 ruby-full && \
    gem install pgslice

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

COPY fill_partition_data.sh .
COPY partition_and_archive.sh .