FROM ankane/pgslice:v0.6.1

RUN apk update && apk add unzip bash postgresql16 python3 aws-cli

COPY fill_partition_data.sh .
COPY partition_and_archive.sh .