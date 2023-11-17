# Grabbing directly from the bcgov maintained patroni image.
# For details, see: https://github.com/bcgov/patroni-postgres-container/
FROM image-registry.openshift-image-registry.svc:5000/bcgov/patroni-postgres:12.4-latest

ENV POSTGIS_MAJOR 3
ENV POSTGIS_VERSION 3.3.4+dfsg-1.pgdg100+1

# Switch to root user for package installs
USER 0

# PostGIS requirements taken from https://github.com/postgis/docker-postgis
RUN apt-get update \
    && apt-cache showpkg postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
    && apt-get install -y --no-install-recommends \
    # ca-certificates: for accessing remote raster files;
    #   fix: https://github.com/postgis/docker-postgis/issues/307
    ca-certificates \
    \
    postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR=$POSTGIS_VERSION \
    postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts \
    pgbackrest \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p -m 777 /var/log/pgbackrest \
    && chown postgres:postgres /var/log/pgbackrest \
    && mkdir -p /etc/pgbackrest \
    && mkdir -p /etc/pgbackrest/conf.d \
    && touch /etc/pgbackrest/pgbackrest.conf \
    && chmod 777 /etc/pgbackrest/pgbackrest.conf \
    && chown postgres:postgres /etc/pgbackrest/pgbackrest.conf


EXPOSE 5432 8008 2222
# ENV LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 EDITOR=/usr/bin/editor
# ENV HOME=/home/postgres
# ENV SSHD_CONF_DIR=/home/postgres/ssh_config_template
# ENV START_SSHD=false

# ADD start_sshd.sh /run/

# COPY ssh /ssh_conf_template
# ADD ssh/ssh_config /etc/ssh/ssh_config
# RUN chmod 777 /ssh_conf_template

RUN echo \ 
    "[global] \n \
    repo1-type=s3 \n \
    repo1-storage-verify-tls=n \n \
    repo1-s3-endpoint=$OBJECT_STORE_SERVER \n\
    repo1-s3-uri-style=path \n\
    repo1-s3-bucket=$OBJECT_STORE_BUCKET \n\
    repo1-s3-key=$OBJECT_STORE_USER_ID \n \
    repo1-s3-key-secret=$OBJECT_STORE_SECRET \n \
    repo1-s3-region=eu-west-3 \n \
    \n \
    repo1-path=/repo1 \n \
    repo1-retention-full=3 \n \
    start-fast=y \n \
    log-level-console=info \n \
    log-level-file=debug \n \
    delta=y \n \
    process-max=2 \n \
    \n \
    [demo-cluster-1] \n \
    pg1-path=/home/postgres/pgdata/pgroot/data \
    pg1-port=5432 \n \
    pg1-user=postgres" >> /etc/pgbackrest/pgbackrest.conf

# Add the POSTGIS command to the end of the post_init script.
COPY init_postgis /usr/share/scripts/patroni/
RUN cat /usr/share/scripts/patroni/init_postgis >> /usr/share/scripts/patroni/post_init.sh
RUN rm /usr/share/scripts/patroni/init_postgis

# Switch back to default user
USER 1001