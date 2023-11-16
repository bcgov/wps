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

# Add the POSTGIS command to the end of the post_init script.
COPY init_postgis /usr/share/scripts/patroni/
RUN cat /usr/share/scripts/patroni/init_postgis >> /usr/share/scripts/patroni/post_init.sh
RUN rm /usr/share/scripts/patroni/init_postgis

# configure pgbackrest
RUN mkdir -p /home/pgbackrest \
    && touch /home/pgbackrest/pgbackrest.conf \
    && echo "[global] \
    repo1-type=s3 \
    repo1-storage-verify-tls=n \
    repo1-s3-endpoint=$OBJECT_STORE_SERVER \
    repo1-s3-uri-style=path \
    repo1-s3-bucket=$OBJECT_STORE_BUCKET \
    repo1-s3-key=$OBJECT_STORE_USER_ID \
    repo1-s3-key-secret=$OBJECT_STORE_SECRET \
    repo1-s3-region=eu-west-3 \
    \
    repo1-path=/repo1 \
    repo1-retention-full=3 \
    start-fast=y \
    log-level-console=info \
    log-level-file=debug \
    delta=y \
    process-max=2 \
    \
    [demo-cluster-1] \
    pg1-port=5432 \
    pg1-user=postgres" >> /home/pgbackrest/pgbackrest.conf

# Switch back to default user
USER 1001