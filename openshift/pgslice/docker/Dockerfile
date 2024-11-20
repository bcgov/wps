FROM ankane/pgslice:v0.6.1

RUN echo "https://dl-cdn.alpinelinux.org/alpine/v3.21/main" >> /etc/apk/repositories

RUN apk update && apk add unzip bash postgresql16 python3 aws-cli

COPY fill_partition_data.sh .
COPY partition_and_archive.sh .