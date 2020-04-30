FROM alpine:3.11

ARG OC_VERSION=3.11.0
ARG GLIBC_VERSION=2.31-r0

# Install GNU C Library & dependencies
RUN wget -q -O /etc/apk/keys/sgerrand.rsa.pub https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub \
    && wget "https://github.com/sgerrand/alpine-pkg-glibc/releases/download/${GLIBC_VERSION}/glibc-${GLIBC_VERSION}.apk" \
    && apk --no-cache add make git ca-certificates "glibc-${GLIBC_VERSION}.apk" \
    && rm "glibc-${GLIBC_VERSION}.apk"

# Install OpenShift CLI
RUN wget --quiet -O oc.tar.gz "https://github.com/openshift/origin/releases/download/v${OC_VERSION}/openshift-origin-client-tools-v${OC_VERSION}-0cbc58b-linux-64bit.tar.gz" \
    && FILE=$(tar -tf oc.tar.gz | grep '/oc$') \
    && tar -zxf oc.tar.gz "$FILE" \
    && mv "$FILE" /usr/local/bin/oc \
    && rm -rf oc.tar.gz openshift-origin-client-tools-v*

# Action repo contents to /deployment dir
COPY ./scripts /scripts

ENTRYPOINT ["/scripts/entrypoint.sh"]