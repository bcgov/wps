# Defaults to the official Canonical image on Amazon ECR Public (avoids Docker Hub pull limits,
# no login), so the image builds off-cluster without an Artifactory login.
# The OpenShift BuildConfig (openshift/build.yaml) passes the Artifactory mirror instead:
# DOCKER_IMAGE=artifacts.developer.gov.bc.ca/docker-remote/ubuntu:24.04
ARG DOCKER_IMAGE=public.ecr.aws/ubuntu/ubuntu:24.04
FROM ${DOCKER_IMAGE}

# Omit checksum if not required
ENV AWS_REQUEST_CHECKSUM_CALCULATION when_required

RUN apt-get update && \
    apt-get install -y build-essential ca-certificates libpq-dev postgresql-client-16 python3 ruby-full && \
    gem install pgslice

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

COPY fill_partition_data.sh .
COPY partition_and_archive.sh .