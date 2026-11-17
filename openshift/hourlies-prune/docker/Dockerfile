# Defaults to Docker Hub so the image builds off-cluster without an Artifactory login.
# The OpenShift BuildConfig (openshift/build.yaml) passes the Artifactory mirror instead:
# DOCKER_IMAGE=artifacts.developer.gov.bc.ca/docker-remote/ubuntu:24.04
ARG DOCKER_IMAGE=ubuntu:24.04
FROM ${DOCKER_IMAGE}

RUN apt-get update && apt-get -y install ca-certificates curl unzip

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

# Copy script.
COPY prune_hourlies.sh .

# Configure the default command to run.
CMD sh prune_hourlies.sh