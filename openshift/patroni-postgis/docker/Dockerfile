# Grabbing directly from the bcgov maintained patroni image.
# For details, see: https://github.com/bcgov/patroni-postgres-container/
FROM image-registry.openshift-image-registry.svc:5000/bcgov/patroni-postgres:12.4-latest

ENV POSTGIS_MAJOR 3
ENV POSTGIS_VERSION 3.1.1+dfsg-1.pgdg100+1

# Switch to root user for package installs
USER 0

# PostGIS requirements taken from https://github.com/postgis/docker-postgis
RUN apt-get update \
    && apt-cache showpkg postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
    && apt-get install -y --no-install-recommends \
    postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR=$POSTGIS_VERSION \
    postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts=$POSTGIS_VERSION \
    && rm -rf /var/lib/apt/lists/*

# Add the POSTGIS command to the end of the post_init script.
COPY init_postgis /usr/share/scripts/patroni/
RUN cat /usr/share/scripts/patroni/init_postgis >> /usr/share/scripts/patroni/post_init.sh
RUN rm /usr/share/scripts/patroni/init_postgis

# Switch back to default user
USER 1001