FROM ankane/pgslice:v0.6.1

RUN echo "https://dl-cdn.alpinelinux.org/alpine/v3.21/main" >> /etc/apk/repositories
RUN apk update 
RUN apk del postgresql-common postgresql15-client postgresql15 
RUN apk add unzip bash postgresql16-client python3 aws-cli

COPY fill_partition_data.sh .
COPY partition_and_archive.sh .